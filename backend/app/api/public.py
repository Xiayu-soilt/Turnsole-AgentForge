import json

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models import Bot, Tenant
from app.schemas.schemas import ChatIn
from app.api.chat import _stream_chat

router = APIRouter(prefix="/api/public", tags=["public"])


@router.get("/agents")
def list_public_agents(db: Session = Depends(get_db)):
    bots = (
        db.query(Bot)
        .filter(Bot.is_published == True)  # noqa: E712
        .order_by(Bot.id.desc())
        .all()
    )
    tenant_ids = {b.tenant_id for b in bots}
    tenants = {}
    if tenant_ids:
        for t in db.query(Tenant).filter(Tenant.id.in_(tenant_ids)).all():
            tenants[t.id] = t.name
    return [
        {
            "publish_token": b.publish_token,
            "name": b.name,
            "welcome_message": b.welcome_message or "你好，请问有什么可以帮您？",
            "company": tenants.get(b.tenant_id, ""),
            "kb_count": len(b.kb_ids or []),
        }
        for b in bots
    ]


@router.get("/{token}/info")
def public_info(token: str, db: Session = Depends(get_db)):
    bot = (
        db.query(Bot)
        .filter(Bot.publish_token == token, Bot.is_published == True)  # noqa: E712
        .first()
    )
    if bot is None:
        raise HTTPException(status_code=404, detail="智能体不存在或未发布")
    return {
        "name": bot.name,
        "avatar": bot.avatar or "",
        "welcome_message": bot.welcome_message or "你好，请问有什么可以帮您？",
        "suggested_questions": bot.suggested_questions or [],
    }


@router.post("/{token}/stream")
async def public_stream(token: str, payload: ChatIn, db: Session = Depends(get_db)):
    bot = (
        db.query(Bot)
        .filter(Bot.publish_token == token, Bot.is_published == True)  # noqa: E712
        .first()
    )
    if bot is None:
        raise HTTPException(status_code=404, detail="智能体不存在或未发布")
    return StreamingResponse(
        _stream_chat(db, bot, payload, source="web"),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )
