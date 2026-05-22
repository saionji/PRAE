#!/usr/bin/env python3
# SOURCE: PDAE ${PDAE_HOME}/tools/check_contracts.py (v5.8.0, 2026-04-19)
# Do not modify; re-copy from PDAE to update.
"""
check_contracts.py — PDAE v5.8.0 契约检查脚本

从 contracts.yaml 读取约束规则，对代码进行确定性检查。
非 AI 检查 AI — 用确定性脚本守护约束。

退出码:
  0 = 所有检查通过
  1 = IMMUTABLE 违规 (阻塞合并)
  2 = CRITICAL 违规 (阻塞合并)
  3 = NEED_REVIEW 变更 (不阻塞，需聚焦复核)
  4 = contracts.yaml 格式错误

用法:
  python3 tools/check_contracts.py --contracts contracts.yaml --src src/
  python3 tools/check_contracts.py --contracts contracts.yaml --src src/ --level immutable
  python3 tools/check_contracts.py --contracts contracts.yaml --src src/ --id IMM-001
"""

import argparse
import ast
import glob
import hashlib
import json
import os
import re
import sys
from dataclasses import dataclass, field as _field
from pathlib import Path

try:
    import yaml
except ImportError:
    print("[ERROR] pyyaml 未安装。请运行: pip install pyyaml")
    sys.exit(4)


# ========================================
# ANSI 颜色
# ========================================
class Color:
    PASS = "\033[92m"   # 绿色
    FAIL = "\033[91m"   # 红色
    WARN = "\033[93m"   # 黄色
    RESET = "\033[0m"
    BOLD = "\033[1m"


def colored(text: str, color: str) -> str:
    """如果终端支持颜色则着色，否则返回原文"""
    if sys.stdout.isatty():
        return f"{color}{text}{Color.RESET}"
    return text


# ========================================
# 文件匹配
# ========================================
def find_files(patterns: list[str], src_dir: str, exclude: list[str] | None = None) -> list[str]:
    """根据 glob 模式查找文件"""
    matched = set()
    for pattern in patterns:
        full_pattern = os.path.join(src_dir, pattern)
        matched.update(glob.glob(full_pattern, recursive=True))

    if exclude:
        excluded = set()
        for pattern in exclude:
            full_pattern = os.path.join(src_dir, pattern)
            excluded.update(glob.glob(full_pattern, recursive=True))
        matched -= excluded

    return sorted(matched)


def read_file(filepath: str) -> str:
    """读取文件内容，处理编码异常"""
    try:
        with open(filepath, "r", encoding="utf-8", errors="replace") as f:
            return f.read()
    except (OSError, IOError) as e:
        print(f"  [WARN] 无法读取 {filepath}: {e}")
        return ""


# ========================================
# 检查器
# ========================================
class CheckResult:
    def __init__(self, rule_id: str, name: str, passed: bool, message: str, level: str):
        self.rule_id = rule_id
        self.name = name
        self.passed = passed
        self.message = message
        self.level = level  # immutable / critical / need_review


def check_grep_literal(rule: dict, src_dir: str) -> CheckResult:
    """grep_literal: 简单文本匹配"""
    rule_id = rule["id"]
    name = rule.get("name", rule_id)
    pattern = rule["pattern"]
    expected = rule.get("expected", "")
    files = find_files(rule.get("files", ["**/*"]), src_dir)

    found = False
    for filepath in files:
        content = read_file(filepath)
        if pattern in content:
            if expected:
                if expected in content:
                    found = True
                    break
            else:
                found = True
                break

    if found:
        return CheckResult(rule_id, name, True, "匹配成功", rule.get("_level", "immutable"))
    else:
        return CheckResult(rule_id, name, False,
                           f"未找到 '{pattern}'" + (f" 或 '{expected}'" if expected else ""),
                           rule.get("_level", "immutable"))


