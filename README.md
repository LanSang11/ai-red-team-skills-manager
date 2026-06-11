# 🛡️ AI Red Team Skills Manager

An intelligent Skills management system designed specifically for red team penetration testers. Manage AI Agent Skills across multiple platforms (Claude Code, OpenClaw, Hermes) with ease.

English | [中文](./README_CN.md)

## ✨ Features

| Feature | Description | Status |
|---------|-------------|--------|
| **Status Overview** | View shared repository and Agent Skills status | ✅ |
| **Smart Recommendation** | File system scan + user profile gap analysis | ✅ |
| **Format-Aware Install** | Support OpenClaw/Hermes/Claude Code formats | ✅ |
| **Hash Incremental Sync** | SHA-256 based smart sync, only copy changed files | ✅ |
| **Security Audit** | Prompt injection detection, suspicious file scanning | ✅ |
| **Smart Cleanup** | Safe duplicate Skills cleanup (dry-run + recycle bin) | ✅ |
| **Ecosystem Auto-Detection** | Auto-detect existing Skills config and Agent paths | ✅ |

## 🚀 Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/LanSang11/ai-red-team-skills-manager.git
cd ai-red-team-skills-manager

# Install dependencies
pip install -r requirements.txt
```

### Basic Usage

```bash
# View status
python src/main.py status

# Smart recommendation
python src/main.py recommend

# Install a Skill
python src/main.py install nmap-recon

# Batch install
python src/main.py install-all

# Sync (preview)
python src/main.py sync

# Sync (execute)
python src/main.py sync --no-dry-run

# Security audit
python src/main.py audit

# Clean duplicates (preview)
python src/main.py clean
```

## 📖 Command Details

### `status` - Status Overview

Display shared Skills repository and each Agent's Skills count, path, and format information.

```bash
python src/main.py status
```

### `recommend` - Smart Recommendation

Scan shared repository, compare with each Agent's installed Skills, recommend missing Skills based on user profile.

```bash
python src/main.py recommend                      # All Agents
python src/main.py recommend --agent claude-code   # Specific Agent
python src/main.py recommend --top 10              # Limit count
```

### `install` - Install Skill

Install Skill from shared repository to Agent directory.

```bash
python src/main.py install nmap-recon                    # Install to all Agents
python src/main.py install nmap-recon --agent openclaw   # Install to specific Agent
python src/main.py install nmap-recon --force            # Force overwrite
```

### `sync` - Sync Skills

SHA-256 hash-based incremental sync, only copy changed files.

```bash
python src/main.py sync                                    # Preview sync
python src/main.py sync --no-dry-run                       # Execute sync
python src/main.py sync --source claude-code               # Sync from specific Agent
python src/main.py sync --diff claude-code openclaw        # Compare differences
```

### `audit` - Security Audit

Scan Skills for security threats:

- **Prompt Injection Detection**: Identify `ignore previous instructions` attack patterns
- **Suspicious File Detection**: Flag .exe/.bat/.ps1 executable files
- **Suspicious Link Detection**: Pastebin, free domains, bare IPs
- **Encoded Payload Detection**: Base64 encoded suspicious content
- **Shell Injection Detection**: eval/exec/subprocess dangerous calls

```bash
python src/main.py audit                            # Full audit
python src/main.py audit --target nmap-recon        # Audit specific Skill
python src/main.py audit --verbose                  # Show all levels
python src/main.py audit --integrity                # Integrity check only
```

### `clean` - Clean Duplicates

Clean duplicate Skills in Agent directory (default dry-run mode).

```bash
python src/main.py clean                            # Preview
python src/main.py clean --no-dry-run               # Execute (move to recycle bin)
python src/main.py clean --no-dry-run --no-backup   # Permanent delete
```

## 🤖 Supported Agents

| Agent | Format | Default Path |
|-------|--------|--------------|
| Claude Code | YAML frontmatter | `~/.claude/skills` |
| OpenClaw | OpenClaw metadata | `~/.openclaw/skills` |
| Hermes | YAML frontmatter | `~/.hermes/skills` |

## 📁 Project Structure

```
ai-red-team-skills-manager/
├── src/
│   ├── main.py              # CLI entry point
│   ├── core/
│   │   ├── config.py        # Configuration management (auto-detect ecosystem)
│   │   ├── logger.py        # Logging (loguru singleton)
│   │   ├── context.py       # Application context (singleton)
│   │   ├── skill_parser.py  # Skill format parser
│   │   └── manager.py       # Core manager
│   ├── recommender/
│   │   └── recommender.py   # Smart recommendation engine
│   ├── installer/
│   │   └── installer.py     # Skills installer
│   ├── syncer/
│   │   └── syncer.py        # Skills syncer
│   └── auditor/
│       └── auditor.py       # Security auditor
├── requirements.txt
└── README.md
```

## 🔧 Dependencies

- Python 3.8+
- pyyaml >= 6.0
- rich >= 12.0.0
- loguru >= 0.6.0
- colorama >= 0.4.6
- tabulate >= 0.9.0

## 🛡️ Security Features

- Prompt injection detection
- Suspicious file scanning
- Base64 payload detection
- Shell injection detection
- Integrity verification

## 📄 License

Apache License 2.0

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📧 Contact

GitHub: [LanSang11](https://github.com/LanSang11)

---

**Keywords**: Red Team, Penetration Testing, AI Agent, Skills Management, Claude Code, OpenClaw, Hermes, Security Tools
