#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import asyncio
import aiohttp
import json

async def test_es_template_list():
    """测试ES查询模板列表API的dataResourceId字段"""
    
    # 配置
    base_url = "http://localhost:8082"
    
    # 使用提供的访问令牌
    token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI1IiwiZXhwIjoxNzU4NzE3Nzk3fQ.GforYnFpXcKGhbxT20_5CwSlBDpNogPEiE_U04bd8C0"
    print(f"使用提供的token: {token[:20]}...")
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    async with aiohttp.ClientSession() as session:
        try:
            # 查询ES查询模板列表
            print("查询ES查询模板列表...")
            async with session.get(
                f"{base_url}/api/v1/es/templates",
                headers=headers
            ) as response:
                print(f"响应状态码: {response.status}")
                
                if response.status == 200:
                    result = await response.json()
                    
                    # 获取模板列表
                    templates = result.get("data", [])
                    print(f"查询成功，共找到 {len(templates)} 个模板")
                    
                    # 检查每个模板是否包含dataResourceId字段
                    for template in templates:
                        template_id = template.get("id")
                        template_name = template.get("name")
                        data_resource_id = template.get("dataResourceId")
                        
                        print(f"模板ID: {template_id}, 名称: {template_name}, dataResourceId: {data_resource_id}")
                        
                        if data_resource_id is not None:
                            print(f"✅ 模板 {template_id} 的dataResourceId字段正常: {data_resource_id}")
                        else:
                            print(f"❌ 模板 {template_id} 的dataResourceId字段缺失或为None")
                    
                else:
                    error_text = await response.text()
                    print(f"查询失败: {error_text}")
                    
        except Exception as e:
            print(f"请求异常: {str(e)}")

if __name__ == "__main__":
    asyncio.run(test_es_template_list())