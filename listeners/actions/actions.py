from logging import Logger

from slack_bolt import Ack
from slack_sdk import WebClient


def handle_feedback(ack: Ack, body: dict, client: WebClient, logger: Logger):
    """
    Handles user feedback on AI-generated responses via thumbs up/down buttons.

    Args:
        ack: Function to acknowledge the action request
        body: Action payload containing feedback details (message, channel, user, action value)
        client: Slack WebClient for making API calls
        logger: Logger instance for debugging and error tracking
    """
    try:
        ack()
        message_ts = body["message"]["ts"]
        channel_id = body["channel"]["id"]
        feedback_type = body["actions"][0]["value"]
        is_positive = feedback_type == "good-feedback"

        if is_positive:
            client.chat_postEphemeral(
                channel=channel_id,
                user=body["user"]["id"],
                thread_ts=message_ts,
                text="We're glad you found this useful.",
            )
        else:
            client.chat_postEphemeral(
                channel=channel_id,
                user=body["user"]["id"],
                thread_ts=message_ts,
                text="Sorry to hear that response wasn't up to par :slightly_frowning_face: Starting a new chat may help with AI mistakes and hallucinations.",
            )

        logger.debug(f"Handled feedback: type={feedback_type}, message_ts={message_ts}")
    except Exception as error:
        logger.error(f":warning: Something went wrong! {error}")
