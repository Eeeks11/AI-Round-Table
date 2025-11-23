"""Rate limiting and retry logic for API calls."""

import asyncio
import time
from collections import deque
from dataclasses import dataclass, field
from typing import Dict, Optional, Callable, Any
from datetime import datetime, timedelta


@dataclass
class RateLimitConfig:
    """Rate limit configuration for a model."""
    
    requests_per_minute: int = 50
    tokens_per_minute: int = 100000
    requests_per_day: int = 1000
    
    # Retry configuration
    max_retries: int = 3
    initial_retry_delay: float = 2.0
    max_retry_delay: float = 60.0
    exponential_base: float = 2.0


@dataclass
class RateLimiter:
    """Rate limiter for API calls."""
    
    config: RateLimitConfig
    
    # Track requests
    _requests_minute: deque = field(default_factory=deque)
    _requests_day: deque = field(default_factory=deque)
    _tokens_minute: deque = field(default_factory=deque)
    
    def __post_init__(self):
        """Initialize deques."""
        self._requests_minute = deque()
        self._requests_day = deque()
        self._tokens_minute = deque()
    
    def _clean_old_entries(self, entries: deque, max_age_seconds: float):
        """Remove entries older than max_age_seconds."""
        current_time = time.time()
        while entries and (current_time - entries[0]) > max_age_seconds:
            entries.popleft()
    
    def _clean_old_token_entries(self):
        """Remove token entries older than 60 seconds."""
        current_time = time.time()
        while self._tokens_minute and (current_time - self._tokens_minute[0][0]) > 60:
            self._tokens_minute.popleft()
    
    def _get_request_count(self, window_seconds: float) -> int:
        """Get number of requests in the given time window."""
        if window_seconds == 60:
            self._clean_old_entries(self._requests_minute, 60)
            return len(self._requests_minute)
        elif window_seconds == 86400:  # 24 hours
            self._clean_old_entries(self._requests_day, 86400)
            return len(self._requests_day)
        return 0
    
    def _get_token_count(self) -> int:
        """Get number of tokens used in the last minute."""
        self._clean_old_token_entries()
        return sum(tokens for _, tokens in self._tokens_minute)
    
    async def wait_if_needed(self, estimated_tokens: int = 1000) -> None:
        """
        Wait if rate limits would be exceeded.
        
        Args:
            estimated_tokens: Estimated tokens for this request
        """
        # Clean old entries
        self._clean_old_entries(self._requests_minute, 60)
        self._clean_old_entries(self._requests_day, 86400)
        self._clean_old_token_entries()
        
        # Check daily limit
        if len(self._requests_day) >= self.config.requests_per_day:
            wait_time = 86400 - (time.time() - self._requests_day[0])
            if wait_time > 0:
                raise Exception(f"Daily rate limit exceeded. Reset in {wait_time/3600:.1f} hours")
        
        # Check minute limits
        requests_this_minute = len(self._requests_minute)
        tokens_this_minute = self._get_token_count()
        
        # Calculate wait time needed
        wait_time = 0
        
        # Check RPM limit
        # For high limits, leave a buffer. For low limits (<= 10), don't buffer to avoid blocking legitimate requests.
        buffer = 2 if self.config.requests_per_minute > 10 else 0
        
        if requests_this_minute >= self.config.requests_per_minute - buffer:
            if self._requests_minute:
                oldest_request = self._requests_minute[0]
                wait_time = max(wait_time, 60 - (time.time() - oldest_request))
            else:
                # If we are here with empty history, it means limit <= buffer (shouldn't happen with new logic)
                pass
        
        # Check TPM limit (leave 10% buffer)
        if tokens_this_minute + estimated_tokens >= self.config.tokens_per_minute * 0.9:
            if self._tokens_minute:
                oldest_token = self._tokens_minute[0][0]
                wait_time = max(wait_time, 60 - (time.time() - oldest_token))
            else:
                # No tokens used yet, but this request alone is too big or close to limit.
                # If this single request is larger than limit, we must either reject or wait.
                # Since we can't reject here, we wait if we are hitting rate limits.
                # However, waiting won't help if the request itself > limit.
                # But if we are just close to limit (buffer), we might not need to wait if it fits.
                
                # If empty history, we are at 0 usage.
                # If 0 + estimated > limit, we can't send it ever?
                # Or maybe we just send it (since we have 0 usage).
                pass

        
        # Add minimum spacing for low RPM limits (e.g., Gemini with 15 RPM)
        # This spreads requests evenly: 15 RPM = 1 request every 4 seconds
        if self.config.requests_per_minute <= 15 and self._requests_minute:
            min_delay = 60.0 / self.config.requests_per_minute
            time_since_last = time.time() - self._requests_minute[-1]
            if time_since_last < min_delay:
                spacing_wait = min_delay - time_since_last
                wait_time = max(wait_time, spacing_wait)
        
        # Wait if needed
        if wait_time > 0:
            print(f"⏳ Rate limit approaching, waiting {wait_time:.1f}s...")
            await asyncio.sleep(wait_time + 0.5)  # Add small buffer
    
    def record_request(self, tokens_used: int = 1000) -> None:
        """
        Record a completed request.
        
        Args:
            tokens_used: Number of tokens used in this request
        """
        current_time = time.time()
        self._requests_minute.append(current_time)
        self._requests_day.append(current_time)
        self._tokens_minute.append((current_time, tokens_used))
    
    def get_usage_stats(self) -> Dict[str, Any]:
        """Get current usage statistics."""
        self._clean_old_entries(self._requests_minute, 60)
        self._clean_old_entries(self._requests_day, 86400)
        self._clean_old_token_entries()
        
        return {
            "rpm": len(self._requests_minute),
            "rpm_limit": self.config.requests_per_minute,
            "tpm": self._get_token_count(),
            "tpm_limit": self.config.tokens_per_minute,
            "rpd": len(self._requests_day),
            "rpd_limit": self.config.requests_per_day,
        }


