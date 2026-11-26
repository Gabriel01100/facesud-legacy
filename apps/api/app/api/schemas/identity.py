from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class LoginRequest(BaseModel):
    email: str = Field(min_length=3, max_length=320)
    password: str = Field(min_length=1, max_length=1024)


class AuthenticatedAccount(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    email: str


class LoginResponse(AuthenticatedAccount):
    csrf_token: str


class CsrfTokenResponse(BaseModel):
    csrf_token: str
