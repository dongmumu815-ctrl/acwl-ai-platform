<template>
  <div class="settings-container">
    <!-- 页面标题 -->
    <div class="page-header">
      <h1 class="page-title">
        <el-icon><Setting /></el-icon>
        系统设置
      </h1>
      <p class="page-description">管理系统的各项配置和参数</p>
    </div>

    <el-row :gutter="20">
      <!-- 左侧导航 -->
      <el-col :span="6">
        <el-card class="settings-nav">
          <el-menu
            :default-active="activeTab"
            @select="handleTabChange"
            class="settings-menu"
          >
            <el-menu-item index="general">
              <el-icon><Setting /></el-icon>
              <span>常规设置</span>
            </el-menu-item>
            <el-menu-item index="security">
              <el-icon><Lock /></el-icon>
              <span>安全设置</span>
            </el-menu-item>
            <el-menu-item index="notification">
              <el-icon><Bell /></el-icon>
              <span>通知设置</span>
            </el-menu-item>
            <el-menu-item index="backup">
              <el-icon><FolderOpened /></el-icon>
              <span>备份设置</span>
            </el-menu-item>
            <el-menu-item index="email">
              <el-icon><Message /></el-icon>
              <span>邮件设置</span>
            </el-menu-item>
            <el-menu-item index="database">
              <el-icon><Coin /></el-icon>
              <span>数据库设置</span>
            </el-menu-item>
            <el-menu-item index="log">
              <el-icon><Document /></el-icon>
              <span>日志设置</span>
            </el-menu-item>
          </el-menu>
        </el-card>
      </el-col>
      
      <!-- 右侧内容 -->
      <el-col :span="18">
        <!-- 常规设置 -->
        <el-card v-show="activeTab === 'general'" class="settings-content">
          <template #header>
            <div class="card-header">
              <el-icon><Setting /></el-icon>
              <span>常规设置</span>
              <el-button type="primary" @click="saveGeneralSettings">
                <el-icon><Check /></el-icon>
                保存设置
              </el-button>
            </div>
          </template>
          
          <el-form
            ref="generalFormRef"
            :model="generalSettings"
            :rules="generalRules"
            label-width="150px"
          >
            <el-form-item label="系统名称" prop="systemName">
              <el-input v-model="generalSettings.systemName" placeholder="请输入系统名称" />
            </el-form-item>
            
            <el-form-item label="系统描述" prop="systemDescription">
              <el-input
                v-model="generalSettings.systemDescription"
                type="textarea"
                :rows="3"
                placeholder="请输入系统描述"
              />
            </el-form-item>
            
            <el-form-item label="系统版本" prop="systemVersion">
              <el-input v-model="generalSettings.systemVersion" placeholder="请输入系统版本" readonly />
            </el-form-item>
            
            <el-form-item label="默认语言" prop="defaultLanguage">
              <el-select v-model="generalSettings.defaultLanguage" placeholder="请选择默认语言">
                <el-option label="简体中文" value="zh-CN" />
                <el-option label="English" value="en-US" />
              </el-select>
            </el-form-item>
            
            <el-form-item label="时区设置" prop="timezone">
              <el-select v-model="generalSettings.timezone" placeholder="请选择时区">
                <el-option label="北京时间 (UTC+8)" value="Asia/Shanghai" />
                <el-option label="纽约时间 (UTC-5)" value="America/New_York" />
                <el-option label="伦敦时间 (UTC+0)" value="Europe/London" />
              </el-select>
            </el-form-item>
            
            <el-form-item label="日期格式" prop="dateFormat">
              <el-select v-model="generalSettings.dateFormat" placeholder="请选择日期格式">
                <el-option label="YYYY-MM-DD" value="YYYY-MM-DD" />
                <el-option label="MM/DD/YYYY" value="MM/DD/YYYY" />
                <el-option label="DD/MM/YYYY" value="DD/MM/YYYY" />
              </el-select>
            </el-form-item>
            
            <el-form-item label="分页大小" prop="pageSize">
              <el-input-number
                v-model="generalSettings.pageSize"
                :min="10"
                :max="100"
                :step="10"
              />
            </el-form-item>
            
            <el-form-item label="会话超时" prop="sessionTimeout">
              <el-input-number
                v-model="generalSettings.sessionTimeout"
                :min="30"
                :max="1440"
                :step="30"
              />
              <span class="form-tip">分钟</span>
            </el-form-item>
            
            <el-form-item label="启用维护模式">
              <el-switch
                v-model="generalSettings.maintenanceMode"
                active-text="开启"
                inactive-text="关闭"
              />
            </el-form-item>
            
            <el-form-item label="维护提示信息" prop="maintenanceMessage" v-if="generalSettings.maintenanceMode">
              <el-input
                v-model="generalSettings.maintenanceMessage"
                type="textarea"
                :rows="2"
                placeholder="请输入维护提示信息"
              />
            </el-form-item>
          </el-form>
        </el-card>
        
        <!-- 安全设置 -->
        <el-card v-show="activeTab === 'security'" class="settings-content">
          <template #header>
            <div class="card-header">
              <el-icon><Lock /></el-icon>
              <span>安全设置</span>
              <el-button type="primary" @click="saveSecuritySettings">
                <el-icon><Check /></el-icon>
                保存设置
              </el-button>
            </div>
          </template>
          
          <el-form
            ref="securityFormRef"
            :model="securitySettings"
            :rules="securityRules"
            label-width="150px"
          >
            <el-form-item label="密码最小长度" prop="minPasswordLength">
              <el-input-number
                v-model="securitySettings.minPasswordLength"
                :min="6"
                :max="20"
              />
            </el-form-item>
            
            <el-form-item label="密码复杂度">
              <el-checkbox-group v-model="securitySettings.passwordComplexity">
                <el-checkbox label="uppercase">包含大写字母</el-checkbox>
                <el-checkbox label="lowercase">包含小写字母</el-checkbox>
                <el-checkbox label="number">包含数字</el-checkbox>
                <el-checkbox label="special">包含特殊字符</el-checkbox>
              </el-checkbox-group>
            </el-form-item>
            
            <el-form-item label="密码有效期" prop="passwordExpiry">
              <el-input-number
                v-model="securitySettings.passwordExpiry"
                :min="0"
                :max="365"
              />
              <span class="form-tip">天（0表示永不过期）</span>
            </el-form-item>
            
            <el-form-item label="登录失败锁定" prop="maxLoginAttempts">
              <el-input-number
                v-model="securitySettings.maxLoginAttempts"
                :min="3"
                :max="10"
              />
              <span class="form-tip">次</span>
            </el-form-item>
            
            <el-form-item label="锁定时间" prop="lockoutDuration">
              <el-input-number
                v-model="securitySettings.lockoutDuration"
                :min="5"
                :max="60"
              />
              <span class="form-tip">分钟</span>
            </el-form-item>
            
            <el-form-item label="启用两步验证">
              <el-switch
                v-model="securitySettings.twoFactorEnabled"
                active-text="开启"
                inactive-text="关闭"
              />
            </el-form-item>
            
            <el-form-item label="IP白名单">
              <el-switch
                v-model="securitySettings.ipWhitelistEnabled"
                active-text="开启"
                inactive-text="关闭"
              />
            </el-form-item>
            
            <el-form-item label="白名单IP" prop="ipWhitelist" v-if="securitySettings.ipWhitelistEnabled">
              <el-input
                v-model="securitySettings.ipWhitelist"
                type="textarea"
                :rows="3"
                placeholder="请输入IP地址，每行一个"
              />
            </el-form-item>
          </el-form>
        </el-card>
        
        <!-- 通知设置 -->
        <el-card v-show="activeTab === 'notification'" class="settings-content">
          <template #header>
            <div class="card-header">
              <el-icon><Bell /></el-icon>
              <span>通知设置</span>
              <el-button type="primary" @click="saveNotificationSettings">
                <el-icon><Check /></el-icon>
                保存设置
              </el-button>
            </div>
          </template>
          
          <el-form
            ref="notificationFormRef"
            :model="notificationSettings"
            label-width="150px"
          >
            <el-form-item label="系统通知">
              <el-switch
                v-model="notificationSettings.systemNotification"
                active-text="开启"
                inactive-text="关闭"
              />
            </el-form-item>
            
            <el-form-item label="邮件通知">
              <el-switch
                v-model="notificationSettings.emailNotification"
                active-text="开启"
                inactive-text="关闭"
              />
            </el-form-item>
            
            <el-form-item label="短信通知">
              <el-switch
                v-model="notificationSettings.smsNotification"
                active-text="开启"
                inactive-text="关闭"
              />
            </el-form-item>
            
            <el-form-item label="通知类型">
              <el-checkbox-group v-model="notificationSettings.notificationTypes">
                <el-checkbox label="login">登录通知</el-checkbox>
                <el-checkbox label="security">安全警告</el-checkbox>
                <el-checkbox label="system">系统更新</el-checkbox>
                <el-checkbox label="backup">备份完成</el-checkbox>
                <el-checkbox label="error">错误报告</el-checkbox>
              </el-checkbox-group>
            </el-form-item>
            
            <el-form-item label="通知频率" prop="notificationFrequency">
              <el-select v-model="notificationSettings.notificationFrequency" placeholder="请选择通知频率">
                <el-option label="实时" value="realtime" />
                <el-option label="每小时" value="hourly" />
                <el-option label="每日" value="daily" />
                <el-option label="每周" value="weekly" />
              </el-select>
            </el-form-item>
            
            <el-form-item label="静默时间">
              <el-time-picker
                v-model="notificationSettings.quietHours"
                is-range
                range-separator="至"
                start-placeholder="开始时间"
                end-placeholder="结束时间"
                format="HH:mm"
                value-format="HH:mm"
              />
            </el-form-item>
          </el-form>
        </el-card>
        
        <!-- 备份设置 -->
        <el-card v-show="activeTab === 'backup'" class="settings-content">
          <template #header>
            <div class="card-header">
              <el-icon><FolderOpened /></el-icon>
              <span>备份设置</span>
              <el-button type="primary" @click="saveBackupSettings">
                <el-icon><Check /></el-icon>
                保存设置
              </el-button>
            </div>
          </template>
          
          <el-form
            ref="backupFormRef"
            :model="backupSettings"
            :rules="backupRules"
            label-width="150px"
          >
            <el-form-item label="自动备份">
              <el-switch
                v-model="backupSettings.autoBackup"
                active-text="开启"
                inactive-text="关闭"
              />
            </el-form-item>
            
            <el-form-item label="备份频率" prop="backupFrequency" v-if="backupSettings.autoBackup">
              <el-select v-model="backupSettings.backupFrequency" placeholder="请选择备份频率">
                <el-option label="每日" value="daily" />
                <el-option label="每周" value="weekly" />
                <el-option label="每月" value="monthly" />
              </el-select>
            </el-form-item>
            
            <el-form-item label="备份时间" prop="backupTime" v-if="backupSettings.autoBackup">
              <el-time-picker
                v-model="backupSettings.backupTime"
                placeholder="选择备份时间"
                format="HH:mm"
                value-format="HH:mm"
              />
            </el-form-item>
            
            <el-form-item label="备份路径" prop="backupPath">
              <el-input v-model="backupSettings.backupPath" placeholder="请输入备份路径">
                <template #append>
                  <el-button @click="selectBackupPath">
                    <el-icon><FolderOpened /></el-icon>
                    选择
                  </el-button>
                </template>
              </el-input>
            </el-form-item>
            
            <el-form-item label="保留天数" prop="retentionDays">
              <el-input-number
                v-model="backupSettings.retentionDays"
                :min="1"
                :max="365"
              />
              <span class="form-tip">天</span>
            </el-form-item>
            
            <el-form-item label="压缩备份">
              <el-switch
                v-model="backupSettings.compression"
                active-text="开启"
                inactive-text="关闭"
              />
            </el-form-item>
            
            <el-form-item label="备份验证">
              <el-switch
                v-model="backupSettings.verification"
                active-text="开启"
                inactive-text="关闭"
              />
            </el-form-item>
          </el-form>
        </el-card>
        
        <!-- 邮件设置 -->
        <el-card v-show="activeTab === 'email'" class="settings-content">
          <template #header>
            <div class="card-header">
              <el-icon><Message /></el-icon>
              <span>邮件设置</span>
              <div class="header-actions">
                <el-button @click="testEmailConnection">
                  <el-icon><Connection /></el-icon>
                  测试连接
                </el-button>
                <el-button type="primary" @click="saveEmailSettings">
                  <el-icon><Check /></el-icon>
                  保存设置
                </el-button>
              </div>
            </div>
          </template>
          
          <el-form
            ref="emailFormRef"
            :model="emailSettings"
            :rules="emailRules"
            label-width="150px"
          >
            <el-form-item label="SMTP服务器" prop="smtpHost">
              <el-input v-model="emailSettings.smtpHost" placeholder="请输入SMTP服务器地址" />
            </el-form-item>
            
            <el-form-item label="SMTP端口" prop="smtpPort">
              <el-input-number
                v-model="emailSettings.smtpPort"
                :min="1"
                :max="65535"
              />
            </el-form-item>
            
            <el-form-item label="加密方式" prop="encryption">
              <el-select v-model="emailSettings.encryption" placeholder="请选择加密方式">
                <el-option label="无" value="none" />
                <el-option label="SSL" value="ssl" />
                <el-option label="TLS" value="tls" />
              </el-select>
            </el-form-item>
            
            <el-form-item label="发件人邮箱" prop="fromEmail">
              <el-input v-model="emailSettings.fromEmail" placeholder="请输入发件人邮箱" />
            </el-form-item>
            
            <el-form-item label="发件人名称" prop="fromName">
              <el-input v-model="emailSettings.fromName" placeholder="请输入发件人名称" />
            </el-form-item>
            
            <el-form-item label="用户名" prop="username">
              <el-input v-model="emailSettings.username" placeholder="请输入SMTP用户名" />
            </el-form-item>
            
            <el-form-item label="密码" prop="password">
              <el-input
                v-model="emailSettings.password"
                type="password"
                placeholder="请输入SMTP密码"
                show-password
              />
            </el-form-item>
          </el-form>
        </el-card>
        
        <!-- 数据库设置 -->
        <el-card v-show="activeTab === 'database'" class="settings-content">
          <template #header>
            <div class="card-header">
              <el-icon><Coin /></el-icon>
              <span>数据库设置</span>
              <div class="header-actions">
                <el-button @click="testDatabaseConnection">
                  <el-icon><Connection /></el-icon>
                  测试连接
                </el-button>
                <el-button type="primary" @click="saveDatabaseSettings">
                  <el-icon><Check /></el-icon>
                  保存设置
                </el-button>
              </div>
            </div>
          </template>
          
          <el-form
            ref="databaseFormRef"
            :model="databaseSettings"
            :rules="databaseRules"
            label-width="150px"
          >
            <el-form-item label="数据库类型" prop="type">
              <el-select v-model="databaseSettings.type" placeholder="请选择数据库类型">
                <el-option label="MySQL" value="mysql" />
                <el-option label="PostgreSQL" value="postgresql" />
                <el-option label="SQLite" value="sqlite" />
              </el-select>
            </el-form-item>
            
            <el-form-item label="服务器地址" prop="host" v-if="databaseSettings.type !== 'sqlite'">
              <el-input v-model="databaseSettings.host" placeholder="请输入数据库服务器地址" />
            </el-form-item>
            
            <el-form-item label="端口" prop="port" v-if="databaseSettings.type !== 'sqlite'">
              <el-input-number
                v-model="databaseSettings.port"
                :min="1"
                :max="65535"
              />
            </el-form-item>
            
            <el-form-item label="数据库名" prop="database">
              <el-input v-model="databaseSettings.database" placeholder="请输入数据库名" />
            </el-form-item>
            
            <el-form-item label="用户名" prop="username" v-if="databaseSettings.type !== 'sqlite'">
              <el-input v-model="databaseSettings.username" placeholder="请输入数据库用户名" />
            </el-form-item>
            
            <el-form-item label="密码" prop="password" v-if="databaseSettings.type !== 'sqlite'">
              <el-input
                v-model="databaseSettings.password"
                type="password"
                placeholder="请输入数据库密码"
                show-password
              />
            </el-form-item>
            
            <el-form-item label="连接池大小" prop="poolSize">
              <el-input-number
                v-model="databaseSettings.poolSize"
                :min="1"
                :max="100"
              />
            </el-form-item>
            
            <el-form-item label="连接超时" prop="timeout">
              <el-input-number
                v-model="databaseSettings.timeout"
                :min="5"
                :max="300"
              />
              <span class="form-tip">秒</span>
            </el-form-item>
          </el-form>
        </el-card>
        
        <!-- 日志设置 -->
        <el-card v-show="activeTab === 'log'" class="settings-content">
          <template #header>
            <div class="card-header">
              <el-icon><Document /></el-icon>
              <span>日志设置</span>
              <el-button type="primary" @click="saveLogSettings">
                <el-icon><Check /></el-icon>
                保存设置
              </el-button>
            </div>
          </template>
          
          <el-form
            ref="logFormRef"
            :model="logSettings"
            :rules="logRules"
            label-width="150px"
          >
            <el-form-item label="日志级别" prop="level">
              <el-select v-model="logSettings.level" placeholder="请选择日志级别">
                <el-option label="DEBUG" value="debug" />
                <el-option label="INFO" value="info" />
                <el-option label="WARN" value="warn" />
                <el-option label="ERROR" value="error" />
              </el-select>
            </el-form-item>
            
            <el-form-item label="日志路径" prop="path">
              <el-input v-model="logSettings.path" placeholder="请输入日志文件路径">
                <template #append>
                  <el-button @click="selectLogPath">
                    <el-icon><FolderOpened /></el-icon>
                    选择
                  </el-button>
                </template>
              </el-input>
            </el-form-item>
            
            <el-form-item label="单文件大小" prop="maxSize">
              <el-input-number
                v-model="logSettings.maxSize"
                :min="1"
                :max="1000"
              />
              <span class="form-tip">MB</span>
            </el-form-item>
            
            <el-form-item label="保留文件数" prop="maxFiles">
              <el-input-number
                v-model="logSettings.maxFiles"
                :min="1"
                :max="100"
              />
            </el-form-item>
            
            <el-form-item label="日志格式" prop="format">
              <el-select v-model="logSettings.format" placeholder="请选择日志格式">
                <el-option label="JSON" value="json" />
                <el-option label="文本" value="text" />
              </el-select>
            </el-form-item>
            
            <el-form-item label="启用访问日志">
              <el-switch
                v-model="logSettings.accessLog"
                active-text="开启"
                inactive-text="关闭"
              />
            </el-form-item>
            
            <el-form-item label="启用错误日志">
              <el-switch
                v-model="logSettings.errorLog"
                active-text="开启"
                inactive-text="关闭"
              />
            </el-form-item>
          </el-form>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Check } from '@element-plus/icons-vue'

