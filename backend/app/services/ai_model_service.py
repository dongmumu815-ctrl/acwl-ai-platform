#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI模型调用服务
用于调用各种AI服务提供商的模型
"""

import asyncio
import aiohttp
import json
from datetime import datetime
from typing import Dict, Any, Optional, List
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.model_service_config import ModelServiceProvider
from app.schemas.agent import AgentChatRequest, AgentChatResponse


class AIModelService:
    """AI模型调用服务"""
    
    @staticmethod
    async def chat_with_model(
        config,
        system_prompt: str,
        user_message: str,
        context: Optional[Dict[str, Any]] = None,
        images: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        与AI模型进行对话
        
        Args:
            config: 模型服务配置对象
            system_prompt: 系统提示词
            user_message: 用户消息
            context: 上下文信息（包含历史消息等）
            
        Returns:
            包含响应内容、token使用量、处理时间等信息的字典
        """
        start_time = datetime.now()
        
        try:
            # 构建消息列表
            messages = []
            
            # 添加系统提示词
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            
            # 添加历史消息（如果有）
            if context and context.get("previous_messages"):
                for msg in context["previous_messages"]:
                    if msg.get("role") and msg.get("content"):
                        messages.append({
                            "role": msg["role"],
                            "content": msg["content"]
                        })
            
            # 添加当前用户消息
            user_msg = {"role": "user", "content": user_message}
            
            # 如果有图片，构建多模态消息格式
            if images and len(images) > 0:
                # 对于支持多模态的模型（如Ollama的视觉模型），使用特殊格式
                if config.provider in ["ollama", "vllm"] and any(keyword in config.model_name.lower() for keyword in ["vision", "vl", "visual", "multimodal"]):
                    # Ollama视觉模型格式
                    user_msg["images"] = images
                else:
                    # 其他模型，将图片信息添加到消息内容中
                    image_info = f"\n\n[用户上传了 {len(images)} 张图片]\n"
                    user_msg["content"] = user_message + image_info
            
            messages.append(user_msg)
            
            # 打印LLM请求参数
            print("\n=== LLM接口请求参数 ===")
            print(f"模型提供商: {config.provider}")
            print(f"模型名称: {config.model_name}")
            print(f"API端点: {config.api_endpoint}")
            print(f"消息数量: {len(messages)}")
            print("消息列表:")
            for i, msg in enumerate(messages):
                print(f"  [{i+1}] {msg['role']}: {msg['content'][:100]}{'...' if len(msg['content']) > 100 else ''}")
            print("========================\n")
            
            # 根据不同的提供商调用相应的服务
            if config.provider == ModelServiceProvider.OPENAI.value:
                result = await AIModelService._call_openai_service(config, messages)
            elif config.provider == ModelServiceProvider.CLAUDE.value:
                result = await AIModelService._call_claude_service(config, messages)
            elif config.provider == ModelServiceProvider.QWEN.value:
                result = await AIModelService._call_qwen_service(config, messages)
            elif config.provider == ModelServiceProvider.DOUBAO.value:
                result = await AIModelService._call_doubao_service(config, messages)
            elif config.provider in [ModelServiceProvider.OLLAMA.value, ModelServiceProvider.VLLM.value]:
                result = await AIModelService._call_local_service(config, messages)
            else:
                result = await AIModelService._call_generic_service(config, messages)
            
            # 计算处理时间
            processing_time = (datetime.now() - start_time).total_seconds()
            result["processing_time"] = processing_time
            
            return result
            
        except Exception as e:
            processing_time = (datetime.now() - start_time).total_seconds()
            return {
                "success": False,
                "error": str(e),
                "processing_time": processing_time,
                "message": f"调用AI模型时发生错误: {str(e)}",
                "tokens_used": 0
            }
    
    @staticmethod
    async def _call_openai_service(config, messages: List[Dict]) -> Dict[str, Any]:
        """调用OpenAI服务"""
        headers = {
            "Authorization": f"Bearer {config.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": config.model_name,
            "messages": messages,
            "max_tokens": config.max_tokens or 4096,
            "temperature": float(config.temperature or 0.7),
            "top_p": float(config.top_p or 0.9),
            "frequency_penalty": float(config.frequency_penalty or 0.0),
            "presence_penalty": float(config.presence_penalty or 0.0)
        }
        
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=config.timeout)) as session:
            async with session.post(config.api_endpoint, headers=headers, json=payload) as response:
                if response.status == 200:
                    data = await response.json()
                    content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
                    tokens_used = data.get("usage", {}).get("total_tokens", 0)
                    return {
                        "success": True,
                        "message": content,
                        "tokens_used": tokens_used,
                        "metadata": {
                            "model": config.model_name,
                            "provider": config.provider
                        }
                    }
                else:
                    error_text = await response.text()
                    return {
                        "success": False,
                        "error": error_text,
                        "message": f"OpenAI API调用失败: {error_text}",
                        "tokens_used": 0
                    }
    
    @staticmethod
    async def _call_claude_service(config, messages: List[Dict]) -> Dict[str, Any]:
        """调用Claude服务"""
        headers = {
            "x-api-key": config.api_key,
            "Content-Type": "application/json",
            "anthropic-version": config.api_version or "2023-06-01"
        }
        
        payload = {
            "model": config.model_name,
            "max_tokens": config.max_tokens or 4096,
            "messages": messages,
            "temperature": float(config.temperature or 0.7),
            "top_p": float(config.top_p or 0.9)
        }
        
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=config.timeout)) as session:
            async with session.post(config.api_endpoint, headers=headers, json=payload) as response:
                if response.status == 200:
                    data = await response.json()
                    content = data.get("content", [{}])[0].get("text", "")
                    tokens_used = data.get("usage", {}).get("input_tokens", 0) + data.get("usage", {}).get("output_tokens", 0)
                    return {
                        "success": True,
                        "message": content,
                        "tokens_used": tokens_used,
                        "metadata": {
                            "model": config.model_name,
                            "provider": config.provider
                        }
                    }
                else:
                    error_text = await response.text()
                    return {
                        "success": False,
                        "error": error_text,
                        "message": f"Claude API调用失败: {error_text}",
                        "tokens_used": 0
                    }
    
    @staticmethod
    async def _call_qwen_service(config, messages: List[Dict]) -> Dict[str, Any]:
        """调用通义千问服务"""
        headers = {
            "Authorization": f"Bearer {config.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": config.model_name,
            "input": {
                "messages": messages
            },
            "parameters": {
                "max_tokens": config.max_tokens or 4096,
                "temperature": float(config.temperature or 0.7),
                "top_p": float(config.top_p or 0.9),
                "frequency_penalty": float(config.frequency_penalty or 0.0),
                "presence_penalty": float(config.presence_penalty or 0.0)
            }
        }
        
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=config.timeout)) as session:
            async with session.post(config.api_endpoint, headers=headers, json=payload) as response:
                if response.status == 200:
                    data = await response.json()
                    content = data.get("output", {}).get("text", "")
                    tokens_used = data.get("usage", {}).get("total_tokens", 0)
                    return {
                        "success": True,
                        "message": content,
                        "tokens_used": tokens_used,
                        "metadata": {
                            "model": config.model_name,
                            "provider": config.provider
                        }
                    }
                else:
                    error_text = await response.text()
                    return {
                        "success": False,
                        "error": error_text,
                        "message": f"通义千问API调用失败: {error_text}",
                        "tokens_used": 0
                    }
    
    @staticmethod
    async def _call_doubao_service(config, messages: List[Dict]) -> Dict[str, Any]:
        """调用豆包服务"""
        headers = {
            "Authorization": f"Bearer {config.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": config.model_name,
            "messages": messages,
            "max_tokens": config.max_tokens or 4096,
            "temperature": float(config.temperature or 0.7),
            "top_p": float(config.top_p or 0.9),
            "frequency_penalty": float(config.frequency_penalty or 0.0),
            "presence_penalty": float(config.presence_penalty or 0.0)
        }
        
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=config.timeout)) as session:
            async with session.post(config.api_endpoint, headers=headers, json=payload) as response:
                if response.status == 200:
                    data = await response.json()
                    content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
                    tokens_used = data.get("usage", {}).get("total_tokens", 0)
                    return {
                        "success": True,
                        "message": content,
                        "tokens_used": tokens_used,
                        "metadata": {
                            "model": config.model_name,
                            "provider": config.provider
                        }
                    }
                else:
                    error_text = await response.text()
                    return {
                        "success": False,
                        "error": error_text,
                        "message": f"豆包API调用失败: {error_text}",
                        "tokens_used": 0
                    }
    
    @staticmethod
    async def _call_local_service(config, messages: List[Dict]) -> Dict[str, Any]:
        """调用本地服务(Ollama/vLLM)"""
        headers = {"Content-Type": "application/json"}
        
        # Ollama格式
        if config.provider == ModelServiceProvider.OLLAMA.value:
            payload = {
                "model": config.model_name,
                "messages": messages,
                "stream": False,
                "options": {
                    "temperature": float(config.temperature or 0.7),
                    "top_p": float(config.top_p or 0.9),
                    "frequency_penalty": float(config.frequency_penalty or 0.0),
                    "presence_penalty": float(config.presence_penalty or 0.0),
                    "num_predict": config.max_tokens or 4096
                }
            }
        else:  # vLLM格式
            payload = {
                "model": config.model_name,
                "messages": messages,
                "max_tokens": config.max_tokens or 4096,
                "temperature": float(config.temperature or 0.7),
                "top_p": float(config.top_p or 0.9),
                "frequency_penalty": float(config.frequency_penalty or 0.0),
                "presence_penalty": float(config.presence_penalty or 0.0)
            }
        
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=config.timeout)) as session:
            async with session.post(config.api_endpoint, headers=headers, json=payload) as response:
                if response.status == 200:
                    data = await response.json()
                    if config.provider == ModelServiceProvider.OLLAMA.value:
                        content = data.get("message", {}).get("content", "")
                        tokens_used = len(content.split())  # 简单估算
                    else:
                        content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
                        tokens_used = data.get("usage", {}).get("total_tokens", len(content.split()))
                    
                    return {
                        "success": True,
                        "message": content,
                        "tokens_used": tokens_used,
                        "metadata": {
                            "model": config.model_name,
                            "provider": config.provider
                        }
                    }
                else:
                    error_text = await response.text()
                    return {
                        "success": False,
                        "error": error_text,
                        "message": f"本地服务API调用失败: {error_text}",
                        "tokens_used": 0
                    }
    
    @staticmethod
    async def _call_generic_service(config, messages: List[Dict]) -> Dict[str, Any]:
        """调用通用服务"""
        headers = {"Content-Type": "application/json"}
        if config.api_key:
            headers["Authorization"] = f"Bearer {config.api_key}"
        
        payload = {
            "model": config.model_name,
            "messages": messages,
            "max_tokens": config.max_tokens or 4096,
            "temperature": float(config.temperature or 0.7),
            "top_p": float(config.top_p or 0.9),
            "frequency_penalty": float(config.frequency_penalty or 0.0),
            "presence_penalty": float(config.presence_penalty or 0.0)
        }
        
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=config.timeout)) as session:
            async with session.post(config.api_endpoint, headers=headers, json=payload) as response:
                if response.status == 200:
                    data = await response.json()
                    # 尝试多种可能的响应格式
                    content = ""
                    tokens_used = 0
                    
                    if "choices" in data:
                        content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
                        tokens_used = data.get("usage", {}).get("total_tokens", 0)
                    elif "message" in data:
                        content = data.get("message", {}).get("content", "")
                    elif "text" in data:
                        content = data.get("text", "")
                    elif "response" in data:
                        content = data.get("response", "")
                    
                    if not tokens_used:
                        tokens_used = len(content.split())  # 简单估算
                    
                    return {
                        "success": True,
                        "message": content,
                        "tokens_used": tokens_used,
                        "metadata": {
                            "model": config.model_name,
                            "provider": config.provider
                        }
                    }
                else:
                    error_text = await response.text()
                    return {
                        "success": False,
                        "error": error_text,
                        "message": f"通用API调用失败: {error_text}",
                        "tokens_used": 0
                    }