# Rate Limit Update: Pay-As-You-Go (PAYG)

## Update
The user confirmed they are using a **Pay-As-You-Go** (Paid) account for Google Gemini models.

## Changes
I have updated the rate limit configurations to match the standard Google AI Studio Paid Tier limits:

### Gemini Pro (`gemini_pro`)
- **Old (Free)**: 2 RPM, 32k TPM.
- **New (Paid)**: 360 RPM, 2,000,000 TPM.
- **Retries**: Increased to 10 (for robustness).
- **Delay**: Reset to standard (2s initial) since we don't need the "penalty box" wait of the free tier.

### Gemini Flash (`gemini_flash`)
- **Old (Free)**: 15 RPM, 1M TPM.
- **New (Paid)**: 1,000 RPM, 4,000,000 TPM.

## Note on 429 Errors
If the user *still* encounters `429 Rate limit exceeded` errors with these settings:
1.  **Project Quota**: The Google Cloud Project might have a manual quota cap set in the console (IAM & Admin > Quotas).
2.  **Model Availability**: `gemini-3.0-pro` might be a limited preview model with strict limits *regardless* of billing status.
3.  **Region**: The API key might be bound to a region with limited capacity.

The system will now attempt to send requests at high speed (up to 360 RPM). If the API rejects them, the retry logic (10 attempts) will kick in.
