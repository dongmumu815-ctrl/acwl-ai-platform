#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查数据表结构
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import text
from app.core.database import engine

def check_data_uploads_structure():
    """
    检查 data_uploads 表结构
    """
    try:
        with engine.connect() as connection:
            # 查看表结构
            result = connection.execute(text('DESCRIBE data_uploads'))
            columns = result.fetchall()
            
            print("当前 data_uploads 表结构:")
            print("-" * 80)
            print(f"{'字段名':<25} {'类型':<20} {'允许NULL':<10} {'键':<10} {'默认值':<15} {'额外':<15}")
            print("-" * 80)
            
            for col in columns:
                print(f"{col[0]:<25} {col[1]:<20} {col[2]:<10} {col[3]:<10} {str(col[4]):<15} {col[5]:<15}")
            
            print(f"\n总共 {len(columns)} 个字段")
            
    except Exception as e:
        print(f"检查表结构失败: {e}")

if __name__ == "__main__":
    check_data_uploads_structure()