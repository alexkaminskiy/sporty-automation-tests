"""API test — stake validation business rules (TC-02 / TC-03 / TC-04 in docs/test_plan.md).

WHY THIS TEST: stake validation is the highest financial-risk surface in the feature — a bug
here either blocks legitimate revenue (over-strict rejection) or lets an invalid/overdrawn bet
through (under-strict rejection, i.e. real money bug). It's also the scenario set most exposed
to client-side-only validation bypass, since a UI-only check is trivially defeated by calling
the API directly, which is exactly what these tests do. Chosen over the equivalent UI test
because: (a) it runs in milliseconds vs. seconds per case, so the full boundary matrix is cheap
to run on every commit, (b) it tests the source of truth directly — the API is what actually
enforces money movement, the UI is just a client of it, and (c) parametrized boundary testing
is far more naturally expressed against a JSON API than against form-field UI interactions.
"""
import pytest

from config import MAX_STAKE, MIN_STAKE
from api_client.betting_api import BettingAPIClient

VALIDATION_ERROR_STATUS = 422


@pytest.fixture
def valid_match_id(api_client: BettingAPIClient) -> str:
    matches = api_client.get_matches().json()
    assert matches, "GET /api/matches returned no matches — cannot build a valid bet payload"
    return matches[0]["id"]


class TestStakeBoundaryValidation:
    @pytest.mark.api
    @pytest.mark.parametrize(
        "stake",
        [0, -1, -0.01, MIN_STAKE - 0.01],
        ids=["zero", "negative_whole", "negative_fraction", "just_below_min"],
    )
    def test_stake_below_minimum_is_rejected(self, api_client, reset_balance, valid_match_id, stake):
        response = api_client.place_bet(valid_match_id, "HOME", stake)
        assert response.status_code == VALIDATION_ERROR_STATUS, (
            f"stake={stake} is below the minimum ({MIN_STAKE}) and must be rejected with "
            f"{VALIDATION_ERROR_STATUS}, got {response.status_code}: {response.text}"
        )

    @pytest.mark.api
    @pytest.mark.parametrize(
        "stake",
        [MAX_STAKE + 0.01, 150.00, 1000.00],
        ids=["just_above_max", "well_above_max", "way_above_max"],
    )
    def test_stake_above_maximum_is_rejected(self, api_client, reset_balance, valid_match_id, stake):
        response = api_client.place_bet(valid_match_id, "HOME", stake)
        assert response.status_code == VALIDATION_ERROR_STATUS, (
            f"stake={stake} exceeds the maximum ({MAX_STAKE}) and must be rejected with "
            f"{VALIDATION_ERROR_STATUS}, got {response.status_code}: {response.text}"
        )

    @pytest.mark.api
    @pytest.mark.parametrize("stake", [MIN_STAKE, MAX_STAKE], ids=["min_boundary", "max_boundary"])
    def test_stake_at_valid_boundary_is_accepted(self, api_client, reset_balance, valid_match_id, stake):
        response = api_client.place_bet(valid_match_id, "HOME", stake)
        assert response.status_code == 200, (
            f"stake={stake} is exactly at a valid boundary and must be accepted, "
            f"got {response.status_code}: {response.text}"
        )

    @pytest.mark.api
    @pytest.mark.parametrize("stake", [10.999, 5.001, 33.333], ids=["3dp_a", "3dp_b", "3dp_c"])
    def test_stake_with_invalid_precision_is_rejected(self, api_client, reset_balance, valid_match_id, stake):
        response = api_client.place_bet(valid_match_id, "HOME", stake)
        assert response.status_code == VALIDATION_ERROR_STATUS, (
            f"stake={stake} has more than 2 decimal places and must be rejected, "
            f"got {response.status_code}: {response.text}"
        )

    @pytest.mark.api
    def test_stake_exceeding_balance_is_rejected_and_balance_unchanged(
        self, api_client, reset_balance, valid_match_id
    ):
        balance_before = api_client.get_balance().json()["balance"]
        over_balance_stake = min(balance_before + 10.00, MAX_STAKE)
        if over_balance_stake <= balance_before:
            pytest.skip("Starting balance already exceeds MAX_STAKE — cannot construct an "
                        "over-balance stake within the stake cap")

        response = api_client.place_bet(valid_match_id, "HOME", round(over_balance_stake, 2))
        assert response.status_code == VALIDATION_ERROR_STATUS

        balance_after = api_client.get_balance().json()["balance"]
        assert balance_after == balance_before, (
            "A rejected bet must not deduct from balance — "
            f"was {balance_before}, now {balance_after}"
        )


class TestSelectionAndRequestValidation:

    @pytest.mark.api
    def test_invalid_selection_value_is_rejected(self, api_client, reset_balance, valid_match_id):
        response = api_client.place_bet(valid_match_id, "HOME_WIN", 10.00)  # not HOME/DRAW/AWAY
        assert response.status_code == VALIDATION_ERROR_STATUS

    @pytest.mark.api
    def test_unknown_match_id_is_rejected(self, api_client, reset_balance):
        response = api_client.place_bet("does-not-exist-999", "HOME", 10.00)
        assert response.status_code == VALIDATION_ERROR_STATUS

    @pytest.mark.api
    def test_missing_stake_field_is_rejected(self, api_client, reset_balance, valid_match_id):
        response = api_client.place_bet_raw({"matchId": valid_match_id, "selection": "HOME"})
        assert response.status_code in (400, VALIDATION_ERROR_STATUS)

    @pytest.mark.api
    def test_malformed_json_body_returns_400(self, api_client, reset_balance):
        response = api_client.place_bet_raw(["not", "an", "object"])
        assert response.status_code == 400
    @pytest.mark.api
    def test_missing_user_id_header_returns_401(self, api_client, valid_match_id):
        unauthenticated_client = api_client.without_auth()
        response = unauthenticated_client.place_bet(valid_match_id, "HOME", 10.00)
        assert response.status_code == 401


class TestBalanceReset:

    @pytest.mark.api
    def test_reset_balance_returns_to_starting_value_and_is_persisted(self, api_client):
        from config import STARTING_BALANCE

        api_client.place_bet(api_client.get_matches().json()[0]["id"], "HOME", 10.00)
        reset_response = api_client.reset_balance()
        assert reset_response.status_code == 200
        assert reset_response.json()["balance"] == pytest.approx(STARTING_BALANCE, abs=0.01)

        # Response body and persisted state must be consistent after reset (spec §5.3).
        balance_response = api_client.get_balance()
        assert balance_response.json()["balance"] == pytest.approx(STARTING_BALANCE, abs=0.01)
