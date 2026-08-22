from pathlib import Path

from dry4objc.core import find_duplicates


def test_cross_file_duplicate_is_found(tmp_path: Path) -> None:
    first = tmp_path / ("a_" + 'sample.m')
    second = tmp_path / ("b_" + 'sample.m')
    first.write_text('@interface Choice\n- (int)choose:(int)a other:(int)b;\n@end\n@implementation Choice\n- (int)choose:(int)a other:(int)b {\n  if (a && b) { return 1; }\n  return 0;\n}\n@end\n', encoding="utf-8")
    second.write_text('@interface Selection\n- (int)decide:(int)a other:(int)b;\n@end\n@implementation Selection\n- (int)decide:(int)a other:(int)b {\n  if (a && b) { return 1; }\n  return 0;\n}\n@end\n', encoding="utf-8")
    duplicates = find_duplicates(tmp_path, min_tokens=8)
    assert duplicates


def test_non_overlapping_same_file_duplicate_is_found(tmp_path: Path) -> None:
    path = tmp_path / 'sample.m'
    path.write_text('@interface Choice\n- (int)choose:(int)a other:(int)b;\n@end\n@implementation Choice\n- (int)choose:(int)a other:(int)b {\n  if (a && b) { return 1; }\n  return 0;\n}\n@end\n' + "\n" + '@interface Selection\n- (int)decide:(int)a other:(int)b;\n@end\n@implementation Selection\n- (int)decide:(int)a other:(int)b {\n  if (a && b) { return 1; }\n  return 0;\n}\n@end\n', encoding="utf-8")
    duplicates = find_duplicates(tmp_path, min_tokens=8)
    assert any(item.locations[0].file == item.locations[1].file for item in duplicates)
