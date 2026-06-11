"""Security auditor - scan skills for threats, integrity issues, and policy violations.

Checks:
- Prompt injection patterns in SKILL.md and other text files
- Suspicious file types (.exe, .bat, .ps1, etc.)
- File integrity verification (hash-based)
- Suspicious URL patterns
- Base64-encoded payloads
- Shell command injection patterns
"""

import re
import hashlib
import base64
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from ..core.config import Config
from ..core.logger import get_logger
from ..core.skill_parser import parse_skill


@dataclass
class AuditFinding:
    """A single audit finding."""
    severity: str  # critical, high, medium, low, info
    category: str  # prompt_injection, suspicious_file, integrity, policy
    skill_name: str
    file_path: str
    description: str
    detail: str = ""


@dataclass
class AuditReport:
    """Complete audit report."""
    total_skills: int = 0
    total_files: int = 0
    findings: List[AuditFinding] = field(default_factory=list)

    @property
    def critical_count(self) -> int:
        return sum(1 for f in self.findings if f.severity == "critical")

    @property
    def high_count(self) -> int:
        return sum(1 for f in self.findings if f.severity == "high")

    @property
    def medium_count(self) -> int:
        return sum(1 for f in self.findings if f.severity == "medium")

    @property
    def low_count(self) -> int:
        return sum(1 for f in self.findings if f.severity == "low")

    @property
    def is_clean(self) -> bool:
        return self.critical_count == 0 and self.high_count == 0


# --- Prompt injection patterns ---
PROMPT_INJECTION_PATTERNS = [
    (r"ignore\s+(all\s+)?previous\s+instructions", "忽略先前指令"),
    (r"ignore\s+(all\s+)?above\s+instructions", "忽略上方指令"),
    (r"disregard\s+(all\s+)?prior\s+instructions", "无视先前指令"),
    (r"you\s+are\s+now\s+", "角色切换指令"),
    (r"system\s*:\s*you\s+are", "系统提示注入"),
    (r"act\s+as\s+(?:a\s+)?(?:different|new)", "角色伪装指令"),
    (r"forget\s+(?:everything|all|your)", "记忆清除指令"),
    (r"override\s+(?:your|the)\s+(?:rules|instructions|system)", "规则覆盖指令"),
    (r"<\|system\|>", "系统标记注入"),
    (r"<\|im_start\|>system", "ChatML系统注入"),
    (r"\[INST\]\s*<<SYS>>", "Llama系统注入"),
]

# --- Suspicious URL patterns ---
SUSPICIOUS_URL_PATTERNS = [
    (r"https?://pastebin\.com/", "Pastebin链接"),
    (r"https?://gist\.github\.com/", "GitHub Gist链接"),
    (r"https?://.*\.(?:tk|ml|ga|cf)\b", "免费域名链接"),
    (r"https?://\d+\.\d+\.\d+\.\d+", "裸IP地址链接"),
    (r"https?://.*\.onion\b", "暗网地址"),
]

# --- Shell injection patterns ---
SHELL_INJECTION_PATTERNS = [
    (r"(?:;|\|)\s*(?:rm\s+-rf|mkfs|dd\s+if=)", "危险Shell命令"),
    (r"curl\s+.*\|\s*(?:bash|sh|python)", "远程代码执行"),
    (r"wget\s+.*\|\s*(?:bash|sh|python)", "远程代码执行"),
    (r"eval\s*\(", "eval调用"),
    (r"exec\s*\(", "exec调用"),
    (r"__import__\s*\(", "动态导入"),
    (r"subprocess\.(?:call|Popen|run)\s*\(", "子进程调用"),
    (r"os\.(?:system|popen|exec)\s*\(", "OS命令调用"),
]


