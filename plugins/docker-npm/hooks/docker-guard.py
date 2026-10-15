#!/usr/bin/env python3
"""PreToolUse (Bash): refuse to add/remove/update packages on the host in a dockerized project.

A project counts as dockerized when a compose file exists in the working directory or a parent.
Only package-changing commands are blocked (install, add, remove, update, ci...); running scripts
(`pnpm test`, `npm run build`) and global installs (-g) are left alone.
Bypass for a one-off: prefix the command with DOCKER_NPM_ALLOW_HOST=1.

Exit code 2 blocks the call and sends stderr back to Claude.
"""
import json
import os
import re
import sys

MANAGERS = {"npm", "pnpm", "yarn", "bun"}
MUTATING = {
    "install", "i", "add", "remove", "rm", "uninstall", "un", "update", "upgrade", "up",
    "ci", "dedupe", "prune", "link", "unlink",
}
COMPOSE_FILE = re.compile(r"^(docker-)?compose(\..+)?\.ya?ml$")
SEGMENT_SPLIT = re.compile(r"&&|\|\||;|\||\n")
ENV_ASSIGNMENT = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*=")


def find_compose_file(start):
    current = os.path.abspath(start or os.getcwd())
    while True:
        try:
            for name in sorted(os.listdir(current)):
                if COMPOSE_FILE.match(name):
                    return os.path.join(current, name)
        except OSError:
            return None
        parent = os.path.dirname(current)
        if parent == current:
            return None
        current = parent


def is_host_package_change(segment):
    tokens = segment.split()
    while tokens and (ENV_ASSIGNMENT.match(tokens[0]) or tokens[0] == "sudo"):
        tokens = tokens[1:]
    if not tokens or tokens[0] not in MANAGERS:
        return False
    arguments = tokens[1:]
    if "-g" in arguments or "--global" in arguments:
        return False
    # `yarn` alone installs; otherwise the sub-command is one of the first few words
    # (flags such as -F <workspace> or --filter <name> may come before it)
    if tokens[0] == "yarn" and not arguments:
        return True
    return any(word in MUTATING for word in arguments[:4])


def main():
    payload = json.load(sys.stdin)
    command = payload.get("tool_input", {}).get("command", "")
    if not command or "DOCKER_NPM_ALLOW_HOST=1" in command or os.environ.get("DOCKER_NPM_ALLOW_HOST") == "1":
        return 0
    if not any(is_host_package_change(segment.strip()) for segment in SEGMENT_SPLIT.split(command)):
        return 0
    compose_file = find_compose_file(payload.get("cwd"))
    if compose_file is None:
        return 0
    print(
        f"Blocked: this project runs in Docker ({compose_file}). Do not change packages on the host "
        "(node_modules would be built for the wrong OS/arch/Node). Use the docker-npm skill instead, e.g. "
        "/docker-npm install <package> [--dev] [--target <service>] [--workspace <name>]. "
        "One-off bypass: prefix the command with DOCKER_NPM_ALLOW_HOST=1.",
        file=sys.stderr,
    )
    return 2


if __name__ == "__main__":
    sys.exit(main())
