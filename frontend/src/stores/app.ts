import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export type ThemeMode = 'light' | 'dark' | 'auto'
export type Language = 'zh-CN' | 'en-US'

export const useAppStore = defineStore('app', () => {
  // 状态
  const sidebarCollapsed = ref(false)
  const themeMode = ref<ThemeMode>('auto')
  const isDark = ref(false)
  const language = ref<Language>('zh-CN')
  const loading = ref(false)
  const pageTitle = ref('ACWL AI')
  
  // 计算属性
  const sidebarWidth = computed(() => {
    return sidebarCollapsed.value ? '64px' : '240px'
  })
  
  const mainContentStyle = computed(() => {
    return {
      marginLeft: sidebarWidth.value,
      transition: 'margin-left 0.3s ease'
    }
  })
  
  // 动作
  const toggleSidebar = () => {
    sidebarCollapsed.value = !sidebarCollapsed.value
    // 保存到本地存储
    localStorage.setItem('sidebarCollapsed', String(sidebarCollapsed.value))
  }
  
  const setSidebarCollapsed = (collapsed: boolean) => {
    sidebarCollapsed.value = collapsed
    localStorage.setItem('sidebarCollapsed', String(collapsed))
  }
  
  const setThemeMode = (mode: ThemeMode) => {
    themeMode.value = mode
    localStorage.setItem('themeMode', mode)
    
    // 根据模式设置主题
    if (mode === 'light') {
      setDark(false)
    } else if (mode === 'dark') {
      setDark(true)
    } else {
      // auto 模式，根据系统主题
      const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)')
      setDark(mediaQuery.matches)
    }
  }
  
  const setDark = (dark: boolean) => {
    isDark.value = dark
    
    // 更新 HTML 类名
    if (dark) {
      document.documentElement.classList.add('dark')
    } else {
      document.documentElement.classList.remove('dark')
    }
    
    // 更新 Element Plus 主题
    if (dark) {
      document.documentElement.setAttribute('class', 'dark')
    } else {
      document.documentElement.removeAttribute('class')
    }
  }
  
  const setLanguage = (lang: Language) => {
    language.value = lang
    localStorage.setItem('language', lang)
    
    // 更新 HTML lang 属性
    document.documentElement.lang = lang === 'zh-CN' ? 'zh-CN' : 'en'
  }
  
  const setLoading = (loading_: boolean) => {
    loading.value = loading_
  }
  
  const setPageTitle = (title: string) => {
    pageTitle.value = title
    document.title = `${title} - ACWL AI`
  }
  
  // 初始化应用设置
  const initializeApp = () => {
    // 从本地存储恢复设置
    const savedSidebarCollapsed = localStorage.getItem('sidebarCollapsed')
    if (savedSidebarCollapsed !== null) {
      sidebarCollapsed.value = savedSidebarCollapsed === 'true'
    }
    
    const savedThemeMode = localStorage.getItem('themeMode') as ThemeMode
    if (savedThemeMode && ['light', 'dark', 'auto'].includes(savedThemeMode)) {
      setThemeMode(savedThemeMode)
    } else {
      setThemeMode('auto')
    }
    
    const savedLanguage = localStorage.getItem('language') as Language
    if (savedLanguage && ['zh-CN', 'en-US'].includes(savedLanguage)) {
      setLanguage(savedLanguage)
    } else {
      setLanguage('zh-CN')
    }
  }
  
  // 重置应用设置
  const resetApp = () => {
    sidebarCollapsed.value = false
    setThemeMode('auto')
    setLanguage('zh-CN')
    loading.value = false
    pageTitle.value = 'ACWL AI'
    
    // 清除本地存储
    localStorage.removeItem('sidebarCollapsed')
    localStorage.removeItem('themeMode')
    localStorage.removeItem('language')
  }
  
  return {
    // 状态
    sidebarCollapsed,
    themeMode,
    isDark,
    language,
    loading,
    pageTitle,
    
    // 计算属性
    sidebarWidth,
    mainContentStyle,
    
    // 动作
    toggleSidebar,
    setSidebarCollapsed,
    setThemeMode,
    setDark,
    setLanguage,
    setLoading,
    setPageTitle,
    initializeApp,
    resetApp
  }
})