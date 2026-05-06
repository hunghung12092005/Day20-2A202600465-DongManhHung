"""Command-line entrypoint for the lab starter."""

import json
from pathlib import Path
from typing import Annotated

import typer
import yaml
from rich.console import Console
from rich.panel import Panel

from multi_agent_research_lab.core.config import get_settings
from multi_agent_research_lab.core.schemas import AgentName, AgentResult
from multi_agent_research_lab.core.schemas import ResearchQuery
from multi_agent_research_lab.core.state import ResearchState
from multi_agent_research_lab.evaluation.benchmark import run_benchmark
from multi_agent_research_lab.evaluation.report import render_markdown_report
from multi_agent_research_lab.graph.workflow import MultiAgentWorkflow
from multi_agent_research_lab.observability.logging import configure_logging
from multi_agent_research_lab.services.llm_client import LLMClient
from multi_agent_research_lab.services.storage import LocalArtifactStore

app = typer.Typer(help="Multi-Agent Research Lab starter CLI")
console = Console()


def _init() -> None:
    settings = get_settings()
    configure_logging(settings.log_level)


@app.command()
def baseline(
    query: Annotated[str, typer.Option("--query", "-q", help="Research query")],
) -> None:
    """Run a single-agent baseline."""

    _init()
    request = ResearchQuery(query=query)
    state = ResearchState(request=request)
    response = LLMClient().complete(
        system_prompt=(
            "You are a single-agent research assistant. Answer clearly, identify trade-offs, "
            "and give a concise summary for technical learners."
        ),
        user_prompt=query,
    )
    state.final_answer = response.content
    state.agent_results.append(
        AgentResult(
            agent=AgentName.WRITER,
            content=response.content,
            metadata={
                "input_tokens": response.input_tokens,
                "output_tokens": response.output_tokens,
                "cost_usd": response.cost_usd,
            },
        )
    )
    console.print(Panel.fit(state.final_answer, title="Single-Agent Baseline"))


@app.command("multi-agent")
def multi_agent(
    query: Annotated[str, typer.Option("--query", "-q", help="Research query")],
) -> None:
    """Run the multi-agent workflow."""

    _init()
    state = ResearchState(request=ResearchQuery(query=query))
    workflow = MultiAgentWorkflow()
    result = workflow.run(state)
    store = LocalArtifactStore()
    trace_path = store.write_text("traces/latest_trace.json", json.dumps(result.trace, indent=2))
    console.print(Panel.fit(f"Trace saved to {trace_path}", title="Trace"))
    console.print(result.model_dump_json(indent=2))


@app.command()
def benchmark(
    config_path: Annotated[
        str,
        typer.Option("--config", "-c", help="Path to benchmark config YAML"),
    ] = "configs/lab_default.yaml",
) -> None:
    """Run benchmark queries for baseline and multi-agent workflows and save a report."""

    _init()
    config = _load_yaml_config(Path(config_path))
    queries = config.get("benchmark", {}).get("queries", [])
    store = LocalArtifactStore()
    metrics = []
    for query in queries:
        baseline_state, baseline_metrics = run_benchmark(
            run_name="baseline",
            query=query,
            runner=_run_baseline_query,
        )
        multi_state, multi_metrics = run_benchmark(
            run_name="multi-agent",
            query=query,
            runner=_run_multi_query,
        )
        metrics.extend([baseline_metrics, multi_metrics])
        slug = _slugify(query)
        store.write_text(f"traces/{slug}_baseline.json", json.dumps(baseline_state.trace, indent=2))
        store.write_text(f"traces/{slug}_multi_agent.json", json.dumps(multi_state.trace, indent=2))
    report = render_markdown_report(metrics)
    report_path = store.write_text("benchmark_report.md", report)
    console.print(Panel.fit(str(report_path), title="Benchmark Report"))


def _run_baseline_query(query: str) -> ResearchState:
    state = ResearchState(request=ResearchQuery(query=query))
    response = LLMClient().complete(
        system_prompt=(
            "You are a single-agent research assistant. Answer clearly, identify trade-offs, "
            "and provide a concise synthesis."
        ),
        user_prompt=query,
    )
    state.final_answer = response.content
    state.add_trace_event(
        "baseline.completed",
        {
            "name": "baseline",
            "payload": {
                "input_tokens": response.input_tokens,
                "output_tokens": response.output_tokens,
                "cost_usd": response.cost_usd,
            },
        },
    )
    return state


def _run_multi_query(query: str) -> ResearchState:
    state = ResearchState(request=ResearchQuery(query=query))
    return MultiAgentWorkflow().run(state)


def _load_yaml_config(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def _slugify(value: str) -> str:
    return "".join(character.lower() if character.isalnum() else "_" for character in value).strip("_")


if __name__ == "__main__":
    app()
