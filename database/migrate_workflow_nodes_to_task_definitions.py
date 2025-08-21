#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据迁移脚本：将 acwl_workflow_nodes 表数据迁移到 acwl_task_definitions 表

该脚本将工作流节点数据迁移到统一的任务定义表中，实现节点定义的统一管理。
"""

import mysql.connector
import json
from datetime import datetime
from typing import Dict, Any, Optional

# 数据库配置
DB_CONFIG = {
    'host': 'localhost',
    'port': 3306,
    'user': 'root',
    'password': '2wsx1QAZaczt',
    'database': 'acwl-ai-data',
    'charset': 'utf8mb4'
}

# 节点类型映射：从 workflow_nodes 到 task_definitions
NODE_TYPE_MAPPING = {
    'START': 'custom',
    'END': 'custom', 
    'PYTHON_CODE': 'custom',
    'SQL_QUERY': 'data_analysis',
    'CONDITION': 'custom',
    'LOOP': 'custom',
    'PARALLEL': 'custom',
    'MERGE': 'custom',
    'DATA_TRANSFORM': 'etl',
    'API_CALL': 'custom',
    'FILE_OPERATION': 'custom',
    'EMAIL_SEND': 'custom',
    'DELAY': 'custom',
    'SUBPROCESS': 'custom',
    'CUSTOM': 'custom'
}

# 错误处理映射
ERROR_HANDLING_MAPPING = {
    'FAIL': 'normal',
    'SKIP': 'low', 
    'RETRY': 'high',
    'CUSTOM': 'normal'
}

def get_database_connection():
    """获取数据库连接"""
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        return connection
    except mysql.connector.Error as e:
        print(f"数据库连接失败: {e}")
        return None

def get_workflow_nodes_data(connection) -> list:
    """获取所有工作流节点数据"""
    cursor = connection.cursor(dictionary=True)
    query = """
    SELECT 
        id, workflow_id, node_name, display_name, description, node_type,
        node_config, input_parameters, output_parameters, position_x, position_y,
        executor_group, timeout_seconds, max_retry_count, retry_interval_seconds,
        error_handling, is_optional, created_at, updated_at
    FROM acwl_workflow_nodes
    ORDER BY id
    """
    
    cursor.execute(query)
    nodes = cursor.fetchall()
    cursor.close()
    return nodes

def map_node_to_task_definition(node: Dict[str, Any]) -> Dict[str, Any]:
    """将工作流节点数据映射为任务定义数据"""
    # 基础字段映射
    task_def = {
        'name': node['node_name'],
        'display_name': node['display_name'],
        'description': node['description'],
        'task_type': NODE_TYPE_MAPPING.get(node['node_type'], 'custom'),
        'task_category': f"workflow_{node['workflow_id']}",  # 使用工作流ID作为分类
        'executor_group': node['executor_group'] or 'default',
        'priority': ERROR_HANDLING_MAPPING.get(node['error_handling'], 'normal'),
        'timeout_seconds': node['timeout_seconds'] or 3600,
        'max_retry_count': node['max_retry_count'] or 3,
        'retry_interval_seconds': node['retry_interval_seconds'] or 60,
        'project_id': None,  # 需要根据实际情况设置
        'created_by': 5,  # admin用户ID
        'is_active': 1,
        'version': 1
    }
    
    # 构建任务配置
    task_config = {
        'original_node_type': node['node_type'],
        'workflow_id': node['workflow_id'],
        'position': {
            'x': node['position_x'],
            'y': node['position_y']
        },
        'is_optional': bool(node['is_optional']),
        'error_handling': node['error_handling']
    }
    
    # 合并原始节点配置
    if node['node_config']:
        if isinstance(node['node_config'], str):
            original_config = json.loads(node['node_config'])
        else:
            original_config = node['node_config']
        task_config.update(original_config)
    
    task_def['task_config'] = json.dumps(task_config, ensure_ascii=False)
    
    # 设置资源需求
    resource_requirements = {
        'cpu': 1,
        'memory': '512MB',
        'timeout_seconds': task_def['timeout_seconds']
    }
    task_def['resource_requirements'] = json.dumps(resource_requirements, ensure_ascii=False)
    
    # 设置环境变量
    environment_variables = {
        'WORKFLOW_ID': str(node['workflow_id']),
        'NODE_TYPE': node['node_type']
    }
    task_def['environment_variables'] = json.dumps(environment_variables, ensure_ascii=False)
    
    # 设置依赖关系
    dependencies = {
        'input_parameters': node['input_parameters'] or {},
        'output_parameters': node['output_parameters'] or {}
    }
    task_def['dependencies'] = json.dumps(dependencies, ensure_ascii=False)
    
    # 根据节点类型设置命令模板和脚本内容
    if node['node_type'] == 'PYTHON_CODE':
        task_def['command_template'] = 'python -c "{script_content}"'
        task_def['script_content'] = '# Python代码节点\nprint("执行Python代码")'
    elif node['node_type'] == 'SQL_QUERY':
        task_def['command_template'] = 'mysql -h {host} -u {user} -p{password} -e "{sql_query}"'
        task_def['script_content'] = '-- SQL查询节点\nSELECT 1;'
    else:
        task_def['command_template'] = 'echo "执行{node_type}节点"'.format(node_type=node['node_type'])
        task_def['script_content'] = f'# {node["node_type"]}节点\necho "节点执行完成"'
    
    return task_def

def insert_task_definition(connection, task_def: Dict[str, Any]) -> bool:
    """插入任务定义到数据库"""
    cursor = connection.cursor()
    
    insert_query = """
    INSERT INTO acwl_task_definitions (
        name, display_name, description, task_type, task_category,
        executor_group, priority, timeout_seconds, max_retry_count,
        retry_interval_seconds, task_config, resource_requirements,
        environment_variables, command_template, script_content,
        dependencies, project_id, created_by, is_active, version
    ) VALUES (
        %(name)s, %(display_name)s, %(description)s, %(task_type)s, %(task_category)s,
        %(executor_group)s, %(priority)s, %(timeout_seconds)s, %(max_retry_count)s,
        %(retry_interval_seconds)s, %(task_config)s, %(resource_requirements)s,
        %(environment_variables)s, %(command_template)s, %(script_content)s,
        %(dependencies)s, %(project_id)s, %(created_by)s, %(is_active)s, %(version)s
    )
    """
    
    try:
        cursor.execute(insert_query, task_def)
        cursor.close()
        return True
    except mysql.connector.Error as e:
        print(f"插入任务定义失败: {e}")
        print(f"任务定义数据: {task_def}")
        cursor.close()
        return False

def migrate_workflow_nodes():
    """执行数据迁移"""
    print("开始迁移工作流节点数据到任务定义表...")
    
    # 获取数据库连接
    connection = get_database_connection()
    if not connection:
        return False
    
    try:
        # 获取工作流节点数据
        print("正在获取工作流节点数据...")
        nodes = get_workflow_nodes_data(connection)
        print(f"找到 {len(nodes)} 个工作流节点")
        
        # 设置自动提交为False
        connection.autocommit = False
        
        success_count = 0
        failed_count = 0
        
        # 逐个迁移节点
        for i, node in enumerate(nodes, 1):
            print(f"正在迁移节点 {i}/{len(nodes)}: {node['node_name']}")
            
            # 映射节点数据
            task_def = map_node_to_task_definition(node)
            
            # 插入任务定义
            if insert_task_definition(connection, task_def):
                success_count += 1
                print(f"  ✅ 成功迁移节点: {node['node_name']}")
            else:
                failed_count += 1
                print(f"  ❌ 迁移失败节点: {node['node_name']}")
        
        # 提交事务
        if failed_count == 0:
            connection.commit()
            print(f"\n🎉 数据迁移完成！")
            print(f"成功迁移: {success_count} 个节点")
            print(f"失败: {failed_count} 个节点")
        else:
            connection.rollback()
            print(f"\n❌ 数据迁移失败，已回滚事务")
            print(f"成功: {success_count} 个节点")
            print(f"失败: {failed_count} 个节点")
            return False
            
    except Exception as e:
        connection.rollback()
        print(f"迁移过程中发生错误: {e}")
        return False
    finally:
        connection.close()
    
    return True

def verify_migration():
    """验证迁移结果"""
    print("\n正在验证迁移结果...")
    
    connection = get_database_connection()
    if not connection:
        return False
    
    try:
        cursor = connection.cursor()
        
        # 检查任务定义表数据量
        cursor.execute("SELECT COUNT(*) FROM acwl_task_definitions")
        task_count = cursor.fetchone()[0]
        
        # 检查工作流节点表数据量
        cursor.execute("SELECT COUNT(*) FROM acwl_workflow_nodes")
        node_count = cursor.fetchone()[0]
        
        print(f"工作流节点数量: {node_count}")
        print(f"任务定义数量: {task_count}")
        
        if task_count == node_count:
            print("✅ 数据迁移验证成功！")
            return True
        else:
            print("❌ 数据迁移验证失败，数量不匹配")
            return False
            
    except Exception as e:
        print(f"验证过程中发生错误: {e}")
        return False
    finally:
        connection.close()

if __name__ == "__main__":
    print("=" * 60)
    print("工作流节点数据迁移脚本")
    print("=" * 60)
    
    # 执行迁移
    if migrate_workflow_nodes():
        # 验证迁移结果
        verify_migration()
    else:
        print("数据迁移失败")
    
    print("\n迁移脚本执行完成")