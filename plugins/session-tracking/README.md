# session-tracking

Two manual skills for freelance-style work sessions.

- `/session-start` loads the project context (`docs/PROJECT_SUMMARY.md`, `CLAUDE.md` or `README.md`, plus the latest `resume/` file) and opens a row in `TIME_TRACKING.md`.
- `/session-end [summary]` writes `resume/session_NN_YYYYMMDD_HHMM.md`, updates `docs/PROJECT_SUMMARY.md` if it exists, and closes the row (end time, duration, summary, running total).

## Optional global tracking

To also log every project in a single file, set `SESSION_GLOBAL_TRACKING` to the path of that file. If the variable is unset or empty, only the per-project file is used.

Use an **absolute path** in both options below. `settings.json` does not expand `$HOME` or `~`, so the skill would receive the literal text.

### Option 1: shell profile

```bash
export SESSION_GLOBAL_TRACKING="$HOME/projects/TIME_TRACKING.md"
```

Add it to `~/.bashrc` (or `~/.zshrc`). Claude Code inherits it only if it is started from a shell that read this file, so restart your terminal, and in VS Code reload the window or quit VS Code completely.

### Option 2: Claude Code `settings.json` (recommended)

In `~/.claude/settings.json`:

```json
{
  "env": {
    "SESSION_GLOBAL_TRACKING": "/home/<you>/projects/TIME_TRACKING.md"
  }
}
```

This does not depend on how Claude Code is launched (terminal, IDE extension, desktop). Restart Claude Code after editing it. To limit it to one project, put the same `env` block in that project's `.claude/settings.json` instead.

### Check

Ask Claude for the value, or run `printenv SESSION_GLOBAL_TRACKING` in a Claude Code shell: it must print the absolute path.

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
