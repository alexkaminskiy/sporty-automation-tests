from pydantic import BaseModel, Field, ConfigDict
from enum import Enum


class BetOutcome(str, Enum):
    HOME = "HOME"
    DRAW = "DRAW"
    AWAY = "AWAY"


class BetSuccessResponse(BaseModel):
    model_config = ConfigDict(strict=False)  # allow int->float coercion for stake/odds/payout

    message: str
    match_id: str = Field(alias="matchId")
    selection: BetOutcome
    stake: float = Field(gt=0)
    odds: float = Field(gt=1)  # decimal odds are always > 1
    payout: float = Field(ge=0)
    balance: float = Field(ge=0)
    currency: str = Field(min_length=3, max_length=3)  # ISO 4217

class BetErrorResponse(BaseModel):
    error: str  # e.g. "invalid_selection"
    message: str  # e.g. "Selection must be one of: HOME, DRAW, AWAY."
