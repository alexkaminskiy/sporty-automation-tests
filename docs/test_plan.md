# Test Plan — Single Bet Placement

**Application under test:** https://qae-assignment-tau.vercel.app/?user-id=candidate-dLlAp5NuMH
**Feature:** Single Bet Placement (see `Feature_Specification.pdf`)
**Scope:** Match selection → bet slip → stake entry → placement → receipt/error handling, plus the
API rules that back them (`GET /api/matches`, `GET /api/balance`, `POST /api/place-bet`,
`POST /api/reset-balance`).

## Prioritization rationale

Scenarios are selected to cover: one happy path that proves the core money-moving flow works
end-to-end, the negative/boundary cases on stake validation (the highest financial-risk surface —
a bug here either blocks legitimate bets or lets an invalid bet through), and the stateful
edge cases (single active selection, concurrent placement) that are easy to get wrong in a
React-style UI backed by an async API. Filters (2.6) are deliberately excluded from the top 6 —
they're presentation-layer and lower risk than anything touching money.

---

### TC-01 — Place a valid single bet end-to-end (happy path)
- **Priority:** Critical
- **Risk rationale:** This is the core revenue path. If it breaks, the product doesn't work at
all — every other scenario is meaningless without this one passing. Also the only scenario that
validates receipt data consistency against pre-placement display (spec 2.4: "All values should be
consistent with what was shown before placement").
- **Steps:**
  1. Load the app with a valid `user-id`, note starting balance (expected €125.50 on a fresh user).
  2. Select any upcoming match, click the `1` (home) odds button.
  3. Confirm bet slip shows the selected match, odds, and balance.
  4. Enter a valid stake, e.g. `10.00`.
  5. Confirm potential payout displayed = stake × odds.
  6. Click **Place Bet**.
- **Expected result:** Button shows `Placing...` loading state, then resolves to the success
receipt modal. Receipt shows bet ID, match (home team listed first), selection, stake, odds,
payout, and timestamp — all matching what was shown in the bet slip. Balance is decremented by
the stake amount in both the header and bet slip. Closing the receipt returns to the match list
with no active selection.

---

### TC-02 — Stake exceeding available balance is rejected
- **Priority:** Critical
- **Risk rationale:** Allowing a bet to be placed for more than the user owns is a direct
financial-integrity bug (negative balance), not just a UX annoyance. Business rule requires
"Must not exceed available balance" at both UI and API layers (spec 4.1) — testing both layers
matters because a client-side-only check can be bypassed via direct API calls.
- **Steps:**
  1. Note current balance (e.g. €125.50).
  2. Select a match/outcome.
  3. Enter a stake greater than balance but ≤ €100 max (e.g. balance €50, stake €75), or if
balance > €100, use the max boundary case in TC-04 instead and force a low-balance state via
repeated betting.
  4. Attempt to place the bet.
  5. Repeat the same payload directly against `POST /api/place-bet` with `x-user-id` header,
bypassing the UI.
- **Expected result:** UI shows "Insufficient balance" and blocks submission (Place Bet
disabled or submission rejected client-side). API independently rejects with `422` and does not
deduct balance. Balance is unchanged after both attempts.

---

### TC-03 — Stake boundary validation: below minimum, above maximum, and the €1.00/€1.01 spec conflict
- **Priority:** High
- **Risk rationale:** Boundary defects are the single most common source of off-by-one bugs in
stake validation, and here the two source documents **disagree**: the assignment overview lists
stake min as €1.00, while Feature Spec §4.1 lists the minimum as €1.01. This scenario is designed
to determine which the implementation actually follows, since automated tests need a ground truth
to assert against.
- **Steps:**
  1. Attempt stake = `0.99` → expect rejection.
  2. Attempt stake = `1.00` → record actual behavior (accepted or rejected — this resolves the
spec ambiguity).
  3. Attempt stake = `1.01` → expect acceptance per both docs.
  4. Attempt stake = `100.00` → expect acceptance (max boundary).
  5. Attempt stake = `100.01` → expect rejection ("Maximum stake is €100.00").
  6. Repeat steps 1, 4, 5 directly via API.
- **Expected result:** UI shows the documented copy ("Minimum stake is €1.00", "Maximum stake is
€100.00") at the correct boundary and blocks submission; API returns `422` for out-of-range
values and accepts in-range ones. Actual behavior at exactly €1.00 is documented as a defect
candidate against whichever spec it contradicts.

---

### TC-04 — Non-numeric stake and invalid decimal precision are rejected
- **Priority:** High
- **Risk rationale:** Spec explicitly requires numeric-only input with ≤2 decimal places (§4.1,
§4.4) at both UI and API layers. A precision bug here (e.g. accepting `10.999`) creates rounding
disputes on payout calculations — a support/trust problem, not just a validation nit.
- **Steps:**
  1. In the UI stake field, attempt to type non-numeric characters (`abc`, `--`, multiple decimal
points).
  2. Attempt stake = `10.999` (3 decimal places).
  3. Send `stake: "10.50"` (string instead of number) and `stake: 10.999` directly via API.
- **Expected result:** UI input either blocks non-numeric characters at the input-mask level or
rejects on submit with clear messaging; 3-decimal stake is rejected. API returns `422` for
invalid precision and `400`/`422` for wrong type, per spec's declared error classes.

---

### TC-05 — Selecting a new outcome replaces the previous selection; only one bet slip selection at a time
- **Priority:** Medium
- **Risk rationale:** Spec 2.1 explicitly calls out "Selecting a new odds button replaces the
previous selection" and 2.2 states the slip "Shows one active selection at a time." This is a
state-management scenario — the kind of thing that's easy to get right in isolation but breaks
once a second match's odds are clicked, or once remove (`x`)/Remove All interacts with it.
- **Steps:**
  1. Select match A, outcome `1`. Confirm bet slip shows match A / home selection.
  2. Without removing, click outcome `X` on the same match A.
  3. Confirm bet slip now shows the draw selection for match A, not both.
  4. Select an outcome on a different match B.
  5. Confirm bet slip now shows only match B's selection (match A selection cleared).
  6. Use per-selection remove (`x`) and confirm slip returns to empty state.
- **Expected result:** At every step, exactly one selection is shown in the slip, and any stake
previously entered is either cleared or clearly revalidated against the new selection (spec
doesn't state which — worth noting as an observation either way).

---

### TC-06 — Duplicate/concurrent bet placement is blocked (409) while a bet is in progress
- **Priority:** Medium
- **Risk rationale:** Spec explicitly documents a `409 bet already in progress (same user)` error
class. Double-submission (double-click on Place Bet, or a slow network causing a user to retry) is
a classic way to accidentally place two bets or double-deduct balance if the backend doesn't guard
against it — direct financial risk.
- **Steps:**
  1. Select a match/outcome, enter a valid stake.
  2. Fire two `POST /api/place-bet` requests back-to-back with the same payload (simulating a
double-click) directly via API, and separately try rapid double-clicking **Place Bet** in the UI.
- **Expected result:** Exactly one bet is placed and one balance deduction occurs. The second
concurrent request receives `409`, and the UI does not show two success receipts or double-decrement
the balance. `Placing...` state should also disable the button to prevent this at the UI layer.

---

## Explicitly out of scope for this plan
- Date/odds filters (§2.6) — presentation/query concern, lower financial risk, no money movement.
- Multi-bet/accumulator, live betting, non-football sports, mobile UX — explicitly out of scope
per Feature Spec §1.
