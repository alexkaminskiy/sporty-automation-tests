"""Central configuration for the automation suite.

All environment-specific values live here so tests never hardcode URLs or
credentials. Override via environment variables for CI.
"""

import os

BASE_URL = os.getenv("QAE_BASE_URL", "https://qae-assignment-tau.vercel.app")
USER_ID = os.getenv("QAE_USER_ID", "candidate-dLlAp5NuMH")
API_BASE_URL = f"{BASE_URL}/api"

# Business rule constants (Feature_Specification.pdf §3/§4.1).
# NOTE: spec has a documented conflict between MIN_STAKE = 1.00 (§3) and 1.01 (§4.1) — see
# docs/execution_results.md BUG-01. Set this to whatever the live implementation actually
# enforces once TC-03 has been executed; tests reference this single source of truth so the
# fix is a one-line change.
MIN_STAKE = 1.01
MAX_STAKE = 100.00
MIN_ODDS = 1.01
MAX_ODDS = 1000.00
STARTING_BALANCE = 125.50
CURRENCY = "EUR"

# Selenium
IMPLICIT_WAIT_SECONDS = (
    0  # we use explicit waits only — implicit wait mixed with explicit
)
# waits causes inconsistent timeouts, so keep this at 0
EXPLICIT_WAIT_SECONDS = 10
HEADLESS = os.getenv("QAE_HEADLESS", "false").lower() == "true"
