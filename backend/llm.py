"""LLM interface for Gemini API."""

import os

from google import genai
from google.genai import types

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
    Send a message to Gemini and return its text reply.

    Args:
        user_message (str):
            The latest message typed by the user. Must be a non-empty string.

        conversation_history (list):
            Prior turns in Gemini's native format. Each item is a dict:
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
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key or not api_key.strip():
        return "Error: GEMINI_API_KEY environment variable is not set."

    # --- Build contents (do NOT mutate caller's list) ---
    contents = conversation_history + [
        {"role": "user", "parts": [{"text": user_message}]}
    ]

    # --- Config ---
    config = types.GenerateContentConfig(
        system_instruction=_SYSTEM_PROMPT,
        max_output_tokens=512,
        temperature=0.3,
    )

    # --- API call ---
    try:
        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=contents,
            config=config,
        )
        return response.text
    except Exception as e:
        return f"Error: Could not get a response from Gemini. Details: {str(e)}"
