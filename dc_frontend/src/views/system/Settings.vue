<template>
  <div class="system-settings">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="header-left">
        <h1 class="page-title">系统设置</h1>
        <p class="page-description">配置系统参数和功能选项</p>
      </div>
      <div class="header-right">
        <el-button @click="handleReset">
          <el-icon><Refresh /></el-icon>
          重置
        </el-button>
        <el-button
          type="primary"
          :loading="saving"
          @click="handleSave"
        >
          <el-icon><Check /></el-icon>
          保存设置
        </el-button>
      </div>
    </div>

    <!-- 设置内容 -->
    <div class="settings-content">
      <el-row :gutter="24">
        <!-- 左侧设置菜单 -->
        <el-col :span="6">
          <el-card class="settings-menu">
            <el-menu
              v-model:default-active="activeTab"
              mode="vertical"
              @select="handleTabChange"
            >
              <el-menu-item index="basic">
                <el-icon><Setting /></el-icon>
                <span>基本设置</span>
              </el-menu-item>
              <el-menu-item index="security">
                <el-icon><Lock /></el-icon>
                <span>安全设置</span>
              </el-menu-item>
              <el-menu-item index="email">
                <el-icon><Message /></el-icon>
                <span>邮件设置</span>
              </el-menu-item>
              <el-menu-item index="storage">
                <el-icon><FolderOpened /></el-icon>
                <span>存储设置</span>
              </el-menu-item>
              <el-menu-item index="backup">
                <el-icon><Download /></el-icon>
                <span>备份设置</span>
              </el-menu-item>
              <el-menu-item index="logs">
                <el-icon><Document /></el-icon>
                <span>日志设置</span>
              </el-menu-item>
              <el-menu-item index="performance">
                <el-icon><TrendCharts /></el-icon>
                <span>性能设置</span>
              </el-menu-item>
            </el-menu>
          </el-card>
        </el-col>

        <!-- 右侧设置表单 -->
        <el-col :span="18">
          <el-card>
            <!-- 基本设置 -->
            <div v-if="activeTab === 'basic'" class="settings-panel">
              <h3 class="panel-title">基本设置</h3>
              <el-form
                ref="basicFormRef"
                :model="settings.basic"
                :rules="basicRules"
                label-width="120px"
              >
                <el-form-item label="系统名称" prop="system_name">
                  <el-input
                    v-model="settings.basic.system_name"
                    placeholder="请输入系统名称"
                    maxlength="50"
                  />
                </el-form-item>

                <el-form-item label="系统描述" prop="system_description">
                  <el-input
                    v-model="settings.basic.system_description"
                    type="textarea"
                    :rows="3"
                    placeholder="请输入系统描述"
                    maxlength="200"
                    show-word-limit
                  />
                </el-form-item>

                <el-form-item label="系统版本" prop="system_version">
                  <el-input
                    v-model="settings.basic.system_version"
                    placeholder="请输入系统版本"
                    maxlength="20"
                  />
                </el-form-item>

                <el-form-item label="默认语言">
                  <el-select v-model="settings.basic.default_language" style="width: 200px">
                    <el-option label="中文" value="zh-CN" />
                    <el-option label="English" value="en-US" />
                  </el-select>
                </el-form-item>

                <el-form-item label="默认时区">
                  <el-select v-model="settings.basic.default_timezone" style="width: 200px">
                    <el-option label="北京时间" value="Asia/Shanghai" />
                    <el-option label="UTC" value="UTC" />
                    <el-option label="纽约时间" value="America/New_York" />
                    <el-option label="伦敦时间" value="Europe/London" />
                  </el-select>
                </el-form-item>

                <el-form-item label="分页大小">
                  <el-input-number
                    v-model="settings.basic.default_page_size"
                    :min="10"
                    :max="100"
                    :step="10"
                    style="width: 200px"
                  />
                </el-form-item>

                <el-form-item label="维护模式">
                  <el-switch
                    v-model="settings.basic.maintenance_mode"
                    active-text="开启"
                    inactive-text="关闭"
                  />
                  <div class="field-tip">
                    开启后，除管理员外其他用户无法访问系统
                  </div>
                </el-form-item>

                <el-form-item label="用户注册">
                  <el-switch
                    v-model="settings.basic.allow_registration"
                    active-text="允许"
                    inactive-text="禁止"
                  />
                </el-form-item>
              </el-form>
            </div>

            <!-- 安全设置 -->
            <div v-if="activeTab === 'security'" class="settings-panel">
              <h3 class="panel-title">安全设置</h3>
              <el-form
                ref="securityFormRef"
                :model="settings.security"
                label-width="120px"
              >
                <el-form-item label="密码策略">
                  <div class="password-policy">
                    <el-checkbox v-model="settings.security.password_policy.require_uppercase">
                      要求大写字母
                    </el-checkbox>
                    <el-checkbox v-model="settings.security.password_policy.require_lowercase">
                      要求小写字母
                    </el-checkbox>
                    <el-checkbox v-model="settings.security.password_policy.require_numbers">
                      要求数字
                    </el-checkbox>
                    <el-checkbox v-model="settings.security.password_policy.require_symbols">
                      要求特殊字符
                    </el-checkbox>
                  </div>
                </el-form-item>

                <el-form-item label="密码长度">
                  <el-input-number
                    v-model="settings.security.password_policy.min_length"
                    :min="6"
                    :max="50"
                    style="width: 200px"
                  />
                  <span class="field-unit">位</span>
                </el-form-item>

                <el-form-item label="密码有效期">
                  <el-input-number
                    v-model="settings.security.password_expiry_days"
                    :min="0"
                    :max="365"
                    style="width: 200px"
                  />
                  <span class="field-unit">天（0表示永不过期）</span>
                </el-form-item>

                <el-form-item label="登录失败限制">
                  <el-input-number
                    v-model="settings.security.max_login_attempts"
                    :min="3"
                    :max="10"
                    style="width: 200px"
                  />
                  <span class="field-unit">次</span>
                </el-form-item>

                <el-form-item label="账户锁定时间">
                  <el-input-number
                    v-model="settings.security.lockout_duration"
                    :min="5"
                    :max="1440"
                    style="width: 200px"
                  />
                  <span class="field-unit">分钟</span>
                </el-form-item>

                <el-form-item label="会话超时">
                  <el-input-number
                    v-model="settings.security.session_timeout"
                    :min="30"
                    :max="1440"
                    style="width: 200px"
                  />
                  <span class="field-unit">分钟</span>
                </el-form-item>

                <el-form-item label="双因子认证">
                  <el-switch
                    v-model="settings.security.enable_2fa"
                    active-text="启用"
                    inactive-text="禁用"
                  />
                </el-form-item>

                <el-form-item label="IP白名单">
                  <el-input
                    v-model="settings.security.ip_whitelist"
                    type="textarea"
                    :rows="3"
                    placeholder="每行一个IP地址或IP段，如：192.168.1.1 或 192.168.1.0/24"
                  />
                </el-form-item>
              </el-form>
            </div>

            <!-- 邮件设置 -->
            <div v-if="activeTab === 'email'" class="settings-panel">
              <h3 class="panel-title">邮件设置</h3>
              <el-form
                ref="emailFormRef"
                :model="settings.email"
                :rules="emailRules"
                label-width="120px"
              >
                <el-form-item label="SMTP服务器" prop="smtp_host">
                  <el-input
                    v-model="settings.email.smtp_host"
                    placeholder="请输入SMTP服务器地址"
                  />
                </el-form-item>

                <el-form-item label="SMTP端口" prop="smtp_port">
                  <el-input-number
                    v-model="settings.email.smtp_port"
                    :min="1"
                    :max="65535"
                    style="width: 200px"
                  />
                </el-form-item>

                <el-form-item label="发件人邮箱" prop="from_email">
                  <el-input
                    v-model="settings.email.from_email"
                    placeholder="请输入发件人邮箱"
                  />
                </el-form-item>

                <el-form-item label="发件人名称">
                  <el-input
                    v-model="settings.email.from_name"
                    placeholder="请输入发件人名称"
                  />
                </el-form-item>

                <el-form-item label="用户名">
                  <el-input
                    v-model="settings.email.smtp_username"
                    placeholder="请输入SMTP用户名"
                  />
                </el-form-item>

                <el-form-item label="密码">
                  <el-input
                    v-model="settings.email.smtp_password"
                    type="password"
                    placeholder="请输入SMTP密码"
                    show-password
                  />
                </el-form-item>

                <el-form-item label="加密方式">
                  <el-select v-model="settings.email.smtp_encryption" style="width: 200px">
                    <el-option label="无" value="none" />
                    <el-option label="SSL" value="ssl" />
                    <el-option label="TLS" value="tls" />
                  </el-select>
                </el-form-item>

                <el-form-item>
                  <el-button @click="testEmailConnection">
                    <el-icon><Connection /></el-icon>
                    测试连接
                  </el-button>
                </el-form-item>
              </el-form>
            </div>

            <!-- 存储设置 -->
            <div v-if="activeTab === 'storage'" class="settings-panel">
              <h3 class="panel-title">存储设置</h3>
              <el-form
                ref="storageFormRef"
                :model="settings.storage"
                label-width="120px"
              >
                <el-form-item label="存储类型">
                  <el-select v-model="settings.storage.storage_type" style="width: 200px">
                    <el-option label="本地存储" value="local" />
                    <el-option label="阿里云OSS" value="aliyun_oss" />
                    <el-option label="腾讯云COS" value="tencent_cos" />
                    <el-option label="AWS S3" value="aws_s3" />
                  </el-select>
                </el-form-item>

                <el-form-item label="存储路径">
                  <el-input
                    v-model="settings.storage.storage_path"
                    placeholder="请输入存储路径"
                  />
                </el-form-item>

                <el-form-item label="最大文件大小">
                  <el-input-number
                    v-model="settings.storage.max_file_size"
                    :min="1"
                    :max="1024"
                    style="width: 200px"
                  />
                  <span class="field-unit">MB</span>
                </el-form-item>

                <el-form-item label="允许的文件类型">
                  <el-input
                    v-model="settings.storage.allowed_file_types"
                    placeholder="如：jpg,png,pdf,xlsx"
                  />
                </el-form-item>

                <el-form-item label="存储配置">
                  <el-input
                    v-model="settings.storage.storage_config"
                    type="textarea"
                    :rows="5"
                    placeholder="JSON格式的存储配置"
                  />
                </el-form-item>
              </el-form>
            </div>

            <!-- 备份设置 -->
            <div v-if="activeTab === 'backup'" class="settings-panel">
              <h3 class="panel-title">备份设置</h3>
              <el-form
                ref="backupFormRef"
                :model="settings.backup"
                label-width="120px"
              >
                <el-form-item label="自动备份">
                  <el-switch
                    v-model="settings.backup.auto_backup"
                    active-text="启用"
                    inactive-text="禁用"
                  />
                </el-form-item>

                <el-form-item label="备份频率">
                  <el-select v-model="settings.backup.backup_frequency" style="width: 200px">
                    <el-option label="每天" value="daily" />
                    <el-option label="每周" value="weekly" />
                    <el-option label="每月" value="monthly" />
                  </el-select>
                </el-form-item>

                <el-form-item label="备份时间">
                  <el-time-picker
                    v-model="settings.backup.backup_time"
                    format="HH:mm"
                    value-format="HH:mm"
                    style="width: 200px"
                  />
                </el-form-item>

                <el-form-item label="保留天数">
                  <el-input-number
                    v-model="settings.backup.retention_days"
                    :min="1"
                    :max="365"
                    style="width: 200px"
                  />
                  <span class="field-unit">天</span>
                </el-form-item>

                <el-form-item label="备份路径">
                  <el-input
                    v-model="settings.backup.backup_path"
                    placeholder="请输入备份存储路径"
                  />
                </el-form-item>

                <el-form-item label="压缩备份">
                  <el-switch
                    v-model="settings.backup.compress_backup"
                    active-text="启用"
                    inactive-text="禁用"
                  />
                </el-form-item>

                <el-form-item>
                  <el-button type="primary" @click="createBackup">
                    <el-icon><Download /></el-icon>
                    立即备份
                  </el-button>
                </el-form-item>
              </el-form>
            </div>

            <!-- 日志设置 -->
            <div v-if="activeTab === 'logs'" class="settings-panel">
              <h3 class="panel-title">日志设置</h3>
              <el-form
                ref="logsFormRef"
                :model="settings.logs"
                label-width="120px"
              >
                <el-form-item label="日志级别">
                  <el-select v-model="settings.logs.log_level" style="width: 200px">
                    <el-option label="DEBUG" value="debug" />
                    <el-option label="INFO" value="info" />
                    <el-option label="WARNING" value="warning" />
                    <el-option label="ERROR" value="error" />
                  </el-select>
                </el-form-item>

                <el-form-item label="日志保留">
                  <el-input-number
                    v-model="settings.logs.log_retention_days"
                    :min="1"
                    :max="365"
                    style="width: 200px"
                  />
                  <span class="field-unit">天</span>
                </el-form-item>

                <el-form-item label="日志文件大小">
                  <el-input-number
                    v-model="settings.logs.max_log_file_size"
                    :min="1"
                    :max="1024"
                    style="width: 200px"
                  />
                  <span class="field-unit">MB</span>
                </el-form-item>

                <el-form-item label="记录用户操作">
                  <el-switch
                    v-model="settings.logs.log_user_actions"
                    active-text="启用"
                    inactive-text="禁用"
                  />
                </el-form-item>

                <el-form-item label="记录API调用">
                  <el-switch
                    v-model="settings.logs.log_api_calls"
                    active-text="启用"
                    inactive-text="禁用"
                  />
                </el-form-item>

                <el-form-item label="记录数据库查询">
                  <el-switch
                    v-model="settings.logs.log_database_queries"
                    active-text="启用"
                    inactive-text="禁用"
                  />
                </el-form-item>
              </el-form>
            </div>

            <!-- 性能设置 -->
            <div v-if="activeTab === 'performance'" class="settings-panel">
              <h3 class="panel-title">性能设置</h3>
              <el-form
                ref="performanceFormRef"
                :model="settings.performance"
                label-width="120px"
              >
                <el-form-item label="缓存启用">
                  <el-switch
                    v-model="settings.performance.enable_cache"
                    active-text="启用"
                    inactive-text="禁用"
                  />
                </el-form-item>

                <el-form-item label="缓存过期时间">
                  <el-input-number
                    v-model="settings.performance.cache_ttl"
                    :min="60"
                    :max="86400"
                    style="width: 200px"
                  />
                  <span class="field-unit">秒</span>
                </el-form-item>

                <el-form-item label="数据库连接池">
                  <el-input-number
                    v-model="settings.performance.db_pool_size"
                    :min="5"
                    :max="100"
                    style="width: 200px"
                  />
                  <span class="field-unit">个</span>
                </el-form-item>

                <el-form-item label="API限流">
                  <el-switch
                    v-model="settings.performance.enable_rate_limit"
                    active-text="启用"
                    inactive-text="禁用"
                  />
                </el-form-item>

                <el-form-item label="每分钟请求数">
                  <el-input-number
                    v-model="settings.performance.rate_limit_per_minute"
                    :min="10"
                    :max="1000"
                    style="width: 200px"
                  />
                  <span class="field-unit">次</span>
                </el-form-item>

                <el-form-item label="压缩响应">
                  <el-switch
                    v-model="settings.performance.enable_compression"
                    active-text="启用"
                    inactive-text="禁用"
                  />
                </el-form-item>
              </el-form>
            </div>
          </el-card>
        </el-col>
      </el-row>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import type { FormInstance, FormRules } from 'element-plus'
