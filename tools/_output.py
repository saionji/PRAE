"""共用输出模块：统一 CLI 输出格式和退出码。"""
from __future__ import annotations
import json
import sys
from typing import Any

EXIT_PASS = 0
EXIT_FAIL = 1
EXIT_ERROR = 2


def result(passed: bool, checks: list[dict], summary: str, data: dict | None = None) -> None:
    """输出 JSON 结果到 stdout，退出码 0=通过 1=不通过。"""
    payload: dict[str, Any] = {
        "passed": passed,
        "summary": summary,
        "checks": checks,
    }
    if data:
        payload["data"] = data
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    sys.exit(EXIT_PASS if passed else EXIT_FAIL)


def error(message: str, data: dict | None = None) -> None:
    """输出错误信息（文件缺失/格式错误），退出码 2。"""
    payload: dict[str, Any] = {
        "passed": False,
        "error": message,
    }
    if data:
        payload["data"] = data
    print(json.dumps(payload, ensure_ascii=False, indent=2), file=sys.stderr)
    sys.exit(EXIT_ERROR)


def check_item(name: str, passed: bool, detail: str = "") -> dict:
    """创建一个检查项字典。"""
    item: dict[str, Any] = {"name": name, "passed": passed}
    if detail:
        item["detail"] = detail
    return item
