import { api } from './request'

/**
 * 工作流管理API
 */
export const workflowApi = {
  /**
   * 获取工作流列表
   * @param {object} params 查询参数
   */
  getWorkflowList(params = {}) {
    return api.get('/workflows/', params)
  },
  
  /**
   * 获取工作流详情
   * @param {number} id 工作流ID
   */
  getWorkflowDetail(id) {
    return api.get(`/workflows/${id}`)
  },
  
  /**
   * 创建工作流
   * @param {object} data 工作流数据
   */
  createWorkflow(data) {
    return api.post('/workflows/', data)
  },
  
  /**
   * 更新工作流
   * @param {number} id 工作流ID
   * @param {object} data 工作流数据
   */
  updateWorkflow(id, data) {
    return api.put(`/workflows/${id}`, data)
  },
  
  /**
   * 删除工作流
   * @param {number} id 工作流ID
   */
  deleteWorkflow(id) {
    return api.delete(`/workflows/${id}`)
  },
  
  /**
   * 执行工作流
   * @param {number} id 工作流ID
   * @param {object} params 执行参数
   */
  executeWorkflow(id, params = {}) {
    return api.post(`/workflows/${id}/execute`, params)
  },
  
  /**
   * 停止工作流执行
   * @param {number} id 工作流ID
   * @param {string} executionId 执行ID
   */
  stopWorkflowExecution(id, executionId) {
    return api.post(`/workflows/${id}/executions/${executionId}/stop`)
  },
  
  /**
   * 获取工作流执行历史
   * @param {number} id 工作流ID
   * @param {object} params 查询参数
   */
  getWorkflowExecutions(id, params = {}) {
    return api.get(`/workflows/${id}/executions`, params)
  },
  
  /**
   * 获取工作流执行详情
   * @param {number} id 工作流ID
   * @param {string} executionId 执行ID
   */
  getWorkflowExecutionDetail(id, executionId) {
    return api.get(`/workflows/${id}/executions/${executionId}`)
  },
  
  /**
   * 获取工作流执行日志
   * @param {number} id 工作流ID
   * @param {string} executionId 执行ID
   */
  getWorkflowExecutionLogs(id, executionId) {
    return api.get(`/workflows/${id}/executions/${executionId}/logs`)
  },
  
  /**
   * 克隆工作流
   * @param {number} id 工作流ID
   * @param {object} data 克隆配置
   */
  cloneWorkflow(id, data = {}) {
    return api.post(`/workflows/${id}/clone`, data)
  },
  
  /**
   * 导出工作流
   * @param {number} id 工作流ID
   */
  exportWorkflow(id) {
    return api.download(`/workflows/${id}/export`, {}, `workflow_${id}.json`)
  },
  
  /**
   * 导入工作流
   * @param {FormData} formData 文件数据
   */
  importWorkflow(formData) {
    return api.upload('/workflows/import', formData)
  }
}

/**
 * 任务管理API
 */
export const taskApi = {
  /**
   * 获取任务列表
   * @param {object} params 查询参数
   */
  getTaskList(params = {}) {
    return api.get('/tasks/', params)
  },
  
  /**
   * 获取任务详情
   * @param {number} id 任务ID
   */
  getTaskDetail(id) {
    return api.get(`/tasks/${id}`)
  },
  
  /**
   * 创建任务
   * @param {object} data 任务数据
   */
  createTask(data) {
    return api.post('/tasks', data)
  },
  
  /**
   * 更新任务
   * @param {number} id 任务ID
   * @param {object} data 任务数据
   */
  updateTask(id, data) {
    return api.put(`/tasks/${id}`, data)
  },
  
  /**
   * 删除任务
   * @param {number} id 任务ID
   */
  deleteTask(id) {
    return api.delete(`/tasks/${id}`)
  },
  
  /**
   * 执行任务
   * @param {number} id 任务ID
   * @param {object} params 执行参数
   */
  executeTask(id, params = {}) {
    return api.post(`/tasks/${id}/execute`, params)
  },
  
  /**
   * 停止任务执行
   * @param {number} id 任务ID
   * @param {string} executionId 执行ID
   */
  stopTaskExecution(id, executionId) {
    return api.post(`/tasks/${id}/executions/${executionId}/stop`)
  },
  
  /**
   * 获取任务执行历史
   * @param {number} id 任务ID
   * @param {object} params 查询参数
   */
  getTaskExecutions(id, params = {}) {
    return api.get(`/tasks/${id}/executions`, params)
  },
  
  /**
   * 获取任务模板列表
   */
  getTaskTemplates() {
    return api.get('/task-templates')
  },
  
  /**
   * 获取任务类型列表
   */
  getTaskTypes() {
    return api.get('/task-types')
  }
}

/**
 * 项目管理API
 */
export const projectApi = {
  /**
   * 获取项目列表
   * @param {object} params 查询参数
   * @param {object} config 请求配置
   */
  getProjectList(params = {}, config = {}) {
    return api.get('/projects/', params, config)
  },
  
  /**
   * 获取项目详情
   * @param {number} id 项目ID
   */
  getProjectDetail(id) {
    return api.get(`/projects/${id}`)
  },
  
  /**
   * 创建项目
   * @param {object} data 项目数据
   */
  createProject(data) {
    return api.post('/projects', data)
  },
  
  /**
   * 更新项目
   * @param {number} id 项目ID
   * @param {object} data 项目数据
   */
  updateProject(id, data) {
    return api.put(`/projects/${id}`, data)
  },
  
  /**
   * 删除项目
   * @param {number} id 项目ID
   */
  deleteProject(id) {
    return api.delete(`/projects/${id}`)
  },
  
  /**
   * 获取项目成员
   * @param {number} id 项目ID
   */
  getProjectMembers(id) {
    return api.get(`/projects/${id}/members`)
  },
  
  /**
   * 添加项目成员
   * @param {number} id 项目ID
   * @param {object} data 成员数据
   */
  addProjectMember(id, data) {
    return api.post(`/projects/${id}/members`, data)
  },
  
  /**
   * 移除项目成员
   * @param {number} id 项目ID
   * @param {number} memberId 成员ID
   */
  removeProjectMember(id, memberId) {
    return api.delete(`/projects/${id}/members/${memberId}`)
  }
}