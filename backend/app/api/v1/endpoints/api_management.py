#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
API管理端点

提供平台管理、API管理、批次管理等功能的REST API接口
使用多数据库功能连接到 acwl_api_system 数据库
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, Form, Body
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_, text
from sqlalchemy.orm import selectinload, joinedload
from datetime import datetime, timedelta
import uuid
import json

from app.core.database import get_db
from app.core.response import success_response
from app.api.v1.endpoints.auth import get_current_active_user
from app.models.user import User
from app.core.security import get_password_hash
from app.schemas.common import PaginatedResponse
from app.schemas.api import CustomApiCopy, CustomApiResponse, ApiFieldUpdate, ApiFieldCreate, CustomApiUpdate
from app.core.multi_db_manager import get_db_session
from app.models.api_management import Customer, CustomApi, ApiField, DataBatch, ApiUsageLog, DataUpload
from app.models.resource_type import DataResourceType
from app.core.config import settings
from app.services.db_service import LinkTaskService, SysDictService
import redis

router = APIRouter()

# Redis客户端初始化
try:
    redis_client = redis.Redis(
        host=settings.REDIS_HOST,
        port=settings.REDIS_PORT,
        password=settings.REDIS_PASSWORD,
        db=settings.REDIS_DB,
        decode_responses=True
    )
except Exception as e:
    print(f"Redis连接失败: {e}")
    redis_client = None

def invalidate_api_fields_cache(api_id: int):
    """
    清除API字段相关的Redis缓存
    
    Args:
        api_id: API ID
    """
    if not redis_client:
        return
    
    try:
        # 清除有序和无序的缓存键
        cache_keys = [
            f"api_fields:{api_id}:True",   # 有序缓存
            f"api_fields:{api_id}:False"   # 无序缓存
        ]
        
        for key in cache_keys:
            redis_client.delete(key)
        
        print(f"已清除API {api_id} 的字段缓存")
    except Exception as e:
        print(f"清除缓存失败: {e}")

# Mock数据已删除，现在使用真实的数据库操作

# ==================== 平台管理 ====================

