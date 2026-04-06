from collections import defaultdict, deque
from datetime import datetime, timedelta, timezone


class FraudDetector:
	def __init__(
		self,
		large_amount_threshold: float = 50_000.0,
		rapid_tx_limit: int = 3,
		window_seconds: int = 60,
	) -> None:
		self.large_amount_threshold = large_amount_threshold
		self.rapid_tx_limit = rapid_tx_limit
		self.window = timedelta(seconds=window_seconds)
		self.history: dict[int, deque[tuple[datetime, float, str | None]]] = defaultdict(deque)

	def evaluate(self, account_id: int, amount: float, location: str | None) -> list[str]:
		reasons: list[str] = []
		now = datetime.now(timezone.utc)
		account_history = self.history[account_id]

		while account_history and now - account_history[0][0] > self.window:
			account_history.popleft()

		if amount >= self.large_amount_threshold:
			reasons.append("Large amount transfer")

		if len(account_history) >= self.rapid_tx_limit:
			reasons.append("Multiple rapid transactions")

		if account_history and location and account_history[-1][2] and location != account_history[-1][2]:
			reasons.append("Location mismatch")

		account_history.append((now, amount, location))
		return reasons


fraud_detector = FraudDetector()
