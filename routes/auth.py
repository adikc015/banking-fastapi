from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models.user import User, UserRole
from schemas.auth import KYCRequest, LoginResponse, RegisterRequest
from schemas.user import UserOut
from utils.security import (
	create_access_token,
	get_current_user,
	get_user_by_email,
	hash_password,
	verify_password,
)

router = APIRouter()


@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
async def register(payload: RegisterRequest, db: AsyncSession = Depends(get_db)) -> User:
	existing = await get_user_by_email(db, payload.email)
	if existing:
		raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")

	role = UserRole.ADMIN if payload.role.lower() == "admin" else UserRole.CUSTOMER
	user = User(
		full_name=payload.full_name,
		email=payload.email,
		password_hash=hash_password(payload.password),
		role=role,
	)
	db.add(user)
	await db.commit()
	await db.refresh(user)
	return user


@router.post("/login", response_model=LoginResponse)
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)) -> LoginResponse:
	# OAuth2PasswordRequestForm uses 'username', so this project treats it as email.
	user = await get_user_by_email(db, form_data.username)
	if user is None or not verify_password(form_data.password, user.password_hash):
		raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

	token = create_access_token(subject=str(user.id), role=user.role.value)
	return LoginResponse(access_token=token)


@router.get("/me", response_model=UserOut)
async def me(current_user: User = Depends(get_current_user)) -> User:
	return current_user


@router.post("/kyc", response_model=UserOut)
async def verify_kyc(
	payload: KYCRequest,
	db: AsyncSession = Depends(get_db),
	current_user: User = Depends(get_current_user),
) -> User:
	aadhaar_ok = payload.aadhaar_number.isdigit() and len(payload.aadhaar_number) == 12
	pan_ok = len(payload.pan_number) == 10 and payload.pan_number[:5].isalpha() and payload.pan_number[-1].isalpha()

	if not aadhaar_ok or not pan_ok:
		raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid Aadhaar or PAN format")

	current_user.aadhaar_number = payload.aadhaar_number
	current_user.pan_number = payload.pan_number.upper()
	current_user.is_kyc_verified = True

	await db.commit()
	await db.refresh(current_user)
	return current_user


@router.get("/admin/users", response_model=list[UserOut])
async def list_users(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)) -> list[User]:
	if current_user.role != UserRole.ADMIN:
		raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")

	result = await db.execute(select(User).order_by(User.id))
	return list(result.scalars().all())
