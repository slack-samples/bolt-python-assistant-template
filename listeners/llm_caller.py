import os
from typing import List, Dict
from langchain_groq import ChatGroq

# Set Groq API Key (consider using environment variables instead of hardcoding)
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
if not GROQ_API_KEY:
    raise ValueError("GROQ_API_KEY environment variable is not set")

DEFAULT_SYSTEM_CONTENT = """
You are EthicALL, a smart, empathetic AI assistant. When mentioned directly:
1. Respond to general questions while maintaining your compliance focus
2. Politely redirect non-compliance questions to your core purpose
3. Always maintain professional tone
4. Keep responses concise (1-3 paragraphs max)
You are strictly prohibited from answering irrelevant questions. Do only what is your profession.
Your purpose is to protect the organization and its people while maintaining a positive, collaborative environment.
"""

def call_llm(
    messages_in_thread: List[Dict[str, str]],
    system_content: str = DEFAULT_SYSTEM_CONTENT,
) -> str:
    """
    Call the Groq LLM with the given messages and system content.

    Args:
        messages_in_thread: List of message dictionaries with 'role' and 'content' keys
        system_content: System message content to set context for the LLM

    Returns:
        str: Raw response from the LLM
    """
    if not isinstance(messages_in_thread, list):
        raise TypeError("messages_in_thread must be a list of dictionaries")

    llm = ChatGroq(model="llama3-8b-8192", groq_api_key=GROQ_API_KEY)

    messages = [{"role": "system", "content": system_content}]
    messages.extend(messages_in_thread)

    try:
        response = llm.invoke(messages)
        if isinstance(response, dict) and "content" in response:
            return response["content"]
        else:
            return str(response)
    except Exception as e:
        raise RuntimeError(f"Error calling Groq LLM: {str(e)}")
