import re
import shutil
import uuid
from pathlib import Path

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.core.config import settings
from app.db.session import get_db
from app.models import Document, KnowledgeBase, User
from app.schemas.schemas import AIDocCreate, DocOut, KBCreate, KBOut
from app.services import vector_store
from app.services.ingest import ingest_document

router = APIRouter(prefix="/api/kb", tags=["knowledge"])

ALLOWED_TYPES = {"pdf", "docx", "doc", "md", "txt", "csv", "log"}


@router.get("", response_model=list[KBOut])
def list_kbs(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    kbs = (
        db.query(KnowledgeBase)
        .filter(KnowledgeBase.tenant_id == user.tenant_id)
        .order_by(KnowledgeBase.id.desc())
        .all()
    )
    result = []
    for kb in kbs:
        docs = db.query(Document).filter(Document.kb_id == kb.id).all()
        result.append(
            KBOut(
                id=kb.id,
                name=kb.name,
                description=kb.description or "",
                created_at=kb.created_at,
                doc_count=len(docs),
                chunk_count=sum(d.chunk_count for d in docs if d.status == "done"),
            )
        )
    return result


@router.post("", response_model=KBOut)
def create_kb(
    data: KBCreate, user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    kb = KnowledgeBase(tenant_id=user.tenant_id, name=data.name, description=data.description)
    db.add(kb)
    db.commit()
    db.refresh(kb)
    return KBOut(
        id=kb.id, name=kb.name, description=kb.description or "", created_at=kb.created_at
    )


@router.delete("/{kb_id}")
def delete_kb(kb_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    kb = (
        db.query(KnowledgeBase)
        .filter(KnowledgeBase.id == kb_id, KnowledgeBase.tenant_id == user.tenant_id)
        .first()
    )
    if kb is None:
        raise HTTPException(status_code=404, detail="知识库不存在")

    docs = db.query(Document).filter(Document.kb_id == kb_id).all()
    for doc in docs:
        _safe_remove(doc.file_path)
    vector_store.delete_kb(user.tenant_id, kb_id)
    db.delete(kb)
    db.commit()
    return {"ok": True}


@router.get("/{kb_id}/docs", response_model=list[DocOut])
def list_docs(
    kb_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    kb = (
        db.query(KnowledgeBase)
        .filter(KnowledgeBase.id == kb_id, KnowledgeBase.tenant_id == user.tenant_id)
        .first()
    )
    if kb is None:
        raise HTTPException(status_code=404, detail="知识库不存在")
    docs = db.query(Document).filter(Document.kb_id == kb_id).order_by(Document.id.desc()).all()
    return [
        DocOut(
            id=d.id,
            kb_id=d.kb_id,
            filename=d.filename,
            file_type=d.file_type,
            size=d.size,
            status=d.status,
            chunk_count=d.chunk_count,
            error=d.error or "",
            created_at=d.created_at,
        )
        for d in docs
    ]


@router.post("/{kb_id}/docs", response_model=DocOut)
def upload_doc(
    kb_id: int,
    file: UploadFile,
    background: BackgroundTasks,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    kb = (
        db.query(KnowledgeBase)
        .filter(KnowledgeBase.id == kb_id, KnowledgeBase.tenant_id == user.tenant_id)
        .first()
    )
    if kb is None:
        raise HTTPException(status_code=404, detail="知识库不存在")

    filename = file.filename or "unnamed"
    suffix = Path(filename).suffix.lower().lstrip(".")
    if suffix not in ALLOWED_TYPES:
        raise HTTPException(status_code=400, detail=f"不支持的文件类型: .{suffix}（支持 PDF/Word/Markdown/TXT）")

    upload_dir = Path(settings.UPLOAD_DIR)
    upload_dir.mkdir(parents=True, exist_ok=True)
    saved_name = f"{uuid.uuid4().hex}.{suffix}" if suffix else f"{uuid.uuid4().hex}.txt"
    save_path = upload_dir / saved_name

    with open(save_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    size = save_path.stat().st_size
    doc = Document(
        kb_id=kb_id,
        tenant_id=user.tenant_id,
        filename=filename,
        file_path=str(save_path),
        file_type=suffix,
        size=size,
        status="pending",
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)

    background.add_task(ingest_document, doc.id)

    return DocOut(
        id=doc.id,
        kb_id=doc.kb_id,
        filename=doc.filename,
        file_type=doc.file_type,
        size=doc.size,
        status=doc.status,
        chunk_count=doc.chunk_count,
        error=doc.error or "",
        created_at=doc.created_at,
    )


@router.post("/{kb_id}/docs/ai", response_model=DocOut)
def create_ai_doc(
    kb_id: int,
    data: AIDocCreate,
    background: BackgroundTasks,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    kb = (
        db.query(KnowledgeBase)
        .filter(KnowledgeBase.id == kb_id, KnowledgeBase.tenant_id == user.tenant_id)
        .first()
    )
    if kb is None:
        raise HTTPException(status_code=404, detail="知识库不存在")

    upload_dir = Path(settings.UPLOAD_DIR)
    upload_dir.mkdir(parents=True, exist_ok=True)
    safe_title = re.sub(r'[\\/:*?"<>|]', "_", data.title.strip()) or "AI 文档"
    saved_name = f"{uuid.uuid4().hex}.md"
    save_path = upload_dir / saved_name
    save_path.write_text(data.content, encoding="utf-8")

    doc = Document(
        kb_id=kb_id,
        tenant_id=user.tenant_id,
        filename=f"{safe_title}.md",
        file_path=str(save_path),
        file_type="md",
        size=save_path.stat().st_size,
        status="pending",
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)

    background.add_task(ingest_document, doc.id)

    return DocOut(
        id=doc.id,
        kb_id=doc.kb_id,
        filename=doc.filename,
        file_type=doc.file_type,
        size=doc.size,
        status=doc.status,
        chunk_count=doc.chunk_count,
        error=doc.error or "",
        created_at=doc.created_at,
    )


@router.delete("/{kb_id}/docs/{doc_id}")
def delete_doc(
    kb_id: int, doc_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    doc = (
        db.query(Document)
        .filter(
            Document.id == doc_id,
            Document.kb_id == kb_id,
            Document.tenant_id == user.tenant_id,
        )
        .first()
    )
    if doc is None:
        raise HTTPException(status_code=404, detail="文档不存在")
    _safe_remove(doc.file_path)
    vector_store.delete_document(user.tenant_id, kb_id, doc_id)
    db.delete(doc)
    db.commit()
    return {"ok": True}


@router.post("/{kb_id}/docs/{doc_id}/retry", response_model=DocOut)
def retry_doc(
    kb_id: int, doc_id: int, background: BackgroundTasks,
    user: User = Depends(get_current_user), db: Session = Depends(get_db),
):
    doc = (
        db.query(Document)
        .filter(
            Document.id == doc_id,
            Document.kb_id == kb_id,
            Document.tenant_id == user.tenant_id,
        )
        .first()
    )
    if doc is None:
        raise HTTPException(status_code=404, detail="文档不存在")
    doc.status = "pending"
    db.commit()
    background.add_task(ingest_document, doc.id)
    db.refresh(doc)
    return DocOut(
        id=doc.id, kb_id=doc.kb_id, filename=doc.filename, file_type=doc.file_type,
        size=doc.size, status=doc.status, chunk_count=doc.chunk_count,
        error=doc.error or "", created_at=doc.created_at,
    )


def _safe_remove(path: str):
    try:
        Path(path).unlink(missing_ok=True)
    except OSError:
        pass
