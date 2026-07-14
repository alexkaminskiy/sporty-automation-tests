# QA Engineer Home Assignment — Single Bet Placement

This repository contains a compact automation suite for validating the single-bet placement flow against a live betting app. It combines API-level regression checks with a browser-driven end-to-end journey so the most important business rules can be verified from both layers.

## What is in this project

- API validation tests for stake boundaries, selection handling, authentication, malformed payloads, and balance reset in [tests/test_api_bet_validation.py](tests/test_api_bet_validation.py)
- A single end-to-end UI test for the critical bet-placement flow in [tests/test_e2e_bet_placement.py](tests/test_e2e_bet_placement.py)
- Page Object Model classes for the browser flow in [pages/](pages/)
- A thin HTTP client for the betting API in [api_client/](api_client/)
- Test planning, execution notes, and defect reporting in [docs/](docs/)

## Current execution status

The suite has already been exercised against the live application at https://qae-assignment-tau.vercel.app/?user-id=candidate-dLlAp5NuMH. The latest run surfaced several real issues, which are documented in [docs/execution_results.md](docs/execution_results.md):

- API run: 4 failed, 14 passed, 1 skipped
- UI/E2E flow: the browser journey failed during bet placement because the receipt payout and quoted payout were inconsistent
- Defects include negative stake acceptance, reset-balance behavior, and payout/receipt inconsistency

## Project structure

| Deliverable | Location |
|---|---|
| Test plan | [docs/test_plan.md](docs/test_plan.md) |
| Execution results and bug reports | [docs/execution_results.md](docs/execution_results.md) |
| Automation tests | [tests/](tests/) |
| Page objects | [pages/](pages/) |
| API client | [api_client/](api_client/) |
| Recommendations | [docs/strategy_recommendations.md](docs/strategy_recommendations.md) |

## Setup

Requires Python 3.10+ and Google Chrome. Selenium Manager will resolve the browser driver automatically in most environments.

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Configuration

Defaults live in [config.py](config.py) and can be overridden with environment variables when needed:

```bash
export QAE_BASE_URL="https://qae-assignment-tau.vercel.app"
export QAE_USER_ID="candidate-dLlAp5NuMH"
export QAE_HEADLESS="true"       # set "false" to watch the browser locally
```

## Running the tests

```bash
# Fast API-only regression suite
pytest -m api -v

# Full suite, including the browser test
pytest -v

# Browser-only E2E run
QAE_HEADLESS=false pytest -m e2e -v
```

## Design notes

- The UI layer uses a Page Object Model so locator updates stay localized to [pages/](pages/)
- The API suite is the fast feedback layer for boundary and validation defects
- The E2E test is intentionally limited to the single highest-value journey because it is slower and more fragile than API checks
- The balance-reset fixture is used to ensure each test starts from a known state

## Tooling choices

The stack stays intentionally small: Python, pytest, Selenium, and requests. This keeps the setup simple while still covering both API and UI behavior.
