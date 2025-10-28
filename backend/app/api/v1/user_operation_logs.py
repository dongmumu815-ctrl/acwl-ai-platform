# from fastapi import APIRouter, Depends, Query, HTTPException, Path
# from sqlalchemy.orm import Session
# from typing import List, Optional, Dict, Any
# from datetime import datetime, timedelta
# from pydantic import BaseModel, Field

# from ...database import get_db
# from ...models.user_operation_log import UserOperationLog
# from ...core.auth import get_current_user
# from ...models.user import User
# from ...core.response import success_response, error_response
# from ...core.pagination import paginate

# router = APIRouter(prefix="/user-operation-logs", tags=["用户操作日志"])


# class UserOperationLogResponse(BaseModel):
#     """用户操作日志响应模型"""
#     id: int
#     request_id: Optional[str] = None
#     trace_id: Optional[str] = None
#     user_id: Optional[int] = None
#     username: Optional[str] = None
#     user_roles: Optional[List[str]] = None
#     session_id: Optional[str] = None
#     ip: Optional[str] = None
#     user_agent: Optional[str] = None
#     referrer: Optional[str] = None
#     method: str
#     url: str
#     path: str
#     module: Optional[str] = None
#     action_type: str
#     action_name: Optional[str] = None
#     resource_type: Optional[str] = None
#     resource_id: Optional[str] = None
#     resource_name: Optional[str] = None
#     request_query: Optional[Dict[str, Any]] = None
#     request_body: Optional[Dict[str, Any]] = None
#     before_data: Optional[Dict[str, Any]] = None
#     after_data: Optional[Dict[str, Any]] = None
#     extra: Optional[Dict[str, Any]] = None
#     response_status: Optional[int] = None
#     success: bool
#     error_code: Optional[str] = None
#     error_message: Optional[str] = None
#     duration_ms: Optional[int] = None
#     server_host: Optional[str] = None
#     env: Optional[str] = None
#     created_at: datetime
    
#     # 计算属性
#     is_success: bool
#     is_error: bool
#     has_exception: bool
#     operation_summary: str
    
#     class Config:
#         from_attributes = True


# class UserOperationLogDetailResponse(UserOperationLogResponse):
#     """用户操作日志详情响应模型（包含敏感信息）"""
#     exception_stack: Optional[str] = None


# class UserOperationLogQueryParams(BaseModel):
#     """用户操作日志查询参数"""
#     user_id: Optional[int] = Field(None, description="用户ID")
#     username: Optional[str] = Field(None, description="用户名")
#     module: Optional[str] = Field(None, description="业务模块")
#     action_type: Optional[str] = Field(None, description="操作类型")
#     resource_type: Optional[str] = Field(None, description="资源类型")
#     resource_id: Optional[str] = Field(None, description="资源ID")
#     success: Optional[bool] = Field(None, description="是否成功")
#     error_code: Optional[str] = Field(None, description="错误码")
#     ip: Optional[str] = Field(None, description="客户端IP")
#     method: Optional[str] = Field(None, description="HTTP方法")
#     start_time: Optional[datetime] = Field(None, description="开始时间")
#     end_time: Optional[datetime] = Field(None, description="结束时间")
#     keyword: Optional[str] = Field(None, description="关键词搜索（URL、错误信息等）")


# class OperationStatsResponse(BaseModel):
#     """操作统计响应模型"""
#     total_operations: int = Field(description="总操作数")
#     success_operations: int = Field(description="成功操作数")
#     error_operations: int = Field(description="失败操作数")
#     success_rate: float = Field(description="成功率")
#     avg_duration_ms: float = Field(description="平均耗时（毫秒）")
#     action_stats: Dict[str, Dict[str, int]] = Field(description="操作类型统计")
#     period_days: int = Field(description="统计周期（天）")


