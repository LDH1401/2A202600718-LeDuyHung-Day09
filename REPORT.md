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

## Phần 4: Multi-Agent In-Process

### 1. Lệnh đã chạy

Chạy demo Stage 4:

```bash
uv run python stages/stage_4_milti_agent/main.py
```

Chạy bài tập thêm Privacy Agent:

```bash
OPENROUTER_MAX_TOKENS=512 uv run python exercises/exercise_4_multiagent.py
```

Em dùng `OPENROUTER_MAX_TOKENS=512` khi chạy bài exercise vì OpenRouter báo thiếu credit nếu để `max_tokens=1024`.

### 2. Kết quả chạy demo Stage 4

Stage 4 chạy thành công. Câu hỏi test:

```text
If a company breaks a contract and avoids taxes, what are the legal and regulatory consequences?
```

Luồng graph được in ra:

```text
analyze_law -> check_routing -> [call_tax + call_compliance] -> aggregate -> END
```

Các node đã chạy:

- `analyze_law`: Lead attorney phân tích pháp lý tổng quát.
- `check_routing`: Router quyết định `needs_tax=True`, `needs_compliance=True`.
- `call_tax_specialist`: Tax specialist agent chạy.
- `call_compliance_specialist`: Compliance specialist agent chạy.
- `aggregate`: Tổng hợp các phân tích thành final answer.

Kết quả cuối cùng là báo cáo tổng hợp về việc công ty vi phạm hợp đồng và trốn thuế. Nội dung chính gồm:

- **Criminal consequences**: tax evasion theo 26 U.S.C. § 7201, nguy cơ phạt tù đến 5 năm, phạt tiền cho cá nhân/công ty, SOX violations, RICO nếu có pattern gian lận, trách nhiệm cá nhân của officers/directors.
- **Civil penalties**: civil fraud penalty 75% theo IRC § 6663, accuracy-related penalty, failure-to-file/pay penalties, interest, compensatory damages, consequential damages, liquidated damages, specific performance.
- **Corporate/regulatory consequences**: IRS audit, tax liens, asset seizures, SEC violations, officer/director bars, mất license, debarment khỏi government contracts, giảm credit rating, reputational damage.
- **Recommended actions**: thuê legal counsel, cân nhắc voluntary disclosure với IRS, remediation compliance, negotiate settlement, internal investigation.

Terminal cũng có cảnh báo deprecated:

```text
Importing Send from langgraph.constants is deprecated.
create_react_agent has been moved to `langchain.agents`.
```

Cảnh báo này không làm demo lỗi, nhưng cho biết về sau nên đổi import sang API mới.

### 3. Bước 2: Phân tích kiến trúc code

#### Câu 1: `class State(TypedDict)` / shared state nằm ở đâu?

Trong file demo, shared state được định nghĩa bằng `LegalState(TypedDict)`:

```python
class LegalState(TypedDict):
    question: str
    law_analysis: str
    needs_tax: bool
    needs_compliance: bool
    tax_result: Annotated[str, _last_wins]
    compliance_result: Annotated[str, _last_wins]
    final_answer: str
```

State này là dữ liệu chung đi qua toàn bộ graph. `question` là đầu vào, `law_analysis` là phân tích tổng quát, `needs_tax` và `needs_compliance` là cờ routing, `tax_result` và `compliance_result` là kết quả từ specialist agents, còn `final_answer` là câu trả lời cuối cùng.

`tax_result` và `compliance_result` dùng `Annotated[str, _last_wins]` để LangGraph xử lý việc nhiều nhánh song song ghi vào state.

#### Câu 2: Các agent functions nằm ở đâu?

Các function chính trong Stage 4 gồm:

- `analyze_law`: đóng vai lead attorney, phân tích pháp lý tổng quát.
- `check_routing`: dùng LLM để quyết định có cần tax/compliance specialist không.
- `call_tax_specialist`: tạo ReAct tax agent inline, dùng tool `search_tax_law`.
- `call_compliance_specialist`: tạo ReAct compliance agent inline, dùng tool `search_compliance_law`.
- `aggregate`: tổng hợp tất cả phân tích thành final answer.

Điểm khác Stage 3 là mỗi specialist có prompt riêng theo chuyên môn, thay vì một agent duy nhất xử lý mọi lĩnh vực.

