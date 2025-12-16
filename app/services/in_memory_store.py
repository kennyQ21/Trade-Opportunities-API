"""
In-Memory Store Module
Provides in-memory storage for API keys and rate limiting
"""
from collections import defaultdict, deque
from datetime import datetime, timedelta
from typing import Dict, Deque, Tuple, Optional
import asyncio
import secrets


class APIKeyStore:
    """In-memory storage for API keys"""
    
    def __init__(self):
        # Store: {api_key: user_id}
        self.keys: Dict[str, str] = {}
        
        # Pre-populate with demo keys
        self.keys["demo-key-12345"] = "demo"
        self.keys["guest-key-67890"] = "guest"
        self.keys["test-key-abcde"] = "test"
    
    def generate_key(self, user_id: str) -> str:
        """Generate a new API key for a user"""
        api_key = f"{user_id}-{secrets.token_urlsafe(16)}"
        self.keys[api_key] = user_id
        return api_key
    
    def verify_key(self, api_key: str) -> Optional[str]:
        """Verify API key and return user_id"""
        return self.keys.get(api_key)
    
    def revoke_key(self, api_key: str) -> bool:
        """Revoke an API key"""
        if api_key in self.keys:
            del self.keys[api_key]
            return True
        return False


class RateLimiter:
    """In-memory rate limiter with per-user tracking"""
    
    def __init__(self, requests_per_minute: int = 5, requests_per_hour: int = 30):
        self.requests_per_minute = requests_per_minute
        self.requests_per_hour = requests_per_hour
        
        # Store timestamps of requests per user
        self.minute_requests: Dict[str, Deque[datetime]] = defaultdict(lambda: deque())
        self.hour_requests: Dict[str, Deque[datetime]] = defaultdict(lambda: deque())
        
        # Lock for thread safety
        self._lock = asyncio.Lock()
    
    async def check_rate_limit(self, user_id: str) -> Tuple[bool, str]:
        """
        Check if user has exceeded rate limits
        
        Args:
            user_id: User identifier
            
        Returns:
            (allowed, message) tuple
        """
        async with self._lock:
            now = datetime.utcnow()
            
            # Clean old entries
            self._clean_old_entries(user_id, now)
            
            # Check minute limit
            if len(self.minute_requests[user_id]) >= self.requests_per_minute:
                oldest = self.minute_requests[user_id][0]
                wait_time = 60 - (now - oldest).total_seconds()
                return False, f"Rate limit exceeded. Try again in {int(wait_time)} seconds."
            
            # Check hour limit
            if len(self.hour_requests[user_id]) >= self.requests_per_hour:
                oldest = self.hour_requests[user_id][0]
                wait_time = 3600 - (now - oldest).total_seconds()
                return False, f"Hourly rate limit exceeded. Try again in {int(wait_time / 60)} minutes."
            
            # Record request
            self.minute_requests[user_id].append(now)
            self.hour_requests[user_id].append(now)
            
            return True, "OK"
    
    def _clean_old_entries(self, user_id: str, now: datetime):
        """Remove entries older than the time window"""
        minute_ago = now - timedelta(minutes=1)
        hour_ago = now - timedelta(hours=1)
        
        # Clean minute window
        while self.minute_requests[user_id] and self.minute_requests[user_id][0] < minute_ago:
            self.minute_requests[user_id].popleft()
        
        # Clean hour window
        while self.hour_requests[user_id] and self.hour_requests[user_id][0] < hour_ago:
            self.hour_requests[user_id].popleft()
    
    def get_remaining_requests(self, user_id: str) -> Dict[str, int]:
        """Get remaining requests for user"""
        now = datetime.utcnow()
        self._clean_old_entries(user_id, now)
        
        return {
            "per_minute": self.requests_per_minute - len(self.minute_requests[user_id]),
            "per_hour": self.requests_per_hour - len(self.hour_requests[user_id])
        }


# Global instances
api_key_store = APIKeyStore()
rate_limiter = RateLimiter()
