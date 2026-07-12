#!/usr/bin/env python3
"""Lightweight offline structural scan for GDScript files.

This is not a replacement for Godot's parser. It catches unbalanced delimiters,
unterminated strings, mixed leading indentation, missing function colons, and
empty colon blocks in the shipped source when the Godot binary is unavailable.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ERRORS: list[str] = []


def scan_file(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    stack: list[tuple[str, int]] = []
    pairs = {")": "(", "]": "[", "}": "{"}
    opener = set(pairs.values())
    quote: str | None = None
    escaped = False
    line = 1
    index = 0
    while index < len(text):
        char = text[index]
        if char == "\n":
            line += 1
        if quote is not None:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == quote:
                quote = None
            index += 1
            continue
        if char == "#":
            end = text.find("\n", index)
            if end == -1:
                break
            index = end
            continue
        if char in ('"', "'"):
            quote = char
        elif char in opener:
            stack.append((char, line))
        elif char in pairs:
            if not stack or stack[-1][0] != pairs[char]:
                ERRORS.append(f"{path.relative_to(ROOT)}:{line}: unmatched {char}")
            else:
                stack.pop()
        index += 1
    if quote is not None:
        ERRORS.append(f"{path.relative_to(ROOT)}:{line}: unterminated string")
    for char, opened_line in stack:
        ERRORS.append(f"{path.relative_to(ROOT)}:{opened_line}: unclosed {char}")

    lines = text.splitlines()
    for number, raw in enumerate(lines, start=1):
        leading = raw[: len(raw) - len(raw.lstrip(" \t"))]
        if " " in leading and "\t" in leading:
            ERRORS.append(f"{path.relative_to(ROOT)}:{number}: mixed leading tabs and spaces")
        stripped = raw.strip()
        if stripped.startswith("func ") and not stripped.endswith(":"):
            ERRORS.append(f"{path.relative_to(ROOT)}:{number}: function declaration lacks colon")
        block_prefixes = ("func ", "if ", "elif ", "else:", "for ", "while ", "match ")
        is_control_block = stripped.startswith(block_prefixes)
        if not is_control_block or not stripped.endswith(":"):
            continue
        current_indent = len(leading.replace("\t", "    "))
        for following in range(number, len(lines)):
            nxt = lines[following]
            nxt_stripped = nxt.strip()
            if not nxt_stripped or nxt_stripped.startswith("#"):
                continue
            nxt_leading = nxt[: len(nxt) - len(nxt.lstrip(" \t"))]
            nxt_indent = len(nxt_leading.replace("\t", "    "))
            if nxt_indent <= current_indent:
                ERRORS.append(
                    f"{path.relative_to(ROOT)}:{number}: control block has no indented statement"
                )
            break


def main() -> int:
    files = sorted((ROOT / "scripts").glob("*.gd"))
    for path in files:
        scan_file(path)
    if ERRORS:
        print("FAIL")
        for error in ERRORS:
            print(" -", error)
        return 1
    print(f"PASS: {len(files)} GDScript files passed offline structural scanning")
    return 0


if __name__ == "__main__":
    sys.exit(main())
