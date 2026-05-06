"""Benchmark report rendering."""

from multi_agent_research_lab.core.schemas import BenchmarkMetrics


def render_markdown_report(metrics: list[BenchmarkMetrics]) -> str:
    """Render benchmark metrics to markdown."""

    lines = [
        "# Benchmark Report",
        "",
        "| Run | Latency (s) | Cost (USD) | Quality | Citation Coverage | Failure Rate | Notes |",
        "|---|---:|---:|---:|---:|---:|---|",
    ]
    for item in metrics:
        cost = "" if item.estimated_cost_usd is None else f"{item.estimated_cost_usd:.4f}"
        quality = "" if item.quality_score is None else f"{item.quality_score:.1f}"
        citation_coverage = "" if item.citation_coverage is None else f"{item.citation_coverage:.0%}"
        failure_rate = "" if item.failure_rate is None else f"{item.failure_rate:.0%}"
        lines.append(
            f"| {item.run_name} | {item.latency_seconds:.2f} | {cost} | {quality} | "
            f"{citation_coverage} | {failure_rate} | {item.notes} |"
        )
    if metrics:
        best_quality = max(metrics, key=lambda item: item.quality_score or 0.0)
        fastest = min(metrics, key=lambda item: item.latency_seconds)
        lines.extend(
            [
                "",
                "## Summary",
                "",
                f"- Highest quality run: `{best_quality.run_name}` ({best_quality.quality_score or 0:.1f}/10)",
                f"- Fastest run: `{fastest.run_name}` ({fastest.latency_seconds:.2f}s)",
                "- Review the trace exports in `reports/traces/` alongside this report for step-level details.",
            ]
        )
    return "\n".join(lines) + "\n"
