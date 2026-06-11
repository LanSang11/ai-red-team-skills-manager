"""Skills manager - core operations on the skills filesystem."""

import os
import shutil
import hashlib
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from .config import Config
from .logger import get_logger
from .skill_parser import SkillInfo, parse_skill, infer_category


class SkillsManager:
    """Core skills manager - status, discovery, cleanup."""

    def __init__(self, config: Config, console: Console):
        self.config = config
        self.console = console
        self.logger = get_logger()

    # --- Status & Display ---

    def show_status(self):
        """Display comprehensive skills status with rich tables."""
        self.console.print(Panel.fit("📊 AI Red Team Skills Manager 状态", style="bold blue"))

        # Shared skills status
        shared_path = self.config.get_shared_skills_path()
        categories = self.config.get_skill_categories()

        if shared_path.exists():
            table = Table(title="共享 Skills 仓库")
            table.add_column("类别", style="cyan")
            table.add_column("数量", style="magenta")
            table.add_column("路径", style="green")

            total = 0
            for cat_name in categories:
                cat_path = shared_path / cat_name
                if cat_path.exists():
                    count = len([d for d in cat_path.iterdir() if d.is_dir()])
                else:
                    count = 0
                total += count
                table.add_row(cat_name, str(count), str(cat_path))

            # Also count skills in root of shared_path (uncategorized)
            root_skills = 0
            if shared_path.exists():
                root_skills = len([
                    d for d in shared_path.iterdir()
                    if d.is_dir() and not d.name.startswith(("_", ".")) and d.name not in categories
                ])
                total += root_skills

            table.add_row("[bold]总计[/bold]", str(total), "")
            self.console.print(table)
        else:
            self.console.print(f"[red]⚠ 共享 Skills 目录不存在: {shared_path}[/red]")

        # Agent status
        self.console.print()
        table = Table(title="各 Agent Skills 状态")
        table.add_column("Agent", style="cyan")
        table.add_column("格式", style="yellow")
        table.add_column("Skills 数量", style="magenta")
        table.add_column("状态", style="green")
        table.add_column("路径", style="dim")

        for agent_name, agent_info in self.config.get_enabled_agents().items():
            agent_path = self.config.get_agent_skills_path(agent_name)
            fmt = agent_info.get("format", "unknown")

            if agent_path and agent_path.exists():
                count = len([d for d in agent_path.iterdir() if d.is_dir()])
                status = "[green]✓ 已配置[/green]"
            else:
                count = 0
                status = "[red]✗ 不存在[/red]"

            table.add_row(agent_name, fmt, str(count), status, str(agent_path or "N/A"))

        self.console.print(table)

        # Cross-agent sync directories
        self._show_sync_dirs(shared_path)

    def _show_sync_dirs(self, shared_path: Path):
        """Show cross-agent sync directories if they exist."""
        parent = shared_path.parent if shared_path.name == "shared-skills" else shared_path
        agents = list(self.config.get_enabled_agents().keys())

        sync_dirs = []
        for d in parent.iterdir():
            if d.is_dir() and not d.name.startswith(("_", ".")):
                # Check if dir name is a combination of agent names
                for a1 in agents:
                    for a2 in agents:
                        if a1 != a2 and d.name == f"{a1.replace('-', '_')}{a2.replace('-', '_')}":
                            count = len([x for x in d.iterdir() if x.is_dir()])
                            sync_dirs.append((d.name, count, str(d)))
                        # Also check with hyphens
                        if a1 != a2 and d.name == f"{a1}{a2}":
                            count = len([x for x in d.iterdir() if x.is_dir()])
                            sync_dirs.append((d.name, count, str(d)))

        if sync_dirs:
            self.console.print()
            table = Table(title="跨 Agent 同步目录")
            table.add_column("目录", style="cyan")
            table.add_column("Skills 数量", style="magenta")
            table.add_column("路径", style="dim")
            for name, count, path in sync_dirs:
                table.add_row(name, str(count), path)
            self.console.print(table)

    # --- Discovery ---

    def get_all_skills(self) -> List[SkillInfo]:
        """Discover all skills in shared directory with full metadata parsing."""
        shared_path = self.config.get_shared_skills_path()
        categories = self.config.get_skill_categories()
        skills = []

        if not shared_path.exists():
            return skills

        # Scan category subdirectories
        for cat_name in categories:
            cat_path = shared_path / cat_name
            if not cat_path.exists():
                continue
            for skill_dir in cat_path.iterdir():
                if not skill_dir.is_dir() or skill_dir.name.startswith((".", "_")):
                    continue
                info = parse_skill(skill_dir)
                if info:
                    info.category = cat_name
                    skills.append(info)
                else:
                    # Directory without SKILL.md - still track it
                    skills.append(SkillInfo(
                        name=skill_dir.name,
                        category=cat_name,
                        path=str(skill_dir),
                        format="unknown",
                    ))

        # Scan uncategorized skills in root
        for skill_dir in shared_path.iterdir():
            if not skill_dir.is_dir() or skill_dir.name.startswith((".", "_")):
                continue
            if skill_dir.name in categories:
                continue
            info = parse_skill(skill_dir)
            if info:
                info.category = infer_category(info, categories)
                skills.append(info)

        return skills

    def get_agent_skills(self, agent_name: str) -> List[SkillInfo]:
        """Discover all skills for a specific agent."""
        agent_path = self.config.get_agent_skills_path(agent_name)
        skills = []

        if not agent_path or not agent_path.exists():
            return skills

        for skill_dir in agent_path.iterdir():
            if not skill_dir.is_dir() or skill_dir.name.startswith((".", "_")):
                continue
            info = parse_skill(skill_dir)
            if info:
                skills.append(info)
            else:
                skills.append(SkillInfo(
                    name=skill_dir.name,
                    path=str(skill_dir),
                    format="unknown",
                ))

        return skills

    def skill_exists(self, skill_name: str) -> bool:
        """Check if a skill exists in shared directory."""
        shared_path = self.config.get_shared_skills_path()
        if not shared_path.exists():
            return False

        for cat_name in self.config.get_skill_categories():
            if (shared_path / cat_name / skill_name).exists():
                return True
        if (shared_path / skill_name).exists():
            return True
        return False

    def get_skill_category(self, skill_name: str) -> Optional[str]:
        """Get the category of a skill in shared directory."""
        shared_path = self.config.get_shared_skills_path()
        if not shared_path.exists():
            return None

        for cat_name in self.config.get_skill_categories():
            if (shared_path / cat_name / skill_name).exists():
                return cat_name
        return None

    # --- Cleanup ---

    def clean_duplicates(self, dry_run: bool = True, backup: bool = True) -> Dict[str, int]:
        """Clean duplicate skills from agent directories (skills that exist in shared).

        Args:
            dry_run: If True, only show what would be deleted without actually deleting.
            backup: If True, move to trash instead of permanent delete.

        Returns:
            Dict mapping agent_name to count of cleaned skills.
        """
        self.console.print(Panel.fit(
            f"🧹 清理重复 Skills {'[DRY RUN]' if dry_run else '[LIVE]'}",
            style="bold yellow" if dry_run else "bold red",
        ))

        shared_path = self.config.get_shared_skills_path()
        if not shared_path.exists():
            self.console.print("[red]共享 Skills 目录不存在[/red]")
            return {}

        # Build set of shared skill names
        shared_skills = set()
        for cat_name in self.config.get_skill_categories():
            cat_path = shared_path / cat_name
            if cat_path.exists():
                for d in cat_path.iterdir():
                    if d.is_dir():
                        shared_skills.add(d.name)

        self.console.print(f"共享 Skills 总数: {len(shared_skills)}")

        results: Dict[str, int] = {}

        for agent_name in self.config.get_enabled_agents():
            agent_path = self.config.get_agent_skills_path(agent_name)
            if not agent_path or not agent_path.exists():
                continue

            cleaned = 0
            for skill_name in shared_skills:
                skill_path = agent_path / skill_name
                if not skill_path.exists():
                    continue

                if dry_run:
                    self.console.print(f"  [yellow]⚠ 将删除[/yellow] {agent_name}: {skill_name}")
                    cleaned += 1
                else:
                    try:
                        if backup:
                            trash_dir = agent_path / ".trash"
                            trash_dir.mkdir(exist_ok=True)
                            shutil.move(str(skill_path), str(trash_dir / skill_name))
                            self.console.print(f"  [yellow]📦 移至回收站[/yellow] {agent_name}: {skill_name}")
                        else:
                            shutil.rmtree(skill_path)
                            self.console.print(f"  [red]✗ 删除[/red] {agent_name}: {skill_name}")
                        cleaned += 1
                    except Exception as e:
                        self.console.print(f"  [red]✗ 删除失败[/red] {agent_name}: {skill_name} - {e}")
                        self.logger.error(f"Failed to clean {agent_name}/{skill_name}: {e}")

            if cleaned > 0:
                results[agent_name] = cleaned
                self.console.print(f"[green]✅ {agent_name}: {cleaned} 个重复 Skills[/green]")

        if dry_run and results:
            self.console.print("\n[yellow]这是 DRY RUN 模式，未实际删除。使用 --no-dry-run 执行删除。[/yellow]")

        return results

    # --- Utility ---

    @staticmethod
    def file_hash(filepath: Path) -> str:
        """Calculate SHA-256 hash of a file."""
        h = hashlib.sha256()
        with open(filepath, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                h.update(chunk)
        return h.hexdigest()

    @staticmethod
    def dir_hash(dirpath: Path) -> str:
        """Calculate a composite hash of all files in a directory."""
        h = hashlib.sha256()
        for filepath in sorted(dirpath.rglob("*")):
            if filepath.is_file():
                h.update(filepath.name.encode())
                h.update(SkillsManager.file_hash(filepath).encode())
        return h.hexdigest()
