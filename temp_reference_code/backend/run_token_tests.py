#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
运行Token接口测试的便捷脚本

提供多种测试运行方式：
1. 完整的功能测试（使用requests直接测试）
2. pytest单元测试
3. 快速验证测试

Author: System
Date: 2024
"""

import sys
import os
import argparse
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def run_functional_tests():
    """
    运行功能测试（使用requests）
    """
    print("\n=== 运行功能测试 ===")
    try:
        from test_token_endpoint import main
        results = main()
        return results
    except ImportError as e:
        print(f"❌ 导入测试模块失败: {e}")
        return None
    except Exception as e:
        print(f"❌ 运行功能测试失败: {e}")
        return None

def run_pytest_tests():
    """
    运行pytest单元测试
    """
    print("\n=== 运行pytest单元测试 ===")
    try:
        import pytest
        
        # 运行token认证相关的测试
        test_files = [
            "tests/test_token_auth.py"
        ]
        
        args = ["-v", "--tb=short"] + test_files
        result = pytest.main(args)
        
        return result == 0  # pytest返回0表示成功
    except ImportError:
        print("❌ pytest未安装，请运行: pip install pytest")
        return False
    except Exception as e:
        print(f"❌ 运行pytest测试失败: {e}")
        return False

def run_quick_test():
    """
    运行快速验证测试
    """
    print("\n=== 运行快速验证测试 ===")
    
    try:
        import requests
        import time
        import hmac
        import hashlib
        import random
        import string
        
        # 测试配置
        BASE_URL = "http://localhost:8000"
        TOKEN_ENDPOINT = f"{BASE_URL}/api/v1/auth/token"
        
        # 测试客户数据
        TEST_CUSTOMER = {
            "app_id": "test_app_001",
            "app_secret": "test_secret_123456789"
        }
        
        def generate_nonce(length=12):
            """生成随机nonce"""
            chars = string.ascii_letters + string.digits
            return ''.join(random.choice(chars) for _ in range(length))
        
        def generate_signature(appid, timestamp, nonce, secret):
            """生成签名"""
            signature_data = f"{appid}{timestamp}{nonce}"
            signature = hmac.new(
                secret.encode('utf-8'),
                signature_data.encode('utf-8'),
                hashlib.sha256
            ).hexdigest().upper()
            return signature
        
        # 创建认证请求
        appid = TEST_CUSTOMER["app_id"]
        timestamp = int(time.time())
        nonce = generate_nonce()
        secret = TEST_CUSTOMER["app_secret"]
        signature = generate_signature(appid, timestamp, nonce, secret)
        
        auth_data = {
            "appid": appid,
            "timestamp": timestamp,
            "nonce": nonce,
            "signature": signature
        }
        
        print(f"测试接口: {TOKEN_ENDPOINT}")
        print(f"请求数据: {auth_data}")
        
        # 发送请求
        try:
            response = requests.post(
                TOKEN_ENDPOINT,
                json=auth_data,
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            
            print(f"\n响应状态码: {response.status_code}")
            print(f"响应内容: {response.text}")
            
            if response.status_code == 200:
                data = response.json()
                if all(key in data for key in ["access_token", "data_key", "expires_in"]):
                    print("\n✅ 快速测试通过！Token接口基本功能正常")
                    return True
                else:
                    print("\n❌ 响应缺少必需字段")
                    return False
            else:
                print(f"\n❌ 请求失败，状态码: {response.status_code}")
                return False
                
        except requests.exceptions.ConnectionError:
            print("\n❌ 连接失败，请确保服务器正在运行")
            return False
        except Exception as e:
            print(f"\n❌ 请求异常: {e}")
            return False
            
    except ImportError as e:
        print(f"❌ 导入依赖失败: {e}")
        return False
    except Exception as e:
        print(f"❌ 快速测试异常: {e}")
        return False

def check_server_status():
    """
    检查服务器状态
    """
    print("\n=== 检查服务器状态 ===")
    
    try:
        import requests
        
        # 检查服务器是否运行
        base_url = "http://localhost:8000"
        
        try:
            response = requests.get(f"{base_url}/docs", timeout=5)
            if response.status_code == 200:
                print("✅ 服务器正在运行")
                return True
            else:
                print(f"⚠️ 服务器响应异常，状态码: {response.status_code}")
                return False
        except requests.exceptions.ConnectionError:
            print("❌ 无法连接到服务器")
            print("请确保服务器正在运行：")
            print("  cd backend")
            print("  python main.py")
            print("  或")
            print("  uvicorn app.main:app --reload")
            return False
        except Exception as e:
            print(f"❌ 检查服务器状态异常: {e}")
            return False
            
    except ImportError:
        print("❌ requests库未安装")
        return False

def show_test_info():
    """
    显示测试信息
    """
    print("\n" + "="*60)
    print("Token接口测试工具")
    print("="*60)
    print("\n测试文件说明:")
    print("1. test_token_endpoint.py - 完整功能测试（使用requests）")
    print("2. tests/test_token_auth.py - pytest单元测试")
    print("3. run_token_tests.py - 本脚本（测试运行器）")
    
    print("\n测试场景包括:")
    print("• 正常认证流程")
    print("• 时间窗口校验（±5分钟）")
    print("• 防重放攻击（nonce校验）")
    print("• 签名验证（HMAC-SHA256）")
    print("• 参数验证")
    print("• 错误处理")
    print("• 并发请求")
    
    print("\n注意事项:")
    print("• 确保服务器正在运行（http://localhost:8000）")
    print("• 确保数据库中存在测试客户数据")
    print("• 测试客户: app_id=test_app_001, app_secret=test_secret_123456789")
    print("="*60)

def main():
    """
    主函数
    """
    parser = argparse.ArgumentParser(
        description="Token接口测试工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例用法:
  python run_token_tests.py --quick          # 快速测试
  python run_token_tests.py --functional     # 功能测试
  python run_token_tests.py --pytest         # pytest测试
  python run_token_tests.py --all            # 运行所有测试
  python run_token_tests.py --info           # 显示测试信息
        """
    )
    
    parser.add_argument(
        "--quick", 
        action="store_true", 
        help="运行快速验证测试"
    )
    parser.add_argument(
        "--functional", 
        action="store_true", 
        help="运行完整功能测试"
    )
    parser.add_argument(
        "--pytest", 
        action="store_true", 
        help="运行pytest单元测试"
    )
    parser.add_argument(
        "--all", 
        action="store_true", 
        help="运行所有测试"
    )
    parser.add_argument(
        "--info", 
        action="store_true", 
        help="显示测试信息"
    )
    parser.add_argument(
        "--check-server", 
        action="store_true", 
        help="检查服务器状态"
    )
    
    args = parser.parse_args()
    
    # 如果没有指定参数，显示帮助信息
    if not any(vars(args).values()):
        show_test_info()
        parser.print_help()
        return
    
    # 显示测试信息
    if args.info:
        show_test_info()
        return
    
    # 检查服务器状态
    if args.check_server:
        check_server_status()
        return
    
    # 检查服务器状态（在运行测试前）
    if not check_server_status():
        print("\n⚠️ 服务器未运行，某些测试可能失败")
        response = input("是否继续运行测试？(y/N): ")
        if response.lower() != 'y':
            return
    
    results = []
    
    # 运行快速测试
    if args.quick or args.all:
        result = run_quick_test()
        results.append(("快速测试", result))
    
    # 运行功能测试
    if args.functional or args.all:
        result = run_functional_tests()
        results.append(("功能测试", result is not None))
    
    # 运行pytest测试
    if args.pytest or args.all:
        result = run_pytest_tests()
        results.append(("pytest测试", result))
    
    # 显示测试结果总结
    if results:
        print("\n" + "="*60)
        print("测试结果总结")
        print("="*60)
        
        passed_count = 0
        for test_name, result in results:
            status = "✅ 通过" if result else "❌ 失败"
            print(f"{test_name:<15} {status}")
            if result:
                passed_count += 1
        
        total_count = len(results)
        print(f"\n总计: {passed_count}/{total_count} 项测试通过")
        
        if passed_count == total_count:
            print("\n🎉 所有测试通过！")
        else:
            print(f"\n⚠️ 有 {total_count - passed_count} 项测试失败")

if __name__ == "__main__":
    main()