#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
API依赖模块
"""

from .project import (
    get_project_by_id,
    check_project_access,
    check_project_read_access,
    check_project_write_access,
    check_project_manage_access,
    check_project_member_manage_access,
    check_project_datasource_manage_access,
    get_user_project_role
)

from .common import (
    get_db,
    get_current_user,
    get_current_user_sync,
    get_current_active_user,
    get_current_admin_user,
    check_permission,
    check_role
)

__all__ = [
    # 项目相关依赖
    "get_project_by_id",
    "check_project_access",
    "check_project_read_access",
    "check_project_write_access",
    "check_project_manage_access",
    "check_project_member_manage_access",
    "check_project_datasource_manage_access",
    "get_user_project_role",
    
    # 通用依赖
    "get_db",
    "get_current_user",
    "get_current_user_sync",
    "get_current_active_user",
    "get_current_admin_user",
    "check_permission",
    "check_role"
]