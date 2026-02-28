import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { taskApi } from '@/api/workflow'

/**
 * 任务状态管理
 */
export const useTaskStore = defineStore('task', () => {
  // 状态
  const tasks = ref([])
  const currentTask = ref(null)
  const taskExecutions = ref([])
  const taskTemplates = ref([])
  const taskTypes = ref([])
  const loading = ref(false)
  const total = ref(0)
  
  // 计算属性
  const taskCount = computed(() => tasks.value.length)
  const runningTasks = computed(() => 
    tasks.value.filter(t => t.status === 'running')
  )
  const completedTasks = computed(() => 
    tasks.value.filter(t => t.status === 'completed')
  )
  const failedTasks = computed(() => 
    tasks.value.filter(t => t.status === 'failed')
  )
  
  /**
   * 获取任务列表
   * @param {object} params 查询参数
   */
  const getTaskList = async (params = {}) => {
    loading.value = true
    try {
      const response = await taskApi.getTaskList(params)
      tasks.value = response.data.items
      total.value = response.data.total
      return response
    } catch (error) {
      throw error
    } finally {
      loading.value = false
    }
  }
  
  /**
   * 获取任务详情
   * @param {number} id 任务ID
   */
  const getTaskDetail = async (id) => {
    loading.value = true
    try {
      const response = await taskApi.getTaskDetail(id)
      currentTask.value = response.data
      return response
    } catch (error) {
      throw error
    } finally {
      loading.value = false
    }
  }
  
  /**
   * 创建任务
   * @param {object} data 任务数据
   */
  const createTask = async (data) => {
    loading.value = true
    try {
      const response = await taskApi.createTask(data)
      const newTask = response.data
      tasks.value.unshift(newTask)
      total.value += 1
      return response
    } catch (error) {
      throw error
    } finally {
      loading.value = false
    }
  }
  
  /**
   * 更新任务
   * @param {number} id 任务ID
   * @param {object} data 任务数据
   */
  const updateTask = async (id, data) => {
    loading.value = true
    try {
      const response = await taskApi.updateTask(id, data)
      const updatedTask = response.data
      
      // 更新列表中的任务
      const index = tasks.value.findIndex(t => t.id === id)
      if (index !== -1) {
        tasks.value[index] = updatedTask
      }
      
      // 更新当前任务
      if (currentTask.value && currentTask.value.id === id) {
        currentTask.value = updatedTask
      }
      
      return response
    } catch (error) {
      throw error
    } finally {
      loading.value = false
    }
  }
  
  /**
   * 删除任务
   * @param {number} id 任务ID
   */
  const deleteTask = async (id) => {
    loading.value = true
    try {
      const response = await taskApi.deleteTask(id)
      
      // 从列表中移除
      const index = tasks.value.findIndex(t => t.id === id)
      if (index !== -1) {
        tasks.value.splice(index, 1)
        total.value -= 1
      }
      
      // 清除当前任务
      if (currentTask.value && currentTask.value.id === id) {
        currentTask.value = null
      }
      
      return response
    } catch (error) {
      throw error
    } finally {
      loading.value = false
    }
  }
  
  /**
   * 执行任务
   * @param {number} id 任务ID
   * @param {object} params 执行参数
   */
  const executeTask = async (id, params = {}) => {
    loading.value = true
    try {
      const response = await taskApi.executeTask(id, params)
      
      // 更新任务状态
      const task = tasks.value.find(t => t.id === id)
      if (task) {
        task.status = 'running'
        task.last_execution_time = new Date().toISOString()
      }
      
      if (currentTask.value && currentTask.value.id === id) {
        currentTask.value.status = 'running'
        currentTask.value.last_execution_time = new Date().toISOString()
      }
      
      return response
    } catch (error) {
      throw error
    } finally {
      loading.value = false
    }
  }
  
  /**
   * 获取任务执行历史
   * @param {number} id 任务ID
   * @param {object} params 查询参数
   */
  const getTaskExecutions = async (id, params = {}) => {
    loading.value = true
    try {
      const response = await taskApi.getTaskExecutions(id, params)
      taskExecutions.value = response.data.items
      return response
    } catch (error) {
      throw error
    } finally {
      loading.value = false
    }
  }
  
  /**
   * 获取所有任务实例
   * @param {object} params 查询参数
   */
  const getAllTaskInstances = async (params = {}) => {
    loading.value = true
    try {
      const response = await taskApi.getAllTaskInstances(params)
      return response.data
    } catch (error) {
      throw error
    } finally {
      loading.value = false
    }
  }

  /**
   * 获取任务实例日志文件
   * @param {number} instanceId 实例ID
   * @param {object} params 查询参数
   */
  const getTaskInstanceLogFile = async (instanceId, params = {}) => {
    // 日志获取不影响全局loading，因为通常在对话框中加载
    try {
      const response = await taskApi.getTaskInstanceLogFile(instanceId, params)
      return response.data
    } catch (error) {
      throw error
    }
  }
  
  /**
   * 获取任务模板列表
   */
  const getTaskTemplates = async () => {
    loading.value = true
    try {
      const response = await taskApi.getTaskTemplates()
      taskTemplates.value = response.data
      return response
    } catch (error) {
      throw error
    } finally {
      loading.value = false
    }
  }
  
  /**
   * 获取任务类型列表
   */
  const getTaskTypes = async () => {
    loading.value = true
    try {
      const response = await taskApi.getTaskTypes()
      taskTypes.value = response.data
      return response
    } catch (error) {
      throw error
    } finally {
      loading.value = false
    }
  }
  
  /**
   * 设置当前任务
   * @param {object} task 任务对象
   */
  const setCurrentTask = (task) => {
    currentTask.value = task
  }
  
  /**
   * 清除当前任务
   */
  const clearCurrentTask = () => {
    currentTask.value = null
  }
  
  /**
   * 重置状态
   */
  const resetState = () => {
    tasks.value = []
    currentTask.value = null
    taskExecutions.value = []
    taskTemplates.value = []
    taskTypes.value = []
    loading.value = false
    total.value = 0
  }
  
  return {
    // 状态
    tasks,
    currentTask,
    taskExecutions,
    taskTemplates,
    taskTypes,
    loading,
    total,
    
    // 计算属性
    taskCount,
    runningTasks,
    completedTasks,
    failedTasks,
    
    // 方法
    getTaskList,
    getTaskDetail,
    createTask,
    updateTask,
    deleteTask,
    executeTask,
    getTaskExecutions,
    getAllTaskInstances,
    getTaskInstanceLogFile,
    getTaskTemplates,
    getTaskTypes,
    setCurrentTask,
    clearCurrentTask,
    resetState
  }
})