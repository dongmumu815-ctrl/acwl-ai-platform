#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Agent管理API端点
"""

from typing import List, Optional, Dict, Any
import json
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query, status, Header
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import and_, or_, desc, asc, select, func
from sqlalchemy.orm import selectinload
import time

from app.core.database import get_db
from app.core.config import settings
from .auth import get_current_user
from app.models import Agent, AgentConversation, AgentMessage, AgentTool, User, ModelServiceConfig
from app.schemas.agent import (
    AgentCreate, AgentUpdate, AgentResponse, AgentListResponse, AgentQueryParams,
    AgentToolCreate, AgentToolUpdate, AgentToolResponse, AgentToolListResponse,
    AgentConversationCreate, AgentConversationUpdate, AgentConversationResponse, AgentConversationListResponse,
    AgentMessageCreate, AgentMessageResponse, AgentMessageListResponse,
    AgentChatRequest, AgentChatResponse, AgentStatsResponse,
    AgentConfigValidationResponse,
    AgentToolGenerateRequest, AgentToolGenerateResponse,
    AgentToolExecuteRequest, AgentToolExecuteResponse,
    AgentSkillInvokeRequest, AgentSkillInvokeResponse,
    AgentSkillNameListResponse
)
from app.services.review_content_safety_agent_db import EnhancedContentSafetyAgentDB
from app.schemas.common import SimpleResponseModel as ResponseModel
from app.core.logger import logger


def verify_agent_skill_api_key(x_api_key: Optional[str] = Header(None)) -> str:
    expected_key = (settings.AGENT_SKILL_API_KEY or '').strip()
    provided_key = (x_api_key or '').strip()

    if not expected_key:
        raise HTTPException(status_code=500, detail='AGENT_SKILL_API_KEY is not configured')
    if not provided_key or provided_key != expected_key:
        raise HTTPException(status_code=401, detail='Invalid API key')
    return provided_key


async def resolve_agent_model_config(db: AsyncSession, model_name: Optional[str]) -> Dict[str, Any]:
    normalized_name = (model_name or '').strip()
    if normalized_name:
        query = select(ModelServiceConfig).where(
            ModelServiceConfig.model_name == normalized_name,
            ModelServiceConfig.is_active == True
        ).limit(1)
        result = await db.execute(query)
        config = result.scalar_one_or_none()
        if not config:
            raise HTTPException(status_code=404, detail=f"Model service config not found for model_name: {normalized_name}")
    else:
        query = select(ModelServiceConfig).where(ModelServiceConfig.is_active == True).limit(1)
        result = await db.execute(query)
        config = result.scalar_one_or_none()
        if not config:
            raise HTTPException(status_code=400, detail="No active model service config found. Please specify one.")

    return {
        'model_name': config.model_name,
        'api_key': config.api_key or "",
        'provider': config.provider,
        'base_url': config.api_endpoint or ""
    }

router = APIRouter()


# ============================================
# Agent CRUD操作
# ============================================

@router.post("/", response_model=AgentResponse, status_code=status.HTTP_201_CREATED)
async def create_agent(
    agent_data: AgentCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    创建新的Agent
    
    Args:
        agent_data: Agent创建数据
        db: 数据库会话
        current_user: 当前用户
        
    Returns:
        创建的Agent信息
    """
    try:
        # 验证模型服务配置是否存在
        config_query = select(ModelServiceConfig).where(ModelServiceConfig.id == agent_data.model_service_config_id)
        config_result = await db.execute(config_query)
        config = config_result.scalar_one_or_none()
        if not config:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Model service config with id {agent_data.model_service_config_id} not found"
            )
        
        # 创建Agent
        agent = Agent(
            **agent_data.model_dump(),
            created_by=current_user.id,
            updated_by=current_user.id
        )
        
        db.add(agent)
        await db.commit()
        await db.refresh(agent)
        
        # 构建响应数据
        response_data = AgentResponse.model_validate(agent)
        response_data.model_name = config.model_name
        response_data.creator_name = current_user.username
        response_data.updater_name = current_user.username
        
        logger.info(f"Agent created: {agent.id} by user {current_user.id}")
        return response_data
        
    except Exception as e:
        await db.rollback()
        logger.error(f"Error creating agent: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create agent: {str(e)}"
        )


@router.get("/", response_model=AgentListResponse)
async def list_agents(
    params: AgentQueryParams = Depends(),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取Agent列表
    
    Args:
        params: 查询参数
        db: 数据库会话
        current_user: 当前用户
        
    Returns:
        Agent列表和分页信息
    """
    try:
        # 构建查询
        query = select(Agent).options(
            selectinload(Agent.model_service_config),
            selectinload(Agent.creator)
        ).join(ModelServiceConfig, Agent.model_service_config_id == ModelServiceConfig.id)
        
        # 权限过滤：只能看到公开的或自己创建的Agent
        if current_user.role != "admin":
            query = query.where(
                or_(
                    Agent.is_public == True,
                    Agent.created_by == current_user.id,
                    Agent.allowed_users.contains([current_user.id])
                )
            )
        
        # 应用过滤条件
        if params.search:
            search_term = f"%{params.search}%"
            query = query.where(
                or_(
                    Agent.name.ilike(search_term),
                    Agent.description.ilike(search_term)
                )
            )
        
        if params.agent_type:
            query = query.where(Agent.agent_type == params.agent_type)
        
        if params.status:
            query = query.where(Agent.status == params.status)
        
        if params.model_service_config_id:
            query = query.where(Agent.model_service_config_id == params.model_service_config_id)
        
        if params.is_public is not None:
            query = query.where(Agent.is_public == params.is_public)
        
        if params.created_by:
            query = query.where(Agent.created_by == params.created_by)
        
        if params.tags:
            for tag in params.tags:
                query = query.where(Agent.tags.contains([tag]))
        
        # 排序
        if params.order_by:
            order_field = getattr(Agent, params.order_by, None)
            if order_field:
                if params.order_desc:
                    query = query.order_by(desc(order_field))
                else:
                    query = query.order_by(asc(order_field))
        
        # 获取总数
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await db.execute(count_query)
        total = total_result.scalar()
        
        # 分页
        offset = (params.page - 1) * params.size
        query = query.offset(offset).limit(params.size)
        
        # 执行查询
        result = await db.execute(query)
        agents = result.scalars().all()
        
        # 构建响应数据
        items = []
        for agent in agents:
            item_data = {
                "id": agent.id,
                "name": agent.name,
                "description": agent.description,
                "agent_type": agent.agent_type,
                "status": agent.status,
                "model_service_config_id": agent.model_service_config_id,
                "model_name": agent.model_service_config.name if agent.model_service_config else None,
                "is_public": agent.is_public,
                "usage_count": agent.usage_count,
                "last_used_at": agent.last_used_at,
                "created_by": agent.created_by,
                "creator_name": agent.creator.username if agent.creator else None,
                "created_at": agent.created_at,
                "updated_at": agent.updated_at,
                "tags": agent.tags
            }
            items.append(item_data)
        
        return AgentListResponse(
            items=items,
            total=total,
            page=params.page,
            size=params.size,
            pages=(total + params.size - 1) // params.size
        )
        
    except Exception as e:
        logger.error(f"Error listing agents: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list agents: {str(e)}"
        )


@router.get("/{agent_id:int}", response_model=AgentResponse)
async def get_agent(
    agent_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取单个Agent详情
    
    Args:
        agent_id: Agent ID
        db: 数据库会话
        current_user: 当前用户
        
    Returns:
        Agent详细信息
    """
    try:
        # 预加载关联对象以避免greenlet错误
        query = select(Agent).options(
            selectinload(Agent.model_service_config),
            selectinload(Agent.creator),
            selectinload(Agent.updater)
        ).where(Agent.id == agent_id)
        result = await db.execute(query)
        agent = result.scalar_one_or_none()
        if not agent:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Agent with id {agent_id} not found"
            )
        
        # 权限检查
        if current_user.role != "admin" and not agent.is_public and agent.created_by != current_user.id:
            if not agent.allowed_users or current_user.id not in agent.allowed_users:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Not enough permissions to access this agent"
                )
        
        # 构建响应数据
        response_data = AgentResponse.model_validate(agent)
        response_data.model_name = agent.model_service_config.name if agent.model_service_config else None
        response_data.creator_name = agent.creator.username if agent.creator else None
        response_data.updater_name = agent.updater.username if agent.updater else None
        
        return response_data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting agent {agent_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get agent: {str(e)}"
        )


