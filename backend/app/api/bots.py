import secrets

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.db.session import get_db
from app.models import Bot, KnowledgeBase, User
from app.schemas.schemas import BotCreate, BotOut, BotUpdate

router = APIRouter(prefix="/api/bots", tags=["bots"])


def _to_out(bot: Bot) -> BotOut:
    return BotOut(
        id=bot.id,
        name=bot.name,
        avatar=bot.avatar or "",
        system_prompt=bot.system_prompt or "",
        welcome_message=bot.welcome_message or "",
        suggested_questions=bot.suggested_questions or [],
        temperature=bot.temperature,
        kb_ids=bot.kb_ids or [],
        is_published=bool(bot.is_published),
        publish_token=bot.publish_token or "",
        created_at=bot.created_at,
    )


@router.get("", response_model=list[BotOut])
def list_bots(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    bots = (
        db.query(Bot).filter(Bot.tenant_id == user.tenant_id).order_by(Bot.id.desc()).all()
    )
    return [_to_out(b) for b in bots]


@router.post("", response_model=BotOut)
def create_bot(data: BotCreate, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    _validate_kb_ids(data.kb_ids, user.tenant_id, db)
    bot = Bot(
        tenant_id=user.tenant_id,
        name=data.name,
        avatar=data.avatar,
        system_prompt=data.system_prompt,
        welcome_message=data.welcome_message,
        suggested_questions=data.suggested_questions,
        temperature=data.temperature,
        kb_ids=data.kb_ids,
    )
    db.add(bot)
    db.commit()
    db.refresh(bot)
    return _to_out(bot)


@router.get("/{bot_id}", response_model=BotOut)
def get_bot(bot_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    bot = _get_owned(bot_id, user, db)
    return _to_out(bot)


@router.put("/{bot_id}", response_model=BotOut)
def update_bot(
    bot_id: int,
    data: BotUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    bot = _get_owned(bot_id, user, db)
    updates = data.model_dump(exclude_unset=True)
    if "kb_ids" in updates:
        _validate_kb_ids(updates["kb_ids"], user.tenant_id, db)
    for key, value in updates.items():
        setattr(bot, key, value)
    db.commit()
    db.refresh(bot)
    return _to_out(bot)


@router.delete("/{bot_id}")
def delete_bot(bot_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    bot = _get_owned(bot_id, user, db)
    db.delete(bot)
    db.commit()
    return {"ok": True}


@router.post("/{bot_id}/publish")
def publish_bot(bot_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    bot = _get_owned(bot_id, user, db)
    if not bot.kb_ids:
        raise HTTPException(status_code=400, detail="请先为智能体绑定至少一个知识库")
    if not bot.publish_token:
        bot.publish_token = secrets.token_urlsafe(24)
    bot.is_published = True
    db.commit()
    return {"ok": True, "publish_token": bot.publish_token}


@router.post("/{bot_id}/unpublish")
def unpublish_bot(bot_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    bot = _get_owned(bot_id, user, db)
    bot.is_published = False
    db.commit()
    return {"ok": True}


def _get_owned(bot_id: int, user: User, db: Session) -> Bot:
    bot = db.get(Bot, bot_id)
    if bot is None or bot.tenant_id != user.tenant_id:
        raise HTTPException(status_code=404, detail="智能体不存在")
    return bot


def _validate_kb_ids(kb_ids: list[int], tenant_id: int, db: Session):
    if not kb_ids:
        return
    owned = (
        db.query(KnowledgeBase.id)
        .filter(KnowledgeBase.id.in_(kb_ids), KnowledgeBase.tenant_id == tenant_id)
        .all()
    )
    if len(owned) != len(set(kb_ids)):
        raise HTTPException(status_code=400, detail="包含无权限或无效的知识库")