# @router.get("/", response_model=Dict[str, Any], summary="获取用户操作日志列表")
# async def get_user_operation_logs(
#     page: int = Query(1, ge=1, description="页码"),
#     size: int = Query(20, ge=1, le=100, description="每页数量"),
#     user_id: Optional[int] = Query(None, description="用户ID"),
#     username: Optional[str] = Query(None, description="用户名"),
#     module: Optional[str] = Query(None, description="业务模块"),
#     action_type: Optional[str] = Query(None, description="操作类型"),
#     resource_type: Optional[str] = Query(None, description="资源类型"),
#     resource_id: Optional[str] = Query(None, description="资源ID"),
#     success: Optional[bool] = Query(None, description="是否成功"),
#     error_code: Optional[str] = Query(None, description="错误码"),
#     ip: Optional[str] = Query(None, description="客户端IP"),
#     method: Optional[str] = Query(None, description="HTTP方法"),
#     start_time: Optional[datetime] = Query(None, description="开始时间"),
#     end_time: Optional[datetime] = Query(None, description="结束时间"),
#     keyword: Optional[str] = Query(None, description="关键词搜索"),
#     db: Session = Depends(get_db),
#     current_user: User = Depends(get_current_user)
# ):
#     """
#     获取用户操作日志列表
    
#     支持多种筛选条件和分页查询
#     """
#     try:
#         # 构建查询
#         query = db.query(UserOperationLog)
        
#         # 应用筛选条件
#         if user_id is not None:
#             query = query.filter(UserOperationLog.user_id == user_id)
        
#         if username:
#             query = query.filter(UserOperationLog.username.like(f"%{username}%"))
        
#         if module:
#             query = query.filter(UserOperationLog.module == module)
        
#         if action_type:
#             query = query.filter(UserOperationLog.action_type == action_type)
        
#         if resource_type:
#             query = query.filter(UserOperationLog.resource_type == resource_type)
        
#         if resource_id:
#             query = query.filter(UserOperationLog.resource_id == resource_id)
        
#         if success is not None:
#             query = query.filter(UserOperationLog.success == success)
        
#         if error_code:
#             query = query.filter(UserOperationLog.error_code == error_code)
        
#         if ip:
#             query = query.filter(UserOperationLog.ip == ip)
        
#         if method:
#             query = query.filter(UserOperationLog.method == method)
        
#         if start_time:
#             query = query.filter(UserOperationLog.created_at >= start_time)
        
#         if end_time:
#             query = query.filter(UserOperationLog.created_at <= end_time)
        
#         if keyword:
#             # 关键词搜索：URL、错误信息、资源名称等
#             keyword_filter = (
#                 UserOperationLog.url.like(f"%{keyword}%") |
#                 UserOperationLog.error_message.like(f"%{keyword}%") |
#                 UserOperationLog.resource_name.like(f"%{keyword}%") |
#                 UserOperationLog.action_name.like(f"%{keyword}%")
#             )
#             query = query.filter(keyword_filter)
        
#         # 按时间倒序排列
#         query = query.order_by(UserOperationLog.created_at.desc())
        
#         # 分页
#         result = paginate(query, page, size)
        
#         # 转换为响应格式（不包含敏感信息）
#         items = []
#         for log in result['items']:
#             log_dict = log.to_dict(include_sensitive=False)
#             items.append(log_dict)
        
#         result['items'] = items
        
#         return success_response(data=result, message="获取用户操作日志列表成功")
    
#     except Exception as e:
#         return error_response(message=f"获取用户操作日志列表失败: {str(e)}")


# @router.get("/{log_id}", response_model=Dict[str, Any], summary="获取用户操作日志详情")
# async def get_user_operation_log_detail(
#     log_id: int = Path(..., description="日志ID"),
#     include_sensitive: bool = Query(False, description="是否包含敏感信息"),
#     db: Session = Depends(get_db),
#     current_user: User = Depends(get_current_user)
# ):
#     """
#     获取用户操作日志详情
    
#     可选择是否包含敏感信息（如异常堆栈）
#     """
#     try:
#         log = db.query(UserOperationLog).filter(UserOperationLog.id == log_id).first()
        
#         if not log:
#             raise HTTPException(status_code=404, detail="操作日志不存在")
        
#         # 转换为字典格式
#         log_dict = log.to_dict(include_sensitive=include_sensitive)
        
#         return success_response(data=log_dict, message="获取用户操作日志详情成功")
    
#     except HTTPException:
#         raise
#     except Exception as e:
#         return error_response(message=f"获取用户操作日志详情失败: {str(e)}")


