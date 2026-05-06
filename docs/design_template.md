# Design Template

## Problem

Hệ thống cần xử lý các câu hỏi research dài, cần tìm nguồn, phân tích, rồi viết câu trả
lời cuối có citation và có thể benchmark được chất lượng so với single-agent baseline.

## Why multi-agent?

Single-agent phù hợp khi câu hỏi ngắn và ít bước. Với các bài research dài, tách vai trò
giúp giảm tải ngữ cảnh cho từng bước: `Researcher` tập trung tìm evidence, `Analyst`
tập trung lập luận, `Writer` tập trung trình bày. Đổi lại là tăng orchestration overhead,
nên cần benchmark để kiểm tra có đáng hay không.

## Agent roles

| Agent | Responsibility | Input | Output | Failure mode |
|---|---|---|---|---|
| Supervisor | Chọn bước tiếp theo và dừng đúng lúc | `ResearchState` | route tiếp theo | loop quá số vòng, route sai |
| Researcher | Tìm nguồn và ghi research notes | query, max sources | `sources`, `research_notes` | không tìm thấy nguồn |
| Analyst | Rút insight và trade-off | research notes, sources | `analysis_notes` | bỏ sót weak evidence |
| Writer | Viết câu trả lời cuối có nguồn | research notes, analysis notes | `final_answer` | trả lời dài dòng hoặc thiếu citation |

## Shared state

- `request`: giữ query gốc và các ràng buộc đầu vào
- `iteration`, `route_history`: debug orchestration và chống loop
- `sources`: tập nguồn đã thu thập
- `research_notes`: handoff từ Researcher sang Analyst/Writer
- `analysis_notes`: handoff từ Analyst sang Writer
- `final_answer`: output cuối
- `agent_results`: lưu artefact và metadata theo từng agent
- `trace`: ghi event theo bước để benchmark và debug
- `errors`: lưu failure mode hoặc fallback đã xảy ra

## Routing policy

Graph đơn giản:

`supervisor -> researcher -> supervisor -> analyst -> supervisor -> writer -> critic`

Điều kiện dừng:

- Nếu đã có `final_answer` thì `done`
- Nếu vượt `max_iterations` mà chưa có câu trả lời thì ép route sang `writer`
- Nếu workflow vượt `timeout_seconds` thì dừng và ghi lỗi

## Guardrails

- Max iterations: dùng `MAX_ITERATIONS`, mặc định 6
- Timeout: dùng `TIMEOUT_SECONDS`, mặc định 60 giây
- Retry: client/provider fallback sang chế độ offline thay vì crash
- Fallback: search và LLM đều có local fallback
- Validation: `Analyst` và `Writer` kiểm tra đủ input trước khi chạy

## Benchmark plan

- Query: dùng các query trong `configs/lab_default.yaml`
- Metric: latency, cost, quality score, citation coverage, failure rate
- Expected outcome: multi-agent chậm hơn baseline nhưng thường có quality và citation coverage tốt hơn
