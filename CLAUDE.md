# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

This is a Slack AI Agent App built with Bolt for Python, implementing a multi-agent system using Google ADK (Agent Development Kit) with Gemini models. The app provides AI-powered assistance through Slack's Assistant interface with streaming responses.

## Development Commands

### Environment Setup

```sh
# Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate  # Windows: .\.venv\Scripts\Activate

# Install dependencies
pip install -r requirements.txt
```

### Running the App

```sh
# Using Slack CLI (recommended)
slack run

# Or directly with Python
python3 app.py
```

### Code Quality

```sh
# Lint code
ruff check

# Format code
ruff format
```

### Testing

```sh
# Run all tests
pytest

# Run specific test file
pytest tests/test_file.py

# Run with verbose output
pytest -v
```

## Architecture

### Multi-Agent System

The application uses Google ADK to implement a hierarchical multi-agent architecture:

- **CoordinatorAgent** (`ai/agents.py:55-78`): Root agent that analyzes user requests and delegates to specialized agents
- **MathAgent** (`ai/agents.py:20-28`): Handles mathematical calculations and numerical operations
- **TextAgent** (`ai/agents.py:31-40`): Processes text formatting, word counting, and list creation
- **InfoAgent** (`ai/agents.py:43-52`): Provides current time, help information, and general queries

Each agent uses the `gemini-2.0-flash` model and has access to specific tools defined in `ai/tools.py`.

### Request Flow

1. **Entry Point** (`app.py`): Thin entry point that initializes the Bolt app and registers listeners
2. **Listener Registration** (`listeners/__init__.py`): Routes incoming Slack events to appropriate handlers
3. **Event Handlers**:
   - `listeners/assistant/message.py`: Handles messages in assistant threads
   - `listeners/events/app_mentioned.py`: Handles @mentions of the bot
   - `listeners/assistant/assistant_thread_started.py`: Sets up suggested prompts when threads start
4. **LLM Integration** (`ai/llm_caller.py`): Provides `call_llm()` async generator that streams responses from the ADK agent system
5. **Response Streaming**: Uses Slack's `chat_stream` API to stream chunks back to the user in real-time

### Key Design Patterns

- **Async Streaming**: All LLM responses are streamed using async generators to provide real-time feedback
- **Event Loop Management**: Creates new event loops in synchronous Bolt handlers to call async ADK functions
- **Session Management**: Uses thread timestamps as session IDs to maintain conversation context
- **Tool-Based Architecture**: Agents use Python functions as tools, automatically exposed to the LLM by ADK

## Configuration

### Required Environment Variables

```sh
SLACK_BOT_TOKEN=xoxb-...         # From OAuth & Permissions
SLACK_APP_TOKEN=xapp-...         # App-level token with connections:write
```

### Google ADK Authentication (one of):

```sh
# Option 1: Service account (production)
GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account-key.json

# Option 2: API key (development)
GOOGLE_API_KEY=your-api-key

# Option 3: Use `gcloud auth application-default login`
```

## Adding New Agents

To add a new specialized agent:

1. Create tools in `ai/tools.py` following the existing pattern (functions returning `Dict[str, Any]`)
2. Define the agent in `ai/agents.py`:
   ```python
   new_agent = Agent(
       name="AgentName",
       model="gemini-2.0-flash",
       description="When to use this agent",
       instruction="Detailed instructions for the agent",
       tools=[tool1, tool2],
   )
   ```
3. Add the agent to `coordinator_agent.sub_agents` list
4. Update the coordinator's instruction to explain when to delegate to the new agent

## Slack-Specific Conventions

- **Markdown Compatibility**: Agents are instructed to convert markdown to Slack-compatible format
- **Slack Syntax Preservation**: User mentions (`<@USER_ID>`) and channel mentions (`<#CHANNEL_ID>`) must be preserved as-is in responses
- **Status Messages**: Use playful loading messages during "thinking" state (see `listeners/assistant/message.py:40-46`)
- **Feedback Blocks**: Responses include feedback blocks for user interaction (`listeners/views/feedback_block.py`)

## Project Structure Notes

- `/listeners`: Organized by Slack Platform feature (events, assistant, actions, views)
- `/ai`: Contains all LLM and agent-related code, separated from Slack-specific logic
- Socket Mode is used for local development (no public URL required)
- For OAuth/distribution, use `app_oauth.py` instead of `app.py`