# @router.get("/stats/overview", response_model=Dict[str, Any], summary="获取操作统计概览")
# async def get_operation_stats_overview(
#     days: int = Query(30, ge=1, le=365, description="统计天数"),
#     user_id: Optional[int] = Query(None, description="用户ID"),
#     module: Optional[str] = Query(None, description="业务模块"),
#     action_type: Optional[str] = Query(None, description="操作类型"),
#     db: Session = Depends(get_db),
#     current_user: User = Depends(get_current_user)
# ):
#     """
#     获取操作统计概览
    
#     包括总操作数、成功率、平均耗时、操作类型分布等
#     """
#     try:
#         stats = UserOperationLog.get_operation_stats(
#             db=db,
#             user_id=user_id,
#             module=module,
#             action_type=action_type,
#             days=days
#         )
        
#         return success_response(data=stats, message="获取操作统计概览成功")
    
#     except Exception as e:
#         return error_response(message=f"获取操作统计概览失败: {str(e)}")


# @router.get("/stats/trends", response_model=Dict[str, Any], summary="获取操作趋势统计")
# async def get_operation_trends(
#     days: int = Query(7, ge=1, le=90, description="统计天数"),
#     user_id: Optional[int] = Query(None, description="用户ID"),
#     module: Optional[str] = Query(None, description="业务模块"),
#     action_type: Optional[str] = Query(None, description="操作类型"),
#     db: Session = Depends(get_db),
#     current_user: User = Depends(get_current_user)
# ):
#     """
#     获取操作趋势统计
    
#     按天统计操作数量和成功率趋势
#     """
#     try:
#         end_date = datetime.utcnow().date()
#         start_date = end_date - timedelta(days=days-1)
        
#         # 构建查询
#         query = db.query(UserOperationLog).filter(
#             UserOperationLog.created_at >= datetime.combine(start_date, datetime.min.time()),
#             UserOperationLog.created_at <= datetime.combine(end_date, datetime.max.time())
#         )
        
#         if user_id:
#             query = query.filter(UserOperationLog.user_id == user_id)
        
#         if module:
#             query = query.filter(UserOperationLog.module == module)
        
#         if action_type:
#             query = query.filter(UserOperationLog.action_type == action_type)
        
#         logs = query.all()
        
#         # 按日期分组统计
#         daily_stats = {}
#         for i in range(days):
#             date = start_date + timedelta(days=i)
#             daily_stats[date.isoformat()] = {
#                 'date': date.isoformat(),
#                 'total': 0,
#                 'success': 0,
#                 'error': 0,
#                 'success_rate': 0.0
#             }
        
#         for log in logs:
#             date_key = log.created_at.date().isoformat()
#             if date_key in daily_stats:
#                 daily_stats[date_key]['total'] += 1
#                 if log.success:
#                     daily_stats[date_key]['success'] += 1
#                 else:
#                     daily_stats[date_key]['error'] += 1
        
#         # 计算成功率
#         for stats in daily_stats.values():
#             if stats['total'] > 0:
#                 stats['success_rate'] = stats['success'] / stats['total']
        
#         # 转换为列表格式
#         trends = list(daily_stats.values())
#         trends.sort(key=lambda x: x['date'])
        
#         return success_response(data={
#             'trends': trends,
#             'period_days': days,
#             'start_date': start_date.isoformat(),
#             'end_date': end_date.isoformat()
#         }, message="获取操作趋势统计成功")
    
#     except Exception as e:
#         return error_response(message=f"获取操作趋势统计失败: {str(e)}")


# @router.get("/user/{user_id}/logs", response_model=Dict[str, Any], summary="获取指定用户的操作日志")
# async def get_user_logs(
#     user_id: int = Path(..., description="用户ID"),
#     page: int = Query(1, ge=1, description="页码"),
#     size: int = Query(20, ge=1, le=100, description="每页数量"),
#     action_type: Optional[str] = Query(None, description="操作类型"),
#     start_time: Optional[datetime] = Query(None, description="开始时间"),
#     end_time: Optional[datetime] = Query(None, description="结束时间"),
#     db: Session = Depends(get_db),
#     current_user: User = Depends(get_current_user)
# ):
#     """
#     获取指定用户的操作日志
    
