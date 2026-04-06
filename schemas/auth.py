from pydantic import BaseModel, EmailStr, Field


class RegisterRequest(BaseModel):
    full_name: str = Field(min_length=2, max_length=120)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    role: str = Field(default="customer")


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class KYCRequest(BaseModel):
    aadhaar_number: str = Field(min_length=12, max_length=12)
    pan_number: str = Field(min_length=10, max_length=10)
