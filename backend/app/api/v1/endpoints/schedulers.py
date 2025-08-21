from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from datetime import datetime, timedelta
import uuid
import logging

from app.core.database import get_db
from app.models import SchedulerNode, SchedulerLock
from app.models.scheduler import SchedulerRole, SchedulerStatus
from app.schemas.scheduler import (
    SchedulerNode as SchedulerNodeSchema,
    SchedulerNodeCreate,
    SchedulerNodeUpdate,
    SchedulerNodeHeartbeat,
    SchedulerNodeStatusUpdate,
    SchedulerClusterStatus,
    SchedulerNodeQueryParams,
    SchedulerNodeListResponse
)
from .auth import get_current_user
from app.models.user import User
from sqlalchemy import and_, or_, func

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/nodes", response_model=SchedulerNodeListResponse)
async def get_scheduler_nodes(
    params: SchedulerNodeQueryParams = Depends(),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取调度器节点列表
    
    Args:
        params: 查询参数
        db: 数据库会话
        current_user: 当前用户
        
    Returns:
        调度器节点列表响应
    """
    try:
        # 构建查询条件
        query = db.query(SchedulerNode)
        
        if params.node_name:
            query = query.filter(SchedulerNode.node_name.ilike(f"%{params.node_name}%"))
        
        if params.role:
            query = query.filter(SchedulerNode.role == params.role)
        
        if params.status:
            query = query.filter(SchedulerNode.status == params.status)
        
        if not params.include_offline:
            query = query.filter(SchedulerNode.status != SchedulerStatus.OFFLINE)
        
        # 获取总数
        total = query.count()
        
        # 分页和排序
        if params.sort_by:
            sort_column = getattr(SchedulerNode, params.sort_by, None)
            if sort_column:
                if params.sort_order == "desc":
                    query = query.order_by(sort_column.desc())
                else:
                    query = query.order_by(sort_column.asc())
        else:
            query = query.order_by(SchedulerNode.registration_time.desc())
        
        nodes = query.offset(params.skip).limit(params.limit).all()
        
        return SchedulerNodeListResponse(
            total=total,
            page=params.page,
            size=params.size,
            pages=(total + params.size - 1) // params.size,
            items=nodes
        )
        
    except Exception as e:
        logger.error(f"获取调度器节点列表失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取调度器节点列表失败"
        )


@router.post("/nodes", response_model=SchedulerNodeSchema)
async def register_scheduler_node(
    node_data: SchedulerNodeCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    注册调度器节点
    
    Args:
        node_data: 节点创建数据
        db: 数据库会话
        current_user: 当前用户
        
    Returns:
        创建的调度器节点
    """
    try:
        # 生成节点ID
        node_id = node_data.node_id or f"scheduler-{uuid.uuid4().hex[:8]}"
        
        # 检查节点ID是否已存在
        existing_node = db.query(SchedulerNode).filter(
            SchedulerNode.node_id == node_id
        ).first()
        
        if existing_node:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"节点ID '{node_id}' 已存在"
            )
        
        # 检查IP和端口组合是否已存在
        existing_endpoint = db.query(SchedulerNode).filter(
            and_(
                SchedulerNode.host_ip == node_data.host_ip,
                SchedulerNode.port == node_data.port
            )
        ).first()
        
        if existing_endpoint:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"地址 {node_data.host_ip}:{node_data.port} 已被使用"
            )
        
        # 创建新节点
        new_node = SchedulerNode(
            node_id=node_id,
            node_name=node_data.node_name,
            host_ip=node_data.host_ip,
            port=node_data.port,
            version=node_data.version,
            capabilities=node_data.capabilities,
            resource_info=node_data.resource_info,
            metadata=node_data.metadata,
            role=SchedulerRole.FOLLOWER,  # 新节点默认为FOLLOWER
            status=SchedulerStatus.ONLINE,
            registration_time=datetime.utcnow(),
            last_heartbeat=datetime.utcnow()
        )
        
        db.add(new_node)
        db.commit()
        db.refresh(new_node)
        
        logger.info(f"调度器节点注册成功: {node_id}")
        return new_node
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"注册调度器节点失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="注册调度器节点失败"
        )


@router.get("/nodes/{node_id}", response_model=SchedulerNodeSchema)
async def get_scheduler_node(
    node_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取调度器节点详情
    
    Args:
        node_id: 节点ID
        db: 数据库会话
        current_user: 当前用户
        
    Returns:
        调度器节点详情
    """
    try:
        node = db.query(SchedulerNode).filter(
            SchedulerNode.node_id == node_id
        ).first()
        
        if not node:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"调度器节点 '{node_id}' 不存在"
            )
        
        return node
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取调度器节点详情失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取调度器节点详情失败"
        )


@router.put("/nodes/{node_id}", response_model=SchedulerNodeSchema)
async def update_scheduler_node(
    node_id: str,
    node_data: SchedulerNodeUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    更新调度器节点信息
    
    Args:
        node_id: 节点ID
        node_data: 节点更新数据
        db: 数据库会话
        current_user: 当前用户
        
    Returns:
        更新后的调度器节点
    """
    try:
        node = db.query(SchedulerNode).filter(
            SchedulerNode.node_id == node_id
        ).first()
        
        if not node:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"调度器节点 '{node_id}' 不存在"
            )
        
        # 更新字段
        update_data = node_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(node, field, value)
        
        db.commit()
        db.refresh(node)
        
        logger.info(f"调度器节点更新成功: {node_id}")
        return node
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"更新调度器节点失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="更新调度器节点失败"
        )


