#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Doris集成功能测试脚本

测试Doris客户端的各项功能，包括连接、写入、查询等。
用于验证Doris集成是否正常工作。

Author: System
Date: 2024
"""

import sys
import time
import asyncio
from pathlib import Path
from datetime import datetime, timedelta

# 添加项目根目录到Python路径
sys.path.append(str(Path(__file__).parent))

from app.core.config import settings
from app.core.doris_client import DorisClient, get_doris_client, log_api_access_to_doris
from app.core.logging import log_api_access, setup_logging
from loguru import logger


def test_configuration():
    """
    测试配置信息
    
    Returns:
        bool: 配置是否正确
    """
    print("\n=== 测试配置信息 ===")
    
    print(f"Doris启用状态: {settings.DORIS_ENABLED}")
    print(f"Doris主机: {settings.DORIS_HOST}")
    print(f"HTTP端口: {settings.DORIS_HTTP_PORT}")
    print(f"查询端口: {settings.DORIS_QUERY_PORT}")
    print(f"用户名: {settings.DORIS_USER}")
    print(f"数据库: {settings.DORIS_DATABASE}")
    print(f"表名: {settings.DORIS_ACCESS_LOG_TABLE}")
    print(f"批量大小: {settings.DORIS_BATCH_SIZE}")
    print(f"刷新间隔: {settings.DORIS_FLUSH_INTERVAL}秒")
    
    if not settings.DORIS_ENABLED:
        print("⚠️  Doris未启用，请在配置中设置 DORIS_ENABLED=True")
        return False
    
    print("✅ 配置检查通过")
    return True


def test_client_creation():
    """
    测试客户端创建
    
    Returns:
        bool: 客户端创建是否成功
    """
    print("\n=== 测试客户端创建 ===")
    
    try:
        # 创建新的客户端实例
        client = DorisClient()
        
        print(f"客户端启用状态: {client.enabled}")
        print(f"后台任务运行状态: {client.background_task_running}")
        print(f"队列大小: {client.log_queue.qsize()}")
        print(f"缓冲区大小: {len(client.batch_buffer)}")
        
        # 获取全局客户端实例
        global_client = get_doris_client()
        print(f"全局客户端启用状态: {global_client.enabled}")
        
        print("✅ 客户端创建成功")
        return True
        
    except Exception as e:
        print(f"❌ 客户端创建失败: {e}")
        return False


def test_database_connection():
    """
    测试数据库连接
    
    Returns:
        bool: 连接是否成功
    """
    print("\n=== 测试数据库连接 ===")
    
    try:
        import pymysql
        
        # 测试查询端口连接
        connection = pymysql.connect(
            host=settings.DORIS_HOST,
            port=settings.DORIS_QUERY_PORT,
            user=settings.DORIS_USER,
            password=settings.DORIS_PASSWORD,
            charset='utf8mb4',
            connect_timeout=10
        )
        
        with connection.cursor() as cursor:
            cursor.execute("SELECT VERSION()")
            version = cursor.fetchone()
            print(f"Doris版本: {version[0]}")
            
            cursor.execute("SHOW DATABASES")
            databases = cursor.fetchall()
            print(f"可用数据库: {[db[0] for db in databases]}")
        
        connection.close()
        print("✅ 数据库连接成功")
        return True
        
    except Exception as e:
        print(f"❌ 数据库连接失败: {e}")
        return False


def test_table_operations():
    """
    测试表操作
    
    Returns:
        bool: 表操作是否成功
    """
    print("\n=== 测试表操作 ===")
    
    try:
        client = get_doris_client()
        
        if not client.enabled:
            print("❌ Doris客户端未启用")
            return False
        
        # 创建表
        print("创建数据库和表...")
        client.create_table_if_not_exists()
        
        # 验证表是否存在
        import pymysql
        connection = pymysql.connect(
            host=settings.DORIS_HOST,
            port=settings.DORIS_QUERY_PORT,
            user=settings.DORIS_USER,
            password=settings.DORIS_PASSWORD,
            database=settings.DORIS_DATABASE,
            charset='utf8mb4'
        )
        
        with connection.cursor() as cursor:
            cursor.execute(f"SHOW TABLES LIKE '{settings.DORIS_ACCESS_LOG_TABLE}'")
            table_exists = cursor.fetchone()
            
            if table_exists:
                print(f"✅ 表 {settings.DORIS_ACCESS_LOG_TABLE} 存在")
                
                # 获取表结构
                cursor.execute(f"DESCRIBE {settings.DORIS_ACCESS_LOG_TABLE}")
                columns = cursor.fetchall()
                print(f"表字段数量: {len(columns)}")
                
                # 获取表行数
                cursor.execute(f"SELECT COUNT(*) FROM {settings.DORIS_ACCESS_LOG_TABLE}")
                row_count = cursor.fetchone()[0]
                print(f"当前数据行数: {row_count}")
            else:
                print(f"❌ 表 {settings.DORIS_ACCESS_LOG_TABLE} 不存在")
                return False
        
        connection.close()
        return True
        
    except Exception as e:
        print(f"❌ 表操作失败: {e}")
        return False


def test_data_insertion():
    """
    测试数据插入
    
    Returns:
        bool: 数据插入是否成功
    """
    print("\n=== 测试数据插入 ===")
    
    try:
        client = get_doris_client()
        
        if not client.enabled:
            print("❌ Doris客户端未启用")
            return False
        
        # 记录插入前的队列状态
        initial_queue_size = client.log_queue.qsize()
        initial_buffer_size = len(client.batch_buffer)
        
        print(f"插入前队列大小: {initial_queue_size}")
        print(f"插入前缓冲区大小: {initial_buffer_size}")
        
        # 插入测试数据
        test_data = [
            {
                "method": "GET",
                "url": "/api/v1/test/1",
                "status_code": 200,
                "response_time": 0.123,
                "client_ip": "192.168.1.100",
                "user_agent": "Test Agent 1.0",
                "user_id": "test_user_1"
            },
            {
                "method": "POST",
                "url": "/api/v1/test/2",
                "status_code": 201,
                "response_time": 0.456,
                "client_ip": "192.168.1.101",
                "user_agent": "Test Agent 2.0",
                "user_id": "test_user_2",
                "request_size": 1024,
                "response_size": 2048
            },
            {
                "method": "PUT",
                "url": "/api/v1/test/3",
                "status_code": 500,
                "response_time": 1.234,
                "client_ip": "192.168.1.102",
                "user_agent": "Test Agent 3.0",
                "user_id": "test_user_3",
                "error_message": "Internal Server Error"
            }
        ]
        
        print(f"插入 {len(test_data)} 条测试数据...")
        
        for i, data in enumerate(test_data):
            client.log_access(**data)
            print(f"  插入第 {i+1} 条数据: {data['method']} {data['url']}")
        
        # 等待数据处理
        print("等待数据处理...")
        time.sleep(2)
        
        # 检查队列状态
        final_queue_size = client.log_queue.qsize()
        final_buffer_size = len(client.batch_buffer)
        
        print(f"插入后队列大小: {final_queue_size}")
        print(f"插入后缓冲区大小: {final_buffer_size}")
        
        # 强制刷新缓冲区
        if hasattr(client, '_flush_batch') and final_buffer_size > 0:
            print("强制刷新缓冲区...")
            client._flush_batch()
            time.sleep(1)
        
        print("✅ 数据插入完成")
        return True
        
    except Exception as e:
        print(f"❌ 数据插入失败: {e}")
        return False


def test_data_query():
    """
    测试数据查询
    
    Returns:
        bool: 数据查询是否成功
    """
    print("\n=== 测试数据查询 ===")
    
    try:
        client = get_doris_client()
        
        if not client.enabled:
            print("❌ Doris客户端未启用")
            return False
        
        # 等待数据写入完成
        print("等待数据写入完成...")
        time.sleep(3)
        
        # 查询所有数据
        print("查询最近的访问记录...")
        results = client.query_access_logs(limit=10)
        
        if results:
            print(f"✅ 查询成功，找到 {len(results)} 条记录")
            
            print("\n最近的访问记录:")
            print("-" * 100)
            print(f"{'时间':<20} {'方法':<6} {'URL':<25} {'状态码':<6} {'响应时间':<8} {'客户端IP':<15}")
            print("-" * 100)
            
            for result in results[:5]:  # 只显示前5条
                timestamp = str(result.get('timestamp', ''))[:19]
                method = result.get('method', '')
                url = result.get('url', '')[:23] + '...' if len(result.get('url', '')) > 25 else result.get('url', '')
                status_code = result.get('status_code', '')
                response_time = f"{result.get('response_time', 0):.3f}s"
                client_ip = result.get('client_ip', '')
                
                print(f"{timestamp:<20} {method:<6} {url:<25} {status_code:<6} {response_time:<8} {client_ip:<15}")
            
            print("-" * 100)
            
            # 测试条件查询
            print("\n测试条件查询...")
            
            # 按方法查询
            get_results = client.query_access_logs(method="GET", limit=5)
            print(f"GET请求数量: {len(get_results)}")
            
            # 按状态码查询
            error_results = client.query_access_logs(status_code=500, limit=5)
            print(f"500错误数量: {len(error_results)}")
            
            # 按时间范围查询
            start_time = (datetime.now() - timedelta(hours=1)).strftime('%Y-%m-%d %H:%M:%S')
            recent_results = client.query_access_logs(start_time=start_time, limit=5)
            print(f"最近1小时请求数量: {len(recent_results)}")
            
            return True
        else:
            print("⚠️  查询成功但没有找到数据")
            print("可能原因:")
            print("1. 数据还在写入队列中，尚未刷新到数据库")
            print("2. 数据写入失败")
            print("3. 表结构问题")
            return False
            
    except Exception as e:
        print(f"❌ 数据查询失败: {e}")
        return False


def test_logging_integration():
    """
    测试日志集成功能
    
    Returns:
        bool: 日志集成是否成功
    """
    print("\n=== 测试日志集成功能 ===")
    
    try:
        # 设置日志
        setup_logging("DEBUG")
        
        # 测试log_api_access函数
        print("测试log_api_access函数...")
        
        log_api_access(
            method="GET",
            url="/api/v1/integration/test",
            status_code=200,
            response_time=0.789,
            client_ip="192.168.1.200",
            user_agent="Integration Test Agent",
            user_id="integration_user",
            request_size=512,
            response_size=1024,
            session_id="session_123",
            api_key="test_api_key"
        )
        
        print("✅ 日志集成测试完成")
        
        # 测试便捷函数
        print("测试便捷函数...")
        
        log_api_access_to_doris(
            method="POST",
            url="/api/v1/convenience/test",
            status_code=201,
            response_time=0.321,
            client_ip="192.168.1.201",
            user_agent="Convenience Test Agent",
            user_id="convenience_user"
        )
        
        print("✅ 便捷函数测试完成")
        return True
        
    except Exception as e:
        print(f"❌ 日志集成测试失败: {e}")
        return False


def test_performance():
    """
    测试性能
    
    Returns:
        bool: 性能测试是否成功
    """
    print("\n=== 测试性能 ===")
    
    try:
        client = get_doris_client()
        
        if not client.enabled:
            print("❌ Doris客户端未启用")
            return False
        
        # 性能测试参数
        test_count = 100
        batch_size = 10
        
        print(f"插入 {test_count} 条记录进行性能测试...")
        
        start_time = time.time()
        
        for i in range(test_count):
            client.log_access(
                method="GET" if i % 2 == 0 else "POST",
                url=f"/api/v1/performance/test/{i}",
                status_code=200 if i % 10 != 9 else 500,
                response_time=0.1 + (i % 10) * 0.01,
                client_ip=f"192.168.1.{100 + i % 50}",
                user_agent=f"Performance Test Agent {i}",
                user_id=f"perf_user_{i % 20}",
                request_size=1024 + i * 10,
                response_size=2048 + i * 20
            )
            
            # 每批次显示进度
            if (i + 1) % batch_size == 0:
                print(f"  已插入 {i + 1}/{test_count} 条记录")
        
        insert_time = time.time() - start_time
        
        print(f"插入完成，耗时: {insert_time:.2f}秒")
        print(f"平均插入速度: {test_count / insert_time:.1f} 条/秒")
        
        # 等待数据处理
        print("等待数据处理完成...")
        time.sleep(5)
        
        # 强制刷新
        if hasattr(client, '_flush_batch'):
            client._flush_batch()
            time.sleep(2)
        
        # 查询性能测试
        print("测试查询性能...")
        
        query_start = time.time()
        results = client.query_access_logs(limit=test_count)
        query_time = time.time() - query_start
        
        print(f"查询完成，耗时: {query_time:.2f}秒")
        print(f"查询到 {len(results)} 条记录")
        print(f"查询速度: {len(results) / query_time:.1f} 条/秒")
        
        print("✅ 性能测试完成")
        return True
        
    except Exception as e:
        print(f"❌ 性能测试失败: {e}")
        return False


def cleanup_test_data():
    """
    清理测试数据
    
    Returns:
        bool: 清理是否成功
    """
    print("\n=== 清理测试数据 ===")
    
    try:
        import pymysql
        
        connection = pymysql.connect(
            host=settings.DORIS_HOST,
            port=settings.DORIS_QUERY_PORT,
            user=settings.DORIS_USER,
            password=settings.DORIS_PASSWORD,
            database=settings.DORIS_DATABASE,
            charset='utf8mb4'
        )
        
        with connection.cursor() as cursor:
            # 删除测试数据
            cursor.execute(f"""
                DELETE FROM {settings.DORIS_ACCESS_LOG_TABLE} 
                WHERE url LIKE '/api/v1/test/%' 
                   OR url LIKE '/api/v1/integration/%'
                   OR url LIKE '/api/v1/convenience/%'
                   OR url LIKE '/api/v1/performance/%'
            """)
            
            deleted_rows = cursor.rowcount
            connection.commit()
            
            print(f"✅ 清理完成，删除了 {deleted_rows} 条测试数据")
        
        connection.close()
        return True
        
    except Exception as e:
        print(f"❌ 清理测试数据失败: {e}")
        return False


def main():
    """
    主测试函数
    
    Returns:
        bool: 所有测试是否通过
    """
    print("Doris集成功能测试")
    print("=" * 50)
    
    test_results = []
    
    # 执行所有测试
    tests = [
        ("配置测试", test_configuration),
        ("客户端创建测试", test_client_creation),
        ("数据库连接测试", test_database_connection),
        ("表操作测试", test_table_operations),
        ("数据插入测试", test_data_insertion),
        ("数据查询测试", test_data_query),
        ("日志集成测试", test_logging_integration),
        ("性能测试", test_performance)
    ]
    
    for test_name, test_func in tests:
        try:
            print(f"\n{'='*20} {test_name} {'='*20}")
            result = test_func()
            test_results.append((test_name, result))
            
            if result:
                print(f"✅ {test_name} 通过")
            else:
                print(f"❌ {test_name} 失败")
                
        except Exception as e:
            print(f"❌ {test_name} 异常: {e}")
            test_results.append((test_name, False))
    
    # 清理测试数据
    print(f"\n{'='*20} 清理测试数据 {'='*20}")
    cleanup_test_data()
    
    # 显示测试结果汇总
    print("\n" + "=" * 50)
    print("测试结果汇总")
    print("=" * 50)
    
    passed_count = 0
    total_count = len(test_results)
    
    for test_name, result in test_results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{test_name:<20} {status}")
        if result:
            passed_count += 1
    
    print("-" * 50)
    print(f"总计: {total_count} 个测试")
    print(f"通过: {passed_count} 个测试")
    print(f"失败: {total_count - passed_count} 个测试")
    print(f"成功率: {passed_count / total_count * 100:.1f}%")
    
    if passed_count == total_count:
        print("\n🎉 所有测试通过！Doris集成功能正常")
        return True
    else:
        print("\n⚠️  部分测试失败，请检查配置和环境")
        return False


if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n用户中断测试")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n测试过程中发生未预期的错误: {e}")
        sys.exit(1)