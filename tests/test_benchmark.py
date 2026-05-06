from multi_agent_research_lab.cli import _run_multi_query
from multi_agent_research_lab.evaluation.benchmark import run_benchmark


def test_benchmark_returns_quality_and_coverage() -> None:
    _, metrics = run_benchmark(
        run_name="multi-agent",
        query="Summarize production guardrails for LLM agents",
        runner=_run_multi_query,
    )
    assert metrics.quality_score is not None
    assert metrics.citation_coverage is not None
    assert metrics.failure_rate == 0.0
