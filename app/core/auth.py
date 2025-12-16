"""
Authentication Module
Handles API key authentication for the FastAPI application
"""
from fastapi import HTTPException, Security, status
from fastapi.security import APIKeyHeader
from typing import Optional

from app.services.in_memory_store import api_key_store

# API Key header scheme
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


async def get_current_user(api_key: Optional[str] = Security(api_key_header)):
    """Verify API key and return User object"""
    from app.models import User
    
    # Allow guest access if no API key provided
    if api_key is None:
        return User(username="guest", disabled=False)
    
    # Verify API key
    user_id = api_key_store.verify_key(api_key)
    
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired API key",
            headers={"WWW-Authenticate": "ApiKey"},
        )
    
    return User(username=user_id, disabled=False)