import {
  Refresh,
  Check,
  Setting,
  Lock,
  Message,
  FolderOpened,
  Download,
  Document,
  TrendCharts,
  Connection
} from '@element-plus/icons-vue'
import {
  getSystemSettings,
  updateSystemSettings,
  testEmailConnection as testEmail,
  createSystemBackup
} from '@/api/system'

// 响应式数据
const activeTab = ref('basic')
const saving = ref(false)
const basicFormRef = ref<FormInstance>()
const securityFormRef = ref<FormInstance>()
const emailFormRef = ref<FormInstance>()
const storageFormRef = ref<FormInstance>()
const backupFormRef = ref<FormInstance>()
const logsFormRef = ref<FormInstance>()
const performanceFormRef = ref<FormInstance>()

// 设置数据
const settings = reactive({
  basic: {
    system_name: '',
    system_description: '',
    system_version: '',
    default_language: 'zh-CN',
    default_timezone: 'Asia/Shanghai',
    default_page_size: 20,
    maintenance_mode: false,
    allow_registration: true
  },
  security: {
    password_policy: {
      min_length: 8,
      require_uppercase: true,
      require_lowercase: true,
      require_numbers: true,
      require_symbols: true
    },
    password_expiry_days: 90,
    max_login_attempts: 5,
    lockout_duration: 30,
    session_timeout: 120,
    enable_2fa: false,
    ip_whitelist: ''
  },
  email: {
    smtp_host: '',
    smtp_port: 587,
    from_email: '',
    from_name: '',
    smtp_username: '',
    smtp_password: '',
    smtp_encryption: 'tls'
  },
  storage: {
    storage_type: 'local',
    storage_path: '/uploads',
    max_file_size: 100,
    allowed_file_types: 'jpg,jpeg,png,gif,pdf,doc,docx,xls,xlsx',
    storage_config: '{}'
  },
  backup: {
    auto_backup: true,
    backup_frequency: 'daily',
    backup_time: '02:00',
    retention_days: 30,
    backup_path: '/backups',
    compress_backup: true
  },
  logs: {
    log_level: 'info',
    log_retention_days: 30,
    max_log_file_size: 100,
    log_user_actions: true,
    log_api_calls: true,
    log_database_queries: false
  },
  performance: {
    enable_cache: true,
    cache_ttl: 3600,
    db_pool_size: 20,
    enable_rate_limit: true,
    rate_limit_per_minute: 100,
    enable_compression: true
  }
})

