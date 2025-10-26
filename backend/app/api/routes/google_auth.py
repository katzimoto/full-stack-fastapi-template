from datetime import timedelta

from authlib.integrations.starlette_client import OAuth
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import RedirectResponse

from app import crud
from app.api.deps import SessionDep
from app.core import security
from app.core.config import settings
from app.models import Token

router = APIRouter(tags=["login"])


oauth = OAuth()
oauth.register(
    name="google",
    client_id=settings.GOOGLE_CLIENT_ID,
    client_secret=settings.GOOGLE_CLIENT_SECRET,
    access_token_url="https://accounts.google.com/o/oauth2/token",
    authorize_url="https://accounts.google.com/o/oauth2/auth",
    api_base_url="https://www.googleapis.com/oauth2/v1/",
)


@router.get("/auth/google")
async def auth_google(request: Request):
    redirect_uri = (
        settings.FRONTEND_HOST + settings.API_V1_STR + "/auth/google/callback"
    )
    return await oauth.google.authorize_redirect(request, redirect_uri)


@router.get("/auth/google/callback")
async def auth_google_callback(session: SessionDep, request: Request) -> Token:
    token = await oauth.google.authorize_access_token(request)
    user_info = await oauth.google.get("userinfo", token=token)
    # Process user_info and create a user session
    user = crud.get_user_by_email(session=session, email=user_info.get("email"))
    if not user:
        # Create a new user if not exists
        return RedirectResponse(url=settings.FRONTEND_HOST + "/register")
    elif not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    return Token(
        access_token=security.create_access_token(
            user.id, expires_delta=access_token_expires
        )
    )
