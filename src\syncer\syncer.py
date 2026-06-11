"""Skills syncer - synchronize skills across agents using hash-based incremental sync.

Features:
- Hash-based comparison (only copy changed files)
- Bidirectional sync support
- Dry-run mode
- Cross-agent sync directory management
"""

import shutil
import hashlib
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from ..core.config import Config
from ..core.logger import get_logger
from ..core.manager import SkillsManager


class SkillsSyncer:
    """Skills syncer - keep skills consistent across all agents."""

    def __init__(self, config: Config, console: Console):
        self.config = config
        self.console = console
        self.logger = get_logger()
        self.manager = SkillsManager(config, console)

    def sync_all(self, dry_run: bool = True, source_agent: Optional[str] = None) -> Dict[str, int]:
        """Synchronize skills across all agents.

        Strategy: Use shared-skills as the source of truth.
        For each agent, ensure all shared skills are present and up-to-date.

        Args:
            dry_run: If True, only show what would be synced.
            source_agent: Use this agent as source instead of shared-skills.

        Returns:
            Dict mapping agent_name to count of synced skills.
        """
        mode_str = "[DRY RUN]" if dry_run else "[LIVE]"
        self.console.print(Panel.fit(
            f"🔄 同步 Skills {mode_str}",
            style="bold yellow" if dry_run else "bold green",
        ))

        # Determine source
        if source_agent:
            source_path = self.config.get_agent_skills_path(source_agent)
            if not source_path or not source_path.exists():
                self.console.print(f"[red]✗ 源 Agent 不存在: {source_agent}[/red]")
                return {}
            source_name = source_agent
        else:
            source_path = self.config.get_shared_skills_path()
            source_name = "shared"

        if not source_path or not source_path.exists():
            self.console.print(f"[red]✗ 源目录不存在: {source_path}[/red]")
            return {}

        # Build source skill index (name -> path, hash)
        source_index = self._build_skill_index(source_path)
        self.console.print(f"源 ({source_name}): {len(source_index)} 个 Skills")

        results: Dict[str, int] = {}

        for agent_name, agent_info in self.config.get_enabled_agents().items():
            if source_agent and agent_name == source_agent:
                continue

            agent_path = self.config.get_agent_skills_path(agent_name)
            if not agent_path:
                continue

            agent_index = self._build_skill_index(agent_path) if agent_path.exists() else {}

            synced = 0
            for skill_name, (skill_path, skill_hash) in source_index.items():
                if skill_name in agent_index:
                    _, agent_hash = agent_index[skill_name]
                    if agent_hash == skill_hash:
                        continue  # Already up to date

                # Need to sync
                if dry_run:
                    status = "更新" if skill_name in agent_index else "新增"
                    self.console.print(f"  [yellow]⚠ {agent_name}: {status} {skill_name}[/yellow]")
                else:
                    target = agent_path / skill_name
                    try:
                        if target.exists():
                            shutil.rmtree(target)
                        shutil.copytree(skill_path, target)
                        self.console.print(f"  [green]✓ {agent_name}: 同步 {skill_name}[/green]")
                    except Exception as e:
                        self.console.print(f"  [red]✗ {agent_name}: {skill_name} 失败 - {e}[/red]")
                        self.logger.error(f"Sync failed {agent_name}/{skill_name}: {e}")
                        continue

                synced += 1

            if synced > 0:
                results[agent_name] = synced
                self.console.print(
                    f"[{'yellow' if dry_run else 'green'}]"
                    f"✅ {agent_name}: {synced} 个 Skills 需要同步"
                    f"[/{'yellow' if dry_run else 'green'}]"
                )
            else:
                self.console.print(f"[dim]  ✓ {agent_name}: 已是最新[/dim]")

        if dry_run and results:
            self.console.print("\n[yellow]这是 DRY RUN 模式，未实际同步。使用 --no-dry-run 执行同步。[/yellow]")

        return results

    def sync_agent_to_shared(self, agent_name: str, dry_run: bool = True) -> int:
        """Sync an agent's unique skills back to shared directory.

        This is useful when you've created/modified skills in an agent
        and want to promote them to the shared repository.

        Args:
            agent_name: Source agent name.
            dry_run: If True, only show what would be synced.

        Returns:
            Count of skills synced.
        """
        agent_path = self.config.get_agent_skills_path(agent_name)
        if not agent_path or not agent_path.exists():
            self.console.print(f"[red]✗ Agent 目录不存在: {agent_name}[/red]")
            return 0

        shared_path = self.config.get_shared_skills_path()
        categories = self.config.get_skill_categories()

        # Build shared skill set
        shared_names: Set[str] = set()
        for cat_name in categories:
            cat_path = shared_path / cat_name
            if cat_path.exists():
                for d in cat_path.iterdir():
                    if d.is_dir():
                        shared_names.add(d.name)

        # Find agent-only skills
        agent_index = self._build_skill_index(agent_path)
        unique = {name: (path, h) for name, (path, h) in agent_index.items() if name not in shared_names}

        if not unique:
            self.console.print(f"[green]✅ {agent_name} 没有独有的 Skills 需要同步[/green]")
            return 0

        self.console.print(f"[bold]{agent_name} 独有 Skills: {len(unique)}[/bold]")

        synced = 0
        for skill_name, (skill_path, _) in unique.items():
            # Default to "tools" category for unknown skills
            target = shared_path / "tools" / skill_name
            if dry_run:
                self.console.print(f"  [yellow]⚠ 将同步 {skill_name} -> shared/tools/[/yellow]")
            else:
                try:
                    if target.exists():
                        shutil.rmtree(target)
                    shutil.copytree(skill_path, target)
                    self.console.print(f"  [green]✓ 同步 {skill_name} -> shared/tools/[/green]")
                except Exception as e:
                    self.console.print(f"  [red]✗ {skill_name} 同步失败 - {e}[/red]")
                    continue
            synced += 1

        return synced

    def show_diff(self, agent1: str, agent2: str):
        """Show skill differences between two agents."""
        path1 = self.config.get_agent_skills_path(agent1)
        path2 = self.config.get_agent_skills_path(agent2)

        index1 = self._build_skill_index(path1) if path1 and path1.exists() else {}
        index2 = self._build_skill_index(path2) if path2 and path2.exists() else {}

        names1 = set(index1.keys())
        names2 = set(index2.keys())

        only1 = sorted(names1 - names2)
        only2 = sorted(names2 - names1)
        common = sorted(names1 & names2)

        # Check for content differences in common skills
        changed = []
        for name in common:
            _, h1 = index1[name]
            _, h2 = index2[name]
            if h1 != h2:
                changed.append(name)

        # Display
        self.console.print(Panel.fit(f"📊 {agent1} vs {agent2} 差异分析", style="bold blue"))

        table = Table(title="差异概览")
        table.add_column("类型", style="cyan")
        table.add_column("数量", style="magenta")

        table.add_row(f"仅 {agent1}", str(len(only1)))
        table.add_row(f"仅 {agent2}", str(len(only2)))
        table.add_row("内容不同", str(len(changed)))
        table.add_row("完全相同", str(len(common) - len(changed)))
        self.console.print(table)

        if only1:
            self.console.print(f"\n[bold cyan]仅在 {agent1}:[/bold cyan]")
            for name in only1:
                self.console.print(f"  • {name}")

        if only2:
            self.console.print(f"\n[bold cyan]仅在 {agent2}:[/bold cyan]")
            for name in only2:
                self.console.print(f"  • {name}")

        if changed:
            self.console.print(f"\n[bold yellow]内容不同:[/bold yellow]")
            for name in changed:
                self.console.print(f"  • {name}")

    # --- Internal methods ---

    def _build_skill_index(self, base_path: Path) -> Dict[str, Tuple[Path, str]]:
        """Build an index of skills: name -> (path, hash).

        Only indexes top-level directories (not nested category dirs).
        """
        index: Dict[str, Tuple[Path, str]] = {}

        if not base_path.exists():
            return index

        for item in base_path.iterdir():
            if not item.is_dir() or item.name.startswith((".", "_")):
                continue

            # Skip category directories if they contain sub-skills
            categories = self.config.get_skill_categories()
            if item.name in categories:
                # Index skills inside category dirs
                for sub in item.iterdir():
                    if sub.is_dir() and not sub.name.startswith((".", "_")):
                        h = self.manager.dir_hash(sub)
                        index[sub.name] = (sub, h)
            else:
                h = self.manager.dir_hash(item)
                index[item.name] = (item, h)

        return index
