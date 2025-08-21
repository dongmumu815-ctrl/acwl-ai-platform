<template>
  <div class="settings">
    <div class="settings-header">
      <h2>系统设置</h2>
      <div class="header-actions">
        <el-button @click="resetSettings" :loading="loading">
          <el-icon><RefreshLeft /></el-icon>
          重置设置
        </el-button>
        <el-button type="primary" @click="saveSettings" :loading="loading">
          <el-icon><Check /></el-icon>
          保存设置
        </el-button>
      </div>
    </div>

    <div class="settings-content" v-loading="loading">
      <el-row :gutter="20">
        <el-col :span="16">
          <el-tabs v-model="activeTab" class="settings-tabs">
            <!-- 基本设置 -->
            <el-tab-pane label="基本设置" name="basic">
              <el-card>
                <template #header>
                  <span>系统基本配置</span>
                </template>
                
                <el-form :model="settings.basic" label-width="120px">
                  <el-form-item label="系统名称">
                    <el-input v-model="settings.basic.system_name" placeholder="请输入系统名称" />
                  </el-form-item>
                  
                  <el-form-item label="系统描述">
                    <el-input
                      v-model="settings.basic.system_description"
                      type="textarea"
                      :rows="3"
                      placeholder="请输入系统描述"
                    />
                  </el-form-item>
                  
                  <el-form-item label="系统版本">
                    <el-input v-model="settings.basic.system_version" readonly />
                  </el-form-item>
                  
                  <el-form-item label="时区设置">
                    <el-select v-model="settings.basic.timezone" placeholder="选择时区">
                      <el-option
                        v-for="tz in timezones"
                        :key="tz.value"
                        :label="tz.label"
                        :value="tz.value"
                      />
                    </el-select>
                  </el-form-item>
                  
                  <el-form-item label="语言设置">
                    <el-select v-model="settings.basic.language" placeholder="选择语言">
                      <el-option label="简体中文" value="zh-CN" />
                      <el-option label="English" value="en-US" />
                    </el-select>
                  </el-form-item>
                  
                  <el-form-item label="主题设置">
                    <el-radio-group v-model="settings.basic.theme">
                      <el-radio label="light">浅色主题</el-radio>
                      <el-radio label="dark">深色主题</el-radio>
                      <el-radio label="auto">跟随系统</el-radio>
                    </el-radio-group>
                  </el-form-item>
                </el-form>
              </el-card>
            </el-tab-pane>

            <!-- 执行设置 -->
            <el-tab-pane label="执行设置" name="execution">
              <el-card>
                <template #header>
                  <span>工作流执行配置</span>
                </template>
                
                <el-form :model="settings.execution" label-width="150px">
                  <el-form-item label="最大并发执行数">
                    <el-input-number
                      v-model="settings.execution.max_concurrent_executions"
                      :min="1"
                      :max="100"
                      controls-position="right"
                    />
                    <div class="form-item-tip">同时执行的工作流最大数量</div>
                  </el-form-item>
                  
                  <el-form-item label="默认超时时间">
                    <el-input-number
                      v-model="settings.execution.default_timeout"
                      :min="60"
                      :max="86400"
                      controls-position="right"
                    />
                    <span class="input-suffix">秒</span>
                    <div class="form-item-tip">工作流执行的默认超时时间</div>
                  </el-form-item>
                  
                  <el-form-item label="默认重试次数">
                    <el-input-number
                      v-model="settings.execution.default_retry_count"
                      :min="0"
                      :max="10"
                      controls-position="right"
                    />
                    <div class="form-item-tip">任务失败时的默认重试次数</div>
                  </el-form-item>
                  
                  <el-form-item label="重试间隔">
                    <el-input-number
                      v-model="settings.execution.retry_delay"
                      :min="1"
                      :max="3600"
                      controls-position="right"
                    />
                    <span class="input-suffix">秒</span>
                    <div class="form-item-tip">重试之间的等待时间</div>
                  </el-form-item>
                  
                  <el-form-item label="任务队列大小">
                    <el-input-number
                      v-model="settings.execution.task_queue_size"
                      :min="100"
                      :max="10000"
                      controls-position="right"
                    />
                    <div class="form-item-tip">等待执行的任务队列最大长度</div>
                  </el-form-item>
                  
                  <el-form-item label="启用任务优先级">
                    <el-switch v-model="settings.execution.enable_task_priority" />
                    <div class="form-item-tip">是否启用任务优先级调度</div>
                  </el-form-item>
                </el-form>
              </el-card>
            </el-tab-pane>

            <!-- 存储设置 -->
            <el-tab-pane label="存储设置" name="storage">
              <el-card>
                <template #header>
                  <span>数据存储配置</span>
                </template>
                
                <el-form :model="settings.storage" label-width="150px">
                  <el-form-item label="执行记录保留">
                    <el-input-number
                      v-model="settings.storage.execution_retention_days"
                      :min="1"
                      :max="365"
                      controls-position="right"
                    />
                    <span class="input-suffix">天</span>
                    <div class="form-item-tip">执行记录的保留天数</div>
                  </el-form-item>
                  
                  <el-form-item label="日志保留时间">
                    <el-input-number
                      v-model="settings.storage.log_retention_days"
                      :min="1"
                      :max="90"
                      controls-position="right"
                    />
                    <span class="input-suffix">天</span>
                    <div class="form-item-tip">系统日志的保留天数</div>
                  </el-form-item>
                  
                  <el-form-item label="文件存储路径">
                    <el-input v-model="settings.storage.file_storage_path" placeholder="文件存储路径" />
                    <div class="form-item-tip">工作流文件的存储路径</div>
                  </el-form-item>
                  
                  <el-form-item label="最大文件大小">
                    <el-input-number
                      v-model="settings.storage.max_file_size"
                      :min="1"
                      :max="1024"
                      controls-position="right"
                    />
                    <span class="input-suffix">MB</span>
                    <div class="form-item-tip">单个文件的最大大小限制</div>
                  </el-form-item>
                  
                  <el-form-item label="启用数据压缩">
                    <el-switch v-model="settings.storage.enable_compression" />
                    <div class="form-item-tip">是否启用数据压缩存储</div>
                  </el-form-item>
                  
                  <el-form-item label="自动清理">
                    <el-switch v-model="settings.storage.auto_cleanup" />
                    <div class="form-item-tip">是否自动清理过期数据</div>
                  </el-form-item>
                </el-form>
              </el-card>
            </el-tab-pane>

            <!-- 通知设置 -->
            <el-tab-pane label="通知设置" name="notification">
              <el-card>
                <template #header>
                  <span>通知配置</span>
                </template>
                
                <el-form :model="settings.notification" label-width="120px">
                  <el-form-item label="启用邮件通知">
                    <el-switch v-model="settings.notification.enable_email" />
                  </el-form-item>
                  
                  <template v-if="settings.notification.enable_email">
                    <el-form-item label="SMTP服务器">
                      <el-input v-model="settings.notification.smtp_host" placeholder="SMTP服务器地址" />
                    </el-form-item>
                    
                    <el-form-item label="SMTP端口">
                      <el-input-number
                        v-model="settings.notification.smtp_port"
                        :min="1"
                        :max="65535"
                        controls-position="right"
                      />
                    </el-form-item>
                    
                    <el-form-item label="发件人邮箱">
                      <el-input v-model="settings.notification.smtp_user" placeholder="发件人邮箱" />
                    </el-form-item>
                    
                    <el-form-item label="邮箱密码">
                      <el-input
                        v-model="settings.notification.smtp_password"
                        type="password"
                        placeholder="邮箱密码或授权码"
                        show-password
                      />
                    </el-form-item>
                    
                    <el-form-item label="启用SSL">
                      <el-switch v-model="settings.notification.smtp_ssl" />
                    </el-form-item>
                    
                    <el-form-item>
                      <el-button @click="testEmailConnection" :loading="testingEmail">
                        测试邮件连接
                      </el-button>
                    </el-form-item>
                  </template>
                  
                  <el-divider />
                  
                  <el-form-item label="通知事件">
                    <el-checkbox-group v-model="settings.notification.events">
                      <el-checkbox label="workflow_success">工作流执行成功</el-checkbox>
                      <el-checkbox label="workflow_failure">工作流执行失败</el-checkbox>
                      <el-checkbox label="task_failure">任务执行失败</el-checkbox>
                      <el-checkbox label="system_error">系统错误</el-checkbox>
                      <el-checkbox label="resource_warning">资源警告</el-checkbox>
                    </el-checkbox-group>
                  </el-form-item>
                  
                  <el-form-item label="默认收件人">
                    <el-select
                      v-model="settings.notification.default_recipients"
                      multiple
                      filterable
                      allow-create
                      placeholder="输入邮箱地址"
                      style="width: 100%"
                    >
                      <el-option
                        v-for="email in commonEmails"
                        :key="email"
                        :label="email"
                        :value="email"
                      />
                    </el-select>
                  </el-form-item>
                </el-form>
              </el-card>
            </el-tab-pane>

            <!-- 安全设置 -->
            <el-tab-pane label="安全设置" name="security">
              <el-card>
                <template #header>
                  <span>安全配置</span>
                </template>
                
                <el-form :model="settings.security" label-width="150px">
                  <el-form-item label="会话超时时间">
                    <el-input-number
                      v-model="settings.security.session_timeout"
                      :min="300"
                      :max="86400"
                      controls-position="right"
                    />
                    <span class="input-suffix">秒</span>
                    <div class="form-item-tip">用户会话的超时时间</div>
                  </el-form-item>
                  
                  <el-form-item label="密码最小长度">
                    <el-input-number
                      v-model="settings.security.password_min_length"
                      :min="6"
                      :max="32"
                      controls-position="right"
                    />
                    <div class="form-item-tip">用户密码的最小长度要求</div>
                  </el-form-item>
                  
                  <el-form-item label="密码复杂度">
                    <el-checkbox-group v-model="settings.security.password_requirements">
                      <el-checkbox label="uppercase">包含大写字母</el-checkbox>
                      <el-checkbox label="lowercase">包含小写字母</el-checkbox>
                      <el-checkbox label="numbers">包含数字</el-checkbox>
                      <el-checkbox label="symbols">包含特殊字符</el-checkbox>
                    </el-checkbox-group>
                  </el-form-item>
                  
                  <el-form-item label="登录失败限制">
                    <el-input-number
                      v-model="settings.security.max_login_attempts"
                      :min="3"
                      :max="10"
                      controls-position="right"
                    />
                    <div class="form-item-tip">连续登录失败次数限制</div>
                  </el-form-item>
                  
                  <el-form-item label="账户锁定时间">
                    <el-input-number
                      v-model="settings.security.lockout_duration"
                      :min="300"
                      :max="3600"
                      controls-position="right"
                    />
                    <span class="input-suffix">秒</span>
                    <div class="form-item-tip">账户被锁定的时间</div>
                  </el-form-item>
                  
                  <el-form-item label="启用双因子认证">
                    <el-switch v-model="settings.security.enable_2fa" />
                    <div class="form-item-tip">是否启用双因子身份认证</div>
                  </el-form-item>
                  
                  <el-form-item label="API访问控制">
                    <el-switch v-model="settings.security.enable_api_rate_limit" />
                    <div class="form-item-tip">是否启用API访问频率限制</div>
                  </el-form-item>
                </el-form>
              </el-card>
            </el-tab-pane>

            <!-- 监控设置 -->
            <el-tab-pane label="监控设置" name="monitoring">
              <el-card>
                <template #header>
                  <span>监控配置</span>
                </template>
                
                <el-form :model="settings.monitoring" label-width="150px">
                  <el-form-item label="启用性能监控">
                    <el-switch v-model="settings.monitoring.enable_performance" />
                    <div class="form-item-tip">是否启用系统性能监控</div>
                  </el-form-item>
                  
                  <el-form-item label="监控数据保留">
                    <el-input-number
                      v-model="settings.monitoring.metrics_retention_days"
                      :min="1"
                      :max="90"
                      controls-position="right"
                    />
                    <span class="input-suffix">天</span>
                    <div class="form-item-tip">监控数据的保留天数</div>
                  </el-form-item>
                  
                  <el-form-item label="采样间隔">
                    <el-input-number
                      v-model="settings.monitoring.sample_interval"
                      :min="10"
                      :max="300"
                      controls-position="right"
                    />
                    <span class="input-suffix">秒</span>
                    <div class="form-item-tip">监控数据的采样间隔</div>
                  </el-form-item>
                  
                  <el-form-item label="CPU使用率警告">
                    <el-input-number
                      v-model="settings.monitoring.cpu_warning_threshold"
                      :min="50"
                      :max="95"
                      controls-position="right"
                    />
                    <span class="input-suffix">%</span>
                    <div class="form-item-tip">CPU使用率警告阈值</div>
                  </el-form-item>
                  
                  <el-form-item label="内存使用率警告">
                    <el-input-number
                      v-model="settings.monitoring.memory_warning_threshold"
                      :min="50"
                      :max="95"
                      controls-position="right"
                    />
                    <span class="input-suffix">%</span>
                    <div class="form-item-tip">内存使用率警告阈值</div>
                  </el-form-item>
                  
                  <el-form-item label="磁盘使用率警告">
                    <el-input-number
                      v-model="settings.monitoring.disk_warning_threshold"
                      :min="70"
                      :max="95"
                      controls-position="right"
                    />
                    <span class="input-suffix">%</span>
                    <div class="form-item-tip">磁盘使用率警告阈值</div>
                  </el-form-item>
                  
                  <el-form-item label="启用健康检查">
                    <el-switch v-model="settings.monitoring.enable_health_check" />
                    <div class="form-item-tip">是否启用系统健康检查</div>
                  </el-form-item>
                </el-form>
              </el-card>
            </el-tab-pane>
          </el-tabs>
        </el-col>
        
        <el-col :span="8">
          <!-- 系统信息 -->
          <el-card class="info-card">
            <template #header>
              <span>系统信息</span>
            </template>
            
            <el-descriptions :column="1" border>
              <el-descriptions-item label="系统版本">
                {{ systemInfo.version || 'v1.0.0' }}
              </el-descriptions-item>
              <el-descriptions-item label="运行时间">
                {{ formatUptime(systemInfo.uptime) }}
              </el-descriptions-item>
              <el-descriptions-item label="CPU使用率">
                <el-progress
                  :percentage="systemInfo.cpu_usage || 0"
                  :status="systemInfo.cpu_usage > 80 ? 'exception' : undefined"
                  :stroke-width="8"
                />
              </el-descriptions-item>
              <el-descriptions-item label="内存使用率">
                <el-progress
                  :percentage="systemInfo.memory_usage || 0"
                  :status="systemInfo.memory_usage > 80 ? 'exception' : undefined"
                  :stroke-width="8"
                />
              </el-descriptions-item>
              <el-descriptions-item label="磁盘使用率">
                <el-progress
                  :percentage="systemInfo.disk_usage || 0"
                  :status="systemInfo.disk_usage > 90 ? 'exception' : undefined"
                  :stroke-width="8"
                />
              </el-descriptions-item>
              <el-descriptions-item label="活跃连接">
                {{ systemInfo.active_connections || 0 }}
              </el-descriptions-item>
            </el-descriptions>
          </el-card>
          
          <!-- 操作日志 -->
          <el-card class="info-card">
            <template #header>
              <div class="card-header">
                <span>最近操作</span>
                <el-button text type="primary" @click="viewAllLogs">
                  查看全部
                </el-button>
              </div>
            </template>
            
            <div v-if="operationLogs.length === 0" class="empty-state">
              <el-empty description="暂无操作记录" :image-size="60" />
            </div>
            
            <div v-else class="log-list">
              <div v-for="log in operationLogs" :key="log.id" class="log-item">
                <div class="log-icon">
                  <el-icon :size="14"><component :is="getLogIcon(log.action)" /></el-icon>
                </div>
                <div class="log-content">
                  <div class="log-action">{{ log.action }}</div>
                  <div class="log-description">{{ log.description }}</div>
                  <div class="log-time">{{ formatDateTime(log.created_at) }}</div>
                </div>
              </div>
            </div>
          </el-card>
          
          <!-- 快速操作 -->
          <el-card class="info-card">
            <template #header>
              <span>快速操作</span>
            </template>
            
            <div class="quick-actions">
              <el-button @click="exportSettings" style="width: 100%; margin-bottom: 12px">
                <el-icon><Download /></el-icon>
                导出配置
              </el-button>
              <el-button @click="importSettings" style="width: 100%; margin-bottom: 12px">
                <el-icon><Upload /></el-icon>
                导入配置
              </el-button>
              <el-button @click="clearCache" style="width: 100%; margin-bottom: 12px">
                <el-icon><Delete /></el-icon>
                清理缓存
              </el-button>
              <el-button @click="restartSystem" type="danger" style="width: 100%">
                <el-icon><RefreshLeft /></el-icon>
                重启系统
              </el-button>
            </div>
          </el-card>
        </el-col>
      </el-row>
    </div>
    
    <!-- 导入配置对话框 -->
    <el-dialog v-model="importDialogVisible" title="导入配置" width="500px">
      <el-upload
        ref="uploadRef"
        :auto-upload="false"
        :show-file-list="false"
        accept=".json"
        :on-change="handleFileChange"
      >
        <el-button type="primary">
          <el-icon><Upload /></el-icon>
          选择配置文件
        </el-button>
        <template #tip>
          <div class="el-upload__tip">
            只能上传 JSON 格式的配置文件
          </div>
        </template>
      </el-upload>
      
      <template #footer>
        <el-button @click="importDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="confirmImport" :disabled="!importFile">
          确认导入
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  RefreshLeft,
  Check,
  Download,
  Upload,
  Delete,
  Setting,
  User,
  Document,
  Warning
} from '@element-plus/icons-vue'
import { useSettingsStore } from '@/stores/settings'
import { formatDateTime, downloadFile } from '@/utils'

