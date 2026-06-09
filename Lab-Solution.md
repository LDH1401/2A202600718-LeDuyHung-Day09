# Lab Solution - Day09 Multi-Agent MCP/A2A

## Checklist nộp bài

Theo `Lab-assignment-checklist.md`, bài nộp gồm:

1. `Lab-Solution.md`: tổng hợp lời giải các bài lab trên lớp.
2. `Lab_Assignment/`: code assignment cải tiến agent Day08 bằng pattern Supervisor - Workers.
3. Code chạy được trước thời điểm nộp bài.

Các file đã hoàn thành:

```text
Lab-Solution.md
Lab_Assignment/README.md
Lab_Assignment/supervisor_workers_day08.py
Lab_Assignment/test_supervisor_workers.py
```

Ngoài ra, các file lab chính đã được cập nhật:

```text
common/llm.py
exercises/exercise_2_tools.py
exercises/exercise_4_multiagent.py
stages/stage_2_rag_tools/main.py
stages/stage_3_single_agent/main.py
tax_agent/graph.py
REPORT.md
chatbot_demo.html
chatbot_server.py
agent_visualization.html
latency_benchmark.py
```

---

## Phần 1 - Direct LLM Calling

### Cách chạy

```bash
uv run python stages/stage_1_direct_llm/main.py
```

### Trả lời câu hỏi trong codelab

1. LLM được khởi tạo trong `common/llm.py` qua hàm `get_llm()`.
2. Model dùng `ChatOpenAI` trỏ tới OpenRouter bằng `openai_api_base="https://openrouter.ai/api/v1"`.
3. Message gửi tới LLM gồm:
   - `SystemMessage`: định nghĩa vai trò, phong cách, phạm vi trả lời.
   - `HumanMessage`: chứa câu hỏi của người dùng.
4. `SystemMessage` giúp model biết phải đóng vai chuyên gia pháp lý; `HumanMessage` là nội dung cần trả lời.

### Bài tập 1.1

Đã chạy Stage 1 với câu hỏi về hậu quả pháp lý khi công ty vi phạm NDA. Kết quả cho thấy Stage 1 trả lời được ở mức tổng quát nhưng không có tool, không có retrieval, không có citation cụ thể.

### Bài tập 1.2

Đã thêm `temperature=0.3` trong `common/llm.py` để output ổn định hơn:

```python
temperature=0.3
```

---

## Phần 2 - LLM + RAG/Tools

### Cách chạy

```bash
uv run python stages/stage_2_rag_tools/main.py
uv run python exercises/exercise_2_tools.py
```

### Trả lời câu hỏi trong codelab

1. `@tool` được dùng để khai báo các function mà LLM có thể gọi.
2. `LEGAL_KNOWLEDGE` là list các dict, mỗi entry có `id`, `keywords`, `text`.
3. LLM được bind với tools bằng:

```python
llm_with_tools = llm.bind_tools(TOOLS)
```

### Bài tập 2.1

Đã thêm knowledge base entry `labor_law` về Bộ luật Lao động Việt Nam 2019 trong:

```text
stages/stage_2_rag_tools/main.py
exercises/exercise_2_tools.py
```

Entry này có các keywords:

```text
lao động, sa thải, hợp đồng lao động, labor, termination
```

### Bài tập 2.2

Đã tạo tool:

```python
check_statute_of_limitations(case_type: str) -> str
```

Tool trả về:

```text
contract -> 4 năm (UCC § 2-725)
tort     -> 2-3 năm tùy bang
property -> 5 năm
```

Tool đã được thêm vào danh sách tools và có nhánh xử lý tool call trong manual orchestration loop.

---

## Phần 3 - Single Agent với ReAct

### Cách chạy

```bash
uv run python stages/stage_3_single_agent/main.py
```

### Trả lời câu hỏi trong codelab

1. `create_react_agent()` tạo agent theo pattern ReAct.
2. Khác Stage 2, Stage 3 không cần tự viết vòng lặp tool-call thủ công.
3. Agent có thể tự quyết định gọi tool nào, quan sát kết quả, rồi tiếp tục gọi tool khác nếu cần.

