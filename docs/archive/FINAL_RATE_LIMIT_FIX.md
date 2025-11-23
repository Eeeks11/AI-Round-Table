# Final Fix: Gemini Pro Rate Limit Persistence

## Issue
Despite previous fixes (global limiting), the user continued to see `429 Rate limit exceeded` errors for Gemini 3.0 Pro. The retries were waiting (20s, 40s, 80s) but still failing.

## Analysis
1.  **Retry Delays Were Too Short**: The previous logic used `min(initial * 2^n, max)`. With `initial=10s`, the first retry was 20s. For Gemini Free/Preview tiers, once you hit a 429, you often need to wait a full minute or more for the sliding window to clear completely, especially if multiple requests were queued. A 20s wait might be insufficient if the "penalty box" is 60s.
2.  **Hard Limit**: The Google API often returns `Retry-After` headers or requires a strict 60s cooldown after a violation.

## Fix Implemented
1.  **Aggressive Backoff for Gemini Pro**:
    - Increased `initial_retry_delay` for Gemini Pro from 10s to **60s**.
    - This means the *first* retry will wait 120s (since the logic multiplies by 2: `60 * 2^0 * 2` was the formula, but I simplified it to ensure it's at least 60s).
    - Actually, the formula is `delay = max(60, min(initial * 2^attempt * 2, max_delay))`.
    - Updated code forces a **minimum 60s wait** specifically for rate limit errors.

2.  **Updated `rate_limiter.py`**:
    - Modified `retry_with_exponential_backoff` to enforce `delay = max(60.0, ...)` when `is_rate_limit` is true.
    - This ensures that ANY rate limit error triggers a safe, long pause (1 minute minimum) before trying again, giving the API quota ample time to reset.

## Expected Behavior
- If a 429 occurs (e.g., due to a burst), the system will print `⏳ Retrying in 120.0s...` (or similar >60s value).
- This long pause is annoying but necessary for the strict Gemini Pro Preview limits to ensure the task eventually succeeds rather than failing 5 times quickly.
