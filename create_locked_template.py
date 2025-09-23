#!/usr/bin/env python3
"""
创建带有锁定条件的SQL模板，用于在SQLQueryBuilder组件中测试
"""

import requests
import json

# API配置
BASE_URL = "http://localhost:8082"
LOGIN_URL = f"{BASE_URL}/api/v1/auth/login/json"
TEMPLATE_URL = f"{BASE_URL}/api/v1/sql/templates"

def get_auth_token():
    """获取认证token"""
    login_data = {
        "email": "admin@acwl.ai",
        "password": "password"
    }
    
    response = requests.post(LOGIN_URL, json=login_data)
    if response.status_code == 200:
        result = response.json()
        return result.get("access_token")
    else:
        print(f"登录失败: {response.status_code} - {response.text}")
        return None

def create_locked_template(token):
    """创建带有锁定条件的SQL模板"""
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    # 模板配置，包含锁定条件
    template_data = {
        "name": "员工查询模板（带锁定条件）",
        "description": "用于测试锁定条件功能的员工查询模板",
        "query": "SELECT * FROM employees WHERE department = :department AND status = :status AND hire_date >= :start_date AND name LIKE :keyword",
        "datasourceId": 1,
        "tags": ["测试", "锁定条件"],
        "is_template": True,
        "config": {
            "conditions": [
                {
                    "name": "department",
                    "label": "部门",
                    "type": "select",
                    "required": True,
                    "locked": True,
                    "lockedValue": "IT",
                    "lockedReason": "当前用户只能查询IT部门数据",
                    "options": [
                        {"label": "IT部门", "value": "IT"},
                        {"label": "HR部门", "value": "HR"},
                        {"label": "财务部门", "value": "Finance"}
                    ]
                },
                {
                    "name": "status",
                    "label": "员工状态",
                    "type": "select",
                    "required": True,
                    "locked": True,
                    "lockedValue": "active",
                    "lockedReason": "只能查询在职员工",
                    "options": [
                        {"label": "在职", "value": "active"},
                        {"label": "离职", "value": "inactive"}
                    ]
                },
                {
                    "name": "start_date",
                    "label": "入职开始日期",
                    "type": "date",
                    "required": True,
                    "locked": False,
                    "placeholder": "请选择入职开始日期"
                },
                {
                    "name": "keyword",
                    "label": "姓名关键词",
                    "type": "text",
                    "required": False,
                    "locked": False,
                    "placeholder": "请输入姓名关键词（可选）"
                }
            ]
        }
    }
    
    response = requests.post(TEMPLATE_URL, json=template_data, headers=headers)
    
    if response.status_code == 200:
        result = response.json()
        if result.get("success"):
            print(f"✅ 成功创建带锁定条件的模板")
            template_data = result.get('data', {})
            print(f"   模板ID: {template_data.get('id')}")
            print(f"   模板名称: {template_data.get('name')}")
            print(f"   锁定条件:")
            
            config = template_data.get('config', {})
            conditions = config.get('conditions', [])
            for condition in conditions:
                if condition.get('locked'):
                    print(f"     - {condition.get('label')}: {condition.get('lockedValue')} (原因: {condition.get('lockedReason')})")
            
            return template_data
        else:
            print(f"❌ 创建模板失败: {result.get('message', '未知错误')}")
            return None
    else:
        print(f"❌ 创建模板失败: {response.status_code}")
        print(f"   错误信息: {response.text}")
        return None

def main():
    print("🔐 创建带锁定条件的SQL模板...")
    
    # 获取认证token
    token = get_auth_token()
    if not token:
        print("❌ 无法获取认证token")
        return
    
    print("✅ 认证成功")
    
    # 创建带锁定条件的模板
    template = create_locked_template(token)
    if template:
        print("\n🎉 模板创建完成！现在可以在SQLQueryBuilder组件中测试锁定条件功能了")
        print(f"   请在浏览器中访问前端应用，选择数据源ID为1的数据源")
        print(f"   然后选择模板 '{template.get('name')}' 来测试锁定条件")
    else:
        print("❌ 模板创建失败")

if __name__ == "__main__":
    main()