from pydantic import BaseModel, ConfigDict, Field


class DepositRequest(BaseModel):
    account_id: int
    amount: float = Field(gt=0)
    location: str | None = None


class WithdrawRequest(BaseModel):
    account_id: int
    amount: float = Field(gt=0)
    location: str | None = None


class TransferRequest(BaseModel):
    from_account_id: int
    to_account_id: int
    amount: float = Field(gt=0)
    location: str | None = None


class TransactionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    transaction_type: str
    from_account_id: int | None
    to_account_id: int | None
    amount: float
    status: str
    location: str | None
    fraud_reason: str | None
