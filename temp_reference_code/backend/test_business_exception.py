#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试业务异常和业务状态码功能

验证 BusinessException 和 BusinessCode 是否正常工作
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.core.business_codes import BusinessCode, BusinessResponse, BusinessException

def test_business_codes():
    """测试业务状态码"""
    print("=== 测试业务状态码 ===")
    
    # 测试成功状态码
    print(f"SUCCESS: code={BusinessCode.SUCCESS.code}, message={BusinessCode.SUCCESS.message}")
    
    # 测试错误状态码
    print(f"API_NOT_FOUND: code={BusinessCode.API_NOT_FOUND.code}, message={BusinessCode.API_NOT_FOUND.message}")
    print(f"TOKEN_INVALID: code={BusinessCode.TOKEN_INVALID.code}, message={BusinessCode.TOKEN_INVALID.message}")
    print(f"BATCH_NOT_FOUND: code={BusinessCode.BATCH_NOT_FOUND.code}, message={BusinessCode.BATCH_NOT_FOUND.message}")
    
    # 测试新添加的状态码
    print(f"TOKEN_MISSING: code={BusinessCode.TOKEN_MISSING.code}, message={BusinessCode.TOKEN_MISSING.message}")
    print(f"ACCESS_DENIED: code={BusinessCode.ACCESS_DENIED.code}, message={BusinessCode.ACCESS_DENIED.message}")
    print(f"BATCH_ALREADY_EXISTS: code={BusinessCode.BATCH_ALREADY_EXISTS.code}, message={BusinessCode.BATCH_ALREADY_EXISTS.message}")
    print(f"REQUEST_TOO_LARGE: code={BusinessCode.REQUEST_TOO_LARGE.code}, message={BusinessCode.REQUEST_TOO_LARGE.message}")
    print(f"CUSTOMER_DISABLED: code={BusinessCode.CUSTOMER_DISABLED.code}, message={BusinessCode.CUSTOMER_DISABLED.message}")

def test_business_response():
    """测试业务响应"""
    print("\n=== 测试业务响应 ===")
    
    # 测试成功响应
    success_response = BusinessResponse.success({"test": "data"})
    print(f"Success Response: {success_response}")
    
    # 测试带消息的成功响应
    success_with_message = BusinessResponse.success({"test": "data"}, "操作成功")
    print(f"Success with Message: {success_with_message}")
    
    # 测试错误响应
    error_response = BusinessResponse.error(BusinessCode.API_NOT_FOUND)
    print(f"Error Response: {error_response}")
    
    # 测试带详情的错误响应
    error_with_detail = BusinessResponse.error(BusinessCode.API_NOT_FOUND, "API 'test_api' 不存在")
    print(f"Error with Detail: {error_with_detail}")
    
    # 测试自定义错误响应
    custom_error = BusinessResponse.custom_error(9999, "自定义错误")
    print(f"Custom Error: {custom_error}")

def test_business_exception():
    """测试业务异常"""
    print("\n=== 测试业务异常 ===")
    
    try:
        # 测试基本异常
        raise BusinessException(BusinessCode.API_NOT_FOUND)
    except BusinessException as e:
        print(f"Basic Exception: code={e.business_code.code}, message={e.business_code.message}, detail={e.detail}")
    
    try:
        # 测试带详情的异常
        raise BusinessException(BusinessCode.TOKEN_INVALID, "Token已过期，请重新登录")
    except BusinessException as e:
        print(f"Exception with Detail: code={e.business_code.code}, message={e.business_code.message}, detail={e.detail}")
        print(f"Exception str: {str(e)}")

def main():
    """主函数"""
    print("开始测试业务异常和状态码功能...\n")
    
    try:
        test_business_codes()
        test_business_response()
        test_business_exception()
        
        print("\n✅ 所有测试通过！")
        
    except Exception as e:
        print(f"\n❌ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()