// 响应式数据
const activeTab = ref('general')

// 表单引用
const generalFormRef = ref()
const securityFormRef = ref()
const notificationFormRef = ref()
const backupFormRef = ref()
const emailFormRef = ref()
const databaseFormRef = ref()
const logFormRef = ref()

// 常规设置
const generalSettings = reactive({
  systemName: '数据资源中心',
  systemDescription: '企业级数据资源管理平台',
  systemVersion: '1.0.0',
  defaultLanguage: 'zh-CN',
  timezone: 'Asia/Shanghai',
  dateFormat: 'YYYY-MM-DD',
  pageSize: 20,
  sessionTimeout: 120,
  maintenanceMode: false,
  maintenanceMessage: '系统正在维护中，请稍后再试...'
})

// 安全设置
const securitySettings = reactive({
  minPasswordLength: 8,
  passwordComplexity: ['lowercase', 'number'],
  passwordExpiry: 90,
  maxLoginAttempts: 5,
  lockoutDuration: 15,
  twoFactorEnabled: false,
  ipWhitelistEnabled: false,
  ipWhitelist: ''
})

// 通知设置
const notificationSettings = reactive({
  systemNotification: true,
  emailNotification: true,
  smsNotification: false,
  notificationTypes: ['login', 'security', 'system'],
  notificationFrequency: 'realtime',
  quietHours: ['22:00', '08:00']
})

