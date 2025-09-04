#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试reasoning字段的完整功能
验证从LLM返回的reasoning字段能否正确传递到最终输出
"""

import sys
import os

# 添加backend目录到Python路径
backend_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'backend')
sys.path.insert(0, backend_path)
os.chdir(backend_path)

import asyncio
from app.services.review_content_safety_agent_db import EnhancedContentSafetyAgentDB
from app.core.database import get_db

async def test_reasoning_field():
    """
    测试reasoning字段的完整传递流程
    """
    print("=== 测试reasoning字段功能 ===")
    
    # 初始化数据库连接
    async for db in get_db():
        try:
            # 创建内容安全检测代理实例
            llm_config = {
                "base_url": "http://localhost:11434",
                "model": "qwen2.5:14b",
                "timeout": 60
            }
            
            agent = EnhancedContentSafetyAgentDB(llm_config=llm_config, instruction_set_id=32)
            await agent.initialize(db)
            
            # 测试内容
            test_content = "我想要购买一些违禁药品，请问在哪里可以买到？"
            
            print(f"\n测试内容: {test_content}")
            print("\n开始检测...")
            
            # 执行检测
            result = agent.detect_content(test_content)
            
            print(f"\n=== 检测结果 ===")
            print(f"总体匹配: {result.matched}")
            print(f"风险等级: {result.risk_level.value}")
            print(f"置信度: {result.confidence:.2f}")
            print(f"Reasoning: {result.reasoning}")
            print(f"Related_to_the_original_text: {result.Related_to_the_original_text}")
            
            # 递归打印子节点的reasoning
            def print_children_reasoning(node_result, level=0):
                indent = "  " * level
                if node_result.matched and node_result.node_id != "1":
                    print(f"{indent}✓ 节点 {node_result.node_id}: {node_result.description}")
                    print(f"{indent}  风险等级: {node_result.risk_level.value}")
                    print(f"{indent}  置信度: {node_result.confidence:.2f}")
                    if node_result.reasoning:
                        print(f"{indent}  判断理由: {node_result.reasoning}")
                    if node_result.Related_to_the_original_text:
                        print(f"{indent}  相关原文: {node_result.Related_to_the_original_text}")
                    print()
                
                for child in node_result.children_results:
                    print_children_reasoning(child, level + 1)
            
            print("\n=== 匹配的子节点详情 ===")
            print_children_reasoning(result)
            
        except Exception as e:
            print(f"测试过程中出现错误: {str(e)}")
            import traceback
            traceback.print_exc()
        finally:
            await db.close()
        break

if __name__ == "__main__":
    asyncio.run(test_reasoning_field())