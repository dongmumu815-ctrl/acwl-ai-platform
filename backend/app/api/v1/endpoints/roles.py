"""
角色管理API路由
提供角色的CRUD操作接口
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.dependencies import get_db, get_current_user_sync as get_current_user
from app.crud.role import crud_role, crud_user_role, crud_role_permission
from app.crud.permission import crud_permission
from app.models.user import User
from app.schemas.role import (
    RoleCreate, RoleUpdate, RoleResponse, RoleListResponse,
    UserRoleCreate, UserRoleResponse, 
    RolePermissionCreate, RolePermissionBatchCreate, RolePermissionResponse,
    RoleWithPermissions, UserWithRoles
)
from app.schemas.common import ResponseModel

router = APIRouter()


@router.get("/", response_model=ResponseModel[RoleListResponse])
def get_roles(
    skip: int = Query(0, ge=0, description="跳过的记录数"),
    limit: int = Query(100, ge=1, le=1000, description="返回的记录数"),
    name: Optional[str] = Query(None, description="角色名称（模糊搜索）"),
    status: Optional[bool] = Query(None, description="状态筛选"),
    is_system: Optional[bool] = Query(None, description="是否系统角色"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取角色列表
    支持分页和筛选
    """
    roles, total = crud_role.get_multi(
        db=db, 
        skip=skip, 
        limit=limit,
        name=name,
        status=status,
        is_system=is_system
    )
    
    return ResponseModel(
        data=RoleListResponse(
            items=[RoleResponse.model_validate(role) for role in roles],
            total=total,
            page=skip // limit + 1,
            size=limit
        ),
        message="获取角色列表成功"
    )


