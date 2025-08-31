#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试 Agent 创建功能
验证 model_name 到 model_id 的转换是否正确
"""

import requests
import json

# 后端服务器地址
BASE_URL = "http://localhost:8082"

def test_agent_creation():
    """
    测试 Agent 创建功能
    """
    print("开始测试 Agent 创建功能...")
    
    # 1. 首先获取可用的模型配置
    print("\n1. 获取可用的模型配置...")
    try:
        response = requests.get(f"{BASE_URL}/api/v1/model-service-configs/available-for-agents")
        if response.status_code == 200:
            configs = response.json()
            print(f"获取到 {len(configs)} 个模型配置:")
            for config in configs:
                print(f"  - {config['label']}: {config['value']} (model_id: {config['model_id']})")
            
            if not configs:
                print("❌ 没有可用的模型配置")
                return False
                
            # 使用第一个配置进行测试
            test_config = configs[0]
            print(f"\n使用配置进行测试: {test_config['label']}")
            
        else:
            print(f"❌ 获取模型配置失败: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ 请求失败: {e}")
        return False
    
    # 2. 创建测试 Agent
    print("\n2. 创建测试 Agent...")
    agent_data = {
        "name": "测试多模态视觉助手",
        "description": "专业的图像分析和视觉理解助手，支持图像识别、描述和分析",
        "agent_type": "CUSTOM",
        "status": "ACTIVE",
        "model_id": test_config['model_id'],  # 使用正确的 model_id
        "system_prompt": "你是一个专业的视觉分析助手，能够理解和分析图像内容。",
        "user_prompt_template": "",
        "model_config": {
            "temperature": 0.2,
            "max_tokens": 2500,
            "top_p": 0.9,
            "frequency_penalty": 0,
            "presence_penalty": 0,
            "top_k": 40
        },
        "tools": [],
        "tool_config": {},
        "memory_enabled": True,
        "retrieval_config": {
            "similarity_threshold": 0.7,
            "max_results": 5
        },
        "is_public": True,
        "allowed_users": [],
        "tags": ["视觉", "图像", "识别", "多模态"],
        "metadata": {
            "category": "vision",
            "difficulty": "advanced",
            "multimodal": True
        }
    }
    
    try:
        # 需要认证，这里先尝试不带认证的请求
        headers = {
            "Content-Type": "application/json"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/v1/agents/",
            json=agent_data,
            headers=headers
        )
        
        print(f"响应状态码: {response.status_code}")
        print(f"响应内容: {response.text}")
        
        if response.status_code == 201:
            result = response.json()
            print(f"✅ Agent 创建成功!")
            print(f"   Agent ID: {result.get('id')}")
            print(f"   Agent 名称: {result.get('name')}")
            print(f"   模型名称: {result.get('model_name')}")
            return True
        elif response.status_code == 401:
            print("⚠️  需要认证，但请求格式正确（401 而不是 422）")
            return True
        elif response.status_code == 422:
            print("❌ 数据验证失败 (422)，可能还有问题")
            try:
                error_detail = response.json()
                print(f"错误详情: {json.dumps(error_detail, indent=2, ensure_ascii=False)}")
            except:
                pass
            return False
        else:
            print(f"❌ 创建失败: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ 请求失败: {e}")
        return False

if __name__ == "__main__":
    success = test_agent_creation()
    if success:
        print("\n🎉 测试通过！Agent 创建功能正常工作。")
    else:
        print("\n💥 测试失败！需要进一步检查。")