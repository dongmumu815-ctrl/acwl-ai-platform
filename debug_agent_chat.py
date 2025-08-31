#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
调试 Agent 聊天 API 中的 "'int' object has no attribute 'get'" 错误
"""

import sys
import os
import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

# 添加后端路径到 sys.path
backend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), 'backend'))
sys.path.insert(0, backend_path)

# 切换到后端目录
os.chdir(backend_path)

from app.core.database import AsyncSessionLocal
from app.models import Agent, ModelServiceConfig
from app.services.ai_model_service import AIModelService
from app.schemas.agent import AgentChatResponse

async def debug_agent_chat():
    """
    调试 Agent 聊天过程中可能出现的错误
    """
    print("开始调试 Agent 聊天...")
    
    # 创建数据库会话
    async with AsyncSessionLocal() as db:
        try:
            # 查询 Agent ID 为 32 的配置
            agent_query = select(Agent).where(Agent.id == 32)
            agent_result = await db.execute(agent_query)
            agent = agent_result.scalar_one_or_none()
            
            if not agent:
                print("未找到 Agent ID 32")
                return
                
            print(f"找到 Agent: {agent.name}")
            print(f"Agent 类型: {agent.agent_type}")
            print(f"模型服务配置 ID: {agent.model_service_config_id}")
            
            # 获取模型服务配置
            config_query = select(ModelServiceConfig).where(ModelServiceConfig.id == agent.model_service_config_id)
            config_result = await db.execute(config_query)
            config = config_result.scalar_one_or_none()
            
            if not config:
                print("未找到模型服务配置")
                return
                
            print(f"模型服务配置: {config.name}")
            print(f"提供商: {config.provider}")
            print(f"模型名称: {config.model_name}")
            
            # 调用 AI 模型服务
            print("\n调用 AI 模型服务...")
            result = await AIModelService.chat_with_model(
                config=config,
                system_prompt=agent.system_prompt or "",
                user_message="你好",
                context="",
                images=[]
            )
            
            print(f"AI 模型服务返回结果类型: {type(result)}")
            print(f"AI 模型服务返回结果: {result}")
            
            # 检查 result 是否有 get 方法
            if hasattr(result, 'get'):
                print("result 有 get 方法")
            else:
                print("result 没有 get 方法！这就是问题所在！")
                print(f"result 的类型: {type(result)}")
                print(f"result 的值: {result}")
                return
            
            # 模拟 agents.py 中的代码逻辑
            print("\n模拟 agents.py 中的返回逻辑...")
            
            # 检查 success 字段
            success = result.get("success", False)
            print(f"success: {success}")
            
            if not success:
                print(f"AI模型调用失败: {result.get('error', '未知错误')}")
                return
            
            # 模拟创建 AgentChatResponse
            session_id = "test_session"
            agent_id = 32
            
            try:
                response = AgentChatResponse(
                    session_id=session_id,
                    message=result.get("message", ""),
                    tokens_used=result.get("tokens_used", 0),
                    processing_time=result.get("processing_time", 0),
                    metadata={
                        "agent_id": agent_id,
                        "model": config.name,
                        "provider": config.provider,
                        "model_name": config.model_name,
                        "memory_enabled": agent.memory_enabled,
                        **result.get("metadata", {})
                    }
                )
                print("成功创建 AgentChatResponse")
                print(f"响应消息: {response.message}")
                
            except Exception as e:
                print(f"创建 AgentChatResponse 时出错: {str(e)}")
                print(f"错误类型: {type(e)}")
                
        except Exception as e:
            print(f"调试过程中出错: {str(e)}")
            print(f"错误类型: {type(e)}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(debug_agent_chat())