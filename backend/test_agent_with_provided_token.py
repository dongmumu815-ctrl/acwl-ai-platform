#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
使用提供的token测试Agent ID 32的审读功能
"""

import requests
import json

def test_agent_chat_with_token():
    """
    使用提供的token测试Agent聊天功能
    """
    print("🚀 开始测试Agent ID 32的审读功能...")
    
    # API配置
    base_url = "http://localhost:3000"
    agent_id = 32
    
    # 使用提供的token
    access_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI1IiwiZXhwIjoxNzU2NDY3Njg1fQ.YZ3NXWvAzklHCsnK0xaPZy_FY4mg0H-mjW1ILAyzoCU"
    
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    # 测试用例
    test_cases = [
        {
            "name": "正常文本测试",
            "message": "这是一个正常的测试消息，用于验证审读功能。"
        },
        {
            "name": "包含敏感词测试",
            "message": "这个消息包含一些可能的敏感内容，需要进行审读检测。"
        },
        {
            "name": "长文本测试",
            "message": "这是一个比较长的测试文本，" * 50 + "用于测试长文本的审读处理。"
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{'='*60}")
        print(f"📝 测试用例 {i}: {test_case['name']}")
        print(f"📝 消息内容: {test_case['message'][:100]}{'...' if len(test_case['message']) > 100 else ''}")
        print(f"📝 消息长度: {len(test_case['message'])} 字符")
        
        # 构建请求数据
        chat_data = {
            "message": test_case['message'],
            "conversation_id": f"test_conv_{i}"
        }
        
        try:
            # 发送聊天请求
            print(f"\n🔄 发送聊天请求...")
            response = requests.post(
                f"{base_url}/api/v1/agents/{agent_id}/chat",
                headers=headers,
                json=chat_data,
                timeout=30
            )
            
            print(f"📊 响应状态码: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ 聊天成功!")
                
                # 打印完整响应内容用于调试
                print(f"\n🔍 完整响应内容:")
                print(json.dumps(result, ensure_ascii=False, indent=2))
                
                print(f"\n📋 审读结果:")
                print(f"   消息: {result.get('message', '')}")
                print(f"   令牌使用: {result.get('tokens_used', 0)}")
                print(f"   执行时间: {result.get('execution_time_ms', 0)}ms")
                
                # 检查元数据中的执行路径
                metadata = result.get('metadata', {})
                if metadata:
                    print(f"\n🔍 元数据分析:")
                    print(f"   审读类型: {metadata.get('review_type', 'unknown')}")
                    
                    # 检查执行路径
                    execution_path = metadata.get('execution_path', [])
                    if execution_path:
                        print(f"\n🌳 执行路径分析:")
                        for j, path_item in enumerate(execution_path):
                            if isinstance(path_item, dict):
                                print(f"     {j+1}. 节点ID: {path_item.get('node_id')}, 标题: {path_item.get('node_title')}, 类型: {path_item.get('node_type')}")
                            else:
                                print(f"     {j+1}. 节点ID: {path_item}")
                        
                        # 判断是否按节点树执行
                        has_node_tree_execution = any(
                            isinstance(item, dict) and 'node_title' in item 
                            for item in execution_path
                        )
                        
                        if has_node_tree_execution:
                            print(f"   ✅ 检测到节点树执行路径")
                        else:
                            print(f"   ⚠️ 未检测到节点树执行路径，可能使用的是数据库审读模式")
                    else:
                        print(f"   ⚠️ 执行路径为空")
                    
                    # 检查LLM分析结果
                    llm_analysis = metadata.get('llm_analysis')
                    if llm_analysis:
                        print(f"\n🤖 LLM分析结果:")
                        print(f"   {llm_analysis}")
                        print(f"   LLM令牌使用: {metadata.get('llm_tokens_used', 0)}")
                    
                    # 检查审读结果详情
                    review_result = metadata.get('review_result')
                    if review_result:
                        print(f"\n📊 审读结果详情:")
                        print(f"   节点ID: {review_result.get('node_id')}")
                        print(f"   描述: {review_result.get('description')}")
                        print(f"   匹配: {review_result.get('matched')}")
                        print(f"   风险等级: {review_result.get('risk_level')}")
                        print(f"   置信度: {review_result.get('confidence')}")
                        print(f"   证据: {review_result.get('evidence')}")
                else:
                    print(f"\n⚠️ 响应中没有元数据信息")
                        
            else:
                print(f"❌ 聊天失败: {response.text}")
                
        except requests.exceptions.Timeout:
            print(f"⏰ 请求超时")
        except requests.exceptions.RequestException as e:
            print(f"❌ 请求异常: {str(e)}")
        except Exception as e:
            print(f"❌ 未知错误: {str(e)}")
    
    print(f"\n{'='*60}")
    print(f"🎯 测试完成!")

if __name__ == "__main__":
    test_agent_chat_with_token()