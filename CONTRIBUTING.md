# 贡献指南

感谢你对 ACWL AI Platform 项目的关注！我们欢迎所有形式的贡献，包括但不限于：

- 报告 Bug
- 提出新功能建议
- 提交代码修复
- 改进文档
- 翻译工作

## 📋 目录

- [行为准则](#行为准则)
- [开发环境设置](#开发环境设置)
- [提交 Bug](#提交-bug)
- [提出功能建议](#提出功能建议)
- [提交代码](#提交代码)
- [代码风格](#代码风格)
- [Pull Request 流程](#pull-request-流程)
- [提交消息规范](#提交消息规范)

## 行为准则

本项目采用 [Contributor Covenant 行为准则](./CODE_OF_CONDUCT.md)。参与本项目即表示你同意遵守其条款。

## 开发环境设置

### 前置要求

- Python 3.10+
- Node.js 16+
- MySQL 8.0+
- Redis 6.0+
- Docker (可选)

### 后端设置

```bash
cd backend

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements.txt

# 配置环境变量
cp .env.example .env
# 编辑 .env 文件，填入你的配置

# 运行服务
python -m uvicorn app.main:app --host 0.0.0.0 --port 8082 --reload
```

### 前端设置

```bash
cd frontend

# 安装依赖
npm install

# 开发模式
npm run dev
```

### 使用 Docker (推荐)

```bash
# 启动所有服务
docker-compose up -d

# 查看日志
docker-compose logs -f backend
```

## 提交 Bug

在提交 Bug 之前，请：

1. 搜索 [Issues](https://github.com/YOUR_USERNAME/acwl-ai-data/issues) 确保该 Bug 尚未被报告
2. 使用最新的代码复现问题
3. 提供详细的复现步骤

提交 Bug 时请包含以下信息：

- 清晰的标题
- 问题描述
- 复现步骤
- 预期行为
- 实际行为
- 环境信息（操作系统、Python 版本、浏览器等）
- 截图或日志（如果适用）

## 提出功能建议

在提出新功能建议之前，请：

1. 搜索 [Issues](https://github.com/YOUR_USERNAME/acwl-ai-data/issues) 确保该功能尚未被提议
2. 考虑该功能是否对项目整体有益

提交功能建议时请包含：

- 清晰的标题
- 功能描述
- 使用场景
- 可能的实现方案（如果有的话）

## 提交代码

### 分支策略

- `main` - 主分支，保持稳定
- `develop` - 开发分支，包含最新功能
- `feature/*` - 功能分支
- `bugfix/*` - Bug 修复分支
- `hotfix/*` - 紧急修复分支

### 工作流程

1. Fork 本仓库
2. 从 `develop` 分支创建你的特性分支
3. 在你的分支上进行开发
4. 编写测试（如果适用）
5. 确保所有测试通过
6. 提交代码
7. 推送到你的 Fork
8. 创建 Pull Request 到 `develop` 分支

## 代码风格

### Python

- 遵循 [PEP 8](https://peps.python.org/pep-0008/) 规范
- 使用 Black 进行代码格式化
- 使用 Flake8 进行代码检查
- 使用类型提示（Type Hints）

```bash
# 格式化代码
black .

# 检查代码
flake8 .

# 类型检查
mypy .
```

### TypeScript/Vue

- 遵循 ESLint 配置
- 使用 Prettier 进行代码格式化

```bash
# 格式化代码
npm run format

# 检查代码
npm run lint

# 类型检查
npm run type-check
```

## Pull Request 流程

1. 确保你的代码通过了所有测试
2. 更新相关文档
3. 确保 PR 描述清晰
4. 链接相关的 Issue
5. 等待代码审查
6. 根据审查意见进行修改

### PR 模板

```markdown
## 描述
简要描述此 PR 的目的

## 相关 Issue
Closes #123

## 更改类型
- [ ] Bug 修复
- [ ] 新功能
- [ ] 文档更新
- [ ] 性能优化
- [ ] 重构
- [ ] 测试

## 测试
描述你如何测试这些更改

## 截图（如果适用）
添加截图以帮助理解更改
```

## 提交消息规范

我们使用 [Conventional Commits](https://www.conventionalcommits.org/) 规范：

```
<type>(<scope>): <description>

[optional body]

[optional footer(s)]
```

### Type 类型

- `feat`: 新功能
- `fix`: Bug 修复
- `docs`: 文档更新
- `style`: 代码格式调整（不影响代码运行）
- `refactor`: 代码重构
- `perf`: 性能优化
- `test`: 添加或修改测试
- `chore`: 构建过程或辅助工具的变动

### 示例

```
feat(agents): 添加 Agent 技能直调功能
fix(auth): 修复 token 刷新问题
docs(readme): 更新安装说明
```

## 📜 许可证

通过贡献代码，你同意你的贡献将根据本项目的 [Apache License 2.0](./LICENSE) 进行分发。

## 致谢

感谢所有为 ACWL AI Platform 做出贡献的开发者！
