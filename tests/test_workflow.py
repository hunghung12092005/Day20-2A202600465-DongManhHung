from multi_agent_research_lab.core.schemas import ResearchQuery
from multi_agent_research_lab.core.state import ResearchState
from multi_agent_research_lab.graph.workflow import MultiAgentWorkflow


def test_multi_agent_workflow_produces_final_answer() -> None:
    state = ResearchState(request=ResearchQuery(query="Summarize production guardrails for LLM agents"))
    result = MultiAgentWorkflow().run(state)
    assert result.final_answer is not None
    assert "Sources:" in result.final_answer
    assert result.route_history == ["researcher", "analyst", "writer"]
    assert any(agent_result.agent == "critic" for agent_result in result.agent_results)

