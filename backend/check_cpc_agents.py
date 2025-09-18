import asyncio
import aiomysql

async def check_data():
    """检查cpc_agents表的数据库配置"""
    try:
        # 连接到acwl-ai数据库
        conn = await aiomysql.connect(
            host='localhost',
            port=3306,
            user='root',
            password='123456',
            db='acwl-ai'
        )
        
        cursor = await conn.cursor()
        
        # 查询cpc_agents表的配置
        await cursor.execute(
            "SELECT table_name, database_name FROM acwl_data_resources WHERE table_name LIKE '%cpc_agents%'"
        )
        result = await cursor.fetchall()
        print('cpc_agents表的数据库配置:', result)
        
        # 查询所有数据资源
        await cursor.execute(
            "SELECT id, table_name, database_name FROM acwl_data_resources ORDER BY id"
        )
        all_resources = await cursor.fetchall()
        print('\n所有数据资源:')
        for resource in all_resources:
            print(f"ID: {resource[0]}, 表名: {resource[1]}, 数据库: {resource[2]}")
        
        await cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"查询失败: {e}")

if __name__ == "__main__":
    asyncio.run(check_data())