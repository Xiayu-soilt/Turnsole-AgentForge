from datetime import datetime

from pydantic import BaseModel, Field


class RegisterIn(BaseModel):
    username: str = Field(min_length=2, max_length=64)
    password: str = Field(min_length=6, max_length=64)
    company: str = Field(min_length=1, max_length=100)


class LoginIn(BaseModel):
    username: str
    password: str


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    username: str
    tenant_id: int
    company: str


class KBCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    description: str = ""


class AIDocCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    content: str = Field(min_length=1)


class KBOut(BaseModel):
    id: int
    name: str
    description: str
    created_at: datetime
    doc_count: int = 0
    chunk_count: int = 0


class DocOut(BaseModel):
    id: int
    kb_id: int
    filename: str
    file_type: str
    size: int
    status: str
    chunk_count: int
    error: str
    created_at: datetime


class BotCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    avatar: str = ""
    system_prompt: str = ""
    welcome_message: str = "你好，请问有什么可以帮您？"
    suggested_questions: list[str] = []
    temperature: float = 0.7
    kb_ids: list[int] = []


class BotUpdate(BaseModel):
    name: str | None = None
    avatar: str | None = None
    system_prompt: str | None = None
    welcome_message: str | None = None
    suggested_questions: list[str] | None = None
    temperature: float | None = None
    kb_ids: list[int] | None = None


class BotOut(BaseModel):
    id: int
    name: str
    avatar: str
    system_prompt: str
    welcome_message: str
    suggested_questions: list
    temperature: float
    kb_ids: list
    is_published: bool
    publish_token: str
    created_at: datetime


class ChatIn(BaseModel):
    message: str = Field(min_length=1, max_length=4000)
    session_key: str = "default"
    conversation_id: int | None = None


class Citation(BaseModel):
    index: int
    doc_id: int
    filename: str
    content: str
    score: float


class MessageOut(BaseModel):
    id: int
    role: str
    content: str
    citations: list
    feedback: str | None
    created_at: datetime


class ConversationOut(BaseModel):
    id: int
    bot_id: int
    session_key: str
    source: str
    created_at: datetime
    messages: list[MessageOut] = []


class StatsOut(BaseModel):
    total_conversations: int
    total_messages: int
    total_user_messages: int
    total_likes: int
    total_dislikes: int
    hit_rate: float
    doc_count: int
    chunk_count: int
    bot_count: int
    kb_count: int
    daily: list[dict] = []
    hot_questions: list[dict] = []
