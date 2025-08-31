#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试risk_level字段的API接口
"""

import requests
import json

def test_instruction_node_api():
    """测试指令节点API接口"""
    base_url = "http://localhost:8082"
    
    # 测试数据
    test_data = {
        "title": "测试节点",
        "description": "测试risk_level字段",
        "node_type": "CONDITION",
        "risk_level": "medium",
        "keywords": "测试,风险等级",
        "condition_text": "测试条件",
        "instruction_set_id": 13
    }
    
    try:
        # 1. 创建指令节点
        print("1. 测试创建指令节点...")
        response = requests.post(
            f"{base_url}/api/v1/instruction-sets/13/nodes",
            json=test_data,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"状态码: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"创建成功: {json.dumps(result, indent=2, ensure_ascii=False)}")
            
            # 检查创建结果中的risk_level字段
            risk_level = result.get('data', {}).get('risk_level')
            print(f"\n✅ 创建的节点risk_level字段值: {risk_level}")
            
            # 2. 获取指令集的所有节点
            print(f"\n2. 测试获取指令集13的所有节点...")
            get_response = requests.get(f"{base_url}/api/v1/instruction-sets/13/nodes")
            print(f"状态码: {get_response.status_code}")
            if get_response.status_code == 200:
                get_result = get_response.json()
                nodes = get_result.get('data', [])
                print(f"获取到 {len(nodes)} 个节点")
                
                # 查找刚创建的节点
                for node in nodes:
                    if node.get('title') == '测试节点':
                        print(f"\n找到测试节点: {json.dumps(node, indent=2, ensure_ascii=False)}")
                        risk_level = node.get('risk_level')
                        print(f"\n✅ 节点列表中的risk_level字段值: {risk_level}")
                        break
            else:
                print(f"获取节点列表失败: {get_response.text}")
        else:
            print(f"创建失败: {response.text}")
            
    except Exception as e:
        print(f"测试出错: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_instruction_node_api()