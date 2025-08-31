from typing import Dict, List, Any, Optional
from sqlalchemy.orm import Session
from app.crud.instruction_set import instruction_node
from app.crud.model_service_config import model_service_config_crud
import json
import re
import requests
from dataclasses import dataclass
from enum import Enum


class RiskLevel(str, Enum):
    """风险等级枚举"""
    SAFE = "safe"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class ReviewResult:
    """审读结果数据类"""
    node_id: str
    description: str
    matched: bool
    risk_level: RiskLevel
    confidence: float
    evidence: List[str]
    sensitive_excerpt: str = ""
    original_length: int = 0
    children_results: List['ReviewResult'] = None

    def __post_init__(self):
        if self.children_results is None:
            self.children_results = []


class OllamaLLMClient:
    """Ollama LLM客户端"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        初始化Ollama客户端
        
        Args:
            config: 模型服务配置字典
        """
        self.model = config.get('model_name', 'qwen2.5:7b')
        self.base_url = config.get('api_url', 'http://localhost:11434')
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
        
        print(f"\n🤖 LLM调用开始:")
        print(f"   📝 节点描述: {node_description}")
        print(f"   🎯 判断标准: {prompt}")
        print(f"   📄 待检测内容: {content[:100]}{'...' if len(content) > 100 else ''}")
        print(f"   🔗 API地址: {self.api_url}")
        print(f"   🧠 模型: {self.model}")
        
        try:
            # 发送请求到Ollama
            request_data = {
                "model": self.model,
                "prompt": full_prompt,
                "stream": False,
                "format": "json"
            }
            
            print(f"   📤 发送请求数据: {json.dumps(request_data, ensure_ascii=False, indent=2)}")
            
            response = requests.post(
                self.api_url,
                json=request_data,
                timeout=30
            )
            
            print(f"   📥 响应状态码: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                llm_response = result.get('response', '')
                
                print(f"   🔍 LLM原始响应: {llm_response}")
                
                # 尝试解析JSON响应
                try:
                    parsed_result = json.loads(llm_response)
                    final_result = {
                        'matched': bool(parsed_result.get('matched', False)),
                        'confidence': float(parsed_result.get('confidence', 0.0)),
                        'reasoning': str(parsed_result.get('reasoning', '无法获取判断理由'))
                    }
                    
                    print(f"   ✅ LLM判断结果:")
                    print(f"      匹配: {final_result['matched']}")
                    print(f"      置信度: {final_result['confidence']:.2f}")
                    print(f"      理由: {final_result['reasoning']}")
                    
                    return final_result
                    
                except json.JSONDecodeError as e:
                    print(f"   ⚠️  JSON解析失败: {str(e)}")
                    print(f"   🔄 使用备用文本解析方法")
                    # 如果JSON解析失败，尝试从文本中提取信息
                    return self._parse_text_response(llm_response)
            else:
                error_msg = f"API请求失败: {response.status_code} - {response.text}"
                print(f"   ❌ {error_msg}")
                raise Exception(error_msg)
                
        except requests.exceptions.RequestException as e:
            error_msg = f"网络请求错误: {str(e)}"
            print(f"   ❌ {error_msg}")
            raise Exception(error_msg)
        except Exception as e:
            error_msg = f"LLM判断错误: {str(e)}"
            print(f"   ❌ {error_msg}")
            raise Exception(error_msg)
    
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


class ContentReviewService:
    """内容审读服务"""
    
    def __init__(self, db: Session):
        self.db = db
        self.llm_client = None
    
    async def review_content(self, content: str, instruction_set_id: int, model_config_id: int) -> ReviewResult:
        """
        审读内容
        
        Args:
            content: 待审读的内容
            instruction_set_id: 指令集ID
            model_config_id: 模型配置ID
            
        Returns:
            审读结果
        """
        # 初始化LLM客户端
        await self._init_llm_client(model_config_id)
        
        # 获取指令集的根节点
        from app.crud.instruction_set import instruction_set
        root_nodes = await instruction_set.get_root_nodes(self.db, instruction_set_id)
        if not root_nodes:
            raise ValueError("指令集没有根节点")
        
        # 从根节点开始审读
        root_node = root_nodes[0]
        result = await self._review_node(content, root_node)
        
        # 计算整体风险等级
        overall_risk = self._calculate_overall_risk(result)
        result.risk_level = overall_risk
        
        return result
    
    async def _init_llm_client(self, model_config_id: int):
        """
        初始化LLM客户端
        
        Args:
            model_config_id: 模型配置ID
        """
        # 获取模型配置
        config = await model_service_config_crud.get(self.db, model_config_id)
        if not config:
            raise ValueError(f"模型配置不存在: {model_config_id}")
        
        # 解析配置
        config_dict = {
            'model_name': config.model_name,
            'api_url': config.api_endpoint,  # 修复字段名：api_endpoint -> api_url
            'api_key': config.api_key
        }
        
        # 根据服务提供商初始化客户端
        if config.provider.lower() == 'ollama':
            self.llm_client = OllamaLLMClient(config_dict)
        else:
            raise ValueError(f"不支持的服务提供商: {config.provider}")
    
    async def _review_node(self, content: str, node) -> ReviewResult:
        """
        审读单个节点
        
        Args:
            content: 待审读内容
            node: 指令节点
            
        Returns:
            审读结果
        """
        print(f"\n🔍 开始审读节点:")
        print(f"   📋 节点ID: {node.id}")
        print(f"   📝 节点标题: {node.title}")
        print(f"   📄 节点描述: {node.description}")
        print(f"   🏷️  节点类型: {node.node_type}")
        print(f"   👨‍👩‍👧‍👦 父节点ID: {node.parent_id}")
        
        evidence = []
        matched = False
        confidence = 0.0
        
        # 解析节点配置
        node_config = json.loads(json.dumps(node.meta_data) if node.meta_data else "{}")
        keywords = node_config.get('keywords', [])
        patterns = node_config.get('patterns', [])
        llm_prompt = node_config.get('llm_prompt', '')
        risk_level_str = node_config.get('risk_level', 'medium')
        
        print(f"   ⚙️  节点配置:")
        print(f"      关键词: {keywords}")
        print(f"      模式: {patterns}")
        print(f"      LLM提示词: {llm_prompt[:100]}{'...' if len(llm_prompt) > 100 else ''}")
        print(f"      风险等级: {risk_level_str}")
        
        # 转换风险等级
        try:
            risk_level = RiskLevel(risk_level_str.lower())
        except ValueError:
            risk_level = RiskLevel.MEDIUM
        
        # 如果有LLM提示词，使用LLM进行智能判断
        if self.llm_client and llm_prompt:
            print(f"   🤖 使用LLM进行智能判断...")
            try:
                llm_result = self.llm_client.judge_content(content, llm_prompt, node.description)
                matched = llm_result['matched']
                confidence = llm_result['confidence']
                evidence.append(f"LLM判断: {llm_result['reasoning']}")
                print(f"   ✅ LLM判断完成: 匹配={matched}, 置信度={confidence:.2f}")
            except Exception as e:
                print(f"   ❌ LLM判断失败: {str(e)}")
                evidence.append(f"LLM判断失败: {str(e)}")
                print(f"   🔄 降级到传统匹配方式")
                # 降级到传统匹配方式
                matched, confidence = self._fallback_detection(content, keywords, patterns, evidence)
        else:
            print(f"   📝 使用传统的关键词和模式匹配")
            # 使用传统的关键词和模式匹配
            matched, confidence = self._fallback_detection(content, keywords, patterns, evidence)
        
        # 递归审读子节点
        children_results = []
        child_nodes = await instruction_node.get_children(self.db, node.id)
        
        print(f"   👶 子节点数量: {len(child_nodes)}")
        
        # 根节点总是检测子节点，其他节点只有在匹配时才检测子节点
        should_check_children = (node.parent_id is None) or matched
        
        print(f"   🔍 是否检测子节点: {should_check_children} (根节点={node.parent_id is None}, 当前匹配={matched})")
        
        if should_check_children:
            for i, child_node in enumerate(child_nodes):
                print(f"   📋 处理子节点 {i+1}/{len(child_nodes)}: {child_node.title}")
                child_result = await self._review_node(content, child_node)
                children_results.append(child_result)
                # 如果子节点匹配，父节点也应该匹配（除了根节点）
                if child_result.matched and node.parent_id is not None:
                    print(f"   ⬆️  子节点匹配，更新父节点状态")
                    matched = True
                    confidence = max(confidence, child_result.confidence * 0.8)
        
        # 提取敏感内容片段
        sensitive_excerpt = self._extract_sensitive_excerpt(content, matched, evidence, keywords)
        
        result = ReviewResult(
            node_id=str(node.id),
            description=node.description,
            matched=matched,
            risk_level=risk_level,
            confidence=confidence,
            evidence=evidence,
            sensitive_excerpt=sensitive_excerpt,
            original_length=len(content),
            children_results=children_results
        )
        
        print(f"   🎯 节点审读完成:")
        print(f"      匹配: {matched}")
        print(f"      风险等级: {risk_level}")
        print(f"      置信度: {confidence:.2f}")
        print(f"      证据数量: {len(evidence)}")
        print(f"      敏感内容: {sensitive_excerpt[:50]}{'...' if len(sensitive_excerpt) > 50 else ''}")
        print(f"      子节点结果数量: {len(children_results)}")
        
        return result
    
    def _fallback_detection(self, content: str, keywords: List[str], patterns: List[str], evidence: List[str]) -> tuple[bool, float]:
        """
        后备检测方法：使用关键词和模式匹配
        
        Args:
            content: 待检测内容
            keywords: 关键词列表
            patterns: 正则表达式模式列表
            evidence: 证据列表
            
        Returns:
            (是否匹配, 置信度)
        """
        matched = False
        confidence = 0.0
        
        # 关键词匹配
        for keyword in keywords:
            if keyword.lower() in content.lower():
                evidence.append(f"关键词匹配: {keyword}")
                matched = True
                confidence += 0.3
        
        # 正则表达式匹配
        for pattern in patterns:
            try:
                matches = re.findall(pattern, content, re.IGNORECASE)
                if matches:
                    evidence.append(f"模式匹配: {pattern} -> {matches}")
                    matched = True
                    confidence += 0.4
            except re.error:
                evidence.append(f"正则表达式错误: {pattern}")
        
        # 限制置信度在0-1之间
        confidence = min(confidence, 1.0)
        
        return matched, confidence
    
    def _extract_sensitive_excerpt(self, content: str, matched: bool, evidence: List[str], keywords: List[str]) -> str:
        """
        提取敏感内容片段
        
        Args:
            content: 原始内容
            matched: 是否匹配
            evidence: 证据列表
            keywords: 关键词列表
            
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
            for keyword in keywords:
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
    
    def _calculate_overall_risk(self, result: ReviewResult) -> RiskLevel:
        """
        计算整体风险等级：从所有匹配的节点中选择最高风险等级
        
        Args:
            result: 审读结果
            
        Returns:
            整体风险等级
        """
        matched_nodes = []
        
        def collect_matched_nodes(node_result: ReviewResult):
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