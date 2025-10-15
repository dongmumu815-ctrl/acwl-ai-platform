#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
验证服务模块

提供数据验证、业务规则检查等功能。

Author: System
Date: 2024
"""

import re
import json
from typing import Any, Dict, List, Optional, Union, Callable
from datetime import datetime, date
from decimal import Decimal, InvalidOperation
from email_validator import validate_email, EmailNotValidError
from urllib.parse import urlparse
from sqlalchemy.orm import Session

from app.core.exceptions import ValidationException
from app.core.business_codes import BusinessException, BusinessCode, BusinessResponse
from app.models.customer import Customer
from app.models.api import CustomApi
from app.models.admin import AdminUser


class ValidationService:
    """
    验证服务
    
    提供各种数据验证和业务规则检查功能
    """
    
    def __init__(self):
        self.logger = self._get_logger()
        
        # 预编译正则表达式
        self.username_pattern = re.compile(r'^[a-zA-Z][a-zA-Z0-9_-]{2,49}$')
        self.phone_pattern = re.compile(r'^1[3-9]\d{9}$')
        self.api_code_pattern = re.compile(r'^[a-zA-Z][a-zA-Z0-9_-]{2,49}$')
        self.field_name_pattern = re.compile(r'^[a-zA-Z][a-zA-Z0-9_]{0,49}$')
        self.config_key_pattern = re.compile(r'^[a-zA-Z][a-zA-Z0-9_.]{1,99}$')
        
        # 邮箱黑名单域名
        self.email_blacklist_domains = {
            '10minutemail.com', 'tempmail.org', 'guerrillamail.com',
            'mailinator.com', 'yopmail.com', 'temp-mail.org'
        }
        
        # 敏感词列表
        self.sensitive_words = {
            'admin', 'administrator', 'root', 'system', 'test',
            'api', 'null', 'undefined', 'delete', 'drop'
        }
    
    def _get_logger(self):
        import logging
        return logging.getLogger(self.__class__.__name__)
    
    def validate_username(self, username: str, check_sensitive: bool = True) -> bool:
        """
        验证用户名格式
        
        Args:
            username: 用户名
            check_sensitive: 是否检查敏感词
            
        Returns:
            是否有效
            
        Raises:
            ValidationException: 验证失败
        """
        if not username:
            raise ValidationException("用户名不能为空")
        
        if not self.username_pattern.match(username):
            raise ValidationException(
                "用户名格式不正确，必须以字母开头，只能包含字母、数字、下划线和连字符，长度3-50字符"
            )
        
        if check_sensitive and username.lower() in self.sensitive_words:
            raise ValidationException(f"用户名 '{username}' 为保留词，不能使用")
        
        return True
    
    def validate_email(self, email: str, check_blacklist: bool = True) -> bool:
        """
        验证邮箱格式
        
        Args:
            email: 邮箱地址
            check_blacklist: 是否检查黑名单
            
        Returns:
            是否有效
            
        Raises:
            ValidationException: 验证失败
        """
        if not email:
            raise ValidationException("邮箱不能为空")
        
        try:
            # 使用email-validator库进行验证
            valid = validate_email(email)
            normalized_email = valid.email
        except EmailNotValidError as e:
            raise ValidationException(f"邮箱格式不正确: {str(e)}")
        
        # 检查黑名单域名
        if check_blacklist:
            domain = normalized_email.split('@')[1].lower()
            if domain in self.email_blacklist_domains:
                raise ValidationException(f"不支持临时邮箱域名: {domain}")
        
        return True
    
    def validate_phone(self, phone: str) -> bool:
        """
        验证手机号格式（中国大陆）
        
        Args:
            phone: 手机号
            
        Returns:
            是否有效
            
        Raises:
            ValidationException: 验证失败
        """
        if not phone:
            raise ValidationException("手机号不能为空")
        
        if not self.phone_pattern.match(phone):
            raise ValidationException("手机号格式不正确")
        
        return True
    
    def validate_password(self, password: str, min_length: int = 8) -> bool:
        """
        验证密码强度
        
        Args:
            password: 密码
            min_length: 最小长度
            
        Returns:
            是否有效
            
        Raises:
            ValidationException: 验证失败
        """
        if not password:
            raise ValidationException("密码不能为空")
        
        if len(password) < min_length:
            raise ValidationException(f"密码长度不能少于{min_length}位")
        
        if len(password) > 128:
            raise ValidationException("密码长度不能超过128位")
        
        # 检查密码复杂度
        has_lower = any(c.islower() for c in password)
        has_upper = any(c.isupper() for c in password)
        has_digit = any(c.isdigit() for c in password)
        has_special = any(c in '!@#$%^&*()_+-=[]{}|;:,.<>?' for c in password)
        
        complexity_count = sum([has_lower, has_upper, has_digit, has_special])
        
        if complexity_count < 3:
            raise ValidationException(
                "密码复杂度不够，至少需要包含以下三种字符类型：小写字母、大写字母、数字、特殊字符"
            )
        
        return True
    
    def validate_url(self, url: str, allowed_schemes: Optional[List[str]] = None) -> bool:
        """
        验证URL格式
        
        Args:
            url: URL地址
            allowed_schemes: 允许的协议列表
            
        Returns:
            是否有效
            
        Raises:
            ValidationException: 验证失败
        """
        if not url:
            raise ValidationException("URL不能为空")
        
        try:
            parsed = urlparse(url)
        except Exception:
            raise ValidationException("URL格式不正确")
        
        if not parsed.scheme or not parsed.netloc:
            raise ValidationException("URL格式不正确，缺少协议或域名")
        
        if allowed_schemes and parsed.scheme not in allowed_schemes:
            raise ValidationException(f"不支持的URL协议: {parsed.scheme}")
        
        return True
    
    def validate_api_code(self, api_code: str) -> bool:
        """
        验证API代码格式
        
        Args:
            api_code: API代码
            
        Returns:
            是否有效
            
        Raises:
            ValidationException: 验证失败
        """
        if not api_code:
            raise ValidationException("API代码不能为空")
        
        if not self.api_code_pattern.match(api_code):
            raise ValidationException(
                "API代码格式不正确，必须以字母开头，只能包含字母、数字、下划线和连字符，长度3-50字符"
            )
        
        if api_code.lower() in self.sensitive_words:
            raise ValidationException(f"API代码 '{api_code}' 为保留词，不能使用")
        
        return True
    
    def validate_field_name(self, field_name: str) -> bool:
        """
        验证字段名格式
        
        Args:
            field_name: 字段名
            
        Returns:
            是否有效
            
        Raises:
            ValidationException: 验证失败
        """
        if not field_name:
            raise ValidationException("字段名不能为空")
        
        if not self.field_name_pattern.match(field_name):
            raise ValidationException(
                "字段名格式不正确，必须以字母开头，只能包含字母、数字和下划线，长度1-50字符"
            )
        
        # 检查SQL关键字
        sql_keywords = {
            'select', 'insert', 'update', 'delete', 'drop', 'create',
            'alter', 'table', 'index', 'view', 'database', 'schema',
            'where', 'order', 'group', 'having', 'join', 'union'
        }
        
        if field_name.lower() in sql_keywords:
            raise ValidationException(f"字段名 '{field_name}' 为SQL关键字，不能使用")
        
        return True
    
    def validate_config_key(self, config_key: str) -> bool:
        """
        验证配置键格式
        
        Args:
            config_key: 配置键
            
        Returns:
            是否有效
            
        Raises:
            ValidationException: 验证失败
        """
        if not config_key:
            raise ValidationException("配置键不能为空")
        
        if not self.config_key_pattern.match(config_key):
            raise ValidationException(
                "配置键格式不正确，必须以字母开头，只能包含字母、数字、下划线和点号，长度2-100字符"
            )
        
        return True
    
    def validate_json(self, json_str: str) -> bool:
        """
        验证JSON格式
        
        Args:
            json_str: JSON字符串
            
        Returns:
            是否有效
            
        Raises:
            ValidationException: 验证失败
        """
        if not json_str:
            raise ValidationException("JSON不能为空")
        
        try:
            json.loads(json_str)
        except json.JSONDecodeError as e:
            raise ValidationException(f"JSON格式不正确: {str(e)}")
        
        return True
    
    def validate_number(
        self,
        value: Union[str, int, float, Decimal],
        min_value: Optional[Union[int, float, Decimal]] = None,
        max_value: Optional[Union[int, float, Decimal]] = None,
        decimal_places: Optional[int] = None
    ) -> bool:
        """
        验证数字格式和范围
        
        Args:
            value: 数值
            min_value: 最小值
            max_value: 最大值
            decimal_places: 小数位数
            
        Returns:
            是否有效
            
        Raises:
            ValidationException: 验证失败
        """
        if value is None:
            raise ValidationException("数值不能为空")
        
        # 转换为Decimal进行精确计算
        try:
            if isinstance(value, str):
                decimal_value = Decimal(value)
            else:
                decimal_value = Decimal(str(value))
        except (InvalidOperation, ValueError):
            raise ValidationException("数值格式不正确")
        
        # 检查范围
        if min_value is not None and decimal_value < Decimal(str(min_value)):
            raise ValidationException(f"数值不能小于{min_value}")
        
        if max_value is not None and decimal_value > Decimal(str(max_value)):
            raise ValidationException(f"数值不能大于{max_value}")
        
        # 检查小数位数
        if decimal_places is not None:
            _, digits, exponent = decimal_value.as_tuple()
            if exponent < -decimal_places:
                raise ValidationException(f"小数位数不能超过{decimal_places}位")
        
        return True
    
    def validate_date(
        self,
        date_value: Union[str, datetime, date],
        date_format: str = "%Y-%m-%d",
        min_date: Optional[Union[str, datetime, date]] = None,
        max_date: Optional[Union[str, datetime, date]] = None
    ) -> bool:
        """
        验证日期格式和范围
        
        Args:
            date_value: 日期值
            date_format: 日期格式
            min_date: 最小日期
            max_date: 最大日期
            
        Returns:
            是否有效
            
        Raises:
            ValidationException: 验证失败
        """
        if date_value is None:
            raise ValidationException("日期不能为空")
        
        # 转换为datetime对象
        if isinstance(date_value, str):
            try:
                parsed_date = datetime.strptime(date_value, date_format)
            except ValueError:
                raise ValidationException(f"日期格式不正确，应为{date_format}")
        elif isinstance(date_value, date):
            parsed_date = datetime.combine(date_value, datetime.min.time())
        elif isinstance(date_value, datetime):
            parsed_date = date_value
        else:
            raise ValidationException("不支持的日期类型")
        
        # 检查范围
        if min_date is not None:
            if isinstance(min_date, str):
                min_datetime = datetime.strptime(min_date, date_format)
            elif isinstance(min_date, date):
                min_datetime = datetime.combine(min_date, datetime.min.time())
            else:
                min_datetime = min_date
            
            if parsed_date < min_datetime:
                raise ValidationException(f"日期不能早于{min_date}")
        
        if max_date is not None:
            if isinstance(max_date, str):
                max_datetime = datetime.strptime(max_date, date_format)
            elif isinstance(max_date, date):
                max_datetime = datetime.combine(max_date, datetime.min.time())
            else:
                max_datetime = max_date
            
            if parsed_date > max_datetime:
                raise ValidationException(f"日期不能晚于{max_date}")
        
        return True
    
    def validate_file_extension(
        self,
        filename: str,
        allowed_extensions: List[str]
    ) -> bool:
        """
        验证文件扩展名
        
        Args:
            filename: 文件名
            allowed_extensions: 允许的扩展名列表
            
        Returns:
            是否有效
            
        Raises:
            ValidationException: 验证失败
        """
        if not filename:
            raise ValidationException("文件名不能为空")
        
        file_ext = filename.lower().split('.')[-1] if '.' in filename else ''
        
        if not file_ext:
            raise ValidationException("文件必须有扩展名")
        
        if f'.{file_ext}' not in [ext.lower() for ext in allowed_extensions]:
            raise ValidationException(f"不支持的文件类型: .{file_ext}")
        
        return True
    
    def validate_uniqueness(
        self,
        db: Session,
        model_class: type,
        field_name: str,
        field_value: Any,
        exclude_id: Optional[int] = None
    ) -> bool:
        """
        验证字段值的唯一性
        
        Args:
            db: 数据库会话
            model_class: 模型类
            field_name: 字段名
            field_value: 字段值
            exclude_id: 排除的记录ID
            
        Returns:
            是否唯一
            
        Raises:
            ValidationException: 验证失败
        """
        if field_value is None:
            return True
        
        query = db.query(model_class).filter(
            getattr(model_class, field_name) == field_value
        )
        
        if exclude_id is not None:
            query = query.filter(model_class.id != exclude_id)
        
        existing = query.first()
        
        if existing:
            raise ValidationException(f"{field_name} '{field_value}' 已存在")
        
        return True
    
    def validate_business_rules(
        self,
        data: Dict[str, Any],
        rules: List[Dict[str, Any]]
    ) -> bool:
        """
        验证业务规则
        
        Args:
            data: 数据字典
            rules: 规则列表
            
        Returns:
            是否通过验证
            
        Raises:
            BusinessException: 业务规则验证失败
        """
        for rule in rules:
            rule_type = rule.get('type')
            field = rule.get('field')
            condition = rule.get('condition')
            message = rule.get('message', f'业务规则验证失败: {field}')
            
            field_value = data.get(field)
            
            if rule_type == 'required' and not field_value:
                raise BusinessException(BusinessCode.DATA_VALIDATION_FAILED, message)
            
            elif rule_type == 'conditional':
                if self._evaluate_condition(data, condition):
                    dependent_field = rule.get('dependent_field')
                    if not data.get(dependent_field):
                        raise BusinessException(BusinessCode.DATA_VALIDATION_FAILED, message)
            
            elif rule_type == 'custom':
                validator_func = rule.get('validator')
                if callable(validator_func) and not validator_func(data):
                    raise BusinessException(BusinessCode.DATA_VALIDATION_FAILED, message)
        
        return True
    
    def _evaluate_condition(self, data: Dict[str, Any], condition: Dict[str, Any]) -> bool:
        """
        评估条件表达式
        
        Args:
            data: 数据字典
            condition: 条件字典
            
        Returns:
            条件是否成立
        """
        field = condition.get('field')
        operator = condition.get('operator')
        value = condition.get('value')
        
        field_value = data.get(field)
        
        if operator == 'eq':
            return field_value == value
        elif operator == 'ne':
            return field_value != value
        elif operator == 'gt':
            return field_value > value
        elif operator == 'gte':
            return field_value >= value
        elif operator == 'lt':
            return field_value < value
        elif operator == 'lte':
            return field_value <= value
        elif operator == 'in':
            return field_value in value
        elif operator == 'not_in':
            return field_value not in value
        elif operator == 'contains':
            return value in str(field_value)
        elif operator == 'not_contains':
            return value not in str(field_value)
        
        return False
    
    def validate_batch_data(
        self,
        data_list: List[Dict[str, Any]],
        validator_func: Callable[[Dict[str, Any]], bool],
        max_batch_size: int = 1000
    ) -> List[Dict[str, Any]]:
        """
        批量验证数据
        
        Args:
            data_list: 数据列表
            validator_func: 验证函数
            max_batch_size: 最大批次大小
            
        Returns:
            验证结果列表
            
        Raises:
            ValidationException: 验证失败
        """
        if not data_list:
            raise ValidationException("数据列表不能为空")
        
        if len(data_list) > max_batch_size:
            raise ValidationException(f"批次大小不能超过{max_batch_size}")
        
        results = []
        
        for i, data in enumerate(data_list):
            try:
                validator_func(data)
                results.append({
                    'index': i,
                    'status': 'success',
                    'data': data
                })
            except (ValidationException, BusinessException) as e:
                results.append({
                    'index': i,
                    'status': 'error',
                    'error': str(e),
                    'data': data
                })
        
        return results
    
    def sanitize_input(self, input_str: str, max_length: int = 1000) -> str:
        """
        清理输入字符串
        
        Args:
            input_str: 输入字符串
            max_length: 最大长度
            
        Returns:
            清理后的字符串
        """
        if not input_str:
            return ''
        
        # 移除控制字符
        sanitized = ''.join(char for char in input_str if ord(char) >= 32 or char in '\n\r\t')
        
        # 限制长度
        if len(sanitized) > max_length:
            sanitized = sanitized[:max_length]
        
        # 移除首尾空白字符
        sanitized = sanitized.strip()
        
        return sanitized
    
    def validate_sql_injection(self, input_str: str) -> bool:
        """
        检查SQL注入风险
        
        Args:
            input_str: 输入字符串
            
        Returns:
            是否安全
            
        Raises:
            ValidationException: 发现SQL注入风险
        """
        if not input_str:
            return True
        
        # SQL注入关键字模式
        sql_patterns = [
            r'\b(union|select|insert|update|delete|drop|create|alter)\b',
            r'\b(exec|execute|sp_|xp_)\b',
            r'[\'";].*[\'";]',
            r'--.*$',
            r'/\*.*\*/',
            r'\bor\s+\d+\s*=\s*\d+',
            r'\band\s+\d+\s*=\s*\d+'
        ]
        
        input_lower = input_str.lower()
        
        for pattern in sql_patterns:
            if re.search(pattern, input_lower, re.IGNORECASE | re.MULTILINE):
                raise ValidationException("输入包含潜在的SQL注入风险")
        
        return True
    
    def validate_xss(self, input_str: str) -> bool:
        """
        检查XSS攻击风险
        
        Args:
            input_str: 输入字符串
            
        Returns:
            是否安全
            
        Raises:
            ValidationException: 发现XSS攻击风险
        """
        if not input_str:
            return True
        
        # XSS攻击模式
        xss_patterns = [
            r'<script[^>]*>.*?</script>',
            r'javascript:',
            r'on\w+\s*=',
            r'<iframe[^>]*>',
            r'<object[^>]*>',
            r'<embed[^>]*>',
            r'<link[^>]*>',
            r'<meta[^>]*>'
        ]
        
        input_lower = input_str.lower()
        
        for pattern in xss_patterns:
            if re.search(pattern, input_lower, re.IGNORECASE | re.DOTALL):
                raise ValidationException("输入包含潜在的XSS攻击风险")
        
        return True


# 全局服务实例
validation_service = ValidationService()


if __name__ == "__main__":
    print("验证服务定义完成")