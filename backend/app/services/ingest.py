from app.db.session import SessionLocal
from app.models import Document
from app.services import doc_parser, vector_store


def ingest_document(document_id: int) -> None:
    db = SessionLocal()
    try:
        doc = db.get(Document, document_id)
        if doc is None or doc.status in ("done", "processing"):
            return

        doc.status = "processing"
        doc.error = ""
        db.commit()

        try:
            text = doc_parser.parse_document(doc.file_path, doc.file_type)
            if not text.strip():
                raise ValueError("文档内容为空或无法解析")

            chunks = doc_parser.split_chunks(text)
            if not chunks:
                raise ValueError("切片结果为空")

            vector_store.add_chunks(
                tenant_id=doc.tenant_id,
                kb_id=doc.kb_id,
                doc_id=doc.id,
                chunks=chunks,
            )

            doc.status = "done"
            doc.chunk_count = len(chunks)
            db.commit()
        except Exception as exc:  # noqa: BLE001
            db.rollback()
            doc = db.get(Document, document_id)
            doc.status = "failed"
            doc.error = str(exc)[:2000]
            db.commit()
    finally:
        db.close()
