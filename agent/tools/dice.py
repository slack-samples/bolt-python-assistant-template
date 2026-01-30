import random

from openai.types.responses import FunctionToolParam


def roll_dice(sides: int = 6, count: int = 1) -> dict:
    if sides < 2:
        return {
            "error": "A die must have at least 2 sides",
            "rolls": [],
            "total": 0,
        }

    if count < 1:
        return {
            "error": "Must roll at least 1 die",
            "rolls": [],
            "total": 0,
        }

    # Roll the dice and calculate the total
    rolls = [random.randint(1, sides) for _ in range(count)]
    total = sum(rolls)

    return {
        "rolls": rolls,
        "total": total,
        "description": f"Rolled a {count}d{sides} to total {total}",
    }


# Tool definition for OpenAI API
#
# https://platform.openai.com/docs/guides/function-calling
roll_dice_definition: FunctionToolParam = {
    "type": "function",
    "name": "roll_dice",
    "description": "Roll one or more dice with a specified number of sides. Use this when the user wants to roll dice or generate random numbers within a range.",
    "parameters": {
        "type": "object",
        "properties": {
            "sides": {
                "type": "integer",
                "description": "The number of sides on the die (e.g., 6 for a standard die, 20 for a d20)",
                "default": 6,
            },
            "count": {
                "type": "integer",
                "description": "The number of dice to roll",
                "default": 1,
            },
        },
        "required": ["sides", "count"],
    },
    "strict": False,
}
