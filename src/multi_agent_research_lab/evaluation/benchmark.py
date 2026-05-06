"""Benchmark skeleton for single-agent vs multi-agent."""

from time import perf_counter
from typing import Callable

from multi_agent_research_lab.core.schemas import BenchmarkMetrics
from multi_agent_research_lab.core.state import ResearchState


Runner = Callable[[str], ResearchState]


def run_benchmark(run_name: str, query: str, runner: Runner) -> tuple[ResearchState, BenchmarkMetrics]:
    """Measure latency and return benchmark metrics for one runner/query pair."""

    started = perf_counter()
    state = runner(query)
    latency = perf_counter() - started
    total_cost = sum(
        float(result.metadata.get("cost_usd", 0.0) or 0.0)
        for result in state.agent_results
    )
    citation_count = 0
    if state.final_answer:
        citation_count = sum(
            1 for marker in [f"[{index}]" for index in range(1, len(state.sources) + 1)] if marker in state.final_answer
        )
    citation_coverage = min(1.0, citation_count / max(1, len(state.sources)))
    quality_score = _estimate_quality_score(state, citation_coverage)
    failure_rate = 0.0 if state.final_answer and not state.errors else 1.0
    metrics = BenchmarkMetrics(
        run_name=run_name,
        latency_seconds=latency,
        estimated_cost_usd=round(total_cost, 6),
        quality_score=quality_score,
        citation_coverage=citation_coverage,
        failure_rate=failure_rate,
        notes=f"routes={','.join(state.route_history)} errors={len(state.errors)}",
    )
    return state, metrics


def _estimate_quality_score(state: ResearchState, citation_coverage: float) -> float:
    score = 4.0
    if state.research_notes:
        score += 1.5
    if state.analysis_notes:
        score += 2.0
    if state.final_answer:
        score += 1.5
    score += min(1.0, citation_coverage) * 1.0
    if state.errors:
        score -= min(2.0, float(len(state.errors)) * 0.5)
    if "analyst" in state.route_history and "writer" in state.route_history:
        score += 0.5
    return round(max(0.0, min(10.0, score)), 2)
