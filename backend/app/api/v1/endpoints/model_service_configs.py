#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
模型服务配置API端点
"""

from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
import json
import asyncio
import aiohttp
from datetime import datetime

from app.core.database import get_db
from app.core.exceptions import NotFoundError, ValidationError
from app.models.user import User
from app.models.model_service_config import ModelServiceProvider
from app.schemas.common import IDResponse
from app.schemas.model_service_config import (
    ModelServiceConfigCreate,
    ModelServiceConfigUpdate,
    ModelServiceConfigResponse,
    ModelServiceConfigListResponse,
    ModelServiceConfigForAgent,
    ModelServiceConfigStats,
    ModelServiceConfigTest,
    ModelServiceConfigTestResult
)
from app.crud.model_service_config import model_service_config_crud
from app.api.v1.endpoints.auth import get_current_active_user, get_current_admin_user

router = APIRouter()


@router.get("/providers", summary="获取支持的服务提供商列表")
async def get_supported_providers(
    current_user: User = Depends(get_current_active_user)
) -> List[dict]:
    """
    获取系统支持的所有服务提供商列表
    """
    providers = []
    for provider in ModelServiceProvider:
        provider_info = {
            "value": provider.value,
            "label": _get_provider_display_name(provider),
            "description": _get_provider_description(provider)
        }
        providers.append(provider_info)
    
    return providers


@router.get("/available-for-agents", summary="获取可用于Agent的模型服务列表")
async def get_available_model_services_for_agents(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> List[ModelServiceConfigForAgent]:
    """
    获取可用于Agent配置的模型服务列表
    只返回激活状态的配置，格式化为前端下拉选择所需的格式
    """
    return await model_service_config_crud.get_for_agents(db)


@router.get("/stats", summary="获取模型服务配置统计信息")
async def get_model_service_config_stats(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> ModelServiceConfigStats:
    """
    获取模型服务配置的统计信息
    包括总数、激活数、按提供商分组等
    """
    stats = await model_service_config_crud.get_stats(db)
    return ModelServiceConfigStats(**stats)


@router.get("/ollama-models", summary="获取Ollama模型列表")
async def get_ollama_models(
    api_endpoint: str = Query(..., description="Ollama API端点"),
    current_user: User = Depends(get_current_active_user)
) -> dict:
    """
    获取指定Ollama服务的模型列表
    通过后端代理请求，避免前端直接调用Ollama服务
    """
    try:
        # 清理端点URL
        clean_endpoint = api_endpoint.rstrip('/')
        tags_url = f"{clean_endpoint}/api/tags"
        
        # 发起请求获取模型列表
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
            async with session.get(tags_url) as response:
                if response.status == 200:
                    data = await response.json()
                    return {
                        "success": True,
                        "models": data.get("models", []),
                        "message": "获取模型列表成功"
                    }
                else:
                    return {
                        "success": False,
                        "models": [],
                        "message": f"请求失败，状态码: {response.status}"
                    }
    except aiohttp.ClientError as e:
        return {
            "success": False,
            "models": [],
            "message": f"网络请求失败: {str(e)}"
        }
    except Exception as e:
        return {
            "success": False,
            "models": [],
            "message": f"获取模型列表失败: {str(e)}"
        }


@router.get("/", summary="获取模型服务配置列表")
async def get_model_service_configs(
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(20, ge=1, le=100, description="每页数量"),
    search: Optional[str] = Query(None, description="搜索关键词"),
    provider: Optional[ModelServiceProvider] = Query(None, description="服务提供商"),
    is_active: Optional[bool] = Query(None, description="是否激活"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> ModelServiceConfigListResponse:
    """
    获取模型服务配置列表
    支持分页、搜索和筛选
    """
    skip = (page - 1) * size
    configs, total = await model_service_config_crud.get_multi(
        db=db,
        skip=skip,
        limit=size,
        search=search,
        provider=provider,
        is_active=is_active
    )
    
    # 转换为响应格式
    config_responses = []
    for config in configs:
        config_dict = config.to_dict()
        config_dict["provider_display_name"] = config.provider_display_name
        config_responses.append(ModelServiceConfigResponse(**config_dict))
    
    return ModelServiceConfigListResponse(
        items=config_responses,
        total=total,
        page=page,
        size=size,
        pages=(total + size - 1) // size
    )


@router.get("/{config_id}", summary="获取模型服务配置详情")
async def get_model_service_config(
    config_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> ModelServiceConfigResponse:
    """
    获取指定ID的模型服务配置详情
    """
    config = await model_service_config_crud.get(db, config_id)
    if not config:
        raise NotFoundError("模型服务配置不存在")
    
    config_dict = config.to_dict()
    config_dict["provider_display_name"] = config.provider_display_name
    return ModelServiceConfigResponse(**config_dict)


@router.post("/", summary="创建模型服务配置")
async def create_model_service_config(
    config_in: ModelServiceConfigCreate,
    current_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
) -> IDResponse:
    """
    创建新的模型服务配置
    只有管理员可以创建
    """
    try:
        config = await model_service_config_crud.create(
            db=db,
            obj_in=config_in,
            created_by=current_user.id
        )
        return IDResponse(id=config.id, message="模型服务配置创建成功")
    except HTTPException:
        raise
    except Exception as e:
        raise ValidationError(f"创建模型服务配置失败: {str(e)}")


@router.put("/{config_id}", summary="更新模型服务配置")
async def update_model_service_config(
    config_id: int,
    config_in: ModelServiceConfigUpdate,
    current_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
) -> ModelServiceConfigResponse:
    """
    更新指定ID的模型服务配置
    只有管理员可以更新
    """
    config = await model_service_config_crud.get(db, config_id)
    if not config:
        raise NotFoundError("模型服务配置不存在")
    
    try:
        updated_config = await model_service_config_crud.update(
            db=db,
            db_obj=config,
            obj_in=config_in
        )
        
        config_dict = updated_config.to_dict()
        config_dict["provider_display_name"] = updated_config.provider_display_name
        return ModelServiceConfigResponse(**config_dict)
    except Exception as e:
        raise ValidationError(f"更新模型服务配置失败: {str(e)}")


@router.delete("/{config_id}", summary="删除模型服务配置")
async def delete_model_service_config(
    config_id: int,
    current_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """
    删除指定ID的模型服务配置
    只有管理员可以删除
    
    如果配置被Agent引用，将返回400错误而不是500错误
    """
    config = await model_service_config_crud.get(db, config_id)
    if not config:
        raise NotFoundError("模型服务配置不存在")
    
    # CRUD层会处理所有错误情况，包括外键约束错误
    await model_service_config_crud.delete(db, config_id)
    
    return {"message": "模型服务配置删除成功"}


@router.patch("/{config_id}/status", summary="切换模型服务配置状态")
async def toggle_model_service_config_status(
    config_id: int,
    is_active: bool,
    current_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
) -> ModelServiceConfigResponse:
    """
    切换模型服务配置的激活状态
    只有管理员可以操作
    """
    config = await model_service_config_crud.toggle_status(
        db=db,
        config_id=config_id,
        is_active=is_active
    )
    
    if not config:
        raise NotFoundError("模型服务配置不存在")
    
    config_dict = config.to_dict()
    config_dict["provider_display_name"] = config.provider_display_name
    return ModelServiceConfigResponse(**config_dict)


@router.get("/available-for-agents", summary="获取可用于Agent的模型服务列表")
async def get_available_model_services_for_agents(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> List[ModelServiceConfigForAgent]:
    """
    获取可用于Agent配置的模型服务列表
    只返回激活状态的配置，格式化为前端下拉选择所需的格式
    """
    return await model_service_config_crud.get_for_agents(db)


@router.get("/stats", summary="获取模型服务配置统计信息")
async def get_model_service_config_stats(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> ModelServiceConfigStats:
    """
    获取模型服务配置的统计信息
    包括总数、激活数、按提供商分组等
    """
    stats = await model_service_config_crud.get_stats(db)
    return ModelServiceConfigStats(**stats)


@router.post("/test", summary="测试模型服务配置")
async def test_model_service_config(
    test_data: ModelServiceConfigTest,
    current_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
) -> ModelServiceConfigTestResult:
    """
    测试模型服务配置
    支持两种模式：
    1. 使用config_id测试已保存的配置
    2. 直接传递配置参数测试新配置
    只有管理员可以测试
    """
    if test_data.config_id:
        # 模式1：测试已保存的配置
        config = await model_service_config_crud.get(db, test_data.config_id)
        if not config:
            raise NotFoundError("模型服务配置不存在")
        
        if not config.is_active:
            raise ValidationError("配置未激活，无法测试")
        
        # 执行测试
        test_result = await _test_model_service(config, test_data.test_message)
        return test_result
    else:
        # 模式2：测试新配置参数
        if not all([test_data.provider, test_data.model_name, test_data.api_endpoint]):
            raise ValidationError("测试新配置时，provider、model_name和api_endpoint为必填字段")
        
        # 创建临时配置对象用于测试
        temp_config = type('TempConfig', (), {
            'provider': test_data.provider,
            'model_name': test_data.model_name,
            'api_endpoint': test_data.api_endpoint,
            'api_key': test_data.api_key,
            'max_tokens': test_data.max_tokens or 4096,
            'temperature': test_data.temperature or 0.7,
            'timeout': test_data.timeout or 30,
            'headers': test_data.headers or [],
            'extra_params': test_data.extra_params or {}
        })()
        
        # 执行测试
        test_result = await _test_model_service(temp_config, test_data.test_message)
        return test_result


@router.get("/providers", summary="获取支持的服务提供商列表")
async def get_supported_providers(
    current_user: User = Depends(get_current_active_user)
) -> List[dict]:
    """
    获取系统支持的所有服务提供商列表
    """
    providers = []
    for provider in ModelServiceProvider:
        provider_info = {
            "value": provider.value,
            "label": _get_provider_display_name(provider),
            "description": _get_provider_description(provider)
        }
        providers.append(provider_info)
    
    return providers


async def _test_model_service(
    config,
    test_message: str
) -> ModelServiceConfigTestResult:
    """
    测试模型服务配置
    
    Args:
        config: 模型服务配置对象
        test_message: 测试消息
        
    Returns:
        测试结果
    """
    start_time = datetime.now()
    
    try:
        # 根据不同的提供商构建请求
        if config.provider == ModelServiceProvider.OPENAI:
            result = await _test_openai_service(config, test_message)
        elif config.provider == ModelServiceProvider.CLAUDE:
            result = await _test_claude_service(config, test_message)
        elif config.provider == ModelServiceProvider.QWEN:
            result = await _test_qwen_service(config, test_message)
        elif config.provider == ModelServiceProvider.DOUBAO:
            result = await _test_doubao_service(config, test_message)
        elif config.provider in [ModelServiceProvider.OLLAMA, ModelServiceProvider.VLLM]:
            result = await _test_local_service(config, test_message)
        else:
            result = await _test_generic_service(config, test_message)
        
        response_time = (datetime.now() - start_time).total_seconds()
        result.response_time = response_time
        return result
        
    except Exception as e:
        response_time = (datetime.now() - start_time).total_seconds()
        return ModelServiceConfigTestResult(
            success=False,
            response_time=response_time,
            error_message=str(e)
        )


async def _test_openai_service(config, test_message: str) -> ModelServiceConfigTestResult:
    """测试OpenAI服务"""
    headers = {
        "Authorization": f"Bearer {config.api_key}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": config.model_name,
        "messages": [{"role": "user", "content": test_message}],
        "max_tokens": min(config.max_tokens or 100, 100),
        "temperature": float(config.temperature or 0.7)
    }
    
    async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=config.timeout)) as session:
        async with session.post(config.api_endpoint, headers=headers, json=payload) as response:
            if response.status == 200:
                data = await response.json()
                content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
                return ModelServiceConfigTestResult(
                    success=True,
                    response_content=content[:200],  # 限制响应长度
                    status_code=response.status
                )
            else:
                error_text = await response.text()
                return ModelServiceConfigTestResult(
                    success=False,
                    error_message=error_text[:200],
                    status_code=response.status
                )


async def _test_claude_service(config, test_message: str) -> ModelServiceConfigTestResult:
    """测试Claude服务"""
    headers = {
        "x-api-key": config.api_key,
        "Content-Type": "application/json",
        "anthropic-version": config.api_version or "2023-06-01"
    }
    
    payload = {
        "model": config.model_name,
        "max_tokens": min(config.max_tokens or 100, 100),
        "messages": [{"role": "user", "content": test_message}]
    }
    
    async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=config.timeout)) as session:
        async with session.post(config.api_endpoint, headers=headers, json=payload) as response:
            if response.status == 200:
                data = await response.json()
                content = data.get("content", [{}])[0].get("text", "")
                return ModelServiceConfigTestResult(
                    success=True,
                    response_content=content[:200],
                    status_code=response.status
                )
            else:
                error_text = await response.text()
                return ModelServiceConfigTestResult(
                    success=False,
                    error_message=error_text[:200],
                    status_code=response.status
                )


async def _test_qwen_service(config, test_message: str) -> ModelServiceConfigTestResult:
    """测试通义千问服务"""
    headers = {
        "Authorization": f"Bearer {config.api_key}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": config.model_name,
        "input": {
            "messages": [{"role": "user", "content": test_message}]
        },
        "parameters": {
            "max_tokens": min(config.max_tokens or 100, 100),
            "temperature": float(config.temperature or 0.7)
        }
    }
    
    async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=config.timeout)) as session:
        async with session.post(config.api_endpoint, headers=headers, json=payload) as response:
            if response.status == 200:
                data = await response.json()
                content = data.get("output", {}).get("text", "")
                return ModelServiceConfigTestResult(
                    success=True,
                    response_content=content[:200],
                    status_code=response.status
                )
            else:
                error_text = await response.text()
                return ModelServiceConfigTestResult(
                    success=False,
                    error_message=error_text[:200],
                    status_code=response.status
                )


async def _test_doubao_service(config, test_message: str) -> ModelServiceConfigTestResult:
    """测试豆包服务"""
    headers = {
        "Authorization": f"Bearer {config.api_key}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": config.model_name,
        "messages": [{"role": "user", "content": test_message}],
        "max_tokens": min(config.max_tokens or 100, 100),
        "temperature": float(config.temperature or 0.7)
    }
    
    async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=config.timeout)) as session:
        async with session.post(config.api_endpoint, headers=headers, json=payload) as response:
            if response.status == 200:
                data = await response.json()
                content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
                return ModelServiceConfigTestResult(
                    success=True,
                    response_content=content[:200],
                    status_code=response.status
                )
            else:
                error_text = await response.text()
                return ModelServiceConfigTestResult(
                    success=False,
                    error_message=error_text[:200],
                    status_code=response.status
                )


async def _test_local_service(config, test_message: str) -> ModelServiceConfigTestResult:
    """测试本地服务(Ollama/vLLM)"""
    headers = {"Content-Type": "application/json"}
    
    # Ollama格式
    if config.provider == ModelServiceProvider.OLLAMA:
        payload = {
            "model": config.model_name,
            "messages": [{"role": "user", "content": test_message}],
            "stream": False
        }
    else:  # vLLM格式
        payload = {
            "model": config.model_name,
            "messages": [{"role": "user", "content": test_message}],
            "max_tokens": min(config.max_tokens or 100, 100),
            "temperature": float(config.temperature or 0.7)
        }
    print(f"发送请求数据: {payload}")
    async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=config.timeout)) as session:
        print(f"请求端点: {config.api_endpoint}")
        async with session.post(config.api_endpoint, headers=headers, json=payload) as response:
            print(f"响应状态码: {response.status}")
            print(f"响应头: {response.headers}")
            if response.status == 200:
                data = await response.json()
                print(f"完整响应数据: {data}")
                if config.provider == ModelServiceProvider.OLLAMA:
                    content = data.get("message", {}).get("content", "")
                else:
                    content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
                
                print(f"提取的内容: {content}")
                return ModelServiceConfigTestResult(
                    success=True,
                    response_content=content[:200],
                    status_code=response.status
                )
            else:
                error_text = await response.text()
                return ModelServiceConfigTestResult(
                    success=False,
                    error_message=error_text[:200],
                    status_code=response.status
                )


async def _test_generic_service(config, test_message: str) -> ModelServiceConfigTestResult:
    """测试通用服务"""
    headers = {"Content-Type": "application/json"}
    if config.api_key:
        headers["Authorization"] = f"Bearer {config.api_key}"
    
    payload = {
        "model": config.model_name,
        "messages": [{"role": "user", "content": test_message}],
        "max_tokens": min(config.max_tokens or 100, 100),
        "temperature": float(config.temperature or 0.7)
    }
    
    async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=config.timeout)) as session:
        async with session.post(config.api_endpoint, headers=headers, json=payload) as response:
            if response.status == 200:
                data = await response.json()
                # 尝试多种可能的响应格式
                content = ""
                if "choices" in data:
                    content = data["choices"][0].get("message", {}).get("content", "")
                elif "content" in data:
                    content = data["content"]
                elif "text" in data:
                    content = data["text"]
                
                return ModelServiceConfigTestResult(
                    success=True,
                    response_content=content[:200],
                    status_code=response.status
                )
            else:
                error_text = await response.text()
                return ModelServiceConfigTestResult(
                    success=False,
                    error_message=error_text[:200],
                    status_code=response.status
                )


def _get_provider_display_name(provider: ModelServiceProvider) -> str:
    """获取提供商显示名称"""
    names = {
        ModelServiceProvider.OPENAI: "OpenAI",
        ModelServiceProvider.CLAUDE: "Anthropic Claude",
        ModelServiceProvider.QWEN: "通义千问",
        ModelServiceProvider.DOUBAO: "豆包",
        ModelServiceProvider.GEMINI: "Google Gemini",
        ModelServiceProvider.OLLAMA: "Ollama",
        ModelServiceProvider.VLLM: "vLLM",
        ModelServiceProvider.CUSTOM: "自定义服务"
    }
    return names.get(provider, provider.value)


def _get_provider_description(provider: ModelServiceProvider) -> str:
    """获取提供商描述"""
    descriptions = {
        ModelServiceProvider.OPENAI: "OpenAI GPT系列模型服务",
        ModelServiceProvider.CLAUDE: "Anthropic Claude系列模型服务",
        ModelServiceProvider.QWEN: "阿里云通义千问模型服务",
        ModelServiceProvider.DOUBAO: "字节跳动豆包模型服务",
        ModelServiceProvider.GEMINI: "Google Gemini模型服务",
        ModelServiceProvider.OLLAMA: "本地部署的Ollama模型服务",
        ModelServiceProvider.VLLM: "本地部署的vLLM模型服务",
        ModelServiceProvider.CUSTOM: "自定义的模型服务接口"
    }
    return descriptions.get(provider, "")