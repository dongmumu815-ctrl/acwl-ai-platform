import asyncio
from app.database import get_db
from app.services.datasource import DatasourceService

async def check_datasource():
    """检查数据源8的配置信息"""
    try:
        # 获取数据库会话
        db_gen = get_db()
        db = next(db_gen)
        
        # 创建服务实例
        service = DatasourceService(db)
        
        # 获取数据源信息
        ds = await service.get_datasource(8)
        
        if ds:
            print(f"数据源信息:")
            print(f"  ID: {ds.id}")
            print(f"  名称: {ds.name}")
            print(f"  类型: {ds.datasource_type}")
            print(f"  主机: {ds.host}")
            print(f"  端口: {ds.port}")
            print(f"  数据库: {ds.database}")
            print(f"  用户名: {ds.username}")
            print(f"  状态: {ds.status}")
        else:
            print("数据源8不存在")
            
    except Exception as e:
        print(f"检查数据源失败: {str(e)}")
    finally:
        if 'db' in locals():
            await db.close()

if __name__ == "__main__":
    asyncio.run(check_datasource())