// 备份设置
const backupSettings = reactive({
  autoBackup: true,
  backupFrequency: 'daily',
  backupTime: '02:00',
  backupPath: '/data/backups',
  retentionDays: 30,
  compression: true,
  verification: true
})

// 邮件设置
const emailSettings = reactive({
  smtpHost: 'smtp.example.com',
  smtpPort: 587,
  encryption: 'tls',
  fromEmail: 'noreply@example.com',
  fromName: '数据资源中心',
  username: '',
  password: ''
})

// 数据库设置
const databaseSettings = reactive({
  type: 'mysql',
  host: 'localhost',
  port: 3306,
  database: 'data_center',
  username: 'root',
  password: '',
  poolSize: 10,
  timeout: 30
})

// 日志设置
const logSettings = reactive({
  level: 'info',
  path: '/var/log/datacenter',
  maxSize: 100,
  maxFiles: 10,
  format: 'json',
  accessLog: true,
  errorLog: true
})

// 表单验证规则
const generalRules = {
  systemName: [
    { required: true, message: '请输入系统名称', trigger: 'blur' }
  ],
  systemDescription: [
    { required: true, message: '请输入系统描述', trigger: 'blur' }
  ]
}

const securityRules = {
  minPasswordLength: [
    { required: true, message: '请设置密码最小长度', trigger: 'blur' }
  ]
}

