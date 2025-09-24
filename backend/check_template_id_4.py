#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
专门查看ID=4的SQL模板数据
"""

import asyncio
import json
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine
from app.core.config import settings

async def check_template_id_4():
    """
    查看ID=4的SQL模板详细数据
    """
    # 创建异步数据库引擎
    database_url = f"mysql+aiomysql://{settings.DB_USER}:{settings.DB_PASSWORD}@{settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}?charset={settings.DB_CHARSET}"
    
    engine = create_async_engine(database_url, echo=False)
    
    try:
        async with engine.begin() as conn:
            print("=== 查看ID=4的SQL模板数据 ===")
            
            # 查看ID=4的完整数据
            result = await conn.execute(text("SELECT * FROM sql_query_templates WHERE id = 4"))
            row = result.fetchone()
            
            if row:
                print(f"ID: {row[0]}")
                print(f"Name: {row[1]}")
                print(f"Description: {row[2]}")
                print(f"Datasource ID: {row[3]}")
                print(f"Data Resource ID: {row[4]}")
                print(f"Created By: {row[5]}")
                print(f"Query: {row[6]}")
                print(f"Tags: {row[7]}")
                print(f"Config: {row[8]}")
                print(f"Is Template: {row[9]}")
                print(f"Created At: {row[10]}")
                print(f"Updated At: {row[11]}")
                
                print("\n=== Query详细内容 ===")
                print(row[6])
                
                print("\n=== Config详细内容 ===")
                if row[8]:
                    try:
                        config_data = json.loads(row[8]) if isinstance(row[8], str) else row[8]
                        print(json.dumps(config_data, indent=2, ensure_ascii=False))
                        
                        # 检查是否有locked_conditions
                        if 'locked_conditions' in config_data:
                            print(f"\n=== Locked Conditions ===")
                            print(json.dumps(config_data['locked_conditions'], indent=2, ensure_ascii=False))
                        
                        # 检查是否有dynamic_conditions
                        if 'dynamic_conditions' in config_data:
                            print(f"\n=== Dynamic Conditions ===")
                            print(json.dumps(config_data['dynamic_conditions'], indent=2, ensure_ascii=False))
                            
                        # 检查是否有conditions
                        if 'conditions' in config_data:
                            print(f"\n=== Conditions ===")
                            print(json.dumps(config_data['conditions'], indent=2, ensure_ascii=False))
                            
                    except Exception as e:
                        print(f"Config解析失败: {e}")
                        print(f"原始Config: {row[8]}")
                else:
                    print("Config为空")
            else:
                print("未找到ID=4的记录")
                
    except Exception as e:
        print(f"数据库连接或查询失败: {e}")
    finally:
        await engine.dispose()

if __name__ == "__main__":
    asyncio.run(check_template_id_4())