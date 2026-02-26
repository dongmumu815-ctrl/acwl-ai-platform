/**
 * 应用管理相关的API接口
 */
import { request } from '@/utils/request'

// --- Enums ---

export enum AppType {
  DOCKER_COMPOSE = 'docker_compose',
  DOCKER_IMAGE = 'docker_image',
  SHELL_SCRIPT = 'shell_script',
  HELM_CHART = 'helm_chart'
}

export enum AppStatus {
  INSTALLING = 'installing',
  RUNNING = 'running',
  STOPPED = 'stopped',
  ERROR = 'error',
  UPGRADING = 'upgrading',
  UNINSTALLING = 'uninstalling',
  UNINSTALLED = 'uninstalled'
}

// --- Interfaces ---

export interface HarborConfig {
  id: number
  name: string
  url: string
  username?: string
  password?: string
  project?: string
  is_default: boolean
  description?: string
  created_at?: string
  updated_at?: string
}

export interface HarborConfigForm {
  name: string
  url: string
  username?: string
  password?: string
  project?: string
  is_default: boolean
  description?: string
}

export interface AppTemplate {
  id: number
  name: string
  display_name?: string
  version: string
  description?: string
  icon?: string
  app_type: AppType
  config_schema?: any
  default_config?: any
  deploy_template?: string
  is_system: boolean
  created_at?: string
  updated_at?: string
}

export interface AppTemplateForm {
  name: string
  display_name?: string
  version: string
  description?: string
  icon?: string
  app_type: AppType
  config_schema?: any
  default_config?: any
  deploy_template?: string
  is_system: boolean
}

export interface AppDeployment {
  id: number
  instance_id: number
  server_id: number
  role: string
  container_id?: string
  status: string
  cpu_limit?: string
  mem_limit?: string
  ports?: any
  created_at?: string
  updated_at?: string
}

export interface AppDeploymentForm {
  server_id: number
  role: string
  cpu_limit?: string
  mem_limit?: string
  ports?: any
}

export interface AppInstance {
  id: number
  name: string
  template_id?: number
  template?: AppTemplate
  status: AppStatus
  config?: any
  description?: string
  deployments?: AppDeployment[]
  created_at?: string
  updated_at?: string
}

export interface AppInstanceForm {
  name: string
  template_id?: number
  description?: string
  config?: any
  deployments: AppDeploymentForm[]
}

// --- API Functions ---

// Harbor Configs
export function getHarborConfigs(params: any): Promise<any> {
  return request.get('/applications/harbor-configs', { params })
}

export function createHarborConfig(data: HarborConfigForm): Promise<any> {
  return request.post('/applications/harbor-configs', data)
}

export function updateHarborConfig(id: number, data: HarborConfigForm): Promise<any> {
  return request.put(`/applications/harbor-configs/${id}`, data)
}

export function deleteHarborConfig(id: number): Promise<any> {
  return request.delete(`/applications/harbor-configs/${id}`)
}

// App Templates
export function getAppTemplates(params: any): Promise<any> {
  return request.get('/applications/templates', { params })
}

export function createAppTemplate(data: AppTemplateForm): Promise<any> {
  return request.post('/applications/templates', data)
}

export function updateAppTemplate(id: number, data: AppTemplateForm): Promise<any> {
  return request.put(`/applications/templates/${id}`, data)
}

export function deleteAppTemplate(id: number): Promise<any> {
  return request.delete(`/applications/templates/${id}`)
}

// App Instances
export function getAppInstances(params: any): Promise<any> {
  return request.get('/applications/instances', { params })
}

export function getAppInstance(id: number): Promise<any> {
  return request.get(`/applications/instances/${id}`)
}

export function createAppInstance(data: AppInstanceForm): Promise<any> {
  return request.post('/applications/instances', data)
}

export function updateAppInstance(id: number, data: Partial<AppInstanceForm>): Promise<any> {
  return request.put(`/applications/instances/${id}`, data)
}

export function deleteAppInstance(id: number, clean_data: boolean = false): Promise<any> {
  return request.delete(`/applications/instances/${id}`, {
    params: { clean_data }
  })
}
