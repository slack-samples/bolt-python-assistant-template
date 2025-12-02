# Migration from OpenAI to Google ADK

This document explains the changes made to migrate from OpenAI to Google's Agent Development Kit (ADK) with a multi-agent system.

## Overview of Changes

### 1. Dependencies Updated

**Before:**
```
openai
```

**After:**
```
google-adk
google-genai
```

### 2. Multi-Agent Architecture

The application now uses a multi-agent system with specialized agents:

#### **CoordinatorAgent** (Root Agent)
- Routes user requests to appropriate specialized agents
- Handles general conversation
- Manages the overall interaction flow

#### **MathAgent**
- Specializes in mathematical calculations
- Tools: `calculate()`
- Handles: Math problems, numerical operations, equations

#### **TextAgent**
- Specializes in text processing and analysis
- Tools: `format_text()`, `count_words()`, `create_list()`
- Handles: Text formatting, word counting, list creation

#### **InfoAgent**
- Provides general information and utilities
- Tools: `get_current_time()`, `get_help_info()`
- Handles: Time queries, help requests, general information

### 3. Custom Tools

New tools have been created in `ai/tools.py`:

- **get_current_time()**: Returns current date and time
- **calculate()**: Safely evaluates mathematical expressions
- **format_text()**: Formats text (uppercase, lowercase, title, reverse)
- **count_words()**: Counts words, characters, and sentences
- **create_list()**: Creates formatted lists from text
- **get_help_info()**: Provides information about available tools

### 4. Streaming Implementation

The streaming mechanism has been updated to work with ADK events:

**Before (OpenAI):**
```python
for event in returned_message:
    if event.type == "response.output_text.delta":
        streamer.append(markdown_text=f"{event.delta}")
```

**After (ADK):**
```python
async for event in call_llm(messages_in_thread, user_id=user_id, session_id=thread_ts):
    if event.content and event.content.parts:
        for part in event.content.parts:
            if part.text:
                streamer.append(markdown_text=part.text)
```

### 5. Session Management

ADK uses session-based conversation management:
- Each user/thread combination gets a unique session
- Sessions maintain conversation history automatically
- No need to manually pass full conversation history

## File Changes

### New Files
- `ai/agents.py` - Multi-agent system definition
- `ai/tools.py` - Custom tools for agents
- `MIGRATION_GUIDE.md` - This file

### Modified Files
- `requirements.txt` - Updated dependencies
- `ai/llm_caller.py` - Rewritten to use ADK
- `listeners/assistant/message.py` - Updated for ADK streaming
- `listeners/events/app_mentioned.py` - Updated for ADK streaming
- `.env.sample` - Updated environment variables
- `README.md` - Updated documentation

## Setup Instructions

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Set Up Google Cloud Authentication

Choose one of the following methods:

#### Option A: Service Account (Recommended for Production)
1. Create a Google Cloud project
2. Enable Vertex AI API
3. Create a service account and download JSON key
4. Set in `.env`:
```
GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account-key.json
```

#### Option B: API Key (Simpler for Development)
1. Get API key from [Google AI Studio](https://aistudio.google.com/app/apikey)
2. Set in `.env`:
```
GOOGLE_API_KEY=YOUR_GOOGLE_API_KEY
```

#### Option C: Application Default Credentials
```bash
gcloud auth application-default login
```

### 3. Run the Application

```bash
python3 app.py
```

## Testing the Multi-Agent System

### Test MathAgent
Send messages like:
- "Calculate 25 * 4 + 10"
- "What is 100 divided by 5?"
- "Solve 2 + 2"

### Test TextAgent
Send messages like:
- "Format 'hello world' in uppercase"
- "Count words in: The quick brown fox jumps over the lazy dog"
- "Create a list from: apples, oranges, bananas"

### Test InfoAgent
Send messages like:
- "What time is it?"
- "What can you do?"
- "Help me understand your capabilities"

### Test Coordinator
Send general messages:
- "Hello, how are you?"
- "Tell me about yourself"
- The coordinator will handle these directly or route to appropriate agents

## Key Benefits

1. **Modularity**: Each agent has a specific responsibility
2. **Extensibility**: Easy to add new agents and tools
3. **Scalability**: Agents can be deployed independently
4. **Maintainability**: Clear separation of concerns
5. **Tool Integration**: Rich ecosystem of tools available
6. **Session Management**: Built-in conversation history

## Troubleshooting

### Authentication Issues
- Ensure Google Cloud credentials are properly set
- Check that Vertex AI API is enabled in your project
- Verify API key is valid (if using API key method)

### Streaming Issues
- ADK events are asynchronous - ensure async/await is properly used
- Check that event loop is created correctly in synchronous contexts

### Agent Routing Issues
- Verify agent descriptions are clear and distinct
- Check that coordinator instructions properly describe when to use each agent
- Review agent logs to see routing decisions

## Future Enhancements

Potential improvements to consider:

1. **Add More Specialized Agents**:
   - SearchAgent for web searches
   - DataAgent for database queries
   - CodeAgent for code generation

2. **Enhance Tools**:
   - Add external API integrations
   - Implement more complex calculations
   - Add file processing capabilities

3. **Improve Routing**:
   - Implement more sophisticated routing logic
   - Add agent selection confidence scores
   - Enable multi-agent collaboration

4. **Add Observability**:
   - Integrate with Google Cloud Trace
   - Add custom logging for agent decisions
   - Implement performance monitoring

## Resources

- [Google ADK Documentation](https://google.github.io/adk-docs/)
- [Multi-Agent Systems Guide](https://google.github.io/adk-docs/agents/multi-agents/)
- [Function Tools Documentation](https://google.github.io/adk-docs/tools/function-tools/)
- [Slack AI Apps Documentation](https://docs.slack.dev/ai/)

