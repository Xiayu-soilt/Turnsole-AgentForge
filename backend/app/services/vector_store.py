import uuid

import chromadb

from app.core.config import settings

_client = None


def get_client() -> chromadb.ClientAPI:
    global _client
    if _client is None:
        _client = chromadb.PersistentClient(path=settings.CHROMA_DIR)
    return _client


def tenant_collection(tenant_id: int):
    client = get_client()
    return client.get_or_create_collection(
        name=f"tenant_{tenant_id}",
        metadata={"hnsw:space": "cosine"},
    )


def add_chunks(tenant_id: int, kb_id: int, doc_id: int, chunks: list[str]) -> list[str]:
    if not chunks:
        return []
    from app.services.embeddings import embed_texts

    vectors = embed_texts(chunks)
    ids = [f"doc{doc_id}_chunk{i}_{uuid.uuid4().hex[:8]}" for i in range(len(chunks))]
    collection = tenant_collection(tenant_id)
    collection.add(
        ids=ids,
        embeddings=vectors,
        documents=chunks,
        metadatas=[
            {"kb_id": kb_id, "doc_id": doc_id, "chunk_index": i}
            for i in range(len(chunks))
        ],
    )
    return ids


def query_chunks(
    tenant_id: int,
    kb_ids: list[int],
    query: str,
    top_k: int | None = None,
) -> list[dict]:
    from app.services.embeddings import embed_query

    top_k = top_k or settings.TOP_K
    collection = tenant_collection(tenant_id)
    if collection.count() == 0:
        return []

    where = None
    if kb_ids:
        where = {"kb_id": {"$in": kb_ids}}

    result = collection.query(
        query_embeddings=[embed_query(query)],
        n_results=min(top_k, collection.count()),
        where=where,
        include=["documents", "metadatas", "distances"],
    )

    hits = []
    docs = result["documents"][0]
    metas = result["metadatas"][0]
    dists = result["distances"][0]
    for doc, meta, dist in zip(docs, metas, dists):
        score = 1 - dist  # cosine distance -> similarity
        hits.append(
            {
                "content": doc,
                "kb_id": meta.get("kb_id"),
                "doc_id": meta.get("doc_id"),
                "score": round(float(score), 4),
            }
        )
    return hits


def delete_document(tenant_id: int, kb_id: int, doc_id: int) -> None:
    collection = tenant_collection(tenant_id)
    try:
        collection.delete(where={"doc_id": doc_id})
    except Exception:
        pass


def delete_kb(tenant_id: int, kb_id: int) -> None:
    collection = tenant_collection(tenant_id)
    try:
        collection.delete(where={"kb_id": kb_id})
    except Exception:
        pass


def kb_chunk_count(tenant_id: int, kb_id: int) -> int:
    collection = tenant_collection(tenant_id)
    try:
        res = collection.get(where={"kb_id": kb_id}, include=[])
        return len(res["ids"])
    except Exception:
        return 0
