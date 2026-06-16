from pathlib import Path

from vmodel_engine.intake import copy_source_requirements, read_requirements_input


def test_read_requirements_input_from_directory(tmp_path: Path) -> None:
    (tmp_path / "User Requirements.txt").write_text("- Users must water plants.\n", encoding="utf-8")
    (tmp_path / "toolchain.md").write_text("# Toolchain\nUse test hardware.\n", encoding="utf-8")
    (tmp_path / "ignore.bin").write_bytes(b"nope")

    text = read_requirements_input(tmp_path)

    assert "Source: User Requirements.txt" in text
    assert "Users must water plants" in text
    assert "Reference Evidence" in text
    assert "toolchain.md" in text
    assert "Use test hardware" not in text
    assert "ignore.bin" not in text


def test_copy_source_requirements_preserves_supported_files(tmp_path: Path) -> None:
    source = tmp_path / "source"
    target = tmp_path / "target"
    source.mkdir()
    (source / "a.txt").write_text("hello", encoding="utf-8")
    (source / "b.bin").write_bytes(b"skip")

    copied = copy_source_requirements(source, target)

    assert copied == [target / "a.txt"]
    assert (target / "a.txt").read_text(encoding="utf-8") == "hello"
    assert not (target / "b.bin").exists()
