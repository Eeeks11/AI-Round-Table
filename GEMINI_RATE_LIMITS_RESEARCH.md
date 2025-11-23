# Gemini Rate Limit Research & Optimization Plan

## Current Status
The system currently encounters rate limit issues with Gemini models ("3.0 pro", "2.5 pro", "2.5 flash").
The existing configuration uses a single set of limits for all Google models:
- **RPM (Requests Per Minute)**: 50
- **TPM (Tokens Per Minute)**: 1,000,000
- **RPD (Requests Per Day)**: 1,000

## Gemini API Rate Limits (Standard Tiers)

Based on standard Google AI Studio limits (proxy for "2.5/3.0" preview behavior):

### Gemini 1.5 Pro (likely baseline for "Pro" models)
| Tier | RPM | TPM | RPD |
|------|-----|-----|-----|
| **Free** | **2** | **32,000** | **50** |
| **Paid** | 360 | 2,000,000 | Unlimited |

### Gemini 1.5 Flash (likely baseline for "Flash" models)
| Tier | RPM | TPM | RPD |
|------|-----|-----|-----|
| **Free** | **15** | **1,000,000** | **1,500** |
| **Paid** | 1,000 | 4,000,000 | Unlimited |

### Preview / Experimental Models
Preview models often have stricter or "Free Tier" equivalent limits regardless of billing status to manage capacity.
- **Typical Preview Limits**: 5-10 RPM, similar TPM to Free tier.

## Analysis of Failure
The current setting of **50 RPM** is significantly higher than the **2 RPM** limit for the Free/Preview tier of Pro models. If the user is utilizing a free key or a preview model with strict limits, the system will send requests 25x faster than allowed, causing immediate `429` errors.

The **TPM limit of 1M** is also unsafe for Pro models on free/preview tiers (limit is 32k). With "long inputs" from deliberation, a single request could easily exceed 32k tokens (approx 128k characters), triggering a rate limit immediately.

## Proposed Solution

### 1. Granular Rate Limit Configuration
We must distinguish between "Pro" and "Flash" models within the Google provider.
- **Pro Models** (`gemini-*-pro`): Use conservative limits (2 RPM, 32K TPM).
- **Flash Models** (`gemini-*-flash`): Use moderate limits (15 RPM, 1M TPM).

### 2. Robust Backoff Strategy
- Increase `max_retries` for Gemini specifically.
- Implement "Smart Wait": If a 429 occurs, parse the "Retry-After" header if available, or default to a much longer wait (e.g., 60s) than the standard backoff.

### 3. Token Management
- The current token estimation (`len/4`) is rough. We will add a safety buffer (multiply by 1.2) to avoid accidental TPM breaches.
- If a request exceeds the TPM limit of the model, we must either:
    a) Fail fast (don't try).
    b) Wait for the *entire* minute window to clear (if the request < TPM limit).

## Implementation Plan
1.  **Modify `RateLimitConfig`**: Add presets for `gemini_pro` and `gemini_flash`.
2.  **Update `RateLimitManager`**: Allow selecting config based on `model_name`, not just `provider`.
3.  **Update `GoogleProvider`**: Dynamically choose the correct rate limiter based on `self.config.model_name`.
4.  **Update `DEFAULT_RATE_LIMITS`**: Set safe defaults.

## specific Configuration for User
Given the user mentions "3.0 pro", "2.5 pro", and "2.5 flash", we will assume these follow standard Pro/Flash tiers.

**New Configs:**
- **Gemini Pro (Any version)**: 2 RPM, 32,000 TPM, 50 RPD.
- **Gemini Flash (Any version)**: 15 RPM, 1,000,000 TPM, 1,500 RPD.

This is a "safe by default" approach. If the user has a paid tier, they can manually increase these in the code, but the default should not crash.
