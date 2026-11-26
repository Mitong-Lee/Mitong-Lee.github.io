#!/usr/bin/env python3
"""Build content.json for the Mitong Li static portfolio site.

The script discovers:
  - each first-level folder inside image/ as a photography project;
  - supported image files inside each project folder (recursive);
  - each Markdown file inside writing/ (recursive).

No third-party Python packages are required.
"""

from __future__ import annotations

import json
import re
from datetime import date
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent
IMAGE_DIR = ROOT / "image"
WRITING_DIR = ROOT / "writing"
OUTPUT_FILE = ROOT / "content.json"

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".gif", ".avif"}
COVER_NAMES = {"cover", "_cover", "thumbnail", "_thumbnail"}


def natural_key(value: str) -> list[Any]:
    """Sort names naturally: 2.webp comes before 10.webp."""
    return [(0, int(part)) if part.isdigit() else (1, part.casefold())
            for part in re.split(r"(\d+)", value)]


def relative_url(path: Path) -> str:
    """Return a URL path relative to index.html, with forward slashes."""
    return "./" + path.relative_to(ROOT).as_posix()


def read_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            raise ValueError("JSON root must be an object")
        return data
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(f"WARNING: Could not read {path.relative_to(ROOT)}: {exc}")
        return {}


def title_from_folder(name: str) -> str:
    """Use the folder name as-is unless a project.json title is supplied."""
    return name


def scan_project(folder: Path) -> dict[str, Any] | None:
    settings = read_json(folder / "project.json")

    images = sorted(
        (path for path in folder.rglob("*")
         if path.is_file() and path.suffix.casefold() in IMAGE_EXTENSIONS),
        key=lambda path: natural_key(path.relative_to(folder).as_posix()),
    )

    if not images:
        return None

    # A file named cover/thumbnail is used as the directory thumbnail and is
    # not included in the photograph sequence. If absent, the first photo is
    # also used as the thumbnail and remains in the sequence.
    explicit_cover = None
    configured_cover = settings.get("cover")
    if isinstance(configured_cover, str) and configured_cover.strip():
        candidate = folder / configured_cover
        if candidate.is_file() and candidate.suffix.casefold() in IMAGE_EXTENSIONS:
            explicit_cover = candidate

    if explicit_cover is None:
        # Only a cover placed directly in the project folder is the project
        # thumbnail. A cover.webp inside a group folder is an ordinary photo.
        explicit_cover = next(
            (path for path in images
             if path.parent == folder and path.stem.casefold() in COVER_NAMES),
            None,
        )

    cover = explicit_cover or images[0]
    photographs = [path for path in images if path != explicit_cover]
    if not photographs:
        # A project containing only a cover still displays that image.
        photographs = [cover]

    default_info = str(settings.get("info", "")).strip()
    project_id = str(settings.get("id", folder.name)).strip() or folder.name
    project_title = str(settings.get("title", title_from_folder(folder.name))).strip() or folder.name

    photo_items = []
    for image_path in photographs:
        # Caption inheritance:
        # project.json -> nearest ancestor group.json -> image-specific JSON.
        # This lets a whole subfolder share one caption without repeating it.
        photo_info = default_info
        relative_parent = image_path.parent.relative_to(folder)
        group_dir = folder
        for part in relative_parent.parts:
            group_dir = group_dir / part
            group_settings = read_json(group_dir / "group.json")
            if "info" in group_settings:
                photo_info = str(group_settings.get("info", "")).strip()

        # Optional sidecar: 01.webp + 01.json. It overrides the inherited
        # caption for this one photograph only.
        sidecar = read_json(image_path.with_suffix(".json"))
        if "info" in sidecar:
            photo_info = str(sidecar.get("info", "")).strip()
        photo_alt = str(sidecar.get("alt", project_title)).strip()
        photo_items.append({
            "src": relative_url(image_path),
            "info": photo_info,
            "alt": photo_alt,
        })

    return {
        "id": project_id,
        "title": project_title,
        "cover": relative_url(cover),
        "info": default_info,
        "photographs": photo_items,
    }


def clean_markdown_title(markdown: str, fallback: str) -> str:
    """Prefer YAML title, then the first H1, then a readable filename."""
    text = markdown.lstrip("\ufeff")

    # Small front-matter reader; no YAML dependency is needed.
    if text.startswith("---"):
        closing = re.search(r"\n---\s*(?:\n|$)", text[3:])
        if closing:
            front_matter = text[3:3 + closing.start()]
            match = re.search(r"(?m)^title\s*:\s*(.*?)\s*$", front_matter)
            if match:
                title = match.group(1).strip().strip("\"'")
                if title:
                    return title
            text = text[3 + closing.end():]

    heading = re.search(r"(?m)^#\s+(.+?)\s*#*\s*$", text)
    if heading:
        return heading.group(1).strip()

    return fallback


def readable_filename(stem: str) -> str:
    """Turn a filename such as 112426-myEssay into a readable title."""
    value = re.sub(r"^\d{6}(?:[-_ ]*)", "", stem)
    value = re.sub(r"([a-z0-9])([A-Z])", r"\1 \2", value)
    value = re.sub(r"[_-]+", " ", value)
    value = re.sub(r"\s+", " ", value).strip()
    return value or stem


def date_prefix(path: Path) -> date | None:
    """Recognize MMDDYY at the beginning of names, e.g. 112426-title.md."""
    match = re.match(r"^(\d{2})(\d{2})(\d{2})(?:[-_ ]|[A-Za-z]|$)", path.stem)
    if not match:
        return None

    month, day, year = (int(part) for part in match.groups())
    year += 2000 if year < 70 else 1900
    try:
        return date(year, month, day)
    except ValueError:
        return None


def scan_writings() -> list[dict[str, str]]:
    if not WRITING_DIR.is_dir():
        return []

    files = sorted(
        (path for path in WRITING_DIR.rglob("*")
         if path.is_file() and path.suffix.casefold() == ".md"),
        key=lambda path: natural_key(path.relative_to(WRITING_DIR).as_posix()),
    )

    # Dated files appear newest first. Undated files follow alphabetically.
    files.sort(
        key=lambda path: (
            date_prefix(path) is None,
            -(date_prefix(path).toordinal()) if date_prefix(path) else 0,
            natural_key(path.relative_to(WRITING_DIR).as_posix()),
        )
    )

    writings = []
    for path in files:
        try:
            markdown = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError) as exc:
            print(f"WARNING: Could not read {path.relative_to(ROOT)}: {exc}")
            continue

        writings.append({
            "title": clean_markdown_title(markdown, readable_filename(path.stem)),
            "file": relative_url(path),
        })

    return writings


def main() -> None:
    projects = []
    if IMAGE_DIR.is_dir():
        folders = sorted(
            (path for path in IMAGE_DIR.iterdir() if path.is_dir()),
            key=lambda path: natural_key(path.name),
        )
        for folder in folders:
            project = scan_project(folder)
            if project:
                projects.append(project)

    data = {
        "projects": projects,
        "writings": scan_writings(),
    }

    OUTPUT_FILE.write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    photo_count = sum(len(project["photographs"]) for project in projects)
    print(f"Generated {OUTPUT_FILE.name}")
    print(f"  Projects: {len(projects)}")
    print(f"  Photographs: {photo_count}")
    print(f"  Markdown articles: {len(data['writings'])}")


if __name__ == "__main__":
    main()
