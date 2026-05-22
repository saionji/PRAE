#!/usr/bin/env python3
# SOURCE: PDAE ${PDAE_HOME}/tools/check_contracts.py (v5.8.0, 2026-04-19)
# Do not modify; re-copy from PDAE to update.
"""
check_contracts.py — PDAE v5.8.0 contract checker

Reads constraint rules from contracts.yaml and runs deterministic checks
against the code. Non-AI checking AI — guard constraints with a
deterministic script.

Exit codes:
  0 = all checks passed
  1 = IMMUTABLE violation (blocks merge)
  2 = CRITICAL violation (blocks merge)
  3 = NEED_REVIEW change (does not block, needs focused review)
  4 = contracts.yaml format error

Usage:
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
    print("[ERROR] pyyaml is not installed. Please run: pip install pyyaml")
    sys.exit(4)


# ========================================
# ANSI colors
# ========================================
class Color:
    PASS = "\033[92m"   # green
    FAIL = "\033[91m"   # red
    WARN = "\033[93m"   # yellow
    RESET = "\033[0m"
    BOLD = "\033[1m"


def colored(text: str, color: str) -> str:
    """Colorize if the terminal supports color, otherwise return the original text"""
    if sys.stdout.isatty():
        return f"{color}{text}{Color.RESET}"
    return text


# ========================================
# File matching
# ========================================
def find_files(patterns: list[str], src_dir: str, exclude: list[str] | None = None) -> list[str]:
    """Find files by glob pattern"""
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
    """Read file content, handling encoding errors"""
    try:
        with open(filepath, "r", encoding="utf-8", errors="replace") as f:
            return f.read()
    except (OSError, IOError) as e:
        print(f"  [WARN] Unable to read {filepath}: {e}")
        return ""


# ========================================
# Checkers
# ========================================
class CheckResult:
    def __init__(self, rule_id: str, name: str, passed: bool, message: str, level: str):
        self.rule_id = rule_id
        self.name = name
        self.passed = passed
        self.message = message
        self.level = level  # immutable / critical / need_review


def check_grep_literal(rule: dict, src_dir: str) -> CheckResult:
    """grep_literal: simple text matching"""
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
        return CheckResult(rule_id, name, True, "match found", rule.get("_level", "immutable"))
    else:
        return CheckResult(rule_id, name, False,
                           f"'{pattern}' not found" + (f" or '{expected}'" if expected else ""),
                           rule.get("_level", "immutable"))


def check_regex_match(rule: dict, src_dir: str) -> CheckResult:
    """regex_match: regular expression matching"""
    rule_id = rule["id"]
    name = rule.get("name", rule_id)
    pattern = rule["pattern"]
    must_match = rule.get("must_match", True)
    files = find_files(rule.get("files", ["**/*"]), src_dir)

    found = False
    try:
        regex = re.compile(pattern)
    except re.error as e:
        return CheckResult(rule_id, name, False, f"regular expression error: {e}",
                           rule.get("_level", "immutable"))

    for filepath in files:
        content = read_file(filepath)
        if regex.search(content):
            found = True
            break

    if must_match:
        passed = found
        msg = "match found" if found else f"no match found for '{pattern}'"
    else:
        passed = not found
        msg = "no forbidden pattern" if not found else f"forbidden pattern found '{pattern}'"

    return CheckResult(rule_id, name, passed, msg, rule.get("_level", "immutable"))


def check_import_guard(rule: dict, src_dir: str) -> CheckResult:
    """import_guard: ACL boundary guard"""
    rule_id = rule["id"]
    name = rule.get("name", rule_id)
    forbidden = rule.get("forbidden_imports", [])
    allowed_in = rule.get("allowed_in", [])
    files = find_files(rule.get("files", ["**/*"]), src_dir)

    # Exclude files listed in allowed_in
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
        detail = "\n".join(violations[:5])  # show at most 5
        return CheckResult(rule_id, name, False,
                           f"found {len(violations)} violations:\n{detail}",
                           rule.get("_level", "critical"))
    else:
        return CheckResult(rule_id, name, True, "ACL boundary intact",
                           rule.get("_level", "critical"))


def check_function_body_hash(rule: dict, src_dir: str) -> CheckResult:
    """function_body_hash_match: function body hash comparison"""
    rule_id = rule["id"]
    name = rule.get("name", rule_id)
    baseline_hash = rule.get("baseline_hash", "")
    files = find_files(rule.get("files", ["**/*"]), src_dir)

    # Simplified implementation: compute hash over the whole file
    for filepath in files:
        content = read_file(filepath)
        current_hash = "sha256:" + hashlib.sha256(content.encode()).hexdigest()[:12]

        if baseline_hash and current_hash != baseline_hash:
            return CheckResult(rule_id, name, False,
                               f"hash changed (baseline: {baseline_hash}, current: {current_hash})",
                               "need_review")

    return CheckResult(rule_id, name, True, "unchanged", "need_review")


def check_ast_import(rule: dict, src_dir: str) -> CheckResult:
    """ast_import_check: check actual import statements via Python AST, fully ignoring comments and strings"""
    rule_id = rule["id"]
    name = rule.get("name", rule_id)
    forbidden = rule.get("forbidden_import", "")
    if not forbidden:
        return CheckResult(
            rule_id, name, False,
            "ast_import_check is missing the forbidden_import field (scalar string)",
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
            print(f"  [WARN] Unable to parse {filepath} (syntax error), skipping AST check")
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
            f"found {len(violations)} violating imports:\n{detail}",
            rule.get("_level", "immutable"),
        )
    return CheckResult(rule_id, name, True, "no violating imports at AST level",
                       rule.get("_level", "immutable"))


def _get_call_name(node: ast.Call) -> str | None:
    """Extract the call name from an AST Call node, supporting the obj.method form"""
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
    """Access a nested dict by a dot-notation path (a.b.c); return None if the path does not exist"""
    keys = dot_path.split(".")
    current = data
    for key in keys:
        if not isinstance(current, dict) or key not in current:
            return None
        current = current[key]
    return current


def check_ast_function_call(rule: dict, src_dir: str) -> CheckResult:
    """ast_function_call: check whether a function call is present or missing via Python AST"""
    rule_id = rule["id"]
    name = rule.get("name", rule_id)
    function_name = rule.get("function_name", "")
    if not function_name:
        return CheckResult(
            rule_id, name, False,
            "ast_function_call is missing the function_name field",
            rule.get("_level", "critical"),
        )
    must_call = rule.get("must_call", True)  # True=must exist, False=call forbidden
    files = find_files(rule.get("files", ["**/*.py"]), src_dir)

    found: list[str] = []
    for filepath in files:
        content = read_file(filepath)
        try:
            tree = ast.parse(content, filename=filepath)
        except SyntaxError:
            print(f"  [WARN] Unable to parse {filepath} (syntax error), skipping AST check")
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
        msg = f"found {len(found)} calls" if passed else f"function call '{function_name}' not found"
    else:
        passed = len(found) == 0
        if passed:
            msg = f"no forbidden call '{function_name}'"
        else:
            detail = "\n".join(found[:5])
            msg = f"found {len(found)} forbidden calls:\n{detail}"

    return CheckResult(rule_id, name, passed, msg, rule.get("_level", "critical"))


def check_schema_match(rule: dict, src_dir: str) -> CheckResult:
    """schema_match: check whether a YAML/JSON file contains all required fields (dot-notation paths)"""
    rule_id = rule["id"]
    name = rule.get("name", rule_id)
    required_keys: list[str] = rule.get("required_keys", [])
    if not required_keys:
        return CheckResult(
            rule_id, name, False,
            "schema_match is missing the required_keys field (list of strings)",
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
            violations.append(f"  {rel}: parse failed ({exc})")
            continue

        for key_path in required_keys:
            if _get_nested_value(data, key_path) is None:
                rel = os.path.relpath(filepath, src_dir)
                violations.append(f"  {rel}: missing field '{key_path}'")

    if violations:
        detail = "\n".join(violations[:5])
        return CheckResult(
            rule_id, name, False,
            f"schema mismatch:\n{detail}",
            rule.get("_level", "critical"),
        )
    return CheckResult(rule_id, name, True, "schema matches", rule.get("_level", "critical"))


# Checker mapping table
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
# Public API — importable by external callers
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
# Main flow
# ========================================
def load_contracts(filepath: str) -> dict:
    """Load contracts.yaml"""
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        if not isinstance(data, dict):
            print(f"[ERROR] {filepath} format error: expected top level to be a dict")
            sys.exit(4)
        return data
    except yaml.YAMLError as e:
        print(f"[ERROR] {filepath} YAML parse error: {e}")
        sys.exit(4)
    except FileNotFoundError:
        print(f"[ERROR] file does not exist: {filepath}")
        sys.exit(4)


def run_checks(contracts: dict, src_dir: str,
               level_filter: set | None = None,
               id_filter: str | None = None) -> list[CheckResult]:
    """Run all checks"""
    results = []

    # Define levels and their corresponding contracts.yaml sections
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
                # Unknown check type, fall back to grep_literal
                print(f"  [WARN] unknown check type '{check_type}', falling back to grep_literal")
                result = check_grep_literal(rule, src_dir)
                results.append(result)

    return results


def print_results(results: list[CheckResult]) -> int:
    """Print results and return the exit code"""
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
Exit codes:
  0 = all checks passed
  1 = IMMUTABLE violation (blocks merge)
  2 = CRITICAL violation (blocks merge)
  3 = NEED_REVIEW change (does not block)
  4 = contracts.yaml format error
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

    # Parse level filter
    level_filter = None
    if args.level:
        level_filter = set(args.level.split(","))

    # Check source directory
    if not os.path.isdir(args.src):
        print(f"[ERROR] source directory does not exist: {args.src}")
        sys.exit(4)

    # Load contracts
    contracts = load_contracts(args.contracts)

    print(f"  Source: {contracts.get('source', 'unknown')}")
    print(f"  Generated: {contracts.get('generated_at', 'unknown')}")
    print(f"  Src dir: {args.src}")

    # Run checks
    results = run_checks(contracts, args.src, level_filter, args.id)

    if not results:
        print("\n  [INFO] no matching check rules")
        sys.exit(0)

    # Print results
    exit_code = print_results(results)
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