@router.delete("/nodes/{node_id}")
async def unregister_scheduler_node(
    node_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    注销调度器节点
    
    Args:
        node_id: 节点ID
        db: 数据库会话
        current_user: 当前用户
        
    Returns:
        操作结果
    """
    try:
        node = db.query(SchedulerNode).filter(
            SchedulerNode.node_id == node_id
        ).first()
        
        if not node:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"调度器节点 '{node_id}' 不存在"
            )
        
        # 如果是Leader节点，需要触发重新选举
        if node.role == SchedulerRole.LEADER:
            logger.warning(f"Leader节点 {node_id} 被注销，需要重新选举")
            # 这里可以添加Leader选举逻辑
        
        db.delete(node)
        db.commit()
        
        logger.info(f"调度器节点注销成功: {node_id}")
        return {"message": f"调度器节点 '{node_id}' 注销成功"}
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"注销调度器节点失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="注销调度器节点失败"
        )


@router.post("/nodes/{node_id}/heartbeat")
async def update_scheduler_heartbeat(
    node_id: str,
    heartbeat_data: SchedulerNodeHeartbeat,
    db: AsyncSession = Depends(get_db)
):
    """
    更新调度器节点心跳
    
    Args:
        node_id: 节点ID
        heartbeat_data: 心跳数据
        db: 数据库会话
        
    Returns:
        操作结果
    """
    try:
        node = db.query(SchedulerNode).filter(
            SchedulerNode.node_id == node_id
        ).first()
        
        if not node:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"调度器节点 '{node_id}' 不存在"
            )
        
        # 更新心跳时间
        node.last_heartbeat = datetime.utcnow()
        
        # 更新其他字段
        if heartbeat_data.status is not None:
            node.status = heartbeat_data.status
        
        if heartbeat_data.role is not None:
            node.role = heartbeat_data.role
        
        if heartbeat_data.version is not None:
            node.version = heartbeat_data.version
        
        if heartbeat_data.capabilities is not None:
            node.capabilities = heartbeat_data.capabilities
        
        if heartbeat_data.resource_usage is not None:
            # 更新节点元数据中的资源使用情况
            if node.node_metadata is None:
                node.node_metadata = {}
            node.node_metadata.update(heartbeat_data.resource_usage)
        
        if heartbeat_data.node_metadata is not None:
            # 更新节点元数据
            if node.node_metadata is None:
                node.node_metadata = {}
            node.node_metadata.update(heartbeat_data.node_metadata)
        
        db.commit()
        
        return {
            "message": "心跳更新成功",
            "timestamp": node.last_heartbeat,
            "status": node.status,
            "role": node.role
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"更新调度器节点心跳失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="更新调度器节点心跳失败"
        )


@router.post("/nodes/{node_id}/status")
async def update_scheduler_status(
    node_id: str,
    status_data: SchedulerNodeStatusUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    更新调度器节点状态
    
    Args:
        node_id: 节点ID
        status_data: 状态更新数据
        db: 数据库会话
        current_user: 当前用户
        
    Returns:
        操作结果
    """
    try:
        node = db.query(SchedulerNode).filter(
            SchedulerNode.node_id == node_id
        ).first()
        
        if not node:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"调度器节点 '{node_id}' 不存在"
            )
        
        old_status = node.status
        node.status = status_data.status
        
        if status_data.metadata:
            node.node_metadata = {**(node.node_metadata or {}), **status_data.metadata}
        
        db.commit()
        
        logger.info(f"调度器节点 {node_id} 状态从 {old_status} 更新为 {status_data.status}")
        
        return {
            "message": "状态更新成功",
            "old_status": old_status,
            "new_status": status_data.status,
            "reason": status_data.reason
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"更新调度器节点状态失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="更新调度器节点状态失败"
        )


