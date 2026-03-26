"""
Shared API Dependencies
-----------------------
FastAPI "dependencies" are reusable functions that run before a route handler.
We use them for things every endpoint needs: auth, DB sessions, etc.

API Key Authentication
  Clients must include this header in every request:
    X-API-Key: your-secret-key

  If the key is missing or wrong, the request is rejected with 401.
"""

from fastapi import Security, HTTPException, status
from fastapi.security import APIKeyHeader
from app.config import settings

# Tells FastAPI to look for the key in the "X-API-Key" request header.
# auto_error=False means we handle the error ourselves (better error message).
_api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


def verify_api_key(api_key: str = Security(_api_key_header)) -> str:
    """
    Dependency that validates the X-API-Key header.
    Add `Depends(verify_api_key)` to any route that needs protection.
    """
    if not api_key or api_key != settings.api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key. Include it as: X-API-Key: <your-key>",
        )
    return api_key
