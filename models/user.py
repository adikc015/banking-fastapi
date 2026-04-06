import enum
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base


class UserRole(str, enum.Enum):
	ADMIN = "admin"
	CUSTOMER = "customer"


class User(Base):
	__tablename__ = "users"

	id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
	full_name: Mapped[str] = mapped_column(String(120), nullable=False)
	email: Mapped[str] = mapped_column(String(120), unique=True, index=True, nullable=False)
	password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
	role: Mapped[UserRole] = mapped_column(Enum(UserRole), default=UserRole.CUSTOMER, nullable=False)
	aadhaar_number: Mapped[str | None] = mapped_column(String(12), nullable=True)
	pan_number: Mapped[str | None] = mapped_column(String(10), nullable=True)
	is_kyc_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
	created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

	accounts = relationship("Account", back_populates="owner", cascade="all,delete-orphan")
	loans = relationship("Loan", back_populates="user", cascade="all,delete-orphan")
