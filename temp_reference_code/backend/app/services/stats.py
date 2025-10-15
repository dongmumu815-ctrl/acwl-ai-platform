#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
统计服务模块

提供各种数据统计和分析功能。

Author: System
Date: 2024
"""

from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta, date
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_, desc, asc, text
from collections import defaultdict, Counter
import json

from app.models.customer import Customer
from app.models.api import CustomApi
from app.models.log import ApiUsageLog, DataUpload
from app.models.admin import AdminUser
from app.core.exceptions import ValidationException
from app.core.business_codes import BusinessException, BusinessCode, BusinessResponse


class StatsService:
    """
    统计服务
    
    提供各种数据统计和分析功能
    """
    
    def __init__(self):
        self.logger = self._get_logger()
    
    def _get_logger(self):
        import logging
        return logging.getLogger(self.__class__.__name__)
    
    def get_overview_stats(
        self,
        db: Session,
        days: int = 30
    ) -> Dict[str, Any]:
        """
        获取概览统计信息
        
        Args:
            db: 数据库会话
            days: 统计天数
            
        Returns:
            概览统计数据
        """
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        # 用户统计
        total_customers = db.query(Customer).count()
        active_customers = db.query(Customer).filter(Customer.is_active == True).count()
        new_customers = db.query(Customer).filter(
            Customer.created_at >= start_date
        ).count()
        
        # API统计
        total_apis = db.query(CustomApi).count()
        active_apis = db.query(CustomApi).filter(CustomApi.status == True).count()
        new_apis = db.query(CustomApi).filter(
            CustomApi.created_at >= start_date
        ).count()
        
        # 调用统计
        total_calls = db.query(ApiUsageLog).count()
        recent_calls = db.query(ApiUsageLog).filter(
            ApiUsageLog.created_at >= start_date
        ).count()
        successful_calls = db.query(ApiUsageLog).filter(
            and_(
                ApiUsageLog.created_at >= start_date,
                and_(ApiUsageLog.response_status >= 200, ApiUsageLog.response_status < 300)
            )
        ).count()
        
        # 上传统计
        total_uploads = db.query(DataUpload).count()
        recent_uploads = db.query(DataUpload).filter(
            DataUpload.created_at >= start_date
        ).count()
        successful_uploads = db.query(DataUpload).filter(
            and_(
                DataUpload.created_at >= start_date,
                DataUpload.status == "completed"
            )
        ).count()
        
        return {
            "period_days": days,
            "customers": {
                "total": total_customers,
                "active": active_customers,
                "new": new_customers,
                "growth_rate": (new_customers / total_customers * 100) if total_customers > 0 else 0
            },
            "apis": {
                "total": total_apis,
                "active": active_apis,
                "new": new_apis,
                "growth_rate": (new_apis / total_apis * 100) if total_apis > 0 else 0
            },
            "api_calls": {
                "total": total_calls,
                "recent": recent_calls,
                "successful": successful_calls,
                "success_rate": (successful_calls / recent_calls * 100) if recent_calls > 0 else 0
            },
            "data_uploads": {
                "total": total_uploads,
                "recent": recent_uploads,
                "successful": successful_uploads,
                "success_rate": (successful_uploads / recent_uploads * 100) if recent_uploads > 0 else 0
            }
        }
    
    def get_daily_stats(
        self,
        db: Session,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        days: int = 30
    ) -> List[Dict[str, Any]]:
        """
        获取每日统计数据
        
        Args:
            db: 数据库会话
            start_date: 开始日期
            end_date: 结束日期
            days: 统计天数（当未指定日期范围时使用）
            
        Returns:
            每日统计数据列表
        """
        if not end_date:
            end_date = datetime.utcnow().date()
        
        if not start_date:
            start_date = end_date - timedelta(days=days - 1)
        
        # 生成日期范围
        date_range = []
        current_date = start_date
        while current_date <= end_date:
            date_range.append(current_date)
            current_date += timedelta(days=1)
        
        daily_stats = []
        
        for target_date in date_range:
            day_start = datetime.combine(target_date, datetime.min.time())
            day_end = datetime.combine(target_date, datetime.max.time())
            
            # 新用户数
            new_customers = db.query(Customer).filter(
                and_(
                    Customer.created_at >= day_start,
                    Customer.created_at <= day_end
                )
            ).count()
            
            # 新API数
            new_apis = db.query(CustomApi).filter(
                and_(
                    CustomApi.created_at >= day_start,
                    CustomApi.created_at <= day_end
                )
            ).count()
            
            # API调用统计
            api_calls = db.query(ApiUsageLog).filter(
                and_(
                    ApiUsageLog.created_at >= day_start,
                    ApiUsageLog.created_at <= day_end
                )
            )
            
            total_calls = api_calls.count()
            successful_calls = api_calls.filter(and_(ApiUsageLog.response_status >= 200, ApiUsageLog.response_status < 300)).count()
            failed_calls = total_calls - successful_calls
            
            # 数据上传统计
            uploads = db.query(DataUpload).filter(
                and_(
                    DataUpload.created_at >= day_start,
                    DataUpload.created_at <= day_end
                )
            )
            
            total_uploads = uploads.count()
            successful_uploads = uploads.filter(DataUpload.status == "completed").count()
            failed_uploads = uploads.filter(DataUpload.status == "failed").count()
            
            daily_stats.append({
                "date": target_date.isoformat(),
                "new_customers": new_customers,
                "new_apis": new_apis,
                "api_calls": {
                    "total": total_calls,
                    "successful": successful_calls,
                    "failed": failed_calls,
                    "success_rate": (successful_calls / total_calls * 100) if total_calls > 0 else 0
                },
                "data_uploads": {
                    "total": total_uploads,
                    "successful": successful_uploads,
                    "failed": failed_uploads,
                    "success_rate": (successful_uploads / total_uploads * 100) if total_uploads > 0 else 0
                }
            })
        
        return daily_stats
    
    def get_hourly_stats(
        self,
        db: Session,
        target_date: Optional[date] = None
    ) -> List[Dict[str, Any]]:
        """
        获取每小时统计数据
        
        Args:
            db: 数据库会话
            target_date: 目标日期
            
        Returns:
            每小时统计数据列表
        """
        if not target_date:
            target_date = datetime.utcnow().date()
        
        hourly_stats = []
        
        for hour in range(24):
            hour_start = datetime.combine(target_date, datetime.min.time()) + timedelta(hours=hour)
            hour_end = hour_start + timedelta(hours=1) - timedelta(seconds=1)
            
            # API调用统计
            api_calls = db.query(ApiUsageLog).filter(
                and_(
                    ApiUsageLog.created_at >= hour_start,
                    ApiUsageLog.created_at <= hour_end
                )
            )
            
            total_calls = api_calls.count()
            successful_calls = api_calls.filter(and_(ApiUsageLog.response_status >= 200, ApiUsageLog.response_status < 300)).count()
            
            # 平均响应时间
            avg_response_time = db.query(func.avg(ApiUsageLog.processing_time)).filter(
                and_(
                    ApiUsageLog.created_at >= hour_start,
                    ApiUsageLog.created_at <= hour_end,
                    ApiUsageLog.processing_time.isnot(None)
                )
            ).scalar() or 0
            
            # 数据上传统计
            uploads = db.query(DataUpload).filter(
                and_(
                    DataUpload.created_at >= hour_start,
                    DataUpload.created_at <= hour_end
                )
            )
            
            total_uploads = uploads.count()
            successful_uploads = uploads.filter(DataUpload.status == "completed").count()
            
            hourly_stats.append({
                "hour": hour,
                "time_range": f"{hour:02d}:00-{(hour+1)%24:02d}:00",
                "api_calls": {
                    "total": total_calls,
                    "successful": successful_calls,
                    "failed": total_calls - successful_calls,
                    "success_rate": (successful_calls / total_calls * 100) if total_calls > 0 else 0,
                    "avg_response_time": float(avg_response_time)
                },
                "data_uploads": {
                    "total": total_uploads,
                    "successful": successful_uploads,
                    "failed": total_uploads - successful_uploads,
                    "success_rate": (successful_uploads / total_uploads * 100) if total_uploads > 0 else 0
                }
            })
        
        return hourly_stats
    
    def get_top_apis(
        self,
        db: Session,
        limit: int = 10,
        days: int = 30,
        order_by: str = "calls"
    ) -> List[Dict[str, Any]]:
        """
        获取热门API统计
        
        Args:
            db: 数据库会话
            limit: 返回数量限制
            days: 统计天数
            order_by: 排序字段（calls, success_rate, avg_response_time）
            
        Returns:
            热门API列表
        """
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        # 基础查询
        query = db.query(
            CustomApi.id,
            CustomApi.api_name,
            CustomApi.api_code,
            CustomApi.customer_id,
            func.count(ApiUsageLog.id).label('total_calls'),
            func.sum(func.case([(and_(ApiUsageLog.response_status >= 200, ApiUsageLog.response_status < 300), 1)], else_=0)).label('successful_calls'),
            func.avg(ApiUsageLog.processing_time).label('avg_response_time'),
            func.sum(ApiUsageLog.data_size).label('total_data_size')
        ).outerjoin(
            ApiUsageLog,
            and_(
                ApiUsageLog.api_id == CustomApi.id,
                ApiUsageLog.created_at >= start_date
            )
        ).group_by(
            CustomApi.id,
            CustomApi.api_name,
            CustomApi.api_code,
            CustomApi.customer_id
        )
        
        # 排序
        if order_by == "success_rate":
            query = query.order_by(
                desc(func.sum(func.case([(and_(ApiUsageLog.response_status >= 200, ApiUsageLog.response_status < 300), 1)], else_=0)) / func.count(ApiUsageLog.id))
            )
        elif order_by == "avg_response_time":
            query = query.order_by(asc(func.avg(ApiUsageLog.processing_time)))
        else:  # calls
            query = query.order_by(desc(func.count(ApiUsageLog.id)))
        
        results = query.limit(limit).all()
        
        top_apis = []
        for result in results:
            total_calls = result.total_calls or 0
            successful_calls = result.successful_calls or 0
            
            top_apis.append({
                "api_id": result.id,
                "api_name": result.api_name,
                "api_code": result.api_code,
                "customer_id": result.customer_id,
                "total_calls": total_calls,
                "successful_calls": successful_calls,
                "failed_calls": total_calls - successful_calls,
                "success_rate": (successful_calls / total_calls * 100) if total_calls > 0 else 0,
                "avg_response_time": float(result.avg_response_time or 0),
                "total_data_size": int(result.total_data_size or 0)
            })
        
        return top_apis
    
    def get_top_customers(
        self,
        db: Session,
        limit: int = 10,
        days: int = 30,
        order_by: str = "calls"
    ) -> List[Dict[str, Any]]:
        """
        获取活跃客户统计
        
        Args:
            db: 数据库会话
            limit: 返回数量限制
            days: 统计天数
            order_by: 排序字段（calls, apis, uploads）
            
        Returns:
            活跃客户列表
        """
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        # 基础查询
        query = db.query(
            Customer.id,
            Customer.name,
            Customer.email,
            func.count(func.distinct(CustomApi.id)).label('total_apis'),
            func.count(ApiUsageLog.id).label('total_calls'),
            func.sum(func.case([(and_(ApiUsageLog.response_status >= 200, ApiUsageLog.response_status < 300), 1)], else_=0)).label('successful_calls'),
            func.count(func.distinct(DataUpload.id)).label('total_uploads')
        ).outerjoin(
            CustomApi, CustomApi.customer_id == Customer.id
        ).outerjoin(
            ApiUsageLog,
            and_(
                ApiUsageLog.customer_id == Customer.id,
                ApiUsageLog.created_at >= start_date
            )
        ).outerjoin(
            DataUpload,
            and_(
                DataUpload.customer_id == Customer.id,
                DataUpload.created_at >= start_date
            )
        ).group_by(
            Customer.id,
            Customer.name,
            Customer.email
        )
        
        # 排序
        if order_by == "apis":
            query = query.order_by(desc(func.count(func.distinct(CustomApi.id))))
        elif order_by == "uploads":
            query = query.order_by(desc(func.count(func.distinct(DataUpload.id))))
        else:  # calls
            query = query.order_by(desc(func.count(ApiUsageLog.id)))
        
        results = query.limit(limit).all()
        
        top_customers = []
        for result in results:
            total_calls = result.total_calls or 0
            successful_calls = result.successful_calls or 0
            
            top_customers.append({
                "customer_id": result.id,
                "name": result.name,
                "email": result.email,
                "total_apis": result.total_apis or 0,
                "total_calls": total_calls,
                "successful_calls": successful_calls,
                "failed_calls": total_calls - successful_calls,
                "success_rate": (successful_calls / total_calls * 100) if total_calls > 0 else 0,
                "total_uploads": result.total_uploads or 0
            })
        
        return top_customers
    
    def get_error_analysis(
        self,
        db: Session,
        days: int = 7,
        limit: int = 20
    ) -> Dict[str, Any]:
        """
        获取错误分析统计
        
        Args:
            db: 数据库会话
            days: 统计天数
            limit: 返回数量限制
            
        Returns:
            错误分析数据
        """
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        # 错误状态码统计
        status_code_stats = db.query(
            ApiUsageLog.status_code,
            func.count(ApiUsageLog.id).label('count')
        ).filter(
            and_(
                ApiUsageLog.created_at >= start_date,
                or_(ApiUsageLog.response_status < 200, ApiUsageLog.response_status >= 300)
            )
        ).group_by(
            ApiUsageLog.status_code
        ).order_by(
            desc(func.count(ApiUsageLog.id))
        ).limit(limit).all()
        
        # 错误消息统计
        error_message_stats = db.query(
            ApiUsageLog.error_message,
            func.count(ApiUsageLog.id).label('count')
        ).filter(
            and_(
                ApiUsageLog.created_at >= start_date,
                or_(ApiUsageLog.response_status < 200, ApiUsageLog.response_status >= 300),
                ApiUsageLog.error_message.isnot(None)
            )
        ).group_by(
            ApiUsageLog.error_message
        ).order_by(
            desc(func.count(ApiUsageLog.id))
        ).limit(limit).all()
        
        # 错误API统计
        error_api_stats = db.query(
            CustomApi.api_name,
            CustomApi.api_code,
            func.count(ApiUsageLog.id).label('error_count')
        ).join(
            ApiUsageLog, ApiUsageLog.api_id == CustomApi.id
        ).filter(
            and_(
                ApiUsageLog.created_at >= start_date,
                or_(ApiUsageLog.response_status < 200, ApiUsageLog.response_status >= 300)
            )
        ).group_by(
            CustomApi.id,
            CustomApi.api_name,
            CustomApi.api_code
        ).order_by(
            desc(func.count(ApiUsageLog.id))
        ).limit(limit).all()
        
        return {
            "period_days": days,
            "status_codes": [
                {
                    "status_code": stat.status_code,
                    "count": stat.count
                }
                for stat in status_code_stats
            ],
            "error_messages": [
                {
                    "error_message": stat.error_message,
                    "count": stat.count
                }
                for stat in error_message_stats
            ],
            "error_apis": [
                {
                    "api_name": stat.api_name,
                    "api_code": stat.api_code,
                    "error_count": stat.error_count
                }
                for stat in error_api_stats
            ]
        }
    
    def get_performance_analysis(
        self,
        db: Session,
        days: int = 7
    ) -> Dict[str, Any]:
        """
        获取性能分析统计
        
        Args:
            db: 数据库会话
            days: 统计天数
            
        Returns:
            性能分析数据
        """
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        # 响应时间统计
        response_time_stats = db.query(
            func.min(ApiUsageLog.processing_time).label('min_time'),
            func.max(ApiUsageLog.processing_time).label('max_time'),
            func.avg(ApiUsageLog.processing_time).label('avg_time'),
            func.count(ApiUsageLog.id).label('total_count')
        ).filter(
            and_(
                ApiUsageLog.created_at >= start_date,
                ApiUsageLog.processing_time.isnot(None)
            )
        ).first()
        
        # 响应时间分布
        response_time_distribution = db.query(
            func.case([
                (ApiUsageLog.processing_time < 100, '< 100ms'),
                (ApiUsageLog.processing_time < 500, '100-500ms'),
                (ApiUsageLog.processing_time < 1000, '500ms-1s'),
                (ApiUsageLog.processing_time < 5000, '1-5s'),
            ], else_='> 5s').label('time_range'),
            func.count(ApiUsageLog.id).label('count')
        ).filter(
            and_(
                ApiUsageLog.created_at >= start_date,
                ApiUsageLog.processing_time.isnot(None)
            )
        ).group_by(
            func.case([
                (ApiUsageLog.processing_time < 100, '< 100ms'),
                (ApiUsageLog.processing_time < 500, '100-500ms'),
                (ApiUsageLog.processing_time < 1000, '500ms-1s'),
                (ApiUsageLog.processing_time < 5000, '1-5s'),
            ], else_='> 5s')
        ).all()
        
        # 慢查询API
        slow_apis = db.query(
            CustomApi.api_name,
            CustomApi.api_code,
            func.avg(ApiUsageLog.processing_time).label('avg_response_time'),
            func.count(ApiUsageLog.id).label('call_count')
        ).join(
            ApiUsageLog, ApiUsageLog.api_id == CustomApi.id
        ).filter(
            and_(
                ApiUsageLog.created_at >= start_date,
                ApiUsageLog.processing_time.isnot(None)
            )
        ).group_by(
            CustomApi.id,
            CustomApi.api_name,
            CustomApi.api_code
        ).having(
            func.avg(ApiUsageLog.processing_time) > 1000  # 大于1秒
        ).order_by(
            desc(func.avg(ApiUsageLog.processing_time))
        ).limit(10).all()
        
        return {
            "period_days": days,
            "response_time_stats": {
                "min_time": float(response_time_stats.min_time or 0),
                "max_time": float(response_time_stats.max_time or 0),
                "avg_time": float(response_time_stats.avg_time or 0),
                "total_count": response_time_stats.total_count or 0
            },
            "response_time_distribution": [
                {
                    "time_range": dist.time_range,
                    "count": dist.count
                }
                for dist in response_time_distribution
            ],
            "slow_apis": [
                {
                    "api_name": api.api_name,
                    "api_code": api.api_code,
                    "avg_response_time": float(api.avg_response_time),
                    "call_count": api.call_count
                }
                for api in slow_apis
            ]
        }
    
    def get_usage_trends(
        self,
        db: Session,
        days: int = 30,
        granularity: str = "daily"
    ) -> Dict[str, Any]:
        """
        获取使用趋势分析
        
        Args:
            db: 数据库会话
            days: 统计天数
            granularity: 粒度（daily, weekly, monthly）
            
        Returns:
            使用趋势数据
        """
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        if granularity == "weekly":
            # 按周统计
            date_format = "%Y-%u"  # 年-周
            date_trunc = func.date_trunc('week', ApiUsageLog.created_at)
        elif granularity == "monthly":
            # 按月统计
            date_format = "%Y-%m"  # 年-月
            date_trunc = func.date_trunc('month', ApiUsageLog.created_at)
        else:
            # 按日统计
            date_format = "%Y-%m-%d"  # 年-月-日
            date_trunc = func.date_trunc('day', ApiUsageLog.created_at)
        
        # API调用趋势
        api_call_trends = db.query(
            date_trunc.label('period'),
            func.count(ApiUsageLog.id).label('total_calls'),
            func.sum(func.case([(and_(ApiUsageLog.response_status >= 200, ApiUsageLog.response_status < 300), 1)], else_=0)).label('successful_calls')
        ).filter(
            ApiUsageLog.created_at >= start_date
        ).group_by(
            date_trunc
        ).order_by(
            date_trunc
        ).all()
        
        # 用户增长趋势
        user_growth_trends = db.query(
            func.date_trunc('day', Customer.created_at).label('period'),
            func.count(Customer.id).label('new_users')
        ).filter(
            Customer.created_at >= start_date
        ).group_by(
            func.date_trunc('day', Customer.created_at)
        ).order_by(
            func.date_trunc('day', Customer.created_at)
        ).all()
        
        # API增长趋势
        api_growth_trends = db.query(
            func.date_trunc('day', CustomApi.created_at).label('period'),
            func.count(CustomApi.id).label('new_apis')
        ).filter(
            CustomApi.created_at >= start_date
        ).group_by(
            func.date_trunc('day', CustomApi.created_at)
        ).order_by(
            func.date_trunc('day', CustomApi.created_at)
        ).all()
        
        return {
            "period_days": days,
            "granularity": granularity,
            "api_call_trends": [
                {
                    "period": trend.period.strftime(date_format) if trend.period else None,
                    "total_calls": trend.total_calls,
                    "successful_calls": trend.successful_calls,
                    "success_rate": (trend.successful_calls / trend.total_calls * 100) if trend.total_calls > 0 else 0
                }
                for trend in api_call_trends
            ],
            "user_growth_trends": [
                {
                    "period": trend.period.strftime("%Y-%m-%d") if trend.period else None,
                    "new_users": trend.new_users
                }
                for trend in user_growth_trends
            ],
            "api_growth_trends": [
                {
                    "period": trend.period.strftime("%Y-%m-%d") if trend.period else None,
                    "new_apis": trend.new_apis
                }
                for trend in api_growth_trends
            ]
        }
    
    def get_custom_stats(
        self,
        db: Session,
        query_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        获取自定义统计数据
        
        Args:
            db: 数据库会话
            query_config: 查询配置
            
        Returns:
            自定义统计数据
            
        Raises:
            ValidationException: 配置验证失败
        """
        try:
            # 验证查询配置
            self._validate_query_config(query_config)
            
            # 构建查询
            query = self._build_custom_query(db, query_config)
            
            # 执行查询
            results = query.all()
            
            # 格式化结果
            formatted_results = self._format_query_results(results, query_config)
            
            return {
                "query_config": query_config,
                "result_count": len(formatted_results),
                "results": formatted_results
            }
        
        except Exception as e:
            self.logger.error(f"Custom stats query failed: {e}")
            raise ValidationException(f"自定义统计查询失败: {str(e)}")
    
    def _validate_query_config(self, config: Dict[str, Any]) -> None:
        """
        验证查询配置
        
        Args:
            config: 查询配置
            
        Raises:
            ValidationException: 验证失败
        """
        required_fields = ['table', 'fields', 'filters']
        for field in required_fields:
            if field not in config:
                raise ValidationException(f"缺少必需字段: {field}")
        
        # 验证表名
        allowed_tables = ['customers', 'apis', 'api_logs', 'uploads', 'admins']
        if config['table'] not in allowed_tables:
            raise ValidationException(f"不支持的表名: {config['table']}")
        
        # 验证字段
        if not isinstance(config['fields'], list) or not config['fields']:
            raise ValidationException("字段列表不能为空")
    
    def _build_custom_query(self, db: Session, config: Dict[str, Any]):
        """
        构建自定义查询
        
        Args:
            db: 数据库会话
            config: 查询配置
            
        Returns:
            查询对象
        """
        # 根据表名选择模型
        table_models = {
            'customers': Customer,
            'apis': CustomApi,
            'api_logs': ApiUsageLog,
            'uploads': DataUpload,
            'admins': AdminUser
        }
        
        model = table_models[config['table']]
        
        # 构建基础查询
        query = db.query(model)
        
        # 应用过滤条件
        for filter_config in config.get('filters', []):
            query = self._apply_filter(query, model, filter_config)
        
        # 应用排序
        if 'order_by' in config:
            query = self._apply_order(query, model, config['order_by'])
        
        # 应用限制
        if 'limit' in config:
            query = query.limit(config['limit'])
        
        return query
    
    def _apply_filter(self, query, model, filter_config: Dict[str, Any]):
        """
        应用过滤条件
        
        Args:
            query: 查询对象
            model: 模型类
            filter_config: 过滤配置
            
        Returns:
            更新后的查询对象
        """
        field_name = filter_config['field']
        operator = filter_config['operator']
        value = filter_config['value']
        
        field = getattr(model, field_name)
        
        if operator == 'eq':
            query = query.filter(field == value)
        elif operator == 'ne':
            query = query.filter(field != value)
        elif operator == 'gt':
            query = query.filter(field > value)
        elif operator == 'gte':
            query = query.filter(field >= value)
        elif operator == 'lt':
            query = query.filter(field < value)
        elif operator == 'lte':
            query = query.filter(field <= value)
        elif operator == 'in':
            query = query.filter(field.in_(value))
        elif operator == 'like':
            query = query.filter(field.like(f"%{value}%"))
        elif operator == 'isnull':
            query = query.filter(field.is_(None))
        elif operator == 'isnotnull':
            query = query.filter(field.isnot(None))
        
        return query
    
    def _apply_order(self, query, model, order_config: Dict[str, Any]):
        """
        应用排序
        
        Args:
            query: 查询对象
            model: 模型类
            order_config: 排序配置
            
        Returns:
            更新后的查询对象
        """
        field_name = order_config['field']
        direction = order_config.get('direction', 'asc')
        
        field = getattr(model, field_name)
        
        if direction == 'desc':
            query = query.order_by(desc(field))
        else:
            query = query.order_by(asc(field))
        
        return query
    
    def _format_query_results(self, results, config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        格式化查询结果
        
        Args:
            results: 查询结果
            config: 查询配置
            
        Returns:
            格式化后的结果列表
        """
        formatted_results = []
        
        for result in results:
            formatted_result = {}
            
            for field in config['fields']:
                if hasattr(result, field):
                    value = getattr(result, field)
                    
                    # 处理特殊类型
                    if isinstance(value, datetime):
                        formatted_result[field] = value.isoformat()
                    elif isinstance(value, date):
                        formatted_result[field] = value.isoformat()
                    else:
                        formatted_result[field] = value
            
            formatted_results.append(formatted_result)
        
        return formatted_results


# 全局服务实例
stats_service = StatsService()


if __name__ == "__main__":
    print("统计服务定义完成")