#### Câu 3: `Send()` API dispatch parallel tasks như thế nào?

`Send()` được dùng trong hàm routing:

```python
def route_to_specialists(state: LegalState) -> list[Send]:
    sends: list[Send] = []
    if state.get("needs_tax"):
        sends.append(Send("call_tax_specialist", state))
    if state.get("needs_compliance"):
        sends.append(Send("call_compliance_specialist", state))
    if not sends:
        sends.append(Send("aggregate", state))
    return sends
```

Nếu câu hỏi cần cả tax và compliance, hàm này trả về hai `Send` objects. LangGraph sẽ dispatch hai nhánh `call_tax_specialist` và `call_compliance_specialist` song song, sau đó cả hai đều đi về `aggregate`.

#### Câu 4: `graph.add_node()` và `graph.add_edge()` hoạt động như thế nào?

Graph được tạo bằng `StateGraph(LegalState)`, sau đó add các node:

```python
graph.add_node("analyze_law", analyze_law)
graph.add_node("check_routing", check_routing)
graph.add_node("call_tax_specialist", call_tax_specialist)
graph.add_node("call_compliance_specialist", call_compliance_specialist)
graph.add_node("aggregate", aggregate)
```

Luồng điều khiển:

```python
graph.set_entry_point("analyze_law")
graph.add_edge("analyze_law", "check_routing")
graph.add_conditional_edges(
    "check_routing",
    route_to_specialists,
    ["call_tax_specialist", "call_compliance_specialist", "aggregate"],
)
graph.add_edge("call_tax_specialist", "aggregate")
graph.add_edge("call_compliance_specialist", "aggregate")
graph.add_edge("aggregate", END)
```

Như vậy graph luôn bắt đầu từ `analyze_law`, sau đó router quyết định đi sang specialist nào, rồi cuối cùng tổng hợp ở `aggregate`.

### 4. Bài tập 4.1 và 4.2: Thêm Privacy Agent

Em đã hoàn thành trong file `exercises/exercise_4_multiagent.py`.

Các thay đổi chính:

- Thêm routing keyword cho privacy:

```python
if any(kw in question_lower for kw in ["data", "privacy", "gdpr", "dữ liệu", "rò rỉ"]):
    tasks.append(Send("privacy_agent", state))
```

- Implement `privacy_agent`:

```python
def privacy_agent(state: State) -> dict:
    """Agent chuyên về bảo vệ dữ liệu cá nhân và GDPR."""
    llm = get_llm()
    prompt = f"""Bạn là chuyên gia về GDPR và luật bảo vệ dữ liệu cá nhân.

Câu hỏi: {state['question']}
Phân tích pháp lý: {state.get('law_analysis', 'N/A')}

Tập trung: GDPR, data protection, privacy rights, data breach, nghĩa vụ thông báo
cho người dùng/cơ quan quản lý, tiền phạt và biện pháp khắc phục."""

    response = llm.invoke([HumanMessage(content=prompt)])
    return {"privacy_analysis": response.content}
```

- Thêm `privacy_analysis` vào phần tổng hợp:

```python
if state.get("privacy_analysis"):
    sections.append(f"🔒 PHÂN TÍCH PRIVACY/GDPR:\n{state['privacy_analysis']}")
```

- Thêm node và edge cho privacy agent:

```python
graph.add_node("privacy_agent", privacy_agent)
graph.add_edge("privacy_agent", "aggregate_results")
```

Trong quá trình test, em cũng sửa graph routing: `check_routing` không nên là một node trả về `list[Send]`, vì node của LangGraph phải trả về `dict`. Cách đúng là dùng `check_routing` làm routing function trong `add_conditional_edges` sau `law_agent`:

```python
graph.add_conditional_edges(
    "law_agent",
    check_routing,
    ["tax_agent", "compliance_agent", "privacy_agent", "aggregate_results"],
)
```

### 5. Kết quả chạy bài tập Privacy Agent

Câu hỏi test:

```text
Nếu công ty bị rò rỉ dữ liệu khách hàng, hậu quả pháp lý và thuế là gì?
```

Bài exercise chạy thành công với:

```bash
OPENROUTER_MAX_TOKENS=512 uv run python exercises/exercise_4_multiagent.py
```

Kết quả cuối cùng bắt đầu bằng báo cáo:

```text
# BÁO CÁO PHÁP LÝ: HẬU QUẢ RÒ RỈ DỮ LIỆU KHÁCH HÀNG
```

Nội dung output xác nhận hệ thống đã tổng hợp được các hướng phân tích:

- Trách nhiệm pháp lý dân sự: bồi thường thiệt hại vật chất, tinh thần, lợi ích bị mất.
- Vi phạm hợp đồng với khách hàng: khách hàng có thể chấm dứt hợp đồng và yêu cầu bồi thường.
- Trách nhiệm hành chính theo Nghị định 13/2023/NĐ-CP về bảo vệ dữ liệu cá nhân.
- Nghĩa vụ khắc phục: thông báo sự cố, xóa dữ liệu thu thập trái phép, khôi phục tình trạng ban đầu.
- Phân tích privacy/GDPR được đưa vào luồng tổng hợp thông qua `privacy_agent`.

Do giới hạn token để tránh lỗi OpenRouter 402, phần final answer bị cắt ở cuối, nhưng chương trình đã exit code `0`, tức là graph chạy thành công và privacy agent đã được tích hợp đúng.

### 6. Nhận xét về Stage 4

Stage 4 tốt hơn Stage 3 vì hệ thống đã tách trách nhiệm cho nhiều agent chuyên môn hóa. Lead attorney phân tích tổng quát, router chọn specialist, tax/compliance/privacy agents xử lý từng domain riêng, rồi aggregator tổng hợp. `Send()` giúp các nhánh độc lập chạy song song, phù hợp với những câu hỏi nhiều mảng pháp lý. Hạn chế của Stage 4 là tất cả vẫn chạy trong cùng một process, chưa có HTTP service, chưa có A2A protocol và chưa có dynamic registry như Stage 5.

## Phần 5: Distributed A2A System

### 1. Lệnh đã chạy

Khởi động toàn bộ hệ thống:

```bash
uv run ./start_all.sh
```

Trong quá trình test thực tế, em chạy bằng môi trường venv và model rẻ hơn để tránh lỗi thiếu credit OpenRouter:

```bash
OPENROUTER_MODEL=openai/gpt-4o-mini OPENROUTER_MAX_TOKENS=256 uv run ./start_all.sh
```

Sau đó chạy client:

```bash
OPENROUTER_MODEL=openai/gpt-4o-mini OPENROUTER_MAX_TOKENS=256 uv run python test_client.py
```

### 2. Kết quả khởi động hệ thống

Stage 5 khởi động thành công 5 service độc lập:

```text
Registry:         http://localhost:10000
Customer Agent:   http://localhost:10100
Law Agent:        http://localhost:10101
Tax Agent:        http://localhost:10102
Compliance Agent: http://localhost:10103
```

Các agent đã tự đăng ký vào Registry:

```text
tax-agent          -> task: tax_question          -> http://localhost:10102
compliance-agent   -> task: compliance_question   -> http://localhost:10103
law-agent          -> task: legal_question        -> http://localhost:10101
customer-agent     -> entry point                 -> http://localhost:10100
```

Điều này xác nhận cơ chế **dynamic discovery**: các agent không cần hardcode URL của nhau trong luồng xử lý chính, mà đăng ký capability với Registry khi khởi động.

### 3. Kết quả chạy `test_client.py`

Câu hỏi test:

```text
If a company breaks a contract and avoids taxes, what are the legal and regulatory consequences?
```

Client kết nối được với Customer Agent:

```text
Connected to agent: Customer Agent v1.0.0
Sending request (this may take 30-60s while agents chain)...
```

Kết quả trả về có response từ hệ thống:

```text
RESPONSE:
. Legal Actions
The injured party may initiate a lawsuit against the breaching company...

Tax Evasion Consequences
Tax evasion involves deliberately misrepresenting or concealing information...
```

Do giới hạn `OPENROUTER_MAX_TOKENS=256`, response bị cắt ngắn ở cuối, nhưng request đã chạy qua đầy đủ các service và trả về HTTP 200.

### 4. Bài tập 5.1: Trace request flow

Trong logs, request được gắn `trace_id`:

```text
trace=570a5035-19f1-4c04-ae60-ec6fa5d19805
context=479a7ceb-4307-427e-9d7d-c4efc04260bc
```

Flow quan sát được:

