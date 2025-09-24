#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简化的资源包数据迁移脚本
将现有的资源包数据转换为基于查询模板的新结构
"""

import asyncio
import json
import logging
import sys
sys.path.append('.')
from datetime import datetime
from typing import Dict, Any, List, Optional
from sqlalchemy import text

from app.core.database import get_db_context

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def get_existing_packages():
    """获取所有现有的资源包（没有template_id的）"""
    async with get_db_context() as db:
        result = await db.execute(text("""
            SELECT id, name, description, type, datasource_id, resource_id, 
                   base_config, locked_conditions, dynamic_conditions, 
                   order_config, limit_config, created_by
            FROM resource_packages 
            WHERE template_id IS NULL
        """))
        
        packages = []
        for row in result.fetchall():
            packages.append({
                'id': row[0],
                'name': row[1],
                'description': row[2],
                'type': row[3],
                'datasource_id': row[4],
                'resource_id': row[5],
                'base_config': json.loads(row[6]) if row[6] else {},
                'locked_conditions': json.loads(row[7]) if row[7] else [],
                'dynamic_conditions': json.loads(row[8]) if row[8] else [],
                'order_config': json.loads(row[9]) if row[9] else {},
                'limit_config': row[10],
                'created_by': row[11]
            })
        
        return packages

async def create_sql_template(package: Dict[str, Any]) -> int:
    """为SQL资源包创建查询模板"""
    async with get_db_context() as db:
        # 从资源包配置构建SQL查询
        base_config = package.get('base_config', {})
        table_name = base_config.get('table_name', 'unknown_table')
        select_fields = base_config.get('select_fields', ['*'])
        
        # 构建基础查询语句
        if isinstance(select_fields, list) and select_fields:
            fields_str = ', '.join(select_fields)
        else:
            fields_str = '*'
        
        base_query = f"SELECT {fields_str} FROM {table_name}"
        
        # 构建WHERE条件（锁定条件）
        conditions = []
        locked_conditions = package.get('locked_conditions', [])
        
        for condition in locked_conditions:
            field = condition.get('field')
            operator = condition.get('operator', '=')
            value = condition.get('value')
            
            if field and value is not None:
                if operator == '=':
                    conditions.append(f"{field} = '{value}'")
                elif operator == '!=':
                    conditions.append(f"{field} != '{value}'")
                elif operator in ['>', '>=', '<', '<=']:
                    conditions.append(f"{field} {operator} {value}")
                elif operator == 'LIKE':
                    conditions.append(f"{field} LIKE '%{value}%'")
                elif operator == 'IN' and isinstance(value, list):
                    value_str = ', '.join([f"'{v}'" for v in value])
                    conditions.append(f"{field} IN ({value_str})")
        
        # 添加动态条件占位符
        dynamic_conditions = package.get('dynamic_conditions', [])
        for i, condition in enumerate(dynamic_conditions):
            field = condition.get('field')
            operator = condition.get('operator', '=')
            param_key = condition.get('param_key', f'param_{i}')
            
            if field:
                if operator in ['=', '!=', '>', '>=', '<', '<=']:
                    conditions.append(f"{field} {operator} :{param_key}")
                elif operator == 'LIKE':
                    conditions.append(f"{field} LIKE :{param_key}")
                elif operator == 'IN':
                    conditions.append(f"{field} IN (:{param_key})")
        
        # 组装完整查询
        if conditions:
            base_query += ' WHERE ' + ' AND '.join(conditions)
        
        # 添加排序
        order_config = package.get('order_config', {})
        if order_config:
            order_field = order_config.get('field')
            order_direction = order_config.get('direction', 'ASC')
            if order_field:
                base_query += f" ORDER BY {order_field} {order_direction}"
        
        # 构建模板配置
        template_config = {
            'base_config': base_config,
            'locked_conditions': locked_conditions,
            'dynamic_conditions': dynamic_conditions,
            'order_config': order_config,
            'limit_config': package.get('limit_config')
        }
        
        # 插入SQL查询模板
        insert_sql = """
        INSERT INTO sql_query_templates 
        (name, description, datasource_id, data_resource_id, created_by, query, config, is_template, created_at)
        VALUES (:name, :description, :datasource_id, :data_resource_id, :created_by, :query, :config, :is_template, :created_at)
        """
        
        result = await db.execute(text(insert_sql), {
            'name': f"{package['name']}_template",
            'description': f"从资源包 '{package['name']}' 迁移的查询模板",
            'datasource_id': package['datasource_id'],
            'data_resource_id': package['resource_id'],
            'created_by': package['created_by'],
            'query': base_query,
            'config': json.dumps(template_config),
            'is_template': True,
            'created_at': datetime.now()
        })
        
        # 获取插入的模板ID
        template_id = result.lastrowid
        logger.info(f"创建SQL模板成功，ID: {template_id}")
        return template_id

async def create_es_template(package: Dict[str, Any]) -> int:
    """为ES资源包创建查询模板"""
    async with get_db_context() as db:
        # 从资源包配置构建ES查询
        base_config = package.get('base_config', {})
        indices = base_config.get('indices', ['*'])
        
        # 构建基础ES查询
        base_query = {
            'query': {
                'bool': {
                    'must': [],
                    'filter': []
                }
            }
        }
        
        # 添加锁定条件
        locked_conditions = package.get('locked_conditions', [])
        for condition in locked_conditions:
            field = condition.get('field')
            operator = condition.get('operator', '=')
            value = condition.get('value')
            
            if field and value is not None:
                if operator == '=':
                    base_query['query']['bool']['filter'].append({
                        'term': {field: value}
                    })
                elif operator == '!=':
                    base_query['query']['bool']['must_not'] = base_query['query']['bool'].get('must_not', [])
                    base_query['query']['bool']['must_not'].append({
                        'term': {field: value}
                    })
                elif operator in ['>', '>=', '<', '<=']:
                    range_query = {field: {}}
                    if operator == '>':
                        range_query[field]['gt'] = value
                    elif operator == '>=':
                        range_query[field]['gte'] = value
                    elif operator == '<':
                        range_query[field]['lt'] = value
                    elif operator == '<=':
                        range_query[field]['lte'] = value
                    
                    base_query['query']['bool']['filter'].append({
                        'range': range_query
                    })
        
        # 添加动态条件占位符
        dynamic_conditions = package.get('dynamic_conditions', [])
        for condition in dynamic_conditions:
            field = condition.get('field')
            operator = condition.get('operator', '=')
            param_key = condition.get('param_key', f'param_{field}')
            
            if field:
                # 使用模板参数占位符
                if operator == '=':
                    base_query['query']['bool']['filter'].append({
                        'term': {field: f'{{{{{param_key}}}}}'}
                    })
                elif operator in ['>', '>=', '<', '<=']:
                    range_query = {field: {}}
                    if operator == '>':
                        range_query[field]['gt'] = f'{{{{{param_key}}}}}'
                    elif operator == '>=':
                        range_query[field]['gte'] = f'{{{{{param_key}}}}}'
                    elif operator == '<':
                        range_query[field]['lt'] = f'{{{{{param_key}}}}}'
                    elif operator == '<=':
                        range_query[field]['lte'] = f'{{{{{param_key}}}}}'
                    
                    base_query['query']['bool']['filter'].append({
                        'range': range_query
                    })
        
        # 添加排序
        order_config = package.get('order_config', {})
        if order_config:
            order_field = order_config.get('field')
            order_direction = order_config.get('direction', 'asc').lower()
            if order_field:
                base_query['sort'] = [{order_field: {'order': order_direction}}]
        
        # 添加大小限制
        limit_config = package.get('limit_config')
        if limit_config:
            base_query['size'] = limit_config
        
        # 插入ES查询模板
        insert_sql = """
        INSERT INTO es_query_templates 
        (name, description, datasource_id, indices, query, is_template, created_by, created_at)
        VALUES (:name, :description, :datasource_id, :indices, :query, :is_template, :created_by, :created_at)
        """
        
        result = await db.execute(text(insert_sql), {
            'name': f"{package['name']}_template",
            'description': f"从资源包 '{package['name']}' 迁移的查询模板",
            'datasource_id': package['datasource_id'],
            'indices': json.dumps(indices),
            'query': json.dumps(base_query),
            'is_template': True,
            'created_by': package['created_by'],
            'created_at': datetime.now()
        })
        
        # 获取插入的模板ID
        template_id = result.lastrowid
        logger.info(f"创建ES模板成功，ID: {template_id}")
        return template_id

async def update_package_with_template(package_id: int, template_id: int, template_type: str, dynamic_params: Dict[str, Any]):
    """更新资源包，关联到新创建的模板"""
    async with get_db_context() as db:
        update_sql = """
        UPDATE resource_packages 
        SET template_id = :template_id, 
            template_type = :template_type, 
            dynamic_params = :dynamic_params
        WHERE id = :package_id
        """
        
        await db.execute(text(update_sql), {
            'template_id': template_id,
            'template_type': template_type,
            'dynamic_params': json.dumps(dynamic_params) if dynamic_params else None,
            'package_id': package_id
        })
        
        logger.info(f"更新资源包 {package_id} 成功，关联模板 {template_id}")

async def migrate_single_package(package: Dict[str, Any]):
    """迁移单个资源包"""
    logger.info(f"开始迁移资源包: {package['name']} (ID: {package['id']})")
    
    # 创建对应的查询模板
    if package['type'] == 'sql':
        template_id = await create_sql_template(package)
    elif package['type'] == 'elasticsearch':
        template_id = await create_es_template(package)
    else:
        raise ValueError(f"不支持的资源包类型: {package['type']}")
    
    # 提取动态参数配置
    dynamic_params = {}
    dynamic_conditions = package.get('dynamic_conditions', [])
    
    for condition in dynamic_conditions:
        param_key = condition.get('param_key')
        default_value = condition.get('default_value')
        if param_key and default_value is not None:
            dynamic_params[param_key] = default_value
    
    # 更新资源包，关联到新创建的模板
    await update_package_with_template(package['id'], template_id, package['type'], dynamic_params)
    
    logger.info(f"成功迁移资源包: {package['name']} -> 模板ID: {template_id}")

async def main():
    """主函数"""
    try:
        logger.info("开始资源包数据迁移...")
        
        # 获取所有需要迁移的资源包
        packages = await get_existing_packages()
        logger.info(f"找到 {len(packages)} 个资源包需要迁移")
        
        if not packages:
            print("✅ 没有需要迁移的资源包")
            return
        
        # 迁移每个资源包
        migrated_count = 0
        failed_count = 0
        
        for package in packages:
            try:
                await migrate_single_package(package)
                migrated_count += 1
            except Exception as e:
                failed_count += 1
                logger.error(f"迁移资源包失败: {package['name']} (ID: {package['id']}), 错误: {str(e)}")
        
        # 验证迁移结果
        remaining_packages = await get_existing_packages()
        
        print("\n" + "="*50)
        print("🎉 资源包数据迁移完成！")
        print("="*50)
        print(f"总资源包数: {len(packages)}")
        print(f"成功迁移: {migrated_count}")
        print(f"迁移失败: {failed_count}")
        print(f"剩余未迁移: {len(remaining_packages)}")
        
        if len(remaining_packages) == 0:
            print("\n✅ 所有资源包都已成功迁移！")
        else:
            print(f"\n⚠️ 还有 {len(remaining_packages)} 个资源包未迁移")
            
    except Exception as e:
        logger.error(f"迁移过程中发生错误: {str(e)}")
        print(f"\n❌ 迁移失败: {str(e)}")
        raise

if __name__ == "__main__":
    asyncio.run(main())