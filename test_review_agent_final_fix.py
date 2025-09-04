#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试Review Agent最终修复效果
验证字段名兼容性处理是否完全解决了KeyError问题
"""

import sys
import os
import asyncio
from sqlalchemy.ext.asyncio import AsyncSession

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(project_root, 'backend'))

from app.core.database import get_db
from app.services.review_content_safety_agent_db import EnhancedContentSafetyAgentDB

async def test_review_agent_final():
    """
    测试Review Agent的最终修复效果
    """
    print("=== Review Agent 最终修复测试 ===")
    
    # 获取数据库会话
    async for db in get_db():
        try:
            # 初始化Review Agent (Agent 32)
            llm_config = {
                'base_url': 'http://localhost:11434',
                'model': 'qwen2.5:14b',
                'temperature': 1.30,
                'max_tokens': 4098,
                'top_p': 0.90,
                'frequency_penalty': 0.0,
                'presence_penalty': 0.0,
                'timeout': 30
            }
            
            agent = EnhancedContentSafetyAgentDB(llm_config=llm_config, instruction_set_id=13)
            await agent.initialize(db)
            
            # 测试内容（包含可能触发敏感检测的内容）
            test_content = """
            The contribution examines a recent ruling of the Italian Corte di Cassazione, 
            concerning the recognition of parentage resulting from medically assisted 
            procreation techniques performed abroad by female same-sex couples. 
            The article focuses on legal interpretations and rights implications 
            without involving any sexual or reproductive behavior descriptions.
            """
            
            print(f"测试内容: {test_content.strip()}")
            print("\n开始检测...")
            
            # 执行内容检测
            result = agent.detect_content(test_content)
            
            print("\n=== 检测结果 ===")
            print(f"匹配状态: {result.matched}")
            print(f"风险等级: {result.risk_level.value}")
            print(f"置信度: {result.confidence:.2f}")
            print(f"敏感摘录: {result.sensitive_excerpt}")
            print(f"Token使用量: {result.tokens_used}")
            print(f"判断理由: {result.evidence}")
            
            # 检查是否有子节点结果
            if result.children_results:
                print("\n=== 子节点检测结果 ===")
                for i, child_result in enumerate(result.children_results):
                    print(f"子节点 {i+1}: {child_result.description}")
                    print(f"  匹配: {child_result.matched}")
                    print(f"  置信度: {child_result.confidence:.2f}")
                    print(f"  风险等级: {child_result.risk_level.value}")
                    if child_result.sensitive_excerpt:
                        print(f"  敏感摘录: {child_result.sensitive_excerpt}")
            
            print("\n✅ 测试完成，未出现KeyError错误！")
            return True
            
        except Exception as e:
            print(f"\n❌ 测试失败: {str(e)}")
            import traceback
            traceback.print_exc()
            return False
        finally:
            await db.close()

if __name__ == "__main__":
    # 运行测试
    success = asyncio.run(test_review_agent_final())
    if success:
        print("\n🎉 Review Agent 字段兼容性修复成功！")
    else:
        print("\n💥 修复仍有问题，需要进一步检查")