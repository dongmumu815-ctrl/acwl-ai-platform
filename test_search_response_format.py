#!/usr/bin/env python3
"""
测试搜索API的响应格式
验证是否符合标准的 {data, message, success} 格式
"""

import requests
import json

def get_admin_token():
    """获取管理员认证令牌"""# 获取管理员令牌
    login_url = "http://localhost:8082/api/v1/auth/login/json"
    login_data = {
        "email": "admin@acwl.ai",
        "password": "password"
    }
    
    try:
        response = requests.post(login_url, json=login_data)
        if response.status_code == 200:
            data = response.json()
            token = data.get("access_token")
            print(f"✅ 获取认证token成功: {token[:50]}...")
            return token
        else:
            print(f"❌ 获取token失败: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"❌ 获取token异常: {e}")
        return None

def test_search_response_format():
    """测试搜索API的响应格式"""
    # 获取认证token
    token = get_admin_token()
    if not token:
        return
    
    # 搜索API URL
    search_url = "http://localhost:8082/api/v1/resource-packages/search"
    
    # 请求头
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    # 请求数据
    search_data = {
        "page": 1,
        "size": 20,
        "sort_by": "created_at",
        "sort_order": "desc"
    }
    
    print("\n🔍 测试搜索API响应格式...")
    print(f"请求数据: {json.dumps(search_data, indent=2, ensure_ascii=False)}")
    
    try:
        response = requests.post(search_url, json=search_data, headers=headers)
        print(f"\n响应状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ 搜索API请求成功!")
            
            # 验证响应格式
            print("\n📋 响应格式验证:")
            
            # 检查必需字段
            required_fields = ["success", "message", "data"]
            missing_fields = []
            
            for field in required_fields:
                if field in data:
                    print(f"  ✅ {field}: {type(data[field]).__name__}")
                else:
                    missing_fields.append(field)
                    print(f"  ❌ {field}: 缺失")
            
            if missing_fields:
                print(f"\n❌ 响应格式不标准，缺失字段: {missing_fields}")
                return
            
            print(f"\n✅ 响应格式符合标准!")
            print(f"success: {data['success']}")
            print(f"message: {data['message']}")
            
            # 检查data字段内容
            if data.get('data'):
                data_content = data['data']
                print(f"\ndata字段内容:")
                print(f"  - items数量: {len(data_content.get('items', []))}")
                print(f"  - total: {data_content.get('total', 0)}")
                print(f"  - page: {data_content.get('page', 0)}")
                print(f"  - size: {data_content.get('size', 0)}")
                
                # 显示前3个资源包
                items = data_content.get('items', [])
                if items:
                    print(f"\n前{min(3, len(items))}个资源包:")
                    for i, item in enumerate(items[:3], 1):
                        print(f"  {i}. ID: {item.get('id')}, 名称: {item.get('name')}")
                        print(f"     类型: {item.get('type')}, 创建时间: {item.get('created_at')}")
            
            print(f"\n完整响应数据:")
            print(json.dumps(data, indent=2, ensure_ascii=False))
            
        else:
            print(f"❌ 搜索API请求失败: {response.status_code}")
            print(f"错误信息: {response.text}")
            
    except Exception as e:
        print(f"❌ 请求异常: {e}")

if __name__ == "__main__":
    test_search_response_format()