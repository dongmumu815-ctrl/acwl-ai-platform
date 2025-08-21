import { request } from '@/utils/request'
import type { PaginatedResponse } from '@/types/common'

// 项目状态枚举
export enum ProjectStatus {
  ACTIVE = 'ACTIVE',
  INACTIVE = 'INACTIVE',
  ARCHIVED = 'ARCHIVED'
}

// 项目类型枚举
export enum ProjectType {
  DATA_ANALYSIS = 'DATA_ANALYSIS',
  MODEL_TRAINING = 'MODEL_TRAINING',
  ETL_PIPELINE = 'ETL_PIPELINE',
  GENERAL = 'GENERAL'
}

// 项目优先级枚举
export enum ProjectPriority {
  LOW = 'LOW',
  MEDIUM = 'MEDIUM',
  HIGH = 'HIGH',
  CRITICAL = 'CRITICAL'
}

// 项目成员角色枚举
export enum ProjectMemberRole {
  ADMIN = 'ADMIN',
  DEVELOPER = 'DEVELOPER',
  VIEWER = 'VIEWER'
}

// 数据源访问类型枚举
export enum ProjectDatasourceAccessType {
  READ = 'read',
  WRITE = 'write',
  ADMIN = 'admin'
}

// 项目接口类型定义
export interface Project {
  id: number
  name: string
  description?: string
  project_type: ProjectType
  status: ProjectStatus
  priority: ProjectPriority
  start_date?: string
  end_date?: string
  tags?: Record<string, any>
  project_metadata?: Record<string, any>
  created_by: number
  created_at: string
  updated_at: string
  is_active: boolean
  creator_username?: string
  members_count?: number
  datasource_count?: number
}

// 项目创建/更新表单类型
export interface ProjectForm {
  name: string
  description?: string
  project_type: ProjectType
  status: ProjectStatus
  priority: ProjectPriority
  start_date?: string
  end_date?: string
  members_count?: number
  tags?: Record<string, any>
  project_metadata?: Record<string, any>
}

// 项目查询参数
export interface ProjectQueryParams {
  page?: number
  size?: number
  search?: string
  name?: string
  project_type?: ProjectType
  status?: ProjectStatus
  priority?: ProjectPriority
  created_by?: number
  start_date_from?: string
  start_date_to?: string
  end_date_from?: string
  end_date_to?: string
  tags?: Record<string, any>
}

// 项目成员接口类型
export interface ProjectMember {
  id: number
  project_id: number
  user_id: number
  username: string
  email?: string
  role: ProjectMemberRole
  notes?: string
  invited_by: number
  invited_at: string
  is_active: boolean
  inviter_username?: string
}

// 项目成员表单类型
export interface ProjectMemberForm {
  user_id: number
  role: ProjectMemberRole
  notes?: string
}

// 项目成员查询参数
export interface ProjectMemberQueryParams {
  page?: number
  size?: number
  search?: string
  username?: string
  role?: ProjectMemberRole
  is_active?: boolean
}

// 项目数据源接口类型
export interface ProjectDatasource {
  id: number
  project_id: number
  datasource_id: number
  datasource_name: string
  datasource_type: string
  access_type: ProjectDatasourceAccessType
  notes?: string
  assigned_by: number
  assigned_at: string
  is_active: boolean
  assigner_username?: string
}

// 项目数据源表单类型
export interface ProjectDatasourceForm {
  datasource_id: number
  access_type: ProjectDatasourceAccessType
  notes?: string
}

// 项目数据源查询参数
export interface ProjectDatasourceQueryParams {
  page?: number
  size?: number
  search?: string
  datasource_name?: string
  datasource_type?: string
  access_type?: ProjectDatasourceAccessType
  is_active?: boolean
}

// 项目活动日志接口类型
export interface ProjectActivity {
  id: number
  project_id: number
  user_id: number
  username: string
  activity_type: string
  target_type: string
  target_id?: number
  description: string
  activity_metadata?: Record<string, any>
  created_at: string
}

// 项目活动查询参数
export interface ProjectActivityQueryParams {
  page?: number
  size?: number
  activity_type?: string
  target_type?: string
  user_id?: number
  date_from?: string
  date_to?: string
}

// 项目统计信息
export interface ProjectStats {
  total_projects: number
  active_projects: number
  completed_projects: number
  my_projects: number
  project_type_distribution: Record<string, number>
  project_status_distribution: Record<string, number>
  recent_activities_count: number
  total_resources: number
}

