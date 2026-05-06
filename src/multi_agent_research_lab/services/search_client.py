"""Search client abstraction for ResearcherAgent."""

import json
from urllib.error import URLError
from urllib.request import Request, urlopen

from multi_agent_research_lab.core.config import get_settings
from multi_agent_research_lab.core.schemas import SourceDocument


class SearchClient:
    """Provider-agnostic search client with Tavily and offline fallback support."""

    def __init__(self) -> None:
        self.api_key = get_settings().tavily_api_key

    def search(self, query: str, max_results: int = 5) -> list[SourceDocument]:
        """Search for documents relevant to a query."""

        if self.api_key:
            try:
                return self._search_tavily(query, max_results)
            except (OSError, ValueError, URLError, TimeoutError):
                return self._offline_search(query, max_results)
        return self._offline_search(query, max_results)

    def _search_tavily(self, query: str, max_results: int) -> list[SourceDocument]:
        payload = json.dumps(
            {
                "api_key": self.api_key,
                "query": query,
                "max_results": max_results,
                "search_depth": "advanced",
                "include_answer": False,
            }
        ).encode("utf-8")
        request = Request(
            url="https://api.tavily.com/search",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urlopen(request, timeout=20) as response:
            data = json.loads(response.read().decode("utf-8"))
        results = data.get("results", [])
        documents: list[SourceDocument] = []
        for item in results[:max_results]:
            documents.append(
                SourceDocument(
                    title=item.get("title", "Untitled source"),
                    url=item.get("url"),
                    snippet=item.get("content", ""),
                    metadata={"provider": "tavily", "score": item.get("score")},
                )
            )
        return documents

    def _offline_search(self, query: str, max_results: int) -> list[SourceDocument]:
        query_lower = query.lower()
        corpus = [
            SourceDocument(
                title="GraphRAG in practice",
                url="https://example.local/graphrag-practice",
                snippet=(
                    "GraphRAG combines retrieval over graph-structured knowledge with reasoning "
                    "so systems can preserve entity relationships and cite source passages."
                ),
                metadata={"topic": "graphrag"},
            ),
            SourceDocument(
                title="State of multi-agent systems",
                url="https://example.local/multi-agent-overview",
                snippet=(
                    "Multi-agent systems help when tasks benefit from decomposition, but they add "
                    "latency, orchestration overhead, and new failure modes."
                ),
                metadata={"topic": "multi-agent"},
            ),
            SourceDocument(
                title="Guardrails for LLM agents",
                url="https://example.local/llm-guardrails",
                snippet=(
                    "Production guardrails include max iterations, timeout budgets, structured "
                    "validation, retries, and clear fallback behavior."
                ),
                metadata={"topic": "guardrails"},
            ),
            SourceDocument(
                title="Customer support agent workflows",
                url="https://example.local/support-workflows",
                snippet=(
                    "Customer support benefits from multi-agent design when routing, policy lookup, "
                    "and response drafting require distinct responsibilities."
                ),
                metadata={"topic": "support"},
            ),
            SourceDocument(
                title="Citation-aware answer writing",
                url="https://example.local/citation-writing",
                snippet=(
                    "Strong research assistants keep citations near claims, note uncertainty, and "
                    "separate evidence gathering from synthesis."
                ),
                metadata={"topic": "writing"},
            ),
        ]
        ranked = sorted(
            corpus,
            key=lambda item: self._match_score(query_lower, item),
            reverse=True,
        )
        matches = [item for item in ranked if self._match_score(query_lower, item) > 0]
        return (matches or ranked)[:max_results]

    def _match_score(self, query: str, document: SourceDocument) -> int:
        haystack = f"{document.title} {document.snippet} {' '.join(map(str, document.metadata.values()))}".lower()
        keywords = [word for word in query.split() if len(word) > 3]
        return sum(1 for keyword in keywords if keyword in haystack)
