"""Researcher agent skeleton."""

from multi_agent_research_lab.agents.base import BaseAgent
from multi_agent_research_lab.core.errors import ValidationError
from multi_agent_research_lab.core.schemas import AgentName, AgentResult
from multi_agent_research_lab.core.state import ResearchState
from multi_agent_research_lab.observability.tracing import trace_span
from multi_agent_research_lab.services.llm_client import LLMClient
from multi_agent_research_lab.services.search_client import SearchClient


class ResearcherAgent(BaseAgent):
    """Collects sources and creates concise research notes."""

    name = "researcher"

    def __init__(
        self,
        search_client: SearchClient | None = None,
        llm_client: LLMClient | None = None,
    ) -> None:
        self.search_client = search_client or SearchClient()
        self.llm_client = llm_client or LLMClient()

    def run(self, state: ResearchState) -> ResearchState:
        """Populate `state.sources` and `state.research_notes`."""

        with trace_span("researcher", {"query": state.request.query}, run_type="tool") as span:
            sources = self.search_client.search(
                state.request.query,
                max_results=state.request.max_sources,
            )
            if not sources:
                raise ValidationError("ResearcherAgent could not retrieve any source documents.")
            source_digest = "\n".join(
                f"- {index}. {source.title}: {source.snippet}"
                for index, source in enumerate(sources, start=1)
            )
            response = self.llm_client.complete(
                system_prompt=(
                    "You are a research agent. Produce concise research notes with key evidence, "
                    "high-signal facts, and explicit source references."
                ),
                user_prompt=(
                    f"Query: {state.request.query}\n"
                    f"Audience: {state.request.audience}\n"
                    f"Sources:\n{source_digest}"
                ),
            )
            notes = "\n".join(
                [
                    "Research Notes",
                    f"Question: {state.request.query}",
                    "",
                    "Evidence Digest:",
                    source_digest,
                    "",
                    "Summary:",
                    response.content,
                ]
            )
            state.sources = sources
            state.research_notes = notes
            state.agent_results.append(
                AgentResult(
                    agent=AgentName.RESEARCHER,
                    content=notes,
                    metadata={
                        "source_count": len(sources),
                        "input_tokens": response.input_tokens,
                        "output_tokens": response.output_tokens,
                        "cost_usd": response.cost_usd,
                    },
                )
            )
        span["attributes"]["source_count"] = len(state.sources)
        state.add_trace_event("researcher.completed", span)
        return state
