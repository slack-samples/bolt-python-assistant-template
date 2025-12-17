import os

import openai
from openai import Stream
from openai.types.responses import ResponseStreamEvent


def call_llm(
    prompt: str,
) -> Stream[ResponseStreamEvent]:
    openai_client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    response = openai_client.responses.create(
        model="gpt-4o-mini",
        input=prompt,
        stream=True,
    )
    return response
