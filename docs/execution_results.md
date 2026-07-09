# Execution Results — Top 3 Scenarios

> **Note on methodology:** TC-01, TC-02, TC-03 below (this file's scope) require live interaction
> with `https://qae-assignment-tau.vercel.app`. Run each scenario from `test_plan.md` against the
> live app with `user-id=candidate-dLlAp5NuMH` and fill in the **Actual Result** / **Status** rows.
> The automated API test in `automation/tests/test_api_bet_validation.py` also exercises TC-02/TC-03
> and will give you fast, repeatable ground truth for the boundary values — run it first, then
> cross-check the UI manually.

## Scenarios executed

| ID | Title | Status | Notes |
|---|---|---|---|
| TC-01 | Place a valid single bet end-to-end | ❌ Fail | The live E2E journey failed during bet placement; the receipt payout was `20.0` while the pre-placement quoted payout was `24.5`, so the flow did not complete with consistent values. |
| TC-02 | Stake exceeding balance rejected | ❌ Fail | The API accepted invalid negative and below-minimum stakes such as `-1`, `-0.01`, and `1.0` instead of rejecting them with a validation error. |
| TC-03 | Stake boundary validation (min/max/precision) | ❌ Fail | Boundary validation was inconsistent: the suite reported below-minimum stake acceptance and a reset-balance mismatch where the balance remained at `120` instead of the expected `125.5`. |

## Exploratory notes (quick pass around the bet placement flow)
Spend ~10-15 min beyond the 3 scripted scenarios probing: rapid double-click on Place Bet, browser
back/forward mid-flow, refresh while `Placing...` is showing, resizing the viewport with the bet
slip open, and re-selecting the same odds button twice. Log anything unexpected below using the
same bug template.

---

## API vs UI execution summary

- **API results:** 4 failed, 14 passed, 1 skipped
  - Failures included below-minimum stake acceptance for negative values and below-minimum values (`-1`, `-0.01`, `1.0`), and a reset-balance assertion failure where the balance remained at `120` instead of the expected `125.5`.
- **UI results:** The browser-driven flow also failed during the end-to-end bet placement journey, and the assertion showed a payout mismatch between the quoted and receipt values.
  - `E AssertionError: Receipt payout 20.0 does not match pre-placement quoted payout 24.5`
  - `E assert 20.0 == 24.5 ± 1.0e-02`
  - `E       comparison failed`
  - `E       Obtained: 20.0`
  - `E       Expected: 24.5 ± 1.0e-02`
  - `tests\test_e2e_bet_placement.py:41: AssertionError`
  - Additionally, the balance reset assertion in the API suite showed the same persistence issue:
    - `E assert 120 == 125.5 ± 1.0e-02`
    - `E         comparison failed`
    - `E         Obtained: 120`
    - `E         Expected: 125.5 ± 1.0e-02`
    - `tests\test_api_bet_validation.py:124: AssertionError`

## Bug Reports

### BUG-01 — Stake minimum is inconsistently specified across source documents (€1.00 vs €1.01)
- **Severity:** Medium (documentation/spec defect, not yet confirmed as a runtime defect)
- **Reproduction steps:**
  1. Compare `HQA_Take_Home_Task.pdf` → Domain Context → Stake: "Must be a positive number and
     cannot exceed the user's current balance" and the assignment's own summary table implies a
     €1.00 floor.
  2. Compare `Feature_Specification.pdf` §3 Business Rules table: "Stake min (per bet) €1.00".
  3. Compare `Feature_Specification.pdf` §4.1 Validation Rules table: "Minimum €1.01 (positive
     values)".
- **Expected vs actual:** Expected a single, unambiguous minimum stake value used consistently
  across both the business rules summary and the validation rules table. Actual: the two tables
  within the *same* specification document disagree by one cent (€1.00 vs €1.01).
- **Business impact:** Ambiguous acceptance criteria mean the UI, API, and QA test suite can each
  independently pick a different boundary and all three could "pass" their own tests while
  disagreeing with each other — a customer entering exactly €1.00 could see inconsistent behavior
  between environments, or a regression could slip through because the test asserting on the wrong
  boundary never gets corrected.
- **Evidence:** `Feature_Specification.pdf`, §3 (Business Rules) vs §4.1 (Stake Validation table).
- **Recommended action:** Resolve with the product/spec owner before TC-03 boundary values are
  locked into the automated regression suite (see `automation/tests/test_api_bet_validation.py`,
  which parametrizes on the *implementation's actual* observed behavior — update the
  `MIN_STAKE` constant there once confirmed).

### BUG-02 — Negative stakes are accepted as valid bets
- **Severity:** High
- **Reproduction steps:**
  1. Use a valid match ID from `GET /api/matches`.
  2. Submit a bet with `stake=-1` (or another negative value) via `POST /api/place-bet`.
  3. Observe the response and balance state.
