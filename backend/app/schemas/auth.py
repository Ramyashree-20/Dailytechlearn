from pydantic import BaseModel, EmailStr, Field


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    # Optional — lets a learner also log in with a username instead of
    # their email later (see LoginRequest.identifier). Email stays
    # required either way; this only adds a second way in.
    username: str | None = Field(default=None, min_length=3, max_length=50)


class LoginRequest(BaseModel):
    # Accepts either the account's email OR its username — resolved
    # against both columns in auth_service.authenticate_user(). Plain
    # str (not EmailStr) since a username isn't a valid email shape.
    identifier: str = Field(min_length=1)
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