def check_regex_match(rule: dict, src_dir: str) -> CheckResult:
    """regex_match: 正则表达式匹配"""
    rule_id = rule["id"]
    name = rule.get("name", rule_id)
    pattern = rule["pattern"]
    must_match = rule.get("must_match", True)
    files = find_files(rule.get("files", ["**/*"]), src_dir)

    found = False
    try:
        regex = re.compile(pattern)
    except re.error as e:
        return CheckResult(rule_id, name, False, f"正则表达式错误: {e}",
                           rule.get("_level", "immutable"))

    for filepath in files:
        content = read_file(filepath)
        if regex.search(content):
            found = True
            break

    if must_match:
        passed = found
        msg = "匹配成功" if found else f"未找到匹配 '{pattern}'"
    else:
        passed = not found
        msg = "无禁止模式" if not found else f"发现禁止模式 '{pattern}'"

    return CheckResult(rule_id, name, passed, msg, rule.get("_level", "immutable"))


def check_import_guard(rule: dict, src_dir: str) -> CheckResult:
    """import_guard: ACL 边界守护"""
    rule_id = rule["id"]
    name = rule.get("name", rule_id)
    forbidden = rule.get("forbidden_imports", [])
    allowed_in = rule.get("allowed_in", [])
    files = find_files(rule.get("files", ["**/*"]), src_dir)

    # 排除 allowed_in 的文件
    if allowed_in:
        allowed_files = set()
        for pattern in allowed_in:
            full_pattern = os.path.join(src_dir, pattern)
            allowed_files.update(glob.glob(full_pattern, recursive=True))
        files = [f for f in files if f not in allowed_files]

    violations = []
    for filepath in files:
        content = read_file(filepath)
        for imp in forbidden:
            for line_num, line in enumerate(content.splitlines(), 1):
                if imp in line and not line.strip().startswith("#"):
                    rel_path = os.path.relpath(filepath, src_dir)
                    violations.append(f"  {rel_path}:{line_num}: {line.strip()}")

    if violations:
        detail = "\n".join(violations[:5])  # 最多显示5个
        return CheckResult(rule_id, name, False,
                           f"发现 {len(violations)} 处违规:\n{detail}",
                           rule.get("_level", "critical"))
    else:
        return CheckResult(rule_id, name, True, "ACL边界完整",
                           rule.get("_level", "critical"))


def check_function_body_hash(rule: dict, src_dir: str) -> CheckResult:
    """function_body_hash_match: 函数体 hash 比对"""
    rule_id = rule["id"]
    name = rule.get("name", rule_id)
    baseline_hash = rule.get("baseline_hash", "")
    files = find_files(rule.get("files", ["**/*"]), src_dir)

    # 简化实现: 对整个文件计算 hash
    for filepath in files:
        content = read_file(filepath)
        current_hash = "sha256:" + hashlib.sha256(content.encode()).hexdigest()[:12]

        if baseline_hash and current_hash != baseline_hash:
            return CheckResult(rule_id, name, False,
                               f"hash 已变更 (baseline: {baseline_hash}, current: {current_hash})",
                               "need_review")

    return CheckResult(rule_id, name, True, "未变更", "need_review")


def check_ast_import(rule: dict, src_dir: str) -> CheckResult:
    """ast_import_check: 通过 Python AST 检查实际 import 语句，完全忽略注释和字符串"""
    rule_id = rule["id"]
    name = rule.get("name", rule_id)
    forbidden = rule.get("forbidden_import", "")
    if not forbidden:
        return CheckResult(
            rule_id, name, False,
            "ast_import_check 缺少 forbidden_import 字段（标量字符串）",
            rule.get("_level", "immutable"),
        )

    except_patterns = rule.get("except", [])
    files = find_files(rule.get("files", ["**/*.py"]), src_dir)
    if except_patterns:
        excluded = set()
        for pat in except_patterns:
            excluded.update(glob.glob(os.path.join(src_dir, pat), recursive=True))
        files = [f for f in files if f not in excluded]

    violations = []
    for filepath in files:
        content = read_file(filepath)
        try:
            tree = ast.parse(content, filename=filepath)
        except SyntaxError:
            print(f"  [WARN] 无法解析 {filepath}（语法错误），跳过 AST 检查")
            continue

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    mod = alias.name or ""
                    if mod == forbidden or mod.startswith(forbidden + "."):
                        rel = os.path.relpath(filepath, src_dir)
                        violations.append(f"  {rel}:{node.lineno}: import {mod}")
            elif isinstance(node, ast.ImportFrom):
                mod = node.module or ""
                if mod == forbidden or mod.startswith(forbidden + "."):
                    rel = os.path.relpath(filepath, src_dir)
                    violations.append(f"  {rel}:{node.lineno}: from {mod} import ...")

    if violations:
        detail = "\n".join(violations[:5])
        return CheckResult(
            rule_id, name, False,
            f"发现 {len(violations)} 处违规 import:\n{detail}",
            rule.get("_level", "immutable"),
        )
    return CheckResult(rule_id, name, True, "AST 级别无违规 import",
                       rule.get("_level", "immutable"))


