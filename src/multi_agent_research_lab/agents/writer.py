"""Writer agent skeleton."""

from multi_agent_research_lab.agents.base import BaseAgent
from multi_agent_research_lab.core.errors import ValidationError
from multi_agent_research_lab.core.schemas import AgentName, AgentResult
from multi_agent_research_lab.core.state import ResearchState
from multi_agent_research_lab.observability.tracing import trace_span


class WriterAgent(BaseAgent):
    """Produces final answer from research and analysis notes."""

    name = "writer"

    def run(self, state: ResearchState) -> ResearchState:
        """Populate `state.final_answer`."""

        if not state.research_notes:
            raise ValidationError("WriterAgent requires research_notes before writing.")
        with trace_span("writer", {"query": state.request.query}, run_type="chain") as span:
            findings = state.analysis_notes or state.research_notes
            citations = [
                f"[{index}] {source.title} - {source.url or 'local source'}"
                for index, source in enumerate(state.sources, start=1)
            ]
            answer = "\n".join(
                [
                    f"Answer for: {state.request.query}",
                    "",
                    f"Audience: {state.request.audience}",
                    "",
                    "Synthesis:",
                    findings,
                    "",
                    "Recommended Response:",
                    (
                        "Use the evidence above to present a balanced answer, call out trade-offs, "
                        "and keep citations near major claims."
                    ),
                    "",
                    "Sources:",
                    "\n".join(citations),
                ]
            )
            state.final_answer = answer
            state.agent_results.append(
                AgentResult(
                    agent=AgentName.WRITER,
                    content=answer,
                    metadata={"citation_count": len(citations)},
                )
            )
        state.add_trace_event("writer.completed", span)
        return state
