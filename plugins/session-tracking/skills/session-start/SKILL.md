---
name: session-start
description: Load project context and open a work session in the time-tracking file(s). Use when the user asks to start, begin or open a work session (e.g. "start the session", "débute la session", "on commence"), or runs /session-start.
---

# session-start

Load the project context and open a session row in the time-tracking file(s). Pair with `/session-end`.

## Conventions (shared with session-end)

- **Project root**: `git rev-parse --show-toplevel`, falling back to the current directory. Never use a subfolder.
- **Project name**: the root folder's basename (or the title of `CLAUDE.md` if present).
- **Dev name**: `git config user.name`, then `git config --global user.name`; if both are empty, ask the user.
- **Project tracking file**: `<root>/TIME_TRACKING.md`.
- **Global tracking file** (optional): the path in the `SESSION_GLOBAL_TRACKING` environment variable (check with `printenv SESSION_GLOBAL_TRACKING`). If unset or empty, skip every "global" step silently.
- **Resume folder**: `<root>/resume/`.
- Date and time come from the shell (`date +%F`, `date +%H:%M`), never from memory.

## Steps

1. **Detect project and dev** with the conventions above.

2. **Load context**:
   - Read `docs/PROJECT_SUMMARY.md` if it exists, otherwise `CLAUDE.md`, otherwise `README.md`.
   - Read the most recent file in `resume/` (highest filename), if any.
   - Tell the user the current state in 2–3 sentences.

3. **Open project tracking**: insert a row after the last table row of `TIME_TRACKING.md`. If a `**Total Time Spent: ...**` line closes the file, keep it last.
   ```
   | <YYYY-MM-DD> | <dev> | <HH:MM> | | | <placeholder, filled at session end> |
   ```
   If the file does not exist, create it:
   ```
   # Time Tracking - <project name>

   | Date | Dev | Start Time | End Time | Duration | Session Summary |
   | :--- | :--- | :--- | :--- | :--- | :--- |
   ```

4. **Open global tracking** (only if `SESSION_GLOBAL_TRACKING` is set): same operation on that file, with the row:
   ```
   | <YYYY-MM-DD> | <project name> | <dev> | <HH:MM> | | | <placeholder> |
   ```
   If the file does not exist, create it (and its folder) with:
   ```
   # Time Tracking — All Projects

   | Date | Project | Dev | Start Time | End Time | Duration | Session Summary |
   | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
   ```

5. **Confirm**: context loaded, tracking file(s) updated, ready to work.

If a row for the same dev is already open (no End Time) from a previous day, warn the user instead of adding a second one, and let them decide.
