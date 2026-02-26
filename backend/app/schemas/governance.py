from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, ConfigDict

# =======================
# Column Schemas
# =======================
class GovernanceColumnBase(BaseModel):
    column_name: str
    data_type: str
    description: Optional[str] = None
    is_primary_key: bool = False
    is_nullable: bool = True
    security_level: Optional[str] = None
    data_standard: Optional[str] = None

class GovernanceColumnCreate(GovernanceColumnBase):
    pass

class GovernanceColumnUpdate(BaseModel):
    description: Optional[str] = None
    security_level: Optional[str] = None
    data_standard: Optional[str] = None

class GovernanceColumn(GovernanceColumnBase):
    id: int
    table_id: int
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

# =======================
# Table Schemas
# =======================
class GovernanceTableBase(BaseModel):
    schema_name: str
    table_name: str
    description: Optional[str] = None
    owner: Optional[str] = None
    classification_level: Optional[str] = None
    retention_period: Optional[int] = None
    tags: Optional[str] = None

class GovernanceTableCreate(GovernanceTableBase):
    datasource_id: int
    columns: Optional[List[GovernanceColumnCreate]] = None

class GovernanceTableUpdate(BaseModel):
    description: Optional[str] = None
    owner: Optional[str] = None
    classification_level: Optional[str] = None
    retention_period: Optional[int] = None
    tags: Optional[str] = None

class GovernanceTable(GovernanceTableBase):
    id: int
    datasource_id: int
    created_at: datetime
    updated_at: datetime
    columns: List[GovernanceColumn] = []
    
    model_config = ConfigDict(from_attributes=True)

class GovernanceTableList(GovernanceTableBase):
    """列表视图，不包含字段详情"""
    id: int
    datasource_id: int
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)
