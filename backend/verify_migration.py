#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
验证资源包数据迁移结果
"""

import asyncio
import json
import sys
sys.path.append('.')
from sqlalchemy import text

from app.core.database import get_db_context

async def verify_migration():
    """验证迁移结果"""
    async with get_db_context() as db:
        # 检查资源包表
        print("📋 检查资源包表数据...")
        result = await db.execute(text("""
            SELECT id, name, type, template_id, template_type, dynamic_params
            FROM resource_packages
        """))
        
        packages = result.fetchall()
        print(f"总资源包数: {len(packages)}")
        
        for package in packages:
            print(f"  - ID: {package[0]}, 名称: {package[1]}, 类型: {package[2]}")
            print(f"    模板ID: {package[3]}, 模板类型: {package[4]}")
            if package[5]:
                dynamic_params = json.loads(package[5])
                print(f"    动态参数: {dynamic_params}")
            else:
                print(f"    动态参数: 无")
            print()
        
        # 检查SQL查询模板表
        print("📋 检查SQL查询模板表...")
        result = await db.execute(text("""
            SELECT id, name, description, datasource_id, is_template
            FROM sql_query_templates
            WHERE is_template = 1
        """))
        
        sql_templates = result.fetchall()
        print(f"SQL模板数: {len(sql_templates)}")
        
        for template in sql_templates:
            print(f"  - ID: {template[0]}, 名称: {template[1]}")
            print(f"    描述: {template[2]}")
            print(f"    数据源ID: {template[3]}")
            print()
        
        # 检查ES查询模板表
        print("📋 检查ES查询模板表...")
        result = await db.execute(text("""
            SELECT id, name, description, datasource_id, is_template
            FROM es_query_templates
            WHERE is_template = 1
        """))
        
        es_templates = result.fetchall()
        print(f"ES模板数: {len(es_templates)}")
        
        for template in es_templates:
            print(f"  - ID: {template[0]}, 名称: {template[1]}")
            print(f"    描述: {template[2]}")
            print(f"    数据源ID: {template[3]}")
            print()
        
        # 验证关联关系
        print("🔗 验证关联关系...")
        result = await db.execute(text("""
            SELECT rp.id, rp.name, rp.template_id, rp.template_type,
                   CASE 
                       WHEN rp.template_type = 'sql' THEN sqt.name
                       WHEN rp.template_type = 'elasticsearch' THEN eqt.name
                   END as template_name
            FROM resource_packages rp
            LEFT JOIN sql_query_templates sqt ON rp.template_id = sqt.id AND rp.template_type = 'sql'
            LEFT JOIN es_query_templates eqt ON rp.template_id = eqt.id AND rp.template_type = 'elasticsearch'
        """))
        
        associations = result.fetchall()
        
        for assoc in associations:
            print(f"资源包 '{assoc[1]}' (ID: {assoc[0]}) -> 模板 '{assoc[4]}' (ID: {assoc[2]}, 类型: {assoc[3]})")
        
        print("\n✅ 迁移验证完成！")

if __name__ == "__main__":
    asyncio.run(verify_migration())