#!/usr/bin/env python3
"""PreToolUse (Write|Edit): refuse to write secrets into committed files.

- Known credential formats are refused in any file except git-ignored `.env` files.
- docker-compose files and .env.example must use `${VAR}` / empty values for anything secret-looking.

Exit code 2 blocks the tool call and sends stderr back to Claude.
"""
import json
import os
import re
import sys

TOKEN_PATTERNS = {
    "AWS access key": re.compile(r"AKIA[0-9A-Z]{16}"),
    "GitHub token": re.compile(r"gh[pousr]_[A-Za-z0-9]{36,}|github_pat_[A-Za-z0-9_]{40,}"),
    "API key (sk-)": re.compile(r"\bsk-[A-Za-z0-9_-]{32,}"),
    "Slack token": re.compile(r"xox[baprs]-[A-Za-z0-9-]{10,}"),
    "Google API key": re.compile(r"AIza[0-9A-Za-z_-]{35}"),
    "private key": re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----"),
}
SECRET_NAME = re.compile(r"(PASSWORD|PASSWD|SECRET|TOKEN|API_?KEY|PRIVATE_KEY|ENCRYPTION_KEY)$", re.IGNORECASE)
ASSIGNMENT = re.compile(r"^\s*(?:-\s*)?([A-Za-z_][A-Za-z0-9_]*)\s*[:=]\s*(.*?)\s*$")


def is_ignored_env_file(name):
    return name.startswith(".env") and not name.endswith((".example", ".sample", ".template"))


def find_secret_assignments(name, content):
    is_compose = name.startswith("docker-compose") or name.startswith("compose")
    is_env_example = name.startswith(".env")
    if not (is_compose or is_env_example):
        return []
    found = []
    for line in content.split("\n"):
        match = ASSIGNMENT.match(line)
        if not match or not SECRET_NAME.search(match.group(1)):
            continue
        value = match.group(2).strip("\"'")
        if value == "" or value.startswith("$"):
            continue
        if is_env_example and value.startswith("#"):
            continue
        found.append(match.group(1))
    return found


def main():
    payload = json.load(sys.stdin)
    tool_input = payload.get("tool_input", {})
    path = tool_input.get("file_path", "")
    content = tool_input.get("content") or tool_input.get("new_string") or ""
    name = os.path.basename(path)
    if not content or is_ignored_env_file(name):
        return 0

    problems = []
    for label, pattern in TOKEN_PATTERNS.items():
        if pattern.search(content):
            problems.append(f"a {label} appears in {path}")
    for key in find_secret_assignments(name, content):
        problems.append(f"{key} has a literal value in {name} (use ${{{key}}} or leave it empty in .env.example)")

    if problems:
        print(
            "Blocked: no secret in committed files.\n  - " + "\n  - ".join(problems)
            + "\nUse ${VAR} substitution read from the git-ignored .env, and document the key with an empty "
            "value in .env.example.",
            file=sys.stderr,
        )
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
