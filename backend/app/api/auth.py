from typing import Annotated

from fastapi import APIRouter, Depends, Request, Response
from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from app.api.deps import current_user
from app.domain.entities import Role, User

router = APIRouter(prefix="/api/v1/auth", tags=["accounts"])


class AuthInput(BaseModel):
    model_config = ConfigDict(extra="forbid")


class LoginInput(AuthInput):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value):
        return str(value).lower()


class RegisterInput(LoginInput):
    name: str = Field(min_length=1, max_length=120)
    password: str = Field(min_length=12, max_length=128)
    role: Role

    @field_validator("name")
    @classmethod
    def normalize_name(cls, value):
        if not value.strip():
            raise ValueError("Укажите имя")
        return value.strip()


class ProfileInput(AuthInput):
    name: str = Field(min_length=1, max_length=120)


class PasswordInput(AuthInput):
    current_password: str = Field(min_length=1, max_length=128)
    new_password: str = Field(min_length=12, max_length=128)


def cookies(response: Response, request: Request, token: str, csrf: str):
    options = dict(
        secure=request.app.state.settings.app_env == "production",
        samesite="lax",
        path="/",
        max_age=request.app.state.settings.session_days * 86400,
    )
    response.set_cookie("sana_session", token, httponly=True, **options)
    response.set_cookie("sana_csrf", csrf, httponly=False, **options)


def clear_cookies(response: Response):
    response.delete_cookie("sana_session", path="/")
    response.delete_cookie("sana_csrf", path="/")


@router.post("/register", status_code=201, response_model=User)
async def register(body: RegisterInput, request: Request, response: Response):
    accounts = request.app.state.accounts
    await accounts.throttle(
        "register:" + (request.client.host if request.client else "unknown"), 20
    )
    await accounts.register(body.name, str(body.email), body.password, body.role)
    user, token, csrf = await accounts.login(str(body.email), body.password)
    cookies(response, request, token, csrf)
    return user


@router.post("/login", response_model=User)
async def login(body: LoginInput, request: Request, response: Response):
    await request.app.state.accounts.throttle(
        "login-ip:" + (request.client.host if request.client else "unknown"),
        100,
    )
    user, token, csrf = await request.app.state.accounts.login(str(body.email), body.password)
    # Revoke the browser's previous session when switching accounts.
    if previous := request.cookies.get("sana_session"):
        await request.app.state.accounts.logout(previous)
    cookies(response, request, token, csrf)
    return user


@router.get("/me", response_model=User)
async def me(user: Annotated[User, Depends(current_user)]):
    return user


@router.post("/logout")
async def logout(
    request: Request, response: Response, user: Annotated[User, Depends(current_user)]
):
    await request.app.state.accounts.logout(request.cookies.get("sana_session", ""))
    clear_cookies(response)
    return {"ok": True}


@router.patch("/profile", response_model=User)
async def profile(
    body: ProfileInput, request: Request, user: Annotated[User, Depends(current_user)]
):
    name = body.name.strip()
    if not name:
        from app.domain.entities import DomainError

        raise DomainError("invalid_name", "Укажите имя.", 422)
    return await request.app.state.accounts.profile(user.id, name)


@router.post("/password")
async def password(
    body: PasswordInput,
    request: Request,
    response: Response,
    user: Annotated[User, Depends(current_user)],
):
    await request.app.state.accounts.change_password(
        user.id, body.current_password, body.new_password
    )
    clear_cookies(response)
    return {"ok": True, "message": "Пароль изменён. Войдите с новым паролем."}
