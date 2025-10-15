#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试内网IP检查功能

验证新添加的内网IP检查逻辑是否正常工作
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.api.v1.router import is_internal_ip

def test_ip_check():
    """
    测试IP检查函数
    """
    print("测试内网IP检查功能...")
    print("="*50)
    
    # 测试用例
    test_cases = [
        # 内网IP - 应该返回True
        ("192.168.1.1", True, "192.168网段"),
        ("192.168.0.100", True, "192.168网段"),
        ("192.168.255.255", True, "192.168网段"),
        ("10.0.0.1", True, "10.0网段"),
        ("10.1.1.1", True, "10.0网段"),
        ("10.255.255.255", True, "10.0网段"),
        
        # 外网IP - 应该返回False
        ("8.8.8.8", False, "Google DNS"),
        ("114.114.114.114", False, "114 DNS"),
        ("172.16.0.1", False, "172网段（不在允许范围内）"),
        ("127.0.0.1", False, "本地回环地址"),
        
        # 无效IP - 应该返回False
        ("invalid_ip", False, "无效IP"),
        ("", False, "空字符串"),
        (None, False, "None值"),
        ("unknown", False, "unknown字符串"),
    ]
    
    success_count = 0
    total_count = len(test_cases)
    
    for ip, expected, description in test_cases:
        try:
            result = is_internal_ip(ip)
            status = "✓" if result == expected else "✗"
            ip_str = str(ip) if ip is not None else "None"
            print(f"{status} {ip_str:<15} -> {result:<5} (期望: {expected:<5}) - {description}")
            if result == expected:
                success_count += 1
        except Exception as e:
            ip_str = str(ip) if ip is not None else "None"
            print(f"✗ {ip_str:<15} -> 错误: {e} - {description}")
    
    print("="*50)
    print(f"测试结果: {success_count}/{total_count} 通过")
    
    if success_count == total_count:
        print("✓ 所有测试通过！")
        return True
    else:
        print("✗ 部分测试失败！")
        return False

if __name__ == "__main__":
    test_ip_check()