#!/usr/bin/env python3
"""PostToolUse (Write|Edit): enforce two global conventions on the code just written.

1. No `if` / `for` / `while` / `else` without braces (only the lines Claude just wrote are checked,
   so pre-existing violations do not nag on every edit).
2. Node + TypeScript projects: no file over 500 lines (extract into the shared toolbox).

Exit code 2 sends stderr back to Claude so it fixes the code in the same turn.
"""
import json
import os
import re
import sys

CODE_EXTENSIONS = (".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs")
IGNORED_PARTS = ("node_modules", "/.next/", "/dist/", "/build/", "/coverage/", "/drizzle/meta/", "/.claude/")
MAX_LINES = 500

STRING_PATTERN = re.compile(r"\"(?:\\.|[^\"\\])*\"|'(?:\\.|[^'\\])*'|`(?:\\.|[^`\\])*`")
CONTROL_PATTERN = re.compile(r"^\s*(\}\s*)?(else\s+)?(if|for|while)\b")
ELSE_PATTERN = re.compile(r"^\s*(\}\s*)?else\b(?!\s+if\b)(.*)$")


def strip_literals(line):
    without_strings = STRING_PATTERN.sub('""', line)
    return re.sub(r"//.*$", "", without_strings)


def rest_after_condition(line):
    """Text after the closing parenthesis of the condition, or None when it spans several lines."""
    start = line.find("(")
    if start == -1:
        return None
    depth = 0
    for index in range(start, len(line)):
        if line[index] == "(":
            depth += 1
        elif line[index] == ")":
            depth -= 1
            if depth == 0:
                return line[index + 1:].strip()
    return None


def next_code_line(lines, index):
    for follower in lines[index + 1:]:
        stripped = strip_literals(follower).strip()
        if stripped:
            return stripped
    return None


def find_brace_violations(snippet):
    lines = snippet.split("\n")
    violations = []
    inside_template = False
    for index, raw in enumerate(lines):
        # Multi-line template literals often hold other languages (SQL, Lua...)
        starts_inside = inside_template
        if strip_literals(raw).count("`") % 2 == 1:
            inside_template = not inside_template
        if starts_inside:
            continue
        line = strip_literals(raw)
        control = CONTROL_PATTERN.match(line)
        else_only = ELSE_PATTERN.match(line)
        rest = None
        if control:
            rest = rest_after_condition(line)
            # `} while (cond);` closes a do/while, it is not a braceless loop
            if rest == ";" and control.group(1):
                continue
        elif else_only:
            rest = else_only.group(2).strip()
        if rest is None:
            continue
        if rest.startswith("{") or rest.startswith("/*"):
            continue
        if rest == "":
            follower = next_code_line(lines, index)
            # A dangling condition continues on the next line only with an operator
            if follower is None or follower.startswith(("{", "&&", "||", "?", ":")):
                continue
        violations.append(raw.strip())
    return violations


def has_node_project(path):
    current = os.path.dirname(os.path.abspath(path))
    while current != os.path.dirname(current):
        if os.path.exists(os.path.join(current, "package.json")):
            return True
        current = os.path.dirname(current)
    return False


def main():
    payload = json.load(sys.stdin)
    tool_input = payload.get("tool_input", {})
    path = tool_input.get("file_path", "")
    if not path.endswith(CODE_EXTENSIONS) or path.endswith(".d.ts"):
        return 0
    if any(part in path for part in IGNORED_PARTS):
        return 0

    problems = []
    snippet = tool_input.get("content") or tool_input.get("new_string") or ""
    violations = find_brace_violations(snippet)
    if violations:
        problems.append(
            "Convention: control statements must always use braces. Fix these lines in "
            + path + ":\n  " + "\n  ".join(violations[:8])
        )

    if os.path.exists(path) and has_node_project(path):
        with open(path, encoding="utf-8", errors="replace") as handle:
            line_count = sum(1 for _ in handle)
        if line_count > MAX_LINES:
            problems.append(
                f"Convention: {path} has {line_count} lines (limit {MAX_LINES}). Reduce it now by extracting "
                "reusable functions into the shared toolbox package (importable by server and client), "
                "not by moving code around in place."
            )

    if problems:
        print("\n\n".join(problems), file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
