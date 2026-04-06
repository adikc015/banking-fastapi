from sqlalchemy.ext.asyncio import AsyncSession

from models.notification import Notification
from utils.logger import get_logger

logger = get_logger(__name__)


def send_transaction_alert(user_email: str, message: str) -> None:
	logger.info("Transaction alert to %s: %s", user_email, message)



def send_loan_update(user_email: str, message: str) -> None:
	logger.info("Loan update to %s: %s", user_email, message)


async def create_notification(
	db: AsyncSession,
	user_id: int,
	title: str,
	message: str,
	channel: str = "in-app",
) -> Notification:
	notification = Notification(user_id=user_id, title=title, message=message, channel=channel)
	db.add(notification)
	await db.commit()
	await db.refresh(notification)
	return notification
