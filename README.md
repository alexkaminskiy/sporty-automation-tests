# QA Engineer Home Assignment — Single Bet Placement

## Contents

| Deliverable | Location |
|---|---|
| Test plan (6 prioritized scenarios) | [`docs/test_plan.md`](docs/test_plan.md) |
| Execution results & bug reports | [`docs/execution_results.md`](docs/execution_results.md) |
| Automation framework + 2 tests | [`tests/`](tests/) and [`pages/`](pages/) |
| Strategy & recommendations | [`docs/strategy_recommendations.md`](docs/strategy_recommendations.md) |

## Known limitation — please read first

The two automated tests were written against the documented API/UI contract in
`Feature_Specification.pdf`, but **not yet executed against the live app**, because this
environment has no network access to `qae-assignment-tau.vercel.app`. Specifically:

- `tests/test_api_bet_validation.py` is implementation-ready — it only needs
  `requests` and network access, no browser, no locator guesswork. Run it first.
- `pages/betting_pages.py` uses `data-testid`-style locators as a best guess. **Before
  running the E2E test**, inspect the real DOM and update the `Locators` class — see the comment
  at the top of that file for exactly what to check.
- `docs/execution_results.md` is a filled-in template: it documents one real finding from
  reviewing the two spec documents (a stake-minimum inconsistency, BUG-01), plus the structure to
  record the other findings once TC-01/02/03 are actually run.

## Setup

Requires Python 3.10+, Google Chrome, and a matching ChromeDriver on `PATH`
(Selenium Manager, bundled with `selenium>=4.6`, will auto-resolve this for you in most cases).

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Configuration

Defaults live in `config.py` and can be overridden via env vars — useful for CI or
testing against a different environment without touching code:

```bash
export QAE_BASE_URL="https://qae-assignment-tau.vercel.app"
export QAE_USER_ID="candidate-dLlAp5NuMH"
export QAE_HEADLESS="true"       # set "false" to watch the browser locally
```

## Running the tests

```bash
# Fast — API tests only, no browser (recommended first pass, see limitation above)
pytest -m "not e2e" -v

# Everything, including the E2E browser test
pytest -v

# Just the E2E test, with the browser visible
QAE_HEADLESS=false pytest -m e2e -v
```

## Design decisions worth calling out

- **Page Object Model** for the UI layer (`automation/pages/`) — keeps locators and interaction
  logic out of test files, so a markup change is a one-file fix, not a find-and-replace across
  every test.
- **Explicit waits only, no implicit wait** (`config.IMPLICIT_WAIT_SECONDS = 0`) — mixing implicit
  and explicit Selenium waits causes timeouts to silently compound; see comment in
  `automation/pages/base_page.py`.
- **`reset_balance` fixture runs before *and* after each test** — guarantees a known starting
  balance and prevents a failed test from leaving stale state that poisons the next one.
- **No test framework abstraction beyond what's needed.** No custom assertion library, no BDD
  layer (Gherkin/behave) — plain pytest + Page Objects is the right amount of structure for a
  2-test suite; adding more would be premature abstraction for a project this size (see
  Recommendation #1 in the strategy doc for what I'd add if it scaled).

## Tooling choices

Only the required stack (Python 3, Selenium + pytest, `requests`) — no Poetry, Allure, or other
add-ons, to keep the setup path (`pip install -r requirements.txt`) as short as possible for
review.
