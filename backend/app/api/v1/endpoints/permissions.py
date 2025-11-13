"""
权限管理API路由
提供权限的CRUD操作接口
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.dependencies import get_db, get_current_user_sync as get_current_user
from app.crud.permission import crud_permission
from app.crud.role import crud_role_permission
from app.models.user import User
from app.schemas.permission import (
    PermissionCreate, PermissionUpdate, PermissionResponse, PermissionListResponse,
    PermissionTreeResponse, PermissionTreeListResponse, PermissionTreeNode, PermissionModuleResponse, PermissionWithRoles,
    UserPermissionResponse
)
from app.schemas.common import ResponseModel

router = APIRouter()

@router.get("/me", response_model=ResponseModel[UserPermissionResponse])
def get_my_permissions(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取当前认证用户的所有权限与角色代码

    - 使用认证信息解析当前用户，无需传入用户ID
    - 返回字段包含：`permissions`、`permission_codes`、`role_codes`
    """
    # 基于当前认证用户ID查询权限与角色代码
    permissions = crud_permission.get_user_permissions(db=db, user_id=current_user.id)
    permission_codes = crud_permission.get_permission_codes_by_user(db=db, user_id=current_user.id)
    role_codes = current_user.get_role_codes()

    return ResponseModel(
        data=UserPermissionResponse(
            user_id=current_user.id,
            username=current_user.username,
            permissions=[PermissionResponse.model_validate(perm) for perm in permissions],
            permission_codes=permission_codes,
            role_codes=role_codes
        ),
        message="获取当前用户权限成功"
    )

