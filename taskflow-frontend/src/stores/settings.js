import { defineStore } from 'pinia'
import { ref, reactive } from 'vue'
import { ElMessage } from 'element-plus'

export const useSettingsStore = defineStore('settings', () => {
  const loading = ref(false)
  
  // 默认设置
  const defaultSettings = {
    basic: {
      system_name: 'ACWL AI TaskFlow',
      system_description: '企业级AI工作流编排系统',
      system_version: '1.0.0',
      timezone: 'Asia/Shanghai',
      language: 'zh-CN',
      theme: 'light'
    },
    execution: {
      max_concurrent_executions: 10,
      default_timeout: 3600,
      default_retry_count: 3,
      retry_delay: 5,
      task_queue_size: 1000,
      enable_task_priority: true,
      retry_policy: 'exponential_backoff'
    },
    storage: {
      execution_retention_days: 30,
      log_retention_days: 30,
      file_storage_path: '/data/storage',
      max_file_size: 100,
      enable_compression: true,
      auto_cleanup: true
    },
    notification: {
      enable_email: false,
      enable_webhook: false,
      notify_on_success: false,
      notify_on_failure: true,
      smtp_ssl: true,
      events: ['workflow_failure', 'system_error'],
      default_recipients: []
    },
    security: {
      session_timeout: 3600,
      password_min_length: 8,
      password_requirements: ['lowercase', 'numbers'],
      max_login_attempts: 5,
      lockout_duration: 900,
      enable_2fa: false,
      enable_api_rate_limit: true
    },
    monitoring: {
      enable_performance: true,
      metrics_retention_days: 30,
      sample_interval: 60,
      cpu_warning_threshold: 80,
      memory_warning_threshold: 85,
      disk_warning_threshold: 90,
      enable_health_check: true
    }
  }

  // 状态
  const settings = reactive(JSON.parse(JSON.stringify(defaultSettings)))

  // Actions
  const getSettings = async () => {
    loading.value = true
    try {
      // 模拟从API加载
      await new Promise(resolve => setTimeout(resolve, 500))
      
      // 尝试从本地存储加载
      const localSettings = localStorage.getItem('app_settings')
      if (localSettings) {
        try {
          const parsed = JSON.parse(localSettings)
          // 深度合并
          Object.keys(parsed).forEach(key => {
            if (settings[key]) {
              Object.assign(settings[key], parsed[key])
            }
          })
        } catch (e) {
          console.error('Failed to parse local settings', e)
        }
      }
      return settings
    } catch (error) {
      console.error('Failed to load settings', error)
      ElMessage.error('加载设置失败')
      return settings
    } finally {
      loading.value = false
    }
  }

  const updateSettings = async (data) => {
    loading.value = true
    try {
      // 模拟保存到API
      await new Promise(resolve => setTimeout(resolve, 800))
      
      // 更新状态
      Object.keys(data).forEach(key => {
        if (settings[key]) {
          Object.assign(settings[key], data[key])
        }
      })
      
      // 保存到本地存储
      localStorage.setItem('app_settings', JSON.stringify(settings))
      
      return settings
    } catch (error) {
      console.error('Failed to save settings', error)
      throw error
    } finally {
      loading.value = false
    }
  }

  const getSystemInfo = async () => {
    // 模拟系统信息
    await new Promise(resolve => setTimeout(resolve, 300))
    return {
      version: 'v1.0.0',
      uptime: 3600 * 24 * 2 + 3600 * 5, // 2天5小时
      cpu_usage: 45,
      memory_usage: 60,
      disk_usage: 30,
      active_connections: 12
    }
  }

  const getOperationLogs = async (params) => {
    // 模拟操作日志
    await new Promise(resolve => setTimeout(resolve, 300))
    return {
      items: [
        {
          id: 1,
          action: 'settings_updated',
          description: '更新了系统基本设置',
          created_at: new Date(Date.now() - 1000 * 60 * 30).toISOString()
        },
        {
          id: 2,
          action: 'system_restarted',
          description: '系统重启成功',
          created_at: new Date(Date.now() - 1000 * 60 * 60 * 24).toISOString()
        },
        {
          id: 3,
          action: 'user_created',
          description: '创建新用户: admin',
          created_at: new Date(Date.now() - 1000 * 60 * 60 * 48).toISOString()
        }
      ],
      total: 3
    }
  }

  const testEmailConnection = async (config) => {
    await new Promise(resolve => setTimeout(resolve, 2000))
    // 模拟测试成功
    return true
  }

  const resetSettings = async () => {
    try {
      await new Promise(resolve => setTimeout(resolve, 300))
      Object.assign(settings, JSON.parse(JSON.stringify(defaultSettings)))
      localStorage.removeItem('app_settings')
    } catch (error) {
      console.error('Failed to reset settings', error)
      throw error
    }
  }

  return {
    loading,
    settings,
    getSettings,
    updateSettings,
    getSystemInfo,
    getOperationLogs,
    testEmailConnection,
    resetSettings
  }
})
