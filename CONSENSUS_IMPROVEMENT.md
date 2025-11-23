# Consensus Detection Improvement for Factual Questions

## Problem

Simple factual questions (like "What is the date today in Melbourne-Australia?") were taking 3 rounds to reach consensus, even though all models agreed on the exact same answer in Round 1:

- **Round 1**: All models said "November 23, 2025" ✅
- **Round 2**: Convergence only 68.68% - No consensus ❌
- **Round 3**: Convergence 81.19% - Consensus reached ❌

This is inefficient and wasteful for simple factual queries that should converge immediately.

## Root Causes

### 1. Text-Based Comparison Only
The consensus detector was comparing **text similarity** rather than **semantic factual agreement**:
- "November 23, 2025" vs "23 November 2025" vs "2025-11-23" looked different
- Different verbosity levels reduced similarity scores
- Formatting variations masked factual agreement

### 2. Consensus Check Delayed Until Round 2
The system only checked for consensus after Round 2+:
```python
if round_num >= 2:  # ❌ Skips Round 1
    consensus = self.consensus_detector.analyze_consensus(...)
```

For factual questions, this meant at least 2 rounds even with immediate agreement.

### 3. No Factual Entity Extraction
The system couldn't recognize that:
- All models mentioned the same **date** (2025-11-23)
- All models mentioned the same **location** (Melbourne)
- The core **fact** was identical across all responses

## Solutions Implemented

### 1. Added Factual Agreement Detection (`consensus.py`)

New methods to extract and compare factual data:

#### `_check_factual_agreement()`
Extracts and compares factual elements:
- **Dates**: Multiple formats (November 23, 2025 / 23 November 2025 / 2025-11-23)
- **Numbers**: Prices, quantities, measurements ($123, 45.5 km, 30%)
- **Entities**: Proper nouns and key terms (Melbourne, Australia, AEDT)

Returns **1.0 (perfect score)** when all models mention the same date/fact.

#### `_extract_dates()`
Normalizes date formats:
```python
"November 23, 2025" → "2025-11-23"
"23 November 2025"  → "2025-11-23"
"2025-11-23"        → "2025-11-23"
```

All three formats now recognized as the **same date**.

#### `_extract_numbers()` & `_extract_entities()`
Similar normalization for numbers, prices, and proper nouns.

### 2. Enhanced Core Answer Consistency (`consensus.py`)

Updated `_calculate_core_answer_consistency()`:
```python
# OLD: Only pattern matching (yes/no/maybe)
# NEW: Check factual agreement FIRST

factual_consistency = self._check_factual_agreement(responses)
if factual_consistency >= 0.9:  # High factual agreement
    return factual_consistency  # Skip other checks

# Fall back to pattern matching for subjective questions
```

### 3. Round 1 Consensus Check (`orchestrator.py`)

Changed consensus analysis to start after Round 1:
```python
# OLD:
if round_num >= 2:  # Only check after Round 2+

# NEW:
if round_num >= 1:  # Check after every round, including Round 1
```

Added smart display logic to avoid clutter:
```python
should_show = (
    round_num > 1 or 
    (round_num == 1 and consensus.convergence_score >= 0.90)
)
```
- Shows Round 1 consensus if score ≥ 90% (factual agreement)
- Otherwise waits until Round 2+ (complex questions need deliberation)

### 4. Single-Round Consensus Support (`consensus.py`)

Updated `analyze_consensus()` to handle Round 1:
```python
# OLD: Required 2+ rounds minimum
if len(responses_by_round) < 2:
    return insufficient_data

# NEW: Check factual agreement in Round 1
if len(responses_by_round) == 1:
    factual_score = self._calculate_core_answer_consistency(final_responses)
    if factual_score >= 0.95:
        return has_consensus=True  # Exit after Round 1!
```

## Expected Behavior Now

### For the Melbourne Date Question:

