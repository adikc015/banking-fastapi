from decimal import Decimal

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.account import Account
from models.transaction import Transaction, TransactionType
from services.fraud_detection import fraud_detector


def _to_decimal(amount: float) -> Decimal:
	return Decimal(str(amount)).quantize(Decimal("0.01"))


async def deposit(db: AsyncSession, account_id: int, amount: float, location: str | None = None) -> Transaction:
	value = _to_decimal(amount)
	if value <= 0:
		raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Amount must be greater than zero")

	async with db.begin():
		account = await db.get(Account, account_id)
		if account is None:
			raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Account not found")

		account.balance += value
		reasons = fraud_detector.evaluate(account_id, float(value), location)
		tx = Transaction(
			transaction_type=TransactionType.DEPOSIT,
			to_account_id=account_id,
			amount=value,
			status="flagged" if reasons else "completed",
			location=location,
			fraud_reason=", ".join(reasons) if reasons else None,
		)
		db.add(tx)

	await db.refresh(tx)
	return tx


async def withdraw(db: AsyncSession, account_id: int, amount: float, location: str | None = None) -> Transaction:
	value = _to_decimal(amount)
	if value <= 0:
		raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Amount must be greater than zero")

	async with db.begin():
		query = select(Account).where(Account.id == account_id).with_for_update()
		result = await db.execute(query)
		account = result.scalar_one_or_none()
		if account is None:
			raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Account not found")

		new_balance = account.balance - value
		if new_balance < account.min_balance:
			raise HTTPException(
				status_code=status.HTTP_400_BAD_REQUEST,
				detail="Minimum balance rule violated",
			)

		account.balance = new_balance
		reasons = fraud_detector.evaluate(account_id, float(value), location)
		tx = Transaction(
			transaction_type=TransactionType.WITHDRAW,
			from_account_id=account_id,
			amount=value,
			status="flagged" if reasons else "completed",
			location=location,
			fraud_reason=", ".join(reasons) if reasons else None,
		)
		db.add(tx)

	await db.refresh(tx)
	return tx


async def transfer(
	db: AsyncSession,
	from_account_id: int,
	to_account_id: int,
	amount: float,
	location: str | None = None,
) -> Transaction:
	value = _to_decimal(amount)
	if value <= 0:
		raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Amount must be greater than zero")
	if from_account_id == to_account_id:
		raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Source and destination must differ")

	async with db.begin():
		ordered_ids = sorted([from_account_id, to_account_id])
		query = select(Account).where(Account.id.in_(ordered_ids)).with_for_update()
		result = await db.execute(query)
		accounts = {account.id: account for account in result.scalars().all()}

		sender = accounts.get(from_account_id)
		receiver = accounts.get(to_account_id)
		if sender is None or receiver is None:
			raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="One or both accounts not found")

		sender_balance_after = sender.balance - value
		if sender_balance_after < sender.min_balance:
			raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Minimum balance rule violated")

		sender.balance = sender_balance_after
		receiver.balance += value

		reasons = fraud_detector.evaluate(from_account_id, float(value), location)
		tx = Transaction(
			transaction_type=TransactionType.TRANSFER,
			from_account_id=from_account_id,
			to_account_id=to_account_id,
			amount=value,
			status="flagged" if reasons else "completed",
			location=location,
			fraud_reason=", ".join(reasons) if reasons else None,
		)
		db.add(tx)

	await db.refresh(tx)
	return tx
