# Rate Limiting Guide

This document explains the rate limiting and retry mechanisms implemented in the multi-model deliberation system.

## Overview

The system now includes comprehensive rate limiting to prevent API errors and ensure smooth operation within provider limits.

## Features

### 1. Automatic Rate Limit Tracking

The system tracks three key metrics for each model:
- **RPM (Requests Per Minute)**: Number of API calls per minute
- **TPM (Tokens Per Minute)**: Estimated tokens used per minute
- **RPD (Requests Per Day)**: Total API calls per day

### 2. Proactive Rate Limit Prevention

Before making an API call, the system checks if limits would be exceeded:
- If approaching limits, it automatically waits the required time
- Prevents rate limit errors before they occur
- Shows clear messages when waiting: `⏳ Rate limit approaching, waiting X.Xs...`

### 3. Exponential Backoff Retry

When errors occur, the system retries with intelligent backoff:
- **Max Retries**: 3 attempts by default
- **Initial Delay**: 2 seconds
- **Max Delay**: 60 seconds
- **Exponential Growth**: Delay doubles with each attempt
- **Special Handling**: Rate limit errors get longer delays

### 4. Usage Statistics

At the end of each session, view your API usage:
```
📊 API Usage Statistics:
────────────────────────────────────────────────────────────────────────────────

Claude Sonnet 4.5:
  RPM: 3/50 (6.0%)
  TPM: 4,200/100,000 (4.2%)
  RPD: 3/1000 (0.3%)

Gemini 3 Pro:
  RPM: 2/50 (4.0%)
  TPM: 3,800/1,000,000 (0.4%)
  RPD: 2/1000 (0.2%)
────────────────────────────────────────────────────────────────────────────────
```

## Default Rate Limits

Based on typical API limits:

### Claude (Anthropic)
- **RPM**: 50 requests per minute
- **TPM**: 100,000 tokens per minute
- **RPD**: 1,000 requests per day

### Gemini (Google)
- **RPM**: 50 requests per minute
- **TPM**: 1,000,000 tokens per minute
- **RPD**: 1,000 requests per day

### GPT (OpenAI)
- **RPM**: 500 requests per minute
- **TPM**: 200,000 tokens per minute
- **RPD**: 10,000 requests per day

### Grok (X.AI)
- **RPM**: 60 requests per minute
- **TPM**: 150,000 tokens per minute
- **RPD**: 1,500 requests per day

## How It Works

### Before Each Request

```python
# 1. Estimate tokens needed
estimated_tokens = (len(prompt) + len(system_message)) // 4 + max_tokens

# 2. Check rate limits
await rate_limiter.wait_if_needed(estimated_tokens)

# 3. Make request with retry logic
async for chunk in retry_with_exponential_backoff(make_request, config):
    yield chunk

# 4. Record successful request
rate_limiter.record_request(estimated_tokens)
```

### When Rate Limit Hit

1. **First Attempt Fails**: Wait 2 seconds, retry
2. **Second Attempt Fails**: Wait 4 seconds, retry
3. **Third Attempt Fails**: Wait 8 seconds, retry
4. **All Attempts Fail**: Raise error to user

For rate limit errors specifically, delays are doubled (4s, 8s, 16s).

## Customizing Rate Limits

### Method 1: Modify Default Limits

Edit `rate_limiter.py`:

```python
DEFAULT_RATE_LIMITS: Dict[str, RateLimitConfig] = {
    "google": RateLimitConfig(
        requests_per_minute=100,  # Increase if you have higher limits
        tokens_per_minute=2000000,
        requests_per_day=5000,
    ),
}
```

### Method 2: Per-Model Configuration

```python
from rate_limiter import RateLimitConfig

# Create custom config
custom_config = RateLimitConfig(
    requests_per_minute=100,
    tokens_per_minute=500000,
    requests_per_day=2000,
    max_retries=5,
    initial_retry_delay=1.0,
    max_retry_delay=30.0
)
```

## Best Practices

### 1. Monitor Usage

- Watch the usage statistics after each session
- If consistently hitting limits, consider:
  - Reducing `--rounds` 
  - Using fewer models with `--models`
  - Adding delays between sessions

### 2. Handle High Volume

For many deliberations:
```bash
# Use specific models to conserve daily limits
python deliberate.py "Question" --models gpt4 claude

# Reduce rounds
python deliberate.py "Question" --rounds 2

# Summary only mode (less token usage)
python deliberate.py "Question" --summary-only
```

### 3. Avoid Hitting Daily Limits

- Each 3-round session with 3 models uses ~9 requests
- With 1000 RPD limit, you can run ~110 sessions per day
- Plan accordingly for batch processing

### 4. Token Estimation

The system uses a rough estimate (4 chars = 1 token). This is conservative but may overestimate for:
- Simple English text (actually ~3.5 chars/token)
- Code with lots of whitespace

And underestimate for:
- Complex Unicode
- Special characters

## Error Messages

### Rate Limit Approaching
```
⏳ Rate limit approaching, waiting 5.2s...
```
**Meaning**: System is proactively waiting to avoid hitting limits.
**Action**: None needed, automatic handling.

### Retry Messages
```
⚠️  Attempt 1 failed: Rate limit exceeded
⏳ Retrying in 4.0s... (2 attempts remaining)
```
**Meaning**: Request failed, automatically retrying.
**Action**: Wait for automatic retry.

### Daily Limit Exceeded
```
❌ Daily rate limit exceeded. Reset in 8.5 hours
```
**Meaning**: Hit daily request limit.
**Action**: Wait for reset or use different model.

## Troubleshooting

### Still Getting Rate Limit Errors

1. **Check Your Actual Limits**: API limits vary by account tier
   - Visit your provider's dashboard
   - Update limits in `rate_limiter.py`

2. **Concurrent Requests**: System makes parallel requests per round
   - 3 models = 3 simultaneous requests
   - May need to reduce parallelism for very low limits

3. **Other Applications**: If using same API key elsewhere
   - Rate limits are shared across all applications
   - Consider separate API keys

### Slow Performance

If you see many wait messages:
- You're near your rate limits
- Consider upgrading your API tier
- Or reduce request frequency

## Implementation Details

### Token Estimation

```python
# Input: prompt + system message + expected output
estimated_tokens = (len(prompt) + len(system_message or "")) // 4 + max_tokens
```

### Time Windows

- **Minute Window**: Rolling 60-second window
- **Daily Window**: Rolling 24-hour window
- **Cleanup**: Old entries removed automatically

### Thread Safety

Each provider has its own rate limiter instance, safe for concurrent use within the same session.

## Future Enhancements

Potential improvements (not yet implemented):

- [ ] Token counting using actual tokenizer
- [ ] Adaptive rate limiting based on API responses
- [ ] Shared rate limiters across multiple processes
- [ ] Priority queuing for important requests
- [ ] Rate limit prediction and warnings

---

Last Updated: 2025-11-21
