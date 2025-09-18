#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
插入数据源模板数据脚本
"""

import pymysql
import re

def insert_datasource_templates():
    """
    从迁移文件中提取并插入数据源模板数据
    """
    try:
        # 连接数据库
        conn = pymysql.connect(
            host='localhost',
            user='root',
            password='2wsx1QAZaczt',
            database='acwl-ai-data',
            charset='utf8mb4'
        )
        cursor = conn.cursor()
        
        # 读取迁移文件
        with open('migrations/003_add_datasource_tables.sql', 'r', encoding='utf-8') as f:
            sql_content = f.read()
        
        # 提取INSERT语句
        insert_pattern = r"INSERT INTO acwl_datasource_templates.*?VALUES\s*\((.*?)\);"
        matches = re.findall(insert_pattern, sql_content, re.DOTALL | re.IGNORECASE)
        
        print(f"找到 {len(matches)} 条插入语句")
        
        if matches:
            # 构建完整的INSERT语句
            insert_sql = """
            INSERT INTO acwl_datasource_templates 
            (name, description, datasource_type, default_port, default_params, 
             connection_url_template, driver_class, validation_query, is_system) 
            VALUES
            """
            
            # 添加所有VALUES子句
            values_clauses = []
            for match in matches:
                values_clauses.append(f"({match})")
            
            full_sql = insert_sql + ",\n".join(values_clauses)
            
            # 执行插入
            cursor.execute(full_sql)
            conn.commit()
            
            # 检查结果
            cursor.execute('SELECT COUNT(*) FROM acwl_datasource_templates')
            result = cursor.fetchone()
            print(f"插入后模板表记录数: {result[0]}")
            
            # 显示插入的模板
            cursor.execute('SELECT name, datasource_type, default_port FROM acwl_datasource_templates ORDER BY datasource_type')
            templates = cursor.fetchall()
            print("\n已插入的数据源模板:")
            for template in templates:
                print(f"- {template[0]} ({template[1]}) - 端口: {template[2]}")
        else:
            print("未找到INSERT语句")
        
        cursor.close()
        conn.close()
        print("\n数据源模板插入完成！")
        
    except Exception as e:
        print(f"插入失败: {e}")
        if 'conn' in locals():
            conn.rollback()
            conn.close()

if __name__ == "__main__":
    insert_datasource_templates()