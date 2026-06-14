import re
import uuid
from datetime import datetime
from pydantic import BaseModel, Field, EmailStr, field_validator, ConfigDict


class UserRegisterRequest(BaseModel):
    first_name: str = Field(
        ...,
        min_length=2,
        max_length=50,
        description="First name of the user",
    )

    last_name: str = Field(
        ...,
        min_length=2,
        max_length=50,
        description="Last name of the user",
    )

    email: EmailStr = Field(
        ...,
        description="Valid user email, auto-validated and cleaned",
        max_length=100,
    )

    password: str = Field(
        ...,
        description="Enter password containing at least one number and one special character",
        max_length=255,
        min_length=8,
    )

    @field_validator("first_name", mode="before")
    @classmethod
    def strip_first_name(cls, value: str) -> str:
        return value.strip() if isinstance(value, str) else value

    @field_validator("last_name", mode="before")
    @classmethod
    def strip_last_name(cls, value: str) -> str:
        return value.strip() if isinstance(value, str) else value

    @field_validator("email", mode="before")
    @classmethod
    def pre_strip_email(cls, value: str) -> str:
        if isinstance(value, str):
            return value.strip()
        return value

    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, value: str) -> str:
        if len(value) < 8:
            raise ValueError("Password must be at least 8 characters long.")

        if not any(char.isdigit() for char in value):
            raise ValueError(
                "Password must contain at least one numerical digit (0-9)."
            )

        # Regex scans for standard special punctuation symbols
        special_char_regex = re.compile(r"[!@#$%^&*(),.?\":{}|<>_+\-=~`[\]\\]")
        if not special_char_regex.search(value):
            raise ValueError("Password must contain at least one special character.")

        return value


class UserLoginRequest(BaseModel):
    email: EmailStr = Field(
        ...,
        description="Enter your valid email",
        max_length=100,
    )

    password: str = Field(
        ...,
        description="Enter your password",
        max_length=255,
    )

class UserResponse(BaseModel):
    id: uuid.UUID
    first_name: str
    last_name: str
    email: str
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class Token(BaseModel):
    access_token: str
    token_type: str
    model_config = ConfigDict(from_attributes=True)
