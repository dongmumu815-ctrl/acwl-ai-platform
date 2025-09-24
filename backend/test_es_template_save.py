#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试ES查询模板保存API，验证data_resource_id字段的保存
"""

import asyncio
import json
import aiohttp
import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 使用提供的访问令牌
ACCESS_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI1IiwiZXhwIjoxNzU4NzE3Nzk3fQ.GforYnFpXcKGhbxT20_5CwSlBDpNogPEiE_U04bd8C0"

async def test_es_template_save():
    """
    测试ES查询模板保存功能
    """
    # API基础URL
    base_url = "http://localhost:8082"
    
    # 测试数据
    template_data = {
        "name": "测试ES模板_data_resource_id",
        "description": "测试data_resource_id字段保存的ES查询模板",
        "datasourceId": 9,  # 使用现有的ES数据源ID
        "dataResourceId": 24,  # 使用现有的数据资源ID
        "indices": ["test_index"],
        "query": {
            "query": {
                "match_all": {}
            }
        },
        "tags": ["测试", "data_resource_id"],
        "isTemplate": True
    }
    
    # 请求头（需要认证token）
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {ACCESS_TOKEN}"
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            # 发送POST请求保存模板
            print("发送ES查询模板保存请求...")
            print(f"请求数据: {json.dumps(template_data, indent=2, ensure_ascii=False)}")
            
            async with session.post(
                f"{base_url}/api/v1/es/templates",
                json=template_data,
                headers=headers
            ) as response:
                print(f"响应状态码: {response.status}")
                
                if response.status == 200:
                    result = await response.json()
                    print(f"保存成功: {json.dumps(result, indent=2, ensure_ascii=False)}")
                    
                    # 获取保存的模板ID
                    template_id = result.get("data", {}).get("id")
                    if template_id:
                        print(f"模板ID: {template_id}")
                        
                        # 查询保存的模板，验证data_resource_id是否正确保存
                        print("\n查询保存的模板...")
                        async with session.get(
                            f"{base_url}/api/v1/es/templates/{template_id}",
                            headers=headers
                        ) as get_response:
                            if get_response.status == 200:
                                template_detail = await get_response.json()
                                saved_data_resource_id = template_detail.get("data", {}).get("dataResourceId")
                                print(f"保存的data_resource_id: {saved_data_resource_id}")
                                
                                if saved_data_resource_id == 24:
                                    print("✅ data_resource_id字段保存成功！")
                                else:
                                    print(f"❌ data_resource_id字段保存失败！期望: 24, 实际: {saved_data_resource_id}")
                            else:
                                print(f"查询模板失败: {get_response.status}")
                                error_text = await get_response.text()
                                print(f"错误信息: {error_text}")
                else:
                    error_text = await response.text()
                    print(f"保存失败: {error_text}")
                    
    except Exception as e:
        print(f"测试过程中发生错误: {str(e)}")

if __name__ == "__main__":
    print(f"使用提供的token: {ACCESS_TOKEN[:20]}...")
    
    # 运行测试
    asyncio.run(test_es_template_save())