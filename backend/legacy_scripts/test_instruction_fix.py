#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试修复后的指令集执行逻辑
"""

import asyncio
import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.database import get_db_context
from app.services.instruction_executor import InstructionExecutor

async def test_instruction_executor():
    """
    测试指令集执行器
    """
    print("=== 测试修复后的指令集执行逻辑 ===")
    
    try:
        # 使用数据库会话上下文管理器
        async with get_db_context() as db:
            # 创建指令执行器
            executor = InstructionExecutor(db)
            
            # 测试内容
            test_content = "这是一个测试内容，包含一些政治敏感词汇，用于测试内容安全检测功能。"
            
            print(f"\n测试内容: {test_content}")
            print("\n开始执行指令集13...")
            
            # 执行指令集13
            result = await executor.execute(13, test_content)
            
            print("\n=== 执行结果 ===")
            print(f"最终结果: {result.get('final_result', '')}")
            print(f"置信度: {result.get('confidence', 0.0)}")
            print(f"执行时间: {result.get('execution_time', 0.0):.2f}秒")
            
            # 打印执行路径
            execution_path = result.get('execution_path', [])
            print(f"\n=== 执行路径 ({len(execution_path)}个节点) ===")
            for i, step in enumerate(execution_path, 1):
                print(f"{i}. {step.get('node_title', '')} (ID: {step.get('node_id', '')}, Type: {step.get('node_type', '')})")
            
            # 打印元数据
            metadata = result.get('metadata', {})
            print(f"\n=== 元数据信息 ===")
            for key, value in metadata.items():
                if key == 'all_detection_results':
                    print(f"{key}: {len(value)}项检测结果")
                    for j, detection in enumerate(value, 1):
                        print(f"  {j}. {detection.get('node_title', '')} - {detection.get('result', '')[:50]}...")
                else:
                    print(f"{key}: {value}")
            
            print("\n=== 测试完成 ===")
            
            # 验证是否执行了所有子检测项
            if 'all_detection_results' in metadata:
                detection_count = len(metadata['all_detection_results'])
                print(f"\n✅ 成功执行了{detection_count}项内容安全检测")
                return True
            else:
                print("\n❌ 未找到所有检测结果，可能存在问题")
                return False
                
    except Exception as e:
        print(f"\n❌ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    # 运行测试
    success = asyncio.run(test_instruction_executor())
    sys.exit(0 if success else 1)