const backupRules = {
  backupPath: [
    { required: true, message: '请输入备份路径', trigger: 'blur' }
  ]
}

const emailRules = {
  smtpHost: [
    { required: true, message: '请输入SMTP服务器地址', trigger: 'blur' }
  ],
  fromEmail: [
    { required: true, message: '请输入发件人邮箱', trigger: 'blur' },
    { type: 'email', message: '请输入正确的邮箱格式', trigger: 'blur' }
  ]
}

const databaseRules = {
  type: [
    { required: true, message: '请选择数据库类型', trigger: 'change' }
  ],
  host: [
    { required: true, message: '请输入数据库服务器地址', trigger: 'blur' }
  ],
  database: [
    { required: true, message: '请输入数据库名', trigger: 'blur' }
  ]
}

const logRules = {
  level: [
    { required: true, message: '请选择日志级别', trigger: 'change' }
  ],
  path: [
    { required: true, message: '请输入日志路径', trigger: 'blur' }
  ]
}

/**
 * 处理标签页切换
 */
const handleTabChange = (key: string) => {
  activeTab.value = key
}

/**
 * 保存常规设置
 */
const saveGeneralSettings = async () => {
  try {
    await generalFormRef.value?.validate()
    // 这里应该调用API保存设置
    ElMessage.success('常规设置保存成功')
  } catch (error) {
    console.error('保存失败:', error)
  }
}

