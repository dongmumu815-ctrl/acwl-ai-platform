#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试配置驱动的SQL模板功能
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
                    return None
        except Exception as e:
            print(f"❌ 登录异常: {str(e)}")
            return None

async def create_template_with_config():
    """创建带有配置的SQL模板"""
    
    # 模板配置示例
    template_config = {
        "conditions": [
            {
                "name": "start_date",
                "label": "开始日期",
                "type": "date",
                "required": True,
                "placeholder": "请选择开始日期",
                "defaultValue": "2024-01-01"
            },
            {
                "name": "end_date", 
                "label": "结束日期",
                "type": "date",
                "required": True,
                "placeholder": "请选择结束日期",
                "defaultValue": "2024-12-31"
            },
            {
                "name": "status",
                "label": "状态",
                "type": "select",
                "required": False,
                "placeholder": "请选择状态",
                "options": [
                    {"label": "活跃", "value": "active"},
                    {"label": "非活跃", "value": "inactive"},
                    {"label": "已删除", "value": "deleted"}
                ],
                "defaultValue": "active"
            },
            {
                "name": "min_amount",
                "label": "最小金额",
                "type": "number",
                "required": False,
                "placeholder": "请输入最小金额",
                "defaultValue": 0
            },
            {
                "name": "keyword",
                "label": "关键词",
                "type": "text",
                "required": False,
                "placeholder": "请输入搜索关键词"
            }
        ]
    }
    
    # 模板数据
    template_data = {
        "name": "用户数据查询模板（配置驱动）",
        "description": "这是一个支持配置驱动条件的用户数据查询模板，演示了必填和可选条件的使用",
        "datasourceId": 1,  # 需要替换为实际的数据源ID
        "dataResourceId": 1,  # 需要替换为实际的数据资源ID
        "query": """SELECT 
    id,
    username,
    email,
    status,
    created_at,
    last_login_at,
    total_amount
FROM users 
WHERE created_at >= '{start_date}' 
    AND created_at <= '{end_date}'
    AND ({status} IS NULL OR status = '{status}')
    AND ({min_amount} IS NULL OR total_amount >= {min_amount})
    AND ({keyword} IS NULL OR username LIKE '%{keyword}%' OR email LIKE '%{keyword}%')
ORDER BY created_at DESC
LIMIT 100""",
        "tags": ["用户查询", "配置驱动", "测试模板"],
        "config": template_config,
        "is_template": True
    }
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {TEST_USER_TOKEN}"
    }
    
    async with aiohttp.ClientSession() as session:
        try:
            # 创建模板
            async with session.post(
                f"{BASE_URL}/api/v1/sql/templates",
                json=template_data,
                headers=headers
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    print("✅ 模板创建成功!")
                    print(f"模板ID: {result.get('data', {}).get('id')}")
                    print(f"模板名称: {result.get('data', {}).get('name')}")
                    print(f"配置信息: {json.dumps(template_config, indent=2, ensure_ascii=False)}")
                    return result.get('data', {}).get('id')
                else:
                    error_text = await response.text()
                    print(f"❌ 模板创建失败: {response.status}")
                    print(f"错误信息: {error_text}")
                    return None
                    
        except Exception as e:
            print(f"❌ 请求异常: {str(e)}")
            return None

async def test_template_list():
    """测试模板列表API"""
    headers = {
        "Authorization": f"Bearer {TEST_USER_TOKEN}"
    }
    
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(
                f"{BASE_URL}/api/v1/sql/templates?datasource_id=1",
                headers=headers
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    print("✅ 模板列表获取成功!")
                    templates = result.get('data', [])
                    print(f"模板数量: {len(templates)}")
                    
                    # 查找带配置的模板
                    config_templates = [t for t in templates if t.get('config')]
                    print(f"带配置的模板数量: {len(config_templates)}")
                    
                    for template in config_templates:
                        print(f"- {template.get('name')} (ID: {template.get('id')})")
                        if template.get('config'):
                            conditions = template['config'].get('conditions', [])
                            print(f"  条件数量: {len(conditions)}")
                            required_count = len([c for c in conditions if c.get('required')])
                            optional_count = len([c for c in conditions if not c.get('required')])
                            print(f"  必填条件: {required_count}, 可选条件: {optional_count}")
                    
                else:
                    error_text = await response.text()
                    print(f"❌ 模板列表获取失败: {response.status}")
                    print(f"错误信息: {error_text}")
                    
        except Exception as e:
            print(f"❌ 请求异常: {str(e)}")

# 全局token变量
TEST_USER_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI1IiwiZXhwIjoxNzU4MzcwNDY2fQ.fEgVEQuWeGs1CYpEs7J2TZNXuiNE8FmPIbMFplqTIcI"

async def main():
    """主函数"""
    print("🚀 开始测试配置驱动的SQL模板功能...")
    print()
    
    # 动态获取认证token
    print("🔑 获取认证token...")
    token = await get_auth_token()
    if not token:
        print("❌ 无法获取认证token，测试终止")
        return
    print(f"✅ 使用token: {token[:20]}...")
    
    # 更新全局token变量
    global TEST_USER_TOKEN
    TEST_USER_TOKEN = token
    
    print("1. 创建带配置的SQL模板...")
    template_id = await create_template_with_config()
    
    print("\n2. 获取模板列表...")
    await test_template_list()
    
    print("\n✅ 测试完成!")
    print("\n📝 接下来可以在前端页面测试:")
    print("1. 打开 http://localhost:3005")
    print("2. 进入SQL查询构建器页面")
    print("3. 选择刚创建的模板")
    print("4. 查看是否显示了配置驱动的条件输入界面")

if __name__ == "__main__":
    asyncio.run(main())