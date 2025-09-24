#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SQL安全验证工具
"""

import re
import sqlparse
from typing import List, Dict, Any, Optional
from sqlparse.sql import Statement, Token
from sqlparse.tokens import Keyword, DML


class SQLSecurityValidator:
    """SQL安全验证器"""
    
    # 危险关键词列表
    DANGEROUS_KEYWORDS = {
        'DROP', 'DELETE', 'UPDATE', 'INSERT', 'ALTER', 'CREATE', 'TRUNCATE',
        'GRANT', 'REVOKE', 'EXEC', 'EXECUTE', 'CALL', 'LOAD', 'OUTFILE',
        'DUMPFILE', 'INTO', 'REPLACE', 'MERGE', 'UPSERT'
    }
    
    # 危险函数列表
    DANGEROUS_FUNCTIONS = {
        'LOAD_FILE', 'INTO_OUTFILE', 'INTO_DUMPFILE', 'BENCHMARK',
        'SLEEP', 'USER', 'DATABASE', 'VERSION', 'CONNECTION_ID'
    }
    
    # 允许的SELECT相关关键词
    ALLOWED_SELECT_KEYWORDS = {
        'SELECT', 'FROM', 'WHERE', 'GROUP', 'BY', 'HAVING', 'ORDER',
        'LIMIT', 'OFFSET', 'AS', 'AND', 'OR', 'NOT', 'IN', 'EXISTS',
        'BETWEEN', 'LIKE', 'IS', 'NULL', 'DISTINCT', 'ALL', 'ANY',
        'SOME', 'UNION', 'INTERSECT', 'EXCEPT', 'JOIN', 'INNER',
        'LEFT', 'RIGHT', 'FULL', 'OUTER', 'ON', 'USING', 'CASE',
        'WHEN', 'THEN', 'ELSE', 'END', 'WITH', 'RECURSIVE'
    }
    
    def __init__(self):
        """初始化验证器"""
        pass
    
    def validate_query(self, query: str) -> Dict[str, Any]:
        """
        验证SQL查询的安全性
        
        Args:
            query: SQL查询语句
            
        Returns:
            验证结果字典，包含is_safe、error_message、warnings等字段
        """
        result = {
            'is_safe': True,
            'error_message': None,
            'warnings': [],
            'query_type': None,
            'tables': [],
            'columns': []
        }
        
        # 基本检查
        if not query or not query.strip():
            result['is_safe'] = False
            result['error_message'] = "查询语句不能为空"
            return result
        
        query = query.strip()
        
        try:
            # 解析SQL语句
            parsed = sqlparse.parse(query)
            if not parsed:
                result['is_safe'] = False
                result['error_message'] = "无法解析SQL语句"
                return result
            
            statement = parsed[0]
            
            # 检查查询类型
            query_type = self._get_query_type(statement)
            result['query_type'] = query_type
            
            if query_type != 'SELECT':
                result['is_safe'] = False
                result['error_message'] = f"只允许SELECT查询，检测到{query_type}操作"
                return result
            
            # 检查危险关键词
            dangerous_check = self._check_dangerous_keywords(query.upper())
            if not dangerous_check['is_safe']:
                result.update(dangerous_check)
                return result
            
            # 检查危险函数
            function_check = self._check_dangerous_functions(query.upper())
            if not function_check['is_safe']:
                result.update(function_check)
                return result
            
            # 提取表名和列名
            result['tables'] = self._extract_tables(statement)
            result['columns'] = self._extract_columns(statement)
            
            # 检查嵌套查询深度
            nesting_check = self._check_nesting_depth(query)
            if not nesting_check['is_safe']:
                result.update(nesting_check)
                return result
            
            # 检查UNION查询数量
            union_check = self._check_union_count(query.upper())
            if not union_check['is_safe']:
                result.update(union_check)
                return result
            
        except Exception as e:
            result['is_safe'] = False
            result['error_message'] = f"SQL解析错误: {str(e)}"
        
        return result
    
    def _get_query_type(self, statement: Statement) -> Optional[str]:
        """获取查询类型"""
        for token in statement.flatten():
            if token.ttype is DML:
                return token.value.upper()
        return None
    
    def _check_dangerous_keywords(self, query: str) -> Dict[str, Any]:
        """检查危险关键词"""
        result = {'is_safe': True, 'error_message': None}
        
        for keyword in self.DANGEROUS_KEYWORDS:
            # 使用词边界匹配，避免误判
            pattern = r'\b' + re.escape(keyword) + r'\b'
            if re.search(pattern, query, re.IGNORECASE):
                result['is_safe'] = False
                result['error_message'] = f"查询包含禁止的关键词: {keyword}"
                break
        
        return result
    
    def _check_dangerous_functions(self, query: str) -> Dict[str, Any]:
        """检查危险函数"""
        result = {'is_safe': True, 'error_message': None}
        
        for func in self.DANGEROUS_FUNCTIONS:
            # 检查函数调用模式
            pattern = r'\b' + re.escape(func) + r'\s*\('
            if re.search(pattern, query, re.IGNORECASE):
                result['is_safe'] = False
                result['error_message'] = f"查询包含禁止的函数: {func}"
                break
        
        return result
    
    def _extract_tables(self, statement: Statement) -> List[str]:
        """提取表名"""
        tables = []
        # 这里可以实现更复杂的表名提取逻辑
        # 简化实现，使用正则表达式
        query_str = str(statement)
        # 匹配FROM子句中的表名
        from_pattern = r'\bFROM\s+([a-zA-Z_][a-zA-Z0-9_]*(?:\.[a-zA-Z_][a-zA-Z0-9_]*)?)'
        matches = re.findall(from_pattern, query_str, re.IGNORECASE)
        tables.extend(matches)
        
        # 匹配JOIN子句中的表名
        join_pattern = r'\bJOIN\s+([a-zA-Z_][a-zA-Z0-9_]*(?:\.[a-zA-Z_][a-zA-Z0-9_]*)?)'
        matches = re.findall(join_pattern, query_str, re.IGNORECASE)
        tables.extend(matches)
        
        return list(set(tables))  # 去重
    
    def _extract_columns(self, statement: Statement) -> List[str]:
        """提取列名"""
        columns = []
        # 简化实现，提取SELECT子句中的列名
        query_str = str(statement)
        # 这里可以实现更复杂的列名提取逻辑
        return columns
    
    def _check_nesting_depth(self, query: str) -> Dict[str, Any]:
        """检查嵌套查询深度"""
        result = {'is_safe': True, 'error_message': None}
        
        # 计算嵌套SELECT的深度
        select_count = len(re.findall(r'\bSELECT\b', query, re.IGNORECASE))
        max_nesting = 3  # 最大允许3层嵌套
        
        if select_count > max_nesting:
            result['is_safe'] = False
            result['error_message'] = f"查询嵌套层数过深，最大允许{max_nesting}层"
        
        return result
    
    def _check_union_count(self, query: str) -> Dict[str, Any]:
        """检查UNION查询数量"""
        result = {'is_safe': True, 'error_message': None}
        
        union_count = len(re.findall(r'\bUNION\b', query, re.IGNORECASE))
        max_unions = 5  # 最大允许5个UNION
        
        if union_count > max_unions:
            result['is_safe'] = False
            result['error_message'] = f"UNION查询数量过多，最大允许{max_unions}个"
        
        return result
    
    def sanitize_query(self, query: str) -> str:
        """
        清理和标准化SQL查询
        
        Args:
            query: 原始SQL查询
            
        Returns:
            清理后的SQL查询
        """
        if not query:
            return ""
        
        # 移除注释
        query = re.sub(r'--.*$', '', query, flags=re.MULTILINE)
        query = re.sub(r'/\*.*?\*/', '', query, flags=re.DOTALL)
        
        # 标准化空白字符
        query = re.sub(r'\s+', ' ', query)
        
        # 移除首尾空白
        query = query.strip()
        
        return query
    
    def add_limit_clause(self, query: str, limit: int) -> str:
        """
        为查询添加LIMIT子句
        
        Args:
            query: SQL查询语句
            limit: 限制数量
            
        Returns:
            添加LIMIT后的SQL查询
        """
        query = query.strip()
        
        # 检查是否已经有LIMIT子句
        if re.search(r'\bLIMIT\s+\d+', query, re.IGNORECASE):
            # 如果已有LIMIT，替换为新的限制
            query = re.sub(r'\bLIMIT\s+\d+', f'LIMIT {limit}', query, flags=re.IGNORECASE)
        else:
            # 如果没有LIMIT，添加到查询末尾
            # 移除末尾的分号（如果有）
            query = re.sub(r';\s*$', '', query)
            query += f' LIMIT {limit}'
        
        return query


# 全局验证器实例
sql_validator = SQLSecurityValidator()