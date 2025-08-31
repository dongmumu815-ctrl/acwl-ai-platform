import { request } from '@/utils/request'
import type { PaginatedResponse } from '@/types/common'

// 模型类型枚举
export enum ModelType {
  LLM = 'LLM',
  EMBEDDING = 'EMBEDDING',
  MULTIMODAL = 'MULTIMODAL',
  OTHER = 'OTHER'
}

// 模型接口类型定义
export interface Model {
  id: number
  name: string
  version: string
  description?: string
  base_model?: string
  model_type: ModelType
  model_size?: number
  parameters?: number
  framework?: string
  quantization?: string
  source_url?: string
  local_path?: string
  is_active: boolean
  created_at: string
  updated_at: string
}

// 模型创建/更新表单类型
export interface ModelForm {
  name: string
  version: string
  description?: string
  base_model?: string
  model_type: ModelType
  model_size?: number
  parameters?: number
  framework?: string
  quantization?: string
  source_url?: string
  local_path?: string
  is_active?: boolean
}

// 模型查询参数类型
export interface ModelQueryParams {
  page?: number
  size?: number
  search?: string
  model_type?: ModelType
  is_active?: boolean
}

// 模型API接口
export const modelApi = {
  /**
   * 获取模型列表
   * @param params 查询参数
   * @returns 分页的模型列表
   */
  getModels(params?: ModelQueryParams) {
    return request.get<PaginatedResponse<Model>>('/models/', { params })
  },

  /**
   * 获取模型详情
   * @param modelId 模型ID
   * @returns 模型详情
   */
  getModel(modelId: number) {
    return request.get<Model>(`/models/${modelId}`)
  },

  /**
   * 创建模型
   * @param data 模型数据
   * @returns 创建结果
   */
  createModel(data: ModelForm) {
    return request.post<{ id: number; message: string }>('/models/', data)
  },

  /**
   * 更新模型
   * @param modelId 模型ID
   * @param data 更新数据
   * @returns 更新结果
   */
  updateModel(modelId: number, data: Partial<ModelForm>) {
    return request.put<{ message: string }>(`/models/${modelId}`, data)
  },

  /**
   * 删除模型
   * @param modelId 模型ID
   * @returns 删除结果
   */
  deleteModel(modelId: number) {
    return request.delete<{ message: string }>(`/models/${modelId}`)
  },

  /**
   * 强制删除模型
   * @param modelId 模型ID
   * @returns 删除结果
   */
  forceDeleteModel(modelId: number) {
    return request.delete<{ message: string }>(`/models/${modelId}`)
  },

  /**
   * 批量删除模型
   * @param modelIds 模型ID数组
   * @returns 删除结果
   */
  batchDeleteModels(modelIds: number[]) {
    return request.post<{ message: string }>('/models/batch-delete', { model_ids: modelIds })
  },

  /**
   * 上传模型文件
   * @param formData 包含文件和元数据的FormData
   * @returns 上传结果
   */
  uploadModel(formData: FormData) {
    return request.post<{ id: number; message: string }>('/models/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })
  },

  /**
   * 获取模型下载链接
   * @param modelId 模型ID
   * @returns 下载链接
   */
  getDownloadUrl(modelId: number) {
    return request.get<{ url: string }>(`/models/${modelId}/download`)
  },

  /**
   * 克隆模型
   * @param modelId 模型ID
   * @param newName 新模型名称
   * @returns 克隆结果
   */
  cloneModel(modelId: number, newName: string) {
    return request.post<{ id: number; message: string }>(`/models/${modelId}/clone`, { name: newName })
  },

  /**
   * 激活/停用模型
   * @param modelId 模型ID
   * @param isActive 是否激活
   * @returns 操作结果
   */
  toggleModelStatus(modelId: number, isActive: boolean) {
    return request.patch<{ message: string }>(`/models/${modelId}/status`, { is_active: isActive })
  },

  /**
   * 获取模型统计信息
   * @returns 统计数据
   */
  getModelStats() {
    return request.get<{
      total: number
      active: number
      training: number
      totalSize: number
    }>('/models/stats')
  },

  /**
   * 获取可用于Agent的模型列表
   * @returns 可用模型列表，格式化为下拉选择所需的格式
   */
  getAvailableModelsForAgents() {
    return request.get<Array<{
      label: string
      value: string
      model_id: number
      description?: string
    }>>('/models/available-for-agents')
  }
}