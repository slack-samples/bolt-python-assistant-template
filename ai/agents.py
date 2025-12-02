"""
Multi-agent system using Google ADK.

This module defines a multi-agent system with specialized agents for different tasks.
"""

from google.adk.agents import Agent
from google.adk.models.lite_llm import LiteLlm

from .tools import (
    get_current_time,
    calculate,
    format_text,
    count_words,
    create_list,
    get_help_info,
)

# Configure OpenAI model via LiteLLM
# Requires OPENAI_API_KEY environment variable
openai_model = LiteLlm(model="openai/gpt-4o")


# Specialized agent for mathematical operations
math_agent = Agent(
    name="MathAgent",
    model=openai_model,
    description="Specializes in mathematical calculations and numerical operations. Use this agent for any math-related queries.",
    instruction="""You are a mathematical expert. You can perform calculations, solve equations,
    and help with numerical problems. Use the calculate tool to evaluate mathematical expressions.
    Always explain your calculations clearly.""",
    tools=[calculate],
)

# Specialized agent for text processing
text_agent = Agent(
    name="TextAgent",
    model=openai_model,
    description="Specializes in text processing, formatting, and analysis. Use this agent for text manipulation tasks.",
    instruction="""You are a text processing expert. You can format text, count words,
    create lists, and analyze text content. Use the available tools to help users with text-related tasks.
    When you include markdown text, convert them to Slack compatible ones.
    When a prompt has Slack's special syntax like <@USER_ID> or <#CHANNEL_ID>, you must keep them as-is in your response.""",
    tools=[format_text, count_words, create_list],
)

# Specialized agent for information and utilities
info_agent = Agent(
    name="InfoAgent",
    model=openai_model,
    description="Provides general information, current time, and help about available capabilities.",
    instruction="""You are an information assistant. You can provide the current time,
    help users understand what tools are available, and answer general questions.
    When you include markdown text, convert them to Slack compatible ones.
    When a prompt has Slack's special syntax like <@USER_ID> or <#CHANNEL_ID>, you must keep them as-is in your response.""",
    tools=[get_current_time, get_help_info],
)

# Coordinator agent that routes requests to specialized agents
coordinator_agent = Agent(
    name="CoordinatorAgent",
    model=openai_model,
    description="Main coordinator that routes user requests to specialized agents.",
    instruction="""You are a helpful assistant coordinator in a Slack workspace.
    Users in the workspace will ask you to help them with various tasks.

    You have access to specialized agents:
    - MathAgent: For mathematical calculations and numerical operations
    - TextAgent: For text processing, formatting, and analysis
    - InfoAgent: For general information, current time, and help

    Analyze the user's request and delegate to the appropriate specialized agent:
    - For math problems, calculations, or numerical queries -> use MathAgent
    - For text formatting, word counting, or list creation -> use TextAgent
    - For time queries, help requests, or general information -> use InfoAgent
    - For general conversation or questions that don't fit the above -> answer directly

    When you include markdown text, convert them to Slack compatible ones.
    When a prompt has Slack's special syntax like <@USER_ID> or <#CHANNEL_ID>, you must keep them as-is in your response.

    Always be professional, helpful, and friendly in your responses.""",
    sub_agents=[math_agent, text_agent, info_agent],
)


def get_root_agent() -> Agent:
    """
    Get the root coordinator agent for the multi-agent system.

    Returns:
        Agent: The coordinator agent that routes requests to specialized agents.
    """
    return coordinator_agent
