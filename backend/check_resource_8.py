import asyncio
import pymysql
from app.core.config import settings

def check_data_resource_8():
    """检查数据资源ID为8的信息"""
    try:
        conn = pymysql.connect(
            host=settings.DB_HOST,
            port=settings.DB_PORT,
            user=settings.DB_USER,
            password=settings.DB_PASSWORD,
            database=settings.DB_NAME,
            charset='utf8mb4'
        )
        
        cursor = conn.cursor()
        
        # 查询数据资源表
        cursor.execute(
            'SELECT id, name, display_name, resource_type, datasource_id, status, is_public, created_by FROM acwl_data_resources WHERE id = 8'
        )
        result = cursor.fetchone()
        
        print('数据资源信息:')
        if result:
            print(f'ID: {result[0]}')
            print(f'名称: {result[1]}')
            print(f'显示名称: {result[2]}')
            print(f'资源类型: {result[3]}')
            print(f'数据源ID: {result[4]}')
            print(f'状态: {result[5]}')
            print(f'是否公开: {result[6]}')
            print(f'创建者: {result[7]}')
        else:
            print('未找到ID为8的数据资源')
            
        # 查询所有数据资源的ID
        cursor.execute('SELECT id, name FROM acwl_data_resources ORDER BY id')
        all_resources = cursor.fetchall()
        print('\n所有数据资源:')
        for resource in all_resources:
            print(f'ID: {resource[0]}, 名称: {resource[1]}')
            
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f'查询失败: {str(e)}')

if __name__ == "__main__":
    check_data_resource_8()