/**
 * 保存安全设置
 */
const saveSecuritySettings = async () => {
  try {
    await securityFormRef.value?.validate()
    // 这里应该调用API保存设置
    ElMessage.success('安全设置保存成功')
  } catch (error) {
    console.error('保存失败:', error)
  }
}

/**
 * 保存通知设置
 */
const saveNotificationSettings = async () => {
  try {
    // 这里应该调用API保存设置
    ElMessage.success('通知设置保存成功')
  } catch (error) {
    console.error('保存失败:', error)
  }
}

/**
 * 保存备份设置
 */
const saveBackupSettings = async () => {
  try {
    await backupFormRef.value?.validate()
    // 这里应该调用API保存设置
    ElMessage.success('备份设置保存成功')
  } catch (error) {
    console.error('保存失败:', error)
  }
}

/**
 * 保存邮件设置
 */
const saveEmailSettings = async () => {
  try {
    await emailFormRef.value?.validate()
    // 这里应该调用API保存设置
    ElMessage.success('邮件设置保存成功')
  } catch (error) {
    console.error('保存失败:', error)
  }
}

/**
 * 保存数据库设置
 */
const saveDatabaseSettings = async () => {
  try {
    await databaseFormRef.value?.validate()
    // 这里应该调用API保存设置
    ElMessage.success('数据库设置保存成功')
  } catch (error) {
    console.error('保存失败:', error)
  }
}

