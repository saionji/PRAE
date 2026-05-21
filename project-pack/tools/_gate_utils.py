"""Shared helpers for PRAE gate evaluators."""
from __future__ import annotations


def collapse_text(text: str, limit: int = 160) -> str:
    compact = " ".join(text.split())
    return compact if len(compact) <= limit else compact[: limit - 3] + "..."


def summarize_violations(prefix: str, violations, limit: int = 3) -> str:
    items = [f"{item.severity}:{item.id}" for item in violations.items[:limit]]
    suffix = "..." if len(violations.items) > limit else ""
    return f"{prefix}: {'; '.join(items)}{suffix}"


def gate_payload(summary_prefix: str, checks: list[dict], *, data: dict | None = None) -> dict:
    passed = all(item["passed"] for item in checks)
    failed_count = sum(1 for item in checks if not item["passed"])
    return {
        "passed": passed,
        "checks": checks,
        "summary": f"{summary_prefix}: {'通过' if passed else f'失败 ({failed_count} 项)'}",
        "data": data or {},
    }
