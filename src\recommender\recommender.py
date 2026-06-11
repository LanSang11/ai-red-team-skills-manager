"""Intelligent skills recommender - filesystem-based analysis with user profile matching.

Instead of hardcoded lists, this recommender:
1. Scans the actual shared-skills directory
2. Parses skill metadata from SKILL.md files
3. Compares against what each agent already has installed
4. Matches user profile interests
5. Identifies gaps and recommends missing skills
"""

from pathlib import Path
from typing import Dict, List, Any, Optional
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from ..core.config import Config
from ..core.logger import get_logger
from ..core.skill_parser import SkillInfo, parse_skill, infer_category


class SkillsRecommender:
    """Intelligent skills recommender based on filesystem analysis and user profile."""

    def __init__(self, config: Config, console: Console):
        self.config = config
        self.console = console
        self.logger = get_logger()

    def recommend(self, agent_name: Optional[str] = None, top_n: int = 0):
        """Show intelligent recommendations.

        Args:
            agent_name: Specific agent to recommend for. None for all agents.
            top_n: Limit recommendations per category. 0 for all.
        """
        self.console.print(Panel.fit("💡 智能 Skills 推荐", style="bold green"))

        # Get user profile for interest matching
        profile = self.config.get_user_profile()
        user_interests = set()
        if profile:
            for field in ("primary_directions", "common_tools", "tags"):
                items = profile.get(field, [])
                if isinstance(items, list):
                    user_interests.update(str(i).lower() for i in items)

        # Discover all shared skills
        shared_skills = self._discover_shared_skills()
        if not shared_skills:
            self.console.print("[yellow]未发现共享 Skills。请检查共享 Skills 目录。[/yellow]")
            return

        # Determine which agents to analyze
        if agent_name:
            agents = {agent_name: self.config.get_agents().get(agent_name, {})}
        else:
            agents = self.config.get_enabled_agents()

        # For each agent, find gaps
        for aname, ainfo in agents.items():
            self.console.print(f"\n[bold cyan]📋 Agent: {aname}[/bold cyan]")

            agent_skills = self._get_agent_skill_names(aname)
            missing = [
                s for s in shared_skills
                if s.name not in agent_skills
            ]

            if not missing:
                self.console.print(f"  [green]✅ {aname} 已安装所有共享 Skills[/green]")
                continue

            # Score and sort by relevance
            scored = self._score_skills(missing, user_interests)
            if top_n > 0:
                scored = scored[:top_n]

            # Display by category
            self._display_recommendations(aname, scored)

    def get_gap_analysis(self) -> Dict[str, List[str]]:
        """Get a gap analysis showing which skills each agent is missing.

        Returns:
            Dict mapping agent_name -> list of missing skill names.
        """
        shared_skills = self._discover_shared_skills()
        shared_names = {s.name for s in shared_skills}

        gaps = {}
        for agent_name in self.config.get_enabled_agents():
            agent_skills = self._get_agent_skill_names(agent_name)
            missing = sorted(shared_names - agent_skills)
            if missing:
                gaps[agent_name] = missing

        return gaps

    def get_recommendations_by_category(self, category: str) -> List[SkillInfo]:
        """Get all skills in a specific category."""
        shared_skills = self._discover_shared_skills()
        return [s for s in shared_skills if s.category == category]

    # --- Internal methods ---

    def _discover_shared_skills(self) -> List[SkillInfo]:
        """Discover all skills in shared directory."""
        shared_path = self.config.get_shared_skills_path()
        categories = self.config.get_skill_categories()
        skills = []

        if not shared_path.exists():
            return skills

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
                    skills.append(SkillInfo(
                        name=skill_dir.name,
                        category=cat_name,
                        path=str(skill_dir),
                    ))

        return skills

    def _get_agent_skill_names(self, agent_name: str) -> set:
        """Get set of skill names installed for an agent."""
        agent_path = self.config.get_agent_skills_path(agent_name)
        if not agent_path or not agent_path.exists():
            return set()
        return {
            d.name for d in agent_path.iterdir()
            if d.is_dir() and not d.name.startswith((".", "_"))
        }

    def _score_skills(self, skills: List[SkillInfo], user_interests: set) -> List[tuple]:
        """Score skills by relevance to user interests. Returns sorted list of (score, skill)."""
        scored = []
        for skill in skills:
            score = 0
            text = f"{skill.name} {skill.description} {' '.join(skill.tags)}".lower()

            # Score based on user interest keyword matching
            for interest in user_interests:
                if interest in text:
                    score += 2

            # Boost security skills (red team context)
            if skill.category == "security":
                score += 3
            elif skill.category == "recon":
                score += 1

            # Boost skills with more metadata (more complete)
            if skill.description:
                score += 1
            if skill.tags:
                score += 1
            if skill.version:
                score += 1

            scored.append((score, skill))

        scored.sort(key=lambda x: x[0], reverse=True)
        return [(s, sk) for s, sk in scored]

    def _display_recommendations(self, agent_name: str, scored_skills: List[tuple]):
        """Display recommendations grouped by category."""
        # Group by category
        by_category: Dict[str, List[tuple]] = {}
        for score, skill in scored_skills:
            cat = skill.category
            if cat not in by_category:
                by_category[cat] = []
            by_category[cat].append((score, skill))

        category_styles = {
            "security": ("bold red", "🔴"),
            "recon": ("bold cyan", "🔵"),
            "tools": ("bold green", "🟢"),
        }

        for cat_name, items in by_category.items():
            style, icon = category_styles.get(cat_name, ("bold white", "⚪"))

            table = Table(title=f"{icon} {cat_name.upper()} 类 ({len(items)} 个)")
            table.add_column("Skill", style="cyan", max_width=30)
            table.add_column("描述", style="white", max_width=50)
            table.add_column("格式", style="yellow", max_width=10)
            table.add_column("相关度", style="magenta", max_width=8)

            for score, skill in items:
                relevance = "⭐" * min(score, 5) if score > 0 else "-"
                desc = skill.description[:47] + "..." if len(skill.description) > 50 else skill.description
                table.add_row(skill.name, desc or "-", skill.format, relevance)

            self.console.print(table)
