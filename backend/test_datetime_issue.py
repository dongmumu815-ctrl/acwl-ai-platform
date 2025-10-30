#!/usr/bin/env python3
"""
测试datetime类型问题，重现'int' object has no attribute 'total_seconds'错误
"""

from datetime import datetime, timedelta

def test_datetime_operations():
    """测试各种datetime操作"""
    
    print("=== 测试datetime操作 ===")
    
    # 正常情况：两个datetime对象相减
    now = datetime.utcnow()
    last_heartbeat = datetime.utcnow() - timedelta(minutes=5)
    
    print(f"now: {now} (type: {type(now)})")
    print(f"last_heartbeat: {last_heartbeat} (type: {type(last_heartbeat)})")
    
    # 正常的时间差计算
    time_diff = now - last_heartbeat
    print(f"time_diff: {time_diff} (type: {type(time_diff)})")
    print(f"time_diff.total_seconds(): {time_diff.total_seconds()}")
    
    print("\n=== 测试可能的错误情况 ===")
    
    # 情况1：last_heartbeat为None
    try:
        last_heartbeat_none = None
        if last_heartbeat_none:
            time_since_heartbeat = (now - last_heartbeat_none).total_seconds()
        else:
            print("last_heartbeat为None，跳过计算")
    except Exception as e:
        print(f"错误1: {e}")
    
    # 情况2：last_heartbeat为整数时间戳
    try:
        last_heartbeat_int = 1692345600  # 整数时间戳
        print(f"last_heartbeat_int: {last_heartbeat_int} (type: {type(last_heartbeat_int)})")
        time_since_heartbeat = (now - last_heartbeat_int).total_seconds()
        print(f"time_since_heartbeat: {time_since_heartbeat}")
    except Exception as e:
        print(f"错误2 (datetime - int): {e}")
    
    # 情况3：now为整数时间戳
    try:
        now_int = 1692345700  # 整数时间戳
        print(f"now_int: {now_int} (type: {type(now_int)})")
        time_since_heartbeat = (now_int - last_heartbeat).total_seconds()
        print(f"time_since_heartbeat: {time_since_heartbeat}")
    except Exception as e:
        print(f"错误3 (int - datetime): {e}")
    
    # 情况4：两个整数相减
    try:
        now_int = 1692345700
        last_heartbeat_int = 1692345600
        print(f"now_int: {now_int}, last_heartbeat_int: {last_heartbeat_int}")
        time_diff_int = now_int - last_heartbeat_int
        print(f"time_diff_int: {time_diff_int} (type: {type(time_diff_int)})")
        time_since_heartbeat = time_diff_int.total_seconds()  # 这会导致错误
        print(f"time_since_heartbeat: {time_since_heartbeat}")
    except Exception as e:
        print(f"错误4 (int.total_seconds()): {e}")

if __name__ == "__main__":
    test_datetime_operations()