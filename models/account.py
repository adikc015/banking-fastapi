import enum
from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base


class AccountType(str, enum.Enum):
	SAVINGS = "savings"
	CURRENT = "current"


class Account(Base):
	__tablename__ = "accounts"

	id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
	user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
	account_number: Mapped[str] = mapped_column(String(20), unique=True, index=True, nullable=False)
	account_type: Mapped[AccountType] = mapped_column(Enum(AccountType), nullable=False)
	balance: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0.00"), nullable=False)
	min_balance: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0.00"), nullable=False)
	created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

	owner = relationship("User", back_populates="accounts")