```text
test_client.py
  -> Customer Agent :10100
  -> Registry discover("legal_question")
  -> Law Agent :10101
  -> Registry discover("tax_question")
  -> Registry discover("compliance_question")
  -> Tax Agent :10102
  -> Compliance Agent :10103
  -> Law Agent aggregate
  -> Customer Agent final response
```

Các log quan trọng:

```text
CustomerAgent executing ... trace=570a5035...
Customer delegate_to_legal_agent ... depth=0
Registry discovered law-agent for task legal_question
LawAgent executing ... trace=570a5035... depth=1
Routing decision: needs_tax=True needs_compliance=True
Registry discovered compliance-agent for task compliance_question
Registry discovered tax-agent for task tax_question
ComplianceAgent executing ... trace=570a5035... depth=2
TaxAgent executing ... trace=570a5035... depth=2
Tax Agent returned 724 chars
Compliance Agent returned 1252 chars
```

Như vậy `trace_id` được truyền xuyên suốt từ Customer Agent sang Law Agent rồi sang Tax/Compliance Agent. Đây là cơ chế quan trọng để debug hệ thống phân tán.

### 5. Bài tập 5.2: Test dynamic discovery khi Tax Agent bị dừng

Em dừng riêng Tax Agent, giữ các service còn lại:

```text
registry
compliance_agent
law_agent
customer_agent
```

Sau đó chạy lại:

```bash
OPENROUTER_MODEL=openai/gpt-4o-mini OPENROUTER_MAX_TOKENS=256 uv run python test_client.py
```

Kết quả: client vẫn nhận được response từ hệ thống. Trong logs, Law Agent vẫn hỏi Registry:

```text
Registry discovered tax-agent for task tax_question
```

Nhưng vì process Tax Agent đã bị dừng, khi Law Agent gọi endpoint `http://localhost:10102`, nhánh tax báo lỗi:

```text
call_tax failed: All connection attempts failed
```

Compliance Agent vẫn chạy thành công:

```text
ComplianceAgent executing ... depth=2
Compliance Agent returned 1260 chars
```

Sau đó Law Agent vẫn aggregate và Customer Agent vẫn trả response. Điều này cho thấy hệ thống có xử lý lỗi nhánh specialist: nếu Tax Agent unavailable, luồng tổng thể không sập hoàn toàn mà vẫn có thể trả lời dựa trên các phân tích còn lại. Tuy nhiên Registry hiện tại là in-memory registry đơn giản, nên nó vẫn còn record `tax-agent` dù service đã chết; hệ thống chưa có health check tự động để remove agent offline.

### 6. Bài tập 5.3: Modify agent behavior

Em đã sửa `tax_agent/graph.py` để Tax Agent trả lời ngắn gọn hơn. Đã thêm vào `TAX_SYSTEM_PROMPT`:

```text
Keep your response concise, under 120 words. Use short bullets and avoid
repeating points already covered by other agents.
```

Sau khi restart hệ thống và chạy lại `test_client.py`, logs cho thấy Tax Agent vẫn được gọi bình thường:

```text
TaxAgent executing ... depth=2
Tax Agent returned 724 chars
```

Việc sửa prompt này giúp Tax Agent tập trung hơn, tránh lặp lại phần đã được Law Agent hoặc Compliance Agent phân tích.

### 7. Nhận xét về Stage 5

Stage 5 khác Stage 4 ở chỗ mỗi agent là một service HTTP độc lập. Customer Agent, Law Agent, Tax Agent và Compliance Agent không gọi function trực tiếp trong cùng process nữa, mà giao tiếp qua A2A protocol. Registry đóng vai trò service discovery, cho phép agent tự đăng ký capability và được tìm theo task như `legal_question`, `tax_question`, `compliance_question`.

Ưu điểm của Stage 5:

- Kiến trúc phân tán, mỗi agent có thể deploy/scale riêng.
- Có dynamic discovery qua Registry.
- Có `trace_id` và `context_id` để debug request đi qua nhiều service.
- Khi một specialist bị lỗi, hệ thống vẫn có thể degrade thay vì dừng hoàn toàn.

Hạn chế quan sát được:

- Registry hiện tại lưu in-memory, chưa có persistence.
- Registry chưa tự health check/remove agent offline.
- Chạy full chain tốn nhiều LLM calls, nên dễ gặp lỗi OpenRouter 402 nếu API key còn ít credit.
- Một số API đang có deprecation warning, ví dụ endpoint `/.well-known/agent.json` và `A2AClient`.

