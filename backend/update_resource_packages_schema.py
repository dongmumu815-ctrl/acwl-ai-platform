#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
更新resource_packages表结构
添加template_id、template_type、dynamic_params字段
"""

import asyncio
import sys
sys.path.append('.')
from app.core.database import get_db_context
from sqlalchemy import text
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def update_resource_packages_schema():
    """更新resource_packages表结构，添加新字段"""
    
    async with get_db_context() as db:
        try:
            logger.info("开始更新resource_packages表结构...")
            
            # 1. 检查字段是否已存在
            logger.info("检查现有字段...")
            check_columns_sql = """
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_schema = DATABASE() 
            AND table_name = 'resource_packages' 
            AND column_name IN ('template_id', 'template_type', 'dynamic_params')
            """
            
            result = await db.execute(text(check_columns_sql))
            existing_columns = [row[0] for row in result.fetchall()]
            logger.info(f"已存在的新字段: {existing_columns}")
            
            # 2. 添加template_id字段
            if 'template_id' not in existing_columns:
                logger.info("添加template_id字段...")
                await db.execute(text("""
                    ALTER TABLE resource_packages 
                    ADD COLUMN template_id INT NULL 
                    COMMENT '关联的查询模板ID'
                """))
                logger.info("✅ template_id字段添加成功")
            else:
                logger.info("⏭️ template_id字段已存在，跳过")
            
            # 3. 添加template_type字段
            if 'template_type' not in existing_columns:
                logger.info("添加template_type字段...")
                await db.execute(text("""
                    ALTER TABLE resource_packages 
                    ADD COLUMN template_type ENUM('sql', 'elasticsearch') NULL 
                    COMMENT '模板类型'
                """))
                logger.info("✅ template_type字段添加成功")
            else:
                logger.info("⏭️ template_type字段已存在，跳过")
            
            # 4. 添加dynamic_params字段
            if 'dynamic_params' not in existing_columns:
                logger.info("添加dynamic_params字段...")
                await db.execute(text("""
                    ALTER TABLE resource_packages 
                    ADD COLUMN dynamic_params JSON NULL 
                    COMMENT '动态参数配置，用于覆盖模板中的参数'
                """))
                logger.info("✅ dynamic_params字段添加成功")
            else:
                logger.info("⏭️ dynamic_params字段已存在，跳过")
            
            # 5. 添加外键约束（如果需要的话）
            # 注意：这里我们暂时不添加外键约束，因为需要先迁移数据
            logger.info("暂时不添加外键约束，将在数据迁移后添加")
            
            # 6. 提交更改
            await db.commit()
            logger.info("✅ 数据库结构更新完成！")
            
            # 7. 验证更新结果
            logger.info("验证更新结果...")
            verify_sql = """
            SELECT column_name, data_type, is_nullable, column_comment
            FROM information_schema.columns 
            WHERE table_schema = DATABASE() 
            AND table_name = 'resource_packages' 
            AND column_name IN ('template_id', 'template_type', 'dynamic_params')
            ORDER BY column_name
            """
            
            result = await db.execute(text(verify_sql))
            new_columns = result.fetchall()
            
            print("\n=== 新添加的字段 ===")
            for row in new_columns:
                column_name = row[0]
                data_type = row[1]
                is_nullable = row[2]
                column_comment = row[3] or ''
                print(f'{column_name:20} | {data_type:15} | {is_nullable:8} | {column_comment}')
            
            if len(new_columns) == 3:
                logger.info("✅ 所有字段都已成功添加！")
                return True
            else:
                logger.error(f"❌ 字段添加不完整，预期3个字段，实际{len(new_columns)}个")
                return False
                
        except Exception as e:
            logger.error(f"❌ 更新数据库结构时发生错误: {str(e)}")
            await db.rollback()
            raise

async def main():
    """主函数"""
    try:
        success = await update_resource_packages_schema()
        
        if success:
            print("\n" + "="*50)
            print("🎉 resource_packages表结构更新成功！")
            print("="*50)
            print("新增字段:")
            print("- template_id: 关联的查询模板ID")
            print("- template_type: 模板类型 (sql/elasticsearch)")
            print("- dynamic_params: 动态参数配置")
            print("\n下一步: 执行数据迁移脚本")
        else:
            print("\n❌ 表结构更新失败，请检查日志")
            
    except Exception as e:
        print(f"\n❌ 执行过程中发生错误: {str(e)}")

if __name__ == "__main__":
    asyncio.run(main())