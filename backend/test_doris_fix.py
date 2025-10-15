#!/usr/bin/env python3
"""
测试 Doris 查询修复
"""

import requests
import json

def test_doris_query_fix():
    """测试 Doris 查询修复"""
    
    # API 端点
    url = "http://localhost:8082/api/v1/datasources/10/query"
    
    # 测试数据 - 使用一个简单的查询
    test_data = {
        "query": "SELECT * FROM cpc_dw_publication LIMIT 5",
        "limit": 5,
        "timeout": 30
    }
    
    # 请求头
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    
    try:
        print("🚀 开始测试 Doris 查询修复...")
        print(f"📡 请求 URL: {url}")
        print(f"📝 请求数据: {json.dumps(test_data, indent=2, ensure_ascii=False)}")
        
        # 发送请求
        response = requests.post(url, json=test_data, headers=headers, timeout=60)
        
        print(f"📊 响应状态码: {response.status_code}")
        print(f"📄 响应头: {dict(response.headers)}")
        
        # 解析响应
        if response.status_code == 200:
            result = response.json()
            print(f"✅ 响应内容: {json.dumps(result, indent=2, ensure_ascii=False)}")
            
            if result.get('success'):
                print("🎉 查询执行成功！")
                print(f"📊 返回列数: {len(result.get('columns', []))}")
                print(f"📊 返回行数: {result.get('row_count', 0)}")
                print(f"⏱️ 执行时间: {result.get('execution_time', 0)}ms")
                return True
            else:
                print(f"❌ 查询执行失败: {result.get('message', '未知错误')}")
                if result.get('error_details'):
                    print(f"🔍 错误详情: {result.get('error_details')}")
                return False
        else:
            print(f"❌ HTTP 请求失败: {response.status_code}")
            print(f"📄 响应内容: {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ 请求异常: {str(e)}")
        return False
    except json.JSONDecodeError as e:
        print(f"❌ JSON 解析失败: {str(e)}")
        return False
    except Exception as e:
        print(f"❌ 未知错误: {str(e)}")
        return False

def test_simple_query():
    """测试简单查询"""
    
    # API 端点
    url = "http://localhost:8082/api/v1/datasources/10/query"
    
    # 测试数据 - 使用一个更简单的查询
    test_data = {
        "query": "SHOW TABLES",
        "limit": 10,
        "timeout": 30
    }
    
    # 请求头
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    
    try:
        print("\n🔍 测试简单查询 (SHOW TABLES)...")
        print(f"📡 请求 URL: {url}")
        print(f"📝 请求数据: {json.dumps(test_data, indent=2, ensure_ascii=False)}")
        
        # 发送请求
        response = requests.post(url, json=test_data, headers=headers, timeout=60)
        
        print(f"📊 响应状态码: {response.status_code}")
        
        # 解析响应
        if response.status_code == 200:
            result = response.json()
            print(f"✅ 响应内容: {json.dumps(result, indent=2, ensure_ascii=False)}")
            
            if result.get('success'):
                print("🎉 简单查询执行成功！")
                return True
            else:
                print(f"❌ 简单查询执行失败: {result.get('message', '未知错误')}")
                return False
        else:
            print(f"❌ HTTP 请求失败: {response.status_code}")
            print(f"📄 响应内容: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ 简单查询测试失败: {str(e)}")
        return False

if __name__ == "__main__":
    print("🚀 开始测试 Doris 查询修复...")
    
    # 简单查询测试
    simple_test_result = test_simple_query()
    
    # 复杂查询测试
    complex_test_result = test_doris_query_fix()
    
    print("\n📊 测试结果总结:")
    print(f"简单查询测试: {'✅ 通过' if simple_test_result else '❌ 失败'}")
    print(f"复杂查询测试: {'✅ 通过' if complex_test_result else '❌ 失败'}")
    
    if simple_test_result or complex_test_result:
        print("\n🎉 至少有一个测试通过，修复可能有效！")
    else:
        print("\n⚠️  所有测试都失败，需要进一步检查")