## Bài Tập Cộng Điểm

### 1. HTML demo tương tác Agent

Em đã chuẩn bị file HTML demo:

```text
agent_visualization.html
```

File này minh họa luồng tương tác Stage 5:

```text
User / test_client.py
  -> Customer Agent
  -> Registry discover("legal_question")
  -> Law Agent
  -> Registry discover("tax_question", "compliance_question")
  -> Tax Agent + Compliance Agent chạy song song
  -> Law Agent aggregate
  -> Customer Agent
  -> User
```

HTML có 2 chế độ:

- **Offline animation**: có thể mở file trực tiếp trong browser và bấm `Play`, `Step`, `Reset` để xem từng bước.
- **Live mode hooks**: file đã có sẵn các hook `/api/events`, `/api/cases`, `/api/run` nếu sau này muốn nối thêm server SSE để stream event thật.

Trong HTML cũng có bảng latency benchmark:

```text
Full Stage 5: 17.37s
Optimized:    12.34s
Reduction:    5.03s (~29%)
```

### 2. Đo latency full Stage 5

Em thêm script đo latency:

```text
latency_benchmark.py
```

Lệnh đo baseline full Stage 5 qua Customer Agent:

```bash
OPENROUTER_MODEL=openai/gpt-4o-mini OPENROUTER_MAX_TOKENS=128 \
uv run python latency_benchmark.py --target customer --runs 1
```

Kết quả:

```text
Target: customer (Full Stage 5 via Customer Agent)
Run 1: latency=17.37s state=completed response_chars=618
Average latency: 17.37s
```

Vậy latency tổng thời gian trả lời 1 câu hỏi của hệ thống full Stage 5 là:

```text
17.37 giây
```

Lưu ý: để tránh lỗi thiếu credit OpenRouter, em đo bằng model `openai/gpt-4o-mini` và giới hạn `OPENROUTER_MAX_TOKENS=128`. Vì vậy response preview bị ngắn, nhưng A2A task state là `completed`.

### 3. Phương án giảm latency

Vấn đề của full Stage 5 là request phải đi qua Customer Agent trước. Customer Agent dùng LLM để xác định câu hỏi có cần legal specialist không, sau đó mới delegate sang Law Agent. Với các câu hỏi đã biết chắc là câu hỏi pháp lý, bước này tạo thêm:

- 1 HTTP/A2A hop qua Customer Agent.
- 1 LLM call để Customer Agent quyết định delegate.
- Một vòng final response formatting ở Customer Agent.

Phương án tối ưu:

```text
Nếu client đã biết câu hỏi là legal_question, gọi trực tiếp Law Agent :10101.
```

Luồng sau tối ưu:

```text
User / optimized client
  -> Law Agent
  -> Registry discover("tax_question", "compliance_question")
  -> Tax Agent + Compliance Agent
  -> Law Agent aggregate
  -> User
```

Cách này vẫn giữ multi-agent phân tán cho phần quan trọng nhất, nhưng bỏ qua Customer Agent classification/delegation khi không cần thiết.

### 4. Demo sau khi apply phương án giảm latency

Lệnh đo optimized path:

```bash
OPENROUTER_MODEL=openai/gpt-4o-mini OPENROUTER_MAX_TOKENS=128 \
uv run python latency_benchmark.py --target law --runs 1
```

Kết quả:

```text
Target: law (Optimized direct Law Agent path)
Run 1: latency=12.34s state=completed response_chars=661
Average latency: 12.34s
```

So sánh:

| Cách chạy | Latency |
|---|---:|
| Full Stage 5 qua Customer Agent | 17.37s |
| Optimized gọi trực tiếp Law Agent | 12.34s |
| Giảm được | 5.03s |

Tỷ lệ giảm:

```text
5.03 / 17.37 ≈ 28.96%
```

Kết luận: với câu hỏi đã được phân loại sẵn là legal question, gọi trực tiếp Law Agent giúp giảm khoảng **29% latency** trong lần đo này. Trade-off là client phải tự biết khi nào nên bypass Customer Agent; nếu câu hỏi người dùng chưa rõ domain, vẫn nên đi qua Customer Agent để routing an toàn hơn.
