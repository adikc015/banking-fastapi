import enum
from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, Numeric
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base


class LoanStatus(str, enum.Enum):
	PENDING = "pending"
	APPROVED = "approved"
	REJECTED = "rejected"


class Loan(Base):
	__tablename__ = "loans"

	id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
	user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
	principal_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
	annual_interest_rate: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
	tenure_months: Mapped[int] = mapped_column(Integer, nullable=False)
	emi: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
	status: Mapped[LoanStatus] = mapped_column(Enum(LoanStatus), default=LoanStatus.PENDING, nullable=False)
	created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

	user = relationship("User", back_populates="loans")
