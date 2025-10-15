#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
API管理相关数据库模型

对应 acwl_api_system 数据库的表结构
"""

from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, Float, Numeric
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class Customer(Base):
    """
    客户表模型
    对应 acwl_api_system.customers 表
    """
    __tablename__ = "customers"
    
    id = Column(Integer, primary_key=True, index=True, comment="客户ID")
    name = Column(String(100), nullable=False, comment="客户名称")
    email = Column(String(100), nullable=False, unique=True, comment="邮箱地址")
    phone = Column(String(20), nullable=True, comment="电话号码")
    company = Column(String(200), nullable=True, comment="公司名称")
    app_id = Column(String(32), nullable=False, unique=True, comment="应用ID")
    app_secret = Column(String(64), nullable=False, comment="应用密钥")
    password_hash = Column(String(255), nullable=True, comment="登录密码哈希")
    link_read_id = Column(String(50), nullable=True, comment="链接读取ID")
    status = Column(Integer, default=1, comment="状态(1:激活,0:禁用)")
    rate_limit = Column(Integer, nullable=True, comment="每分钟调用限制")
    max_apis = Column(Integer, nullable=True, comment="最大API数量")
    last_login_at = Column(DateTime, nullable=True, comment="最后登录时间")
    last_api_call_at = Column(DateTime, nullable=True, comment="最后调用时间")
    total_api_calls = Column(Integer, default=0, comment="总调用次数")
    secret_reset_at = Column(DateTime, nullable=True, comment="密钥重置时间")
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新时间")
    total_apis = Column(Integer, default=0, comment="总API数量")
    
    # 关联关系
    apis = relationship("CustomApi", back_populates="customer")
    batches = relationship("DataBatch", back_populates="customer")
    usage_logs = relationship("ApiUsageLog", back_populates="customer")

class CustomApi(Base):
    """
    自定义API表模型
    对应 acwl_api_system.custom_apis 表
    """
    __tablename__ = "custom_apis"
    
    id = Column(Integer, primary_key=True, index=True, comment="API ID")
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False, comment="客户ID")
    api_name = Column(String(100), nullable=False, comment="API名称")
    api_code = Column(String(50), nullable=False, comment="API代码")
    api_description = Column(Text, nullable=True, comment="API描述")  # 实际字段名
    api_url = Column(String(200), nullable=False, comment="接口地址")  # 实际字段名
    http_method = Column(String(10), default="POST", comment="HTTP方法")
    status = Column(Integer, default=1, comment="状态(1:激活,0:禁用)")  # 实际字段名
    rate_limit = Column(Integer, nullable=True, comment="每分钟调用限制")
    response_format = Column(String(20), default="JSON", comment="响应格式")
    require_authentication = Column(Boolean, default=True, comment="是否需要认证")  # 实际字段名
    total_calls = Column(Integer, default=0, comment="总调用次数")
    last_called_at = Column(DateTime, nullable=True, comment="最后调用时间")
    link_read_id = Column(String(50), nullable=True, comment="链接读取ID")  # 实际字段名
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新时间")
    
    # 为了兼容性，添加属性映射
    @property
    def description(self):
        """兼容性属性：映射到api_description"""
        return self.api_description
    
    @description.setter
    def description(self, value):
        """兼容性属性：映射到api_description"""
        self.api_description = value
    
    @property
    def endpoint_url(self):
        """兼容性属性：映射到api_url"""
        return self.api_url
    
    @endpoint_url.setter
    def endpoint_url(self, value):
        """兼容性属性：映射到api_url"""
        self.api_url = value
    
    @property
    def is_active(self):
        """兼容性属性：映射到status"""
        return self.status == 1
    
    @is_active.setter
    def is_active(self, value):
        """兼容性属性：映射到status"""
        self.status = 1 if value else 0
    
    # 关联关系
    customer = relationship("Customer", back_populates="apis")
    fields = relationship("ApiField", back_populates="api")
    usage_logs = relationship("ApiUsageLog", back_populates="api")

class ApiField(Base):
    """
    API字段表模型
    对应 acwl_api_system.api_fields 表
    """
    __tablename__ = "api_fields"
    
    id = Column(Integer, primary_key=True, index=True, comment="字段ID")
    api_id = Column(Integer, ForeignKey("custom_apis.id"), nullable=False, comment="API ID")
    field_name = Column(String(50), nullable=False, comment="字段名称")
    field_label = Column(String(100), nullable=False, comment="字段标签")
    field_type = Column(String(20), nullable=False, comment="字段类型")
    is_required = Column(Boolean, default=False, comment="是否必填")
    default_value = Column(Text, nullable=True, comment="默认值")
    max_length = Column(Integer, nullable=True, comment="最大长度")
    min_length = Column(Integer, nullable=True, comment="最小长度")
    max_value = Column(Numeric(20, 6), nullable=True, comment="最大值")
    min_value = Column(Numeric(20, 6), nullable=True, comment="最小值")
    allowed_values = Column(Text, nullable=True, comment="允许的值列表")
    validation_regex = Column(String(500), nullable=True, comment="验证正则表达式")
    validation_message = Column(String(200), nullable=True, comment="验证失败提示")
    sort_order = Column(Integer, default=0, comment="排序顺序")
    description = Column(Text, nullable=True, comment="字段描述")
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新时间")
    
    # 关联关系
    api = relationship("CustomApi", back_populates="fields")

class DataBatch(Base):
    """
    数据批次表模型
    对应 acwl_api_system.data_batches 表
    """
    __tablename__ = "data_batches"
    
    id = Column(Integer, primary_key=True, index=True, comment="批次ID")
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False, comment="客户ID")
    batch_name = Column(String(100), nullable=False, comment="批次名称")
    description = Column(Text, nullable=True, comment="批次描述")
    status = Column(String(20), default="pending", comment="处理状态")
    total_records = Column(Integer, default=0, comment="总记录数")
    processed_records = Column(Integer, default=0, comment="已处理记录数")
    failed_records = Column(Integer, default=0, comment="失败记录数")
    file_path = Column(String(500), nullable=True, comment="文件路径")
    result_file_path = Column(String(500), nullable=True, comment="结果文件路径")
    error_message = Column(Text, nullable=True, comment="错误信息")
    started_at = Column(DateTime, nullable=True, comment="开始时间")
    completed_at = Column(DateTime, nullable=True, comment="完成时间")
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新时间")
    
    # 关联关系
    customer = relationship("Customer", back_populates="batches")

class ApiUsageLog(Base):
    """
    API使用日志表模型
    对应 acwl_api_system.api_usage_logs 表
    """
    __tablename__ = "api_usage_logs"
    
    id = Column(Integer, primary_key=True, index=True, comment="日志ID")
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False, comment="客户ID")
    api_id = Column(Integer, ForeignKey("custom_apis.id"), nullable=False, comment="API ID")
    request_data = Column(Text, nullable=True, comment="请求数据")
    response_data = Column(Text, nullable=True, comment="响应数据")
    status_code = Column(Integer, nullable=False, comment="状态码")
    response_time = Column(Float, nullable=False, comment="响应时间(毫秒)")
    ip_address = Column(String(45), nullable=True, comment="IP地址")
    user_agent = Column(String(500), nullable=True, comment="用户代理")
    error_message = Column(Text, nullable=True, comment="错误信息")
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")
    
    # 关联关系
    customer = relationship("Customer", back_populates="usage_logs")
    api = relationship("CustomApi", back_populates="usage_logs")

class DataUpload(Base):
    """
    数据上传记录表模型
    对应 acwl_api_system.data_uploads 表
    """
    __tablename__ = "data_uploads"
    
    id = Column(Integer, primary_key=True, index=True, comment="上传ID")
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False, comment="客户ID")
    batch_id = Column(Integer, ForeignKey("data_batches.id"), nullable=True, comment="批次ID")
    file_name = Column(String(255), nullable=False, comment="文件名")
    file_size = Column(Integer, nullable=False, comment="文件大小")
    file_type = Column(String(50), nullable=False, comment="文件类型")
    file_path = Column(String(500), nullable=False, comment="文件路径")
    upload_status = Column(String(20), default="uploading", comment="上传状态")
    error_message = Column(Text, nullable=True, comment="错误信息")
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新时间")
    
    # 关联关系
    customer = relationship("Customer")
    batch = relationship("DataBatch")