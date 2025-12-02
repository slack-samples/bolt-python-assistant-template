# Implementing Real-Time Agent Status Updates in Slack AI Assistants

This document provides a comprehensive technical guide for implementing real-time status updates in Slack AI assistants using Google ADK (Agent Development Kit) event streams.

## Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Dependencies](#dependencies)
4. [Understanding Slack's Status API](#understanding-slacks-status-api)
5. [Understanding ADK Events](#understanding-adk-events)
6. [Implementation](#implementation)
7. [Event Flow](#event-flow)
8. [Troubleshooting](#troubleshooting)
9. [Best Practices](#best-practices)

## Overview

By default, Slack AI assistants show generic loading states ("thinking...", "evaluating...", "analyzing..."). This implementation enhances the user experience by displaying real-time information about:

- Which agent is currently processing the request
- What tools are being invoked
- When control transfers between agents

### What This Achieves

**Before:**
```
Status: thinking...
Loading: "Teaching the hamsters to type faster..."
         "Untangling the internet cables..."
```

**After:**
```
Status: is working...
Loading: "CoordinatorAgent is working..."
         "Consulting MathAgent..."
         "Using Calculate..."
```

## Architecture

### High-Level Flow

```
User Message
    ↓
Slack Event Handler
    ↓
LLM Caller (ai/llm_caller.py)
    ↓
ADK Runner.run_async()
    ↓
Event Stream (yields events)
    ↓
Event Processor (detects agents/tools)
    ↓
Status/Content Events
    ↓
Slack Status Update + Response Streaming
```

### Component Responsibilities

| Component | File | Responsibility |
|-----------|------|----------------|
| Event Handler | `listeners/assistant/message.py` | Receives Slack events, manages event loop |
| Event Handler | `listeners/events/app_mentioned.py` | Handles @mentions |
| LLM Caller | `ai/llm_caller.py` | Processes ADK events, yields status/content |
| ADK Runner | Google ADK SDK | Executes agent system, emits events |
| Agents | `ai/agents.py` | Define agent hierarchy and tools |

## Dependencies

### Required Python Packages

```python
# Slack SDK
slack-bolt>=1.18.0
slack-sdk>=3.23.0

# Google ADK
google-genai>=1.0.0  # Includes ADK

# Standard library (no installation needed)
asyncio
logging
typing
```

### Environment Variables

```bash
# Slack Configuration
SLACK_BOT_TOKEN=xoxb-...
SLACK_APP_TOKEN=xapp-...

# Google ADK Authentication (choose one)
GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account.json  # Option 1
GOOGLE_API_KEY=your-api-key                                   # Option 2
# Or use: gcloud auth application-default login                # Option 3
```

### Slack App Scopes Required

```
app_mentions:read
assistant:write
channels:history
channels:read
chat:write
groups:history
groups:read
im:history
im:read
mpim:history
mpim:read
```

## Understanding Slack's Status API

### The `assistant.threads.setStatus` Method

```python
client.assistant_threads_setStatus(
    channel_id: str,      # Required: Channel containing the thread
    thread_ts: str,       # Required: Thread timestamp
    status: str,          # Required: Status text (may be translated by Slack)
    loading_messages: Optional[List[str]] = None  # Optional: Custom rotating messages
)
```

### Key Behaviors

1. **Status Translation**: Slack translates custom `status` values to predefined ones:
   - Your input: `"Processing your request..."`
   - Slack displays: `"thinking..."` or `"evaluating..."`

2. **Loading Messages**: These are **not** translated and display exactly as provided:
   - Your input: `loading_messages=["MathAgent is working..."]`
   - Slack displays: `"MathAgent is working..."`

3. **Display Format**:
   ```
   <App Name> <status>
   <loading_message>
   ```
   Example:
   ```
   MyBot is working...
   Consulting MathAgent...
   ```

4. **Auto-Clearing**: Status automatically clears when:
   - The app sends a reply message
   - You send an empty string: `status=""`

5. **Update Frequency**: You can call `setStatus` multiple times during processing to update the loading message in real-time.

## Understanding ADK Events

### Event Structure

ADK's `runner.run_async()` yields events during agent execution. Each event contains:

```python
class Event:
    author: str                    # Agent name or "user"
    content: Content | None        # Message content with parts
    event_id: str                  # Unique event identifier
    invocation_id: str            # Correlates events in one interaction
    partial: bool                  # True for streaming chunks
    actions: Actions | None        # State changes, transfers, etc.
```

### Key Event Properties

#### 1. `event.author`
Identifies who created the event:
```python
"user"              # User's input message
"CoordinatorAgent"  # Response from coordinator
"MathAgent"         # Response from specialized agent
```

#### 2. `event.content`
Contains the actual message content:
```python
event.content.parts  # List of Part objects
part.text            # Text content of the part
```

#### 3. `event.get_function_calls()`
Returns tool invocations:
```python
function_calls = event.get_function_calls()
for func_call in function_calls:
    func_call.name  # e.g., "calculate", "format_text"
    func_call.args  # Tool arguments
```

#### 4. `event.actions`
Contains control flow information:
```python
event.actions.transfer_to_agent  # Target agent for handoff
event.actions.state_delta        # State changes
event.actions.artifact_delta     # Artifact updates
```

### Event Lifecycle Example

For request: "What is 25 times 4?"

```python
# Event 1: User input echo
Event(author="user", content="What is 25 times 4?")

# Event 2: Coordinator receives request
Event(author="CoordinatorAgent", content=None)

# Event 3: Coordinator decides to transfer
Event(author="CoordinatorAgent",
      actions=Actions(transfer_to_agent="MathAgent"))

# Event 4: MathAgent takes over
Event(author="MathAgent", content=None)

# Event 5: MathAgent requests tool
Event(author="MathAgent",
      function_calls=[FunctionCall(name="calculate", args={"expr": "25*4"})])

# Event 6: Tool result
Event(author="function", content="100")

# Event 7: MathAgent starts response
Event(author="MathAgent", content="The result", partial=True)

# Event 8: Continues streaming
Event(author="MathAgent", content=" is 100", partial=True)

# Event 9: Final response
Event(author="MathAgent", content=".", partial=False)
```

## Implementation

### Step 1: Modify `ai/llm_caller.py`

#### Add Dependencies

```python
import logging
from typing import Dict, List, AsyncGenerator, Literal

from google.adk.runners import InMemoryRunner
from google.genai import types

from .agents import get_root_agent

logger = logging.getLogger(__name__)
```

#### Update Function Signature

Change from yielding strings to yielding event dictionaries:

```python
async def call_llm(
    messages_in_thread: List[Dict[str, str]],
    user_id: str = "default_user",
    session_id: str = None,
) -> AsyncGenerator[Dict[str, str], None]:
    """
    Call the ADK multi-agent system and stream responses with status updates.

    Args:
        messages_in_thread: List of message dictionaries with 'role' and 'content' keys
        user_id: The Slack user ID
        session_id: Optional session ID for maintaining conversation context

    Yields:
        Dict[str, str]: Events with 'type' (either 'status' or 'content') and 'text' keys
            - status events: Updates about what the agent is doing (tool calls, agent transfers)
            - content events: Actual response text to display to the user
    """
```

#### Implement Event Processing

```python
async def call_llm(...) -> AsyncGenerator[Dict[str, str], None]:
    runner = get_adk_runner()

    # Session management (existing code)
    if session_id is None:
        session_id = f"session_{user_id}"

    try:
        await runner.session_service.create_session(
            app_name=_app_name, user_id=user_id, session_id=session_id
        )
    except Exception:
        pass

    # Convert messages to ADK format (existing code)
    last_message = (
        messages_in_thread[-1]
        if messages_in_thread
        else {"role": "user", "content": ""}
    )

    new_message = types.Content(
        role="user", parts=[types.Part(text=last_message["content"])]
    )

    # Track state
    current_agent = None
    has_started_streaming_content = False

    # Process event stream
    async for event in runner.run_async(
        user_id=user_id, session_id=session_id, new_message=new_message
    ):
        # Optional: Log for debugging
        logger.info(f"ADK Event - Author: {event.author}, Has content: {bool(event.content)}")

        # DETECTION 1: Agent changes/transfers
        if event.author and event.author != "user" and event.author != current_agent:
            current_agent = event.author
            if not has_started_streaming_content:
                status_text = f"{current_agent} is working..."
                logger.info(f"Yielding status: {status_text}")
                yield {"type": "status", "text": status_text}

        # DETECTION 2: Tool calls (function calls)
        function_calls = (
            event.get_function_calls() if hasattr(event, "get_function_calls") else []
        )
        logger.info(f"Function calls detected: {len(function_calls)}")
        if function_calls and not has_started_streaming_content:
            for func_call in function_calls:
                tool_name = (
                    func_call.name if hasattr(func_call, "name") else str(func_call)
                )
                # Make tool names more readable
                readable_name = tool_name.replace("_", " ").title()
                status_text = f"Using {readable_name}..."
                logger.info(f"Yielding tool status: {status_text}")
                yield {"type": "status", "text": status_text}

        # DETECTION 3: Explicit agent transfers
        if hasattr(event, "actions") and event.actions:
            logger.info(f"Event has actions: {event.actions}")
            if (
                hasattr(event.actions, "transfer_to_agent")
                and event.actions.transfer_to_agent
            ):
                target_agent = event.actions.transfer_to_agent
                status_text = f"Consulting {target_agent}..."
                logger.info(f"Yielding transfer status: {status_text}")
                yield {"type": "status", "text": status_text}

        # DETECTION 4: Stream content
        if event.content and event.content.parts and event.author != "user":
            for part in event.content.parts:
                if hasattr(part, "text") and part.text:
                    has_started_streaming_content = True
                    yield {"type": "content", "text": part.text}
```

#### Key Implementation Details

1. **`has_started_streaming_content` flag**: Prevents status updates after response text starts streaming. This avoids interrupting the user's reading experience.

2. **`current_agent` tracking**: Only yields status when agent changes to avoid redundant updates.

3. **Tool name formatting**: Converts `calculate` → `Calculate`, `format_text` → `Format Text` for better readability.

4. **Hasattr checks**: Safely checks for optional attributes that may not exist on all event types.

### Step 2: Update Event Handlers

#### For Assistant Thread Messages (`listeners/assistant/message.py`)

```python
def message(
    client: WebClient,
    context: BoltContext,
    logger: Logger,
    payload: dict,
    say: Say,
    set_status: SetStatus,
):
    try:
        channel_id = payload["channel"]
        team_id = context.team_id
        thread_ts = payload["thread_ts"]
        user_id = context.user_id

        # Set initial status
        set_status(status="is thinking...")

        # Fetch conversation history (existing code)
        replies = client.conversations_replies(
            channel=context.channel_id,
            ts=context.thread_ts,
            oldest=context.thread_ts,
            limit=10,
        )
        messages_in_thread: List[Dict[str, str]] = []
        for message in replies["messages"]:
            role = "user" if message.get("bot_id") is None else "assistant"
            messages_in_thread.append({"role": role, "content": message["text"]})

        # Create event loop for async operations
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        # Initialize Slack streaming
        streamer = client.chat_stream(
            channel=channel_id,
            recipient_team_id=team_id,
            recipient_user_id=user_id,
            thread_ts=thread_ts,
        )

        # Stream ADK response with dynamic status updates
        async def stream_response():
            async for event in call_llm(
                messages_in_thread, user_id=user_id, session_id=thread_ts
            ):
                if event["type"] == "status":
                    # Update loading message with real-time agent activity
                    logger.info(f"Setting Slack loading message to: {event['text']}")
                    client.assistant_threads_setStatus(
                        channel_id=channel_id,
                        thread_ts=thread_ts,
                        status="is working...",  # Generic status (may be translated)
                        loading_messages=[event["text"]],  # Specific detail (shows as-is)
                    )
                elif event["type"] == "content":
                    # Stream actual response content
                    if event["text"]:
                        streamer.append(markdown_text=event["text"])

        loop.run_until_complete(stream_response())
        loop.close()

        # Add feedback block and stop streaming
        feedback_block = create_feedback_block()
        streamer.stop(blocks=feedback_block)

    except Exception as e:
        logger.exception(f"Failed to handle a user message event: {e}")
        say(f":warning: Something went wrong! ({e})")
```

#### For App Mentions (`listeners/events/app_mentioned.py`)

```python
def app_mentioned_callback(client: WebClient, event: dict, logger: Logger, say: Say):
    try:
        channel_id = event.get("channel")
        team_id = event.get("team")
        text = event.get("text")
        thread_ts = event.get("thread_ts") or event.get("ts")
        user_id = event.get("user")

        # Set initial status
        client.assistant_threads_setStatus(
            channel_id=channel_id,
            thread_ts=thread_ts,
            status="is thinking...",
            loading_messages=["Starting to process your request..."],
        )

        # Create event loop
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        # Initialize streaming
        streamer = client.chat_stream(
            channel=channel_id,
            recipient_team_id=team_id,
            recipient_user_id=user_id,
            thread_ts=thread_ts,
        )

        # Stream response with dynamic status
        async def stream_response():
            async for event in call_llm(
                [{"role": "user", "content": text}],
                user_id=user_id,
                session_id=thread_ts,
            ):
                if event["type"] == "status":
                    logger.info(f"Setting Slack loading message to: {event['text']}")
                    client.assistant_threads_setStatus(
                        channel_id=channel_id,
                        thread_ts=thread_ts,
                        status="is working...",
                        loading_messages=[event["text"]],
                    )
                elif event["type"] == "content":
                    if event["text"]:
                        streamer.append(markdown_text=event["text"])

        loop.run_until_complete(stream_response())
        loop.close()

        feedback_block = create_feedback_block()
        streamer.stop(blocks=feedback_block)

    except Exception as e:
        logger.exception(f"Failed to handle a user message event: {e}")
        say(f":warning: Something went wrong! ({e})")
```

## Event Flow

### Complete Request-Response Cycle

```
┌─────────────────────────────────────────────────────────────────┐
│ 1. User sends message in Slack                                  │
└───────────────────────────────┬─────────────────────────────────┘
                                │
┌───────────────────────────────▼─────────────────────────────────┐
│ 2. Slack Event Handler receives message                         │
│    - Calls client.assistant_threads_setStatus()                 │
│    - Status: "is thinking..."                                   │
│    - Loading: "Starting to process..."                          │
└───────────────────────────────┬─────────────────────────────────┘
                                │
┌───────────────────────────────▼─────────────────────────────────┐
│ 3. call_llm() invoked with message history                      │
│    - Creates ADK session                                        │
│    - Calls runner.run_async()                                   │
└───────────────────────────────┬─────────────────────────────────┘
                                │
┌───────────────────────────────▼─────────────────────────────────┐
│ 4. ADK Event Stream begins                                      │
│                                                                  │
│    Event 1: author="CoordinatorAgent"                           │
│    └─> Yield: {"type": "status", "text": "CoordinatorAgent..."}│
│    └─> Update Slack: loading_messages=["CoordinatorAgent..."]  │
│                                                                  │
│    Event 2: actions.transfer_to_agent="MathAgent"              │
│    └─> Yield: {"type": "status", "text": "Consulting Math..."}│
│    └─> Update Slack: loading_messages=["Consulting Math..."]   │
│                                                                  │
│    Event 3: author="MathAgent"                                  │
│    └─> Yield: {"type": "status", "text": "MathAgent..."}      │
│    └─> Update Slack: loading_messages=["MathAgent..."]        │
│                                                                  │
│    Event 4: function_call="calculate"                           │
│    └─> Yield: {"type": "status", "text": "Using Calculate..."} │
│    └─> Update Slack: loading_messages=["Using Calculate..."]   │
│                                                                  │
│    Event 5: content="The result is 100"                        │
│    └─> Yield: {"type": "content", "text": "The result is 100"} │
│    └─> Stream to Slack: streamer.append("The result is 100")  │
│    └─> Set flag: has_started_streaming_content = True          │
│                                                                  │
└───────────────────────────────┬─────────────────────────────────┘
                                │
┌───────────────────────────────▼─────────────────────────────────┐
│ 5. Stream completes                                             │
│    - streamer.stop() called                                     │
│    - Status automatically cleared by Slack                      │
│    - User sees complete response                                │
└─────────────────────────────────────────────────────────────────┘
```

## Troubleshooting

### Issue: Custom status shows as "thinking", "evaluating", etc.

**Cause**: Slack translates the `status` parameter to predefined values.

**Solution**: Use `loading_messages` parameter for custom text:
```python
# ❌ This gets translated
status="MathAgent is working..."

# ✅ This displays as-is
status="is working...",
loading_messages=["MathAgent is working..."]
```

### Issue: Status updates don't appear

**Possible Causes:**

1. **Missing scope**: Ensure `assistant:write` scope is added to your Slack app
2. **Wrong parameters**: Verify `channel_id` and `thread_ts` are correct
3. **Status cleared too quickly**: Check if response starts streaming immediately

**Debug Steps:**
```python
# Add logging
logger.info(f"Setting status - channel: {channel_id}, thread: {thread_ts}")
logger.info(f"Status text: {status}, Loading: {loading_messages}")
```

### Issue: No agent or tool names detected

**Possible Causes:**

1. **Events not exposing expected attributes**: ADK version mismatch
2. **Agents responding without intermediate events**: Fast responses skip tool calls

**Debug Steps:**
```python
# Log all event attributes
logger.info(f"Event attributes: {dir(event)}")
logger.info(f"Event author: {event.author}")
logger.info(f"Has function_calls: {hasattr(event, 'get_function_calls')}")
```

### Issue: Async loop errors

**Error**: `RuntimeError: This event loop is already running`

**Cause**: Trying to create nested event loops.

**Solution**: Ensure you create a fresh loop:
```python
loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)
try:
    loop.run_until_complete(stream_response())
finally:
    loop.close()
```

## Best Practices

### 1. Stop Status Updates Before Content Streaming

Once you start streaming actual response content, stop sending status updates:

```python
has_started_streaming_content = False

if event["type"] == "content":
    has_started_streaming_content = True

if event["type"] == "status" and not has_started_streaming_content:
    # Only update status before content starts
    update_slack_status(event["text"])
```

**Rationale**: Avoids disrupting the user's reading experience with status changes.

### 2. Make Tool Names Human-Readable

Transform technical function names:

```python
tool_name = "calculate"
readable_name = tool_name.replace("_", " ").title()  # "Calculate"

tool_name = "format_text"
readable_name = tool_name.replace("_", " ").title()  # "Format Text"
```

### 3. Use Descriptive Status Messages

Be specific about what's happening:

```python
# ❌ Generic
"Processing..."

# ✅ Specific
"MathAgent is calculating..."
"Using Format Text tool..."
"Consulting InfoAgent for current time..."
```

### 4. Handle Errors Gracefully

Always clear status on errors:

```python
try:
    # Process events
    async for event in call_llm(...):
        # Handle event
except Exception as e:
    logger.exception(f"Error: {e}")
    # Clear status
    client.assistant_threads_setStatus(
        channel_id=channel_id,
        thread_ts=thread_ts,
        status="",  # Empty string clears status
    )
    # Notify user
    say(f":warning: Something went wrong!")
```

### 5. Log Extensively During Development

Add detailed logging to understand event flow:

```python
logger.info(f"ADK Event - Author: {event.author}")
logger.info(f"Has content: {bool(event.content)}")
logger.info(f"Function calls: {len(function_calls)}")
logger.info(f"Setting loading message to: {status_text}")
```

Remove or reduce verbosity in production.

### 6. Consider Rate Limiting

Slack API has rate limits. Avoid updating status too frequently:

```python
import time

last_status_update = 0
MIN_UPDATE_INTERVAL = 0.5  # seconds

current_time = time.time()
if current_time - last_status_update >= MIN_UPDATE_INTERVAL:
    client.assistant_threads_setStatus(...)
    last_status_update = current_time
```

### 7. Test with Different Agent Scenarios

Ensure your implementation works across different paths:

```python
# Math request (should show MathAgent + calculate tool)
"What is 25 times 4?"

# Text request (should show TextAgent + count_words tool)
"Count the words in this sentence"

# Info request (should show InfoAgent + get_current_time tool)
"What time is it?"

# Direct response (should show only CoordinatorAgent)
"Hello!"
```

## Example Output Scenarios

### Scenario 1: Math Calculation

**User**: "What is 15 * 8?"

**Status Updates**:
```
1. is thinking...
   "Starting to process your request..."

2. is working...
   "CoordinatorAgent is working..."

3. is working...
   "Consulting MathAgent..."

4. is working...
   "MathAgent is working..."

5. is working...
   "Using Calculate..."

6. [Status cleared, streaming response]
   "The result of 15 * 8 is 120."
```

### Scenario 2: Text Processing

**User**: "Count the words in this sentence please"

**Status Updates**:
```
1. is thinking...
   "Starting to process your request..."

2. is working...
   "CoordinatorAgent is working..."

3. is working...
   "Consulting TextAgent..."

4. is working...
   "TextAgent is working..."

5. is working...
   "Using Count Words..."

6. [Status cleared, streaming response]
   "There are 6 words in your sentence."
```

### Scenario 3: General Query

**User**: "Hello!"

**Status Updates**:
```
1. is thinking...
   "Starting to process your request..."

2. is working...
   "CoordinatorAgent is working..."

3. [Status cleared, streaming response]
   "Hello! How can I help you today?"
```

## Performance Considerations

### Event Processing Overhead

- Each status update makes an API call to Slack
- Typical latency: 50-200ms per call
- Impact: Minimal for most use cases

### Optimization Strategies

1. **Batch rapid updates**: If multiple events occur within 500ms, only send the latest
2. **Skip redundant updates**: Track last status sent, only update if changed
3. **Prioritize content**: Once streaming starts, ignore status events

### Memory Usage

- Event objects are processed in streaming fashion
- No large accumulation of events in memory
- Session history stored in ADK's session service

## Security Considerations

### 1. Sanitize Status Messages

Never include sensitive data in status updates:

```python
# ❌ Dangerous
status_text = f"Querying database for user {user_email}..."

# ✅ Safe
status_text = "Querying database..."
```

### 2. Validate Thread Context

Ensure the bot has access to the channel/thread:

```python
try:
    client.assistant_threads_setStatus(
        channel_id=channel_id,
        thread_ts=thread_ts,
        status="is working...",
    )
except SlackApiError as e:
    if e.response["error"] == "channel_not_found":
        logger.error("Bot not in channel")
        return
```

### 3. Rate Limit Per User

Prevent abuse by rate limiting status updates per user:

```python
from collections import defaultdict
import time

user_status_times = defaultdict(list)

def can_update_status(user_id: str, max_per_minute: int = 60) -> bool:
    now = time.time()
    user_times = user_status_times[user_id]
    # Remove times older than 1 minute
    user_times[:] = [t for t in user_times if now - t < 60]

    if len(user_times) >= max_per_minute:
        return False

    user_times.append(now)
    return True
```

## Extending the Implementation

### Adding Custom Event Types

Extend the event dictionary to include more information:

```python
# In ai/llm_caller.py
yield {
    "type": "status",
    "text": status_text,
    "agent": current_agent,  # Additional metadata
    "tool": tool_name,       # Additional metadata
}

# In event handler
if event["type"] == "status":
    # Use additional metadata for custom logic
    if event.get("tool") == "calculate":
        # Special handling for calculations
        pass
```

### Supporting Multiple Languages

Translate status messages based on user locale:

```python
TRANSLATIONS = {
    "en": {
        "working": "is working...",
        "consulting": "Consulting {agent}...",
        "using_tool": "Using {tool}...",
    },
    "es": {
        "working": "está trabajando...",
        "consulting": "Consultando {agent}...",
        "using_tool": "Usando {tool}...",
    },
}

def get_status_text(key: str, locale: str, **kwargs) -> str:
    template = TRANSLATIONS.get(locale, TRANSLATIONS["en"])[key]
    return template.format(**kwargs)
```

### Adding Progress Indicators

Show numerical progress for long operations:

```python
total_steps = 5
current_step = 0

async for event in runner.run_async(...):
    if event["type"] == "status":
        current_step += 1
        progress = f"[{current_step}/{total_steps}] {event['text']}"
        yield {"type": "status", "text": progress}
```

## Conclusion

This implementation provides users with transparency into the AI agent's decision-making process, enhancing trust and user experience. By leveraging ADK's event system and Slack's loading messages, you can create a sophisticated real-time status update system without significant performance overhead.

For questions or issues, refer to:
- [Slack API Documentation](https://api.slack.com/methods/assistant.threads.setStatus)
- [Google ADK Documentation](https://google.github.io/adk-docs/)
- [Project CLAUDE.md](./CLAUDE.md) for codebase-specific guidance
