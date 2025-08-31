#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试模型服务配置功能的脚本
"""

import requests
import json
from datetime import datetime

# 后端API基础URL
BASE_URL = "http://localhost:8082/api/v1"

def get_auth_token():
    """获取管理员认证token"""
    login_data = {
        "email": "admin@acwl.ai",
        "password": "password"
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/auth/login/json",
            json=login_data,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            data = response.json()
            token = data.get("access_token")
            print(f"✅ 获取认证token成功: {token[:30]}...")
            return token
        else:
            print(f"❌ 登录失败: {response.text}")
            return None
    except Exception as e:
        print(f"❌ 登录异常: {e}")
        return None

def get_auth_headers():
    """获取认证头"""
    token = get_auth_token()
    if token:
        return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    return None

def test_providers_api():
    """测试获取支持的服务提供商列表"""
    headers = get_auth_headers()
    if not headers:
        return None
        
    try:
        # 使用完整的API路径
        response = requests.get(f"{BASE_URL}/model-service-configs/providers", headers=headers)
        print(f"获取服务提供商列表: {response.status_code}")
        if response.status_code == 200:
            providers = response.json()
            print(f"支持的服务提供商: {providers}")
            return providers
        else:
            print(f"错误响应: {response.text}")
            # 尝试直接访问providers端点
            try:
                alt_response = requests.get(f"{BASE_URL}/model-service-configs/providers", headers=headers)
                print(f"备用路径状态: {alt_response.status_code}")
                print(f"备用路径响应: {alt_response.text[:200]}...")
            except Exception as e:
                print(f"备用路径错误: {e}")
            return None
    except Exception as e:
        print(f"请求失败: {e}")
        return None

def create_test_config():
    """创建测试配置"""
    headers = get_auth_headers()
    if not headers:
        return None
        
    # 使用时间戳确保名称唯一
    import time
    timestamp = int(time.time())
    
    test_config = {
        "name": f"test-openai-gpt4-{timestamp}",
        "display_name": "测试 OpenAI GPT-4",
        "provider": "openai",
        "model_name": "gpt-4",
        "api_endpoint": "https://api.openai.com/v1/chat/completions",
        "api_key": "sk-test-key-placeholder",
        "max_tokens": 4096,
        "temperature": 0.7,
        "timeout": 30,
        "is_active": True,
        "is_default": False,
        "description": "测试用的OpenAI GPT-4配置",
        "request_headers": {
            "Content-Type": "application/json"
        },
        "extra_params": {
            "top_p": 1.0,
            "frequency_penalty": 0.0,
            "presence_penalty": 0.0
        }
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/model-service-configs",
            json=test_config,
            headers=headers
        )
        print(f"创建测试配置: {response.status_code}")
        if response.status_code == 201:
            config = response.json()
            print(f"创建成功，配置ID: {config.get('id')}")
            return config
        else:
            print(f"创建失败: {response.text}")
            return None
    except Exception as e:
        print(f"创建配置失败: {e}")
        return None

def get_all_configs():
    """获取所有配置"""
    headers = get_auth_headers()
    if not headers:
        return []
        
    try:
        response = requests.get(f"{BASE_URL}/model-service-configs", headers=headers)
        print(f"获取所有配置: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            configs = data.get('items', [])
            print(f"配置数量: {len(configs)}")
            for config in configs:
                print(f"  - {config['name']} ({config['provider']}/{config['model_name']})")
            return configs
        else:
            print(f"获取失败: {response.text}")
            return []
    except Exception as e:
        print(f"获取配置失败: {e}")
        return []

def get_agent_configs():
    """获取Agent可用的配置"""
    headers = get_auth_headers()
    if not headers:
        return []
        
    try:
        response = requests.get(f"{BASE_URL}/model-service-configs/available-for-agents", headers=headers)
        print(f"获取Agent配置: {response.status_code}")
        if response.status_code == 200:
            configs = response.json()
            print(f"Agent可用配置数量: {len(configs)}")
            if configs:
                print(f"第一个配置示例: {configs[0]}")
            else:
                print("暂无可用配置")
            return configs
        else:
            print(f"获取失败: {response.text}")
            return []
    except Exception as e:
        print(f"获取Agent配置失败: {e}")
        return []

def test_config_connection(config_id):
    """测试配置连接"""
    headers = get_auth_headers()
    if not headers:
        return None
        
    try:
        response = requests.post(f"{BASE_URL}/model-service-configs/{config_id}/test", headers=headers)
        print(f"测试配置连接: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"测试结果: {result}")
            return result
        else:
            print(f"测试失败: {response.text}")
            return None
    except Exception as e:
        print(f"测试连接失败: {e}")
        return None

def main():
    """主测试函数"""
    print("=== 模型服务配置功能测试 ===")
    print(f"测试时间: {datetime.now()}")
    print()
    
    # 1. 测试获取服务提供商
    print("1. 测试获取服务提供商列表")
    providers = test_providers_api()
    print()
    
    # 2. 创建测试配置
    print("2. 创建测试配置")
    test_config = create_test_config()
    print()
    
    # 3. 获取所有配置
    print("3. 获取所有配置")
    all_configs = get_all_configs()
    print()
    
    # 4. 获取Agent配置
    print("4. 获取Agent可用配置")
    agent_configs = get_agent_configs()
    print()
    
    # 5. 测试配置连接（如果有配置的话）
    if test_config and test_config.get('id'):
        print("5. 测试配置连接")
        test_result = test_config_connection(test_config['id'])
        print()
    
    print("=== 测试完成 ===")

if __name__ == "__main__":
    main()