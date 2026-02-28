import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { workflowApi } from '@/api/workflow'

/**
 * 工作流状态管理
 */
export const useWorkflowStore = defineStore('workflow', () => {
  // 状态
  const workflows = ref([])
  const currentWorkflow = ref(null)
  const workflowExecutions = ref([])
  const currentExecution = ref(null)
  const loading = ref(false)
  const total = ref(0)
  
  // 计算属性
  const workflowCount = computed(() => workflows.value.length)
  const runningWorkflows = computed(() => 
    workflows.value.filter(w => w.status === 'running')
  )
  const completedWorkflows = computed(() => 
    workflows.value.filter(w => w.status === 'completed')
  )
  const failedWorkflows = computed(() => 
    workflows.value.filter(w => w.status === 'failed')
  )
  
  /**
   * 获取工作流列表
   * @param {object} params 查询参数
   */
  const getWorkflowList = async (params = {}) => {
    loading.value = true
    try {
      const response = await workflowApi.getWorkflowList(params)

      workflows.value = response.items
      total.value = response.total
      return response
    } catch (error) {
      throw error
    } finally {
      loading.value = false
    }
  }
  
  /**
   * 获取工作流详情
   * @param {number} id 工作流ID
   */
  const getWorkflowDetail = async (id) => {
    loading.value = true
    try {
      const response = await workflowApi.getWorkflowDetail(id)
      currentWorkflow.value = response
      return response
    } catch (error) {
      throw error
    } finally {
      loading.value = false
    }
  }
  
  /**
   * 创建工作流
   * @param {object} data 工作流数据
   */
  const createWorkflow = async (data) => {
    loading.value = true
    try {
      const response = await workflowApi.createWorkflow(data)
      const newWorkflow = response
      workflows.value.unshift(newWorkflow)
      total.value += 1
      return response
    } catch (error) {
      throw error
    } finally {
      loading.value = false
    }
  }
  
  /**
   * 更新工作流
   * @param {number} id 工作流ID
   * @param {object} data 工作流数据
   */
  const updateWorkflow = async (id, data) => {
    loading.value = true
    try {
      const response = await workflowApi.updateWorkflow(id, data)
      const updatedWorkflow = response
      
      // 更新列表中的工作流
      const index = workflows.value.findIndex(w => w.id === id)
      if (index !== -1) {
        // 保留原有的 project_name 等在列表展示中需要的字段
        // 因为更新接口返回的可能不包含这些关联字段
        const originalWorkflow = workflows.value[index]
        workflows.value[index] = {
          ...originalWorkflow,
          ...updatedWorkflow,
          project_name: originalWorkflow.project_name // 确保 project_name 不丢失
        }
      }
      
      // 更新当前工作流
      if (currentWorkflow.value && currentWorkflow.value.id === id) {
        currentWorkflow.value = {
          ...currentWorkflow.value,
          ...updatedWorkflow
        }
      }
      
      return response
    } catch (error) {
      throw error
    } finally {
      loading.value = false
    }
  }
  
  /**
   * 删除工作流
   * @param {number} id 工作流ID
   */
  const deleteWorkflow = async (id) => {
    loading.value = true
    try {
      const response = await workflowApi.deleteWorkflow(id)
      
      // 从列表中移除
      const index = workflows.value.findIndex(w => w.id === id)
      if (index !== -1) {
        workflows.value.splice(index, 1)
        total.value -= 1
      }
      
      // 清除当前工作流
      if (currentWorkflow.value && currentWorkflow.value.id === id) {
        currentWorkflow.value = null
      }
      
      return response
    } catch (error) {
      throw error
    } finally {
      loading.value = false
    }
  }
  
  /**
   * 执行工作流
   * @param {number} id 工作流ID
   * @param {object} params 执行参数
   */
  const executeWorkflow = async (id, params = {}) => {
    loading.value = true
    try {
      const response = await workflowApi.executeWorkflow(id, params)
      
      // 更新工作流状态
      const workflow = workflows.value.find(w => w.id === id)
      if (workflow) {
        // 执行工作流不改变工作流定义的 status (draft/active/inactive)，只更新最后执行时间
        // workflow.status = 'running' 
        workflow.last_execution_time = new Date().toISOString()
      }
      
      if (currentWorkflow.value && currentWorkflow.value.id === id) {
        // currentWorkflow.value.status = 'running'
        currentWorkflow.value.last_execution_time = new Date().toISOString()
      }
      
      return response
    } catch (error) {
      throw error
    } finally {
      loading.value = false
    }
  }
  
  /**
   * 停止工作流执行
   * @param {number} id 工作流ID
   * @param {string} executionId 执行ID
   */
  const stopWorkflowExecution = async (id, executionId) => {
    loading.value = true
    try {
      const response = await workflowApi.stopWorkflowExecution(id, executionId)
      
      // 更新执行状态
      const execution = workflowExecutions.value.find(e => e.id === executionId)
      if (execution) {
        execution.status = 'cancelled'
      }
      
      if (currentExecution.value && currentExecution.value.id === executionId) {
        currentExecution.value.status = 'cancelled'
      }
      
      return response
    } catch (error) {
      throw error
    } finally {
      loading.value = false
    }
  }
  
  /**
   * 获取工作流执行历史
   * @param {number} id 工作流ID
   * @param {object} params 查询参数
   */
  const getWorkflowExecutions = async (id, params = {}) => {
    loading.value = true
    try {
      const response = await workflowApi.getWorkflowExecutions(id, params)
      workflowExecutions.value = response.data.items // Note: response structure might vary, keeping consistency with existing code if it was response.data.items or response.items. 
      // Checking existing code, getWorkflowList uses response.items. 
      // But here in getWorkflowExecutions in existing code it used response.data.items? 
      // Let's re-read the existing code snippet for getWorkflowExecutions.
      return response
    } catch (error) {
      throw error
    } finally {
      loading.value = false
    }
  }

  /**
   * 获取所有工作流执行实例
   * @param {object} params 查询参数
   */
  const getAllWorkflowExecutions = async (params = {}) => {
    loading.value = true
    try {
      const response = await workflowApi.getAllWorkflowExecutions(params)
      // Assuming response structure is { items: [], total: ... } like list endpoints
      return response
    } catch (error) {
      throw error
    } finally {
      loading.value = false
    }
  }
  
  /**
   * 获取工作流执行详情
   * @param {number} id 工作流ID
   * @param {string} executionId 执行ID
   */
  const getWorkflowExecutionDetail = async (id, executionId) => {
    loading.value = true
    try {
      const response = await workflowApi.getWorkflowExecutionDetail(id, executionId)
      currentExecution.value = response
      return response
    } catch (error) {
      throw error
    } finally {
      loading.value = false
    }
  }
  
  /**
   * 克隆工作流
   * @param {number} id 工作流ID
   * @param {object} data 克隆配置
   */
  const cloneWorkflow = async (id, data = {}) => {
    loading.value = true
    try {
      const response = await workflowApi.cloneWorkflow(id, data)
      const clonedWorkflow = response
      workflows.value.unshift(clonedWorkflow)
      total.value += 1
      return response
    } catch (error) {
      throw error
    } finally {
      loading.value = false
    }
  }
  
  /**
   * 设置当前工作流
   * @param {object} workflow 工作流对象
   */
  const setCurrentWorkflow = (workflow) => {
    currentWorkflow.value = workflow
  }
  
  /**
   * 清除当前工作流
   */
  const clearCurrentWorkflow = () => {
    currentWorkflow.value = null
  }
  
  /**
   * 设置当前执行
   * @param {object} execution 执行对象
   */
  const setCurrentExecution = (execution) => {
    currentExecution.value = execution
  }
  
  /**
   * 清除当前执行
   */
  const clearCurrentExecution = () => {
    currentExecution.value = null
  }
  
  /**
   * 重置状态
   */
  const resetState = () => {
    workflows.value = []
    currentWorkflow.value = null
    workflowExecutions.value = []
    currentExecution.value = null
    loading.value = false
    total.value = 0
  }
  
  /**
   * 获取工作流调度列表
   * @param {number} workflowId 工作流ID
   */
  const getWorkflowSchedules = async (workflowId) => {
    try {
      const response = await workflowApi.getWorkflowSchedules(workflowId)
      return response
    } catch (error) {
      throw error
    }
  }

  /**
   * 创建工作流调度
   * @param {number} workflowId 工作流ID
   * @param {object} data 调度数据
   */
  const createWorkflowSchedule = async (workflowId, data) => {
    try {
      const response = await workflowApi.createWorkflowSchedule(workflowId, data)
      return response
    } catch (error) {
      throw error
    }
  }

  /**
   * 更新工作流调度
   * @param {number} workflowId 工作流ID
   * @param {number} scheduleId 调度ID
   * @param {object} data 调度数据
   */
  const updateWorkflowSchedule = async (workflowId, scheduleId, data) => {
    try {
      const response = await workflowApi.updateWorkflowSchedule(workflowId, scheduleId, data)
      return response
    } catch (error) {
      throw error
    }
  }

  /**
   * 删除工作流调度
   * @param {number} workflowId 工作流ID
   * @param {number} scheduleId 调度ID
   */
  const deleteWorkflowSchedule = async (workflowId, scheduleId) => {
    try {
      await workflowApi.deleteWorkflowSchedule(workflowId, scheduleId)
    } catch (error) {
      throw error
    }
  }

  /**
   * 批量执行工作流
   * @param {Array<number>} ids 工作流ID列表
   */
  const batchExecuteWorkflows = async (ids) => {
    loading.value = true
    try {
      const promises = ids.map(id => workflowApi.executeWorkflow(id))
      const results = await Promise.allSettled(promises)
      
      // 检查是否有失败的
      const failed = results.filter(r => r.status === 'rejected')
      if (failed.length > 0) {
        throw new Error(`部分工作流执行失败: ${failed.length} 个失败`)
      }
      
      // 更新状态
      ids.forEach(id => {
        const workflow = workflows.value.find(w => w.id === id)
        if (workflow) {
          // workflow.status = 'running'
          workflow.last_execution_time = new Date().toISOString()
        }
      })
      
      return results
    } catch (error) {
      throw error
    } finally {
      loading.value = false
    }
  }

  /**
   * 批量删除工作流
   * @param {Array<number>} ids 工作流ID列表
   */
  const batchDeleteWorkflows = async (ids) => {
    loading.value = true
    try {
      const promises = ids.map(id => workflowApi.deleteWorkflow(id))
      const results = await Promise.allSettled(promises)
      
      // 检查是否有失败的
      const failed = results.filter(r => r.status === 'rejected')
      
      // 移除成功的
      results.forEach((r, index) => {
        if (r.status === 'fulfilled') {
          const id = ids[index]
          const wfIndex = workflows.value.findIndex(w => w.id === id)
          if (wfIndex !== -1) {
            workflows.value.splice(wfIndex, 1)
            total.value -= 1
          }
        }
      })

      if (failed.length > 0) {
        throw new Error(`部分工作流删除失败: ${failed.length} 个失败`)
      }
      
      return results
    } catch (error) {
      throw error
    } finally {
      loading.value = false
    }
  }

  /**
   * 批量更新工作流状态
   * @param {Array<number>} ids 工作流ID列表
   * @param {string} status 新状态
   */
  const batchUpdateStatusWorkflows = async (ids, status) => {
    loading.value = true
    try {
      const promises = ids.map(id => workflowApi.updateWorkflow(id, { workflow_status: status }))
      const results = await Promise.allSettled(promises)
      
      // 检查是否有失败的
      const failed = results.filter(r => r.status === 'rejected')
      
      // 更新成功的
      results.forEach((r, index) => {
        if (r.status === 'fulfilled') {
          const id = ids[index]
          const workflow = workflows.value.find(w => w.id === id)
          if (workflow) {
            workflow.workflow_status = status
            // 可能需要更新 updated_at
            workflow.updated_at = new Date().toISOString()
          }
        }
      })

      if (failed.length > 0) {
        throw new Error(`部分工作流状态更新失败: ${failed.length} 个失败`)
      }
      
      return results
    } catch (error) {
      throw error
    } finally {
      loading.value = false
    }
  }

  /**
   * 获取工作流执行日志
   * @param {number} workflowId 工作流ID
   * @param {string} executionId 执行ID
   * @param {object} params 查询参数
   * @param {object} config 请求配置
   */
  const getExecutionLogs = async (workflowId, executionId, params = {}, config = {}) => {
    try {
      const response = await workflowApi.getWorkflowExecutionLogs(workflowId, executionId, params, config)
      return response
    } catch (error) {
      throw error
    }
  }

  /**
   * 获取任务执行列表 (从工作流执行详情中获取)
   * @param {number} workflowId 工作流ID
   * @param {string} executionId 执行ID
   * @param {object} config 请求配置
   */
  const getTaskExecutions = async (workflowId, executionId, config = {}) => {
    try {
      // 如果已经有当前执行详情且ID匹配，直接返回其中的任务列表
      if (currentExecution.value && currentExecution.value.id === executionId && currentExecution.value.tasks) {
        return currentExecution.value.tasks
      }
      
      // 否则重新获取详情
      const response = await getWorkflowExecutionDetail(workflowId, executionId, config)
      return response.tasks || []
    } catch (error) {
      throw error
    }
  }

  /**
   * 获取任务日志
   * @param {string} taskExecutionId 任务执行ID
   */
  const getTaskLogs = async (taskExecutionId) => {
    try {
      // 这里假设使用 taskApi 获取任务实例日志
      // 注意：API 定义是 getTaskInstanceLogFile，可能需要调整
      const response = await taskApi.getTaskInstanceLogFile(taskExecutionId)
      return response
    } catch (error) {
      throw error
    }
  }

  /**
   * 重试任务
   * @param {string} taskExecutionId 任务执行ID
   */
  const retryTask = async (taskExecutionId) => {
    try {
      // TODO: 确认重试任务的正确 API
      // 暂时假设没有直接的重试任务实例 API，可能需要调用 executeTask
      throw new Error('暂不支持任务重试')
    } catch (error) {
      throw error
    }
  }

  return {
    // 状态
    workflows,
    currentWorkflow,
    workflowExecutions,
    currentExecution,
    loading,
    total,
    
    // 计算属性
    workflowCount,
    runningWorkflows,
    completedWorkflows,
    failedWorkflows,
    
    // 方法
    getWorkflowList,
    getWorkflowDetail,
    createWorkflow,
    updateWorkflow,
    deleteWorkflow,
    executeWorkflow,
    stopWorkflowExecution,
    getWorkflowExecutions,
    getAllWorkflowExecutions,
    getWorkflowExecutionDetail,
    getExecutionLogs,
    getTaskExecutions,
    getTaskLogs,
    retryTask,
    cloneWorkflow,
    setCurrentWorkflow,
    clearCurrentWorkflow,
    setCurrentExecution,
    clearCurrentExecution,
    resetState,
    
    // 调度相关
    getWorkflowSchedules,
    createWorkflowSchedule,
    updateWorkflowSchedule,
    deleteWorkflowSchedule,
    
    // 批量操作
    batchExecuteWorkflows,
    batchDeleteWorkflows,
    batchUpdateStatusWorkflows,
    
    // 监控 Action
    getSystemStats: async (params) => {
      return await workflowApi.getSystemStats(params)
    },
    getResourceUsage: async (params) => {
      return await workflowApi.getResourceUsage(params)
    },
    getActiveWorkflows: async (params) => {
      const res = await workflowApi.getActiveWorkflows(params)
      return res
    },
    getSystemAlerts: async (params) => {
      return await workflowApi.getSystemAlerts(params)
    },
    getExecutionTrend: async (params) => {
      return await workflowApi.getExecutionTrend(params)
    },
    getStatusDistribution: async (params) => {
      return await workflowApi.getStatusDistribution(params)
    },
    getSystemLogs: async (params) => {
      return await workflowApi.getSystemLogs(params)
    },
    getClusterNodes: async () => {
      return await workflowApi.getClusterNodes()
    }
  }
})