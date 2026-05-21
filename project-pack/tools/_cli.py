"""Shared CLI wrapper helpers for PRAE tools."""
from __future__ import annotations

from collections.abc import Callable
from typing import TypeVar

from _output import error, result

Payload = TypeVar("Payload", bound=dict)


def emit_payload(payload: dict) -> None:
    result(
        payload["passed"],
        payload["checks"],
        payload["summary"],
        data=payload.get("data"),
    )


def run_action(action: Callable[[], Payload], *error_types: type[BaseException]) -> None:
    try:
        payload = action()
    except error_types as exc:
        error(str(exc))
    emit_payload(payload)
