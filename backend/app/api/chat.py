import json

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.db.session import get_db
from app.models import Bot, Conversation, Message, User
from app.schemas.schemas import ChatIn, ConversationOut, MessageOut
from app.services import rag

router = APIRouter(prefix="/api/chat", tags=["chat"])

HISTORY_LIMIT = 8


def _sse(event: str, data: dict) -> str:
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


def _get_or_create_conversation(
    db: Session, bot_id: int, session_key: str, source: str
) -> Conversation:
    conv = (
        db.query(Conversation)
        .filter(Conversation.bot_id == bot_id, Conversation.session_key == session_key)
        .first()
    )
    if conv is None:
        conv = Conversation(bot_id=bot_id, session_key=session_key, source=source)
        db.add(conv)
        db.commit()
        db.refresh(conv)
    return conv


def _load_history(db: Session, conversation_id: int, limit: int = HISTORY_LIMIT) -> list[dict]:
    msgs = (
        db.query(Message)
        .filter(Message.conversation_id == conversation_id)
        .order_by(Message.id.desc())
        .limit(limit)
        .all()
    )
    msgs.reverse()
    return [{"role": m.role, "content": m.content} for m in msgs]


async def _stream_chat(db: Session, bot: Bot, payload: ChatIn, source: str):
    conversation = _get_or_create_conversation(db, bot.id, payload.session_key, source)
    history = _load_history(db, conversation.id)

    user_msg = Message(
        conversation_id=conversation.id, role="user", content=payload.message
    )
    db.add(user_msg)
    db.commit()
    db.refresh(user_msg)

    yield _sse("start", {"conversation_id": conversation.id, "user_message_id": user_msg.id})

    assistant_msg = None
    try:
        async for item in rag.stream_answer(
            bot=bot,
            question=payload.message,
            history=history,
            kb_ids=bot.kb_ids or [],
            tenant_id=bot.tenant_id,
        ):
            if item["type"] == "meta":
                yield _sse("meta", {"low_confidence": item.get("low_confidence", False)})
            elif item["type"] == "chunk":
                yield _sse("chunk", {"content": item["content"]})
            elif item["type"] == "done":
                citations = item.get("citations", [])
                assistant_msg = Message(
                    conversation_id=conversation.id,
                    role="assistant",
                    content=item["full_text"],
                    citations=citations,
                )
                db.add(assistant_msg)
                db.commit()
                db.refresh(assistant_msg)
                yield _sse(
                    "done",
                    {
                        "assistant_message_id": assistant_msg.id,
                        "citations": citations,
                        "low_confidence": len(citations) == 0,
                    },
                )
    except Exception as exc:  # noqa: BLE001
        db.rollback()
        yield _sse("error", {"message": f"生成失败: {exc}"})
        return


@router.post("/{bot_id}/stream")
async def chat_stream(
    bot_id: int,
    payload: ChatIn,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    bot = db.get(Bot, bot_id)
    if bot is None or bot.tenant_id != user.tenant_id:
        raise HTTPException(status_code=404, detail="智能体不存在")
    return StreamingResponse(
        _stream_chat(db, bot, payload, source="debug"),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("/conversations/{conversation_id}", response_model=ConversationOut)
def get_conversation(
    conversation_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    conv = db.get(Conversation, conversation_id)
    if conv is None:
        raise HTTPException(status_code=404, detail="会话不存在")
    bot = db.get(Bot, conv.bot_id)
    if bot is None or bot.tenant_id != user.tenant_id:
        raise HTTPException(status_code=404, detail="会话不存在")
    msgs = (
        db.query(Message)
        .filter(Message.conversation_id == conversation_id)
        .order_by(Message.id.asc())
        .all()
    )
    return ConversationOut(
        id=conv.id,
        bot_id=conv.bot_id,
        session_key=conv.session_key,
        source=conv.source,
        created_at=conv.created_at,
        messages=[
            MessageOut(
                id=m.id,
                role=m.role,
                content=m.content,
                citations=m.citations or [],
                feedback=m.feedback,
                created_at=m.created_at,
            )
            for m in msgs
        ],
    )


@router.post("/messages/{message_id}/feedback")
def feedback(
    message_id: int,
    action: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if action not in ("like", "dislike", "none"):
        raise HTTPException(status_code=400, detail="无效的反馈类型")
    msg = db.get(Message, message_id)
    if msg is None:
        raise HTTPException(status_code=404, detail="消息不存在")
    conv = db.get(Conversation, msg.conversation_id)
    bot = db.get(Bot, conv.bot_id) if conv else None
    if bot is None or bot.tenant_id != user.tenant_id:
        raise HTTPException(status_code=404, detail="消息不存在")
    msg.feedback = None if action == "none" else action
    db.commit()
    return {"ok": True}
