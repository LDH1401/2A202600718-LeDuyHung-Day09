# Báo Cáo Lab 9

## Phần 1: Direct LLM Calling

### 1. Lệnh đã chạy

```bash
uv run python stages/stage_1_direct_llm/main.py
```

### 2. Kết quả chạy Stage 1

Stage 1 đã chạy thành công. Chương trình gửi trực tiếp một system prompt và một câu hỏi của người dùng đến LLM, không dùng tools, không dùng RAG, không có memory và không có nguồn dữ liệu bên ngoài.

Câu hỏi mặc định trong file `stages/stage_1_direct_llm/main.py`:

```text
What are the legal consequences if a company breaches a non-disclosure agreement?
```

LLM trả lời rằng nếu một công ty vi phạm thỏa thuận bảo mật NDA, các hậu quả pháp lý có thể gồm:

- Bồi thường thiệt hại bằng tiền, gồm thiệt hại thực tế, thiệt hại phát sinh và liquidated damages nếu NDA có quy định.
- Lệnh cấm của tòa án, ví dụ temporary restraining order, preliminary injunction hoặc permanent injunction.
- Buộc hoàn trả lợi nhuận thu được từ việc sử dụng trái phép thông tin mật.
- Phí luật sư và án phí nếu hợp đồng có điều khoản fee-shifting.
- Punitive damages trong một số trường hợp cố ý hoặc ác ý.
- Trách nhiệm hình sự nếu hành vi liên quan đến bí mật thương mại.
- Thiệt hại về uy tín và quan hệ kinh doanh.

Kết quả này thể hiện đúng đặc điểm của Stage 1: LLM trả lời dựa trên knowledge có sẵn của model, không tra cứu database và không trích dẫn nguồn luật hiện hành.

### 3. Trả lời câu hỏi đọc code

#### Câu 1: LLM được khởi tạo như thế nào?

LLM được khởi tạo thông qua hàm `get_llm()` trong file `common/llm.py`. Hàm này trả về một object `ChatOpenAI`, nhưng endpoint được trỏ sang OpenRouter bằng:

```python
openai_api_base="https://openrouter.ai/api/v1"
```

Model được lấy từ biến môi trường `OPENROUTER_MODEL`; nếu không cấu hình thì dùng mặc định `anthropic/claude-sonnet-4-5`. API key được lấy từ `OPENROUTER_API_KEY`. Trong quá trình làm lab, em cũng giới hạn output bằng `OPENROUTER_MAX_TOKENS` để tránh lỗi thiếu credit trên OpenRouter.

#### Câu 2: Message được gửi đến LLM có cấu trúc gì?

Message gửi đến LLM là một list gồm hai message:

```python
messages = [
    SystemMessage(
        content=(
            "You are a legal expert. Provide a clear, concise analysis "
            "of the legal question asked. Keep your response under 300 words."
        )
    ),
    HumanMessage(content=QUESTION),
]
```

`SystemMessage` dùng để đặt vai trò và hướng dẫn cách trả lời cho LLM. `HumanMessage` chứa câu hỏi thật của người dùng.

#### Câu 3: Tại sao cần có `SystemMessage` và `HumanMessage`?

Cần tách `SystemMessage` và `HumanMessage` vì mỗi loại message có vai trò khác nhau:

- `SystemMessage` định nghĩa hành vi của LLM, ví dụ yêu cầu đóng vai chuyên gia pháp lý, trả lời rõ ràng, ngắn gọn và dưới 300 từ.
- `HumanMessage` chứa nội dung câu hỏi cụ thể mà người dùng muốn hỏi.

Cách tách này giúp prompt có cấu trúc rõ ràng hơn. Nếu sau này thay câu hỏi, ta chỉ cần đổi `HumanMessage` hoặc biến `QUESTION`, còn quy tắc ứng xử của model trong `SystemMessage` vẫn giữ nguyên.

### 4. Bài tập 1.1: Thay đổi câu hỏi

Yêu cầu của bài là sửa biến `QUESTION` thành một câu hỏi pháp lý khác rồi chạy lại chương trình. Ví dụ có thể thay bằng:

```python
QUESTION = "Nếu một công ty đơn phương chấm dứt hợp đồng lao động trái luật thì hậu quả pháp lý là gì?"
```

Khi thay câu hỏi, luồng xử lý của chương trình không đổi: vẫn gọi `get_llm()`, tạo `SystemMessage` và `HumanMessage`, sau đó gọi `llm.ainvoke(messages)`. Điểm thay đổi duy nhất là nội dung trong `HumanMessage`.

### 5. Bài tập 1.2: Thêm temperature control

Đã thêm tham số `temperature=0.3` vào hàm `get_llm()` trong `common/llm.py`:

