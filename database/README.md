# ACWL-AI 数据库测试数据

本目录包含ACWL-AI项目的数据库schema和测试数据脚本。

## 文件说明

- `schema.sql` - 数据库表结构定义
- `test_data.sql` - 测试数据插入脚本
- `insert_test_data.py` - Python测试数据插入工具
- `insert_test_data.bat` - Windows批处理脚本
- `db_config.py` - 独立数据库配置模块
- `.env.example` - 环境变量配置示例
- `README.md` - 本说明文件

## 使用方法

### 1. 创建数据库表结构

首先确保MySQL数据库已创建，然后执行schema.sql创建表结构：

```bash
# 方法1: 使用MySQL命令行
mysql -h 10.20.1.200 -u root -p acwl-ai < schema.sql

# 方法2: 使用MySQL客户端
mysql -h 10.20.1.200 -u root -p
USE acwl-ai;
source schema.sql;
```

### 2. 插入测试数据

#### 方法1: 使用Windows批处理脚本（最简单）

```bash
# 双击运行或在命令行执行
insert_test_data.bat
```

批处理脚本提供菜单选择：
- 标准插入（交互式）
- 清空数据后插入
- 强制插入（无确认）
- 仅检查数据库连接
- 详细模式插入

#### 方法2: 使用Python脚本（推荐）

```bash
# 进入数据库目录
cd database

# 安装依赖
pip install pymysql

# 基本用法
python insert_test_data.py

# 高级用法
python insert_test_data.py --help
python insert_test_data.py --clear --verbose
python insert_test_data.py --force
python insert_test_data.py --check-only
```

Python脚本提供以下功能：
- 自动读取配置文件中的数据库连接信息
- 支持命令行参数和交互式操作
- 检查表结构是否存在
- 可选择是否清空现有数据
- 显示插入进度和结果统计
- 错误处理和回滚机制
- 支持自定义SQL文件
- 详细的日志输出

#### 方法3: 直接执行SQL文件

```bash
mysql -h 10.20.1.200 -u root -p acwl-ai < test_data.sql
```

## 测试数据内容

### 用户账号

| 用户名 | 邮箱 | 角色 | 密码 |
|--------|------|------|------|
| admin | admin@acwl.ai | admin | password |
| developer | dev@acwl.ai | user | password |
| researcher | research@acwl.ai | user | password |
| tester | test@acwl.ai | user | password |

*注：密码哈希值为 `password` 的bcrypt加密结果*

### 模型数据

- **ChatGLM3-6B**: 对话语言模型，已激活
- **Qwen-7B-Chat**: 对话模型，已激活  
- **BGE-Large-zh-v1.5**: 中文向量模型，已激活
- **Llama2-7B-Chat**: 对话模型，未激活
- **CLIP-ViT-B/32**: 多模态模型，未激活

### 服务器资源

- **GPU-Server-01**: 2x NVIDIA A100 80GB
- **GPU-Server-02**: 4x NVIDIA V100 32GB  
- **Cloud-Server-01**: 1x NVIDIA RTX 4090 24GB

### 部署实例

- **ChatGLM3-6B-Production**: 生产环境部署，运行中
- **Qwen-7B-Development**: 开发环境部署，运行中
- **BGE-Embedding-Service**: 向量服务，运行中

### 数据集

- 中文对话数据集 (100K条记录)
- 英文问答数据集 (50K条记录)
- 多模态图文数据集 (25K条记录)
- 代码生成数据集 (75K条记录)

### 提示词模板

- 代码生成模板
- 文档总结模板
- 翻译模板
- 问答模板

### API密钥

- 管理员主密钥: `ak-admin-1234567890abcdef1234567890abcdef`
- 开发环境密钥: `ak-dev-abcdef1234567890abcdef1234567890`
- 研究项目密钥: `ak-research-1234abcd5678efgh9012ijkl3456mnop`

### AI Agent

- **代码助手**: 代码生成和审查
- **文档助手**: 文档处理和总结
- **翻译助手**: 多语言翻译

### 知识库

- **技术文档知识库**: 技术文档和API文档
- **产品手册知识库**: 产品手册和FAQ

## 数据库配置

### 配置方式

#### 方式1: 使用.env文件（推荐）

1. 复制 `.env.example` 为 `.env`
2. 修改 `.env` 文件中的配置值

```bash
cp .env.example .env
# 然后编辑 .env 文件
```

#### 方式2: 使用环境变量

```bash
# Windows
set DB_HOST=your_host
set DB_PASSWORD=your_password

# Linux/Mac
export DB_HOST=your_host
export DB_PASSWORD=your_password
```

#### 方式3: 使用默认配置

如果没有设置环境变量或.env文件，将使用以下默认配置：

```python
DB_HOST = "10.20.1.200"
DB_PORT = 3306
DB_USER = "root"
DB_PASSWORD = "2wsx1QAZaczt"
DB_NAME = "acwl-ai"
DB_CHARSET = "utf8mb4"
```

## 命令行选项

Python脚本支持以下命令行选项：

```bash
# 显示帮助信息
python insert_test_data.py --help

# 清空现有数据后插入
python insert_test_data.py --clear

# 强制执行，不询问确认
python insert_test_data.py --force

# 仅检查数据库连接和表结构
python insert_test_data.py --check-only

# 显示详细输出
python insert_test_data.py --verbose

# 使用自定义SQL文件
python insert_test_data.py --sql-file custom_data.sql

# 组合使用
python insert_test_data.py --clear --force --verbose
```

## 注意事项

1. **安全提醒**: 测试数据包含示例密码和API密钥，仅用于开发测试，生产环境请务必更换

2. **数据依赖**: 插入测试数据前请确保已执行schema.sql创建表结构

3. **外键约束**: 测试数据考虑了表间的外键关系，按正确顺序插入

4. **数据清理**: Python脚本提供清理现有数据的选项，谨慎使用

5. **字符编码**: 所有文件使用UTF-8编码，支持中文内容

6. **配置安全**: 请勿将包含真实密码的.env文件提交到版本控制系统

7. **权限要求**: 确保数据库用户有足够的权限创建表和插入数据

## 故障排除

### 连接失败
- 检查数据库服务是否启动
- 验证IP地址、端口、用户名和密码
- 确认防火墙设置允许连接

### 表不存在
- 先执行schema.sql创建表结构
- 检查数据库名称是否正确

### 插入失败
- 检查外键约束
- 验证数据格式是否正确
- 查看错误日志获取详细信息

### 权限问题
- 确认数据库用户有足够权限
- 检查表的读写权限

## 扩展测试数据

如需添加更多测试数据，请：

1. 遵循现有的数据格式和约束
2. 注意表间的外键关系
3. 更新相应的统计查询
4. 测试数据的完整性

## 联系支持

如有问题，请联系开发团队或查看项目文档。