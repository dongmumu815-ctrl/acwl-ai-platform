/**
 * 指令集相关的TypeScript类型定义
 */

// 枚举类型
export enum InstructionSetStatus {
  DRAFT = 'DRAFT',
  ACTIVE = 'ACTIVE',
  INACTIVE = 'INACTIVE',
  ARCHIVED = 'ARCHIVED'
}

export enum NodeType {
  EXECUTOR = 'EXECUTOR',      // 执行器节点（根节点）
  CONDITION = 'CONDITION',    // 条件判断节点
  ACTION = 'ACTION',          // 动作执行节点
  BRANCH = 'BRANCH',          // 分支节点
  AGGREGATOR = 'AGGREGATOR',  // 聚合器节点
  CLASSIFIER = 'CLASSIFIER',  // 分类器节点
  RESULT = 'RESULT'           // 结果节点
}

export enum ConditionType {
  CONTAINS = 'CONTAINS',
  REGEX = 'REGEX',
  LENGTH = 'LENGTH',
  KEYWORD = 'KEYWORD',
  AI_CLASSIFICATION = 'AI_CLASSIFICATION',  // AI分类判断
  SENTIMENT_ANALYSIS = 'SENTIMENT_ANALYSIS', // 情感分析
  CONTENT_SAFETY = 'CONTENT_SAFETY',        // 内容安全检测
  CUSTOM_FUNCTION = 'CUSTOM_FUNCTION'       // 自定义函数
}

export enum ActionType {
  RETURN_TEXT = 'RETURN_TEXT',
  EXTRACT_INFO = 'EXTRACT_INFO',
  TRANSFORM = 'TRANSFORM',
  CLASSIFY = 'CLASSIFY',
  APPROVE = 'APPROVE',          // 通过审核
  REJECT = 'REJECT',            // 拒绝审核
  FLAG_CONTENT = 'FLAG_CONTENT', // 标记内容
  SEND_NOTIFICATION = 'SEND_NOTIFICATION', // 发送通知
  LOG_EVENT = 'LOG_EVENT',      // 记录事件
  CUSTOM_ACTION = 'CUSTOM_ACTION' // 自定义动作
}

export enum ExecutionStatus {
  SUCCESS = 'SUCCESS',
  FAILED = 'FAILED',
  TIMEOUT = 'TIMEOUT',
  PENDING = 'PENDING',
  CANCELLED = 'CANCELLED'
}

// 新增枚举类型
export enum LogicOperator {
  AND = 'AND',
  OR = 'OR',
  NOT = 'NOT'
}

export enum ExecutionStrategy {
  SEQUENTIAL = 'SEQUENTIAL',    // 顺序执行
  PARALLEL = 'PARALLEL',       // 并行执行
  CONDITIONAL = 'CONDITIONAL',  // 条件执行
  EARLY_STOP = 'EARLY_STOP'    // 早停执行
}

export enum ScoreType {
  ACCURACY = 'ACCURACY',        // 准确性
  CONFIDENCE = 'CONFIDENCE',    // 置信度
  PERFORMANCE = 'PERFORMANCE',  // 性能
  RELEVANCE = 'RELEVANCE',     // 相关性
  SAFETY = 'SAFETY'            // 安全性
}

export enum AggregationMethod {
  WEIGHTED_AVERAGE = 'WEIGHTED_AVERAGE',
  MAX_SCORE = 'MAX_SCORE',
  MIN_SCORE = 'MIN_SCORE',
  MAJORITY_VOTE = 'MAJORITY_VOTE',
  CONSENSUS = 'CONSENSUS'
}

export enum RiskLevel {
  SAFE = 'safe',
  LOW = 'low',
  MEDIUM = 'medium',
  HIGH = 'high',
  CRITICAL = 'critical'
}

// 基础接口
export interface InstructionSet {
  id: number;
  name: string;
  description?: string;
  version: string;
  status: InstructionSetStatus;
  created_by: number;
  created_at: string;
  updated_at: string;
  is_deleted: boolean;
}

