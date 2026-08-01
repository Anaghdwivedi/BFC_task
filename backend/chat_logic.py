"""Chat routing and session state logic."""

import asyncio
import os
import sys

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from backend.llm import ask_llm

# ── Calculator definitions ─────────────────────────────────────────────────
CALCULATORS = {
    "loan_tenure": {
        "trigger_keywords": [
            "loan tenure", "loan period", "loan duration",
            "how long loan", "emi tenure",
        ],
        "inputs": ["P", "E", "R"],
        "questions": {
            "P": "What is the total loan amount? (in rupees, e.g. 500000)",
            "E": "What is your monthly EMI amount? (in rupees, e.g. 12000)",
            "R": "What is the annual interest rate? (as a percentage, e.g. 8.5)",
        },
        "confirm_template": (
            "Got it — Loan ₹{P} | EMI ₹{E} | Rate {R}%. Calculating..."
        ),
    },
    "sip": {
        "trigger_keywords": [
            "sip", "systematic investment", "monthly investment",
            "invest monthly", "reach a target", "target amount",
        ],
        "inputs": ["target", "R", "years"],
        "questions": {
            "target": "What is your target corpus amount? (in rupees, e.g. 1000000)",
            "R":      "What annual return rate do you expect? (as a percentage, e.g. 12)",
            "years":  "Over how many years do you want to invest? (e.g. 10)",
        },
        "confirm_template": (
            "Got it — Target ₹{target} | Return {R}% | Period {years} year(s). Calculating..."
        ),
    },
    "swp": {
        "trigger_keywords": [
            "swp", "systematic withdrawal", "withdraw monthly",
            "monthly withdrawal", "withdraw from corpus",
        ],
        "inputs": ["P", "years", "R", "W"],
        "questions": {
            "P":     "What is your lumpsum investment amount? (in rupees, e.g. 1000000)",
            "years": "Over how many years do you plan to withdraw? (e.g. 10)",
            "R":     "What annual return rate do you expect? (as a percentage, e.g. 8)",
            "W":     (
                "How much do you want to withdraw monthly? "
                "Enter a fixed amount (e.g. 8000) or a percentage of your corpus (e.g. 1%)"
            ),
        },
        "confirm_template": (
            "Got it — Corpus ₹{P} | Period {years} year(s) | Return {R}% | "
            "Withdrawal {W}/month. Calculating..."
        ),
    },
}


def make_session():
    """
    Create and return a fresh session state dict.
    Call this once per user session when they first connect.

    Returns:
        dict with keys:
            active_calculator (str|None): name of running calculator, or None
            collected_inputs  (dict):     inputs gathered so far for active calc
            conversation_history (list):  Gemini-format message history
    """
    return {
        "active_calculator": None,
        "collected_inputs": {},
        "conversation_history": [],
    }


# Messages that start with these words are conceptual questions — route to LLM
# even if they contain a calculator keyword (e.g. "What is SIP?").
_QUESTION_STARTERS = (
    "what", "how", "why", "who", "when", "where", "which",
    "explain", "define", "tell me about", "can you explain",
)


def _detect_calculator(user_message):
    """
    Check if user_message contains a trigger keyword for any calculator.

    Args:
        user_message (str): The raw user message.

    Returns:
        str | None: The calculator key ("loan_tenure", "sip", "swp")
                    or None if no keyword matched.
    """
    lowered = user_message.lower().lstrip()

    starts_with_question_word = any(lowered.startswith(p) for p in _QUESTION_STARTERS)

    if starts_with_question_word:
        # Bypass to LLM only for pure conceptual questions with no calculation intent.
        # Calculation intent is signalled by personal/quantitative markers:
        #   "my"      → "what is my loan period"    → calculator
        #   "how much"→ "how much SIP do I need?"   → calculator
        # Without these markers:
        #   "What is SIP?"             → LLM
        #   "How does loan tenure work?"→ LLM
        words = lowered.split()
        has_calc_intent = (
            "my" in words
            or "how much" in lowered
            or "how long" in lowered
            or "how many" in lowered
            or "i need" in lowered
            or "i want" in lowered
        )
        if not has_calc_intent:
            return None

    for calc_key, calc_def in CALCULATORS.items():
        for keyword in calc_def["trigger_keywords"]:
            if keyword in lowered:
                return calc_key
    return None


def _parse_numeric_input(raw):
    """
    Try to parse raw user input as a float.

    Args:
        raw (str): The raw string typed by the user.

    Returns:
        float | None: The parsed float, or None if parsing fails.
    """
    try:
        return float(raw.strip())
    except (ValueError, AttributeError):
        return None


_TOOL_NAMES = {
    "loan_tenure": "calculate_loan_tenure",
    "sip":         "calculate_sip",
    "swp":         "calculate_swp",
}


async def _mcp_call(tool_name: str, arguments: dict) -> str:
    """Open a stdio MCP session, call one tool, return its text result."""
    server_params = StdioServerParameters(
        command=sys.executable,
        args=["-m", "backend.mcp_server"],
        env=os.environ.copy(),
    )
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            result = await session.call_tool(tool_name, arguments)
            return result.content[0].text


