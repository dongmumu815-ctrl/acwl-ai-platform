from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict

from app.models.application import AppType, AppStatus

# --- Harbor Config ---

class HarborConfigBase(BaseModel):
    name: str = Field(..., description="配置名称")
    url: str = Field(..., description="Harbor地址")
    username: Optional[str] = Field(None, description="用户名")
    password: Optional[str] = Field(None, description="密码")
    project: Optional[str] = Field(None, description="默认项目")
    is_default: bool = Field(False, description="是否默认仓库")
    description: Optional[str] = Field(None, description="描述")

class HarborConfigCreate(HarborConfigBase):
    pass

class HarborConfigUpdate(BaseModel):
    name: Optional[str] = None
    url: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None
    project: Optional[str] = None
    is_default: Optional[bool] = None
    description: Optional[str] = None

class HarborConfig(HarborConfigBase):
    id: int
    created_at: datetime
    updated_at: datetime
    created_by: Optional[int] = None
    updated_by: Optional[int] = None

    model_config = ConfigDict(from_attributes=True)

# --- App Template ---

class AppTemplateBase(BaseModel):
    name: str = Field(..., description="应用名称")
    display_name: Optional[str] = Field(None, description="显示名称")
    version: str = Field("latest", description="版本")
    description: Optional[str] = Field(None, description="应用描述")
    icon: Optional[str] = Field(None, description="应用图标")
    app_type: AppType = Field(..., description="应用类型")
    config_schema: Optional[Dict[str, Any]] = Field(None, description="配置参数Schema(JSON)")
    default_config: Optional[Dict[str, Any]] = Field(None, description="默认配置值(JSON)")
    deploy_template: Optional[str] = Field(None, description="部署模板")
    is_system: bool = Field(False, description="是否系统内置")

class AppTemplateCreate(AppTemplateBase):
    pass

class AppTemplateUpdate(BaseModel):
    name: Optional[str] = None
    display_name: Optional[str] = None
    version: Optional[str] = None
    description: Optional[str] = None
    icon: Optional[str] = None
    app_type: Optional[AppType] = None
    config_schema: Optional[Dict[str, Any]] = None
    default_config: Optional[Dict[str, Any]] = None
    deploy_template: Optional[str] = None
    is_system: Optional[bool] = None

class AppTemplate(AppTemplateBase):
    id: int
    created_at: datetime
    updated_at: datetime
    created_by: Optional[int] = None
    updated_by: Optional[int] = None

    model_config = ConfigDict(from_attributes=True)

# --- App Deployment ---

class AppDeploymentBase(BaseModel):
    server_id: int
    role: str = "default"
    cpu_limit: Optional[str] = None
    mem_limit: Optional[str] = None
    ports: Optional[Dict[str, Any]] = None

class AppDeploymentCreate(AppDeploymentBase):
    pass

class AppDeploymentUpdate(BaseModel):
    status: Optional[str] = None
    container_id: Optional[str] = None
    role: Optional[str] = None
    cpu_limit: Optional[str] = None
    mem_limit: Optional[str] = None
    ports: Optional[Dict[str, Any]] = None

class AppDeployment(AppDeploymentBase):
    id: int
    instance_id: int
    status: str
    container_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

# --- App Instance ---

class AppInstanceBase(BaseModel):
    name: str
    template_id: Optional[int] = None
    description: Optional[str] = None
    config: Optional[Dict[str, Any]] = None

class AppInstanceCreate(AppInstanceBase):
    deployments: List[AppDeploymentCreate] = Field(..., description="部署目标列表")

class AppInstanceUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[AppStatus] = None
    config: Optional[Dict[str, Any]] = None
    deployments: Optional[List[AppDeploymentCreate]] = Field(None, description="部署目标列表(全量覆盖)")

class AppInstance(AppInstanceBase):
    id: int
    status: AppStatus
    created_at: datetime
    updated_at: datetime
    created_by: Optional[int] = None
    updated_by: Optional[int] = None
    
    template: Optional[AppTemplate] = None
    deployments: List[AppDeployment] = []

    model_config = ConfigDict(from_attributes=True)
