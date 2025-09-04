#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试Review Agent修复后的JSON字段处理
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
from app.services.review_content_safety_agent_db import EnhancedContentSafetyAgentDB

async def test_review_agent_fix():
    """
    测试Review Agent修复后的JSON字段处理
    """
    print("=== 测试Review Agent修复后的JSON字段处理 ===")
    
    # 获取数据库会话
    async for db in get_db():
        try:
            # 查找Agent ID 32及其模型配置
            agent_query = select(Agent).options(
                selectinload(Agent.model_service_config)
            ).where(Agent.id == 32)
            agent_result = await db.execute(agent_query)
            agent = agent_result.scalar_one_or_none()
            
            if not agent or not agent.model_service_config:
                print("❌ Agent 32 或其模型配置不存在")
                return
            
            print(f"✅ 找到Agent: {agent.name}")
            
            # 构建llm_config
            config = agent.model_service_config
            llm_config = {
                'type': config.provider,
                'model': config.model_name,
                'base_url': config.api_endpoint,
                'api_key': config.api_key,
                'temperature': config.temperature,
                'top_p': config.top_p,
                'max_tokens': config.max_tokens,
                'frequency_penalty': config.frequency_penalty,
                'presence_penalty': config.presence_penalty,
                'timeout': config.timeout
            }
            
            print(f"📋 LLM配置: {llm_config}")
            
            # 初始化Review Agent
            review_agent = EnhancedContentSafetyAgentDB(llm_config=llm_config)
            await review_agent.initialize(db)
            
            print("✅ Review Agent初始化成功")
            
            # 测试内容
            test_content = "This content discusses female same-sex couples and medically assisted procreation techniques."
            
            print(f"\n🧪 测试内容: {test_content}")
            
            # 执行内容检测
            result = review_agent.detect_content(test_content)
            
            print(f"\n📊 检测结果:")
            print(f"  匹配: {result.matched}")
            print(f"  风险等级: {result.risk_level}")
            print(f"  置信度: {result.confidence}")
            print(f"  敏感摘录: {result.sensitive_excerpt}")
            print(f"  Token使用量: {result.tokens_used}")
            
            if result.matched:
                print("✅ 成功检测到敏感内容，JSON字段处理正常")
            else:
                print("ℹ️ 未检测到敏感内容")
                
        except Exception as e:
            print(f"❌ 测试过程中发生错误: {e}")
            import traceback
            traceback.print_exc()
        finally:
            await db.close()
        break

if __name__ == "__main__":
    asyncio.run(test_review_agent_fix())