#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修复数据库中的group_type字段值
"""

import pymysql

def fix_group_type():
    """
    修复executor_groups表中的group_type字段值
    """
    try:
        # 连接数据库
        conn = pymysql.connect(
            host='localhost',
            user='root',
            password='123456',
            database='acwl_ai_data',
            charset='utf8mb4'
        )
        
        cursor = conn.cursor()
        
        # 查看当前的group_type值
        cursor.execute('SELECT id, group_name, group_type FROM acwl_executor_groups')
        results = cursor.fetchall()
        
        print('当前分组信息:')
        for row in results:
            print(f'ID: {row[0]}, Name: {row[1]}, Type: {row[2]}')
        
        # 修复group_type字段值
        cursor.execute("UPDATE acwl_executor_groups SET group_type = 'default' WHERE group_type = 'general'")
        updated_rows = cursor.rowcount
        
        conn.commit()
        print(f'已更新 {updated_rows} 行记录')
        
        # 再次查看修复后的值
        cursor.execute('SELECT id, group_name, group_type FROM acwl_executor_groups')
        results = cursor.fetchall()
        
        print('修复后的分组信息:')
        for row in results:
            print(f'ID: {row[0]}, Name: {row[1]}, Type: {row[2]}')
        
        cursor.close()
        conn.close()
        
        print('数据库修复完成')
        
    except Exception as e:
        print(f'修复失败: {e}')

if __name__ == '__main__':
    fix_group_type()