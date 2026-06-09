"""Improve Day08 RAG answer agent with a Supervisor-Workers pattern.

The original Day08 pipeline is a single retrieval/generation flow. This file
keeps the RAG idea but splits the work into one supervisor and three workers:

1. retrieval_worker: finds relevant Day08 legal/news evidence
2. legal_analysis_worker: extracts legal findings from the selected evidence
3. citation_risk_worker: prepares citations and practical recommendations

The implementation is deterministic and offline so the assignment can be run
without an OpenRouter key.
"""

from __future__ import annotations

import argparse
import re
from dataclasses import dataclass
from operator import add
from typing import Annotated, TypedDict

from langgraph.graph import END, START, StateGraph
from langgraph.types import Send


@dataclass(frozen=True)
class LegalDocument:
    """Small local document record used as a Day08-style knowledge base."""

    doc_id: str
    title: str
    source: str
    keywords: tuple[str, ...]
    content: str


KNOWLEDGE_BASE = [
    LegalDocument(
        doc_id="drug_law_2021",
        title="Luật Phòng, chống ma túy 2021",
        source="Luật số 73/2021/QH15",
        keywords=("ma túy", "phòng chống", "cai nghiện", "quản lý", "người sử dụng"),
        content=(
            "Luật Phòng, chống ma túy 2021 quy định trách nhiệm phòng ngừa, phát hiện, "
            "ngăn chặn tệ nạn ma túy; quản lý người sử dụng trái phép chất ma túy; "
            "và tổ chức cai nghiện ma túy tự nguyện hoặc bắt buộc theo điều kiện luật định."
        ),
    ),
    LegalDocument(
        doc_id="criminal_code_drug",
        title="Bộ luật Hình sự 2015 sửa đổi 2017 - tội phạm ma túy",
        source="Chương XX Bộ luật Hình sự",
        keywords=("hình sự", "tàng trữ", "mua bán", "vận chuyển", "ma túy", "trái phép"),
        content=(
            "Các hành vi tàng trữ, vận chuyển, mua bán hoặc chiếm đoạt trái phép chất ma túy "
            "có thể bị truy cứu trách nhiệm hình sự. Mức hình phạt phụ thuộc loại chất, "
            "khối lượng, vai trò của người phạm tội và các tình tiết tăng nặng hoặc giảm nhẹ."
        ),
    ),
    LegalDocument(
        doc_id="rehab_process",
        title="Quy trình cai nghiện ma túy",
        source="Luật Phòng, chống ma túy 2021 và văn bản hướng dẫn",
        keywords=("cai nghiện", "bắt buộc", "tự nguyện", "gia đình", "cộng đồng"),
        content=(
            "Người nghiện ma túy có thể cai nghiện tự nguyện tại gia đình, cộng đồng hoặc "
            "cơ sở cai nghiện. Biện pháp cai nghiện bắt buộc được áp dụng khi có đủ căn cứ "
            "theo luật và phải bảo đảm trình tự, hồ sơ, quyền của người bị áp dụng biện pháp."
        ),
    ),
    LegalDocument(
        doc_id="news_artist_drug",
        title="Tin tức nghệ sĩ liên quan tới ma túy",
        source="Bộ dữ liệu tin tức Day08",
        keywords=("nghệ sĩ", "bị bắt", "sử dụng", "ma túy", "tin tức", "showbiz"),
        content=(
            "Các bài báo trong bộ dữ liệu Day08 thường chỉ là nguồn sự kiện ban đầu. Khi "
            "trả lời về cá nhân cụ thể, hệ thống cần phân biệt thông tin báo chí với kết luận "
            "pháp lý chính thức và tránh khẳng định vượt quá bằng chứng đã truy xuất."
        ),
    ),
    LegalDocument(
        doc_id="rag_citation_rule",
        title="Nguyên tắc trả lời RAG có citation",
        source="Day08 Task 10 - Generation Có Citation",
        keywords=("rag", "citation", "nguồn", "xác minh", "trích dẫn"),
        content=(
            "Câu trả lời RAG chỉ nên dùng thông tin trong context đã truy xuất. Nếu context "
            "không đủ bằng chứng, hệ thống phải nói rõ là không thể xác minh thay vì suy đoán."
        ),
    ),
]

