#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试新的SQL动态修改方案
验证整个流程：从数据库获取模板 -> 动态修改SQL -> 执行查询
"""

import asyncio
import json
import sys
sys.path.append('.')

from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
from app.core.config import settings
from app.services.sql_dynamic_modifier import SQLDynamicModifier


async def test_complete_solution():
    """
    测试完整的SQL动态修改方案
    """
    print("=== 测试新的SQL动态修改方案 ===\n")
    
    # 创建数据库连接
    database_url = f"mysql+aiomysql://{settings.DB_USER}:{settings.DB_PASSWORD}@{settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}?charset={settings.DB_CHARSET}"
    engine = create_async_engine(database_url, echo=False)
    
    # 创建SQL修改器
    modifier = SQLDynamicModifier()
    
    try:
        async with engine.begin() as conn:
            # 获取ID=4的模板数据
            result = await conn.execute(text("SELECT query, config FROM sql_query_templates WHERE id = 4"))
            row = result.fetchone()
            
            if not row:
                print("未找到ID=4的模板")
                return
            
            # 注意：由于数据错位问题，我们使用您提供的正确数据
            sql_query = "SELECT name, description, parent_id, id FROM cpc_agents WHERE node_type = 'agent' AND description = '' AND name = '' ORDER BY id DESC LIMIT 100"
            
            config_str = '{"conditions": [{"name": "node_type", "type": "string", "label": "node_type", "locked": true, "operator": "=", "required": false, "lockedValue": "agent"}, {"name": "description", "type": "string", "label": "description", "locked": false, "operator": "=", "required": false, "defaultValue": ""}, {"name": "name", "type": "string", "label": "name", "locked": false, "operator": "=", "required": false, "defaultValue": ""}]}'
            
            config = json.loads(config_str)
            
            print(f"原始SQL: {sql_query}")
            print(f"配置: {json.dumps(config, indent=2, ensure_ascii=False)}")
            print()
            
            # 测试场景1：不传入任何非锁定参数
            print("=== 场景1：不传入任何非锁定参数 ===")
            user_params1 = {}
            result1 = modifier.modify_sql_by_params(sql_query, config, user_params1)
            print(f"修改后SQL: {result1}")
            print()
            
            # 测试场景2：只传入description参数
            print("=== 场景2：只传入description参数 ===")
            user_params2 = {"description": "测试描述"}
            result2 = modifier.modify_sql_by_params(sql_query, config, user_params2)
            print(f"修改后SQL: {result2}")
            print()
            
            # 测试场景3：传入name和description参数
            print("=== 场景3：传入name和description参数 ===")
            user_params3 = {"name": "测试名称", "description": "测试描述"}
            result3 = modifier.modify_sql_by_params(sql_query, config, user_params3)
            print(f"修改后SQL: {result3}")
            print()
            
            # 测试场景4：传入空字符串参数（应该被过滤掉）
            print("=== 场景4：传入空字符串参数 ===")
            user_params4 = {"name": "", "description": "有效描述"}
            result4 = modifier.modify_sql_by_params(sql_query, config, user_params4)
            print(f"修改后SQL: {result4}")
            print()
            
            # 测试场景5：传入锁定字段的值（应该被忽略，使用lockedValue）
            print("=== 场景5：传入锁定字段的值 ===")
            user_params5 = {"node_type": "user", "description": "测试描述"}  # node_type是锁定的，应该忽略用户值
            result5 = modifier.modify_sql_by_params(sql_query, config, user_params5)
            print(f"修改后SQL: {result5}")
            print()
            
            print("=== 测试完成 ===")
            
    except Exception as e:
        print(f"测试失败: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await engine.dispose()


async def test_with_real_database():
    """
    使用真实数据库测试（如果可以连接到cpc_agents表）
    """
    print("\n=== 尝试连接真实数据库测试 ===")
    
    database_url = f"mysql+aiomysql://{settings.DB_USER}:{settings.DB_PASSWORD}@{settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}?charset={settings.DB_CHARSET}"
    engine = create_async_engine(database_url, echo=False)
    
    modifier = SQLDynamicModifier()
    
    try:
        async with engine.begin() as conn:
            # 检查cpc_agents表是否存在
            check_table = await conn.execute(text("SHOW TABLES LIKE 'cpc_agents'"))
            if not check_table.fetchone():
                print("cpc_agents表不存在，跳过真实数据库测试")
                return
            
            # 使用修改后的SQL执行查询
            sql_query = "SELECT name, description, parent_id, id FROM cpc_agents WHERE node_type = 'agent' AND description = '' AND name = '' ORDER BY id DESC LIMIT 100"
            config = {
                "conditions": [
                    {"name": "node_type", "type": "string", "label": "node_type", "locked": True, "operator": "=", "required": False, "lockedValue": "agent"},
                    {"name": "description", "type": "string", "label": "description", "locked": False, "operator": "=", "required": False, "defaultValue": ""},
                    {"name": "name", "type": "string", "label": "name", "locked": False, "operator": "=", "required": False, "defaultValue": ""}
                ]
            }
            
            # 测试：只查询node_type='agent'的记录
            user_params = {}
            modified_sql = modifier.modify_sql_by_params(sql_query, config, user_params)
            
            print(f"执行SQL: {modified_sql}")
            
            result = await conn.execute(text(modified_sql))
            rows = result.fetchall()
            
            print(f"查询结果数量: {len(rows)}")
            if rows:
                print("前3条结果:")
                for i, row in enumerate(rows[:3]):
                    print(f"  {i+1}. ID: {row[3]}, Name: {row[0]}, Description: {row[1]}")
            
    except Exception as e:
        print(f"真实数据库测试失败: {e}")
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(test_complete_solution())
    asyncio.run(test_with_real_database())