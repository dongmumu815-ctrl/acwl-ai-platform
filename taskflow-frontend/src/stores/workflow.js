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
      currentWorkflow.value = response.data
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
      const newWorkflow = response.data
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
      const updatedWorkflow = response.data
      
      // 更新列表中的工作流
      const index = workflows.value.findIndex(w => w.id === id)
      if (index !== -1) {
        workflows.value[index] = updatedWorkflow
      }
      
      // 更新当前工作流
      if (currentWorkflow.value && currentWorkflow.value.id === id) {
        currentWorkflow.value = updatedWorkflow
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
        workflow.status = 'running'
        workflow.last_execution_time = new Date().toISOString()
      }
      
      if (currentWorkflow.value && currentWorkflow.value.id === id) {
        currentWorkflow.value.status = 'running'
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
      workflowExecutions.value = response.data.items
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
      currentExecution.value = response.data
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
      const clonedWorkflow = response.data
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
    getWorkflowExecutionDetail,
    cloneWorkflow,
    setCurrentWorkflow,
    clearCurrentWorkflow,
    setCurrentExecution,
    clearCurrentExecution,
    resetState
  }
})