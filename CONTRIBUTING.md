# 贡献指南

感谢您对 AI Red Team Skills Manager 项目的关注！我们欢迎所有形式的贡献。

## 如何贡献

### 1. 提交 Bug 报告

如果您发现了 Bug，请通过 GitHub Issues 提交报告，并包含以下信息：

- Bug 的详细描述
- 复现步骤
- 预期行为
- 实际行为
- 环境信息（操作系统、Python 版本等）

### 2. 提出新功能建议

如果您有新功能建议，请通过 GitHub Issues 提交，并包含以下信息：

- 功能的详细描述
- 使用场景
- 预期收益

### 3. 提交代码

如果您想提交代码，请按照以下步骤操作：

1. Fork 本仓库
2. 创建您的特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交您的更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 打开一个 Pull Request

### 4. 改进文档

文档改进包括但不限于：

- 修复拼写错误
- 添加使用示例
- 翻译文档
- 完善 API 文档

## 代码规范

### Python 代码规范

- 遵循 PEP 8 规范
- 使用类型注释
- 编写文档字符串
- 保持代码简洁

### 提交信息规范

提交信息应遵循以下格式：

```
<type>(<scope>): <subject>

<body>

<footer>
```

类型（type）包括：

- `feat`: 新功能
- `fix`: Bug 修复
- `docs`: 文档更新
- `style`: 代码格式调整
- `refactor`: 代码重构
- `test`: 测试相关
- `chore`: 构建/工具相关

## 开发环境

### 1. 克隆仓库

```bash
git clone https://github.com/your-username/ai-red-team-skills-manager.git
cd ai-red-team-skills-manager
```

### 2. 创建虚拟环境

```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate  # Windows
```

### 3. 安装依赖

```bash
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

### 4. 运行测试

```bash
pytest tests/
```

## 行为准则

### 我们的承诺

为了营造一个开放和友好的环境，我们承诺：

- 使用友好和包容的语言
- 尊重不同的观点和经验
- 优雅地接受建设性批评
- 关注对社区最有利的事情
- 对其他社区成员表示同情

### 我们的标准

积极行为包括：

- 使用友好和包容的语言
- 尊重不同的观点和经验
- 优雅地接受建设性批评
- 关注对社区最有利的事情
- 对其他社区成员表示同情

不可接受的行为包括：

- 使用性暗示的语言或图像
- 恶意评论或人身攻击
- 公开或私下骚扰
- 未经许可发布他人的私人信息
- 其他不道德或不专业的行为

## 许可证

通过贡献代码，您同意您的贡献将在 [Apache 2.0 许可证](LICENSE) 下发布。

## 联系方式

如果您有任何问题，请通过以下方式联系我们：

- GitHub Issues
- Email: your-email@example.com

感谢您的贡献！
