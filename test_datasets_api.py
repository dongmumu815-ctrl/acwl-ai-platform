#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试数据集API接口
"""

import requests
import json
from pathlib import Path

# API基础URL
BASE_URL = "http://127.0.0.1:8000/api/v1"

# 测试用户凭据
TEST_USER = {
    "username": "admin",
    "password": "admin123"
}

def get_auth_token():
    """
    获取认证令牌
    
    Returns:
        str: 访问令牌
    """
    try:
        response = requests.post(
            f"{BASE_URL}/auth/login",
            data=TEST_USER
        )
        
        if response.status_code == 200:
            token_data = response.json()
            return token_data.get("access_token")
        else:
            print(f"登录失败: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"登录请求失败: {str(e)}")
        return None

def test_datasets_api():
    """
    测试数据集API接口
    """
    print("=== 数据集API测试 ===")
    
    # 获取认证令牌
    token = get_auth_token()
    if not token:
        print("无法获取认证令牌，测试终止")
        return
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    # 1. 测试获取数据集统计信息
    print("\n1. 测试获取数据集统计信息")
    try:
        response = requests.get(f"{BASE_URL}/datasets/stats", headers=headers)
        print(f"状态码: {response.status_code}")
        if response.status_code == 200:
            stats = response.json()
            print(f"统计信息: {json.dumps(stats, indent=2, ensure_ascii=False)}")
        else:
            print(f"错误: {response.text}")
    except Exception as e:
        print(f"请求失败: {str(e)}")
    
    # 2. 测试创建数据集
    print("\n2. 测试创建数据集")
    dataset_data = {
        "name": "测试数据集",
        "description": "这是一个测试数据集",
        "dataset_type": "text",
        "format": "json",
        "is_public": False,
        "tags": ["测试", "文本"]
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/datasets/",
            headers=headers,
            json=dataset_data
        )
        print(f"状态码: {response.status_code}")
        if response.status_code == 200:
            dataset = response.json()
            dataset_id = dataset["id"]
            print(f"创建成功，数据集ID: {dataset_id}")
            print(f"数据集信息: {json.dumps(dataset, indent=2, ensure_ascii=False)}")
        else:
            print(f"错误: {response.text}")
            dataset_id = None
    except Exception as e:
        print(f"请求失败: {str(e)}")
        dataset_id = None
    
    # 3. 测试获取数据集列表
    print("\n3. 测试获取数据集列表")
    try:
        response = requests.get(
            f"{BASE_URL}/datasets/",
            headers=headers,
            params={
                "page": 1,
                "size": 10,
                "sort_by": "created_at",
                "sort_order": "desc"
            }
        )
        print(f"状态码: {response.status_code}")
        if response.status_code == 200:
            datasets = response.json()
            print(f"数据集列表: {json.dumps(datasets, indent=2, ensure_ascii=False)}")
        else:
            print(f"错误: {response.text}")
    except Exception as e:
        print(f"请求失败: {str(e)}")
    
    # 4. 测试获取数据集详情
    if dataset_id:
        print(f"\n4. 测试获取数据集详情 (ID: {dataset_id})")
        try:
            response = requests.get(
                f"{BASE_URL}/datasets/{dataset_id}",
                headers=headers
            )
            print(f"状态码: {response.status_code}")
            if response.status_code == 200:
                dataset = response.json()
                print(f"数据集详情: {json.dumps(dataset, indent=2, ensure_ascii=False)}")
            else:
                print(f"错误: {response.text}")
        except Exception as e:
            print(f"请求失败: {str(e)}")
    
    # 5. 测试更新数据集
    if dataset_id:
        print(f"\n5. 测试更新数据集 (ID: {dataset_id})")
        update_data = {
            "description": "更新后的数据集描述",
            "tags": ["测试", "文本", "更新"]
        }
        
        try:
            response = requests.put(
                f"{BASE_URL}/datasets/{dataset_id}",
                headers=headers,
                json=update_data
            )
            print(f"状态码: {response.status_code}")
            if response.status_code == 200:
                dataset = response.json()
                print(f"更新成功: {json.dumps(dataset, indent=2, ensure_ascii=False)}")
            else:
                print(f"错误: {response.text}")
        except Exception as e:
            print(f"请求失败: {str(e)}")
    
    # 6. 测试搜索数据集
    print("\n6. 测试搜索数据集")
    try:
        response = requests.get(
            f"{BASE_URL}/datasets/",
            headers=headers,
            params={
                "search": "测试",
                "dataset_type": "text",
                "page": 1,
                "size": 5
            }
        )
        print(f"状态码: {response.status_code}")
        if response.status_code == 200:
            datasets = response.json()
            print(f"搜索结果: {json.dumps(datasets, indent=2, ensure_ascii=False)}")
        else:
            print(f"错误: {response.text}")
    except Exception as e:
        print(f"请求失败: {str(e)}")
    
    # 7. 测试删除数据集
    if dataset_id:
        print(f"\n7. 测试删除数据集 (ID: {dataset_id})")
        try:
            response = requests.delete(
                f"{BASE_URL}/datasets/{dataset_id}",
                headers=headers
            )
            print(f"状态码: {response.status_code}")
            if response.status_code == 200:
                result = response.json()
                print(f"删除成功: {json.dumps(result, indent=2, ensure_ascii=False)}")
            else:
                print(f"错误: {response.text}")
        except Exception as e:
            print(f"请求失败: {str(e)}")

def test_health_check():
    """
    测试健康检查
    """
    print("=== 健康检查测试 ===")
    
    try:
        response = requests.get(f"{BASE_URL}/health/")
        print(f"状态码: {response.status_code}")
        if response.status_code == 200:
            health = response.json()
            print(f"健康状态: {json.dumps(health, indent=2, ensure_ascii=False)}")
        else:
            print(f"错误: {response.text}")
    except Exception as e:
        print(f"请求失败: {str(e)}")

if __name__ == "__main__":
    # 先测试健康检查
    test_health_check()
    
    # 再测试数据集API
    test_datasets_api()
    
    print("\n=== 测试完成 ===")