import random
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models.account import Account, AccountType
from models.user import User
from schemas.account import AccountCreateRequest, AccountOut, InterestRequest
from utils.security import get_current_user

router = APIRouter()


def _new_account_number() -> str:
	return "AC" + "".join(random.choices("0123456789", k=10))


@router.post("/", response_model=AccountOut, status_code=status.HTTP_201_CREATED)
async def create_account(
	payload: AccountCreateRequest,
	db: AsyncSession = Depends(get_db),
	current_user: User = Depends(get_current_user),
) -> Account:
	if not current_user.is_kyc_verified:
		raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="KYC must be verified")

	acc_type = AccountType(payload.account_type)
	min_balance = Decimal("1000.00") if acc_type == AccountType.SAVINGS else Decimal("0.00")

	account = Account(
		user_id=current_user.id,
		account_number=_new_account_number(),
		account_type=acc_type,
		balance=Decimal("0.00"),
		min_balance=min_balance,
	)
	db.add(account)
	await db.commit()
	await db.refresh(account)
	return account


@router.get("/", response_model=list[AccountOut])
async def my_accounts(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)) -> list[Account]:
	result = await db.execute(select(Account).where(Account.user_id == current_user.id).order_by(Account.id))
	return list(result.scalars().all())


@router.post("/{account_id}/interest", response_model=AccountOut)
async def apply_interest(
	account_id: int,
	payload: InterestRequest,
	db: AsyncSession = Depends(get_db),
	current_user: User = Depends(get_current_user),
) -> Account:
	account = await db.get(Account, account_id)
	if account is None or account.user_id != current_user.id:
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Account not found")

	if account.account_type != AccountType.SAVINGS:
		raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Interest is only for savings account")

	rate = Decimal(str(payload.annual_rate)) / Decimal("100")
	monthly_interest = (account.balance * rate / Decimal("12")).quantize(Decimal("0.01"))
	account.balance += monthly_interest

	await db.commit()
	await db.refresh(account)
	return account
