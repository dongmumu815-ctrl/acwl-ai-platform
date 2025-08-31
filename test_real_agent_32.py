#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试真实的Agent ID 32聊天API
用于重现'int' object has no attribute 'get'错误
"""

import asyncio
import sys
import os
from datetime import datetime

# 添加backend目录到Python路径
backend_path = os.path.join(os.path.dirname(__file__), 'backend')
sys.path.insert(0, backend_path)
os.chdir(backend_path)  # 切换到backend目录

from app.core.database import get_db
from app.models import Agent, User
from app.schemas.agent import AgentChatRequest
from app.api.v1.endpoints.agents import chat_with_agent
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

async def test_real_agent_chat():
    """
    测试真实的Agent ID 32聊天功能
    """
    print("=== 测试真实Agent ID 32聊天API ===")
    
    # 获取数据库会话
    async for db in get_db():
        try:
            # 查找Agent ID 32
            agent_query = select(Agent).where(Agent.id == 32)
            agent_result = await db.execute(agent_query)
            agent = agent_result.scalar_one_or_none()
            
            if not agent:
                print("❌ Agent ID 32 不存在")
                return
            
            print(f"✅ 找到Agent: {agent.name} (类型: {agent.agent_type})")
            
            # 查找管理员用户
            user_query = select(User).where(User.username == "admin")
            user_result = await db.execute(user_query)
            user = user_result.scalar_one_or_none()
            
            if not user:
                print("❌ 管理员用户不存在")
                return
            
            print(f"✅ 找到用户: {user.username}")
            
            # 创建聊天请求
            chat_request = AgentChatRequest(
                message="你好，这是一条测试消息",
                session_id=None,
                images=None
            )
            
            print(f"\n📤 发送聊天请求: {chat_request.message}")
            
            # 调用真实的聊天API
            try:
                response = await chat_with_agent(
                    agent_id=32,
                    chat_request=chat_request,
                    db=db,
                    current_user=user
                )
                
                print(f"\n✅ 聊天成功!")
                print(f"会话ID: {response.session_id}")
                print(f"消息: {response.message}")
                print(f"令牌使用: {response.tokens_used}")
                print(f"处理时间: {response.processing_time}ms")
                print(f"元数据: {response.meta_data}")
                
            except Exception as chat_error:
                print(f"\n❌ 聊天失败: {chat_error}")
                print(f"错误类型: {type(chat_error)}")
                
                # 如果是AttributeError且包含'get'，说明重现了问题
                if isinstance(chat_error, AttributeError) and "get" in str(chat_error):
                    print("\n🎯 成功重现了'int' object has no attribute 'get'错误！")
                    print(f"完整错误信息: {chat_error}")
                    
                    # 打印堆栈跟踪
                    import traceback
                    print("\n📋 堆栈跟踪:")
                    traceback.print_exc()
                
                raise
                
        except Exception as e:
            print(f"❌ 测试过程中发生错误: {e}")
            import traceback
            traceback.print_exc()
        finally:
            await db.close()
        break

if __name__ == "__main__":
    asyncio.run(test_real_agent_chat())