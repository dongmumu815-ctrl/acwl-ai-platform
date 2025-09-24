#!/usr/bin/env python3
"""
更新数据库中的SQL模板，使用Jinja2条件语法
"""

import sqlite3
import os

def update_sql_template():
    """
    更新SQL模板为Jinja2条件语法
    """
    # 数据库文件路径
    db_path = os.path.join(os.path.dirname(__file__), "app.db")
    
    if not os.path.exists(db_path):
        print(f"❌ 数据库文件不存在: {db_path}")
        return
    
    try:
        # 连接数据库
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 新的SQL模板（使用Jinja2条件语法）
        new_sql_template = """SELECT name, description, parent_id, id 
FROM cpc_agents 
WHERE node_type = 'agent'
{% if description %} AND description = '{{ description }}'{% endif %}
{% if name %} AND name = '{{ name }}'{% endif %}
ORDER BY id DESC LIMIT 1000"""
        
        print("🔄 更新SQL模板...")
        print(f"新模板内容:\n{new_sql_template}")
        
        # 更新ID为4的SQL模板
        cursor.execute("""
            UPDATE sql_query_templates 
            SET content = ? 
            WHERE id = 4
        """, (new_sql_template,))
        
        # 提交更改
        conn.commit()
        
        # 验证更新
        cursor.execute("SELECT id, name, content FROM sql_query_templates WHERE id = 4")
        result = cursor.fetchone()
        
        if result:
            print(f"✅ SQL模板更新成功!")
            print(f"模板ID: {result[0]}")
            print(f"模板名称: {result[1]}")
            print(f"更新后内容:\n{result[2]}")
        else:
            print("❌ 未找到ID为4的SQL模板")
        
        conn.close()
        
    except sqlite3.Error as e:
        print(f"❌ 数据库操作失败: {e}")
    except Exception as e:
        print(f"❌ 更新失败: {e}")

if __name__ == "__main__":
    update_sql_template()