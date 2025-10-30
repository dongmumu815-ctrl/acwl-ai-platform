import { request } from '@/utils/request'
import type { PaginatedResponse } from '@/types/common'

// 部署状态枚举
export enum DeploymentStatus {
  DEPLOYING = 'deploying',
  RUNNING = 'running',
  STOPPED = 'stopped',
  FAILED = 'failed'
}

// 部署类型枚举
export enum DeploymentType {
  MODEL_INFERENCE = 'model_inference',
  API_SERVICE = 'api_service',
  BATCH_PROCESSING = 'batch_processing'
}

// 部署接口类型定义
export interface Deployment {
  id: number
  deployment_name: string
  model_name?: string
  deployment_type: DeploymentType
  status: DeploymentStatus
  server_id?: number
  port?: number
  endpoint_url?: string
  config?: Record<string, any>
  resource_requirements?: Record<string, any>
  created_by: number
  created_at: string
  updated_at: string
  env_id?: number
  description?: string
  // 关联的模型信息
  model?: {
    id: number
    name: string
    version: string
    model_type?: string
  }
  // 最新的metrics数据
  latest_metrics?: {
    cpu_utilization?: number
    memory_used?: string
    gpu_utilization?: any
    request_count?: number
    average_latency?: number
    error_count?: number
  }
}

// 部署创建/更新表单类型
export interface DeploymentForm {
  deployment_name: string
  model_name?: string
  deployment_type: DeploymentType
  server_id?: number
  port?: number
  config?: Record<string, any>
  resource_requirements?: Record<string, any>
  env_id?: number
  description?: string
}

// 部署查询参数类型
export interface DeploymentQueryParams {
  page?: number
  size?: number
  search?: string
  deployment_type?: DeploymentType
  status?: DeploymentStatus
  env_id?: number | string
  sort_by?: string
  sort_order?: 'asc' | 'desc'
}

// 部署统计信息接口
export interface DeploymentStats {
  total_count: number
  running_count: number
  stopped_count: number
  failed_count: number
  deploying_count: number
  total_requests: number
  type_stats: Record<string, number>
  status_distribution: Record<string, number>
}

// 部署API接口
export const deploymentApi = {
  /**
   * 获取部署列表
   */
  getDeployments(params?: DeploymentQueryParams): Promise<PaginatedResponse<Deployment>> {
    return request.get('/deployments/', params)
  },

  /**
   * 获取部署详情
   */
  getDeployment(deploymentId: number): Promise<Deployment> {
    return request.get(`/deployments/${deploymentId}`)
  },

  /**
   * 创建部署
   */
  createDeployment(data: DeploymentForm): Promise<{ id: number }> {
    return request.post('/deployments/', data)
  },

  /**
   * 更新部署
   */
  updateDeployment(deploymentId: number, data: Partial<DeploymentForm>): Promise<Deployment> {
    return request.put(`/deployments/${deploymentId}`, data)
  },

  /**
   * 删除部署
   */
  deleteDeployment(deploymentId: number): Promise<void> {
    return request.delete(`/deployments/${deploymentId}`)
  },

  /**
   * 启动部署
   */
  startDeployment(deploymentId: number): Promise<void> {
    return request.post(`/deployments/${deploymentId}/start`)
  },

  /**
   * 停止部署
   */
  stopDeployment(deploymentId: number): Promise<void> {
    return request.post(`/deployments/${deploymentId}/stop`)
  },

  /**
   * 重启部署
   */
  restartDeployment(deploymentId: number): Promise<void> {
    return request.post(`/deployments/${deploymentId}/restart`)
  },

  /**
   * 获取部署统计信息
   */
  getDeploymentStats(): Promise<DeploymentStats> {
    return request.get('/deployments/stats')
  },

  /**
   * 获取部署日志
   */
  getDeploymentLogs(deploymentId: number, lines: number = 100): Promise<{ logs: string[] }> {
    return request.get(`/deployments/${deploymentId}/logs`, {
      params: { lines }
    })
  },

  /**
   * 获取可用服务器
   */
  getAvailableServers(): Promise<any[]> {
    return request.get('/deployments/available-servers')
  },

  /**
   * 获取服务器GPU资源
   */
  getServerGPUs(serverId: number): Promise<any[]> {
    return request.get(`/deployments/server-gpus/${serverId}`)
  }
}

// 导出常用方法
export const {
  getDeployments,
  getDeployment,
  createDeployment,
  updateDeployment,
  deleteDeployment,
  startDeployment,
  stopDeployment,
  restartDeployment,
  getDeploymentStats,
  getDeploymentLogs,
  getAvailableServers,
  getServerGPUs
} = deploymentApi