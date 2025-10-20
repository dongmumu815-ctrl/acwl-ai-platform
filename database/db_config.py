#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库配置文件
用于测试数据插入脚本的独立配置
"""

import os
from pathlib import Path
from typing import Optional

def load_env_file(env_path: Path):
    """加载.env文件"""
    if not env_path.exists():
        return
    
    try:
        with open(env_path, 'r', encoding='utf-8') as file:
            for line in file:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key.strip()] = value.strip()
    except Exception as e:
        print(f"⚠️  加载.env文件失败: {e}")

class DatabaseConfig:
    """数据库配置类"""
    
    def __init__(self):
        # 尝试加载.env文件
        env_file = Path(__file__).parent / '.env'
        load_env_file(env_file)
        
        # 从环境变量读取配置，如果没有则使用默认值
        self.DB_HOST = os.getenv('DB_HOST', '10.20.1.200')
        self.DB_PORT = int(os.getenv('DB_PORT', '3306'))
        self.DB_USER = os.getenv('DB_USER', 'root')
        self.DB_PASSWORD = os.getenv('DB_PASSWORD', 'root')
        self.DB_NAME = os.getenv('DB_NAME', 'acwl-ai')
        self.DB_CHARSET = os.getenv('DB_CHARSET', 'utf8mb4')
        
        # 记录配置来源
        self._config_source = 'environment' if env_file.exists() else 'default'
    
    @property
    def database_url(self) -> str:
        """获取数据库连接URL"""
        return (
            f"mysql+pymysql://{self.DB_USER}:{self.DB_PASSWORD}"
            f"@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
            f"?charset={self.DB_CHARSET}"
        )
    
    def validate(self) -> bool:
        """验证配置是否完整"""
        required_fields = ['DB_HOST', 'DB_PORT', 'DB_USER', 'DB_PASSWORD', 'DB_NAME']
        for field in required_fields:
            if not getattr(self, field):
                print(f"❌ 缺少必要配置: {field}")
                return False
        return True
    
    def display_config(self):
        """显示当前配置（隐藏密码）"""
        config_source_text = "环境变量/.env文件" if self._config_source == 'environment' else "默认配置"
        print(f"📋 当前数据库配置 (来源: {config_source_text}):")
        print(f"  主机: {self.DB_HOST}")
        print(f"  端口: {self.DB_PORT}")
        print(f"  用户: {self.DB_USER}")
        print(f"  密码: {'*' * len(self.DB_PASSWORD)}")
        print(f"  数据库: {self.DB_NAME}")
        print(f"  字符集: {self.DB_CHARSET}")
        
        if self._config_source == 'default':
            print("💡 提示: 可创建 .env 文件来自定义配置")

# 创建全局配置实例
db_config = DatabaseConfig()