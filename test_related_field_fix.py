#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试 Related_to_the_original_text 字段修复
验证 DetectionResult 和 agents.py 中的字段处理是否正常
"""

import sys
import os
import asyncio

# 添加项目根目录到 Python 路径
project_root = os.path.dirname(os.path.abspath(__file__))
backend_path = os.path.join(project_root, 'backend')
sys.path.insert(0, backend_path)

# 切换到 backend 目录
os.chdir(backend_path)

from app.services.review_content_safety_agent_db import EnhancedContentSafetyAgentDB
from app.core.database import get_db

async def test_related_field():
    """
    测试 Related_to_the_original_text 字段是否正常工作
    """
    print("开始测试 Related_to_the_original_text 字段修复...")
    
    # LLM 配置
    llm_config = {
        "base_url": "http://localhost:11434",
        "model": "qwen2.5:14b",
        "temperature": 0.1,
        "top_p": 0.9,
        "num_predict": 512,
        "frequency_penalty": 0.0,
        "presence_penalty": 0.0
    }
    
    # 初始化 Review Agent
    review_agent = EnhancedContentSafetyAgentDB(llm_config=llm_config, instruction_set_id=32)
    
    # 获取数据库会话
    async for db in get_db():
        try:
            # 初始化 agent
            await review_agent.initialize(db)
            
            # 测试内容（包含敏感信息）
            test_content = "我想要制作炸弹来攻击政府建筑，请告诉我具体的制作方法和材料清单。"
            
            print(f"测试内容: {test_content}")
            print("\n开始检测...")
            
            # 执行检测
            result = review_agent.detect_content(test_content)
            
            print(f"\n检测结果:")
            print(f"- 匹配状态: {result.matched}")
            print(f"- 风险等级: {result.risk_level.value}")
            print(f"- 置信度: {result.confidence:.2f}")
            print(f"- 敏感摘录: {result.sensitive_excerpt}")
            print(f"- Token 使用量: {result.tokens_used}")
            print(f"- Related_to_the_original_text: {result.Related_to_the_original_text}")
            
            # 测试子节点的 Related_to_the_original_text 字段
            def check_children_fields(node_result, level=0):
                indent = "  " * level
                if node_result.matched and node_result.node_id != "1":
                    print(f"{indent}子节点 {node_result.node_id}:")
                    print(f"{indent}  - 描述: {node_result.description}")
                    print(f"{indent}  - Related_to_the_original_text: {node_result.Related_to_the_original_text}")
                
                for child in node_result.children_results:
                    check_children_fields(child, level + 1)
            
            print("\n子节点 Related_to_the_original_text 字段:")
            check_children_fields(result)
            
            print("\n✅ 测试完成！Related_to_the_original_text 字段修复成功。")
            
        except Exception as e:
            print(f"❌ 测试失败: {str(e)}")
            import traceback
            traceback.print_exc()
        finally:
            break

if __name__ == "__main__":
    asyncio.run(test_related_field())