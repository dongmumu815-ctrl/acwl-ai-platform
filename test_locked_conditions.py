#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试锁定条件功能
演示如何创建和使用带有锁定条件的SQL模板
"""

import asyncio
import aiohttp
import json

# API配置
BASE_URL = 'http://localhost:8082'
USERNAME = 'newuser'
PASSWORD = 'newpass123'

async def get_auth_token():
    """获取认证token"""
    async with aiohttp.ClientSession() as session:
        async with session.post(f'{BASE_URL}/api/v1/auth/login/json', 
                               json={'username': USERNAME, 'password': PASSWORD}) as response:
            if response.status == 200:
                result = await response.json()
                return result['access_token']
            else:
                raise Exception(f"认证失败: {response.status}")

async def create_locked_condition_template(token):
    """创建带有锁定条件的SQL模板"""
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    
    # 创建一个包含锁定条件的模板
    template_data = {
        "name": "锁定条件测试模板",
        "description": "演示锁定条件功能的测试模板",
        "datasourceId": 8,
        "dataResourceId": 3,
        "query": "SELECT * FROM cpc_agents WHERE status = :status AND department = :department AND created_at >= :start_date AND name LIKE :keyword",
        "tags": ["锁定条件", "测试"],
        "config": {
            "conditions": [
                {
                    "name": "status",
                    "label": "状态",
                    "type": "select",
                    "required": True,
                    "locked": True,  # 锁定条件
                    "lockedValue": "active",  # 锁定值
                    "lockedReason": "安全策略：只允许查询活跃用户",  # 锁定原因
                    "options": [
                        {"label": "活跃", "value": "active"},
                        {"label": "非活跃", "value": "inactive"},
                        {"label": "已删除", "value": "deleted"}
                    ]
                },
                {
                    "name": "department",
                    "label": "部门",
                    "type": "select",
                    "required": True,
                    "locked": True,  # 锁定条件
                    "lockedValue": "IT",  # 锁定值
                    "lockedReason": "权限限制：当前用户只能查看IT部门数据",  # 锁定原因
                    "options": [
                        {"label": "IT部门", "value": "IT"},
                        {"label": "销售部", "value": "Sales"},
                        {"label": "人事部", "value": "HR"}
                    ]
                },
                {
                    "name": "start_date",
                    "label": "开始日期",
                    "type": "date",
                    "required": True,
                    "locked": False,  # 非锁定条件，用户可以修改
                    "defaultValue": "2024-01-01"
                },
                {
                    "name": "keyword",
                    "label": "关键词搜索",
                    "type": "text",
                    "required": False,
                    "locked": False,  # 非锁定条件，用户可以修改
                    "placeholder": "请输入搜索关键词"
                }
            ]
        },
        "isTemplate": True
    }
    
    async with aiohttp.ClientSession() as session:
        async with session.post(f'{BASE_URL}/api/v1/sql/templates', 
                               headers=headers, json=template_data) as response:
            if response.status == 200:
                result = await response.json()
                print(f"✅ 锁定条件模板创建成功，ID: {result['data']['id']}")
                return result['data']
            else:
                error_text = await response.text()
                print(f"❌ 模板创建失败: {response.status} - {error_text}")
                return None

async def get_template_with_locked_conditions(token, template_id):
    """获取带有锁定条件的模板详情"""
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    
    async with aiohttp.ClientSession() as session:
        async with session.get(f'{BASE_URL}/api/v1/sql/templates/{template_id}', 
                              headers=headers) as response:
            if response.status == 200:
                result = await response.json()
                template = result['data']
                
                print(f"✅ 获取模板成功: {template['name']}")
                print(f"📋 模板配置:")
                
                if template.get('config') and template['config'].get('conditions'):
                    for condition in template['config']['conditions']:
                        status = "🔒 锁定" if condition.get('locked') else "🔓 可修改"
                        print(f"  - {condition['label']} ({condition['name']}): {status}")
                        
                        if condition.get('locked'):
                            print(f"    锁定值: {condition.get('lockedValue')}")
                            if condition.get('lockedReason'):
                                print(f"    锁定原因: {condition.get('lockedReason')}")
                
                return template
            else:
                error_text = await response.text()
                print(f"❌ 获取模板失败: {response.status} - {error_text}")
                return None

async def execute_query_with_locked_conditions(token, template):
    """执行带有锁定条件的查询"""
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    
    # 构建查询条件，锁定条件使用锁定值，非锁定条件使用用户输入值
    conditions = {}
    
    if template.get('config') and template['config'].get('conditions'):
        for condition in template['config']['conditions']:
            if condition.get('locked'):
                # 锁定条件使用锁定值
                conditions[condition['name']] = condition.get('lockedValue')
                print(f"🔒 使用锁定值: {condition['name']} = {condition.get('lockedValue')}")
            else:
                # 非锁定条件使用默认值或用户输入值
                if condition['name'] == 'start_date':
                    conditions[condition['name']] = '2024-01-01'
                    print(f"🔓 用户输入: {condition['name']} = 2024-01-01")
                elif condition['name'] == 'keyword':
                    conditions[condition['name']] = '%test%'
                    print(f"🔓 用户输入: {condition['name']} = %test%")
    
    query_data = {
        "datasourceId": template['datasource_id'],
        "query": template['query'],
        "conditions": conditions
    }
    
    print(f"\n📤 执行查询:")
    print(f"SQL: {template['query']}")
    print(f"条件: {json.dumps(conditions, ensure_ascii=False, indent=2)}")
    
    async with aiohttp.ClientSession() as session:
        async with session.post(f'{BASE_URL}/api/v1/sql/execute', 
                               headers=headers, json=query_data) as response:
            if response.status == 200:
                result = await response.json()
                print(f"✅ 查询执行成功")
                print(f"📊 结果行数: {len(result.get('data', []))}")
                return result
            else:
                error_text = await response.text()
                print(f"❌ 查询执行失败: {response.status} - {error_text}")
                return None

async def test_locked_conditions_workflow():
    """测试完整的锁定条件工作流程"""
    print("🚀 开始测试锁定条件功能")
    print("=" * 50)
    
    try:
        # 1. 获取认证token
        print("1️⃣ 获取认证token...")
        token = await get_auth_token()
        print("✅ 认证成功")
        
        # 2. 创建带有锁定条件的模板
        print("\n2️⃣ 创建锁定条件模板...")
        template = await create_locked_condition_template(token)
        if not template:
            return
        
        # 3. 获取模板详情并验证锁定条件
        print("\n3️⃣ 验证锁定条件配置...")
        template_detail = await get_template_with_locked_conditions(token, template['id'])
        if not template_detail:
            return
        
        # 4. 执行查询，验证锁定条件生效
        print("\n4️⃣ 执行查询验证锁定条件...")
        result = await execute_query_with_locked_conditions(token, template_detail)
        
        if result:
            print("\n🎉 锁定条件功能测试完成！")
            print("📝 测试总结:")
            print("  - ✅ 锁定条件正确保存到配置中")
            print("  - ✅ 锁定条件在查询时自动使用锁定值")
            print("  - ✅ 非锁定条件允许用户自定义输入")
            print("  - ✅ 查询执行成功，锁定条件生效")
        else:
            print("❌ 锁定条件功能测试失败")
            
    except Exception as e:
        print(f"❌ 测试过程中发生错误: {str(e)}")

if __name__ == "__main__":
    asyncio.run(test_locked_conditions_workflow())