export interface InstructionSetCreate {
  name: string;
  description?: string;
  version?: string;
  status?: InstructionSetStatus;
  created_by: number;
}

export interface InstructionSetUpdate {
  name?: string;
  description?: string;
  version?: string;
  status?: InstructionSetStatus;
}

export interface InstructionNode {
  id: number;
  instruction_set_id: number;
  parent_id?: number;
  title: string;
  description?: string;
  node_type: NodeType;
  condition_text?: string;      // 条件文本
  condition_type: ConditionType; // 条件类型
  keywords?: string;           // 关键词列表（逗号分隔）
  risk_level: RiskLevel;       // 风险等级
  metadata?: Record<string, any>; // 扩展元数据
  sort_order: number;
  is_active: boolean;
  created_at: string;
  updated_at: string;
  children?: InstructionNode[]; // 子节点列表
}

export interface InstructionNodeCreate {
  instruction_set_id?: number;
  parent_id?: number;
  title: string;
  description?: string;
  node_type: NodeType;
  condition_text?: string;
  condition_type?: ConditionType;
  keywords?: string;
  risk_level?: RiskLevel;
  metadata?: Record<string, any>;
  sort_order?: number;
  is_active?: boolean;
}

export interface InstructionNodeUpdate {
  parent_id?: number;
  title?: string;
  description?: string;
  node_type?: NodeType;
  condition_text?: string;
  condition_type?: ConditionType;
  keywords?: string;
  risk_level?: RiskLevel;
  metadata?: Record<string, any>;
  sort_order?: number;
  is_active?: boolean;
}

export interface InstructionExecution {
  id: number;
  instruction_set_id: number;
  input_text: string;
  execution_path?: string;
  final_result?: string;
  confidence_score?: number;
  execution_time_ms?: number;
  status: ExecutionStatus;
  error_message?: string;
  created_at: string;
}

export interface InstructionExecutionCreate {
  instruction_set_id: number;
  input_text: string;
  execution_path?: string;
  final_result?: string;
  confidence_score?: number;
  execution_time_ms?: number;
  status: ExecutionStatus;
  error_message?: string;
}

// 执行请求和响应
export interface InstructionExecuteRequest {
  instruction_set_id: number;
  input_text: string;
  save_execution?: boolean;
}

export interface InstructionExecuteResponse {
  execution_path: ExecutionPathItem[];
  final_result: string;
  confidence_score: number;
  execution_time_ms: number;
  metadata?: Record<string, any>;
  execution_id?: number;
}

export interface ExecutionPathItem {
  node_id: number;
  node_title: string;
  node_type: string;
  timestamp: number;
}

// 树形结构
export interface InstructionTreeNode {
  id: number;
  title: string;
  node_type: NodeType;
  parent_id?: number;
  keywords?: string;
  condition_text?: string;
  risk_level?: string;
  sort_order: number;
  is_active: boolean;
  node_number?: string;
  children: InstructionTreeNode[];
}

// 条件配置
export interface ConditionConfig {
  type: ConditionType;
  value: string;
  operator?: 'eq' | 'gt' | 'lt' | 'gte' | 'lte';
}

// 动作配置
export interface ActionConfig {
  type: ActionType;
  value: string;
  pattern?: string;
  transform_type?: 'upper' | 'lower' | 'title' | 'reverse';
  categories?: string[];
  keywords_map?: Record<string, string[]>;
}

// 统计信息
export interface InstructionSetStatistics {
  total_executions: number;
  success_executions: number;
  failed_executions: number;
  average_execution_time: number;
  average_confidence_score: number;
  most_used_paths: Array<{
    path: string;
    count: number;
  }>;
}

// API响应包装
export interface ApiResponse<T> {
  data: T;
  message?: string;
  success: boolean;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  size: number;
  pages: number;
}

