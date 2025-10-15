#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
日志修复测试脚本

测试修复后的日志配置是否能正常工作，特别是在Windows环境下的文件权限问题。

Author: System
Date: 2024
"""

import time
import threading
from app.core.logging import setup_logging
from loguru import logger


def test_concurrent_logging():
    """
    测试并发日志记录
    
    模拟多线程环境下的日志记录，验证文件锁定问题是否解决
    """
    def log_worker(worker_id: int, count: int):
        """日志工作线程"""
        for i in range(count):
            logger.info(f"Worker {worker_id} - Message {i+1}")
            logger.warning(f"Worker {worker_id} - Warning {i+1}")
            logger.error(f"Worker {worker_id} - Error {i+1}")
            time.sleep(0.01)  # 短暂延迟
    
    print("🧪 开始并发日志测试...")
    
    # 创建多个线程同时写入日志
    threads = []
    for i in range(5):  # 5个并发线程
        thread = threading.Thread(
            target=log_worker, 
            args=(i+1, 10),  # 每个线程写入10条日志
            name=f"LogWorker-{i+1}"
        )
        threads.append(thread)
    
    # 启动所有线程
    start_time = time.time()
    for thread in threads:
        thread.start()
    
    # 等待所有线程完成
    for thread in threads:
        thread.join()
    
    end_time = time.time()
    print(f"✅ 并发日志测试完成，耗时: {end_time - start_time:.2f}秒")


def test_log_rotation():
    """
    测试日志轮转功能
    
    生成大量日志来触发日志轮转
    """
    print("🔄 开始日志轮转测试...")
    
    # 生成大量日志数据来触发轮转
    for i in range(1000):
        logger.info(f"日志轮转测试消息 {i+1} - 这是一条用于测试日志轮转功能的长消息，包含足够的内容来快速达到文件大小限制")
        
        if i % 100 == 0:
            print(f"已生成 {i+1} 条日志...")
    
    print("✅ 日志轮转测试完成")


def test_error_handling():
    """
    测试错误处理
    
    验证日志系统的异常处理能力
    """
    print("⚠️ 开始错误处理测试...")
    
    try:
        # 模拟一些可能导致日志错误的情况
        logger.info("正常日志消息")
        
        # 测试包含特殊字符的日志
        logger.info("包含特殊字符的日志: 中文测试 🚀 \n\t\r")
        
        # 测试异常日志
        try:
            raise ValueError("这是一个测试异常")
        except Exception as e:
            logger.exception(f"捕获到异常: {e}")
        
        print("✅ 错误处理测试完成")
        
    except Exception as e:
        print(f"❌ 错误处理测试失败: {e}")


def main():
    """
    主测试函数
    
    执行所有日志相关的测试
    """
    print("🔧 开始日志修复验证测试")
    print("=" * 50)
    
    # 初始化日志系统
    try:
        setup_logging("DEBUG")
        print("✅ 日志系统初始化成功")
    except Exception as e:
        print(f"❌ 日志系统初始化失败: {e}")
        return
    
    # 基本日志测试
    print("\n📝 基本日志功能测试...")
    logger.debug("这是一条调试日志")
    logger.info("这是一条信息日志")
    logger.warning("这是一条警告日志")
    logger.error("这是一条错误日志")
    logger.critical("这是一条严重错误日志")
    print("✅ 基本日志功能正常")
    
    # 并发测试
    print("\n🔀 并发日志测试...")
    test_concurrent_logging()
    
    # 轮转测试
    print("\n🔄 日志轮转测试...")
    test_log_rotation()
    
    # 错误处理测试
    print("\n⚠️ 错误处理测试...")
    test_error_handling()
    
    print("\n" + "=" * 50)
    print("🎉 所有测试完成！")
    print("\n📁 请检查以下日志文件:")
    print("   - logs/app.log (主日志文件)")
    print("   - logs/app_error.log (错误日志文件)")
    print("   - logs/app_access.log (访问日志文件)")
    print("\n如果没有出现文件权限错误，说明修复成功！")


if __name__ == "__main__":
    main()