import enum
from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from database import Base


class TransactionType(str, enum.Enum):
	DEPOSIT = "deposit"
	WITHDRAW = "withdraw"
	TRANSFER = "transfer"


class Transaction(Base):
	__tablename__ = "transactions"

	id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
	transaction_type: Mapped[TransactionType] = mapped_column(Enum(TransactionType), nullable=False)
	from_account_id: Mapped[int | None] = mapped_column(ForeignKey("accounts.id"), nullable=True, index=True)
	to_account_id: Mapped[int | None] = mapped_column(ForeignKey("accounts.id"), nullable=True, index=True)
	amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
	status: Mapped[str] = mapped_column(String(30), default="completed", nullable=False)
	location: Mapped[str | None] = mapped_column(String(100), nullable=True)
	fraud_reason: Mapped[str | None] = mapped_column(String(255), nullable=True)
	created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
