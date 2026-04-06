from pydantic import BaseModel, ConfigDict, Field


class LoanApplyRequest(BaseModel):
    principal_amount: float = Field(gt=0)
    annual_interest_rate: float = Field(ge=0, le=40)
    tenure_months: int = Field(gt=0, le=600)


class LoanReviewRequest(BaseModel):
    approve: bool


class LoanOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    principal_amount: float
    annual_interest_rate: float
    tenure_months: int
    emi: float
    status: str