const router = useRouter()
const settingsStore = useSettingsStore()

const loading = ref(false)
const testingEmail = ref(false)
const activeTab = ref('basic')
const importDialogVisible = ref(false)
const importFile = ref(null)

const settings = ref({
  basic: {
    system_name: 'TaskFlow',
    system_description: '智能任务流程管理系统',
    system_version: 'v1.0.0',
    timezone: 'Asia/Shanghai',
    language: 'zh-CN',
    theme: 'light'
  },
  execution: {
    max_concurrent_executions: 10,
    default_timeout: 3600,
    default_retry_count: 3,
    retry_delay: 30,
    task_queue_size: 1000,
    enable_task_priority: true
  },
  storage: {
    execution_retention_days: 30,
    log_retention_days: 7,
    file_storage_path: '/data/taskflow',
    max_file_size: 100,
    enable_compression: true,
    auto_cleanup: true
  },
  notification: {
    enable_email: false,
    smtp_host: '',
    smtp_port: 587,
    smtp_user: '',
    smtp_password: '',
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
})

const systemInfo = ref({})
const operationLogs = ref([])

const timezones = [
  { label: '北京时间 (UTC+8)', value: 'Asia/Shanghai' },
  { label: '东京时间 (UTC+9)', value: 'Asia/Tokyo' },
  { label: '纽约时间 (UTC-5)', value: 'America/New_York' },
  { label: '伦敦时间 (UTC+0)', value: 'Europe/London' },
  { label: 'UTC时间 (UTC+0)', value: 'UTC' }
]

const commonEmails = [
  'admin@example.com',
  'support@example.com',
  'ops@example.com'
]

/**
 * 获取设置数据
 */
const fetchSettings = async () => {
  try {
    loading.value = true
    const data = await settingsStore.getSettings()
    if (data) {
      settings.value = { ...settings.value, ...data }
    }
  } catch (error) {
    ElMessage.error('获取设置失败')
    console.error('获取设置失败:', error)
  } finally {
    loading.value = false
  }
}

/**
 * 获取系统信息
 */
const fetchSystemInfo = async () => {
  try {
    systemInfo.value = await settingsStore.getSystemInfo()
  } catch (error) {
    console.error('获取系统信息失败:', error)
  }
}

/**
 * 获取操作日志
 */
const fetchOperationLogs = async () => {
  try {
    const result = await settingsStore.getOperationLogs({ page: 1, size: 10 })
    operationLogs.value = result.items || []
  } catch (error) {
    console.error('获取操作日志失败:', error)
  }
}

/**
 * 保存设置
 */
const saveSettings = async () => {
  try {
    loading.value = true
    await settingsStore.updateSettings(settings.value)
    ElMessage.success('设置保存成功')
  } catch (error) {
    ElMessage.error('设置保存失败')
    console.error('设置保存失败:', error)
  } finally {
    loading.value = false
  }
}

/**
 * 重置设置
 */
const resetSettings = async () => {
  try {
    await ElMessageBox.confirm(
      '确定要重置所有设置吗？此操作将恢复默认配置。',
      '确认重置',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    loading.value = true
    await settingsStore.resetSettings()
    await fetchSettings()
    ElMessage.success('设置重置成功')
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('设置重置失败')
    }
  } finally {
    loading.value = false
  }
}

/**
 * 测试邮件连接
 */
const testEmailConnection = async () => {
  try {
    testingEmail.value = true
    await settingsStore.testEmailConnection(settings.value.notification)
    ElMessage.success('邮件连接测试成功')
  } catch (error) {
    ElMessage.error('邮件连接测试失败')
  } finally {
    testingEmail.value = false
  }
}

/**
 * 导出设置
 */
const exportSettings = () => {
  try {
    const exportData = {
      ...settings.value,
      exported_at: new Date().toISOString(),
      version: '1.0'
    }
    
    const content = JSON.stringify(exportData, null, 2)
    const filename = `taskflow_settings_${Date.now()}.json`
    downloadFile(content, filename, 'application/json')
    ElMessage.success('设置导出成功')
  } catch (error) {
    ElMessage.error('设置导出失败')
  }
}

/**
 * 导入设置
 */
const importSettings = () => {
  importDialogVisible.value = true
}

/**
 * 处理文件选择
 */
const handleFileChange = (file) => {
  importFile.value = file.raw
}

/**
 * 确认导入
 */
const confirmImport = async () => {
  if (!importFile.value) {
    ElMessage.warning('请选择配置文件')
    return
  }
  
  try {
    const reader = new FileReader()
    reader.onload = async (e) => {
      try {
        const importData = JSON.parse(e.target.result)
        
        // 验证配置格式
        if (!importData.basic || !importData.execution) {
          throw new Error('配置文件格式不正确')
        }
        
        await ElMessageBox.confirm(
          '确定要导入此配置吗？当前设置将被覆盖。',
          '确认导入',
          {
            confirmButtonText: '确定',
            cancelButtonText: '取消',
            type: 'warning'
          }
        )
        
        settings.value = { ...settings.value, ...importData }
        await saveSettings()
        importDialogVisible.value = false
        importFile.value = null
        ElMessage.success('配置导入成功')
      } catch (error) {
        ElMessage.error('配置文件解析失败')
      }
    }
    reader.readAsText(importFile.value)
  } catch (error) {
    ElMessage.error('配置导入失败')
  }
}

/**
 * 清理缓存
 */
const clearCache = async () => {
  try {
    await ElMessageBox.confirm(
      '确定要清理系统缓存吗？',
      '确认清理',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    await settingsStore.clearCache()
    ElMessage.success('缓存清理成功')
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('缓存清理失败')
    }
  }
}

/**
 * 重启系统
 */
const restartSystem = async () => {
  try {
    await ElMessageBox.confirm(
      '确定要重启系统吗？重启期间服务将暂时不可用。',
      '确认重启',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    await settingsStore.restartSystem()
    ElMessage.success('系统重启指令已发送')
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('系统重启失败')
    }
  }
}

/**
 * 查看所有日志
 */
const viewAllLogs = () => {
  router.push('/logs')
}

/**
 * 格式化运行时间
 */
const formatUptime = (seconds) => {
  if (!seconds) return '未知'
  
  const days = Math.floor(seconds / 86400)
  const hours = Math.floor((seconds % 86400) / 3600)
  const minutes = Math.floor((seconds % 3600) / 60)
  
  if (days > 0) {
    return `${days}天 ${hours}小时 ${minutes}分钟`
  } else if (hours > 0) {
    return `${hours}小时 ${minutes}分钟`
  } else {
    return `${minutes}分钟`
  }
}

/**
 * 获取日志图标
 */
const getLogIcon = (action) => {
  const icons = {
    'settings_updated': 'Setting',
    'user_created': 'User',
    'user_updated': 'User',
    'system_restarted': 'RefreshLeft',
    'cache_cleared': 'Delete',
    'config_exported': 'Download',
    'config_imported': 'Upload',
    'email_tested': 'Document',
    'error': 'Warning'
  }
  return icons[action] || 'Document'
}

onMounted(async () => {
  await fetchSettings()
  await fetchSystemInfo()
  await fetchOperationLogs()
})
</script>

<style scoped>
.settings {
  padding: 20px;
}

.settings-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.settings-header h2 {
  margin: 0;
  color: var(--el-text-color-primary);
}

.header-actions {
  display: flex;
  gap: 12px;
}

.settings-tabs {
  min-height: 600px;
}

.form-item-tip {
  font-size: 12px;
  color: var(--el-text-color-placeholder);
  margin-top: 4px;
}

.input-suffix {
  margin-left: 8px;
  color: var(--el-text-color-regular);
}

.info-card {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.empty-state {
  text-align: center;
  padding: 20px;
}

.log-list {
  max-height: 300px;
  overflow-y: auto;
}

.log-item {
  display: flex;
  gap: 12px;
  padding: 12px 0;
  border-bottom: 1px solid var(--el-border-color-lighter);
}

.log-item:last-child {
  border-bottom: none;
}

.log-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  background: var(--el-color-primary-light-8);
  color: var(--el-color-primary);
  border-radius: 50%;
  flex-shrink: 0;
}

.log-content {
  flex: 1;
}

.log-action {
  font-weight: 500;
  font-size: 14px;
  margin-bottom: 4px;
}

.log-description {
  font-size: 12px;
  color: var(--el-text-color-regular);
  margin-bottom: 4px;
}

.log-time {
  font-size: 11px;
  color: var(--el-text-color-placeholder);
}

.quick-actions {
  display: flex;
  flex-direction: column;
}
</style>