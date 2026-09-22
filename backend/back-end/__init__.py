"""Package marker. Heavy subpackages are imported by callers, not here.

Avoid eager `agents`/`conversation` imports so the slim paper API
(`trading_app`) can start without google-adk installed.
"""

__all__: list[str] = []