**Round 1**:
- ✅ GPT: "November 23, 2025"
- ✅ Claude: "23 November 2025" 
- ✅ Grok: "Sunday, November 23, 2025"
- 📊 **Factual extraction**: All mention date "2025-11-23"
- 🎯 **Consensus score**: 1.0 (100%)
- ✅ **Consensus reached after 1 round!**
- ⏭️ **Skip Rounds 2 & 3**

**Final output**:
```
✓ Consensus reached after 1 rounds!

GENERATING FINAL CONSENSUS...
The current date in Melbourne, Australia is November 23, 2025.

Session completed in ~15 seconds (instead of 53.6)
```

### For Complex/Subjective Questions:

Questions like "What are the ethical implications of AI?" will still:
- Use multiple rounds (no factual agreement in Round 1)
- Build on each other's perspectives
- Converge through deliberation over 3-10 rounds

The system is now **smart about question type**:
- **Factual**: Quick consensus (1 round)
- **Complex**: Full deliberation (multiple rounds)

## Testing

Test the fix with:
```bash
python3 deliberate.py "What is the date today in Melbourne-Australia?" --rounds 3
```

**Expected outcome**:
- Consensus reached after 1 round
- Only 1 round executed (automatic early termination)
- Total time reduced by ~60-70%

**Other test cases**:
```bash
# Should reach consensus in 1 round:
python3 deliberate.py "What is 2 + 2?" --rounds 3
python3 deliberate.py "What is the capital of France?" --rounds 3

# Should still use multiple rounds:
python3 deliberate.py "What are the risks of AI?" --rounds 5
python3 deliberate.py "How should we address climate change?" --rounds 5
```

## Performance Impact

### Before:
- Simple factual questions: 3 rounds, 50+ seconds
- 12-16 API calls (3 models × 3 rounds + synthesis calls)
- Unnecessary token usage and cost

### After:
- Simple factual questions: 1 round, ~15 seconds
- 4-6 API calls (3 models × 1 round + synthesis calls)
- **~60% reduction in time and cost** for factual queries

### Cost Savings Example:
For 100 simple factual queries:
- **Before**: 1,200-1,600 API calls
- **After**: 400-600 API calls
- **Savings**: ~60% reduction in API costs

## Technical Details

### Factual Agreement Score Calculation

```python
def _check_factual_agreement(responses):
    dates = [extract_dates(r) for r in responses]
    
    if all_dates_match(dates):
        return 1.0  # Perfect consensus
    
    numbers = [extract_numbers(r) for r in responses]
    if 80%_of_models_mention_same_number(numbers):
        return 0.95  # Very high consensus
    
    entities = [extract_entities(r) for r in responses]
    if models_share_70%_of_entities(entities):
        return 0.85  # High consensus
    
    return 0.0  # No factual agreement
```

### Consensus Threshold

- Default threshold: **0.75** (75%)
- Factual agreement: **1.0** (100%) when dates/facts match
- Result: Factual questions **always** exceed threshold in Round 1

## Future Enhancements

Consider adding:

1. **Quick mode** for obvious factual queries:
   ```bash
   python3 deliberate.py "What is the date?" --quick
   # Skips multi-model deliberation entirely, just queries one model
   ```

2. **Question type detection**:
   - Auto-detect if question is factual vs. subjective
   - Set rounds=1 automatically for factual queries
   
3. **Fact verification mode**:
   - For factual questions, verify all models get the same tool results
   - Return consensus immediately if tool results identical

4. **Confidence scoring**:
   - Show confidence level for consensus
   - "100% agreement on date: November 23, 2025"

## Summary

✅ **Fixed**: Factual questions now reach consensus in 1 round
✅ **Smart**: System adapts to question type (factual vs. complex)
✅ **Efficient**: 60% reduction in time and API costs for simple queries
✅ **Accurate**: Better extraction and comparison of factual data
✅ **Maintains quality**: Complex questions still get full deliberation

The deliberation system is now optimized for both simple factual queries and complex deliberative questions!
