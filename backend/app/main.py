import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import ai, audit, auth, bots, chat, knowledge, public, stats
from app.core.config import settings
from app.db.session import Base, engine

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("botforge")


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.APP_NAME,
        description="Turnsole AgentForge 智能体工厂 - 多租户知识库智能体搭建平台",
        version="1.0.0",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:5173",
            "http://127.0.0.1:5173",
            "http://localhost:5174",
            "http://127.0.0.1:5174",
            "http://localhost:5175",
            "http://127.0.0.1:5175",
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(auth.router)
    app.include_router(ai.router)
    app.include_router(knowledge.router)
    app.include_router(bots.router)
    app.include_router(chat.router)
    app.include_router(public.router)
    app.include_router(stats.router)
    app.include_router(audit.router)

    @app.get("/api/health")
    def health():
        return {"status": "ok", "app": settings.APP_NAME}

    @app.on_event("startup")
    def on_startup():
        Base.metadata.create_all(bind=engine)
        logger.info(f"{settings.APP_NAME} started, docs at /docs")

    return app


app = create_app()
