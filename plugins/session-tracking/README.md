# session-tracking

Two manual skills for freelance-style work sessions.

- `/session-start` loads the project context (`docs/PROJECT_SUMMARY.md`, `CLAUDE.md` or `README.md`, plus the latest `resume/` file) and opens a row in `TIME_TRACKING.md`.
- `/session-end [summary]` writes `resume/session_NN_YYYYMMDD_HHMM.md`, updates `docs/PROJECT_SUMMARY.md` if it exists, and closes the row (end time, duration, summary, running total).

## Optional global tracking

To also log every project in a single file, set the path in your shell profile:

```bash
export SESSION_GLOBAL_TRACKING="$HOME/projects/TIME_TRACKING.md"
```

If the variable is unset, only the per-project file is used.

## Files it creates

| Path | Content |
| :--- | :--- |
| `<repo>/TIME_TRACKING.md` | one row per session, with a total line |
| `<repo>/resume/session_NN_*.md` | one summary per session |

## Install

```
/plugin marketplace add zeearth/zeearth-skills
/plugin install session-tracking@zeearth-skills
```

## License

MIT