def _get_call_name(node: ast.Call) -> str | None:
    """从 AST Call 节点提取调用名称，支持 obj.method 形式"""
    if isinstance(node.func, ast.Name):
        return node.func.id
    if isinstance(node.func, ast.Attribute):
        parts: list[str] = []
        cur: ast.expr = node.func
        while isinstance(cur, ast.Attribute):
            parts.append(cur.attr)
            cur = cur.value
        if isinstance(cur, ast.Name):
            parts.append(cur.id)
            return ".".join(reversed(parts))
    return None


def _get_nested_value(data: object, dot_path: str) -> object:
    """按 dot-notation 路径 (a.b.c) 访问嵌套字典，路径不存在返回 None"""
    keys = dot_path.split(".")
    current = data
    for key in keys:
        if not isinstance(current, dict) or key not in current:
            return None
        current = current[key]
    return current


def check_ast_function_call(rule: dict, src_dir: str) -> CheckResult:
    """ast_function_call: 通过 Python AST 检查函数调用是否存在或缺失"""
    rule_id = rule["id"]
    name = rule.get("name", rule_id)
    function_name = rule.get("function_name", "")
    if not function_name:
        return CheckResult(
            rule_id, name, False,
            "ast_function_call 缺少 function_name 字段",
            rule.get("_level", "critical"),
        )
    must_call = rule.get("must_call", True)  # True=必须存在，False=禁止调用
    files = find_files(rule.get("files", ["**/*.py"]), src_dir)

    found: list[str] = []
    for filepath in files:
        content = read_file(filepath)
        try:
            tree = ast.parse(content, filename=filepath)
        except SyntaxError:
            print(f"  [WARN] 无法解析 {filepath}（语法错误），跳过 AST 检查")
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                call_name = _get_call_name(node)
                if call_name and (
                    call_name == function_name or call_name.endswith("." + function_name)
                ):
                    rel = os.path.relpath(filepath, src_dir)
                    found.append(f"  {rel}:{node.lineno}: {call_name}(...)")

    if must_call:
        passed = len(found) > 0
        msg = f"找到 {len(found)} 处调用" if passed else f"未找到函数调用 '{function_name}'"
    else:
        passed = len(found) == 0
        if passed:
            msg = f"无禁止调用 '{function_name}'"
        else:
            detail = "\n".join(found[:5])
            msg = f"发现 {len(found)} 处禁止调用:\n{detail}"

    return CheckResult(rule_id, name, passed, msg, rule.get("_level", "critical"))


def check_schema_match(rule: dict, src_dir: str) -> CheckResult:
    """schema_match: 检查 YAML/JSON 文件是否包含所有必需字段（dot-notation 路径）"""
    rule_id = rule["id"]
    name = rule.get("name", rule_id)
    required_keys: list[str] = rule.get("required_keys", [])
    if not required_keys:
        return CheckResult(
            rule_id, name, False,
            "schema_match 缺少 required_keys 字段（字符串列表）",
            rule.get("_level", "critical"),
        )
    files = find_files(rule.get("files", ["**/*.yaml", "**/*.json"]), src_dir)

    violations: list[str] = []
    for filepath in files:
        content = read_file(filepath)
        if not content.strip():
            continue
        try:
            if filepath.endswith(".json"):
                data: object = json.loads(content)
            else:
                data = yaml.safe_load(content)
        except (yaml.YAMLError, json.JSONDecodeError) as exc:
            rel = os.path.relpath(filepath, src_dir)
            violations.append(f"  {rel}: 解析失败 ({exc})")
            continue

        for key_path in required_keys:
            if _get_nested_value(data, key_path) is None:
                rel = os.path.relpath(filepath, src_dir)
                violations.append(f"  {rel}: 缺少字段 '{key_path}'")

    if violations:
        detail = "\n".join(violations[:5])
        return CheckResult(
            rule_id, name, False,
            f"schema 不匹配:\n{detail}",
            rule.get("_level", "critical"),
        )
    return CheckResult(rule_id, name, True, "schema 匹配", rule.get("_level", "critical"))