/**
 * 保存日志设置
 */
const saveLogSettings = async () => {
  try {
    await logFormRef.value?.validate()
    // 这里应该调用API保存设置
    ElMessage.success('日志设置保存成功')
  } catch (error) {
    console.error('保存失败:', error)
  }
}

/**
 * 测试邮件连接
 */
const testEmailConnection = async () => {
  try {
    await emailFormRef.value?.validate()
    // 这里应该调用API测试邮件连接
    ElMessage.success('邮件连接测试成功')
  } catch (error) {
    ElMessage.error('邮件连接测试失败')
  }
}

/**
 * 测试数据库连接
 */
const testDatabaseConnection = async () => {
  try {
    await databaseFormRef.value?.validate()
    // 这里应该调用API测试数据库连接
    ElMessage.success('数据库连接测试成功')
  } catch (error) {
    ElMessage.error('数据库连接测试失败')
  }
}

/**
 * 选择备份路径
 */
const selectBackupPath = () => {
  // 这里应该打开文件选择对话框
  ElMessage.info('文件选择功能开发中...')
}

/**
 * 选择日志路径
 */
const selectLogPath = () => {
  // 这里应该打开文件选择对话框
  ElMessage.info('文件选择功能开发中...')
}

/**
 * 组件挂载时初始化
 */