DOCS_BY_ID = {doc.doc_id: doc for doc in KNOWLEDGE_BASE}


class AgentState(TypedDict):
    question: str
    selected_doc_ids: list[str]
    supervisor_plan: str
    retrieved_docs: Annotated[list[dict], add]
    legal_findings: Annotated[list[str], add]
    citation_notes: Annotated[list[str], add]
    recommendations: Annotated[list[str], add]
    worker_trace: Annotated[list[str], add]
    final_answer: str


def _tokenize(text: str) -> set[str]:
    return set(re.findall(r"[\wÀ-ỹ]+", text.lower(), flags=re.UNICODE))


def _score_document(question: str, doc: LegalDocument) -> int:
    question_lower = question.lower()
    keyword_score = sum(3 for keyword in doc.keywords if keyword in question_lower)
    token_score = len(_tokenize(question) & _tokenize(doc.content))
    return keyword_score + token_score


def _select_documents(question: str, top_k: int = 3) -> list[LegalDocument]:
    scored = [(_score_document(question, doc), doc) for doc in KNOWLEDGE_BASE]
    scored.sort(key=lambda item: item[0], reverse=True)
    selected = [doc for score, doc in scored if score > 0][:top_k]
    return selected or [DOCS_BY_ID["rag_citation_rule"]]


def _shorten(text: str, max_chars: int = 220) -> str:
    normalized = re.sub(r"\s+", " ", text).strip()
    if len(normalized) <= max_chars:
        return normalized
    return normalized[:max_chars].rsplit(" ", 1)[0] + "..."


def supervisor(state: AgentState) -> dict:
    """Plan the work and decide which evidence each worker should use."""
    selected_docs = _select_documents(state["question"])
    selected_ids = [doc.doc_id for doc in selected_docs]
    titles = ", ".join(doc.title for doc in selected_docs)
    plan = (
        "Supervisor chọn tài liệu liên quan, sau đó giao 3 workers chạy song song: "
        "retrieval_worker lấy evidence, legal_analysis_worker rút ra vấn đề pháp lý, "
        "citation_risk_worker chuẩn bị citation và khuyến nghị. "
        f"Tài liệu được chọn: {titles}."
    )
    return {
        "selected_doc_ids": selected_ids,
        "supervisor_plan": plan,
        "worker_trace": ["supervisor: planned retrieval, legal analysis, citation/risk workers"],
    }


def dispatch_workers(state: AgentState) -> list[Send]:
    """Fan out to three workers after the supervisor has created a plan."""
    return [
        Send("retrieval_worker", state),
        Send("legal_analysis_worker", state),
        Send("citation_risk_worker", state),
    ]


def retrieval_worker(state: AgentState) -> dict:
    """Retrieve Day08-style evidence snippets for the selected documents."""
    docs = [DOCS_BY_ID[doc_id] for doc_id in state["selected_doc_ids"]]
    retrieved = [
        {
            "doc_id": doc.doc_id,
            "title": doc.title,
            "source": doc.source,
            "score": _score_document(state["question"], doc),
            "content": doc.content,
        }
        for doc in docs
    ]
    return {
        "retrieved_docs": retrieved,
        "worker_trace": [f"retrieval_worker: returned {len(retrieved)} evidence chunks"],
    }


def legal_analysis_worker(state: AgentState) -> dict:
    """Extract legal findings from the supervisor-selected evidence."""
    docs = [DOCS_BY_ID[doc_id] for doc_id in state["selected_doc_ids"]]
    findings = []
    for doc in docs:
        findings.append(f"{doc.title}: {_shorten(doc.content)} [{doc.source}]")
    return {
        "legal_findings": findings,
        "worker_trace": [f"legal_analysis_worker: created {len(findings)} legal findings"],
    }


