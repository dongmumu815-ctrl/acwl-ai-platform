#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
资源包数据迁移脚本
将现有的资源包数据转换为基于查询模板的新结构

执行步骤：
1. 为每个现有资源包创建对应的查询模板
2. 更新资源包表结构，添加template_id和template_type字段
3. 将资源包的查询配置迁移到模板中
4. 清理冗余字段
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
from sqlalchemy import text, select, update
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.models.resource_package import ResourcePackage
from app.models.sql_query_template import SQLQueryTemplate
from app.models.es_query_template import ESQueryTemplate

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 创建异步数据库引擎
engine = create_async_engine(settings.DATABASE_URL, echo=True)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


class ResourcePackageMigrator:
    """资源包迁移器"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.migration_log = []
    
    async def migrate_all(self) -> Dict[str, Any]:
        """执行完整的迁移流程
        
        Returns:
            Dict[str, Any]: 迁移结果统计
        """
        logger.info("开始资源包迁移...")
        
        try:
            # 1. 添加新字段
            await self._add_new_columns()
            
            # 2. 获取所有现有资源包
            packages = await self._get_existing_packages()
            logger.info(f"找到 {len(packages)} 个资源包需要迁移")
            
            # 3. 为每个资源包创建模板并更新
            migrated_count = 0
            failed_count = 0
            
            for package in packages:
                try:
                    await self._migrate_single_package(package)
                    migrated_count += 1
                    logger.info(f"成功迁移资源包: {package.name} (ID: {package.id})")
                except Exception as e:
                    failed_count += 1
                    error_msg = f"迁移资源包失败: {package.name} (ID: {package.id}), 错误: {str(e)}"
                    logger.error(error_msg)
                    self.migration_log.append(error_msg)
            
            # 4. 提交事务
            await self.db.commit()
            
            # 5. 验证迁移结果
            validation_result = await self._validate_migration()
            
            result = {
                "total_packages": len(packages),
                "migrated_count": migrated_count,
                "failed_count": failed_count,
                "validation": validation_result,
                "migration_log": self.migration_log
            }
            
            logger.info(f"迁移完成: {result}")
            return result
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"迁移过程中发生错误: {str(e)}")
            raise
    
    async def _add_new_columns(self):
        """添加新的数据库字段"""
        logger.info("添加新的数据库字段...")
        
        # 检查字段是否已存在
        check_columns_sql = """
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name = 'resource_packages' 
        AND column_name IN ('template_id', 'template_type', 'dynamic_params')
        """
        
        result = await self.db.execute(text(check_columns_sql))
        existing_columns = [row[0] for row in result.fetchall()]
        
        # 添加缺失的字段
        if 'template_id' not in existing_columns:
            await self.db.execute(text("""
                ALTER TABLE resource_packages 
                ADD COLUMN template_id INTEGER
            """))
            logger.info("添加 template_id 字段")
        
        if 'template_type' not in existing_columns:
            await self.db.execute(text("""
                ALTER TABLE resource_packages 
                ADD COLUMN template_type ENUM('sql', 'elasticsearch')
            """))
            logger.info("添加 template_type 字段")
        
        if 'dynamic_params' not in existing_columns:
            await self.db.execute(text("""
                ALTER TABLE resource_packages 
                ADD COLUMN dynamic_params JSON COMMENT '动态参数配置，用于覆盖模板中的参数'
            """))
            logger.info("添加 dynamic_params 字段")
    
    async def _get_existing_packages(self) -> List[ResourcePackage]:
        """获取所有现有的资源包"""
        query = select(ResourcePackage).where(ResourcePackage.template_id.is_(None))
        result = await self.db.execute(query)
        return result.scalars().all()
    
    async def _migrate_single_package(self, package: ResourcePackage):
        """迁移单个资源包
        
        Args:
            package: 要迁移的资源包
        """
        logger.info(f"开始迁移资源包: {package.name} (ID: {package.id})")
        
        # 创建对应的查询模板
        if package.type == 'sql':
            template = await self._create_sql_template(package)
        elif package.type == 'elasticsearch':
            template = await self._create_es_template(package)
        else:
            raise ValueError(f"不支持的资源包类型: {package.type}")
        
        # 更新资源包，关联到新创建的模板
        await self._update_package_with_template(package, template)
        
        self.migration_log.append(f"成功迁移资源包: {package.name} -> 模板ID: {template.id}")
    
    async def _create_sql_template(self, package: ResourcePackage) -> SQLQueryTemplate:
        """为SQL资源包创建查询模板
        
        Args:
            package: SQL资源包
            
        Returns:
            SQLQueryTemplate: 创建的SQL查询模板
        """
        # 从资源包配置构建SQL查询
        base_config = package.base_config or {}
        table_name = base_config.get("table_name", "unknown_table")
        select_fields = base_config.get("select_fields", ["*"])
        
        # 构建基础查询语句
        if isinstance(select_fields, list) and select_fields:
            fields_str = ", ".join(select_fields)
        else:
            fields_str = "*"
        
        base_query = f"SELECT {fields_str} FROM {table_name}"
        
        # 构建WHERE条件（锁定条件）
        conditions = []
        locked_conditions = package.locked_conditions or []
        
        for i, condition in enumerate(locked_conditions):
            field = condition.get("field")
            operator = condition.get("operator", "=")
            value = condition.get("value")
            
            if field and value is not None:
                if operator == "=":
                    conditions.append(f"{field} = '{value}'")
                elif operator == "!=":
                    conditions.append(f"{field} != '{value}'")
                elif operator in [">", ">=", "<", "<="]:
                    conditions.append(f"{field} {operator} {value}")
                elif operator == "LIKE":
                    conditions.append(f"{field} LIKE '%{value}%'")
                elif operator == "IN" and isinstance(value, list):
                    value_str = ", ".join([f"'{v}'" for v in value])
                    conditions.append(f"{field} IN ({value_str})")
        
        # 添加动态条件占位符
        dynamic_conditions = package.dynamic_conditions or []
        for i, condition in enumerate(dynamic_conditions):
            field = condition.get("field")
            operator = condition.get("operator", "=")
            param_key = condition.get("param_key", f"param_{i}")
            
            if field:
                if operator in ["=", "!=", ">", ">=", "<", "<="]:
                    conditions.append(f"{field} {operator} :{param_key}")
                elif operator == "LIKE":
                    conditions.append(f"{field} LIKE :{param_key}")
                elif operator == "IN":
                    conditions.append(f"{field} IN (:{param_key})")
        
        # 组装完整查询
        if conditions:
            base_query += " WHERE " + " AND ".join(conditions)
        
        # 添加排序
        if package.order_config:
            order_field = package.order_config.get("field")
            order_direction = package.order_config.get("direction", "ASC")
            if order_field:
                base_query += f" ORDER BY {order_field} {order_direction}"
        
        # 构建模板配置
        template_config = {
            "base_config": base_config,
            "locked_conditions": locked_conditions,
            "dynamic_conditions": dynamic_conditions,
            "order_config": package.order_config,
            "limit_config": package.limit_config
        }
        
        # 创建SQL查询模板
        template = SQLQueryTemplate(
            name=f"{package.name}_template",
            description=f"从资源包 '{package.name}' 迁移的查询模板",
            datasource_id=package.datasource_id,
            data_resource_id=package.resource_id,
            created_by=package.created_by,
            query=base_query,
            config=template_config,
            is_template=True
        )
        
        self.db.add(template)
        await self.db.flush()  # 获取ID但不提交
        
        return template
    
    async def _create_es_template(self, package: ResourcePackage) -> ESQueryTemplate:
        """为ES资源包创建查询模板
        
        Args:
            package: ES资源包
            
        Returns:
            ESQueryTemplate: 创建的ES查询模板
        """
        # 从资源包配置构建ES查询
        base_config = package.base_config or {}
        indices = base_config.get("indices", ["*"])
        
        # 构建基础ES查询
        base_query = {
            "query": {
                "bool": {
                    "must": [],
                    "filter": []
                }
            }
        }
        
        # 添加锁定条件
        locked_conditions = package.locked_conditions or []
        for condition in locked_conditions:
            field = condition.get("field")
            operator = condition.get("operator", "=")
            value = condition.get("value")
            
            if field and value is not None:
                if operator == "=":
                    base_query["query"]["bool"]["filter"].append({
                        "term": {field: value}
                    })
                elif operator == "!=":
                    base_query["query"]["bool"]["must_not"] = base_query["query"]["bool"].get("must_not", [])
                    base_query["query"]["bool"]["must_not"].append({
                        "term": {field: value}
                    })
                elif operator in [">", ">=", "<", "<="]:
                    range_query = {field: {}}
                    if operator == ">":
                        range_query[field]["gt"] = value
                    elif operator == ">=":
                        range_query[field]["gte"] = value
                    elif operator == "<":
                        range_query[field]["lt"] = value
                    elif operator == "<=":
                        range_query[field]["lte"] = value
                    
                    base_query["query"]["bool"]["filter"].append({
                        "range": range_query
                    })
        
        # 添加动态条件占位符
        dynamic_conditions = package.dynamic_conditions or []
        for condition in dynamic_conditions:
            field = condition.get("field")
            operator = condition.get("operator", "=")
            param_key = condition.get("param_key", f"param_{field}")
            
            if field:
                # 使用模板参数占位符
                if operator == "=":
                    base_query["query"]["bool"]["filter"].append({
                        "term": {field: f"{{{{{param_key}}}}}"}
                    })
                elif operator in [">", ">=", "<", "<="]:
                    range_query = {field: {}}
                    if operator == ">":
                        range_query[field]["gt"] = f"{{{{{param_key}}}}}"
                    elif operator == ">=":
                        range_query[field]["gte"] = f"{{{{{param_key}}}}}"
                    elif operator == "<":
                        range_query[field]["lt"] = f"{{{{{param_key}}}}}"
                    elif operator == "<=":
                        range_query[field]["lte"] = f"{{{{{param_key}}}}}"
                    
                    base_query["query"]["bool"]["filter"].append({
                        "range": range_query
                    })
        
        # 添加排序
        if package.order_config:
            order_field = package.order_config.get("field")
            order_direction = package.order_config.get("direction", "asc").lower()
            if order_field:
                base_query["sort"] = [{order_field: {"order": order_direction}}]
        
        # 添加大小限制
        if package.limit_config:
            base_query["size"] = package.limit_config
        
        # 创建ES查询模板
        template = ESQueryTemplate(
            name=f"{package.name}_template",
            description=f"从资源包 '{package.name}' 迁移的查询模板",
            datasource_id=package.datasource_id,
            indices=indices,
            query=base_query,
            is_template=True,
            created_by=package.created_by
        )
        
        self.db.add(template)
        await self.db.flush()  # 获取ID但不提交
        
        return template
    
    async def _update_package_with_template(self, package: ResourcePackage, template):
        """更新资源包，关联到新创建的模板
        
        Args:
            package: 资源包
            template: 查询模板
        """
        # 提取动态参数配置
        dynamic_params = {}
        dynamic_conditions = package.dynamic_conditions or []
        
        for condition in dynamic_conditions:
            param_key = condition.get("param_key")
            default_value = condition.get("default_value")
            if param_key and default_value is not None:
                dynamic_params[param_key] = default_value
        
        # 更新资源包
        update_stmt = update(ResourcePackage).where(
            ResourcePackage.id == package.id
        ).values(
            template_id=template.id,
            template_type=package.type,
            dynamic_params=dynamic_params if dynamic_params else None
        )
        
        await self.db.execute(update_stmt)
    
    async def _validate_migration(self) -> Dict[str, Any]:
        """验证迁移结果
        
        Returns:
            Dict[str, Any]: 验证结果
        """
        logger.info("验证迁移结果...")
        
        # 检查所有资源包是否都有关联的模板
        query = select(ResourcePackage).where(ResourcePackage.template_id.is_(None))
        result = await self.db.execute(query)
        packages_without_template = result.scalars().all()
        
        # 检查模板数量
        sql_template_count_query = select(func.count(SQLQueryTemplate.id))
        sql_result = await self.db.execute(sql_template_count_query)
        sql_template_count = sql_result.scalar()
        
        es_template_count_query = select(func.count(ESQueryTemplate.id))
        es_result = await self.db.execute(es_template_count_query)
        es_template_count = es_result.scalar()
        
        return {
            "packages_without_template": len(packages_without_template),
            "packages_without_template_ids": [p.id for p in packages_without_template],
            "total_sql_templates": sql_template_count,
            "total_es_templates": es_template_count,
            "migration_complete": len(packages_without_template) == 0
        }


async def main():
    """主函数"""
    async with AsyncSessionLocal() as db:
        migrator = ResourcePackageMigrator(db)
        
        try:
            result = await migrator.migrate_all()
            
            print("\n" + "="*50)
            print("资源包迁移完成!")
            print("="*50)
            print(f"总资源包数: {result['total_packages']}")
            print(f"成功迁移: {result['migrated_count']}")
            print(f"迁移失败: {result['failed_count']}")
            print(f"验证结果: {result['validation']}")
            
            if result['migration_log']:
                print("\n迁移日志:")
                for log_entry in result['migration_log']:
                    print(f"  - {log_entry}")
            
            if result['validation']['migration_complete']:
                print("\n✅ 迁移验证通过!")
            else:
                print("\n❌ 迁移验证失败，请检查日志!")
                
        except Exception as e:
            print(f"\n❌ 迁移过程中发生错误: {str(e)}")
            raise


if __name__ == "__main__":
    asyncio.run(main())