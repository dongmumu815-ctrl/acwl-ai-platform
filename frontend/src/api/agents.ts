import request from '@/utils/request'
import type {
  Agent,
  AgentCreate,
  AgentUpdate,
  AgentResponse,
  AgentListResponse,
  AgentTool,
  AgentChat,
  AgentChatResponse,
  AgentStats,
  AgentConfig
} from '@/types/agent'

/**
 * 获取智能体列表
 * @param params 查询参数
 * @returns 智能体列表响应
 */
export function getAgents(params?: {
  page?: number
  size?: number
  search?: string
  agent_type?: string
  status?: string
  is_public?: boolean
  creator_id?: number
}) {
  return request<AgentListResponse>({
    url: '/agents/',
    method: 'get',
    params
  })
}

/**
 * 获取智能体详情
 * @param id 智能体ID
 * @returns 智能体详情
 */
export function getAgent(id: number) {
  return request<AgentResponse>({
    url: `/agents/${id}`,
    method: 'get'
  })
}

/**
 * 创建智能体
 * @param data 创建数据
 * @returns 创建的智能体
 */
export function createAgent(data: AgentCreate) {
  return request<AgentResponse>({
    url: '/agents/',
    method: 'post',
    data
  })
}

/**
 * 更新智能体
 * @param id 智能体ID
 * @param data 更新数据
 * @returns 更新的智能体
 */
export function updateAgent(id: number, data: AgentUpdate) {
  return request<AgentResponse>({
    url: `/agents/${id}`,
    method: 'put',
    data
  })
}

/**
 * 删除智能体
 * @param id 智能体ID
 */
export function deleteAgent(id: number) {
  return request({
    url: `/agents/${id}`,
    method: 'delete'
  })
}

/**
 * 获取智能体工具列表
 * @param id 智能体ID
 * @returns 工具列表
 */
export function getAgentTools(id: number) {
  return request<AgentTool[]>({
    url: `/agents/${id}/tools`,
    method: 'get'
  })
}

/**
 * 与智能体聊天
 * @param id 智能体ID
 * @param data 聊天数据
 * @returns 聊天响应
 */
export function chatWithAgent(id: number, data: AgentChat) {
  return request<AgentChatResponse>({
    url: `/agents/${id}/chat`,
    method: 'post',
    data: data,
    timeout: 600000 // 10分钟超时时间
  })
}

/**
 * 获取智能体统计信息
 * @param id 智能体ID
 * @returns 统计信息
 */
export function getAgentStats(id: number) {
  return request<AgentStats>({
    url: `/agents/${id}/stats`,
    method: 'get'
  })
}

/**
 * 验证智能体配置
 * @param config 配置数据
 * @returns 验证结果
 */
export function validateAgentConfig(config: AgentConfig) {
  return request<{ valid: boolean; errors?: string[] }>({
    url: '/agents/validate-config/',
    method: 'post',
    data: config
  })
}

/**
 * 复制智能体
 * @param id 智能体ID
 * @returns 复制的智能体
 */
export function cloneAgent(id: number) {
  return request<AgentResponse>({
    url: `/agents/${id}/clone`,
    method: 'post'
  })
}

/**
 * 导出智能体配置
 * @param id 智能体ID
 * @returns 配置文件
 */
export function exportAgent(id: number) {
  return request({
    url: `/agents/${id}/export`,
    method: 'get',
    responseType: 'blob'
  })
}

/**
 * 导入智能体配置
 * @param file 配置文件
 * @returns 导入的智能体
 */
export function importAgent(file: File) {
  const formData = new FormData()
  formData.append('file', file)
  
  return request<AgentResponse>({
    url: '/agents/import/',
    method: 'post',
    data: formData,
    headers: {
      'Content-Type': 'multipart/form-data'
    }
  })
}

/**
 * 获取异步任务状态
 * @param taskId 任务ID
 * @returns 任务状态信息
 */
export function getTaskStatus(taskId: string) {
  return request<{
    task_id: string
    status: string
    progress: number
    result?: any
    error?: string
    created_at?: string
    started_at?: string
    completed_at?: string
    metadata?: any
  }>({
    url: `/agents/tasks/${taskId}`,
    method: 'get'
  })
}

/**
 * 取消异步任务
 * @param taskId 任务ID
 * @returns 取消结果
 */
export function cancelTask(taskId: string) {
  return request<{ message: string }>({
    url: `/agents/tasks/${taskId}`,
    method: 'delete'
  })
}