def citation_risk_worker(state: AgentState) -> dict:
    """Prepare citations and conservative recommendations."""
    docs = [DOCS_BY_ID[doc_id] for doc_id in state["selected_doc_ids"]]
    citations = [f"[{doc.title} | {doc.source}]" for doc in docs]
    recommendations = [
        "Chỉ kết luận dựa trên tài liệu đã truy xuất; nếu thiếu dữ kiện thì nêu rõ giới hạn.",
        "Ưu tiên kiểm tra điều luật/văn bản gốc trước khi đưa ra kết luận pháp lý cuối cùng.",
    ]
    if any("nghệ sĩ" in doc.keywords or "tin tức" in doc.keywords for doc in docs):
        recommendations.append(
            "Với nguồn báo chí, cần phân biệt cáo buộc/sự kiện báo chí với bản án hoặc quyết định chính thức."
        )
    return {
        "citation_notes": citations,
        "recommendations": recommendations,
        "worker_trace": [f"citation_risk_worker: prepared {len(citations)} citations"],
    }


def aggregate_results(state: AgentState) -> dict:
    """Combine worker outputs into one final Day08-style RAG answer."""
    if not state.get("legal_findings"):
        answer = "Tôi không thể xác minh thông tin này từ nguồn hiện có."
    else:
        answer_parts = [
            "# Kết quả Supervisor-Workers RAG",
            "",
            f"**Câu hỏi:** {state['question']}",
            "",
            "## Kế hoạch của Supervisor",
            state["supervisor_plan"],
            "",
            "## Phân tích từ Workers",
        ]
        answer_parts.extend(f"- {finding}" for finding in state["legal_findings"])
        answer_parts.extend(
            [
                "",
                "## Khuyến nghị",
                *[f"- {item}" for item in state["recommendations"]],
                "",
                "## Nguồn đã dùng",
                *[f"- {citation}" for citation in state["citation_notes"]],
                "",
                "## Trace",
                *[f"- {event}" for event in state["worker_trace"]],
            ]
        )
        answer = "\n".join(answer_parts)

    return {"final_answer": answer}


def build_graph():
    """Build the Supervisor-Workers graph."""
    graph = StateGraph(AgentState)
    graph.add_node("supervisor", supervisor)
    graph.add_node("retrieval_worker", retrieval_worker)
    graph.add_node("legal_analysis_worker", legal_analysis_worker)
    graph.add_node("citation_risk_worker", citation_risk_worker)
    graph.add_node("aggregate_results", aggregate_results)

    graph.add_edge(START, "supervisor")
    graph.add_conditional_edges(
        "supervisor",
        dispatch_workers,
        ["retrieval_worker", "legal_analysis_worker", "citation_risk_worker"],
    )
    graph.add_edge("retrieval_worker", "aggregate_results")
    graph.add_edge("legal_analysis_worker", "aggregate_results")
    graph.add_edge("citation_risk_worker", "aggregate_results")
    graph.add_edge("aggregate_results", END)
    return graph.compile()


def run(question: str) -> dict:
    graph = build_graph()
    initial_state: AgentState = {
        "question": question,
        "selected_doc_ids": [],
        "supervisor_plan": "",
        "retrieved_docs": [],
        "legal_findings": [],
        "citation_notes": [],
        "recommendations": [],
        "worker_trace": [],
        "final_answer": "",
    }
    return graph.invoke(initial_state)


def main() -> None:
    parser = argparse.ArgumentParser(description="Day08 Supervisor-Workers RAG assignment")
    parser.add_argument(
        "question",
        nargs="?",
        default="Hình phạt cho hành vi tàng trữ trái phép chất ma túy là gì?",
        help="Question to ask the Supervisor-Workers agent",
    )
    args = parser.parse_args()
    result = run(args.question)
    print(result["final_answer"])


if __name__ == "__main__":
    main()
