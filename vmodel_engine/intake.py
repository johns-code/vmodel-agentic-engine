from __future__ import annotations

import re
import zipfile
from pathlib import Path
from xml.etree import ElementTree


SUPPORTED_REQUIREMENT_EXTENSIONS = {".txt", ".md", ".docx", ".pdf"}


def read_requirements_input(path: Path) -> str:
    if path.is_file():
        return _read_supported_file(path)
    if path.is_dir():
        primary_files = _primary_requirement_files(path)
        files_to_read = primary_files or [
            file_path
            for file_path in sorted(path.rglob("*"))
            if file_path.is_file() and file_path.suffix.lower() in SUPPORTED_REQUIREMENT_EXTENSIONS
        ]
        sections: list[str] = []
        for file_path in files_to_read:
            text = _read_supported_file(file_path).strip()
            if text:
                sections.append(f"# Source: {file_path.name}\n\n{text}")
        reference_files = [
            file_path.name
            for file_path in sorted(path.rglob("*"))
            if file_path.is_file()
            and file_path.suffix.lower() in SUPPORTED_REQUIREMENT_EXTENSIONS
            and file_path not in files_to_read
        ]
        if reference_files:
            sections.append(
                "# Reference Evidence\n\n"
                "The following source documents are preserved as evidence and design inputs, "
                "but are not automatically decomposed into implementation tasks. "
                f"Reference documents: {', '.join(reference_files)}."
            )
        if not sections:
            raise ValueError(f"no supported requirements files found in {path}")
        return "\n\n".join(sections)
    raise FileNotFoundError(path)


def copy_source_requirements(source: Path, target_dir: Path) -> list[Path]:
    target_dir.mkdir(parents=True, exist_ok=True)
    copied: list[Path] = []
    if source.is_file():
        target = target_dir / source.name
        target.write_bytes(source.read_bytes())
        return [target]
    for file_path in sorted(source.rglob("*")):
        if file_path.is_file() and file_path.suffix.lower() in SUPPORTED_REQUIREMENT_EXTENSIONS:
            relative = file_path.relative_to(source)
            target = target_dir / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(file_path.read_bytes())
            copied.append(target)
    return copied


def _read_supported_file(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix in {".txt", ".md"}:
        return path.read_text(encoding="utf-8", errors="ignore")
    if suffix == ".docx":
        return _read_docx(path)
    if suffix == ".pdf":
        return _read_pdf(path)
    raise ValueError(f"unsupported requirements file type: {path}")


def _primary_requirement_files(path: Path) -> list[Path]:
    candidates = []
    for file_path in sorted(path.rglob("*")):
        if not file_path.is_file() or file_path.suffix.lower() not in SUPPORTED_REQUIREMENT_EXTENSIONS:
            continue
        normalized = re.sub(r"[^a-z0-9]+", " ", file_path.stem.lower()).strip()
        if normalized in {"user requirements", "requirements"} or normalized.endswith(" requirements"):
            candidates.append(file_path)
    return candidates


def _read_docx(path: Path) -> str:
    with zipfile.ZipFile(path) as archive:
        xml = archive.read("word/document.xml")
    root = ElementTree.fromstring(xml)
    namespace = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
    paragraphs: list[str] = []
    for paragraph in root.findall(".//w:p", namespace):
        text = "".join(node.text or "" for node in paragraph.findall(".//w:t", namespace)).strip()
        if text:
            paragraphs.append(text)
    return "\n".join(paragraphs)


def _read_pdf(path: Path) -> str:
    try:
        import PyPDF2
    except ImportError:
        return f"[PDF text extraction unavailable for {path.name}; original file preserved as source evidence.]"

    text_parts: list[str] = []
    with path.open("rb") as file:
        reader = PyPDF2.PdfReader(file)
        for page in reader.pages:
            text_parts.append(page.extract_text() or "")
    text = "\n".join(text_parts).strip()
    if text:
        return text
    return f"[No extractable PDF text found in {path.name}; original file preserved as source evidence.]"


def source_name(path: Path) -> str:
    name = path.name if path.is_file() else path.parts[-1]
    cleaned = re.sub(r"[^a-zA-Z0-9]+", "-", name).strip("-").lower()
    return cleaned or "requirements"
