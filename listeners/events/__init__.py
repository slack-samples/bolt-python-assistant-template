# This sample app repository contains event listener code to help developers understand what's happening under the hood.
# We recommend using assistant middleware instead of these event listeners.
# For more details, refer to https://tools.slack.dev/bolt-python/concepts/assistant/.

from typing import Dict, Any

from slack_bolt import App
from slack_bolt.request.payload_utils import is_event

from .assistant_thread_started import start_thread_with_suggested_prompts
from .asssistant_thread_context_changed import save_new_thread_context
from .user_message import respond_to_user_message


def register(app: App):
    app.event("assistant_thread_started")(start_thread_with_suggested_prompts)
    app.event("assistant_thread_context_changed")(save_new_thread_context)
    app.event("message", matchers=[is_user_message_event_in_assistant_thread])(respond_to_user_message)
    app.event("message", matchers=[is_message_event_in_assistant_thread])(just_ack)


def is_message_event_in_assistant_thread(body: Dict[str, Any]) -> bool:
    if is_event(body):
        return body["event"]["type"] == "message" and body["event"].get("channel_type") == "im"
    return False


def is_user_message_event_in_assistant_thread(body: Dict[str, Any]) -> bool:
    return is_message_event_in_assistant_thread(body) and body["event"].get("subtype") in (None, "file_share")


def just_ack():
    pass