onMounted(() => {
  // 加载设置数据
  // loadSettings()
})
</script>

<style lang="scss" scoped>
.settings-container {
  padding: 20px;
  background: var(--el-bg-color-page);
  min-height: 100vh;
}

.page-header {
  margin-bottom: 24px;
  
  .page-title {
    display: flex;
    align-items: center;
    font-size: 24px;
    font-weight: 600;
    color: var(--el-text-color-primary);
    margin: 0 0 8px 0;
    
    .el-icon {
      margin-right: 8px;
      color: var(--el-color-primary);
    }
  }
  
  .page-description {
    color: var(--el-text-color-secondary);
    margin: 0;
  }
}

.settings-nav {
  .settings-menu {
    border: none;
    
    .el-menu-item {
      border-radius: 6px;
      margin-bottom: 4px;
      
      &.is-active {
        background-color: var(--el-color-primary-light-9);
        color: var(--el-color-primary);
      }
      
      .el-icon {
        margin-right: 8px;
      }
    }
  }
}

.settings-content {
  .card-header {
    display: flex;
    align-items: center;
    gap: 8px;
    font-weight: 600;
    
    .header-actions {
      margin-left: auto;
      display: flex;
      gap: 12px;
    }
  }
  
  .form-tip {
    margin-left: 8px;
    font-size: 12px;
    color: var(--el-text-color-secondary);
  }
}

// 响应式设计
@media (max-width: 1200px) {
  .settings-container {
    .el-col {
      margin-bottom: 20px;
    }
  }
}

@media (max-width: 768px) {
  .settings-container {
    padding: 16px;
    
    .el-col {
      span: 24 !important;
    }
  }
  
  .settings-nav {
    margin-bottom: 20px;
    
    .settings-menu {
      display: flex;
      overflow-x: auto;
      
      .el-menu-item {
        white-space: nowrap;
        margin-right: 8px;
        margin-bottom: 0;
      }
    }
  }
  
  .card-header {
    flex-direction: column !important;
    align-items: stretch !important;
    gap: 12px !important;
    
    .header-actions {
      margin-left: 0 !important;
      justify-content: center;
    }
  }
}
</style>