"""Optional trading specialist agent — proposals only, never live orders."""
from google.adk.agents import Agent
from dotenv import load_dotenv

from . import trading_tools

load_dotenv()

MODEL_GEMINI_2_5_FLASH = "gemini-2.5-flash"

trading_proposal_agent = Agent(
    name="trading_proposal_agent",
    model=MODEL_GEMINI_2_5_FLASH,
    description=(
        "Paper-trading proposal agent. Can read the paper portfolio and propose "
        "target positions for human approval. Cannot enable live trading, change "
        "credentials, raise risk limits, or bypass the kill switch."
    ),
    instruction=(
        """
You assist with paper trading research only.

Allowed:
- Call get_paper_portfolio to inspect paper positions/events
- Call propose_target_position to create a TargetPositionIntent proposal

Forbidden:
- Claiming an order was sent to a live broker
- Asking the user for API secrets
- Enabling live mode

Always explain that proposals require operator approval and that OMS/EMS derives
orders from target vs current position (e.g. 0.18 -> 0.20 yields BUY 0.02).
"""
    ),
    tools=[
        trading_tools.propose_target_position_tool,
        trading_tools.get_paper_portfolio_tool,
    ],
)
