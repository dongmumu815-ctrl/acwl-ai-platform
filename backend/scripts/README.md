# 检查和维护脚本

这个目录包含用于检查和维护系统的实用脚本。

## 脚本说明

### Agent 相关检查
- `check_agent_32.py` - 检查 Agent ID 32 的详细配置信息
- `check_agent_32_config.py` - 检查 Agent ID 32 的配置参数

### 数据库相关检查
- `check_db_data.py` - 检查数据库中的模型类型数据
- `check_schema.py` - 检查数据库架构
- `check_table_structure.py` - 检查数据库表结构

## 使用方法

这些脚本需要在 `backend` 目录下运行：

```bash
cd backend
python scripts/check_agent_32.py
python scripts/check_db_data.py
# 等等...
```

## 注意事项

- 运行前确保数据库连接配置正确
- 某些脚本可能需要特定的数据库权限
- 建议在开发环境中运行这些检查脚本