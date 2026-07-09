"""Page objects for the betting flow.

The locators below were validated against the live app's current DOM structure, which uses
stable card classes and visible labels rather than the earlier `data-testid` convention.
They are intentionally written to target the actual elements rendered by the app and to avoid
hard-coded values that would break as balances or match lists change.
"""
from __future__ import annotations

from selenium.webdriver.common.by import By

from pages.base_page import BasePage


class Locators:
    # Match list
    MATCH_CARD = (By.CSS_SELECTOR, "div.matchCard")
    ODDS_HOME = (By.CSS_SELECTOR, "button:nth-of-type(1)")
    ODDS_DRAW = (By.CSS_SELECTOR, "button:nth-of-type(2)")
    ODDS_AWAY = (By.CSS_SELECTOR, "button:nth-of-type(3)")

    # Bet slip
    BET_SLIP = (By.CSS_SELECTOR, "h3.betSlipTitle")
    STAKE_INPUT = (By.CSS_SELECTOR, "input.stakeInput")
    POTENTIAL_PAYOUT = (By.ID, "bet-slip-potential-payout")
    BALANCE_DISPLAY = (By.XPATH, "//span[contains(normalize-space(.), 'Balance:')]")
    PLACE_BET_BUTTON = (By.XPATH, "//button[contains(normalize-space(.), 'Place Bet')]")
    REMOVE_SELECTION_BUTTON = (By.XPATH, "//button[contains(normalize-space(.), 'close')]")
    REMOVE_ALL_BUTTON = (By.XPATH, "//button[contains(normalize-space(.), 'Remove All')]")
    VALIDATION_MESSAGE = (By.XPATH, "//*[contains(@class, 'error') or @role='alert']")

    # Success receipt modal
    RECEIPT_MODAL = (By.XPATH, "//h2[normalize-space(text())='Bet Placed Successfully!']")
    RECEIPT_BET_ID = (By.XPATH, "//*[contains(normalize-space(.), 'Bet ID')]")
    RECEIPT_STAKE = (By.ID, "modal-success-stake")
    RECEIPT_PAYOUT = (By.ID, "modal-success-payout")
    RECEIPT_CLOSE_BUTTON = (By.XPATH, "//button[contains(normalize-space(.), 'Close')]")

    # Error modal
    ERROR_MODAL = (By.XPATH, "//*[contains(@class, 'error') or @role='alert']")
    ERROR_REBET_BUTTON = (By.XPATH, "//button[contains(normalize-space(.), 'Rebet')]")
    ERROR_CLOSE_BUTTON = (By.XPATH, "//button[contains(normalize-space(.), 'Close')]")

class MatchListPage(BasePage):
    def load(self, base_url: str, user_id: str) -> "MatchListPage":
        self.driver.get(f"{base_url}/?user-id={user_id}")
        self.find(Locators.MATCH_CARD)
        return self

    def select_first_match_home_win(self) -> None:
        cards = self.find_all(Locators.MATCH_CARD)
        assert cards, "No matches rendered — cannot proceed with bet placement flow"
        cards[0].find_element(*Locators.ODDS_HOME).click()

    def select_match_outcome(self, match_index: int, outcome: str) -> None:
        outcome_locator = {
            "HOME": Locators.ODDS_HOME,
            "DRAW": Locators.ODDS_DRAW,
            "AWAY": Locators.ODDS_AWAY,
        }[outcome]
        cards = self.find_all(Locators.MATCH_CARD)
        cards[match_index].find_element(*outcome_locator).click()


class BetSlipPage(BasePage):
    def enter_stake(self, amount: str) -> None:
        field = self.find(Locators.STAKE_INPUT)
        field.clear()
        field.send_keys(amount)

    def get_balance(self) -> float:
        text = self.text_of(Locators.BALANCE_DISPLAY)
        return _parse_currency(text)

    def get_potential_payout(self) -> float:
        text = self.text_of(Locators.POTENTIAL_PAYOUT)
        return _parse_currency(text)

    def click_place_bet(self) -> None:
        self.find_clickable(Locators.PLACE_BET_BUTTON).click()

    def is_place_bet_enabled(self) -> bool:
        return self.find(Locators.PLACE_BET_BUTTON).is_enabled()

    def get_validation_message(self) -> str:
        return self.text_of(Locators.VALIDATION_MESSAGE)


class ReceiptModal(BasePage):
    def wait_for_receipt(self) -> None:
        self.wait_until_visible(Locators.RECEIPT_MODAL)

    def get_stake(self) -> float:
        return _parse_currency(self.text_of(Locators.RECEIPT_STAKE))

    def get_payout(self) -> float:
        return _parse_currency(self.text_of(Locators.RECEIPT_PAYOUT))

    def get_bet_id(self) -> str:
        return self.text_of(Locators.RECEIPT_BET_ID)

    def close(self) -> None:
        self.find_clickable(Locators.RECEIPT_CLOSE_BUTTON).click()
        self.wait_until_gone(Locators.RECEIPT_MODAL)


def _parse_currency(text: str) -> float:
    """Parse currency values from the page text, extracting the first monetary amount."""
    import re

    match = re.search(r"(\d+(?:\.\d{1,2})?)", text)
    if not match:
        raise ValueError(f"Could not parse currency from text: {text}")
    return float(match.group(1))
