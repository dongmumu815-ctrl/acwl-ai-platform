#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试InstructionExecutor的节点树执行功能
"""

import asyncio
import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.database import get_db
from app.services.instruction_executor import InstructionExecutor
from sqlalchemy.orm import Session

async def test_instruction_executor():
    """
    测试指令执行器的节点树执行功能
    """
    print("🚀 开始测试InstructionExecutor...")
    
    # 获取数据库连接
    from app.core.database import SessionLocal
    db: Session = SessionLocal()
    
    try:
        # 创建指令执行器
        executor = InstructionExecutor(db)
        
        # 测试指令集ID 32（审读Agent使用的指令集）
        instruction_set_id = 32
        test_text = "这是一个测试消息，用于验证审读功能是否正常工作。"
        
        print(f"\n📝 测试参数:")
        print(f"   指令集ID: {instruction_set_id}")
        print(f"   测试文本: {test_text}")
        
        # 执行指令集
        print(f"\n🔄 开始执行指令集...")
        result = await executor.execute(instruction_set_id, test_text)
        
        print(f"\n✅ 执行完成!")
        print(f"📊 执行结果:")
        print(f"   执行路径: {result.get('execution_path', [])}")
        print(f"   最终结果: {result.get('final_result', '')}")
        print(f"   置信度: {result.get('confidence_score', 0.0)}")
        print(f"   执行时间: {result.get('execution_time_ms', 0)}ms")
        print(f"   元数据: {result.get('metadata', {})}")
        
        # 检查是否按节点树执行
        execution_path = result.get('execution_path', [])
        if execution_path:
            print(f"\n🌳 节点执行路径分析:")
            for i, path_item in enumerate(execution_path):
                if isinstance(path_item, dict):
                    print(f"   {i+1}. 节点ID: {path_item.get('node_id')}, 标题: {path_item.get('node_title')}, 类型: {path_item.get('node_type')}")
                else:
                    print(f"   {i+1}. 节点ID: {path_item}")
        else:
            print(f"\n⚠️ 执行路径为空，可能没有按节点树执行")
            
    except Exception as e:
        print(f"❌ 测试失败: {str(e)}")
        import traceback
        print(f"错误详情: {traceback.format_exc()}")
    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(test_instruction_executor())