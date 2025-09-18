#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
增强版内容安全检测Agent
基于用户提供的分类数据构建的更精确的检测树结构
"""

import json
import re
import requests
from typing import Dict, List, Any, Optional, Set
from dataclasses import dataclass
from enum import Enum


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
        self.api_url = f"{self.base_url.rstrip('/')}/api/generate"
        
    def judge_content(self, content: str, prompt: str, node_description: str) -> Dict[str, Any]:
        """
        使用LLM判断内容是否符合特定条件
        
        Args:
            content: 待判断的内容
            prompt: 判断提示词
            node_description: 节点描述
            
        Returns:
            包含判断结果的字典: {matched: bool, confidence: float, reasoning: str}
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
        # print("*"*50)
        # print(f"LLM请求提示词: {full_prompt}")
        # print("*"*50)
        try:
            # 发送请求到Ollama
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
            
            if response.status_code == 200:
                result = response.json()
                llm_response = result.get('response', '')
                
                # 尝试解析JSON响应
                try:
                    parsed_result = json.loads(llm_response)
                    return {
                        'matched': bool(parsed_result.get('matched', False)),
                        'confidence': float(parsed_result.get('confidence', 0.0)),
                        'reasoning': str(parsed_result.get('reasoning', '无法获取判断理由'))
                    }
                except json.JSONDecodeError:
                    # 如果JSON解析失败，尝试从文本中提取信息
                    return self._parse_text_response(llm_response)
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
            'reasoning': response_text[:200] + '...' if len(response_text) > 200 else response_text
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
        
        # 如果有LLM客户端且有提示词，使用LLM进行智能判断
        if llm_client and self.llm_prompt:
            try:
                llm_result = llm_client.judge_content(content, self.llm_prompt, self.description)
                matched = llm_result['matched']
                confidence = llm_result['confidence']
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
                # 如果子节点匹配，父节点也应该匹配（除了根节点）
                if child_result.matched:
                    if self.node_id != "1":  # 根节点不受子节点影响
                        matched = True
                        confidence = max(confidence, child_result.confidence * 0.8)
                    else:
                        # 根节点：如果有子节点匹配，则根节点也匹配，并采用最高风险等级
                        matched = True
                        confidence = max(confidence, child_result.confidence)
        
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
            original_length=len(content)
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
        
        # 如果内容较短（少于200字符），直接返回全文
        if len(content) <= 200:
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
            # 如果没有关键词，返回前100字符
            return content[:100] + "..."
        
        # 找到第一个匹配关键词的位置
        best_excerpt = ""
        for keyword in keywords_found:
            pos = content.lower().find(keyword.lower())
            if pos != -1:
                # 提取关键词前后各50个字符
                start = max(0, pos - 50)
                end = min(len(content), pos + len(keyword) + 50)
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
        
        return best_excerpt or content[:100] + "..."


