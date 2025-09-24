#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SQL动态修改服务
根据前端参数和模板配置动态修改SQL的WHERE条件
"""

import re
import json
from typing import Dict, List, Any, Optional, Tuple
import sqlparse
from sqlparse.sql import Statement, Where, Comparison
from sqlparse.tokens import Keyword, Whitespace


class SQLDynamicModifier:
    """SQL动态修改器"""
    
    def __init__(self):
        """初始化SQL动态修改器"""
        pass
    
    def modify_sql_by_params(self, sql_query: str, config: Dict[str, Any], user_params: Dict[str, Any]) -> str:
        """
        根据用户参数动态修改SQL
        
        Args:
            sql_query: 原始SQL查询语句
            config: 模板配置，包含conditions信息
            user_params: 用户传入的参数
            
        Returns:
            修改后的SQL查询语句
        """
        try:
            # 解析配置中的条件
            conditions = config.get('conditions', [])
            if not conditions:
                return sql_query
            
            # 解析SQL语句
            parsed = sqlparse.parse(sql_query)[0]
            
            # 提取WHERE子句
            where_clause = self._extract_where_clause(parsed)
            if not where_clause:
                return sql_query
            
            # 分析WHERE条件
            where_conditions = self._parse_where_conditions(where_clause)
            
            # 根据配置和用户参数过滤条件
            filtered_conditions = self._filter_conditions(where_conditions, conditions, user_params)
            
            # 重构SQL
            modified_sql = self._rebuild_sql(sql_query, filtered_conditions)
            
            return modified_sql
            
        except Exception as e:
            print(f"SQL修改失败: {e}")
            return sql_query
    
    def _extract_where_clause(self, parsed_sql: Statement) -> Optional[str]:
        """
        提取WHERE子句
        
        Args:
            parsed_sql: 解析后的SQL语句
            
        Returns:
            WHERE子句内容
        """
        try:
            sql_str = str(parsed_sql)
            
            # 使用正则表达式提取WHERE子句
            where_pattern = r'\bWHERE\s+(.+?)(?:\s+ORDER\s+BY|\s+GROUP\s+BY|\s+HAVING|\s+LIMIT|\s*$)'
            match = re.search(where_pattern, sql_str, re.IGNORECASE | re.DOTALL)
            
            if match:
                return match.group(1).strip()
            
            return None
            
        except Exception as e:
            print(f"提取WHERE子句失败: {e}")
            return None
    
    def _parse_where_conditions(self, where_clause: str) -> List[Dict[str, str]]:
        """
        解析WHERE条件
        
        Args:
            where_clause: WHERE子句内容
            
        Returns:
            条件列表，每个条件包含field, operator, value
        """
        conditions = []
        
        try:
            # 按AND分割条件
            and_parts = re.split(r'\s+AND\s+', where_clause, flags=re.IGNORECASE)
            
            for part in and_parts:
                part = part.strip()
                
                # 解析单个条件 (field operator value)
                condition_match = re.match(r"(\w+)\s*([=<>!]+|LIKE|IN)\s*'?([^']*)'?", part, re.IGNORECASE)
                
                if condition_match:
                    field = condition_match.group(1)
                    operator = condition_match.group(2)
                    value = condition_match.group(3)
                    
                    conditions.append({
                        'field': field,
                        'operator': operator,
                        'value': value,
                        'original': part
                    })
            
            return conditions
            
        except Exception as e:
            print(f"解析WHERE条件失败: {e}")
            return []
    
    def _filter_conditions(self, where_conditions: List[Dict[str, str]], 
                          config_conditions: List[Dict[str, Any]], 
                          user_params: Dict[str, Any]) -> List[Dict[str, str]]:
        """
        根据配置和用户参数过滤条件
        
        Args:
            where_conditions: 原始WHERE条件列表
            config_conditions: 配置中的条件定义
            user_params: 用户传入的参数
            
        Returns:
            过滤后的条件列表
        """
        filtered_conditions = []
        
        # 创建配置条件的映射
        config_map = {cond['name']: cond for cond in config_conditions}
        
        for where_cond in where_conditions:
            field_name = where_cond['field']
            
            # 检查是否在配置中定义
            if field_name in config_map:
                config_cond = config_map[field_name]
                
                # 如果是锁定条件，始终保留
                if config_cond.get('locked', False):
                    # 使用锁定值替换
                    if 'lockedValue' in config_cond:
                        where_cond['value'] = config_cond['lockedValue']
                        where_cond['original'] = f"{field_name} {where_cond['operator']} '{config_cond['lockedValue']}'"
                    filtered_conditions.append(where_cond)
                    continue
                
                # 非锁定条件，检查用户是否提供了参数
                if field_name in user_params:
                    user_value = user_params[field_name]
                    # 只有当用户提供了非空值时才保留条件
                    if user_value is not None and str(user_value).strip() != '':
                        where_cond['value'] = str(user_value)
                        where_cond['original'] = f"{field_name} {where_cond['operator']} '{user_value}'"
                        filtered_conditions.append(where_cond)
            else:
                # 不在配置中的条件，保持原样
                filtered_conditions.append(where_cond)
        
        return filtered_conditions
    
    def _rebuild_sql(self, original_sql: str, filtered_conditions: List[Dict[str, str]]) -> str:
        """
        重构SQL语句
        
        Args:
            original_sql: 原始SQL语句
            filtered_conditions: 过滤后的条件列表
            
        Returns:
            重构后的SQL语句
        """
        try:
            # 提取SQL的各个部分
            select_part = self._extract_select_part(original_sql)
            order_part = self._extract_order_part(original_sql)
            limit_part = self._extract_limit_part(original_sql)
            
            # 构建新的WHERE子句
            if filtered_conditions:
                where_clause = " AND ".join([cond['original'] for cond in filtered_conditions])
                new_sql = f"{select_part} WHERE {where_clause}"
            else:
                new_sql = select_part
            
            # 添加ORDER BY和LIMIT
            if order_part:
                new_sql += f" {order_part}"
            if limit_part:
                new_sql += f" {limit_part}"
            
            return new_sql
            
        except Exception as e:
            print(f"重构SQL失败: {e}")
            return original_sql
    
    def _extract_select_part(self, sql: str) -> str:
        """提取SELECT部分"""
        match = re.match(r'(SELECT\s+.+?\s+FROM\s+\w+)', sql, re.IGNORECASE | re.DOTALL)
        return match.group(1) if match else sql
    
    def _extract_order_part(self, sql: str) -> Optional[str]:
        """提取ORDER BY部分"""
        match = re.search(r'(ORDER\s+BY\s+[^L]+?)(?:\s+LIMIT|\s*$)', sql, re.IGNORECASE)
        return match.group(1).strip() if match else None
    
    def _extract_limit_part(self, sql: str) -> Optional[str]:
        """提取LIMIT部分"""
        match = re.search(r'(LIMIT\s+\d+)', sql, re.IGNORECASE)
        return match.group(1) if match else None


# 测试函数
def test_sql_modifier():
    """测试SQL修改器"""
    modifier = SQLDynamicModifier()
    
    # 测试数据
    sql_query = "SELECT name, description, parent_id, id FROM cpc_agents WHERE node_type = 'agent' AND description = '' AND name = '' ORDER BY id DESC LIMIT 100"
    
    config = {
        "conditions": [
            {
                "name": "node_type", 
                "type": "string", 
                "label": "node_type", 
                "locked": True, 
                "operator": "=", 
                "required": False, 
                "lockedValue": "agent"
            },
            {
                "name": "description", 
                "type": "string", 
                "label": "description", 
                "locked": False, 
                "operator": "=", 
                "required": False, 
                "defaultValue": ""
            },
            {
                "name": "name", 
                "type": "string", 
                "label": "name", 
                "locked": False, 
                "operator": "=", 
                "required": False, 
                "defaultValue": ""
            }
        ]
    }
    
    # 测试场景1：只传入description参数
    user_params1 = {"description": "测试描述"}
    result1 = modifier.modify_sql_by_params(sql_query, config, user_params1)
    print("场景1 - 只传入description:")
    print(result1)
    print()
    
    # 测试场景2：传入name和description参数
    user_params2 = {"name": "测试名称", "description": "测试描述"}
    result2 = modifier.modify_sql_by_params(sql_query, config, user_params2)
    print("场景2 - 传入name和description:")
    print(result2)
    print()
    
    # 测试场景3：不传入任何非锁定参数
    user_params3 = {}
    result3 = modifier.modify_sql_by_params(sql_query, config, user_params3)
    print("场景3 - 不传入任何非锁定参数:")
    print(result3)
    print()


if __name__ == "__main__":
    test_sql_modifier()