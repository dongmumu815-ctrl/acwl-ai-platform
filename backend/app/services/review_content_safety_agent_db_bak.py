#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
增强版内容安全检测Agent - 数据库版本
从数据库中读取检测树结构，而不是硬编码
"""

import json
import re
import requests
from typing import Dict, List, Any, Optional, Set
from dataclasses import dataclass
from enum import Enum
import sys
import os

# # 将项目根目录添加到 Python 路径中
# project_root = os.path.dirname(os.path.abspath(__file__))
# sys.path.append(project_root)

# from app.services.db_service import RouterDBService


from multiprocessing.managers import BaseManager 
from typing import Dict, List, Optional, Any, Tuple
import os
import json
import logging
from dotenv import load_dotenv

class PoolManager(BaseManager):
    pass


# 注册 DataService
PoolManager.register('DataService')


class RouterDBService:
    """路由器数据库服务"""
    
    def __init__(self):
        # 加载环境变量
        load_dotenv()
        
        # 从环境变量获取配置，如果没有则使用默认值
        host = os.getenv('DB_SERVICE_HOST', '127.0.0.1')
        port = int(os.getenv('DB_SERVICE_PORT', '50000'))
        auth_key = os.getenv('DB_SERVICE_AUTH_KEY', 'cepiec2024').encode()
        
        print(host, port, auth_key)
        
        self.manager = PoolManager(address=(host, port), authkey=auth_key)
        self.manager.connect()
        self.service = self.manager.DataService()


class OllamaLLMClient:
    """Ollama LLM客户端"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        初始化Ollama客户端
        
        Args:
            config: 配置字典，包含type, model, base_url等
        """
        self.model = config.get('model', 'qwen2.5:7b')
        self.base_url = config.get('base_url', 'http://localhost:11434')
        # self.api_url = f"{self.base_url.rstrip('/')}/api/generate"
        if not self.base_url.rstrip('/').endswith('/api/chat'):
            self.api_url = f"{self.base_url.rstrip('/')}/api/chat"
        else:
            self.api_url = self.base_url.rstrip('/')
        self.api_url = "http://10.8.0.94:11435"
        self.api_url = f"{self.api_url.rstrip('/')}/api/generate"
        print("--------------------------------")
        print(self.api_url)
        
    def judge_content(self, content: str, prompt: str, node_description: str) -> Dict[str, Any]:
        """
        使用LLM判断内容是否符合特定条件
        
        Args:
            content: 待判断的内容
            prompt: 判断提示词
            node_description: 节点描述
            
        Returns:
            包含判断结果的字典: {matched: bool, confidence: float, reasoning: str, tokens_used: int}
        """
        
        # 构建完整的提示词
        full_prompt = f"""
你是一个内容安全检测专家。请根据以下要求判断给定内容是否符合特定条件。

检测节点: {node_description}
判断标准: {prompt}

待检测内容: "{content}"

