# Fix Summary: Global Rate Limits

## Issue
The user reported continued rate limit failures even after model-specific limits were configured. The failures occurred when running multiple Gemini models (3.0 Pro, 2.5 Pro, 2.5 Flash) concurrently.

## Root Cause
1.  **Isolated Rate Limiters**: Each `GoogleProvider` instance created its own `RateLimiter`. When `gemini_3_pro` and `gemini_2_5_pro` ran in parallel, they didn't know about each other's usage.
2.  **Shared Quota**: Google AI Studio "Pro" tier (especially Preview/Free) likely enforces a *Project-level* rate limit (e.g., 2 RPM total) rather than a per-model-name limit. Running two Pro models concurrently immediately doubled the throughput, violating the global limit.

## Fix Implemented
1.  **Shared Rate Limiter Pattern**:
    - Modified `GoogleProvider` to use a class-level registry `_shared_limiters`.
    - All models with "pro" in their name now share a **single** `RateLimiter` instance (2 RPM, 32k TPM).
    - All models with "flash" in their name share a separate "Flash" limiter (15 RPM).
    - This ensures that if `Gemini 3.0 Pro` makes a request, `Gemini 2.5 Pro` sees the usage and waits if necessary.

2.  **Improved Error Handling**:
    - Added specific catching for `google.api_core.exceptions.ResourceExhausted` to ensure it's treated as a retryable rate limit error.
    - Added handling for "blocked" content to distinguish it from rate limits.

## Result
The system now enforces a **global 2 RPM limit** across all concurrent Gemini Pro models, which should eliminate the "Rate limit exceeded" errors caused by parallel execution.
