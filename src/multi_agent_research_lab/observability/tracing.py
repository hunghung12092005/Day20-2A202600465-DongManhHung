"""Tracing hooks with optional LangSmith integration."""

import os
from collections.abc import Iterator
from contextlib import ExitStack, contextmanager
from time import perf_counter
from typing import Any

import langsmith as ls

from multi_agent_research_lab.core.config import Settings, get_settings


def configure_langsmith(settings: Settings | None = None) -> bool:
    """Enable LangSmith tracing from app settings when an API key is configured."""

    active_settings = settings or get_settings()
    if not active_settings.langsmith_api_key:
        return False
    os.environ["LANGSMITH_TRACING"] = "true"
    os.environ["LANGSMITH_API_KEY"] = active_settings.langsmith_api_key
    os.environ["LANGSMITH_PROJECT"] = active_settings.langsmith_project
    return True


def is_langsmith_enabled(settings: Settings | None = None) -> bool:
    """Return True when LangSmith tracing is configured for the current process."""

    active_settings = settings or get_settings()
    if active_settings.langsmith_api_key:
        return True
    return os.environ.get("LANGSMITH_TRACING", "").lower() == "true"


@contextmanager
def trace_span(
    name: str,
    attributes: dict[str, Any] | None = None,
    *,
    run_type: str = "tool",
) -> Iterator[dict[str, Any]]:
    """Emit a local timing span and, when enabled, a LangSmith nested run."""

    started = perf_counter()
    span: dict[str, Any] = {"name": name, "attributes": attributes or {}, "duration_seconds": None}
    with ExitStack() as stack:
        langsmith_run = None
        if is_langsmith_enabled():
            configure_langsmith()
            langsmith_run = stack.enter_context(
                ls.trace(
                    name=name,
                    run_type=run_type,
                    inputs=span["attributes"],
                    project_name=get_settings().langsmith_project,
                )
            )
        try:
            yield span
            if langsmith_run is not None:
                langsmith_run.end(outputs={"attributes": span["attributes"]})
        finally:
            span["duration_seconds"] = perf_counter() - started
