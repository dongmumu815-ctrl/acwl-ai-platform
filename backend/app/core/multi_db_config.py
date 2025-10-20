#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
多数据库配置管理模块
支持配置和管理多个数据库连接
"""

from pydantic import BaseModel, Field
from typing import Dict, Optional, List, Any
from enum import Enum
import os
import json
from pathlib import Path


class DatabaseType(str, Enum):
    """数据库类型枚举"""
    MYSQL = "mysql"
    POSTGRESQL = "postgresql"
    SQLITE = "sqlite"
    ORACLE = "oracle"
    SQLSERVER = "sqlserver"
    MONGODB = "mongodb"


class DatabaseConfig(BaseModel):
    """单个数据库配置"""
    name: str = Field(..., description="数据库配置名称")
    type: DatabaseType = Field(..., description="数据库类型")
    host: str = Field(..., description="数据库主机")
    port: int = Field(..., description="数据库端口")
    username: str = Field(..., description="数据库用户名")
    password: str = Field(..., description="数据库密码")
    database: str = Field(..., description="数据库名称")
    charset: str = Field(default="utf8mb4", description="字符集")
    
    # 连接池配置
    pool_size: int = Field(default=10, description="连接池大小")
    max_overflow: int = Field(default=20, description="最大溢出连接数")
    pool_timeout: int = Field(default=30, description="连接池超时时间")
    pool_recycle: int = Field(default=3600, description="连接回收时间")
    
    # 额外连接参数
    extra_params: Optional[Dict[str, Any]] = Field(default=None, description="额外连接参数")
    
    # 业务标识
    business_tags: List[str] = Field(default=[], description="业务标签，用于路由选择")
    is_primary: bool = Field(default=False, description="是否为主数据库")
    is_active: bool = Field(default=True, description="是否激活")
    
    @property
    def connection_url(self) -> str:
        """
        生成数据库连接URL
        
        Returns:
            str: 数据库连接URL
        """
        if self.type == DatabaseType.MYSQL:
            return f"mysql+aiomysql://{self.username}:{self.password}@{self.host}:{self.port}/{self.database}?charset={self.charset}"
        elif self.type == DatabaseType.POSTGRESQL:
            return f"postgresql+asyncpg://{self.username}:{self.password}@{self.host}:{self.port}/{self.database}"
        elif self.type == DatabaseType.SQLITE:
            return f"sqlite+aiosqlite:///{self.database}"
        elif self.type == DatabaseType.ORACLE:
            return f"oracle+cx_oracle_async://{self.username}:{self.password}@{self.host}:{self.port}/{self.database}"
        elif self.type == DatabaseType.SQLSERVER:
            return f"mssql+aioodbc://{self.username}:{self.password}@{self.host}:{self.port}/{self.database}?driver=ODBC+Driver+17+for+SQL+Server"
        else:
            raise ValueError(f"不支持的数据库类型: {self.type}")
    
    @property
    def sync_connection_url(self) -> str:
        """
        生成同步数据库连接URL
        
        Returns:
            str: 同步数据库连接URL
        """
        if self.type == DatabaseType.MYSQL:
            return f"mysql+pymysql://{self.username}:{self.password}@{self.host}:{self.port}/{self.database}?charset={self.charset}"
        elif self.type == DatabaseType.POSTGRESQL:
            return f"postgresql+psycopg2://{self.username}:{self.password}@{self.host}:{self.port}/{self.database}"
        elif self.type == DatabaseType.SQLITE:
            return f"sqlite:///{self.database}"
        elif self.type == DatabaseType.ORACLE:
            return f"oracle+cx_oracle://{self.username}:{self.password}@{self.host}:{self.port}/{self.database}"
        elif self.type == DatabaseType.SQLSERVER:
            return f"mssql+pyodbc://{self.username}:{self.password}@{self.host}:{self.port}/{self.database}?driver=ODBC+Driver+17+for+SQL+Server"
        else:
            raise ValueError(f"不支持的数据库类型: {self.type}")


class MultiDatabaseConfig:
    """多数据库配置管理器"""
    
    def __init__(self, config_file: Optional[str] = None):
        """
        初始化多数据库配置管理器
        
        Args:
            config_file: 配置文件路径，默认为 multi_db_config.json
        """
        self.config_file = config_file or "multi_db_config.json"
        self.databases: Dict[str, DatabaseConfig] = {}
        self._load_config()
    
    def _load_config(self):
        """从配置文件加载数据库配置"""
        config_path = Path(self.config_file)
        
        if config_path.exists():
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    config_data = json.load(f)
                
                for db_name, db_config in config_data.get('databases', {}).items():
                    self.databases[db_name] = DatabaseConfig(**db_config)
                    
            except Exception as e:
                print(f"加载数据库配置文件失败: {e}")
        else:
            # 创建默认配置
            self._create_default_config()
    
    def _create_default_config(self):
        """创建默认配置"""
        # 主数据库配置（从环境变量或默认值获取）
        primary_db = DatabaseConfig(
            name="primary",
            type=DatabaseType.MYSQL,
            host=os.getenv("DB_HOST", "10.20.1.200"),
            port=int(os.getenv("DB_PORT", "3306")),
            username=os.getenv("DB_USER", "root"),
            password=os.getenv("DB_PASSWORD", "2wsx1QAZaczt"),
            database=os.getenv("DB_NAME", "acwl-ai-data"),
            charset=os.getenv("DB_CHARSET", "utf8mb4"),
            business_tags=["primary", "main", "core"],
            is_primary=True
        )
        
        self.databases["primary"] = primary_db
        self.save_config()
    
    def add_database(self, db_config: DatabaseConfig) -> bool:
        """
        添加数据库配置
        
        Args:
            db_config: 数据库配置对象
            
        Returns:
            bool: 是否添加成功
        """
        try:
            self.databases[db_config.name] = db_config
            self.save_config()
            return True
        except Exception as e:
            print(f"添加数据库配置失败: {e}")
            return False
    
    def remove_database(self, db_name: str) -> bool:
        """
        移除数据库配置
        
        Args:
            db_name: 数据库配置名称
            
        Returns:
            bool: 是否移除成功
        """
        try:
            if db_name in self.databases:
                # 不允许删除主数据库
                if self.databases[db_name].is_primary:
                    print("不能删除主数据库配置")
                    return False
                
                del self.databases[db_name]
                self.save_config()
                return True
            return False
        except Exception as e:
            print(f"移除数据库配置失败: {e}")
            return False
    
    def get_database(self, db_name: str) -> Optional[DatabaseConfig]:
        """
        获取数据库配置
        
        Args:
            db_name: 数据库配置名称
            
        Returns:
            DatabaseConfig: 数据库配置对象
        """
        return self.databases.get(db_name)
    
    def get_primary_database(self) -> Optional[DatabaseConfig]:
        """
        获取主数据库配置
        
        Returns:
            DatabaseConfig: 主数据库配置对象
        """
        for db_config in self.databases.values():
            if db_config.is_primary:
                return db_config
        return None
    
    def get_databases_by_tag(self, tag: str) -> List[DatabaseConfig]:
        """
        根据业务标签获取数据库配置列表
        
        Args:
            tag: 业务标签
            
        Returns:
            List[DatabaseConfig]: 数据库配置列表
        """
        return [
            db_config for db_config in self.databases.values()
            if tag in db_config.business_tags and db_config.is_active
        ]
    
    def get_all_databases(self) -> Dict[str, DatabaseConfig]:
        """
        获取所有数据库配置
        
        Returns:
            Dict[str, DatabaseConfig]: 所有数据库配置
        """
        return self.databases.copy()
    
    def save_config(self):
        """保存配置到文件"""
        try:
            config_data = {
                "databases": {
                    name: db_config.dict() for name, db_config in self.databases.items()
                }
            }
            
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, ensure_ascii=False, indent=2)
                
        except Exception as e:
            print(f"保存数据库配置文件失败: {e}")


# 全局多数据库配置管理器实例
multi_db_config = MultiDatabaseConfig()