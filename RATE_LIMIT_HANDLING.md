# Rate Limit Handling in db_filler.py

## How it Works

When the Fitbit API returns a rate limit error (HTTP 429), `db_filler.py` will:

1. **Detect** the rate limit error by checking for:
   - "retry-after" in error message
   - "rate limit" in error message
   - "429" in error message
   - "too many requests" in error message
   - "HTTPTooManyRequests" exception type

2. **Wait** 100 seconds before retrying

3. **Retry** the same date (doesn't move on or skip)

4. **Never marks as null** - rate limit failures don't increment the failure counter, so the date won't be marked as "no-run"

5. **Keeps trying** indefinitely until it succeeds

## Example Output

```
Processing 2025-04-17 (57 days remaining)...
  Waiting 1 second before next request...
  WARNING: Rate limit hit for 2025-04-17: KeyError: 'retry-after'
  Waiting 100 seconds before retry...
Processing 2025-04-17 (57 days remaining)...
  Waiting 1 second before next request...
  Found run for 2025-04-17
  ...
```

## Other Error Handling

- **Timeout errors**: Retry same date, mark as no-run after 2 failures
- **Network errors**: Wait 30 seconds, retry same date
- **Other errors**: Mark as no-run after 2 failures, move to next date

## Important Notes

- Rate limit errors do NOT count toward the 2-failure limit
- The script will keep retrying the same date indefinitely for rate limits
- Only other types of persistent errors will cause a date to be marked as no-run