# 检查器映射表
CHECKERS = {
    "grep_literal": check_grep_literal,
    "regex_match": check_regex_match,
    "import_guard": check_import_guard,
    "function_body_hash_match": check_function_body_hash,
    "ast_import_check": check_ast_import,
    "ast_function_call": check_ast_function_call,
    "schema_match": check_schema_match,
}


# ========================================
# 公开 API — 可被外部 import 调用
# ========================================


@dataclass
class ViolationItem:
    id: str
    severity: str   # "immutable" / "critical" / "need_review"
    message: str


@dataclass
class Violations:
    items: list[ViolationItem] = _field(default_factory=list)

    def has_immutable(self) -> bool:
        return any(v.severity == "immutable" for v in self.items)

    def has_critical(self) -> bool:
        return any(v.severity == "critical" for v in self.items)

    def has_need_review(self) -> bool:
        return any(v.severity == "need_review" for v in self.items)

    def summary(self) -> str:
        return "\n".join(
            f"[{v.severity.upper()}] {v.id}: {v.message}" for v in self.items
        )


def run_check(
    contracts_path: Path,
    src_paths: list[Path],
    module: str | None = None,
) -> Violations:
    """
    Core check logic — importable by other tools.

    Loads contracts_path, runs all applicable rules against src_paths,
    optionally filtered to rules matching the given module name.
    Returns a Violations object (never raises).
    """
    try:
        with open(contracts_path, "r", encoding="utf-8") as f:
            contracts = yaml.safe_load(f)
        if not isinstance(contracts, dict):
            return Violations()
    except (OSError, yaml.YAMLError):
        return Violations()

    violations = Violations()
    level_map = {
        "immutable": ("immutable", "immutable"),
        "critical": ("critical_rules", "critical"),
        "need_review": ("need_review", "need_review"),
    }

    for _level_name, (yaml_key, result_level) in level_map.items():
        rules = contracts.get(yaml_key, []) or []
        for rule in rules:
            rule_id = rule.get("id", "UNKNOWN")

            # Module filter: skip if rule has a module field that doesn't match
            rule_module = rule.get("module")
            if module is not None and rule_module is not None and rule_module != module:
                continue

            check_type = rule.get("type", "grep_literal")
            rule = {**rule, "_level": result_level}
            checker = CHECKERS.get(check_type, check_grep_literal)

            # Run check against each src_path
            for src_path in src_paths:
                src_dir = str(src_path)
                result = checker(rule, src_dir)
                if not result.passed:
                    violations.items.append(
                        ViolationItem(
                            id=rule_id,
                            severity=result_level,
                            message=result.message,
                        )
                    )
                    break  # one failure per rule is enough

    return violations


# ========================================
# 主流程
# ========================================
def load_contracts(filepath: str) -> dict:
    """加载 contracts.yaml"""
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        if not isinstance(data, dict):
            print(f"[ERROR] {filepath} 格式错误: 期望顶层为字典")
            sys.exit(4)
        return data
    except yaml.YAMLError as e:
        print(f"[ERROR] {filepath} YAML解析错误: {e}")
        sys.exit(4)
    except FileNotFoundError:
        print(f"[ERROR] 文件不存在: {filepath}")
        sys.exit(4)


