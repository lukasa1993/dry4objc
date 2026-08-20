from pathlib import Path

from dry4objc.core import find_duplicates, normalized_tokens


def test_normalizes_identifiers_and_literals(tmp_path: Path) -> None:
    source = tmp_path / "sample.m"
    source.write_text("int answer = 42;\n", encoding="utf-8")
    assert [value for value, _ in normalized_tokens(source)] == ["int", "ID", "=", "NUM", ";"]


def test_finds_duplicate_blocks(tmp_path: Path) -> None:
    (tmp_path / "a.m").write_text("int a(int x) { if (x > 0) return x + 1; return 0; }\n", encoding="utf-8")
    (tmp_path / "b.m").write_text("int b(int y) { if (y > 2) return y + 3; return 4; }\n", encoding="utf-8")
    assert find_duplicates(tmp_path, min_tokens=12)
