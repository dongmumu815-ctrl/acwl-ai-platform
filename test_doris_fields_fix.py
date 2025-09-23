#!/usr/bin/env python3
"""
测试Doris字段获取接口修复
"""

import requests
import json
import sys

def test_doris_fields_api():
    """
    测试Doris数据源字段获取接口
    """
    # API基础URL
    base_url = "http://localhost:8082/api/v1"
    
    # 测试参数 - 根据你提供的URL
    datasource_id = 10
    schema_name = "cepiec-warehouse"
    table_name = "cpc_dw_publication"
    
    # 构建请求URL
    url = f"{base_url}/datasources/{datasource_id}/schemas/{schema_name}/tables/{table_name}/fields/"
    
    print(f"🔍 测试URL: {url}")
    print("=" * 80)
    
    try:
        # 发送GET请求
        response = requests.get(url, timeout=30)
        
        print(f"📊 响应状态码: {response.status_code}")
        print(f"📋 响应头: {dict(response.headers)}")
        print("=" * 80)
        
        if response.status_code == 200:
            # 解析JSON响应
            data = response.json()
            print(f"✅ 请求成功!")
            print(f"📄 响应数据:")
            print(json.dumps(data, indent=2, ensure_ascii=False))
            
            # 检查数据结构
            if data.get("success"):
                fields = data.get("data", [])
                print(f"\n📈 字段统计:")
                print(f"   - 字段总数: {len(fields)}")
                
                if fields:
                    print(f"   - 示例字段:")
                    for i, field in enumerate(fields[:3]):  # 显示前3个字段
                        print(f"     {i+1}. {field.get('name', 'N/A')} ({field.get('type', 'N/A')})")
                        if field.get('comment'):
                            print(f"        注释: {field.get('comment')}")
                    
                    if len(fields) > 3:
                        print(f"     ... 还有 {len(fields) - 3} 个字段")
                else:
                    print("   ⚠️  字段列表为空 - 这可能表示:")
                    print("      1. 表不存在")
                    print("      2. 数据源连接问题")
                    print("      3. 权限不足")
                    print("      4. Schema或表名错误")
            else:
                print(f"❌ API返回失败: {data.get('message', '未知错误')}")
                
        elif response.status_code == 404:
            print("❌ 资源未找到 (404)")
            print("   可能原因:")
            print("   - 数据源ID不存在")
            print("   - Schema名称错误")
            print("   - 表名称错误")
            
        elif response.status_code == 401:
            print("❌ 认证失败 (401)")
            print("   需要登录或提供有效的认证信息")
            
        elif response.status_code == 500:
            print("❌ 服务器内部错误 (500)")
            try:
                error_data = response.json()
                print(f"   错误详情: {error_data}")
            except:
                print(f"   错误详情: {response.text}")
                
        else:
            print(f"❌ 未预期的状态码: {response.status_code}")
            print(f"   响应内容: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ 连接错误: 无法连接到后端服务")
        print("   请确保后端服务正在运行在 http://localhost:8082")
        
    except requests.exceptions.Timeout:
        print("❌ 请求超时")
        print("   数据源连接可能较慢或存在网络问题")
        
    except Exception as e:
        print(f"❌ 测试过程中发生错误: {str(e)}")
        
    print("=" * 80)

def test_datasource_info():
    """
    测试获取数据源信息
    """
    base_url = "http://localhost:8082/api/v1"
    datasource_id = 10
    
    url = f"{base_url}/datasources/{datasource_id}"
    
    print(f"🔍 获取数据源信息: {url}")
    
    try:
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if data.get("success"):
                datasource = data.get("data", {})
                print(f"✅ 数据源信息:")
                print(f"   - 名称: {datasource.get('name', 'N/A')}")
                print(f"   - 类型: {datasource.get('datasource_type', 'N/A')}")
                print(f"   - 主机: {datasource.get('host', 'N/A')}")
                print(f"   - 端口: {datasource.get('port', 'N/A')}")
                print(f"   - 状态: {datasource.get('status', 'N/A')}")
            else:
                print(f"❌ 获取数据源信息失败: {data.get('message', '未知错误')}")
        else:
            print(f"❌ 请求失败: {response.status_code}")
            
    except Exception as e:
        print(f"❌ 获取数据源信息时发生错误: {str(e)}")
        
    print("=" * 80)

if __name__ == "__main__":
    print("🚀 开始测试Doris字段获取接口修复")
    print("=" * 80)
    
    # 首先获取数据源信息
    test_datasource_info()
    
    # 然后测试字段获取接口
    test_doris_fields_api()
    
    print("🏁 测试完成")