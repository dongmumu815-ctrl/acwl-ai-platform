#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Token接口并发测试脚本

测试场景包括：
1. 不同并发级别的性能测试
2. 长时间压力测试
3. 突发流量测试
4. 响应时间统计分析
5. 错误率统计
6. 资源使用监控

Author: System
Date: 2024
"""

import asyncio
import aiohttp
import time
import threading
import queue
import statistics
import json
import hmac
import hashlib
import random
import string
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Any
from concurrent.futures import ThreadPoolExecutor, as_completed
import psutil
import os

# 测试配置
BASE_URL = "http://localhost:8000"
TOKEN_ENDPOINT = f"{BASE_URL}/api/v1/auth/token"

# 测试用客户数据
TEST_CUSTOMER = {
    "app_id": "test_app_001",
    "app_secret": "test_secret_123456789"
}

class ConcurrentTokenTester:
    """
    Token接口并发测试类
    
    提供全面的并发性能测试功能
    """
    
    def __init__(self):
        self.base_url = BASE_URL
        self.token_endpoint = TOKEN_ENDPOINT
        self.test_customer = TEST_CUSTOMER
        self.used_nonces = set()
        self.nonce_lock = threading.Lock()
        
        # 统计数据
        self.stats = {
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'response_times': [],
            'error_codes': {},
            'start_time': None,
            'end_time': None
        }
    
    def generate_nonce(self, length: int = 12) -> str:
        """
        生成线程安全的随机nonce字符串
        
        Args:
            length: nonce长度
            
        Returns:
            str: 随机nonce字符串
        """
        chars = string.ascii_letters + string.digits
        
        with self.nonce_lock:
            while True:
                nonce = ''.join(random.choice(chars) for _ in range(length))
                if nonce not in self.used_nonces:
                    self.used_nonces.add(nonce)
                    return nonce
    
    def generate_signature(self, appid: str, timestamp: int, nonce: str, secret: str) -> str:
        """
        生成HMAC-SHA256签名
        
        Args:
            appid: 应用ID
            timestamp: 时间戳
            nonce: 随机字符串
            secret: 预共享密钥
            
        Returns:
            str: 签名值（大写十六进制）
        """
        signature_data = f"{appid}{timestamp}{nonce}"
        signature = hmac.new(
            secret.encode('utf-8'),
            signature_data.encode('utf-8'),
            hashlib.sha256
        ).hexdigest().upper()
        return signature
    
    def create_auth_request(self) -> Dict[str, Any]:
        """
        创建认证请求数据
        
        Returns:
            Dict[str, Any]: 认证请求数据
        """
        appid = self.test_customer["app_id"]
        timestamp = int(time.time())
        nonce = self.generate_nonce()
        secret = self.test_customer["app_secret"]
        
        signature = self.generate_signature(appid, timestamp, nonce, secret)
        
        return {
            "appid": appid,
            "timestamp": timestamp,
            "nonce": nonce,
            "signature": signature
        }


    
    
    def send_single_request(self, session=None) -> Tuple[int, float, str]:
        """
        发送单个token请求
        
        Args:
            session: requests会话对象（可选）
            
        Returns:
            Tuple[int, float, str]: (状态码, 响应时间, 错误信息)
        """
        import requests
        
        auth_data = self.create_auth_request()
        headers = {"Content-Type": "application/json"}
        
        start_time = time.time()
        try:
            if session:
                response = session.post(
                    self.token_endpoint,
                    json=auth_data,
                    headers=headers,
                    timeout=10
                )
            else:
                response = requests.post(
                    self.token_endpoint,
                    json=auth_data,
                    headers=headers,
                    timeout=10
                )
            
            response_time = time.time() - start_time
            return response.status_code, response_time, ""
            
        except Exception as e:
            response_time = time.time() - start_time
            return 0, response_time, str(e)
    
    async def send_async_request(self, session: aiohttp.ClientSession) -> Tuple[int, float, str]:
        """
        发送异步token请求
        
        Args:
            session: aiohttp会话对象
            
        Returns:
            Tuple[int, float, str]: (状态码, 响应时间, 错误信息)
        """
        auth_data = self.create_auth_request()
        
        start_time = time.time()
        try:
            async with session.post(
                self.token_endpoint,
                json=auth_data,
                headers={"Content-Type": "application/json"},
                timeout=aiohttp.ClientTimeout(total=10)
            ) as response:
                response_time = time.time() - start_time
                return response.status, response_time, ""
                
        except Exception as e:
            response_time = time.time() - start_time
            return 0, response_time, str(e)
    
    def update_stats(self, status_code: int, response_time: float, error_msg: str):
        """
        更新统计数据
        
        Args:
            status_code: HTTP状态码
            response_time: 响应时间
            error_msg: 错误信息
        """
        self.stats['total_requests'] += 1
        self.stats['response_times'].append(response_time)
        
        if status_code == 200:
            self.stats['successful_requests'] += 1
        else:
            self.stats['failed_requests'] += 1
            
            # 记录错误码
            error_key = f"{status_code}_{error_msg[:50]}" if error_msg else str(status_code)
            self.stats['error_codes'][error_key] = self.stats['error_codes'].get(error_key, 0) + 1
    
    def test_thread_based_concurrent(self, num_threads: int, requests_per_thread: int) -> Dict[str, Any]:
        """
        基于线程的并发测试
        
        Args:
            num_threads: 线程数量
            requests_per_thread: 每个线程的请求数量
            
        Returns:
            Dict[str, Any]: 测试结果
        """
        print(f"\n=== 线程并发测试: {num_threads}线程 x {requests_per_thread}请求 ===")
        
        # 重置统计
        self.stats = {
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'response_times': [],
            'error_codes': {},
            'start_time': time.time(),
            'end_time': None
        }
        
        results_queue = queue.Queue()
        
        def worker():
            """工作线程函数"""
            import requests
            session = requests.Session()
            
            for _ in range(requests_per_thread):
                status_code, response_time, error_msg = self.send_single_request(session)
                results_queue.put((status_code, response_time, error_msg))
            
            session.close()
        
        # 启动线程
        threads = []
        start_time = time.time()
        
        for _ in range(num_threads):
            thread = threading.Thread(target=worker)
            thread.start()
            threads.append(thread)
        
        # 等待所有线程完成
        for thread in threads:
            thread.join()
        
        end_time = time.time()
        self.stats['end_time'] = end_time
        
        # 收集结果
        while not results_queue.empty():
            status_code, response_time, error_msg = results_queue.get()
            self.update_stats(status_code, response_time, error_msg)
        
        return self.calculate_metrics()
    
    async def test_async_concurrent(self, concurrent_requests: int, total_requests: int) -> Dict[str, Any]:
        """
        基于异步的并发测试
        
        Args:
            concurrent_requests: 并发请求数
            total_requests: 总请求数
            
        Returns:
            Dict[str, Any]: 测试结果
        """
        print(f"\n=== 异步并发测试: {concurrent_requests}并发 x {total_requests}总请求 ===")
        
        # 重置统计
        self.stats = {
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'response_times': [],
            'error_codes': {},
            'start_time': time.time(),
            'end_time': None
        }
        
        connector = aiohttp.TCPConnector(limit=concurrent_requests)
        timeout = aiohttp.ClientTimeout(total=30)
        
        async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
            # 创建信号量控制并发数
            semaphore = asyncio.Semaphore(concurrent_requests)
            
            async def bounded_request():
                """受限制的请求函数"""
                async with semaphore:
                    return await self.send_async_request(session)
            
            # 创建任务
            tasks = [bounded_request() for _ in range(total_requests)]
            
            # 执行所有任务
            start_time = time.time()
            results = await asyncio.gather(*tasks, return_exceptions=True)
            end_time = time.time()
            
            self.stats['end_time'] = end_time
            
            # 处理结果
            for result in results:
                if isinstance(result, Exception):
                    self.update_stats(0, 0, str(result))
                else:
                    status_code, response_time, error_msg = result
                    self.update_stats(status_code, response_time, error_msg)
        
        return self.calculate_metrics()
    
    def test_burst_traffic(self, burst_size: int, burst_interval: float, num_bursts: int) -> Dict[str, Any]:
        """
        突发流量测试
        
        Args:
            burst_size: 每次突发的请求数量
            burst_interval: 突发间隔（秒）
            num_bursts: 突发次数
            
        Returns:
            Dict[str, Any]: 测试结果
        """
        print(f"\n=== 突发流量测试: {burst_size}请求/突发 x {num_bursts}次突发 ===")
        
        # 重置统计
        self.stats = {
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'response_times': [],
            'error_codes': {},
            'start_time': time.time(),
            'end_time': None
        }
        
        with ThreadPoolExecutor(max_workers=burst_size) as executor:
            for burst_num in range(num_bursts):
                print(f"执行第 {burst_num + 1} 次突发...")
                
                # 提交突发请求
                futures = [executor.submit(self.send_single_request) for _ in range(burst_size)]
                
                # 收集结果
                for future in as_completed(futures):
                    try:
                        status_code, response_time, error_msg = future.result()
                        self.update_stats(status_code, response_time, error_msg)
                    except Exception as e:
                        self.update_stats(0, 0, str(e))
                
                # 等待下一次突发
                if burst_num < num_bursts - 1:
                    time.sleep(burst_interval)
        
        self.stats['end_time'] = time.time()
        return self.calculate_metrics()
    
    def test_sustained_load(self, rps: float, duration_seconds: int) -> Dict[str, Any]:
        """
        持续负载测试
        
        Args:
            rps: 每秒请求数
            duration_seconds: 持续时间（秒）
            
        Returns:
            Dict[str, Any]: 测试结果
        """
        print(f"\n=== 持续负载测试: {rps}RPS x {duration_seconds}秒 ===")
        
        # 重置统计
        self.stats = {
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'response_times': [],
            'error_codes': {},
            'start_time': time.time(),
            'end_time': None
        }
        
        interval = 1.0 / rps  # 请求间隔
        end_time = time.time() + duration_seconds
        
        with ThreadPoolExecutor(max_workers=min(int(rps * 2), 100)) as executor:
            futures = []
            
            while time.time() < end_time:
                # 提交请求
                future = executor.submit(self.send_single_request)
                futures.append(future)
                
                # 控制请求速率
                time.sleep(interval)
                
                # 定期收集已完成的结果
                if len(futures) >= 50:
                    completed_futures = [f for f in futures if f.done()]
                    for future in completed_futures:
                        try:
                            status_code, response_time, error_msg = future.result()
                            self.update_stats(status_code, response_time, error_msg)
                        except Exception as e:
                            self.update_stats(0, 0, str(e))
                        futures.remove(future)
            
            # 收集剩余结果
            for future in as_completed(futures):
                try:
                    status_code, response_time, error_msg = future.result()
                    self.update_stats(status_code, response_time, error_msg)
                except Exception as e:
                    self.update_stats(0, 0, str(e))
        
        self.stats['end_time'] = time.time()
        return self.calculate_metrics()
    
    def calculate_metrics(self) -> Dict[str, Any]:
        """
        计算性能指标
        
        Returns:
            Dict[str, Any]: 性能指标
        """
        if not self.stats['response_times']:
            return {"error": "没有有效的响应时间数据"}
        
        response_times = self.stats['response_times']
        total_time = self.stats['end_time'] - self.stats['start_time']
        
        metrics = {
            'total_requests': self.stats['total_requests'],
            'successful_requests': self.stats['successful_requests'],
            'failed_requests': self.stats['failed_requests'],
            'success_rate': (self.stats['successful_requests'] / self.stats['total_requests']) * 100 if self.stats['total_requests'] > 0 else 0,
            'total_time': total_time,
            'requests_per_second': self.stats['total_requests'] / total_time if total_time > 0 else 0,
            'response_time_stats': {
                'min': min(response_times),
                'max': max(response_times),
                'mean': statistics.mean(response_times),
                'median': statistics.median(response_times),
                'p95': self.percentile(response_times, 95),
                'p99': self.percentile(response_times, 99)
            },
            'error_codes': self.stats['error_codes']
        }
        
        return metrics
    
    def percentile(self, data: List[float], percentile: float) -> float:
        """
        计算百分位数
        
        Args:
            data: 数据列表
            percentile: 百分位数（0-100）
            
        Returns:
            float: 百分位数值
        """
        if not data:
            return 0
        
        sorted_data = sorted(data)
        index = (percentile / 100) * (len(sorted_data) - 1)
        
        if index.is_integer():
            return sorted_data[int(index)]
        else:
            lower = sorted_data[int(index)]
            upper = sorted_data[int(index) + 1]
            return lower + (upper - lower) * (index - int(index))
    
    def print_metrics(self, metrics: Dict[str, Any], test_name: str):
        """
        打印性能指标
        
        Args:
            metrics: 性能指标字典
            test_name: 测试名称
        """
        print(f"\n{'='*60}")
        print(f"{test_name} - 测试结果")
        print(f"{'='*60}")
        
        if 'error' in metrics:
            print(f"❌ 测试失败: {metrics['error']}")
            return
        
        print(f"总请求数: {metrics['total_requests']}")
        print(f"成功请求: {metrics['successful_requests']}")
        print(f"失败请求: {metrics['failed_requests']}")
        print(f"成功率: {metrics['success_rate']:.2f}%")
        print(f"总耗时: {metrics['total_time']:.2f}秒")
        print(f"QPS: {metrics['requests_per_second']:.2f}")
        
        print(f"\n响应时间统计 (秒):")
        rt_stats = metrics['response_time_stats']
        print(f"  最小值: {rt_stats['min']:.4f}")
        print(f"  最大值: {rt_stats['max']:.4f}")
        print(f"  平均值: {rt_stats['mean']:.4f}")
        print(f"  中位数: {rt_stats['median']:.4f}")
        print(f"  P95: {rt_stats['p95']:.4f}")
        print(f"  P99: {rt_stats['p99']:.4f}")
        
        if metrics['error_codes']:
            print(f"\n错误统计:")
            for error_code, count in metrics['error_codes'].items():
                print(f"  {error_code}: {count}次")
    
    def monitor_system_resources(self, duration: int = 60):
        """
        监控系统资源使用情况
        
        Args:
            duration: 监控持续时间（秒）
        """
        print(f"\n=== 系统资源监控 ({duration}秒) ===")
        
        cpu_usage = []
        memory_usage = []
        
        start_time = time.time()
        while time.time() - start_time < duration:
            cpu_usage.append(psutil.cpu_percent(interval=1))
            memory_usage.append(psutil.virtual_memory().percent)
        
        print(f"CPU使用率 - 平均: {statistics.mean(cpu_usage):.1f}%, 最大: {max(cpu_usage):.1f}%")
        print(f"内存使用率 - 平均: {statistics.mean(memory_usage):.1f}%, 最大: {max(memory_usage):.1f}%")
    
    def run_comprehensive_test(self):
        """
        运行综合并发测试
        """
        print(f"\n{'='*80}")
        print(f"Token接口并发性能测试")
        print(f"测试时间: {datetime.now()}")
        print(f"目标接口: {self.token_endpoint}")
        print(f"测试客户: {self.test_customer['app_id']}")
        print(f"{'='*80}")
        
        # 1. 基础并发测试
        test_configs = [
            (10, 10),   # 10线程 x 10请求
            (20, 5),    # 20线程 x 5请求
            (50, 2),    # 50线程 x 2请求
            (100, 1),   # 100线程 x 1请求
        ]
        
        for num_threads, requests_per_thread in test_configs:
            metrics = self.test_thread_based_concurrent(num_threads, requests_per_thread)
            self.print_metrics(metrics, f"线程并发测试 ({num_threads}x{requests_per_thread})")
            time.sleep(2)  # 间隔2秒
        
        # 2. 异步并发测试
        async_configs = [
            (50, 100),   # 50并发 x 100请求
            (100, 200),  # 100并发 x 200请求
        ]
        
        for concurrent, total in async_configs:
            metrics = asyncio.run(self.test_async_concurrent(concurrent, total))
            self.print_metrics(metrics, f"异步并发测试 ({concurrent}并发x{total}请求)")
            time.sleep(2)
        
        # 3. 突发流量测试
        metrics = self.test_burst_traffic(burst_size=30, burst_interval=5.0, num_bursts=3)
        self.print_metrics(metrics, "突发流量测试")
        time.sleep(2)
        
        # 4. 持续负载测试
        metrics = self.test_sustained_load(rps=10.0, duration_seconds=30)
        self.print_metrics(metrics, "持续负载测试")
        
        print(f"\n{'='*80}")
        print("🎉 并发测试完成！")
        print(f"{'='*80}")

def main():
    """
    主函数
    """
    print("请确保以下条件满足:")
    print(f"1. API服务正在运行: {BASE_URL}")
    print(f"2. 测试客户存在: {TEST_CUSTOMER['app_id']}")
    print("3. 数据库连接正常")
    
    input("\n按回车键开始测试...")
    
    # 创建测试实例
    tester = ConcurrentTokenTester()
    
    # 运行综合测试
    tester.run_comprehensive_test()

if __name__ == "__main__":
    main()