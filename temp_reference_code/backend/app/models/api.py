#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
API相关数据库模型

定义自定义API接口和字段结构的数据库模型。
支持动态API创建和灵活的数据结构定义。

Author: System
Date: 2024
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from sqlalchemy import Column, String, Integer, Boolean, Text, ForeignKey, Index, Enum, Numeric, DateTime
from sqlalchemy.orm import relationship, Session
from sqlalchemy.dialects.mysql import JSON
import json
import re

from .base import BaseModel


class CustomApi(BaseModel):
    """
    自定义API模型
    
    存储客户自定义的API接口配置信息
    """
    
    __tablename__ = "custom_apis"
    
    # 关联客户
    customer_id = Column(
        Integer,
        ForeignKey("customers.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="客户ID"
    )
    
    # API基本信息
    api_name = Column(
        String(100),
        nullable=False,
        comment="API名称"
    )
    
    api_code = Column(
        String(50),
        nullable=False,
        comment="API代码（用于生成URL）"
    )
    
    api_description = Column(
        Text,
        nullable=True,
        comment="API描述"
    )
    
    # API配置
    http_method = Column(
        Enum('GET', 'POST', 'PUT', 'DELETE', 'PATCH', name='http_method_enum'),
        nullable=False,
        default='POST',
        comment="HTTP方法"
    )
    
    # 状态管理
    status = Column(
        Boolean,
        nullable=False,
        default=True,
        index=True,
        comment="状态：True-开放，False-停用"
    )
    
    # 频率限制
    rate_limit = Column(
        Integer,
        nullable=True,
        comment="频率限制（每分钟请求数），None表示使用客户默认值"
    )
    
    # 验证配置
    require_authentication = Column(
        Boolean,
        nullable=False,
        default=True,
        comment="是否需要认证"
    )
    
    # API URL
    api_url = Column(
        String(200),
        nullable=False,
        comment="生成的接口URL"
    )
    
    # 响应配置
    response_format = Column(
        Enum('JSON', 'XML', 'TEXT', name='response_format_enum'),
        nullable=False,
        default='JSON',
        comment="响应格式"
    )
    
    # 统计信息
    total_calls = Column(
        Integer,
        nullable=False,
        default=0,
        comment="总调用次数"
    )
    
    last_called_at = Column(
        DateTime,
        nullable=True,
        comment="最后调用时间"
    )
    
    # 外部系统关联
    link_read_id = Column(
        String(50),
        nullable=True,
        index=True,
        comment="链接其他系统的ID"
    )
    
    # 关联关系
    customer = relationship(
        "Customer",
        back_populates="apis"
    )
    
    fields = relationship(
        "ApiField",
        back_populates="api",
        cascade="all, delete-orphan",
        order_by="ApiField.sort_order",
        lazy="dynamic"
    )
    
    usage_logs = relationship(
        "ApiUsageLog",
        back_populates="api",
        cascade="all, delete-orphan",
        lazy="dynamic"
    )
    
    data_uploads = relationship(
        "DataUpload",
        back_populates="api",
        cascade="all, delete-orphan",
        lazy="dynamic"
    )
    
    data_batches = relationship(
        "DataBatch",
        back_populates="api",
        cascade="all, delete-orphan",
        lazy="dynamic"
    )
    
    # 索引和约束
    __table_args__ = (
        Index('idx_api_customer_code', 'customer_id', 'api_code', unique=True),
        Index('idx_api_status_created', 'status', 'created_at'),
        Index('idx_api_method', 'http_method'),
    )
    
    def __init__(self, **kwargs):
        """
        初始化API实例
        
        自动处理api_code的格式化和api_url的生成
        """
        if 'api_code' in kwargs:
            kwargs['api_code'] = self.format_api_code(kwargs['api_code'])
        
        # 如果没有提供api_url，则自动生成
        if 'api_url' not in kwargs and 'api_code' in kwargs and 'customer' in kwargs:
            kwargs['api_url'] = f"/api/v1/custom/{kwargs['customer'].app_id}/{kwargs['api_code']}"
        
        super().__init__(**kwargs)
    
    @staticmethod
    def format_api_code(code: str) -> str:
        """
        格式化API代码
        
        将代码转换为符合URL规范的格式
        
        Args:
            code: 原始代码
        
        Returns:
            str: 格式化后的代码
        """
        # 转换为小写，替换空格和特殊字符为下划线
        code = re.sub(r'[^a-zA-Z0-9_-]', '_', code.lower())
        # 移除连续的下划线
        code = re.sub(r'_+', '_', code)
        # 移除首尾的下划线
        code = code.strip('_')
        return code
    
    def generate_api_url(self) -> str:
        """
        生成API的完整URL路径
        
        Returns:
            str: API URL路径
        """
        return f"/api/v1/custom/{self.customer.app_id}/{self.api_code}"
    
    def is_active(self) -> bool:
        """
        检查API是否处于活跃状态
        
        Returns:
            bool: 是否活跃
        """
        return self.status and self.customer.is_active()
    
    def get_effective_rate_limit(self) -> int:
        """
        获取有效的频率限制
        
        Returns:
            int: 频率限制值
        """
        return self.rate_limit or self.customer.get_effective_rate_limit()
    
    def get_field_definitions(self) -> List['ApiField']:
        """
        获取字段定义列表
        
        Returns:
            List[ApiField]: 按排序顺序的字段列表
        """
        return self.fields.order_by('sort_order').all()
    
    def get_required_fields(self) -> List['ApiField']:
        """
        获取必填字段列表
        
        Returns:
            List[ApiField]: 必填字段列表
        """
        return self.fields.filter(ApiField.is_required == True).all()
    
    def validate_data(self, data: Dict[str, Any]) -> tuple[bool, List[str]]:
        """
        验证提交的数据
        
        Args:
            data: 待验证的数据字典
        
        Returns:
            tuple: (是否验证通过, 错误信息列表)
        """
        errors = []
        field_definitions = self.get_field_definitions()
        
        # 检查必填字段
        for field in field_definitions:
            field_name = field.field_name
            field_value = data.get(field_name)
            
            # 验证必填字段
            if field.is_required and (field_value is None or field_value == ''):
                errors.append(f"字段 '{field.field_label}' 是必填的")
                continue
            
            # 如果字段有值，进行类型和规则验证
            if field_value is not None:
                field_errors = field.validate_value(field_value)
                errors.extend(field_errors)
        
        return len(errors) == 0, errors
    
    def increment_call_count(self, db: Session) -> None:
        """
        增加调用计数
        
        Args:
            db: 数据库会话
        """
        self.total_calls += 1
        self.last_called_at = datetime.utcnow()
        db.commit()
    
    @classmethod
    def get_by_customer_and_code(cls, db: Session, customer_id: int, api_code: str) -> Optional['CustomApi']:
        """
        根据客户ID和API代码获取API
        
        Args:
            db: 数据库会话
            customer_id: 客户ID
            api_code: API代码
        
        Returns:
            Optional[CustomApi]: API实例或None
        """
        return db.query(cls).filter(
            cls.customer_id == customer_id,
            cls.api_code == api_code
        ).first()
    
    @classmethod
    def get_active_apis(cls, db: Session, customer_id: int = None) -> List['CustomApi']:
        """
        获取活跃的API列表
        
        Args:
            db: 数据库会话
            customer_id: 客户ID，如果指定则只获取该客户的API
        
        Returns:
            List[CustomApi]: 活跃API列表
        """
        query = db.query(cls).filter(cls.status == True)
        
        if customer_id:
            query = query.filter(cls.customer_id == customer_id)
        
        return query.all()
    
    def to_dict(self, include_fields: bool = False, **kwargs) -> dict:
        """
        转换为字典
        
        Args:
            include_fields: 是否包含字段定义
            **kwargs: 其他参数
        
        Returns:
            dict: API信息字典
        """
        result = super().to_dict(**kwargs)
        result['api_url'] = self.api_url
        result['effective_rate_limit'] = self.get_effective_rate_limit()
        
        if include_fields:
            result['fields'] = [field.to_dict() for field in self.get_field_definitions()]
        
        return result


class ApiField(BaseModel):
    """
    API字段定义模型
    
    定义API接口的数据结构和验证规则
    """
    
    __tablename__ = "api_fields"
    
    # 关联API
    api_id = Column(
        Integer,
        ForeignKey("custom_apis.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="API ID"
    )
    
    # 字段基本信息
    field_name = Column(
        String(50),
        nullable=False,
        comment="字段名称（程序中使用）"
    )
    
    field_label = Column(
        String(100),
        nullable=False,
        comment="字段标签（用户界面显示）"
    )
    
    field_type = Column(
        Enum('string', 'int', 'float', 'boolean', 'date', 'datetime', 'json', 'file', name='field_type_enum'),
        nullable=False,
        comment="字段类型"
    )
    
    # 验证规则
    is_required = Column(
        Boolean,
        nullable=False,
        default=False,
        comment="是否必填"
    )
    
    default_value = Column(
        Text,
        nullable=True,
        comment="默认值"
    )
    
    # 字符串类型验证
    max_length = Column(
        Integer,
        nullable=True,
        comment="最大长度（字符串类型）"
    )
    
    min_length = Column(
        Integer,
        nullable=True,
        comment="最小长度（字符串类型）"
    )
    
    # 数值类型验证
    max_value = Column(
        Numeric(20, 6),
        nullable=True,
        comment="最大值（数值类型）"
    )
    
    min_value = Column(
        Numeric(20, 6),
        nullable=True,
        comment="最小值（数值类型）"
    )
    
    # 枚举值验证
    allowed_values = Column(
        JSON,
        nullable=True,
        comment="允许的值列表（JSON数组格式）"
    )
    
    # 正则表达式验证
    validation_regex = Column(
        String(500),
        nullable=True,
        comment="验证正则表达式"
    )
    
    validation_message = Column(
        String(200),
        nullable=True,
        comment="验证失败提示信息"
    )
    
    # 排序和显示
    sort_order = Column(
        Integer,
        nullable=False,
        default=0,
        comment="排序顺序"
    )
    
    # 字段描述
    description = Column(
        Text,
        nullable=True,
        comment="字段描述"
    )
    
    # 关联关系
    api = relationship(
        "CustomApi",
        back_populates="fields"
    )
    
    # 索引和约束
    __table_args__ = (
        Index('idx_field_api_name', 'api_id', 'field_name', unique=True),
        Index('idx_field_sort', 'api_id', 'sort_order'),
        Index('idx_field_type', 'field_type'),
    )
    
    def validate_value(self, value: Any) -> List[str]:
        """
        验证字段值
        
        Args:
            value: 待验证的值
        
        Returns:
            List[str]: 错误信息列表
        """
        errors = []
        
        # 类型转换和验证
        try:
            converted_value = self._convert_value(value)
        except (ValueError, TypeError) as e:
            errors.append(f"字段 '{self.field_label}' 类型错误: {str(e)}")
            return errors
        
        # 字符串长度验证
        if self.field_type == 'string' and isinstance(converted_value, str):
            if self.min_length is not None and len(converted_value) < self.min_length:
                errors.append(f"字段 '{self.field_label}' 长度不能少于 {self.min_length} 个字符")
            
            if self.max_length is not None and len(converted_value) > self.max_length:
                errors.append(f"字段 '{self.field_label}' 长度不能超过 {self.max_length} 个字符")
        
        # 数值范围验证
        if self.field_type in ['int', 'float'] and isinstance(converted_value, (int, float)):
            if self.min_value is not None and converted_value < float(self.min_value):
                errors.append(f"字段 '{self.field_label}' 值不能小于 {self.min_value}")
            
            if self.max_value is not None and converted_value > float(self.max_value):
                errors.append(f"字段 '{self.field_label}' 值不能大于 {self.max_value}")
        
        # 枚举值验证
        if self.allowed_values and converted_value not in self.allowed_values:
            errors.append(f"字段 '{self.field_label}' 值必须是以下之一: {', '.join(map(str, self.allowed_values))}")
        
        # 正则表达式验证
        if self.validation_regex and self.field_type == 'string':
            if not re.match(self.validation_regex, str(converted_value)):
                message = self.validation_message or f"字段 '{self.field_label}' 格式不正确"
                errors.append(message)
        
        return errors
    
    def _convert_value(self, value: Any) -> Any:
        """
        根据字段类型转换值
        
        Args:
            value: 原始值
        
        Returns:
            Any: 转换后的值
        
        Raises:
            ValueError: 类型转换失败
        """
        if value is None or value == '':
            return None
        
        if self.field_type == 'string':
            return str(value)
        
        elif self.field_type == 'int':
            return int(value)
        
        elif self.field_type == 'float':
            return float(value)
        
        elif self.field_type == 'boolean':
            if isinstance(value, bool):
                return value
            if isinstance(value, str):
                return value.lower() in ('true', '1', 'yes', 'on')
            return bool(value)
        
        elif self.field_type == 'date':
            if isinstance(value, str):
                from datetime import datetime
                return datetime.strptime(value, '%Y-%m-%d').date()
            return value
        
        elif self.field_type == 'datetime':
            if isinstance(value, str):
                from datetime import datetime
                # 尝试多种日期时间格式
                formats = ['%Y-%m-%d %H:%M:%S', '%Y-%m-%dT%H:%M:%S', '%Y-%m-%d']
                for fmt in formats:
                    try:
                        return datetime.strptime(value, fmt)
                    except ValueError:
                        continue
                raise ValueError(f"无法解析日期时间格式: {value}")
            return value
        
        elif self.field_type == 'json':
            if isinstance(value, str):
                return json.loads(value)
            return value
        
        elif self.field_type == 'file':
            # 文件类型暂时返回原值，由上传处理逻辑处理
            return value
        
        return value
    
    @classmethod
    def get_by_api_and_name(cls, db: Session, api_id: int, field_name: str) -> Optional['ApiField']:
        """
        根据API ID和字段名获取字段定义
        
        Args:
            db: 数据库会话
            api_id: API ID
            field_name: 字段名
        
        Returns:
            Optional[ApiField]: 字段定义或None
        """
        return db.query(cls).filter(
            cls.api_id == api_id,
            cls.field_name == field_name
        ).first()
    
    def to_dict(self, **kwargs) -> dict:
        """
        转换为字典
        
        Returns:
            dict: 字段定义字典
        """
        result = super().to_dict(**kwargs)
        
        # 处理特殊字段
        if self.allowed_values:
            result['allowed_values'] = self.allowed_values
        
        if self.max_value is not None:
            result['max_value'] = float(self.max_value)
        
        if self.min_value is not None:
            result['min_value'] = float(self.min_value)
        
        return result


if __name__ == "__main__":
    # 测试模型功能
    import logging
    logger = logging.getLogger(__name__)
    logger.info("API模型定义完成")
    logger.info(f"CustomApi表名: {CustomApi.__tablename__}")
    logger.info(f"ApiField表名: {ApiField.__tablename__}")
    
    # 测试API代码格式化
    test_codes = ["User Data Upload", "user-data-upload", "user_data_upload", "用户数据上传"]
    for code in test_codes:
        formatted = CustomApi.format_api_code(code)
        logger.info(f"'{code}' -> '{formatted}'")
    
    logger.info("API模型测试完成")