@router.put("/{agent_id}", response_model=AgentResponse)
async def update_agent(
    agent_id: int,
    agent_data: AgentUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    更新Agent信息
    
    Args:
        agent_id: Agent ID
        agent_data: 更新数据
        db: 数据库会话
        current_user: 当前用户
        
    Returns:
        更新后的Agent信息
    """
    try:
        # 预加载关联对象以避免greenlet错误
        query = select(Agent).options(
            selectinload(Agent.model_service_config),
            selectinload(Agent.creator),
            selectinload(Agent.updater)
        ).where(Agent.id == agent_id)
        result = await db.execute(query)
        agent = result.scalar_one_or_none()
        if not agent:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Agent with id {agent_id} not found"
            )
        
        # 权限检查：只有创建者或管理员可以修改
        if current_user.role != "admin" and agent.created_by != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions to update this agent"
            )
        
        # 验证模型服务配置是否存在（如果要更新模型服务配置）
        if agent_data.model_service_config_id:
            config_query = select(ModelServiceConfig).where(ModelServiceConfig.id == agent_data.model_service_config_id)
            config_result = await db.execute(config_query)
            config = config_result.scalar_one_or_none()
            if not config:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Model service config with id {agent_data.model_service_config_id} not found"
                )
        
        # 更新字段
        update_data = agent_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(agent, field, value)
        
        agent.updated_by = current_user.id
        
        await db.commit()
        
        # 重新查询以获取更新后的数据和关联对象
        updated_query = select(Agent).options(
            selectinload(Agent.model_service_config),
            selectinload(Agent.creator),
            selectinload(Agent.updater)
        ).where(Agent.id == agent_id)
        updated_result = await db.execute(updated_query)
        updated_agent = updated_result.scalar_one()
        
        # 构建响应数据
        response_data = AgentResponse.model_validate(updated_agent)
        response_data.model_name = updated_agent.model_service_config.name if updated_agent.model_service_config else None
        response_data.creator_name = updated_agent.creator.username if updated_agent.creator else None
        response_data.updater_name = updated_agent.updater.username if updated_agent.updater else None
        
        logger.info(f"Agent updated: {agent.id} by user {current_user.id}")
        return response_data
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating agent {agent_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update agent: {str(e)}"
        )


@router.delete("/{agent_id}", response_model=ResponseModel)
async def delete_agent(
    agent_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    删除Agent
    
    Args:
        agent_id: Agent ID
        db: 数据库会话
        current_user: 当前用户
        
    Returns:
        删除结果
    """
    try:
        query = select(Agent).where(Agent.id == agent_id)
        result = await db.execute(query)
        agent = result.scalar_one_or_none()
        if not agent:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Agent with id {agent_id} not found"
            )
        
        # 权限检查：只有创建者或管理员可以删除
        if current_user.role != "admin" and agent.created_by != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions to delete this agent"
            )
        
        # 检查是否有关联的会话
        conversation_query = select(func.count(AgentConversation.id)).where(
            AgentConversation.agent_id == agent_id
        )
        conversation_result = await db.execute(conversation_query)
        conversation_count = conversation_result.scalar()
        
        if conversation_count > 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot delete agent with {conversation_count} active conversations"
            )
        
        await db.delete(agent)
        await db.commit()
        
        logger.info(f"Agent deleted: {agent_id} by user {current_user.id}")
        return ResponseModel(message="Agent deleted successfully")
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error deleting agent {agent_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete agent: {str(e)}"
        )


# ============================================
# Agent工具管理
# ============================================

