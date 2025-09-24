#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import asyncio
import aiohttp
import json

async def test_es_template_api():
    """测试ES模板API修复"""
    
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
            # 1. 先获取ES模板列表
            print("1. 获取ES模板列表...")
            async with session.get(
                f"{base_url}/api/v1/es/templates",
                headers=headers
            ) as response:
                print(f"响应状态码: {response.status}")
                
                if response.status == 200:
                    result = await response.json()
                    templates = result.get("data", [])
                    print(f"找到 {len(templates)} 个ES模板")
                    
                    if templates:
                        # 2. 测试获取第一个模板的详情
                        template_id = templates[0]["id"]
                        print(f"\n2. 测试获取模板详情，模板ID: {template_id}")
                        
                        async with session.get(
                            f"{base_url}/api/v1/es/templates/{template_id}",
                            headers=headers
                        ) as detail_response:
                            print(f"模板详情响应状态码: {detail_response.status}")
                            
                            if detail_response.status == 200:
                                detail_result = await detail_response.json()
                                template_data = detail_result.get("data", {})
                                print(f"✅ 成功获取模板详情:")
                                print(f"   - 模板名称: {template_data.get('name')}")
                                print(f"   - 模板描述: {template_data.get('description')}")
                                print(f"   - 数据源ID: {template_data.get('datasourceId')}")
                                print(f"   - 数据资源ID: {template_data.get('dataResourceId')}")
                                print(f"   - 索引: {template_data.get('indices')}")
                                
                                # 检查是否有config字段（用于资源包查询页面）
                                if 'config' in template_data:
                                    print(f"   - 配置信息: {template_data.get('config')}")
                                else:
                                    print("   - ⚠️ 模板数据中没有config字段")
                                    
                            else:
                                error_text = await detail_response.text()
                                print(f"❌ 获取模板详情失败: {error_text}")
                    else:
                        print("❌ 没有找到ES模板，无法测试详情API")
                        
                else:
                    error_text = await response.text()
                    print(f"❌ 获取模板列表失败: {error_text}")
                    
        except Exception as e:
            print(f"请求异常: {str(e)}")

if __name__ == "__main__":
    asyncio.run(test_es_template_api())