// 项目仪表板数据
export interface ProjectDashboard {
  stats: ProjectStats
  recent_projects: Project[]
  my_recent_activities: ProjectActivity[]
  upcoming_deadlines: Project[]
}

// 批量操作数据
export interface BatchOperationData {
  ids: number[]
  action: 'activate' | 'deactivate' | 'delete'
}

// 项目API
export const projectApi = {
  /**
   * 获取项目列表
   */
  getProjects(params?: ProjectQueryParams): Promise<PaginatedResponse<Project>> {
    return request.get('/projects/', { params })
  },

  /**
   * 获取项目详情
   */
  getProject(projectId: number): Promise<Project> {
    return request.get(`/projects/${projectId}`)
  },

  /**
   * 创建项目
   */
  createProject(data: ProjectForm): Promise<Project> {
    return request.post('/projects/', data)
  },

  /**
   * 更新项目
   */
  updateProject(projectId: number, data: Partial<ProjectForm>): Promise<Project> {
    return request.put(`/projects/${projectId}`, data)
  },

  /**
   * 删除项目
   */
  deleteProject(projectId: number): Promise<void> {
    return request.delete(`/projects/${projectId}`)
  },

  /**
   * 获取项目成员列表
   */
  getProjectMembers(projectId: number, params?: ProjectMemberQueryParams): Promise<PaginatedResponse<ProjectMember>> {
    return request.get(`/projects/${projectId}/members`, { params })
  },

  /**
   * 添加项目成员
   */
  addProjectMember(projectId: number, data: ProjectMemberForm): Promise<ProjectMember> {
    return request.post(`/projects/${projectId}/members`, data)
  },

  /**
   * 更新项目成员
   */
  updateProjectMember(projectId: number, memberId: number, data: Partial<ProjectMemberForm>): Promise<ProjectMember> {
    return request.put(`/projects/${projectId}/members/${memberId}`, data)
  },

  /**
   * 移除项目成员
   */
  removeProjectMember(projectId: number, memberId: number): Promise<void> {
    return request.delete(`/projects/${projectId}/members/${memberId}`)
  },

  /**
   * 获取项目数据源列表
   */
  getProjectDatasources(projectId: number, params?: ProjectDatasourceQueryParams): Promise<PaginatedResponse<ProjectDatasource>> {
    return request.get(`/projects/${projectId}/datasources`, { params })
  },

  /**
   * 分配项目数据源
   */
  assignProjectDatasource(projectId: number, data: ProjectDatasourceForm): Promise<ProjectDatasource> {
    return request.post(`/projects/${projectId}/datasources`, data)
  },

  /**
   * 更新项目数据源
   */
  updateProjectDatasource(projectId: number, datasourceId: number, data: Partial<ProjectDatasourceForm>): Promise<ProjectDatasource> {
    return request.put(`/projects/${projectId}/datasources/${datasourceId}`, data)
  },

  /**
   * 移除项目数据源
   */
  removeProjectDatasource(projectId: number, datasourceId: number): Promise<void> {
    return request.delete(`/projects/${projectId}/datasources/${datasourceId}`)
  },

  /**
   * 获取项目活动日志
   */
  getProjectActivities(projectId: number, params?: ProjectActivityQueryParams): Promise<PaginatedResponse<ProjectActivity>> {
    return request.get(`/projects/${projectId}/activities`, { params })
  },

  /**
   * 获取项目统计信息
   */
  getProjectStats(): Promise<ProjectStats> {
    return request.get('/projects/stats')
  },

  /**
   * 获取项目仪表板数据
   */
  getProjectDashboard(): Promise<ProjectDashboard> {
    return request.get('/projects/dashboard')
  },

  /**
   * 批量操作项目
   */
  batchOperateProjects(data: BatchOperationData): Promise<void> {
    return request.post('/projects/batch', data)
  }
}

// 导出常用方法
export const getProjects = projectApi.getProjects
export const getProject = projectApi.getProject
export const createProject = projectApi.createProject
export const updateProject = projectApi.updateProject
export const deleteProject = projectApi.deleteProject
export const getProjectMembers = projectApi.getProjectMembers
export const addProjectMember = projectApi.addProjectMember
export const updateProjectMember = projectApi.updateProjectMember
export const removeProjectMember = projectApi.removeProjectMember
export const getProjectDatasources = projectApi.getProjectDatasources
export const assignProjectDatasource = projectApi.assignProjectDatasource
export const updateProjectDatasource = projectApi.updateProjectDatasource
export const removeProjectDatasource = projectApi.removeProjectDatasource
export const getProjectActivities = projectApi.getProjectActivities
export const getProjectStats = projectApi.getProjectStats
export const getProjectDashboard = projectApi.getProjectDashboard

