# Hệ Thống Multi-Agent Pháp Lý với Giao Thức A2A

Đây là một hệ thống tư vấn pháp lý phân tán, nơi các AI agent chuyên biệt phối hợp với nhau bằng [giao thức Agent-to-Agent (A2A) của Google](https://github.com/google/A2A). Được xây dựng bằng **LangGraph**, **LangChain** và **a2a-sdk**, dự án này vừa là một demo chạy được, vừa là lộ trình học thực hành — đi từ một lời gọi API LLM đơn giản (Stage 1) đến một mạng multi-agent phân tán hoàn chỉnh (Stage 5).

## Kiến Trúc

```
                     ┌─────────────────────┐
                     │  Dịch vụ Registry   │  :10000
                     │  /register          │
                     │  /discover/{task}   │
                     └─────────┬───────────┘
                               │  (các agent tự đăng ký khi khởi động)
          ┌────────────────────┼─────────────────────┐
          │                    │                     │
   Tax Agent :10102   Law Agent :10101    Compliance Agent :10103
          │                    │                     │
          └─────────► ủy quyền song song ◄───────────┘
                               │
                        Customer Agent :10100
                               │
                            Người dùng
```

**Customer Agent** nhận câu hỏi từ người dùng và ủy quyền cho **Law Agent**. **Law Agent** phân tích khía cạnh pháp lý, sau đó gửi song song sang **Tax Agent** và **Compliance Agent** thông qua API `Send` của LangGraph. Các kết quả được tổng hợp thành một bản phân tích pháp lý đầy đủ.

Việc khám phá agent hoàn toàn động — các agent đăng ký năng lực của mình với **Registry** khi khởi động và tìm nhau trong lúc chạy. Không có URL agent bị hardcode.

### Chi Tiết Agent

| Agent | Port | Pattern LangGraph | Vai trò |
|---|---|---|---|
| Customer Agent | 10100 | `create_react_agent` | Điểm vào — định tuyến câu hỏi của người dùng đến Law Agent |
| Law Agent | 10101 | `StateGraph` tùy chỉnh | Agent điều phối — phân tích luật, ủy quyền song song |
| Tax Agent | 10102 | `create_react_agent` | Chuyên gia — luật thuế, IRS, hình phạt, FBAR/FATCA |
| Compliance Agent | 10103 | `create_react_agent` | Chuyên gia — SEC, SOX, FCPA, GDPR, AML |
| Registry | 10000 | FastAPI (không phải agent) | Khám phá dịch vụ và đăng ký agent |

### Luồng Request

```
Câu hỏi của người dùng
  → Customer Agent: LLM nhận diện miền pháp lý, gọi delegate tool
    → Registry: discover("legal_question") → endpoint của Law Agent
    → Law Agent:
        [analyze_law]      LLM phân tích hợp đồng/bồi thường ngoài hợp đồng
        [check_routing]    LLM quyết định: needs_tax? needs_compliance?
        [call_tax]         ──→ Registry discover → Tax Agent (A2A)     ┐
        [call_compliance]  ──→ Registry discover → Compliance (A2A)    ├ song song
        [aggregate]        Kết hợp tất cả phân tích thành phản hồi cuối ┘
  → Customer Agent trả phản hồi cho người dùng
```

### Các Pattern Thiết Kế Chính

- **Khám phá động** — các agent tìm nhau thông qua Registry, không dùng URL hardcode
- **Ủy quyền song song** — API `Send` của LangGraph dispatch các nhánh tax và compliance đồng thời
- **Lan truyền trace** — `trace_id` và `context_id` đi qua từng A2A hop để hỗ trợ debug
- **Chặn độ sâu** — `MAX_DELEGATION_DEPTH = 3` ngăn vòng lặp ủy quyền vô hạn
- **Annotated reducers** — `Annotated[str, _last_wins]` xử lý việc nhiều nhánh song song ghi vào cùng field trong state

## Tech Stack

| Tầng | Lựa chọn |
|---|---|
| Agent framework | [LangGraph](https://langchain-ai.github.io/langgraph/) |
| Nhà cung cấp LLM | Bất kỳ model nào qua [OpenRouter](https://openrouter.ai) (API tương thích OpenAI) |
| A2A transport | [a2a-sdk](https://pypi.org/project/a2a-sdk/) |
| Registry | FastAPI + store trong bộ nhớ |
| Package manager | [uv](https://docs.astral.sh/uv/) |

## 📚 Codelab cho Sinh Viên

**Thời gian:** 2 giờ | **Ngôn ngữ:** Tiếng Việt

Codelab hướng dẫn từng bước xây dựng multi-agent system, từ cơ bản đến nâng cao:

- **[CODELAB.md](CODELAB.md)** - Hướng dẫn chi tiết cho sinh viên
- **[INSTRUCTOR_GUIDE.md](INSTRUCTOR_GUIDE.md)** - Hướng dẫn cho giảng viên
- **[QUICK_REFERENCE.md](QUICK_REFERENCE.md)** - Tài liệu tham khảo nhanh
- **[exercises/](exercises/)** - Bài tập thực hành với skeleton code
- **[exercises/SOLUTIONS.md](exercises/SOLUTIONS.md)** - Đáp án chi tiết

### Lộ Trình Học

```
Stage 1: Direct LLM (20 phút)
    ↓
Stage 2: RAG + Tools (30 phút)
    ↓
Stage 3: ReAct Agent (25 phút)
    ↓
Stage 4: Multi-Agent (30 phút)
    ↓
Stage 5: Distributed A2A (30 phút)
    ↓
Tổng kết & Q&A (15 phút)
```

**Bắt đầu:** Đọc [CODELAB.md](CODELAB.md)

---

## Bắt Đầu

### Yêu Cầu Trước Khi Chạy

- Python 3.11+
- Package manager [uv](https://docs.astral.sh/uv/)
- API key [OpenRouter](https://openrouter.ai)

### Cài Đặt

```bash
# Clone và cài đặt
git clone <repo-url>
cd legal_multiagent
uv sync

# Cấu hình môi trường
cp .env.example .env
# Chỉnh sửa .env với OpenRouter API key của bạn
```

### Chạy Toàn Bộ Hệ Thống (Stage 5)

```bash
# Khởi động cả 5 service (registry + 4 agents)
./start_all.sh

# Trong terminal khác, gửi một câu hỏi test
uv run python test_client.py
```

### Chạy Demo Từng Stage

Không cần server — mỗi demo chạy như một script độc lập:

```bash
uv run python stages/stage_1_direct_llm/main.py
uv run python stages/stage_2_rag_tools/main.py
uv run python stages/stage_3_single_agent/main.py
uv run python stages/stage_4_multi_agent/main.py
```

## Các Stage Phát Triển LLM

Thư mục `stages/` chứa các demo tăng dần độ phức tạp từ đơn giản đến nâng cao, khớp với lộ trình trong `docs/10_llm_roadmap.svg`:

| Stage | Tên | Nội dung minh họa |
|---|---|---|
| **1** | Gọi LLM trực tiếp | Prompt không trạng thái → phản hồi. Không tool, không memory. |
| **2** | LLM + RAG / Tools | Tool calling với knowledge base khớp từ khóa và công cụ tính thiệt hại. Điều phối thủ công một lượt. |
| **3** | Single Agent (ReAct) | Vòng lặp tự động Think → Act → Observe qua `create_react_agent`. Agent tự quyết định gọi tool nào và khi nào. |
| **4** | Multi-Agent (In-Process) | Nhiều agent chuyên biệt chạy song song qua `StateGraph` + API `Send`. Cùng topology với Stage 5 nhưng chạy trong một process. |
| **5** | Distributed A2A (Dự án này) | Hệ thống phân tán hoàn chỉnh — mỗi agent là một HTTP service độc lập, giao tiếp bằng giao thức A2A với khám phá động. |

Mỗi thư mục stage có một sơ đồ `architecture.svg` và một file `main.py` tự chạy.

## Cấu Trúc Dự Án

```
legal_multiagent/
├── start_all.sh               # Khởi chạy tất cả service theo đúng thứ tự
├── test_client.py             # Client test E2E
├── pyproject.toml             # Dependencies (quản lý bằng uv)
├── .env.example               # Các biến môi trường cần thiết
│
├── common/                    # Tiện ích dùng chung
│   ├── llm.py                 # get_llm() → ChatOpenAI qua OpenRouter
│   ├── a2a_client.py          # delegate() — gửi message A2A
│   └── registry_client.py     # discover() / register() — Registry API
│
├── registry/                  # Khám phá dịch vụ (port 10000)
├── customer_agent/            # Agent điểm vào (port 10100)
├── law_agent/                 # Agent điều phối pháp lý (port 10101)
├── tax_agent/                 # Chuyên gia thuế (port 10102)
├── compliance_agent/          # Chuyên gia compliance (port 10103)
│
├── stages/                    # Demo học tập tăng dần (1-4)
│   ├── stage_1_direct_llm/
│   ├── stage_2_rag_tools/
│   ├── stage_3_single_agent/
│   └── stage_4_multi_agent/
│
└── docs/                      # Sơ đồ kiến trúc (SVG)
```

Mỗi module agent có cùng cấu trúc:
- **`graph.py`** — định nghĩa graph LangGraph (toàn bộ logic agent)
- **`agent_executor.py`** — cầu nối giữa A2A SDK và LangGraph
- **`__main__.py`** — bootstrap server, agent card, đăng ký agent

## Cấu Hình

| Biến môi trường | Mô tả | Mặc định |
|---|---|---|
| `OPENROUTER_API_KEY` | OpenRouter API key của bạn | (bắt buộc) |
| `OPENROUTER_MODEL` | Định danh model | `anthropic/claude-sonnet-4-5` |
| `REGISTRY_URL` | URL của Registry service | `http://localhost:10000` |

Model có thể thay bằng bất kỳ model nào OpenRouter hỗ trợ, ví dụ `openai/gpt-4o`, `google/gemini-2.0-flash`.

## Sơ Đồ Tài Liệu

Thư mục `docs/` chứa các sơ đồ kiến trúc SVG:

| Sơ đồ | Chủ đề |
|---|---|
| `01_why_multiagent` | Vì sao dùng multi-agent thay vì LLM nguyên khối |
| `02_a2a_vs_traditional` | Giao thức A2A so với multi-agent truyền thống |
| `03_a2a_protocol` | Chi tiết kỹ thuật của giao thức A2A |
| `04_system_architecture` | Kiến trúc toàn hệ thống |
| `05_law_agent_graph` | Phân tích sâu StateGraph của Law Agent |
| `06_request_flow` | Luồng request end-to-end với trace propagation |
| `07_a2a_intro` | Giới thiệu giao thức A2A |
| `08_a2a_core_concepts` | Các khái niệm cốt lõi của A2A (Agent Cards, Tasks, Parts) |
| `09_a2a_interaction_flow` | Các pattern luồng tương tác A2A |
| `10_llm_roadmap` | Lộ trình phát triển LLM (Stages 1-5) |
