#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RBAC 权限与角色种子脚本：对齐前端 PERMISSIONS/ROLES 常量

运行：python legacy_scripts/seed_permissions_roles.py
说明：
- 批量创建缺失的权限（使用冒号风格，如 user:read），与前端保持一致
- 创建/确保 developer、operator 角色存在
- 将新权限分配到各角色，不会删除已有系统权限的分配
- 将管理员用户绑定到 admin 角色，以便权限计算
"""

import os
import sys
from typing import List

# 将项目 backend 目录加入路径，方便脚本直接运行
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from sqlalchemy.orm import Session

# 预加载所有模型，确保关系解析不会失败（如 User -> ResourcePackage）
import app.models  # noqa: F401

from app.core.database import SessionLocal
from app.crud.permission import crud_permission
from app.crud.role import crud_role, crud_role_permission, crud_user_role
from app.crud.user import crud_user
from app.schemas.permission import PermissionCreate
from app.schemas.role import RoleCreate, RolePermissionCreate, UserRoleCreate


def ensure_admin_user(db: Session):
    """确保管理员用户存在，如不存在则创建"""
    admin = crud_user.get_by_username(db, "admin")
    if not admin:
        admin = crud_user.create(
            db,
            username="admin",
            email="admin@acwl.ai",
            password="admin123",
            role="admin",
            is_admin=True,
            is_active=True,
        )
        print("✅ 已创建管理员用户 admin / admin123")
    else:
        print("ℹ️ 管理员用户已存在")
    return admin


def ensure_roles(db: Session, admin_id: int):
    """创建/确保基础与扩展角色存在，并返回所有相关角色

    基础角色：super_admin、admin、user、guest
    扩展角色：developer、operator
    - 若 super_admin 不存在则创建，并标记为系统角色
    - 其余角色若不存在则创建为普通角色
    """
    roles = {}

    # 基础角色定义（含是否系统角色）
    base_role_defs = [
        ("super_admin", "超级管理员", True, "拥有所有系统权限的最高角色"),
        ("admin", "管理员", False, "系统管理员，拥有大部分管理权限"),
        ("user", "用户", False, "普通用户角色"),
        ("guest", "访客", False, "访客角色，权限最少")
    ]

    # 加载或创建基础角色
    for code, name, is_system, desc in base_role_defs:
        r = crud_role.get_by_code(db, code)
        if not r:
            r = crud_role.create(
                db,
                RoleCreate(name=name, code=code, description=desc, status=True, is_system=is_system),
                created_by=admin_id,
            )
            print(f"✅ 已创建基础角色: {name} ({code})，系统角色={is_system}")
        roles[code] = r

    # 创建新增角色
    for code, name, desc in [
        ("developer", "开发者", "开发者角色，具备测试与部署权限"),
        ("operator", "运维人员", "运维角色，具备系统监控与部署权限"),
    ]:
        r = crud_role.get_by_code(db, code)
        if not r:
            r = crud_role.create(
                db,
                RoleCreate(name=name, code=code, description=desc, status=True),
                created_by=admin_id,
            )
            print(f"✅ 已创建角色: {name} ({code})")
        roles[code] = r

    return roles


def build_permissions() -> List[PermissionCreate]:
    """构建需要创建的权限列表（冒号风格，与前端一致）"""
    perms: List[PermissionCreate] = []

    def add(name: str, code: str, module: str, resource: str, action: str, sort: int):
        perms.append(
            PermissionCreate(
                name=name,
                code=code,
                description=name,
                module=module,
                resource=resource,
                action=action,
                status=True,
                sort_order=sort,
            )
        )

    # 用户管理
    add("用户管理-查看", "user:read", "用户管理", "user", "read", 100)
    add("用户管理-创建", "user:create", "用户管理", "user", "create", 101)
    add("用户管理-编辑", "user:update", "用户管理", "user", "update", 102)
    add("用户管理-删除", "user:delete", "用户管理", "user", "delete", 103)

    # 角色管理
    add("角色管理-查看", "role:read", "角色管理", "role", "read", 110)
    add("角色管理-创建", "role:create", "角色管理", "role", "create", 111)
    add("角色管理-编辑", "role:update", "角色管理", "role", "update", 112)
    add("角色管理-删除", "role:delete", "角色管理", "role", "delete", 113)

    # 权限管理
    add("权限管理-查看", "permission:read", "权限管理", "permission", "read", 120)
    add("权限管理-创建", "permission:create", "权限管理", "permission", "create", 121)
    add("权限管理-编辑", "permission:update", "权限管理", "permission", "update", 122)
    add("权限管理-删除", "permission:delete", "权限管理", "permission", "delete", 123)

    # 模型管理
    add("模型管理-查看", "model:read", "模型管理", "model", "read", 200)
    add("模型管理-创建", "model:create", "模型管理", "model", "create", 201)
    add("模型管理-编辑", "model:update", "模型管理", "model", "update", 202)
    add("模型管理-删除", "model:delete", "模型管理", "model", "delete", 203)
    add("模型管理-部署", "model:deploy", "模型管理", "model", "deploy", 204)

    # 数据集管理
    add("数据集管理-查看", "dataset:read", "数据集管理", "dataset", "read", 300)
    add("数据集管理-创建", "dataset:create", "数据集管理", "dataset", "create", 301)
    add("数据集管理-编辑", "dataset:update", "数据集管理", "dataset", "update", 302)
    add("数据集管理-删除", "dataset:delete", "数据集管理", "dataset", "delete", 303)

    # 项目管理
    add("项目管理-查看", "project:read", "项目管理", "project", "read", 500)
    add("项目管理-创建", "project:create", "项目管理", "project", "create", 501)
    add("项目管理-编辑", "project:update", "项目管理", "project", "update", 502)
    add("项目管理-删除", "project:delete", "项目管理", "project", "delete", 503)

    # 系统管理
    add("系统管理-查看", "system:read", "系统管理", "system", "read", 600)
    add("系统管理-更新", "system:update", "系统管理", "system", "update", 601)
    add("系统管理-监控", "system:monitor", "系统管理", "system", "monitor", 602)

    # 指令集管理
    add("指令集管理-查看", "instruction_set:read", "指令集管理", "instruction_set", "read", 700)
    add("指令集管理-创建", "instruction_set:create", "指令集管理", "instruction_set", "create", 701)
    add("指令集管理-编辑", "instruction_set:update", "指令集管理", "instruction_set", "update", 702)
    add("指令集管理-删除", "instruction_set:delete", "指令集管理", "instruction_set", "delete", 703)
    add("指令集管理-测试", "instruction_set:test", "指令集管理", "instruction_set", "test", 704)

    return perms


def mark_system_permissions(db: Session, codes: List[str]) -> int:
    """将创建的权限标记为系统权限，避免被误删"""
    from app.models.permission import Permission  # 延迟导入，避免循环
    updated = 0
    for code in codes:
        p = crud_permission.get_by_code(db, code)
        if p and not p.is_system:
            p.is_system = True
            updated += 1
    if updated:
        db.commit()
    return updated


def assign_permissions(db: Session, role_code: str, perm_codes: List[str], created_by: int) -> int:
    """为指定角色分配权限（逐条创建，避免清空原有分配）"""
    role = crud_role.get_by_code(db, role_code)
    if not role:
        print(f"⚠️ 未找到角色 {role_code}，跳过分配")
        return 0
    assigned = 0
    for code in perm_codes:
        perm = crud_permission.get_by_code(db, code)
        if not perm:
            print(f"⚠️ 未找到权限 {code}，跳过")
            continue
        crud_role_permission.create(
            db,
            RolePermissionCreate(role_id=role.id, permission_id=perm.id),
            created_by,
        )
        assigned += 1
    return assigned


def ensure_user_role(db: Session, user_id: int, role_code: str, created_by: int):
    """确保用户与角色的关联存在"""
    role = crud_role.get_by_code(db, role_code)
    if not role:
        print(f"⚠️ 未找到角色 {role_code}，无法关联用户")
        return
    crud_user_role.create(db, UserRoleCreate(user_id=user_id, role_id=role.id), created_by)


def assign_all_system_permissions_to_super_admin(db: Session, created_by: int) -> int:
    """为 super_admin 绑定所有系统且启用的权限

    说明：
    - 仅追加绑定，不会删除已存在的绑定记录
    - 通过直接使用 CRUD 层绕过 API 端点中的系统角色限制
    - 避免清空已有分配，逐条 create 以保持幂等
    返回：新增绑定数量
    """
    from app.models.permission import Permission

    super_admin_role = crud_role.get_by_code(db, "super_admin")
    if not super_admin_role:
        print("⚠️ 未找到角色 super_admin，跳过系统权限绑定")
        return 0

    # 查询所有启用的系统权限
    system_perms = db.query(Permission).filter(
        Permission.status == True,
        Permission.is_system == True,
    ).all()

    assigned = 0
    for perm in system_perms:
        crud_role_permission.create(
            db,
            RolePermissionCreate(role_id=super_admin_role.id, permission_id=perm.id),
            created_by,
        )
        assigned += 1

    if assigned:
        print(f"✅ super_admin 绑定系统权限数量: +{assigned}")
    else:
        print("ℹ️ super_admin 无需新增系统权限绑定")
    return assigned


def main():
    db = SessionLocal()
    try:
        print("=== RBAC 种子脚本：对齐前端 PERMISSIONS / ROLES ===")

        # 管理员用户
        admin = ensure_admin_user(db)

        # 角色
        roles = ensure_roles(db, admin.id)

        # 批量创建权限（已存在则跳过）
        perms_to_create = build_permissions()
        created_perms = crud_permission.batch_create(db, perms_to_create, created_by=admin.id)
        print(f"✅ 权限创建/跳过数量: {len(created_perms)}")

        # 标记为系统权限，防止误删
        updated_count = mark_system_permissions(db, [p.code for p in perms_to_create])
        if updated_count:
            print(f"✅ 已将 {updated_count} 个新权限标记为系统权限")

        # 将管理员用户绑定到 admin 角色（用于权限计算）
        ensure_user_role(db, admin.id, "admin", admin.id)
        print("✅ 管理员用户已绑定到 admin 角色")

        # 将管理员用户绑定到 super_admin 角色（用于全局权限放行）
        ensure_user_role(db, admin.id, "super_admin", admin.id)
        print("✅ 管理员用户已绑定到 super_admin 角色")

        # 为各角色分配权限
        admin_codes = [p.code for p in perms_to_create]  # 管理员拥有全部新权限
        user_codes = [
            "model:read",
            "model:deploy",
            "instruction_set:read",
            "project:read",
        ]
        guest_codes = ["project:read"]
        developer_codes = [
            "model:read",
            "model:deploy",
            "instruction_set:read",
            "instruction_set:test",
            "project:read",
        ]
        operator_codes = [
            "system:monitor",
            "model:deploy",
        ]

        assigned_admin = assign_permissions(db, "admin", admin_codes, admin.id)
        assigned_user = assign_permissions(db, "user", user_codes, admin.id)
        assigned_guest = assign_permissions(db, "guest", guest_codes, admin.id)
        assigned_dev = assign_permissions(db, "developer", developer_codes, admin.id)
        assigned_ops = assign_permissions(db, "operator", operator_codes, admin.id)

        print("=== 分配结果 ===")
        print(f"admin: +{assigned_admin} 个权限（不影响原有系统权限）")
        # 为 super_admin 角色追加所有系统权限绑定（不影响原绑定）
        assigned_sa = assign_all_system_permissions_to_super_admin(db, admin.id)
        print(f"super_admin: +{assigned_sa} 个系统权限绑定")
        print(f"user: +{assigned_user} 个权限")
        print(f"guest: +{assigned_guest} 个权限")
        print(f"developer: +{assigned_dev} 个权限")
        print(f"operator: +{assigned_ops} 个权限")

        print("=== 完成 ===")
    except Exception as e:
        print(f"❌ 种子脚本执行失败: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()