#     支持按操作类型和时间范围筛选
#     """
#     try:
#         # 构建查询
#         query = db.query(UserOperationLog).filter(UserOperationLog.user_id == user_id)
        
#         if action_type:
#             query = query.filter(UserOperationLog.action_type == action_type)
        
#         if start_time:
#             query = query.filter(UserOperationLog.created_at >= start_time)
        
#         if end_time:
#             query = query.filter(UserOperationLog.created_at <= end_time)
        
#         # 按时间倒序排列
#         query = query.order_by(UserOperationLog.created_at.desc())
        
#         # 分页
#         result = paginate(query, page, size)
        
#         # 转换为响应格式
#         items = []
#         for log in result['items']:
#             log_dict = log.to_dict(include_sensitive=False)
#             items.append(log_dict)
        
#         result['items'] = items
        
#         return success_response(data=result, message="获取用户操作日志成功")
    
#     except Exception as e:
#         return error_response(message=f"获取用户操作日志失败: {str(e)}")


# @router.get("/resource/{resource_type}/logs", response_model=Dict[str, Any], summary="获取指定资源的操作日志")
# async def get_resource_logs(
#     resource_type: str = Path(..., description="资源类型"),
#     resource_id: Optional[str] = Query(None, description="资源ID"),
#     page: int = Query(1, ge=1, description="页码"),
#     size: int = Query(20, ge=1, le=100, description="每页数量"),
#     start_time: Optional[datetime] = Query(None, description="开始时间"),
#     end_time: Optional[datetime] = Query(None, description="结束时间"),
#     db: Session = Depends(get_db),
#     current_user: User = Depends(get_current_user)
# ):
#     """
#     获取指定资源的操作日志
    
#     支持按资源ID和时间范围筛选
#     """
#     try:
#         # 构建查询
#         query = db.query(UserOperationLog).filter(UserOperationLog.resource_type == resource_type)
        
#         if resource_id:
#             query = query.filter(UserOperationLog.resource_id == resource_id)
        
#         if start_time:
#             query = query.filter(UserOperationLog.created_at >= start_time)
        
#         if end_time:
#             query = query.filter(UserOperationLog.created_at <= end_time)
        
#         # 按时间倒序排列
#         query = query.order_by(UserOperationLog.created_at.desc())
        
#         # 分页
#         result = paginate(query, page, size)
        
#         # 转换为响应格式
#         items = []
#         for log in result['items']:
#             log_dict = log.to_dict(include_sensitive=False)
#             items.append(log_dict)
        
#         result['items'] = items
        
#         return success_response(data=result, message="获取资源操作日志成功")
    
#     except Exception as e:
#         return error_response(message=f"获取资源操作日志失败: {str(e)}")


# @router.get("/errors", response_model=Dict[str, Any], summary="获取错误日志")
# async def get_error_logs(
#     page: int = Query(1, ge=1, description="页码"),
#     size: int = Query(20, ge=1, le=100, description="每页数量"),
#     error_code: Optional[str] = Query(None, description="错误码"),
#     start_time: Optional[datetime] = Query(None, description="开始时间"),
#     end_time: Optional[datetime] = Query(None, description="结束时间"),
#     keyword: Optional[str] = Query(None, description="错误信息关键词"),
#     db: Session = Depends(get_db),
#     current_user: User = Depends(get_current_user)
# ):
#     """
#     获取错误日志
    
#     专门用于查看系统错误和异常情况
#     """
#     try:
#         # 构建查询（只查询失败的操作）
#         query = db.query(UserOperationLog).filter(UserOperationLog.success == False)
        
#         if error_code:
#             query = query.filter(UserOperationLog.error_code == error_code)
        
#         if start_time:
#             query = query.filter(UserOperationLog.created_at >= start_time)
        
#         if end_time:
#             query = query.filter(UserOperationLog.created_at <= end_time)
        
#         if keyword:
#             query = query.filter(UserOperationLog.error_message.like(f"%{keyword}%"))
        
#         # 按时间倒序排列
#         query = query.order_by(UserOperationLog.created_at.desc())
        
#         # 分页
#         result = paginate(query, page, size)
        
