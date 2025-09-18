import pymysql
from app.core.config import settings

def check_databases():
    """检查MySQL中实际存在的数据库"""
    try:
        conn = pymysql.connect(
            host=settings.DB_HOST,
            port=settings.DB_PORT,
            user=settings.DB_USER,
            password=settings.DB_PASSWORD,
            charset='utf8mb4'
        )
        
        cursor = conn.cursor()
        cursor.execute('SHOW DATABASES')
        databases = cursor.fetchall()
        
        print('MySQL中存在的数据库:')
        for db in databases:
            print(f'  - {db[0]}')
            
        # 检查是否存在acwl-ai数据库
        db_names = [db[0] for db in databases]
        if 'acwl-ai' in db_names:
            print('\n✓ acwl-ai 数据库存在')
        else:
            print('\n✗ acwl-ai 数据库不存在')
            
        # 检查是否存在类似名称的数据库
        similar_dbs = [db for db in db_names if 'acwl' in db.lower()]
        if similar_dbs:
            print(f'\n包含"acwl"的数据库: {similar_dbs}')
            
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f'检查数据库失败: {str(e)}')

if __name__ == "__main__":
    check_databases()