from collections.abc import AsyncGenerator
import os

from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

load_dotenv(override=True)

DATABASE_URL = os.getenv(
	"DATABASE_URL",
	"mysql+aiomysql://root:password@127.0.0.1:3306/banking_app",
)

engine = create_async_engine(DATABASE_URL, echo=False, future=True, pool_pre_ping=True)
AsyncSessionLocal = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)


class Base(DeclarativeBase):
	pass


async def get_db() -> AsyncGenerator[AsyncSession, None]:
	async with AsyncSessionLocal() as session:
		yield session


async def init_db() -> None:
	# Import models here so SQLAlchemy can discover metadata before create_all.
	from models import account, loan, notification, transaction, user  # noqa: F401

	async with engine.begin() as conn:
		await conn.run_sync(Base.metadata.create_all)
