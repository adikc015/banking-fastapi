from datetime import datetime, timedelta, timezone
import os

import bcrypt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models.user import User, UserRole

SECRET_KEY = os.getenv("SECRET_KEY", "replace-this-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def hash_password(password: str) -> str:
	return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
	return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))


def create_access_token(subject: str, role: str, expires_delta: timedelta | None = None) -> str:
	expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
	payload = {"sub": subject, "role": role, "exp": expire}
	return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


async def get_current_user(
	token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)
) -> User:
	credentials_exception = HTTPException(
		status_code=status.HTTP_401_UNAUTHORIZED,
		detail="Could not validate credentials",
		headers={"WWW-Authenticate": "Bearer"},
	)

	try:
		payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
		user_id = payload.get("sub")
		if user_id is None:
			raise credentials_exception
	except JWTError as exc:
		raise credentials_exception from exc

	user = await db.get(User, int(user_id))
	if user is None:
		raise credentials_exception
	return user


async def get_current_admin(current_user: User = Depends(get_current_user)) -> User:
	if current_user.role != UserRole.ADMIN:
		raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
	return current_user


async def get_user_by_email(db: AsyncSession, email: str) -> User | None:
	query = select(User).where(User.email == email)
	result = await db.execute(query)
	return result.scalar_one_or_none()
