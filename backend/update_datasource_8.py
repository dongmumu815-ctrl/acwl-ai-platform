import pymysql
from app.core.config import settings

def update_datasource_8():
    """更新数据源8的database_name字段"""
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
        cursor.execute(
            "UPDATE acwl_datasources SET database_name = 'acwl-agents' WHERE id = 8"
        )
        conn.commit()
        
        print('数据源8的database_name已更新为acwl-agents')
        
        # 验证更新结果
        cursor.execute(
            'SELECT id, name, database_name FROM acwl_datasources WHERE id = 8'
        )
        result = cursor.fetchone()
        
        if result:
            print(f'更新后的数据源信息: ID={result[0]}, 名称={result[1]}, 数据库={result[2]}')
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f'更新失败: {str(e)}')

if __name__ == "__main__":
    update_datasource_8()