@router.get("/link-types", summary="获取关联任务类型")
async def get_link_types(
    current_user: User = Depends(get_current_active_user)
):
    """获取关联任务类型列表"""
    try:
        service = LinkTaskService()
        result = service.get_link_menu_types()
        
        if not result['success']:
            raise HTTPException(status_code=500, detail=result.get('error', '获取任务类型失败'))
            
        return success_response(data=result['data'])
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/dict-data", summary="获取系统字典数据")
async def get_dict_data(
    dict_type: str,
    current_user: User = Depends(get_current_active_user)
):
    try:
        service = SysDictService()
        result = service.get_dict_by_type(dict_type)
        if not result['success']:
            raise HTTPException(status_code=500, detail=result.get('error', '获取字典数据失败'))
        return success_response(data=result['data'])
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/customers", summary="获取客户列表")
async def get_customers(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=1000, description="每页数量"),
    search: Optional[str] = Query(None, description="搜索关键词"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """获取客户列表 - 从 acwl_api_system 数据库获取真实数据"""
    
    try:
        # 使用多数据库功能连接到 api_system 数据库
        async for api_db in get_db_session(db_name="api_system"):
            print(f"🔍 [DEBUG] ===== 客户列表查询开始 =====")
            print(f"🔍 [DEBUG] 目标数据库: api_system")
            print(f"🔍 [DEBUG] 数据库会话: {api_db}")
            print(f"🔍 [DEBUG] 数据库引擎URL: {api_db.bind.url}")
            print(f"🔍 [DEBUG] 查询表: {Customer.__tablename__}")
            print(f"🔍 [DEBUG] 搜索条件: {search}")
            print(f"🔍 [DEBUG] 分页参数: page={page}, page_size={page_size}")
 
            # 构建查询
            query = select(Customer)
            
            # 搜索条件
            if search:
                search_pattern = f"%{search}%"
                query = query.where(
                    or_(
                        Customer.name.like(search_pattern),
                        Customer.email.like(search_pattern),
                        Customer.company.like(search_pattern)
                    )
                )
            
            # 获取总数
            count_query = select(func.count(Customer.id))
            if search:
                count_query = count_query.where(
                    or_(
                        Customer.name.like(search_pattern),
                        Customer.email.like(search_pattern),
                        Customer.company.like(search_pattern)
                    )
                )
            
            total_result = await api_db.execute(count_query)
            total = total_result.scalar()
            print(f"🔍 [DEBUG] 总记录数查询结果: {total}")
            
            # 分页查询
            query = query.offset((page - 1) * page_size).limit(page_size)
            query = query.order_by(Customer.created_at.desc())
            print(f"🔍 [DEBUG] 最终SQL查询: {query}")
            
            result = await api_db.execute(query)
            customers = result.scalars().all()
            print(f"🔍 [DEBUG] 查询返回记录数: {len(customers)}")
            print(f"🔍 [DEBUG] 客户记录详情:")
            for i, customer in enumerate(customers):
                print(f"🔍 [DEBUG]   [{i+1}] ID:{customer.id}, 名称:{customer.name}, 邮箱:{customer.email}")
            
            # 转换为字典格式
            items = []
            for customer in customers:
                item = {
                    "id": customer.id,
                    "name": customer.name,
                    "email": customer.email,
                    "phone": customer.phone,
                    "company": customer.company,
                    "app_id": customer.app_id,
                    "rate_limit": customer.rate_limit,
                    "max_apis": customer.max_apis,
                    "total_api_calls": customer.total_api_calls,
                    "last_api_call_at": customer.last_api_call_at.isoformat() if customer.last_api_call_at else None,
                    "is_active": customer.status == 1,  # 将status转换为is_active
                    "created_at": customer.created_at.isoformat(),
                    "updated_at": customer.updated_at.isoformat()
                }
                items.append(item)
            
            return success_response({
                "items": items,
                "total": total,
                "page": page,
                "page_size": page_size,
                "total_pages": (total + page_size - 1) // page_size
            })
            break  # 只需要执行一次
            
    except Exception as e:
        print(f"数据库连接失败: {e}")
        raise HTTPException(status_code=500, detail="数据库连接失败")

@router.get("/customers/{customer_id}", summary="获取客户详情")
async def get_customer(
    customer_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """获取客户详情"""
    
    try:
        async for api_db in get_db_session(db_name="api_system"):
            query = select(Customer).where(Customer.id == customer_id)
            result = await api_db.execute(query)
            customer = result.scalar_one_or_none()
            
            if not customer:
                raise HTTPException(status_code=404, detail="客户不存在")
            
            return success_response({
                "id": customer.id,
                "name": customer.name,
                "email": customer.email,
                "phone": customer.phone,
                "company": customer.company,
                "app_id": customer.app_id,
                "rate_limit": customer.rate_limit,
                "max_apis": customer.max_apis,
                "total_api_calls": customer.total_api_calls,
                "last_api_call_at": customer.last_api_call_at.isoformat() if customer.last_api_call_at else None,
                "is_active": customer.status == 1,
                "created_at": customer.created_at.isoformat(),
                "updated_at": customer.updated_at.isoformat()
            })
            break
            
    except HTTPException:
        raise
    except Exception as e:
        print(f"数据库连接失败: {e}")
        raise HTTPException(status_code=500, detail="数据库连接失败")

@router.post("/customers", summary="创建客户")
async def create_customer(
    name: str = Form(...),
    email: str = Form(...),
    phone: Optional[str] = Form(None),
    company: Optional[str] = Form(None),
    rate_limit: int = Form(100),
    max_apis: int = Form(10),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """创建客户"""
    
    try:
        async for api_db in get_db_session(db_name="api_system"):
            # 检查邮箱是否已存在
            existing_query = select(Customer).where(Customer.email == email)
            existing_result = await api_db.execute(existing_query)
            if existing_result.scalar_one_or_none():
                raise HTTPException(status_code=400, detail="邮箱已存在")
            
            # 创建新客户
            new_customer = Customer(
                name=name,
                email=email,
                phone=phone,
                company=company,
                app_id=str(uuid.uuid4())[:8],
                app_secret=str(uuid.uuid4()),
                rate_limit=rate_limit,
                max_apis=max_apis,
                status=1,  # 活跃状态
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            
            api_db.add(new_customer)
            await api_db.commit()
            await api_db.refresh(new_customer)
            
            return success_response({
                "id": new_customer.id,
                "name": new_customer.name,
                "email": new_customer.email,
                "phone": new_customer.phone,
                "company": new_customer.company,
                "app_id": new_customer.app_id,
                "rate_limit": new_customer.rate_limit,
                "max_apis": new_customer.max_apis,
                "is_active": new_customer.status == 1,
                "created_at": new_customer.created_at.isoformat(),
                "updated_at": new_customer.updated_at.isoformat()
            })
            break
            
    except HTTPException:
        raise
    except Exception as e:
        print(f"创建客户失败: {e}")
        raise HTTPException(status_code=500, detail="创建客户失败")

@router.put("/customers/{customer_id}", summary="更新客户")
async def update_customer(
    customer_id: int,
    name: Optional[str] = Form(None),
    email: Optional[str] = Form(None),
    phone: Optional[str] = Form(None),
    company: Optional[str] = Form(None),
    rate_limit: Optional[int] = Form(None),
    max_apis: Optional[int] = Form(None),
    is_active: Optional[bool] = Form(None),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """更新客户"""
    
    try:
        async for api_db in get_db_session(db_name="api_system"):
            # 查找客户
            query = select(Customer).where(Customer.id == customer_id)
            result = await api_db.execute(query)
            customer = result.scalar_one_or_none()
            
            if not customer:
                raise HTTPException(status_code=404, detail="客户不存在")
            
            # 更新字段
            if name is not None:
                customer.name = name
            if email is not None:
                # 检查邮箱是否已被其他客户使用
                existing_query = select(Customer).where(
                    and_(Customer.email == email, Customer.id != customer_id)
                )
                existing_result = await api_db.execute(existing_query)
                if existing_result.scalar_one_or_none():
                    raise HTTPException(status_code=400, detail="邮箱已被其他客户使用")
                customer.email = email
            if phone is not None:
                customer.phone = phone
            if company is not None:
                customer.company = company
            if rate_limit is not None:
                customer.rate_limit = rate_limit
            if max_apis is not None:
                customer.max_apis = max_apis
            if is_active is not None:
                customer.status = 1 if is_active else 0
            
            customer.updated_at = datetime.now()
            
            await api_db.commit()
            await api_db.refresh(customer)
            
            return success_response({
                "id": customer.id,
                "name": customer.name,
                "email": customer.email,
                "phone": customer.phone,
                "company": customer.company,
                "app_id": customer.app_id,
                "rate_limit": customer.rate_limit,
                "max_apis": customer.max_apis,
                "is_active": customer.status == 1,
                "created_at": customer.created_at.isoformat(),
                "updated_at": customer.updated_at.isoformat()
            })
            break
            
    except HTTPException:
        raise
    except Exception as e:
        print(f"更新客户失败: {e}")
        raise HTTPException(status_code=500, detail="更新客户失败")

@router.delete("/customers/{customer_id}", summary="删除客户")
async def delete_customer(
    customer_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """删除客户"""
    
    try:
        async for api_db in get_db_session(db_name="api_system"):
            # 查找客户
            query = select(Customer).where(Customer.id == customer_id)
            result = await api_db.execute(query)
            customer = result.scalar_one_or_none()
            
            if not customer:
                raise HTTPException(status_code=404, detail="客户不存在")
            
            # 删除客户
            await api_db.delete(customer)
            await api_db.commit()
            
            return success_response({"message": "客户删除成功"})
            break
            
    except HTTPException:
        raise
    except Exception as e:
        print(f"删除客户失败: {e}")
        raise HTTPException(status_code=500, detail="删除客户失败")

@router.post("/customers/{customer_id}/reset-secret", summary="重置客户密钥")
async def reset_customer_secret(
    customer_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """重置客户密钥"""
    
    try:
        async for api_db in get_db_session(db_name="api_system"):
            # 查找客户
            query = select(Customer).where(Customer.id == customer_id)
            result = await api_db.execute(query)
            customer = result.scalar_one_or_none()
            
            if not customer:
                raise HTTPException(status_code=404, detail="客户不存在")
            
            # 生成新密钥
            new_secret = str(uuid.uuid4())
            customer.app_secret = new_secret
            customer.updated_at = datetime.now()
            
            await api_db.commit()
            
            return success_response({"app_secret": new_secret})
            break
            
    except HTTPException:
        raise
    except Exception as e:
        print(f"重置客户密钥失败: {e}")
        raise HTTPException(status_code=500, detail="重置客户密钥失败")

@router.post("/customers/{customer_id}/reset-password", summary="重置客户密码")
async def reset_customer_password(
    customer_id: int,
    password: Optional[str] = Body(None, embed=True),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """重置客户密码

    - 如果提供了 `password`，则使用该明文生成哈希并保存。
    - 如果未提供，则服务端生成一个随机强密码，保存哈希并返回一次性明文。
    """
    import secrets, string

    def generate_strong_password(length: int = 16) -> str:
        alphabet = string.ascii_letters + string.digits + "!@#$%^&*()-_=+[]{}"  # 包含大小写、数字和特殊字符
        # 确保至少包含各类字符
        password_chars = [
            secrets.choice(string.ascii_lowercase),
            secrets.choice(string.ascii_uppercase),
            secrets.choice(string.digits),
            secrets.choice("!@#$%^&*()-_=+[]{}")
        ]
        password_chars += [secrets.choice(alphabet) for _ in range(length - 4)]
        secrets.SystemRandom().shuffle(password_chars)
        return "".join(password_chars)

    plain_password = password or generate_strong_password()

    # 使用真实数据库会话持久化保存密码哈希
    async for api_db in get_db_session(db_name="api_system"):
        db_customer = await api_db.get(Customer, customer_id)
        if not db_customer:
            raise HTTPException(status_code=404, detail="客户不存在")

        # 仅保存哈希，不保存明文
        try:
            db_customer.password_hash = get_password_hash(plain_password)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
            
        db_customer.updated_at = datetime.utcnow()

        await api_db.commit()
        break

    return success_response({"password": plain_password})

# ==================== API管理 ====================

@router.get("/apis", summary="获取API列表")
async def get_apis(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    search: Optional[str] = Query(None, description="搜索关键词"),
    customer_id: Optional[int] = Query(None, description="客户ID"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """获取API列表 - 优先从 acwl_api_system 数据库读取真实数据，失败时回退到模拟数据"""

    try:
        # 使用多数据库功能连接到 api_system 数据库
        async for api_db in get_db_session(db_name="api_system"):
            print(f"🔍 [DEBUG] ===== API列表查询开始 =====")
            print(f"🔍 [DEBUG] 目标数据库: api_system")
            print(f"🔍 [DEBUG] 数据库会话: {api_db}")
            print(f"🔍 [DEBUG] 查询表: {CustomApi.__tablename__}")
            print(f"🔍 [DEBUG] 搜索条件: {search}, 客户ID: {customer_id}")
            print(f"🔍 [DEBUG] 分页参数: page={page}, page_size={page_size}")

            # 构建基本查询，预加载平台信息
            query = select(CustomApi).options(selectinload(CustomApi.customer))

            # 搜索条件
            if search:
                search_pattern = f"%{search}%"
                query = query.where(
                    or_(
                        CustomApi.api_name.like(search_pattern),
                        CustomApi.api_code.like(search_pattern)
                    )
                )

            # 客户过滤
            if customer_id:
                query = query.where(CustomApi.customer_id == customer_id)

            # 总数查询
            count_query = select(func.count(CustomApi.id))
            if search:
                search_pattern = f"%{search}%"
                count_query = count_query.where(
                    or_(
                        CustomApi.api_name.like(search_pattern),
                        CustomApi.api_code.like(search_pattern)
                    )
                )
            if customer_id:
                count_query = count_query.where(CustomApi.customer_id == customer_id)

            total_result = await api_db.execute(count_query)
            total = total_result.scalar() or 0
            print(f"🔍 [DEBUG] 总记录数: {total}")

            # 分页与排序
            query = query.order_by(CustomApi.created_at.desc())
            query = query.offset((page - 1) * page_size).limit(page_size)
            print(f"🔍 [DEBUG] 最终SQL查询: {query}")

            result = await api_db.execute(query)
            apis = result.scalars().all()
            print(f"🔍 [DEBUG] 返回API记录数: {len(apis)}")

            # 转换为字典并序列化时间、平台信息
            items: List[dict] = []
            for api in apis:
                item = {
                    "id": api.id,
                    "customer_id": api.customer_id,
                    "api_name": api.api_name,
                    "api_code": api.api_code,
                    "description": api.api_description,  # 使用正确的字段名
                    "endpoint_url": api.api_url,         # 使用正确的字段名
                    "http_method": api.http_method,
                    "request_format": getattr(api, 'request_format', 'json'),  # 安全访问
                    "response_format": api.response_format,
                    "resource_type_id": getattr(api, 'resource_type_id', None),
                    "link_read_id": getattr(api, 'link_read_id', None),
                    "mapping_config_id": getattr(api, 'mapping_config_id', None),
                    "is_active": api.status == 1,        # 正确的状态转换
                    "total_calls": api.total_calls or 0,
                    "last_called_at": api.last_called_at.isoformat() if api.last_called_at else None,
                    "created_at": api.created_at.isoformat() if api.created_at else None,
                    "updated_at": api.updated_at.isoformat() if api.updated_at else None,
                }

                # 附加平台信息（只包含前端需要的基础字段）
                if getattr(api, "customer", None):
                    customer = api.customer
                    item["customer"] = {
                        "id": getattr(customer, "id", None),
                        "name": getattr(customer, "name", None),
                        "company": getattr(customer, "company", None),
                        "email": getattr(customer, "email", None),
                    }

                items.append(item)

            return success_response({
                "items": items,
                "total": total,
                "page": page,
                "page_size": page_size,
                "total_pages": (total + page_size - 1) // page_size
            })
            break  # 只需要执行一次

    except Exception as e:
        print(f"获取API列表失败: {e}")
        raise HTTPException(status_code=500, detail="数据库连接失败")

@router.get("/apis/{api_id}", summary="获取API详情")
async def get_api(
    api_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """获取API详情"""
    
    try:
        async for api_db in get_db_session(db_name="api_system"):
            # 查询API详情，包含平台信息
            query = select(CustomApi).options(joinedload(CustomApi.customer)).where(CustomApi.id == api_id)
            result = await api_db.execute(query)
            api = result.scalar_one_or_none()
            
            if not api:
                raise HTTPException(status_code=404, detail="API不存在")
            
            # 刷新数据以确保获取最新值
            await api_db.refresh(api)
            
            # 构建返回数据
            api_data = {
                "id": api.id,
                "customer_id": api.customer_id,
                "api_name": api.api_name,
                "api_code": api.api_code,
                "description": api.api_description,
                "endpoint_url": api.api_url,
                "http_method": api.http_method,
                "request_format": getattr(api, 'request_format', 'json'),
                "response_format": api.response_format,
                "resource_type_id": getattr(api, 'resource_type_id', None),
                "link_read_id": getattr(api, 'link_read_id', None),
                "mapping_config_id": getattr(api, 'mapping_config_id', None),
                "is_active": api.status == 1,
                "total_calls": api.total_calls or 0,
                "last_called_at": api.last_called_at.isoformat() if api.last_called_at else None,
                "created_at": api.created_at.isoformat() if api.created_at else None,
                "updated_at": api.updated_at.isoformat() if api.updated_at else None,
            }
            
            # 添加平台信息
            if api.customer:
                api_data["customer"] = {
                    "id": api.customer.id,
                    "name": api.customer.name,
                    "company": api.customer.company,
                    "email": api.customer.email,
                }
            
            return success_response(api_data)
            break
            
    except HTTPException:
        raise
    except Exception as e:
        print(f"获取API详情失败: {e}")
        raise HTTPException(status_code=500, detail="数据库连接失败")

@router.post("/apis", summary="创建API")
async def create_api(
    api_data: dict = Body(...),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    创建API
    
    接收JSON格式的API创建数据，如果指定了resource_type_id，
    会自动从资源类型的metadata字段中解析并创建API字段
    """
    
    try:
        async for api_db in get_db_session(db_name="api_system"):
            # 从请求体中提取数据
            customer_id = api_data.get("customer_id")
            api_name = api_data.get("api_name")
            api_code = api_data.get("api_code")
            api_description = api_data.get("api_description")
            http_method = api_data.get("http_method", "POST")
            response_format = api_data.get("response_format", "json")
            resource_type_id = api_data.get("resource_type_id")
            link_read_id = api_data.get("link_read_id")
            
            # 验证必需字段
            if not all([customer_id, api_name, api_code]):
                raise HTTPException(status_code=422, detail="缺少必需字段: customer_id, api_name, api_code")
            
            # 检查客户是否存在
            customer_query = select(Customer).where(Customer.id == customer_id)
            customer_result = await api_db.execute(customer_query)
            customer = customer_result.scalar_one_or_none()
            
            if not customer:
                raise HTTPException(status_code=404, detail="客户不存在")
            
            # 创建新API
            new_api = CustomApi(
                customer_id=customer_id,
                api_name=api_name,
                api_code=api_code,
                api_description=api_description,
                api_url=f"/api/custom/{api_code}",
                http_method=http_method,
                response_format=response_format,
                resource_type_id=resource_type_id,
                link_read_id=link_read_id,
                status=1,  # 默认激活
                total_calls=0,
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            
            api_db.add(new_api)
            await api_db.commit()
            await api_db.refresh(new_api)
            
            # 如果指定了resource_type_id，自动创建字段
            if resource_type_id:
                await _create_fields_from_resource_type(api_db, new_api.id, resource_type_id)
            
            # 构建返回数据
            api_data = {
                "id": new_api.id,
                "customer_id": new_api.customer_id,
                "api_name": new_api.api_name,
                "api_code": new_api.api_code,
                "description": new_api.api_description,
                "endpoint_url": new_api.api_url,
                "http_method": new_api.http_method,
                "response_format": new_api.response_format,
                "resource_type_id": new_api.resource_type_id,
                "link_read_id": new_api.link_read_id,
                "is_active": new_api.status == 1,
                "total_calls": new_api.total_calls,
                "created_at": new_api.created_at.isoformat(),
                "updated_at": new_api.updated_at.isoformat(),
                "customer": {
                    "id": customer.id,
                    "name": customer.name,
                    "company": customer.company,
                    "email": customer.email,
                }
            }
            
            return success_response(api_data)
            break
            
    except HTTPException:
        raise
    except Exception as e:
        print(f"创建API失败: {e}")
        raise HTTPException(status_code=500, detail="创建API失败")

@router.put("/apis/{api_id}", summary="更新API")
async def update_api(
    api_id: int,
    update_data: CustomApiUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    更新API配置
    
    注意：根据业务需求，以下字段有固定默认值，不建议修改：
    - 请求方法：POST
    - 请求格式：json
    - 响应格式：json
    """
    
    try:
        print('11111111111111111111111111111111111111111111111111111111111111')
        print(f"DEBUG: 接收到的参数 - update_data: {update_data}")
        if update_data:
            print(f"DEBUG: update_data 类型: {type(update_data)}")
            print(f"DEBUG: update_data 内容: {update_data.__dict__ if hasattr(update_data, '__dict__') else 'No __dict__'}")
            print(f"DEBUG: update_data.api_name: {getattr(update_data, 'api_name', 'ATTR_NOT_FOUND')}")
            print(f"DEBUG: update_data.api_description: {getattr(update_data, 'api_description', 'ATTR_NOT_FOUND')}")
        async for api_db in get_db_session(db_name="api_system"):
            # 查找要更新的API
            query = select(CustomApi).options(joinedload(CustomApi.customer)).where(CustomApi.id == api_id)
            result = await api_db.execute(query)
            api = result.scalar_one_or_none()
            
            if not api:
                raise HTTPException(status_code=404, detail="API不存在")
            
            # 更新字段（使用JSON Body）
            print(f"DEBUG: 收到的更新数据: api_name={getattr(update_data, 'api_name', None)}, api_description={getattr(update_data, 'api_description', None)}")
            print(f"DEBUG: 更新前的值: api_name={api.api_name}, api_description={api.api_description}")
            
            if update_data.api_name is not None:
                print(f"DEBUG: 正在更新 api_name 从 '{api.api_name}' 到 '{update_data.api_name}'")
                api.api_name = update_data.api_name
            if update_data.api_description is not None:
                print(f"DEBUG: 正在更新 api_description 从 '{api.api_description}' 到 '{update_data.api_description}'")
                api.api_description = update_data.api_description
            if update_data.http_method is not None:
                api.http_method = update_data.http_method
            if update_data.response_format is not None:
                api.response_format = update_data.response_format
            if hasattr(update_data, 'request_format') and getattr(update_data, 'request_format') is not None:
                api.request_format = getattr(update_data, 'request_format')
            # 支持 is_active 与 status 两种字段
            if update_data.is_active is not None:
                api.status = 1 if update_data.is_active else 0
            elif update_data.status is not None:
                api.status = 1 if update_data.status else 0
            if update_data.resource_type_id is not None:
                api.resource_type_id = update_data.resource_type_id
            if update_data.link_read_id is not None:
                api.link_read_id = update_data.link_read_id
            if update_data.mapping_config_id is not None:
                api.mapping_config_id = update_data.mapping_config_id
            
            # 更新时间戳
            api.updated_at = datetime.now()
            
            print(f"DEBUG: 提交前的值: api_name={api.api_name}, api_description={api.api_description}")
            
            await api_db.commit()
            
            print(f"DEBUG: 提交后，刷新前的值: api_name={api.api_name}, api_description={api.api_description}")
            
            await api_db.refresh(api)
            
            print(f"DEBUG: 刷新后的值: api_name={api.api_name}, api_description={api.api_description}")
            
            # 构建返回数据
            api_data = {
                "id": api.id,
                "customer_id": api.customer_id,
                "api_name": api.api_name,
                "api_code": api.api_code,
                "description": api.api_description,
                "endpoint_url": api.api_url,
                "http_method": api.http_method,
                "request_format": getattr(api, 'request_format', 'json'),
                "response_format": api.response_format,
                "resource_type_id": getattr(api, 'resource_type_id', None),
                "link_read_id": getattr(api, 'link_read_id', None),
                "mapping_config_id": getattr(api, 'mapping_config_id', None),
                "is_active": api.status == 1,
                "total_calls": api.total_calls or 0,
                "last_called_at": api.last_called_at.isoformat() if api.last_called_at else None,
                "created_at": api.created_at.isoformat() if api.created_at else None,
                "updated_at": api.updated_at.isoformat() if api.updated_at else None,
            }
            
            # 添加平台信息
            if api.customer:
                api_data["customer"] = {
                    "id": api.customer.id,
                    "name": api.customer.name,
                    "company": api.customer.company,
                    "email": api.customer.email,
                }
            
            return success_response(api_data)
            break
            
    except HTTPException:
        raise
    except Exception as e:
        print(f"更新API失败: {e}")
        raise HTTPException(status_code=500, detail="更新API失败")

@router.post("/apis/{api_id}/copy", summary="复制API")
async def copy_api(
    api_id: int,
    copy_data: CustomApiCopy,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    复制API到指定客户
    
    将现有API复制到目标客户，包括API配置和字段定义
    """
    
    try:
        async for api_db in get_db_session(db_name="api_system"):
            # 查找源API
            source_query = select(CustomApi).options(
                selectinload(CustomApi.customer),
                selectinload(CustomApi.fields)
            ).where(CustomApi.id == api_id)
            source_result = await api_db.execute(source_query)
            source_api = source_result.scalar_one_or_none()
            
            if not source_api:
                raise HTTPException(status_code=404, detail="源API不存在")
            
            # 验证目标客户是否存在
            target_customer_query = select(Customer).where(Customer.id == copy_data.target_customer_id)
            target_customer_result = await api_db.execute(target_customer_query)
            target_customer = target_customer_result.scalar_one_or_none()
            
            if not target_customer:
                raise HTTPException(status_code=404, detail="目标客户不存在")
            
            # 检查目标客户是否已有相同API代码
            existing_api_query = select(CustomApi).where(
                and_(
                    CustomApi.customer_id == copy_data.target_customer_id,
                    CustomApi.api_code == copy_data.new_api_code
                )
            )
            existing_api_result = await api_db.execute(existing_api_query)
            existing_api = existing_api_result.scalar_one_or_none()
            
            if existing_api:
                raise HTTPException(status_code=400, detail="目标客户已存在相同API代码")
            
            # 创建新API
            new_api = CustomApi(
                customer_id=copy_data.target_customer_id,
                api_name=copy_data.new_api_name or source_api.api_name,
                api_code=copy_data.new_api_code,
                api_description=source_api.api_description,
                api_url=f"/api/v1/custom/{copy_data.new_api_code}",
                http_method=source_api.http_method,
                status=source_api.status,
                rate_limit=source_api.rate_limit,
                response_format=source_api.response_format,
                require_authentication=source_api.require_authentication,
                link_read_id=source_api.link_read_id,
                resource_type_id=getattr(source_api, 'resource_type_id', None),
                total_calls=0,  # 重置调用次数
                last_called_at=None,  # 重置最后调用时间
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            
            api_db.add(new_api)
            await api_db.flush()  # 获取新API的ID
            
            # 复制字段定义
            if hasattr(source_api, 'fields') and source_api.fields:
                for source_field in source_api.fields:
                    new_field = ApiField(
                        api_id=new_api.id,
                        field_name=source_field.field_name,
                        field_label=source_field.field_label,
                        field_type=source_field.field_type,
                        is_required=source_field.is_required,
                        is_upload=getattr(source_field, 'is_upload', 1),
                        default_value=source_field.default_value,
                        max_length=source_field.max_length,
                        min_length=source_field.min_length,
                        max_value=source_field.max_value,
                        min_value=source_field.min_value,
                        allowed_values=getattr(source_field, 'allowed_values', None),
                        validation_regex=getattr(source_field, 'validation_regex', None),
                        validation_message=getattr(source_field, 'validation_message', None),
                        description=source_field.description,
                        sort_order=source_field.sort_order,
                        created_at=datetime.now(),
                        updated_at=datetime.now()
                    )
                    api_db.add(new_field)
            
            await api_db.commit()
            await api_db.refresh(new_api)
            
            # 构建返回数据
            api_data = {
                "id": new_api.id,
                "customer_id": new_api.customer_id,
                "api_name": new_api.api_name,
                "api_code": new_api.api_code,
                "description": new_api.api_description,
                "endpoint_url": new_api.api_url,
                "http_method": new_api.http_method,
                "request_format": getattr(new_api, 'request_format', 'json'),
                "response_format": new_api.response_format,
                "resource_type_id": getattr(new_api, 'resource_type_id', None),
                "mapping_config_id": getattr(new_api, 'mapping_config_id', None),
                "is_active": new_api.status == 1,
                "total_calls": new_api.total_calls or 0,
                "last_called_at": new_api.last_called_at.isoformat() if new_api.last_called_at else None,
                "created_at": new_api.created_at.isoformat() if new_api.created_at else None,
                "updated_at": new_api.updated_at.isoformat() if new_api.updated_at else None,
                "customer": {
                    "id": target_customer.id,
                    "name": target_customer.name,
                    "company": target_customer.company,
                    "email": target_customer.email,
                }
            }
            
            return success_response(api_data, message="API复制成功")
            break
            
    except HTTPException:
        raise
    except Exception as e:
        print(f"复制API失败: {e}")
        raise HTTPException(status_code=500, detail=f"复制API失败: {str(e)}")


@router.delete("/apis/{api_id}", summary="删除API")
async def delete_api(
    api_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    删除API
    
    删除指定的API及其相关的字段定义和使用日志
    """
    
    try:
        async for api_db in get_db_session(db_name="api_system"):
            # 先检查API是否存在（不加载关联关系避免字段不匹配问题）
            api_exists_query = select(CustomApi.id).where(CustomApi.id == api_id)
            api_exists_result = await api_db.execute(api_exists_query)
            api_exists = api_exists_result.scalar_one_or_none()
            
            if not api_exists:
                raise HTTPException(status_code=404, detail="API不存在")
            
            # 1. 先删除相关的使用日志记录（使用原生SQL）
            try:
                await api_db.execute(text("DELETE FROM api_usage_logs WHERE api_id = :api_id"), {"api_id": api_id})
            except Exception as log_delete_error:
                print(f"删除使用日志时出错（可能表不存在或字段不匹配）: {log_delete_error}")
                # 继续执行，不因为日志删除失败而中断API删除
            
            # 2. 删除相关的字段定义（使用原生SQL）
            try:
                await api_db.execute(text("DELETE FROM api_fields WHERE api_id = :api_id"), {"api_id": api_id})
            except Exception as field_delete_error:
                print(f"删除API字段时出错: {field_delete_error}")
            
            # 3. 删除API本身（使用原生SQL）
            await api_db.execute(text("DELETE FROM custom_apis WHERE id = :api_id"), {"api_id": api_id})
            await api_db.commit()
            
            return success_response({"id": api_id}, message="API删除成功")
            break
            
    except HTTPException:
        raise
    except Exception as e:
        print(f"删除API失败: {e}")
        raise HTTPException(status_code=500, detail=f"删除API失败: {str(e)}")

# ==================== 批次管理 ====================

@router.get("/batches", summary="获取批次列表")
async def get_batches(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    search: Optional[str] = Query(None, description="搜索关键词"),
    customer_id: Optional[int] = Query(None, description="客户ID"),
    status: Optional[str] = Query(None, description="状态"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """获取批次列表"""
    
    try:
        async for api_db in get_db_session(db_name="api_system"):
            # 构建查询条件
            query = select(DataBatch).options(joinedload(DataBatch.customer))
            
            # 添加搜索条件
            if search:
                query = query.where(DataBatch.batch_name.ilike(f"%{search}%"))
            if customer_id:
                query = query.where(DataBatch.customer_id == customer_id)
            if status:
                query = query.where(DataBatch.status == status)
            
            # 获取总数
            count_query = select(func.count(DataBatch.id))
            if search:
                count_query = count_query.where(DataBatch.batch_name.ilike(f"%{search}%"))
            if customer_id:
                count_query = count_query.where(DataBatch.customer_id == customer_id)
            if status:
                count_query = count_query.where(DataBatch.status == status)
            
            total_result = await api_db.execute(count_query)
            total = total_result.scalar()
            
            # 分页查询
            query = query.offset((page - 1) * page_size).limit(page_size)
            result = await api_db.execute(query)
            batches = result.scalars().all()
            
            # 构建返回数据
            items = []
            for batch in batches:
                item = {
                    "id": batch.id,
                    "customer_id": batch.customer_id,
                    "batch_name": batch.batch_name,
                    "status": batch.status,
                    "total_records": batch.total_records or 0,
                    "processed_records": batch.processed_records or 0,
                    "success_records": batch.success_records or 0,
                    "failed_records": batch.failed_records or 0,
                    "created_at": batch.created_at.isoformat() if batch.created_at else None,
                    "updated_at": batch.updated_at.isoformat() if batch.updated_at else None,
                    "started_at": batch.started_at.isoformat() if batch.started_at else None,
                    "completed_at": batch.completed_at.isoformat() if batch.completed_at else None,
                }
                
                # 添加平台信息
                if batch.customer:
                    item["customer"] = {
                        "id": batch.customer.id,
                        "name": batch.customer.name,
                        "company": batch.customer.company,
                        "email": batch.customer.email,
                    }
                
                items.append(item)
            
            return success_response({
                "items": items,
                "total": total,
                "page": page,
                "page_size": page_size,
                "total_pages": (total + page_size - 1) // page_size
            })
            break
            
    except Exception as e:
        print(f"获取批次列表失败: {e}")
        raise HTTPException(status_code=500, detail="数据库连接失败")

@router.get("/batches/{batch_id}", summary="获取批次详情")
async def get_batch(
    batch_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """获取批次详情"""
    
    try:
        async for api_db in get_db_session(db_name="api_system"):
            # 查询批次详情，包含平台信息
            query = select(DataBatch).options(joinedload(DataBatch.customer)).where(DataBatch.id == batch_id)
            result = await api_db.execute(query)
            batch = result.scalar_one_or_none()
            
            if not batch:
                raise HTTPException(status_code=404, detail="批次不存在")
            
            # 构建返回数据
            batch_data = {
                "id": batch.id,
                "customer_id": batch.customer_id,
                "batch_name": batch.batch_name,
                "status": batch.status,
                "total_records": batch.total_records or 0,
                "processed_records": batch.processed_records or 0,
                "success_records": batch.success_records or 0,
                "failed_records": batch.failed_records or 0,
                "created_at": batch.created_at.isoformat() if batch.created_at else None,
                "updated_at": batch.updated_at.isoformat() if batch.updated_at else None,
                "started_at": batch.started_at.isoformat() if batch.started_at else None,
                "completed_at": batch.completed_at.isoformat() if batch.completed_at else None,
            }
            
            # 添加平台信息
            if batch.customer:
                batch_data["customer"] = {
                    "id": batch.customer.id,
                    "name": batch.customer.name,
                    "company": batch.customer.company,
                    "email": batch.customer.email,
                }
            
            return success_response(batch_data)
            break
            
    except HTTPException:
        raise
    except Exception as e:
        print(f"获取批次详情失败: {e}")
        raise HTTPException(status_code=500, detail="数据库连接失败")

@router.post("/batches", summary="创建批次")
async def create_batch(
    customer_id: int = Form(...),
    batch_name: str = Form(...),
    description: Optional[str] = Form(None),
    file: Optional[UploadFile] = File(None),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """创建批次"""
    
    try:
        async for api_db in get_db_session(db_name="api_system"):
            # 检查客户是否存在
            customer_query = select(Customer).where(Customer.id == customer_id)
            customer_result = await api_db.execute(customer_query)
            customer = customer_result.scalar_one_or_none()
            
            if not customer:
                raise HTTPException(status_code=404, detail="客户不存在")
            
            # 处理文件上传
            file_path = None
            if file:
                file_path = f"/uploads/{file.filename}"
                # 这里可以添加实际的文件保存逻辑
            
            # 创建新批次
            new_batch = DataBatch(
                customer_id=customer_id,
                batch_name=batch_name,
                description=description,
                file_path=file_path,
                status="pending",
                total_records=0,
                processed_records=0,
                success_records=0,
                failed_records=0,
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            
            api_db.add(new_batch)
            await api_db.commit()
            await api_db.refresh(new_batch)
            
            # 构建返回数据
            batch_data = {
                "id": new_batch.id,
                "customer_id": new_batch.customer_id,
                "batch_name": new_batch.batch_name,
                "description": new_batch.description,
                "file_path": new_batch.file_path,
                "status": new_batch.status,
                "total_records": new_batch.total_records,
                "processed_records": new_batch.processed_records,
                "success_records": new_batch.success_records,
                "failed_records": new_batch.failed_records,
                "created_at": new_batch.created_at.isoformat(),
                "updated_at": new_batch.updated_at.isoformat(),
                "customer": {
                    "id": customer.id,
                    "name": customer.name,
                    "company": customer.company,
                    "email": customer.email,
                }
            }
            
            return success_response(batch_data)
            break
            
    except HTTPException:
        raise
    except Exception as e:
        print(f"创建批次失败: {e}")
        raise HTTPException(status_code=500, detail="创建批次失败")

# ==================== 统计信息 ====================

@router.get("/stats/system", summary="获取系统统计")
async def get_system_stats(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """获取系统统计信息"""
    
    try:
        async for api_db in get_db_session(db_name="api_system"):
            # 统计客户数量
            total_customers_query = select(func.count(Customer.id))
            total_customers_result = await api_db.execute(total_customers_query)
            total_customers = total_customers_result.scalar()
            
            # 统计活跃平台数量（按需求：等于 customers 表总数）
            active_customers = total_customers
            
            # 统计API数量
            total_apis_query = select(func.count(CustomApi.id))
            total_apis_result = await api_db.execute(total_apis_query)
            total_apis = total_apis_result.scalar()
            
            # 统计批次数量
            total_batches_query = select(func.count(DataBatch.id))
            total_batches_result = await api_db.execute(total_batches_query)
            total_batches = total_batches_result.scalar()
            
            # 统计不同状态的批次数量
            pending_batches_query = select(func.count(DataBatch.id)).where(DataBatch.status == 'pending')
            pending_batches_result = await api_db.execute(pending_batches_query)
            pending_batches = pending_batches_result.scalar()
            
            processing_batches_query = select(func.count(DataBatch.id)).where(DataBatch.status == 'processing')
            processing_batches_result = await api_db.execute(processing_batches_query)
            processing_batches = processing_batches_result.scalar()
            
            completed_batches_query = select(func.count(DataBatch.id)).where(DataBatch.status == 'completed')
            completed_batches_result = await api_db.execute(completed_batches_query)
            completed_batches = completed_batches_result.scalar()
            
            failed_batches_query = select(func.count(DataBatch.id)).where(DataBatch.status == 'failed')
            failed_batches_result = await api_db.execute(failed_batches_query)
            failed_batches = failed_batches_result.scalar()
            
            # 统计总API调用次数（按需求：custom_apis.total_calls 的总和）
            total_api_calls_query = select(func.sum(CustomApi.total_calls))
            total_api_calls_result = await api_db.execute(total_api_calls_query)
            total_api_calls = int(total_api_calls_result.scalar() or 0)
            
            stats = {
                "totalCustomers": total_customers,
                "totalApis": total_apis,
                "totalBatches": total_batches,
                "totalUploads": 0,  # 可以根据需要添加文件上传统计
                "totalApiCalls": total_api_calls,
                "activeCustomers": active_customers,
                "pendingBatches": pending_batches,
                "processingBatches": processing_batches,
                "completedBatches": completed_batches,
                "failedBatches": failed_batches
            }
            
            return success_response(stats)
            break
            
    except Exception as e:
        print(f"获取系统统计失败: {e}")
        raise HTTPException(status_code=500, detail="数据库连接失败")

@router.get("/admin/apis/{api_id}/documentation", summary="生成API文档")
async def generate_api_documentation(
    api_id: int,
    format: str = Query("markdown", description="文档格式: markdown, html, json"),
    current_user: User = Depends(get_current_active_user)
):
    """
    生成API文档
    
    支持的格式:
    - markdown: Markdown格式文档
    - html: HTML格式文档  
    - json: OpenAPI 3.0 JSON格式
    """
    
    # 获取API信息
    try:
        # 使用多数据库功能连接到 api_system 数据库
        async for api_db in get_db_session(db_name="api_system"):
            query = select(CustomApi).options(selectinload(CustomApi.customer)).where(CustomApi.id == api_id)
            result = await api_db.execute(query)
            api = result.scalar_one_or_none()
            
            if not api:
                raise HTTPException(status_code=404, detail="API不存在")
            
            # 获取API字段信息
            fields_query = select(ApiField).where(ApiField.api_id == api_id).order_by(ApiField.sort_order)
            fields_result = await api_db.execute(fields_query)
            api_fields = fields_result.scalars().all()
            break
        
        # 根据格式生成文档
        if format == "markdown":
            documentation = _generate_markdown_doc(api, api_fields)
        elif format == "html":
            documentation = _generate_html_doc(api, api_fields)
        elif format == "json":
            documentation = _generate_openapi_doc(api, api_fields)
        else:
            raise HTTPException(status_code=400, detail="不支持的文档格式")
        
        return success_response({
            "documentation": documentation,
            "format": format,
            "api_id": api_id,
            "api_name": api.api_name
        })
        
    except Exception as e:
        print(f"生成API文档失败: {e}")
        raise HTTPException(status_code=500, detail=f"生成文档失败: {str(e)}")

@router.get("/admin/apis/{api_id}/docs", summary="获取API Swagger文档")
async def get_api_swagger_docs(
    api_id: int,
    token: str = Query(..., description="认证token"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取API的Swagger UI文档页面
    """
    
    try:
        db_session = get_db_session(db_name="api_system")
        
        # 查询API详情
        query = select(CustomApi).options(selectinload(CustomApi.customer)).where(CustomApi.id == api_id)
        result = db_session.execute(query)
        api = result.scalar_one_or_none()
        
        if not api:
            raise HTTPException(status_code=404, detail="API不存在")
        
        # 生成OpenAPI规范
        openapi_spec = _generate_openapi_doc(api)
        
        # 生成Swagger UI HTML页面
        swagger_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>{api.api_name} - API文档</title>
            <link rel="stylesheet" type="text/css" href="https://unpkg.com/swagger-ui-dist@3.52.5/swagger-ui.css" />
            <style>
                html {{ box-sizing: border-box; overflow: -moz-scrollbars-vertical; overflow-y: scroll; }}
                *, *:before, *:after {{ box-sizing: inherit; }}
                body {{ margin:0; background: #fafafa; }}
            </style>
        </head>
        <body>
            <div id="swagger-ui"></div>
            <script src="https://unpkg.com/swagger-ui-dist@3.52.5/swagger-ui-bundle.js"></script>
            <script src="https://unpkg.com/swagger-ui-dist@3.52.5/swagger-ui-standalone-preset.js"></script>
            <script>
                window.onload = function() {{
                    const ui = SwaggerUIBundle({{
                        url: 'data:application/json;base64,' + btoa(unescape(encodeURIComponent('{openapi_spec}'))),
                        dom_id: '#swagger-ui',
                        deepLinking: true,
                        presets: [
                            SwaggerUIBundle.presets.apis,
                            SwaggerUIStandalonePreset
                        ],
                        plugins: [
                            SwaggerUIBundle.plugins.DownloadUrl
                        ],
                        layout: "StandaloneLayout"
                    }});
                }};
            </script>
        </body>
        </html>
        """
        
        from fastapi.responses import HTMLResponse
        return HTMLResponse(content=swagger_html)
        
    except Exception as e:
        print(f"获取API文档失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取文档失败: {str(e)}")

def _generate_markdown_doc(api: CustomApi, api_fields: list = None) -> str:
    """
    生成完整的Markdown格式API服务文档
    
    Args:
        api: API对象
        api_fields: API字段列表
        
    Returns:
        Markdown文档内容
    """
    doc = []
    
    # 文档标题
    doc.append(f"# 📋 {api.customer.name if api.customer else '客户'}数据采集API服务文档")
    doc.append("")
    doc.append("本文档描述了完整的数据采集API服务，包含认证、数据上传、批次管理和结果查询四个核心功能。")
    doc.append("")
    
    # 目录
    doc.append("## 📑 目录")
    doc.append("")
    doc.append("- [🔐 1. 认证接口](#1-认证接口)")
    doc.append("- [📤 2. 数据上传接口](#2-数据上传接口)")
    doc.append("- [✅ 3. 批次完成接口](#3-批次完成接口)")
    doc.append("- [📥 4. 结果查询接口](#4-结果查询接口)")
    doc.append("- [📬 5. 结果接收确认接口](#5-结果接收确认接口)")
    doc.append("- [🔄 6. 完整调用流程](#6-完整调用流程)")
    doc.append("- [🔔 7. 回调通知机制](#7-回调通知机制)")
    doc.append("- [📋 8. 业务状态码说明](#8-业务状态码说明)")
    doc.append("- [⚠️ 9. 注意事项](#9-注意事项)")
    doc.append("")
    
    # 1. 认证接口
    doc.append("## 🔐 1. 认证接口")
    doc.append("")
    doc.append("### 接口信息")
    doc.append("- **接口地址**: `/api/v1/auth/token`")
    doc.append("- **请求方法**: `POST`")
    doc.append("- **功能说明**: 获取访问令牌和数据加密密钥")
    doc.append("- **认证方式**: 签名认证")
    doc.append("")
    
    doc.append("### 请求参数")
    doc.append("")
    doc.append("| 字段名 | 类型 | 必填 | 描述 |")
    doc.append("|--------|------|------|------|")
    doc.append("| appid | String | 是 | 应用唯一标识 |")
    doc.append("| timestamp | Long | 是 | 当前时间戳（毫秒） |")
    doc.append("| nonce | String | 是 | 随机字符串（8-16位） |")
    doc.append("| signature | String | 是 | HMAC-SHA256签名 |")
    doc.append("")
    
    doc.append("### 签名生成规则")
    doc.append("")
    doc.append("```")
    doc.append("signature_data = appid + timestamp + nonce")
    doc.append("signature = HMAC_SHA256(secret, signature_data).hexdigest().upper()")
    doc.append("```")
    doc.append("")
    
    doc.append("### 请求示例")
    doc.append("")
    doc.append("```json")
    doc.append("{")
    doc.append('    "appid": "your_app_id",')
    doc.append('    "timestamp": 1640995200000,')
    doc.append('    "nonce": "abc123def456",')
    doc.append('    "signature": "ABCD1234..."')
    doc.append("}")
    doc.append("```")
    doc.append("")
    
    doc.append("### 响应示例")
    doc.append("")
    doc.append("```json")
    doc.append("{")
    doc.append('    "code": 0,')
    doc.append('    "message": "认证成功",')
    doc.append('    "data": {')
    doc.append('        "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",')
    doc.append('        "data_key": "base64_encoded_key",')
    doc.append('        "expires_in": 3600')
    doc.append('    }')
    doc.append("}")
    doc.append("```")
    doc.append("")
    
    # 2. 数据上传接口
    doc.append("## 📤 2. 数据上传接口")
    doc.append("")
    doc.append("### 接口信息")
    doc.append(f"- **接口地址**: `/api/v1/{{batch_id}}/{api.api_code}`")
    doc.append(f"- **请求方法**: `{api.http_method}`")
    doc.append("- **功能说明**: 上传业务数据到指定批次")
    doc.append("- **认证方式**: Bearer Token")
    doc.append("- **数据加密**: 支持AES-256-GCM加密")
    doc.append("- **数据签名**: 支持HMAC-SHA256签名验证")
    doc.append("")
    
    doc.append("### 请求头")
    doc.append("")
    doc.append("| 字段名 | 类型 | 必填 | 描述 |")
    doc.append("|--------|------|------|------|")
    doc.append("| Authorization | String | 是 | Bearer {access_token} |")
    doc.append("| Content-Type | String | 是 | application/json |")
    doc.append("| X-Data-Encrypted | String | 否 | true（启用加密时） |")
    doc.append("| X-Data-Signature | String | 否 | 数据签名（启用签名验证时） |")
    doc.append("")
    
    doc.append("### 路径参数")
    doc.append("")
    doc.append("| 参数名 | 类型 | 必填 | 描述 |")
    doc.append("|--------|------|------|------|")
    doc.append("| batch_id | String | 是 | 批次唯一标识 |")
    doc.append("")
    

    
    if api_fields:
        upload_fields = [f for f in api_fields if getattr(f, "is_upload", 0) == 1 or str(getattr(f, "is_upload", 0)) == "1"]
        if upload_fields:
            doc.append("### 数据字段说明")
            doc.append("")
            doc.append("| 字段名 | 类型 | 必填 | 描述 |")
            doc.append("|--------|------|------|------|")
            for field in upload_fields:
                required = "是" if field.is_required else "否"
                doc.append(f"| {field.field_name} | {field.field_type} | {required} | {field.description or '无描述'} |")
            doc.append("")
    
    doc.append("### 数据签名机制")
    doc.append("")
    doc.append("为确保数据完整性和防篡改，系统支持HMAC-SHA256数据签名验证：")
    doc.append("")
    doc.append("#### 签名生成规则")
    doc.append("")
    doc.append("```")
    doc.append("signature = HMAC_SHA256(data_key, encrypted_data).hexdigest().upper()")
    doc.append("```")
    doc.append("")
    doc.append("- **签名密钥**: 使用认证接口返回的`data_key`")
    doc.append("- **签名数据**: 加密后的数据（`data`字段的值）")
    doc.append("- **签名算法**: HMAC-SHA256")
    doc.append("- **签名格式**: 十六进制字符串（大写）")
    doc.append("")
    doc.append("#### 签名传递方式")
    doc.append("")
    doc.append("签名可通过以下两种方式传递（优先级：请求体 > 请求头）：")
    doc.append("")
    doc.append("1. **请求体中的signature字段**")
    doc.append("2. **请求头X-Data-Signature**")
    doc.append("")
    doc.append("#### 服务端验证流程")
    doc.append("")
    doc.append("1. 提取客户的`data_key`")
    doc.append("2. 使用相同规则重新计算签名")
    doc.append("3. 比较计算结果与提供的签名")
    doc.append("4. 签名不匹配时返回错误码2003")
    doc.append("")
    
    doc.append("### 加密请求示例")
    doc.append("")
    doc.append("```json")
    doc.append("{")
    doc.append('    "timestamp": 1640995200000,')
    doc.append('    "nonce": "random_string",')
    doc.append('    "data": "base64_encrypted_data",')
    doc.append('    "iv": "base64_iv",')
    doc.append('    "signature": "ABCD1234567890ABCDEF...",')
    doc.append('    "needread": false')
    doc.append("}")
    doc.append("```")
    doc.append("")
    doc.append("### 客户端实现示例（Python）")
    doc.append("")
    doc.append("```python")
    doc.append("import hmac")
    doc.append("import hashlib")
    doc.append("")
    doc.append("def generate_data_signature(data_key: str, encrypted_data: str) -> str:")
    doc.append('    """生成数据签名"""')
    doc.append("    signature = hmac.new(")
    doc.append("        data_key.encode('utf-8'),")
    doc.append("        encrypted_data.encode('utf-8'),")
    doc.append("        hashlib.sha256")
    doc.append("    ).hexdigest().upper()")
    doc.append("    return signature")
    doc.append("```")
    doc.append("")
    
    doc.append("### 响应示例")
    doc.append("")
    doc.append("```json")
    doc.append("{")
    doc.append('    "code": 0,')
    doc.append('    "message": "数据上传成功",')
    doc.append('    "data": {')
    doc.append('        "batch_id": "batch_123",')
    doc.append('        "record_count": 100,')
    doc.append('        "upload_time": 1704067200')
    doc.append('    }')
    doc.append("}")
    doc.append("```")
    doc.append("")
    
    # 3. 批次完成接口
    doc.append("## ✅ 3. 批次完成接口")
    doc.append("")
    doc.append("### 接口信息")
    doc.append(f"- **接口地址**: `/api/v1/batch/{api.api_code}/{{batch_id}}/complete`")
    doc.append("- **请求方法**: `POST`")
    doc.append("- **功能说明**: 标记批次数据上传完成，触发后续处理")
    doc.append("- **认证方式**: Bearer Token")
    doc.append("- **数据加密**: 支持AES-256-GCM加密")
    doc.append("- **数据签名**: 支持HMAC-SHA256签名验证")
    doc.append("")
    
    doc.append("### 请求头")
    doc.append("")
    doc.append("| 字段名 | 类型 | 必填 | 描述 |")
    doc.append("|--------|------|------|------|")
    doc.append("| Authorization | String | 是 | Bearer {access_token} |")
    doc.append("| X-Data-Encrypted | String | 是 | true |")
    doc.append("| X-Data-Signature | String | 否 | 数据签名（推荐使用） |")
    doc.append("")
    
    doc.append("### 路径参数")
    doc.append("")
    doc.append("| 参数名 | 类型 | 必填 | 描述 |")
    doc.append("|--------|------|------|------|")
    doc.append("| batch_id | String | 是 | 批次唯一标识 |")
    doc.append("")
    
    doc.append("### 请求体参数")
    doc.append("")
    doc.append("| 字段名 | 类型 | 必填 | 描述 |")
    doc.append("|--------|------|------|------|")
    doc.append("| timestamp | Long | 是 | 当前时间戳（秒） |")
    doc.append("| nonce | String | 是 | 随机字符串（8-16位） |")
    doc.append("| data | String | 是 | AES-GCM加密后的完成数据（Base64编码） |")
    doc.append("| iv | String | 是 | 初始化向量（Base64编码） |")
    doc.append("| signature | String | 否 | 数据签名（HMAC-SHA256） |")
    doc.append("| needread | Boolean | 否 | 是否需要读取确认，默认false |")
    doc.append("")
    
    doc.append("### 完成数据结构（加密前）")
    doc.append("")
    doc.append("```json")
    doc.append("{")
    doc.append('    "callback_url": "https://your-domain.com/callback/{api.api_code}/{batch_id}/{status}/{total}/{success_count}/{failed_count}/{timestamp}",')
    doc.append('    "total": 1000,')
    doc.append('    "remark": "批次处理完成"')
    doc.append("}")
    doc.append("```")
    doc.append("")
    
    doc.append("#### callback_url 字段说明")
    doc.append("")
    doc.append("- **字段用途**: 客户自定义的回调通知地址（可选）")
    doc.append("- **URL格式**: 必须是完整的HTTP/HTTPS地址")
    doc.append("- **变量替换**: `{api.api_code}` 会被替换为实际的API代码")
    doc.append("- **通知时机**: 批次处理完成后，系统会自动调用此地址通知客户")
    doc.append("")
    doc.append("### 数据签名说明")
    doc.append("")
    doc.append("批次完成接口的签名机制与数据上传接口相同：")
    doc.append("")
    doc.append("- **签名对象**: 加密后的数据（`data`字段值）")
    doc.append("- **签名密钥**: 认证接口返回的`data_key`")
    doc.append("- **签名算法**: HMAC-SHA256")
    doc.append("- **传递方式**: 请求体`signature`字段或请求头`X-Data-Signature`")
    doc.append("")
    
    doc.append("### 请求示例")
    doc.append("")
    doc.append("```json")
    doc.append("{")
    doc.append('    "timestamp": 1640995200000,')
    doc.append('    "nonce": "random_string",')
    doc.append('    "data": "encrypted_completion_data",')
    doc.append('    "iv": "base64_iv",')
    doc.append('    "signature": "ABCD1234567890ABCDEF...",')
    doc.append('    "needread": false')
    doc.append("}")
    doc.append("```")
    doc.append("")
    
    doc.append("### 响应示例")
    doc.append("")
    doc.append("```json")
    doc.append("{")
    doc.append('    "code": 0,')
    doc.append('    "message": "批次完成标记成功",')
    doc.append('    "data": {')
    doc.append('        "batch_id": "batch_123",')
    doc.append('        "status": "completed",')
    doc.append('        "completed_at": 1704067200')
    doc.append('    }')
    doc.append("}")
    doc.append("```")
    doc.append("")
    
    # 4. 结果查询接口
    doc.append("## 📥 4. 结果查询接口")
    doc.append("")
    doc.append("### 接口信息")
    doc.append(f"- **接口地址**: `/api/v1/results/{api.api_code}/{{batch_id}}/{{datetime}}`")
    doc.append("- **请求方法**: `GET`")
    doc.append("- **功能说明**: 查询批次处理结果")
    doc.append("- **认证方式**: Bearer Token")
    doc.append("- **数据加密**: 支持AES-256-GCM加密返回")
    doc.append("- **数据签名**: 返回结果包含HMAC-SHA256签名")
    doc.append("")
    
    doc.append("### 请求头")
    doc.append("")
    doc.append("| 字段名 | 类型 | 必填 | 描述 |")
    doc.append("|--------|------|------|------|")
    doc.append("| Authorization | String | 是 | Bearer {access_token} |")
    doc.append("")
    
    doc.append("### 路径参数")
    doc.append("")
    doc.append("| 参数名 | 类型 | 必填 | 描述 |")
    doc.append("|--------|------|------|------|")
    doc.append("| batch_id | String | 是 | 批次唯一标识 |")
    doc.append("| datetime | Long | 是 | 查询时间（Unix时间戳，毫秒） |")
    doc.append("")
    
    doc.append("### 响应字段说明")
    doc.append("")
    doc.append("| 字段名 | 类型 | 描述 |")
    doc.append("|--------|------|------|")
    doc.append("| status | String | 批次状态：processing/completed/failed/cancelled |")
    doc.append("| data | String | 加密后的结果数据（Base64编码），仅在completed/failed时返回 |")
    doc.append("| iv | String | 初始化向量（Base64编码），用于解密data字段 |")
    doc.append("| result_sign | String | 结果数据签名（HMAC-SHA256），用于验证数据完整性 |")
    doc.append("| last_modified | Long | 数据最后修改时间（Unix时间戳，毫秒） |")
    doc.append("| created_at | Long | 批次创建时间（Unix时间戳，毫秒） |")
    # doc.append("| completed_at | Long | 批次完成时间（Unix时间戳，毫秒），仅在completed/failed时返回 |")
    doc.append("| has_changes | Boolean | 自datetime参数时间以来是否有变更（仅在提供datetime参数时返回） |")
    doc.append("")
    
    doc.append("### 结果数据结构说明")
    doc.append("")
    doc.append("data字段解密后为JSON格式，包含以下结构：")
    doc.append("")
    doc.append("```json")
    doc.append("{")
    doc.append('    "batch_id": "batch_20241201_001",')
    doc.append('    "results": [')
    doc.append("        {")
    doc.append('            "source_system_id": "xxxxxx1",')
    doc.append('            "status": "pass",')
    doc.append('            "msg": "通过"')
    doc.append("        },")
    doc.append("        {")
    doc.append('            "source_system_id": "xxxxxx2",')
    doc.append('            "status": "prohibit",')
    doc.append('            "msg": "不通过"')
    doc.append("        }",)
    doc.append("        {")
    doc.append('            "source_system_id": "xxxxxx3",')
    doc.append('            "status": "restriction",')
    doc.append('            "msg": "限制"')
    doc.append("        }")
    doc.append("    ]")
    doc.append("}")
    doc.append("```")
    doc.append("")
    doc.append("**字段说明：**")
    doc.append("")
    doc.append("| 字段名 | 类型 | 描述 |")
    doc.append("|--------|------|------|")
    doc.append("| batch_id | String | 批次唯一标识 |")
    doc.append("| total | Integer | 总记录数 |")
    doc.append("| success_count | Integer | 成功处理数量 |")
    doc.append("| failed_count | Integer | 失败处理数量 |")
    doc.append("| results | Array | 处理结果数组 |")
    doc.append("| results[].id | String | 记录唯一标识 |")
    doc.append("| results[].status | String | 记录处理状态：success/failed |")
    doc.append("| results[].data | Object | 成功时返回的数据（具体结构依API而定） |")
    doc.append("| results[].error | String | 失败时的错误信息 |")
    doc.append("")
    
    doc.append("### 结果数据签名机制")
    doc.append("")
    doc.append("服务端在返回处理结果时会生成数据签名，确保结果数据的完整性：")
    doc.append("")
    doc.append("#### 签名生成规则")
    doc.append("")
    doc.append("```")
    doc.append("result_sign = HMAC_SHA256(data_key, encrypted_result_data).hexdigest()")
    doc.append("```")
    doc.append("")
    doc.append("- **签名密钥**: 客户的`data_key`")
    doc.append("- **签名数据**: 加密后的结果数据（`data`字段值）")
    doc.append("- **签名算法**: HMAC-SHA256")
    doc.append("- **签名格式**: 十六进制字符串（小写）")
    doc.append("")
    doc.append("#### 客户端验证示例（Python）")
    doc.append("")
    doc.append("```python")
    doc.append("import hmac")
    doc.append("import hashlib")
    doc.append("")
    doc.append("def verify_result_signature(data_key: str, encrypted_data: str, signature: str) -> bool:")
    doc.append('    """验证结果数据签名"""')
    doc.append("    expected_signature = hmac.new(")
    doc.append("        data_key.encode('utf-8'),")
    doc.append("        encrypted_data.encode('utf-8'),")
    doc.append("        hashlib.sha256")
    doc.append("    ).hexdigest()")
    doc.append("    return hmac.compare_digest(expected_signature, signature)")
    doc.append("```")
    doc.append("")
    
    doc.append("### 响应示例")
    doc.append("")
    doc.append("#### 处理中状态")
    doc.append("")
    doc.append("```json")
    doc.append("{")
    doc.append('    "code": 0,')
    doc.append('    "message": "批次结果查询成功",')
    doc.append('    "data": {')
    doc.append('        "status": "processing",')
    doc.append('        "data": null,')
    doc.append('        "iv": null,')
    doc.append('        "result_sign": null,')
    doc.append('        "last_modified": 1704065400,')
    doc.append('        "created_at": 1704063600,')
    doc.append('        "completed_at": null')
    doc.append('    }')
    doc.append("}")
    doc.append("```")
    doc.append("")
    doc.append("#### 处理完成状态")
    doc.append("")
    doc.append("```json")
    doc.append("{")
    doc.append('    "code": 0,')
    doc.append('    "message": "批次结果查询成功",')
    doc.append('    "data": {')
    doc.append('        "status": "completed",')
    doc.append('        "data": "base64_encrypted_result_data",')
    doc.append('        "iv": "base64_initialization_vector",')
    doc.append('        "result_sign": "abcd1234567890abcdef...",')
    doc.append('        "last_modified": 1704067200,')
    doc.append('        "created_at": 1704063600,')
    doc.append('        "completed_at": 1704067200')
    doc.append('    }')
    doc.append("}")
    doc.append("```")
    doc.append("")
    doc.append("#### 增量同步响应（有变更）")
    doc.append("")
    doc.append("```json")
    doc.append("{")
    doc.append('    "code": 0,')
    doc.append('    "message": "批次结果查询成功",')
    doc.append('    "data": {')
    doc.append('        "status": "completed",')
    doc.append('        "data": "base64_encrypted_result_data",')
    doc.append('        "iv": "base64_initialization_vector",')
    doc.append('        "result_sign": "abcd1234567890abcdef...",')
    doc.append('        "last_modified": 1704067200,')
    doc.append('        "created_at": 1704063600,')
    doc.append('        "completed_at": 1704067200,')
    doc.append('        "has_changes": true')
    doc.append('    }')
    doc.append("}")
    doc.append("```")
    doc.append("")
    doc.append("#### 增量同步响应（无变更）")
    doc.append("")
    doc.append("```json")
    doc.append("{")
    doc.append('    "code": 0,')
    doc.append('    "message": "批次结果查询成功",')
    doc.append('    "data": {')
    doc.append('        "status": "completed",')
    doc.append('        "data": null,')
    doc.append('        "iv": null,')
    doc.append('        "result_sign": null,')
    doc.append('        "last_modified": 1704063600,')
    doc.append('        "created_at": 1704063600,')
    doc.append('        "completed_at": 1704063600,')
    doc.append('        "has_changes": false')
    doc.append('    }')
    doc.append("}")
    doc.append("```")
    doc.append("")
    
    # 5. 结果接收确认接口
    doc.append("## 📬 5. 结果接收确认接口")
    doc.append("")
    doc.append("### 接口信息")
    doc.append(f"- **接口地址**: `/api/v1/results/{api.api_code}/{{batch_id}}/confirm`")
    doc.append("- **请求方法**: `POST`")
    doc.append("- **功能说明**: 客户端确认已接收并校验处理结果，系统记录确认状态")
    doc.append("- **认证方式**: Bearer Token")
    doc.append("- **数据加密**: 支持AES-256-GCM加密")
    doc.append("- **数据签名**: 支持HMAC-SHA256签名验证")
    doc.append("")
    doc.append("### 请求头")
    doc.append("")
    doc.append("| 字段名 | 类型 | 必填 | 描述 |")
    doc.append("|--------|------|------|------|")
    doc.append("| Authorization | String | 是 | Bearer {access_token} |")
    doc.append("| X-Data-Encrypted | String | 是 | true |")
    doc.append("| X-Data-Signature | String | 否 | 数据签名（推荐使用） |")
    doc.append("")
    doc.append("### 路径参数")
    doc.append("")
    doc.append("| 参数名 | 类型 | 必填 | 描述 |")
    doc.append("|--------|------|------|------|")
    doc.append("| batch_id | String | 是 | 批次唯一标识 |")
    doc.append("")
    doc.append("### 请求体参数")
    doc.append("")
    doc.append("| 字段名 | 类型 | 必填 | 描述 |")
    doc.append("|--------|------|------|------|")
    doc.append("| timestamp | Long | 是 | 当前时间戳（毫秒） |")
    doc.append("| nonce | String | 是 | 随机字符串（8-16位） |")
    doc.append("| data | String | 是 | AES-GCM加密后的确认数据（Base64编码） |")
    doc.append("| iv | String | 是 | 初始化向量（Base64编码） |")
    doc.append("| signature | String | 否 | 数据签名（HMAC-SHA256） |")
    doc.append("")
    doc.append("### 确认数据结构（加密前）")
    doc.append("")
    doc.append("```json")
    doc.append("{")
    doc.append('    "ack_time": 1704067500000,')
    doc.append('    "result_sign": "客户端已验证的结果签名",')
    doc.append('    "remark": "确认无误"')
    doc.append("}")
    doc.append("```")
    doc.append("")
    doc.append("### data 字段（解密后）示例")
    doc.append("")
    doc.append("```json")
    doc.append("[")
    doc.append('  { "system_source_id": "17279102", "status": "1", "desc": "" },')
    doc.append('  { "system_source_id": "17279095", "status": "1", "desc": "同步成功" }')
    doc.append("]")
    doc.append("```")
    doc.append("")
    doc.append("### 响应示例")
    doc.append("")
    doc.append("```json")
    doc.append("{")
    doc.append('    "code": 0,')
    doc.append('    "message": "确认接收成功",')
    doc.append('    "data": {')
    doc.append('        "batch_id": "batch_123",')
    doc.append('        "status": "acknowledged",')
    doc.append('        "confirmed_at": 1704067560000')
    doc.append('    }')
    doc.append("}")
    doc.append("```")
    doc.append("")
    
    # 6. 完整调用流程
    doc.append("## 🔄 6. 完整调用流程")
    doc.append("")
    doc.append("### 步骤说明")
    doc.append("")
    doc.append("1. **认证获取令牌**")
    doc.append("   - 调用认证接口获取 `access_token` 和 `data_key`")
    doc.append("   - 保存令牌用于后续接口调用")
    doc.append("")
    doc.append("2. **上传业务数据**")
    doc.append("   - 使用 `data_key` 加密业务数据")
    doc.append("   - 调用数据上传接口，传入 `batch_id`")
    doc.append("   - 可多次调用上传同一批次的不同数据")
    doc.append("")
    doc.append("3. **标记批次完成**")
    doc.append("   - 所有数据上传完成后，调用批次完成接口")
    doc.append("   - 系统开始处理该批次数据")
    doc.append("")
    doc.append("4. **查询处理结果**")
    doc.append("   - 调用结果查询接口获取处理结果")
    doc.append("   - 可轮询查询直到处理完成")
    doc.append("")
    doc.append("5. **确认结果已接收**")
    doc.append("   - 成功获取并校验结果后，调用确认接口")
    doc.append("   - 系统记录确认状态用于对账与重发控制")
    doc.append("")
    
    doc.append("### 流程图")
    doc.append("")
    doc.append("```")
    doc.append("客户端                    API服务")
    doc.append("  |                         |")
    doc.append("  |-- 1. 认证请求 --------->|")
    doc.append("  |<-- access_token --------|")
    doc.append("  |                         |")
    doc.append("  |-- 2. 上传数据 --------->|")
    doc.append("  |<-- 上传成功 ------------|")
    doc.append("  |                         |")
    doc.append("  |-- 3. 标记完成 --------->|")
    doc.append("  |<-- 完成确认 ------------|")
    doc.append("  |                         |")
    doc.append("  |          ... 等待处理 ...|")
    doc.append("  |                         |")
    doc.append("  |<-- 4. 回调通知 ---------|  (处理完成)")
    doc.append("  |                         |")
    doc.append("  |-- 5. 查询结果 --------->|  (收到回调后)")
    doc.append("  |<-- 处理结果 ------------|")
    doc.append("  |                         |")
    doc.append("  |-- 6. 确认接收 --------->|")
    doc.append("  |<-- 确认成功 ------------|")
    doc.append("```")
    doc.append("")
    
    # 7. 回调通知机制
    doc.append("## 🔔 7. 回调通知机制")
    doc.append("")
    doc.append("当批次状态发生变更时，系统会自动向客户端指定的回调地址发送通知。")
    doc.append("")
    doc.append("### 回调触发时机")
    doc.append("- 批次状态变更为 `completed`（处理完成）")
    doc.append("- 批次状态变更为 `failed`（处理失败）")
    doc.append("- 批次状态变更为 `changed`（状态更新）")
    doc.append("")
    doc.append("### 回调请求格式")
    doc.append("")
    doc.append("**请求方式：** `GET`")
    doc.append("")
    doc.append("系统会按照客户端提交的callback_url模板进行回调，自动替换其中的模板变量：")
    doc.append("")
    doc.append("**模板变量：**")
    doc.append("- `{api.api_code}` - API代码")
    doc.append("- `{batch_id}` - 批次ID")
    doc.append("- `{status}` - 处理状态（completed/failed/changed）")
    doc.append("- `{total}` - 总记录数")
    doc.append("- `{success_count}` - 成功处理数量")
    doc.append("- `{failed_count}` - 失败处理数量")
    doc.append("- `{timestamp}` - 状态变更时间戳（Unix时间戳）")
    doc.append("")
    doc.append("### 回调示例")
    doc.append("")
    doc.append("**配置的callback_url：**")
    doc.append("```")
    doc.append("https://client.example.com/callback/{api.api_code}/{batch_id}/{status}/{total}/{success_count}/{failed_count}/{timestamp}")
    doc.append("```")
    doc.append("")
    doc.append("**实际回调请求：**")
    doc.append("```")
    doc.append("GET https://client.example.com/callback/DATA_API_001/batch_20241201_001/completed/1000/980/20/1733024400")
    doc.append("```")
    doc.append("")
    doc.append("### 客户端响应要求")
    doc.append("")
    doc.append("- 客户端应返回HTTP状态码200表示接收成功")
    doc.append("- 响应体内容不做要求，建议返回简单的确认信息")
    doc.append("- 如果回调失败，系统会进行重试（最多3次，间隔递增）")
    doc.append("")
    doc.append("### 客户端实现示例")
    doc.append("")
    doc.append("**Python Flask示例：**")
    doc.append("```python")
    doc.append("from flask import Flask")
    doc.append("")
    doc.append("app = Flask(__name__)")
    doc.append("")
    doc.append("@app.route('/callback/<api_code>/<batch_id>/<status>/<int:total>/<int:success_count>/<int:failed_count>/<int:timestamp>', methods=['GET'])")
    doc.append("def handle_callback(api_code, batch_id, status, total, success_count, failed_count, timestamp):")
    doc.append("    # 从URL路径获取参数")
    doc.append("    print(f'API代码：{api_code}')")
    doc.append("    print(f'批次ID：{batch_id}')")
    doc.append("    print(f'处理状态：{status}')")
    doc.append("    print(f'总记录数：{total}')")
    doc.append("    print(f'成功数量：{success_count}')")
    doc.append("    print(f'失败数量：{failed_count}')")
    doc.append("    print(f'状态变更时间戳：{timestamp}')")
    doc.append("    ")
    doc.append("    # 处理回调通知")
    doc.append("    print(f'收到批次 {batch_id} 状态变更通知：{status}')")
    doc.append("    print(f'处理结果：总数 {total}，成功 {success_count}，失败 {failed_count}')")
    doc.append("    ")
    doc.append("    # 可以在这里触发查询结果的逻辑")
    doc.append("    # query_batch_result(batch_id)")
    doc.append("    ")
    doc.append("    return 'OK', 200")
    doc.append("```")
    doc.append("")
    
    # 8. 业务状态码说明
    doc.append("## 📋 8. 业务状态码说明")
    doc.append("")
    doc.append("所有接口都使用统一的响应格式，包含业务状态码(code)、消息(message)和数据(data)三个字段：")
    doc.append("")
    doc.append("```json")
    doc.append("{")
    doc.append('    "code": 0,        // 业务状态码，0表示成功')
    doc.append('    "message": "...", // 响应消息')
    doc.append('    "data": {...}     // 响应数据，失败时为null')
    doc.append("}")
    doc.append("```")
    doc.append("")
    doc.append("### 常用状态码")
    doc.append("")
    doc.append("| 状态码 | 说明 | 场景 |")
    doc.append("|--------|------|------|")
    doc.append("| 0 | 成功 | 请求处理成功 |")
    doc.append("| 1001 | 认证失败 | 签名验证失败或凭据无效 |")
    doc.append("| 1006 | Token无效或已过期 | 访问令牌失效 |")
    doc.append("| 1007 | 缺少认证令牌 | 请求头缺少Authorization |")
    doc.append("| 1009 | 客户账户已停用 | 客户状态异常 |")
    doc.append("| 2001 | 数据验证失败 | 请求参数格式错误 |")
    doc.append("| 2002 | 数据解密失败 | 数据密钥错误或数据损坏 |")
    doc.append("| 2003 | 数据签名验证失败 | 数据完整性校验失败 |")
    doc.append("| 3001 | 批次不存在 | 指定的批次ID不存在 |")
    doc.append("| 3002 | 批次状态异常 | 批次已完成或处理中 |")
    doc.append("| 4001 | API不存在 | 指定的API不存在 |")
    doc.append("| 5001 | 内部服务器错误 | 系统内部错误 |")
    doc.append("| 5002 | 数据库操作失败 | 数据保存或查询失败 |")
    doc.append("| 5003 | 请求数据过大 | 上传数据超过限制 |")
    doc.append("")
    doc.append("### 错误响应示例")
    doc.append("")
    doc.append("```json")
    doc.append("{")
    doc.append('    "code": 1006,')
    doc.append('    "message": "Token无效或已过期",')
    doc.append('    "data": null')
    doc.append("}")
    doc.append("```")
    doc.append("")
    
    # 9. 注意事项
    doc.append("## ⚠️ 9. 注意事项")
    doc.append("")
    doc.append("### 安全要求")
    doc.append("- 所有接口调用必须使用HTTPS")
    doc.append("- 签名密钥和数据密钥需妥善保管")
    doc.append("- 建议对敏感数据进行加密传输")
    doc.append("")
    
    doc.append("### 性能建议")
    doc.append("- 单次上传数据量建议不超过10MB")
    doc.append("- 批次记录数建议不超过10000条")
    doc.append("- 合理设置请求超时时间")
    doc.append("")
    
    doc.append("### 错误处理")
    doc.append("- 网络异常时建议重试，最多3次")
    doc.append("- 认证失败时需重新获取令牌")
    doc.append("- 详细错误信息请查看响应中的message字段")
    doc.append("")
    
    # 页脚
    doc.append("---")
    doc.append("")
    doc.append("📝 *本文档由系统自动生成，如有疑问请联系技术支持*")
    doc.append("")
    
    return "\n".join(doc)

def _generate_html_doc(api: CustomApi, api_fields: list = None) -> str:
    """
    生成HTML格式的API文档
    """
    
    customer_name = api.customer.name if api.customer else "未知客户"
    
    html_content = f"""
    <!DOCTYPE html>
    <html lang="zh-CN">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{api.api_name} - API文档</title>
        <style>
            body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; line-height: 1.6; color: #333; max-width: 800px; margin: 0 auto; padding: 20px; }}
            h1 {{ color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 10px; }}
            h2 {{ color: #34495e; margin-top: 30px; }}
            .info-table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
            .info-table th, .info-table td {{ border: 1px solid #ddd; padding: 12px; text-align: left; }}
            .info-table th {{ background-color: #f8f9fa; font-weight: 600; }}
            .status-active {{ color: #27ae60; font-weight: bold; }}
            .status-inactive {{ color: #e74c3c; font-weight: bold; }}
            .method-tag {{ display: inline-block; padding: 4px 8px; border-radius: 4px; font-size: 12px; font-weight: bold; color: white; }}
            .method-get {{ background-color: #61affe; }}
            .method-post {{ background-color: #49cc90; }}
            .method-put {{ background-color: #fca130; }}
            .method-delete {{ background-color: #f93e3e; }}
            .description {{ background-color: #f8f9fa; padding: 15px; border-radius: 5px; margin: 15px 0; }}
            .footer {{ margin-top: 40px; padding-top: 20px; border-top: 1px solid #eee; color: #666; font-size: 14px; text-align: center; }}
        </style>
    </head>
    <body>
        <h1>{api.api_name}</h1>
        
        <h2>基本信息</h2>
        <table class="info-table">
            <tr><th>API名称</th><td>{api.api_name}</td></tr>
            <tr><th>API代码</th><td>{api.api_code}</td></tr>
            <tr><th>所属平台</th><td>{customer_name}</td></tr>
            <tr><th>请求方法</th><td><span class="method-tag method-{api.http_method.lower()}">{api.http_method}</span></td></tr>
            <tr><th>接口地址</th><td>{api.api_url or 'N/A'}</td></tr>
            <tr><th>状态</th><td><span class="{'status-active' if api.status == 1 else 'status-inactive'}">{'激活' if api.status == 1 else '禁用'}</span></td></tr>
        </table>
        
        <h2>描述</h2>
        <div class="description">
            {api.api_description or '暂无描述'}
        </div>
        
        <h2>请求和响应格式</h2>
        <table class="info-table">
            <tr><th>请求格式</th><td>{getattr(api, 'request_format', 'json').upper()}</td></tr>
            <tr><th>响应格式</th><td>{api.response_format.upper()}</td></tr>
            <tr><th>认证要求</th><td>{'需要认证' if getattr(api, 'require_authentication', True) else '无需认证'}</td></tr>
        </table>
        
        <h2>调用统计</h2>
        <table class="info-table">
            <tr><th>总调用次数</th><td>{api.total_calls or 0}</td></tr>
            <tr><th>最后调用时间</th><td>{api.last_called_at or '从未调用'}</td></tr>
        </table>
        
        <h2>创建信息</h2>
        <table class="info-table">
            <tr><th>创建时间</th><td>{api.created_at}</td></tr>
            <tr><th>更新时间</th><td>{api.updated_at}</td></tr>
        </table>
        
        <div class="footer">
            <p>此文档由系统自动生成</p>
        </div>
    </body>
    </html>
    """
    
    return html_content

def _generate_openapi_doc(api: CustomApi, api_fields: list = None) -> str:
    """
    生成OpenAPI 3.0格式的API文档
    """
    
    import json
    
    customer_name = api.customer.name if api.customer else "未知客户"
    
    openapi_spec = {
        "openapi": "3.0.0",
        "info": {
            "title": f"{api.api_name}",
            "description": api.api_description or "API描述",
            "version": "1.0.0",
            "contact": {
                "name": customer_name
            }
        },
        "servers": [
            {
                "url": api.api_url or "/api",
                "description": "API服务器"
            }
        ],
        "paths": {
            f"/{api.api_code}": {
                api.http_method.lower(): {
                    "summary": api.api_name,
                    "description": api.api_description or "API描述",
                    "operationId": api.api_code,
                    "tags": [customer_name],
                    "responses": {
                        "200": {
                            "description": "成功响应",
                            "content": {
                                f"application/{api.response_format}": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "code": {
                                                "type": "integer",
                                                "example": 200
                                            },
                                            "message": {
                                                "type": "string",
                                                "example": "success"
                                            },
                                            "data": {
                                                "type": "object",
                                                "description": "响应数据"
                                            }
                                        }
                                    }
                                }
                            }
                        },
                        "400": {
                            "description": "请求错误"
                        },
                        "401": {
                            "description": "未授权"
                        },
                        "500": {
                            "description": "服务器错误"
                        }
                    }
                }
            }
        },
        "components": {
            "securitySchemes": {
                "bearerAuth": {
                    "type": "http",
                    "scheme": "bearer",
                    "bearerFormat": "JWT"
                }
            }
        }
    }
    
    # 如果需要认证，添加安全要求
    if getattr(api, 'require_authentication', True):
        openapi_spec["paths"][f"/{api.api_code}"][api.http_method.lower()]["security"] = [
            {"bearerAuth": []}
        ]
    
    # 如果是POST/PUT请求，添加请求体
    if api.http_method.upper() in ['POST', 'PUT', 'PATCH']:
        openapi_spec["paths"][f"/{api.api_code}"][api.http_method.lower()]["requestBody"] = {
            "required": True,
            "content": {
                f"application/{getattr(api, 'request_format', 'json')}": {
                    "schema": {
                        "type": "object",
                        "properties": {
                            "data": {
                                "type": "object",
                                "description": "请求数据"
                            }
                        }
                    }
                }
            }
        }
    
    return json.dumps(openapi_spec, ensure_ascii=False, indent=2)

@router.get("/stats/batch-status", summary="获取批次状态统计")
async def get_batch_status_stats(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """获取批次状态统计"""
    
    try:
        async for api_db in get_db_session(db_name="api_system"):
            # 统计不同状态的批次数量
            pending_query = select(func.count(DataBatch.id)).where(DataBatch.status == 'pending')
            pending_result = await api_db.execute(pending_query)
            pending_count = pending_result.scalar()
            
            processing_query = select(func.count(DataBatch.id)).where(DataBatch.status == 'processing')
            processing_result = await api_db.execute(processing_query)
            processing_count = processing_result.scalar()
            
            completed_query = select(func.count(DataBatch.id)).where(DataBatch.status == 'completed')
            completed_result = await api_db.execute(completed_query)
            completed_count = completed_result.scalar()
            
            failed_query = select(func.count(DataBatch.id)).where(DataBatch.status == 'failed')
            failed_result = await api_db.execute(failed_query)
            failed_count = failed_result.scalar()
            
            stats = {
                "pending": pending_count,
                "processing": processing_count,
                "completed": completed_count,
                "failed": failed_count
            }
            
            return success_response(stats)
            break
            
    except Exception as e:
        print(f"获取批次状态统计失败: {e}")
        raise HTTPException(status_code=500, detail="数据库连接失败")

@router.get("/stats/api-calls", summary="获取API调用统计")
async def get_api_call_stats(
    start_date: Optional[str] = Query(None, description="开始日期"),
    end_date: Optional[str] = Query(None, description="结束日期"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """获取API调用统计"""
    
    # 模拟7天的数据
    stats = []
    base_date = datetime.now() - timedelta(days=6)
    
    for i in range(7):
        date = base_date + timedelta(days=i)
        stats.append({
            "date": date.strftime("%Y-%m-%d"),
            "calls": 100 + i * 20,
            "success_calls": 95 + i * 18,
            "failed_calls": 5 + i * 2
        })
    
    return success_response(stats)

@router.get("/stats/type-count-trend", summary="获取数据增长趋势(type_count)")
async def get_type_count_trend(
    days: int = Query(90, ge=1, le=365, description="查询天数"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    try:
        start_date = datetime.now().date() - timedelta(days=days - 1)
        dates: List[str] = []
        series_map: dict = {}

        async for api_db in get_db_session(db_name="primary"):
            query = text(
                """
                SELECT `date`, `type_count`
                FROM acwl_type_count
                WHERE `date` >= :start_date
                ORDER BY `date` ASC
                """
            )
            result = await api_db.execute(query, {"start_date": start_date})
            rows = result.fetchall()

        for row in rows:
            d = getattr(row, "date", None)
            tc = getattr(row, "type_count", None)
            if d is None and isinstance(row, (tuple, list)):
                d = row[0]
                tc = row[1]

            if isinstance(d, datetime):
                date_str = d.date().isoformat()
            elif hasattr(d, "isoformat"):
                date_str = d.isoformat()
            else:
                date_str = str(d)
            dates.append(date_str)

            if isinstance(tc, list):
                items = tc
            else:
                try:
                    items = json.loads(tc) if tc else []
                except Exception:
                    items = []

            current_keys = set()
            for item in items:
                key = str(item.get("key", "")).strip()
                count = int(item.get("doc_count", 0) or 0)
                current_keys.add(key)

                if key not in series_map:
                    series_map[key] = [0] * (len(dates) - 1)
                series_map[key].append(count)

            for existing_key in list(series_map.keys()):
                if existing_key not in current_keys:
                    series_map[existing_key].append(0)

        return success_response({"dates": dates, "series": series_map})
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"查询数据增长趋势失败: {e}")

@router.get("/logs/api-usage", summary="获取API使用日志")
async def get_api_usage_logs(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    api_id: Optional[int] = Query(None, description="API ID"),
    customer_id: Optional[int] = Query(None, description="客户ID"),
    status_code: Optional[int] = Query(None, description="HTTP状态码"),
    search: Optional[str] = Query(None, description="搜索关键词"),
    start_date: Optional[str] = Query(None, description="开始日期(YYYY-MM-DD或ISO格式)"),
    end_date: Optional[str] = Query(None, description="结束日期(YYYY-MM-DD或ISO格式)"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """获取API使用日志，支持过滤和分页（兼容实际表结构）"""
    try:
        async for api_db in get_db_session(db_name="api_system"):
            # 构建过滤条件
            where_clauses = []
            params: dict = {
                "offset": (page - 1) * page_size,
                "limit": page_size
            }
            if api_id:
                where_clauses.append("l.api_id = :api_id")
                params["api_id"] = api_id
            if customer_id:
                where_clauses.append("l.customer_id = :customer_id")
                params["customer_id"] = customer_id
            if status_code:
                # 映射前端的 status_code 到实际表字段 response_status
                where_clauses.append("l.response_status = :status_code")
                params["status_code"] = status_code
            if search:
                params["pattern"] = f"%{search}%"
                where_clauses.append(
                    "(l.request_url LIKE :pattern OR l.error_message LIKE :pattern OR l.client_ip LIKE :pattern OR l.user_agent LIKE :pattern)"
                )

            def parse_date(s: Optional[str]) -> Optional[datetime]:
                if not s:
                    return None
                try:
                    return datetime.fromisoformat(s)
                except Exception:
                    try:
                        return datetime.strptime(s, "%Y-%m-%d")
                    except Exception:
                        return None
            start_dt = parse_date(start_date)
            end_dt = parse_date(end_date)
            if start_dt:
                where_clauses.append("l.created_at >= :start_dt")
                params["start_dt"] = start_dt
            if end_dt:
                where_clauses.append("l.created_at <= :end_dt")
                params["end_dt"] = end_dt

            where_sql = (" WHERE " + " AND ".join(where_clauses)) if where_clauses else ""

            # 统计总数
            count_sql = text("SELECT COUNT(*) AS cnt FROM api_usage_logs l" + where_sql)
            total_result = await api_db.execute(count_sql, params)
            total = total_result.scalar() or 0

            # 查询列表（包含客户与API信息）
            select_sql = text(
                """
                SELECT 
                  l.id, l.customer_id, l.api_id,
                  l.request_params, l.response_headers, l.encrypted_data,
                  l.response_status, l.processing_time, l.client_ip, l.user_agent,
                  l.error_message, l.created_at,
                  c.id AS c_id, c.name AS c_name, c.company AS c_company, c.email AS c_email,
                  a.id AS a_id, a.api_name AS a_api_name, a.api_code AS a_api_code, a.api_url AS a_api_url, a.http_method AS a_http_method
                FROM api_usage_logs l
                LEFT JOIN customers c ON l.customer_id = c.id
                LEFT JOIN custom_apis a ON l.api_id = a.id
                """ + where_sql + " ORDER BY l.created_at DESC LIMIT :offset, :limit"
            )
            rows = await api_db.execute(select_sql, params)
            results = rows.fetchall()

            items = []
            import json
            for r in results:
                # 处理请求数据与响应数据的展示
                req_params = getattr(r, "request_params", None)
                if isinstance(req_params, (dict, list)):
                    request_data = json.dumps(req_params, ensure_ascii=False)
                else:
                    request_data = req_params

                encrypted_data = getattr(r, "encrypted_data", None)
                response_data = None
                if encrypted_data is not None:
                    try:
                        response_data = str(encrypted_data)
                        if len(response_data) > 1000:
                            response_data = response_data[:1000] + "..."
                    except Exception:
                        response_data = None

                processing = getattr(r, "processing_time", 0) or 0
                response_time_ms = int(float(processing) * 1000)

                item = {
                    "id": getattr(r, "id", None),
                    "customer_id": getattr(r, "customer_id", None),
                    "api_id": getattr(r, "api_id", None),
                    "request_data": request_data,
                    "response_data": response_data,
                    "status_code": getattr(r, "response_status", None),
                    "response_time": response_time_ms,
                    "ip_address": getattr(r, "client_ip", None),
                    "user_agent": getattr(r, "user_agent", None),
                    "error_message": getattr(r, "error_message", None),
                    "created_at": r.created_at.isoformat() if getattr(r, "created_at", None) else None,
                    "customer": None,
                    "api": None
                }

                if getattr(r, "c_id", None):
                    item["customer"] = {
                        "id": getattr(r, "c_id", None),
                        "name": getattr(r, "c_name", None),
                        "company": getattr(r, "c_company", None),
                        "email": getattr(r, "c_email", None)
                    }
                if getattr(r, "a_id", None):
                    item["api"] = {
                        "id": getattr(r, "a_id", None),
                        "api_name": getattr(r, "a_api_name", None),
                        "api_code": getattr(r, "a_api_code", None),
                        "endpoint_url": getattr(r, "a_api_url", None),
                        "http_method": getattr(r, "a_http_method", None)
                    }

                items.append(item)

            total_pages = (total + page_size - 1) // page_size
            return success_response({
                "items": items,
                "total": total,
                "page": page,
                "page_size": page_size,
                "total_pages": total_pages
            })
    except Exception as e:
        print(f"获取API使用日志失败: {e}")
        raise HTTPException(status_code=500, detail="获取API使用日志失败")

@router.get("/logs/data-uploads", summary="获取数据上传记录")
async def get_data_upload_logs(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    batch_id: Optional[int] = Query(None, description="批次ID"),
    customer_id: Optional[int] = Query(None, description="客户ID"),
    upload_status: Optional[str] = Query(None, description="上传状态(uploading/completed/failed)"),
    search: Optional[str] = Query(None, description="搜索文件名关键词"),
    start_date: Optional[str] = Query(None, description="开始日期(YYYY-MM-DD或ISO格式)"),
    end_date: Optional[str] = Query(None, description="结束日期(YYYY-MM-DD或ISO格式)"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """获取数据上传记录，支持过滤和分页"""
    try:
        async for api_db in get_db_session(db_name="api_system"):
            query = select(DataUpload).options(
                selectinload(DataUpload.customer),
                selectinload(DataUpload.batch)
            )
            count_query = select(func.count(DataUpload.id))

            conditions = []
            if batch_id:
                conditions.append(DataUpload.batch_id == batch_id)
            if customer_id:
                conditions.append(DataUpload.customer_id == customer_id)
            if upload_status:
                conditions.append(DataUpload.upload_status == upload_status)
            if search:
                conditions.append(DataUpload.file_name.like(f"%{search}%"))

            def parse_date(s: Optional[str]) -> Optional[datetime]:
                if not s:
                    return None
                try:
                    return datetime.fromisoformat(s)
                except Exception:
                    try:
                        return datetime.strptime(s, "%Y-%m-%d")
                    except Exception:
                        return None
            start_dt = parse_date(start_date)
            end_dt = parse_date(end_date)
            if start_dt:
                conditions.append(DataUpload.created_at >= start_dt)
            if end_dt:
                conditions.append(DataUpload.created_at <= end_dt)

            if conditions:
                query = query.where(and_(*conditions))
                count_query = count_query.where(and_(*conditions))

            total_result = await api_db.execute(count_query)
            total = total_result.scalar() or 0

            query = query.order_by(DataUpload.created_at.desc())\
                .offset((page - 1) * page_size)\
                .limit(page_size)
            uploads_result = await api_db.execute(query)
            uploads = uploads_result.scalars().all()

            items = []
            for up in uploads:
                item = {
                    "id": up.id,
                    "customer_id": up.customer_id,
                    "batch_id": up.batch_id,
                    "file_name": up.file_name,
                    "file_size": up.file_size,
                    "file_type": up.file_type,
                    "file_path": up.file_path,
                    "upload_status": up.upload_status,
                    "error_message": up.error_message,
                    "created_at": up.created_at.isoformat() if getattr(up, "created_at", None) else None,
                    "updated_at": up.updated_at.isoformat() if getattr(up, "updated_at", None) else None
                }
                if getattr(up, "customer", None):
                    item["customer"] = {
                        "id": getattr(up.customer, "id", None),
                        "name": getattr(up.customer, "name", None),
                        "company": getattr(up.customer, "company", None),
                        "email": getattr(up.customer, "email", None)
                    }
                if getattr(up, "batch", None):
                    item["batch"] = {
                        "id": getattr(up.batch, "id", None),
                        "batch_name": getattr(up.batch, "batch_name", None),
                        "status": getattr(up.batch, "status", None),
                        "total_records": getattr(up.batch, "total_records", 0),
                        "processed_records": getattr(up.batch, "processed_records", 0),
                        "failed_records": getattr(up.batch, "failed_records", 0),
                        "created_at": up.batch.created_at.isoformat() if getattr(up.batch, "created_at", None) else None
                    }
                items.append(item)

            total_pages = (total + page_size - 1) // page_size
            return success_response({
                "items": items,
                "total": total,
                "page": page,
                "page_size": page_size,
                "total_pages": total_pages
            })
            break
    except Exception as e:
        print(f"获取数据上传记录失败: {e}")
        raise HTTPException(status_code=500, detail="获取数据上传记录失败")

@router.get("/stats/customer-activity", summary="获取客户活跃度统计")
async def get_customer_activity_stats(
    limit: int = Query(10, description="返回数量"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """获取客户活跃度统计"""
    
    try:
        async for api_db in get_db_session(db_name="api_system"):
            # 按API调用次数排序获取客户
            query = select(Customer).order_by(desc(Customer.total_api_calls)).limit(limit)
            result = await api_db.execute(query)
            customers = result.scalars().all()
            
            stats = []
            for customer in customers:
                stats.append({
                    "customer_name": customer.name,
                    "api_calls": customer.total_api_calls or 0,
                    "last_call_date": customer.last_api_call_at.isoformat() if customer.last_api_call_at else customer.created_at.isoformat()
                })
            
            return success_response(stats)
            break
            
    except Exception as e:
        print(f"获取客户活跃度统计失败: {e}")
        raise HTTPException(status_code=500, detail="数据库连接失败")


# ==================== API字段管理 ====================

@router.get("/apis/{api_id}/fields", summary="获取API字段列表")
async def get_api_fields(api_id: int):
    """
    获取指定API的字段列表
    
    Args:
        api_id: API ID
        
    Returns:
        API字段列表
    """
    try:
        async for api_db in get_db_session(db_name="api_system"):
            # 检查API是否存在
            api_query = select(CustomApi).where(CustomApi.id == api_id)
            api_result = await api_db.execute(api_query)
            api = api_result.scalar_one_or_none()
            
            if not api:
                raise HTTPException(status_code=404, detail="API不存在")
            
            # 获取字段列表
            fields_query = select(ApiField).where(ApiField.api_id == api_id).order_by(ApiField.sort_order)
            fields_result = await api_db.execute(fields_query)
            fields = fields_result.scalars().all()
            
            # 转换为字典格式
            items = []
            for field in fields:
                items.append({
                    "id": field.id,
                    "api_id": field.api_id,
                    "field_name": field.field_name,
                    "field_type": field.field_type,
                    "is_required": field.is_required,
                    "is_upload": getattr(field, 'is_upload', 0),
                    "default_value": field.default_value,
                    "description": field.description,
                    "sort_order": field.sort_order,
                    "created_at": field.created_at.isoformat() if field.created_at else None,
                    "updated_at": field.updated_at.isoformat() if field.updated_at else None
                })
            
            return success_response({
                "items": items,
                "total": len(items),
                "page": 1,
                "page_size": len(items)
            })
            break
            
    except HTTPException:
        raise
    except Exception as e:
        print(f"获取API字段列表失败: {e}")
        raise HTTPException(status_code=500, detail="数据库连接失败")


@router.post("/apis/{api_id}/fields", summary="创建API字段")
async def create_api_field(
    api_id: int,
    field_data: ApiFieldCreate
):
    """
    为指定API创建新字段
    
    Args:
        api_id: API ID
        field_data: 字段创建数据，包含字段名称、类型、是否必填等信息
        
    Returns:
        创建的字段信息
    """
    try:
        async for api_db in get_db_session(db_name="api_system"):
            # 检查API是否存在
            api_query = select(CustomApi).where(CustomApi.id == api_id)
            api_result = await api_db.execute(api_query)
            api = api_result.scalar_one_or_none()
            
            if not api:
                raise HTTPException(status_code=404, detail="API不存在")
            
            # 检查字段名是否已存在
            existing_field_query = select(ApiField).where(
                ApiField.api_id == api_id,
                ApiField.field_name == field_data.field_name
            )
            existing_field_result = await api_db.execute(existing_field_query)
            existing_field = existing_field_result.scalar_one_or_none()
            
            if existing_field:
                raise HTTPException(status_code=400, detail="字段名已存在")
            
            # 创建新字段
            new_field = ApiField(
                api_id=api_id,
                field_name=field_data.field_name,
                field_label=field_data.field_label or field_data.field_name,  # 如果没有提供 field_label，使用 field_name
                field_type=field_data.field_type,
                is_required=field_data.is_required,
                is_upload=getattr(field_data, 'is_upload', 0),
                default_value=field_data.default_value,
                description=field_data.description,
                sort_order=field_data.sort_order,
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            
            api_db.add(new_field)
            await api_db.commit()
            await api_db.refresh(new_field)
            
            # 清除相关缓存
            invalidate_api_fields_cache(api_id)
            
            return success_response({
                "id": new_field.id,
                "api_id": new_field.api_id,
                "field_name": new_field.field_name,
                "field_label": new_field.field_label,
                "field_type": new_field.field_type,
                "is_required": new_field.is_required,
                "is_upload": getattr(new_field, 'is_upload', 0),
                "default_value": new_field.default_value,
                "description": new_field.description,
                "sort_order": new_field.sort_order,
                "created_at": new_field.created_at.isoformat() if new_field.created_at else None,
                "updated_at": new_field.updated_at.isoformat() if new_field.updated_at else None
            })
            break
            
    except HTTPException:
        raise
    except Exception as e:
        print(f"创建API字段失败: {e}")
        raise HTTPException(status_code=500, detail="数据库连接失败")


@router.get("/apis/{api_id}/fields/{field_id}", summary="获取API字段详情")
async def get_api_field(api_id: int, field_id: int):
    """
    获取指定API字段的详细信息
    
    Args:
        api_id: API ID
        field_id: 字段ID
        
    Returns:
        字段详细信息
    """
    try:
        async for api_db in get_db_session(db_name="api_system"):
            # 查询字段
            field_query = select(ApiField).where(
                ApiField.id == field_id,
                ApiField.api_id == api_id
            )
            field_result = await api_db.execute(field_query)
            field = field_result.scalar_one_or_none()
            
            if not field:
                raise HTTPException(status_code=404, detail="字段不存在")
            
            return success_response({
                "id": field.id,
                "api_id": field.api_id,
                "field_name": field.field_name,
                "field_type": field.field_type,
                "is_required": field.is_required,
                "default_value": field.default_value,
                "description": field.description,
                "sort_order": field.sort_order,
                "created_at": field.created_at.isoformat() if field.created_at else None,
                "updated_at": field.updated_at.isoformat() if field.updated_at else None
            })
            break
            
    except HTTPException:
        raise
    except Exception as e:
        print(f"获取API字段详情失败: {e}")
        raise HTTPException(status_code=500, detail="数据库连接失败")


@router.put("/apis/{api_id}/fields/{field_id}", summary="更新API字段")
async def update_api_field(
    api_id: int,
    field_id: int,
    field_data: ApiFieldUpdate
):
    """
    更新指定API字段
    
    Args:
        api_id: API ID
        field_id: 字段ID
        field_data: 字段更新数据
        
    Returns:
        更新后的字段信息
    """
    try:
        async for api_db in get_db_session(db_name="api_system"):
            # 查询字段
            field_query = select(ApiField).where(
                ApiField.id == field_id,
                ApiField.api_id == api_id
            )
            field_result = await api_db.execute(field_query)
            field = field_result.scalar_one_or_none()
            
            if not field:
                raise HTTPException(status_code=404, detail="字段不存在")
            
            # 更新字段信息
            if field_data.field_name is not None:
                field.field_name = field_data.field_name
            if field_data.field_type is not None:
                field.field_type = field_data.field_type
            if field_data.is_required is not None:
                field.is_required = field_data.is_required
            # 是否上传：1 为勾选，0 为不勾选
            if getattr(field_data, 'is_upload', None) is not None:
                field.is_upload = field_data.is_upload
            if field_data.default_value is not None:
                field.default_value = field_data.default_value
            if field_data.description is not None:
                field.description = field_data.description
            if field_data.sort_order is not None:
                field.sort_order = field_data.sort_order
            
            field.updated_at = datetime.now()
            
            await api_db.commit()
            await api_db.refresh(field)
            
            # 清除相关缓存
            invalidate_api_fields_cache(api_id)
            
            return success_response({
                "id": field.id,
                "api_id": field.api_id,
                "field_name": field.field_name,
                "field_type": field.field_type,
                "is_required": field.is_required,
                "is_upload": getattr(field, 'is_upload', 0),
                "default_value": field.default_value,
                "description": field.description,
                "sort_order": field.sort_order,
                "created_at": field.created_at.isoformat() if field.created_at else None,
                "updated_at": field.updated_at.isoformat() if field.updated_at else None
            })
            break
            
    except HTTPException:
        raise
    except Exception as e:
        print(f"更新API字段失败: {e}")
        raise HTTPException(status_code=500, detail="数据库连接失败")


@router.delete("/apis/{api_id}/fields/{field_id}", summary="删除API字段")
async def delete_api_field(api_id: int, field_id: int):
    """
    删除指定API字段
    
    Args:
        api_id: API ID
        field_id: 字段ID
        
    Returns:
        操作结果
    """
    try:
        async for api_db in get_db_session(db_name="api_system"):
            # 查询字段
            field_query = select(ApiField).where(
                ApiField.id == field_id,
                ApiField.api_id == api_id
            )
            field_result = await api_db.execute(field_query)
            field = field_result.scalar_one_or_none()
            
            if not field:
                raise HTTPException(status_code=404, detail="字段不存在")
            
            # 删除字段
            await api_db.delete(field)
            await api_db.commit()
            
            # 清除相关缓存
            invalidate_api_fields_cache(api_id)
            
            return success_response({"message": "字段删除成功"})
            break
            
    except HTTPException:
        raise
    except Exception as e:
        print(f"删除API字段失败: {e}")
        raise HTTPException(status_code=500, detail="数据库连接失败")

@router.post("/apis/{api_id}/field-mapping", summary="保存API字段映射")
async def save_api_field_mapping(
    api_id: int,
    payload: dict
):
    """
    保存API字段到数据表字段的映射关系
    
    请求体包含：
    - datasource_id: 数据源ID
    - schema: Schema名称（可选）
    - table: 表名称
    - mappings: 映射关系 { 源字段: 目标字段 }
    """
    try:
        async for api_db in get_db_session(db_name="api_system"):
            api_query = select(CustomApi).where(CustomApi.id == api_id)
            api_result = await api_db.execute(api_query)
            api = api_result.scalar_one_or_none()
            if not api:
                raise HTTPException(status_code=404, detail="API不存在")
            
            # 目前仅校验并回传成功，后续可将映射持久化到专用表
            # 校验基本字段
            if not payload or "datasource_id" not in payload or "table" not in payload or "mappings" not in payload:
                raise HTTPException(status_code=400, detail="请求参数不完整")
            
            # 简要校验映射格式
            mappings = payload.get("mappings", {})
            if not isinstance(mappings, dict):
                raise HTTPException(status_code=400, detail="mappings 必须为对象")
            
            return success_response({"saved": True, "api_id": api_id})
            break
    except HTTPException:
        raise
    except Exception as e:
        print(f"保存字段映射失败: {e}")
        raise HTTPException(status_code=500, detail="数据库连接失败")

@router.get("/resource-types", summary="获取资源类型列表")
async def get_resource_types():
    """
    获取资源类型列表，用于API创建时选择
    
    Returns:
        资源类型列表
    """
    try:
        async for db in get_db_session(db_name="primary"):
            # 查询所有资源类型
            query = select(DataResourceType).order_by(DataResourceType.name)
            result = await db.execute(query)
            resource_types = result.scalars().all()
            
            # 构造返回数据
            resource_type_list = []
            for rt in resource_types:
                resource_type_list.append({
                    "id": rt.id,
                    "name": rt.name,
                    "describe": rt.describe,
                    "metadata": rt.meta  # 使用meta属性而不是metadata
                })
            
            return success_response({
                "resource_types": resource_type_list,
                "total": len(resource_type_list)
            })
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取资源类型列表失败: {str(e)}")


async def _create_fields_from_resource_type(api_db: AsyncSession, api_id: int, resource_type_id: int):
    """
    从资源类型的metadata字段中解析并创建API字段
    
    Args:
        api_db: API数据库会话
        api_id: API ID
        resource_type_id: 资源类型ID
    """
    try:
        # 从主数据库获取资源类型的metadata
        async for primary_db in get_db_session(db_name="primary"):
            resource_type_query = select(DataResourceType).where(DataResourceType.id == resource_type_id)
            resource_type_result = await primary_db.execute(resource_type_query)
            resource_type = resource_type_result.scalar_one_or_none()
            
            if not resource_type or not resource_type.meta:
                return
            
            # 解析metadata JSON
            metadata_fields = resource_type.meta
            if isinstance(metadata_fields, str):
                import json
                metadata_fields = json.loads(metadata_fields)
            
            # 为每个字段创建API字段
            sort_order = 1
            for field_info in metadata_fields:
                field_name = field_info.get("key")
                field_type = field_info.get("type", "string")
                is_required = field_info.get("required", False)
                description = field_info.get("description", "")
                
                if not field_name:
                    continue
                
                # 检查字段是否已存在
                existing_field_query = select(ApiField).where(
                    ApiField.api_id == api_id,
                    ApiField.field_name == field_name
                )
                existing_field_result = await api_db.execute(existing_field_query)
                existing_field = existing_field_result.scalar_one_or_none()
                
                if existing_field:
                    continue  # 跳过已存在的字段
                
                # 创建新字段
                new_field = ApiField(
                    api_id=api_id,
                    field_name=field_name,
                    field_label=field_name,
                    field_type=field_type,
                    is_required=is_required,
                    # 新创建的API字段默认可上传
                    is_upload=1,
                    description=description,
                    sort_order=sort_order,
                    created_at=datetime.now(),
                    updated_at=datetime.now()
                )
                
                api_db.add(new_field)
                sort_order += 1
            
            await api_db.commit()
            
    except Exception as e:
        # 如果字段创建失败，记录错误但不影响API创建
        print(f"创建字段时出错: {str(e)}")
        await api_db.rollback()
