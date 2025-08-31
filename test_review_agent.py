#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试审读类型 Agent 的执行过程
"""

import sys
import os
import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

# 添加后端路径到 sys.path
backend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), 'backend'))
sys.path.insert(0, backend_path)

# 切换到后端目录
os.chdir(backend_path)

from app.core.database import AsyncSessionLocal
from app.models import Agent, ModelServiceConfig
from app.services.instruction_executor import InstructionExecutor

async def test_review_agent():
    """
    测试审读类型 Agent 的执行过程
    """
    print("测试审读类型 Agent...")
    
    # 创建数据库会话
    async with AsyncSessionLocal() as db:
        try:
            # 查询 Agent ID 为 32 的配置
            agent_query = select(Agent).options(
                selectinload(Agent.model_service_config)
            ).where(Agent.id == 32)
            agent_result = await db.execute(agent_query)
            agent = agent_result.scalar_one_or_none()
            
            if not agent:
                print("未找到 Agent ID 32")
                return
                
            print(f"找到 Agent: {agent.name}")
            print(f"Agent 类型: {agent.agent_type}")
            
            # 检查是否有指令集配置
            if hasattr(agent, 'instruction_set_id') and agent.instruction_set_id:
                instruction_set_id = agent.instruction_set_id
                print(f"指令集 ID: {instruction_set_id}")
            else:
                print("Agent 没有指令集配置，尝试查找默认指令集...")
                # 这里可能需要根据实际情况查找指令集
                instruction_set_id = 1  # 假设使用 ID 为 1 的指令集
                print(f"使用默认指令集 ID: {instruction_set_id}")
            
            # 创建指令执行器
            print("\n创建指令执行器...")
            executor = InstructionExecutor(db)
            
            # 执行指令集
            print("\n执行指令集...")
            test_message = "你好，这是一个测试消息"
            
            try:
                result = await executor.execute(
                    instruction_set_id=instruction_set_id,
                    input_text=test_message
                )
                
                print(f"\n指令执行结果类型: {type(result)}")
                print(f"指令执行结果: {result}")
                
                print(f"\n=== 原始执行结果 ===")
                print(f"result类型: {type(result)}")
                print(f"result内容: {result}")
                
                # 模拟agents.py中的审读结果处理逻辑
                execution_result = result
                metadata = execution_result.get("metadata", {}) if hasattr(execution_result, 'get') else {}
                
                print(f"\n=== 调试信息 ===")
                print(f"execution_result类型: {type(execution_result)}")
                print(f"execution_result内容: {execution_result}")
                print(f"metadata类型: {type(metadata)}")
                print(f"metadata内容: {metadata}")
                if hasattr(execution_result, 'get'):
                    print(f"review_type: {metadata.get('review_type')}")
                    print(f"comprehensive_result存在: {'comprehensive_result' in metadata}")
                
                # 检查是否为增强版审读结果
                if hasattr(execution_result, 'get') and metadata.get("review_type") == "enhanced" and "comprehensive_result" in metadata:
                    print("\n使用增强版审读结果逻辑")
                    # 增强版审读结果
                    final_result = {
                        "success": True,
                        "message": execution_result.get("final_result", "审读完成"),
                        "tokens_used": 0,
                        "processing_time": execution_result.get("execution_time_ms", 0),
                        "metadata": {
                            "agent_type": "review",
                            "instruction_set_id": instruction_set_id,
                            "execution_path": execution_result.get("execution_path", []),
                            "review_details": metadata,
                            "async_processing": False,
                            "comprehensive_result": metadata.get("comprehensive_result"),
                            "overall_result": metadata.get("overall_result"),
                            "matched_nodes": metadata.get("matched_nodes"),
                            "tree_structure": metadata.get("tree_structure"),
                            "total_matched_count": metadata.get("total_matched_count")
                        }
                    }
                elif hasattr(execution_result, 'get'):
                    print("\n使用传统审读结果逻辑")
                    # 传统审读结果
                    review_result = {
                        "risk_level": "MEDIUM",
                        "confidence": execution_result.get("confidence_score", 0.5),
                        "flagged_content": [],
                        "suggestions": []
                    }
                    
                    final_result_text = execution_result.get("final_result", "")
                    confidence = execution_result.get("confidence_score", 0.0)
                    
                    if "高风险" in final_result_text or "危险" in final_result_text or confidence > 0.8:
                        review_result["risk_level"] = "HIGH"
                        review_result["suggestions"].append("检测到高风险内容，建议仔细审核")
                    elif "低风险" in final_result_text or "安全" in final_result_text or confidence < 0.3:
                        review_result["risk_level"] = "LOW"
                        review_result["suggestions"].append("内容风险较低，可以正常发布")
                    else:
                        review_result["risk_level"] = "MEDIUM"
                        review_result["suggestions"].append("建议进一步审核确认")
                    
                    final_result = {
                        "success": True,
                        "message": execution_result.get("final_result", "审读完成"),
                        "tokens_used": 0,
                        "processing_time": execution_result.get("execution_time_ms", 0),
                        "metadata": {
                            "agent_type": "review",
                            "instruction_set_id": instruction_set_id,
                            "execution_path": execution_result.get("execution_path", []),
                            "review_details": execution_result.get("metadata", {}),
                            "review_result": review_result,
                            "async_processing": False
                        }
                    }
                else:
                    print("\nexecution_result不是字典类型，无法处理")
                    final_result = {
                        "success": False,
                        "error": f"执行结果类型错误: {type(execution_result)}",
                        "message": str(execution_result)
                    }
                
                print(f"\n=== 最终result ===")
                print(f"final_result类型: {type(final_result)}")
                print(f"final_result内容: {final_result}")
                
                # 检查final_result是否有get方法
                if hasattr(final_result, 'get'):
                    print("final_result 有 get 方法")
                    
                    # 模拟 agents.py 中的逻辑
                    success = final_result.get("success", False)
                    print(f"success: {success}")
                    
                    if not success:
                        print(f"指令执行失败: {final_result.get('error', '未知错误')}")
                    else:
                        print("指令执行成功")
                        
                        # 尝试访问其他字段
                        message = final_result.get("message", "")
                        tokens_used = final_result.get("tokens_used", 0)
                        processing_time = final_result.get("processing_time", 0)
                        metadata_final = final_result.get("metadata", {})
                        
                        print(f"消息: {message}")
                        print(f"令牌使用: {tokens_used}")
                        print(f"处理时间: {processing_time}")
                        print(f"元数据: {metadata_final}")
                        
                else:
                    print("final_result 没有 get 方法！这就是问题所在！")
                    print(f"final_result 的类型: {type(final_result)}")
                    print(f"final_result 的值: {final_result}")
                    
                    # 尝试调用 get 方法看看会发生什么
                    try:
                        test_get = final_result.get("success", False)
                        print(f"意外地成功调用了 get 方法: {test_get}")
                    except Exception as get_error:
                        print(f"调用 get 方法时出错: {str(get_error)}")
                        print(f"错误类型: {type(get_error)}")
                        
            except Exception as exec_error:
                print(f"执行指令集时出错: {str(exec_error)}")
                print(f"错误类型: {type(exec_error)}")
                import traceback
                traceback.print_exc()
                
        except Exception as e:
            print(f"测试过程中出错: {str(e)}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_review_agent())