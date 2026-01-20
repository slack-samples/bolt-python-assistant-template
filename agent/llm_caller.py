import json
import os

import openai
from openai.types.responses import ResponseInputParam
from slack_sdk.models.messages.chunk import TaskUpdateChunk
from slack_sdk.web.chat_stream import ChatStream

from agent.tools.dice import roll_dice, roll_dice_definition


def call_llm(
    streamer: ChatStream,
    prompts: ResponseInputParam,
):
    """
    Stream an LLM response to prompts with an example dice rolling function

    https://docs.slack.dev/tools/python-slack-sdk/web#sending-streaming-messages
    https://platform.openai.com/docs/guides/text
    https://platform.openai.com/docs/guides/streaming-responses
    https://platform.openai.com/docs/guides/function-calling
    """
    llm = openai.OpenAI(
        api_key=os.getenv("OPENAI_API_KEY"),
    )
    tool_calls = []
    response = llm.responses.create(
        model="gpt-4o-mini",
        input=prompts,
        tools=[
            roll_dice_definition,
        ],
        stream=True,
    )
    for event in response:
        # Markdown text from the LLM response is streamed in chat as it arrives
        if event.type == "response.output_text.delta":
            streamer.append(markdown_text=f"{event.delta}")

        # Function calls are saved for later computation and a new task is shown
        if event.type == "response.output_item.done":
            if event.item.type == "function_call":
                tool_calls.append(event.item)
                if event.item.name == "roll_dice":
                    args = json.loads(event.item.arguments)
                    streamer.append(
                        chunks=[
                            TaskUpdateChunk(
                                id=f"{event.item.call_id}",
                                title=f"Rolling a {args['count']}d{args['sides']}...",
                                status="in_progress",
                            ),
                        ],
                    )

    # Tool calls are performed and tasks are marked as completed in Slack
    if tool_calls:
        for call in tool_calls:
            if call.name == "roll_dice":
                args = json.loads(call.arguments)
                prompts.append(
                    {
                        "id": call.id,
                        "call_id": call.call_id,
                        "type": "function_call",
                        "name": "roll_dice",
                        "arguments": call.arguments,
                    }
                )
                result = roll_dice(**args)
                prompts.append(
                    {
                        "type": "function_call_output",
                        "call_id": call.call_id,
                        "output": json.dumps(result),
                    }
                )
                if result.get("error") is not None:
                    streamer.append(
                        chunks=[
                            TaskUpdateChunk(
                                id=f"{call.call_id}",
                                title=f"{result['error']}",
                                status="error",
                            ),
                        ],
                    )
                else:
                    streamer.append(
                        chunks=[
                            TaskUpdateChunk(
                                id=f"{call.call_id}",
                                title=f"{result['description']}",
                                status="complete",
                            ),
                        ],
                    )

        # Complete the LLM response after making tool calls
        call_llm(streamer, prompts)
