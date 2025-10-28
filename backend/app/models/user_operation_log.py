from sqlalchemy import Column, BigInteger, String, Integer, DateTime, Text, JSON, Boolean, Index
from sqlalchemy.sql import func
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from .base import BaseModel


class UserOperationLog(BaseModel):
    """
    用户操作与审计日志模型
    
    记录用户在系统中的所有操作行为，用于审计、监控和分析
    """
    
    __tablename__ = 'user_operation_logs'
    
    # 主键
    id = Column(BigInteger, primary_key=True, autoincrement=True, comment='主键ID')
    
    # 请求标识
    request_id = Column(String(64), nullable=True, comment='请求ID（前端/中间件传入或后端生成）')
    trace_id = Column(String(64), nullable=True, comment='链路追踪ID（可选，便于分布式追踪）')
    
    # 用户信息
    user_id = Column(BigInteger, nullable=True, comment='用户ID（未登录可为空）')
    username = Column(String(64), nullable=True, comment='用户名快照（避免后续改名导致审计困难）')
    user_roles = Column(JSON, nullable=True, comment='用户角色集合（JSON数组）')
    session_id = Column(String(64), nullable=True, comment='会话/Token标识（避免过度存储敏感内容）')
    
    # 客户端信息
    ip = Column(String(45), nullable=True, comment='客户端IP（兼容IPv6）')
    user_agent = Column(String(255), nullable=True, comment='浏览器UA')
    referrer = Column(String(512), nullable=True, comment='来源页Referrer')
    
    # 请求信息
    method = Column(String(10), nullable=False, comment='HTTP方法（GET/POST/PUT/DELETE/PATCH等）')
    url = Column(String(1024), nullable=False, comment='完整URL（含查询串）')
    path = Column(String(512), nullable=False, comment='路径（不含域名与查询串）')
    
    # 业务信息
    module = Column(String(64), nullable=True, comment='业务模块（如 resource、package、api 等）')
    action_type = Column(String(64), nullable=False, comment='操作类型代码（如 create/update/delete/login 等）')
    action_name = Column(String(128), nullable=True, comment='操作名称描述（人类可读）')
    
    # 资源信息
    resource_type = Column(String(64), nullable=True, comment='资源类型（如 datasource、resource、package、api 等）')
    resource_id = Column(String(128), nullable=True, comment='资源ID/编码（字符串以兼容多源ID）')
    resource_name = Column(String(255), nullable=True, comment='资源名称快照')
    
    # 请求数据
    request_query = Column(JSON, nullable=True, comment='查询参数（已脱敏）')
    request_body = Column(JSON, nullable=True, comment='请求体（已脱敏/采样存储）')
    
    # 数据变更
    before_data = Column(JSON, nullable=True, comment='变更前数据快照（部分字段）')
    after_data = Column(JSON, nullable=True, comment='变更后数据快照（部分字段）')
    
    # 扩展信息
    extra = Column(JSON, nullable=True, comment='扩展上下文（业务标签、客户端信息等）')
    
    # 响应信息
    response_status = Column(Integer, nullable=True, comment='响应状态码')
    success = Column(Boolean, nullable=False, default=True, comment='是否成功（1成功/0失败）')
    error_code = Column(String(64), nullable=True, comment='错误码（业务定义）')
    error_message = Column(Text, nullable=True, comment='错误信息摘要（脱敏）')
    exception_stack = Column(Text, nullable=True, comment='异常堆栈（仅服务端）')
    
    # 性能信息
    duration_ms = Column(Integer, nullable=True, comment='接口/操作耗时（毫秒）')
    
    # 系统信息
    server_host = Column(String(128), nullable=True, comment='服务主机名/实例ID')
    env = Column(String(32), nullable=True, comment='环境（dev/test/prod 等）')
    
    # 时间戳
    created_at = Column(DateTime(6), nullable=False, default=func.now(), comment='记录创建时间')
    
    # 索引定义
    __table_args__ = (
        Index('idx_created_at', 'created_at'),
        Index('idx_user_action_time', 'user_id', 'action_type', 'created_at'),
        Index('idx_module_action_time', 'module', 'action_type', 'created_at'),
        Index('idx_resource_time', 'resource_type', 'resource_id', 'created_at'),
        Index('idx_request_id', 'request_id'),
        Index('idx_status_time', 'response_status', 'created_at'),
        # 全文索引需要在数据库层面创建
        {'comment': '用户操作与审计日志'}
    )
    
    @property
    def is_success(self) -> bool:
        """是否成功"""
        return self.success
    
    @property
    def is_error(self) -> bool:
        """是否有错误"""
        return not self.success or self.error_code is not None
    
    @property
    def has_exception(self) -> bool:
        """是否有异常堆栈"""
        return self.exception_stack is not None
    
    @property
    def operation_summary(self) -> str:
        """操作摘要"""
        parts = []
        if self.username:
            parts.append(f"用户:{self.username}")
        if self.action_name:
            parts.append(f"操作:{self.action_name}")
        elif self.action_type:
            parts.append(f"操作:{self.action_type}")
        if self.resource_name:
            parts.append(f"资源:{self.resource_name}")
        elif self.resource_id:
            parts.append(f"资源ID:{self.resource_id}")
        return " | ".join(parts) if parts else "未知操作"
    
    def mark_success(self, db: Session, response_status: int = 200, duration_ms: int = None):
        """
        标记操作成功
        
        Args:
            db: 数据库会话
            response_status: 响应状态码
            duration_ms: 耗时（毫秒）
        """
        self.success = True
        self.response_status = response_status
        if duration_ms is not None:
            self.duration_ms = duration_ms
        db.commit()
    
    def mark_failure(self, db: Session, error_code: str = None, error_message: str = None,
                    exception_stack: str = None, response_status: int = 500, duration_ms: int = None):
        """
        标记操作失败
        
        Args:
            db: 数据库会话
            error_code: 错误码
            error_message: 错误信息
            exception_stack: 异常堆栈
            response_status: 响应状态码
            duration_ms: 耗时（毫秒）
        """
        self.success = False
        self.error_code = error_code
        self.error_message = error_message
        self.exception_stack = exception_stack
        self.response_status = response_status
        if duration_ms is not None:
            self.duration_ms = duration_ms
        db.commit()
    
    @classmethod
    def create_log(cls, db: Session, **kwargs) -> 'UserOperationLog':
        """
        创建操作日志
        
        Args:
            db: 数据库会话
            **kwargs: 日志数据
        
        Returns:
            UserOperationLog: 创建的日志记录
        """
        log = cls(**kwargs)
        db.add(log)
        db.commit()
        db.refresh(log)
        return log
    
    @classmethod
    def get_by_request_id(cls, db: Session, request_id: str) -> Optional['UserOperationLog']:
        """
        根据请求ID获取日志
        
        Args:
            db: 数据库会话
            request_id: 请求ID
        
        Returns:
            Optional[UserOperationLog]: 日志记录或None
        """
        return db.query(cls).filter(cls.request_id == request_id).first()
    
    @classmethod
    def get_user_logs(cls, db: Session, user_id: int, limit: int = 100, 
                     action_type: str = None, start_time: datetime = None, 
                     end_time: datetime = None) -> List['UserOperationLog']:
        """
        获取用户操作日志
        
        Args:
            db: 数据库会话
            user_id: 用户ID
            limit: 限制数量
            action_type: 操作类型
            start_time: 开始时间
            end_time: 结束时间
        
        Returns:
            List[UserOperationLog]: 用户日志列表
        """
        query = db.query(cls).filter(cls.user_id == user_id)
        
        if action_type:
            query = query.filter(cls.action_type == action_type)
        
        if start_time:
            query = query.filter(cls.created_at >= start_time)
        
        if end_time:
            query = query.filter(cls.created_at <= end_time)
        
        return query.order_by(cls.created_at.desc()).limit(limit).all()
    
    @classmethod
    def get_resource_logs(cls, db: Session, resource_type: str, resource_id: str = None,
                         limit: int = 100, start_time: datetime = None, 
                         end_time: datetime = None) -> List['UserOperationLog']:
        """
        获取资源操作日志
        
        Args:
            db: 数据库会话
            resource_type: 资源类型
            resource_id: 资源ID
            limit: 限制数量
            start_time: 开始时间
            end_time: 结束时间
        
        Returns:
            List[UserOperationLog]: 资源日志列表
        """
        query = db.query(cls).filter(cls.resource_type == resource_type)
        
        if resource_id:
            query = query.filter(cls.resource_id == resource_id)
        
        if start_time:
            query = query.filter(cls.created_at >= start_time)
        
        if end_time:
            query = query.filter(cls.created_at <= end_time)
        
        return query.order_by(cls.created_at.desc()).limit(limit).all()
    
    @classmethod
    def get_error_logs(cls, db: Session, limit: int = 100, 
                      start_time: datetime = None, end_time: datetime = None,
                      error_code: str = None) -> List['UserOperationLog']:
        """
        获取错误日志
        
        Args:
            db: 数据库会话
            limit: 限制数量
            start_time: 开始时间
            end_time: 结束时间
            error_code: 错误码
        
        Returns:
            List[UserOperationLog]: 错误日志列表
        """
        query = db.query(cls).filter(cls.success == False)
        
        if error_code:
            query = query.filter(cls.error_code == error_code)
        
        if start_time:
            query = query.filter(cls.created_at >= start_time)
        
        if end_time:
            query = query.filter(cls.created_at <= end_time)
        
        return query.order_by(cls.created_at.desc()).limit(limit).all()
    
    @classmethod
    def get_operation_stats(cls, db: Session, user_id: int = None, 
                           module: str = None, action_type: str = None,
                           days: int = 30) -> Dict[str, Any]:
        """
        获取操作统计信息
        
        Args:
            db: 数据库会话
            user_id: 用户ID
            module: 业务模块
            action_type: 操作类型
            days: 统计天数
        
        Returns:
            Dict[str, Any]: 统计信息
        """
        start_date = datetime.utcnow() - timedelta(days=days)
        
        query = db.query(cls).filter(cls.created_at >= start_date)
        
        if user_id:
            query = query.filter(cls.user_id == user_id)
        
        if module:
            query = query.filter(cls.module == module)
        
        if action_type:
            query = query.filter(cls.action_type == action_type)
        
        logs = query.all()
        
        total_operations = len(logs)
        success_operations = sum(1 for log in logs if log.success)
        error_operations = total_operations - success_operations
        
        # 计算平均耗时
        durations = [log.duration_ms for log in logs if log.duration_ms is not None]
        avg_duration = sum(durations) / len(durations) if durations else 0
        
        # 统计操作类型分布
        action_stats = {}
        for log in logs:
            action = log.action_type
            if action not in action_stats:
                action_stats[action] = {'total': 0, 'success': 0, 'error': 0}
            action_stats[action]['total'] += 1
            if log.success:
                action_stats[action]['success'] += 1
            else:
                action_stats[action]['error'] += 1
        
        return {
            'total_operations': total_operations,
            'success_operations': success_operations,
            'error_operations': error_operations,
            'success_rate': success_operations / total_operations if total_operations > 0 else 0,
            'avg_duration_ms': avg_duration,
            'action_stats': action_stats,
            'period_days': days
        }
    
    def to_dict(self, include_sensitive: bool = False, **kwargs) -> dict:
        """
        转换为字典
        
        Args:
            include_sensitive: 是否包含敏感信息
            **kwargs: 其他参数
        
        Returns:
            dict: 日志记录字典
        """
        result = super().to_dict(**kwargs)
        
        # 添加计算属性
        result['is_success'] = self.is_success
        result['is_error'] = self.is_error
        result['has_exception'] = self.has_exception
        result['operation_summary'] = self.operation_summary
        
        # 处理敏感信息
        if not include_sensitive:
            # 移除或脱敏敏感字段
            result.pop('exception_stack', None)
            if result.get('request_body'):
                result['request_body'] = '[已脱敏]'
            if result.get('user_agent'):
                result['user_agent'] = result['user_agent'][:50] + '...' if len(result['user_agent']) > 50 else result['user_agent']
        
        return result


if __name__ == "__main__":
    # 测试模型功能
    print("用户操作日志模型定义完成")
    print(f"UserOperationLog表名: {UserOperationLog.__tablename__}")
    
    print("\n用户操作日志模型测试完成")