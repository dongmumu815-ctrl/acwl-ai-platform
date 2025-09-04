#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试修改后的review_content_safety_agent_db.py
验证数据库访问方式的修改是否正确
"""

import asyncio
import sys
import os

# 添加项目路径
backend_path = os.path.join(os.path.dirname(__file__), 'backend')
sys.path.insert(0, backend_path)
print(f"添加路径: {backend_path}")

from app.services.review_content_safety_agent_db import EnhancedContentSafetyAgentDB
from app.core.database import get_db
from sqlalchemy.ext.asyncio import AsyncSession

async def test_agent_initialization():
    """
    测试Agent的初始化和数据库访问
    """
    print("开始测试修改后的内容安全检测Agent...")
    
    # LLM配置
    llm_config = {
        'type': 'ollama',
        'model': 'qwen2.5:7b',
        'base_url': 'http://localhost:11434'
    }
    
    try:
        # 创建Agent实例
        agent = EnhancedContentSafetyAgentDB(
            llm_config=llm_config,
            instruction_set_id=13
        )
        print("Agent实例创建成功")
        
        # 获取数据库会话
        async for db in get_db():
            print("获取数据库会话成功")
            
            # 异步初始化Agent
            await agent.initialize(db)
            print("Agent初始化成功")
            
            # 测试内容检测
            test_content = "这是一个测试内容"
            result = agent.detect_content(test_content)
            print(f"检测结果: {result}")
            
            break  # 只使用第一个数据库会话
            
    except Exception as e:
        print(f"测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    print("测试完成！")
    return True

if __name__ == "__main__":
    # 运行测试
    success = asyncio.run(test_agent_initialization())
    if success:
        print("\n✅ 所有测试通过！数据库访问方式修改成功。")
    else:
        print("\n❌ 测试失败，请检查修改。")
        sys.exit(1)