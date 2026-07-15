from __future__ import annotations

import json
from dataclasses import dataclass

from django.conf import settings
from openai import OpenAI

from tickets.models import Ticket


class QwenServiceError(RuntimeError):
    """通义千问调用或解析失败。"""


@dataclass(frozen=True)
class TicketAIResult:
    """AI 分析工单后返回的标准结果。"""

    summary: str
    category: str
    priority: str
    suggested_reply: str


def analyze_ticket(
    ticket: Ticket,
) -> TicketAIResult:
    """调用通义千问分析一张工单。"""

    if not settings.DASHSCOPE_API_KEY:
        raise QwenServiceError(
            "没有配置 DASHSCOPE_API_KEY。"
        )

    client = OpenAI(
        api_key=settings.DASHSCOPE_API_KEY,
        base_url=settings.DASHSCOPE_BASE_URL,
        timeout=60.0,
        max_retries=2,
    )

    system_prompt = """
你是企业客服工单分析助手。

请分析用户工单，并且只返回一个合法的 JSON 对象。
不能输出 Markdown 代码块，也不能输出 JSON 以外的内容。

JSON 必须包含以下字段：

{
  "summary": "用一句话概括用户问题",
  "category": "account/payment/technical/suggestion/other 中的一项",
  "priority": "low/medium/high/urgent 中的一项",
  "suggested_reply": "给用户的专业、礼貌、可执行的中文回复"
}

分类说明：
account：账号、登录、密码、权限问题
payment：订单、支付、退款、发票问题
technical：系统错误、程序故障、功能异常
suggestion：意见、建议、功能需求
other：无法归入以上分类的问题

优先级说明：
low：普通建议或低影响问题
medium：影响部分使用，但有替代方案
high：核心功能不可用，明显影响工作
urgent：大范围故障、安全风险或严重资金风险
""".strip()

    user_prompt = f"""
请分析下面这张工单。

工单标题：
{ticket.title}

问题描述：
{ticket.description}
""".strip()

    try:
        response = client.chat.completions.create(
            model=settings.QWEN_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": system_prompt,
                },
                {
                    "role": "user",
                    "content": user_prompt,
                },
            ],
            response_format={
                "type": "json_object"
            },
            temperature=0.1,
        )

    except Exception as exc:
        raise QwenServiceError(
            "调用通义千问失败。"
        ) from exc

    if not response.choices:
        raise QwenServiceError(
            "通义千问没有返回候选结果。"
        )

    content = (
        response.choices[0].message.content
        or ""
    ).strip()

    try:
        data = json.loads(content)

    except json.JSONDecodeError as exc:
        raise QwenServiceError(
            "通义千问返回的内容不是合法 JSON。"
        ) from exc

    summary = str(
        data.get("summary", "")
    ).strip()

    suggested_reply = str(
        data.get("suggested_reply", "")
    ).strip()

    category = str(
        data.get("category", "")
    ).strip().lower()

    priority = str(
        data.get("priority", "")
    ).strip().lower()

    valid_categories = {
        value
        for value, _label
        in Ticket.Category.choices
    }

    valid_priorities = {
        value
        for value, _label
        in Ticket.Priority.choices
    }

    if category not in valid_categories:
        category = Ticket.Category.OTHER

    if priority not in valid_priorities:
        priority = Ticket.Priority.MEDIUM

    if not summary:
        raise QwenServiceError(
            "AI 没有生成有效的工单摘要。"
        )

    if not suggested_reply:
        raise QwenServiceError(
            "AI 没有生成有效的建议回复。"
        )

    return TicketAIResult(
        summary=summary[:1000],
        category=category,
        priority=priority,
        suggested_reply=suggested_reply[:2000],
    )