```python
return ChatOpenAI(
    model=os.getenv("OPENROUTER_MODEL", "anthropic/claude-sonnet-4-5"),
    openai_api_key=os.getenv("OPENROUTER_API_KEY"),
    openai_api_base="https://openrouter.ai/api/v1",
    temperature=0.3,
    max_tokens=int(os.getenv("OPENROUTER_MAX_TOKENS", "1024")),
)
```

`temperature=0.3` làm output ổn định hơn, ít ngẫu nhiên hơn. Điều này phù hợp với bài lab pháp lý vì câu trả lời cần nhất quán, rõ ràng và tránh sáng tạo quá mức.

### 6. Nhận xét về Stage 1

Stage 1 là cách dùng LLM đơn giản nhất: gửi prompt và nhận câu trả lời. Ưu điểm là dễ hiểu, dễ chạy và phản hồi nhanh. Tuy nhiên, hạn chế là không có memory, không dùng tools, không tra cứu knowledge base, không kiểm chứng bằng dữ liệu bên ngoài và không đảm bảo trích dẫn luật/case law mới nhất.

## Phần 2: LLM + RAG & Tools

### 1. Lệnh đã chạy

```bash
uv run python stages/stage_2_rag_tools/main.py
```

### 2. Kết quả chạy Stage 2

Stage 2 đã chạy thành công sau khi em thêm code cho bài 2.1 và 2.2. Chương trình cho LLM nhận danh sách tools gồm `search_legal_database`, `calculate_damages` và tool mới `check_statute_of_limitations`. Sau đó LLM tự quyết định gọi tool phù hợp, chương trình thực thi tool, đưa kết quả tool trở lại cho LLM, rồi LLM tạo câu trả lời cuối cùng dựa trên dữ liệu đã truy xuất.

Câu hỏi được dùng:

```text
What are the legal consequences if a company breaches a non-disclosure agreement?
```

Ở lần chạy này, LLM yêu cầu gọi 2 tool call, cả hai đều là `search_legal_database` nhưng với query khác nhau:

```text
Tool: search_legal_database
Args: {'query': 'non-disclosure agreement breach legal consequences remedies'}

Tool: search_legal_database
Args: {'query': 'NDA breach damages injunctive relief confidentiality'}
```

Tool trả về kết quả từ knowledge base. Trong lần chạy này, kết quả hiển thị bắt đầu với entry `[ucc_breach]`, có thông tin về remedies for breach of contract theo UCC Article 2, expectation damages, consequential damages theo chuẩn `Hadley v. Baxendale`, specific performance, cover damages và thời hiệu thường là 4 năm theo UCC § 2-725. Câu trả lời cuối cùng cũng sử dụng thêm các thông tin liên quan đến NDA, DTSA, UTSA, liquidated damages, injunctive relief và Economic Espionage Act.

Sau khi nhận kết quả từ tool, LLM tạo câu trả lời cuối cùng có căn cứ hơn Stage 1. Câu trả lời nêu các hậu quả pháp lý chính khi công ty vi phạm NDA:

- Civil remedies như injunctive relief, monetary damages, unjust enrichment, consequential damages và liquidated damages nếu NDA có điều khoản này.
- Enhanced damages theo DTSA, có thể lên đến 2 lần actual damages nếu hành vi willful và malicious.
- Attorney's fees trong một số trường hợp.
- Bảo vệ theo luật liên bang DTSA và luật cấp bang như UTSA.
- Criminal liability theo Economic Espionage Act trong trường hợp nghiêm trọng liên quan đến trade secrets.
- Reputational damage, mất cơ hội kinh doanh, regulatory scrutiny và breach of fiduciary duties nếu officers/directors liên quan.

Kết quả này cho thấy Stage 2 tốt hơn Stage 1 vì câu trả lời được grounding bằng dữ liệu truy xuất từ knowledge base, có nhắc đến statute/case cụ thể như UCC, `Hadley v. Baxendale`, DTSA và Economic Espionage Act, thay vì chỉ dựa vào kiến thức sẵn có của model.

### 3. Bước 2: Phân tích code

#### Câu 1: Hàm `@tool` decorator được dùng ở đâu?

Trong file `stages/stage_2_rag_tools/main.py`, `@tool` được dùng trước các function mà ta muốn biến thành tool cho LLM gọi:

```python
@tool
def search_legal_database(query: str) -> str:
    ...

@tool
def calculate_damages(breach_type: str, contract_value: float) -> str:
    ...

@tool
def check_statute_of_limitations(case_type: str) -> str:
    ...
```

