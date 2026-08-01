"""Phase 7 — End-to-end test runner using Flask test client. No source files modified."""

import json
import sys
import backend.app as app_module

flask_app = app_module.app
results = []


def send(session_id, message):
    with flask_app.test_client() as client:
        r = client.post(
            "/chat",
            data=json.dumps({"message": message, "session_id": session_id}),
            content_type="application/json",
        )
        data = r.get_json()
        return data.get("reply", data.get("error", "NO REPLY KEY"))


def sep():
    print("-" * 72)


def verdict_line(label, verdict, details=""):
    print(f"  Verdict : [{verdict}]" + (f" — {details}" if details else ""))


# Clear any leftover sessions from a previous run
app_module.SESSIONS.clear()

print("SERVER UP: using Flask test client (no subprocess)")
sep()

# ── SCENARIO 1 — LLM: general finance question ────────────────────────────
print("SCENARIO 1 — General finance question")
r1 = send("test-s1", "What is SIP?")
print("  Input   : What is SIP?")
print("  Response:", r1)
if "GEMINI_API_KEY" in r1:
    v1 = "NO_KEY"
elif "RESOURCE_EXHAUSTED" in r1 or "429" in r1:
    v1 = "QUOTA"
elif "Could not get a response" in r1:
    v1 = "FAIL"
elif ("sip" in r1.lower() or "invest" in r1.lower() or "mutual" in r1.lower()):
    v1 = "PASS"
else:
    v1 = "FAIL"
verdict_line("Scenario 1", v1)
results.append(("Scenario 1 — What is SIP?", r1, v1))
sep()

# ── SCENARIO 2 — LLM: off-topic question ──────────────────────────────────
print("SCENARIO 2 — Off-topic question")
r2 = send("test-s2", "What's the weather today?")
print("  Input   : What's the weather today?")
print("  Response:", r2)
if "GEMINI_API_KEY" in r2:
    v2 = "NO_KEY"
elif "RESOURCE_EXHAUSTED" in r2 or "429" in r2:
    v2 = "QUOTA"
elif "Could not get a response" in r2:
    v2 = "FAIL"
elif (
    "weather" not in r2.lower() or "finance" in r2.lower()
) and not any(w in r2.lower() for w in ["sunny", "rain", "temperature", "celsius", "forecast"]):
    v2 = "PASS"
else:
    v2 = "FAIL"
verdict_line("Scenario 2", v2)
results.append(("Scenario 2 — Off-topic (weather)", r2, v2))
sep()

# ── SCENARIO 3 — Loan tenure happy path ───────────────────────────────────
print("SCENARIO 3 — Loan tenure happy path (4 turns)")
sid3 = "test-s3"

t3_1 = send(sid3, "Calculate my loan tenure")
print("  Turn 1 in : Calculate my loan tenure")
print("  Turn 1 out:", t3_1)
v3_1 = "PASS" if "loan amount" in t3_1.lower() else "FAIL"

t3_2 = send(sid3, "1000000")
print("  Turn 2 in : 1000000")
print("  Turn 2 out:", t3_2)
v3_2 = "PASS" if ("emi" in t3_2.lower() or "monthly" in t3_2.lower()) else "FAIL"

t3_3 = send(sid3, "12000")
print("  Turn 3 in : 12000")
print("  Turn 3 out:", t3_3)
v3_3 = "PASS" if ("interest" in t3_3.lower() or "rate" in t3_3.lower()) else "FAIL"

t3_4 = send(sid3, "10")
print("  Turn 4 in : 10")
print("  Turn 4 out:", t3_4)
v3_4 = "PASS" if "Loan Tenure:" in t3_4 and "Got it" in t3_4 else "FAIL"

v3_all = all(v == "PASS" for v in [v3_1, v3_2, v3_3, v3_4])
verdict_line("Scenario 3", "PASS" if v3_all else "FAIL",
             f"turns: {v3_1}/{v3_2}/{v3_3}/{v3_4}")
results.append(("Scenario 3 — Loan Tenure walkthrough", t3_4, "PASS" if v3_all else "FAIL"))
sep()

# ── SCENARIO 4 — EMI too low edge case ────────────────────────────────────
print("SCENARIO 4 — EMI too low edge case (4 turns)")
sid4 = "test-s4"

t4_1 = send(sid4, "Calculate my loan tenure")
print("  Turn 1 in : Calculate my loan tenure")
print("  Turn 1 out:", t4_1)

t4_2 = send(sid4, "1000000")
print("  Turn 2 in : 1000000  (P)")
print("  Turn 2 out:", t4_2)

