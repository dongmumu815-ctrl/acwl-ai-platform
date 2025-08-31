from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, Enum, ForeignKey, JSON, DECIMAL
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base
import enum


class InstructionSetStatus(str, enum.Enum):
    """指令集状态枚举"""
    ACTIVE = "ACTIVE"      # 激活
    INACTIVE = "INACTIVE"  # 未激活
    DRAFT = "DRAFT"        # 草稿


class NodeType(str, enum.Enum):
    """节点类型枚举"""
    EXECUTOR = "EXECUTOR"      # 执行器节点
    CONDITION = "CONDITION"    # 条件节点
    ACTION = "ACTION"          # 动作节点
    BRANCH = "BRANCH"          # 分支节点
    AGGREGATOR = "AGGREGATOR"  # 聚合器节点
    CLASSIFIER = "CLASSIFIER"  # 分类器节点
    RESULT = "RESULT"          # 结果节点


class ConditionType(str, enum.Enum):
    """条件类型枚举"""
    TEXT_ANALYSIS = "TEXT_ANALYSIS"        # 文本分析
    KEYWORD_MATCH = "KEYWORD_MATCH"        # 关键词匹配
    REGEX_MATCH = "REGEX_MATCH"            # 正则匹配
    AI_CLASSIFICATION = "AI_CLASSIFICATION" # AI分类
    SENTIMENT_ANALYSIS = "SENTIMENT_ANALYSIS" # 情感分析
    CONTENT_SAFETY = "CONTENT_SAFETY"      # 内容安全检测
    CUSTOM_FUNCTION = "CUSTOM_FUNCTION"    # 自定义函数
    CONTAINS = "CONTAINS"                  # 包含检测
    REGEX = "REGEX"                        # 正则表达式
    LENGTH = "LENGTH"                      # 长度检测
    KEYWORD = "KEYWORD"                    # 关键词检测


class ActionType(str, enum.Enum):
    """动作类型枚举"""
    CONTINUE = "CONTINUE"              # 继续
    STOP = "STOP"                      # 停止
    BRANCH = "BRANCH"                  # 分支
    CLASSIFY = "CLASSIFY"              # 分类
    APPROVE = "APPROVE"                # 批准
    REJECT = "REJECT"                  # 拒绝
    FLAG_CONTENT = "FLAG_CONTENT"      # 标记内容
    SEND_NOTIFICATION = "SEND_NOTIFICATION"  # 发送通知
    LOG_EVENT = "LOG_EVENT"            # 记录事件
    CUSTOM_ACTION = "CUSTOM_ACTION"    # 自定义动作
    ESCALATE = "ESCALATE"              # 升级处理


class ExecutionStatus(str, enum.Enum):
    """执行状态枚举"""
    SUCCESS = "SUCCESS"  # 成功
    FAILED = "FAILED"    # 失败
    TIMEOUT = "TIMEOUT"  # 超时


class InstructionSet(Base):
    """指令集模型"""
    __tablename__ = "instruction_sets"

    id = Column(Integer, primary_key=True, index=True, comment="主键ID")
    name = Column(String(255), nullable=False, index=True, comment="指令集名称")
    description = Column(Text, comment="指令集描述")
    version = Column(String(50), default="1.0.0", comment="版本号")
    status = Column(Enum(InstructionSetStatus), default=InstructionSetStatus.DRAFT, index=True, comment="状态")
    created_by = Column(Integer, index=True, comment="创建者ID")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), comment="更新时间")

    # 关系
    nodes = relationship("InstructionNode", back_populates="instruction_set", cascade="all, delete-orphan")
    executions = relationship("InstructionExecution", back_populates="instruction_set", cascade="all, delete-orphan")


class RiskLevel(str, enum.Enum):
    """风险等级枚举"""
    safe = "safe"
    low = "low"
    medium = "medium"
    high = "high"
    critical = "critical"


class InstructionNode(Base):
    """指令节点模型"""
    __tablename__ = "instruction_nodes"

    id = Column(Integer, primary_key=True, index=True, comment="主键ID")
    instruction_set_id = Column(Integer, ForeignKey("instruction_sets.id", ondelete="CASCADE"), nullable=False, index=True, comment="所属指令集ID")
    parent_id = Column(Integer, ForeignKey("instruction_nodes.id", ondelete="CASCADE"), nullable=True, index=True, comment="父节点ID")
    node_type = Column(Enum(NodeType), nullable=False, index=True, comment="节点类型")
    title = Column(String(255), nullable=False, comment="节点标题")
    description = Column(Text, comment="节点描述")
    keywords = Column(Text, comment="关键词")
    condition_text = Column(Text, comment="条件文本")
    condition_type = Column(Enum(ConditionType), default=ConditionType.AI_CLASSIFICATION, comment="条件类型")
    action_type = Column(Enum(ActionType), default=ActionType.CONTINUE, comment="动作类型")
    result_value = Column(String(500), comment="结果值")
    result_confidence = Column(DECIMAL(3, 2), default=0.00, comment="结果置信度")
    risk_level = Column(Enum(RiskLevel), default=RiskLevel.medium, comment="风险等级")
    sort_order = Column(Integer, default=0, index=True, comment="排序顺序")
    is_active = Column(Boolean, default=True, index=True, comment="是否激活")
    meta_data = Column(JSON, comment="扩展元数据")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), comment="更新时间")

    # 关系
    instruction_set = relationship("InstructionSet", back_populates="nodes")
    parent = relationship("InstructionNode", remote_side=[id])


class InstructionExecution(Base):
    """指令执行历史模型"""
    __tablename__ = "instruction_executions"

    id = Column(Integer, primary_key=True, index=True, comment="主键ID")
    instruction_set_id = Column(Integer, ForeignKey("instruction_sets.id", ondelete="CASCADE"), nullable=False, index=True, comment="指令集ID")
    input_text = Column(Text, nullable=False, comment="输入文本")
    execution_path = Column(JSON, comment="执行路径")
    final_result = Column(String(500), comment="最终结果")
    confidence_score = Column(DECIMAL(3, 2), comment="置信度分数")
    execution_time_ms = Column(Integer, comment="执行时间（毫秒）")
    status = Column(Enum(ExecutionStatus), default=ExecutionStatus.SUCCESS, index=True, comment="执行状态")
    error_message = Column(Text, comment="错误信息")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True, comment="创建时间")

    # 关系
    instruction_set = relationship("InstructionSet", back_populates="executions")