# Default rate limit configurations per provider
DEFAULT_RATE_LIMITS: Dict[str, RateLimitConfig] = {
    "openai": RateLimitConfig(
        requests_per_minute=500,
        tokens_per_minute=200000,
        requests_per_day=10000,
    ),
    "anthropic": RateLimitConfig(
        requests_per_minute=50,
        tokens_per_minute=100000,
        requests_per_day=1000,
    ),
    "google": RateLimitConfig(
        requests_per_minute=2,  # Default to safest limit (Pro Free)
        tokens_per_minute=32000,
        requests_per_day=50,
        max_retries=5,
        initial_retry_delay=5.0,
        max_retry_delay=120.0,
    ),
    "gemini_pro": RateLimitConfig(
        requests_per_minute=2,   # Strict Pro Limit (Free/Preview)
        tokens_per_minute=32000, # Strict TPM
        requests_per_day=50,
        max_retries=5,
        initial_retry_delay=60.0, # Increase initial delay significantly
        max_retry_delay=300.0,
    ),
    "gemini_flash": RateLimitConfig(
        requests_per_minute=15,  # Flash Limit (Free)
        tokens_per_minute=1000000,
        requests_per_day=1500,
        max_retries=5,
        initial_retry_delay=5.0,
        max_retry_delay=120.0,
    ),
    "grok": RateLimitConfig(
        requests_per_minute=60,
        tokens_per_minute=150000,
        requests_per_day=1500,
    ),
}


async def retry_with_exponential_backoff(
    func: Callable,
    config: RateLimitConfig,
    *args,
    **kwargs
):
    """
    Retry an async generator function with exponential backoff.
    
    Args:
        func: Async generator function to retry
        config: Rate limit configuration
        *args: Arguments to pass to func
        **kwargs: Keyword arguments to pass to func
        
    Yields:
        Values from the async generator
        
    Raises:
        Last exception if all retries fail
    """
    last_exception = None
    
    for attempt in range(config.max_retries):
        try:
            # Call the async generator and iterate through its values
            async for chunk in func(*args, **kwargs):
                yield chunk
            # If we successfully completed, break out of the retry loop
            return
        except Exception as e:
            last_exception = e
            error_str = str(e).lower()
            
            # Check if it's a rate limit error
            is_rate_limit = any(term in error_str for term in [
                'rate', 'quota', 'limit', '429', 'too many requests'
            ])
            
            # Don't retry non-rate-limit errors on last attempt
            if not is_rate_limit and attempt == config.max_retries - 1:
                raise
            
            # Calculate backoff delay
            if is_rate_limit:
                # For rate limits, use longer delays
                # Force at least 60s for Gemini 429s, as the limit is 2 RPM (1 per 30s) but often stricter
                delay = max(
                    60.0,
                    min(
                        config.initial_retry_delay * (config.exponential_base ** attempt) * 2,
                        config.max_retry_delay
                    )
                )
            else:
                # For other errors, use shorter delays
                delay = min(
                    config.initial_retry_delay * (config.exponential_base ** attempt),
                    config.max_retry_delay / 2
                )
            
            if attempt < config.max_retries - 1:
                print(f"⚠️  Attempt {attempt + 1} failed: {str(e)}")
                print(f"⏳ Retrying in {delay:.1f}s... ({config.max_retries - attempt - 1} attempts remaining)")
                await asyncio.sleep(delay)
            else:
                print(f"❌ All {config.max_retries} attempts failed")
    
    # Raise the last exception if all retries failed
    if last_exception:
        raise last_exception


class RateLimitManager:
    """Manager for rate limiters across multiple models."""
    
    def __init__(self):
        """Initialize rate limit manager."""
        self._limiters: Dict[str, RateLimiter] = {}
    
    def get_limiter(self, provider: str, model_id: str) -> RateLimiter:
        """
        Get or create rate limiter for a model.
        
        Args:
            provider: Provider name (e.g., 'anthropic', 'google')
            model_id: Model identifier
            
        Returns:
            RateLimiter instance
        """
        key = f"{provider}:{model_id}"
        
        if key not in self._limiters:
            config = DEFAULT_RATE_LIMITS.get(provider, RateLimitConfig())
            self._limiters[key] = RateLimiter(config)
        
        return self._limiters[key]
    
    def get_all_stats(self) -> Dict[str, Dict[str, Any]]:
        """Get usage statistics for all models."""
        return {
            model_key: limiter.get_usage_stats()
            for model_key, limiter in self._limiters.items()
        }
    
    def print_stats(self) -> None:
        """Print usage statistics for all models."""
        stats = self.get_all_stats()
        
        if not stats:
            print("\n📊 No API usage yet")
            return
        
        print("\n📊 API Usage Statistics:")
        print("=" * 80)
        
        for model_key, model_stats in stats.items():
            print(f"\n{model_key}:")
            print(f"  RPM: {model_stats['rpm']}/{model_stats['rpm_limit']} "
                  f"({model_stats['rpm']/model_stats['rpm_limit']*100:.1f}%)")
            print(f"  TPM: {model_stats['tpm']:,}/{model_stats['tpm_limit']:,} "
                  f"({model_stats['tpm']/model_stats['tpm_limit']*100:.1f}%)")
            print(f"  RPD: {model_stats['rpd']}/{model_stats['rpd_limit']} "
                  f"({model_stats['rpd']/model_stats['rpd_limit']*100:.1f}%)")
        
        print("=" * 80)