// 表单验证规则
const basicRules: FormRules = {
  system_name: [
    { required: true, message: '请输入系统名称', trigger: 'blur' }
  ]
}

const emailRules: FormRules = {
  smtp_host: [
    { required: true, message: '请输入SMTP服务器地址', trigger: 'blur' }
  ],
  smtp_port: [
    { required: true, message: '请输入SMTP端口', trigger: 'blur' }
  ],
  from_email: [
    { required: true, message: '请输入发件人邮箱', trigger: 'blur' },
    { type: 'email', message: '请输入正确的邮箱格式', trigger: 'blur' }
  ]
}

/**
 * 加载系统设置
 */
const loadSettings = async () => {
  try {
    const response = await getSystemSettings()
    Object.assign(settings, response.data)
  } catch (error) {
    ElMessage.error('加载系统设置失败')
  }
}

/**
 * 处理标签页切换
 */
const handleTabChange = (key: string) => {
  activeTab.value = key
}

/**
 * 处理保存设置
 */
const handleSave = async () => {
  try {
    saving.value = true
    await updateSystemSettings(settings)
    ElMessage.success('设置保存成功')
  } catch (error) {
    ElMessage.error('设置保存失败')
  } finally {
    saving.value = false
  }
}

/**
 * 处理重置设置
 */
