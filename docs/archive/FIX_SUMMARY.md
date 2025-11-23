# Fixed: Gemini 3.0 Pro Rate Limit Crash

## Issue
The user encountered `IndexError: deque index out of range` when using Gemini 3.0 Pro.

## Root Cause
The rate limiter logic had two bugs that triggered when using strict rate limits (like Gemini Pro's 2 RPM / 32k TPM) combined with empty usage history:

1.  **TPM Check Bug**: When `estimated_tokens` for a request exceeded 90% of the TPM limit (which is easy with Gemini Pro's low 32k limit), the code attempted to access `self._tokens_minute[0][0]` to calculate wait time. However, if this was the *first* request, `_tokens_minute` was empty, causing the crash.
2.  **RPM Buffer Bug**: For low RPM limits (e.g., 2), the calculated buffer resulted in checking `if requests >= 0` which is always true, causing access to `self._requests_minute[0]` which was empty on the first request.

## Fix
1.  **Safe Deque Access**: Added checks `if self._tokens_minute:` and `if self._requests_minute:` before accessing elements.
2.  **Smart Buffer**: Adjusted RPM buffer logic to disable buffering for low-limit models (RPM <= 10), ensuring we don't trigger wait logic unnecessarily for the first request.
3.  **Behavior**: 
    - If a single request exceeds the TPM limit but history is empty, we now allow it to proceed (fail-fast or succeed) rather than crashing or waiting indefinitely.
    - Gemini Pro requests are now spaced out (1 per ~30s) to ensure compliance with the 2 RPM limit.

## Verification
- Reproduced the `IndexError` with a script.
- Applied fixes.
- Verified with reproduction script (passed).
- Verified general rate limit logic (RPM spacing working correctly).
