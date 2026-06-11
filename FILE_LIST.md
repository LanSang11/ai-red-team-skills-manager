# 文件列表说明

## 📁 项目结构

```
ai-red-team-skills-manager/
├── .gitignore              # Git 忽略文件
├── CHANGELOG.md            # 更新日志
├── CODE_OF_CONDUCT.md      # 行为准则
├── CONTRIBUTING.md         # 贡献指南
├── LICENSE                 # Apache 2.0 许可证
├── README.md               # 项目说明文档
├── SECURITY.md             # 安全政策
├── requirements.txt        # Python 依赖
├── src/                    # 源代码目录
│   ├── main.py             # 主程序入口
│   ├── core/               # 核心模块
│   │   ├── __init__.py     # 模块初始化
│   │   ├── config.py       # 配置管理
│   │   ├── logger.py       # 日志管理
│   │   └── manager.py      # Skills 管理器
│   ├── recommender/        # 推荐系统
│   │   ├── __init__.py     # 模块初始化
│   │   └── recommender.py  # 推荐系统实现
│   ├── installer/          # 安装系统
│   │   └── __init__.py     # 模块初始化
│   ├── syncer/             # 同步系统
│   │   └── __init__.py     # 模块初始化
│   └── auditor/            # 审计系统
│       └── __init__.py     # 模块初始化
├── docs/                   # 文档目录
├── scripts/                # 脚本目录
├── config/                 # 配置目录
└── tests/                  # 测试目录
```

## 📊 文件统计

- **总文件数**: 18
- **总目录数**: 11
- **Python 文件**: 8
- **Markdown 文件**: 6
- **配置文件**: 3
- **其他文件**: 1

## 📝 文件说明

### 核心文件

1. **README.md** - 项目说明文档
   - 项目介绍
   - 痛点分析
   - 功能说明
   - 快速开始
   - 贡献指南

2. **LICENSE** - Apache 2.0 许可证
   - 开源许可证
   - 允许商业使用

3. **requirements.txt** - Python 依赖
   - 核心依赖
   - 安全相关依赖
   - 数据处理依赖
   - 开发工具依赖

### 文档文件

4. **CONTRIBUTING.md** - 贡献指南
   - 如何贡献
   - 代码规范
   - 提交规范
   - 开发环境

5. **CHANGELOG.md** - 更新日志
   - 版本历史
   - 功能更新
   - Bug 修复

6. **SECURITY.md** - 安全政策
   - 漏洞报告
   - 安全更新
   - 安全最佳实践

7. **CODE_OF_CONDUCT.md** - 行为准则
   - 社区规范
   - 行为标准
   - 执行机制

### 源代码文件

8. **src/main.py** - 主程序入口
   - 命令行参数解析
   - 功能调用
   - 错误处理

9. **src/core/config.py** - 配置管理
   - 配置文件读取
   - 配置项管理
   - 默认配置

10. **src/core/logger.py** - 日志管理
    - 日志级别
    - 日志格式
    - 日志输出

11. **src/core/manager.py** - Skills 管理器
    - 状态显示
    - 重复清理
    - Skills 管理

12. **src/recommender/recommender.py** - 推荐系统
    - 用户画像分析
    - 智能推荐
    - 分类推荐

### 模块文件

13. **src/core/__init__.py** - 核心模块初始化
14. **src/recommender/__init__.py** - 推荐系统模块初始化
15. **src/installer/__init__.py** - 安装系统模块初始化
16. **src/syncer/__init__.py** - 同步系统模块初始化
17. **src/auditor/__init__.py** - 审计系统模块初始化

### 配置文件

18. **.gitignore** - Git 忽略文件
    - Python 缓存文件
    - 虚拟环境
    - IDE 配置
    - 日志文件

## 🎯 使用说明

### 1. 查看项目

```bash
cd ai-red-team-skills-manager
```

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

### 3. 运行程序

```bash
python src/main.py
```

### 4. 上传到 GitHub

1. 在 GitHub 上创建新仓库
2. 仓库名称: `ai-red-team-skills-manager`
3. 上传所有文件
4. 设置仓库描述和标签

## 📊 项目亮点

1. **专为红队设计** - 针对红队渗透测试工程师的需求
2. **智能推荐** - 基于用户画像的个性化推荐
3. **自动安装** - 一键安装推荐的 Skills
4. **多 Agent 同步** - 自动同步到所有 Agent
5. **安全审计** - 验证 Skills 的安全性
6. **分层管理** - 共享 Skills + 专属 Skills

## 🏷️ 推荐标签

- `red-team`
- `penetration-testing`
- `ai-agent`
- `security`
- `skills-manager`
- `automation`
