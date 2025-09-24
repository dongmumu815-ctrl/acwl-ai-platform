"""
智能SQL模板解析器
自动处理SQL模板中的参数过滤，无需修改原始模板结构
"""

import re
import logging
from typing import Dict, Any, List, Tuple
from jinja2 import Template

logger = logging.getLogger(__name__)


class SmartSQLTemplateProcessor:
    """
    智能SQL模板处理器
    
    功能：
    1. 自动检测SQL模板中的Jinja2参数占位符
    2. 智能移除包含空参数的整个WHERE条件
    3. 保持SQL语法的正确性
    4. 支持复杂的SQL结构（JOIN、子查询等）
    """
    
    def __init__(self):
        # 匹配Jinja2变量的正则表达式
        self.jinja_var_pattern = re.compile(r'\{\{\s*(\w+)\s*\}\}')
        
        # 匹配WHERE条件的正则表达式（包括AND/OR连接的条件）
        self.where_condition_pattern = re.compile(
            r'(AND|OR)?\s+(\w+)\s*(=|!=|<|>|<=|>=|LIKE|IN)\s*[\'"]?\{\{\s*(\w+)\s*\}\}[\'"]?',
            re.IGNORECASE
        )
    
    def process_template(self, sql_template: str, params: Dict[str, Any]) -> str:
        """
        处理SQL模板，智能过滤空参数
        
        Args:
            sql_template: 原始SQL模板
            params: 参数字典
            
        Returns:
            处理后的SQL语句
        """
        logger.info(f"开始处理SQL模板，参数: {params}")
        
        # 1. 检测模板中的所有参数
        template_vars = self._extract_template_variables(sql_template)
        logger.info(f"模板中检测到的参数: {template_vars}")
        
        # 2. 识别空参数
        empty_params = self._identify_empty_params(params, template_vars)
        logger.info(f"空参数: {empty_params}")
        
        # 3. 智能移除包含空参数的WHERE条件
        processed_sql = self._remove_empty_conditions(sql_template, empty_params)
        logger.info(f"移除空条件后的SQL: {processed_sql}")
        
        # 4. 过滤参数，只保留有效参数
        filtered_params = {k: v for k, v in params.items() 
                          if k not in empty_params and k in template_vars}
        logger.info(f"过滤后的参数: {filtered_params}")
        
        # 5. 渲染最终SQL
        try:
            jinja_template = Template(processed_sql)
            final_sql = jinja_template.render(**filtered_params)
            
            # 6. 清理多余的空格和连接符
            final_sql = self._clean_sql_syntax(final_sql)
            logger.info(f"最终SQL: {final_sql}")
            
            return final_sql
        except Exception as e:
            logger.error(f"SQL模板渲染失败: {str(e)}")
            raise ValueError(f"SQL模板渲染失败: {str(e)}")
    
    def _extract_template_variables(self, sql_template: str) -> List[str]:
        """提取SQL模板中的所有Jinja2变量"""
        matches = self.jinja_var_pattern.findall(sql_template)
        return list(set(matches))  # 去重
    
    def _identify_empty_params(self, params: Dict[str, Any], template_vars: List[str]) -> List[str]:
        """识别空参数"""
        empty_params = []
        for var in template_vars:
            value = params.get(var)
            if value is None or value == "" or (isinstance(value, str) and value.strip() == ""):
                empty_params.append(var)
        return empty_params
    
    def _remove_empty_conditions(self, sql_template: str, empty_params: List[str]) -> str:
        """智能移除包含空参数的WHERE条件"""
        if not empty_params:
            return sql_template
        
        processed_sql = sql_template
        
        # 为每个空参数移除相关的WHERE条件
        for param in empty_params:
            # 构建匹配该参数的条件的正则表达式
            condition_pattern = re.compile(
                rf'(AND|OR)?\s+\w+\s*(=|!=|<|>|<=|>=|LIKE|IN)\s*[\'"]?\{{\{{\s*{param}\s*\}}\}}[\'"]?',
                re.IGNORECASE
            )
            
            # 移除匹配的条件
            processed_sql = condition_pattern.sub('', processed_sql)
        
        return processed_sql
    
    def _clean_sql_syntax(self, sql: str) -> str:
        """清理SQL语法，移除多余的AND/OR连接符"""
        # 移除WHERE后直接跟AND/OR的情况
        sql = re.sub(r'WHERE\s+(AND|OR)\s+', 'WHERE ', sql, flags=re.IGNORECASE)
        
        # 移除连续的AND/OR
        sql = re.sub(r'(AND|OR)\s+(AND|OR)\s+', r'\1 ', sql, flags=re.IGNORECASE)
        
        # 移除末尾的AND/OR
        sql = re.sub(r'\s+(AND|OR)\s*$', '', sql, flags=re.IGNORECASE)
        
        # 移除多余的空格
        sql = re.sub(r'\s+', ' ', sql)
        
        # 如果WHERE后面没有条件，移除WHERE
        sql = re.sub(r'WHERE\s+(ORDER\s+BY|GROUP\s+BY|HAVING|LIMIT|$)', r'\1', sql, flags=re.IGNORECASE)
        
        return sql.strip()


# 创建全局实例
smart_sql_processor = SmartSQLTemplateProcessor()