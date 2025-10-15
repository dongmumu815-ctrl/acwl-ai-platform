#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查 data_batches 表结构
"""

from app.core.database import engine
from sqlalchemy import text

def check_data_batches_table():
    """
    检查 data_batches 表的字段结构
    """
    try:
        with engine.connect() as conn:
            result = conn.execute(text('DESCRIBE data_batches'))
            print("data_batches 表结构:")
            print("-" * 50)
            for row in result:
                print(f"{row[0]}: {row[1]} {row[2] if row[2] == 'YES' else 'NOT NULL'} {row[4] if row[4] else ''}")
    except Exception as e:
        print(f"检查表结构失败: {e}")

if __name__ == "__main__":
    check_data_batches_table()