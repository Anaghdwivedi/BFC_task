# Financial Chatbot

A conversational financial assistant built with Python Flask and **Anthropic Claude** (`claude-haiku-4-5-20251001`). The chatbot handles general finance questions through the LLM and runs three interactive calculators — Loan Tenure, SIP, and SWP — collecting inputs one at a time in a natural chat flow. Calculators are exposed as **MCP (Model Context Protocol) tools** and invoked via a stdio subprocess.

---

## Features

- **Finance-only scope** — politely declines off-topic questions and redirects to finance
- **Interactive calculators** — collects inputs conversationally, one question per turn
  - **Loan Tenure** — how long to repay a loan given principal, EMI, and interest rate
  - **SIP** — required monthly investment to reach a target corpus
  - **SWP** — final balance and withdrawal summary for a systematic withdrawal plan
- **Input validation** — catches non-numeric and non-positive inputs with a helpful re-prompt
- **Session isolation** — each browser tab gets its own independent session
- **MCP integration (bonus)** — calculators are registered as MCP tools; the chatbot calls them via a stdio MCP server subprocess rather than direct function calls

---

## LLM Used

**Anthropic Claude — `claude-haiku-4-5-20251001`**

- API: [Anthropic Messages API](https://docs.anthropic.com/en/api/messages)
- SDK: `anthropic` Python package
- System prompt enforces finance-only scope
- Temperature: 0.3 for consistent, factual answers
- Max tokens: 512

---

## Project Structure

```
financial-chatbot/
├── requirements.txt
├── .env.example          # Copy to .env and fill in your API key
├── backend/
│   ├── app.py            # Flask server, routes, session store
│   ├── chat_logic.py     # Message routing, calculator state machine, MCP client
│   ├── calculators.py    # Pure math functions (Loan Tenure, SIP, SWP)
│   ├── llm.py            # Anthropic Claude API wrapper
│   └── mcp_server.py     # MCP server — exposes calculators as tools over stdio
├── frontend/
│   └── index.html        # Self-contained chat UI (no external dependencies)
└── tests/
    └── test_e2e.py       # 26-scenario end-to-end test suite
```

---

## Prerequisites

- Python 3.8+
- An [Anthropic API key](https://console.anthropic.com/)

---

## Setup & Run

**1. Clone the repository**

```bash
git clone https://github.com/Anaghdwivedi/BFC_task.git
cd BFC_task
```

**2. Install dependencies**

```bash
pip install -r requirements.txt
```

**3. Set your Anthropic API key**

Windows (PowerShell):
```bash
$env:ANTHROPIC_API_KEY="your_api_key_here"
```

Windows (Command Prompt):
```bash
set ANTHROPIC_API_KEY=your_api_key_here
```

macOS / Linux:
```bash
export ANTHROPIC_API_KEY=your_api_key_here
```

**4. Start the server**

```bash
python -m flask --app backend.app run --host 0.0.0.0 --port 5000
```

**5. Open the chat UI**

Navigate to: [http://localhost:5000/ui](http://localhost:5000/ui)

---

## Example Conversations

### 1 — General finance question

```
You:  What is the difference between SIP and lump sum investing?

Bot:  SIP (Systematic Investment Plan) spreads your investment across many
      smaller amounts over time, reducing timing risk through rupee-cost
      averaging. A lump sum puts all your money in at once, which can yield
      higher returns in a consistently rising market but carries more timing
      risk. SIP is generally recommended for salaried investors with a
      regular income.
```

---

### 2 — Off-topic question declined

```
You:  What's the weather today?

Bot:  I'm only able to help with financial topics. Could I assist you with
      savings, investments, EMIs, or any other finance question?

You:  Write me a Python function to sort a list.

Bot:  That's outside my area — I can only help with finance-related topics
      like budgeting, loans, SIP, SWP, or investing. Let me know if you
      have a financial question!
```

---

### 3 — Full Loan Tenure calculator walkthrough

Trigger phrases: *"calculate my loan tenure"*, *"what is my loan period"*, *"EMI tenure"*

```
You:  Calculate my loan tenure

Bot:  Sure! I can help you calculate that.
      What is the total loan amount? (in rupees, e.g. 500000)

You:  1000000

Bot:  What is your monthly EMI amount? (in rupees, e.g. 12000)

You:  12000

Bot:  What is the annual interest rate? (as a percentage, e.g. 8.5)

You:  10

Bot:  Got it — Loan ₹1000000 | EMI ₹12000 | Rate 10%. Calculating...

      Loan Tenure: 11 year(s) and 6 month(s)
```

---

## API Reference

### `POST /chat`

**Request body:**
```json
{
  "message": "Calculate my loan tenure",
  "session_id": "any-unique-string"
}
```

**Response:**
```json
{
  "reply": "Sure! I can help you calculate that.\nWhat is the total loan amount? ..."
}
```

**Validation errors (HTTP 400):**
```json
{
  "error": "Field 'message' must be a non-empty string."
}
```

### `GET /`

Health check — returns `{"status": "ok", "message": "Financial Chatbot API is running."}`.

### `GET /ui`

Serves the frontend chat page.

---

## End-to-End Tests

Run the full 26-scenario test suite (requires `ANTHROPIC_API_KEY` for LLM scenarios):

```bash
python tests/test_e2e.py
```

26/26 PASS on a live run with the API key set.

---

## MCP Integration (Bonus)

The three calculators are registered as MCP tools in `backend/mcp_server.py` and served over stdio transport. When a calculator is triggered, `chat_logic.py` launches the MCP server as a subprocess and calls the appropriate tool via a JSON-RPC session rather than calling the math functions directly.

**Tools exposed:**
| Tool | Inputs |
|---|---|
| `calculate_loan_tenure` | `P` (principal), `E` (EMI), `R` (annual rate %) |
| `calculate_sip` | `target` (corpus), `R` (annual return %), `years` |
| `calculate_swp` | `P` (corpus), `years`, `R` (annual return %), `W` (monthly withdrawal) |

---

## Environment Variables

| Variable | Required | Description |
|---|---|---|
| `ANTHROPIC_API_KEY` | Yes | Anthropic API key — used only in `backend/llm.py` |

---

## Design Decisions

- **Session state in memory** — `SESSIONS` is a plain Python dict keyed by `session_id`. No database required; sessions reset when the server restarts.
- **No LLM for calculators** — calculator inputs are collected through a deterministic state machine. The LLM is only called for free-text finance questions, making calculator behaviour predictable and testable without an API key.
- **Smart keyword routing** — messages starting with question words ("what", "how", "why", etc.) go to the LLM unless they contain personal/quantitative intent markers like "my", "how much", or "how long". This prevents "What is SIP?" from accidentally triggering the SIP calculator while still routing "What is my loan period?" to the Loan Tenure calculator.
- **MCP over stdio** — each calculator invocation spawns a fresh MCP subprocess, sends a JSON-RPC `tools/call` request, and reads the result. This demonstrates the MCP protocol end-to-end without requiring a persistent background process.
- **Positive-value validation at collection time** — negative numbers are rejected immediately with a re-prompt rather than accepted and failing later in the math function.
- **XSS safety** — the frontend sets `textContent` (not `innerHTML`) on all bot replies.
