import { defineStore } from 'pinia'
import { ref } from 'vue'

/**
 * 应用状态管理
 */
export const useAppStore = defineStore('app', () => {
  // 状态
  const sidebarCollapsed = ref(false)
  const theme = ref('light')
  const language = ref('zh-CN')
  const breadcrumbs = ref([])
  const pageLoading = ref(false)
  const globalLoading = ref(false)
  
  /**
   * 切换侧边栏折叠状态
   */
  const toggleSidebar = () => {
    sidebarCollapsed.value = !sidebarCollapsed.value
    localStorage.setItem('sidebarCollapsed', sidebarCollapsed.value)
  }
  
  /**
   * 设置侧边栏折叠状态
   * @param {boolean} collapsed 是否折叠
   */
  const setSidebarCollapsed = (collapsed) => {
    sidebarCollapsed.value = collapsed
    localStorage.setItem('sidebarCollapsed', collapsed)
  }
  
  /**
   * 设置主题
   * @param {string} newTheme 主题名称
   */
  const setTheme = (newTheme) => {
    theme.value = newTheme
    localStorage.setItem('theme', newTheme)
    document.documentElement.setAttribute('data-theme', newTheme)
  }
  
  /**
   * 设置语言
   * @param {string} newLanguage 语言代码
   */
  const setLanguage = (newLanguage) => {
    language.value = newLanguage
    localStorage.setItem('language', newLanguage)
  }
  
  /**
   * 设置面包屑
   * @param {array} crumbs 面包屑数组
   */
  const setBreadcrumbs = (crumbs) => {
    breadcrumbs.value = crumbs
  }
  
  /**
   * 添加面包屑
   * @param {object} crumb 面包屑项
   */
  const addBreadcrumb = (crumb) => {
    breadcrumbs.value.push(crumb)
  }
  
  /**
   * 清除面包屑
   */
  const clearBreadcrumbs = () => {
    breadcrumbs.value = []
  }
  
  /**
   * 设置页面加载状态
   * @param {boolean} loading 是否加载中
   */
  const setPageLoading = (loading) => {
    pageLoading.value = loading
  }
  
  /**
   * 设置全局加载状态
   * @param {boolean} loading 是否加载中
   */
  const setGlobalLoading = (loading) => {
    globalLoading.value = loading
  }
  
  /**
   * 初始化应用设置
   */
  const initializeApp = () => {
    // 从localStorage恢复设置
    const savedSidebarCollapsed = localStorage.getItem('sidebarCollapsed')
    if (savedSidebarCollapsed !== null) {
      sidebarCollapsed.value = savedSidebarCollapsed === 'true'
    }
    
    const savedTheme = localStorage.getItem('theme')
    if (savedTheme) {
      setTheme(savedTheme)
    }
    
    const savedLanguage = localStorage.getItem('language')
    if (savedLanguage) {
      language.value = savedLanguage
    }
  }
  
  return {
    // 状态
    sidebarCollapsed,
    theme,
    language,
    breadcrumbs,
    pageLoading,
    globalLoading,
    
    // 方法
    toggleSidebar,
    setSidebarCollapsed,
    setTheme,
    setLanguage,
    setBreadcrumbs,
    addBreadcrumb,
    clearBreadcrumbs,
    setPageLoading,
    setGlobalLoading,
    initializeApp
  }
})