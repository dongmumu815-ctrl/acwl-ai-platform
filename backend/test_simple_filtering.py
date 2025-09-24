#!/usr/bin/env python3
"""
测试简单的参数过滤方案
验证只有非空参数会被包含在SQL渲染中
"""

from jinja2 import Template

def test_simple_parameter_filtering():
    """
    测试简单的参数过滤逻辑
    """
    print("🧪 测试简单的参数过滤方案")
    print("=" * 50)
    
    # 模拟SQL模板（原始格式）
    sql_template = """SELECT name, description, parent_id, id 
FROM cpc_agents 
WHERE node_type = 'agent'
{% if description %} AND description = '{{ description }}'{% endif %}
{% if name %} AND name = '{{ name }}'{% endif %}
ORDER BY id DESC LIMIT 1000"""
    
    print(f"📝 SQL模板:\n{sql_template}\n")
    
    # 测试场景
    test_cases = [
        {
            "name": "空参数测试",
            "params": {"description": "", "name": ""}
        },
        {
            "name": "只有description参数",
            "params": {"description": "test description", "name": ""}
        },
        {
            "name": "只有name参数", 
            "params": {"description": "", "name": "test name"}
        },
        {
            "name": "两个参数都有值",
            "params": {"description": "test description", "name": "test name"}
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"🔍 测试场景 {i}: {test_case['name']}")
        print(f"原始参数: {test_case['params']}")
        
        # 简单的参数过滤：只保留非空字符串的参数
        filtered_params = {}
        for key, value in test_case['params'].items():
            if value is not None and value != "":
                filtered_params[key] = value
        
        print(f"过滤后参数: {filtered_params}")
        
        # 使用Jinja2模板引擎渲染SQL
        jinja_template = Template(sql_template)
        rendered_sql = jinja_template.render(**filtered_params)
        
        # 清理SQL格式
        clean_sql = ' '.join(rendered_sql.split())
        print(f"生成的SQL: {clean_sql}")
        print("-" * 40)

if __name__ == "__main__":
    test_simple_parameter_filtering()