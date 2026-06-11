# 🛡️ AI Red Team Skills Manager

专为红队渗透测试工程师设计的 AI Agent Skills 智能管理系统。

[English](./README.md) | 中文

## ✨ 核心功能

| 功能 | 说明 | 状态 |
|------|------|------|
| **状态总览** | 查看共享仓库和各 Agent 的 Skills 状态 | ✅ |
| **智能推荐** | 基于文件系统扫描 + 用户画像的差距分析推荐 | ✅ |
| **格式感知安装** | 支持 OpenClaw/Hermes/Claude Code 三种格式 | ✅ |
| **Hash 增量同步** | 基于 SHA-256 的智能同步，仅复制变更文件 | ✅ |
| **安全审计** | Prompt 注入检测、可疑文件扫描、完整性校验 | ✅ |
| **智能清理** | 安全的重复 Skills 清理（dry-run + 回收站） | ✅ |
| **生态系统自动检测** | 自动识别现有 Skills 配置和 Agent 路径 | ✅ |

## 🚀 快速开始

### 安装

```bash
# 克隆仓库
git clone https://github.com/LanSang11/ai-red-team-skills-manager.git
cd ai-red-team-skills-manager

# 安装依赖
pip install -r requirements.txt
```

### 基本使用

```bash
# 查看状态
python src/main.py status

# 智能推荐
python src/main.py recommend

# 安装 Skill
python src/main.py install nmap-recon

# 批量安装
python src/main.py install-all

# 同步 (预览)
python src/main.py sync

# 同步 (执行)
python src/main.py sync --no-dry-run

# 安全审计
python src/main.py audit

# 清理重复 (预览)
python src/main.py clean
```

## 📖 命令详解

### `status` - 状态总览

显示共享 Skills 仓库和各 Agent 的 Skills 数量、路径、格式信息。

```bash
python src/main.py status
```

### `recommend` - 智能推荐

扫描共享仓库，对比各 Agent 已安装的 Skills，基于用户画像推荐缺失的 Skills。

```bash
python src/main.py recommend                      # 所有 Agent
python src/main.py recommend --agent claude-code   # 指定 Agent
python src/main.py recommend --top 10              # 限制数量
```

### `install` - 安装 Skill

从共享仓库安装 Skill 到 Agent 目录。

```bash
python src/main.py install nmap-recon                    # 安装到所有 Agent
python src/main.py install nmap-recon --agent openclaw   # 安装到指定 Agent
python src/main.py install nmap-recon --force            # 强制覆盖
```

### `sync` - 同步 Skills

基于 SHA-256 哈希的增量同步，仅复制变更文件。

```bash
python src/main.py sync                                    # 预览同步
python src/main.py sync --no-dry-run                       # 执行同步
python src/main.py sync --source claude-code               # 从指定 Agent 同步
python src/main.py sync --diff claude-code openclaw        # 对比差异
```

### `audit` - 安全审计

扫描 Skills 中的安全威胁：

- **Prompt 注入检测**: 识别 `ignore previous instructions` 等攻击模式
- **可疑文件检测**: 标记 .exe/.bat/.ps1 等可执行文件
- **可疑链接检测**: Pastebin、免费域名、裸 IP 等
- **编码载荷检测**: Base64 编码的可疑内容
- **Shell 注入检测**: eval/exec/subprocess 等危险调用

```bash
python src/main.py audit                            # 全量审计
python src/main.py audit --target nmap-recon        # 审计指定 Skill
python src/main.py audit --verbose                  # 显示所有级别
python src/main.py audit --integrity                # 仅完整性校验
```

### `clean` - 清理重复

清理 Agent 目录中与共享仓库重复的 Skills（默认 dry-run 模式）。

```bash
python src/main.py clean                            # 预览
python src/main.py clean --no-dry-run               # 执行（移至回收站）
python src/main.py clean --no-dry-run --no-backup   # 永久删除
```

## 🤖 支持的 Agent

| Agent | 格式 | 默认路径 |
|-------|------|----------|
| Claude Code | YAML frontmatter | `~/.claude/skills` |
| OpenClaw | OpenClaw metadata | `~/.openclaw/skills` |
| Hermes | YAML frontmatter | `~/.hermes/skills` |

## 📁 项目结构

```
ai-red-team-skills-manager/
├── src/
│   ├── main.py              # CLI 入口
│   ├── core/
│   │   ├── config.py        # 配置管理（自动检测生态系统）
│   │   ├── logger.py        # 日志（loguru 单例）
│   │   ├── context.py       # 应用上下文（单例）
│   │   ├── skill_parser.py  # Skill 格式解析器
│   │   └── manager.py       # 核心管理器
│   ├── recommender/
│   │   └── recommender.py   # 智能推荐引擎
│   ├── installer/
│   │   └── installer.py     # Skills 安装器
│   ├── syncer/
│   │   └── syncer.py        # Skills 同步器
│   └── auditor/
│       └── auditor.py       # 安全审计器
├── requirements.txt
└── README.md
```

## 🔧 依赖项

- Python 3.8+
- pyyaml >= 6.0
- rich >= 12.0.0
- loguru >= 0.6.0
- colorama >= 0.4.6
- tabulate >= 0.9.0

## 🛡️ 安全特性

- Prompt 注入检测
- 可疑文件扫描
- Base64 载荷检测
- Shell 注入检测
- 完整性校验

## 💡 设计亮点

1. **生态系统自动检测**: 首次运行自动识别现有配置
2. **单例模式**: Config、Logger、Context 全局唯一
3. **格式感知**: 自动处理不同 Agent 的 Skills 格式差异
4. **安全第一**: 内置完整的安全审计机制
5. **用户画像**: 基于兴趣和工具偏好进行智能推荐

## 📄 许可证

Apache License 2.0

## 🤝 贡献

欢迎贡献！请随时提交 Pull Request。

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

## 📧 联系方式

GitHub: [LanSang11](https://github.com/LanSang11)

---

**关键词**: 红队、渗透测试、AI Agent、Skills 管理、Claude Code、OpenClaw、Hermes、安全工具
