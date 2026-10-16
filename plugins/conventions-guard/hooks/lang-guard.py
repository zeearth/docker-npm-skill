#!/usr/bin/env python3
"""PostToolUse (Write|Edit): Markdown files are written in English unless told otherwise.

Only the text just written is analysed, with a stop-word count (French vs English). A file can opt
out with an HTML comment `<!-- lang: fr -->` (any language code) in its first 5 lines, which is how
"unless the user says otherwise" is recorded. Exit code 2 sends stderr back to Claude.
"""
import json
import re
import sys

IGNORED_PARTS = ("node_modules", "/.claude/", "/CHANGELOG")
MIN_WORDS = 25
FRENCH_RATIO = 0.6

FRENCH_WORDS = {
    "le", "la", "les", "des", "une", "un", "du", "de", "est", "sont", "pour", "dans", "avec", "sur",
    "pas", "que", "qui", "ce", "cette", "ces", "et", "ou", "au", "aux", "en", "ne", "se", "il", "elle",
    "nous", "vous", "plus", "par", "mais", "sans", "sous", "chaque", "aussi", "être", "peut", "donc",
}
ENGLISH_WORDS = {
    "the", "is", "are", "for", "in", "with", "on", "not", "that", "this", "these", "and", "or", "to",
    "of", "it", "we", "you", "more", "by", "but", "without", "each", "also", "be", "can", "so", "a",
    "an", "as", "at", "from", "when", "if", "only", "which", "will", "has", "have",
}
OPT_OUT = re.compile(r"<!--\s*lang:\s*[a-z]{2}\s*-->", re.IGNORECASE)


def prose_words(text):
    without_code = re.sub(r"```.*?```", " ", text, flags=re.DOTALL)
    without_code = re.sub(r"`[^`]*`", " ", without_code)
    return re.findall(r"[a-zA-ZÀ-ÿ']+", without_code.lower())


def main():
    data = json.load(sys.stdin)
    tool_input = data.get("tool_input", {})
    path = tool_input.get("file_path", "")
    if not path.lower().endswith((".md", ".mdx")) or any(part in path for part in IGNORED_PARTS):
        return 0
    written = tool_input.get("content") or tool_input.get("new_string") or ""
    try:
        with open(path, encoding="utf-8") as handle:
            head = "\n".join(handle.read().split("\n")[:5])
    except OSError:
        head = ""
    if OPT_OUT.search(head) or OPT_OUT.search(written):
        return 0

    words = [word.split("'")[-1] for word in prose_words(written)]
    french = sum(1 for word in words if word in FRENCH_WORDS)
    english = sum(1 for word in words if word in ENGLISH_WORDS)
    if len(words) < MIN_WORDS or french + english == 0:
        return 0
    if french / (french + english) >= FRENCH_RATIO:
        sys.stderr.write(
            f"{path} looks written in French. Markdown files must be in English unless the user said "
            "otherwise: rewrite it in English, or, if the user asked for another language here, add "
            "`<!-- lang: fr -->` in the first lines to record it.\n"
        )
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
