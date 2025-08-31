from typing import Dict, List, Any, Optional
from sqlalchemy.orm import Session
from app.crud.instruction_set import instruction_set, instruction_node
from app.models.instruction_set import NodeType, ConditionType, ActionType
from app.services.content_review_service import ContentReviewService
from app.services.ai_model_service import AIModelService
from app.crud.model_service_config import model_service_config_crud
import time
import re
import json
import sys
import os

# 添加 example_review.py 的路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from example_review import EnhancedContentSafetyAgent


class InstructionExecutor:
    """指令集执行器"""
    
    def __init__(self, db: Session):
        self.db = db
        self.execution_path = []
        self.start_time = None
        self.review_service = ContentReviewService(db)
        # 初始化增强版审读代理
        self.enhanced_review_agent = None
        
    async def execute(self, instruction_set_id: int, input_text: str) -> Dict[str, Any]:
        """执行指令集
        
        Args:
            instruction_set_id: 指令集ID
            input_text: 输入文本
            
        Returns:
            执行结果字典
        """
        self.start_time = time.time()
        self.execution_path = []
        
        # 获取指令集信息
        instruction_set_info = await instruction_set.get(self.db, instruction_set_id)
        if not instruction_set_info:
            raise ValueError(f"指令集 {instruction_set_id} 不存在")
        
        print(f"\n=== 开始执行指令集 {instruction_set_id}: {instruction_set_info.name} ===")
        print(f"指令集描述: {instruction_set_info.description}")
        print(f"输入文本: {input_text[:100]}{'...' if len(input_text) > 100 else ''}")
        
        # 检查是否为审读类型的指令集
        is_review_instruction = "审读" in instruction_set_info.name or "review" in instruction_set_info.name.lower()
        
        if is_review_instruction:
            # 对于审读指令集，也按照节点树结构执行
            print(f"\n📋 这是审读类型指令集，将按照节点树结构执行")
            # 注释掉原来的数据库审读方式
            # return await self._execute_database_review(instruction_set_id, input_text)
            # 备用：使用增强版审读代理
            # return await self._execute_enhanced_review(input_text)
        
        # 获取根节点
        root_nodes = await instruction_set.get_root_nodes(self.db, instruction_set_id)
        if not root_nodes:
            print("❌ 指令集为空，没有根节点")
            raise ValueError("指令集没有根节点")
        
        print(f"\n📋 指令集树型结构:")
        for i, root_node in enumerate(root_nodes):
            await self._print_node_tree(root_node, level=0, is_last=i == len(root_nodes) - 1)
        
        print(f"\n🚀 开始执行指令...")
        
        # 从第一个根节点开始执行
        print(f"\n▶️ 执行根节点: {root_nodes[0].title} (ID: {root_nodes[0].id})")
        result = await self._execute_node(root_nodes[0], input_text)
        
        execution_time = int((time.time() - self.start_time) * 1000)
        
        print(f"\n🎯 最终执行结果:")
        print(f"   结果: {result.get('result', '')}")
        print(f"   置信度: {result.get('confidence', 0.0)}")
        print(f"   执行时间: {execution_time}ms")
        print(f"=== 指令集执行完成 ===")
        
        return {
            "execution_path": self.execution_path,
            "final_result": result.get("result", ""),
            "confidence_score": result.get("confidence", 0.0),
            "execution_time_ms": execution_time,
            "metadata": result.get("metadata", {})
        }
    
    async def _execute_enhanced_review(self, input_text: str) -> Dict[str, Any]:
        """
        使用增强版审读代理执行审读
        
        Args:
            input_text: 待审读的文本
            
        Returns:
            审读结果字典
        """
        try:
            print(f"\n🚀 开始增强版审读执行流程...")
            print(f"📝 输入文本长度: {len(input_text)} 字符")
            print(f"📝 输入文本预览: {input_text[:100]}{'...' if len(input_text) > 100 else ''}")
            
            # 初始化增强版审读代理
            if self.enhanced_review_agent is None:
                print(f"🔧 初始化增强版审读代理...")
                llm_config = {
                    "type": "ollama",
                    "model": "qwen2.5:7b",
                    "base_url": "http://bt.acoming.net:11868"
                }
                self.enhanced_review_agent = EnhancedContentSafetyAgent(llm_config)
                print(f"✅ 增强版审读代理初始化完成")
            
            print(f"\n🔍 开始执行内容安全检测...")
            print(f"🌳 加载检测树结构...")
            
            # 执行全面审读
            comprehensive_result = self.enhanced_review_agent.get_comprehensive_detection_result(input_text)
            
            execution_time = int((time.time() - self.start_time) * 1000)
            
            # 构建执行路径 (使用虚拟节点ID)
            self.execution_path = [0]  # 0表示增强版审读虚拟节点
            
            # 判断最终结果
            overall_result = comprehensive_result['overall_result']
            final_result = "审读通过" if not overall_result['matched'] else f"审读未通过 - {overall_result['risk_level']}"
            
            print(f"\n🎯 增强版审读执行完成:")
            print(f"   📊 检测结果: {'❌ 检测到问题' if overall_result['matched'] else '✅ 未检测到问题'}")
            print(f"   ⚠️  风险等级: {overall_result['risk_level']}")
            print(f"   🎯 置信度: {overall_result['confidence']:.2f}")
            print(f"   🔢 总命中节点数: {comprehensive_result['total_matched_count']}")
            print(f"   ⏱️  执行时间: {execution_time}ms")
            
            # 输出命中节点详情
            if comprehensive_result['matched_nodes']:
                print(f"\n📋 命中节点详情:")
                for i, node in enumerate(comprehensive_result['matched_nodes'], 1):
                    print(f"   {i}. 节点: {node.get('description', 'N/A')}")
                    print(f"      风险等级: {node.get('risk_level', 'N/A')}")
                    print(f"      置信度: {node.get('confidence', 0):.2f}")
                    if node.get('evidence'):
                        print(f"      证据: {node['evidence'][:100]}{'...' if len(str(node['evidence'])) > 100 else ''}")
            
            # 输出检测树结构概览
            if comprehensive_result.get('tree_structure'):
                print(f"\n🌳 检测树结构概览:")
                tree_str = json.dumps(comprehensive_result['tree_structure'], ensure_ascii=False, indent=2)
                print(f"   树结构大小: {len(tree_str)} 字符")
                print(f"   根节点数量: {len(comprehensive_result['tree_structure']) if isinstance(comprehensive_result['tree_structure'], list) else 1}")
            
            return {
                "execution_path": self.execution_path,
                "final_result": final_result,
                "confidence_score": overall_result['confidence'],
                "execution_time_ms": execution_time,
                "metadata": {
                    "review_type": "enhanced",
                    "comprehensive_result": comprehensive_result,
                    "overall_result": overall_result,
                    "matched_nodes": comprehensive_result['matched_nodes'],
                    "tree_structure": comprehensive_result['tree_structure'],
                    "total_matched_count": comprehensive_result['total_matched_count'],
                    "execution_summary": {
                        "input_length": len(input_text),
                        "detection_time_ms": execution_time,
                        "nodes_checked": comprehensive_result.get('nodes_checked', 0),
                        "nodes_matched": comprehensive_result['total_matched_count']
                    }
                }
            }
            
        except Exception as e:
            print(f"❌ 增强版审读执行失败: {str(e)}")
            print(f"🔍 错误详情: {type(e).__name__}")
            import traceback
            print(f"📋 错误堆栈: {traceback.format_exc()}")
            
            execution_time = int((time.time() - self.start_time) * 1000)
            
            return {
                "execution_path": self.execution_path,
                "final_result": f"审读执行失败: {str(e)}",
                "confidence_score": 0.0,
                "execution_time_ms": execution_time,
                "metadata": {
                    "review_type": "enhanced",
                    "error": str(e),
                    "error_type": type(e).__name__,
                    "execution_failed": True
                }
            }
    
    async def _execute_database_review(self, instruction_set_id: int, input_text: str) -> Dict[str, Any]:
        """
        使用数据库指令集执行审读
        
        Args:
            instruction_set_id: 指令集ID
            input_text: 待审读的文本
            
        Returns:
            审读结果字典
        """
        try:
            print(f"\n🚀 开始数据库指令集审读执行流程...")
            print(f"📝 指令集ID: {instruction_set_id}")
            print(f"📝 输入文本长度: {len(input_text)} 字符")
            print(f"📝 输入文本预览: {input_text[:100]}{'...' if len(input_text) > 100 else ''}")
            
            # 获取指令集信息
            instruction_set_info = await instruction_set.get(self.db, instruction_set_id)
            print(f"\n📋 指令集信息:")
            print(f"   名称: {instruction_set_info.name}")
            print(f"   描述: {instruction_set_info.description}")
            print(f"   版本: {instruction_set_info.version}")
            print(f"   状态: {instruction_set_info.status}")
            
            # 获取指令集的根节点
            print(f"\n🔍 从数据库加载指令集根节点...")
            root_nodes = await instruction_set.get_root_nodes(self.db, instruction_set_id)
            if not root_nodes:
                print(f"❌ 指令集没有根节点")
                raise ValueError("指令集没有根节点")
            
            print(f"✅ 成功加载 {len(root_nodes)} 个根节点")
            for i, root_node in enumerate(root_nodes):
                print(f"   根节点 {i+1}: {root_node.title} (ID: {root_node.id})")
                print(f"   节点类型: {root_node.node_type}")
                print(f"   节点描述: {root_node.description}")
                
                # 解析节点配置
                if root_node.meta_data:
                    print(f"   节点配置: {json.dumps(root_node.meta_data, ensure_ascii=False, indent=2)}")
            
            # 获取完整的指令树结构
            print(f"\n🌳 加载完整指令树结构...")
            tree_nodes = await instruction_node.get_tree(self.db, instruction_set_id)
            print(f"✅ 成功加载指令树，共 {len(tree_nodes)} 个根节点")
            
            # 打印树结构
            for i, root_node in enumerate(tree_nodes):
                await self._print_node_tree_with_config(root_node, level=0, is_last=i == len(tree_nodes) - 1)
            
            # 使用ContentReviewService进行审读
            print(f"\n🔧 初始化内容审读服务...")
            review_service = ContentReviewService(self.db)
            
            # 获取默认模型配置
            print(f"🔍 查找可用的模型配置...")
            default_config = await model_service_config_crud.get_default_config(self.db)
            if not default_config:
                # 如果没有默认配置，获取第一个可用的配置
                configs = await model_service_config_crud.get_active_configs(self.db)
                if not configs:
                    raise ValueError("没有可用的模型配置")
                default_config = configs[0]
                print(f"⚠️ 没有默认模型配置，使用第一个可用配置")
            
            model_config_id = default_config.id
            print(f"📊 使用模型配置: {default_config.name} (ID: {model_config_id})")
            print(f"📊 模型提供商: {default_config.provider}")
            print(f"📊 模型名称: {default_config.model_name}")
            
            print(f"\n🚀 开始执行审读...")
            review_result = await review_service.review_content(input_text, instruction_set_id, model_config_id)
            
            execution_time = int((time.time() - self.start_time) * 1000)
            
            # 构建执行路径 (使用根节点ID)
            root_node_ids = [node.id for node in root_nodes]
            self.execution_path = root_node_ids if root_node_ids else [instruction_set_id]
            
            # 判断最终结果
            final_result = "审读通过" if not review_result.matched else f"审读未通过 - {review_result.risk_level}"
            
            print(f"\n🎯 数据库指令集审读执行完成:")
            print(f"   📊 检测结果: {'❌ 检测到问题' if review_result.matched else '✅ 未检测到问题'}")
            print(f"   ⚠️  风险等级: {review_result.risk_level}")
            print(f"   🎯 置信度: {review_result.confidence:.2f}")
            print(f"   📝 证据: {review_result.evidence}")
            print(f"   ⏱️  执行时间: {execution_time}ms")
            
            # 递归打印子节点结果
            if review_result.children_results:
                print(f"\n📋 子节点审读结果:")
                self._print_review_results(review_result.children_results, level=1)
            
            return {
                "execution_path": self.execution_path,
                "final_result": final_result,
                "confidence_score": review_result.confidence,
                "execution_time_ms": execution_time,
                "metadata": {
                    "review_type": "database",
                    "instruction_set_id": instruction_set_id,
                    "review_result": {
                        "node_id": review_result.node_id,
                        "description": review_result.description,
                        "matched": review_result.matched,
                        "risk_level": review_result.risk_level,
                        "confidence": review_result.confidence,
                        "evidence": review_result.evidence,
                        "sensitive_excerpt": review_result.sensitive_excerpt
                    },
                    "execution_summary": {
                        "input_length": len(input_text),
                        "detection_time_ms": execution_time,
                        "nodes_loaded": len(tree_nodes),
                        "root_nodes_count": len(root_nodes)
                    }
                }
            }
            
        except Exception as e:
            print(f"❌ 数据库指令集审读执行失败: {str(e)}")
            print(f"🔍 错误详情: {type(e).__name__}")
            import traceback
            print(f"📋 错误堆栈: {traceback.format_exc()}")
            
            execution_time = int((time.time() - self.start_time) * 1000)
            
            return {
                "execution_path": self.execution_path,
                "final_result": f"审读执行失败: {str(e)}",
                "confidence_score": 0.0,
                "execution_time_ms": execution_time,
                "metadata": {
                    "review_type": "database",
                    "error": str(e),
                    "error_type": type(e).__name__,
                    "execution_failed": True
                }
            }
    
    async def _print_node_tree_with_config(self, node, level: int = 0, is_last: bool = True):
        """
        递归打印节点树结构及其配置信息
        
        Args:
            node: 节点对象
            level: 缩进级别
            is_last: 是否为最后一个节点
        """
        indent = "  " * level
        prefix = "└─ " if is_last else "├─ "
        
        print(f"{indent}{prefix}{node.title} (ID: {node.id})")
        print(f"{indent}   类型: {node.node_type}")
        print(f"{indent}   描述: {node.description}")
        
        if node.meta_data:
            print(f"{indent}   配置: {json.dumps(node.meta_data, ensure_ascii=False)}")
        
        # 递归打印子节点
        if hasattr(node, 'children') and node.children:
            for i, child in enumerate(node.children):
                await self._print_node_tree_with_config(child, level + 1, i == len(node.children) - 1)
    
    def _print_review_results(self, results, level: int = 0):
        """
        递归打印审读结果
        
        Args:
            results: 审读结果列表
            level: 缩进级别
        """
        indent = "  " * level
        
        for i, result in enumerate(results):
            print(f"{indent}├─ 节点 {result.node_id}: {result.description}")
            print(f"{indent}   匹配: {'是' if result.matched else '否'}")
            print(f"{indent}   风险等级: {result.risk_level}")
            print(f"{indent}   置信度: {result.confidence:.2f}")
            if result.evidence:
                print(f"{indent}   证据: {result.evidence}")
            if result.sensitive_excerpt:
                print(f"{indent}   敏感内容: {result.sensitive_excerpt}")
            
            # 递归打印子节点结果
            if result.children_results:
                self._print_review_results(result.children_results, level + 1)
    
    async def _execute_node(self, node, input_text: str) -> Dict[str, Any]:
        """执行单个节点
        
        Args:
            node: 指令节点
            input_text: 输入文本
            
        Returns:
            节点执行结果
        """
        # 记录执行路径
        self.execution_path.append({
            "node_id": node.id,
            "node_title": node.title,
            "node_type": node.node_type.value,
            "timestamp": time.time()
        })
        
        print(f"\n  🔄 执行节点: {node.title} (ID: {node.id}, Type: {node.node_type.value})")
        
        # 检查节点是否激活
        if not node.is_active:
            print(f"  ⏭️ 节点未激活，跳过执行")
            return {"result": "节点未激活", "confidence": 0.0}
        
        # 根据节点类型执行不同逻辑
        if node.node_type == NodeType.CONDITION:
            result = await self._execute_condition_node(node, input_text)
        elif node.node_type == NodeType.ACTION:
            result = await self._execute_action_node(node, input_text)
        elif node.node_type == NodeType.BRANCH:
            result = await self._execute_branch_node(node, input_text)
        else:
            result = {"result": "未知节点类型", "confidence": 0.0}
        
        print(f"  ✅ 节点执行完成: {result.get('result', '')[:50]}{'...' if len(str(result.get('result', ''))) > 50 else ''}")
        return result
    
    async def _execute_condition_node(self, node, input_text: str) -> Dict[str, Any]:
        """
        执行条件节点 - 新的执行逻辑：
        1. 一级节点全部通过，执行所有二级节点
        2. 二级节点命中时执行其子节点
        3. 所有节点执行都要走LLM
        4. 记录所有执行过的节点和结论
        
        Args:
            node: 条件节点
            input_text: 输入文本
            
        Returns:
            执行结果字典
        """
        try:
            # 使用节点的实际字段
            condition_type = node.condition_type or ConditionType.AI_CLASSIFICATION
            condition_value = node.condition_text or ""
            condition_config = json.loads(node.meta_data or "{}") if node.meta_data else {}
            
            # 强制所有节点都走LLM进行AI分类判断
            print(f"    🤖 使用LLM进行节点判断: {node.title}")
            ai_result = await self._classify_with_ai_for_node(node, input_text, condition_config)
            result = ai_result["result"]
            confidence = ai_result["confidence"]
            reasoning = ai_result.get("reasoning", "")
            
            # 记录节点执行结果
            node_execution_record = {
                "node_id": node.id,
                "node_title": node.title,
                "node_type": node.node_type.value,
                "execution_result": result,
                "confidence": confidence,
                "reasoning": reasoning,
                "timestamp": time.time()
            }
            
            # 获取子节点
            child_nodes = await instruction_node.get_children(self.db, node.id)
            child_nodes.sort(key=lambda x: x.sort_order)
            
            # 判断是否为根节点（一级节点）
            parent_nodes = await instruction_node.get_parents(self.db, node.id)
            is_root_node = len(parent_nodes) == 0
            
            if is_root_node:
                print(f"    🌟 一级节点（根节点）: {node.title} - 强制通过，执行所有二级子节点")
                # 一级节点强制通过，执行所有二级子节点
                all_child_results = []
                overall_confidence = 0.0
                hit_children = []  # 记录命中的子节点
                
                for child_node in child_nodes:
                    if child_node.is_active:
                        print(f"      🔄 执行二级节点: {child_node.title}")
                        child_result = await self._execute_node(child_node, input_text)
                        
                        child_record = {
                            "node_id": child_node.id,
                            "node_title": child_node.title,
                            "node_type": child_node.node_type.value,
                            "result": child_result.get("result", ""),
                            "confidence": child_result.get("confidence", 0.0),
                            "reasoning": child_result.get("reasoning", ""),
                            "metadata": child_result.get("metadata", {})
                        }
                        
                        all_child_results.append(child_record)
                        overall_confidence += child_result.get("confidence", 0.0)
                        
                        # 检查二级节点是否命中（需要执行其子节点）
                        if child_result.get("hit", False) or child_result.get("confidence", 0.0) > 0.5:
                            hit_children.append(child_node)
                            print(f"        ✅ 二级节点命中: {child_node.title}，将执行其子节点")
                
                # 执行命中的二级节点的子节点
                for hit_child in hit_children:
                    grandchild_nodes = await instruction_node.get_children(self.db, hit_child.id)
                    for grandchild_node in grandchild_nodes:
                        if grandchild_node.is_active:
                            print(f"        🔄 执行三级节点: {grandchild_node.title}")
                            grandchild_result = await self._execute_node(grandchild_node, input_text)
                            
                            grandchild_record = {
                                "node_id": grandchild_node.id,
                                "node_title": grandchild_node.title,
                                "node_type": grandchild_node.node_type.value,
                                "parent_node_id": hit_child.id,
                                "parent_node_title": hit_child.title,
                                "result": grandchild_result.get("result", ""),
                                "confidence": grandchild_result.get("confidence", 0.0),
                                "reasoning": grandchild_result.get("reasoning", ""),
                                "metadata": grandchild_result.get("metadata", {})
                            }
                            
                            all_child_results.append(grandchild_record)
                            overall_confidence += grandchild_result.get("confidence", 0.0)
                
                # 计算平均置信度
                avg_confidence = overall_confidence / len(all_child_results) if all_child_results else 0.0
                
                return {
                    "result": f"一级节点执行完成，共执行了{len(all_child_results)}个子节点，其中{len(hit_children)}个二级节点命中",
                    "confidence": avg_confidence,
                    "hit": len(hit_children) > 0,
                    "reasoning": f"一级节点{node.title}强制通过，执行了所有二级子节点，命中的二级节点进一步执行了子节点",
                    "metadata": {
                        "node_execution_record": node_execution_record,
                        "all_child_results": all_child_results,
                        "hit_children_count": len(hit_children),
                        "total_executed_nodes": len(all_child_results)
                    }
                }
            
            else:
                # 二级或更深层节点的处理逻辑
                print(f"    🔍 二级/深层节点: {node.title} - 判断结果: {result}")
                
                if result:
                    print(f"      ✅ 节点命中，执行子节点")
                    # 节点命中，执行所有子节点
                    child_results = []
                    for child_node in child_nodes:
                        if child_node.is_active:
                            child_result = await self._execute_node(child_node, input_text)
                            child_results.append({
                                "node_id": child_node.id,
                                "node_title": child_node.title,
                                "result": child_result.get("result", ""),
                                "confidence": child_result.get("confidence", 0.0),
                                "reasoning": child_result.get("reasoning", "")
                            })
                    
                    return {
                        "result": f"节点命中: {reasoning}",
                        "confidence": confidence,
                        "hit": True,
                        "reasoning": reasoning,
                        "metadata": {
                            "node_execution_record": node_execution_record,
                            "child_results": child_results
                        }
                    }
                else:
                    print(f"      ❌ 节点未命中")
                    return {
                        "result": f"节点未命中: {reasoning}",
                        "confidence": confidence,
                        "hit": False,
                        "reasoning": reasoning,
                        "metadata": {
                            "node_execution_record": node_execution_record
                        }
                    }
            
        except Exception as e:
            print(f"    ❌ 条件节点执行错误: {str(e)}")
            return {
                "result": f"条件执行错误: {str(e)}",
                "confidence": 0.0,
                "hit": False,
                "reasoning": f"执行出错: {str(e)}",
                "metadata": {"error": str(e)}
            }
    
    async def _execute_action_node(self, node, input_text: str) -> Dict[str, Any]:
        """执行动作节点
        
        Args:
            node: 动作节点
            input_text: 输入文本
            
        Returns:
            动作执行结果
        """
        try:
            # 使用节点的实际字段
            action_type = node.action_type or ActionType.CONTINUE
            action_value = node.result_value or ""
            action_config = json.loads(node.meta_data or "{}") if node.meta_data else {}
            
            if action_type == ActionType.APPROVE:
                # 批准动作
                result_text = action_value or "内容已批准"
                return {
                    "result": result_text,
                    "confidence": 1.0,
                    "metadata": {
                        "action_type": action_type.value,
                        "action_value": action_value
                    }
                }
                
            elif action_type == ActionType.REJECT:
                # 拒绝动作
                result_text = action_value or "内容被拒绝"
                return {
                    "result": result_text,
                    "confidence": 1.0,
                    "metadata": {
                        "action_type": action_type.value,
                        "action_value": action_value
                    }
                }
                
            elif action_type == ActionType.FLAG_CONTENT:
                # 标记内容
                result_text = action_value or "内容已标记"
                return {
                    "result": result_text,
                    "confidence": 1.0,
                    "metadata": {
                        "action_type": action_type.value,
                        "action_value": action_value
                    }
                }
                
            elif action_type == ActionType.CLASSIFY:
                # 分类动作
                categories = action_config.get("categories", [])
                if categories:
                    # 简单的关键词匹配分类
                    best_category = "未分类"
                    best_score = 0.0
                    
                    for category in categories:
                        if category.lower() in input_text.lower():
                            best_score = 1.0
                            best_category = category
                            break
                    
                    return {
                        "result": f"分类结果: {best_category}",
                        "confidence": best_score,
                        "metadata": {
                            "action_type": action_type.value,
                            "category": best_category,
                            "categories": categories
                        }
                    }
                else:
                    return {
                        "result": "分类配置未设置",
                        "confidence": 0.0
                    }
                    
            elif action_type == ActionType.CONTINUE:
                # 继续执行
                return {
                    "result": action_value or "继续执行",
                    "confidence": 1.0,
                    "metadata": {
                        "action_type": action_type.value,
                        "action_value": action_value
                    }
                }
                
            elif action_type == ActionType.STOP:
                # 停止执行
                return {
                    "result": action_value or "停止执行",
                    "confidence": 1.0,
                    "metadata": {
                        "action_type": action_type.value,
                        "action_value": action_value
                    }
                }
            
            # 默认处理
            else:
                return {
                    "result": action_value or f"执行动作: {action_type.value}",
                    "confidence": 1.0,
                    "metadata": {
                        "action_type": action_type.value,
                        "action_value": action_value
                    }
                }
            
        except Exception as e:
            return {
                "result": f"动作执行错误: {str(e)}",
                "confidence": 0.0,
                "metadata": {"error": str(e)}
            }
    
    async def _execute_branch_node(self, node, input_text: str) -> Dict[str, Any]:
        """执行分支节点
        
        Args:
            node: 分支节点
            input_text: 输入文本
            
        Returns:
            分支执行结果
        """
        # 获取所有子节点并按优先级执行
        child_nodes = await instruction_node.get_children(self.db, node.id)
        child_nodes.sort(key=lambda x: x.sort_order)
        
        results = []
        total_confidence = 0.0
        
        print(f"    🌿 分支节点有 {len(child_nodes)} 个子节点")
        
        for child_node in child_nodes:
            if child_node.is_active:
                print(f"    ▶️ 执行分支子节点: {child_node.title}")
                child_result = await self._execute_node(child_node, input_text)
                results.append(child_result)
                total_confidence += child_result.get("confidence", 0.0)
            else:
                print(f"    ⏭️ 跳过非活跃子节点: {child_node.title}")
        
        if results:
            # 选择置信度最高的结果
            best_result = max(results, key=lambda x: x.get("confidence", 0.0))
            avg_confidence = total_confidence / len(results)
            
            print(f"    🎯 分支执行完成，选择最佳结果: {best_result.get('result', '')[:50]}{'...' if len(str(best_result.get('result', ''))) > 50 else ''}")
            
            return {
                "result": best_result.get("result", ""),
                "confidence": avg_confidence,
                "metadata": {
                    "branch_results": results,
                    "selected_result": best_result
                }
            }
        else:
            print(f"    ❌ 分支节点无可执行子节点")
            return {
                "result": "分支节点无可执行子节点",
                "confidence": 0.0
            }
    
    def _check_content_safety(self, text: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """检查内容安全性
        
        Args:
            text: 待检测文本
            config: 安全检测配置
            
        Returns:
            安全检测结果
        """
        try:
            # 获取检测类型和阈值
            safety_type = config.get("safety_type", "general")  # general, adult, violence, hate
            threshold = config.get("threshold", 0.5)
            
            # 简单的关键词检测实现（实际项目中应该调用专业的内容安全API）
            unsafe_keywords = {
                "adult": ["色情", "性", "裸体", "成人"],
                "violence": ["暴力", "杀", "死", "血", "打", "伤害"],
                "hate": ["仇恨", "歧视", "种族", "恶意"],
                "general": ["色情", "暴力", "仇恨", "违法", "毒品"]
            }
            
            keywords = unsafe_keywords.get(safety_type, unsafe_keywords["general"])
            matched_keywords = []
            
            for keyword in keywords:
                if keyword in text:
                    matched_keywords.append(keyword)
            
            # 计算风险分数
            risk_score = len(matched_keywords) / len(keywords) if keywords else 0.0
            is_safe = risk_score < threshold
            
            return {
                "is_safe": is_safe,
                "confidence": 1.0 - risk_score,
                "risk_score": risk_score,
                "matched_keywords": matched_keywords,
                "safety_type": safety_type
            }
            
        except Exception as e:
            return {
                "is_safe": True,  # 默认安全
                "confidence": 0.0,
                "error": str(e)
            }
    
    def _analyze_sentiment(self, text: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """分析文本情感
        
        Args:
            text: 待分析文本
            config: 情感分析配置
            
        Returns:
            情感分析结果
        """
        try:
            target_sentiment = config.get("target_sentiment", "positive")  # positive, negative, neutral
            
            # 简单的情感词典实现（实际项目中应该使用专业的情感分析模型）
            positive_words = ["好", "棒", "优秀", "喜欢", "满意", "开心", "高兴"]
            negative_words = ["坏", "差", "糟糕", "讨厌", "不满", "难过", "生气"]
            
            positive_count = sum(1 for word in positive_words if word in text)
            negative_count = sum(1 for word in negative_words if word in text)
            
            if positive_count > negative_count:
                detected_sentiment = "positive"
                confidence = positive_count / (positive_count + negative_count + 1)
            elif negative_count > positive_count:
                detected_sentiment = "negative"
                confidence = negative_count / (positive_count + negative_count + 1)
            else:
                detected_sentiment = "neutral"
                confidence = 0.5
            
            matches_target = detected_sentiment == target_sentiment
            
            return {
                "matches_target": matches_target,
                "confidence": confidence,
                "detected_sentiment": detected_sentiment,
                "target_sentiment": target_sentiment,
                "positive_count": positive_count,
                "negative_count": negative_count
            }
            
        except Exception as e:
            return {
                "matches_target": False,
                "confidence": 0.0,
                "error": str(e)
            }
    
    async def _classify_with_ai(self, text: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """使用AI进行文本分类
        
        Args:
            text: 待分类文本
            config: AI分类配置
            
        Returns:
            AI分类结果
        """
        try:
            # 获取配置参数
            model_config_id = config.get("model_config_id")
            classification_prompt = config.get("prompt", "请判断以下文本是否符合要求：")
            target_category = config.get("target_category", "符合")
            
            if not model_config_id:
                return {
                    "result": False,
                    "confidence": 0.0,
                    "error": "未配置模型服务"
                }
            
            # 获取模型配置
            model_config = await model_service_config_crud.get(self.db, model_config_id)
            if not model_config:
                return {
                    "result": False,
                    "confidence": 0.0,
                    "error": f"模型配置不存在: {model_config_id}"
                }
            
            # 构建提示词
            full_prompt = f"{classification_prompt}\n\n文本内容：{text}\n\n请回答：符合 或 不符合"
            
            # 调用AI模型
            messages = [
                {"role": "user", "content": full_prompt}
            ]
            
            ai_service = AIModelService()
            response = await ai_service.chat_with_model(model_config, messages)
            
            if not response or "content" not in response:
                return {
                    "result": False,
                    "confidence": 0.0,
                    "error": "AI模型响应为空"
                }
            
            # 解析AI响应
            ai_response = response["content"].strip()
            result = target_category in ai_response or "符合" in ai_response
            
            # 计算置信度（简单实现）
            confidence = 0.8 if result else 0.2
            
            return {
                "result": result,
                "confidence": confidence,
                "ai_response": ai_response,
                "target_category": target_category
            }
            
        except Exception as e:
            return {
                "result": False,
                "confidence": 0.0,
                "error": f"AI分类失败: {str(e)}"
            }
    
    async def _classify_with_ai_for_node(self, node, input_text: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        使用AI对节点进行分类判断，专门为新的执行逻辑设计
        
        Args:
            node: 节点对象
            input_text: 待分类文本
            config: 节点配置
            
        Returns:
            AI分类结果，包含reasoning字段
        """
        try:
            # 获取默认模型配置
            default_config = await model_service_config_crud.get_default_config(self.db)
            if not default_config:
                configs = await model_service_config_crud.get_active_configs(self.db)
                if not configs:
                    return {
                        "result": False,
                        "confidence": 0.0,
                        "reasoning": "没有可用的模型配置",
                        "error": "没有可用的模型配置"
                    }
                default_config = configs[0]
            
            # 构建针对节点的专门提示词
            node_prompt = f"""
你是一个内容安全检测专家。请分析以下文本是否符合节点"{node.title}"的检测要求。

节点描述：{node.description or '无描述'}
节点条件：{node.condition_text or '无特定条件'}

待检测文本：
{input_text}

请按以下格式回答：
判断结果：[符合/不符合]
置信度：[0.0-1.0之间的数值]
推理过程：[详细说明你的判断依据和推理过程]

注意：
1. 如果文本涉及该节点要检测的内容类型，请回答"符合"
2. 如果文本不涉及该节点要检测的内容类型，请回答"不符合"
3. 置信度应该反映你对判断的确信程度
4. 推理过程要详细说明判断依据
"""
            
            # 调用AI模型
            ai_service = AIModelService()
            response = await ai_service.chat_with_model(
                config=default_config,
                system_prompt="你是一个内容安全检测专家。",
                user_message=node_prompt
            )
            
            if not response or not response.get("success") or not response.get("message"):
                return {
                    "result": False,
                    "confidence": 0.0,
                    "reasoning": "AI模型响应为空或失败",
                    "error": response.get("error", "AI模型响应为空")
                }
            
            # 解析AI响应
            ai_response = response["message"].strip()
            
            # 提取判断结果
            result = "符合" in ai_response
            
            # 提取置信度
            confidence = 0.5  # 默认置信度
            confidence_match = re.search(r'置信度[：:](\\d*\\.?\\d+)', ai_response)
            if confidence_match:
                try:
                    confidence = float(confidence_match.group(1))
                    confidence = max(0.0, min(1.0, confidence))  # 确保在0-1范围内
                except ValueError:
                    confidence = 0.5
            
            # 提取推理过程
            reasoning_match = re.search(r'推理过程[：:](.*?)(?=\n|$)', ai_response, re.DOTALL)
            reasoning = reasoning_match.group(1).strip() if reasoning_match else ai_response
            
            print(f"      🤖 AI判断结果: {result}, 置信度: {confidence:.2f}")
            print(f"      💭 推理过程: {reasoning[:100]}{'...' if len(reasoning) > 100 else ''}")
            
            return {
                "result": result,
                "confidence": confidence,
                "reasoning": reasoning,
                "ai_response": ai_response,
                "model_config": {
                    "id": default_config.id,
                    "name": default_config.name,
                    "provider": default_config.provider,
                    "model_name": default_config.model_name
                }
            }
            
        except Exception as e:
            print(f"      ❌ AI分类出错: {str(e)}")
            return {
                "result": False,
                "confidence": 0.0,
                "reasoning": f"AI分类执行出错: {str(e)}",
                "error": str(e)
            }
    
    def get_parents(self, node, all_nodes):
        """
        获取节点的所有父节点
        
        Args:
            node: 当前节点
            all_nodes: 所有节点列表
            
        Returns:
            父节点列表
        """
        parents = []
        for n in all_nodes:
            if hasattr(n, 'children') and node in n.children:
                parents.append(n)
        return parents
    
    def _execute_custom_function(self, text: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """执行自定义函数
        
        Args:
            text: 输入文本
            config: 自定义函数配置
            
        Returns:
            自定义函数执行结果
        """
        try:
            function_name = config.get("function_name", "")
            function_params = config.get("params", {})
            
            # 这里可以根据function_name调用不同的自定义函数
            # 目前提供一个示例实现
            if function_name == "text_length_check":
                min_length = function_params.get("min_length", 0)
                max_length = function_params.get("max_length", 1000)
                text_length = len(text)
                
                result = min_length <= text_length <= max_length
                confidence = 1.0 if result else 0.0
                
                return {
                    "result": result,
                    "confidence": confidence,
                    "text_length": text_length,
                    "min_length": min_length,
                    "max_length": max_length
                }
            
            # 默认返回
            return {
                "result": True,
                "confidence": 0.5,
                "message": f"未实现的自定义函数: {function_name}"
            }
            
        except Exception as e:
            return {
                "result": False,
                "confidence": 0.0,
                "error": str(e)
            }
    
    async def _print_node_tree(self, node, level: int = 0, is_last: bool = True, prefix: str = ""):
        """打印节点树型结构
        
        Args:
            node: 节点对象
            level: 层级
            is_last: 是否为最后一个节点
            prefix: 前缀字符串
        """
        # 构建树型结构的前缀
        if level == 0:
            tree_prefix = ""
        else:
            tree_prefix = prefix + ("└── " if is_last else "├── ")
        
        # 节点状态图标
        status_icon = "✅" if node.is_active else "❌"
        
        # 节点类型图标
        type_icons = {
            "CONDITION": "🔍",
            "ACTION": "⚡",
            "BRANCH": "🌿"
        }
        type_icon = type_icons.get(node.node_type.value, "📄")
        
        print(f"{tree_prefix}{status_icon} {type_icon} {node.title} (ID: {node.id}, Type: {node.node_type.value})")
        
        # 获取子节点
        try:
            child_nodes = await instruction_node.get_children(self.db, node.id)
            child_nodes.sort(key=lambda x: x.sort_order)
            
            for i, child_node in enumerate(child_nodes):
                is_child_last = i == len(child_nodes) - 1
                child_prefix = prefix + ("    " if is_last else "│   ")
                await self._print_node_tree(child_node, level + 1, is_child_last, child_prefix)
        except Exception as e:
            print(f"{prefix}    ❌ 获取子节点失败: {str(e)}")