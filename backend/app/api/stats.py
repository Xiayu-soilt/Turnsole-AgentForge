from datetime import datetime, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.db.session import get_db
from app.models import Bot, Conversation, Document, KnowledgeBase, Message, User
from app.schemas.schemas import StatsOut

router = APIRouter(prefix="/api/stats", tags=["stats"])


@router.get("", response_model=StatsOut)
def dashboard(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    tid = user.tenant_id

    bot_ids = [b.id for b in db.query(Bot.id).filter(Bot.tenant_id == tid).all()]
    conv_ids = (
        [c.id for c in db.query(Conversation.id).filter(Conversation.bot_id.in_(bot_ids)).all()]
        if bot_ids
        else []
    )

    total_conversations = len(conv_ids)
    total_messages = 0
    total_user_messages = 0
    total_likes = 0
    total_dislikes = 0
    cited_messages = 0
    assistant_messages = 0
    hot_counter: dict[str, int] = {}

    if conv_ids:
        msgs = (
            db.query(Message)
            .filter(Message.conversation_id.in_(conv_ids))
            .order_by(Message.id.asc())
            .all()
        )
        total_messages = len(msgs)
        for m in msgs:
            if m.role == "user":
                total_user_messages += 1
                key = m.content.strip()[:40]
                hot_counter[key] = hot_counter.get(key, 0) + 1
            else:
                assistant_messages += 1
                if m.citations:
                    cited_messages += 1
            if m.feedback == "like":
                total_likes += 1
            elif m.feedback == "dislike":
                total_dislikes += 1

    hit_rate = (cited_messages / assistant_messages) if assistant_messages else 0.0

    doc_count = (
        db.query(func.count(Document.id))
        .filter(Document.tenant_id == tid, Document.status == "done")
        .scalar()
    ) or 0
    chunk_count = (
        db.query(func.sum(Document.chunk_count)).filter(Document.tenant_id == tid).scalar()
    ) or 0
    bot_count = db.query(func.count(Bot.id)).filter(Bot.tenant_id == tid).scalar() or 0
    kb_count = db.query(func.count(KnowledgeBase.id)).filter(KnowledgeBase.tenant_id == tid).scalar() or 0

    daily = _daily_stats(db, conv_ids)
    hot_questions = [
        {"question": q, "count": c}
        for q, c in sorted(hot_counter.items(), key=lambda kv: kv[1], reverse=True)[:10]
    ]

    return StatsOut(
        total_conversations=total_conversations,
        total_messages=total_messages,
        total_user_messages=total_user_messages,
        total_likes=total_likes,
        total_dislikes=total_dislikes,
        hit_rate=round(hit_rate, 4),
        doc_count=doc_count,
        chunk_count=chunk_count,
        bot_count=bot_count,
        kb_count=kb_count,
        daily=daily,
        hot_questions=hot_questions,
    )


def _daily_stats(db: Session, conv_ids: list[int], days: int = 14) -> list[dict]:
    result = []
    today = datetime.utcnow().date()
    for offset in range(days - 1, -1, -1):
        day = today - timedelta(days=offset)
        day_start = datetime(day.year, day.month, day.day)
        day_end = day_start + timedelta(days=1)
        if conv_ids:
            count = (
                db.query(func.count(Message.id))
                .filter(
                    Message.conversation_id.in_(conv_ids),
                    Message.role == "user",
                    Message.created_at >= day_start,
                    Message.created_at < day_end,
                )
                .scalar()
            ) or 0
        else:
            count = 0
        result.append({"date": day.isoformat(), "count": count})
    return result
