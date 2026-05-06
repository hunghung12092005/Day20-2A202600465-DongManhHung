"""LangGraph workflow skeleton."""

import langsmith as ls
from time import perf_counter

from multi_agent_research_lab.agents import AnalystAgent, CriticAgent, ResearcherAgent, SupervisorAgent, WriterAgent
from multi_agent_research_lab.core.config import Settings, get_settings
from multi_agent_research_lab.core.errors import AgentExecutionError
from multi_agent_research_lab.core.state import ResearchState
from multi_agent_research_lab.observability.tracing import configure_langsmith, is_langsmith_enabled, trace_span


class MultiAgentWorkflow:
    """Builds and runs the multi-agent graph."""

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()
        self.supervisor = SupervisorAgent(self.settings)
        self.researcher = ResearcherAgent()
        self.analyst = AnalystAgent()
        self.writer = WriterAgent()
        self.critic = CriticAgent()

    def build(self) -> dict[str, object]:
        """Create a provider-agnostic graph description."""

        return {
            "entrypoint": "supervisor",
            "nodes": {
                "supervisor": self.supervisor,
                "researcher": self.researcher,
                "analyst": self.analyst,
                "writer": self.writer,
                "critic": self.critic,
            },
            "routes": {
                "supervisor": ["researcher", "analyst", "writer", "done"],
                "researcher": ["supervisor"],
                "analyst": ["supervisor"],
                "writer": ["done"],
            },
        }

    def run(self, state: ResearchState) -> ResearchState:
        """Execute the graph and return final state."""

        graph = self.build()
        started = perf_counter()
        nodes = graph["nodes"]
        with self._workflow_trace(state):
            with trace_span("workflow", {"query": state.request.query}, run_type="chain"):
                while True:
                    if perf_counter() - started > self.settings.timeout_seconds:
                        state.errors.append("Workflow timed out before producing a final answer.")
                        break
                    self.supervisor.run(state)
                    route = state.route_history[-1]
                    if route == "done":
                        break
                    agent = nodes.get(route)
                    if agent is None:
                        state.errors.append(f"Unknown route selected by supervisor: {route}")
                        break
                    state = agent.run(state)
                    if route == "writer":
                        state = self.critic.run(state)
                        break
        if not state.final_answer:
            raise AgentExecutionError(
                "Multi-agent workflow ended without a final answer. "
                f"Route history: {state.route_history}; errors: {state.errors}"
            )
        state.add_trace_event(
            "workflow.completed",
            {
                "name": "workflow",
                "payload": {
                    "iterations": state.iteration,
                    "route_history": state.route_history,
                    "error_count": len(state.errors),
                },
            },
        )
        return state

    def _workflow_trace(self, state: ResearchState):
        if not is_langsmith_enabled(self.settings):
            return ls.tracing_context(enabled=False)
        configure_langsmith(self.settings)
        return ls.trace(
            "multi_agent_workflow",
            run_type="chain",
            project_name=self.settings.langsmith_project,
            inputs={"query": state.request.query, "audience": state.request.audience},
            tags=["multi-agent", "lab"],
            metadata={"max_iterations": self.settings.max_iterations},
        )