const handleReset = async () => {
  try {
    await ElMessageBox.confirm(
      '确定要重置所有设置吗？此操作不可撤销。',
      '重置设置',
      {
        type: 'warning'
      }
    )
    
    await loadSettings()
    ElMessage.success('设置已重置')
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('重置设置失败')
    }
  }
}

/**
 * 测试邮件连接
 */
const testEmailConnection = async () => {
  try {
    await testEmail(settings.email)
    ElMessage.success('邮件连接测试成功')
  } catch (error) {
    ElMessage.error('邮件连接测试失败')
  }
}

/**
 * 创建备份
 */
const createBackup = async () => {
  try {
    await createSystemBackup()
    ElMessage.success('备份创建成功')
  } catch (error) {
    ElMessage.error('备份创建失败')
  }
}

// 组件挂载时加载数据
onMounted(() => {
  loadSettings()
})
</script>

<style lang="scss" scoped>
@use "@/styles/variables.scss" as *;

.system-settings {
  padding: $spacing-lg;
  background-color: var(--el-bg-color-page);
  min-height: 100vh;

  .page-header {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    margin-bottom: $spacing-lg;

    .header-left {
      .page-title {
        margin: 0 0 $spacing-xs 0;
        font-size: $font-size-xl;
        font-weight: 600;
        color: var(--el-text-color-primary);
      }

      .page-description {
        margin: 0;
        color: var(--el-text-color-regular);
        font-size: $font-size-sm;
      }
    }

    .header-right {
      display: flex;
      gap: $spacing-sm;
    }
  }

  .settings-content {
    .settings-menu {
      :deep(.el-card__body) {
        padding: 0;
      }

      :deep(.el-menu) {
        border-right: none;
      }
    }

    .settings-panel {
      .panel-title {
        margin: 0 0 $spacing-lg 0;
        font-size: $font-size-lg;
        font-weight: 600;
        color: var(--el-text-color-primary);
        border-bottom: 2px solid var(--el-color-primary);
        padding-bottom: $spacing-xs;
      }

      .field-tip {
        font-size: $font-size-sm;
        color: var(--el-text-color-secondary);
        margin-top: $spacing-xs;
      }

      .field-unit {
        margin-left: $spacing-sm;
        font-size: $font-size-sm;
        color: var(--el-text-color-regular);
      }

      .password-policy {
        display: flex;
        flex-direction: column;
        gap: $spacing-sm;
      }
    }
  }
}

// 响应式设计
@media (max-width: 1200px) {
  .system-settings {
    .settings-content {
      :deep(.el-col) {
        width: 100%;
        margin-bottom: $spacing-lg;
      }
    }
  }
}

@media (max-width: 768px) {
  .system-settings {
    padding: $spacing-md;

    .page-header {
      flex-direction: column;
      gap: $spacing-md;

      .header-right {
        width: 100%;
        justify-content: center;
      }
    }
  }
}

// 暗色主题适配
@media (prefers-color-scheme: dark) {
  .system-settings {
    background-color: var(--el-bg-color-page);
  }
}
</style>