### Bài tập 3.1

Đã thêm tool `search_case_law` vào `stages/stage_3_single_agent/main.py`.

Tool hỗ trợ các án lệ mẫu:

```text
breach     -> Hadley v. Baxendale (1854)
negligence -> Donoghue v. Stevenson (1932)
contract   -> Carlill v. Carbolic Smoke Ball Co (1893)
```

Tool đã được thêm vào `TOOLS`.

### Bài tập 3.2

Phiên bản LangGraph hiện tại không có tham số chính thức `verbose=True`; signature dùng `debug=True`. Vì vậy em bật:

```python
create_react_agent(..., debug=True)
```

Ngoài ra file Stage 3 đang stream từng update nên vẫn quan sát được quá trình:

```text
THINK + ACT
OBSERVE
FINAL ANSWER
```

---

## Phần 4 - Multi-Agent In-Process

### Cách chạy

```bash
uv run python stages/stage_4_milti_agent/main.py
uv run python exercises/exercise_4_multiagent.py
```

### Trả lời câu hỏi trong codelab

1. `State` là shared state dùng chung giữa các node trong LangGraph.
2. Các agent functions gồm `law_agent`, `tax_agent`, `compliance_agent`.
3. `Send()` được dùng để dispatch nhiều task song song.
4. `graph.add_node()` khai báo node; `graph.add_edge()` và `graph.add_conditional_edges()` định nghĩa luồng chạy.

### Bài tập 4.1

Đã thêm `privacy_agent` trong `exercises/exercise_4_multiagent.py`.

Agent này phân tích:

```text
GDPR, data protection, privacy rights, data breach, nghĩa vụ thông báo, tiền phạt.
```

### Bài tập 4.2

Đã implement conditional routing:

```text
tax/irs/thuế              -> tax_agent
compliance/sec/regulation -> compliance_agent
data/privacy/gdpr/dữ liệu -> privacy_agent
```

Nếu không có keyword phù hợp, graph đi thẳng tới `aggregate_results`.

---

## Phần 5 - Distributed A2A System

### Cách chạy

Terminal 1:

```bash
OPENROUTER_MODEL=openai/gpt-4o-mini OPENROUTER_MAX_TOKENS=128 \
uv run bash start_all.sh
```

Terminal 2:

```bash
OPENROUTER_MODEL=openai/gpt-4o-mini OPENROUTER_MAX_TOKENS=128 \
uv run python test_client.py
```

### Bài tập 5.1 - Trace request flow

Đã trace request full Stage 5 với ví dụ:

```text
trace_id: 570a5035-19f1-4c04-ae60-ec6fa5d19805
context_id: 479a7ceb-4307-427e-9d7d-c4efc04260bc
```

Sequence flow:

```text
User/test_client.py
  -> Customer Agent
  -> Registry discover("legal_question")
  -> Law Agent
  -> Registry discover("tax_question", "compliance_question")
  -> Tax Agent + Compliance Agent
  -> Law Agent aggregate
  -> Customer Agent
  -> User
```

### Bài tập 5.2 - Dynamic discovery

Đã test khi Tax Agent bị dừng. Registry vẫn trả metadata của Tax Agent nhưng endpoint không kết nối được. Law Agent ghi nhận lỗi `call_tax failed`, nhưng Compliance Agent vẫn chạy và hệ thống vẫn trả response cuối cùng.

Kết luận: hệ thống có khả năng degrade một phần, nhưng Registry hiện chưa có health-check để tự loại agent offline.

### Bài tập 5.3 - Modify agent behavior

Đã sửa `tax_agent/graph.py` để Tax Agent trả lời ngắn gọn hơn:

```text
Keep your response concise, under 120 words.
Use short bullets and avoid repeating points already covered by other agents.
```

---

## Bài tập cộng điểm

### HTML chatbot demo Stage 5

Đã tạo chatbot web:

```text
chatbot_demo.html
chatbot_server.py
```

Cách chạy:

```bash
OPENROUTER_MODEL=openai/gpt-4o-mini OPENROUTER_MAX_TOKENS=128 \
uv run bash start_all.sh
```

Terminal khác:

