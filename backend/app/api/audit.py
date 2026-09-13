from datetime import datetime

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.db.session import get_db
from app.models import Bot, Conversation, Message, User

router = APIRouter(prefix="/api/conversations", tags=["audit"])


class ConversationSummary(BaseModel):
    id: int
    bot_id: int
    bot_name: str
    session_key: str
    source: str
    created_at: datetime
    message_count: int
    last_message: str


class ConversationDetail(BaseModel):
    id: int
    bot_name: str
    session_key: str
    source: str
    created_at: datetime
    messages: list


@router.get("", response_model=list[ConversationSummary])
def list_conversations(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    limit: int = 100,
):
    bot_map = {
        b.id: b.name for b in db.query(Bot).filter(Bot.tenant_id == user.tenant_id).all()
    }
    if not bot_map:
        return []

    convs = (
        db.query(Conversation)
        .filter(Conversation.bot_id.in_(bot_map.keys()))
        .order_by(Conversation.id.desc())
        .limit(limit)
        .all()
    )

    result = []
    for conv in convs:
        msgs = (
            db.query(Message)
            .filter(Message.conversation_id == conv.id)
            .order_by(Message.id.desc())
            .all()
        )
        last = msgs[0].content[:60] if msgs else ""
        result.append(
            ConversationSummary(
                id=conv.id,
                bot_id=conv.bot_id,
                bot_name=bot_map.get(conv.bot_id, ""),
                session_key=conv.session_key,
                source=conv.source,
                created_at=conv.created_at,
                message_count=len(msgs),
                last_message=last,
            )
        )
    return result


@router.get("/{conversation_id}", response_model=ConversationDetail)
def conversation_detail(
    conversation_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    conv = db.get(Conversation, conversation_id)
    if conv is None:
        from fastapi import HTTPException

        raise HTTPException(status_code=404, detail="会话不存在")
    bot = db.get(Bot, conv.bot_id)
    if bot is None or bot.tenant_id != user.tenant_id:
        from fastapi import HTTPException

        raise HTTPException(status_code=404, detail="会话不存在")

    msgs = (
        db.query(Message)
        .filter(Message.conversation_id == conv.id)
        .order_by(Message.id.asc())
        .all()
    )

    return ConversationDetail(
        id=conv.id,
        bot_name=bot.name,
        session_key=conv.session_key,
        source=conv.source,
        created_at=conv.created_at,
        messages=[
            {
                "id": m.id,
                "role": m.role,
                "content": m.content,
                "citations": m.citations or [],
                "feedback": m.feedback,
                "created_at": m.created_at.isoformat(),
            }
            for m in msgs
        ],
    )
