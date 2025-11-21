# Database Schema and Logic

## How `cache.db` Works

### Null Entries Are INTENTIONAL

The `runs` table contains entries with `activity_type = 'None'` for **days with no runs**. This is by design!

**Purpose**: Prevent redundant API calls
- If a date has no runs, we mark it with `activity_type = 'None'`
- Next time db_filler runs, it sees the entry and skips that date
- Saves API calls and respects rate limits

### Entry Types

1. **Run entries**: Have distance, duration, elevation, etc.
   ```
   activity_type = 'Run' or 'Treadmill run'
   distance = [value]
   duration = [value]
   ```

2. **No-run entries**: Days with no activities
   ```
   activity_type = 'None'
   distance = NULL
   duration = NULL
   ```

3. **Incomplete entries**: Should not exist (these are bugs)
   ```
   activity_type = NULL
   distance = NULL
   ```

### How `db_filler.py` Handles Dates

```python
while processing dates:
    if date_is_complete(date):
        skip_date()  # Already processed
    else:
        try:
            activities = fetch_from_fitbit()
            if has_run:
                cache_run()  # Store run data
            else:
                cache_no_run()  # Store activity_type='None'
            move_to_next_date()
        except RateLimitError:
            wait_100_seconds()
            retry_same_date()  # Don't cache anything
        except OtherError:
            if failed_twice:
                cache_no_run()  # Assume no run after 2 failures
            move_to_next_date()
```

### When to Clean Null Entries

**✅ Safe to delete null entries when:**
- Starting fresh reprocessing (clear_runs.py does this)
- You know specific dates had runs but are marked as None
- Recovering from interrupted processing

**❌ Don't delete null entries when:**
- Normal operation (they're supposed to be there!)
- Days genuinely had no activities
- You want to avoid redundant API calls

### Rate Limit Handling

When rate limited:
1. ❌ Does NOT create entry in database
2. ⏱️ Waits 100 seconds
3. 🔄 Retries same date
4. ✅ Only caches after successful API response

This prevents incomplete entries from rate limit errors.