class EnhancedContentSafetyAgent:
    """增强版内容安全检测Agent"""
    
    def __init__(self, llm_config: Dict[str, Any] = None):
        """
        初始化增强版内容安全检测Agent
        
        Args:
            llm_config: LLM配置字典
        """
        self.llm_client = None
        
        # 初始化LLM客户端
        if llm_config and llm_config.get('type') == 'ollama':
            self.llm_client = OllamaLLMClient(llm_config)
        
        self.root_node = self._build_enhanced_detection_tree()
    
    def _build_enhanced_detection_tree(self) -> ContentSafetyNode:
        """
        构建基于用户数据的增强版检测树结构
        """
        # 第1级：根节点
        root = ContentSafetyNode(
            node_id="1",
            description="内容安全检测",
            node_type=NodeType.CONDITION,
            keywords=["."],  # 匹配任何内容
            risk_level=RiskLevel.SAFE,
            llm_prompt="请对以下内容进行初步安全性检测。如果内容包含任何文字，返回匹配=true以便进行详细检测；如果内容为空或无意义，返回匹配=false。"
        )
        
        # 第2级：主要分类（根据用户提供的分类重新整理）
        
        # 2.1 国家制度
        national_system = ContentSafetyNode(
            node_id="2.1",
            description="国家制度相关内容检测",
            node_type=NodeType.CONDITION,
            keywords=["国家制度", "社会主义制度", "中国道路", "宪政制度", "政治制度", "国家体制", "制度缺陷", "制度问题", "体制问题"],
            risk_level=RiskLevel.HIGH,
            llm_prompt="请判断以下内容是否涉及攻击国家制度的内容，包括攻击社会主义制度、中国道路模式、宪政制度等。"
        )
        
        # 2.1.1 攻击社会主义制度
        attack_socialist_system = ContentSafetyNode(
            node_id="2.1.1",
            description="攻击社会主义制度内容检测",
            node_type=NodeType.CONDITION,
            keywords=["社会主义制度", "社会主义道路", "社会主义核心价值观", "马克思主义", "共产主义", "社会主义优越性"],
            risk_level=RiskLevel.CRITICAL,
            llm_prompt="请判断以下内容是否涉及攻击社会主义制度的内容，包括否定社会主义道路、攻击社会主义核心价值观等。"
        )
        
        # 2.1.2 攻击中国道路模式
        attack_china_model = ContentSafetyNode(
            node_id="2.1.2",
            description="攻击中国道路模式内容检测",
            node_type=NodeType.CONDITION,
            keywords=["中国道路", "中国模式", "中国特色", "发展道路", "改革开放", "中国经验"],
            risk_level=RiskLevel.CRITICAL,
            llm_prompt="请判断以下内容是否涉及攻击中国道路模式的内容，包括否定中国特色发展道路、攻击改革开放政策等。"
        )
        
        # 2.1.3 攻击宪政制度
        attack_constitutional_system = ContentSafetyNode(
            node_id="2.1.3",
            description="攻击宪政制度内容检测",
            node_type=NodeType.CONDITION,
            keywords=["宪政制度", "宪法", "人民代表大会", "政治制度", "民主集中制", "人民当家作主"],
            risk_level=RiskLevel.CRITICAL,
            llm_prompt="请判断以下内容是否涉及攻击宪政制度的内容，包括否定人民代表大会制度、攻击民主集中制等。"
        )
        
        # 2.2 国家统一
        national_unity = ContentSafetyNode(
            node_id="2.2",
            description="国家统一相关内容检测",
            node_type=NodeType.CONDITION,
            keywords=["国家统一", "一国两制", "颜色革命", "台湾", "香港", "西藏", "新疆", "内蒙古", "分裂", "独立"],
            risk_level=RiskLevel.CRITICAL,
            llm_prompt="请判断以下内容是否涉及危害国家统一的内容，包括反对一国两制、支持颜色革命、涉台涉港涉藏涉疆涉蒙等分裂内容。"
        )
        
        # 2.2.1 反对一国两制
        oppose_one_country_two_systems = ContentSafetyNode(
            node_id="2.2.1",
            description="反对一国两制内容检测",
            node_type=NodeType.CONDITION,
            keywords=["一国两制", "港人治港", "澳人治澳", "高度自治", "基本法"],
            risk_level=RiskLevel.CRITICAL,
            llm_prompt="请判断以下内容是否涉及反对一国两制的内容，包括否定港人治港、澳人治澳、高度自治等。"
        )
        
        # 2.2.2 支持颜色革命
        support_color_revolution = ContentSafetyNode(
            node_id="2.2.2",
            description="支持颜色革命内容检测",
            node_type=NodeType.CONDITION,
            keywords=["颜色革命", "政权更迭", "街头政治", "暴力抗议", "推翻政府"],
            risk_level=RiskLevel.CRITICAL,
            llm_prompt="请判断以下内容是否涉及支持颜色革命的内容，包括煽动政权更迭、支持暴力抗议等。"
        )
        
        # 2.2.3 涉台内容
        taiwan_related = ContentSafetyNode(
            node_id="2.2.3",
            description="涉台分裂内容检测",
            node_type=NodeType.CONDITION,
            keywords=["台湾独立", "台独", "中华民国", "两岸分治", "台海冲突"],
            risk_level=RiskLevel.CRITICAL,
            llm_prompt="请判断以下内容是否涉及台湾分裂的内容，包括支持台独、否定一个中国原则等。"
        )
        
        # 2.2.4 涉港内容
        hongkong_related = ContentSafetyNode(
            node_id="2.2.4",
            description="涉港分裂内容检测",
            node_type=NodeType.CONDITION,
            keywords=["香港独立", "港独", "光复香港", "时代革命", "反送中"],
            risk_level=RiskLevel.CRITICAL,
            llm_prompt="请判断以下内容是否涉及香港分裂的内容，包括支持港独、煽动反政府活动等。"
        )
        
        # 2.2.5 涉藏内容
        tibet_related = ContentSafetyNode(
            node_id="2.2.5",
            description="涉藏分裂内容检测",
            node_type=NodeType.CONDITION,
            keywords=["西藏独立", "藏独", "达赖喇嘛", "流亡政府", "自由西藏"],
            risk_level=RiskLevel.CRITICAL,
            llm_prompt="请判断以下内容是否涉及西藏分裂的内容，包括支持藏独、宣传达赖集团等。"
        )
        
        # 2.2.6 涉疆内容
        xinjiang_related = ContentSafetyNode(
            node_id="2.2.6",
            description="涉疆分裂内容检测",
            node_type=NodeType.CONDITION,
            keywords=["新疆独立", "疆独", "东突厥斯坦", "维吾尔族", "种族灭绝"],
            risk_level=RiskLevel.CRITICAL,
            llm_prompt="请判断以下内容是否涉及新疆分裂的内容，包括支持疆独、传播不实信息等。"
        )
        
        # 2.2.7 涉蒙内容
        mongolia_related = ContentSafetyNode(
            node_id="2.2.7",
            description="涉蒙分裂内容检测",
            node_type=NodeType.CONDITION,
            keywords=["内蒙古独立", "蒙独", "南蒙古", "蒙古族", "民族自决"],
            risk_level=RiskLevel.CRITICAL,
            llm_prompt="请判断以下内容是否涉及内蒙古分裂的内容，包括支持蒙独、煽动民族分裂等。"
        )
        
        # 2.3 领土完整
        territory_integrity = ContentSafetyNode(
            node_id="2.3",
            description="领土完整相关内容检测",
            node_type=NodeType.CONDITION,
            keywords=["领土完整", "主权争议", "边界问题", "海域争端", "岛屿争议"],
            risk_level=RiskLevel.HIGH,
            llm_prompt="请判断以下内容是否涉及危害领土完整的内容，包括否定中国领土主权、支持分裂活动等。"
        )
        
        # 2.3.1 地图错误标注
        map_misrepresentation = ContentSafetyNode(
            node_id="2.3.1",
            description="地图错误标注检测",
            node_type=NodeType.CONDITION,
            keywords=["地图标注", "领土标识", "国界线", "行政区划", "主权标示"],
            risk_level=RiskLevel.HIGH,
            llm_prompt="请判断以下内容是否涉及地图错误标注，包括错误标示中国领土、否定主权归属等。"
        )
        
        # 2.3.2 新疆西藏边界问题
        xinjiang_tibet_boundary = ContentSafetyNode(
            node_id="2.3.2",
            description="新疆西藏边界问题检测",
            node_type=NodeType.CONDITION,
            keywords=["阿克赛钦", "藏南地区", "中印边界", "拉达克", "边界争议"],
            risk_level=RiskLevel.HIGH,
            llm_prompt="请判断以下内容是否涉及新疆西藏边界争议，包括否定中国对争议地区的主权等。"
        )
        
        # 2.3.3 海洋领土争端
        maritime_territory_disputes = ContentSafetyNode(
            node_id="2.3.3",
            description="海洋领土争端检测",
            node_type=NodeType.CONDITION,
            keywords=["南海争议", "钓鱼岛", "黄岩岛", "西沙群岛", "南沙群岛"],
            risk_level=RiskLevel.HIGH,
            llm_prompt="请判断以下内容是否涉及海洋领土争端，包括否定中国对南海、钓鱼岛等的主权。"
        )
        
        # 2.3.4 历史争议领土
        historical_disputed_territories = ContentSafetyNode(
            node_id="2.3.4",
            description="历史争议领土检测",
            node_type=NodeType.CONDITION,
            keywords=["历史领土", "割让土地", "不平等条约", "领土变迁", "主权归属"],
            risk_level=RiskLevel.MEDIUM,
            llm_prompt="请判断以下内容是否涉及历史争议领土问题，包括质疑中国对历史领土的合法权益等。"
        )
        
        # 2.3.5 麦克马洪线问题
        mcmahon_line_issues = ContentSafetyNode(
            node_id="2.3.5",
            description="麦克马洪线问题检测",
            node_type=NodeType.CONDITION,
            keywords=["麦克马洪线", "中印边界", "藏南", "阿鲁纳恰尔邦", "边界划分"],
            risk_level=RiskLevel.HIGH,
            llm_prompt="请判断以下内容是否涉及麦克马洪线问题，包括承认非法边界线、否定中国领土主权等。"
        )
        
        # 构建树结构
        root.add_child(national_system)
        
        # 添加国家制度的子节点
        national_system.add_child(attack_socialist_system)
        national_system.add_child(attack_china_model)
        national_system.add_child(attack_constitutional_system)
        
        root.add_child(national_unity)
        
        # 添加国家统一的子节点
        national_unity.add_child(oppose_one_country_two_systems)
        national_unity.add_child(support_color_revolution)
        national_unity.add_child(taiwan_related)
        national_unity.add_child(hongkong_related)
        national_unity.add_child(tibet_related)
        national_unity.add_child(xinjiang_related)
        national_unity.add_child(mongolia_related)
        
        root.add_child(territory_integrity)
        
        # 添加领土完整的子节点
        territory_integrity.add_child(map_misrepresentation)
        territory_integrity.add_child(xinjiang_tibet_boundary)
        territory_integrity.add_child(maritime_territory_disputes)
        territory_integrity.add_child(historical_disputed_territories)
        territory_integrity.add_child(mcmahon_line_issues)
        
        return root
    
    def detect_content(self, content: str) -> DetectionResult:
        """
        检测内容安全性
        
        Args:
            content: 待检测的内容
            
        Returns:
            检测结果
        """
        result = self.root_node.detect(content, self.llm_client)
        
        # 计算整体风险等级：从所有匹配的子节点中选择最高风险等级
        overall_risk = self._calculate_overall_risk(result)
        
        # 检查是否有子节点匹配
        has_matched_children = self._has_matched_children(result)
        
        # 更新结果的风险等级和匹配状态
        result.risk_level = overall_risk
        if has_matched_children:
            result.matched = True
            # 如果有匹配的子节点但根节点没有敏感摘录，使用第一个匹配子节点的摘录
            if not result.sensitive_excerpt:
                first_matched_excerpt = self._get_first_matched_excerpt(result)
                if first_matched_excerpt:
                    result.sensitive_excerpt = first_matched_excerpt
        
        return result
    
    def get_all_matched_nodes(self, result: DetectionResult) -> List[Dict[str, Any]]:
        """
        获取所有命中的节点信息
        
        Args:
            result: 检测结果
            
        Returns:
            所有命中节点的详细信息列表
        """
        matched_nodes = []
        
        def collect_matched_nodes(node_result: DetectionResult, path: str = ""):
            current_path = f"{path}/{node_result.node_id}" if path else node_result.node_id
            
            if node_result.matched:
                matched_nodes.append({
                    "node_id": node_result.node_id,
                    "description": node_result.description,
                    "path": current_path,
                    "risk_level": node_result.risk_level.value,
                    "confidence": node_result.confidence,
                    "evidence": node_result.evidence,
                    "sensitive_excerpt": node_result.sensitive_excerpt,
                    "reasons": node_result.evidence  # 命中理由
                })
            
            # 递归处理子节点
            for child_result in node_result.children_results:
                collect_matched_nodes(child_result, current_path)
        
        collect_matched_nodes(result)
        return matched_nodes
    
    def get_detection_tree_structure(self, result: DetectionResult) -> Dict[str, Any]:
        """
        获取检测树结构信息
        
        Args:
            result: 检测结果
            
        Returns:
            树结构信息
        """
        def build_tree_structure(node_result: DetectionResult) -> Dict[str, Any]:
            return {
                "node_id": node_result.node_id,
                "description": node_result.description,
                "matched": node_result.matched,
                "risk_level": node_result.risk_level.value,
                "confidence": node_result.confidence,
                "evidence": node_result.evidence,
                "sensitive_excerpt": node_result.sensitive_excerpt,
                "children": [build_tree_structure(child) for child in node_result.children_results]
            }
        
        return build_tree_structure(result)
    
    def get_comprehensive_detection_result(self, content: str) -> Dict[str, Any]:
        """
        获取全面的检测结果，包括所有命中节点和树结构
        
        Args:
            content: 待检测的内容
            
        Returns:
            包含所有信息的检测结果
        """
        result = self.detect_content(content)
        matched_nodes = self.get_all_matched_nodes(result)
        tree_structure = self.get_detection_tree_structure(result)
        
        return {
            "overall_result": {
                "matched": result.matched,
                "risk_level": result.risk_level.value,
                "confidence": result.confidence,
                "evidence": result.evidence,
                "sensitive_excerpt": result.sensitive_excerpt
            },
            "matched_nodes": matched_nodes,
            "tree_structure": tree_structure,
            "total_matched_count": len(matched_nodes)
        }
    
    def _calculate_overall_risk(self, result: DetectionResult) -> RiskLevel:
        """
        计算整体风险等级：从所有匹配的节点中选择最高风险等级
        
        Args:
            result: 检测结果
            
        Returns:
            整体风险等级
        """
        matched_nodes = []
        
        def collect_matched_nodes(node_result: DetectionResult):
            if node_result.matched:
                matched_nodes.append(node_result)
            for child in node_result.children_results:
                collect_matched_nodes(child)
        
        collect_matched_nodes(result)
        
        if not matched_nodes:
            return RiskLevel.SAFE
        
        # 风险等级评分
        risk_scores = {
            RiskLevel.SAFE: 0,
            RiskLevel.LOW: 1,
            RiskLevel.MEDIUM: 2,
            RiskLevel.HIGH: 3,
            RiskLevel.CRITICAL: 4
        }
        
        # 找到最高风险等级
        max_risk_score = max(risk_scores[node.risk_level] for node in matched_nodes)
        
        for level, score in risk_scores.items():
            if score == max_risk_score:
                return level
        
        return RiskLevel.SAFE
    
    def _has_matched_children(self, result: DetectionResult) -> bool:
        """
        检查是否有匹配的子节点
        
        Args:
            result: 检测结果
            
        Returns:
            是否有匹配的子节点
        """
        def check_children(node_result: DetectionResult) -> bool:
            # 检查当前节点（排除根节点）
            if node_result.node_id != "1" and node_result.matched:
                return True
            # 递归检查子节点
            for child in node_result.children_results:
                if check_children(child):
                    return True
            return False
        
        return check_children(result)
    
    def _get_first_matched_excerpt(self, result: DetectionResult) -> str:
        """
        获取第一个匹配节点的敏感摘录
        
        Args:
            result: 检测结果
            
        Returns:
            第一个匹配节点的敏感摘录
        """
        def find_first_excerpt(node_result: DetectionResult) -> str:
            # 检查当前节点（排除根节点）
            if node_result.node_id != "1" and node_result.matched and node_result.sensitive_excerpt:
                return node_result.sensitive_excerpt
            # 递归检查子节点
            for child in node_result.children_results:
                excerpt = find_first_excerpt(child)
                if excerpt:
                    return excerpt
            return ""
        
        return find_first_excerpt(result)
    
    def print_detection_tree(self, node: ContentSafetyNode = None, level: int = 0):
        """
        打印检测树结构
        
        Args:
            node: 当前节点，默认为根节点
            level: 当前层级
        """
        if node is None:
            node = self.root_node
        
        indent = "  " * level
        print(f"{indent}{node.node_id}: {node.description} (风险等级: {node.risk_level.value})")
        
        for child in node.children:
            self.print_detection_tree(child, level + 1)


