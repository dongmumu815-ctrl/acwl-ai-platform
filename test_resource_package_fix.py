#!/usr/bin/env python3
"""
测试资源包创建API修复
"""
import requests
import json

def test_create_resource_package():
    """测试创建资源包API"""
    url = "http://localhost:8082/api/v1/resource-packages/"
    
    # 测试数据
    data = {
        "name": "testeeee",
        "description": "testttest", 
        "type": "sql",
        "datasource_id": 8,
        "base_config": {
            "schema": "acwl-agents",
            "table": "cpc_agents", 
            "fields": ["name", "description", "parent_id", "id"]
        },
        "dynamic_conditions": [
            {
                "logic": "AND",
                "field": "node_type", 
                "operator": "=",
                "value": "agent",
                "locked": False
            }
        ],
        "is_active": True,
        "limit_config": 1000,
        "locked_conditions": [],
        "tags": ["常用查询"]
    }
    
    # 添加认证头（如果需要）
    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer test-token"  # 根据实际情况调整
    }
    
    try:
        print("正在测试资源包创建API...")
        print(f"URL: {url}")
        print(f"数据: {json.dumps(data, indent=2, ensure_ascii=False)}")
        
        response = requests.post(url, json=data, headers=headers)
        
        print(f"\n响应状态码: {response.status_code}")
        print(f"响应头: {dict(response.headers)}")
        
        if response.status_code == 200:
            print("✅ API调用成功!")
            result = response.json()
            print(f"响应数据: {json.dumps(result, indent=2, ensure_ascii=False)}")
        else:
            print(f"❌ API调用失败!")
            print(f"错误信息: {response.text}")
            
    except Exception as e:
        print(f"❌ 请求异常: {str(e)}")

if __name__ == "__main__":
    test_create_resource_package()