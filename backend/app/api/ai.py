import json
import re

from fastapi import APIRouter, Depends
from langchain_core.messages import HumanMessage
from pydantic import BaseModel

from app.core.deps import get_current_user
from app.models import User
from app.services.llm import get_llm

router = APIRouter(prefix="/api/ai", tags=["AI 智能分析"], dependencies=[Depends(get_current_user)])

KB_STYLES = {
    "concise": "语言专业简洁，控制在 40~60 字，突出知识库定位。",
    "detailed": "语言专业详实，控制在 80~120 字，说明用途、适合上传的文档类型与预期效果。",
    "lively": "语言活泼有感染力，可用一个贴切的比喻开头，控制在 50~80 字，突出使用场景。",
}

AGENT_STYLES = {
    "professional": "风格专业严谨，用词精准，适合企业对客场景。",
    "friendly": "风格亲切友善，多用温暖鼓励的语气，像朋友一样交流。",
    "humorous": "风格幽默风趣，回答中可适当使用轻松的比喻和调侃，但不失专业底线。",
    "concise": "风格简洁干练，直击要点，能用一句话说清的绝不用两句。",
}

DOC_STYLES = {
    "tutorial": "写成教学讲解文档：概念引入、原理说明、示例演示、常见误区，适合初学者阅读。",
    "handbook": "写成制度手册文档：条款分明，用清晰的章节编号，语言正式规范。",
    "faq": "写成 FAQ 问答文档：每个知识点用「## 问题」小节组织，先给简短结论再展开说明。",
    "science": "写成科普文章：生动有趣，多用生活化的例子类比，让非专业读者也能看懂。",
}


class KbSuggestIn(BaseModel):
    name: str
    style: str = "concise"


class AgentSuggestIn(BaseModel):
    name: str
    kb_names: list[str] = []
    style: str = "friendly"


class DocGenIn(BaseModel):
    topic: str
    kb_name: str = ""
    style: str = "tutorial"
    points: str = ""


def _clean(text: str) -> str:
    return text.strip().strip('"“”')


def _parse_json(content: str) -> dict:
    m = re.search(r"\{.*\}", content, re.DOTALL)
    if not m:
        raise ValueError("AI 未返回合法 JSON")
    return json.loads(m.group(0))


@router.post("/kb-description")
def suggest_kb_description(payload: KbSuggestIn):
    name = payload.name.strip()
    if not name:
        return {"description": ""}
    style_hint = KB_STYLES.get(payload.style, KB_STYLES["concise"])

    prompt = (
        f"用户想在企业知识库平台上创建一个名为「{name}」的知识库，请生成一段知识库描述。要求：{style_hint}"
        "直接输出描述正文，不要任何前缀、引号、标题或解释。"
    )
    llm = get_llm(temperature=0.3)
    resp = llm.invoke([HumanMessage(content=prompt)])
    return {"description": _clean(resp.content)}


@router.post("/agent-profile")
def suggest_agent_profile(payload: AgentSuggestIn):
    name = payload.name.strip()
    if not name:
        return {"system_prompt": "", "welcome_message": "", "suggested_questions": []}
    style_hint = AGENT_STYLES.get(payload.style, AGENT_STYLES["friendly"])
    kb_part = ""
    if payload.kb_names:
        kb_part = "该智能体绑定了以下知识库：" + "、".join(payload.kb_names) + "。"

    prompt = (
        f"用户想在企业平台上创建一个名为「{name}」的智能问答智能体。{kb_part}"
        f"人设要求：{style_hint}\n"
        "请生成智能体配置三件套：system_prompt（人设提示词，120~200 字，包含角色定位、服务范围、"
        "语气风格、回答规范：简洁分点、依据知识库回答、知识库没有相关信息时如实告知、不编造事实）、"
        "welcome_message（开场白，20 字以内，需体现智能体定位）、"
        "suggested_questions（3 个推荐问题，必须围绕智能体的服务范围和知识库主题设计，不要通用问题）。\n"
        '严格按以下 JSON 格式输出，不要输出任何其他内容：\n'
        '{"system_prompt": "...", "welcome_message": "...", "suggested_questions": ["...", "...", "..."]}'
    )
    llm = get_llm(temperature=0.4)
    resp = llm.invoke([HumanMessage(content=prompt)])
    try:
        data = _parse_json(resp.content)
        return {
            "system_prompt": str(data.get("system_prompt", "")),
            "welcome_message": str(data.get("welcome_message", "")),
            "suggested_questions": [str(q) for q in data.get("suggested_questions", [])][:3],
        }
    except (ValueError, json.JSONDecodeError):
        return {
            "system_prompt": _clean(resp.content),
            "welcome_message": "",
            "suggested_questions": [],
        }


@router.post("/generate-doc")
def generate_doc(payload: DocGenIn):
    topic = payload.topic.strip()
    if not topic:
        return {"title": "", "content": ""}
    style_hint = DOC_STYLES.get(payload.style, DOC_STYLES["tutorial"])
    kb_part = f"该文档将存入「{payload.kb_name}」知识库，供智能体检索回答使用。" if payload.kb_name else ""
    points_part = f"必须覆盖以下要点：{payload.points.strip()}。" if payload.points.strip() else ""

    prompt = (
        f"请围绕主题「{topic}」撰写一篇高质量知识文档。{kb_part}{points_part}"
        f"写作要求：{style_hint}\n"
        "使用 Markdown 格式，篇幅 600~1000 字，信息密度要高（后续会被切片用于 RAG 检索，"
        "所以每个小节都要有独立完整的知识点）。\n"
        '第一行输出文档标题（# 开头）。直接输出文档内容，不要任何额外解释。'
    )
    llm = get_llm(temperature=0.5)
    resp = llm.invoke([HumanMessage(content=prompt)])
    content = resp.content.strip()
    title = topic
    m = re.match(r"^#\s+(.+)", content)
    if m:
        title = m.group(1).strip()
    return {"title": title, "content": content}
