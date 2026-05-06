# Project Summary

## 1. Lab này làm gì

Đây là bài lab xây dựng một **hệ thống research multi-agent** để trả lời các câu hỏi dài và cần tìm nguồn.

Project hỗ trợ 2 cách chạy:

- `baseline`: một agent làm toàn bộ từ đầu đến cuối
- `multi-agent`: chia thành nhiều vai trò:
  - `Supervisor`: điều phối
  - `Researcher`: tìm nguồn
  - `Analyst`: phân tích nguồn
  - `Writer`: viết câu trả lời cuối
  - `Critic`: kiểm tra citation coverage

Mục tiêu của lab là:

- hiểu cách thiết kế nhiều agent
- chia trách nhiệm rõ ràng giữa các agent
- truyền dữ liệu qua shared state
- trace được workflow
- benchmark `single-agent` và `multi-agent`

## 2. Kiến trúc tổng quan

Luồng xử lý chính:

```text
User Query
   |
   v
Supervisor
   |
   +--> Researcher -> sources + research_notes
   |
   +--> Analyst    -> analysis_notes
   |
   +--> Writer     -> final_answer
   |
   +--> Critic     -> citation review
   |
   v
Trace + Benchmark Report
```

Shared state chính nằm trong `ResearchState`:

- `request`: câu hỏi đầu vào
- `iteration`: số bước đã chạy
- `route_history`: agent nào đã được gọi
- `sources`: danh sách nguồn
- `research_notes`: ghi chú từ researcher
- `analysis_notes`: ghi chú từ analyst
- `final_answer`: đáp án cuối
- `agent_results`: output của từng agent
- `trace`: nhật ký các bước
- `errors`: lỗi nếu có

## 3. Công nghệ và provider đang dùng

- `OpenAI API`: dùng cho phần sinh nội dung LLM
- `Tavily API`: dùng để web search thật
- `Pydantic`: schema và state
- `Typer`: CLI
- `PyYAML`: đọc config benchmark
- `pytest`: test

Repo cũng có fallback local:

- nếu OpenAI không gọi được thì có offline fallback
- nếu Tavily không gọi được thì có local mock corpus

## 4. Cách chạy project

Vào thư mục project:

```bash
cd /home/hung/code/AI_CODE_VIN/lab/day20/Day20-2A202600465-DongManhHung
source .venv/bin/activate
```

### Chạy test

```bash
pytest -q
```

Kỳ vọng:

- thấy `6 passed`

### Chạy baseline

```bash
python -m multi_agent_research_lab.cli baseline --query "Summarize production guardrails for LLM agents"
```

Ý nghĩa:

- chỉ dùng một agent
- trả ra câu trả lời cuối ngay trên terminal

### Chạy multi-agent

```bash
python -m multi_agent_research_lab.cli multi-agent --query "Summarize production guardrails for LLM agents"
```

Ý nghĩa:

- chạy đủ workflow nhiều agent
- in ra toàn bộ JSON state
- ghi trace vào file:

`reports/traces/latest_trace.json`

### Chạy benchmark

```bash
python -m multi_agent_research_lab.cli benchmark
```

Ý nghĩa:

- chạy nhiều query trong `configs/lab_default.yaml`
- so sánh `baseline` với `multi-agent`
- ghi report vào:

`reports/benchmark_report.md`

## 5. Cách đọc kết quả

### Baseline

Bạn sẽ thấy:

- một câu trả lời cuối
- không có chia bước

Đây là cách làm đơn giản nhất.

### Multi-agent

Bạn sẽ thấy một JSON lớn. Các trường quan trọng nhất:

- `route_history`
  - ví dụ: `["researcher", "analyst", "writer"]`
  - nghĩa là supervisor đã route đúng qua 3 bước

- `sources`
  - danh sách nguồn web mà researcher tìm được
  - nếu thấy `provider: tavily` thì đang dùng web search thật

- `research_notes`
  - phần tổng hợp nguồn ban đầu

- `analysis_notes`
  - phần phân tích trade-off, evidence, risk

- `final_answer`
  - đây là đáp án cuối cùng

- `trace`
  - log từng bước chạy

- `errors`
  - nếu là `[]` thì workflow chạy ổn

## 6. Benchmark hiện đang đo gì

File:

- `reports/benchmark_report.md`

Các cột:

- `Latency (s)`: thời gian chạy
- `Cost (USD)`: chi phí ước tính
- `Quality`: điểm chất lượng nội bộ
- `Citation Coverage`: mức độ có citation
- `Failure Rate`: có fail hay không

Kết luận thường thấy:

- `baseline` nhanh hơn
- `multi-agent` chậm hơn
- `multi-agent` có citation và trace tốt hơn

## 7. Những file quan trọng nhất

### Entry point

- `src/multi_agent_research_lab/cli.py`
  - lệnh `baseline`, `multi-agent`, `benchmark`

### Core

- `src/multi_agent_research_lab/core/config.py`
  - đọc `.env`
- `src/multi_agent_research_lab/core/state.py`
  - shared state toàn workflow
- `src/multi_agent_research_lab/core/schemas.py`
  - schema cho query, source, metrics

### Agents

- `src/multi_agent_research_lab/agents/supervisor.py`
  - quyết định route
- `src/multi_agent_research_lab/agents/researcher.py`
  - gọi search và tạo `research_notes`
- `src/multi_agent_research_lab/agents/analyst.py`
  - tạo `analysis_notes`
- `src/multi_agent_research_lab/agents/writer.py`
  - tạo `final_answer`
- `src/multi_agent_research_lab/agents/critic.py`
  - kiểm tra citation coverage

### Services

- `src/multi_agent_research_lab/services/llm_client.py`
  - wrapper cho OpenAI
- `src/multi_agent_research_lab/services/search_client.py`
  - wrapper cho Tavily và local fallback
- `src/multi_agent_research_lab/services/storage.py`
  - ghi report và trace

### Workflow

- `src/multi_agent_research_lab/graph/workflow.py`
  - orchestration multi-agent

### Evaluation

- `src/multi_agent_research_lab/evaluation/benchmark.py`
  - chạy benchmark
- `src/multi_agent_research_lab/evaluation/report.py`
  - render markdown report

### Observability

- `src/multi_agent_research_lab/observability/tracing.py`
  - trace span
- `src/multi_agent_research_lab/observability/logging.py`
  - setup logging

## 8. Deliverables của project này

Project hiện đã có đủ các output quan trọng:

- benchmark report:
  - `reports/benchmark_report.md`
- trace mới nhất:
  - `reports/traces/latest_trace.json`
- failure mode:
  - `reports/failure_mode.md`

## 9. Trạng thái hiện tại của project

Project đã được hoàn thiện để:

- chạy end-to-end
- có baseline và multi-agent
- dùng OpenAI thật
- dùng Tavily thật
- có fallback local khi provider lỗi
- có benchmark report
- có trace JSON
- có test pass

## 10. Tóm tắt ngắn gọn

Nếu giải thích bài này thật nhanh:

- `baseline` là 1 agent tự làm tất cả
- `multi-agent` là nhiều agent chia việc
- project này cho bạn thấy rõ:
  - ai làm gì
  - dữ liệu chuyền qua các bước như nào
  - nguồn nào được dùng
  - multi-agent có đáng dùng hơn baseline không

Nếu chỉ cần demo nhanh, chạy:

```bash
source .venv/bin/activate
python -m multi_agent_research_lab.cli baseline --query "Summarize production guardrails for LLM agents"
python -m multi_agent_research_lab.cli multi-agent --query "Summarize production guardrails for LLM agents"
python -m multi_agent_research_lab.cli benchmark
```
