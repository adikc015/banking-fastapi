from utils.logger import get_logger

logger = get_logger(__name__)


def send_transaction_alert(user_email: str, message: str) -> None:
    logger.info("Transaction alert to %s: %s", user_email, message)


def send_loan_update(user_email: str, message: str) -> None:
    logger.info("Loan update to %s: %s", user_email, message)
