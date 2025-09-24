#!/usr/bin/env python3
"""
测试ES查询模板保存时data_resource_id字段是否正确返回
"""

import requests
import json

# 配置
BASE_URL = "http://localhost:3005"
ACCESS_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI1IiwiZXhwIjoxNzU4NzE5Nzg4fQ.WXE2vvwS-UJXe66OghF2tXBWBY2UDofI4r2IcXJs4Dc"

def test_save_template_with_data_resource_id():
    """测试保存模板时data_resource_id字段是否正确返回"""
    
    # 准备测试数据
    template_data = {
        "name": "测试模板_data_resource_id",
        "description": "测试data_resource_id字段保存和返回",
        "datasourceId": 9,
        "dataResourceId": 24,  # 使用驼峰命名
        "indices": [],
        "query": {
            "query": {"match_all": {}},
            "_source": ["isbn_10", "isbn_13"],
            "from": 0,
            "size": 20
        },
        "tags": []
    }
    
    # 发送保存请求
    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }
    
    print("发送保存模板请求...")
    print(f"请求数据: {json.dumps(template_data, indent=2, ensure_ascii=False)}")
    
    response = requests.post(
        f"{BASE_URL}/api/v1/es/templates",
        headers=headers,
        json=template_data
    )
    
    print(f"响应状态码: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print(f"保存响应: {json.dumps(result, indent=2, ensure_ascii=False)}")
        
        # 检查返回数据中是否包含dataResourceId字段
        data = result.get("data", {})
        data_resource_id = data.get("dataResourceId")
        
        if data_resource_id is not None:
            print(f"✅ 成功: dataResourceId字段已正确返回，值为: {data_resource_id}")
            return data.get("id")
        else:
            print("❌ 失败: 返回数据中缺少dataResourceId字段")
            return None
    else:
        print(f"❌ 保存失败: {response.text}")
        return None

if __name__ == "__main__":
    print("=== 测试ES查询模板保存时data_resource_id字段返回 ===")
    template_id = test_save_template_with_data_resource_id()
    
    if template_id:
        print(f"\n模板ID {template_id} 保存成功，dataResourceId字段已正确返回")
    else:
        print("\n测试失败")