def run_checks(contracts: dict, src_dir: str,
               level_filter: set | None = None,
               id_filter: str | None = None) -> list[CheckResult]:
    """执行所有检查"""
    results = []

    # 定义级别和对应的 contracts.yaml 节
    level_map = {
        "immutable": ("immutable", "immutable"),
        "critical": ("critical_rules", "critical"),
        "need_review": ("need_review", "need_review"),
    }

    for level_name, (yaml_key, result_level) in level_map.items():
        if level_filter and level_name not in level_filter:
            continue

        rules = contracts.get(yaml_key, [])
        if not rules:
            continue

        for rule in rules:
            rule_id = rule.get("id", "UNKNOWN")

            if id_filter and rule_id != id_filter:
                continue

            check_type = rule.get("type", "grep_literal")
            rule["_level"] = result_level

            checker = CHECKERS.get(check_type)
            if checker:
                result = checker(rule, src_dir)
                results.append(result)
            else:
                # 未知检查类型，回退为 grep_literal
                print(f"  [WARN] 未知检查类型 '{check_type}'，回退为 grep_literal")
                result = check_grep_literal(rule, src_dir)
                results.append(result)

    return results


def print_results(results: list[CheckResult]) -> int:
    """打印结果并返回退出码"""
    pass_count = 0
    fail_count = 0
    warn_count = 0
    max_exit_code = 0

    print()
    print(colored("=" * 60, Color.BOLD))
    print(colored("  PDAE Contract Check Results", Color.BOLD))
    print(colored("=" * 60, Color.BOLD))
    print()

    for r in results:
        if r.passed:
            if r.level == "need_review":
                status = colored("[PASS]", Color.PASS)
            else:
                status = colored("[PASS]", Color.PASS)
            print(f"  {status} {r.rule_id}: {r.name} ✅")
            pass_count += 1
        else:
            if r.level == "need_review":
                status = colored("[WARN]", Color.WARN)
                print(f"  {status} {r.rule_id}: {r.name} ⚠️")
                print(f"         {r.message}")
                warn_count += 1
                max_exit_code = max(max_exit_code, 3)
            elif r.level == "critical":
                status = colored("[FAIL]", Color.FAIL)
                print(f"  {status} {r.rule_id}: {r.name} ❌")
                print(f"         {r.message}")
                fail_count += 1
                max_exit_code = max(max_exit_code, 2)
            else:  # immutable
                status = colored("[FAIL]", Color.FAIL)
                print(f"  {status} {r.rule_id}: {r.name} ❌")
                print(f"         {r.message}")
                fail_count += 1
                max_exit_code = max(max_exit_code, 1)

    print()
    print(colored("-" * 60, Color.BOLD))
    summary = f"  Result: {pass_count} PASS, {fail_count} FAIL, {warn_count} WARN"
    if fail_count > 0:
        print(colored(summary, Color.FAIL))
    elif warn_count > 0:
        print(colored(summary, Color.WARN))
    else:
        print(colored(summary, Color.PASS))

    if max_exit_code > 0:
        print(f"  Exit code: {max_exit_code}")
    print()

    return max_exit_code


def main():
    parser = argparse.ArgumentParser(
        description="PDAE v5.8.0 contract checker",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
退出码:
  0 = 所有检查通过
  1 = IMMUTABLE 违规 (阻塞合并)
  2 = CRITICAL 违规 (阻塞合并)
  3 = NEED_REVIEW 变更 (不阻塞)
  4 = contracts.yaml 格式错误
        """
    )
    parser.add_argument("--contracts", "-c", required=True,
                        help="Path to the contracts.yaml file")
    parser.add_argument("--src", "-s", required=True,
                        help="Source code directory")
    parser.add_argument("--level", "-l", default=None,
                        help="Check levels (comma-separated): immutable,critical,need_review")
    parser.add_argument("--id", default=None,
                        help="Check only a specific rule ID")

    args = parser.parse_args()

    # 解析级别过滤
    level_filter = None
    if args.level:
        level_filter = set(args.level.split(","))

    # 检查源目录
    if not os.path.isdir(args.src):
        print(f"[ERROR] 源目录不存在: {args.src}")
        sys.exit(4)

    # 加载 contracts
    contracts = load_contracts(args.contracts)

    print(f"  Source: {contracts.get('source', 'unknown')}")
    print(f"  Generated: {contracts.get('generated_at', 'unknown')}")
    print(f"  Src dir: {args.src}")

    # 执行检查
    results = run_checks(contracts, args.src, level_filter, args.id)

    if not results:
        print("\n  [INFO] 没有匹配的检查规则")
        sys.exit(0)

    # 打印结果
    exit_code = print_results(results)
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