请严格按照以下JSON格式回复，不要包含任何其他内容：
{{
    "matched": true/false,
    "confidence": 0.0-1.0之间的数值,
    "reasoning": "详细的判断理由"
}}
"""     
        try:
            # 发送请求到Ollama

            print("++++++++++++++++++++++++++++++++++++++++++")
            print("url:",self.api_url,self.model)
            print("content", content)
            print("prompt:", full_prompt)
            print("node_description", node_description)

            response = requests.post(
                self.api_url,
                json={
                    "model": self.model,
                    "prompt": full_prompt,
                    "stream": False,
                    "format": "json"
                },
                timeout=30
            )
            print("^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^")
            print(response)
            
            if response.status_code == 200:
                result = response.json()
                llm_response = result.get('response', '')
                
                # 尝试解析JSON响应
                try:
                    parsed_result = json.loads(llm_response)
                    # 估算token使用量（简单估算：输入+输出字符数/4）
                    tokens_used = (len(full_prompt) + len(llm_response)) // 4
                    return {
                        'matched': bool(parsed_result.get('matched', False)),
                        'confidence': float(parsed_result.get('confidence', 0.0)),
                        'reasoning': str(parsed_result.get('reasoning', '无法获取判断理由')),
                        'tokens_used': tokens_used
                    }
                except json.JSONDecodeError:
                    # 如果JSON解析失败，尝试从文本中提取信息
                    result = self._parse_text_response(llm_response)
                    # 估算token使用量
                    result['tokens_used'] = (len(full_prompt) + len(llm_response)) // 4
                    return result
            else:
                raise Exception(f"API请求失败: {response.status_code} - {response.text}")
                
        except requests.exceptions.RequestException as e:
            raise Exception(f"网络请求错误: {str(e)}")
        except Exception as e:
            raise Exception(f"LLM判断错误: {str(e)}")
    
    def _parse_text_response(self, response_text: str) -> Dict[str, Any]:
        """
        从文本响应中解析判断结果（备用方法）
        
        Args:
            response_text: LLM的文本响应
            
        Returns:
            解析后的结果字典
        """
        # 简单的文本解析逻辑
        response_lower = response_text.lower()
        
        # 判断是否匹配
        matched = any(keyword in response_lower for keyword in ['true', '是', '匹配', '符合', '包含'])
        
        # 尝试提取置信度
        confidence = 0.5  # 默认置信度
        import re
        conf_match = re.search(r'confidence["\s]*:?["\s]*(\d+\.?\d*)', response_lower)
        if conf_match:
            try:
                confidence = float(conf_match.group(1))
                if confidence > 1.0:
                    confidence = confidence / 100.0  # 如果是百分比形式
            except ValueError:
                pass
        
        return {
            'matched': matched,
            'confidence': confidence,
            'reasoning': response_text[:200] + '...' if len(response_text) > 200 else response_text,
            'tokens_used': 0  # 默认值，会在调用处被重新设置
        }


class NodeType(Enum):
    """节点类型枚举"""
    CONDITION = "CONDITION"
    ACTION = "ACTION"


class RiskLevel(Enum):
    """风险等级枚举"""
    SAFE = "safe"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class DetectionResult:
    """检测结果数据类"""
    node_id: str
    description: str
    matched: bool
    risk_level: RiskLevel
    confidence: float
    evidence: List[str]
    children_results: List['DetectionResult']
    sensitive_excerpt: str = ""  # 敏感内容摘录
    original_length: int = 0  # 原文长度
    tokens_used: int = 0  # LLM调用消耗的token数量


class ContentSafetyNode:
    """内容安全检测节点"""
    
    def __init__(self, node_id: str, description: str, node_type: NodeType, 
                 keywords: List[str] = None, patterns: List[str] = None,
                 risk_level: RiskLevel = RiskLevel.MEDIUM, 
                 llm_prompt: str = None):
        """
        初始化检测节点
        
        Args:
            node_id: 节点ID
            description: 节点描述
            node_type: 节点类型
            keywords: 关键词列表（作为LLM判断的辅助）
            patterns: 正则表达式模式列表（作为LLM判断的辅助）
            risk_level: 风险等级
            llm_prompt: LLM判断提示词
        """
        self.node_id = node_id
        self.description = description
        self.node_type = node_type
        self.keywords = keywords or []
        self.patterns = patterns or []
        self.risk_level = risk_level
        self.llm_prompt = llm_prompt
        self.children: List[ContentSafetyNode] = []
        self.parent: Optional[ContentSafetyNode] = None
    
    def add_child(self, child: 'ContentSafetyNode'):
        """添加子节点"""
        child.parent = self
        self.children.append(child)
    
    def detect(self, content: str, llm_client=None) -> DetectionResult:
        """
        通过LLM智能检测内容是否匹配当前节点条件
        
        Args:
            content: 待检测内容
            llm_client: LLM客户端实例
            
        Returns:
            检测结果
        """
        evidence = []
        matched = False
        confidence = 0.0
        tokens_used = 0  # 初始化token使用量
        
        # 如果有LLM客户端且有提示词，使用LLM进行智能判断
        if llm_client and self.llm_prompt:
            try:
                llm_result = llm_client.judge_content(content, self.llm_prompt, self.description)
                matched = llm_result['matched']
                confidence = llm_result['confidence']
                tokens_used += llm_result.get('tokens_used', 0)  # 累计token使用量
                evidence.append(f"LLM判断: {llm_result['reasoning']}")
            except Exception as e:
                evidence.append(f"LLM判断失败: {str(e)}")
                # 降级到传统匹配方式
                matched, confidence = self._fallback_detection(content, evidence)
        else:
            # 使用传统的关键词和模式匹配作为后备
            matched, confidence = self._fallback_detection(content, evidence)
        
        # 递归检测子节点
        children_results = []
        # 根节点总是检测子节点，其他节点只有在匹配时才检测子节点
        should_check_children = (self.node_id == "1") or matched
        
        if should_check_children:
            for child in self.children:
                child_result = child.detect(content, llm_client)
                children_results.append(child_result)
                tokens_used += child_result.tokens_used  # 累计子节点的token使用量
                # 如果子节点匹配，父节点也应该匹配（除了根节点）
                if child_result.matched:
                    if self.node_id != "1":  # 根节点不受子节点影响
                        matched = True
                    confidence = max(confidence, child_result.confidence * 0.8)
        
        # 提取敏感内容片段
        sensitive_excerpt = self._extract_sensitive_excerpt(content, matched, evidence)
        
        return DetectionResult(
            node_id=self.node_id,
            description=self.description,
            matched=matched,
            risk_level=self.risk_level,
            confidence=confidence,
            evidence=evidence,
            children_results=children_results,
            sensitive_excerpt=sensitive_excerpt,
            original_length=len(content),
            tokens_used=tokens_used  # 添加token使用量
        )
    
    def _fallback_detection(self, content: str, evidence: List[str]) -> tuple[bool, float]:
        """
        后备检测方法：使用关键词和模式匹配
        
        Args:
            content: 待检测内容
            evidence: 证据列表
            
        Returns:
            (是否匹配, 置信度)
        """
        matched = False
        confidence = 0.0
        
        # 关键词匹配
        for keyword in self.keywords:
            if keyword.lower() in content.lower():
                evidence.append(f"关键词匹配: {keyword}")
                matched = True
                confidence += 0.3
        
        # 正则表达式匹配
        for pattern in self.patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            if matches:
                evidence.append(f"模式匹配: {pattern} -> {matches}")
                matched = True
                confidence += 0.4
        
        # 限制置信度在0-1之间
        confidence = min(confidence, 1.0)
        
        return matched, confidence
    
    def _extract_sensitive_excerpt(self, content: str, matched: bool, evidence: List[str]) -> str:
        """
        提取敏感内容片段
        
        Args:
            content: 原始内容
            matched: 是否匹配
            evidence: 证据列表
            
        Returns:
            敏感内容摘录
        """
        if not matched or not content:
            return ""
        
        # 如果内容较短（少于300字符），直接返回全文
        if len(content) <= 300:
            return content
        
        # 尝试从证据中提取关键词
        keywords_found = []
        for ev in evidence:
            if "关键词匹配:" in ev:
                keyword = ev.split("关键词匹配:")[1].strip()
                keywords_found.append(keyword)
        
        # 如果没有找到关键词，从节点关键词中查找
        if not keywords_found:
            for keyword in self.keywords:
                if keyword.lower() in content.lower():
                    keywords_found.append(keyword)
        
        if not keywords_found:
            # 如果没有关键词，返回前200字符
            return content[:200] + "..."
        
        # 找到第一个匹配关键词的位置
        best_excerpt = ""
        for keyword in keywords_found:
            pos = content.lower().find(keyword.lower())
            if pos != -1:
                # 提取关键词前后各100个字符
                start = max(0, pos - 100)
                end = min(len(content), pos + len(keyword) + 100)
                excerpt = content[start:end]
                
                # 如果不是从开头开始，添加省略号
                if start > 0:
                    excerpt = "..." + excerpt
                # 如果不是到结尾，添加省略号
                if end < len(content):
                    excerpt = excerpt + "..."
                
                # 选择最长的摘录
                if len(excerpt) > len(best_excerpt):
                    best_excerpt = excerpt
        
        return best_excerpt or content[:200] + "..."


class EnhancedContentSafetyAgentDB:
    """增强版内容安全检测Agent - 数据库版本"""
    
    def __init__(self, llm_config: Dict[str, Any] = None, instruction_set_id: int = 13):
        """
        初始化增强版内容安全检测Agent
        
        Args:
            llm_config: LLM配置字典
            instruction_set_id: 指令集ID，默认为13
        """
        self.llm_client = None
        self.instruction_set_id = instruction_set_id
        
        # 初始化LLM客户端
        if llm_config and llm_config.get('type') == 'ollama':
            self.llm_client = OllamaLLMClient(llm_config)
        
        # 从数据库加载检测树
        self.root_node = self._load_detection_tree_from_db()
    
    def _load_detection_tree_from_db(self) -> ContentSafetyNode:
        """
        从数据库中加载检测树结构
        
        Returns:
            根节点
        """
        print(f"正在从数据库加载指令集 {self.instruction_set_id}...")
        
        # 初始化数据库服务
        db = RouterDBService()
        
        # 查询指令集中的所有节点
        query_sql = """
        SELECT id, parent_id, node_type, title, description, condition_text, keywords, condition_text,risk_level,
               result_value, result_confidence, sort_order, condition_config
        FROM instruction_nodes 
        WHERE instruction_set_id = %s 
        ORDER BY sort_order, id
        """
        
        result = db.service.execute_sql('agent_db', query_sql, (self.instruction_set_id,))
        print(result)
        if not result['success'] or not result['data']:
            raise Exception(f"无法从数据库加载指令集 {self.instruction_set_id}")
        
        nodes_data = result['data']
        print(f"从数据库加载了 {len(nodes_data)} 个节点")
        
        # 构建节点映射
        nodes_map = {}
        
        # 按层级组织节点
        nodes_by_parent = {}
        for node in nodes_data:
            parent_id = node['parent_id']
            if parent_id not in nodes_by_parent:
                nodes_by_parent[parent_id] = []
            nodes_by_parent[parent_id].append(node)
        
        # 递归创建节点并生成编号
        def create_nodes_with_numbers(parent_id, parent_number=""):
            if parent_id not in nodes_by_parent:
                return
            
            for i, node_data in enumerate(nodes_by_parent[parent_id], 1):
                # 生成节点编号，类似instruction_sets.py的机制
                if parent_number:
                    node_number = f"{parent_number}.{i}"
                else:
                    node_number = str(i)
                
                description = node_data['description'] or node_data['title']
                
                # 解析condition_config
                condition_config = {}
                if node_data['condition_config']:
                    try:
                        condition_config = json.loads(node_data['condition_config'])
                    except json.JSONDecodeError:
                        print(f"警告: 节点 {node_number} 的condition_config解析失败")
                
                # 提取配置信息
                #print(node_data["keywords"],node_data["condition_text"])
                # print("-----------")
                # import sys
                # sys.exit()
                keywords = condition_config.get('keywords', [])
                patterns = condition_config.get('patterns', [])
                llm_prompt = condition_config.get('llm_prompt', node_data['condition_text'])
                risk_level_str = condition_config.get('risk_level', 'medium')

                keywords=node_data["keywords"]
                llm_prompt=node_data["condition_text"]
                risk_level_str=node_data["risk_level"]
                
                # 转换风险等级
                try:
                    risk_level = RiskLevel(risk_level_str)
                except ValueError:
                    risk_level = RiskLevel.MEDIUM
                
                # 转换节点类型
                node_type = NodeType.CONDITION if node_data['node_type'] == 'CONDITION' else NodeType.ACTION
                
                # 创建节点
                node = ContentSafetyNode(
                    node_id=node_number,  # 使用层级编号
                    description=description,
                    node_type=node_type,
                    keywords=keywords,
                    patterns=patterns,
                    risk_level=risk_level,
                    llm_prompt=llm_prompt
                )
                
                nodes_map[node_data['id']] = node
                
                # 递归创建子节点
                create_nodes_with_numbers(node_data['id'], node_number)
        
        # 从根节点开始创建
        create_nodes_with_numbers(None)
        
        # 第二遍：建立父子关系
        root_node = None
        for node_data in nodes_data:
            current_node = nodes_map[node_data['id']]
            
            if node_data['parent_id'] is None:
                # 这是根节点
                root_node = current_node
            else:
                # 添加到父节点
                parent_node = nodes_map.get(node_data['parent_id'])
                if parent_node:
                    parent_node.add_child(current_node)
        
        if root_node is None:
            raise Exception("未找到根节点")
        
        print(f"检测树构建完成，根节点: {root_node.node_id}")
        
        # 打印指令集内容
        self._print_instruction_set(nodes_data, nodes_map)
        
        return root_node
    
    def _print_instruction_set(self, nodes_data: List[Dict], nodes_map: Dict):
        """
        打印指令集内容
        
        Args:
            nodes_data: 节点数据列表
            nodes_map: 节点映射字典
        """
        print("\n" + "="*80)
        print(f"指令集 {self.instruction_set_id} 内容:")
        print("="*80)
        
        # 按层级组织节点
        nodes_by_parent = {}
        for node in nodes_data:
            parent_id = node['parent_id']
            if parent_id not in nodes_by_parent:
                nodes_by_parent[parent_id] = []
            nodes_by_parent[parent_id].append(node)
        
        # 递归打印节点树
        def print_node_tree(parent_id, level=0):
            if parent_id not in nodes_by_parent:
                return
            
            for node in nodes_by_parent[parent_id]:
                indent = "  " * level
                # 从nodes_map中获取已创建的节点，使用其node_id
                created_node = nodes_map.get(node['id'])
                if created_node:
                    node_number = created_node.node_id
                else:
                    node_number = "未知"
                description = node['description'] or node['title']
                
                # 解析condition_config获取风险等级
                risk_level = "medium"
                if node['condition_config']:
                    try:
                        config = json.loads(node['condition_config'])
                        risk_level = config.get('risk_level', 'medium')
                    except:
                        pass
                
                print(f"{indent}├─ {node_number}: {description} (风险等级: {risk_level})")
                
                # 递归打印子节点
                print_node_tree(node['id'], level + 1)
        
        # 从根节点开始打印
        print_node_tree(None)
        print("="*80 + "\n")
    
    def detect_content(self, content: str) -> DetectionResult:
        """
        检测内容安全性
        
        Args:
            content: 待检测的内容
            
        Returns:
            检测结果
        """
        return self.root_node.detect(content, self.llm_client)
    
    def _calculate_overall_risk(self, result: DetectionResult) -> RiskLevel:
        """
        计算整体风险等级
        
        Args:
            result: 检测结果
            
        Returns:
            整体风险等级
        """
        if not result.matched:
            return RiskLevel.SAFE
        
        # 收集所有匹配节点的风险等级
        risk_levels = []
        
        def collect_risks(node_result):
            if node_result.matched:
                risk_levels.append(node_result.risk_level)
            for child in node_result.children_results:
                collect_risks(child)
        
        collect_risks(result)
        
        if not risk_levels:
            return RiskLevel.SAFE
        
        # 返回最高风险等级
        risk_priority = {
            RiskLevel.SAFE: 0,
            RiskLevel.LOW: 1,
            RiskLevel.MEDIUM: 2,
            RiskLevel.HIGH: 3,
            RiskLevel.CRITICAL: 4
        }
        
        max_risk = max(risk_levels, key=lambda x: risk_priority[x])
        return max_risk
    
    def _has_matched_children(self, result: DetectionResult) -> bool:
        """
        检查是否有匹配的子节点
        
        Args:
            result: 检测结果
            
        Returns:
            是否有匹配的子节点
        """
        for child in result.children_results:
            if child.matched or self._has_matched_children(child):
                return True
        return False
    
    def _get_first_matched_excerpt(self, result: DetectionResult) -> str:
        """
        获取第一个匹配节点的敏感内容摘录
        
        Args:
            result: 检测结果
            
        Returns:
            敏感内容摘录
        """
        if result.matched and result.sensitive_excerpt:
            return result.sensitive_excerpt
        
        for child in result.children_results:
            excerpt = self._get_first_matched_excerpt(child)
            if excerpt:
                return excerpt
        
        return ""


def main():
    """
    主函数：测试数据库版本的内容安全检测Agent
    """
    print("测试增强版内容安全检测Agent - 数据库版本")
    
    # 创建Agent实例
    agent = EnhancedContentSafetyAgentDB(instruction_set_id=13)
    
    # 测试内容
    test_content = "我觉得社会主义制度有很多问题"
    
    print(f"\n测试内容: {test_content}")
    print("-" * 60)
    
    # 执行检测
    result = agent.detect_content(test_content)
    
    # 计算总体风险等级
    overall_risk = agent._calculate_overall_risk(result)
    
    # 输出结果
    print(f"检测结果: {result.matched}")
    print(f"风险等级: {overall_risk.value}")
    print(f"置信度: {result.confidence:.2f}")
    
    if result.evidence:
        print(f"证据: {result.evidence}")
    
    if result.sensitive_excerpt:
        print(f"敏感内容摘录: {result.sensitive_excerpt}")


if __name__ == "__main__":
    main()