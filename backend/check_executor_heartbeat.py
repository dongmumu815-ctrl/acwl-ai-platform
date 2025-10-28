#!/usr/bin/env python3
"""
检查ExecutorNode表中last_heartbeat字段的数据类型
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
from app.models.executor import ExecutorNode
from datetime import datetime

def check_executor_heartbeat_types():
    """检查ExecutorNode表中last_heartbeat字段的数据类型"""
    
    # 创建数据库连接
    engine = create_engine(settings.database_url)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    with SessionLocal() as db:
        try:
            # 查询前10个ExecutorNode记录
            nodes = db.query(ExecutorNode).limit(10).all()
            
            print(f"检查到 {len(nodes)} 个ExecutorNode记录:")
            print("-" * 80)
            
            for node in nodes:
                print(f"ID: {node.id}")
                print(f"Node ID: {node.node_id}")
                print(f"Node Name: {node.node_name}")
                print(f"Last Heartbeat: {node.last_heartbeat}")
                print(f"Last Heartbeat Type: {type(node.last_heartbeat)}")
                
                # 检查是否为int或float类型
                if isinstance(node.last_heartbeat, (int, float)):
                    print(f"⚠️  发现异常类型: {type(node.last_heartbeat)} - 值: {node.last_heartbeat}")
                
                print("-" * 40)
                
        except Exception as e:
            print(f"查询失败: {e}")

if __name__ == "__main__":
    check_executor_heartbeat_types()