# 使用示例
if __name__ == "__main__":
    # 配置LLM客户端
    llm_config = {
        "type": "ollama",
        "model": "qwen2.5:7b",
        "base_url": "http://bt.acoming.net:11868"
    }
    
    # 创建检测器
    detector = EnhancedContentSafetyAgent(llm_config)
    
    # 打印检测树结构
    print("增强版内容安全检测树结构：")
    detector.print_detection_tree()
    
    # 测试内容检测
    test_content = "我觉得社会主义制度有很多问题"
    
    # 使用新的全面检测方法
    comprehensive_result = detector.get_comprehensive_detection_result(test_content)
    
    print(f"\n检测内容: {test_content}")
    print(f"\n=== 整体检测结果 ===")
    print(f"检测结果: {comprehensive_result['overall_result']['matched']}")
    print(f"风险等级: {comprehensive_result['overall_result']['risk_level']}")
    print(f"置信度: {comprehensive_result['overall_result']['confidence']}")
    print(f"证据: {comprehensive_result['overall_result']['evidence']}")
    print(f"敏感摘录: {comprehensive_result['overall_result']['sensitive_excerpt']}")
    
    print(f"\n=== 命中节点详情 (共{comprehensive_result['total_matched_count']}个) ===")
    for i, node in enumerate(comprehensive_result['matched_nodes'], 1):
        print(f"\n{i}. 节点ID: {node['node_id']}")
        print(f"   描述: {node['description']}")
        print(f"   路径: {node['path']}")
        print(f"   风险等级: {node['risk_level']}")
        print(f"   置信度: {node['confidence']}")
        print(f"   命中理由: {node['reasons']}")
        print(f"   敏感摘录: {node['sensitive_excerpt']}")
    
    print(f"\n=== 完整树结构 ===")
    print(json.dumps(comprehensive_result['tree_structure'], ensure_ascii=False, indent=2))