@router.get("/cluster/status", response_model=SchedulerClusterStatus)
async def get_cluster_status(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取调度器集群状态
    
    Args:
        db: 数据库会话
        current_user: 当前用户
        
    Returns:
        集群状态信息
    """
    try:
        # 获取所有节点
        all_nodes = db.query(SchedulerNode).all()
        total_nodes = len(all_nodes)
        
        # 统计在线节点
        online_nodes = len([
            node for node in all_nodes 
            if node.status == SchedulerStatus.ONLINE
        ])
        
        # 查找Leader节点
        leader_node = db.query(SchedulerNode).filter(
            SchedulerNode.role == SchedulerRole.LEADER
        ).first()
        
        # 判断集群健康状态
        if total_nodes == 0:
            cluster_health = "no_nodes"
        elif online_nodes == 0:
            cluster_health = "all_offline"
        elif leader_node is None:
            cluster_health = "no_leader"
        elif leader_node.status != SchedulerStatus.ONLINE:
            cluster_health = "leader_offline"
        elif online_nodes < total_nodes * 0.5:
            cluster_health = "degraded"
        else:
            cluster_health = "healthy"
        
        return SchedulerClusterStatus(
            total_nodes=total_nodes,
            online_nodes=online_nodes,
            leader_node_id=leader_node.node_id if leader_node else None,
            leader_node_name=leader_node.node_name if leader_node else None,
            leader_election_time=leader_node.leader_election_time if leader_node else None,
            cluster_health=cluster_health,
            nodes=all_nodes
        )
        
    except Exception as e:
        logger.error(f"获取集群状态失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取集群状态失败"
        )


@router.post("/cluster/elect-leader")
async def trigger_leader_election(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    触发Leader选举
    
    Args:
        db: 数据库会话
        current_user: 当前用户
        
    Returns:
        选举结果
    """
    try:
        # 获取所有在线的FOLLOWER和CANDIDATE节点
        candidate_nodes = db.query(SchedulerNode).filter(
            and_(
                SchedulerNode.status == SchedulerStatus.ONLINE,
                or_(
                    SchedulerNode.role == SchedulerRole.FOLLOWER,
                    SchedulerNode.role == SchedulerRole.CANDIDATE
                )
            )
        ).order_by(SchedulerNode.registration_time.asc()).all()
        
        if not candidate_nodes:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="没有可用的候选节点进行Leader选举"
            )
        
        # 简单的Leader选举：选择注册时间最早的节点
        new_leader = candidate_nodes[0]
        
        # 将当前Leader设为FOLLOWER
        current_leader = db.query(SchedulerNode).filter(
            SchedulerNode.role == SchedulerRole.LEADER
        ).first()
        
        if current_leader:
            current_leader.role = SchedulerRole.FOLLOWER
        
        # 设置新Leader
        new_leader.role = SchedulerRole.LEADER
        new_leader.leader_election_time = datetime.utcnow()
        
        # 将其他候选节点设为FOLLOWER
        for node in candidate_nodes[1:]:
            if node.role == SchedulerRole.CANDIDATE:
                node.role = SchedulerRole.FOLLOWER
        
        db.commit()
        
        logger.info(f"Leader选举完成，新Leader: {new_leader.node_id}")
        
        return {
            "message": "Leader选举成功",
            "new_leader_id": new_leader.node_id,
            "new_leader_name": new_leader.node_name,
            "election_time": new_leader.leader_election_time,
            "previous_leader_id": current_leader.node_id if current_leader else None
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Leader选举失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Leader选举失败"
        )


@router.post("/maintenance/cleanup-offline")
async def cleanup_offline_nodes(
    offline_threshold_minutes: int = Query(30, description="离线阈值（分钟）"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    清理离线节点
    
    Args:
        offline_threshold_minutes: 离线阈值（分钟）
        db: 数据库会话
        current_user: 当前用户
        
    Returns:
        清理结果
    """
    try:
        threshold_time = datetime.utcnow() - timedelta(minutes=offline_threshold_minutes)
        
        # 查找超过阈值时间未心跳的节点
        offline_nodes = db.query(SchedulerNode).filter(
            or_(
                SchedulerNode.last_heartbeat < threshold_time,
                SchedulerNode.last_heartbeat.is_(None)
            )
        ).all()
        
        cleaned_nodes = []
        leader_changed = False
        
        for node in offline_nodes:
            # 如果是Leader节点离线，需要触发重新选举
            if node.role == SchedulerRole.LEADER:
                leader_changed = True
                logger.warning(f"Leader节点 {node.node_id} 离线，将触发重新选举")
            
            # 标记为离线
            node.status = SchedulerStatus.OFFLINE
            if node.role == SchedulerRole.LEADER:
                node.role = SchedulerRole.FOLLOWER
            
            cleaned_nodes.append({
                "node_id": node.node_id,
                "node_name": node.node_name,
                "last_heartbeat": node.last_heartbeat
            })
        
        db.commit()
        
        # 如果Leader离线，触发重新选举
        if leader_changed:
            try:
                # 这里可以调用Leader选举逻辑
                pass
            except Exception as e:
                logger.error(f"自动Leader选举失败: {str(e)}")
        
        logger.info(f"清理了 {len(cleaned_nodes)} 个离线节点")
        
        return {
            "message": f"成功清理 {len(cleaned_nodes)} 个离线节点",
            "cleaned_nodes": cleaned_nodes,
            "leader_changed": leader_changed,
            "threshold_minutes": offline_threshold_minutes
        }
        
    except Exception as e:
        db.rollback()
        logger.error(f"清理离线节点失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="清理离线节点失败"
        )