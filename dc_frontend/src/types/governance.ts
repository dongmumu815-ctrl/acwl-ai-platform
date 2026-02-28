export interface GovernanceColumn {
  id: number
  table_id: number
  column_name: string
  data_type: string
  is_primary_key: boolean
  is_nullable: boolean
  description?: string
  security_level?: string
  data_standard?: string
  data_quality_rule?: string
  tags?: string[]
  updated_at: string
  updated_by?: number
}

export interface GovernanceTable {
  id: number
  datasource_id: number
  schema_name: string
  table_name: string
  description?: string
  owner?: string
  classification_level?: string
  retention_period?: string
  tags?: string[]
  row_count?: number
  storage_size?: number
  last_analyzed?: string
  created_at: string
  updated_at: string
  created_by?: number
  updated_by?: number
  columns?: GovernanceColumn[]
}

export interface GovernanceTableListQuery {
  page?: number
  size?: number
  search?: string
  datasource_id?: number
}

export interface GovernanceTableUpdate {
  description?: string
  owner?: string
  classification_level?: string
  retention_period?: string
  tags?: string[]
}

export interface GovernanceColumnUpdate {
  description?: string
  security_level?: string
  data_standard?: string
  tags?: string[]
}
