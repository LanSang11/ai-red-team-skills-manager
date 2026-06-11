#!/usr/bin/env python3
"""AI Red Team Skills Manager - CLI entry point.

专为红队渗透测试工程师设计的 AI Agent Skills 智能管理系统。
支持多 Agent (Claude Code, OpenClaw, Hermes) 的 Skills 统一管理。
"""

import sys
import os
import argparse
from pathlib import Path

# Force UTF-8 on Windows to support emoji and unicode
if sys.platform == "win32":
    os.system("chcp 65001 >nul 2>&1")
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.core.config import Config
from src.core.context import AppContext
from src.core.manager import SkillsManager
from src.recommender.recommender import SkillsRecommender
from src.installer.installer import SkillsInstaller
from src.syncer.syncer import SkillsSyncer
from src.auditor.auditor import SkillsAuditor


def build_parser() -> argparse.ArgumentParser:
    """Build the CLI argument parser."""
    parser = argparse.ArgumentParser(
        prog="skills-manager",
        description="AI Red Team Skills Manager - 智能 Skills 管理系统",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""\
示例:
  %(prog)s status                        # 查看 Skills 状态
  %(prog)s recommend                     # 智能推荐 (所有 Agent)
  %(prog)s recommend --agent openclaw    # 推荐给指定 Agent
  %(prog)s install nmap-recon            # 安装指定 Skill
  %(prog)s install nmap-recon --agent claude-code
  %(prog)s install-all                   # 批量安装所有共享 Skills
  %(prog)s sync                          # 同步 (dry-run)
  %(prog)s sync --no-dry-run             # 执行实际同步
  %(prog)s sync --diff claude-code openclaw  # 对比两个 Agent
  %(prog)s audit                         # 安全审计
  %(prog)s audit --target nmap-recon     # 审计指定 Skill
  %(prog)s clean                         # 清理重复 (dry-run)
  %(prog)s clean --no-dry-run            # 执行实际清理
""",
    )

    subparsers = parser.add_subparsers(dest="command", help="可用命令")

    # status
    subparsers.add_parser("status", help="查看 Skills 状态")

    # recommend
    p = subparsers.add_parser("recommend", help="智能推荐 Skills")
    p.add_argument("--agent", "-a", help="指定目标 Agent")
    p.add_argument("--top", "-n", type=int, default=0, help="限制推荐数量")

    # install
    p = subparsers.add_parser("install", help="安装指定 Skill")
    p.add_argument("skill_name", help="Skill 名称")
    p.add_argument("--agent", "-a", help="目标 Agent (默认所有)")
    p.add_argument("--force", "-f", action="store_true", help="强制覆盖已存在的 Skill")

    # install-all
    p = subparsers.add_parser("install-all", help="批量安装所有共享 Skills")
    p.add_argument("--agent", "-a", help="目标 Agent (默认所有)")
    p.add_argument("--force", "-f", action="store_true", help="强制覆盖")

    # sync
    p = subparsers.add_parser("sync", help="同步 Skills 到所有 Agent")
    p.add_argument("--no-dry-run", action="store_true", help="执行实际同步 (默认仅预览)")
    p.add_argument("--source", "-s", help="使用指定 Agent 作为源 (默认共享目录)")
    p.add_argument("--diff", nargs=2, metavar=("AGENT1", "AGENT2"), help="对比两个 Agent 的差异")

    # audit
    p = subparsers.add_parser("audit", help="安全审计")
    p.add_argument("--target", "-t", help="审计指定 Skill 或 Agent")
    p.add_argument("--verbose", "-v", action="store_true", help="显示所有级别 (含低危)")
    p.add_argument("--integrity", action="store_true", help="仅执行完整性校验")

    # clean
    p = subparsers.add_parser("clean", help="清理重复 Skills")
    p.add_argument("--no-dry-run", action="store_true", help="执行实际删除")
    p.add_argument("--no-backup", action="store_true", help="永久删除 (不移至回收站)")

    return parser


def main():
    """Main entry point."""
    parser = build_parser()
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    # Initialize shared context (singleton)
    ctx = AppContext()
    config = ctx.config
    console = ctx.console

    # Create shared manager
    manager = SkillsManager(config, console)

    if args.command == "status":
        manager.show_status()

    elif args.command == "recommend":
        recommender = SkillsRecommender(config, console)
        recommender.recommend(agent_name=args.agent, top_n=args.top)

    elif args.command == "install":
        installer = SkillsInstaller(config, console)
        installer.install(args.skill_name, agent_name=args.agent, force=args.force)

    elif args.command == "install-all":
        installer = SkillsInstaller(config, console)
        installer.install_all(agent_name=args.agent, force=args.force)

    elif args.command == "sync":
        syncer = SkillsSyncer(config, console)
        if args.diff:
            syncer.show_diff(args.diff[0], args.diff[1])
        else:
            dry_run = not args.no_dry_run
            syncer.sync_all(dry_run=dry_run, source_agent=args.source)

    elif args.command == "audit":
        auditor = SkillsAuditor(config, console)
        if args.integrity:
            auditor.audit_integrity()
        else:
            auditor.audit(target=args.target, verbose=args.verbose)

    elif args.command == "clean":
        dry_run = not args.no_dry_run
        backup = not args.no_backup
        manager.clean_duplicates(dry_run=dry_run, backup=backup)


if __name__ == "__main__":
    main()