@router.get("/tools/", response_model=AgentToolListResponse)
async def list_agent_tools(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    search: Optional[str] = Query(None),
    tool_type: Optional[str] = Query(None),
    is_enabled: Optional[bool] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取Agent工具列表
    """
    try:
        # 同步文件系统中的技能到数据库
        await agent_skill_service.sync_skills_with_db(db)
        
        query = select(AgentTool)
        
        # 应用过滤条件
        if search:
            search_term = f"%{search}%"
            query = query.where(
                or_(
                    AgentTool.name.ilike(search_term),
                    AgentTool.display_name.ilike(search_term),
                    AgentTool.description.ilike(search_term)
                )
            )
        
        if tool_type:
            query = query.where(AgentTool.tool_type == tool_type)
        
        if is_enabled is not None:
            query = query.where(AgentTool.is_enabled == is_enabled)
        
        # 分页
        total_query = select(func.count(AgentTool.id))
        if search:
            search_term = f"%{search}%"
            total_query = total_query.where(
                or_(
                    AgentTool.name.ilike(search_term),
                    AgentTool.display_name.ilike(search_term),
                    AgentTool.description.ilike(search_term)
                )
            )
        if tool_type:
            total_query = total_query.where(AgentTool.tool_type == tool_type)
        if is_enabled is not None:
            total_query = total_query.where(AgentTool.is_enabled == is_enabled)
        
        total_result = await db.execute(total_query)
        total = total_result.scalar()
        
        offset = (page - 1) * size
        query = query.offset(offset).limit(size).order_by(desc(AgentTool.created_at))
        result = await db.execute(query)
        tools = result.scalars().all()
        
        items = [AgentToolResponse.model_validate(tool) for tool in tools]
        
        return AgentToolListResponse(
            items=items,
            total=total,
            page=page,
            size=size,
            pages=(total + size - 1) // size
        )
        
    except Exception as e:
        logger.error(f"Error listing agent tools: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list agent tools: {str(e)}"
        )


@router.get("/public/tools/names", response_model=AgentSkillNameListResponse)
async def list_public_agent_skill_names(
    db: AsyncSession = Depends(get_db),
    api_key: str = Depends(verify_agent_skill_api_key)
):
    """通过 API Key 获取所有已启用技能名"""
    try:
        await agent_skill_service.sync_skills_with_db(db)
        query = select(AgentTool.name).where(AgentTool.is_enabled == True).order_by(asc(AgentTool.name))
        result = await db.execute(query)
        skills = [name for name in result.scalars().all() if isinstance(name, str) and name.strip()]
        return AgentSkillNameListResponse(skills=skills)
    except Exception as e:
        logger.error(f"Error listing public skill names: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list skill names: {str(e)}"
        )


from app.services.agent_skills import agent_skill_service

@router.get("/public/tools/names", response_model=AgentSkillNameListResponse)
async def list_public_agent_skill_names(
    db: AsyncSession = Depends(get_db),
    api_key: str = Depends(verify_agent_skill_api_key)
):
    """通过 API Key 获取所有已启用技能名"""
    try:
        await agent_skill_service.sync_skills_with_db(db)
        query = select(AgentTool.name).where(AgentTool.is_enabled == True).order_by(asc(AgentTool.name))
        result = await db.execute(query)
        skills = [name for name in result.scalars().all() if isinstance(name, str) and name.strip()]
        return AgentSkillNameListResponse(skills=skills)
    except Exception as e:
        logger.error(f"Error listing public skill names: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list skill names: {str(e)}"
        )

@router.post("/tools/execute", response_model=AgentToolExecuteResponse)
async def execute_agent_tool_task(
    request: AgentToolExecuteRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    执行Agent工具任务
    """
    try:
        normalized_skill_names = []
        for skill_name in request.skill_names or []:
            if isinstance(skill_name, str):
                cleaned_name = skill_name.strip()
                if cleaned_name and cleaned_name not in normalized_skill_names:
                    normalized_skill_names.append(cleaned_name)

        if not normalized_skill_names:
            raise HTTPException(status_code=400, detail="At least one valid skill name is required")

        skill_query = select(AgentTool).where(AgentTool.name.in_(normalized_skill_names))
        skill_result = await db.execute(skill_query)
        db_skills = skill_result.scalars().all()
        db_skill_map = {tool.name: tool for tool in db_skills}

        missing_skills = [name for name in normalized_skill_names if name not in db_skill_map]
        if missing_skills:
            raise HTTPException(status_code=404, detail=f"Skills not found: {', '.join(missing_skills)}")

        disabled_skills = [tool.name for tool in db_skills if not tool.is_enabled]
        if disabled_skills:
            raise HTTPException(status_code=400, detail=f"Skills are disabled: {', '.join(disabled_skills)}")

        # 1. 确定模型配置
        model_config = await resolve_agent_model_config(db, request.model_name)

        # 2. 调用 AgentSkillService
        result = await agent_skill_service.execute_skill_task(
            prompt=(request.prompt or "").strip(),
            model_config=model_config,
            enabled_skills=normalized_skill_names
        )
        
        return AgentToolExecuteResponse(
            result=result
        )
        
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        logger.error(f"Error executing tool task: {str(e)}\n{traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to execute tool task: {str(e)}"
        )


@router.post("/tools/{skill_name}/invoke", response_model=AgentSkillInvokeResponse)
async def invoke_agent_skill(
    skill_name: str,
    request: AgentSkillInvokeRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        normalized_name = (skill_name or "").strip()
        if not normalized_name:
            raise HTTPException(status_code=400, detail="skill_name is required")

        await agent_skill_service.sync_skills_with_db(db)

        query = select(AgentTool).where(AgentTool.name == normalized_name)
        result = await db.execute(query)
        tool = result.scalar_one_or_none()
        if not tool:
            raise HTTPException(status_code=404, detail=f"Skill not found: {normalized_name}")
        if not tool.is_enabled:
            raise HTTPException(status_code=400, detail=f"Skill is disabled: {normalized_name}")

        model_config = await resolve_agent_model_config(db, request.model_name)
        invoke_result = await agent_skill_service.execute_skill_task(
            prompt=(request.prompt or "").strip(),
            model_config=model_config,
            enabled_skills=[normalized_name]
        )
        return AgentSkillInvokeResponse(skill_name=normalized_name, result=invoke_result)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error invoking skill {skill_name}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to invoke skill: {str(e)}"
        )


@router.post("/public/tools/{skill_name}/invoke", response_model=AgentSkillInvokeResponse)
async def invoke_agent_skill_by_api_key(
    skill_name: str,
    request: AgentSkillInvokeRequest,
    db: AsyncSession = Depends(get_db),
    api_key: str = Depends(verify_agent_skill_api_key)
):
    try:
        normalized_name = (skill_name or "").strip()
        if not normalized_name:
            raise HTTPException(status_code=400, detail="skill_name is required")

        await agent_skill_service.sync_skills_with_db(db)

        query = select(AgentTool).where(AgentTool.name == normalized_name)
        result = await db.execute(query)
        tool = result.scalar_one_or_none()
        if not tool:
            raise HTTPException(status_code=404, detail=f"Skill not found: {normalized_name}")
        if not tool.is_enabled:
            raise HTTPException(status_code=400, detail=f"Skill is disabled: {normalized_name}")

        model_config = await resolve_agent_model_config(db, request.model_name)

        invoke_result = await agent_skill_service.execute_skill_task(
            prompt=(request.prompt or "").strip(),
            model_config=model_config,
            enabled_skills=[normalized_name]
        )
        return AgentSkillInvokeResponse(skill_name=normalized_name, result=invoke_result)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error invoking skill by api key {skill_name}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to invoke skill: {str(e)}"
        )


