#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Doris数据库初始化脚本

用于初始化Doris数据库和创建访问日志表结构。
提供数据库连接测试和表结构验证功能。

Author: System
Date: 2024
"""

import sys
import os
import asyncio
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.append(str(Path(__file__).parent))

from app.core.config import settings
from app.core.doris_client import DorisClient, get_doris_client
from loguru import logger


def test_doris_connection():
    """
    测试Doris数据库连接
    
    Returns:
        bool: 连接是否成功
    """
    print("\n=== 测试Doris数据库连接 ===")
    
    if not settings.DORIS_ENABLED:
        print("❌ Doris未启用，请在配置中启用DORIS_ENABLED")
        return False
    
    print(f"Doris主机: {settings.DORIS_HOST}")
    print(f"HTTP端口: {settings.DORIS_HTTP_PORT}")
    print(f"查询端口: {settings.DORIS_QUERY_PORT}")
    print(f"用户名: {settings.DORIS_USER}")
    print(f"数据库: {settings.DORIS_DATABASE}")
    print(f"表名: {settings.DORIS_ACCESS_LOG_TABLE}")
    
    try:
        # 创建客户端实例
        client = DorisClient()
        
        if not client.enabled:
            print("❌ Doris客户端未启用")
            return False
        
        # 测试连接
        import pymysql
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
            print(f"✅ 连接成功！Doris版本: {version[0]}")
        
        connection.close()
        return True
        
    except Exception as e:
        print(f"❌ 连接失败: {e}")
        return False


def create_database_and_table():
    """
    创建数据库和表结构
    
    Returns:
        bool: 创建是否成功
    """
    print("\n=== 创建数据库和表结构 ===")
    
    try:
        client = get_doris_client()
        
        if not client.enabled:
            print("❌ Doris客户端未启用")
            return False
        
        # 创建数据库和表
        client.create_table_if_not_exists()
        print("✅ 数据库和表创建成功")
        
        return True
        
    except Exception as e:
        print(f"❌ 创建失败: {e}")
        return False


def verify_table_structure():
    """
    验证表结构
    
    Returns:
        bool: 验证是否成功
    """
    print("\n=== 验证表结构 ===")
    
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
        
        with connection.cursor(pymysql.cursors.DictCursor) as cursor:
            # 检查表是否存在
            cursor.execute(f"SHOW TABLES LIKE '{settings.DORIS_ACCESS_LOG_TABLE}'")
            table_exists = cursor.fetchone()
            
            if not table_exists:
                print(f"❌ 表 {settings.DORIS_ACCESS_LOG_TABLE} 不存在")
                return False
            
            print(f"✅ 表 {settings.DORIS_ACCESS_LOG_TABLE} 存在")
            
            # 获取表结构
            cursor.execute(f"DESCRIBE {settings.DORIS_ACCESS_LOG_TABLE}")
            columns = cursor.fetchall()
            
            print("\n表结构:")
            print("-" * 80)
            print(f"{'字段名':<20} {'类型':<20} {'是否为空':<10} {'键':<10} {'默认值':<15} {'备注':<20}")
            print("-" * 80)
            
            for column in columns:
                field = column.get('Field', '')
                type_info = column.get('Type', '')
                null_info = column.get('Null', '')
                key_info = column.get('Key', '')
                default_info = str(column.get('Default', '')) if column.get('Default') is not None else ''
                extra_info = column.get('Extra', '')
                
                print(f"{field:<20} {type_info:<20} {null_info:<10} {key_info:<10} {default_info:<15} {extra_info:<20}")
            
            print("-" * 80)
            print(f"总共 {len(columns)} 个字段")
        
        connection.close()
        return True
        
    except Exception as e:
        print(f"❌ 验证失败: {e}")
        return False


def test_insert_and_query():
    """
    测试插入和查询数据
    
    Returns:
        bool: 测试是否成功
    """
    print("\n=== 测试数据插入和查询 ===")
    
    try:
        client = get_doris_client()
        
        if not client.enabled:
            print("❌ Doris客户端未启用")
            return False
        
        # 插入测试数据
        print("插入测试数据...")
        for i in range(5):
            client.log_access(
                method="GET",
                url=f"/api/test/init/{i}",
                status_code=200,
                response_time=0.1 + i * 0.01,
                client_ip="192.168.1.100",
                user_agent="Doris Init Test Agent",
                user_id=f"test_user_{i}",
                request_size=1024,
                response_size=2048,
                session_id=f"session_{i}"
            )
        
        print("等待数据写入...")
        import time
        time.sleep(3)  # 等待批量写入
        
        # 强制刷新缓冲区
        if hasattr(client, '_flush_batch'):
            client._flush_batch()
            time.sleep(2)
        
        # 查询数据
        print("查询测试数据...")
        results = client.query_access_logs(limit=10)
        
        if results:
            print(f"✅ 查询成功，找到 {len(results)} 条记录")
            print("\n最近的访问记录:")
            print("-" * 120)
            print(f"{'时间':<20} {'方法':<8} {'URL':<30} {'状态码':<8} {'响应时间':<10} {'客户端IP':<15} {'用户ID':<15}")
            print("-" * 120)
            
            for result in results[:5]:  # 只显示前5条
                timestamp = str(result.get('timestamp', ''))[:19]
                method = result.get('method', '')
                url = result.get('url', '')[:28] + '...' if len(result.get('url', '')) > 30 else result.get('url', '')
                status_code = result.get('status_code', '')
                response_time = f"{result.get('response_time', 0):.3f}s"
                client_ip = result.get('client_ip', '')
                user_id = result.get('user_id', '')
                
                print(f"{timestamp:<20} {method:<8} {url:<30} {status_code:<8} {response_time:<10} {client_ip:<15} {user_id:<15}")
            
            print("-" * 120)
            return True
        else:
            print("⚠️  查询成功但没有找到数据，可能数据还在写入中")
            return True
            
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False


def show_configuration():
    """
    显示当前配置信息
    """
    print("\n=== 当前Doris配置 ===")
    print(f"启用状态: {settings.DORIS_ENABLED}")
    print(f"主机地址: {settings.DORIS_HOST}")
    print(f"HTTP端口: {settings.DORIS_HTTP_PORT}")
    print(f"查询端口: {settings.DORIS_QUERY_PORT}")
    print(f"用户名: {settings.DORIS_USER}")
    print(f"密码: {'*' * len(settings.DORIS_PASSWORD) if settings.DORIS_PASSWORD else '(空)'}")
    print(f"数据库: {settings.DORIS_DATABASE}")
    print(f"表名: {settings.DORIS_ACCESS_LOG_TABLE}")
    print(f"批量大小: {settings.DORIS_BATCH_SIZE}")
    print(f"刷新间隔: {settings.DORIS_FLUSH_INTERVAL}秒")
    print(f"HTTP URL: {settings.DORIS_HTTP_URL}")
    print(f"JDBC URL: {settings.DORIS_JDBC_URL}")


def main():
    """
    主函数
    """
    print("Doris数据库初始化工具")
    print("=" * 50)
    
    # 显示配置
    show_configuration()
    
    # 测试连接
    if not test_doris_connection():
        print("\n❌ 初始化失败：无法连接到Doris数据库")
        return False
    
    # 创建数据库和表
    if not create_database_and_table():
        print("\n❌ 初始化失败：无法创建数据库和表")
        return False
    
    # 验证表结构
    if not verify_table_structure():
        print("\n❌ 初始化失败：表结构验证失败")
        return False
    
    # 测试插入和查询
    if not test_insert_and_query():
        print("\n⚠️  初始化完成，但数据测试失败")
        return True
    
    print("\n✅ Doris数据库初始化完成！")
    print("\n接下来的步骤:")
    print("1. 在配置文件中设置 DORIS_ENABLED=True")
    print("2. 重启应用以启用Doris日志记录")
    print("3. 访问API接口测试日志记录功能")
    
    return True


if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n用户中断操作")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n未预期的错误: {e}")
        sys.exit(1)