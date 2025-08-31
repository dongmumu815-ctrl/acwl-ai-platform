import sqlite3

def check_database():
    """检查数据库表和结构"""
    try:
        conn = sqlite3.connect('backend/test.db')
        cursor = conn.cursor()
        
        # 检查所有表
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        
        print('数据库中的表:')
        for table in tables:
            print(f"  {table[0]}")
        
        # 如果有instruction_nodes表，检查其结构
        table_names = [table[0] for table in tables]
        if 'instruction_nodes' in table_names:
            print('\ninstruction_nodes表结构:')
            cursor.execute('PRAGMA table_info(instruction_nodes)')
            rows = cursor.fetchall()
            
            for row in rows:
                print(f"  {row[1]} ({row[2]}) - {'NOT NULL' if row[3] else 'NULL'}")
            
            # 检查是否有keywords字段
            has_keywords = any(row[1] == 'keywords' for row in rows)
            print(f"\n是否有keywords字段: {has_keywords}")
            
            # 如果有keywords字段，查看一些数据
            if has_keywords:
                cursor.execute('SELECT id, title, keywords FROM instruction_nodes LIMIT 5')
                data_rows = cursor.fetchall()
                print("\n前5条记录的keywords数据:")
                for row in data_rows:
                    print(f"  ID: {row[0]}, Title: {row[1]}, Keywords: {row[2]}")
        else:
            print('\ninstruction_nodes表不存在')
        
        conn.close()
        
    except Exception as e:
        print(f"错误: {e}")

if __name__ == '__main__':
    check_database()