class SkillsAuditor:
    """Security auditor for skills repository."""

    def __init__(self, config: Config, console: Console):
        self.config = config
        self.console = console
        self.logger = get_logger()

    def audit(self, target: Optional[str] = None, verbose: bool = False) -> AuditReport:
        """Run a full security audit.

        Args:
            target: Specific skill name or agent name to audit. None for all.
            verbose: Show all findings including info-level.

        Returns:
            AuditReport with all findings.
        """
        self.console.print(Panel.fit("🔍 安全审计", style="bold red"))

        report = AuditReport()

        if target:
            # Audit specific skill or agent
            if self.config.get_agent_skills_path(target):
                self._audit_agent(target, report)
            else:
                self._audit_skill_by_name(target, report)
        else:
            # Audit everything
            self._audit_shared_skills(report)
            for agent_name in self.config.get_enabled_agents():
                self._audit_agent(agent_name, report)

        # Display report
        self._display_report(report, verbose)

        return report

    def audit_integrity(self) -> Dict[str, List[str]]:
        """Check file integrity across shared and agent directories.

        Returns:
            Dict mapping skill_name to list of locations where it differs.
        """
        self.console.print(Panel.fit("🔐 完整性校验", style="bold cyan"))

        shared_path = self.config.get_shared_skills_path()
        categories = self.config.get_skill_categories()

        # Build shared skill hashes
        shared_hashes: Dict[str, str] = {}
        for cat_name in categories:
            cat_path = shared_path / cat_name
            if not cat_path.exists():
                continue
            for skill_dir in cat_path.iterdir():
                if skill_dir.is_dir():
                    shared_hashes[skill_dir.name] = self._dir_hash(skill_dir)

        # Compare with agents
        conflicts: Dict[str, List[str]] = {}
        for agent_name in self.config.get_enabled_agents():
            agent_path = self.config.get_agent_skills_path(agent_name)
            if not agent_path or not agent_path.exists():
                continue

            for skill_dir in agent_path.iterdir():
                if not skill_dir.is_dir() or skill_dir.name.startswith((".", "_")):
                    continue
                if skill_dir.name in shared_hashes:
                    agent_hash = self._dir_hash(skill_dir)
                    if agent_hash != shared_hashes[skill_dir.name]:
                        if skill_dir.name not in conflicts:
                            conflicts[skill_dir.name] = []
                        conflicts[skill_dir.name].append(agent_name)

        if conflicts:
            table = Table(title="完整性冲突")
            table.add_column("Skill", style="cyan")
            table.add_column("冲突的 Agents", style="red")
            for name, agents in conflicts.items():
                table.add_row(name, ", ".join(agents))
            self.console.print(table)
        else:
            self.console.print("[green]✅ 所有 Skills 完整性校验通过[/green]")

        return conflicts

    # --- Internal audit methods ---

    def _audit_shared_skills(self, report: AuditReport):
        """Audit all skills in shared directory."""
        shared_path = self.config.get_shared_skills_path()
        categories = self.config.get_skill_categories()

        for cat_name in categories:
            cat_path = shared_path / cat_name
            if not cat_path.exists():
                continue
            for skill_dir in cat_path.iterdir():
                if skill_dir.is_dir() and not skill_dir.name.startswith((".", "_")):
                    self._audit_skill_dir(skill_dir, skill_dir.name, report)

    def _audit_agent(self, agent_name: str, report: AuditReport):
        """Audit all skills for a specific agent."""
        agent_path = self.config.get_agent_skills_path(agent_name)
        if not agent_path or not agent_path.exists():
            return

        for skill_dir in agent_path.iterdir():
            if skill_dir.is_dir() and not skill_dir.name.startswith((".", "_")):
                self._audit_skill_dir(skill_dir, skill_dir.name, report)

    def _audit_skill_by_name(self, skill_name: str, report: AuditReport):
        """Audit a specific skill by name (search shared + all agents)."""
        shared_path = self.config.get_shared_skills_path()
        categories = self.config.get_skill_categories()

        found = False
        for cat_name in categories:
            skill_dir = shared_path / cat_name / skill_name
            if skill_dir.exists():
                self._audit_skill_dir(skill_dir, skill_name, report)
                found = True

        if not found:
            for agent_name in self.config.get_enabled_agents():
                agent_path = self.config.get_agent_skills_path(agent_name)
                if agent_path:
                    skill_dir = agent_path / skill_name
                    if skill_dir.exists():
                        self._audit_skill_dir(skill_dir, skill_name, report)
                        found = True

        if not found:
            self.console.print(f"[red]未找到 Skill: {skill_name}[/red]")

    def _audit_skill_dir(self, skill_dir: Path, skill_name: str, report: AuditReport):
        """Audit a single skill directory."""
        report.total_skills += 1

        suspicious_exts = self.config.get("audit.suspicious_extensions", [".exe", ".bat", ".ps1"])

        for filepath in skill_dir.rglob("*"):
            if not filepath.is_file():
                continue

            report.total_files += 1
            rel_path = str(filepath.relative_to(skill_dir))

            # Check suspicious file extensions
            if filepath.suffix.lower() in suspicious_exts:
                report.findings.append(AuditFinding(
                    severity="high",
                    category="suspicious_file",
                    skill_name=skill_name,
                    file_path=rel_path,
                    description=f"可疑文件类型: {filepath.suffix}",
                    detail=f"文件: {filepath}",
                ))

            # Check text files for content patterns
            if filepath.suffix.lower() in (".md", ".txt", ".py", ".sh", ".yaml", ".yml", ".json", ".js"):
                try:
                    content = filepath.read_text(encoding="utf-8", errors="ignore")
                    self._check_content_patterns(content, skill_name, rel_path, report)
                except Exception:
                    pass

            # Check for base64-encoded content (potential hidden payloads)
            if filepath.suffix.lower() in (".md", ".txt", ".py"):
                try:
                    content = filepath.read_text(encoding="utf-8", errors="ignore")
                    self._check_base64(content, skill_name, rel_path, report)
                except Exception:
                    pass

    def _check_content_patterns(self, content: str, skill_name: str, file_path: str, report: AuditReport):
        """Check content for various suspicious patterns."""
        content_lower = content.lower()

        # Prompt injection patterns
        for pattern, desc in PROMPT_INJECTION_PATTERNS:
            if re.search(pattern, content_lower):
                report.findings.append(AuditFinding(
                    severity="critical",
                    category="prompt_injection",
                    skill_name=skill_name,
                    file_path=file_path,
                    description=f"疑似 Prompt 注入: {desc}",
                    detail=f"匹配模式: {pattern}",
                ))

        # Suspicious URLs
        for pattern, desc in SUSPICIOUS_URL_PATTERNS:
            matches = re.findall(pattern, content, re.IGNORECASE)
            if matches:
                report.findings.append(AuditFinding(
                    severity="medium",
                    category="suspicious_url",
                    skill_name=skill_name,
                    file_path=file_path,
                    description=f"可疑链接: {desc}",
                    detail=f"URL: {matches[0][:80]}",
                ))

        # Shell injection patterns (only in Python/shell files)
        if file_path.endswith((".py", ".sh")):
            for pattern, desc in SHELL_INJECTION_PATTERNS:
                if re.search(pattern, content):
                    report.findings.append(AuditFinding(
                        severity="medium",
                        category="shell_injection",
                        skill_name=skill_name,
                        file_path=file_path,
                        description=f"可疑代码模式: {desc}",
                        detail=f"匹配模式: {pattern}",
                    ))

    def _check_base64(self, content: str, skill_name: str, file_path: str, report: AuditReport):
        """Check for suspicious base64-encoded content."""
        # Look for long base64 strings (> 100 chars)
        b64_pattern = r"[A-Za-z0-9+/]{100,}={0,2}"
        matches = re.findall(b64_pattern, content)

        for match in matches:
            try:
                decoded = base64.b64decode(match)
                # Check if decoded content looks suspicious
                decoded_str = decoded.decode("utf-8", errors="ignore")
                if any(kw in decoded_str.lower() for kw in ["http", "exec", "eval", "import", "system"]):
                    report.findings.append(AuditFinding(
                        severity="high",
                        category="encoded_payload",
                        skill_name=skill_name,
                        file_path=file_path,
                        description="疑似 Base64 编码的可疑内容",
                        detail=f"解码片段: {decoded_str[:100]}",
                    ))
            except Exception:
                pass

    def _dir_hash(self, dirpath: Path) -> str:
        """Calculate composite hash of all files in a directory."""
        h = hashlib.sha256()
        for filepath in sorted(dirpath.rglob("*")):
            if filepath.is_file():
                h.update(filepath.name.encode())
                try:
                    h.update(filepath.read_bytes())
                except Exception:
                    pass
        return h.hexdigest()

    # --- Display ---

    def _display_report(self, report: AuditReport, verbose: bool):
        """Display the audit report with rich formatting."""
        self.console.print()

        # Summary
        summary_table = Table(title="审计摘要")
        summary_table.add_column("指标", style="cyan")
        summary_table.add_column("数量", style="magenta")
        summary_table.add_row("审计 Skills", str(report.total_skills))
        summary_table.add_row("扫描文件", str(report.total_files))
        summary_table.add_row("[red]严重 (Critical)[/red]", str(report.critical_count))
        summary_table.add_row("[red]高危 (High)[/red]", str(report.high_count))
        summary_table.add_row("[yellow]中危 (Medium)[/yellow]", str(report.medium_count))
        summary_table.add_row("[blue]低危 (Low)[/blue]", str(report.low_count))
        self.console.print(summary_table)

        # Detailed findings
        if not report.findings:
            self.console.print("\n[green]✅ 未发现安全问题[/green]")
            return

        # Filter by severity if not verbose
        findings = report.findings
        if not verbose:
            findings = [f for f in findings if f.severity in ("critical", "high")]

        if not findings:
            self.console.print("\n[green]✅ 未发现高危问题 (使用 --verbose 查看所有)[/green]")
            return

        severity_styles = {
            "critical": "bold red",
            "high": "red",
            "yellow": "yellow",
            "medium": "yellow",
            "low": "blue",
            "info": "dim",
        }

        table = Table(title="详细发现")
        table.add_column("严重度", style="cyan", max_width=10)
        table.add_column("类别", style="yellow", max_width=15)
        table.add_column("Skill", style="green", max_width=20)
        table.add_column("文件", style="dim", max_width=25)
        table.add_column("描述", style="white", max_width=40)

        for f in findings:
            style = severity_styles.get(f.severity, "white")
            table.add_row(
                f"[{style}]{f.severity.upper()}[/{style}]",
                f.category,
                f.skill_name,
                f.file_path,
                f.description,
            )

        self.console.print(table)

        # Verdict
        if report.is_clean:
            self.console.print("\n[green]✅ 安全审计通过[/green]")
        else:
            self.console.print(f"\n[red]⚠ 发现 {report.critical_count + report.high_count} 个高危/严重问题，请立即处理[/red]")
