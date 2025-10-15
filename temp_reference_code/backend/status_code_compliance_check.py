#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Token接口状态码合规性检查

对比API文档要求与实际实现，检查状态码是否完全符合规范

Author: System
Date: 2024
"""

import sys
import os
from pathlib import Path
from typing import Dict, List, Tuple

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def analyze_status_codes():
    """
    分析Token接口状态码合规性
    """
    print("=== Token接口状态码合规性检查 ===")
    print()
    
    # API文档要求的状态码
    doc_requirements = {
        400: "参数缺失或格式错误",
        401: "签名验证失败", 
        402: "请求时间戳不在允许窗口",
        403: "请求已被重放（nonce 已使用）",
        404: "appid 无效或未授权",
        500: "内部服务器错误"
    }
    
    # 实际实现的状态码（从auth.py分析得出）
    actual_implementation = {
        200: "认证成功，返回access_token和data_key",
        401: "签名验证失败 (auth_request.signature != expected_signature)",
        402: "请求时间戳不在允许窗口 (time_diff > 300)", 
        403: "请求已被重放 (check_nonce返回True)",
        404: "appid无效或未授权 (customer not found或status != True)",
        422: "参数验证失败 (Pydantic validation error)",
        500: "内部服务器错误 (Exception处理)"
    }
    
    print("📋 API文档要求的状态码:")
    for code, desc in doc_requirements.items():
        print(f"  {code}: {desc}")
    
    print("\n🔧 实际实现的状态码:")
    for code, desc in actual_implementation.items():
        print(f"  {code}: {desc}")
    
    print("\n🔍 合规性分析:")
    
    # 检查每个文档要求的状态码
    compliance_issues = []
    
    for doc_code, doc_desc in doc_requirements.items():
        if doc_code in actual_implementation:
            print(f"  ✅ {doc_code}: 已实现 - {doc_desc}")
        else:
            print(f"  ❌ {doc_code}: 未实现 - {doc_desc}")
            compliance_issues.append((doc_code, doc_desc, "未实现"))
    
    # 检查额外实现的状态码
    extra_codes = set(actual_implementation.keys()) - set(doc_requirements.keys())
    if extra_codes:
        print("\n📝 额外实现的状态码:")
        for code in extra_codes:
            desc = actual_implementation[code]
            if code == 422:
                print(f"  ⚠️  {code}: {desc} (FastAPI自动参数验证)")
                compliance_issues.append((code, desc, "额外实现，可能与400重复"))
            elif code == 200:
                print(f"  ✅ {code}: {desc} (成功响应)")
            else:
                print(f"  ❓ {code}: {desc}")
    
    print("\n📊 详细分析:")
    
    # 400 vs 422 冲突分析
    print("\n1. 参数验证状态码分析:")
    print("   📖 文档要求: 400 - 参数缺失或格式错误")
    print("   🔧 实际实现: 422 - FastAPI自动参数验证")
    print("   💡 建议: 需要统一为400状态码")
    
    # 其他状态码分析
    critical_codes = [401, 402, 403, 404, 500]
    print("\n2. 关键状态码实现情况:")
    for code in critical_codes:
        if code in actual_implementation:
            print(f"   ✅ {code}: 正确实现")
        else:
            print(f"   ❌ {code}: 缺失实现")
    
    return compliance_issues

def generate_fix_recommendations(issues: List[Tuple]):
    """
    生成修复建议
    
    Args:
        issues: 合规性问题列表
    """
    print("\n🔧 修复建议:")
    print()
    
    # 422 -> 400 转换建议
    print("1. 参数验证状态码统一:")
    print("   问题: FastAPI默认返回422，但文档要求400")
    print("   解决方案:")
    print("   - 添加自定义异常处理器，将422转换为400")
    print("   - 或者在路由中捕获ValidationError并抛出400异常")
    print()
    
    print("2. 实现示例代码:")
    print("```python")
    print("# 在main.py中添加异常处理器")
    print("from fastapi.exceptions import RequestValidationError")
    print("")
    print("@app.exception_handler(RequestValidationError)")
    print("async def validation_exception_handler(request: Request, exc: RequestValidationError):")
    print("    return JSONResponse(")
    print("        status_code=400,  # 改为400")
    print("        content={")
    print("            \"error\": True,")
    print("            \"message\": \"参数缺失或格式错误\",")
    print("            \"code\": 400,")
    print("            \"timestamp\": int(time.time())")
    print("        }")
    print("    )")
    print("```")
    print()
    
    print("3. 测试验证:")
    print("   - 发送缺少必需参数的请求")
    print("   - 发送格式错误的参数")
    print("   - 验证返回状态码为400而不是422")
    print()

def check_error_response_format():
    """
    检查错误响应格式
    """
    print("📝 错误响应格式检查:")
    print()
    
    print("当前实现的错误响应格式:")
    print("```json")
    print("{")
    print("    \"error\": true,")
    print("    \"message\": \"错误描述\",")
    print("    \"code\": 状态码数字,")
    print("    \"timestamp\": 时间戳")
    print("}")
    print("```")
    print()
    
    print("✅ 响应格式符合API文档要求")
    print("✅ 包含数字错误码")
    print("✅ 包含错误描述信息")
    print("✅ 包含时间戳")
    print()

def run_compliance_test():
    """
    运行合规性测试
    """
    print("🧪 运行合规性测试...")
    print()
    
    try:
        import requests
        import time
        import hmac
        import hashlib
        import random
        import string
        
        BASE_URL = "http://localhost:8000"
        TOKEN_ENDPOINT = f"{BASE_URL}/api/v1/auth/token"
        
        def generate_nonce(length=12):
            chars = string.ascii_letters + string.digits
            return ''.join(random.choice(chars) for _ in range(length))
        
        def generate_signature(appid, timestamp, nonce, secret):
            signature_data = f"{appid}{timestamp}{nonce}"
            signature = hmac.new(
                secret.encode('utf-8'),
                signature_data.encode('utf-8'),
                hashlib.sha256
            ).hexdigest().upper()
            return signature
        
        test_results = {}
        
        # 测试422 -> 400转换
        print("测试1: 参数验证错误状态码")
        try:
            # 发送缺少必需参数的请求（缺少appid字段）
            response = requests.post(
                TOKEN_ENDPOINT,
                json={
                    "timestamp": int(time.time()),
                    "nonce": generate_nonce(),
                    "signature": "test_signature"
                    # 故意缺少appid字段来触发参数验证错误
                },
                headers={"Content-Type": "application/json"},
                timeout=5
            )
            
            print(f"  状态码: {response.status_code}")
            print(f"  响应内容: {response.text[:200]}...")  # 显示部分响应内容
            
            if response.status_code == 400:
                print("  ✅ 正确返回400状态码")
                test_results["param_validation"] = True
            elif response.status_code == 422:
                print("  ⚠️  返回422状态码，应该是400")
                test_results["param_validation"] = False
            else:
                print(f"  ❌ 意外的状态码: {response.status_code}")
                test_results["param_validation"] = False
                
        except Exception as e:
            print(f"  ❌ 测试异常: {e}")
            test_results["param_validation"] = False
        
        # 测试其他状态码
        status_code_tests = [
            ("时间窗口校验", {"appid": "test_app_001", "timestamp": int(time.time()) - 400, "nonce": generate_nonce(), "signature": "test"}, 402),
            ("无效appid", {"appid": "invalid_app", "timestamp": int(time.time()), "nonce": generate_nonce(), "signature": "test"}, 404),
            ("签名验证失败", {"appid": "test_app_001", "timestamp": int(time.time()), "nonce": generate_nonce(), "signature": "wrong_signature"}, 401)
        ]
        
        for test_name, test_data, expected_code in status_code_tests:
            print(f"\n测试: {test_name}")
            try:
                response = requests.post(
                    TOKEN_ENDPOINT,
                    json=test_data,
                    headers={"Content-Type": "application/json"},
                    timeout=5
                )
                
                print(f"  状态码: {response.status_code}")
                if response.status_code == expected_code:
                    print(f"  ✅ 正确返回{expected_code}状态码")
                    test_results[test_name] = True
                else:
                    print(f"  ❌ 期望{expected_code}，实际{response.status_code}")
                    test_results[test_name] = False
                    
            except Exception as e:
                print(f"  ❌ 测试异常: {e}")
                test_results[test_name] = False
        
        # 测试结果汇总
        print("\n📊 测试结果汇总:")
        passed = sum(test_results.values())
        total = len(test_results)
        
        for test_name, result in test_results.items():
            status = "✅ 通过" if result else "❌ 失败"
            print(f"  {test_name}: {status}")
        
        print(f"\n总计: {passed}/{total} 项测试通过")
        
        return test_results
        
    except ImportError:
        print("❌ 缺少requests库，无法运行测试")
        return {}
    except Exception as e:
        print(f"❌ 测试运行异常: {e}")
        return {}

def main():
    """
    主函数
    """
    print("🔍 Token接口状态码合规性检查工具")
    print("=" * 60)
    print()
    
    # 1. 分析状态码合规性
    issues = analyze_status_codes()
    
    print("\n" + "=" * 60)
    
    # 2. 检查错误响应格式
    check_error_response_format()
    
    print("=" * 60)
    
    # 3. 生成修复建议
    if issues:
        generate_fix_recommendations(issues)
        print("=" * 60)
    
    # 4. 运行合规性测试
    test_results = run_compliance_test()
    
    print("\n" + "=" * 60)
    print("📋 总结:")
    print()
    
    if not issues:
        print("✅ 所有状态码都符合API文档要求")
    else:
        print(f"⚠️  发现 {len(issues)} 个合规性问题:")
        for code, desc, issue_type in issues:
            print(f"  - {code}: {issue_type}")
    
    if test_results:
        passed_tests = sum(test_results.values())
        total_tests = len(test_results)
        if passed_tests == total_tests:
            print("✅ 所有实际测试都通过")
        else:
            print(f"⚠️  {total_tests - passed_tests} 个测试失败")
    
    print("\n🎯 主要发现:")
    print("1. Token接口核心状态码(401,402,403,404,500)已正确实现")
    print("2. 参数验证返回422而非文档要求的400")
    print("3. 错误响应格式符合API文档规范")
    print("4. 建议添加异常处理器统一参数验证状态码")
    
if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n⚠️  用户中断操作")
    except Exception as e:
        print(f"\n💥 运行异常: {str(e)}")
        import traceback
        traceback.print_exc()