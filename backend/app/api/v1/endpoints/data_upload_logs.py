#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据上传日志（Doris）接口

提供从 Doris 数据库读取同步日志表 `logs_data_sync` 的分页查询。
"""

from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Query
from app.core.config import settings
from app.core.response import paginated_response, error_response
import aiomysql

router = APIRouter()


async def _query_doris_logs(
    page: int,
    size: int,
    sort_by: str = "sync_start_time",
    order: str = "desc",
    start_time: Optional[str] = None,
    end_time: Optional[str] = None,
    batch_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    查询 Doris 中的日志数据
    """
    # 计算分页偏移量
    offset = (page - 1) * size

    # 安全的排序处理（白名单）
    allowed_sort_fields = {
        "sync_start_time",
        "sync_end_time",
        "total_data_count",
        "success_data_count",
        "failed_data_count",
        "create_time",
        "update_time"
    }
    sort_field = sort_by if sort_by in allowed_sort_fields else "sync_start_time"
    sort_order = "DESC" if order.lower() == "desc" else "ASC"

    # 过滤条件构建
    where_clauses = []
    params: List[Any] = []

    if batch_id:
        where_clauses.append("batch_id = %s")
        params.append(batch_id)

    if start_time and end_time:
        where_clauses.append("sync_start_time BETWEEN %s AND %s")
        params.extend([start_time, end_time])
    elif start_time:
        where_clauses.append("sync_start_time >= %s")
        params.append(start_time)
    elif end_time:
        where_clauses.append("sync_start_time <= %s")
        params.append(end_time)

    where_sql = f" WHERE {' AND '.join(where_clauses)}" if where_clauses else ""

    # 基础查询语句
    base_select = (
        "SELECT id, batch_id, data_source_name, platform_name, target_table_name, "
        "target_table_desc, need_review, resource_type, sync_start_time, sync_end_time, "
        "total_data_count, success_data_count, failed_data_count, sync_status, failure_reason, "
        "retry_upload, encryption_method, operator, sync_log, create_time, update_time "
        "FROM logs_data_sync" +
        where_sql +
        f" ORDER BY {sort_field} {sort_order} "
        "LIMIT %s OFFSET %s"
    )

    count_sql = "SELECT COUNT(*) AS total FROM logs_data_sync" + where_sql

    # 连接 Doris（MySQL 协议）
    connection = await aiomysql.connect(
        host=settings.DORIS_HOST,
        port=settings.DORIS_PORT,
        user=settings.DORIS_USER,
        password=settings.DORIS_PASSWORD,
        db=settings.DORIS_DATABASE,
        charset="utf8mb4"
    )

    try:
        async with connection.cursor(aiomysql.DictCursor) as cursor:
            # 查询总数
            await cursor.execute(count_sql, params)
            count_row = await cursor.fetchone()
            total = int(count_row.get("total", 0)) if count_row else 0

            # 查询分页数据
            await cursor.execute(base_select, (*params, size, offset))
            rows = await cursor.fetchall()

            items: List[Dict[str, Any]] = []
            for row in rows:
                # 转换成前端友好的结构（保持字段名一致）
                items.append({
                    "id": row.get("id"),
                    "batch_id": row.get("batch_id"),
                    "data_source_name": row.get("data_source_name"),
                    "platform_name": row.get("platform_name"),
                    "target_table_name": row.get("target_table_name"),
                    "target_table_desc": row.get("target_table_desc"),
                    "need_review": row.get("need_review"),
                    "resource_type": row.get("resource_type"),
                    "sync_start_time": row.get("sync_start_time"),
                    "sync_end_time": row.get("sync_end_time"),
                    "total_data_count": row.get("total_data_count"),
                    "success_data_count": row.get("success_data_count"),
                    "failed_data_count": row.get("failed_data_count"),
                    "sync_status": row.get("sync_status"),
                    "failure_reason": row.get("failure_reason"),
                    "retry_upload": row.get("retry_upload"),
                    "encryption_method": row.get("encryption_method"),
                    "operator": row.get("operator"),
                    "sync_log": row.get("sync_log"),
                    "create_time": row.get("create_time"),
                    "update_time": row.get("update_time"),
                })

            return {"items": items, "total": total}
    finally:
        connection.close()


@router.get("/", summary="获取数据上传日志（Doris）")
async def get_data_upload_logs(
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(20, ge=1, le=settings.MAX_PAGE_SIZE, description="每页大小"),
    sort_by: Optional[str] = Query("sync_start_time", description="排序字段"),
    order: Optional[str] = Query("desc", description="排序顺序：asc/desc"),
    start_time: Optional[str] = Query(None, description="开始时间，格式 YYYY-MM-DD HH:MM:SS"),
    end_time: Optional[str] = Query(None, description="结束时间，格式 YYYY-MM-DD HH:MM:SS"),
    batch_id: Optional[str] = Query(None, description="按批次号过滤")
):
    try:
        result = await _query_doris_logs(
            page=page,
            size=size,
            sort_by=sort_by or "sync_start_time",
            order=order or "desc",
            start_time=start_time,
            end_time=end_time,
            batch_id=batch_id
        )
        return paginated_response(items=result["items"], total=result["total"], page=page, size=size, message="获取数据上传日志成功")
    except Exception as e:
        return error_response(message="查询Doris日志失败", error_code="DORIS_QUERY_ERROR", detail=str(e))