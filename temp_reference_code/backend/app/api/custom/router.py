#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
自定义API路由器

提供动态生成的自定义API路由功能。

Author: System
Date: 2024
"""

from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.orm import Session
from typing import Dict, Any

from app.core.database import get_db
from app.services.api import custom_api_service
from app.services.auth import AuthService
from app.schemas.base import BaseResponse
from app.models.api import CustomApi
from app.core.business_codes import BusinessException, BusinessCode

# 创建自定义API路由器
custom_api_router = APIRouter(
    tags=["custom-api"]
)

# 服务实例
api_service = custom_api_service
auth_service = AuthService()


@custom_api_router.api_route(
    "/api/{api_code}",
    methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
    summary="动态自定义API"
)
async def handle_custom_api(
    api_code: str,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    处理自定义API请求
    
    根据API代码动态处理不同的自定义API请求。
    
    Args:
        api_code: API代码
        request: 请求对象
        db: 数据库会话
        
    Returns:
        API响应结果
    """
    try:
        # 获取API配置 - 需要遍历所有客户来查找API
        # 由于只提供了api_code，我们需要在所有客户中查找
        api_config = db.query(CustomApi).filter(
            CustomApi.api_code == api_code
        ).first()
        
        if not api_config:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"API '{api_code}' 不存在"
            )
        
        # 检查API状态
        if not api_config.status:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"API '{api_code}' 已停用"
            )
        
        # 验证HTTP方法
        if request.method != api_config.http_method:
            raise HTTPException(
                status_code=status.HTTP_405_METHOD_NOT_ALLOWED,
                detail=f"API '{api_code}' 不支持 {request.method} 方法"
            )
        
        # 处理认证（如果需要）
        customer_id = None
        batch_id = None
        
        if api_config.require_authentication:
            # 获取Authorization头
            authorization = request.headers.get("Authorization")
            if not authorization:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="缺少Authorization头"
                )
            
            # 获取平台信息
            from app.api.v1.endpoints.data import get_current_customer
            try:
                customer_info = get_current_customer(authorization)
                customer_id = customer_info["customer_id"]
            except HTTPException:
                raise
            except Exception as e:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="认证失败"
                )
        
        # 获取请求数据
        if request.method in ["POST", "PUT", "PATCH"]:
            try:
                request_data = await request.json()
            except Exception:
                request_data = {}
        else:
            request_data = dict(request.query_params)
        
        # 从请求数据中提取batch_id（如果存在）
        batch_id = request_data.get("batch_id")

        
        
        # 验证请求数据（根据字段定义）
        validated_data = api_service.validate_request_data(
            db, api_config.id, request_data
        )
        
        # 处理API逻辑（这里可以根据需要扩展）
        result = api_service.process_custom_api(
            db, api_config, validated_data, customer_id, batch_id
        )
        
        # # 记录API调用
        # api_service.log_api_call(
        #     db,
        #     api_config.id,
        #     request.client.host if request.client else None,
        #     request_data,
        #     result,
        #     True
        # )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        from app.core.exceptions import ValidationException, CustomException
        
        # 记录错误到日志
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"处理自定义API请求时发生错误: {str(e)}", exc_info=True)
        
        # 记录错误
        # if 'api_config' in locals():
        #     api_service.log_api_call(
        #         db,
        #         api_config.id,
        #         request.client.host if request.client else None,
        #         request_data if 'request_data' in locals() else {},
        #         {"error": str(e)},
        #         False
        #     )
        
        # 如果是ValidationException或其他CustomException，直接抛出让全局异常处理器处理
        if isinstance(e, CustomException):
            raise e
        
        # 其他异常抛出为500错误
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"处理API请求时发生错误: {str(e)}"
        )


@custom_api_router.get("/", response_model=BaseResponse, summary="自定义API根路径")
async def custom_api_root():
    """
    自定义API根路径
    
    Returns:
        基础响应信息
    """
    return BaseResponse(
        success=True,
        message="自定义API服务正常运行"
    )