@router.post("/tools/generate", response_model=AgentToolGenerateResponse)
async def generate_agent_tool_code(
    request: AgentToolGenerateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    生成Agent工具代码
    """
    try:
        # 1. 确定模型配置
        model_config = {}
        if request.model_service_config_id:
            query = select(ModelServiceConfig).where(ModelServiceConfig.id == request.model_service_config_id)
            result = await db.execute(query)
            config = result.scalar_one_or_none()
            if not config:
                raise HTTPException(status_code=404, detail="Model service config not found")
            model_config = {
                'model_name': config.model_name,
                'api_key': config.api_key or "",
                'provider': config.provider,
                'base_url': config.api_endpoint or ""
            }
        else:
            # 尝试使用第一个可用的配置，或者系统默认
            # 这里简单起见，如果没有指定，我们查找第一个启用的配置
            query = select(ModelServiceConfig).where(ModelServiceConfig.is_active == True).limit(1)
            result = await db.execute(query)
            config = result.scalar_one_or_none()
            if config:
                model_config = {
                    'model_name': config.model_name,
                    'api_key': config.api_key or "",
                    'provider': config.provider,
                    'base_url': config.api_endpoint or ""
                }
            else:
                 raise HTTPException(status_code=400, detail="No active model service config found. Please specify one.")

        # 2. 调用 AgentSkillService
        # 使用 execute_skill_task，只启用 agent_skill_generator
        
        # 尝试读取 skill-creator 的指南以增强 Prompt
        skill_guide = ""
        try:
            # 假设 skill-creator 位于 system skills 目录下
            from pathlib import Path
            system_skills_path = Path(agent_skill_service.skill_adapter.system_skills_path)
            skill_creator_md = system_skills_path / "skill-creator" / "SKILL.md"
            
            if skill_creator_md.exists():
                skill_guide = skill_creator_md.read_text(encoding="utf-8")
                # 截取一部分关键原则，避免 Prompt 过长
                # 这里我们提取 "Core Principles" 和 "Anatomy of a Skill" 部分
                # 或者简单地作为参考附录
        except Exception as e:
            logger.warning(f"Failed to load skill-creator guide: {e}")

        # 构造 Prompt
        prompt = f"""
You are an expert in ModelScope Agent development and Skill creation.
I need to generate a new Agent Skill based on the following requirements.

Requirements: {request.requirements}

"""

        prompt_with_guide = prompt
        if skill_guide:
            prompt_with_guide += f"""
Reference Guide (Best Practices for Skill Creation):
---
{skill_guide[:2000]}... (truncated)
---

Based on the guide above, please generate a high-quality skill structure.
The skill MUST include a `SKILL.md` file following the guide's format.
"""

        prompt_with_guide += f"""
Please follow these strict rules:
1. DO NOT use LangChain or any other framework. Use `modelscope-agent` SDK for Python scripts.
2. The output MUST be a valid JSON object where keys are filenames (e.g., "SKILL.md", "scripts/plugin.py") and values are the file content.
3. Provide ONLY the JSON object in your final answer, wrapped in ```json ... ```.

Structure the skill as:
- `SKILL.md`: Metadata and instructions (Required)
- `scripts/`: Directory for Python scripts (if needed)
- `references/`: Directory for documentation (if needed)

Example Output JSON Structure:
{{
  "SKILL.md": "---\\nname: my-skill\\ndescription: ...\\n---\\n\\n# My Skill\\n...",
  "scripts/my_tool.py": "from modelscope_agent.tools import BaseTool, register_tool\\n\\n@register_tool('my_tool')\\nclass MyTool(BaseTool):\\n..."
}}

Now, generate the JSON.
"""
        
        # 首次尝试：带指南
        raw_result = await agent_skill_service.execute_skill_task(
            prompt=prompt_with_guide,
            model_config=model_config,
            enabled_skills=[] # 不使用任何工具，强制直接生成
        )

        # 检查是否失败 (502, timeout, etc causing "Execution failed")
        if "Execution failed" in raw_result or "status code: 502" in raw_result:
            logger.warning("Generation with skill guide failed, retrying without guide...")
            
            # 降级重试：不带指南
            simple_prompt = prompt + f"""
Please follow these strict rules:
1. DO NOT use LangChain or any other framework. Use `modelscope-agent` SDK for Python scripts.
2. The output MUST be a valid JSON object where keys are filenames (e.g., "SKILL.md", "scripts/plugin.py") and values are the file content.
3. Provide ONLY the JSON object in your final answer, wrapped in ```json ... ```.

Structure the skill as:
- `SKILL.md`: Metadata and instructions (Required)
- `scripts/`: Directory for Python scripts (if needed)
- `references/`: Directory for documentation (if needed)

Example Output JSON Structure:
{{
  "SKILL.md": "---\\nname: my-skill\\ndescription: ...\\n---\\n\\n# My Skill\\n...",
  "scripts/my_tool.py": "from modelscope_agent.tools import BaseTool, register_tool\\n\\n@register_tool('my_tool')\\nclass MyTool(BaseTool):\\n..."
}}

Now, generate the JSON.
"""
            raw_result = await agent_skill_service.execute_skill_task(
                prompt=simple_prompt,
                model_config=model_config,
                enabled_skills=[]
            )

        
        # 3. 解析结果
        # 结果可能包含自然语言，也可能直接是JSON。
        # 我们尝试寻找 JSON 块
        import json
        import re
        
        code_structure = {}
        
        # 尝试提取 ```json ... ``` (最常见)
        json_match = re.search(r"```json\s*(.*?)\s*```", raw_result, re.DOTALL)
        if json_match:
            try:
                code_structure = json.loads(json_match.group(1))
            except Exception as e:
                logger.warning(f"Failed to parse JSON block: {e}")
        
        # 尝试提取 ``` ... ``` (没有语言标识)
        if not code_structure:
             json_match = re.search(r"```\s*(\{.*?\})\s*```", raw_result, re.DOTALL)
             if json_match:
                try:
                    code_structure = json.loads(json_match.group(1))
                except Exception as e:
                    logger.warning(f"Failed to parse generic code block as JSON: {e}")

        # 如果没有找到代码块，尝试直接解析（如果整个返回就是JSON）
        if not code_structure:
            try:
                # 尝试清理前后空白
                cleaned_result = raw_result.strip()
                code_structure = json.loads(cleaned_result)
            except:
                pass

        # 尝试更宽泛的正则提取 (寻找最外层的 { ... })
        if not code_structure:
            try:
                # 寻找第一个 { 和最后一个 }
                start = raw_result.find('{')
                end = raw_result.rfind('}')
                if start != -1 and end != -1:
                    json_str = raw_result[start:end+1]
                    code_structure = json.loads(json_str)
            except Exception as e:
                logger.warning(f"Failed to extract JSON using broad search: {e}")
            
        # 如果还是空的，可能在 tool output 里，或者 Agent 没有正确返回 JSON。
        
        return AgentToolGenerateResponse(
            code_structure=code_structure,
            raw_response=raw_result
        )
        
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        logger.error(f"Error generating tool code: {str(e)}\n{traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate tool code: {str(e)}"
        )


@router.post("/tools/", response_model=AgentToolResponse)
async def create_agent_tool(
    tool_data: AgentToolCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    创建Agent工具
    """
    # 只有管理员可以创建工具
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admin can create agent tools"
        )
        
    try:
        # 检查名称是否存在
        query = select(AgentTool).where(AgentTool.name == tool_data.name)
        result = await db.execute(query)
        if result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Tool with name {tool_data.name} already exists"
            )
            
        code_content = tool_data.code
        new_tool = AgentTool(**tool_data.model_dump(exclude={"code"}))
        db.add(new_tool)
        await db.commit()
        await db.refresh(new_tool)
        
        try:
            if code_content:
                path = agent_skill_service.save_or_update_custom_skill(new_tool.name, code_content)
                if path:
                    new_tool.code = agent_skill_service._path_code(path)
                    db.add(new_tool)
                    await db.commit()
                    await db.refresh(new_tool)
        except Exception as e:
            logger.warning(f"Failed to persist custom skill for {new_tool.name}: {e}")
        
        return AgentToolResponse.model_validate(new_tool)
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error creating agent tool: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create agent tool: {str(e)}"
        )


