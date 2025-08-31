#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
创建测试指令集数据
"""

import asyncio
import aiohttp
import json
from typing import Dict, Any, List


class InstructionSetCreator:
    """指令集创建器"""
    
    def __init__(self, base_url: str = "http://localhost:8082"):
        """初始化创建器"""
        self.base_url = base_url
        self.api_prefix = f"{base_url}/api/v1/instruction-sets"
    
    async def create_instruction_set(self, name: str, description: str) -> int:
        """创建指令集"""
        async with aiohttp.ClientSession() as session:
            data = {
                "name": name,
                "description": description,
                "version": "1.0.0",
                "status": "ACTIVE"
            }
            
            async with session.post(self.api_prefix, json=data) as response:
                if response.status == 200:
                    result = await response.json()
                    if result.get('success'):
                        instruction_set_id = result['data']['id']
                        print(f"✅ 创建指令集成功: {name} (ID: {instruction_set_id})")
                        return instruction_set_id
                    else:
                        print(f"❌ 创建指令集失败: {result.get('message')}")
                else:
                    error_text = await response.text()
                    print(f"❌ HTTP错误 {response.status}: {error_text}")
        return None
    
    async def create_instruction_node(self, instruction_set_id: int, node_data: Dict[str, Any]) -> int:
        """创建指令节点"""
        async with aiohttp.ClientSession() as session:
            url = f"{self.api_prefix}/{instruction_set_id}/nodes"
            
            async with session.post(url, json=node_data) as response:
                if response.status == 200:
                    result = await response.json()
                    if result.get('success'):
                        node_id = result['data']['id']
                        print(f"  ✅ 创建节点成功: {node_data['title']} (ID: {node_id})")
                        return node_id
                    else:
                        print(f"  ❌ 创建节点失败: {result.get('message')}")
                else:
                    error_text = await response.text()
                    print(f"  ❌ HTTP错误 {response.status}: {error_text}")
        return None
    
    async def create_content_safety_instruction_set(self):
        """创建内容安全检测指令集"""
        print("🏗️  开始创建内容安全检测指令集...")
        
        # 创建指令集
        instruction_set_id = await self.create_instruction_set(
            "内容安全检测",
            "用于检测文本内容的安全性，包括政治敏感、违法违规等内容"
        )
        
        if not instruction_set_id:
            print("❌ 指令集创建失败，终止操作")
            return None
        
        # 创建根节点
        root_node_id = await self.create_instruction_node(instruction_set_id, {
            "instruction_set_id": instruction_set_id,
            "title": "内容安全检测",
            "description": "检测输入文本的安全性",
            "node_type": "CONDITION",
            "condition_text": "检测文本内容安全性",
            "condition_type": "AI_CLASSIFICATION",
            "action_type": "CONTINUE",
            "sort_order": 1,
            "is_active": True
        })
        
        if not root_node_id:
            return None
        
        # 创建二级节点
        level2_nodes = [
            {
                "title": "国家制度相关内容检测",
                "description": "检测攻击国家制度的内容",
                "node_type": "CONDITION",
                "condition_text": "检测攻击国家制度内容",
                "parent_id": root_node_id,
                "sort_order": 1
            },
            {
                "title": "国家统一相关内容检测",
                "description": "检测分裂国家统一的内容",
                "node_type": "CONDITION",
                "condition_text": "检测分裂国家统一内容",
                "parent_id": root_node_id,
                "sort_order": 2
            },
            {
                "title": "领土完整相关内容检测",
                "description": "检测损害领土完整的内容",
                "node_type": "CONDITION",
                "condition_text": "检测损害领土完整内容",
                "parent_id": root_node_id,
                "sort_order": 3
            }
        ]
        
        level2_node_ids = []
        for node_data in level2_nodes:
            node_id = await self.create_instruction_node(instruction_set_id, node_data)
            if node_id:
                level2_node_ids.append(node_id)
        
        # 创建三级节点 - 国家制度相关
        if len(level2_node_ids) >= 1:
            level3_nodes_1 = [
                {
                    "title": "攻击社会主义制度内容检测",
                    "description": "检测攻击社会主义制度的内容",
                    "node_type": "ACTION",
                    "condition_text": "检测攻击社会主义制度",
                    "parent_id": level2_node_ids[0],
                    "sort_order": 1
                },
                {
                    "title": "攻击中国道路模式内容检测",
                    "description": "检测攻击中国发展道路的内容",
                    "node_type": "ACTION",
                    "condition_text": "检测攻击中国道路模式",
                    "parent_id": level2_node_ids[0],
                    "sort_order": 2
                },
                {
                    "title": "攻击宪政制度内容检测",
                    "description": "检测攻击宪政制度的内容",
                    "node_type": "ACTION",
                    "condition_text": "检测攻击宪政制度",
                    "parent_id": level2_node_ids[0],
                    "sort_order": 3
                }
            ]
            
            for node_data in level3_nodes_1:
                await self.create_instruction_node(instruction_set_id, node_data)
        
        # 创建三级节点 - 国家统一相关
        if len(level2_node_ids) >= 2:
            level3_nodes_2 = [
                {
                    "title": "反对一国两制内容检测",
                    "description": "检测反对一国两制的内容",
                    "node_type": "ACTION",
                    "condition_text": "检测反对一国两制",
                    "parent_id": level2_node_ids[1],
                    "sort_order": 1
                },
                {
                    "title": "支持颜色革命内容检测",
                    "description": "检测支持颜色革命的内容",
                    "node_type": "ACTION",
                    "condition_text": "检测支持颜色革命",
                    "parent_id": level2_node_ids[1],
                    "sort_order": 2
                },
                {
                    "title": "涉台内容检测",
                    "description": "检测涉台敏感内容",
                    "node_type": "ACTION",
                    "condition_text": "检测涉台内容",
                    "parent_id": level2_node_ids[1],
                    "sort_order": 3
                },
                {
                    "title": "涉港内容检测",
                    "description": "检测涉港敏感内容",
                    "node_type": "ACTION",
                    "condition_text": "检测涉港内容",
                    "parent_id": level2_node_ids[1],
                    "sort_order": 4
                },
                {
                    "title": "涉藏内容检测",
                    "description": "检测涉藏敏感内容",
                    "node_type": "ACTION",
                    "condition_text": "检测涉藏内容",
                    "parent_id": level2_node_ids[1],
                    "sort_order": 5
                },
                {
                    "title": "涉疆内容检测",
                    "description": "检测涉疆敏感内容",
                    "node_type": "ACTION",
                    "condition_text": "检测涉疆内容",
                    "parent_id": level2_node_ids[1],
                    "sort_order": 6
                },
                {
                    "title": "涉蒙内容检测",
                    "description": "检测涉蒙敏感内容",
                    "node_type": "ACTION",
                    "condition_text": "检测涉蒙内容",
                    "parent_id": level2_node_ids[1],
                    "sort_order": 7
                }
            ]
            
            for node_data in level3_nodes_2:
                await self.create_instruction_node(instruction_set_id, node_data)
        
        # 创建三级节点 - 领土完整相关
        if len(level2_node_ids) >= 3:
            level3_nodes_3 = [
                {
                    "title": "地图错绘漏绘内容检测",
                    "description": "检测地图错绘漏绘的内容",
                    "node_type": "ACTION",
                    "condition_text": "检测地图错绘漏绘",
                    "parent_id": level2_node_ids[2],
                    "sort_order": 1
                },
                {
                    "title": "新疆西藏边界问题检测",
                    "description": "检测新疆西藏边界问题的内容",
                    "node_type": "ACTION",
                    "condition_text": "检测新疆西藏边界问题",
                    "parent_id": level2_node_ids[2],
                    "sort_order": 2
                }
            ]
            
            for node_data in level3_nodes_3:
                await self.create_instruction_node(instruction_set_id, node_data)
        
        print(f"\n🎉 内容安全检测指令集创建完成! (ID: {instruction_set_id})")
        return instruction_set_id


async def main():
    """主函数"""
    print("🚀 开始创建测试指令集数据")
    print("="*50)
    
    creator = InstructionSetCreator()
    
    # 创建内容安全检测指令集
    instruction_set_id = await creator.create_content_safety_instruction_set()
    
    if instruction_set_id:
        print(f"\n✨ 测试数据创建完成! 指令集ID: {instruction_set_id}")
        print(f"🔗 可以使用以下URL测试树结构:")
        print(f"   http://localhost:8082/api/v1/instruction-sets/{instruction_set_id}/tree")
    else:
        print("\n❌ 测试数据创建失败!")


if __name__ == "__main__":
    asyncio.run(main())