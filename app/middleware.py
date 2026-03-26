"""
Request Logging Middleware
--------------------------
Automatically runs for EVERY request before and after the route handler.

What it does:
  1. Generates a unique request ID (e.g. "a3f7b2c1")
  2. Records the start time
  3. Lets the request proceed normally
  4. After the response is ready, logs method, path, status, and duration
  5. Adds X-Request-ID and X-Response-Time headers to the response
     (useful for debugging — visible in browser dev tools)

Example log output:
  {"level":"INFO","message":"request","method":"POST","path":"/api/query",
   "status_code":200,"duration_ms":8432.1,"request_id":"a3f7b2c1"}
"""

import time
import uuid
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from app.logging_config import logger


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        request_id = uuid.uuid4().hex[:8]   # short 8-char ID, e.g. "a3f7b2c1"
        start_time = time.perf_counter()

        response = await call_next(request)

        duration_ms = round((time.perf_counter() - start_time) * 1000, 1)

        logger.info(
            "request",
            extra={
                "request_id":  request_id,
                "method":      request.method,
                "path":        request.url.path,
                "status_code": response.status_code,
                "duration_ms": duration_ms,
            },
        )

        # Attach helpful headers to every response
        response.headers["X-Request-ID"]    = request_id
        response.headers["X-Response-Time"] = f"{duration_ms}ms"

        return response
