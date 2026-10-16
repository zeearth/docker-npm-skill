# conventions-guard

Three [Claude Code](https://claude.com/claude-code) hooks that turn written conventions into checks Claude cannot forget. Both run on every `Write` and `Edit`, and a failure is sent back to Claude so it fixes the code in the same turn.

## What it checks

| Hook | When | Rule |
| :--- | :--- | :--- |
| `secret-guard.py` | before the write | Refuses known credential formats (AWS, GitHub, `sk-`, Slack, Google API keys, private keys) in any file except git-ignored `.env*`. In `docker-compose*.yml`, a `*PASSWORD`, `*SECRET`, `*TOKEN`, `*API_KEY` or `*ENCRYPTION_KEY` variable must be `${VAR}`; in `.env.example` it must be empty. |
| `code-guard.py` | after the write | No `if` / `for` / `while` / `else` without braces in `.ts .tsx .js .jsx .mjs .cjs` (only the lines just written are checked, template literals are skipped). In a project with a `package.json`, a file over 500 lines must be reduced by extracting reusable functions into a shared package. |
| `lang-guard.py` | after the write | Markdown files (`.md`, `.mdx`) must be in English. A stop-word count flags French prose in the text just written (code blocks ignored). To record a file that is French on purpose, put `<!-- lang: fr -->` in its first 5 lines. `.claude/` and `CHANGELOG*` are skipped. |

`node_modules`, `.next`, `dist`, `build`, `coverage`, `*.d.ts` and `.claude/` are ignored.

## Install

```
/plugin marketplace add zeearth/zeearth-skills
/plugin install conventions-guard@zeearth-skills
```

Requires `python3`. Files written through `Bash` (heredocs) are not seen: the hooks watch `Write` and `Edit` only.

## Tuning

The limits live at the top of `hooks/code-guard.py` (`MAX_LINES`, `CODE_EXTENSIONS`, `IGNORED_PARTS`), `hooks/lang-guard.py` (`FRENCH_RATIO`, `MIN_WORDS`) and `hooks/secret-guard.py` (`TOKEN_PATTERNS`, `SECRET_NAME`).

## License

MIT
