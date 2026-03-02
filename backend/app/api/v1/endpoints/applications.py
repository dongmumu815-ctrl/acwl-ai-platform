from fastapi import APIRouter, Depends, Query, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Any, Dict

from app.core.database import get_db, AsyncSessionLocal
from app.api.v1.endpoints.auth import get_current_active_user
from app.models.user import User
from app.models.server import Server
from app.schemas.common import PaginatedResponse
from app.crud.application import harbor_config, app_template, app_instance
from app.services.application_service import ApplicationService
from app.schemas.application import (
    HarborConfig, HarborConfigCreate, HarborConfigUpdate, HarborTestConnection,
    AppTemplate, AppTemplateCreate, AppTemplateUpdate,
    AppInstance, AppInstanceCreate, AppInstanceUpdate,
    AppStatus
)
import httpx

router = APIRouter()

async def run_deploy_task(instance_id: int):
    """
    后台任务：执行应用部署
    """
    async with AsyncSessionLocal() as db:
        service = ApplicationService(db)
        await service.deploy_app(instance_id)

async def run_cleanup_task(nodes_info: List[Dict[str, Any]]):
    """
    后台任务：清理节点
    """
    async with AsyncSessionLocal() as db:
        service = ApplicationService(db)
        await service.cleanup_removed_nodes(nodes_info)

# --- Harbor Configs ---

