"""Shared output module: unifies CLI output format and exit codes."""
from __future__ import annotations
import json
import sys
from typing import Any

EXIT_PASS = 0
EXIT_FAIL = 1
EXIT_ERROR = 2


def result(passed: bool, checks: list[dict], summary: str, data: dict | None = None) -> None:
    """Output the JSON result to stdout; exit code 0=passed, 1=failed."""
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
    """Output an error message (file missing / format error); exit code 2."""
    payload: dict[str, Any] = {
        "passed": False,
        "error": message,
    }
    if data:
        payload["data"] = data
    print(json.dumps(payload, ensure_ascii=False, indent=2), file=sys.stderr)
    sys.exit(EXIT_ERROR)


def check_item(name: str, passed: bool, detail: str = "") -> dict:
    """Create a check-item dictionary."""
    item: dict[str, Any] = {"name": name, "passed": passed}
    if detail:
        item["detail"] = detail
    return item
