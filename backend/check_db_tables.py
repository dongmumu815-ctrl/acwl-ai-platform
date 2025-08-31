import sys
import asyncio
sys.path.append('.')

from app.core.database import engine
from sqlalchemy import text

async def check_tables():
    """检查数据库表结构"""
    async with engine.begin() as conn:
        # 检查 acwl_model_service_configs 表是否存在
        result = await conn.execute(text("""
            SELECT COUNT(*) as count 
            FROM information_schema.tables 
            WHERE table_schema = DATABASE() 
            AND table_name = 'acwl_model_service_configs'
        """))
        
        model_service_configs_exists = result.fetchone()[0] > 0
        print(f"acwl_model_service_configs 表存在: {model_service_configs_exists}")
        
        if model_service_configs_exists:
            # 检查表结构
            result = await conn.execute(text("""
                DESCRIBE acwl_model_service_configs
            """))
            print("\nacwl_model_service_configs 表结构:")
            for row in result:
                print(f"  {row[0]} - {row[1]} - {row[2]} - {row[3]} - {row[4]} - {row[5]}")
        
        # 检查 acwl_agents 表结构
        result = await conn.execute(text("""
            SELECT COUNT(*) as count 
            FROM information_schema.tables 
            WHERE table_schema = DATABASE() 
            AND table_name = 'acwl_agents'
        """))
        
        agents_exists = result.fetchone()[0] > 0
        print(f"\nacwl_agents 表存在: {agents_exists}")
        
        if agents_exists:
            result = await conn.execute(text("""
                DESCRIBE acwl_agents
            """))
            print("\nacwl_agents 表结构:")
            for row in result:
                print(f"  {row[0]} - {row[1]} - {row[2]} - {row[3]} - {row[4]} - {row[5]}")

if __name__ == "__main__":
    asyncio.run(check_tables())