// 选项配置
export interface ProjectTypeOption {
  value: ProjectType
  label: string
  icon: string
}

export interface ProjectStatusOption {
  value: ProjectStatus
  label: string
  type: 'success' | 'danger' | 'warning' | 'info'
}

export interface ProjectPriorityOption {
  value: ProjectPriority
  label: string
  type: 'success' | 'danger' | 'warning' | 'info'
}

export interface ProjectMemberRoleOption {
  value: ProjectMemberRole
  label: string
  type: 'success' | 'danger' | 'warning' | 'info'
}

// 项目类型选项
export const PROJECT_TYPES: ProjectTypeOption[] = [
  { value: ProjectType.DATA_ANALYSIS, label: '数据分析', icon: 'Search' },
  { value: ProjectType.MODEL_TRAINING, label: '模型训练', icon: 'Setting' },
  { value: ProjectType.ETL_PIPELINE, label: 'ETL管道', icon: 'Monitor' },
  { value: ProjectType.GENERAL, label: '通用项目', icon: 'More' }
]

// 项目状态选项
export const PROJECT_STATUS_OPTIONS: ProjectStatusOption[] = [
  { value: ProjectStatus.ACTIVE, label: '激活', type: 'success' },
  { value: ProjectStatus.INACTIVE, label: '未激活', type: 'warning' },
  { value: ProjectStatus.ARCHIVED, label: '已归档', type: 'info' }
]

// 项目优先级选项
export const PROJECT_PRIORITY_OPTIONS: ProjectPriorityOption[] = [
  { value: ProjectPriority.LOW, label: '低', type: 'info' },
  { value: ProjectPriority.MEDIUM, label: '中', type: 'warning' },
  { value: ProjectPriority.HIGH, label: '高', type: 'danger' },
  { value: ProjectPriority.CRITICAL, label: '紧急', type: 'danger' }
]

// 项目成员角色选项
export const PROJECT_MEMBER_ROLE_OPTIONS: ProjectMemberRoleOption[] = [
  { value: ProjectMemberRole.ADMIN, label: '管理员', type: 'danger' },
  { value: ProjectMemberRole.DEVELOPER, label: '开发者', type: 'success' },
  { value: ProjectMemberRole.VIEWER, label: '查看者', type: 'info' }
]

// 工具函数

/**
 * 获取项目类型标签
 */
export function getProjectTypeLabel(type: ProjectType): string {
  const option = PROJECT_TYPES.find(item => item.value === type)
  return option?.label || type
}

/**
 * 获取项目状态配置
 */
export function getProjectStatusConfig(status: ProjectStatus): ProjectStatusOption {
  return PROJECT_STATUS_OPTIONS.find(item => item.value === status) || 
    { value: status, label: status, type: 'info' }
}

/**
 * 获取项目优先级配置
 */
export function getProjectPriorityConfig(priority: ProjectPriority): ProjectPriorityOption {
  return PROJECT_PRIORITY_OPTIONS.find(item => item.value === priority) || 
    { value: priority, label: priority, type: 'info' }
}

/**
 * 获取项目成员角色配置
 */
export function getProjectMemberRoleConfig(role: ProjectMemberRole): ProjectMemberRoleOption {
  return PROJECT_MEMBER_ROLE_OPTIONS.find(item => item.value === role) || 
    { value: role, label: role, type: 'info' }
}



/**
 * 计算项目进度百分比（基于时间）
 */
export function calculateProjectProgress(startDate?: string, endDate?: string): number {
  if (!startDate || !endDate) return 0
  
  const start = new Date(startDate).getTime()
  const end = new Date(endDate).getTime()
  const now = Date.now()
  
  if (now < start) return 0
  if (now > end) return 100
  
  return Math.round(((now - start) / (end - start)) * 100)
}

/**
 * 检查项目是否即将到期（7天内）
 */
export function isProjectNearDeadline(endDate?: string): boolean {
  if (!endDate) return false
  
  const end = new Date(endDate).getTime()
  const now = Date.now()
  const sevenDaysLater = now + 7 * 24 * 60 * 60 * 1000
  
  return end <= sevenDaysLater && end > now
}

/**
 * 检查项目是否已过期
 */
export function isProjectOverdue(endDate?: string): boolean {
  if (!endDate) return false
  
  const end = new Date(endDate).getTime()
  const now = Date.now()
  
  return end < now
}