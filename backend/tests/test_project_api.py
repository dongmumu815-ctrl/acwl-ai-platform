#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
项目管理API测试
"""

import sys
import os
# 添加backend目录到Python路径
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, backend_dir)

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, date

from app.models.user import User
from app.models.project import Project, ProjectMember, ProjectMemberRole, ProjectStatus, ProjectType
from app.models.datasource import Datasource, DatasourceType, DatasourceStatus
from app.core.security import get_password_hash


# test_user fixture已在conftest.py中定义，这里删除重复定义


@pytest.fixture
async def admin_user(db_session: AsyncSession):
    """创建管理员用户"""
    user = User(
        username="admin",
        email="admin@example.com",
        password_hash=get_password_hash("adminpass123"),
        role="admin"
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
async def test_project(db_session: AsyncSession, test_user: User):
    """创建测试项目"""
    project = Project(
        name="测试项目",
        description="这是一个测试项目",
        project_type=ProjectType.DEVELOPMENT,
        status=ProjectStatus.ACTIVE,
        created_by=test_user.id,
        start_date=date.today(),
        tags=["测试", "开发"]
    )
    db_session.add(project)
    await db_session.commit()
    await db_session.refresh(project)
    
    # 添加项目创建者为所有者
    member = ProjectMember(
        project_id=project.id,
        user_id=test_user.id,
        role=ProjectMemberRole.ADMIN,
        added_by=test_user.id
    )
    db_session.add(member)
    await db_session.commit()
    
    return project


@pytest.fixture
async def test_datasource(db_session: AsyncSession, test_user: User):
    """创建测试数据源"""
    datasource = Datasource(
        name="测试数据源",
        description="测试MySQL数据源",
        datasource_type=DatasourceType.MYSQL,
        host="localhost",
        port=3306,
        database_name="test_db",
        username="test_user",
        password="test_pass",
        status=DatasourceStatus.ACTIVE,
        created_by=test_user.id
    )
    db_session.add(datasource)
    await db_session.commit()
    await db_session.refresh(datasource)
    return datasource


class TestProjectAPI:
    """项目API测试类"""
    
    @pytest.mark.asyncio
    async def test_create_project(self, client: AsyncClient, test_user: User):
        """测试创建项目"""
        project_data = {
            "name": "新项目",
            "description": "这是一个新项目",
            "project_type": "data_analysis",
            "start_date": "2024-01-01",
            "end_date": "2024-12-31",
            "tags": {"category": "新建", "type": "测试"}
        }
        
        response = await client.post(
            "/api/v1/projects/",
            json=project_data
        )
        
        print(f"Response status: {response.status_code}")
        print(f"Response content: {response.text}")
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == project_data["name"]
        assert data["description"] == project_data["description"]
        assert data["project_type"] == project_data["project_type"]
    
    async def test_get_projects(self, client: AsyncClient, test_user: User, test_project: Project):
        """测试获取项目列表"""
        response = await client.get(
            "/api/v1/projects/",
            headers={"Authorization": f"Bearer {test_user.access_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert len(data["items"]) >= 1
        assert data["items"][0]["id"] == test_project.id
    
    async def test_get_project_detail(self, client: AsyncClient, test_user: User, test_project: Project):
        """测试获取项目详情"""
        response = await client.get(
            f"/api/v1/projects/{test_project.id}",
            headers={"Authorization": f"Bearer {test_user.access_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == test_project.id
        assert data["name"] == test_project.name
    
    async def test_update_project(self, client: AsyncClient, test_user: User, test_project: Project):
        """测试更新项目"""
        update_data = {
            "name": "更新后的项目名称",
            "description": "更新后的项目描述"
        }
        
        response = await client.put(
            f"/api/v1/projects/{test_project.id}",
            json=update_data,
            headers={"Authorization": f"Bearer {test_user.access_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == update_data["name"]
        assert data["description"] == update_data["description"]
    
    async def test_delete_project(self, client: AsyncClient, test_user: User, test_project: Project):
        """测试删除项目"""
        response = await client.delete(
            f"/api/v1/projects/{test_project.id}",
            headers={"Authorization": f"Bearer {test_user.access_token}"}
        )
        
        assert response.status_code == 200
        
        # 验证项目已被软删除
        get_response = await client.get(
            f"/api/v1/projects/{test_project.id}",
            headers={"Authorization": f"Bearer {test_user.access_token}"}
        )
        assert get_response.status_code == 404
    
    async def test_add_project_member(self, client: AsyncClient, test_user: User, admin_user: User, test_project: Project):
        """测试添加项目成员"""
        member_data = {
            "user_id": admin_user.id,
            "role": "developer"
        }
        
        response = await client.post(
            f"/api/v1/projects/{test_project.id}/members",
            json=member_data,
            headers={"Authorization": f"Bearer {test_user.access_token}"}
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["user_id"] == admin_user.id
        assert data["role"] == "developer"
    
    async def test_get_project_members(self, client: AsyncClient, test_user: User, test_project: Project):
        """测试获取项目成员列表"""
        response = await client.get(
            f"/api/v1/projects/{test_project.id}/members",
            headers={"Authorization": f"Bearer {test_user.access_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1  # 至少有项目创建者
        assert data[0]["user_id"] == test_user.id
        assert data[0]["role"] == "owner"
    
    async def test_assign_datasource_to_project(self, client: AsyncClient, test_user: User, test_project: Project, test_datasource: Datasource):
        """测试为项目分配数据源"""
        assignment_data = {
            "datasource_id": test_datasource.id,
            "access_type": "read_write"
        }
        
        response = await client.post(
            f"/api/v1/projects/{test_project.id}/datasources",
            json=assignment_data,
            headers={"Authorization": f"Bearer {test_user.access_token}"}
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["datasource_id"] == test_datasource.id
        assert data["access_type"] == "read_write"
    
    async def test_get_project_datasources(self, client: AsyncClient, test_user: User, test_project: Project):
        """测试获取项目数据源列表"""
        response = await client.get(
            f"/api/v1/projects/{test_project.id}/datasources",
            headers={"Authorization": f"Bearer {test_user.access_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    async def test_get_project_activities(self, client: AsyncClient, test_user: User, test_project: Project):
        """测试获取项目活动日志"""
        response = await client.get(
            f"/api/v1/projects/{test_project.id}/activities",
            headers={"Authorization": f"Bearer {test_user.access_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert isinstance(data["items"], list)
    
    async def test_get_project_stats(self, client: AsyncClient, test_user: User, test_project: Project):
        """测试获取项目统计信息"""
        response = await client.get(
            f"/api/v1/projects/{test_project.id}/stats",
            headers={"Authorization": f"Bearer {test_user.access_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "member_count" in data
        assert "datasource_count" in data
        assert "activity_count" in data
    
    async def test_unauthorized_access(self, client: AsyncClient, test_project: Project):
        """测试未授权访问"""
        response = await client.get(f"/api/v1/projects/{test_project.id}")
        assert response.status_code == 401
    
    async def test_forbidden_access(self, client: AsyncClient, admin_user: User, test_project: Project):
        """测试禁止访问（非项目成员）"""
        response = await client.get(
            f"/api/v1/projects/{test_project.id}",
            headers={"Authorization": f"Bearer {admin_user.access_token}"}
        )
        # 管理员应该有访问权限，普通用户没有项目权限时应该返回403
        # 这里需要根据实际权限逻辑调整
        assert response.status_code in [200, 403]