@router.get("/tools/{tool_id}", response_model=AgentToolResponse)
async def get_agent_tool(
    tool_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取单个Agent工具详情
    """
    try:
        query = select(AgentTool).where(AgentTool.id == tool_id)
        result = await db.execute(query)
        tool = result.scalar_one_or_none()
        
        if not tool:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Tool with id {tool_id} not found"
            )
            
        try:
            path = agent_skill_service._extract_path(tool.code)
            if not path:
                skill_info = agent_skill_service.skill_adapter.get_skill(tool.name)
                if skill_info:
                    path = skill_info.get("path", "")
            if path:
                code_content = agent_skill_service._read_skill_files(path)
                if code_content != "{}":
                    tool.code = code_content
        except Exception as e:
            logger.warning(f"Failed to auto-sync skill code for {tool.name}: {e}")
            
        return AgentToolResponse.model_validate(tool)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting agent tool: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get agent tool: {str(e)}"
        )


@router.put("/tools/{tool_id}", response_model=AgentToolResponse)
async def update_agent_tool(
    tool_id: int,
    tool_data: AgentToolUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    更新Agent工具
    """
    # 只有管理员可以更新工具
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admin can update agent tools"
        )
        
    try:
        query = select(AgentTool).where(AgentTool.id == tool_id)
        result = await db.execute(query)
        tool = result.scalar_one_or_none()
        
        if not tool:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Tool with id {tool_id} not found"
            )
            
        # 更新字段
        update_data = tool_data.model_dump(exclude_unset=True)
        code_content = update_data.pop("code", None)
        for field, value in update_data.items():
            setattr(tool, field, value)
            
        await db.commit()
        await db.refresh(tool)
        
        try:
            if code_content is not None:
                path = agent_skill_service.save_or_update_custom_skill(tool.name, code_content)
                if path:
                    tool.code = agent_skill_service._path_code(path)
                    db.add(tool)
                    await db.commit()
                    await db.refresh(tool)
        except Exception as e:
            logger.warning(f"Failed to persist custom skill for {tool.name}: {e}")
        
        return AgentToolResponse.model_validate(tool)
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error updating agent tool: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update agent tool: {str(e)}"
        )


