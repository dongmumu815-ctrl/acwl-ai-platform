#!/usr/bin/env python3
"""调试执行器心跳时间的脚本"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from datetime import datetime
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
from app.models.executor import ExecutorNode

def debug_executor_heartbeat():
    """调试执行器心跳时间"""
    
    # 创建数据库连接
    engine = create_engine(settings.database_url)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    with SessionLocal() as db:
        # 查询所有执行器节点的心跳信息
        result = db.execute(
            select(ExecutorNode.node_id, ExecutorNode.last_heartbeat)
        )
        
        nodes = result.fetchall()
        
        if nodes:
            print(f"找到 {len(nodes)} 个执行器节点:")
            for node in nodes:
                print(f"\n节点ID: {node.node_id}")
                print(f"心跳时间值: {node.last_heartbeat}")
                print(f"心跳时间类型: {type(node.last_heartbeat)}")
                
                # 检查是否为整数或浮点数
                if isinstance(node.last_heartbeat, (int, float)):
                    print(f"⚠️  发现问题：last_heartbeat是数字类型 {type(node.last_heartbeat)}")
                    try:
                        converted_time = datetime.fromtimestamp(node.last_heartbeat)
                        print(f"转换后的时间: {converted_time}")
                    except Exception as e:
                        print(f"转换失败: {e}")
                elif isinstance(node.last_heartbeat, datetime):
                    print("✅ last_heartbeat是正确的datetime类型")
                elif node.last_heartbeat is None:
                    print("ℹ️  last_heartbeat为None")
                else:
                    print(f"❓ 未知类型: {type(node.last_heartbeat)}")
        else:
            print("未找到任何执行器节点")

if __name__ == "__main__":
    debug_executor_heartbeat()