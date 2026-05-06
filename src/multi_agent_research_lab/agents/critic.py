"""Optional critic agent skeleton for bonus work."""

from multi_agent_research_lab.agents.base import BaseAgent
from multi_agent_research_lab.core.errors import ValidationError
from multi_agent_research_lab.core.schemas import AgentName, AgentResult
from multi_agent_research_lab.core.state import ResearchState


class CriticAgent(BaseAgent):
    """Optional fact-checking and safety-review agent."""

    name = "critic"

    def run(self, state: ResearchState) -> ResearchState:
        """Validate final answer and append findings."""

        if not state.final_answer:
            raise ValidationError("CriticAgent requires final_answer before review.")
        citation_count = sum(1 for token in state.final_answer.split() if token.startswith("["))
        coverage = citation_count / max(1, len(state.sources))
        critique = (
            f"Critic review: citation markers={citation_count}, "
            f"source_count={len(state.sources)}, estimated_coverage={coverage:.2f}."
        )
        state.agent_results.append(
            AgentResult(
                agent=AgentName.CRITIC,
                content=critique,
                metadata={"citation_coverage": round(min(coverage, 1.0), 2)},
            )
        )
        state.add_trace_event(
            "critic.completed",
            {"name": "critic", "payload": {"citation_coverage": round(min(coverage, 1.0), 2)}},
        )
        return state
