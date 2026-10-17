# personas

`/persona <id>` puts Claude in an expert persona for the rest of the conversation, so you stop restating the role each time.

## Bundled personas

| Id | Persona |
| :--- | :--- |
| `cto` | CTO |
| `webdesigner` | Senior Web Designer |
| `fullstack` | Senior Full-Stack Developer |
| `dba` | Database Architect |
| `docs` | Expert Documentation Writer |
| `product-owner` | Expert Product Owner |
| `security` | Expert Security Reviewer |

## Commands

- `/persona webdesigner` activates a persona (natural phrasing such as "en tant que WebDesigner senior" works too).
- `/persona list` shows the personas, which layers define each, and their description.
- `/persona show <id>` prints the merged result without activating it.
- `/persona new <id>` creates a global or project persona (or an override).
- `/persona off` goes back to the default behaviour.

## Layers: complete, do not replace

A persona is resolved from up to three files, lowest priority first:

1. bundled with the plugin (`personas/<id>.md`)
2. global: `~/.claude/personas/<id>.md`
3. project: `<project>/.claude/personas/<id>.md`

Files are split in `## Sections`. When merging:

- a section present in a higher layer **replaces** the same section below;
- a section only present in a higher layer is **added**;
- a heading ending with ` +` (for example `## Priorities +`) **appends** to the lower section instead of replacing it;
- `replace: true` in the front matter makes that file ignore every lower layer.

Example: the project file `.claude/personas/webdesigner.md` only needs

```markdown
## Stack +

- HeroUI v3 and Tailwind 4, theming through CSS variables in `globals.css`.
- Mockups are `.dc.html` artboards; screens must work in light and dark.
```

and the bundled "Senior Web Designer" keeps every other section.

## Default persona per project

Add a line to the project's `CLAUDE.md`, for example: "UI screens: use the `webdesigner` persona." Claude adopts it when the task matches. A persona never overrides CLAUDE.md rules or the answer language.

The merge is done by `skills/persona/resolve.py` (Python 3, no dependency).
