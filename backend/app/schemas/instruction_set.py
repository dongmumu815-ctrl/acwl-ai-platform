from typing import List, Optional, Dict, Any
from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, Field
from app.models.instruction_set import (
    InstructionSetStatus, NodeType, ConditionType, ActionType, ExecutionStatus, RiskLevel
)


class InstructionSetBase(BaseModel):
    """指令集基础模型"""
    name: str = Field(..., description="指令集名称")
    description: Optional[str] = Field(None, description="指令集描述")
    version: str = Field(default="1.0.0", description="版本号")
    status: InstructionSetStatus = Field(default=InstructionSetStatus.DRAFT, description="状态")


class InstructionSetCreate(InstructionSetBase):
    """创建指令集请求模型"""
    created_by: Optional[int] = Field(None, description="创建者ID")


class InstructionSetUpdate(BaseModel):
    """更新指令集请求模型"""
    name: Optional[str] = Field(None, description="指令集名称")
    description: Optional[str] = Field(None, description="指令集描述")
    version: Optional[str] = Field(None, description="版本号")
    status: Optional[InstructionSetStatus] = Field(None, description="状态")


class InstructionNodeBase(BaseModel):
    """指令节点基础模型"""
    parent_id: Optional[int] = Field(None, description="父节点ID")
    node_type: NodeType = Field(..., description="节点类型")
    title: str = Field(..., description="节点标题")
    description: Optional[str] = Field(None, description="节点描述")
    keywords: Optional[str] = Field(None, description="关键词")
    condition_text: Optional[str] = Field(None, description="条件文本")
    condition_type: ConditionType = Field(default=ConditionType.AI_CLASSIFICATION, description="条件类型")
    action_type: ActionType = Field(default=ActionType.CONTINUE, description="动作类型")
    result_value: Optional[str] = Field(None, description="结果值")
    result_confidence: Decimal = Field(default=Decimal('0.00'), description="结果置信度")
    risk_level: RiskLevel = Field(default=RiskLevel.medium, description="风险等级")
    sort_order: int = Field(default=0, description="排序顺序")
    is_active: bool = Field(default=True, description="是否激活")
    meta_data: Optional[Dict[str, Any]] = Field(None, description="扩展元数据", alias="metadata")


class InstructionNodeCreate(InstructionNodeBase):
    """创建指令节点请求模型"""
    instruction_set_id: int = Field(..., description="所属指令集ID")


class InstructionNodeUpdate(BaseModel):
    """更新指令节点请求模型"""
    parent_id: Optional[int] = Field(None, description="父节点ID")
    node_type: Optional[NodeType] = Field(None, description="节点类型")
    title: Optional[str] = Field(None, description="节点标题")
    description: Optional[str] = Field(None, description="节点描述")
    keywords: Optional[str] = Field(None, description="关键词")
    condition_text: Optional[str] = Field(None, description="条件文本")
    condition_type: Optional[ConditionType] = Field(None, description="条件类型")
    action_type: Optional[ActionType] = Field(None, description="动作类型")
    result_value: Optional[str] = Field(None, description="结果值")
    result_confidence: Optional[Decimal] = Field(None, description="结果置信度")
    risk_level: Optional[RiskLevel] = Field(None, description="风险等级")
    sort_order: Optional[int] = Field(None, description="排序顺序")
    is_active: Optional[bool] = Field(None, description="是否激活")
    meta_data: Optional[Dict[str, Any]] = Field(None, description="扩展元数据", alias="metadata")


class InstructionNode(InstructionNodeBase):
    """指令节点响应模型"""
    id: int = Field(..., description="节点ID")
    instruction_set_id: int = Field(..., description="所属指令集ID")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")
    children: List['InstructionNode'] = Field(default=[], description="子节点列表")

    class Config:
        from_attributes = True


class InstructionSet(InstructionSetBase):
    """指令集响应模型"""
    id: int = Field(..., description="指令集ID")
    created_by: Optional[int] = Field(None, description="创建者ID")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")

    class Config:
        from_attributes = True


