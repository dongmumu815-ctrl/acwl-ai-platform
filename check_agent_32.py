#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查 Agent ID 32 的详细配置
"""

import sys
import os
import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

# 添加后端路径到 sys.path
backend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), 'backend'))
sys.path.insert(0, backend_path)

# 切换到后端目录
os.chdir(backend_path)

from app.core.database import AsyncSessionLocal
from app.models import Agent, ModelServiceConfig

async def check_agent_32():
    """
    检查 Agent ID 32 的详细配置
    """
    print("检查 Agent ID 32 的配置...")
    
    # 创建数据库会话
    async with AsyncSessionLocal() as db:
        try:
            # 查询 Agent ID 为 32 的详细信息
            agent_query = select(Agent).options(
                selectinload(Agent.model_service_config)
            ).where(Agent.id == 32)
            agent_result = await db.execute(agent_query)
            agent = agent_result.scalar_one_or_none()
            
            if not agent:
                print("未找到 Agent ID 32")
                return
                
            print(f"Agent 详细信息:")
            print(f"  ID: {agent.id}")
            print(f"  名称: {agent.name}")
            print(f"  类型: {agent.agent_type}")
            print(f"  状态: {agent.status}")
            print(f"  是否启用: {agent.is_enabled}")
            print(f"  记忆功能: {agent.memory_enabled}")
            print(f"  模型服务配置 ID: {agent.model_service_config_id}")
            print(f"  系统提示: {agent.system_prompt[:100] if agent.system_prompt else 'None'}...")
            print(f"  创建者 ID: {agent.created_by}")
            print(f"  创建时间: {agent.created_at}")
            print(f"  更新时间: {agent.updated_at}")
            
            # 检查模型服务配置
            if agent.model_service_config:
                config = agent.model_service_config
                print(f"\n模型服务配置详细信息:")
                print(f"  ID: {config.id}")
                print(f"  名称: {config.name}")
                print(f"  显示名称: {config.display_name}")
                print(f"  提供商: {config.provider}")
                print(f"  模型类型: {config.model_type}")
                print(f"  模型名称: {config.model_name}")
                print(f"  API 端点: {config.api_endpoint}")
                print(f"  API 密钥: {'***' if config.api_key else 'None'}")
                print(f"  最大令牌数: {config.max_tokens}")
                print(f"  温度: {config.temperature}")
                print(f"  是否激活: {config.is_active}")
                print(f"  是否默认: {config.is_default}")
                print(f"  额外配置: {config.extra_config}")
            else:
                print("\n模型服务配置: None")
                
            # 检查 Agent 的特殊属性
            print(f"\nAgent 对象的所有属性:")
            for attr in dir(agent):
                if not attr.startswith('_'):
                    try:
                        value = getattr(agent, attr)
                        if not callable(value):
                            print(f"  {attr}: {value}")
                    except Exception as e:
                        print(f"  {attr}: <无法访问: {e}>")
                        
        except Exception as e:
            print(f"检查过程中出错: {str(e)}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(check_agent_32())