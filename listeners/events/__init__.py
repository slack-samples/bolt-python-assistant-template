from typing import Dict, Any

from slack_bolt import App
from slack_bolt.request.payload_utils import is_event
from .app_mention import respond_to_mention
from .assistant_thread_started import start_thread_with_suggested_prompts
from .asssistant_thread_context_changed import save_new_thread_context

def register(app: App):
    app.event("assistant_thread_started")(start_thread_with_suggested_prompts)
    app.event("assistant_thread_context_changed")(save_new_thread_context)
    app.event("message", matchers=[is_user_message_event_in_assistant_thread])(respond_to_user_message)
    app.event("message", matchers=[is_message_event_in_assistant_thread])(just_ack)
    app.event("message")(handle_app_mention)

def handle_app_mention(payload: dict, client, logger):
    event = payload.get("event", {})
    channel_id = event.get("channel")
    thread_ts = event.get("ts")
    user = event.get("user")
    
    try:
        client.chat_postMessage(
            channel=channel_id,
            thread_ts=thread_ts,
            text=f"Hi <@{user}>, how can I help you?"
        )
    except Exception as e:
        logger.exception(f"Failed to handle app_mention event: {e}")


    
def is_message_event_in_assistant_thread(body: Dict[str, Any]) -> bool:
    if is_event(body):
        return body["event"]["type"] == "message" and body["event"].get("channel_type") == "im"
    return False


def is_user_message_event_in_assistant_thread(body: Dict[str, Any]) -> bool:
    return is_message_event_in_assistant_thread(body) and body["event"].get("subtype") in (None, "file_share")

def just_ack():
    pass