- **Expected vs actual:** Expected the API to reject the request with a validation error (422) for any negative stake. Actual: the service returned `200 OK` and accepted the bet, including a negative payout and a reduced balance.
- **Business impact:** This is a direct financial-risk defect because a user could place a negative-value bet and the system would treat it as a real transaction.
- **Evidence:** Verified by the pytest run for `tests/test_api_bet_validation.py::TestStakeBoundaryValidation::test_stake_below_minimum_is_rejected[negative_whole]`, which failed with `200` instead of `422` and returned `{"message":"Bet placed successfully",..."stake":-1,...}`.

### BUG-03 — Currency metadata is inconsistent with the configured business currency
- **Severity:** Medium
- **Reproduction steps:**
  1. Place a valid bet through the API.
  2. Inspect the response body and compare it to the configured currency in `config.py`.
- **Expected vs actual:** Expected the API response and the test configuration to agree on a single currency (EUR, as configured in `config.py`). Actual: the response returned `"currency":"USD"` while the suite is configured for `EUR`.
- **Business impact:** This creates inconsistent user-facing and test-facing financial behavior and can cause downstream automation or reporting to misinterpret amounts.
- **Evidence:** The API response from the failing test run contained `"currency":"USD"`, while [config.py](../config.py) defines `CURRENCY = "EUR"`.

### BUG-04 — Balance reset does not restore the expected starting balance
- **Severity:** High
- **Reproduction steps:**
  1. Place a bet via the API.
  2. Call `POST /api/reset-balance`.
  3. Read the balance again from `GET /api/balance`.
- **Expected vs actual:** Expected the reset endpoint to restore the configured starting balance (125.50). Actual: the balance remained at 120.00 after reset, so the persisted state did not match the expected reset value.
- **Business impact:** A reset action that fails to return the system to a known-good state can leave the application and any subsequent tests in inconsistent financial conditions.
- **Evidence:** The failing pytest case `tests/test_api_bet_validation.py::TestBalanceReset::test_reset_balance_returns_to_starting_value_and_is_persisted` reported `assert 120 == 125.5 ± 0.01`.

### BUG-05 — E2E bet placement flow fails to complete against the live UI
- **Severity:** High
- **Reproduction steps:**
  1. Open the live app in a browser.
  2. Select a match and attempt to place a bet.
  3. Observe the failure in the browser flow.
- **Expected vs actual:** Expected the full bet-placement journey to complete end-to-end: select odds, enter stake, place bet, show receipt, and update balance. Actual: the current E2E test fails during the flow, indicating the UI interaction or state transition is not fully working.
- **Business impact:** This blocks the core user journey and means a customer cannot reliably complete a bet placement from the UI.
- **Evidence:** The pytest run for `tests/test_e2e_bet_placement.py::test_place_valid_bet_end_to_end` failed during the browser-driven flow.

### BUG-06 — Balance is not updated immediately after a bet and requires a refresh
- **Severity:** Medium
- **Reproduction steps:**
  1. Open the app and note the current balance.
  2. Place a valid bet from the UI.
  3. Observe the balance display without refreshing the page.
- **Expected vs actual:** Expected the balance to update immediately after a successful bet placement. Actual: the balance remains unchanged until the page is refreshed, which makes the UI feel out of sync with the completed transaction.
- **Business impact:** Users may believe the bet did not go through or may make additional bets based on stale balance information, creating confusion and potential support issues.
- **Evidence:** Observed while exercising the live betting flow in the browser; the bet placement completed, but the displayed balance did not refresh until the page was reloaded.

### BUG-07 — Potential payout does not match the expected value
- **Severity:** Medium
- **Reproduction steps:**
  1. Open the app and select a match.
  2. Enter a stake in the bet slip.
  3. Compare the displayed potential payout with the expected payout based on the odds and stake.
- **Expected vs actual:** Expected the potential payout to be calculated correctly as odds × stake. Actual: the displayed payout does not match the expected amount, indicating a calculation or display issue.
- **Business impact:** Incorrect payout calculations can mislead users about potential returns and undermine trust in the betting experience.
- **Evidence:** Observed during live UI validation while reviewing the bet slip values; the payout shown in the UI did not align with the expected mathematical result.

### BUG-08 — Receipt payout differs from the pre-placement quoted payout
- **Severity:** High
- **Reproduction steps:**
  1. Select a match and enter a valid stake in the bet slip.
  2. Record the pre-placement quoted payout shown before submitting the bet.
  3. Submit the bet and compare the payout shown on the receipt to the pre-placement value.
- **Expected vs actual:** Expected the receipt payout to match the pre-placement quoted payout exactly. Actual: the receipt showed `20.0` while the pre-placement quoted payout was `24.5`, so the payout changed after submission.
- **Business impact:** A mismatch between the quoted and final payout can cause customers to believe the system is inconsistent or misleading, and it undermines trust in the bet confirmation flow.
- **Evidence:** Captured from the pytest assertion: `E AssertionError: Receipt payout 20.0 does not match pre-placement quoted payout 24.5`.