```bash
OPENROUTER_MODEL=openai/gpt-4o-mini OPENROUTER_MAX_TOKENS=128 \
uv run python chatbot_server.py
```

Mở:

```text
http://localhost:8080
```

Chatbot có 2 mode:

```text
Full Stage 5   -> gọi Customer Agent
Fast Law Agent -> gọi trực tiếp Law Agent để giảm latency
```

Ngoài ra có `agent_visualization.html` để minh họa luồng agent bằng animation.

### Latency benchmark

Đã thêm:

```text
latency_benchmark.py
```

Kết quả đo:

| Cách chạy | Latency |
|---|---:|
| Full Stage 5 qua Customer Agent | 17.37s |
| Optimized gọi trực tiếp Law Agent | 12.34s |
| Giảm được | 5.03s |

Tỷ lệ giảm:

```text
5.03 / 17.37 ≈ 28.96%
```

Phương án giảm latency: nếu client đã biết chắc câu hỏi thuộc domain pháp lý, gọi trực tiếp Law Agent để bỏ qua bước Customer Agent classification/delegation.

---

## Lab Assignment - Improve Day08 Agent bằng Supervisor-Workers

### Mục tiêu

Cải tiến agent Day08 RAG bằng pattern Supervisor - Workers, tối thiểu 2-3 workers. Em triển khai 1 supervisor và 3 workers trong folder:

```text
Lab_Assignment/
```

### Kiến trúc

```text
User question
  -> supervisor
      -> chọn tài liệu liên quan
      -> lập kế hoạch
      -> dispatch workers song song
          -> retrieval_worker
          -> legal_analysis_worker
          -> citation_risk_worker
  -> aggregate_results
  -> final answer có citation + trace
```

### Vai trò các thành phần

| Thành phần | Vai trò |
|---|---|
| `supervisor` | Chọn tài liệu, lập kế hoạch, giao việc |
| `retrieval_worker` | Truy xuất evidence từ local Day08 knowledge base |
| `legal_analysis_worker` | Rút ra phân tích pháp lý từ evidence |
| `citation_risk_worker` | Chuẩn bị citation và khuyến nghị chống hallucination |
| `aggregate_results` | Tổng hợp câu trả lời cuối |

### Cách chạy

```bash
uv run python Lab_Assignment/supervisor_workers_day08.py
```

Hoặc dùng `.venv`:

```bash
.venv/bin/python Lab_Assignment/supervisor_workers_day08.py
```

Chạy test:

```bash
.venv/bin/python -m unittest Lab_Assignment.test_supervisor_workers
```

### Kết quả demo

Với câu hỏi:

```text
Hình phạt cho hành vi tàng trữ trái phép chất ma túy là gì?
```

Hệ thống trả về:

```text
Supervisor chọn tài liệu liên quan.
retrieval_worker returned 3 evidence chunks.
legal_analysis_worker created 3 legal findings.
citation_risk_worker prepared 3 citations.
Final answer có phân tích, khuyến nghị, nguồn và trace.
```

### Điểm cải tiến so với Day08 pipeline đơn tuyến

- Có supervisor điều phối thay vì một hàm generation làm hết.
- Tách retrieval, legal analysis, citation/risk thành worker riêng.
- Có worker trace để debug.
- Có citation và khuyến nghị không suy đoán khi thiếu nguồn.
- Chạy offline, không phụ thuộc API key.

---

## Lệnh kiểm tra cuối

```bash
.venv/bin/python -m py_compile \
  exercises/exercise_2_tools.py \
  stages/stage_3_single_agent/main.py \
  Lab_Assignment/supervisor_workers_day08.py

.venv/bin/python Lab_Assignment/supervisor_workers_day08.py

.venv/bin/python -m unittest Lab_Assignment.test_supervisor_workers
```

Kết quả kiểm tra trên máy:

```text
py_compile: OK
Lab_Assignment.test_supervisor_workers: Ran 1 test - OK
Exercise 2 smoke test:
  search_legal_knowledge("sa thải hợp đồng lao động") -> [labor_law] ...
  check_statute_of_limitations("contract") -> 4 năm (UCC § 2-725)
```