@router.get("/{role_id}", response_model=ResponseModel[RoleResponse])
def get_role(
    role_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    根据ID获取角色详情
    """
    role = crud_role.get(db=db, role_id=role_id)
    if not role:
        raise HTTPException(status_code=404, detail="角色不存在")
    
    return ResponseModel(
        data=RoleResponse.model_validate(role),
        message="获取角色详情成功"
    )


@router.post("/", response_model=ResponseModel[RoleResponse])
def create_role(
    role_in: RoleCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    创建新角色
    """
    # 检查角色代码是否已存在
    existing_role = crud_role.get_by_code(db=db, code=role_in.code)
    if existing_role:
        raise HTTPException(status_code=400, detail="角色代码已存在")
    
    # 检查角色名称是否已存在
    existing_name = crud_role.get_by_name(db=db, name=role_in.name)
    if existing_name:
        raise HTTPException(status_code=400, detail="角色名称已存在")
    
    role = crud_role.create(db=db, obj_in=role_in, created_by=current_user.id)
    
    return ResponseModel(
        data=RoleResponse.model_validate(role),
        message="创建角色成功"
    )


@router.put("/{role_id}", response_model=ResponseModel[RoleResponse])
def update_role(
    role_id: int,
    role_in: RoleUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    更新角色信息
    """
    role = crud_role.get(db=db, role_id=role_id)
    if not role:
        raise HTTPException(status_code=404, detail="角色不存在")
    
    # 系统角色不能修改
    if role.is_system:
        raise HTTPException(status_code=400, detail="系统角色不能修改")
    
    # 检查角色代码是否已存在（排除当前角色）
    if role_in.code and role_in.code != role.code:
        existing_role = crud_role.get_by_code(db=db, code=role_in.code)
        if existing_role:
            raise HTTPException(status_code=400, detail="角色代码已存在")
    
    # 检查角色名称是否已存在（排除当前角色）
    if role_in.name and role_in.name != role.name:
        existing_name = crud_role.get_by_name(db=db, name=role_in.name)
        if existing_name:
            raise HTTPException(status_code=400, detail="角色名称已存在")
    
    role = crud_role.update(db=db, db_obj=role, obj_in=role_in, updated_by=current_user.id)
    
    return ResponseModel(
        data=RoleResponse.model_validate(role),
        message="更新角色成功"
    )


@router.delete("/{role_id}", response_model=ResponseModel[bool])
def delete_role(
    role_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    删除角色
    """
    role = crud_role.get(db=db, role_id=role_id)
    if not role:
        raise HTTPException(status_code=404, detail="角色不存在")
    
    # 系统角色不能删除
    if role.is_system:
        raise HTTPException(status_code=400, detail="系统角色不能删除")
    
    # 检查是否有用户使用该角色
    users = crud_role.get_users_by_role(db=db, role_id=role_id)
    if users:
        raise HTTPException(status_code=400, detail=f"该角色正在被 {len(users)} 个用户使用，无法删除")
    
    success = crud_role.delete(db=db, role_id=role_id)
    if not success:
        raise HTTPException(status_code=400, detail="删除角色失败")
    
    return ResponseModel(
        data=True,
        message="删除角色成功"
    )


@router.get("/{role_id}/permissions", response_model=ResponseModel[RoleWithPermissions])
def get_role_permissions(
    role_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取角色的权限列表
    """
    role = crud_role.get_with_permissions(db=db, role_id=role_id)
    if not role:
        raise HTTPException(status_code=404, detail="角色不存在")
    
    return ResponseModel(
        data=RoleWithPermissions.model_validate(role),
        message="获取角色权限成功"
    )


@router.post("/{role_id}/permissions", response_model=ResponseModel[List[RolePermissionResponse]])
def assign_permissions_to_role(
    role_id: int,
    permission_data: RolePermissionBatchCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    为角色分配权限
    """
    role = crud_role.get(db=db, role_id=role_id)
    if not role:
        raise HTTPException(status_code=404, detail="角色不存在")
    
    # 系统角色不能修改权限
    if role.is_system:
        raise HTTPException(status_code=400, detail="系统角色不能修改权限")
    
    # 验证权限是否存在
    for permission_id in permission_data.permission_ids:
        permission = crud_permission.get(db=db, permission_id=permission_id)
        if not permission:
            raise HTTPException(status_code=400, detail=f"权限ID {permission_id} 不存在")
    
    role_permissions = crud_role_permission.assign_permissions_to_role(
        db=db, 
        role_id=role_id, 
        permission_ids=permission_data.permission_ids,
        created_by=current_user.id
    )
    
    return ResponseModel(
        data=[RolePermissionResponse.model_validate(rp) for rp in role_permissions],
        message="分配权限成功"
    )


@router.delete("/{role_id}/permissions/{permission_id}", response_model=ResponseModel[bool])
def remove_permission_from_role(
    role_id: int,
    permission_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    移除角色的权限
    """
    role = crud_role.get(db=db, role_id=role_id)
    if not role:
        raise HTTPException(status_code=404, detail="角色不存在")
    
    # 系统角色不能修改权限
    if role.is_system:
        raise HTTPException(status_code=400, detail="系统角色不能修改权限")
    
    success = crud_role_permission.delete(db=db, role_id=role_id, permission_id=permission_id)
    if not success:
        raise HTTPException(status_code=400, detail="移除权限失败")
    
    return ResponseModel(
        data=True,
        message="移除权限成功"
    )


@router.get("/{role_id}/users", response_model=ResponseModel[List[UserWithRoles]])
def get_role_users(
    role_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取拥有指定角色的用户列表
    """
    role = crud_role.get(db=db, role_id=role_id)
    if not role:
        raise HTTPException(status_code=404, detail="角色不存在")
    
    users = crud_role.get_users_by_role(db=db, role_id=role_id)
    
    return ResponseModel(
        data=[UserWithRoles.model_validate(user) for user in users],
        message="获取角色用户成功"
    )


@router.get("/users/{user_id}/roles", response_model=ResponseModel[List[RoleResponse]])
def get_user_roles(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取指定用户的角色列表（函数级注释）

    - 基于用户ID查询当前有效角色
    - 返回 `RoleResponse` 数组，便于前端进行差异同步
    """
    roles = crud_user_role.get_roles_by_user(db=db, user_id=user_id)
    return ResponseModel(
        data=[RoleResponse.model_validate(r) for r in roles],
        message="获取用户角色成功"
    )


@router.post("/assign-user", response_model=ResponseModel[UserRoleResponse])
def assign_role_to_user(
    user_role_in: UserRoleCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    为用户分配角色
    """
    # 验证用户是否存在
    from app.crud.user import crud_user
    user = crud_user.get(db=db, id=user_role_in.user_id)
    if not user:
        raise HTTPException(status_code=400, detail="用户不存在")
    
    # 验证角色是否存在
    role = crud_role.get(db=db, role_id=user_role_in.role_id)
    if not role:
        raise HTTPException(status_code=400, detail="角色不存在")
    
    user_role = crud_user_role.create(db=db, obj_in=user_role_in, created_by=current_user.id)
    
    return ResponseModel(
        data=UserRoleResponse.model_validate(user_role),
        message="分配角色成功"
    )


@router.delete("/remove-user", response_model=ResponseModel[bool])
def remove_role_from_user(
    user_id: int,
    role_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    移除用户的角色
    """
    success = crud_user_role.delete(db=db, user_id=user_id, role_id=role_id)
    if not success:
        raise HTTPException(status_code=400, detail="移除角色失败")
    
    return ResponseModel(
        data=True,
        message="移除角色成功"
    )


@router.delete("/remove-user/{user_id}/{role_id}", response_model=ResponseModel[bool])
def remove_role_from_user_path(
    user_id: int,
    role_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """移除用户的角色（函数级注释）

    - 使用路径参数明确传递 `user_id` 与 `role_id`
    - 避免与 `/{role_id}` 动态路由匹配冲突，确保稳定删除
    """
    success = crud_user_role.delete(db=db, user_id=user_id, role_id=role_id)
    if not success:
        raise HTTPException(status_code=400, detail="移除角色失败")
    return ResponseModel(data=True, message="移除角色成功")