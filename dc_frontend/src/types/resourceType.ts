export type FieldType = 'string' | 'number' | 'boolean' | 'date' | 'object' | 'array'

export interface ResourceField {
  key: string
  label?: string
  type?: FieldType
  required?: boolean
  default?: any
  description?: string
}

export interface ResourceTypeItem {
  id: string
  name: string
  describe?: string
  metadata?: ResourceField[]
  create_time?: string
  update_time?: string
}

export interface ResourceTypeListResponse {
  items: ResourceTypeItem[]
  total: number
  page: number
  page_size: number
  total_pages: number
}