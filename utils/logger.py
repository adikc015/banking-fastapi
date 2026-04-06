import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path


def configure_logging() -> None:
	Path("logs").mkdir(exist_ok=True)
	formatter = logging.Formatter("%(asctime)s | %(levelname)s | %(name)s | %(message)s")

	file_handler = RotatingFileHandler("logs/app.log", maxBytes=1_000_000, backupCount=3)
	file_handler.setFormatter(formatter)

	stream_handler = logging.StreamHandler()
	stream_handler.setFormatter(formatter)

	root = logging.getLogger()
	root.setLevel(logging.INFO)

	if not root.handlers:
		root.addHandler(file_handler)
		root.addHandler(stream_handler)


def get_logger(name: str) -> logging.Logger:
	return logging.getLogger(name)
