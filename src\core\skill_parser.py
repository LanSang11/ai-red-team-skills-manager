"""Skill file format parser supporting OpenClaw, Hermes, and Claude Code formats.

Supports three main formats:
- OpenClaw: Custom metadata block ending with <<<END_OF_SKILL_METADATA>>>
- Hermes: YAML frontmatter (--- delimiters)
- Claude Code: YAML frontmatter with user-invocable / allowed-tools fields
- Plain Markdown: No metadata, extracts title and description from content
"""

import json
import re
import yaml
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional


@dataclass
class SkillInfo:
    """Parsed skill information."""

    name: str
    description: str = ""
    version: str = ""
    author: str = ""
    tags: List[str] = field(default_factory=list)
    category: str = "tools"
    format: str = "unknown"  # openclaw, hermes, claude, plain
    path: str = ""
    metadata: Dict[str, object] = field(default_factory=dict)

    @property
    def dir_name(self) -> str:
        """Get the directory name of the skill."""
        return Path(self.path).name if self.path else self.name


def parse_skill(skill_dir: Path) -> Optional[SkillInfo]:
    """Parse a skill directory and extract metadata.

    Tries parsing in order:
    1. YAML frontmatter (Hermes / Claude Code)
    2. OpenClaw custom metadata block
    3. Plain markdown fallback

    Args:
        skill_dir: Path to the skill directory.

    Returns:
        SkillInfo if SKILL.md exists, None otherwise.
    """
    skill_md = skill_dir / "SKILL.md"
    if not skill_md.exists():
        return None

    try:
        content = skill_md.read_text(encoding="utf-8")
    except Exception:
        return None

    if not content.strip():
        return None

    # Try YAML frontmatter (Hermes / Claude Code)
    info = _parse_yaml_frontmatter(content, skill_dir)
    if info:
        return info

    # Try OpenClaw custom metadata format
    info = _parse_openclaw_format(content, skill_dir)
    if info:
        return info

    # Fallback: plain markdown
    return _parse_plain_markdown(content, skill_dir)


def infer_category(skill: SkillInfo, categories: Dict[str, List[str]]) -> str:
    """Infer skill category from name, description, tags, and path.

    Args:
        skill: Parsed skill info.
        categories: Category definitions from config.

    Returns:
        Best matching category name, or 'tools' as default.
    """
    text = f"{skill.name} {skill.description} {' '.join(skill.tags)} {skill.path}".lower()

    scores: Dict[str, int] = {}
    for cat, keywords in categories.items():
        score = sum(1 for kw in keywords if kw.lower() in text)
        if score > 0:
            scores[cat] = score

    if scores:
        return max(scores, key=scores.get)
    return "tools"


# --- Internal parsers ---


def _parse_yaml_frontmatter(content: str, skill_dir: Path) -> Optional[SkillInfo]:
    """Parse YAML frontmatter format (Hermes and Claude Code)."""
    match = re.match(r"^---\s*\n(.*?)\n---\s*\n", content, re.DOTALL)
    if not match:
        return None

    try:
        metadata = yaml.safe_load(match.group(1))
        if not isinstance(metadata, dict):
            return None
    except Exception:
        return None

    # Determine format by characteristic fields
    fmt = "hermes"
    if "user-invocable" in metadata or "allowed-tools" in metadata:
        fmt = "claude"

    tags = metadata.get("tags", [])
    if isinstance(tags, str):
        tags = [t.strip() for t in tags.split(",")]

    return SkillInfo(
        name=metadata.get("name", skill_dir.name),
        description=metadata.get("description", ""),
        version=metadata.get("version", ""),
        author=metadata.get("author", ""),
        tags=tags,
        format=fmt,
        path=str(skill_dir),
        metadata=metadata,
    )


def _parse_openclaw_format(content: str, skill_dir: Path) -> Optional[SkillInfo]:
    """Parse OpenClaw custom metadata format (ends with <<<END_OF_SKILL_METADATA>>>)."""
    match = re.match(r"^(.*?)<<<END_OF_SKILL_METADATA>>>", content, re.DOTALL)
    if not match:
        return None

    meta_text = match.group(1)
    metadata: Dict[str, object] = {}

    for line in meta_text.strip().split("\n"):
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if ":" in line:
            key, _, value = line.partition(":")
            key = key.strip().lower()
            value = value.strip()
            if key == "tags":
                metadata[key] = [t.strip() for t in value.split(",")]
            elif key == "version":
                metadata[key] = value
            else:
                metadata[key] = value

    if not metadata:
        return None

    # Also try to load _meta.json for additional info
    meta_json = skill_dir / "_meta.json"
    if meta_json.exists():
        try:
            with open(meta_json, "r", encoding="utf-8") as f:
                json_meta = json.load(f)
                if isinstance(json_meta, dict):
                    metadata.update(json_meta)
        except Exception:
            pass

    tags = metadata.get("tags", [])
    if isinstance(tags, str):
        tags = [t.strip() for t in tags.split(",")]

    return SkillInfo(
        name=metadata.get("name", metadata.get("slug", skill_dir.name)),
        description=metadata.get("description", ""),
        version=metadata.get("version", ""),
        author=metadata.get("author", metadata.get("ownerId", "")),
        tags=tags,
        format="openclaw",
        path=str(skill_dir),
        metadata=metadata,
    )


def _parse_plain_markdown(content: str, skill_dir: Path) -> SkillInfo:
    """Parse plain markdown without structured metadata."""
    # Extract title from first heading
    title_match = re.search(r"^#\s+(.+)$", content, re.MULTILINE)
    name = title_match.group(1).strip() if title_match else skill_dir.name

    # Extract description from first non-heading, non-empty line
    desc = ""
    for line in content.split("\n"):
        stripped = line.strip()
        if stripped and not stripped.startswith("#") and not stripped.startswith(">"):
            desc = stripped
            break

    # Try to extract tags from common patterns
    tags: List[str] = []
    tags_match = re.search(r"(?:tags?|keywords?):\s*(.+)", content, re.IGNORECASE)
    if tags_match:
        tags = [t.strip() for t in tags_match.group(1).split(",")]

    return SkillInfo(
        name=name,
        description=desc[:300],
        tags=tags,
        format="plain",
        path=str(skill_dir),
    )
