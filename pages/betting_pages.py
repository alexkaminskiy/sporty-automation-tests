"""Page objects for the betting flow.

The page contains a dynamic list of match cards. Instead of relying on
hardcoded IDs (e.g. Manchester Utd vs Chelsea), all interactions are scoped
to the corresponding match card, making the implementation independent of
the actual fixtures displayed.
"""

import re

from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement

from pages.base_page import BasePage


class Locators:
    # Match list
    MATCH_CARD = (By.CSS_SELECTOR, "div.matchCard")

    # Match card internals
    TEAM_NAMES = (By.CSS_SELECTOR, ".teamName")
    ODDS_BUTTONS = (By.CSS_SELECTOR, "button[id^='odds-']")

    # Bet slip
    BET_SLIP = (By.CSS_SELECTOR, "h3.betSlipTitle")
    STAKE_INPUT = (By.CSS_SELECTOR, "input.stakeInput")
    POTENTIAL_PAYOUT = (By.ID, "bet-slip-potential-payout")
    BALANCE_DISPLAY = (
        By.XPATH,
        "//span[contains(normalize-space(.), 'Balance:')]",
    )
    PLACE_BET_BUTTON = (
        By.XPATH,
        "//button[contains(normalize-space(.), 'Place Bet')]",
    )
    REMOVE_SELECTION_BUTTON = (
        By.XPATH,
        "//button[contains(normalize-space(.), 'close')]",
    )
    REMOVE_ALL_BUTTON = (
        By.XPATH,
        "//button[contains(normalize-space(.), 'Remove All')]",
    )
    VALIDATION_MESSAGE = (
        By.XPATH,
        "//*[contains(@class, 'error') or @role='alert']",
    )

    # Success receipt modal
    RECEIPT_MODAL = (
        By.XPATH,
        "//h2[normalize-space()='Bet Placed Successfully!']",
    )
    RECEIPT_BET_ID = (
        By.XPATH,
        "//*[contains(normalize-space(.), 'Bet ID')]",
    )
    RECEIPT_STAKE = (By.ID, "modal-success-stake")
    RECEIPT_PAYOUT = (By.ID, "modal-success-payout")
    RECEIPT_CLOSE_BUTTON = (
        By.XPATH,
        "//button[contains(normalize-space(.), 'Close')]",
    )

    # Error modal
    ERROR_MODAL = (
        By.XPATH,
        "//*[contains(@class, 'error') or @role='alert']",
    )
    ERROR_REBET_BUTTON = (
        By.XPATH,
        "//button[contains(normalize-space(.), 'Rebet')]",
    )
    ERROR_CLOSE_BUTTON = (
        By.XPATH,
        "//button[contains(normalize-space(.), 'Close')]",
    )


class MatchCard:
    """Represents a single match card."""

    OUTCOME_INDEX = {
        "HOME": 0,
        "DRAW": 1,
        "AWAY": 2,
    }

    def __init__(self, element: WebElement):
        self.element = element

    @property
    def teams(self) -> tuple[str, str]:
        teams = self.element.find_elements(*Locators.TEAM_NAMES)
        return teams[0].text, teams[1].text

    @property
    def home_team(self) -> str:
        return self.teams[0]

    @property
    def away_team(self) -> str:
        return self.teams[1]

    def select_outcome(self, outcome: str) -> None:
        outcome = outcome.upper()

        if outcome not in self.OUTCOME_INDEX:
            raise ValueError(f"Unknown outcome: {outcome}")

        buttons = self.element.find_elements(*Locators.ODDS_BUTTONS)

        if len(buttons) < 3:
            raise AssertionError(
                f"Expected at least 3 odds buttons, found {len(buttons)}"
            )

        buttons[self.OUTCOME_INDEX[outcome]].click()


class MatchListPage(BasePage):
    def load(self, base_url: str, user_id: str) -> "MatchListPage":
        self.driver.get(f"{base_url}/?user-id={user_id}")
        self.find(Locators.MATCH_CARD)
        return self

    @property
    def matches(self) -> list[MatchCard]:
        return [
            MatchCard(card)
            for card in self.find_all(Locators.MATCH_CARD)
        ]

    def select_first_match_home_win(self) -> None:
        matches = self.matches
        assert matches, "No matches rendered."

        matches[0].select_outcome("HOME")

    def select_match_outcome(
        self,
        match_index: int,
        outcome: str,
    ) -> None:
        self.matches[match_index].select_outcome(outcome)

    def find_match(
        self,
        home_team: str,
        away_team: str,
    ) -> MatchCard:
        for match in self.matches:
            if (
                match.home_team == home_team
                and match.away_team == away_team
            ):
                return match

        raise AssertionError(
            f"Match '{home_team}' vs '{away_team}' not found."
        )


class BetSlipPage(BasePage):
    def enter_stake(self, amount: str) -> None:
        field = self.find(Locators.STAKE_INPUT)
        field.clear()
        field.send_keys(amount)

    def get_balance(self) -> float:
        return _parse_currency(
            self.text_of(Locators.BALANCE_DISPLAY)
        )

    def get_potential_payout(self) -> float:
        return _parse_currency(
            self.text_of(Locators.POTENTIAL_PAYOUT)
        )

    def click_place_bet(self) -> None:
        self.find_clickable(
            Locators.PLACE_BET_BUTTON
        ).click()

    def is_place_bet_enabled(self) -> bool:
        return self.find(
            Locators.PLACE_BET_BUTTON
        ).is_enabled()

    def get_validation_message(self) -> str:
        return self.text_of(
            Locators.VALIDATION_MESSAGE
        )


class ReceiptModal(BasePage):
    def wait_for_receipt(self) -> None:
        self.wait_until_visible(
            Locators.RECEIPT_MODAL
        )

    def get_stake(self) -> float:
        return _parse_currency(
            self.text_of(Locators.RECEIPT_STAKE)
        )

    def get_payout(self) -> float:
        return _parse_currency(
            self.text_of(Locators.RECEIPT_PAYOUT)
        )

    def get_bet_id(self) -> str:
        return self.text_of(
            Locators.RECEIPT_BET_ID
        )

    def close(self) -> None:
        self.find_clickable(
            Locators.RECEIPT_CLOSE_BUTTON
        ).click()
        self.wait_until_gone(
            Locators.RECEIPT_MODAL
        )


def _parse_currency(text: str) -> float:
    """Extract the first currency value from text."""
    match = re.search(r"(\d+(?:\.\d{1,2})?)", text)

    if not match:
        raise ValueError(
            f"Could not parse currency from: {text}"
        )

    return float(match.group(1))