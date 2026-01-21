import time
from logging import Logger

from openai.types.responses import ResponseInputParam
from slack_bolt import BoltContext, Say, SetStatus
from slack_sdk import WebClient
from slack_sdk.models.messages.chunk import (
    MarkdownTextChunk,
    PlanUpdateChunk,
    TaskUpdateChunk,
)

from agent.llm_caller import call_llm
from listeners.views.feedback_block import create_feedback_block


def message(
    client: WebClient,
    context: BoltContext,
    logger: Logger,
    message: dict,
    payload: dict,
    say: Say,
    set_status: SetStatus,
):
    """
    Handles when users send messages or select a prompt in an assistant thread and generate AI responses:

    Args:
        client: Slack WebClient for making API calls
        context: Bolt context containing channel and thread information
        logger: Logger instance for error tracking
        payload: Event payload with message details (channel, user, text, etc.)
        say: Function to send messages to the thread
        set_status: Function to update the assistant's status
    """
    try:
        channel_id = payload["channel"]
        team_id = context.team_id
        thread_ts = payload["thread_ts"]
        user_id = context.user_id

        # The first example shows detailed thinking steps similar to tool calls
        # displayed as plan.
        if message["text"] == "Wonder a few deep thoughts.":
            streamer = client.chat_stream(
                channel=channel_id,
                recipient_team_id=team_id,
                recipient_user_id=user_id,
                thread_ts=thread_ts,
                task_display_mode="plan",
            )
            streamer.append(
                chunks=[
                    MarkdownTextChunk(
                        text="Hello.\nI have received the task. ",
                    ),
                    MarkdownTextChunk(
                        text="This task appears manageable.\nThat is good.",
                    ),
                    TaskUpdateChunk(
                        id="001",
                        title="Understanding the task...",
                        status="in_progress",
                        details="- Identifying the goal\n- Identifying constraints",
                    ),
                    TaskUpdateChunk(
                        id="002",
                        title="Performing acrobatics...",
                        status="pending",
                    ),
                ],
            )
            time.sleep(4)

            streamer.append(
                chunks=[
                    PlanUpdateChunk(
                        title="Adding the final pieces...",
                    ),
                    TaskUpdateChunk(
                        id="001",
                        title="Understanding the task...",
                        status="complete",
                        details="\n- Pretending this was obvious",
                        output="We'll continue to ramble now",
                    ),
                    TaskUpdateChunk(
                        id="002",
                        title="Performing acrobatics...",
                        status="in_progress",
                        details="- Jumping atop ropes\n- Juggling bowling pins\n- Riding a single wheel too",
                    ),
                ],
            )
            time.sleep(4)

            streamer.stop(
                chunks=[
                    PlanUpdateChunk(
                        title="Decided to put on a show",
                    ),
                    TaskUpdateChunk(
                        id="002",
                        title="Performing acrobatics...",
                        status="complete",
                    ),
                    MarkdownTextChunk(
                        text="The crowd appears to be astounded and applauds :popcorn:"
                    ),
                ],
            )

        # This second example shows a generated text response for a provided prompt
        # displayed as a timeline.
        else:
            set_status(
                status="thinking...",
                loading_messages=[
                    "Teaching the hamsters to type faster…",
                    "Untangling the internet cables…",
                    "Consulting the office goldfish…",
                    "Polishing up the response just for you…",
                    "Convincing the AI to stop overthinking…",
                ],
            )

            streamer = client.chat_stream(
                channel=channel_id,
                recipient_team_id=team_id,
                recipient_user_id=user_id,
                thread_ts=thread_ts,
                task_display_mode="timeline",
            )
            prompts: ResponseInputParam = [
                {
                    "role": "user",
                    "content": message["text"],
                },
            ]
            call_llm(streamer, prompts)

            feedback_block = create_feedback_block()
            streamer.stop(
                blocks=feedback_block,
            )

    except Exception as e:
        logger.exception(f"Failed to handle a user message event: {e}")
        say(f":warning: Something went wrong! ({e})")
