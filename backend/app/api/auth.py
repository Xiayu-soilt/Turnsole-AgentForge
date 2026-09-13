from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.core.security import create_access_token, hash_password, verify_password
from app.db.session import get_db
from app.models import Tenant, User
from app.schemas.schemas import LoginIn, RegisterIn, TokenOut

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/register", response_model=TokenOut)
def register(data: RegisterIn, db: Session = Depends(get_db)):
    exists = db.query(User).filter(User.username == data.username).first()
    if exists:
        raise HTTPException(status_code=400, detail="用户名已被注册")

    tenant = Tenant(name=data.company)
    db.add(tenant)
    db.flush()

    user = User(
        tenant_id=tenant.id,
        username=data.username,
        password_hash=hash_password(data.password),
        role="owner",
    )
    db.add(user)
    db.commit()

    token = create_access_token(user.id, tenant.id)
    return TokenOut(
        access_token=token,
        username=user.username,
        tenant_id=tenant.id,
        company=tenant.name,
    )


@router.post("/login", response_model=TokenOut)
def login(data: LoginIn, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == data.username).first()
    if user is None or not verify_password(data.password, user.password_hash):
        raise HTTPException(status_code=401, detail="用户名或密码错误")

    tenant = db.get(Tenant, user.tenant_id)
    token = create_access_token(user.id, user.tenant_id)
    return TokenOut(
        access_token=token,
        username=user.username,
        tenant_id=user.tenant_id,
        company=tenant.name if tenant else "",
    )


@router.get("/me")
def me(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    tenant = db.get(Tenant, user.tenant_id)
    return {
        "id": user.id,
        "username": user.username,
        "role": user.role,
        "tenant_id": user.tenant_id,
        "company": tenant.name if tenant else "",
    }
