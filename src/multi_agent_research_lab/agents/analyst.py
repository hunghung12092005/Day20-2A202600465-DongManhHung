"""Analyst agent skeleton."""

from multi_agent_research_lab.agents.base import BaseAgent
from multi_agent_research_lab.core.errors import ValidationError
from multi_agent_research_lab.core.schemas import AgentName, AgentResult
from multi_agent_research_lab.core.state import ResearchState
from multi_agent_research_lab.observability.tracing import trace_span
from multi_agent_research_lab.services.llm_client import LLMClient


class AnalystAgent(BaseAgent):
    """Turns research notes into structured insights."""

    name = "analyst"

    def __init__(self, llm_client: LLMClient | None = None) -> None:
        self.llm_client = llm_client or LLMClient()

    def run(self, state: ResearchState) -> ResearchState:
        """Populate `state.analysis_notes`."""

        if not state.research_notes:
            raise ValidationError("AnalystAgent requires research_notes before analysis.")

        with trace_span("analyst", {"query": state.request.query}, run_type="chain") as span:
            response = self.llm_client.complete(
                system_prompt=(
                    "You are an analyst agent. Extract key claims, compare trade-offs, identify "
                    "weak evidence, and recommend how the final answer should be framed."
                ),
                user_prompt=state.research_notes,
            )
            coverage_flags = [
                f"- Source {index}: {source.title} supports the topic via {source.snippet}"
                for index, source in enumerate(state.sources, start=1)
            ]
            analysis = "\n".join(
                [
                    "Analysis Notes",
                    "",
                    "Key Takeaways:",
                    response.content,
                    "",
                    "Evidence Check:",
                    "\n".join(coverage_flags),
                    "",
                    "Risks:",
                    "- Multi-agent workflows improve decomposition but may increase latency.",
                    "- Weak or missing citations should be called out explicitly.",
                ]
            )
            state.analysis_notes = analysis
            state.agent_results.append(
                AgentResult(
                    agent=AgentName.ANALYST,
                    content=analysis,
                    metadata={
                        "input_tokens": response.input_tokens,
                        "output_tokens": response.output_tokens,
                        "cost_usd": response.cost_usd,
                    },
                )
            )
        state.add_trace_event("analyst.completed", span)
        return state
