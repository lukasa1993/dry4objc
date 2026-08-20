from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Token:
    value: str
    kind: str
    line: int
    column: int
    start: int
    end: int


MULTI = (
    "<<=", ">>=", "...", "===", "!==", "->*", "::", "++", "--", "->",
    "&&", "||", "==", "!=", "<=", ">=", "+=", "-=", "*=", "/=", "%=",
    "&=", "|=", "^=", "<<", ">>", "##",
)


def tokenize(text: str) -> list[Token]:
    tokens: list[Token] = []
    index = 0
    line = 1
    column = 1
    length = len(text)

    def advance(fragment: str) -> None:
        nonlocal line, column
        newlines = fragment.count("\n")
        if newlines:
            line += newlines
            column = len(fragment.rsplit("\n", 1)[-1]) + 1
        else:
            column += len(fragment)

    while index < length:
        start = index
        start_line = line
        start_column = column
        character = text[index]
        if character.isspace():
            index += 1
            while index < length and text[index].isspace():
                index += 1
            advance(text[start:index])
            continue
        if text.startswith("//", index):
            index = text.find("\n", index)
            if index < 0:
                break
            advance(text[start:index])
            continue
        if text.startswith("/*", index):
            end = text.find("*/", index + 2)
            index = length if end < 0 else end + 2
            advance(text[start:index])
            continue
        if character in {'"', "'"} or (character == "@" and index + 1 < length and text[index + 1] == '"'):
            quote_index = index + 1 if character == "@" else index
            quote = text[quote_index]
            index = quote_index + 1
            escaped = False
            while index < length:
                current = text[index]
                index += 1
                if escaped:
                    escaped = False
                elif current == "\\":
                    escaped = True
                elif current == quote:
                    break
            fragment = text[start:index]
            tokens.append(Token(fragment, "string", start_line, start_column, start, index))
            advance(fragment)
            continue
        if character.isalpha() or character == "_":
            index += 1
            while index < length and (text[index].isalnum() or text[index] == "_"):
                index += 1
            fragment = text[start:index]
            tokens.append(Token(fragment, "identifier", start_line, start_column, start, index))
            advance(fragment)
            continue
        if character.isdigit():
            index += 1
            while index < length and (text[index].isalnum() or text[index] in "._"):
                index += 1
            fragment = text[start:index]
            tokens.append(Token(fragment, "number", start_line, start_column, start, index))
            advance(fragment)
            continue
        operator = next((value for value in MULTI if text.startswith(value, index)), character)
        index += len(operator)
        tokens.append(Token(operator, "operator", start_line, start_column, start, index))
        advance(operator)
    return tokens


import os
from pathlib import Path
from typing import Sequence

EXCLUDED_DIRS = {".git", ".hg", ".build", "build", "DerivedData", "Pods", "target", "vendor"}


def discover_files(root: Path, filters: Sequence[str] = ()) -> list[Path]:
    files: list[Path] = []
    for directory, dirnames, filenames in os.walk(root):
        dirnames[:] = sorted(name for name in dirnames if name not in EXCLUDED_DIRS and not name.lower().startswith("test"))
        for filename in sorted(filenames):
            if not filename.endswith((".m", ".mm")):
                continue
            path = Path(directory, filename)
            relative = path.relative_to(root).as_posix()
            if filters and not any(fragment in relative for fragment in filters):
                continue
            files.append(path)
    return files


import hashlib
from dataclasses import asdict, dataclass

KEYWORDS = {
    "auto", "break", "case", "char", "const", "continue", "default", "do", "double", "else", "enum", "extern", "float", "for", "goto", "if", "inline", "int", "long", "register", "restrict", "return", "short", "signed", "sizeof", "static", "struct", "switch", "typedef", "union", "unsigned", "void", "volatile", "while",
    "interface", "implementation", "protocol", "property", "synthesize", "dynamic", "selector", "encode", "class", "public", "private", "protected", "package", "try", "catch", "finally", "throw", "synchronized", "autoreleasepool", "end",
}


@dataclass(frozen=True)
class Location:
    file: str
    start_line: int
    end_line: int


@dataclass(frozen=True)
class Duplicate:
    token_count: int
    locations: tuple[Location, ...]

    def to_dict(self) -> dict[str, object]:
        return {"token_count": self.token_count, "locations": [asdict(location) for location in self.locations]}


def normalized_tokens(path: Path) -> list[tuple[str, int]]:
    out: list[tuple[str, int]] = []
    for token in tokenize(path.read_text(encoding="utf-8")):
        if token.kind == "identifier":
            value = token.value if token.value in KEYWORDS else "ID"
        elif token.kind == "number":
            value = "NUM"
        elif token.kind == "string":
            value = "STR"
        else:
            value = token.value
        out.append((value, token.line))
    return out


def find_duplicates(root: Path, min_tokens: int = 40, filters: Sequence[str] = (), max_groups: int = 50) -> list[Duplicate]:
    if min_tokens < 4:
        raise ValueError("min_tokens must be at least 4")
    groups: dict[str, list[Location]] = {}
    for path in discover_files(root, filters):
        values = normalized_tokens(path)
        for start in range(len(values) - min_tokens + 1):
            window = values[start:start + min_tokens]
            digest = hashlib.sha256("\0".join(value for value, _ in window).encode()).hexdigest()
            groups.setdefault(digest, []).append(Location(path.relative_to(root).as_posix(), window[0][1], window[-1][1]))
    candidates: list[Duplicate] = []
    for locations in groups.values():
        unique = tuple(dict.fromkeys(locations))
        if len(unique) >= 2:
            candidates.append(Duplicate(min_tokens, unique))
    candidates.sort(key=lambda item: (-len(item.locations), item.locations[0].file, item.locations[0].start_line))
    selected: list[Duplicate] = []
    for candidate in candidates:
        first, second = candidate.locations[:2]
        if any(old.locations[0].file == first.file and old.locations[1].file == second.file and abs(old.locations[0].start_line - first.start_line) <= 2 and abs(old.locations[1].start_line - second.start_line) <= 2 for old in selected):
            continue
        selected.append(candidate)
        if len(selected) >= max_groups:
            break
    return selected
