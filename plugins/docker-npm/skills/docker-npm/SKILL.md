---
name: docker-npm
description: Install, update, remove, list or audit npm packages inside the Docker container of a project (never on the host), on any project. Takes the target docker service/container, the package(s) and the options (workspace, dev, exact...). Use when the user asks to add/install/update/upgrade/remove/uninstall a package, dependency or lib in a dockerized Node project, or says "npm/pnpm/yarn/bun install in docker".
argument-hint: <install|update|remove|list|outdated|audit> [packages...] [--target <service|container>] [--workspace <name>] [--dev] [--exact] [--peer] [--optional]
---

# docker-npm

Run package-manager operations **inside the project's Docker container**, so that `node_modules` is built for the container's OS/arch/Node version and, through the bind mount, mirrored on the host (VS Code then resolves types with no TS alerts). Never run `npm`/`pnpm`/`yarn`/`bun` on the host.

## Inputs

Parse `$ARGUMENTS`; ask the user (AskUserQuestion) only for what is missing and cannot be detected.

| Input | Meaning | Default |
| :--- | :--- | :--- |
| action | `install` (add), `update`, `remove`, `list`, `outdated`, `audit`, `sync` (install from lockfile) | required |
| packages | one or more names, optional `@version` / `@tag` | required for install/remove; none = all for update |
| `--target` | compose service name, or a plain container name | detected (step 2) |
| `--workspace` / `-F` | workspace/package of a monorepo | root, or ask if several workspaces and the package clearly belongs to one |
| `--dev` / `--exact` / `--peer` / `--optional` | dependency kind and pinning | prod dependency, caret range |

Extra flags the user gives are passed through to the package manager after checking they exist for it.

## Procedure

1. **Validate package specs.** Each must match `^(@[a-z0-9._~-]+/)?[a-z0-9._~-]+(@[A-Za-z0-9._^~<>=*|-]+)?$`. Refuse anything else (no shell metacharacters, URLs or git specs unless the user explicitly asked for one and confirms). Pass each spec as a separate argument; never build the command through string interpolation of untrusted text.
2. **Detect the project setup** (read-only):
   - Compose file: `docker-compose.y*ml` / `compose.y*ml`; list services with `docker compose --profile '*' config --services` (without it, services under a `profiles:` entry such as a `tools` toolbox are hidden).
   - Package manager: from `packageManager` in `package.json`, else the lockfile (`pnpm-lock.yaml`, `package-lock.json`, `yarn.lock`, `bun.lock`). Check it is available in the container (`<pm> -v`); if not, report it instead of falling back to another manager.
   - Target, in order: explicit `--target`; a one-shot toolbox service (`tools`, `toolbox`, `cli`, `node`); the service whose command runs the app that owns the package; else ask. If the project has no compose file, use a container name (`docker ps`).
   - Bind mount: check whether the repo root (or the workspace dir) is bind-mounted into the target (`docker compose config` volumes) and whether `node_modules` is shadowed by a named/anonymous volume. Record the result as `MIRRORED` (bind mount, nothing to copy) or `ISOLATED` (baked in the image or in a volume): step 6 depends on it.
   - Working dir inside the container, and that the container user is the host UID/GID (`id -u`). If it runs as root, add `--user "$(id -u):$(id -g)"` so no root-owned files appear on the host.
3. **Build the command.** One-shot service: `docker compose run --rm --no-deps [--user ...] <service> <pm> <subcommand> ...`. Running container without a one-shot service: `docker compose exec -T <service> ...` (or `docker exec` for a bare container). Always non-interactive.

   | action | pnpm | npm | yarn (berry) | bun |
   | :--- | :--- | :--- | :--- | :--- |
   | install | `add [-D] [-E] [-F ws] pkg` | `install [-D] [-E] [-w ws] pkg` | `add [-D] [-E] pkg` (`workspace ws add`) | `add [-d] [-E] pkg` |
   | update | `update [-F ws] [pkg] [--latest]` | `update [pkg]` | `up [pkg]` | `update [pkg]` |
   | remove | `remove [-F ws] pkg` | `uninstall [-w ws] pkg` | `remove pkg` | `remove pkg` |
   | outdated | `outdated -r` | `outdated` | `upgrade-interactive` is interactive: use `npm outdated` | `outdated` |
   | audit | `audit` | `audit` | `npm audit` | `audit` |
   | sync | `install --frozen-lockfile` | `ci` | `install --immutable` | `install --frozen-lockfile` |

   Workspace packages of the same monorepo are added as `name@workspace:*` (pnpm/yarn) or by workspace protocol of the manager in use.
