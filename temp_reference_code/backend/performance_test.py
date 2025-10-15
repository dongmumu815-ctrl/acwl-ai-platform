#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
性能测试脚本 - 用于测试API响应时间优化效果

使用方法:
1. 确保API服务正在运行
2. 运行此脚本: python performance_test.py
3. 查看响应时间统计
"""

import asyncio
import aiohttp
import time
import statistics
from typing import List, Dict
import json

# 测试配置
BASE_URL = "http://localhost:8000/api/v1"
API_CODE = "test_api"  # 替换为实际的API代码
TEST_COUNT = 50  # 测试次数
CONCURRENT_REQUESTS = 10  # 并发请求数

# 测试数据
TEST_DATA = {
    "field1": "test_value",
    "field2": 123,
    "batch_id": "test_batch"
}

# 认证头（如果需要）
HEADERS = {
    "Content-Type": "application/json",
    # "Authorization": "Bearer your_token_here"  # 如果API需要认证，请取消注释并填入token
}

async def make_request(session: aiohttp.ClientSession, url: str, data: dict = None) -> Dict:
    """
    发送单个HTTP请求并测量响应时间
    
    Args:
        session: aiohttp会话
        url: 请求URL
        data: 请求数据
        
    Returns:
        包含响应时间和状态的字典
    """
    start_time = time.time()
    
    try:
        if data:
            async with session.post(url, json=data, headers=HEADERS) as response:
                response_data = await response.text()
                end_time = time.time()
                
                return {
                    "response_time": (end_time - start_time) * 1000,  # 转换为毫秒
                    "status_code": response.status,
                    "success": response.status < 400,
                    "response_size": len(response_data)
                }
        else:
            async with session.get(url, headers=HEADERS) as response:
                response_data = await response.text()
                end_time = time.time()
                
                return {
                    "response_time": (end_time - start_time) * 1000,
                    "status_code": response.status,
                    "success": response.status < 400,
                    "response_size": len(response_data)
                }
                
    except Exception as e:
        end_time = time.time()
        return {
            "response_time": (end_time - start_time) * 1000,
            "status_code": 0,
            "success": False,
            "error": str(e),
            "response_size": 0
        }

async def run_performance_test():
    """
    运行性能测试
    """
    print(f"🚀 开始API性能测试")
    print(f"📊 测试配置:")
    print(f"   - 基础URL: {BASE_URL}")
    print(f"   - API代码: {API_CODE}")
    print(f"   - 测试次数: {TEST_COUNT}")
    print(f"   - 并发数: {CONCURRENT_REQUESTS}")
    print("="*50)
    
    url = f"{BASE_URL}/{API_CODE}"
    results = []
    
    # 创建连接器，优化连接池
    connector = aiohttp.TCPConnector(
        limit=100,  # 总连接池大小
        limit_per_host=50,  # 每个主机的连接数
        ttl_dns_cache=300,  # DNS缓存时间
        use_dns_cache=True,
    )
    
    async with aiohttp.ClientSession(connector=connector) as session:
        # 预热请求
        print("🔥 预热请求...")
        await make_request(session, url, TEST_DATA)
        
        # 批量测试
        print(f"⚡ 开始 {TEST_COUNT} 次请求测试...")
        
        # 分批并发执行
        for batch_start in range(0, TEST_COUNT, CONCURRENT_REQUESTS):
            batch_end = min(batch_start + CONCURRENT_REQUESTS, TEST_COUNT)
            batch_size = batch_end - batch_start
            
            print(f"📈 执行第 {batch_start + 1}-{batch_end} 次请求...")
            
            # 创建并发任务
            tasks = [
                make_request(session, url, TEST_DATA)
                for _ in range(batch_size)
            ]
            
            # 执行并发请求
            batch_results = await asyncio.gather(*tasks)
            results.extend(batch_results)
            
            # 显示批次结果
            batch_times = [r["response_time"] for r in batch_results if r["success"]]
            if batch_times:
                avg_time = statistics.mean(batch_times)
                print(f"   批次平均响应时间: {avg_time:.2f}ms")
    
    # 分析结果
    analyze_results(results)

def analyze_results(results: List[Dict]):
    """
    分析测试结果
    
    Args:
        results: 测试结果列表
    """
    print("\n" + "="*50)
    print("📊 性能测试结果分析")
    print("="*50)
    
    # 基本统计
    total_requests = len(results)
    successful_requests = [r for r in results if r["success"]]
    failed_requests = [r for r in results if not r["success"]]
    
    success_rate = len(successful_requests) / total_requests * 100
    
    print(f"📈 请求统计:")
    print(f"   - 总请求数: {total_requests}")
    print(f"   - 成功请求: {len(successful_requests)}")
    print(f"   - 失败请求: {len(failed_requests)}")
    print(f"   - 成功率: {success_rate:.2f}%")
    
    if successful_requests:
        # 响应时间统计
        response_times = [r["response_time"] for r in successful_requests]
        
        avg_time = statistics.mean(response_times)
        median_time = statistics.median(response_times)
        min_time = min(response_times)
        max_time = max(response_times)
        
        # 计算百分位数
        response_times_sorted = sorted(response_times)
        p95_time = response_times_sorted[int(len(response_times_sorted) * 0.95)]
        p99_time = response_times_sorted[int(len(response_times_sorted) * 0.99)]
        
        print(f"\n⏱️  响应时间统计:")
        print(f"   - 平均响应时间: {avg_time:.2f}ms")
        print(f"   - 中位数响应时间: {median_time:.2f}ms")
        print(f"   - 最小响应时间: {min_time:.2f}ms")
        print(f"   - 最大响应时间: {max_time:.2f}ms")
        print(f"   - 95%百分位: {p95_time:.2f}ms")
        print(f"   - 99%百分位: {p99_time:.2f}ms")
        
        # 性能评估
        print(f"\n🎯 性能评估:")
        if avg_time < 100:
            print(f"   ✅ 优秀 - 平均响应时间 < 100ms")
        elif avg_time < 200:
            print(f"   ✅ 良好 - 平均响应时间 < 200ms")
        elif avg_time < 500:
            print(f"   ⚠️  一般 - 平均响应时间 < 500ms")
        else:
            print(f"   ❌ 需要优化 - 平均响应时间 >= 500ms")
        
        # 响应大小统计
        response_sizes = [r["response_size"] for r in successful_requests]
        avg_size = statistics.mean(response_sizes)
        print(f"   - 平均响应大小: {avg_size:.0f} bytes")
    
    # 错误分析
    if failed_requests:
        print(f"\n❌ 错误分析:")
        error_counts = {}
        for req in failed_requests:
            status = req.get("status_code", "unknown")
            error_counts[status] = error_counts.get(status, 0) + 1
        
        for status, count in error_counts.items():
            print(f"   - HTTP {status}: {count} 次")
    
    print("\n" + "="*50)
    print("🎉 测试完成!")
    
    # 优化建议
    if successful_requests:
        avg_time = statistics.mean([r["response_time"] for r in successful_requests])
        if avg_time > 200:
            print("\n💡 优化建议:")
            print("   1. 检查数据库查询是否有适当的索引")
            print("   2. 考虑添加Redis缓存")
            print("   3. 优化日志记录频率")
            print("   4. 检查是否有不必要的数据库事务")
            print("   5. 考虑使用连接池优化数据库连接")

if __name__ == "__main__":
    print("🔧 API性能测试工具")
    print("请确保API服务正在运行，并根据需要修改测试配置")
    print()
    
    try:
        asyncio.run(run_performance_test())
    except KeyboardInterrupt:
        print("\n⏹️  测试被用户中断")
    except Exception as e:
        print(f"\n❌ 测试过程中发生错误: {e}")