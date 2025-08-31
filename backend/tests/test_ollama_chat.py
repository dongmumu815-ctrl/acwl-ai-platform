#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Ollama聊天测试
测试与Ollama API的连接并让AI讲个笑话
"""

import requests
import json

def test_ollama_chat():
    """
    测试Ollama聊天功能
    连接到指定的Ollama服务器，使用qwen2.5:14b模型让AI讲个笑话
    """
    # Ollama API配置
    ollama_url = "http://cepiec-ai.acoming.net:11868"
    model_name = "qwen2.5:14b"
    
    # 构建请求数据
    chat_data = {
        "model": model_name,
        "messages": [
            {
                "role": "user",
                "content": "请给我讲一个有趣的笑话"
            }
        ],
        "stream": False
    }
    
    try:
        print(f"正在连接到Ollama服务器: {ollama_url}")
        print(f"使用模型: {model_name}")
        print("正在请求AI讲笑话...\n")
        
        # 发送POST请求到Ollama API
        response = requests.post(
            f"{ollama_url}/api/chat",
            json=chat_data,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        # 检查响应状态
        if response.status_code == 200:
            result = response.json()
            
            # 提取AI的回复
            if "message" in result and "content" in result["message"]:
                joke = result["message"]["content"]
                print("=" * 50)
                print("AI讲的笑话:")
                print("=" * 50)
                print(joke)
                print("=" * 50)
                return True
            else:
                print("错误: 响应格式不正确")
                print(f"响应内容: {result}")
                return False
        else:
            print(f"请求失败，状态码: {response.status_code}")
            print(f"错误信息: {response.text}")
            return False
            
    except requests.exceptions.Timeout:
        print("错误: 请求超时，请检查网络连接或服务器状态")
        return False
    except requests.exceptions.ConnectionError:
        print("错误: 无法连接到Ollama服务器，请检查服务器地址和端口")
        return False
    except Exception as e:
        print(f"发生未知错误: {str(e)}")
        return False

def test_ollama_models():
    """
    测试获取Ollama可用模型列表
    """
    ollama_url = "http://cepiec-ai.acoming.net:11868"
    
    try:
        print("\n正在获取可用模型列表...")
        response = requests.get(f"{ollama_url}/api/tags", timeout=10)
        
        if response.status_code == 200:
            models = response.json()
            print("\n可用模型:")
            print("-" * 30)
            if "models" in models:
                for model in models["models"]:
                    print(f"- {model.get('name', 'Unknown')}")
            else:
                print("未找到模型信息")
        else:
            print(f"获取模型列表失败，状态码: {response.status_code}")
            
    except Exception as e:
        print(f"获取模型列表时发生错误: {str(e)}")

if __name__ == "__main__":
    print("Ollama聊天测试开始")
    print("=" * 60)
    
    # 首先测试获取模型列表
    test_ollama_models()
    
    # 然后测试聊天功能
    success = test_ollama_chat()
    
    print("\n" + "=" * 60)
    if success:
        print("测试完成！AI成功讲了个笑话 😄")
    else:
        print("测试失败，请检查配置和网络连接 😞")