#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查 Agent 32 的模型配置参数
"""

import asyncio
import sys
import os

# 添加backend目录到Python路径
backend_path = os.path.join(os.path.dirname(__file__), 'backend')
sys.path.insert(0, backend_path)
os.chdir(backend_path)  # 切换到backend目录

from app.core.database import get_db
from app.models import Agent
from sqlalchemy import select
from sqlalchemy.orm import selectinload

async def check_agent_32_config():
    """
    检查 Agent 32 的模型配置参数
    """
    print("=== 检查 Agent 32 的模型配置参数 ===")
    
    # 获取数据库会话
    async for db in get_db():
        try:
            # 查找Agent ID 32及其模型配置
            agent_query = select(Agent).options(
                selectinload(Agent.model_service_config)
            ).where(Agent.id == 32)
            agent_result = await db.execute(agent_query)
            agent = agent_result.scalar_one_or_none()
            
            if not agent:
                print("❌ Agent ID 32 不存在")
                return
            
            print(f"✅ 找到Agent: {agent.name} (类型: {agent.agent_type})")
            
            # 检查模型服务配置
            if agent.model_service_config:
                config = agent.model_service_config
                print(f"\n📋 模型配置参数:")
                print(f"  配置名称: {config.name}")
                print(f"  显示名称: {config.display_name}")
                print(f"  提供商: {config.provider}")
                print(f"  模型名称: {config.model_name}")
                print(f"  API端点: {config.api_endpoint}")
                print(f"  \n🔧 模型参数:")
                print(f"  温度(temperature): {config.temperature}")
                print(f"  最大tokens: {config.max_tokens}")
                print(f"  top_p: {config.top_p}")
                print(f"  频率惩罚(frequency_penalty): {config.frequency_penalty}")
                print(f"  存在惩罚(presence_penalty): {config.presence_penalty}")
                print(f"  超时时间: {config.timeout}")
                print(f"  重试次数: {config.retry_count}")
                print(f"  是否激活: {config.is_active}")
                print(f"  是否默认: {config.is_default}")
                
                # 检查这些参数在调用时的实际使用情况
                print(f"\n🚀 实际调用时的参数转换:")
                print(f"  temperature: {float(config.temperature or 0.7)}")
                print(f"  top_p: {float(config.top_p or 0.9)}")
                print(f"  max_tokens: {config.max_tokens or 4096}")
                print(f"  frequency_penalty: {float(config.frequency_penalty or 0.0)}")
                print(f"  presence_penalty: {float(config.presence_penalty or 0.0)}")
                print(f"  timeout: {config.timeout or 30}")
            else:
                print("❌ Agent 32 没有配置模型服务")
                
        except Exception as e:
            print(f"❌ 检查过程中发生错误: {e}")
            import traceback
            traceback.print_exc()
        finally:
            await db.close()
        break

if __name__ == "__main__":
    asyncio.run(check_agent_32_config())