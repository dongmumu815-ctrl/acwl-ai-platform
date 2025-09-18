import pymysql
from app.core.config import settings

def query_datasource_8():
    """查询数据源ID为8的信息"""
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
            'SELECT id, name, datasource_type, host, port, database_name, username, status, connection_params, is_enabled FROM acwl_datasources WHERE id = 8'
        )
        result = cursor.fetchone()
        
        print('数据源信息:')
        if result:
            print(f'ID: {result[0]}')
            print(f'名称: {result[1]}')
            print(f'类型: {result[2]}')
            print(f'主机: {result[3]}')
            print(f'端口: {result[4]}')
            print(f'数据库: {result[5]}')
            print(f'用户名: {result[6]}')
            print(f'状态: {result[7]}')
            print(f'连接参数: {result[8]}')
            print(f'是否启用: {result[9]}')
        else:
            print('未找到ID为8的数据源')
            
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f'查询失败: {str(e)}')

if __name__ == "__main__":
    query_datasource_8()