`search_legal_database` dùng để tìm thông tin liên quan trong legal knowledge base. `calculate_damages` dùng để ước tính thiệt hại dựa trên loại breach và giá trị hợp đồng. `check_statute_of_limitations` là tool mới của bài 2.2, dùng để trả về thời hiệu khởi kiện theo loại vụ án như `contract`, `tort` hoặc `property`. Nhờ `@tool`, các hàm Python này không chỉ là function bình thường nữa mà trở thành tools có schema để LLM có thể lựa chọn và gọi.

#### Câu 2: `LEGAL_KNOWLEDGE` được cấu trúc như thế nào?

`LEGAL_KNOWLEDGE` là một list gồm nhiều dictionary. Mỗi dictionary là một mẩu kiến thức pháp lý:

```python
{
    "id": "nda_trade_secret",
    "keywords": ["nda", "non-disclosure", "confidential", "trade secret", "agreement"],
    "text": (
        "NDA breaches may trigger both contractual and statutory liability..."
    ),
}
```

Mỗi entry có 3 phần chính:

- `id`: định danh của mẩu kiến thức, ví dụ `ucc_breach`, `nda_trade_secret`, `dtsa_details`.
- `keywords`: danh sách từ khóa dùng để match với query của người dùng hoặc query do LLM tạo ra.
- `text`: nội dung pháp lý chi tiết sẽ được trả về nếu entry phù hợp.

Trong demo này, knowledge base chưa phải vector database thật. Nó là một knowledge base mô phỏng, tìm kiếm bằng cách tách query thành các từ rồi so sánh overlap với `keywords` của từng entry.

Sau bài 2.1, em đã thêm entry mới `labor_law` vào `LEGAL_KNOWLEDGE` với các keyword như `lao động`, `sa thải`, `hợp đồng lao động`, `labor`, `termination`. Entry này chứa thông tin tóm tắt về Bộ luật Lao động Việt Nam 2019 và các trường hợp người sử dụng lao động có thể đơn phương chấm dứt hợp đồng.

#### Câu 3: LLM được bind với tools ra sao?

Đầu tiên, code gom các tool vào danh sách:

```python
TOOLS = [search_legal_database, calculate_damages, check_statute_of_limitations]
```

Sau đó, trong hàm `main()`, LLM được khởi tạo bằng `get_llm()` và bind với tools bằng `.bind_tools()`:

```python
llm = get_llm()
llm_with_tools = llm.bind_tools(TOOLS)
tool_map = {t.name: t for t in TOOLS}
```

`llm_with_tools` là phiên bản LLM đã biết mình có thể gọi các tools nào. Khi nhận câu hỏi, LLM có thể trả về `tool_calls` thay vì trả lời trực tiếp. Code sau đó dùng `tool_map` để tìm đúng function theo tên tool, thực thi tool, rồi append kết quả vào messages bằng `ToolMessage`.

### 4. Nhận xét về Stage 2

Stage 2 minh họa flow cơ bản của RAG và tool calling. So với Stage 1, câu trả lời đáng tin hơn vì có dữ liệu được truy xuất từ knowledge base. Tuy nhiên, orchestration vẫn còn thủ công: lập trình viên phải tự viết vòng lặp gọi tool, tự append `ToolMessage`, và demo chỉ xử lý một lượt tool call. Đây là lý do Stage 3 sẽ chuyển sang ReAct agent để agent tự động lặp Think → Act → Observe.

## Phần 3: Single Agent với ReAct

### 1. Lệnh đã chạy

```bash
uv run python stages/stage_3_single_agent/main.py
```

### 2. Kết quả chạy Stage 3

Stage 3 đã chạy thành công. Chương trình tạo một single agent theo ReAct loop để xử lý câu hỏi phức tạp gồm nhiều mảng pháp lý khác nhau: privacy, tax và compliance.

Câu hỏi được dùng:

```text
A tech startup with $5M revenue was caught sharing user data without consent and failed to pay taxes on overseas revenue. What are all the legal consequences?
```

Khi chạy, terminal có cảnh báo:

```text
LangGraphDeprecatedSinceV10: create_react_agent has been moved to `langchain.agents`.
```

Cảnh báo này không làm chương trình lỗi. Nó chỉ báo rằng `create_react_agent` trong `langgraph.prebuilt` đã deprecated và về sau nên đổi sang API mới từ `langchain.agents`.

### 3. Quan sát output ReAct

Agent tự động quyết định gọi nhiều tools liên tiếp. Ở bước đầu, agent gọi các tools sau:

```text
Tool: search_legal_database
Args: {'query': 'sharing user data without consent privacy violations penalties'}

Tool: search_legal_database
Args: {'query': 'failure to pay taxes on overseas revenue international tax evasion'}

Tool: search_legal_database
Args: {'query': 'tech startup regulatory compliance requirements data protection'}

Tool: check_compliance_requirements
Args: {'industry': 'technology', 'company_size': 'startup'}

Tool: calculate_penalty
Args: {'violation_type': 'data_privacy', 'severity': 'high', 'annual_revenue': 5000000}

Tool: calculate_penalty
Args: {'violation_type': 'tax_evasion', 'severity': 'high', 'annual_revenue': 5000000}
```

