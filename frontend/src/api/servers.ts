/**
 * 服务器管理相关的API接口
 */
import { request } from '@/utils/request'

/**
 * 服务器表单数据接口
 */
export interface ServerForm {
  /** 服务器名称 */
  name: string
  /** IP地址 */
  ip_address: string
  /** SSH端口 */
  ssh_port: number
  /** SSH用户名 */
  ssh_username: string
  /** SSH密码 */
  ssh_password: string
  /** SSH密钥文件路径（可选） */
  ssh_key_path?: string
  /** 服务器类型 */
  server_type: string
  /** 操作系统信息 */
  os_info: string
  /** 总内存 */
  total_memory: string
  /** 总存储 */
  total_storage: string
  /** CPU核心数 */
  total_cpu_cores: number | null
}

/**
 * 服务器响应数据接口
 */
export interface ServerResponse extends ServerForm {
  /** 服务器ID */
  id: number
  /** 服务器状态 */
  status?: string
  /** GPU数量 */
  gpu_count?: number
  /** 部署数量 */
  deployment_count?: number
  /** 创建时间 */
  created_at?: string
  /** 更新时间 */
  updated_at?: string
}

/**
 * API响应包装接口
 */
export interface ApiResponse<T = any> {
  /** 响应数据 */
  data: T
  /** 响应消息 */
  message?: string
  /** 响应状态码 */
  code?: number
}

/**
 * 分页响应接口
 */
export interface PaginatedResponse<T = any> {
  /** 数据列表 */
  data: T[]
  /** 总数量 */
  total: number
  /** 当前页 */
  page: number
  /** 每页大小 */
  size: number
}

/**
 * 创建服务器
 * @param data 服务器表单数据
 * @returns Promise<ApiResponse<ServerResponse>>
 */
export function createServer(data: ServerForm): Promise<ApiResponse<ServerResponse>> {
  return request.post('/servers/', data)
}

/**
 * 更新服务器
 * @param id 服务器ID
 * @param data 服务器表单数据
 * @returns Promise<ApiResponse<ServerResponse>>
 */
export function updateServer(id: number, data: ServerForm): Promise<ApiResponse<ServerResponse>> {
  return request.put(`/servers/${id}`, data)
}

/**
 * 获取服务器列表
 * @param params 查询参数
 * @returns Promise<ApiResponse<PaginatedResponse<ServerResponse>>>
 */
export function getServers(params?: {
  page?: number
  size?: number
  search?: string
  server_type?: string
  status?: string
}): Promise<ApiResponse<PaginatedResponse<ServerResponse>>> {
  return request.get('/servers/', params)
}

/**
 * 删除服务器
 * @param id 服务器ID
 * @returns Promise<ApiResponse<void>>
 */
export function deleteServer(id: number): Promise<ApiResponse<void>> {
  return request.delete(`/servers/${id}`)
}

/**
 * 根据ID获取服务器详情
 * @param id 服务器ID
 * @returns Promise<ApiResponse<ServerResponse>>
 */
export function getServerById(id: number): Promise<ApiResponse<ServerResponse>> {
  return request.get(`/servers/${id}`)
}

/**
 * 测试服务器连接
 * @param id 服务器ID
 * @returns Promise<ApiResponse<{ status: string; message: string }>>
 */
export function testServerConnection(id: number): Promise<ApiResponse<{ status: string; message: string }>> {
  return request.post(`/servers/${id}/test-connection`)
}

/**
 * 获取服务器GPU资源
 * @param id 服务器ID
 * @returns Promise<ApiResponse<any[]>>
 */
export function getServerGpuResources(id: number): Promise<ApiResponse<any[]>> {
  return request.get(`/servers/${id}/gpu-resources`)
}

/**
 * 扫描服务器GPU
 * @param id 服务器ID
 * @returns Promise<ApiResponse<any[]>>
 */
export function scanServerGpus(id: number): Promise<ApiResponse<any[]>> {
  return request.post(`/servers/${id}/scan-gpus`)
}

/**
 * 获取服务器统计数据
 * @returns Promise<ApiResponse<{ total: number; online: number; offline: number; total_gpus: number }>>
 */
export function getServerStats(): Promise<ApiResponse<{ total: number; online: number; offline: number; total_gpus: number }>> {
  return request.get('/servers/stats')
}
