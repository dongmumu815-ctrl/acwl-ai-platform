#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试Review Agent是否正确使用温度等配置参数
"""

import asyncio
import sys
import os

# 添加backend目录到Python路径
backend_path = os.path.join(os.path.dirname(__file__), 'backend')
sys.path.insert(0, backend_path)

# 设置环境变量
os.environ.setdefault('PYTHONPATH', backend_path)

try:
    from app.core.database import get_db
    from app.services.review_content_safety_agent_db import EnhancedContentSafetyAgentDB
except ImportError as e:
    print(f"导入错误: {e}")
    print("请确保在项目根目录下运行此脚本")
    sys.exit(1)

async def test_temperature_config():
    """
    测试温度等配置参数是否正确传递和使用
    """
    print("开始测试Review Agent温度配置参数...")
    
    # 模拟从agents.py传递的llm_config
    llm_config = {
        "type": "ollama",
        "model": "qwen2.5:7b",
        "base_url": "http://localhost:11434",
        "api_key": None,
        "temperature": 1.30,  # Agent 32的实际配置
        "top_p": 0.90,
        "max_tokens": 4098,
        "frequency_penalty": 0.0,
        "presence_penalty": 0.0,
        "timeout": 30
    }
    
    try:
        # 创建Agent实例
        print("创建EnhancedContentSafetyAgentDB实例...")
        agent = EnhancedContentSafetyAgentDB(
            llm_config=llm_config,
            instruction_set_id=13
        )
        print("Agent实例创建成功")
        
        # 检查LLM客户端是否正确初始化
        if agent.llm_client:
            print("\n=== LLM客户端配置检查 ===")
            print(f"模型: {agent.llm_client.model}")
            print(f"API URL: {agent.llm_client.api_url}")
            print(f"温度: {agent.llm_client.temperature}")
            print(f"Top-p: {agent.llm_client.top_p}")
            print(f"最大tokens: {agent.llm_client.max_tokens}")
            print(f"频率惩罚: {agent.llm_client.frequency_penalty}")
            print(f"存在惩罚: {agent.llm_client.presence_penalty}")
            print(f"超时时间: {agent.llm_client.timeout}")
            
            # 验证配置是否正确
            assert agent.llm_client.temperature == 1.30, f"温度配置错误: 期望1.30, 实际{agent.llm_client.temperature}"
            assert agent.llm_client.top_p == 0.90, f"Top-p配置错误: 期望0.90, 实际{agent.llm_client.top_p}"
            assert agent.llm_client.max_tokens == 4098, f"Max tokens配置错误: 期望4098, 实际{agent.llm_client.max_tokens}"
            
            print("\n✅ 所有配置参数验证通过！")
        else:
            print("❌ LLM客户端未正确初始化")
            return False
            
        # 获取数据库会话并初始化Agent
        async for db in get_db():
            print("\n初始化Agent数据库连接...")
            await agent.initialize(db)
            print("Agent初始化成功")
            break
            
        print("\n=== 测试完成 ===")
        print("Review Agent现在会在调用Ollama时使用以下配置:")
        print(f"- 温度: {agent.llm_client.temperature}")
        print(f"- Top-p: {agent.llm_client.top_p}")
        print(f"- 最大tokens: {agent.llm_client.max_tokens}")
        print(f"- 频率惩罚: {agent.llm_client.frequency_penalty}")
        print(f"- 存在惩罚: {agent.llm_client.presence_penalty}")
        
        return True
            
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    # 运行测试
    success = asyncio.run(test_temperature_config())
    if success:
        print("\n🎉 测试成功！Review Agent现在正确使用温度等配置参数。")
    else:
        print("\n💥 测试失败，请检查代码修改。")
        sys.exit(1)