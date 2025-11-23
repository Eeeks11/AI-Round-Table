# Final System Update: Increased Capacity

## Changes Implemented

### 1. Fixed Truncated Responses (Max Tokens)
- The default `max_tokens` limit was too low (`2000`), causing long deliberations to be cut off.
- **Updated Value**: `8192` tokens (~32,000 chars).
- This change was applied to:
    - `config.py` (Default `ModelConfig` and `DeliberationConfig`)
    - `deliberate.py` (CLI default)
    - `models.json` (All preset models)

### 2. Increased Deliberation Rounds
- **Default Rounds**: Increased from `3` to `10`.
- **Max Rounds**: Increased cap from `10` to `20`.
- This allows for deeper, more extensive debate cycles before forced consensus.

### 3. Rate Limits (Recap)
- **Gemini Pro**: 360 RPM (PAYG Tier)
- **Gemini Flash**: 1000 RPM (PAYG Tier)
- **Global Safety**: Strict shared limiters prevent concurrent models from violating project quotas.
- **Recovery**: 10 retries with exponential backoff (minimum 60s wait on 429) ensures resilience.

## Verification
- You can now run deep deliberations without cutoffs.
- Example: `python deliberate.py "Complex topic" --rounds 15` works correctly.
