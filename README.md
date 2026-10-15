# zeearth-skills

A [Claude Code](https://claude.com/claude-code) plugin marketplace with small, focused plugins for day-to-day development workflows.

## Install

```
/plugin marketplace add zeearth/zeearth-skills
/plugin install <plugin>@zeearth-skills
```

## Plugins

| Plugin | What it does |
| :--- | :--- |
| [docker-npm](plugins/docker-npm) | Install, update, remove, list and audit npm packages inside your project's Docker container, never on the host. |
| [session-tracking](plugins/session-tracking) | `/session-start` and `/session-end`: load project context, write a per-session resume, and keep time-tracking tables up to date. |
| [conventions-guard](plugins/conventions-guard) | Hooks that check every write: braces on control statements, 500-line limit on Node/TS files, no secrets in committed files. |

## License

MIT
