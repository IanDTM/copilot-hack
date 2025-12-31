# Backlog Issue: Improve Log Message String Formatting for Clarity

## Description
The log message for whack success in `whack-a-mole/backend/app.py` (lines 518-519) uses string continuation where the space separator appears at the beginning of the second string, making it less obvious that proper spacing exists.

## Current Code
```python
print(
    f"[Thread-{thread_name}] Whack success!"
    f" Hole {hole}, Time: {result['reaction_time']:.3f}s"
)
```

## Suggested Improvement
Move the space to the end of the first string for better clarity:
```python
print(
    f"[Thread-{thread_name}] Whack success! "
    f"Hole {hole}, Time: {result['reaction_time']:.3f}s"
)
```

## Location
- **File**: `whack-a-mole/backend/app.py`
- **Lines**: 518-519
- **Commit Reference**: 2f38f6fac1f58668cbb86df2875738737df2725e

## Priority
Low - This is a code style/readability improvement. The current code functions correctly and produces the expected output with proper spacing.

## Labels
- `good first issue`
- `code-quality`
- `python`

## Origin
This issue was identified during code review on PR #4:
https://github.com/IanDTM/copilot-hack/pull/4#discussion_r2655765837
