"""E2E UI test — the single highest-value automated test candidate.

WHY THIS TEST: this covers the critical user journey (TC-01 in docs/test_plan.md) — select
match, enter stake, place bet, receive receipt, balance decremented. It's the one flow every
other feature depends on, it touches the full stack (UI -> API -> balance state), and a
regression here means the product's core function is broken. It's expensive to run (real
browser, real network round-trips) which is exactly why it's reserved for the one journey that
justifies that cost, rather than being used to also cover boundary/negative cases — those are
covered far more cheaply at the API layer (see test_api_bet_validation.py).
"""
import pytest

from config import BASE_URL, USER_ID
from pages.betting_pages import BetSlipPage, MatchListPage, ReceiptModal


@pytest.mark.e2e
def test_place_valid_bet_end_to_end(driver, reset_balance):
    match_list = MatchListPage(driver)
    bet_slip = BetSlipPage(driver)
    receipt = ReceiptModal(driver)

    match_list.load(BASE_URL, USER_ID)

    starting_balance = bet_slip.get_balance()
    stake = 10.00

    match_list.select_first_match_home_win()
    bet_slip.enter_stake(str(stake))
    expected_payout = bet_slip.get_potential_payout()

    bet_slip.click_place_bet()
    receipt.wait_for_receipt()

    # Receipt values must match what was shown in the slip before submission (spec §2.4).
    assert receipt.get_stake() == pytest.approx(stake, abs=0.01), (
        f"Receipt stake {receipt.get_stake()} does not match entered stake {stake}"
    )
    assert receipt.get_payout() == pytest.approx(expected_payout, abs=0.01), (
        f"Receipt payout {receipt.get_payout()} does not match pre-placement "
        f"quoted payout {expected_payout}"
    )
    assert receipt.get_bet_id(), "Receipt must include a non-empty bet ID"

    receipt.close()

    # Balance must be decremented by exactly the stake, everywhere it's displayed.
    ending_balance = bet_slip.get_balance()
    assert ending_balance == pytest.approx(starting_balance - stake, abs=0.01), (
        f"Expected balance {starting_balance - stake:.2f} after a €{stake} bet, "
        f"got {ending_balance:.2f}"
    )
