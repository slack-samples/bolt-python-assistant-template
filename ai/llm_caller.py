import os
from typing import Dict, List

import openai
from openai import Stream
from openai.types.responses import ResponseStreamEvent

DEFAULT_SYSTEM_CONTENT = """
You're an assistant in a Slack workspace.
Users in the workspace will ask you to help them write something or to think better about a specific topic.
You'll respond to those questions in a professional way.
When you include markdown text, convert them to Slack compatible ones.
When a prompt has Slack's special syntax like <@USER_ID> or <#CHANNEL_ID>, you must keep them as-is in your response.
"""


def call_llm(
    messages_in_thread: List[Dict[str, str]],
    system_content: str = DEFAULT_SYSTEM_CONTENT,
) -> Stream[ResponseStreamEvent]:
    openai_client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    messages = [{"role": "system", "content": system_content}]
    messages.extend(messages_in_thread)
    response = openai_client.responses.create(
        model="gpt-4o-mini", input=messages, stream=True
    )
    return response
