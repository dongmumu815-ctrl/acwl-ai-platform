#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试配置保存功能
"""

import asyncio
import aiohttp
import json

# 测试配置
BASE_URL = "http://localhost:8082"

async def get_auth_token():
    """获取认证token"""
    login_data = {
        "username": "newuser",
        "password": "newpass123"
    }
    
    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(
                f"{BASE_URL}/api/v1/auth/login/json",
                json=login_data,
                headers={"Content-Type": "application/json"}
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    return result.get("access_token")
                else:
                    print(f"❌ 登录失败: {response.status}")
                    text = await response.text()
                    print(f"错误信息: {text}")
                    return None
        except Exception as e:
            print(f"❌ 登录请求失败: {e}")
            return None

async def create_template_with_config(token):
    """创建带配置的SQL模板"""
    template_data = {
        "name": "测试配置保存模板",
        "description": "测试前端配置保存功能",
        "datasourceId": 8,
        "dataResourceId": 3,
        "query": "SELECT * FROM cpc_agents WHERE status = :status AND created_at >= :start_date",
        "tags": ["测试", "配置"],
        "config": {
            "conditions": [
                {
                    "name": "status",
                    "label": "状态",
                    "type": "select",
                    "required": True,
                    "options": [
                        {"label": "活跃", "value": "active"},
                        {"label": "非活跃", "value": "inactive"}
                    ],
                    "defaultValue": "active"
                },
                {
                    "name": "start_date",
                    "label": "开始日期",
                    "type": "date",
                    "required": True,
                    "defaultValue": "2024-01-01"
                }
            ]
        },
        "isTemplate": True
    }
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(
                f"{BASE_URL}/api/v1/sql/templates",
                json=template_data,
                headers=headers
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    print("✅ 模板创建成功!")
                    print(f"模板ID: {result['data']['id']}")
                    print(f"模板名称: {result['data']['name']}")
                    return result['data']['id']
                else:
                    print(f"❌ 模板创建失败: {response.status}")
                    text = await response.text()
                    print(f"错误信息: {text}")
                    return None
        except Exception as e:
            print(f"❌ 创建模板请求失败: {e}")
            return None

async def get_template_detail(token, template_id):
    """获取模板详情，验证配置是否正确保存"""
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(
                f"{BASE_URL}/api/v1/sql/templates/{template_id}",
                headers=headers
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    print("✅ 模板详情获取成功!")
                    template = result['data']
                    print(f"模板名称: {template['name']}")
                    print(f"配置信息: {json.dumps(template.get('config', {}), indent=2, ensure_ascii=False)}")
                    
                    # 验证配置是否正确保存
                    config = template.get('config', {})
                    if config and 'conditions' in config:
                        print("✅ 配置信息保存正确!")
                        return True
                    else:
                        print("❌ 配置信息未正确保存!")
                        return False
                else:
                    print(f"❌ 获取模板详情失败: {response.status}")
                    text = await response.text()
                    print(f"错误信息: {text}")
                    return False
        except Exception as e:
            print(f"❌ 获取模板详情请求失败: {e}")
            return False

async def update_template_config(token, template_id):
    """更新模板配置，测试更新功能"""
    update_data = {
        "name": "测试配置保存模板（已更新）",
        "description": "测试前端配置更新功能",
        "datasourceId": 8,
        "dataResourceId": 3,
        "query": "SELECT * FROM cpc_agents WHERE status = :status AND created_at >= :start_date AND name LIKE :keyword",
        "tags": ["测试", "配置", "更新"],
        "config": {
            "conditions": [
                {
                    "name": "status",
                    "label": "状态",
                    "type": "select",
                    "required": True,
                    "options": [
                        {"label": "活跃", "value": "active"},
                        {"label": "非活跃", "value": "inactive"},
                        {"label": "已删除", "value": "deleted"}
                    ],
                    "defaultValue": "active"
                },
                {
                    "name": "start_date",
                    "label": "开始日期",
                    "type": "date",
                    "required": True,
                    "defaultValue": "2024-01-01"
                },
                {
                    "name": "keyword",
                    "label": "关键词",
                    "type": "text",
                    "required": False,
                    "placeholder": "请输入搜索关键词"
                }
            ]
        },
        "isTemplate": True
    }
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    async with aiohttp.ClientSession() as session:
        try:
            async with session.put(
                f"{BASE_URL}/api/v1/sql/templates/{template_id}",
                json=update_data,
                headers=headers
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    print("✅ 模板更新成功!")
                    print(f"模板名称: {result['data']['name']}")
                    return True
                else:
                    print(f"❌ 模板更新失败: {response.status}")
                    text = await response.text()
                    print(f"错误信息: {text}")
                    return False
        except Exception as e:
            print(f"❌ 更新模板请求失败: {e}")
            return False

async def main():
    """主测试函数"""
    print("🚀 开始测试配置保存功能...")
    print()
    
    # 获取认证token
    print("🔑 获取认证token...")
    token = await get_auth_token()
    if not token:
        print("❌ 无法获取认证token，测试终止")
        return
    print(f"✅ 使用token: {token[:20]}...")
    print()
    
    # 创建带配置的模板
    print("1. 创建带配置的SQL模板...")
    template_id = await create_template_with_config(token)
    if not template_id:
        print("❌ 模板创建失败，测试终止")
        return
    print()
    
    # 获取模板详情，验证配置保存
    print("2. 验证配置是否正确保存...")
    config_saved = await get_template_detail(token, template_id)
    print()
    
    # 更新模板配置
    print("3. 更新模板配置...")
    update_success = await update_template_config(token, template_id)
    print()
    
    # 再次验证配置保存
    print("4. 验证更新后的配置...")
    config_updated = await get_template_detail(token, template_id)
    print()
    
    # 测试结果总结
    print("📊 测试结果总结:")
    print(f"✅ 模板创建: {'成功' if template_id else '失败'}")
    print(f"✅ 配置保存: {'成功' if config_saved else '失败'}")
    print(f"✅ 模板更新: {'成功' if update_success else '失败'}")
    print(f"✅ 配置更新: {'成功' if config_updated else '失败'}")
    
    if template_id and config_saved and update_success and config_updated:
        print("\n🎉 所有测试通过！配置保存功能正常工作！")
    else:
        print("\n❌ 部分测试失败，需要进一步检查！")

if __name__ == "__main__":
    asyncio.run(main())