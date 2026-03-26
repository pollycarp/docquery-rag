"""
Structured JSON Logging
-----------------------
Configures the application logger to output JSON lines instead of plain text.

Why JSON logs?
  Plain text logs are hard to search and filter.
  JSON logs can be ingested by tools like Datadog, Loki, or CloudWatch
  and queried like a database: "show me all requests slower than 2000ms".

Every log line will look like:
  {"timestamp": "2025-01-01T12:00:00", "level": "INFO", "message": "request",
   "method": "POST", "path": "/api/query", "status_code": 200, "duration_ms": 450}
"""

import json
import logging
import sys
from datetime import datetime, timezone


class JSONFormatter(logging.Formatter):
    """Formats log records as single-line JSON strings."""

    def format(self, record: logging.LogRecord) -> str:
        log_entry: dict = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level":     record.levelname,
            "logger":    record.name,
            "message":   record.getMessage(),
        }

        # Any extra fields passed via logger.info("msg", extra={...})
        # are attached directly to the LogRecord — pick them up here
        reserved = logging.LogRecord.__dict__.keys() | {
            "message", "asctime", "exc_info", "exc_text", "stack_info"
        }
        for key, value in record.__dict__.items():
            if key not in reserved and not key.startswith("_"):
                log_entry[key] = value

        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_entry)


def setup_logging(level: int = logging.INFO) -> None:
    """
    Call once at app startup to configure JSON logging for the whole app.
    After calling this, use: logger = logging.getLogger("rag")
    """
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JSONFormatter())

    root_logger = logging.getLogger("rag")
    root_logger.setLevel(level)
    root_logger.handlers = [handler]
    root_logger.propagate = False


# Module-level logger — import this wherever you need to log
logger = logging.getLogger("rag")
