import { createPinia } from 'pinia'

/**
 * 创建Pinia实例
 */
const pinia = createPinia()

export default pinia

// 导出所有store
export { useUserStore } from './user'
export { useWorkflowStore } from './workflow'
export { useTaskStore } from './task'
export { useProjectStore } from './project'
export { useAppStore } from './app'