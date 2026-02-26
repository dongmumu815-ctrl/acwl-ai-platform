/**
 * 智能体状态枚举
 */
export enum AgentStatus {
  ACTIVE = 'active',
  INACTIVE = 'inactive',
  DRAFT = 'draft',
  ARCHIVED = 'archived'
}

/**
 * 智能体类型枚举
 * 与后端保持一致，默认都使用CUSTOM类型
 */
export enum AgentType {
  CHAT = 'CHAT',
  CODE = 'CODE',
  DOCUMENT = 'DOCUMENT',
  ANALYSIS = 'ANALYSIS',
  WORKFLOW = 'WORKFLOW',
  REVIEW = 'REVIEW',
  CUSTOM = 'CUSTOM'
}



/**
 * 工具类型枚举
 */
export enum ToolType {
  BUILTIN = 'builtin',
  CUSTOM = 'custom',
  API = 'api',
  PLUGIN = 'plugin'
}

/**
 * 智能体基础信息
 */
export interface AgentBase {
  name: string
  description?: string
  agent_type: AgentType
  model_service_config_id: number
  system_prompt?: string
  user_prompt_template?: string
  temperature?: number
  max_tokens?: number
  top_p?: number
  frequency_penalty?: number
  presence_penalty?: number
  is_public?: boolean
  tags?: string[]
  model_params?: Record<string, any>
  instruction_set_id?: number  // 关联的指令集ID（仅REVIEW类型使用）
}

/**
 * 智能体创建数据
 */
export interface AgentCreate extends AgentBase {
  tools?: number[]
  permissions?: {
    allowed_users?: number[]
    allowed_roles?: string[]
    max_usage_per_user?: number
    max_usage_per_day?: number
  }
}

/**
 * 智能体更新数据
 */
export interface AgentUpdate extends Partial<AgentCreate> {}

/**
 * 智能体完整信息
 */
export interface Agent extends AgentBase {
  id: number
  status: AgentStatus
  creator_id: number
  creator_name?: string
  usage_count: number
  last_used_at?: string
  created_at: string
  updated_at: string
  tools?: AgentTool[]
  permissions?: AgentPermissions
  model?: {
    id: number
    name: string
    provider: string
  }
}

/**
 * 智能体工具
 */
export interface AgentTool {
  id: number
  name: string
  display_name: string
  description?: string
  tool_type: ToolType
  config_schema?: Record<string, any>
  default_config?: Record<string, any>
  code?: string
  is_enabled: boolean
  is_builtin: boolean
  created_at: string
  updated_at: string
}

export interface AgentToolCreate {
  name: string
  display_name: string
  description?: string
  tool_type: ToolType
  config_schema?: Record<string, any>
  default_config?: Record<string, any>
  code?: string
  is_enabled?: boolean
  is_builtin?: boolean
}

export interface AgentToolUpdate {
  display_name?: string
  description?: string
  tool_type?: ToolType
  config_schema?: Record<string, any>
  default_config?: Record<string, any>
  code?: string
  is_enabled?: boolean
}

/**
 * 代码生成请求
 */
export interface AgentToolGenerateRequest {
  requirements: string
  model_service_config_id?: number
}

/**
 * 代码生成响应
 */
export interface AgentToolGenerateResponse {
  code_structure: Record<string, string>
  raw_response: string
}

/**
 * 智能体权限配置
 */
export interface AgentPermissions {
  allowed_users?: number[]
  allowed_roles?: string[]
  max_usage_per_user?: number
  max_usage_per_day?: number
  created_at: string
  updated_at: string
}

/**
 * 智能体配置
 */
export interface AgentConfig {
  model_params: {
    temperature?: number
    max_tokens?: number
    top_p?: number
    frequency_penalty?: number
    presence_penalty?: number
  }
  prompt_config: {
    system_prompt?: string
    user_prompt_template?: string
  }
  tool_config: {
    enabled_tools: number[]
    tool_settings?: Record<string, any>
  }
  permission_config?: {
    allowed_users?: number[]
    allowed_roles?: string[]
    max_usage_per_user?: number
    max_usage_per_day?: number
  }
}

/**
 * 智能体聊天消息
 */
export interface AgentMessage {
  id?: string
  role: 'user' | 'assistant' | 'system'
  content: string
  timestamp?: string
  meta_data?: {
    thinking?: string
    tool_calls?: ToolCall[]
    usage?: {
      prompt_tokens: number
      completion_tokens: number
      total_tokens: number
    }
  }
}

/**
 * 工具调用信息
 */
export interface ToolCall {
  id: string
  name: string
  arguments: Record<string, any>
  result?: any
  error?: string
}

/**
 * 智能体聊天请求
 */
export interface AgentChat {
  message: string
  session_id?: string
  context?: Record<string, any>
  stream?: boolean
}

/**
 * 智能体聊天响应
 */
export interface AgentChatResponse {
  session_id: string
  message: string
  tokens_used?: number
  processing_time?: number
  metadata?: Record<string, any>
}

/**
 * 智能体统计信息
 */
export interface AgentStats {
  total_usage: number
  daily_usage: number
  weekly_usage: number
  monthly_usage: number
  avg_response_time: number
  success_rate: number
  last_7_days_usage: Array<{
    date: string
    count: number
  }>
  top_users: Array<{
    user_id: number
    user_name: string
    usage_count: number
  }>
}

/**
 * API响应包装
 */
export interface AgentResponse {
  data: Agent
  message: string
}

export interface AgentListResponse {
  data: {
    items: Agent[]
    total: number
    page: number
    size: number
    pages: number
  }
  message: string
}

/**
 * 智能体表单数据
 */
export interface AgentFormData extends AgentCreate {
  id?: number
}

/**
 * 智能体筛选参数
 */
export interface AgentFilterParams {
  search?: string
  agent_type?: AgentType
  category?: AgentCategory
  status?: AgentStatus
  is_public?: boolean
  creator_id?: number
  tags?: string[]
  page?: number
  size?: number
}

/**
 * 智能体导出配置
 */
export interface AgentExportConfig {
  include_conversations?: boolean
  include_statistics?: boolean
  format?: 'json' | 'yaml'
}

/**
 * 智能体导入结果
 */
export interface AgentImportResult {
  success: boolean
  agent?: Agent
  errors?: string[]
  warnings?: string[]
}