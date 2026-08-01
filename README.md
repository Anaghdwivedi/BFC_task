# Financial Chatbot

A conversational financial assistant built with Python Flask and Google Gemini. The chatbot handles general finance questions through an LLM and runs three interactive calculators — Loan Tenure, SIP, and SWP — collecting inputs one at a time in a natural chat flow.

---

## Features

- **Finance-only scope** — politely declines off-topic questions and redirects to finance
- **Interactive calculators** — collects inputs conversationally, one question per turn
  - **Loan Tenure** — how long to repay a loan given principal, EMI, and interest rate
  - **SIP** — required monthly investment to reach a target corpus
  - **SWP** — final balance and withdrawal summary for a systematic withdrawal plan
- **Input validation** — catches non-numeric and non-positive inputs at collection time with a helpful re-prompt
- **Session isolation** — each browser tab gets its own independent session

---

## Project Structure

```
financial-chatbot/
├── requirements.txt
├── backend/
│   ├── app.py            # Flask server, routes, session store
│   ├── chat_logic.py     # Message routing, calculator state machine
│   ├── calculators.py    # Pure math functions (Loan Tenure, SIP, SWP)
│   └── llm.py            # Gemini API wrapper (google-genai SDK)
└── frontend/
    └── index.html        # Self-contained chat UI (no external dependencies)
```

---

## Prerequisites

- Python 3.8+
- A [Google Gemini API key](https://aistudio.google.com/app/apikey)

---

## Setup & Run

**1. Clone or unzip the project**

```bash
cd financial-chatbot
```

**2. Install dependencies**

```bash
pip install -r requirements.txt
```

**3. Set your Gemini API key**

Windows (Command Prompt):
```bash
set GEMINI_API_KEY=your_api_key_here
```

Windows (PowerShell):
```bash
$env:GEMINI_API_KEY="your_api_key_here"
```

macOS / Linux:
```bash
export GEMINI_API_KEY=your_api_key_here
```

**4. Start the server**

```bash
python -m flask --app backend.app run --host 0.0.0.0 --port 5000
```

**5. Open the chat UI**

Navigate to: [http://localhost:5000/ui](http://localhost:5000/ui)

---

## Usage

### General finance questions

Type any finance question and the assistant will answer using Gemini:

```
You:  What is the difference between SIP and lump sum investing?
Bot:  SIP (Systematic Investment Plan) spreads your investment across many
      smaller amounts over time, reducing timing risk through rupee-cost
      averaging. Lump sum investing puts all your money in at once...
```

Off-topic questions are politely declined:

```
You:  What's the weather today?
Bot:  I'm only able to help with financial topics. Could I assist you with
      savings, investments, EMIs, or any other finance question?
```

### Loan Tenure Calculator

Trigger with phrases like: *"Calculate my loan tenure"*, *"loan period"*, *"EMI tenure"*

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

### SIP Calculator

Trigger with phrases like: *"SIP calculation"*, *"monthly investment"*, *"target amount"*

### SWP Calculator

Trigger with phrases like: *"SWP"*, *"systematic withdrawal"*, *"withdraw monthly"*

```
You:  I want to do SWP
Bot:  Sure! I can help you calculate that.
      What is your lumpsum investment amount? (in rupees, e.g. 1000000)

You:  2000000
Bot:  Over how many years do you plan to withdraw? (e.g. 10)

You:  15
Bot:  What annual return rate do you expect? (as a percentage, e.g. 8)

You:  9
Bot:  How much do you want to withdraw monthly? Enter a fixed amount (e.g. 8000)
      or a percentage of your corpus (e.g. 1%)

You:  15000
Bot:  Got it — Corpus ₹2000000 | Period 15 year(s) | Return 9% | Withdrawal 15000/month.

      SWP Results:
        Final Balance:     ₹1785386.90
        Total Withdrawn:   ₹2700000.00
        Total Profit/Loss: ₹2485386.90
```

---

## API Reference

The frontend communicates with the backend over a single endpoint.

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

Run the test suite (requires `GEMINI_API_KEY` to be set for LLM scenarios):

```bash
PYTHONIOENCODING=utf-8 python tests/test_e2e.py
```

| Scenario | What is tested | Result |
|---|---|---|
| 1 — General finance question | "What is SIP?" routed to LLM | ✅ PASS |
| 2 — Off-topic refusal | "What's the weather today?" declined | ✅ PASS |
| 3 — Loan Tenure happy path | Full 4-turn calculator walkthrough | ✅ PASS |
| 4 — EMI too low edge case | Error detected, clear message returned | ✅ PASS |
| 5 — Negative input + recovery | Bad input rejected, session continues | ✅ PASS |
| 6 — Full SWP walkthrough | Full 5-turn calculator walkthrough | ✅ PASS |

Scenarios 1 and 2 require `GEMINI_API_KEY` to reach the LLM. Scenarios 3–6 (calculators) run without an API key.

---

## Environment Variables

| Variable | Required | Description |
|---|---|---|
| `GEMINI_API_KEY` | Yes | Google Gemini API key — used only in `backend/llm.py` |
| `PORT` | No | Server port (default: `5000`) |

---

## Design Decisions

- **Session state in memory** — `SESSIONS` is a plain Python dict keyed by `session_id`. No database required; sessions reset when the server restarts.
- **No LLM for calculators** — calculator inputs are collected through a deterministic state machine (`chat_logic.py`). The LLM is only called for free-text finance questions. This makes calculator behaviour predictable and testable without an API key.
- **Calculator keyword bypass for questions** — messages starting with "what", "how", "why", etc. go directly to the LLM even if they contain calculator keywords (e.g. "What is SIP?"), preventing accidental calculator triggers.
- **Positive-value validation at collection time** — negative numbers are rejected immediately with a re-prompt rather than accepted and failing later in the math function.
- **XSS safety** — the frontend sets `textContent` (not `innerHTML`) on all bot replies.
- **google-genai SDK** — uses the current `google-genai` package (not the deprecated `google-generativeai`).
