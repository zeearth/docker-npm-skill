---
name: persona
description: Put Claude in an expert persona (cto, webdesigner, fullstack, dba, docs, product-owner, security) for the rest of the conversation. Use when the user runs /persona, names a persona ("en tant que WebDesigner senior", "as a security reviewer", "mets-toi en CTO"), or asks to list, create or switch personas.
argument-hint: <persona-id> | list | show <id> | new <id> | off
---

# persona

Personas are Markdown files merged from three layers (lowest to highest priority): bundled with this plugin, global (`~/.claude/personas/<id>.md`), project (`.claude/personas/<id>.md`). A higher layer completes the lower ones: sections with the same heading are replaced, new sections are added, a heading ending with ` +` appends to the lower section, and `replace: true` in the front matter drops every lower layer.

The resolver is `${CLAUDE_SKILL_DIR}/resolve.py` (if that variable was not substituted, find it with `find ~/.claude/plugins -name resolve.py -path '*personas*'`). Always run it from the project root so the project layer is found. Never merge the files by hand.

## Commands

- **`<id>`** (or a natural request such as "en tant que WebDesigner senior"): run `python3 <resolver> show <id>`, read the merged persona and adopt it for the rest of the conversation. Match the id loosely against `list` when the user's wording differs ("WebDesigner Senior" is `webdesigner`, "Relecteur sécurité" is `security`). Answer in one short line naming the persona and its layers (for example "WebDesigner senior (global + projet)"), then carry on with the user's request if there was one.
- **`list`**: run `python3 <resolver> list` and show id, layers and description as a table.
- **`show <id>`**: print the merged persona without adopting it.
- **`off`**: drop the persona and go back to the default behaviour.
- **`new <id>`**: ask which scope (global or project) and what the persona should add or change. Get the target path with `python3 <resolver> path <id> <scope>`. For a project override of an existing persona, write ONLY the sections that differ (front matter `name` and `description` are optional); for a brand new persona write the full set of sections. Show the file written.

Only one persona is active at a time; switching replaces the previous one. A persona changes the point of view, priorities and deliverables, never the user's rules (CLAUDE.md, conventions, permissions) and never the answer language: reply in the language the user writes in. If several personas are asked at once, pick the first and say so.

A project can name a default persona in its CLAUDE.md (for example "UI screens: use the webdesigner persona"). When the task clearly matches such a line and no persona is active, adopt it and say so in one line.