4. **Before installing a new package**: show `<pm> view <pkg> name version description` (or `npm view`) from the container and check the name matches the user's intent (typosquatting). `--latest`/major updates: list the majors and ask before applying.
5. **Run it**, then verify:
   - the command exit code and any peer-dependency warnings or ignored build scripts (pnpm 10: `pnpm ignored-builds`; only add a package to `onlyBuiltDependencies` if the user agrees, since build scripts execute code);
   - `git diff --stat` on `package.json` and the lockfile shows only the expected changes;
   - ownership of new files on the host (`ls -ld node_modules`), fix the setup if root-owned;
   - types for untyped packages: if the package has no bundled types, propose `@types/<pkg>` as `--dev`.
6. **Sync the host `node_modules`** so the IDE (VS Code) resolves types and shows no TS alerts. Mandatory after install, update, remove and sync.
   - `MIRRORED`: nothing to copy, only verify that the new package exists under the host `node_modules` (or the workspace one) and is owned by the host user.
   - `ISOLATED`: stream the folders out of the container, preserving symlinks (pnpm relies on them), into a temporary directory next to the project, never straight over the existing one:
     `docker compose run --rm --no-deps -T <service> tar -C <workdir> -cf - node_modules <workspace>/node_modules ... | tar -C <tmpdir> -xf -`
     (include the root `node_modules` and the `node_modules` of every workspace that exists in the container; extraction runs as the host user so ownership is correct). Then mirror it onto the host with deletions, so removed packages disappear: `rsync -a --delete <tmpdir>/node_modules/ node_modules/` for each folder. If `rsync` is missing on the host, run rsync from a throwaway container with both directories mounted, or ask the user before replacing the old folder; never `rm -rf` it on your own. Remove the temporary directory once done (it is Claude's own scratch copy; leave the removal to the user if the permission system flags it).
   - Platform caveat: copied native binaries only run on the host if it has the same OS/arch as the container (true for Linux/WSL). On another host the copy still provides types; say so.
   - If the container user is root, the extracted tree would be root-owned only when using `docker cp`; prefer the `tar` pipe above, or `docker cp` followed by an ownership check.
   - Confirm afterwards: the package directory exists on the host, and (TypeScript projects) that the host-side typecheck target of the IDE would resolve it, e.g. `ls node_modules/<pkg>` or `ls <workspace>/node_modules/<pkg>`.
7. **Run the project's typecheck** if a script exists (`typecheck`, `tsc --noEmit`), also inside the container, and report errors introduced by the change.
8. **Apply the change to the running app**: if the target service has the repo bind-mounted, a dev watcher usually picks it up; if the service image bakes dependencies (no bind mount), rebuild it (`docker compose build <service>`) and recreate it. Mention which one was needed. Remember that services under a compose `profiles:` entry are not rebuilt by a plain `docker compose build`.
9. **Report** in a few lines: action, packages with the resolved versions, workspace, target, what changed in `package.json`/lockfile, typecheck result, and anything left to do. Do not commit unless asked.

## Rules

- Never run the package manager on the host, never use `sudo`, never `--force`/`--legacy-peer-deps` without telling the user why.
- Never delete `node_modules`, the lockfile or the pnpm store to "fix" something without the user's approval; a removal flagged by the permission system is left to the user.
- Do not edit `package.json` dependencies by hand: go through the package manager so the lockfile stays consistent.
- If a command fails, show the relevant output and diagnose (wrong target, missing network, Node/engine mismatch, peer conflict) instead of retrying blindly.
- Secrets: never print `.env` contents or registry auth tokens (`.npmrc`); if a private registry is needed, pass the token through an env var from the git-ignored `.env`.
