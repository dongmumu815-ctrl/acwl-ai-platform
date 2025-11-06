#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
用户操作日志查询接口
提供分页查询与详情查询
"""
from typing import Optional, List, Dict, Any
from datetime import datetime

from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from ....core.response import success_response, paginated_response
from ....core.database import get_db as get_async_db
from .auth import get_current_user
from ....models.user import User

router = APIRouter()


def parse_date(s: Optional[str]) -> Optional[datetime]:
    """将字符串解析为datetime，支持ISO格式"""
    if not s:
        return None
    try:
        # 支持 "YYYY-MM-DD" 或 ISO 字符串
        return datetime.fromisoformat(s)
    except Exception:
        return None


@router.get("/", summary="用户操作日志分页查询")
@router.get("/", response_model=Dict[str, Any])
async def list_user_operation_logs(
    current_user: User = Depends(get_current_user),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    keyword: Optional[str] = Query(None),
    method: Optional[str] = Query(None),
    path: Optional[str] = Query(None),
    status_code: Optional[int] = Query(None),
    result_status: Optional[str] = Query(None),  # 'success' or 'failure'
    ip_address: Optional[str] = Query(None),
    module: Optional[str] = Query(None),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    db: AsyncSession = Depends(get_async_db),
):
    """查询用户操作日志列表"""
    where_clauses: List[str] = []
    params: Dict[str, Any] = {}
    # 新增：动态检测可用字段，兼容不同版本的表结构
    columns_result = await db.execute(text(
        "SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'user_operation_logs'"
    ))
    available_columns = {row[0] for row in columns_result.fetchall()}

    where_clauses = []
    if method and 'method' in available_columns:
        where_clauses.append("method = :method")
        params["method"] = method
    if path and 'path' in available_columns:
        where_clauses.append("path LIKE :path")
        params["path"] = f"%{path}%"
    # 状态码过滤：兼容 response_status 字段
    if status_code is not None:
        if 'status_code' in available_columns:
            where_clauses.append("status_code = :status_code")
            params["status_code"] = status_code
        elif 'response_status' in available_columns:
            where_clauses.append("response_status = :status_code")
            params["status_code"] = status_code
    # 结果过滤：优先 result_status；若不存在则使用 success 字段
    if result_status:
        if 'result_status' in available_columns:
            where_clauses.append("result_status = :result_status")
            params["result_status"] = result_status
        elif 'success' in available_columns:
            where_clauses.append("success = :success_val")
            params["success_val"] = 1 if result_status == 'success' else 0
    # IP过滤：兼容 ip 字段
    if ip_address:
        if 'ip_address' in available_columns:
            where_clauses.append("ip_address = :ip_address")
            params["ip_address"] = ip_address
        elif 'ip' in available_columns:
            where_clauses.append("ip = :ip_address")
            params["ip_address"] = ip_address
    # 模块过滤（可选字段）
    if module and 'module' in available_columns:
        where_clauses.append("module LIKE :module")
        params["module"] = f"%{module}%"

    # 关键字搜索：用户名 / 路径 / 请求ID
    if keyword:
        keyword_clauses = []
        if 'username' in available_columns:
            keyword_clauses.append("username LIKE :kw")
        if 'path' in available_columns:
            keyword_clauses.append("path LIKE :kw")
        if 'request_id' in available_columns:
            keyword_clauses.append("request_id LIKE :kw")
        if keyword_clauses:
            where_clauses.append("(" + " OR ".join(keyword_clauses) + ")")
            params["kw"] = f"%{keyword}%"

    # 日期范围：需要 created_at 字段存在
    if start_date and 'created_at' in available_columns:
        where_clauses.append("created_at >= :start_date")
        params["start_date"] = start_date
    if end_date and 'created_at' in available_columns:
        where_clauses.append("created_at <= :end_date")
        params["end_date"] = end_date

    where_sql = " WHERE " + " AND ".join(where_clauses) if where_clauses else ""

    # 统计总数
    count_sql = text("SELECT COUNT(*) AS cnt FROM user_operation_logs" + where_sql)
    count_res = await db.execute(count_sql, params)
    total = count_res.scalar() or 0

    # 选择可用字段进行查询
    select_fields = ["id"]
    for col in [
        "request_id",
        "user_id",
        "username",
        "method",
        "path",
        "status_code",
        "result_status",
        "ip_address",
        "duration_ms",
        "created_at",
    ]:
        if col in available_columns:
            select_fields.append(col)

    order_col = "created_at" if "created_at" in available_columns else "id"
    offset = (page - 1) * size
    # 使用数字字面量避免驱动对占位符的处理问题，且改用 SELECT * 规避列缺失
    select_sql = text(
        f"SELECT * FROM user_operation_logs{where_sql} ORDER BY {order_col} DESC LIMIT {int(size)} OFFSET {int(offset)}"
    )
    result = await db.execute(select_sql, params)
    rows = result.mappings().all()

    # 将结果标准化为统一结构，缺失字段置为 None
    items = []
    for r in rows:
        # 优先使用success字段，如果不存在则使用result_status
        success_value = r.get("success")
        result_status_value = r.get("result_status")
        
        # 根据success字段值确定result_status
        if success_value is not None:
            if success_value == 1 or success_value == "1" or success_value is True:
                final_result_status = "success"
            else:
                final_result_status = "failure"
        elif result_status_value is not None:
            final_result_status = result_status_value
        else:
            final_result_status = None
            
        items.append({
            "id": r.get("id"),
            "request_id": r.get("request_id"),
            "user_id": r.get("user_id"),
            "username": r.get("username"),
            "method": r.get("method"),
            "path": r.get("path"),
            "status_code": r.get("status_code") or r.get("response_status"),
            "result_status": final_result_status,
            "ip_address": r.get("ip_address") or r.get("ip"),
            "duration_ms": r.get("duration_ms"),
            "created_at": r.get("created_at"),
            # 新增字段
            "module": r.get("module"),
            "response_status": r.get("response_status"),
            "server_host": r.get("server_host"),
            "user_agent": r.get("user_agent"),
            "referer": r.get("referer"),
            "request_size": r.get("request_size"),
            "response_size": r.get("response_size"),
            "session_id": r.get("session_id"),
            "trace_id": r.get("trace_id"),
        })

    return {
        "total": total,
        "page": page,
        "size": size,
        "items": items,
    }


@router.get("/{log_id}", summary="用户操作日志详情")
async def get_user_operation_log_detail(
    log_id: int,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user)
):
    """根据日志ID获取详情"""
    # 主记录
    main_sql = text("SELECT * FROM user_operation_logs WHERE id = :id")
    main_row = (await db.execute(main_sql, {"id": log_id})).mappings().fetchone()
    if not main_row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="日志不存在")

    data = {
        "log": {
            "id": main_row.get("id"),
            "request_id": main_row.get("request_id"),
            "user_id": main_row.get("user_id"),
            "username": main_row.get("username"),
            "method": main_row.get("method"),
            "path": main_row.get("path"),
            "response_status": main_row.get("response_status"),
            "success": main_row.get("success"),
            "ip": main_row.get("ip"),
            "duration_ms": main_row.get("duration_ms"),
            "created_at": main_row.get("created_at"),
            # 新增字段
            "module": main_row.get("module"),
            "action_type": main_row.get("action_type"),
            "action_name": main_row.get("action_name"),
            "resource_type": main_row.get("resource_type"),
            "resource_id": main_row.get("resource_id"),
            "resource_name": main_row.get("resource_name"),
            "server_host": main_row.get("server_host"),
            "user_agent": main_row.get("user_agent"),
            "referrer": main_row.get("referrer"),
            "session_id": main_row.get("session_id"),
            "trace_id": main_row.get("trace_id"),
            "env": main_row.get("env"),
            "error_code": main_row.get("error_code"),
        },
        "detail": None
    }

    # 详情信息直接从主表获取
    if main_row:
        data["detail"] = {
            "request_query": main_row.get("request_query"),
            "request_body": main_row.get("request_body"),
            "before_data": main_row.get("before_data"),
            "after_data": main_row.get("after_data"),
            "extra": main_row.get("extra"),
            "error_message": main_row.get("error_message"),
            "exception_stack": main_row.get("exception_stack"),
            "created_at": main_row.get("created_at"),
        }
 
    return data


@router.post("/ui-event")
async def log_ui_event():
    """前端UI埋点事件接收
    该接口不做业务处理，仅用于让中间件记录请求与请求体。
    返回统一结构，便于前端封装器处理。
    """
    return {
        "success": True,
        "data": {"ok": True},
        "message": "UI event received"
    }