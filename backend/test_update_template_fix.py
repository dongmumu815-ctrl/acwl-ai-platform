#!/usr/bin/env python3
"""
测试ES查询模板更新时所有字段是否正确保存
"""

import requests
import json

# 配置
BASE_URL = "http://localhost:3005"
ACCESS_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI1IiwiZXhwIjoxNzU4NzE5Nzg4fQ.WXE2vvwS-UJXe66OghF2tXBWBY2UDofI4r2IcXJs4Dc"

def create_test_template():
    """创建一个测试模板"""
    template_data = {
        "name": "测试模板_更新前",
        "description": "更新前的描述",
        "datasourceId": 9,
        "dataResourceId": 24,
        "indices": [],
        "query": {
            "query": {"match_all": {}},
            "_source": ["isbn_10"],
            "from": 0,
            "size": 10
        },
        "tags": []
    }
    
    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }
    
    print("创建测试模板...")
    response = requests.post(
        f"{BASE_URL}/api/v1/es/templates",
        headers=headers,
        json=template_data
    )
    
    if response.status_code == 200:
        result = response.json()
        template_id = result.get("data", {}).get("id")
        print(f"✅ 测试模板创建成功，ID: {template_id}")
        return template_id
    else:
        print(f"❌ 创建测试模板失败: {response.text}")
        return None

def update_template(template_id):
    """更新模板"""
    update_data = {
        "name": "测试模板_更新后",
        "description": "更新后的描述",
        "datasourceId": 9,
        "dataResourceId": 25,  # 修改dataResourceId
        "indices": ["new_index"],
        "query": {
            "query": {"match_all": {}},
            "_source": ["isbn_10", "isbn_13"],
            "from": 0,
            "size": 20
        },
        "tags": ["updated"]
    }
    
    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }
    
    print(f"更新模板 {template_id}...")
    print(f"更新数据: {json.dumps(update_data, indent=2, ensure_ascii=False)}")
    
    response = requests.put(
        f"{BASE_URL}/api/v1/es/templates/{template_id}",
        headers=headers,
        json=update_data
    )
    
    print(f"响应状态码: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print(f"更新响应: {json.dumps(result, indent=2, ensure_ascii=False)}")
        
        # 检查返回数据中的字段
        data = result.get("data", {})
        name = data.get("name")
        description = data.get("description")
        data_resource_id = data.get("dataResourceId")
        
        print(f"\n=== 更新结果检查 ===")
        print(f"模板名称: {name} (期望: 测试模板_更新后)")
        print(f"模板描述: {description} (期望: 更新后的描述)")
        print(f"数据资源ID: {data_resource_id} (期望: 25)")
        
        success = True
        if name != "测试模板_更新后":
            print("❌ 模板名称更新失败")
            success = False
        if description != "更新后的描述":
            print("❌ 模板描述更新失败")
            success = False
        if data_resource_id != 25:
            print("❌ 数据资源ID更新失败")
            success = False
            
        if success:
            print("✅ 所有字段更新成功")
        
        return success
    else:
        print(f"❌ 更新失败: {response.text}")
        return False

def verify_template_update(template_id):
    """通过查询API验证模板更新"""
    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }
    
    print(f"\n验证模板 {template_id} 的更新...")
    response = requests.get(
        f"{BASE_URL}/api/v1/es/templates/{template_id}",
        headers=headers
    )
    
    if response.status_code == 200:
        result = response.json()
        data = result.get("data", {})
        
        print(f"查询结果: {json.dumps(data, indent=2, ensure_ascii=False)}")
        
        name = data.get("name")
        description = data.get("description")
        data_resource_id = data.get("dataResourceId")
        
        print(f"\n=== 查询验证结果 ===")
        print(f"模板名称: {name}")
        print(f"模板描述: {description}")
        print(f"数据资源ID: {data_resource_id}")
        
        if (name == "测试模板_更新后" and 
            description == "更新后的描述" and 
            data_resource_id == 25):
            print("✅ 查询验证：所有字段都已正确更新")
            return True
        else:
            print("❌ 查询验证：字段更新不完整")
            return False
    else:
        print(f"❌ 查询验证失败: {response.text}")
        return False

if __name__ == "__main__":
    print("=== 测试ES查询模板更新功能 ===")
    
    # 创建测试模板
    template_id = create_test_template()
    if not template_id:
        print("测试失败：无法创建测试模板")
        exit(1)
    
    # 更新模板
    update_success = update_template(template_id)
    
    # 验证更新
    verify_success = verify_template_update(template_id)
    
    if update_success and verify_success:
        print(f"\n🎉 测试成功：模板 {template_id} 的所有字段都已正确更新")
    else:
        print(f"\n❌ 测试失败：模板 {template_id} 更新存在问题")