@router.get("/harbor-configs", response_model=PaginatedResponse[HarborConfig], summary="获取Harbor配置列表")
async def get_harbor_configs(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    items, total = await harbor_config.get_multi(db, skip=(page - 1) * size, limit=size)
    return PaginatedResponse(
        items=items, total=total, page=page, size=size, pages=(total + size - 1) // size
    )

@router.post("/harbor-configs/test-connection", summary="测试Harbor连接")
async def test_harbor_connection(
    obj_in: HarborTestConnection,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    url = obj_in.url
    username = obj_in.username
    password = obj_in.password

    # 如果有 ID 且密码为空，从数据库获取
    if obj_in.id and not password:
        db_obj = await harbor_config.get(db, obj_in.id)
        if db_obj:
            password = db_obj.password

    if not password:
        raise HTTPException(status_code=400, detail="密码不能为空")

    # 去掉 URL 末尾的斜杠
    if url.endswith("/"):
        url = url[:-1]

    try:
        async with httpx.AsyncClient(verify=False, timeout=10.0) as client:
            # 尝试获取当前用户信息
            # Harbor API: /api/v2.0/users/current
            resp = await client.get(
                f"{url}/api/v2.0/users/current",
                auth=(username, password)
            )
            
            if resp.status_code == 200:
                return {"success": True, "message": "连接成功"}
            elif resp.status_code == 401:
                return {"success": False, "message": "用户名或密码错误"}
            else:
                return {"success": False, "message": f"连接失败: {resp.status_code} {resp.text[:100]}"}
    except Exception as e:
        return {"success": False, "message": f"连接异常: {str(e)}"}


@router.post("/harbor-configs", response_model=HarborConfig, summary="创建Harbor配置")
async def create_harbor_config(
    obj_in: HarborConfigCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    return await harbor_config.create(db, obj_in, current_user.id)

@router.put("/harbor-configs/{id}", response_model=HarborConfig, summary="更新Harbor配置")
async def update_harbor_config(
    id: int,
    obj_in: HarborConfigUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    db_obj = await harbor_config.get(db, id)
    if not db_obj:
        raise HTTPException(status_code=404, detail="Harbor config not found")
    return await harbor_config.update(db, db_obj, obj_in, current_user.id)

@router.delete("/harbor-configs/{id}", summary="删除Harbor配置")
async def delete_harbor_config(
    id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    success = await harbor_config.delete(db, id)
    if not success:
        raise HTTPException(status_code=404, detail="Harbor config not found")
    return {"success": True}

# --- App Templates ---

@router.get("/templates", response_model=PaginatedResponse[AppTemplate], summary="获取应用模板列表")
async def get_app_templates(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    items, total = await app_template.get_multi(db, skip=(page - 1) * size, limit=size)
    return PaginatedResponse(
        items=items, total=total, page=page, size=size, pages=(total + size - 1) // size
    )

@router.post("/templates", response_model=AppTemplate, summary="创建应用模板")
async def create_app_template(
    obj_in: AppTemplateCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    return await app_template.create(db, obj_in, current_user.id)

@router.put("/templates/{id}", response_model=AppTemplate, summary="更新应用模板")
async def update_app_template(
    id: int,
    obj_in: AppTemplateUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    db_obj = await app_template.get(db, id)
    if not db_obj:
        raise HTTPException(status_code=404, detail="App template not found")
    return await app_template.update(db, db_obj, obj_in, current_user.id)

@router.delete("/templates/{id}", summary="删除应用模板")
async def delete_app_template(
    id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    success = await app_template.delete(db, id)
    if not success:
        raise HTTPException(status_code=404, detail="App template not found")
    return {"success": True}

# --- App Instances ---

@router.get("/instances", response_model=PaginatedResponse[AppInstance], summary="获取应用实例列表")
async def get_app_instances(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    items, total = await app_instance.get_multi(db, skip=(page - 1) * size, limit=size)
    return PaginatedResponse(
        items=items, total=total, page=page, size=size, pages=(total + size - 1) // size
    )

@router.get("/instances/{id}", response_model=AppInstance, summary="获取应用实例详情")
async def get_app_instance_detail(
    id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    item = await app_instance.get(db, id)
    if not item:
        raise HTTPException(status_code=404, detail="App instance not found")
    return item

@router.put("/instances/{id}", response_model=AppInstance, summary="更新应用实例(含扩缩容)")
async def update_app_instance(
    id: int,
    obj_in: AppInstanceUpdate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    db_obj = await app_instance.get(db, id)
    if not db_obj:
        raise HTTPException(status_code=404, detail="App instance not found")
        
    # 如果更新了部署列表，计算差异并触发清理
    if obj_in.deployments is not None:
        # 现有部署
        current_map = {(d.server_id, d.role): d for d in db_obj.deployments}
        # 新部署Key
        new_keys = set((d.server_id, d.role if d.role else "default") for d in obj_in.deployments)
        
        removed_ids = []
        removed_deployments = []
        
        for key, deploy in current_map.items():
            if key not in new_keys:
                removed_ids.append(deploy.server_id)
                removed_deployments.append(deploy)
        
        if removed_ids:
            # 获取服务器信息
            stmt = select(Server).where(Server.id.in_(removed_ids))
            result = await db.execute(stmt)
            servers = {s.id: s for s in result.scalars().all()}
            
            cleanup_info = []
            for d in removed_deployments:
                srv = servers.get(d.server_id)
                if srv:
                    info = {
                        "server_info": {
                            "ip_address": srv.ip_address,
                            "ssh_port": srv.ssh_port,
                            "ssh_username": srv.ssh_username,
                            "ssh_password": srv.ssh_password,
                            "ssh_key_path": getattr(srv, "ssh_key_path", None)
                        },
                        "deploy_path": f"/opt/acwl-apps/instances/{d.instance_id}"
                    }
                    cleanup_info.append(info)
            
            if cleanup_info:
                background_tasks.add_task(run_cleanup_task, cleanup_info)

    # 更新数据库
    updated_instance = await app_instance.update(db, db_obj, obj_in, current_user.id)
    
    # 触发部署任务 (处理新增和配置变更)
    background_tasks.add_task(run_deploy_task, updated_instance.id)
    
    return updated_instance

@router.post("/instances", response_model=AppInstance, summary="部署新应用")
async def create_app_instance(
    obj_in: AppInstanceCreate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    # 创建数据库记录
    instance = await app_instance.create(db, obj_in, current_user.id)
    
    # 触发异步部署任务
    background_tasks.add_task(run_deploy_task, instance.id)
    
    return instance

async def run_uninstall_task(instance_id: int, clean_data: bool = False):
    """
    后台任务：执行应用卸载
    """
    async with AsyncSessionLocal() as db:
        service = ApplicationService(db)
        await service.uninstall_app(instance_id, clean_data)

@router.delete("/instances/{id}", summary="删除应用实例")
async def delete_app_instance(
    id: int,
    background_tasks: BackgroundTasks,
    clean_data: bool = Query(False, description="是否清理数据目录"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    item = await app_instance.get(db, id)
    if not item:
        raise HTTPException(status_code=404, detail="App instance not found")
        
    # 触发异步卸载任务（包含停止、删除容器和删除数据库记录）
    background_tasks.add_task(run_uninstall_task, id, clean_data)
    
    return {"success": True, "message": "Uninstall task submitted"}

@router.post("/instances/{id}/actions/initialize-doris", summary="初始化 Doris 集群")
async def initialize_doris_cluster(
    id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    初始化 Doris 集群 (自动注册 BE/Follower)
    """
    service = ApplicationService(db)
    try:
        result = await service.initialize_doris_cluster(id)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# TODO: Add action endpoints (start, stop, etc.)