class InstructionSetWithNodes(InstructionSet):
    """包含节点的指令集响应模型"""
    nodes: List[InstructionNode] = Field(default=[], description="节点列表")
    executions: List['InstructionExecution'] = Field(default=[], description="执行记录列表")

    class Config:
        from_attributes = True


class InstructionExecutionBase(BaseModel):
    """指令执行基础模型"""
    input_text: str = Field(..., description="输入文本")
    execution_path: Optional[List[int]] = Field(None, description="执行路径")
    final_result: Optional[str] = Field(None, description="最终结果")
    confidence_score: Optional[Decimal] = Field(None, description="置信度分数")
    execution_time_ms: Optional[int] = Field(None, description="执行时间（毫秒）")
    status: ExecutionStatus = Field(default=ExecutionStatus.SUCCESS, description="执行状态")
    error_message: Optional[str] = Field(None, description="错误信息")


class InstructionExecutionCreate(InstructionExecutionBase):
    """创建指令执行请求模型"""
    instruction_set_id: int = Field(..., description="指令集ID")


class InstructionExecution(InstructionExecutionBase):
    """指令执行响应模型"""
    id: int = Field(..., description="执行ID")
    instruction_set_id: int = Field(..., description="指令集ID")
    created_at: datetime = Field(..., description="创建时间")

    class Config:
        from_attributes = True


class InstructionExecuteRequest(BaseModel):
    """执行指令集请求模型"""
    instruction_set_id: int = Field(..., description="指令集ID")
    input_text: str = Field(..., description="输入文本")
    save_execution: bool = Field(default=True, description="是否保存执行记录")


class InstructionExecuteResponse(BaseModel):
    """执行指令集响应模型"""
    final_result: str = Field(..., description="最终结果")
    confidence_score: Decimal = Field(..., description="置信度分数")
    execution_path: List[int] = Field(..., description="执行路径")
    execution_time_ms: int = Field(..., description="执行时间（毫秒）")
    execution_id: Optional[int] = Field(None, description="执行记录ID")


class InstructionTreeNode(BaseModel):
    """指令树节点模型"""
    id: int = Field(..., description="节点ID")
    title: str = Field(..., description="节点标题")
    node_type: NodeType = Field(..., description="节点类型")
    parent_id: Optional[int] = Field(None, description="父节点ID")
    keywords: Optional[str] = Field(None, description="关键词")
    condition_text: Optional[str] = Field(None, description="条件文本")
    risk_level: RiskLevel = Field(default=RiskLevel.medium, description="风险等级")
    sort_order: int = Field(..., description="排序顺序")
    is_active: bool = Field(..., description="是否激活")
    node_number: str = Field(..., description="节点编号")
    children: List['InstructionTreeNode'] = Field(default=[], description="子节点")


class PaginatedResponse(BaseModel):
    """分页响应模型"""
    success: bool = Field(default=True, description="请求是否成功")
    data: List[Any] = Field(..., description="数据列表")
    total: int = Field(..., description="总记录数")
    page: int = Field(..., description="当前页码")
    page_size: int = Field(..., description="每页大小")
    total_pages: int = Field(..., description="总页数")
    has_next: bool = Field(..., description="是否有下一页")
    has_prev: bool = Field(..., description="是否有上一页")


class InstructionSetListResponse(BaseModel):
    """指令集列表响应模型"""
    success: bool = Field(default=True, description="请求是否成功")
    data: List[InstructionSet] = Field(..., description="指令集列表")
    total: int = Field(..., description="总记录数")
    page: int = Field(..., description="当前页码")
    page_size: int = Field(..., description="每页大小")
    total_pages: int = Field(..., description="总页数")
    has_next: bool = Field(..., description="是否有下一页")
    has_prev: bool = Field(..., description="是否有上一页")


# 解决前向引用问题
InstructionNode.model_rebuild()
InstructionTreeNode.model_rebuild()