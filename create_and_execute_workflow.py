#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
创建并执行一个包含SQL任务和Python任务的工作流

该脚本将：
1. 创建一个新的工作流
2. 添加开始节点
3. 添加SQL查询任务节点
4. 添加Python代码执行任务节点
5. 添加结束节点
6. 创建节点之间的连接
7. 执行工作流
"""

import asyncio
import json
import aiohttp
from datetime import datetime
from typing import Dict, Any

# API基础配置
API_BASE_URL = "http://localhost:8082/api/v1"
HEADERS = {
    "Content-Type": "application/json",
    "Accept": "application/json"
}

# 测试用户凭据（实际使用时应该从环境变量或配置文件读取）
TEST_USER_CREDENTIALS = {
    "username": "admin",
    "password": "password"
}

class WorkflowManager:
    """工作流管理器"""
    
    def __init__(self):
        self.session = None
        self.auth_token = None
        
    async def __aenter__(self):
        """异步上下文管理器入口"""
        self.session = aiohttp.ClientSession()
        await self.authenticate()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        if self.session:
            await self.session.close()
            
    async def authenticate(self):
        """用户认证获取token"""
        try:
            # 尝试登录获取token
            login_url = f"{API_BASE_URL}/auth/login"
            async with self.session.post(login_url, data=TEST_USER_CREDENTIALS) as response:
                if response.status == 200:
                    data = await response.json()
                    self.auth_token = data.get("access_token")
                    # 更新请求头
                    HEADERS["Authorization"] = f"Bearer {self.auth_token}"
                    print("✅ 用户认证成功")
                else:
                    print(f"❌ 用户认证失败: {response.status}")
                    # 如果认证失败，继续尝试不带认证的请求
        except Exception as e:
            print(f"⚠️ 认证过程出现异常，将尝试不带认证的请求: {e}")
            
    async def create_workflow(self) -> Dict[str, Any]:
        """创建工作流"""
        workflow_data = {
            "name": f"demo_sql_python_workflow_{int(datetime.now().timestamp())}",
            "display_name": "演示SQL和Python任务工作流",
            "description": "这是一个演示工作流，包含SQL查询任务和Python代码执行任务",
            "workflow_category": "demo",
            "workflow_version": "1.0.0",
            "workflow_status": "active",
            "timeout_seconds": 3600,
            "max_retry_count": 1,
            "input_parameters": {
                "database_name": {
                    "type": "string",
                    "description": "数据库名称",
                    "default": "test_db"
                },
                "table_name": {
                    "type": "string", 
                    "description": "表名称",
                    "default": "test_table"
                }
            },
            "output_parameters": {
                "sql_result": {
                    "type": "object",
                    "description": "SQL查询结果"
                },
                "python_result": {
                    "type": "object",
                    "description": "Python处理结果"
                }
            }
        }
        
        url = f"{API_BASE_URL}/workflows/"
        async with self.session.post(url, json=workflow_data, headers=HEADERS) as response:
            if response.status == 201:
                workflow = await response.json()
                print(f"✅ 工作流创建成功: {workflow['name']} (ID: {workflow['id']})")
                return workflow
            else:
                error_text = await response.text()
                raise Exception(f"创建工作流失败: {response.status} - {error_text}")
                
    async def create_start_node(self, workflow_id: int) -> Dict[str, Any]:
        """创建开始节点"""
        node_data = {
            "workflow_id": workflow_id,
            "node_name": "start_node",
            "display_name": "开始",
            "description": "工作流开始节点",
            "node_type": "start",
            "node_config": {},
            "position_x": 100,
            "position_y": 100,
            "timeout_seconds": 60,
            "max_retry_count": 0,
            "error_handling": "fail"
        }
        
        url = f"{API_BASE_URL}/workflows/{workflow_id}/nodes"
        async with self.session.post(url, json=node_data, headers=HEADERS) as response:
            if response.status == 201:
                node = await response.json()
                print(f"✅ 开始节点创建成功: {node['node_name']} (ID: {node['id']})")
                return node
            else:
                error_text = await response.text()
                raise Exception(f"创建开始节点失败: {response.status} - {error_text}")
                
    async def create_sql_node(self, workflow_id: int) -> Dict[str, Any]:
        """创建SQL查询任务节点"""
        node_data = {
            "workflow_id": workflow_id,
            "node_name": "sql_query_node",
            "display_name": "SQL查询任务",
            "description": "执行SQL查询获取数据",
            "node_type": "sql_query",
            "node_config": {
                "sql_query": "SELECT COUNT(*) as total_count, MAX(created_at) as latest_time FROM ${table_name} WHERE created_at >= DATE_SUB(NOW(), INTERVAL 1 DAY)",
                "database_connection": "default",
                "timeout_seconds": 300,
                "fetch_size": 1000,
                "parameters": {
                    "table_name": "${input.table_name}"
                }
            },
            "input_parameters": {
                "table_name": {
                    "type": "string",
                    "description": "要查询的表名"
                }
            },
            "output_parameters": {
                "query_result": {
                    "type": "object",
                    "description": "SQL查询结果"
                },
                "row_count": {
                    "type": "integer",
                    "description": "返回的行数"
                }
            },
            "position_x": 300,
            "position_y": 100,
            "timeout_seconds": 600,
            "max_retry_count": 2,
            "error_handling": "retry"
        }
        
        url = f"{API_BASE_URL}/workflows/{workflow_id}/nodes"
        async with self.session.post(url, json=node_data, headers=HEADERS) as response:
            if response.status == 201:
                node = await response.json()
                print(f"✅ SQL查询节点创建成功: {node['node_name']} (ID: {node['id']})")
                return node
            else:
                error_text = await response.text()
                raise Exception(f"创建SQL查询节点失败: {response.status} - {error_text}")
                
    async def create_python_node(self, workflow_id: int) -> Dict[str, Any]:
        """创建Python代码执行任务节点"""
        python_code = '''
# Python数据处理任务
import json
from datetime import datetime

def process_sql_result(sql_result, input_data):
    """
    处理SQL查询结果
    
    Args:
        sql_result: SQL查询返回的结果
        input_data: 工作流输入数据
        
    Returns:
        dict: 处理后的结果
    """
    print(f"开始处理SQL查询结果: {sql_result}")
    print(f"输入数据: {input_data}")
    
    # 模拟数据处理逻辑
    processed_data = {
        "processing_time": datetime.now().isoformat(),
        "original_sql_result": sql_result,
        "input_parameters": input_data,
        "processed_metrics": {
            "total_records": sql_result.get("total_count", 0) if isinstance(sql_result, dict) else 0,
            "processing_status": "success",
            "data_quality_score": 0.95
        }
    }
    
    # 添加一些计算逻辑
    if isinstance(sql_result, dict) and "total_count" in sql_result:
        total_count = sql_result["total_count"]
        processed_data["analysis"] = {
            "is_high_volume": total_count > 1000,
            "volume_category": "high" if total_count > 1000 else "medium" if total_count > 100 else "low",
            "recommendation": "考虑数据分区" if total_count > 10000 else "当前数据量适中"
        }
    
    print(f"处理完成，结果: {processed_data}")
    return processed_data

# 主执行逻辑
if __name__ == "__main__":
    # 获取上一个节点的输出数据
    sql_result = context.get("sql_query_node", {}).get("output", {})
    input_data = context.get("input", {})
    
    # 处理数据
    result = process_sql_result(sql_result, input_data)
    
    # 设置输出
    output = {
        "processed_data": result,
        "execution_time": datetime.now().isoformat(),
        "status": "completed"
    }
'''
        
        node_data = {
            "workflow_id": workflow_id,
            "node_name": "python_process_node",
            "display_name": "Python数据处理任务",
            "description": "使用Python处理SQL查询结果",
            "node_type": "python_code",
            "node_config": {
                "python_code": python_code,
                "python_version": "3.8+",
                "required_packages": ["json", "datetime"],
                "execution_timeout": 300,
                "memory_limit_mb": 512,
                "environment_variables": {
                    "PYTHONPATH": "/app",
                    "LOG_LEVEL": "INFO"
                }
            },
            "input_parameters": {
                "sql_result": {
                    "type": "object",
                    "description": "来自SQL查询节点的结果",
                    "source": "sql_query_node.output.query_result"
                }
            },
            "output_parameters": {
                "processed_data": {
                    "type": "object",
                    "description": "处理后的数据"
                },
                "execution_time": {
                    "type": "string",
                    "description": "执行时间"
                },
                "status": {
                    "type": "string",
                    "description": "执行状态"
                }
            },
            "position_x": 500,
            "position_y": 100,
            "timeout_seconds": 600,
            "max_retry_count": 2,
            "error_handling": "retry"
        }
        
        url = f"{API_BASE_URL}/workflows/{workflow_id}/nodes"
        async with self.session.post(url, json=node_data, headers=HEADERS) as response:
            if response.status == 201:
                node = await response.json()
                print(f"✅ Python处理节点创建成功: {node['node_name']} (ID: {node['id']})")
                return node
            else:
                error_text = await response.text()
                raise Exception(f"创建Python处理节点失败: {response.status} - {error_text}")
                
    async def create_end_node(self, workflow_id: int) -> Dict[str, Any]:
        """创建结束节点"""
        node_data = {
            "workflow_id": workflow_id,
            "node_name": "end_node",
            "display_name": "结束",
            "description": "工作流结束节点",
            "node_type": "end",
            "node_config": {
                "collect_outputs": True,
                "final_output_mapping": {
                    "sql_result": "sql_query_node.output",
                    "python_result": "python_process_node.output"
                }
            },
            "position_x": 700,
            "position_y": 100,
            "timeout_seconds": 60,
            "max_retry_count": 0,
            "error_handling": "fail"
        }
        
        url = f"{API_BASE_URL}/workflows/{workflow_id}/nodes"
        async with self.session.post(url, json=node_data, headers=HEADERS) as response:
            if response.status == 201:
                node = await response.json()
                print(f"✅ 结束节点创建成功: {node['node_name']} (ID: {node['id']})")
                return node
            else:
                error_text = await response.text()
                raise Exception(f"创建结束节点失败: {response.status} - {error_text}")
                
    async def create_connection(self, workflow_id: int, source_node_id: int, target_node_id: int, connection_type: str = "success") -> Dict[str, Any]:
        """创建节点连接"""
        connection_data = {
            "workflow_id": workflow_id,
            "source_node_id": source_node_id,
            "target_node_id": target_node_id,
            "connection_type": connection_type,
            "connection_config": {}
        }
        
        url = f"{API_BASE_URL}/workflows/{workflow_id}/connections"
        async with self.session.post(url, json=connection_data, headers=HEADERS) as response:
            if response.status == 201:
                connection = await response.json()
                print(f"✅ 节点连接创建成功: {source_node_id} -> {target_node_id} (ID: {connection['id']})")
                return connection
            else:
                error_text = await response.text()
                raise Exception(f"创建节点连接失败: {response.status} - {error_text}")
                
    async def execute_workflow(self, workflow_id: int) -> Dict[str, Any]:
        """执行工作流"""
        execute_data = {
            "input_data": {
                "database_name": "acwl_ai_data",
                "table_name": "acwl_users"
            },
            "priority": "normal",
            "scheduled_time": datetime.now().isoformat()
        }
        
        url = f"{API_BASE_URL}/workflows/{workflow_id}/execute"
        async with self.session.post(url, json=execute_data, headers=HEADERS) as response:
            if response.status == 201:
                instance = await response.json()
                print(f"✅ 工作流执行启动成功: {instance['instance_id']} (ID: {instance['id']})")
                return instance
            else:
                error_text = await response.text()
                raise Exception(f"执行工作流失败: {response.status} - {error_text}")
                
    async def get_workflow_instance_status(self, instance_id: int) -> Dict[str, Any]:
        """获取工作流实例状态"""
        url = f"{API_BASE_URL}/workflows/instances/{instance_id}"
        async with self.session.get(url, headers=HEADERS) as response:
            if response.status == 200:
                instance = await response.json()
                return instance
            else:
                error_text = await response.text()
                raise Exception(f"获取工作流实例状态失败: {response.status} - {error_text}")
                
    async def monitor_workflow_execution(self, instance_id: int, max_wait_time: int = 300):
        """监控工作流执行状态"""
        print(f"🔍 开始监控工作流实例 {instance_id} 的执行状态...")
        
        start_time = datetime.now()
        instance = None  # 初始化变量
        
        while True:
            try:
                instance = await self.get_workflow_instance_status(instance_id)
                status = instance.get("status", "unknown")
                
                print(f"📊 当前状态: {status}")
                
                if status in ["success", "failed", "cancelled", "timeout"]:
                    print(f"🏁 工作流执行完成，最终状态: {status}")
                    if status == "success":
                        print("✅ 工作流执行成功！")
                    else:
                        print(f"❌ 工作流执行失败，状态: {status}")
                        if "error_message" in instance:
                            print(f"错误信息: {instance['error_message']}")
                    break
                    
                # 检查是否超时
                elapsed_time = (datetime.now() - start_time).total_seconds()
                if elapsed_time > max_wait_time:
                    print(f"⏰ 监控超时 ({max_wait_time}秒)，停止监控")
                    break
                    
                # 等待5秒后再次检查
                await asyncio.sleep(5)
                
            except Exception as e:
                print(f"❌ 监控过程中出现错误: {e}")
                break
                
        return instance

async def main():
    """主函数"""
    print("🚀 开始创建并执行包含SQL和Python任务的工作流...")
    
    try:
        async with WorkflowManager() as wm:
            # 1. 创建工作流
            print("\n📝 步骤1: 创建工作流")
            workflow = await wm.create_workflow()
            workflow_id = workflow["id"]
            
            # 2. 创建节点
            print("\n🔧 步骤2: 创建工作流节点")
            start_node = await wm.create_start_node(workflow_id)
            sql_node = await wm.create_sql_node(workflow_id)
            python_node = await wm.create_python_node(workflow_id)
            end_node = await wm.create_end_node(workflow_id)
            
            # 3. 创建连接
            print("\n🔗 步骤3: 创建节点连接")
            await wm.create_connection(workflow_id, start_node["id"], sql_node["id"])
            await wm.create_connection(workflow_id, sql_node["id"], python_node["id"])
            await wm.create_connection(workflow_id, python_node["id"], end_node["id"])
            
            # 4. 执行工作流
            print("\n▶️ 步骤4: 执行工作流")
            instance = await wm.execute_workflow(workflow_id)
            instance_id = instance["id"]
            
            # 5. 监控执行状态
            print("\n👀 步骤5: 监控执行状态")
            final_instance = await wm.monitor_workflow_execution(instance_id)
            
            # 6. 输出最终结果
            print("\n📋 执行结果摘要:")
            print(f"工作流ID: {workflow_id}")
            print(f"工作流名称: {workflow['name']}")
            print(f"实例ID: {instance_id}")
            print(f"最终状态: {final_instance.get('status', 'unknown')}")
            
            if final_instance.get("output_data"):
                print(f"输出数据: {json.dumps(final_instance['output_data'], indent=2, ensure_ascii=False)}")
                
    except Exception as e:
        print(f"❌ 执行过程中出现错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    # 运行主函数
    asyncio.run(main())