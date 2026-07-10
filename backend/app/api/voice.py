import json

from fastapi import APIRouter
from pydantic import BaseModel

from app.core.llm import get_llm

router = APIRouter(prefix="/api/voice", tags=["语音"])

# 可导航的页面映射：关键词 → {路由, 名称}
NAV_MAP = {
    "知识库":     {"route": "/knowledge",  "name": "知识库"},
    "课程":       {"route": "/course",     "name": "课程学习"},
    "课程学习":   {"route": "/course",     "name": "课程学习"},
    "测验":       {"route": "/quiz",       "name": "在线测验"},
    "在线测验":   {"route": "/quiz",       "name": "在线测验"},
    "考试":       {"route": "/quiz",       "name": "在线测验"},
    "学习进度":   {"route": "/dashboard",  "name": "学习进度"},
    "进度":       {"route": "/dashboard",  "name": "学习进度"},
    "错题本":     {"route": "/wrongbook",  "name": "错题本"},
    "错题":       {"route": "/wrongbook",  "name": "错题本"},
    "个人中心":   {"route": "/profile",    "name": "个人中心"},
    "个人":       {"route": "/profile",    "name": "个人中心"},
    "首页":       {"route": "/knowledge",  "name": "知识库"},
}

NAV_LIST = "\n".join(f"- {k} → {v['name']}" for k, v in NAV_MAP.items())


class VoiceRequest(BaseModel):
    text: str


class VoiceResponse(BaseModel):
    action: str       # "navigate" | "chat" | "unknown"
    target: str       # 路由路径 或 空
    target_name: str  # 目标名称 或 空
    reply: str        # 给用户的回复


SYSTEM_PROMPT = f"""你是一个智能学习助手的语音指令解析器。用户会通过语音输入文字，你需要判断用户意图并返回 JSON。

## 规则

1. 如果用户想**打开/前往/进入**某个页面，action 为 "navigate"，target 为页面路由前缀（如 /knowledge），target_name 为中文名称。
2. 如果用户只是**聊天/问候/提问/闲聊**，action 为 "chat"，reply 为友好回复。
3. 如果**无法判断意图**，action 为 "unknown"，reply 为礼貌提示。

## 可导航页面（target 必须是以下路由前缀之一）

{NAV_LIST}

路由前缀映射：
- 知识库 → /knowledge
- 课程学习 → /course
- 在线测验 → /quiz
- 学习进度 → /dashboard
- 错题本 → /wrongbook
- 个人中心 → /profile

## 输出格式（严格 JSON，不要带任何额外内容）

{{"action": "navigate", "target": "/xxx", "target_name": "xxx", "reply": "好的，正在打开xxx"}}
{{"action": "chat", "target": "", "target_name": "", "reply": "你好！..."}}
{{"action": "unknown", "target": "", "target_name": "", "reply": "抱歉，..."}}

## 示例

用户: 打开错题本
{{"action": "navigate", "target": "/wrongbook", "target_name": "错题本", "reply": "好的，正在打开错题本"}}

用户: 你好
{{"action": "chat", "target": "", "target_name": "", "reply": "你好！我是 AI 学习助手，有什么可以帮你的吗？"}}

用户: 今天天气怎么样
{{"action": "unknown", "target": "", "target_name": "", "reply": "抱歉，我目前只支持打开学习相关页面和简单对话，无法查询天气信息。"}}

现在请解析用户输入，只返回 JSON。"""


@router.post("/command", response_model=VoiceResponse)
def process_voice_command(data: VoiceRequest):
    text = data.text.strip()
    if not text:
        return VoiceResponse(
            action="unknown",
            target="",
            target_name="",
            reply="没有检测到语音内容，请重试。",
        )

    llm = get_llm()
    messages = [
        ("system", SYSTEM_PROMPT),
        ("user", text),
    ]

    try:
        resp = llm.invoke(messages)
        content = resp.content.strip()
        # 清理可能的 markdown 代码块
        if content.startswith("```"):
            content = content.split("\n", 1)[-1]
            if content.endswith("```"):
                content = content[:-3]
            content = content.strip()
        
        result = json.loads(content)
        action = result.get("action", "unknown")
        target = result.get("target", "")
        target_name = result.get("target_name", "")
        reply = result.get("reply", "")

        # 验证 navigate 的 target 是否合法
        if action == "navigate":
            valid_targets = [v["route"] for v in NAV_MAP.values()]
            valid_targets = list(set(valid_targets))
            if target not in valid_targets:
                action = "unknown"
                target = ""
                target_name = ""
                reply = reply or "抱歉，我无法识别您想打开的页面。"

        return VoiceResponse(
            action=action,
            target=target,
            target_name=target_name,
            reply=reply,
        )
    except (json.JSONDecodeError, Exception) as e:
        return VoiceResponse(
            action="unknown",
            target="",
            target_name="",
            reply="抱歉，我暂时无法处理您的请求，请稍后再试。",
        )
