# Instructions for Claude Code

- For large files, use grep to search for specific content instead of reading entire files
- Use offset and limit parameters when reading large files
- Ask me what specific part of a file you need before reading it
```

**Option 2: Tell Claude Code to be more selective**

When working with Claude Code, you can say things like:
- "Search for the function `xyz` in that file instead of reading the whole thing"
- "Read lines 100-200 of that file"
- "Grep for 'database connection' in the large files"

**Option 3: Use the /compact command**

If Claude Code's context gets too full, type:
```
/compact