#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简化的服务测试脚本
"""

import asyncio
import sys
import os
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.database import get_db
from app.services.executor_cluster import ExecutorClusterService
from app.services.scheduler_cluster import SchedulerClusterService
from app.schemas.executor import ExecutorNodeQueryParams, ExecutorGroupQueryParams
from app.schemas.scheduler import SchedulerNodeQueryParams

async def test_services():
    """
    测试执行器和调度器服务
    """
    print(f"\n开始服务测试 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 50)
    
    try:
        async for db in get_db():
            # 测试执行器服务
            print("\n=== 执行器服务测试 ===")
            executor_service = ExecutorClusterService(db)
            
            # 获取执行器分组
            group_params = ExecutorGroupQueryParams()
            groups, group_total = await executor_service.get_executor_groups(group_params)
            print(f"执行器分组数量: {len(groups)}")
            for group in groups:
                print(f"  - {group.group_name}: {group.display_name}")
            
            # 获取执行器节点
            params = ExecutorNodeQueryParams()
            nodes, total = await executor_service.get_executor_nodes(params)
            print(f"执行器节点数量: {total}")
            for node in nodes:
                print(f"  - {node.node_name} ({node.node_id}): {node.status}")
            
            # 测试调度器服务
            print("\n=== 调度器服务测试 ===")
            scheduler_service = SchedulerClusterService(db)
            
            # 获取调度器节点
            params = SchedulerNodeQueryParams()
            nodes, total = await scheduler_service.get_scheduler_nodes(params)
            print(f"调度器节点数量: {total}")
            for node in nodes:
                print(f"  - {node.node_name} ({node.node_id}): {node.status} [{node.role}]")
            
            # 获取集群状态
            cluster_status = await scheduler_service.get_cluster_status()
            print(f"\n集群状态:")
            print(f"  总节点数: {cluster_status.total_nodes}")
            print(f"  在线节点数: {cluster_status.online_nodes}")
            print(f"  Leader节点: {cluster_status.leader_node_id}")
            print(f"  集群健康度: {cluster_status.cluster_health}")
            
            break
            
    except Exception as e:
        print(f"测试失败: {e}")
        import traceback
        traceback.print_exc()
    
    print(f"\n测试完成 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 50)

if __name__ == "__main__":
    asyncio.run(test_services())