t4_3 = send(sid4, "500")
print("  Turn 3 in : 500  (EMI — too low)")
print("  Turn 3 out:", t4_3)

t4_4 = send(sid4, "10")
print("  Turn 4 in : 10  (rate)")
print("  Turn 4 out:", t4_4)

v4 = "PASS" if "Error" in t4_4 and "monthly interest" in t4_4.lower() else "FAIL"
verdict_line("Scenario 4", v4)
results.append(("Scenario 4 — EMI too low", t4_4, v4))
sep()

# ── SCENARIO 5 — Negative input mid-calculator ────────────────────────────
print("SCENARIO 5 — Negative input mid-calculator (3 turns)")
sid5 = "test-s5"

t5_1 = send(sid5, "Calculate my loan tenure")
print("  Turn 1 in : Calculate my loan tenure")
print("  Turn 1 out:", t5_1)

t5_2 = send(sid5, "-500000")
print("  Turn 2 in : -500000  (negative P)")
print("  Turn 2 out:", t5_2)
v5_2 = (
    "PASS"
    if any(w in t5_2.lower() for w in ["valid", "number", "positive"])
    and "emi" not in t5_2.lower()
    else "FAIL"
)

t5_3 = send(sid5, "500000")
print("  Turn 3 in : 500000  (recovery)")
print("  Turn 3 out:", t5_3)
v5_3 = "PASS" if ("emi" in t5_3.lower() or "monthly" in t5_3.lower()) else "FAIL"

v5 = "PASS" if v5_2 == "PASS" and v5_3 == "PASS" else "FAIL"
verdict_line("Scenario 5", v5, f"bad-input:{v5_2} / recovery:{v5_3}")
results.append(("Scenario 5 — Negative input + recovery", t5_3, v5))
sep()

# ── SCENARIO 6 — Full SWP walkthrough ─────────────────────────────────────
print("SCENARIO 6 — Full SWP walkthrough (5 turns)")
sid6 = "test-s6"

t6_1 = send(sid6, "I want to do SWP")
print("  Turn 1 in : I want to do SWP")
print("  Turn 1 out:", t6_1)
v6_1 = "PASS" if "lumpsum" in t6_1.lower() else "FAIL"

t6_2 = send(sid6, "2000000")
print("  Turn 2 in : 2000000  (P)")
print("  Turn 2 out:", t6_2)
v6_2 = "PASS" if ("year" in t6_2.lower() or "period" in t6_2.lower()) else "FAIL"

t6_3 = send(sid6, "15")
print("  Turn 3 in : 15  (years)")
print("  Turn 3 out:", t6_3)
v6_3 = "PASS" if ("return" in t6_3.lower() or "rate" in t6_3.lower()) else "FAIL"

t6_4 = send(sid6, "9")
print("  Turn 4 in : 9  (R%)")
print("  Turn 4 out:", t6_4)
v6_4 = "PASS" if "withdraw" in t6_4.lower() else "FAIL"

t6_5 = send(sid6, "15000")
print("  Turn 5 in : 15000  (W)")
print("  Turn 5 out:", t6_5)
v6_5 = (
    "PASS"
    if (
        "Final Balance:" in t6_5
        and "Total Withdrawn:" in t6_5
        and "Total Profit/Loss:" in t6_5
    )
    else "FAIL"
)

v6 = "PASS" if all(v == "PASS" for v in [v6_1, v6_2, v6_3, v6_4, v6_5]) else "FAIL"
verdict_line("Scenario 6", v6, f"turns: {v6_1}/{v6_2}/{v6_3}/{v6_4}/{v6_5}")
results.append(("Scenario 6 — Full SWP walkthrough", t6_5, v6))
sep()

# ── SUMMARY TABLE ──────────────────────────────────────────────────────────
print("SUMMARY TABLE")
sep()
print(f"{'Scenario':<42} {'Verdict'}")
sep()
for label, resp, verdict in results:
    print(f"{label:<42} [{verdict}]")
    print(f"  Response (first 100 chars): {resp[:100]}")
    print()
sep()
passed = sum(1 for _, _, v in results if v == "PASS")
no_key = sum(1 for _, _, v in results if v == "NO_KEY")
quota  = sum(1 for _, _, v in results if v == "QUOTA")
failed  = sum(1 for _, _, v in results if v == "FAIL")
print(f"PASS: {passed}  |  NO_KEY: {no_key}  |  QUOTA (retry later): {quota}  |  FAIL: {failed}")
