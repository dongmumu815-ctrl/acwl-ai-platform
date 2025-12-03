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
    batch_id: Optional[str] = None,
    exclude_data_source_name: Optional[str] = None,
    exclude_platform_name: Optional[str] = None
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

    # 排除指定数据源（不区分大小写）
    if exclude_data_source_name:
        where_clauses.append("LOWER(data_source_name) <> LOWER(%s)")
        params.append(exclude_data_source_name)

    # 排除指定数据平台名称
    if exclude_platform_name:
        where_clauses.append("platform_name <> %s")
        params.append(exclude_platform_name)

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
        # aiomysql.Connection.close() 是同步方法，不能使用 await
        connection.close()


@router.get("/", summary="获取数据上传日志（Doris）")
async def get_data_upload_logs(
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(20, ge=1, le=settings.MAX_PAGE_SIZE, description="每页大小"),
    sort_by: Optional[str] = Query("sync_start_time", description="排序字段"),
    order: Optional[str] = Query("desc", description="排序顺序：asc/desc"),
    start_time: Optional[str] = Query(None, description="开始时间，格式 YYYY-MM-DD HH:MM:SS"),
    end_time: Optional[str] = Query(None, description="结束时间，格式 YYYY-MM-DD HH:MM:SS"),
    batch_id: Optional[str] = Query(None, description="按批次号过滤"),
    exclude_data_source_name: Optional[str] = Query(None, description="排除的数据源名称"),
    exclude_platform_name: Optional[str] = Query(None, description="排除的数据平台名称")
):
    try:
        result = await _query_doris_logs(
            page=page,
            size=size,
            sort_by=sort_by or "sync_start_time",
            order=order or "desc",
            start_time=start_time,
            end_time=end_time,
            batch_id=batch_id,
            exclude_data_source_name=exclude_data_source_name,
            exclude_platform_name=exclude_platform_name
        )
        return paginated_response(items=result["items"], total=result["total"], page=page, size=size, message="获取数据上传日志成功")
    except Exception as e:
        return error_response(message="查询Doris日志失败", error_code="DORIS_QUERY_ERROR", detail=str(e))


@router.get("/details/{batch_id}", summary="获取指定批次的明细数据（通过 DataService 路由至 task_db 与 doris-read）")
async def get_batch_details(
    batch_id: str,
    limit: int = Query(200, ge=1, le=2000, description="返回的最大明细条数"),
    offset: int = Query(0, ge=0, description="明细偏移量"),
    q: str | None = Query(None, description="全字段搜索关键字（匹配所有页）")
):
    """
    处理流程：
    1) 在 task_db 查询批次对应的来源表（cpc_task_instance + cpc_task_origin_name_menu）以获取 table_name；
    2) 根据 table_name 选择 doris-read 中的目标表：期刊文章表或图书表；
    3) 在 doris-read 中按 task_id = batch_id 查询明细数据，并返回至前端。
    """
    try:
        # 延迟导入，避免不必要的启动时开销
        from app.services.db_service import RouterDBService

        router_service = RouterDBService()
        service = router_service.service

        # 1) 在 task_db 查询 table_name
        sql1 = (
            "SELECT t1.id, t2.table_name "
            "FROM cpc_task_instance t1 "
            "LEFT JOIN cpc_task_origin_name_menu t2 ON t1.task_origin_id = t2.id "
            "WHERE t1.task_source_code = %s LIMIT 1"
        )

        res1 = service.execute_sql("task_db", sql1, (batch_id,))
        if not res1 or not res1.get("success"):
            detail = res1.get("error") if isinstance(res1, dict) else "未知错误"
            return error_response(message="查询 task_db 失败", error_code="TASK_DB_QUERY_ERROR", detail=str(detail))

        rows1 = res1.get("data") or []
        if not rows1:
            return error_response(message="未找到批次对应的来源记录", error_code="BATCH_NOT_FOUND", detail=f"batch_id={batch_id}")

        table_name = (rows1[0] or {}).get("table_name")
        _task_instance_id = (rows1[0] or {}).get("id")  # 不使用该值作为 task_id，按需求以 batch_id 作为 task_id
        if not table_name:
            return error_response(message="来源记录缺少 table_name 字段", error_code="TABLE_NAME_MISSING", detail=f"batch_id={batch_id}")

        # 2) 构建 doris-read 查询（使用 batch_id 作为 task_id）
        if table_name == "cpc_rc_periodical_articles":
            # 选取常用字段用于展示与检索
            base_sql = (
                "SELECT source_system_id, periodical_name, doi, publisher, title, author, final_pass, final_pass_time "
                "FROM cpc_rc_periodical_articles WHERE task_id = %s"
            )
            count_sql = "SELECT COUNT(*) AS total FROM cpc_rc_periodical_articles WHERE task_id = %s"

            # 服务端全字段搜索：在常用字段与 final_pass 上做 LIKE / CAST 匹配
            params: list = [_task_instance_id]
            count_params: list = [_task_instance_id]
            if q:
                like = f"%{q}%"
                search_cols = [
                    "source_system_id", "periodical_name", "doi", "publisher", "title", "author"
                ]
                like_clause = "(" + " OR ".join([f"{c} LIKE %s" for c in search_cols] + ["CAST(final_pass AS CHAR) LIKE %s"]) + ")"
                base_sql = base_sql + f" AND {like_clause}"
                count_sql = count_sql + f" AND {like_clause}"
                like_params = [like] * (len(search_cols) + 1)
                params.extend(like_params)
                count_params.extend(like_params)

            # 追加分页控制
            sql2 = base_sql + " LIMIT %s OFFSET %s"
            params2 = params + [limit, offset]

            # 总数查询（用于分页）
            res_count = service.execute_sql("doris-read", count_sql, tuple(count_params))

            res2 = service.execute_sql("doris-read", sql2, tuple(params2))
        else:
            # 图书表：保留基础查询与分页；若后续需要可按具体字段扩展检索
            base_sql = "SELECT * FROM cpc_rc_books WHERE task_id = %s"
            count_sql = "SELECT COUNT(*) AS total FROM cpc_rc_books WHERE task_id = %s"
            params2 = [_task_instance_id, limit, offset]
            res_count = service.execute_sql("doris-read", count_sql, (_task_instance_id,))
            res2 = service.execute_sql("doris-read", base_sql + " LIMIT %s OFFSET %s", tuple(params2))
        # 调试输出可按需开启
        # print("details query resp:", res2)
        if not res2 or not res2.get("success"):
            detail = res2.get("error") if isinstance(res2, dict) else "未知错误"
            return error_response(message="查询 doris-read 失败", error_code="DORIS_QUERY_ERROR", detail=str(detail))

        items = res2.get("data") or []
        total = 0
        if res_count and res_count.get("success"):
            count_rows = res_count.get("data") or []
            if count_rows:
                # DataService 可能返回 [{'total': 123}] 或 [{'COUNT(*)': 123}]
                first = count_rows[0] or {}
                total = int(first.get("total") or first.get("COUNT(*)") or 0)
        return {
            "success": True,
            "message": "获取批次明细成功",
            "data": {
                "batch_id": batch_id,
                "table_name": table_name,
                "limit": limit,
                "offset": offset,
                "items": items,
                "count": total or len(items)
            }
        }
    except Exception as e:
        return error_response(message="获取批次明细失败", error_code="BATCH_DETAILS_ERROR", detail=str(e))