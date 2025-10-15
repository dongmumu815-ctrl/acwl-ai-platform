#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
触发API调用，查看调试输出
"""

import asyncio
import aiohttp

async def trigger_debug():
    """触发API调用"""
    token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI1IiwiZXhwIjoxNzYwMDA0NjYxfQ.Fx5LvGD4ZBcLWpxW2CNzR7rtC0QwOdyoJvGPjR2MdqE"
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    print("🚀 发送API请求，触发调试输出...")
    
    async with aiohttp.ClientSession() as session:
        async with session.get("http://localhost:8082/api/v1/customers", headers=headers) as response:
            if response.status == 200:
                data = await response.json()
                print(f"✅ 请求成功，返回 {len(data['data']['items'])} 条记录")
            else:
                print(f"❌ 请求失败: {response.status}")

if __name__ == "__main__":
    asyncio.run(trigger_debug())