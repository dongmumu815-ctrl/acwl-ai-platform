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
    return api.post(`/workflows/instances/${executionId}/cancel`)
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
   * 获取所有工作流执行实例
   * @param {object} params 查询参数
   */
  getAllWorkflowExecutions(params = {}) {
    return api.get('/workflows/instances', params)
  },
  
  /**
   * 获取工作流执行详情
   * @param {number} id 工作流ID
   * @param {string} executionId 执行ID
   * @param {object} config 请求配置
   */
  getWorkflowExecutionDetail(id, executionId, config = {}) {
    return api.get(`/workflows/instances/${executionId}`, {}, config)
  },
  
  /**
   * 获取工作流执行日志
   * @param {number} id 工作流ID
   * @param {string} executionId 执行ID
   * @param {object} params 查询参数
   * @param {object} config 请求配置
   */
  getWorkflowExecutionLogs(id, executionId, params = {}, config = {}) {
    return api.get(`/workflows/instances/${executionId}/logs`, params, config)
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
   * 获取工作流调度列表
   * @param {number} workflowId 工作流ID
   */
  getWorkflowSchedules(workflowId) {
    return api.get(`/workflows/${workflowId}/schedules`)
  },

  /**
   * 创建工作流调度
   * @param {number} workflowId 工作流ID
   * @param {object} data 调度数据
   */
  createWorkflowSchedule(workflowId, data) {
    return api.post(`/workflows/${workflowId}/schedules`, data)
  },

  /**
   * 更新工作流调度
   * @param {number} workflowId 工作流ID
   * @param {number} scheduleId 调度ID
   * @param {object} data 调度数据
   */
  updateWorkflowSchedule(workflowId, scheduleId, data) {
    return api.put(`/workflows/${workflowId}/schedules/${scheduleId}`, data)
  },

  /**
   * 删除工作流调度
   * @param {number} workflowId 工作流ID
   * @param {number} scheduleId 调度ID
   */
  deleteWorkflowSchedule(workflowId, scheduleId) {
    return api.delete(`/workflows/${workflowId}/schedules/${scheduleId}`)
  },

  // 监控相关 API
  getSystemStats(params = {}) {
    return api.get('/monitoring/stats', params)
  },

  getResourceUsage(params = {}) {
    return api.get('/monitoring/resources', params)
  },

  getActiveWorkflows(params = {}) {
    return api.get('/monitoring/active-workflows', params)
  },

  getSystemAlerts(params = {}) {
    return api.get('/monitoring/alerts', params)
  },

  getExecutionTrend(params = {}) {
    return api.get('/monitoring/trend', params)
  },

  getStatusDistribution(params = {}) {
    return api.get('/monitoring/distribution', params)
  },

  getSystemLogs(params = {}) {
    // 暂时使用空接口或 mock
    return Promise.resolve({ items: [] })
  },

  getClusterNodes() {
    return api.get('/monitoring/nodes')
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
   * 获取任务执行历史 (特定任务)
   * @param {number} id 任务ID
   * @param {object} params 查询参数
   */
  getTaskExecutions(id, params = {}) {
    return api.get(`/tasks/${id}/executions`, params)
  },

  /**
   * 获取所有任务实例列表 (全局)
   * @param {object} params 查询参数
   */
  getAllTaskInstances(params = {}) {
    return api.get('/tasks/instances', params)
  },

  /**
   * 获取任务实例日志文件
   * @param {number} instanceId 实例ID
   * @param {object} params 查询参数 (start, length)
   */
  getTaskInstanceLogFile(instanceId, params = {}) {
    return api.get(`/tasks/instances/${instanceId}/logs/file`, params)
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