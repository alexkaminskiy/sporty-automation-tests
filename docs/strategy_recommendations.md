# Strategy & Recommendations

## Why these 2 tests for automation

**E2E UI test — valid bet placement, start to finish.** This is the one journey every other
feature depends on: match selection, stake entry, submission, receipt, and balance update all
have to work together correctly. It's the most expensive test to run (real browser, full network
round trip, most brittle to markup changes) — which is exactly why I limited myself to *one* UI
test rather than spreading UI coverage across boundary cases. Boundary/negative scenarios don't
need a browser to prove the business rule holds; they need the API to reject the request.

**API test — stake validation business rules.** Stake handling is where real money bugs live: an
over-strict check blocks legitimate revenue, an under-strict check lets someone place a bet they
can't afford or with invalid precision. Testing it at the API layer directly (rather than only
through the UI) also proves the rule is enforced *server-side*, not just as client-side form
validation that a direct API call could bypass — which is exactly the gap spec §4.1 is trying to
close by requiring "UI + API" enforcement on every stake rule. It's also the cheapest place to run
a full boundary matrix (parametrized, no browser, sub-second per case), so it's the natural home
for exhaustive edge-case coverage instead of the slow E2E path.

Between the two, they cover: the full user journey once, and the highest-financial-risk business
rule exhaustively — the combination the task description asks for ("critical user journey" +
"validation or business rule check via the API").

## What I left manual-only, and why

- **Filters (date range, odds range)** — presentation/query-layer feature, no money movement, and
  lower likelihood of a subtle regression slipping through unnoticed (a broken filter is visibly
  broken to any user immediately, unlike a boundary-value stake bug).
- **Error modal Rebet/Close behavior (§2.5)** — worth automating in a mature suite, but it's UI
  state-transition testing that depends heavily on the exact modal markup I don't have access to
  yet in this environment. I'd add it as the *second* E2E test once locators are confirmed against
  the real DOM (see the note at the top of `automation/pages/betting_pages.py`).
- **Visual/layout checks** (bet slip fixed positioning, responsive behavior) — better suited to
  visual regression tooling than functional Selenium assertions; out of scope for a 2-test budget.
- **Exploratory testing** (double-click races, refresh-mid-flow) — genuinely benefits from a human
  noticing something odd; I've captured the ones worth turning into regression tests
  (TC-06, duplicate submission) but exploratory testing itself doesn't automate well by nature.

## Top recommendations if this scaled

1. **CI/CD: split by speed and gate accordingly.** Run the full API validation suite (`-m api`,
   or just the non-`e2e`-marked tests) on every PR — it's fast enough to be a hard merge gate.
   Run the E2E suite (`-m e2e`) against a deployed preview environment post-merge or on a schedule,
   not on every commit, since headless Chrome + real network calls make it the slowest and
   flakiest layer. `pytest.ini` already has `e2e`/`api` markers set up for exactly this split.

2. **Add a contract/schema layer between API and UI tests.** Right now nothing pins down the exact
   response shape of `/api/place-bet` or `/api/matches` beyond what's in the spec doc. A thin
   Pydantic (or `jsonschema`) validation step on every API response would catch a backend
   contract change (renamed field, type change) before it silently breaks the UI — cheaper to
   detect at the API layer than to wait for an E2E test to fail with an opaque locator timeout.

3. **Resolve the stake-minimum spec conflict (BUG-01) before it becomes a false-negative in CI.**
   `automation/config.py::MIN_STAKE` is currently pinned to one of the two documented values as a
   single source of truth specifically so this doesn't silently diverge between the UI, the API,
   and the test suite. Once TC-03 is executed against the real app, whichever value is *actually*
   enforced should be confirmed with the spec owner and the losing document corrected — otherwise
   whoever writes the next test picks whichever number they see first and the suite ends up
   internally inconsistent.
4. **Add parallel execution.** The API suite is the obvious first candidate — no browser,
   no shared state, sub-second per case — so `pytest-xdist` (`pytest -n auto -m api`) is close to
   a free win once tests are confirmed independent (no shared fixtures mutating global state, no
   test-order dependencies). E2E parallelization is a bigger lift: each worker needs its own
   browser context and, more importantly, its own test data — two workers racing to place a bet
   against the same `valid_match_id` will produce flaky balance assertions. That means parallel
   E2E either needs per-worker match/account fixtures or a test-only endpoint to mint isolated
   data (ties into the fixture-strategy note below). Sequencing matters here: parallelize API
   first since it's low-risk and immediately shortens the PR-gate feedback loop from (1); treat
   E2E parallelization as a follow-up once the fixture strategy exists, not a day-one change.

5. **Add reporting.** Two distinct needs, don't conflate them:
   - **CI-facing (fast signal):** JUnit XML output (`--junitxml=report.xml`) so the CI platform
     renders pass/fail per test natively — this is what should drive the merge gate from (1), not
     a parsed stdout log.
   - **Human-facing (debugging failures):** `pytest-html` or Allure for the E2E suite specifically,
     with screenshot-on-failure wired into a Playwright/Selenium fixture teardown. This is the
     one that actually pays for itself — an E2E test failing on a locator timeout is close to
     undebuggable from a log line alone; a screenshot + DOM snapshot at failure time turns a
     "rerun and hope" investigation into a two-minute fix. Allure additionally gives history/trend
     view across runs, which matters more once (4) is parallelizing and failures need to be
     distinguished from genuine regressions vs. shared-state flakiness.
   - Skip building a custom reporting layer — this is a solved problem and a bespoke dashboard is
     exactly the kind of abstraction the 2-test/current scope doesn't justify yet.

6. **Add logging.** Test *output* (pass/fail, from item 5) tells you *what* broke; logging tells
   you *why* — the two aren't substitutes. Minimum viable setup:
   - **API layer:** log request/response pairs (method, URL, status, latency, and body for
     non-2xx responses) at `DEBUG`, gated behind a `--log-cli-level` flag rather than always-on,
     so a green CI run stays quiet and a failing one can be rerun locally with full request/
     response visibility. This is what actually lets you tell "the API returned 400 as expected"
     apart from "the API returned 500 and the assertion happened to also fail" — a distinction
     the JUnit XML from (5) doesn't carry today.
   - **E2E layer:** browser console logs and network-tab equivalents (`page.on("console")`,
     `page.on("response")` in Playwright, or Selenium's performance log) captured alongside the
     screenshot-on-failure from (5), not as a separate mechanism — a screenshot shows *that* the
     receipt didn't render, a console log showing a JS exception or a failed XHR shows *why*.
   - **Don't** route this through `print()` — use the standard `logging` module with a per-test
     handler (or `caplog` in pytest) so log volume scales with `-n auto` from (4) without
     interleaving into unreadable noise across parallel workers.
   - Skip structured/JSON logging or a log aggregation pipeline (ELK, Datadog) at this scale —
     that's justified once there's a deployed environment with its own logs to correlate against,
     not for a 2-test suite. Revisit alongside the contract/schema layer in (2) if this scales
     far enough that cross-service log correlation becomes the bottleneck, not before.
     
Runner-up: a lightweight **test data / fixture strategy for match IDs** — tests currently fetch
`GET /api/matches` and use whatever match happens to be first (`valid_match_id` fixture). That's
fine for a small fixed catalog, but if match data becomes dynamic (rotating fixtures, real kickoff
times), tests should either seed a known match via a test-only endpoint or filter for one with
stable characteristics (e.g. odds within a known range) rather than assuming index 0 stays valid.
