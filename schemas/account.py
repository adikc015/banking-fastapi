from pydantic import BaseModel, ConfigDict, Field


class AccountCreateRequest(BaseModel):
    account_type: str = Field(pattern="^(savings|current)$")


class AccountOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    account_number: str
    account_type: str
    balance: float
    min_balance: float


class InterestRequest(BaseModel):
    annual_rate: float = Field(gt=0, lt=30)
