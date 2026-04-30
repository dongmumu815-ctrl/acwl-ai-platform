import { request } from '@/utils/request'

export interface Dataset {
  id: number
  name: string
  description: string
  dataset_type: 'text' | 'image' | 'audio' | 'video' | 'multimodal'
  format: string | null
  is_public: boolean
  tags: string[]
  size: number | null
  record_count: number | null
  storage_path: string | null
  status: 'pending' | 'processing' | 'ready' | 'error'
  preview: any[] | null
  created_by: number | null
  created_at: string
  updated_at: string
}

export interface DatasetListParams {
  search?: string
  dataset_type?: string
  status?: string
  is_public?: boolean
  tags?: string[]
  sort_by?: string
  sort_order?: string
  page?: number
  size?: number
}

export interface DatasetListResponse {
  items: Dataset[]
  total: number
  page: number
  size: number
  pages: number
}

export interface DatasetCreateData {
  name: string
  description?: string
  dataset_type: string
  format?: string
  is_public?: boolean
  tags?: string[]
}

export interface DatasetUpdateData {
  name?: string
  description?: string
  dataset_type?: string
  format?: string
  is_public?: boolean
  tags?: string[]
  status?: string
}

export interface DatasetStats {
  total: number
  total_samples: number
  total_size: number
  processing: number
  by_type: Record<string, number>
  by_status: Record<string, number>
}

export const getDatasets = (params?: DatasetListParams) => {
  return request.get<DatasetListResponse>('datasets/', params)
}

export const getDatasetStats = () => {
  return request.get<DatasetStats>('datasets/stats')
}

export const getDataset = (id: number) => {
  return request.get<Dataset>(`datasets/${id}`)
}

export const createDataset = (data: DatasetCreateData) => {
  return request.post<Dataset>('datasets/', data)
}

export const updateDataset = (id: number, data: DatasetUpdateData) => {
  return request.put<Dataset>(`datasets/${id}`, data)
}

export const deleteDataset = (id: number) => {
  return request.delete(`datasets/${id}`)
}

export const uploadDatasetFiles = (id: number, files: File[]) => {
  const formData = new FormData()
  files.forEach(file => {
    formData.append('files', file)
  })
  
  return request.post<Dataset>(`datasets/${id}/upload`, formData, {
    headers: {
      'Content-Type': 'multipart/form-data'
    }
  })
}

export const getDatasetPreview = (id: number, limit = 10) => {
  return request.get<any>(`datasets/${id}/preview`, { limit })
}

export const downloadDatasetFile = (id: number, filename?: string) => {
  return request.download(`datasets/${id}/download`, {}, filename || `${id}.zip`)
}
