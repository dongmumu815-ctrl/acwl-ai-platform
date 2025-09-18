#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
服务器管理API测试脚本
"""

import asyncio
import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db_context
from app.models.server import Server, GPUResource, ServerType, ServerStatus
from app.services.server_service import ServerService


async def test_server_operations():
    """
    测试服务器管理操作
    """
    print("开始测试服务器管理功能...")
    
    async with get_db_context() as db:
        server_service = ServerService(db)
        
        # 测试创建服务器
        print("\n1. 测试创建服务器")
        server_data = {
            "name": "测试服务器-01",
            "ip_address": "192.168.1.100",
            "ssh_port": 22,
            "ssh_username": "ubuntu",
            "server_type": ServerType.physical,
            "os_info": "Ubuntu 22.04 LTS",
            "status": ServerStatus.offline,
            "total_memory": "64GB",
            "total_storage": "1TB",
            "total_cpu_cores": 16
        }
        
        try:
            server = await server_service.create_server(server_data, user_id=1)
            print(f"✓ 服务器创建成功: {server['name']} (ID: {server['id']})")
            server_id = server["id"]
        except Exception as e:
            print(f"✗ 服务器创建失败: {str(e)}")
            return
        
        # 测试获取服务器列表
        print("\n2. 测试获取服务器列表")
        try:
            servers = await server_service.get_servers()
            print(f"✓ 获取到 {len(servers['items'])} 台服务器")
            for server in servers['items']:
                print(f"  - {server['name']} ({server['ip_address']}) - {server['status']}")
        except Exception as e:
            print(f"✗ 获取服务器列表失败: {str(e)}")
        
        # 测试更新服务器状态
        print("\n3. 测试更新服务器状态")
        try:
            update_data = {"status": ServerStatus.online}
            updated_server = await server_service.update_server(server_id, update_data)
            print(f"✓ 服务器状态更新成功: {updated_server['status']}")
        except Exception as e:
            print(f"✗ 更新服务器状态失败: {str(e)}")
        
        # 测试添加GPU资源
        print("\n4. 测试添加GPU资源")
        gpu_data = {
            "server_id": server_id,
            "gpu_name": "NVIDIA RTX 4090",
            "gpu_type": "RTX 4090",
            "memory_size": "24GB",
            "cuda_version": "12.2",
            "device_id": "0",
            "is_available": True
        }
        
        try:
            gpu = await server_service.add_gpu_resource(gpu_data)
            print(f"✓ GPU资源添加成功: {gpu['gpu_name']} (ID: {gpu['id']})")
        except Exception as e:
            print(f"✗ 添加GPU资源失败: {str(e)}")
        
        # 测试获取服务器GPU资源
        print("\n5. 测试获取服务器GPU资源")
        try:
            gpus = await server_service.get_server_gpus(server_id)
            print(f"✓ 获取到 {len(gpus)} 个GPU资源")
            for gpu in gpus:
                print(f"  - {gpu['gpu_name']} ({gpu['memory_size']}) - 可用: {gpu['is_available']}")
        except Exception as e:
            print(f"✗ 获取GPU资源失败: {str(e)}")
        
        # 测试获取服务器详情
        print("\n6. 测试获取服务器详情")
        try:
            server_detail = await server_service.get_server(server_id)
            print(f"✓ 服务器详情获取成功:")
            print(f"  名称: {server_detail['name']}")
            print(f"  IP: {server_detail['ip_address']}")
            print(f"  状态: {server_detail['status']}")
            print(f"  GPU数量: {len(server_detail.get('gpu_resources', []))}")
        except Exception as e:
            print(f"✗ 获取服务器详情失败: {str(e)}")
        
        # 测试删除服务器
        print("\n7. 测试删除服务器")
        try:
            await server_service.delete_server(server_id)
            print(f"✓ 服务器删除成功")
        except Exception as e:
            print(f"✗ 删除服务器失败: {str(e)}")
    
    print("\n测试完成!")


async def test_database_connection():
    """
    测试数据库连接
    """
    print("测试数据库连接...")
    
    try:
        # 使用get_db_context上下文管理器获取数据库会话
        async with get_db_context() as db:
            # 简单查询测试
            from sqlalchemy import text
            result = await db.execute(text("SELECT 1 as test"))
            row = result.fetchone()
            if row and row[0] == 1:
                print("✓ 数据库连接成功")
                return True
            else:
                print("✗ 数据库查询结果异常")
                return False
    except Exception as e:
        print(f"✗ 数据库连接失败: {str(e)}")
        return False


async def main():
    """
    主测试函数
    """
    print("=" * 50)
    print("服务器管理系统测试")
    print("=" * 50)
    
    # 测试数据库连接
    if not await test_database_connection():
        print("数据库连接失败，退出测试")
        return
    
    # 测试服务器操作
    await test_server_operations()


if __name__ == "__main__":
    # 使用asyncio.run()运行主函数，它会自动创建新的事件循环
    # 并在完成后关闭它，避免资源泄漏
    asyncio.run(main())