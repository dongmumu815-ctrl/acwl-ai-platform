from sqlalchemy import Integer, String, Text, Boolean, DateTime, JSON, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from typing import Optional, List, Dict, Any, TYPE_CHECKING

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.datasource import Datasource
    from app.models.data_resource import DataResource


class SQLQueryTemplate(Base):
    """
    SQL查询模板模型
    用于存储用户保存的SQL查询模板和实例
    """
    
    __tablename__ = "sql_query_templates"
    __table_args__ = {"comment": "SQL查询模板表，存储用户保存的SQL查询模板和实例"}
    
    # 基础字段
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True, comment="主键ID")
    name: Mapped[str] = mapped_column(String(255), nullable=False, comment="模板名称")
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True, comment="模板描述")
    
    # 关联字段
    datasource_id: Mapped[int] = mapped_column(Integer, ForeignKey("acwl_datasources.id"), nullable=False, comment="数据源ID")
    data_resource_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("acwl_data_resources.id"), nullable=True, comment="数据资源ID")
    created_by: Mapped[int] = mapped_column(Integer, ForeignKey("acwl_users.id"), nullable=False, comment="创建者ID")
    
    # 查询内容
    query: Mapped[str] = mapped_column(Text, nullable=False, comment="SQL查询语句")
    tags: Mapped[Optional[List[str]]] = mapped_column(JSON, nullable=True, comment="标签列表")
    config: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True, comment="查询条件配置信息，包括必填条件、可选条件等")
    
    # 模板标识
    is_template: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, comment="是否为模板（True）还是查询实例（False）")
    
    # 时间戳
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), comment="创建时间")
    updated_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), comment="更新时间")
    
    # 关系映射
    datasource: Mapped["Datasource"] = relationship("Datasource", back_populates="sql_query_templates")
    data_resource: Mapped[Optional["DataResource"]] = relationship("DataResource", back_populates="sql_query_templates")
    creator: Mapped["User"] = relationship("User", back_populates="sql_query_templates")
    
    def to_dict(self) -> Dict[str, Any]:
        """
        将模型转换为字典格式
        
        Returns:
            Dict[str, Any]: 模型的字典表示
        """
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "datasourceId": self.datasource_id,
            "dataResourceId": self.data_resource_id,
            "query": self.query,
            "tags": self.tags or [],
            "config": self.config or {},
            "isTemplate": self.is_template,
            "createdBy": self.created_by,
            "createdAt": self.created_at.isoformat() if self.created_at else None,
            "updatedAt": self.updated_at.isoformat() if self.updated_at else None
        }
    
    def __repr__(self) -> str:
        return f"<SQLQueryTemplate(id={self.id}, name='{self.name}', datasource_id={self.datasource_id})>"