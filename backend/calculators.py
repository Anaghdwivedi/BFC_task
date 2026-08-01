"""Calculator functions for Loan Tenure, SIP, and SWP."""

import math


def calculate_loan_tenure(P, E, R):
    """
    Calculate the loan repayment tenure.

    Args:
        P (int|float): Loan principal amount in rupees. Must be > 0.
        E (int|float): Monthly EMI amount in rupees. Must be > 0.
        R (int|float): Annual interest rate as a percentage. Must be > 0 and <= 100.

    Returns:
        str: Tenure in "X year(s) and Y month(s)" format, or an error message string.
    """
    # --- Type validation ---
    if not isinstance(P, (int, float)):
        return "Error: Loan amount must be a number."
    if not isinstance(E, (int, float)):
        return "Error: EMI amount must be a number."
    if not isinstance(R, (int, float)):
        return "Error: Interest rate must be a number."

    # --- Value validation ---
    if P <= 0:
        return "Error: Loan amount must be a positive number."
    if E <= 0:
        return "Error: EMI amount must be a positive number."
    if R <= 0 or R > 100:
        return "Error: Interest rate must be between 0 and 100."

    # --- Compute monthly rate ---
    r = (1 + R / 100) ** (1 / 12) - 1

    # --- EMI viability check ---
    monthly_interest = P * r
    if (E - monthly_interest) <= 0:
        return (
            f"Error: EMI is too low. It does not cover the monthly interest of "
            f"₹{monthly_interest:.2f}. Please increase your EMI."
        )

    # --- Compute number of months ---
    n = math.log(E / (E - P * r)) / math.log(1 + r)

    # --- Convert to years and months ---
    total_months = round(n)
    years_part = total_months // 12
    months_part = total_months % 12

    # --- Return result ---
    if months_part == 0:
        return f"Loan Tenure: {years_part} year(s)"
    return f"Loan Tenure: {years_part} year(s) and {months_part} month(s)"


def calculate_sip(target, R, years):
    """
    Calculate the monthly SIP amount required to reach a target corpus.

    Args:
        target (int|float): Target corpus amount in rupees. Must be > 0.
        R      (int|float): Expected annual return rate as a percentage. Must be > 0 and <= 100.
        years  (int|float): Investment period in years. Must be > 0.

    Returns:
        str: Required monthly SIP amount, or an error message string.
    """
    # --- Type validation ---
    if not isinstance(target, (int, float)):
        return "Error: Target amount must be a number."
    if not isinstance(R, (int, float)):
        return "Error: Return rate must be a number."
    if not isinstance(years, (int, float)):
        return "Error: Investment period must be a number."

    # --- Value validation ---
    if target <= 0:
        return "Error: Target amount must be a positive number."
    if R <= 0 or R > 100:
        return "Error: Return rate must be between 0 and 100."
    if years <= 0:
        return "Error: Investment period must be a positive number."

    # --- Compute monthly rate ---
    r = (1 + R / 100) ** (1 / 12) - 1

    # --- Compute number of months ---
    n = years * 12

    # --- Compute SIP ---
    SIP = (target * r) / ((1 + r) ** n - 1) * (1 + r)

    return f"Required Monthly SIP: ₹{SIP:.2f}"


def calculate_swp(P, years, R, W):
    """
    Calculate the Systematic Withdrawal Plan (SWP) outcomes.

    Args:
        P     (int|float): Lumpsum investment amount in rupees. Must be > 0.
        years (int|float): Investment period in years. Must be > 0.
        R     (int|float): Expected annual return rate as a percentage. Must be > 0 and <= 100.
        W     (int|float|str): Monthly withdrawal — either a plain number (e.g. 8000)
                               or a percentage string ending with '%' (e.g. "1%").

    Returns:
        str: Final balance, total withdrawn, and total profit/loss, or an error message string.
    """
    # --- Type validation for P, years, R ---
    if not isinstance(P, (int, float)):
        return "Error: Lumpsum amount must be a number."
    if not isinstance(years, (int, float)):
        return "Error: Investment period must be a number."
    if not isinstance(R, (int, float)):
        return "Error: Return rate must be a number."

    # --- Value validation for P, years, R ---
    if P <= 0:
        return "Error: Lumpsum amount must be a positive number."
    if years <= 0:
        return "Error: Investment period must be a positive number."
    if R <= 0 or R > 100:
        return "Error: Return rate must be between 0 and 100."

    # --- Parse W ---
    if isinstance(W, str) and W.strip().endswith("%"):
        try:
            percentage = float(W.strip().rstrip("%"))
        except ValueError:
            return "Error: Withdrawal percentage is not a valid number."
        if percentage <= 0 or percentage > 100:
            return "Error: Withdrawal percentage must be between 0 and 100."
        monthly_W = P * percentage / 100
    elif isinstance(W, (int, float)):
        monthly_W = float(W)
        if monthly_W <= 0:
            return "Error: Withdrawal amount must be a positive number."
    else:
        return "Error: Withdrawal must be a number or a percentage string like '2%'."

    # --- Compute monthly rate ---
    r = (1 + R / 100) ** (1 / 12) - 1

    # --- Compute number of months ---
    n = years * 12

    # --- Compute Final Value ---
    FV = P * (1 + r) ** n - monthly_W * ((1 + r) ** n - 1) / r

    # --- Compute totals ---
    total_withdrawn = monthly_W * n
    total_profit = FV + total_withdrawn - P

    # --- Build result string ---
    result = (
        f"SWP Results:\n"
        f"  Final Balance:     ₹{FV:.2f}\n"
        f"  Total Withdrawn:   ₹{total_withdrawn:.2f}\n"
        f"  Total Profit/Loss: ₹{total_profit:.2f}"
    )

    if FV < 0:
        result += "\n  ⚠ Warning: Corpus exhausted before the investment period ended."

    return result
