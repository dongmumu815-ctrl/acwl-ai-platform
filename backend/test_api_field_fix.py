#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试 API 字段创建接口修复

验证修复后的 /api/v1/apis/{id}/fields 接口能够正确处理缺少 field_label 的请求。

Author: System
Date: 2024
"""

import requests
import json
import sys
from datetime import datetime

# 配置
BASE_URL = "http://localhost:8082"
API_ID = 15  # 使用用户提到的 API ID

def test_api_field_creation():
    """
    测试 API 字段创建接口
    
    测试用例：
    1. 使用用户原始数据（缺少 field_label）
    2. 验证接口是否能正确处理并自动生成 field_label
    """
    print("=== 测试 API 字段创建接口修复 ===")
    print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"API ID: {API_ID}")
    print()
    
    # 用户原始数据（缺少 field_label）
    test_data = {
        "field_name": "test",
        "field_type": "string",
        "is_required": False,
        "default_value": "test",
        "description": "test",
        "validation_rules": "test",  # 注意：这个字段在 schema 中应该是 validation_regex
        "field_order": 1  # 注意：这个字段在 schema 中应该是 sort_order
    }
    
    print("📋 原始测试数据:")
    print(json.dumps(test_data, indent=2, ensure_ascii=False))
    print()
    
    # 修正数据以匹配 schema
    corrected_data = {
        "field_name": "test_fixed",
        "field_type": "string", 
        "is_required": False,
        "default_value": "test",
        "description": "test",
        "validation_regex": "test",  # 修正字段名
        "sort_order": 1  # 修正字段名
        # 注意：故意不包含 field_label 来测试自动生成功能
    }
    
    print("🔧 修正后的测试数据:")
    print(json.dumps(corrected_data, indent=2, ensure_ascii=False))
    print()
    
    # 发送请求
    url = f"{BASE_URL}/api/v1/apis/{API_ID}/fields"
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    
    try:
        print(f"🚀 发送 POST 请求到: {url}")
        response = requests.post(url, json=corrected_data, headers=headers, timeout=10)
        
        print(f"📊 响应状态码: {response.status_code}")
        print(f"📊 响应头: {dict(response.headers)}")
        print()
        
        if response.status_code == 200:
            print("✅ 请求成功!")
            response_data = response.json()
            print("📄 响应数据:")
            print(json.dumps(response_data, indent=2, ensure_ascii=False))
            
            # 验证 field_label 是否自动生成
            if 'data' in response_data and 'field_label' in response_data['data']:
                field_label = response_data['data']['field_label']
                print(f"\n🎯 field_label 自动生成结果: '{field_label}'")
                if field_label == corrected_data['field_name']:
                    print("✅ field_label 自动生成成功，使用了 field_name 作为默认值")
                else:
                    print(f"⚠️  field_label 值为 '{field_label}'，与预期的 '{corrected_data['field_name']}' 不同")
            else:
                print("⚠️  响应中未找到 field_label 字段")
                
        elif response.status_code == 422:
            print("❌ 请求失败 - 422 Unprocessable Entity")
            try:
                error_data = response.json()
                print("📄 错误详情:")
                print(json.dumps(error_data, indent=2, ensure_ascii=False))
                
                # 分析错误
                if 'detail' in error_data:
                    for error in error_data['detail']:
                        if error.get('type') == 'missing' and 'field_label' in error.get('loc', []):
                            print("\n❌ 修复失败：field_label 字段仍然是必填的")
                            return False
                        else:
                            print(f"\n⚠️  其他验证错误: {error}")
            except json.JSONDecodeError:
                print("📄 错误响应（非JSON格式）:")
                print(response.text)
        else:
            print(f"❌ 请求失败 - HTTP {response.status_code}")
            print("📄 响应内容:")
            print(response.text)
            
    except requests.exceptions.RequestException as e:
        print(f"❌ 网络请求失败: {e}")
        return False
    except Exception as e:
        print(f"❌ 测试过程中发生错误: {e}")
        return False
    
    return response.status_code == 200

def test_with_field_label():
    """
    测试包含 field_label 的正常请求
    """
    print("\n" + "="*50)
    print("=== 测试包含 field_label 的正常请求 ===")
    
    test_data = {
        "field_name": "test_with_label",
        "field_label": "测试标签",
        "field_type": "string",
        "is_required": True,
        "default_value": "default_test",
        "description": "包含 field_label 的测试字段",
        "sort_order": 2
    }
    
    print("📋 测试数据:")
    print(json.dumps(test_data, indent=2, ensure_ascii=False))
    print()
    
    url = f"{BASE_URL}/api/v1/apis/{API_ID}/fields"
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    
    try:
        print(f"🚀 发送 POST 请求到: {url}")
        response = requests.post(url, json=test_data, headers=headers, timeout=10)
        
        print(f"📊 响应状态码: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ 包含 field_label 的请求成功!")
            response_data = response.json()
            print("📄 响应数据:")
            print(json.dumps(response_data, indent=2, ensure_ascii=False))
            return True
        else:
            print(f"❌ 请求失败 - HTTP {response.status_code}")
            print("📄 响应内容:")
            print(response.text)
            return False
            
    except Exception as e:
        print(f"❌ 测试过程中发生错误: {e}")
        return False

def main():
    """
    主测试函数
    """
    print("🔧 API 字段创建接口修复测试")
    print("="*60)
    
    # 测试1：缺少 field_label 的请求
    success1 = test_api_field_creation()
    
    # 测试2：包含 field_label 的正常请求
    success2 = test_with_field_label()
    
    print("\n" + "="*60)
    print("📊 测试结果总结:")
    print(f"  - 缺少 field_label 的请求: {'✅ 通过' if success1 else '❌ 失败'}")
    print(f"  - 包含 field_label 的请求: {'✅ 通过' if success2 else '❌ 失败'}")
    
    if success1 and success2:
        print("\n🎉 所有测试通过！API 字段创建接口修复成功！")
        return 0
    else:
        print("\n❌ 部分测试失败，需要进一步检查。")
        return 1

if __name__ == "__main__":
    sys.exit(main())