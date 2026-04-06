from collections import defaultdict, deque
from datetime import datetime, timedelta, timezone
from functools import wraps

from fastapi import HTTPException, Request, status


class InMemoryLimiter:
	def __init__(self) -> None:
		self._hits: dict[str, deque[datetime]] = defaultdict(deque)

	@staticmethod
	def _parse_limit(limit_rule: str) -> tuple[int, timedelta]:
		number, unit = limit_rule.split("/")
		value = int(number)
		unit = unit.strip().lower()

		if unit in {"second", "seconds"}:
			return value, timedelta(seconds=1)
		if unit in {"minute", "minutes"}:
			return value, timedelta(minutes=1)
		if unit in {"hour", "hours"}:
			return value, timedelta(hours=1)
		raise ValueError(f"Unsupported rate limit unit: {unit}")

	def limit(self, limit_rule: str):
		max_requests, window = self._parse_limit(limit_rule)

		def decorator(func):
			@wraps(func)
			async def wrapper(*args, **kwargs):
				request = kwargs.get("request")
				if request is None:
					for item in args:
						if isinstance(item, Request):
							request = item
							break

				if request is None:
					return await func(*args, **kwargs)

				client_host = request.client.host if request.client else "unknown"
				key = f"{client_host}:{request.url.path}"
				now = datetime.now(timezone.utc)

				queue = self._hits[key]
				while queue and (now - queue[0]) > window:
					queue.popleft()

				if len(queue) >= max_requests:
					raise HTTPException(
						status_code=status.HTTP_429_TOO_MANY_REQUESTS,
						detail="Rate limit exceeded. Try again later.",
					)

				queue.append(now)
				return await func(*args, **kwargs)

			return wrapper

		return decorator


limiter = InMemoryLimiter()