#         # 转换为响应格式（包含异常堆栈）
#         items = []
#         for log in result['items']:
#             log_dict = log.to_dict(include_sensitive=True)
#             items.append(log_dict)
        
#         result['items'] = items
        
#         return success_response(data=result, message="获取错误日志成功")
    
#     except Exception as e:
#         return error_response(message=f"获取错误日志失败: {str(e)}")


# @router.get("/export", summary="导出用户操作日志")
# async def export_user_operation_logs(
#     format: str = Query("csv", regex="^(csv|excel)$", description="导出格式"),
#     user_id: Optional[int] = Query(None, description="用户ID"),
#     module: Optional[str] = Query(None, description="业务模块"),
#     action_type: Optional[str] = Query(None, description="操作类型"),
#     start_time: Optional[datetime] = Query(None, description="开始时间"),
#     end_time: Optional[datetime] = Query(None, description="结束时间"),
#     limit: int = Query(10000, ge=1, le=50000, description="导出数量限制"),
#     db: Session = Depends(get_db),
#     current_user: User = Depends(get_current_user)
# ):
#     """
#     导出用户操作日志
    
#     支持CSV和Excel格式导出
#     """
#     try:
#         # 构建查询
#         query = db.query(UserOperationLog)
        
#         if user_id:
#             query = query.filter(UserOperationLog.user_id == user_id)
        
#         if module:
#             query = query.filter(UserOperationLog.module == module)
        
#         if action_type:
#             query = query.filter(UserOperationLog.action_type == action_type)
        
#         if start_time:
#             query = query.filter(UserOperationLog.created_at >= start_time)
        
#         if end_time:
#             query = query.filter(UserOperationLog.created_at <= end_time)
        
#         # 按时间倒序排列并限制数量
#         logs = query.order_by(UserOperationLog.created_at.desc()).limit(limit).all()
        
#         if not logs:
#             return error_response(message="没有找到符合条件的日志记录")
        
#         # 准备导出数据
#         export_data = []
#         for log in logs:
#             log_dict = log.to_dict(include_sensitive=False)
#             # 简化数据结构，便于导出
#             export_record = {
#                 'ID': log_dict['id'],
#                 '请求ID': log_dict.get('request_id', ''),
#                 '用户ID': log_dict.get('user_id', ''),
#                 '用户名': log_dict.get('username', ''),
#                 'IP地址': log_dict.get('ip', ''),
#                 'HTTP方法': log_dict['method'],
#                 'URL路径': log_dict['path'],
#                 '业务模块': log_dict.get('module', ''),
#                 '操作类型': log_dict['action_type'],
#                 '操作名称': log_dict.get('action_name', ''),
#                 '资源类型': log_dict.get('resource_type', ''),
#                 '资源ID': log_dict.get('resource_id', ''),
#                 '资源名称': log_dict.get('resource_name', ''),
#                 '响应状态': log_dict.get('response_status', ''),
#                 '是否成功': '是' if log_dict['success'] else '否',
#                 '错误码': log_dict.get('error_code', ''),
#                 '错误信息': log_dict.get('error_message', ''),
#                 '耗时(ms)': log_dict.get('duration_ms', ''),
#                 '服务主机': log_dict.get('server_host', ''),
#                 '环境': log_dict.get('env', ''),
#                 '创建时间': log_dict['created_at']
#             }
#             export_data.append(export_record)
        
#         # 根据格式返回不同的响应
#         if format == "csv":
#             # 这里应该生成CSV文件并返回下载链接
#             # 实际实现中需要使用pandas或csv模块生成文件
#             return success_response(data={
#                 'download_url': '/api/v1/downloads/user-operation-logs.csv',
#                 'total_records': len(export_data),
#                 'format': 'csv'
#             }, message="CSV导出任务已创建")
        
#         elif format == "excel":
#             # 这里应该生成Excel文件并返回下载链接
#             # 实际实现中需要使用pandas或openpyxl模块生成文件
#             return success_response(data={
#                 'download_url': '/api/v1/downloads/user-operation-logs.xlsx',
#                 'total_records': len(export_data),
#                 'format': 'excel'
#             }, message="Excel导出任务已创建")
    
#     except Exception as e:
#         return error_response(message=f"导出用户操作日志失败: {str(e)}")
