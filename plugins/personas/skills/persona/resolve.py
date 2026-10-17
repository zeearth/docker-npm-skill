#!/usr/bin/env python3
"""Resolve a persona from its layers and print the merged Markdown.

Layers, lowest to highest priority:
  1. bundled   <plugin>/personas/<id>.md
  2. global    ~/.claude/personas/<id>.md
  3. project   <project>/.claude/personas/<id>.md

Merge rule: a higher layer COMPLETES the lower ones. Sections (## headings) are matched by name:
a section present in several layers is replaced by the highest one, a new section is appended.
A heading ending with " +" appends to the lower section instead of replacing it.
`replace: true` in a file's front matter makes that layer ignore every lower one.

Usage: resolve.py list | show <id> [--project DIR] | path <id> <global|project> [--project DIR]
"""
import os
import re
import sys

PLUGIN_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


def layer_dirs(project):
    return [
        ("bundled", os.path.join(PLUGIN_ROOT, "personas")),
        ("global", os.path.expanduser("~/.claude/personas")),
        ("project", os.path.join(project, ".claude", "personas")),
    ]


def parse(text):
    meta = {}
    body = text
    match = re.match(r"^---\n(.*?)\n---\n?(.*)$", text, re.S)
    if match:
        for line in match.group(1).splitlines():
            if ":" in line:
                key, value = line.split(":", 1)
                meta[key.strip()] = value.strip()
        body = match.group(2)
    sections = []
    current = ["_intro", []]
    for line in body.splitlines():
        heading = re.match(r"^## +(.*?)\s*$", line)
        if heading:
            sections.append(current)
            current = [heading.group(1), []]
        else:
            current[1].append(line)
    sections.append(current)
    return meta, [(name, "\n".join(lines).strip()) for name, lines in sections if name != "_intro" or "\n".join(lines).strip()]


def load_layers(persona_id, project):
    found = []
    for label, directory in layer_dirs(project):
        path = os.path.join(directory, persona_id + ".md")
        if os.path.isfile(path):
            with open(path, encoding="utf-8") as handle:
                found.append((label, path) + parse(handle.read()))
    return found


def merge(layers):
    start = 0
    for index, layer in enumerate(layers):
        if layer[2].get("replace", "").lower() == "true":
            start = index
    meta = {}
    order = []
    bodies = {}
    for _label, _path, layer_meta, sections in layers[start:]:
        meta.update({key: value for key, value in layer_meta.items() if key != "replace"})
        for name, body in sections:
            append = name.endswith(" +")
            key = name[:-2].strip() if append else name
            if key not in bodies:
                order.append(key)
                bodies[key] = body
            elif append:
                bodies[key] = (bodies[key] + "\n" + body).strip()
            else:
                bodies[key] = body
    return meta, order, bodies, layers[start:]


def command_list(project):
    ids = {}
    for label, directory in layer_dirs(project):
        if os.path.isdir(directory):
            for name in sorted(os.listdir(directory)):
                if name.endswith(".md") and not name.startswith("_"):
                    ids.setdefault(name[:-3], []).append(label)
    for persona_id in sorted(ids):
        meta, _order, _bodies, _used = merge(load_layers(persona_id, project))
        print(f"{persona_id}\t[{' + '.join(ids[persona_id])}]\t{meta.get('description', '')}")


def command_show(persona_id, project):
    layers = load_layers(persona_id, project)
    if not layers:
        print(f"No persona named '{persona_id}'. Run list to see the available ones.", file=sys.stderr)
        return 1
    meta, order, bodies, used = merge(layers)
    print(f"# Persona: {meta.get('name', persona_id)}")
    print(f"<!-- layers: {' + '.join(label for label, *_ in used)} -->")
    if "_intro" in bodies:
        print(f"\n{bodies['_intro']}")
    for key in order:
        if key != "_intro":
            print(f"\n## {key}\n\n{bodies[key]}")
    return 0


def command_path(persona_id, scope, project):
    base = os.path.expanduser("~/.claude/personas") if scope == "global" else os.path.join(project, ".claude", "personas")
    print(os.path.join(base, persona_id + ".md"))
    return 0


def main(argv):
    project = os.getcwd()
    if "--project" in argv:
        index = argv.index("--project")
        project = os.path.abspath(argv[index + 1])
        argv = argv[:index] + argv[index + 2:]
    if not argv or argv[0] == "list":
        command_list(project)
        return 0
    if argv[0] == "show" and len(argv) == 2:
        return command_show(argv[1], project)
    if argv[0] == "path" and len(argv) == 3 and argv[2] in ("global", "project"):
        return command_path(argv[1], argv[2], project)
    print(__doc__, file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
