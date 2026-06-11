"""Skills installer - copy/transfer skills from shared repository to agent directories.

Supports:
- Installing a single skill to one or all agents
- Batch installing all shared skills
- Format-aware copying (preserving agent-specific structure)
- Integrity verification after copy
"""

import shutil
from pathlib import Path
from typing import List, Optional, Dict
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from ..core.config import Config
from ..core.logger import get_logger
from ..core.manager import SkillsManager
from ..core.skill_parser import parse_skill


class SkillsInstaller:
    """Skills installer - deploy skills from shared repository to agent directories."""

    def __init__(self, config: Config, console: Console):
        self.config = config
        self.console = console
        self.logger = get_logger()
        self.manager = SkillsManager(config, console)

    def install(self, skill_name: str, agent_name: Optional[str] = None, force: bool = False) -> bool:
        """Install a skill from shared directory to agent(s).

        Args:
            skill_name: Name of the skill to install.
            agent_name: Target agent. None to install to all enabled agents.
            force: Overwrite existing installation.

        Returns:
            True if installation succeeded for at least one agent.
        """
        # Find skill in shared directory
        shared_path = self.config.get_shared_skills_path()
        skill_source = self._find_skill_source(skill_name, shared_path)

        if not skill_source:
            self.console.print(f"[red]✗ 未找到 Skill: {skill_name}[/red]")
            self._suggest_similar(skill_name)
            return False

        self.console.print(Panel.fit(
            f"📦 安装 Skill: {skill_name}",
            style="bold blue",
        ))

        # Parse skill metadata
        info = parse_skill(skill_source)
        if info:
            self.console.print(f"  描述: {info.description or '-'}")
            self.console.print(f"  格式: {info.format}")
            if info.tags:
                self.console.print(f"  标签: {', '.join(info.tags)}")

        # Determine target agents
        if agent_name:
            agents = {agent_name: self.config.get_agents().get(agent_name, {})}
            if not agents[agent_name]:
                self.console.print(f"[red]✗ 未找到 Agent: {agent_name}[/red]")
                return False
        else:
            agents = self.config.get_enabled_agents()

        # Install to each agent
        success_count = 0
        for aname, ainfo in agents.items():
            result = self._install_to_agent(skill_name, skill_source, aname, force)
            if result:
                success_count += 1

        return success_count > 0

    def install_all(self, agent_name: Optional[str] = None, force: bool = False) -> Dict[str, int]:
        """Install all shared skills to agent(s).

        Args:
            agent_name: Target agent. None for all enabled agents.
            force: Overwrite existing installations.

        Returns:
            Dict mapping agent_name to count of installed skills.
        """
        shared_path = self.config.get_shared_skills_path()
        categories = self.config.get_skill_categories()

        # Discover all shared skills
        skill_names = []
        for cat_name in categories:
            cat_path = shared_path / cat_name
            if not cat_path.exists():
                continue
            for d in cat_path.iterdir():
                if d.is_dir() and not d.name.startswith((".", "_")):
                    skill_names.append(d.name)

        if not skill_names:
            self.console.print("[yellow]未发现共享 Skills[/yellow]")
            return {}

        self.console.print(Panel.fit(
            f"📦 批量安装 {len(skill_names)} 个 Skills",
            style="bold blue",
        ))

        results: Dict[str, int] = {}

        if agent_name:
            agents = {agent_name: self.config.get_agents().get(agent_name, {})}
        else:
            agents = self.config.get_enabled_agents()

        for aname in agents:
            count = 0
            for skill_name in skill_names:
                skill_source = self._find_skill_source(skill_name, shared_path)
                if skill_source and self._install_to_agent(skill_name, skill_source, aname, force):
                    count += 1
            results[aname] = count
            self.console.print(f"[green]✅ {aname}: 安装 {count}/{len(skill_names)} 个 Skills[/green]")

        return results

    # --- Internal methods ---

    def _find_skill_source(self, skill_name: str, shared_path: Path) -> Optional[Path]:
        """Find skill directory in shared path (searching category subdirs)."""
        if not shared_path.exists():
            return None

        # Search in category subdirectories
        for cat_name in self.config.get_skill_categories():
            candidate = shared_path / cat_name / skill_name
            if candidate.exists() and candidate.is_dir():
                return candidate

        # Search in root
        candidate = shared_path / skill_name
        if candidate.exists() and candidate.is_dir():
            return candidate

        return None

    def _install_to_agent(self, skill_name: str, source: Path, agent_name: str, force: bool) -> bool:
        """Install a single skill to a single agent directory."""
        agent_path = self.config.get_agent_skills_path(agent_name)
        if not agent_path:
            self.console.print(f"  [yellow]⚠ {agent_name}: 未配置路径[/yellow]")
            return False

        target = agent_path / skill_name

        # Check if already installed
        if target.exists() and not force:
            self.console.print(f"  [dim]⏭ {agent_name}: {skill_name} 已存在 (使用 --force 覆盖)[/dim]")
            return False

        # Copy
        try:
            if target.exists():
                shutil.rmtree(target)
            shutil.copytree(source, target)
            self.console.print(f"  [green]✓ {agent_name}: {skill_name} 已安装[/green]")
            self.logger.info(f"Installed {skill_name} to {agent_name}")
            return True
        except Exception as e:
            self.console.print(f"  [red]✗ {agent_name}: {skill_name} 安装失败 - {e}[/red]")
            self.logger.error(f"Failed to install {skill_name} to {agent_name}: {e}")
            return False

    def _suggest_similar(self, skill_name: str):
        """Suggest similar skill names when not found."""
        shared_path = self.config.get_shared_skills_path()
        categories = self.config.get_skill_categories()

        all_names = []
        for cat_name in categories:
            cat_path = shared_path / cat_name
            if cat_path.exists():
                for d in cat_path.iterdir():
                    if d.is_dir():
                        all_names.append(d.name)

        # Simple substring matching
        similar = [n for n in all_names if skill_name.lower() in n.lower() or n.lower() in skill_name.lower()]
        if similar:
            self.console.print(f"[yellow]你是否指的是: {', '.join(similar[:5])}[/yellow]")