@router.get("/check/{permission_code}", response_model=ResponseModel[bool])
def check_my_permission(
    permission_code: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    检查当前认证用户是否拥有指定权限

    - 使用认证信息解析当前用户，无需传入用户ID
    - 返回布尔值表示是否拥有指定权限
    """
    has_permission = crud_permission.check_user_permission(
        db=db, user_id=current_user.id, permission_code=permission_code
    )
    return ResponseModel(data=has_permission, message="权限检查完成")


@router.get("/", response_model=ResponseModel[PermissionListResponse])
def get_permissions(
    skip: int = Query(0, ge=0, description="跳过的记录数"),
    limit: int = Query(100, ge=1, le=1000, description="返回的记录数"),
    name: Optional[str] = Query(None, description="权限名称（模糊搜索）"),
    module: Optional[str] = Query(None, description="模块筛选"),
    resource: Optional[str] = Query(None, description="资源筛选"),
    action: Optional[str] = Query(None, description="操作筛选"),
    status: Optional[bool] = Query(None, description="状态筛选"),
    is_system: Optional[bool] = Query(None, description="是否系统权限"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取权限列表
    支持分页和筛选
    """
    permissions, total = crud_permission.get_multi(
        db=db, 
        skip=skip, 
        limit=limit,
        name=name,
        module=module,
        resource=resource,
        action=action,
        status=status,
        is_system=is_system
    )
    
    return ResponseModel(
        data=PermissionListResponse(
            items=[PermissionResponse.model_validate(perm) for perm in permissions],
            total=total,
            page=skip // limit + 1,
            size=limit
        ),
        message="获取权限列表成功"
    )


@router.get("/tree", response_model=ResponseModel[PermissionTreeListResponse])
def get_permissions_tree(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取权限树形结构（按模块分组）
    """
    tree_data = crud_permission.get_tree_structure(db=db)
    
    tree_nodes = []
    for module, permissions in tree_data.items():
        permission_nodes = []
        for perm in permissions:
            permission_nodes.append(PermissionTreeNode(
                id=perm.id,
                name=perm.name,
                code=perm.code,
                module=perm.module,
                resource=perm.resource,
                action=perm.action,
                is_system=perm.is_system,
                status=perm.status,
                sort_order=perm.sort_order,
                role_count=getattr(perm, 'role_count', 0)
            ))
        
        tree_nodes.append(PermissionTreeResponse(
            module=module,
            permissions=permission_nodes
        ))
    
    return ResponseModel(
        data=PermissionTreeListResponse(modules=tree_nodes),
        message="获取权限树形结构成功"
    )


@router.get("/modules", response_model=ResponseModel[List[str]])
def get_permission_modules(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取所有权限模块
    """
    modules = crud_permission.get_modules(db=db)
    
    return ResponseModel(
        data=modules,
        message="获取权限模块成功"
    )


@router.get("/modules/{module}", response_model=ResponseModel[List[PermissionResponse]])
def get_permissions_by_module(
    module: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    根据模块获取权限列表
    """
    permissions = crud_permission.get_by_module(db=db, module=module)
    
    return ResponseModel(
        data=[PermissionResponse.model_validate(perm) for perm in permissions],
        message="获取模块权限成功"
    )


@router.get("/{permission_id}", response_model=ResponseModel[PermissionResponse])
def get_permission(
    permission_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    根据ID获取权限详情
    """
    permission = crud_permission.get(db=db, permission_id=permission_id)
    if not permission:
        raise HTTPException(status_code=404, detail="权限不存在")
    
    return ResponseModel(
        data=PermissionResponse.model_validate(permission),
        message="获取权限详情成功"
    )


@router.post("/", response_model=ResponseModel[PermissionResponse])
def create_permission(
    permission_in: PermissionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    创建新权限
    """
    # 检查权限代码是否已存在
    existing_permission = crud_permission.get_by_code(db=db, code=permission_in.code)
    if existing_permission:
        raise HTTPException(status_code=400, detail="权限代码已存在")
    
    # 检查权限名称是否已存在
    existing_name = crud_permission.get_by_name(db=db, name=permission_in.name)
    if existing_name:
        raise HTTPException(status_code=400, detail="权限名称已存在")
    
    permission = crud_permission.create(db=db, obj_in=permission_in, created_by=current_user.id)
    
    return ResponseModel(
        data=PermissionResponse.model_validate(permission),
        message="创建权限成功"
    )


@router.post("/batch", response_model=ResponseModel[List[PermissionResponse]])
def batch_create_permissions(
    permissions_in: List[PermissionCreate],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    批量创建权限
    """
    # 检查权限代码是否重复
    codes = [perm.code for perm in permissions_in]
    if len(codes) != len(set(codes)):
        raise HTTPException(status_code=400, detail="权限代码存在重复")
    
    # 检查权限代码是否已存在
    for perm in permissions_in:
        existing = crud_permission.get_by_code(db=db, code=perm.code)
        if existing:
            raise HTTPException(status_code=400, detail=f"权限代码 {perm.code} 已存在")
    
    permissions = crud_permission.batch_create(db=db, permissions_data=permissions_in, created_by=current_user.id)
    
    return ResponseModel(
        data=[PermissionResponse.model_validate(perm) for perm in permissions],
        message="批量创建权限成功"
    )


@router.put("/{permission_id}", response_model=ResponseModel[PermissionResponse])
def update_permission(
    permission_id: int,
    permission_in: PermissionUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    更新权限信息
    """
    permission = crud_permission.get(db=db, permission_id=permission_id)
    if not permission:
        raise HTTPException(status_code=404, detail="权限不存在")
    
    # 系统权限不能修改
    if permission.is_system:
        raise HTTPException(status_code=400, detail="系统权限不能修改")
    
    # 检查权限代码是否已存在（排除当前权限）
    if permission_in.code and permission_in.code != permission.code:
        existing_permission = crud_permission.get_by_code(db=db, code=permission_in.code)
        if existing_permission:
            raise HTTPException(status_code=400, detail="权限代码已存在")
    
    # 检查权限名称是否已存在（排除当前权限）
    if permission_in.name and permission_in.name != permission.name:
        existing_name = crud_permission.get_by_name(db=db, name=permission_in.name)
        if existing_name:
            raise HTTPException(status_code=400, detail="权限名称已存在")
    
    permission = crud_permission.update(db=db, db_obj=permission, obj_in=permission_in, updated_by=current_user.id)
    
    return ResponseModel(
        data=PermissionResponse.model_validate(permission),
        message="更新权限成功"
    )


@router.delete("/{permission_id}", response_model=ResponseModel[bool])
def delete_permission(
    permission_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    删除权限
    """
    permission = crud_permission.get(db=db, permission_id=permission_id)
    if not permission:
        raise HTTPException(status_code=404, detail="权限不存在")
    
    # 系统权限不能删除
    if permission.is_system:
        raise HTTPException(status_code=400, detail="系统权限不能删除")
    
    # 检查是否有角色使用该权限
    roles = crud_role_permission.get_roles_by_permission(db=db, permission_id=permission_id)
    if roles:
        raise HTTPException(status_code=400, detail=f"该权限正在被 {len(roles)} 个角色使用，无法删除")
    
    success = crud_permission.delete(db=db, permission_id=permission_id)
    if not success:
        raise HTTPException(status_code=400, detail="删除权限失败")
    
    return ResponseModel(
        data=True,
        message="删除权限成功"
    )


@router.get("/{permission_id}/roles", response_model=ResponseModel[PermissionWithRoles])
def get_permission_roles(
    permission_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取拥有指定权限的角色列表
    """
    permission = crud_permission.get_with_roles(db=db, permission_id=permission_id)
    if not permission:
        raise HTTPException(status_code=404, detail="权限不存在")
    
    return ResponseModel(
        data=PermissionWithRoles.model_validate(permission),
        message="获取权限角色成功"
    )


@router.get("/user/{user_id}", response_model=ResponseModel[UserPermissionResponse])
def get_user_permissions(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取用户的所有权限与角色代码
    
    - 返回字段包含：`permissions`、`permission_codes`、`role_codes`
    - 其中 `role_codes` 来自新角色系统，支持多角色场景
    """
    # 验证用户是否存在
    from app.crud.user import crud_user
    user = crud_user.get(db=db, id=user_id)
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    permissions = crud_permission.get_user_permissions(db=db, user_id=user_id)
    permission_codes = crud_permission.get_permission_codes_by_user(db=db, user_id=user_id)
    # 计算用户角色代码（新角色系统），仅返回启用状态的角色
    role_codes = user.get_role_codes()
    
    return ResponseModel(
        data=UserPermissionResponse(
            # 补充 username 字段，避免响应模型缺失导致 500
            user_id=user_id,
            username=user.username,
            permissions=[PermissionResponse.model_validate(perm) for perm in permissions],
            permission_codes=permission_codes,
            role_codes=role_codes
        ),
        message="获取用户权限成功"
    )


@router.get("/check/{user_id}/{permission_code}", response_model=ResponseModel[bool])
def check_user_permission(
    user_id: int,
    permission_code: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    检查用户是否拥有指定权限
    """
    has_permission = crud_permission.check_user_permission(db=db, user_id=user_id, permission_code=permission_code)
    
    return ResponseModel(
        data=has_permission,
        message="权限检查完成"
    )