@router.delete("/tools/{tool_id}")
async def delete_agent_tool(
    tool_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    删除Agent工具
    """
    # 只有管理员可以删除工具
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admin can delete agent tools"
        )
        
    try:
        query = select(AgentTool).where(AgentTool.id == tool_id)
        result = await db.execute(query)
        tool = result.scalar_one_or_none()
        
        if not tool:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Tool with id {tool_id} not found"
            )
            
        if tool.is_builtin:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot delete builtin tool"
            )
            
        # 尝试删除文件系统中的技能文件
        try:
            # 只有 custom 类型的工具才可能在文件系统中
            if tool.tool_type == 'custom':
                if agent_skill_service.skill_adapter.delete_skill(tool.name):
                    logger.info(f"Deleted skill files for {tool.name}")
        except Exception as e:
            logger.warning(f"Failed to delete skill files for {tool.name}: {e}")
            # 不阻断数据库删除，但记录日志
            
        await db.delete(tool)
        await db.commit()
        
        return {"message": "Tool deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error deleting agent tool: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete agent tool: {str(e)}"
        )


# ============================================
# Agent聊天功能
# ============================================

@router.post("/{agent_id}/chat", response_model=AgentChatResponse)
async def chat_with_agent(
    agent_id: int,
    chat_request: AgentChatRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    与Agent聊天
    
    Args:
        agent_id: Agent ID
        chat_request: 聊天请求
        db: 数据库会话
        current_user: 当前用户
        
    Returns:
        Agent回复
    """
    try:
        # 验证Agent是否存在且可用，预加载关联对象以避免greenlet错误
        query = select(Agent).options(
            selectinload(Agent.model_service_config)
        ).where(Agent.id == agent_id)
        db_result = await db.execute(query)
        agent = db_result.scalar_one_or_none()
        if not agent:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Agent with id {agent_id} not found"
            )
        
        # 权限检查
        if current_user.role != "admin" and not agent.is_public and agent.created_by != current_user.id:
            if not agent.allowed_users or current_user.id not in agent.allowed_users:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Not enough permissions to chat with this agent"
                )
        
        # 检查Agent状态
        from app.models.agent import AgentStatus
        if agent.status != AgentStatus.ACTIVE:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Agent is not active"
            )
        
        # 检查模型服务配置
        if not agent.model_service_config:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Agent没有配置模型服务"
            )
        
        if not agent.model_service_config.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Agent的模型服务配置未激活"
            )
        
        # 处理记忆功能和历史消息
        context = chat_request.context or {}
        
        # 如果启用了记忆功能，从数据库获取历史消息
        print("agent.memory_enabled:::",agent.memory_enabled)
        if agent.memory_enabled and chat_request.session_id:
            try:
                # 查找或创建会话
                conversation_query = select(AgentConversation).where(
                    and_(
                        AgentConversation.agent_id == agent_id,
                        AgentConversation.user_id == current_user.id,
                        AgentConversation.session_id == chat_request.session_id,
                        AgentConversation.is_active == True
                    )
                )
                conversation_db_result = await db.execute(conversation_query)
                conversation = conversation_db_result.scalar_one_or_none()
                
                if conversation:
                    # 获取历史消息
                    max_history = 10  # 默认最大历史记录数
                    if agent.memory_config and agent.memory_config.get("max_history"):
                        max_history = agent.memory_config["max_history"]
                    
                    messages_query = select(AgentMessage).where(
                        AgentMessage.conversation_id == conversation.id
                    ).order_by(desc(AgentMessage.created_at)).limit(max_history)
                    
                    messages_db_result = await db.execute(messages_query)
                    historical_messages = messages_db_result.scalars().all()
                    
                    # 将历史消息添加到上下文中（按时间正序）
                    previous_messages = []
                    for msg in reversed(historical_messages):
                        previous_messages.append({
                            "role": msg.role,
                            "content": msg.content
                        })
                    
                    # 合并前端传递的历史消息和数据库中的历史消息
                    if context.get("previous_messages"):
                        context["previous_messages"] = previous_messages + context["previous_messages"]
                    else:
                        context["previous_messages"] = previous_messages
                        
            except Exception as e:
                logger.warning(f"Failed to load conversation history: {str(e)}")
                # 记忆功能失败不应该阻止聊天，继续使用前端传递的上下文
        
        # 根据Agent类型选择处理方式
        from app.models.agent import AgentType
        from app.services.ai_model_service import AIModelService

        configured_skill_names = []
        for skill_name in (agent.tools or []):
            if isinstance(skill_name, str):
                cleaned_name = skill_name.strip()
                if cleaned_name and cleaned_name not in configured_skill_names:
                    configured_skill_names.append(cleaned_name)

        enabled_agent_skills = []
        if configured_skill_names:
            skill_query = select(AgentTool).where(
                AgentTool.name.in_(configured_skill_names),
                AgentTool.is_enabled == True
            )
            skill_result = await db.execute(skill_query)
            skill_rows = skill_result.scalars().all()
            enabled_agent_skills = [tool.name for tool in skill_rows]
        
        try:
            if agent.agent_type == AgentType.REVIEW:

                # 创建数据库版本的检测器，使用指令集ID 13
                 # 配置LLM（如果服务可用）

                print("agent.model_service_config:::",agent.model_service_config)
                print("+++++++++++++++++++++++++++++++++")
                llm_config = {
                    "type": agent.model_service_config.provider,
                    "model": agent.model_service_config.model_name,
                    "base_url": agent.model_service_config.api_endpoint,
                    "api_key": agent.model_service_config.api_key,
                    "temperature": float(agent.model_service_config.temperature or 0.7),
                    "top_p": float(agent.model_service_config.top_p or 0.9),
                    "max_tokens": agent.model_service_config.max_tokens or 4096,
                    "frequency_penalty": float(agent.model_service_config.frequency_penalty or 0.0),
                    "presence_penalty": float(agent.model_service_config.presence_penalty or 0.0),
                    "timeout": agent.model_service_config.timeout or 30
                }
                
                detector = EnhancedContentSafetyAgentDB(llm_config=llm_config, instruction_set_id=agent.instruction_set_id)
                # 初始化检测器
                await detector.initialize(db)
                # 审核Agent：直接返回审核结果
                start_time = time.time()
                detection_result = detector.detect_content(chat_request.message)
                end_time = time.time()
                detection_time = end_time - start_time
                
                # 构建详细的检测结果信息
                detection_info = []
                # detection_info.append(f"检测结果: {detection_result.matched}")
                # 英文到中文的风险等级映射
                risk_level_map = {
                    'critical': '严重风险',
                    'high': '高风险', 
                    'medium': '中等风险',
                    'low': '低风险',
                    'safe': '安全'
                }
                risk_level_cn = risk_level_map.get(detection_result.risk_level.value, detection_result.risk_level.value)
                # detection_info.append(f"风险等级: {risk_level_cn}")
                # detection_info.append(f"置信度: {detection_result.confidence:.2f}")
                detection_info.append(f"原文长度: {detection_result.original_length}")
                detection_info.append(f"检测耗时: {detection_time:.3f} 秒")
                detection_info.append(f"Token消耗量: {detection_result.tokens_used}")
                
                if detection_result.evidence:
                    detection_info.append(f"证据: {detection_result.evidence}")
                
                if detection_result.sensitive_excerpt:
                    detection_info.append(f"敏感内容摘录: {detection_result.sensitive_excerpt}")
                
                # 收集匹配的节点信息
                matched_nodes = []
                def collect_matched_nodes(node_result):
                    """递归收集匹配的风险节点信息"""
                    if node_result.matched and node_result.node_id != "1":
                        matched_nodes.append({
                            'id': node_result.node_id,
                            'description': node_result.description,
                            'risk_level': node_result.risk_level.value,
                            'confidence': node_result.confidence,
                            'excerpt': node_result.sensitive_excerpt,
                            'Related_to_the_original_text': node_result.Related_to_the_original_text,
                            'reasoning': node_result.reasoning
                        })
                    for child in node_result.children_results:
                        collect_matched_nodes(child)
                
                collect_matched_nodes(detection_result)
                
                # 按风险等级优先级排序和统计
                risk_priority = {'critical': 4, 'high': 3, 'medium': 2, 'low': 1, 'safe': 0}
                risk_stats = {'严重风险': 0, '高风险': 0, '中等风险': 0, '低风险': 0, '安全': 0}
                # 英文到中文的映射
                risk_level_map = {
                    'critical': '严重风险',
                    'high': '高风险', 
                    'medium': '中等风险',
                    'low': '低风险',
                    'safe': '安全'
                }
                
                # 统计各风险等级的命中数量
                for node in matched_nodes:
                    risk_level = node['risk_level']
                    risk_level_cn = risk_level_map.get(risk_level, risk_level)
                    if risk_level_cn in risk_stats:
                        risk_stats[risk_level_cn] += 1
                
                # 按风险等级优先级排序节点
                matched_nodes.sort(key=lambda x: risk_priority.get(x['risk_level'], 0), reverse=True)
                
                # 获取最高风险等级
                highest_risk_level = '安全'
                highest_risk_confidence = 1
                mg_contents=""
                if matched_nodes:
                    highest_risk_level = risk_level_map.get(matched_nodes[0]['risk_level'], matched_nodes[0]['risk_level'])
                    highest_risk_confidence = matched_nodes[0]['confidence']
                    mg_contents = matched_nodes[0].get('Related_to_the_original_text', matched_nodes[0].get('Related_to_the_original_text', '无法获取相关原文'))
                # 更新检测结果的风险等级为最高风险等级
                detection_info[1] = f"风险等级: {highest_risk_level}"
                detection_info[2] = f"置信度: {highest_risk_confidence:.2f}"
                detection_info[3] = f"敏感内容摘录: {mg_contents}"
                
                # 添加风险等级统计信息
                risk_summary = []
                for level in ['严重风险', '高风险', '中等风险', '低风险', '安全']:
                    count = risk_stats[level]
                    if count > 0:
                        risk_summary.append(f"{level}命中{count}个")
                
                if risk_summary:
                    detection_info.append(f"风险等级统计: {', '.join(risk_summary)}")
                
                if matched_nodes:
                    detection_info.append("匹配的节点:")
                    for node in matched_nodes:
                        detection_info.append(f"  ✓ 匹配节点: {node['id']} - {node['description']}")
                        node_risk_level_cn = risk_level_map.get(node['risk_level'], node['risk_level'])
                        detection_info.append(f"    风险等级: {node_risk_level_cn}")
                        detection_info.append(f"    置信度: {node['confidence']:.2f}")
                        # 显示详细判断理由
                        if node.get('reasoning'):
                            detection_info.append(f"    判断理由: {node['reasoning']}")
                        # 显示检测理由（相关原文）
                        if node.get('Related_to_the_original_text'):
                            detection_info.append(f"    敏感摘录: {node['Related_to_the_original_text']}")
                        # 显示敏感摘录内容（如果存在）
                        # if node.get('excerpt'):
                        #     detection_info.append(f"    敏感摘录: {node['excerpt']}")
                else:
                    detection_info.append("未匹配任何风险节点")
                
                # 将所有检测信息合并为一个字符串
                detailed_message = "\n".join(detection_info)
                
                # 同时打印到控制台（用于调试）
                print(detailed_message)
                print("--------",agent.model_service_config)
                
                result = {
                    "success": True,
                    "message": detailed_message,
                    "tokens_used": detection_result.tokens_used,  # 添加token消耗量
                    "processing_time": detection_time,  # 添加处理时间
                    "meta_data": {
                        "is_violent": False,
                        "is_harmful": False,
                        "is_offensive": False,
                        "is_unsafe": False
                    }
                }

            else:
                if enabled_agent_skills:
                    prompt_parts = []
                    if agent.system_prompt:
                        prompt_parts.append(f"系统提示词：\n{agent.system_prompt}")

                    previous_messages = context.get("previous_messages", []) if context else []
                    if previous_messages:
                        history_lines = []
                        for msg in previous_messages[-10:]:
                            role = msg.get("role", "user")
                            content = msg.get("content", "")
                            if content:
                                history_lines.append(f"{role}: {content}")
                        if history_lines:
                            prompt_parts.append("历史对话：\n" + "\n".join(history_lines))

                    if chat_request.images and len(chat_request.images) > 0:
                        prompt_parts.append(f"用户上传了 {len(chat_request.images)} 张图片。")

                    prompt_parts.append(f"用户问题：\n{chat_request.message}")
                    runtime_prompt = "\n\n".join(prompt_parts)

                    skill_model_config = {
                        'model_name': agent.model_service_config.model_name,
                        'api_key': agent.model_service_config.api_key or "",
                        'provider': agent.model_service_config.provider,
                        'base_url': agent.model_service_config.api_endpoint or ""
                    }
                    skill_response = await agent_skill_service.execute_skill_task(
                        prompt=runtime_prompt,
                        model_config=skill_model_config,
                        enabled_skills=enabled_agent_skills
                    )
                    if isinstance(skill_response, str) and skill_response.startswith("Execution failed:"):
                        result = {
                            "success": False,
                            "error": skill_response,
                            "message": skill_response,
                            "tokens_used": 0,
                            "metadata": {
                                "enabled_skills": enabled_agent_skills
                            }
                        }
                    else:
                        result = {
                            "success": True,
                            "message": skill_response,
                            "tokens_used": 0,
                            "metadata": {
                                "enabled_skills": enabled_agent_skills
                            }
                        }
                else:
                    result = await AIModelService.chat_with_model(
                        config=agent.model_service_config,
                        system_prompt=agent.system_prompt or "",
                        user_message=chat_request.message,
                        context=context,
                        images=chat_request.images
                    )
            
            if not result.get("success", False):
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"AI模型调用失败: {result.get('error', '未知错误')}"
                )
            
            # 生成会话ID
            session_id = chat_request.session_id or f"session_{agent_id}_{int(datetime.now().timestamp())}"
            
            # 如果启用了记忆功能，保存消息到数据库
            if agent.memory_enabled:
                try:
                    # 查找或创建会话
                    conversation_query = select(AgentConversation).where(
                        and_(
                            AgentConversation.agent_id == agent_id,
                            AgentConversation.user_id == current_user.id,
                            AgentConversation.session_id == session_id,
                            AgentConversation.is_active == True
                        )
                    )
                    conversation_result = await db.execute(conversation_query)
                    conversation = conversation_result.scalar_one_or_none()
                    
                    if not conversation:
                        # 创建新会话
                        conversation = AgentConversation(
                            agent_id=agent_id,
                            user_id=current_user.id,
                            session_id=session_id,
                            title=f"与{agent.name}的对话",
                            context={},
                            is_active=True
                        )
                        db.add(conversation)
                        await db.flush()  # 获取conversation.id
                    
                    # 保存用户消息
                    user_message_meta = {}
                    user_content_type = "text"
                    
                    # 如果有图片，更新内容类型和元数据
                    if chat_request.images and len(chat_request.images) > 0:
                        user_content_type = "multimodal"
                        user_message_meta["images"] = chat_request.images
                        user_message_meta["image_count"] = len(chat_request.images)
                    
                    user_message = AgentMessage(
                        conversation_id=conversation.id,
                        role="user",
                        content=chat_request.message,
                        content_type=user_content_type,
                        meta_data=user_message_meta
                    )
                    db.add(user_message)
                    
                    # 保存助手回复
                    assistant_message = AgentMessage(
                        conversation_id=conversation.id,
                        role="assistant",
                        content=result.get("message", ""),
                        content_type="text",
                        tokens_used=result.get("tokens_used", 0),
                        processing_time=result.get("processing_time", 0),
                        meta_data=result.get("metadata", {})
                    )
                    db.add(assistant_message)
                    
                except Exception as e:
                    logger.warning(f"Failed to save conversation messages: {str(e)}")
                    # 保存失败不应该阻止聊天响应
            
            # 更新使用统计
            agent.usage_count += 1
            now_result = await db.execute(select(func.now()))
            agent.last_used_at = now_result.scalar()
            await db.commit()
            
            return AgentChatResponse(
                session_id=session_id,
                message=result.get("message", ""),
                tokens_used=result.get("tokens_used", 0),
                processing_time=result.get("processing_time", 0),
                meta_data={
                    "agent_id": agent_id,
                    "model": agent.model_service_config.name,
                    "provider": agent.model_service_config.provider,
                    "model_name": agent.model_service_config.model_name,
                    "memory_enabled": agent.memory_enabled,
                    **result.get("metadata", {})
                }
            )
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"AI模型调用异常: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"AI模型调用异常: {str(e)}"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error chatting with agent {agent_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to chat with agent: {str(e)}"
        )