export interface InstructionSetListResponse {
  success: boolean;
  data: InstructionSet[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
  has_next: boolean;
  has_prev: boolean;
}

// 查询参数
export interface InstructionSetQuery {
  skip?: number;
  limit?: number;
  status?: InstructionSetStatus;
  created_by?: number;
  search?: string;
}

export interface InstructionNodeQuery {
  instruction_set_id: number;
  parent_id?: number;
  skip?: number;
  limit?: number;
}

export interface InstructionExecutionQuery {
  instruction_set_id: number;
  skip?: number;
  limit?: number;
  status?: ExecutionStatus;
  start_date?: string;
  end_date?: string;
}

// 表单数据
export interface InstructionSetFormData {
  name: string;
  description: string;
  version: string;
  status: InstructionSetStatus;
}

export interface InstructionNodeFormData {
  title: string;
  description: string;
  node_type: NodeType;
  condition_text: string;
  condition_type: ConditionType;
  keywords: string[];
  metadata: Record<string, any>;
  sort_order: number;
  is_active: boolean;
}

// 树操作
export interface TreeOperation {
  type: 'add' | 'edit' | 'delete' | 'move';
  node?: InstructionTreeNode;
  parent_id?: number;
  new_parent_id?: number;
  sort_order?: number;
}

// 拖拽数据
export interface DragDropData {
  dragNode: InstructionTreeNode;
  dropNode: InstructionTreeNode;
  dropPosition: 'before' | 'after' | 'inside';
}

// 新增配置接口

/**
 * 执行器配置接口
 */
export interface ExecutorConfig {
  strategy: ExecutionStrategy;
  max_parallel_nodes?: number;
  timeout_ms?: number;
  retry_count?: number;
  early_stop_conditions?: EarlyStopCondition[];
  global_variables?: Record<string, any>;
}

/**
 * 早停条件配置
 */
export interface EarlyStopCondition {
  condition_type: 'confidence_threshold' | 'time_limit' | 'error_rate';
  threshold_value: number;
  operator: 'gt' | 'lt' | 'eq' | 'gte' | 'lte';
}

/**
 * 评分配置接口
 */
export interface ScoreConfig {
  enabled: boolean;
  score_types: ScoreType[];
  weights?: Record<ScoreType, number>;
  aggregation_method: AggregationMethod;
  min_threshold?: number;
  max_threshold?: number;
}

/**
 * 复杂条件配置接口
 */
export interface ComplexConditionConfig {
  logic_operator: LogicOperator;
  conditions: ConditionItem[];
  nested_groups?: ComplexConditionConfig[];
}

/**
 * 条件项接口
 */
export interface ConditionItem {
  id: string;
  type: ConditionType;
  field: string;
  operator: 'eq' | 'ne' | 'gt' | 'lt' | 'gte' | 'lte' | 'contains' | 'regex';
  value: any;
  weight?: number;
  description?: string;
}

/**
 * 聚合器配置接口
 */
export interface AggregatorConfig {
  input_nodes: number[];
  aggregation_method: AggregationMethod;
  weights?: Record<number, number>;
  conflict_resolution: 'highest_score' | 'majority_vote' | 'weighted_average';
  min_consensus_threshold?: number;
}

/**
 * 分类器配置接口
 */
export interface ClassifierConfig {
  categories: ClassificationCategory[];
  default_category?: string;
  confidence_threshold: number;
  multi_label: boolean;
  model_config?: {
    model_name: string;
    api_endpoint?: string;
    parameters?: Record<string, any>;
  };
}

/**
 * 分类类别接口
 */
export interface ClassificationCategory {
  id: string;
  name: string;
  description?: string;
  keywords?: string[];
  patterns?: string[];
  examples?: string[];
  weight?: number;
}

/**
 * 执行结果接口
 */
export interface NodeExecutionResult {
  node_id: number;
  status: ExecutionStatus;
  result: any;
  scores?: Record<ScoreType, number>;
  execution_time_ms: number;
  error_message?: string;
  metadata?: Record<string, any>;
}

/**
 * 指令集执行上下文
 */
export interface ExecutionContext {
  input_data: any;
  variables: Record<string, any>;
  execution_path: number[];
  current_node_id?: number;
  start_time: number;
  timeout_ms?: number;
  user_id?: number;
  session_id?: string;
}