Sau đó agent quan sát kết quả từ từng tool:

- `search_legal_database` trả về thông tin về data privacy, gồm CCPA, GDPR, FTC Act Section 5, class action và quyền khởi kiện cá nhân theo CCPA.
- `search_legal_database` trả về thông tin về tax evasion, gồm 26 U.S.C. § 7201, civil fraud penalty 75%, back taxes, interest và trách nhiệm cá nhân của officers.
- `check_compliance_requirements` trả về các framework áp dụng cho startup công nghệ: CCPA/CPRA, GDPR nếu có EU users, FTC Act Section 5 và SOC 2.
- `calculate_penalty` ước tính penalty cho `data_privacy` mức high severity là `$500,000`, cộng thêm nguy cơ GDPR fines và class action exposure.
- `calculate_penalty` ước tính penalty cho `tax_evasion` mức high severity là `$500,000`, cộng thêm criminal charges và civil fraud penalty 75%.

Kết quả cuối cùng của agent là một bản phân tích tổng hợp gồm:

- Data privacy violations: CCPA, GDPR, FTC Act Section 5, class action, statutory damages.
- Tax evasion consequences: criminal exposure, civil fraud penalty, back taxes, FBAR/FATCA, personal liability của officers/directors.
- Compliance issues: CCPA/CPRA, GDPR, FTC Act Section 5, SOC 2.
- Operational consequences: mất niềm tin của nhà đầu tư, khó lấy SOC 2, SEC investigation nếu khai sai tài chính, reputational damage.
- Total financial exposure: tối thiểu khoảng `$1M+` base penalties, chưa tính back taxes, interest, class action settlements và legal defense costs.
- Recommended actions: thuê tax attorney, privacy counsel, internal investigation, notify users nếu bắt buộc, triển khai compliance program.

### 4. Bước 3: Phân tích code

#### Câu 1: `create_react_agent()` nằm ở đâu?

Trong file `stages/stage_3_single_agent/main.py`, `create_react_agent()` được import trong hàm `main()`:

```python
from langgraph.prebuilt import create_react_agent
```

Sau đó graph được tạo bằng:

```python
graph = create_react_agent(model=llm, tools=TOOLS, prompt=SYSTEM_PROMPT)
```

Hàm này là phần chính giúp tạo agent tự động theo ReAct pattern. Thay vì tự viết logic gọi tool từng bước, ta chỉ truyền vào model, danh sách tools và system prompt.

#### Câu 2: So sánh với Stage 2

Stage 2 vẫn phải orchestration thủ công. Code phải tự:

- Gọi LLM lần đầu.
- Kiểm tra `response.tool_calls`.
- Tìm đúng tool trong `tool_map`.
- Execute tool.
- Append `ToolMessage`.
- Gọi LLM lần hai để tổng hợp câu trả lời.

Stage 3 không cần viết manual tool loop như vậy. Agent tự quyết định cần gọi tool nào, gọi bao nhiêu tool, quan sát kết quả và tiếp tục xử lý cho đến khi có final answer. Vì vậy Stage 3 phù hợp hơn với câu hỏi phức tạp có nhiều phần như privacy + tax + compliance.

#### Câu 3: `agent_executor.invoke()` / gọi agent một lần hoạt động như thế nào?

Trong code hiện tại, demo dùng stream thay vì gọi `invoke()` trực tiếp:

```python
async for chunk in graph.astream(inputs, stream_mode="updates"):
    ...
```

Ý tưởng vẫn giống yêu cầu trong codelab: ta chỉ gửi input ban đầu một lần:

```python
inputs = {"messages": [{"role": "user", "content": QUESTION}]}
```

Sau đó agent tự chạy toàn bộ ReAct loop bên trong. Việc dùng `astream()` giúp in ra từng bước `THINK + ACT`, `OBSERVE` và `FINAL ANSWER`, nên dễ quan sát quá trình reasoning hơn.

### 5. Nhận xét về Stage 3

Stage 3 cải thiện rõ so với Stage 2 vì agent tự động chia câu hỏi phức tạp thành nhiều sub-task, tự gọi nhiều tools và tự tổng hợp kết quả. Tuy nhiên, hệ thống vẫn chỉ có một agent duy nhất xử lý mọi domain. Điều này tạo hạn chế: không có chuyên môn hóa riêng cho tax, privacy hay compliance, và các tool calls vẫn là bottleneck tuần tự. Stage 4 sẽ giải quyết bằng cách tách thành nhiều agent chuyên biệt chạy song song.