# ============================================
# 异步任务管理
# ============================================

@router.get("/tasks/{task_id}", response_model=Dict[str, Any])
async def get_task_status(
    task_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    获取异步任务状态
    
    Args:
        task_id: 任务ID
        current_user: 当前用户
        
    Returns:
        任务状态信息
    """
    try:
        from app.services.async_task_service import async_task_service
        
        task_result = async_task_service.get_task_status(task_id)
        if not task_result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Task with id {task_id} not found"
            )
        
        # 检查任务权限（只有创建任务的用户可以查看）
        if (task_result.metadata and 
            task_result.metadata.get("user_id") != current_user.id and 
            current_user.role != "admin"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions to access this task"
            )
        
        return {
            "task_id": task_result.task_id,
            "status": task_result.status.value,
            "progress": task_result.progress,
            "result": task_result.result,
            "error": task_result.error,
            "created_at": task_result.created_at.isoformat() if task_result.created_at else None,
            "started_at": task_result.started_at.isoformat() if task_result.started_at else None,
            "completed_at": task_result.completed_at.isoformat() if task_result.completed_at else None,
            "metadata": task_result.metadata
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting task status {task_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get task status: {str(e)}"
        )


@router.delete("/tasks/{task_id}", response_model=ResponseModel)
async def cancel_task(
    task_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    取消异步任务
    
    Args:
        task_id: 任务ID
        current_user: 当前用户
        
    Returns:
        取消结果
    """
    try:
        from app.services.async_task_service import async_task_service
        
        task_result = async_task_service.get_task_status(task_id)
        if not task_result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Task with id {task_id} not found"
            )
        
        # 检查任务权限（只有创建任务的用户可以取消）
        if (task_result.metadata and 
            task_result.metadata.get("user_id") != current_user.id and 
            current_user.role != "admin"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions to cancel this task"
            )
        
        success = async_task_service.cancel_task(task_id)
        if success:
            return ResponseModel(message="Task cancelled successfully")
        else:
            return ResponseModel(message="Task is not running or already completed")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error cancelling task {task_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to cancel task: {str(e)}"
        )


