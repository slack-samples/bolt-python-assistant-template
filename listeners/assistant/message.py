import time
from logging import Logger

from openai.types.responses import ResponseInputParam
from slack_bolt import BoltAgent, BoltContext, Say
from slack_sdk.models.messages.chunk import (
    MarkdownTextChunk,
    PlanUpdateChunk,
    TaskUpdateChunk,
)

from agent.llm_caller import call_llm
from listeners.views.feedback_block import create_feedback_block


def message(
    agent: BoltAgent,
    context: BoltContext,
    logger: Logger,
    message: dict,
    payload: dict,
    say: Say,
):
    """
    Handles when users send messages or select a prompt in an assistant thread and generate AI responses:

    Args:
        agent: BoltAgent for making API calls
        client: Slack WebClient for making API calls
        context: Bolt context containing channel and thread information
        logger: Logger instance for error tracking
        payload: Event payload with message details (channel, user, text, etc.)
        say: Function to send messages to the thread
    """
    try:
        channel_id = payload["channel"]
        team_id = context.team_id
        thread_ts = payload["thread_ts"]
        user_id = context.user_id

        # The first example shows a message with thinking steps that has different
        # chunks to construct and update a plan alongside text outputs.
        if message["text"] == "Wonder a few deep thoughts.":
            agent.set_status(
                status="thinking...",
                loading_messages=[
                    "Teaching the hamsters to type faster…",
                    "Untangling the internet cables…",
                    "Consulting the office goldfish…",
                    "Polishing up the response just for you…",
                    "Convincing the AI to stop overthinking…",
                ],
            )

            time.sleep(4)

            streamer = agent.chat_stream(task_display_mode="plan")
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
                    ),
                ],
            )
            time.sleep(4)

            feedback_block = create_feedback_block()
            streamer.stop(
                chunks=[
                    PlanUpdateChunk(
                        title="Decided to put on a show",
                    ),
                    TaskUpdateChunk(
                        id="002",
                        title="Performing acrobatics...",
                        status="complete",
                        details="- Jumped atop ropes\n- Juggled bowling pins\n- Rode a single wheel too",
                    ),
                    MarkdownTextChunk(
                        text="The crowd appears to be astounded and applauds :popcorn:"
                    ),
                ],
                blocks=feedback_block,
            )

        # This second example shows a generated text response for a provided prompt
        # displayed as a timeline.
        else:
            agent.set_status(
                status="thinking...",
                loading_messages=[
                    "Teaching the hamsters to type faster…",
                    "Untangling the internet cables…",
                    "Consulting the office goldfish…",
                    "Polishing up the response just for you…",
                    "Convincing the AI to stop overthinking…",
                ],
            )

            streamer = agent.chat_stream(task_display_mode="timeline")
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
