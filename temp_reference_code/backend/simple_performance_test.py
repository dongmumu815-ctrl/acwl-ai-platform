#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简化版性能测试脚本 - 仅使用Python标准库

使用方法:
1. 确保API服务正在运行
2. 运行此脚本: python simple_performance_test.py
3. 查看响应时间统计

注意: 此版本使用urllib而非aiohttp，适合快速测试
"""

import urllib.request
import urllib.parse
import urllib.error
import json
import time
import statistics
import threading
from typing import List, Dict
from concurrent.futures import ThreadPoolExecutor, as_completed

# 测试配置
BASE_URL = "http://localhost:8000/api/v1"
API_CODE = "test22333"  # 替换为实际的API代码
TEST_COUNT = 20  # 测试次数（减少以适应同步测试）
CONCURRENT_REQUESTS = 5  # 并发请求数
TIMEOUT = 10  # 请求超时时间（秒）

# 测试数据
TEST_DATA = {
    "test": "test_value",
    "field2": 123,
    "batch_id": "test_batch"
}

# 认证头（如果需要）
HEADERS = {
    "Content-Type": "application/json",
    "User-Agent": "Performance-Test-Script/1.0",
    "Authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI2IiwidHlwZSI6ImN1c3RvbWVyIiwiZXhwIjoxNzUyODEwODE1LCJpYXQiOjE3NTI3MjQ0MTUsImp0aSI6ImpTWmJieVMwZjg5TmtlaGlfZTFqWEtGeE1YQ0trTFdLT2dTR2ZhOWk2bGsiLCJjdXN0b21lcl9pZCI6NiwiYXBwX2lkIjoidGVzdF9hcHBfMDAxIn0.WF9iyukM_hdBEdUPiEoTz5wlxLrrUZal3YXCDwhKzlo"  # 如果API需要认证，请取消注释并填入token
}

def make_request(url: str, data: dict = None, request_id: int = 0) -> Dict:
    """
    发送单个HTTP请求并测量响应时间
    
    Args:
        url: 请求URL
        data: 请求数据（POST请求时使用）
        request_id: 请求ID，用于标识
        
    Returns:
        包含响应时间和状态的字典
    """
    start_time = time.time()
    
    try:
        if data:
            # POST请求
            json_data = json.dumps(data).encode('utf-8')
            request = urllib.request.Request(
                url, 
                data=json_data, 
                headers=HEADERS,
                method='POST'
            )
        else:
            # GET请求
            request = urllib.request.Request(url, headers=HEADERS)
        
        with urllib.request.urlopen(request, timeout=TIMEOUT) as response:
            response_data = response.read().decode('utf-8')
            end_time = time.time()
            
            return {
                "request_id": request_id,
                "response_time": (end_time - start_time) * 1000,  # 转换为毫秒
                "status_code": response.getcode(),
                "success": True,
                "response_size": len(response_data),
                "error": None
            }
            
    except urllib.error.HTTPError as e:
        end_time = time.time()
        return {
            "request_id": request_id,
            "response_time": (end_time - start_time) * 1000,
            "status_code": e.code,
            "success": False,
            "response_size": 0,
            "error": f"HTTP {e.code}: {e.reason}"
        }
        
    except urllib.error.URLError as e:
        end_time = time.time()
        return {
            "request_id": request_id,
            "response_time": (end_time - start_time) * 1000,
            "status_code": 0,
            "success": False,
            "response_size": 0,
            "error": f"URL错误: {str(e.reason)}"
        }
        
    except Exception as e:
        end_time = time.time()
        return {
            "request_id": request_id,
            "response_time": (end_time - start_time) * 1000,
            "status_code": 0,
            "success": False,
            "response_size": 0,
            "error": f"请求异常: {str(e)}"
        }

def run_performance_test():
    """
    运行性能测试
    """
    print(f"🚀 开始API性能测试")
    print(f"📊 测试配置:")
    print(f"   - 基础URL: {BASE_URL}")
    print(f"   - API代码: {API_CODE}")
    print(f"   - 测试次数: {TEST_COUNT}")
    print(f"   - 并发数: {CONCURRENT_REQUESTS}")
    print(f"   - 超时时间: {TIMEOUT}秒")
    print("="*50)
    
    url = f"{BASE_URL}/{API_CODE}"
    results = []
    
    # 预热请求
    print("🔥 预热请求...")
    warmup_result = make_request(url, TEST_DATA, 0)
    if warmup_result["success"]:
        print(f"   预热成功，响应时间: {warmup_result['response_time']:.2f}ms")
    else:
        print(f"   预热失败: {warmup_result['error']}")
        print("   ⚠️  继续测试，但结果可能不准确")
    
    print(f"\n⚡ 开始 {TEST_COUNT} 次请求测试...")
    
    # 使用线程池进行并发测试
    with ThreadPoolExecutor(max_workers=CONCURRENT_REQUESTS) as executor:
        # 提交所有任务
        future_to_id = {
            executor.submit(make_request, url, TEST_DATA, i): i 
            for i in range(1, TEST_COUNT + 1)
        }
        
        # 收集结果
        completed_count = 0
        for future in as_completed(future_to_id):
            request_id = future_to_id[future]
            try:
                result = future.result()
                results.append(result)
                completed_count += 1
                
                # 显示进度
                if completed_count % 5 == 0 or completed_count == TEST_COUNT:
                    success_count = sum(1 for r in results if r["success"])
                    print(f"   进度: {completed_count}/{TEST_COUNT}, 成功: {success_count}")
                    
            except Exception as exc:
                print(f"   请求 {request_id} 生成异常: {exc}")
                results.append({
                    "request_id": request_id,
                    "response_time": 0,
                    "status_code": 0,
                    "success": False,
                    "response_size": 0,
                    "error": f"执行异常: {str(exc)}"
                })
    
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
    
    success_rate = len(successful_requests) / total_requests * 100 if total_requests > 0 else 0
    
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
        p95_index = int(len(response_times_sorted) * 0.95)
        p99_index = int(len(response_times_sorted) * 0.99)
        p95_time = response_times_sorted[min(p95_index, len(response_times_sorted) - 1)]
        p99_time = response_times_sorted[min(p99_index, len(response_times_sorted) - 1)]
        
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
        if response_sizes:
            avg_size = statistics.mean(response_sizes)
            print(f"   - 平均响应大小: {avg_size:.0f} bytes")
        
        # 性能分布
        print(f"\n📊 响应时间分布:")
        fast_requests = len([t for t in response_times if t < 100])
        medium_requests = len([t for t in response_times if 100 <= t < 300])
        slow_requests = len([t for t in response_times if t >= 300])
        
        print(f"   - 快速响应 (<100ms): {fast_requests} 次 ({fast_requests/len(response_times)*100:.1f}%)")
        print(f"   - 中等响应 (100-300ms): {medium_requests} 次 ({medium_requests/len(response_times)*100:.1f}%)")
        print(f"   - 慢速响应 (>=300ms): {slow_requests} 次 ({slow_requests/len(response_times)*100:.1f}%)")
    
    # 错误分析
    if failed_requests:
        print(f"\n❌ 错误分析:")
        error_counts = {}
        for req in failed_requests:
            status = req.get("status_code", "unknown")
            error_counts[status] = error_counts.get(status, 0) + 1
        
        for status, count in error_counts.items():
            print(f"   - HTTP {status}: {count} 次")
        
        # 显示前3个错误详情
        print(f"\n🔍 错误详情（前3个）:")
        for i, req in enumerate(failed_requests[:3]):
            print(f"   {i+1}. 请求ID {req['request_id']}: {req['error']}")
    
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
            print("   6. 查看 PERFORMANCE_OPTIMIZATION.md 获取详细优化指南")

def print_usage():
    """
    打印使用说明
    """
    print("🔧 简化版API性能测试工具")
    print("\n📝 使用前请确保:")
    print("   1. API服务正在运行 (默认: http://localhost:8000)")
    print("   2. 修改脚本中的API_CODE为实际的API代码")
    print("   3. 如果API需要认证，请在HEADERS中添加Authorization")
    print("\n🚀 运行测试:")
    print("   python simple_performance_test.py")
    print("\n📊 如需更高级的测试功能，请安装aiohttp:")
    print("   pip install -r test_requirements.txt")
    print("   python performance_test.py")
    print()

if __name__ == "__main__":
    print_usage()
    
    try:
        # 检查URL连通性
        print("🔗 检查API服务连通性...")
        test_url = f"{BASE_URL.replace('/v1', '')}/docs"  # 尝试访问文档页面
        try:
            with urllib.request.urlopen(test_url, timeout=5) as response:
                if response.getcode() == 200:
                    print("   ✅ API服务连通正常")
                else:
                    print(f"   ⚠️  API服务响应异常: {response.getcode()}")
        except:
            print("   ⚠️  无法连接到API服务，但继续测试...")
        
        print()
        run_performance_test()
        
    except KeyboardInterrupt:
        print("\n⏹️  测试被用户中断")
    except Exception as e:
        print(f"\n❌ 测试过程中发生错误: {e}")
        print("\n🔍 可能的解决方案:")
        print("   1. 检查API服务是否正在运行")
        print("   2. 确认API_CODE是否正确")
        print("   3. 检查网络连接")
        print("   4. 查看API服务日志")