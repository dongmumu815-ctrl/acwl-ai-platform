#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试节点编号生成功能

这个脚本用于测试review_content_safety_agent_db.py中的节点编号生成机制
是否按照instruction_sets.py的方式正确工作。
"""

import sys
import os
import requests
import json

def test_agent_chat():
    """
    通过API测试代理聊天功能，观察节点编号输出
    """
    print("开始测试节点编号生成功能...")
    
    # API配置
    base_url = "http://localhost:8082"
    agent_id = 32  # 使用已知的代理ID
    
    # 测试消息
    test_message = "这是一个测试消息，用于检查节点编号是否正确生成。"
    
    try:
        # 发送聊天请求
        chat_url = f"{base_url}/api/v1/agents/{agent_id}/chat"
        payload = {
            "message": test_message,
            "conversation_id": "test_node_numbering"
        }
        
        print(f"发送请求到: {chat_url}")
        print(f"消息内容: {test_message}")
        
        response = requests.post(
            chat_url,
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        print(f"\n响应状态码: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("\n聊天响应:")
            print(json.dumps(result, indent=2, ensure_ascii=False))
            print("\n测试完成！请检查后端日志中的节点编号输出。")
        else:
            print(f"请求失败: {response.status_code}")
            print(f"错误信息: {response.text}")
            
    except requests.exceptions.RequestException as e:
        print(f"请求异常: {str(e)}")
    except Exception as e:
        print(f"测试失败: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_agent_chat()