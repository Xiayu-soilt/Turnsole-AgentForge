import json
import re
from typing import AsyncIterator

from app.core.config import settings
from app.services import vector_store

DEFAULT_SYSTEM = (
    "你是企业智能助手，必须基于提供的【知识库片段】回答问题。\n"
    "规则：\n"
    "1. 回答内容优先依据知识库片段，并在句尾用 [1] [2] 标注引用来源编号。\n"
    "2. 如果知识库片段不足以回答问题，诚实说明知识库中暂无相关内容，"
    "不要编造事实，可以建议用户咨询相关人员。\n"
    "3. 用简洁、专业、友好的中文回答。"
)


def _build_context(hits: list[dict]) -> str:
    if not hits:
        return "（本次检索未命中任何知识库片段）"
    parts = []
    for i, hit in enumerate(hits, start=1):
        content = hit["content"][:800]
        parts.append(f"[{i}] {content}")
    return "\n\n".join(parts)


def _default_prompt(bot) -> str:
    base = bot.system_prompt.strip() if bot.system_prompt else ""
    if base:
        return (
            f"{base}\n\n"
            "同时遵守：回答基于提供的【知识库片段】，句尾用 [1] [2] 标注引用；"
            "知识库片段不足以回答时诚实说明，不要编造。"
        )
    return DEFAULT_SYSTEM


def _filter_hits(hits: list[dict], threshold: float | None = None) -> list[dict]:
    threshold = threshold if threshold is not None else settings.SCORE_THRESHOLD
    return [h for h in hits if h["score"] >= threshold]


def build_messages(bot, question: str, history: list[dict], kb_ids: list[int], tenant_id: int):
    hits = vector_store.query_chunks(tenant_id=tenant_id, kb_ids=kb_ids, query=question)
    filtered = _filter_hits(hits)

    context = _build_context(filtered)
    system = _default_prompt(bot)

    messages = [{"role": "system", "content": system + "\n\n【知识库片段】\n" + context}]
    for h in history[-8:]:
        if h.get("role") in ("user", "assistant") and h.get("content"):
            messages.append({"role": h["role"], "content": h["content"]})
    messages.append({"role": "user", "content": question})

    citations = []
    seen_docs = {}
    for i, hit in enumerate(filtered, start=1):
        doc_id = hit.get("doc_id")
        citations.append(
            {
                "index": i,
                "doc_id": doc_id,
                "content": hit["content"],
                "score": hit["score"],
                "filename": seen_docs.get(doc_id, ""),
            }
        )
    return messages, citations, filtered


async def stream_answer(
    bot, question: str, history: list[dict], kb_ids: list[int], tenant_id: int
) -> AsyncIterator[dict]:
    from app.services.llm import get_llm

    messages, citations, hits = build_messages(
        bot=bot, question=question, history=history, kb_ids=kb_ids, tenant_id=tenant_id
    )

    low_confidence = len(hits) == 0
    if low_confidence:
        yield {"type": "meta", "citations": [], "low_confidence": True}

    llm = get_llm(temperature=bot.temperature, streaming=True)
    buffer = []
    async for chunk in llm.astream(messages):
        content = chunk.content
        if not content:
            continue
        if isinstance(content, list):
            content = "".join(
                c.get("text", "") if isinstance(c, dict) else str(c) for c in content
            )
        buffer.append(content)
        yield {"type": "chunk", "content": content}

    full_text = "".join(buffer)
    citations = _attach_filenames(citations)
    yield {"type": "done", "citations": citations, "full_text": full_text}


def _attach_filenames(citations: list[dict]) -> list[dict]:
    doc_ids = {c["doc_id"] for c in citations if c.get("doc_id")}
    if not doc_ids:
        return citations
    from app.db.session import SessionLocal
    from app.models import Document

    db = SessionLocal()
    try:
        rows = db.query(Document.id, Document.filename).filter(
            Document.id.in_(doc_ids)
        ).all()
        name_map = {r.id: r.filename for r in rows}
        for c in citations:
            c["filename"] = name_map.get(c.get("doc_id"), "")
        return citations
    finally:
        db.close()


def extract_citation_refs(text: str) -> list[int]:
    return [int(m) for m in re.findall(r"\[(\d+)\]", text)]


def dumps(obj) -> str:
    return json.dumps(obj, ensure_ascii=False)
