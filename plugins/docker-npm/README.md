# docker-npm

A [Claude Code](https://claude.com/claude-code) skill that installs, updates, removes, lists and audits npm packages **inside your project's Docker container**, never on the host.

## Why

When Node runs in Docker, running `npm install` on the host builds `node_modules` for the wrong OS, architecture or Node version. This skill:

- runs the package manager (pnpm, npm, yarn or bun, detected from `packageManager` or the lockfile) in the right compose service;
- keeps the host `node_modules` in sync (bind mount check, or a `tar` pipe plus `rsync` when the container has its own copy) so the IDE resolves types with no TypeScript alerts;
- checks the package name before installing (typosquatting), flags ignored build scripts, and runs the project's typecheck afterwards;
- never uses `sudo` or `--force` silently, never deletes `node_modules` or the lockfile on its own, and never prints `.env` or `.npmrc` secrets.

## Requirements

- Docker with Compose, and a Node project that runs in a container.
- Claude Code.

## Install

As a plain skill (global):

```bash
git clone https://github.com/zeearth/claude-skills.git
mkdir -p ~/.claude/skills
cp -r claude-skills/plugins/docker-npm/skills/docker-npm ~/.claude/skills/
```

For a single project, copy `plugins/docker-npm/skills/docker-npm` to `<project>/.claude/skills/` instead.

As a plugin: `/plugin marketplace add zeearth/claude-skills`, then `/plugin install docker-npm@claude-skills`.

## Usage

```
/docker-npm install zod
/docker-npm install vitest --dev --target tools --workspace @acme/web
/docker-npm update --target tools
/docker-npm remove left-pad
/docker-npm outdated
/docker-npm audit
```

Claude also triggers it from plain requests such as "add zod to the web app".

| Option | Meaning |
| :--- | :--- |
| `--target` | compose service or container name (detected if omitted) |
| `--workspace` | workspace of a monorepo |
| `--dev`, `--exact`, `--peer`, `--optional` | dependency kind and pinning |

Actions: `install`, `update`, `remove`, `list`, `outdated`, `audit`, `sync`.

## Limits

- Native binaries copied to the host only run if the host has the same OS and architecture as the container (true for Linux and WSL). Otherwise you still get the types.
- Interactive commands are avoided on purpose.

## License

MIT
