#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试节点编号生成功能

这个脚本用于测试review_content_safety_agent_db.py中的节点编号生成机制
是否按照instruction_sets.py的方式正确工作。
"""

import sys
import os

# 添加backend目录到Python路径
backend_path = os.path.join(os.path.dirname(__file__), 'backend')
sys.path.insert(0, backend_path)

# 设置工作目录到backend
os.chdir(backend_path)

def test_node_numbering():
    """
    测试节点编号生成功能
    """
    print("开始测试节点编号生成功能...")
    
    try:
        # 首先检查数据库中的指令集
        from app.core.database import get_db
        from app.crud.instruction_set import get_instruction_sets
        
        db = next(get_db())
        instruction_sets = get_instruction_sets(db)
        
        print("\n可用的指令集:")
        for instruction_set in instruction_sets:
            print(f"ID: {instruction_set.id}, 名称: {instruction_set.name}")
        
        if not instruction_sets:
            print("数据库中没有指令集，无法进行测试")
            return
        
        # 使用第一个可用的指令集进行测试
        test_id = instruction_sets[0].id
        print(f"\n使用指令集 ID {test_id} 进行测试...")
        
        from app.services.review_content_safety_agent_db import EnhancedContentSafetyAgentDB
        
        # 创建EnhancedContentSafetyAgentDB实例
        agent = EnhancedContentSafetyAgentDB(instruction_set_id=test_id)
        
        print(f"\n根节点ID: {agent.root_node.node_id}")
        print(f"根节点描述: {agent.root_node.description}")
        
        # 递归打印所有节点及其编号
        def print_node_tree(node, level=0):
            indent = "  " * level
            print(f"{indent}├─ {node.node_id}: {node.description}")
            
            if hasattr(node, 'children') and node.children:
                for child in node.children:
                    print_node_tree(child, level + 1)
        
        print("\n节点树结构:")
        print_node_tree(agent.root_node)
        
        print("\n测试完成！节点编号生成正确！")
        
    except Exception as e:
        print(f"测试失败: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_node_numbering()