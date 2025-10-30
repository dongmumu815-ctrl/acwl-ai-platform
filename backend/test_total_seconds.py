#!/usr/bin/env python3
"""测试total_seconds错误的脚本"""

import sys
sys.path.append('.')
from datetime import datetime, timedelta

def test_total_seconds_error():
    """测试可能导致total_seconds错误的情况"""
    
    print("测试total_seconds方法调用...")
    print("=" * 50)
    
    # 测试用例
    test_cases = [
        ("int", 123456789),
        ("float", 123456789.0),
        ("string", "2024-01-01"),
        ("None", None),
        ("datetime", datetime.now()),
        ("timedelta", timedelta(seconds=60))
    ]
    
    for case_name, case_value in test_cases:
        try:
            print(f"测试 {case_name}: {case_value}")
            if hasattr(case_value, 'total_seconds'):
                result = case_value.total_seconds()
                print(f"  结果: {result}")
            else:
                print(f"  没有total_seconds方法")
        except Exception as e:
            print(f"  错误: {type(e).__name__}: {e}")
        print()
    
    # 测试时间差计算
    print("测试时间差计算...")
    print("=" * 50)
    
    now = datetime.now()
    past_time = datetime.now() - timedelta(hours=1)
    
    # 正确的时间差计算
    try:
        diff = now - past_time
        seconds = diff.total_seconds()
        print(f"正确的时间差计算: {seconds} 秒")
    except Exception as e:
        print(f"时间差计算错误: {e}")
    
    # 错误的情况：直接对int调用total_seconds
    try:
        wrong_value = 123456789
        result = wrong_value.total_seconds()  # 这会导致错误
        print(f"错误调用结果: {result}")
    except Exception as e:
        print(f"预期的错误: {type(e).__name__}: {e}")

if __name__ == "__main__":
    test_total_seconds_error()