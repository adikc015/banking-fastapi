import os

from authlib.integrations.starlette_client import OAuth
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import HTMLResponse
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models.user import User, UserRole
from utils.security import create_access_token, get_user_by_email, hash_password

router = APIRouter(prefix="/oauth", tags=["OAuth"])
oauth = OAuth()

google_client_id = os.getenv("OAUTH_GOOGLE_CLIENT_ID")
google_client_secret = os.getenv("OAUTH_GOOGLE_CLIENT_SECRET")
google_redirect_uri = os.getenv("OAUTH_GOOGLE_REDIRECT_URI")

if google_client_id and google_client_secret:
	oauth.register(
		name="google",
		client_id=google_client_id,
		client_secret=google_client_secret,
		server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
		client_kwargs={"scope": "openid email profile"},
	)


def _get_google_client():
	client = oauth.create_client("google")
	if client is None:
		raise HTTPException(
			status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
			detail="Google OAuth is not configured. Set client id and secret in .env.",
		)
	return client


@router.get("/google/start")
async def google_start(request: Request):
	client = _get_google_client()
	if not google_redirect_uri:
		raise HTTPException(
			status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
			detail="Google OAuth redirect URI is missing in .env.",
		)
	return await client.authorize_redirect(request, google_redirect_uri)


@router.get("/google/callback")
async def google_callback(request: Request, db: AsyncSession = Depends(get_db)):
	client = _get_google_client()

	token = await client.authorize_access_token(request)
	userinfo = token.get("userinfo")
	if userinfo is None:
		response = await client.get("userinfo", token=token)
		userinfo = response.json()

	email = userinfo.get("email")
	full_name = userinfo.get("name") or userinfo.get("given_name") or "Google User"
	if not email:
		raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Google account did not return an email")

	user = await get_user_by_email(db, email)
	if user is None:
		user = User(
			full_name=full_name,
			email=email,
			password_hash=hash_password(email + "google-oauth"),
			role=UserRole.CUSTOMER,
		)
		db.add(user)
		await db.commit()
		await db.refresh(user)

	access_token = create_access_token(subject=str(user.id), role=user.role.value)
	return HTMLResponse(
		f"""
		<!doctype html>
		<html>
		  <body>
		    <script>
		      localStorage.setItem('banking_token', {access_token!r});
		      window.close();
		    </script>
		    <p>OAuth login complete. You can close this window.</p>
		  </body>
		</html>
		"""
	)
