import pymysql
import re
from app.core.config import settings

def extract_table_name_from_sql(sql: str) -> str:
    """
    从SQL语句中提取表名
    
    Args:
        sql: SQL查询语句
        
    Returns:
        表名
    """
    # 移除注释和多余空格
    sql = re.sub(r'--.*?\n', ' ', sql)
    sql = re.sub(r'/\*.*?\*/', ' ', sql, flags=re.DOTALL)
    sql = re.sub(r'\s+', ' ', sql).strip()
    
    # 匹配FROM子句中的表名
    pattern = r'\bFROM\s+([`"\[]?)(\w+)([`"\]]?)(?:\s+(?:AS\s+)?\w+)?'
    match = re.search(pattern, sql, re.IGNORECASE)
    
    if match:
        return match.group(2)
    
    return None

def get_database_name_for_table(table_name: str, datasource_id: int) -> str:
    """
    根据表名和数据源ID获取对应的数据库名称
    
    Args:
        table_name: 表名
        datasource_id: 数据源ID
        
    Returns:
        数据库名称
    """
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
        
        # 首先查找数据资源表中是否有对应的记录
        cursor.execute(
            'SELECT database_name FROM acwl_data_resources WHERE table_name = %s AND datasource_id = %s',
            (table_name, datasource_id)
        )
        result = cursor.fetchone()
        
        if result and result[0]:
            print(f'从数据资源表找到表 {table_name} 对应的数据库: {result[0]}')
            cursor.close()
            conn.close()
            return result[0]
        
        # 如果数据资源表中没有找到，则使用数据源配置中的database_name
        cursor.execute(
            'SELECT database_name FROM acwl_datasources WHERE id = %s',
            (datasource_id,)
        )
        result = cursor.fetchone()
        
        if result and result[0]:
            print(f'从数据源配置找到数据源 {datasource_id} 对应的数据库: {result[0]}')
            cursor.close()
            conn.close()
            return result[0]
        
        cursor.close()
        conn.close()
        return None
        
    except Exception as e:
        print(f'查询数据库名称失败: {str(e)}')
        return None

def test_query_logic():
    """
    测试查询逻辑
    """
    # 测试SQL解析
    test_sql = "SELECT name, description, parent_id FROM cpc_agents ORDER BY id DESC LIMIT 100"
    table_name = extract_table_name_from_sql(test_sql)
    print(f'从SQL中提取的表名: {table_name}')
    
    if table_name:
        # 测试数据库名称查找
        database_name = get_database_name_for_table(table_name, 8)
        print(f'表 {table_name} 对应的数据库名称: {database_name}')
        
        if database_name:
            print(f'建议的修复方案: 在查询前使用 USE `{database_name}` 语句')
        else:
            print('未找到对应的数据库名称，需要检查数据配置')
    else:
        print('无法从SQL中提取表名')

if __name__ == "__main__":
    test_query_logic()