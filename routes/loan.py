from decimal import Decimal

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models.loan import Loan, LoanStatus
from models.user import User, UserRole
from schemas.loan import LoanApplyRequest, LoanOut, LoanReviewRequest
from services.loan_service import calculate_emi
from services.notification_service import send_loan_update
from utils.security import get_current_user

router = APIRouter()


@router.post("/apply", response_model=LoanOut, status_code=status.HTTP_201_CREATED)
async def apply_loan(
	payload: LoanApplyRequest,
	db: AsyncSession = Depends(get_db),
	current_user: User = Depends(get_current_user),
) -> Loan:
	principal = Decimal(str(payload.principal_amount))
	rate = Decimal(str(payload.annual_interest_rate))
	emi = calculate_emi(principal, rate, payload.tenure_months)

	loan = Loan(
		user_id=current_user.id,
		principal_amount=principal,
		annual_interest_rate=rate,
		tenure_months=payload.tenure_months,
		emi=emi,
		status=LoanStatus.PENDING,
	)
	db.add(loan)
	await db.commit()
	await db.refresh(loan)
	return loan


@router.get("/", response_model=list[LoanOut])
async def my_loans(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)) -> list[Loan]:
	rows = await db.execute(select(Loan).where(Loan.user_id == current_user.id).order_by(Loan.id.desc()))
	return list(rows.scalars().all())


@router.post("/{loan_id}/review", response_model=LoanOut)
async def review_loan(
	loan_id: int,
	payload: LoanReviewRequest,
	background_tasks: BackgroundTasks,
	db: AsyncSession = Depends(get_db),
	current_user: User = Depends(get_current_user),
) -> Loan:
	if current_user.role != UserRole.ADMIN:
		raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")

	loan = await db.get(Loan, loan_id)
	if loan is None:
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Loan not found")

	loan.status = LoanStatus.APPROVED if payload.approve else LoanStatus.REJECTED
	await db.commit()
	await db.refresh(loan)

	user = await db.get(User, loan.user_id)
	if user:
		background_tasks.add_task(
			send_loan_update,
			user.email,
			f"Your loan #{loan.id} is {loan.status.value}",
		)

	return loan


@router.get("/admin/pending", response_model=list[LoanOut])
async def pending_loans(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)) -> list[Loan]:
	if current_user.role != UserRole.ADMIN:
		raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")

	rows = await db.execute(select(Loan).where(Loan.status == LoanStatus.PENDING).order_by(Loan.id))
	return list(rows.scalars().all())
