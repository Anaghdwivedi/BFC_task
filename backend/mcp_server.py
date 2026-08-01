"""MCP server — exposes the three financial calculators as MCP tools.

Run as a subprocess via stdio transport:
    python -m backend.mcp_server

The server is NOT intended to be imported by other modules.
chat_logic.py launches it as a subprocess and communicates over stdio.
"""

import anyio
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

from backend.calculators import calculate_loan_tenure, calculate_sip, calculate_swp

server = Server("financial-calculators")


@server.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="calculate_loan_tenure",
            description=(
                "Calculate how long (in years and months) it takes to repay a loan "
                "given the principal, monthly EMI, and annual interest rate."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "P": {
                        "type": "number",
                        "description": "Loan principal amount in rupees. Must be > 0.",
                    },
                    "E": {
                        "type": "number",
                        "description": "Monthly EMI amount in rupees. Must be > 0.",
                    },
                    "R": {
                        "type": "number",
                        "description": "Annual interest rate as a percentage (e.g. 10 for 10%). Must be > 0 and <= 100.",
                    },
                },
                "required": ["P", "E", "R"],
            },
        ),
        Tool(
            name="calculate_sip",
            description=(
                "Calculate the required monthly SIP investment amount to reach "
                "a target corpus over a given number of years at an expected annual return."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "target": {
                        "type": "number",
                        "description": "Target corpus amount in rupees. Must be > 0.",
                    },
                    "R": {
                        "type": "number",
                        "description": "Expected annual return rate as a percentage (e.g. 12 for 12%). Must be > 0 and <= 100.",
                    },
                    "years": {
                        "type": "number",
                        "description": "Investment period in years. Must be > 0.",
                    },
                },
                "required": ["target", "R", "years"],
            },
        ),
        Tool(
            name="calculate_swp",
            description=(
                "Calculate the Systematic Withdrawal Plan (SWP) outcome: "
                "final balance, total amount withdrawn, and total profit/loss."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "P": {
                        "type": "number",
                        "description": "Lumpsum investment amount in rupees. Must be > 0.",
                    },
                    "years": {
                        "type": "number",
                        "description": "Withdrawal period in years. Must be > 0.",
                    },
                    "R": {
                        "type": "number",
                        "description": "Expected annual return rate as a percentage. Must be > 0 and <= 100.",
                    },
                    "W": {
                        "type": "number",
                        "description": "Fixed monthly withdrawal amount in rupees. Must be > 0.",
                    },
                },
                "required": ["P", "years", "R", "W"],
            },
        ),
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    if name == "calculate_loan_tenure":
        result = calculate_loan_tenure(
            P=float(arguments["P"]),
            E=float(arguments["E"]),
            R=float(arguments["R"]),
        )
    elif name == "calculate_sip":
        result = calculate_sip(
            target=float(arguments["target"]),
            R=float(arguments["R"]),
            years=float(arguments["years"]),
        )
    elif name == "calculate_swp":
        result = calculate_swp(
            P=float(arguments["P"]),
            years=float(arguments["years"]),
            R=float(arguments["R"]),
            W=float(arguments["W"]),
        )
    else:
        result = "Error: Unknown tool."

    return [TextContent(type="text", text=result)]


async def main() -> None:
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options(),
        )


if __name__ == "__main__":
    anyio.run(main)
