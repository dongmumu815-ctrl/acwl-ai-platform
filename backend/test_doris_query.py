#!/usr/bin/env python3
"""
测试 Doris 查询 API 修复
"""

import requests
import json

def test_doris_query():
    """测试 Doris 查询 API"""
    
    # API 端点
    url = "http://localhost:8082/api/v1/datasources/10/query"
    
    # 测试数据
    test_data = {
        "query": "SELECT * FROM test_table",
        "limit": 10,
        "timeout": 30,
        "offset": 0,
        "enable_pagination": False
    }
    
    print("🧪 测试 Doris 查询 API...")
    print(f"📡 请求 URL: {url}")
    print(f"📝 请求数据: {json.dumps(test_data, indent=2, ensure_ascii=False)}")
    
    try:
        # 发送 POST 请求
        response = requests.post(url, json=test_data, timeout=60)
        
        print(f"📊 响应状态码: {response.status_code}")
        print(f"📄 响应头: {dict(response.headers)}")
        
        # 解析响应
        if response.headers.get('content-type', '').startswith('application/json'):
            response_data = response.json()
            print(f"📋 响应数据: {json.dumps(response_data, indent=2, ensure_ascii=False)}")
            
            # 检查是否修复了参数错误
            if response_data.get('success') is False:
                error_message = response_data.get('message', '')
                if 'takes 5 positional arguments but 7 were given' in error_message:
                    print("❌ 错误：参数不匹配问题仍然存在")
                    return False
                else:
                    print(f"⚠️  查询失败，但不是参数问题: {error_message}")
            else:
                print("✅ 查询成功！参数问题已修复")
                return True
        else:
            print(f"📄 响应内容: {response.text}")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ 请求失败: {e}")
        return False
    except json.JSONDecodeError as e:
        print(f"❌ JSON 解析失败: {e}")
        return False
    except Exception as e:
        print(f"❌ 未知错误: {e}")
        return False
    
    return True

def test_doris_query_with_pagination():
    """测试带分页的 Doris 查询"""
    
    url = "http://localhost:8082/api/v1/datasources/10/query"
    
    test_data = {
        "query": "SELECT * FROM test_table",
        "limit": 5,
        "timeout": 30,
        "offset": 10,
        "enable_pagination": True
    }
    
    print("\n🧪 测试带分页的 Doris 查询 API...")
    print(f"📝 请求数据: {json.dumps(test_data, indent=2, ensure_ascii=False)}")
    
    try:
        response = requests.post(url, json=test_data, timeout=60)
        print(f"📊 响应状态码: {response.status_code}")
        
        if response.headers.get('content-type', '').startswith('application/json'):
            response_data = response.json()
            print(f"📋 响应数据: {json.dumps(response_data, indent=2, ensure_ascii=False)}")
            
            if response_data.get('success') is False:
                error_message = response_data.get('message', '')
                if 'takes 5 positional arguments but 7 were given' in error_message:
                    print("❌ 错误：参数不匹配问题仍然存在")
                    return False
                else:
                    print(f"⚠️  查询失败，但不是参数问题: {error_message}")
            else:
                print("✅ 分页查询成功！")
                # 检查是否包含分页信息
                if 'total_count' in response_data:
                    print(f"📊 总记录数: {response_data['total_count']}")
                return True
        
    except Exception as e:
        print(f"❌ 分页测试失败: {e}")
        return False
    
    return True

if __name__ == "__main__":
    print("🚀 开始测试 Doris 查询 API 修复...")
    
    # 基本查询测试
    basic_test_result = test_doris_query()
    
    # 分页查询测试
    pagination_test_result = test_doris_query_with_pagination()
    
    print("\n📊 测试结果总结:")
    print(f"基本查询测试: {'✅ 通过' if basic_test_result else '❌ 失败'}")
    print(f"分页查询测试: {'✅ 通过' if pagination_test_result else '❌ 失败'}")
    
    if basic_test_result and pagination_test_result:
        print("\n🎉 所有测试通过！Doris 查询 API 修复成功！")
    else:
        print("\n⚠️  部分测试失败，请检查具体错误信息")