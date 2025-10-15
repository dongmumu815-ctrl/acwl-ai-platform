#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Token接口简化并发测试脚本

使用标准库实现的并发测试，包括：
1. 多线程并发测试
2. 性能指标统计
3. 错误率分析
4. 响应时间分析

Author: System
Date: 2024
"""

import requests
import time
import threading
import queue
import statistics
import json
import hmac
import hashlib
import random
import string
from datetime import datetime
from typing import Dict, List, Tuple, Any
from concurrent.futures import ThreadPoolExecutor, as_completed

# 测试配置
BASE_URL = "http://localhost:8000"
TOKEN_ENDPOINT = f"{BASE_URL}/api/v1/auth/token"

# 测试用客户数据
TEST_CUSTOMER = {
    "app_id": "test_app_001",
    "app_secret": "test_secret_123456789"
}

class SimpleConcurrentTester:
    """
    简化版Token接口并发测试类
    
    使用标准库实现并发测试功能
    """
    
    def __init__(self):
        self.base_url = BASE_URL
        self.token_endpoint = TOKEN_ENDPOINT
        self.test_customer = TEST_CUSTOMER
        self.used_nonces = set()
        self.nonce_lock = threading.Lock()
        
        # 统计数据
        self.reset_stats()
    
    def reset_stats(self):
        """
        重置统计数据
        """
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
    
    def update_stats(self, status_code: int, response_time: float, error_msg: str):
        """
        更新统计数据（线程安全）
        
        Args:
            status_code: HTTP状态码
            response_time: 响应时间
            error_msg: 错误信息
        """
        with self.nonce_lock:  # 复用锁来保护统计数据
            self.stats['total_requests'] += 1
            self.stats['response_times'].append(response_time)
            
            if status_code == 200:
                self.stats['successful_requests'] += 1
            else:
                self.stats['failed_requests'] += 1
                
                # 记录错误码
                error_key = f"{status_code}_{error_msg[:30]}" if error_msg else str(status_code)
                self.stats['error_codes'][error_key] = self.stats['error_codes'].get(error_key, 0) + 1
    
    def test_basic_concurrent(self, num_threads: int, requests_per_thread: int) -> Dict[str, Any]:
        """
        基础并发测试
        
        Args:
            num_threads: 线程数量
            requests_per_thread: 每个线程的请求数量
            
        Returns:
            Dict[str, Any]: 测试结果
        """
        print(f"\n=== 基础并发测试: {num_threads}线程 x {requests_per_thread}请求 ===")
        
        self.reset_stats()
        self.stats['start_time'] = time.time()
        
        def worker():
            """工作线程函数"""
            session = requests.Session()
            
            for _ in range(requests_per_thread):
                status_code, response_time, error_msg = self.send_single_request(session)
                self.update_stats(status_code, response_time, error_msg)
            
            session.close()
        
        # 启动线程
        threads = []
        
        for _ in range(num_threads):
            thread = threading.Thread(target=worker)
            thread.start()
            threads.append(thread)
        
        # 等待所有线程完成
        for thread in threads:
            thread.join()
        
        self.stats['end_time'] = time.time()
        return self.calculate_metrics()
    
    def test_thread_pool_concurrent(self, max_workers: int, total_requests: int) -> Dict[str, Any]:
        """
        线程池并发测试
        
        Args:
            max_workers: 最大工作线程数
            total_requests: 总请求数
            
        Returns:
            Dict[str, Any]: 测试结果
        """
        print(f"\n=== 线程池并发测试: {max_workers}工作线程 x {total_requests}总请求 ===")
        
        self.reset_stats()
        self.stats['start_time'] = time.time()
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # 提交所有任务
            futures = [executor.submit(self.send_single_request) for _ in range(total_requests)]
            
            # 收集结果
            for future in as_completed(futures):
                try:
                    status_code, response_time, error_msg = future.result()
                    self.update_stats(status_code, response_time, error_msg)
                except Exception as e:
                    self.update_stats(0, 0, str(e))
        
        self.stats['end_time'] = time.time()
        return self.calculate_metrics()
    
    def test_burst_load(self, burst_size: int, burst_count: int, interval: float) -> Dict[str, Any]:
        """
        突发负载测试
        
        Args:
            burst_size: 每次突发的请求数
            burst_count: 突发次数
            interval: 突发间隔（秒）
            
        Returns:
            Dict[str, Any]: 测试结果
        """
        print(f"\n=== 突发负载测试: {burst_size}请求/次 x {burst_count}次突发 ===")
        
        self.reset_stats()
        self.stats['start_time'] = time.time()
        
        for burst_num in range(burst_count):
            print(f"执行第 {burst_num + 1}/{burst_count} 次突发...")
            
            with ThreadPoolExecutor(max_workers=burst_size) as executor:
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
            if burst_num < burst_count - 1:
                time.sleep(interval)
        
        self.stats['end_time'] = time.time()
        return self.calculate_metrics()
    
    def test_sustained_load(self, target_rps: float, duration: int) -> Dict[str, Any]:
        """
        持续负载测试
        
        Args:
            target_rps: 目标每秒请求数
            duration: 持续时间（秒）
            
        Returns:
            Dict[str, Any]: 测试结果
        """
        print(f"\n=== 持续负载测试: {target_rps}RPS x {duration}秒 ===")
        
        self.reset_stats()
        self.stats['start_time'] = time.time()
        
        request_interval = 1.0 / target_rps
        end_time = time.time() + duration
        request_count = 0
        
        with ThreadPoolExecutor(max_workers=min(int(target_rps * 2), 50)) as executor:
            futures = []
            
            while time.time() < end_time:
                # 提交请求
                future = executor.submit(self.send_single_request)
                futures.append((future, time.time()))
                request_count += 1
                
                # 控制请求速率
                time.sleep(request_interval)
                
                # 定期收集完成的结果
                if len(futures) >= 20:
                    completed_futures = [(f, t) for f, t in futures if f.done()]
                    for future, submit_time in completed_futures:
                        try:
                            status_code, response_time, error_msg = future.result()
                            self.update_stats(status_code, response_time, error_msg)
                        except Exception as e:
                            self.update_stats(0, 0, str(e))
                        futures.remove((future, submit_time))
            
            # 收集剩余结果
            for future, submit_time in futures:
                try:
                    status_code, response_time, error_msg = future.result()
                    self.update_stats(status_code, response_time, error_msg)
                except Exception as e:
                    self.update_stats(0, 0, str(e))
        
        self.stats['end_time'] = time.time()
        print(f"实际发送请求数: {request_count}")
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
        
        # 计算百分位数
        sorted_times = sorted(response_times)
        count = len(sorted_times)
        
        def percentile(p):
            index = int((p / 100.0) * (count - 1))
            return sorted_times[min(index, count - 1)]
        
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
                'p90': percentile(90),
                'p95': percentile(95),
                'p99': percentile(99)
            },
            'error_codes': self.stats['error_codes']
        }
        
        return metrics
    
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
        print(f"实际QPS: {metrics['requests_per_second']:.2f}")
        
        print(f"\n响应时间统计 (秒):")
        rt_stats = metrics['response_time_stats']
        print(f"  最小值: {rt_stats['min']:.4f}")
        print(f"  最大值: {rt_stats['max']:.4f}")
        print(f"  平均值: {rt_stats['mean']:.4f}")
        print(f"  中位数: {rt_stats['median']:.4f}")
        print(f"  P90: {rt_stats['p90']:.4f}")
        print(f"  P95: {rt_stats['p95']:.4f}")
        print(f"  P99: {rt_stats['p99']:.4f}")
        
        if metrics['error_codes']:
            print(f"\n错误统计:")
            for error_code, count in metrics['error_codes'].items():
                print(f"  {error_code}: {count}次")
        
        # 性能评估
        self.evaluate_performance(metrics)
    
    def evaluate_performance(self, metrics: Dict[str, Any]):
        """
        评估性能表现
        
        Args:
            metrics: 性能指标字典
        """
        print(f"\n性能评估:")
        
        success_rate = metrics['success_rate']
        avg_response_time = metrics['response_time_stats']['mean']
        p95_response_time = metrics['response_time_stats']['p95']
        qps = metrics['requests_per_second']
        
        # 成功率评估
        if success_rate >= 99.5:
            print(f"  ✅ 成功率优秀: {success_rate:.2f}%")
        elif success_rate >= 95:
            print(f"  ⚠️ 成功率良好: {success_rate:.2f}%")
        else:
            print(f"  ❌ 成功率较低: {success_rate:.2f}%")
        
        # 响应时间评估
        if avg_response_time <= 0.1:
            print(f"  ✅ 平均响应时间优秀: {avg_response_time:.4f}s")
        elif avg_response_time <= 0.5:
            print(f"  ⚠️ 平均响应时间良好: {avg_response_time:.4f}s")
        else:
            print(f"  ❌ 平均响应时间较慢: {avg_response_time:.4f}s")
        
        # P95响应时间评估
        if p95_response_time <= 0.2:
            print(f"  ✅ P95响应时间优秀: {p95_response_time:.4f}s")
        elif p95_response_time <= 1.0:
            print(f"  ⚠️ P95响应时间良好: {p95_response_time:.4f}s")
        else:
            print(f"  ❌ P95响应时间较慢: {p95_response_time:.4f}s")
        
        # QPS评估
        if qps >= 100:
            print(f"  ✅ QPS表现优秀: {qps:.2f}")
        elif qps >= 50:
            print(f"  ⚠️ QPS表现良好: {qps:.2f}")
        else:
            print(f"  ❌ QPS表现一般: {qps:.2f}")
    
    def run_quick_test(self):
        """
        运行快速并发测试
        """
        print(f"\n{'='*80}")
        print(f"Token接口快速并发测试")
        print(f"测试时间: {datetime.now()}")
        print(f"目标接口: {self.token_endpoint}")
        print(f"测试客户: {self.test_customer['app_id']}")
        print(f"{'='*80}")
        
        # 1. 基础并发测试
        metrics = self.test_basic_concurrent(10, 5)
        self.print_metrics(metrics, "基础并发测试 (10线程x5请求)")
        
        time.sleep(1)
        
        # 2. 线程池测试
        metrics = self.test_thread_pool_concurrent(20, 50)
        self.print_metrics(metrics, "线程池测试 (20工作线程x50请求)")
        
        time.sleep(1)
        
        # 3. 突发负载测试
        metrics = self.test_burst_load(15, 3, 2.0)
        self.print_metrics(metrics, "突发负载测试 (15请求x3次突发)")
        
        print(f"\n{'='*80}")
        print("🎉 快速并发测试完成！")
        print(f"{'='*80}")
    
    def run_comprehensive_test(self):
        """
        运行全面并发测试
        """
        print(f"\n{'='*80}")
        print(f"Token接口全面并发测试")
        print(f"测试时间: {datetime.now()}")
        print(f"目标接口: {self.token_endpoint}")
        print(f"测试客户: {self.test_customer['app_id']}")
        print(f"{'='*80}")
        
        # 1. 不同并发级别测试
        concurrent_configs = [
            (5, 10),    # 5线程 x 10请求
            (10, 10),   # 10线程 x 10请求
            (20, 5),    # 20线程 x 5请求
            (50, 2),    # 50线程 x 2请求
        ]
        
        for threads, requests in concurrent_configs:
            metrics = self.test_basic_concurrent(threads, requests)
            self.print_metrics(metrics, f"并发测试 ({threads}线程x{requests}请求)")
            time.sleep(2)
        
        # 2. 线程池测试
        pool_configs = [
            (10, 50),   # 10工作线程 x 50请求
            (20, 100),  # 20工作线程 x 100请求
            (30, 150),  # 30工作线程 x 150请求
        ]
        
        for workers, total in pool_configs:
            metrics = self.test_thread_pool_concurrent(workers, total)
            self.print_metrics(metrics, f"线程池测试 ({workers}工作线程x{total}请求)")
            time.sleep(2)
        
        # 3. 突发负载测试
        metrics = self.test_burst_load(25, 4, 3.0)
        self.print_metrics(metrics, "突发负载测试 (25请求x4次突发)")
        time.sleep(2)
        
        # 4. 持续负载测试
        metrics = self.test_sustained_load(10.0, 30)
        self.print_metrics(metrics, "持续负载测试 (10RPS x 30秒)")
        
        print(f"\n{'='*80}")
        print("🎉 全面并发测试完成！")
        print(f"{'='*80}")

def check_server_status():
    """
    检查服务器状态
    
    Returns:
        bool: 服务器是否可用
    """
    try:
        response = requests.get(f"{BASE_URL}/docs", timeout=5)
        if response.status_code == 200:
            print(f"✅ 服务器状态正常: {BASE_URL}")
            return True
        else:
            print(f"❌ 服务器响应异常: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 无法连接到服务器: {e}")
        return False

def main():
    """
    主函数
    """
    print("Token接口并发测试工具")
    print("=" * 50)
    
    # 检查服务器状态
    if not check_server_status():
        print("\n请确保API服务正在运行后再试")
        return
    
    print(f"\n测试配置:")
    print(f"  API地址: {BASE_URL}")
    print(f"  Token接口: {TOKEN_ENDPOINT}")
    print(f"  测试客户: {TEST_CUSTOMER['app_id']}")
    
    print("\n请选择测试模式:")
    print("1. 快速测试 (约2分钟)")
    print("2. 全面测试 (约10分钟)")
    print("3. 自定义测试")
    
    choice = input("\n请输入选择 (1-3): ").strip()
    
    tester = SimpleConcurrentTester()
    
    if choice == "1":
        tester.run_quick_test()
    elif choice == "2":
        tester.run_comprehensive_test()
    elif choice == "3":
        print("\n自定义测试选项:")
        print("1. 基础并发测试")
        print("2. 线程池测试")
        print("3. 突发负载测试")
        print("4. 持续负载测试")
        
        custom_choice = input("请选择测试类型 (1-4): ").strip()
        
        if custom_choice == "1":
            threads = int(input("线程数 (默认10): ") or "10")
            requests = int(input("每线程请求数 (默认10): ") or "10")
            metrics = tester.test_basic_concurrent(threads, requests)
            tester.print_metrics(metrics, "自定义基础并发测试")
        
        elif custom_choice == "2":
            workers = int(input("工作线程数 (默认20): ") or "20")
            total = int(input("总请求数 (默认100): ") or "100")
            metrics = tester.test_thread_pool_concurrent(workers, total)
            tester.print_metrics(metrics, "自定义线程池测试")
        
        elif custom_choice == "3":
            burst_size = int(input("突发请求数 (默认20): ") or "20")
            burst_count = int(input("突发次数 (默认3): ") or "3")
            interval = float(input("突发间隔秒数 (默认2.0): ") or "2.0")
            metrics = tester.test_burst_load(burst_size, burst_count, interval)
            tester.print_metrics(metrics, "自定义突发负载测试")
        
        elif custom_choice == "4":
            rps = float(input("目标RPS (默认5.0): ") or "5.0")
            duration = int(input("持续时间秒 (默认20): ") or "20")
            metrics = tester.test_sustained_load(rps, duration)
            tester.print_metrics(metrics, "自定义持续负载测试")
        
        else:
            print("无效选择")
    else:
        print("无效选择")

if __name__ == "__main__":
    main()