# ============================================
# Agent统计信息
# ============================================

@router.get("/stats/", response_model=AgentStatsResponse)
async def get_agent_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取Agent统计信息
    
    Args:
        db: 数据库会话
        current_user: 当前用户
        
    Returns:
        Agent统计信息
    """
    try:
        # 基础统计
        total_agents_query = select(func.count(Agent.id))
        total_agents_result = await db.execute(total_agents_query)
        total_agents = total_agents_result.scalar()
        
        active_agents_query = select(func.count(Agent.id)).where(Agent.status == "active")
        active_agents_result = await db.execute(active_agents_query)
        active_agents = active_agents_result.scalar()
        
        total_conversations_query = select(func.count(AgentConversation.id))
        total_conversations_result = await db.execute(total_conversations_query)
        total_conversations = total_conversations_result.scalar()
        
        total_messages_query = select(func.count(AgentMessage.id))
        total_messages_result = await db.execute(total_messages_query)
        total_messages = total_messages_result.scalar()
        
        # 热门Agent（按使用次数排序）
        popular_agents_query = select(Agent).where(
            Agent.status == "active",
            Agent.is_public == True
        ).order_by(desc(Agent.usage_count)).limit(5)
        
        popular_agents_result = await db.execute(popular_agents_query)
        popular_agents_data = popular_agents_result.scalars().all()
        
        popular_agents = []
        for agent in popular_agents_data:
            item_data = {
                "id": agent.id,
                "name": agent.name,
                "description": agent.description,
                "agent_type": agent.agent_type,
                "status": agent.status,
                "model_service_config_id": agent.model_service_config_id,
                "model_name": agent.model_service_config.name if agent.model_service_config else None,
                "is_public": agent.is_public,
                "usage_count": agent.usage_count,
                "last_used_at": agent.last_used_at,
                "created_by": agent.created_by,
                "creator_name": agent.creator.username if agent.creator else None,
                "created_at": agent.created_at,
                "updated_at": agent.updated_at,
                "tags": agent.tags
            }
            popular_agents.append(item_data)
        
        # 最近会话
        recent_conversations_query = select(AgentConversation).where(
            AgentConversation.user_id == current_user.id
        ).order_by(desc(AgentConversation.updated_at)).limit(5)
        
        recent_conversations_result = await db.execute(recent_conversations_query)
        recent_conversations_data = recent_conversations_result.scalars().all()
        
        recent_conversations = []
        for conv in recent_conversations_data:
            conv_data = {
                "id": conv.id,
                "agent_id": conv.agent_id,
                "session_id": conv.session_id,
                "title": conv.title,
                "context": conv.context,
                "user_id": conv.user_id,
                "is_active": conv.is_active,
                "created_at": conv.created_at,
                "updated_at": conv.updated_at,
                "agent_name": conv.agent.name if conv.agent else None,
                "user_name": conv.user.username if conv.user else None,
                "message_count": (await db.execute(select(func.count(AgentMessage.id)).where(AgentMessage.conversation_id == conv.id))).scalar()
            }
            recent_conversations.append(conv_data)
        
        return AgentStatsResponse(
            total_agents=total_agents,
            active_agents=active_agents,
            total_conversations=total_conversations,
            total_messages=total_messages,
            popular_agents=popular_agents,
            recent_conversations=recent_conversations
        )
        
    except Exception as e:
        logger.error(f"Error getting agent stats: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get agent stats: {str(e)}"
        )


# ============================================
# Agent配置验证
# ============================================

@router.post("/validate-config", response_model=AgentConfigValidationResponse)
async def validate_agent_config(
    config_data: Dict[str, Any],
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    验证Agent配置
    
    Args:
        config_data: 配置数据
        db: 数据库会话
        current_user: 当前用户
        
    Returns:
        验证结果
    """
    try:
        errors = []
        warnings = []
        
        # 验证模型配置
        if "model_config" in config_data:
            model_config = config_data["model_config"]
            if isinstance(model_config, dict):
                # 验证温度参数
                if "temperature" in model_config:
                    temp = model_config["temperature"]
                    if not isinstance(temp, (int, float)) or temp < 0 or temp > 2:
                        errors.append("Temperature must be between 0 and 2")
                
                # 验证最大token数
                if "max_tokens" in model_config:
                    max_tokens = model_config["max_tokens"]
                    if not isinstance(max_tokens, int) or max_tokens < 1 or max_tokens > 8192:
                        errors.append("Max tokens must be between 1 and 8192")
        
        # 验证工具配置
        if "tools" in config_data:
            tools = config_data["tools"]
            if isinstance(tools, list):
                for tool_name in tools:
                    tool_query = select(AgentTool).where(AgentTool.name == tool_name)
                    tool_result = await db.execute(tool_query)
                    tool = tool_result.scalar_one_or_none()
                    if not tool:
                        warnings.append(f"Tool '{tool_name}' not found")
                    elif not tool.is_enabled:
                        warnings.append(f"Tool '{tool_name}' is disabled")
        
        # 验证记忆配置
        if "memory_config" in config_data:
            memory_config = config_data["memory_config"]
            if isinstance(memory_config, dict):
                if "max_history" in memory_config:
                    max_history = memory_config["max_history"]
                    if not isinstance(max_history, int) or max_history < 1 or max_history > 100:
                        errors.append("Max history must be between 1 and 100")
        
        is_valid = len(errors) == 0
        
        return AgentConfigValidationResponse(
            is_valid=is_valid,
            errors=errors,
            warnings=warnings
        )
        
    except Exception as e:
        logger.error(f"Error validating agent config: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to validate agent config: {str(e)}"
        )
