# Lab Assignment - Improve Day08 Agent With Supervisor-Workers

## Mục tiêu

Bài assignment cải tiến agent RAG của Day08 bằng pattern **Supervisor - Workers**.
Thay vì một pipeline đơn tuyến làm hết retrieval, analysis và generation, hệ thống
được tách thành:

- `supervisor`: đọc câu hỏi, chọn tài liệu liên quan và lập kế hoạch.
- `retrieval_worker`: truy xuất evidence từ knowledge base Day08.
- `legal_analysis_worker`: phân tích pháp lý từ evidence đã chọn.
- `citation_risk_worker`: chuẩn bị citation và khuyến nghị để tránh hallucination.
- `aggregate_results`: tổng hợp kết quả thành câu trả lời cuối cùng.

## Cách chạy

Từ thư mục gốc repo:

```bash
uv run python Lab_Assignment/supervisor_workers_day08.py
```

Hoặc chạy với câu hỏi riêng:

```bash
uv run python Lab_Assignment/supervisor_workers_day08.py \
  "Quy trình cai nghiện bắt buộc theo Luật Phòng chống ma túy 2021 là gì?"
```

Nếu môi trường `uv` gặp lỗi snap, có thể dùng venv trực tiếp:

```bash
.venv/bin/python Lab_Assignment/supervisor_workers_day08.py
```

## Điểm cải tiến so với Day08 agent đơn tuyến

- Tách trách nhiệm rõ ràng: retrieval, analysis, citation/risk.
- Supervisor quyết định tài liệu cần dùng trước khi giao việc cho workers.
- Workers chạy theo fan-out/fan-in graph bằng LangGraph `Send`.
- Câu trả lời cuối cùng có trace để biết worker nào đã làm gì.
- Chạy offline, không cần API key, phù hợp để demo và nộp bài.

## File chính

```text
Lab_Assignment/
├── README.md
├── __init__.py
└── supervisor_workers_day08.py
```
