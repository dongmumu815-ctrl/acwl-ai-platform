#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试执行器和调度器服务

用于验证执行器和调度器服务的基本功能
"""

import asyncio
import sys
import os
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.database import get_db
from app.services.executor_cluster import ExecutorClusterService
from app.services.scheduler_cluster import SchedulerClusterService
from app.schemas.executor import ExecutorGroupQueryParams
from app.schemas.scheduler import SchedulerNodeQueryParams


async def test_executor_service():
    """
    测试执行器服务
    """
    print("\n=== 测试执行器服务 ===")
    
    try:
        async for db in get_db():
            service = ExecutorClusterService(db)
            
            # 1. 测试获取执行器分组
            print("\n1. 获取执行器分组:")
            params = ExecutorGroupQueryParams()
            groups, total = await service.get_executor_groups(params)
            print(f"   找到 {total} 个执行器分组")
            for group in groups:
                print(f"   - 分组: {group.group_name} ({group.display_name})")
                print(f"     ID: {group.id}, 类型: {group.group_type}")
                print(f"     最大并发任务: {group.max_concurrent_tasks}")
            
            # 2. 测试获取执行器节点
            print("\n2. 获取执行器节点:")
            from app.schemas.executor import ExecutorNodeQueryParams
            node_params = ExecutorNodeQueryParams()
            nodes, node_total = await service.get_executor_nodes(node_params)
            print(f"   找到 {node_total} 个执行器节点")
            for node in nodes:
                print(f"   - 节点: {node.node_name} ({node.node_id[:8]}...)")
                print(f"     状态: {node.status}, 地址: {node.host_ip}:{node.port}")
                print(f"     当前负载: {node.current_load}/{node.max_concurrent_tasks}")
                print(f"     最后心跳: {node.last_heartbeat}")
                
                # 检查资源使用情况
                if hasattr(node, 'resource_usage') and node.resource_usage:
                    resource = node.resource_usage
                    if isinstance(resource, dict):
                        cpu = resource.get('cpu_percent', 'N/A')
                        memory = resource.get('memory_percent', 'N/A')
                        print(f"     资源使用: CPU {cpu}%, 内存 {memory}%")
            
            # 3. 测试集群状态
            print("\n3. 执行器集群状态:")
            cluster_status = await service.get_cluster_status()
            print(f"   总节点数: {cluster_status.total_nodes}")
            print(f"   在线节点数: {cluster_status.online_nodes}")
            print(f"   离线节点数: {cluster_status.offline_nodes}")
            print(f"   总任务容量: {cluster_status.total_capacity}")
            print(f"   当前负载: {cluster_status.current_load}")
            
            break
            
    except Exception as e:
        print(f"   执行器服务测试失败: {e}")
        import traceback
        traceback.print_exc()


async def test_scheduler_service():
    """
    测试调度器服务
    """
    print("\n=== 测试调度器服务 ===")
    
    try:
        async for db in get_db():
            service = SchedulerClusterService(db)
            
            # 1. 测试获取调度器节点
            print("\n1. 获取调度器节点:")
            params = SchedulerNodeQueryParams()
            nodes, total = await service.get_scheduler_nodes(params)
            print(f"   找到 {total} 个调度器节点")
            for node in nodes:
                print(f"   - 节点: {node.node_name} ({node.node_id[:8]}...)")
                print(f"     状态: {node.status}, 角色: {node.role}")
                print(f"     地址: {node.host_ip}:{node.port}")
                print(f"     最后心跳: {node.last_heartbeat}")
                
                # 检查是否是Leader
                if hasattr(node, 'role') and node.role == 'leader':
                    print(f"     *** 这是Leader节点 ***")
                    if hasattr(node, 'leader_lease_expires'):
                        print(f"     Leader租约到期: {node.leader_lease_expires}")
            
            # 2. 测试集群状态
            print("\n2. 调度器集群状态:")
            cluster_status = await service.get_cluster_status()
            print(f"   总节点数: {cluster_status.total_nodes}")
            print(f"   在线节点数: {cluster_status.online_nodes}")
            print(f"   Leader节点ID: {cluster_status.leader_node_id or '无'}")
            print(f"   集群健康状态: {cluster_status.health_status}")
            
            # 3. 测试Leader选举状态
            if cluster_status.leader_node_id:
                print(f"\n3. Leader选举状态: 已选举")
                print(f"   当前Leader: {cluster_status.leader_node_id}")
            else:
                print(f"\n3. Leader选举状态: 未选举或选举中")
                print(f"   建议触发Leader选举")
            
            break
            
    except Exception as e:
        print(f"   调度器服务测试失败: {e}")
        import traceback
        traceback.print_exc()


async def test_service_communication():
    """
    测试服务间通信
    """
    print("\n=== 测试服务间通信 ===")
    
    try:
        async for db in get_db():
            executor_service = ExecutorClusterService(db)
            scheduler_service = SchedulerClusterService(db)
            
            # 1. 检查执行器和调度器是否都在线
            print("\n1. 检查服务在线状态:")
            
            from app.schemas.executor import ExecutorNodeQueryParams
            executor_params = ExecutorNodeQueryParams()
            executor_nodes, _ = await executor_service.get_executor_nodes(executor_params)
            online_executors = [n for n in executor_nodes if n.status == 'ONLINE']
            print(f"   在线执行器节点: {len(online_executors)}")
            
            scheduler_params = SchedulerNodeQueryParams()
            scheduler_nodes, _ = await scheduler_service.get_scheduler_nodes(scheduler_params)
            online_schedulers = [n for n in scheduler_nodes if n.status in ['running', 'standby']]
            print(f"   在线调度器节点: {len(online_schedulers)}")
            
            # 2. 检查Leader状态
            cluster_status = await scheduler_service.get_cluster_status()
            if cluster_status.leader_node_id:
                print(f"   调度器Leader: {cluster_status.leader_node_id}")
                print(f"   ✅ 集群状态正常")
            else:
                print(f"   ⚠️  没有调度器Leader")
            
            # 3. 模拟基本的服务发现
            print("\n2. 服务发现测试:")
            if online_executors and online_schedulers:
                print(f"   ✅ 执行器和调度器都在线，可以进行任务调度")
                print(f"   执行器总容量: {sum(n.max_concurrent_tasks for n in online_executors)}")
                print(f"   当前总负载: {sum(n.current_load for n in online_executors)}")
            else:
                print(f"   ⚠️  服务不完整，无法进行任务调度")
            
            break
            
    except Exception as e:
        print(f"   服务通信测试失败: {e}")
        import traceback
        traceback.print_exc()


async def main():
    """
    主测试函数
    """
    print(f"开始测试服务 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 50)
    
    # 运行所有测试
    await test_executor_service()
    await test_scheduler_service()
    await test_service_communication()
    
    print("\n" + "=" * 50)
    print(f"测试完成 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n测试被用户中断")
    except Exception as e:
        print(f"测试异常退出: {e}")
        sys.exit(1)