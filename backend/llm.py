"""LLM interface — Claude (Anthropic API)."""

import os

import anthropic

_SYSTEM_PROMPT = (
    "You are a financial assistant. Your job is to help users with financial "
    "topics only — savings, loans, investing, interest rates, budgeting, SIP, "
    "SWP, EMI, mutual funds, and related subjects. "
    "If the user asks about anything outside of finance (weather, sports, coding "
    "help, general trivia, personal advice unrelated to money, etc.), politely "
    "decline and redirect them back to finance topics. "
    "Be concise, clear, and helpful."
)


def ask_llm(user_message, conversation_history):
    """
    Send a message to Claude and return its text reply.

    Args:
        user_message (str):
            The latest message typed by the user. Must be a non-empty string.

        conversation_history (list):
            Prior turns stored in Gemini-compatible format:
                {"role": "user" | "model", "parts": [{"text": "..."}]}
            Pass an empty list [] if this is the first message.
            This list is NOT mutated — the caller owns it.

    Returns:
        str: The model's reply text, or a plain English error message string.
    """
    # --- Input validation ---
    if not isinstance(user_message, str) or not user_message.strip():
        return "Error: Message cannot be empty."

    if not isinstance(conversation_history, list):
        return "Error: Conversation history must be a list."

    # --- API key ---
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key or not api_key.strip():
        return "Error: ANTHROPIC_API_KEY environment variable is not set."

    # --- Convert history from internal format to Anthropic format ---
    # Internal: {"role": "user"|"model", "parts": [{"text": "..."}]}
    # Anthropic: {"role": "user"|"assistant", "content": "..."}
    messages = []
    for turn in conversation_history:
        role = "assistant" if turn["role"] == "model" else turn["role"]
        text = turn["parts"][0]["text"]
        messages.append({"role": role, "content": text})

    messages.append({"role": "user", "content": user_message})

    # --- API call ---
    try:
        client = anthropic.Anthropic(api_key=api_key)
        response = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=512,
            temperature=0.3,
            system=_SYSTEM_PROMPT,
            messages=messages,
        )
        return response.content[0].text
    except Exception as e:
        return f"Error: Could not get a response from Claude. Details: {str(e)}"
