# Lab 20: Multi-Agent Research System

Repo hoàn chỉnh cho bài lab **Multi-Agent Systems**: xây dựng hệ thống nghiên cứu gồm
**Supervisor + Researcher + Analyst + Writer**, có benchmark với single-agent baseline,
trace nội bộ và benchmark report xuất ra thư mục `reports/`.

## Learning outcomes

Sau 2 giờ lab, học viên cần có thể:

1. Thiết kế role rõ ràng cho nhiều agent.
2. Xây dựng shared state đủ thông tin cho handoff.
3. Thêm guardrail tối thiểu: max iterations, timeout, retry/fallback, validation.
4. Trace được luồng chạy và giải thích agent nào làm gì.
5. Benchmark single-agent vs multi-agent theo quality, latency, cost.

## Architecture mục tiêu

```text
User Query
   |
   v
Supervisor / Router
   |------> Researcher Agent  -> research_notes
   |------> Analyst Agent     -> analysis_notes
   |------> Writer Agent      -> final_answer
   |
   v
Trace + Benchmark Report
```

## Cấu trúc repo

```text
.
├── src/multi_agent_research_lab/
│   ├── agents/              # Agent interfaces + implementations
│   ├── core/                # Config, state, schemas, errors
│   ├── graph/               # Workflow orchestration
│   ├── services/            # LLM, search, storage clients
│   ├── evaluation/          # Benchmark/evaluation helpers
│   ├── observability/       # Logging/tracing hooks
│   └── cli.py               # CLI entrypoint
├── configs/                 # YAML configs for lab variants
├── docs/                    # Lab guide, rubric, design notes
├── tests/                   # Unit tests for skeleton behavior
├── notebooks/               # Optional notebook entrypoint
├── scripts/                 # Helper scripts
├── .env.example             # Environment variables template
├── pyproject.toml           # Python project config
├── Dockerfile               # Containerized dev/runtime
└── Makefile                 # Common commands
```

## Quickstart

### 1. Tạo môi trường

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\\Scripts\\activate
pip install -e "[dev,llm]"
cp .env.example .env
```

### 2. Cấu hình API keys

Mở `.env` và điền key cần thiết.

```bash
OPENAI_API_KEY=...
# optional
LANGSMITH_API_KEY=...
TAVILY_API_KEY=...
```

### 3. Chạy smoke test

```bash
make test
python -m multi_agent_research_lab.cli --help
```

### 4. Chạy baseline

```bash
python -m multi_agent_research_lab.cli baseline \
  --query "Research GraphRAG state-of-the-art and write a 500-word summary"
```

Nếu có `OPENAI_API_KEY`, baseline sẽ gọi model thật. Nếu không có key hoặc không truy cập
được provider, repo dùng offline fallback để vẫn demo được end-to-end.

### 5. Chạy multi-agent

```bash
python -m multi_agent_research_lab.cli multi-agent \
  --query "Research GraphRAG state-of-the-art and write a 500-word summary"
```

Lệnh này sẽ chạy đủ pipeline `supervisor -> researcher -> analyst -> writer`, sau đó
ghi trace JSON vào `reports/traces/latest_trace.json`.

### 6. Chạy benchmark

```bash
python -m multi_agent_research_lab.cli benchmark
```

Lệnh này chạy các query trong `configs/lab_default.yaml`, benchmark baseline và
multi-agent, rồi ghi `reports/benchmark_report.md` cùng các trace JSON tương ứng.

## Milestones trong 2 giờ lab

| Thời lượng | Milestone | File gợi ý |
|---:|---|---|
| 0-15' | Setup, chạy baseline | `cli.py`, `services/llm_client.py` |
| 15-45' | Review Supervisor / workflow | `agents/supervisor.py`, `graph/workflow.py` |
| 45-75' | Review Researcher, Analyst, Writer | `agents/*.py`, `core/state.py` |
| 75-95' | Chạy trace + benchmark | `observability/tracing.py`, `evaluation/benchmark.py` |
| 95-115' | Peer review theo rubric | `docs/peer_review_rubric.md` |
| 115-120' | Exit ticket | `docs/lab_guide.md` |

## Quy ước production trong repo

- Tách rõ `agents`, `services`, `core`, `graph`, `evaluation`, `observability`.
- Không hard-code API key trong code.
- Tất cả input/output chính dùng Pydantic schema.
- Có type hints, linting, formatting, unit test tối thiểu.
- Có logging/tracing hook ngay từ đầu.
- Không để agent chạy vô hạn: dùng `max_iterations`, `timeout_seconds`.
- Có benchmark report thay vì chỉ demo output đẹp.

## Những gì repo hiện có

1. `LLMClient` có hỗ trợ OpenAI và offline fallback.
2. `SearchClient` có hỗ trợ Tavily và offline mock corpus.
3. `Supervisor`, `Researcher`, `Analyst`, `Writer`, `Critic` đã được triển khai.
4. `MultiAgentWorkflow` chạy orchestration end-to-end với guardrails cơ bản.
5. Benchmark report và trace export được tạo tự động.

## Deliverables

Học viên nộp:

1. GitHub repo cá nhân.
2. Screenshot trace hoặc link trace.
3. `reports/benchmark_report.md` so sánh single vs multi-agent.
4. Một đoạn giải thích failure mode và cách fix.

## References

- Anthropic: Building effective agents — https://www.anthropic.com/engineering/building-effective-agents
- OpenAI Agents SDK orchestration/handoffs — https://developers.openai.com/api/docs/guides/agents/orchestration
- LangGraph concepts — https://langchain-ai.github.io/langgraph/concepts/
- LangSmith tracing — https://docs.smith.langchain.com/
- Langfuse tracing — https://langfuse.com/docs
