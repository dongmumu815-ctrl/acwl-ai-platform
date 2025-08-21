import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { projectApi } from '@/api/workflow'

/**
 * 项目状态管理
 */
export const useProjectStore = defineStore('project', () => {
  // 状态
  const projects = ref([])
  const currentProject = ref(null)
  const projectMembers = ref([])
  const loading = ref(false)
  const total = ref(0)
  
  // 计算属性
  const projectCount = computed(() => projects.value.length)
  const activeProjects = computed(() => 
    projects.value.filter(p => p.status === 'ACTIVE')
  )
  const archivedProjects = computed(() => 
    projects.value.filter(p => p.status === 'ARCHIVED')
  )
  
  /**
   * 获取项目列表
   * @param {object} params 查询参数
   * @param {object} config 请求配置（如 skipAutoRedirect）
   */
  const getProjectList = async (params = {}, config = {}) => {
    loading.value = true
    try {
      // 分离查询参数和请求配置
      const { skipAutoRedirect, ...queryParams } = params
      const requestConfig = skipAutoRedirect ? { skipAutoRedirect: true } : {}
      
      const response = await projectApi.getProjectList(queryParams, requestConfig)
      projects.value = response.items
      total.value = response.total
      return response
    } catch (error) {
      throw error
    } finally {
      loading.value = false
    }
  }
  
  /**
   * 获取项目详情
   * @param {number} id 项目ID
   */
  const getProjectDetail = async (id) => {
    loading.value = true
    try {
      const response = await projectApi.getProjectDetail(id)
      currentProject.value = response.data
      return response
    } catch (error) {
      throw error
    } finally {
      loading.value = false
    }
  }
  
  /**
   * 创建项目
   * @param {object} data 项目数据
   */
  const createProject = async (data) => {
    loading.value = true
    try {
      const response = await projectApi.createProject(data)
      const newProject = response.data
      projects.value.unshift(newProject)
      total.value += 1
      return response
    } catch (error) {
      throw error
    } finally {
      loading.value = false
    }
  }
  
  /**
   * 更新项目
   * @param {number} id 项目ID
   * @param {object} data 项目数据
   */
  const updateProject = async (id, data) => {
    loading.value = true
    try {
      const response = await projectApi.updateProject(id, data)
      const updatedProject = response.data
      
      // 更新列表中的项目
      const index = projects.value.findIndex(p => p.id === id)
      if (index !== -1) {
        projects.value[index] = updatedProject
      }
      
      // 更新当前项目
      if (currentProject.value && currentProject.value.id === id) {
        currentProject.value = updatedProject
      }
      
      return response
    } catch (error) {
      throw error
    } finally {
      loading.value = false
    }
  }
  
  /**
   * 删除项目
   * @param {number} id 项目ID
   */
  const deleteProject = async (id) => {
    loading.value = true
    try {
      const response = await projectApi.deleteProject(id)
      
      // 从列表中移除
      const index = projects.value.findIndex(p => p.id === id)
      if (index !== -1) {
        projects.value.splice(index, 1)
        total.value -= 1
      }
      
      // 清除当前项目
      if (currentProject.value && currentProject.value.id === id) {
        currentProject.value = null
      }
      
      return response
    } catch (error) {
      throw error
    } finally {
      loading.value = false
    }
  }
  
  /**
   * 获取项目成员
   * @param {number} id 项目ID
   */
  const getProjectMembers = async (id) => {
    loading.value = true
    try {
      const response = await projectApi.getProjectMembers(id)
      projectMembers.value = response.data
      return response
    } catch (error) {
      throw error
    } finally {
      loading.value = false
    }
  }
  
  /**
   * 添加项目成员
   * @param {number} id 项目ID
   * @param {object} data 成员数据
   */
  const addProjectMember = async (id, data) => {
    loading.value = true
    try {
      const response = await projectApi.addProjectMember(id, data)
      const newMember = response.data
      projectMembers.value.push(newMember)
      return response
    } catch (error) {
      throw error
    } finally {
      loading.value = false
    }
  }
  
  /**
   * 移除项目成员
   * @param {number} id 项目ID
   * @param {number} memberId 成员ID
   */
  const removeProjectMember = async (id, memberId) => {
    loading.value = true
    try {
      const response = await projectApi.removeProjectMember(id, memberId)
      
      // 从成员列表中移除
      const index = projectMembers.value.findIndex(m => m.id === memberId)
      if (index !== -1) {
        projectMembers.value.splice(index, 1)
      }
      
      return response
    } catch (error) {
      throw error
    } finally {
      loading.value = false
    }
  }
  
  /**
   * 设置当前项目
   * @param {object} project 项目对象
   */
  const setCurrentProject = (project) => {
    currentProject.value = project
  }
  
  /**
   * 清除当前项目
   */
  const clearCurrentProject = () => {
    currentProject.value = null
  }
  
  /**
   * 重置状态
   */
  const resetState = () => {
    projects.value = []
    currentProject.value = null
    projectMembers.value = []
    loading.value = false
    total.value = 0
  }
  
  return {
    // 状态
    projects,
    currentProject,
    projectMembers,
    loading,
    total,
    
    // 计算属性
    projectCount,
    activeProjects,
    archivedProjects,
    
    // 方法
    getProjectList,
    getProjectDetail,
    createProject,
    updateProject,
    deleteProject,
    getProjectMembers,
    addProjectMember,
    removeProjectMember,
    setCurrentProject,
    clearCurrentProject,
    resetState
  }
})