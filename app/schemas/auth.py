from pydantic import BaseModel, Field


class RegisterRequest(BaseModel):
    email: str  # validated by router / regex is sufficient at API boundary
    password: str = Field(..., min_length=8)
    display_name: str | None = None


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: int
    display_name: str | None


class UserPublic(BaseModel):
    id: int
    email: str
    display_name: str | None
