#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
运行Token接口并发测试的简单脚本

Author: System
Date: 2024
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from test_token_concurrent_simple import SimpleConcurrentTester, check_server_status

def main():
    """
    主函数 - 运行并发测试
    """
    print("Token接口并发测试")
    print("=" * 50)
    
    # 检查服务器状态
    print("检查服务器状态...")
    if not check_server_status():
        print("❌ 服务器不可用，请确保API服务正在运行")
        return
    
    # 创建测试实例
    tester = SimpleConcurrentTester()
    
    print("\n开始并发测试...")
    
    # 测试1: 基础并发测试
    print("\n1. 基础并发测试 (5线程 x 3请求)")
    try:
        metrics = tester.test_basic_concurrent(5, 3)
        tester.print_metrics(metrics, "基础并发测试")
    except Exception as e:
        print(f"❌ 基础并发测试失败: {e}")
    
    # 测试2: 线程池测试
    print("\n2. 线程池测试 (10工作线程 x 20请求)")
    try:
        metrics = tester.test_thread_pool_concurrent(10, 20)
        tester.print_metrics(metrics, "线程池测试")
    except Exception as e:
        print(f"❌ 线程池测试失败: {e}")
    
    # 测试3: 突发负载测试
    print("\n3. 突发负载测试 (10请求 x 2次突发)")
    try:
        metrics = tester.test_burst_load(10, 2, 1.0)
        tester.print_metrics(metrics, "突发负载测试")
    except Exception as e:
        print(f"❌ 突发负载测试失败: {e}")
    
    print("\n🎉 并发测试完成！")
    print("=" * 50)

if __name__ == "__main__":
    main()