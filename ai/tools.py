"""
Custom tools for ADK agents.

This module contains various tools that agents can use to perform specific tasks.
"""

import datetime
from typing import Dict, Any


def get_current_time() -> Dict[str, str]:
    """
    Get the current date and time.

    Returns:
        dict: A dictionary containing the current date and time information.
    """
    now = datetime.datetime.now()
    return {
        "status": "success",
        "current_time": now.strftime("%Y-%m-%d %H:%M:%S"),
        "day_of_week": now.strftime("%A"),
        "timezone": "UTC"
        if datetime.datetime.now().tzinfo is None
        else str(datetime.datetime.now().tzinfo),
    }


def calculate(expression: str) -> Dict[str, Any]:
    """
    Safely evaluate a mathematical expression.

    Args:
        expression (str): A mathematical expression to evaluate (e.g., "2 + 2", "10 * 5").

    Returns:
        dict: A dictionary containing the result or error message.
    """
    try:
        # Only allow safe mathematical operations
        allowed_chars = set("0123456789+-*/().  ")
        if not all(c in allowed_chars for c in expression):
            return {
                "status": "error",
                "message": "Invalid characters in expression. Only numbers and basic operators (+, -, *, /, parentheses) are allowed.",
            }

        result = eval(expression, {"__builtins__": {}}, {})
        return {"status": "success", "expression": expression, "result": result}
    except Exception as e:
        return {"status": "error", "message": f"Error evaluating expression: {str(e)}"}


def format_text(text: str, format_type: str = "uppercase") -> Dict[str, str]:
    """
    Format text in various ways.

    Args:
        text (str): The text to format.
        format_type (str): The type of formatting to apply.
            Options: 'uppercase', 'lowercase', 'title', 'reverse'.
            Defaults to 'uppercase'.

    Returns:
        dict: A dictionary containing the formatted text.
    """
    format_type = format_type.lower()

    if format_type == "uppercase":
        formatted = text.upper()
    elif format_type == "lowercase":
        formatted = text.lower()
    elif format_type == "title":
        formatted = text.title()
    elif format_type == "reverse":
        formatted = text[::-1]
    else:
        return {
            "status": "error",
            "message": f"Unknown format type: {format_type}. Use 'uppercase', 'lowercase', 'title', or 'reverse'.",
        }

    return {
        "status": "success",
        "original": text,
        "formatted": formatted,
        "format_type": format_type,
    }


def count_words(text: str) -> Dict[str, Any]:
    """
    Count words, characters, and sentences in a text.

    Args:
        text (str): The text to analyze.

    Returns:
        dict: A dictionary containing word count, character count, and sentence count.
    """
    words = text.split()
    sentences = text.count(".") + text.count("!") + text.count("?")

    return {
        "status": "success",
        "word_count": len(words),
        "character_count": len(text),
        "character_count_no_spaces": len(text.replace(" ", "")),
        "sentence_count": sentences if sentences > 0 else 1,
    }


def create_list(items: str, separator: str = ",") -> Dict[str, Any]:
    """
    Create a formatted list from comma-separated or custom-separated items.

    Args:
        items (str): Items separated by a delimiter.
        separator (str): The separator used between items. Defaults to comma.

    Returns:
        dict: A dictionary containing the formatted list.
    """
    item_list = [item.strip() for item in items.split(separator) if item.strip()]

    formatted_list = "\n".join([f"{i + 1}. {item}" for i, item in enumerate(item_list)])

    return {
        "status": "success",
        "item_count": len(item_list),
        "items": item_list,
        "formatted_list": formatted_list,
    }


def get_help_info() -> Dict[str, str]:
    """
    Get information about available tools and capabilities.

    Returns:
        dict: A dictionary containing help information.
    """
    return {
        "status": "success",
        "message": "I have access to several tools",
        "available_tools": [
            "get_current_time - Get current date and time",
            "calculate - Perform mathematical calculations",
            "format_text - Format text (uppercase, lowercase, title, reverse)",
            "count_words - Count words, characters, and sentences",
            "create_list - Create formatted lists from text",
        ],
    }