def _call_via_mcp(calc_key: str, inputs: dict) -> str:
    """
    Resolve inputs to the correct types, then invoke the matching
    calculator via the MCP server subprocess.

    Args:
        calc_key (str): One of "loan_tenure", "sip", "swp".
        inputs   (dict): All collected inputs for this calculator.

    Returns:
        str: The calculator result string or an error string.
    """
    tool_name = _TOOL_NAMES.get(calc_key)
    if tool_name is None:
        return "Error: Unknown calculator."

    try:
        if calc_key == "loan_tenure":
            args = {
                "P": float(inputs["P"]),
                "E": float(inputs["E"]),
                "R": float(inputs["R"]),
            }
        elif calc_key == "sip":
            args = {
                "target": float(inputs["target"]),
                "R":      float(inputs["R"]),
                "years":  float(inputs["years"]),
            }
        elif calc_key == "swp":
            # W may be a percentage string — resolve to a float before the MCP call
            # (the MCP server's inputSchema for W is number-only)
            w_raw = inputs["W"].strip()
            if w_raw.endswith("%"):
                pct   = float(w_raw.rstrip("%"))
                w_val = float(inputs["P"]) * pct / 100
            else:
                try:
                    w_val = float(w_raw)
                except ValueError:
                    return "Error: Withdrawal amount must be a number or a percentage like '1%'."
            args = {
                "P":     float(inputs["P"]),
                "years": float(inputs["years"]),
                "R":     float(inputs["R"]),
                "W":     w_val,
            }
        else:
            return "Error: Unknown calculator."

        return asyncio.run(_mcp_call(tool_name, args))

    except Exception as e:
        return f"Error: Calculator call failed. Details: {str(e)}"


def _run_calculator(calc_key, inputs):
    """
    Delegate to the MCP client. Calculators are now invoked as MCP tools
    via a stdio subprocess rather than direct function calls.

    Args:
        calc_key (str): One of "loan_tenure", "sip", "swp".
        inputs   (dict): All collected inputs for this calculator.

    Returns:
        str: The calculator result string or an error string.
    """
    return _call_via_mcp(calc_key, inputs)


def handle_message(user_message, session):
    """
    Process one user message and return the bot's reply.

    This function is the single entry point for all chat logic.
    It modifies session state in-place.

    Args:
        user_message (str): The raw text from the user.
        session      (dict): The session state dict from make_session().
                             Modified in-place by this function.

    Returns:
        str: The bot's reply to display to the user.

    Session state keys used:
        session["active_calculator"]    (str|None)
        session["collected_inputs"]     (dict)
        session["conversation_history"] (list)

    Branch logic:
        A — Calculator is already running  → collect next input or run calc
        B — No calc running, keyword found → start calculator flow
        C — No calc, no keyword            → pass to LLM
    """
    # --- Guard: basic input check ---
    if not isinstance(user_message, str) or not user_message.strip():
        return "Please type a message."

    user_message = user_message.strip()

    # ── BRANCH A: A calculator is already running ──────────────────────────
    if session["active_calculator"] is not None:
        calc_key = session["active_calculator"]
        calc_def = CALCULATORS[calc_key]
        inputs   = session["collected_inputs"]
        all_keys = calc_def["inputs"]

        # Find the next input we still need
        next_key = None
        for key in all_keys:
            if key not in inputs:
                next_key = key
                break

        # next_key should never be None here (would mean all inputs already collected
        # but we haven't run the calculator yet — defensive guard)
        if next_key is None:
            session["active_calculator"] = None
            session["collected_inputs"]  = {}
            return "Something went wrong with the calculator state. Please start again."

        # Special handling: W field for SWP accepts "%" strings
        if next_key == "W":
            raw = user_message.strip()
            if raw.endswith("%"):
                inputs["W"] = raw
            else:
                val = _parse_numeric_input(raw)
                if val is None:
                    return (
                        "That doesn't look like a valid amount. "
                        "Please enter a number (e.g. 8000) or a percentage (e.g. 1%)."
                    )
                inputs["W"] = raw
        else:
            # All other fields must be a positive number
            val = _parse_numeric_input(user_message)
            if val is None or val <= 0:
                question = calc_def["questions"][next_key]
                return (
                    f"That doesn't look like a valid positive number. "
                    f"{question}"
                )
            inputs[next_key] = user_message.strip()

        # Check if we still have remaining inputs needed
        remaining = [k for k in all_keys if k not in inputs]

        if remaining:
            return calc_def["questions"][remaining[0]]

        # All inputs collected — confirm, run, clear state
        confirm_msg = calc_def["confirm_template"].format(**inputs)
        result      = _run_calculator(calc_key, inputs)

        session["active_calculator"] = None
        session["collected_inputs"]  = {}

        return f"{confirm_msg}\n\n{result}"

    # ── BRANCH B: No calculator running — check for keyword trigger ────────
    triggered = _detect_calculator(user_message)

    if triggered is not None:
        calc_def       = CALCULATORS[triggered]
        first_key      = calc_def["inputs"][0]
        first_question = calc_def["questions"][first_key]

        session["active_calculator"] = triggered
        session["collected_inputs"]  = {}

        return (
            f"Sure! I can help you calculate that.\n"
            f"{first_question}"
        )

    # ── BRANCH C: No calculator trigger — pass to LLM ─────────────────────
    history = session["conversation_history"]
    reply   = ask_llm(user_message, history)

    # Update history ONLY on LLM path — calculator turns are structured state
    history.append({"role": "user",  "parts": [{"text": user_message}]})
    history.append({"role": "model", "parts": [{"text": reply}]})

    return reply
