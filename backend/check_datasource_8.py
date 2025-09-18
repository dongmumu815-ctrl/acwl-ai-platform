import asyncio
from app.core.database import get_db
from app.models.datasource import Datasource
from sqlalchemy import select

async def check_datasource():
    """检查数据源ID为8的配置信息"""
    async for db in get_db():
        try:
            result = await db.execute(select(Datasource).where(Datasource.id == 8))
            datasource = result.scalar_one_or_none()
            
            if datasource:
                print(f'数据源名称: {datasource.name}')
                print(f'类型: {datasource.datasource_type}')
                print(f'主机: {datasource.host}')
                print(f'端口: {datasource.port}')
                print(f'数据库: {datasource.database_name}')
                print(f'用户名: {datasource.username}')
                print(f'状态: {datasource.status}')
                print(f'连接参数: {datasource.connection_params}')
                print(f'是否启用: {datasource.is_enabled}')
                print(f'最后测试时间: {datasource.last_test_time}')
                print(f'最后测试结果: {datasource.last_test_result}')
            else:
                print('数据源ID为8的记录不存在')
        except Exception as e:
            print(f'查询失败: {str(e)}')
        break

if __name__ == "__main__":
    asyncio.run(check_datasource())