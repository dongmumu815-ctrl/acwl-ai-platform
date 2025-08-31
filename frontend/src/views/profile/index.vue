<template>
  <div class="profile-page">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="header-content">
        <div class="header-left">
          <h1 class="page-title">
            <el-icon><User /></el-icon>
            个人资料
          </h1>
          <p class="page-description">管理您的个人信息和账户设置</p>
        </div>
      </div>
    </div>
    
    <div class="profile-container">
      <el-row :gutter="20">
        <!-- 左侧个人信息卡片 -->
        <el-col :xs="24" :sm="8" :md="6">
          <div class="profile-card">
            <el-card shadow="never">
              <div class="profile-info">
                <div class="avatar-section">
                  <el-avatar
                    :size="120"
                    :src="userInfo.avatar"
                    class="profile-avatar"
                  >
                    {{ userInfo.username?.charAt(0).toUpperCase() }}
                  </el-avatar>
                  <el-upload
                    class="avatar-uploader"
                    action="#"
                    :show-file-list="false"
                    :before-upload="beforeAvatarUpload"
                    :on-success="handleAvatarSuccess"
                  >
                    <el-button size="small" type="primary" class="upload-btn">
                      <el-icon><Camera /></el-icon>
                      更换头像
                    </el-button>
                  </el-upload>
                </div>
                
                <div class="user-details">
                  <h3 class="username">{{ userInfo.username }}</h3>
                  <p class="email">{{ userInfo.email }}</p>
                  <div class="user-meta">
                    <div class="meta-item">
                      <el-icon><Calendar /></el-icon>
                      <span>注册于 {{ formatDate(userInfo.created_at) }}</span>
                    </div>
                    <div class="meta-item">
                      <el-icon><Clock /></el-icon>
                      <span>最后登录 {{ formatDate(userInfo.last_login) }}</span>
                    </div>
                    <div class="meta-item">
                      <el-icon><Location /></el-icon>
                      <span>{{ userInfo.location || '未设置' }}</span>
                    </div>
                  </div>
                  
                  <div class="user-stats">
                    <div class="stat-item">
                      <div class="stat-value">{{ userStats.models }}</div>
                      <div class="stat-label">模型</div>
                    </div>
                    <div class="stat-item">
                      <div class="stat-value">{{ userStats.trainings }}</div>
                      <div class="stat-label">训练</div>
                    </div>
                    <div class="stat-item">
                      <div class="stat-value">{{ userStats.deployments }}</div>
                      <div class="stat-label">部署</div>
                    </div>
                  </div>
                </div>
              </div>
            </el-card>
          </div>
        </el-col>
        
        <!-- 右侧设置内容 -->
        <el-col :xs="24" :sm="16" :md="18">
          <div class="profile-settings">
            <el-tabs v-model="activeTab" type="border-card">
              <!-- 基本信息 -->
              <el-tab-pane label="基本信息" name="basic">
                <el-card shadow="never">
                  <template #header>
                    <div class="section-header">
                      <h3>基本信息</h3>
                      <p>更新您的个人基本信息</p>
                    </div>
                  </template>
                  
                  <el-form
                    ref="basicFormRef"
                    :model="basicForm"
                    :rules="basicRules"
                    label-width="100px"
                  >
                    <el-row :gutter="20">
                      <el-col :xs="24" :sm="12">
                        <el-form-item label="用户名" prop="username">
                          <el-input
                            v-model="basicForm.username"
                            placeholder="请输入用户名"
                            disabled
                          />
                          <div class="form-tip">用户名不可修改</div>
                        </el-form-item>
                      </el-col>
                      
                      <el-col :xs="24" :sm="12">
                        <el-form-item label="邮箱" prop="email">
                          <el-input
                            v-model="basicForm.email"
                            placeholder="请输入邮箱地址"
                            type="email"
                          />
                        </el-form-item>
                      </el-col>
                    </el-row>
                    
                    <el-row :gutter="20">
                      <el-col :xs="24" :sm="12">
                        <el-form-item label="真实姓名">
                          <el-input
                            v-model="basicForm.realName"
                            placeholder="请输入真实姓名"
                          />
                        </el-form-item>
                      </el-col>
                      
                      <el-col :xs="24" :sm="12">
                        <el-form-item label="手机号">
                          <el-input
                            v-model="basicForm.phone"
                            placeholder="请输入手机号"
                          />
                        </el-form-item>
                      </el-col>
                    </el-row>
                    
                    <el-row :gutter="20">
                      <el-col :xs="24" :sm="12">
                        <el-form-item label="性别">
                          <el-radio-group v-model="basicForm.gender">
                            <el-radio value="male">男</el-radio>
                <el-radio value="female">女</el-radio>
                <el-radio value="other">其他</el-radio>
                          </el-radio-group>
                        </el-form-item>
                      </el-col>
                      
                      <el-col :xs="24" :sm="12">
                        <el-form-item label="生日">
                          <el-date-picker
                            v-model="basicForm.birthday"
                            type="date"
                            placeholder="选择生日"
                            style="width: 100%"
                          />
                        </el-form-item>
                      </el-col>
                    </el-row>
                    
                    <el-row :gutter="20">
                      <el-col :xs="24" :sm="12">
                        <el-form-item label="所在地区">
                          <el-input
                            v-model="basicForm.location"
                            placeholder="请输入所在地区"
                          />
                        </el-form-item>
                      </el-col>
                      
                      <el-col :xs="24" :sm="12">
                        <el-form-item label="职业">
                          <el-input
                            v-model="basicForm.occupation"
                            placeholder="请输入职业"
                          />
                        </el-form-item>
                      </el-col>
                    </el-row>
                    
                    <el-form-item label="个人简介">
                      <el-input
                        v-model="basicForm.bio"
                        type="textarea"
                        :rows="4"
                        placeholder="介绍一下自己吧..."
                        maxlength="500"
                        show-word-limit
                      />
                    </el-form-item>
                    
                    <el-form-item label="个人网站">
                      <el-input
                        v-model="basicForm.website"
                        placeholder="https://example.com"
                      />
                    </el-form-item>
                    
                    <el-form-item>
                      <el-button
                        type="primary"
                        @click="updateBasicInfo"
                        :loading="updating.basic"
                      >
                        保存更改
                      </el-button>
                      <el-button @click="resetBasicForm">
                        重置
                      </el-button>
                    </el-form-item>
                  </el-form>
                </el-card>
              </el-tab-pane>
              
              <!-- 安全设置 -->
              <el-tab-pane label="安全设置" name="security">
                <el-card shadow="never">
                  <template #header>
                    <div class="section-header">
                      <h3>安全设置</h3>
                      <p>管理您的账户安全</p>
                    </div>
                  </template>
                  
                  <!-- 修改密码 -->
                  <div class="security-section">
                    <h4>修改密码</h4>
                    <el-form
                      ref="passwordFormRef"
                      :model="passwordForm"
                      :rules="passwordRules"
                      label-width="120px"
                      style="max-width: 500px"
                    >
                      <el-form-item label="当前密码" prop="currentPassword">
                        <el-input
                          v-model="passwordForm.currentPassword"
                          type="password"
                          placeholder="请输入当前密码"
                          show-password
                        />
                      </el-form-item>
                      
                      <el-form-item label="新密码" prop="newPassword">
                        <el-input
                          v-model="passwordForm.newPassword"
                          type="password"
                          placeholder="请输入新密码"
                          show-password
                        />
                      </el-form-item>
                      
                      <el-form-item label="确认新密码" prop="confirmPassword">
                        <el-input
                          v-model="passwordForm.confirmPassword"
                          type="password"
                          placeholder="请确认新密码"
                          show-password
                        />
                      </el-form-item>
                      
                      <el-form-item>
                        <el-button
                          type="primary"
                          @click="updatePassword"
                          :loading="updating.password"
                        >
                          更新密码
                        </el-button>
                      </el-form-item>
                    </el-form>
                  </div>
                  
                  <el-divider />
                  
                  <!-- 双因子认证 -->
                  <div class="security-section">
                    <h4>双因子认证</h4>
                    <div class="two-factor-section">
                      <div class="two-factor-info">
                        <div class="info-content">
                          <h5>{{ userInfo.two_factor_enabled ? '已启用' : '未启用' }}</h5>
                          <p>
                            {{ userInfo.two_factor_enabled 
                              ? '您的账户已启用双因子认证，登录时需要额外的验证码' 
                              : '启用双因子认证可以为您的账户提供额外的安全保护' 
                            }}
                          </p>
                        </div>
                        <div class="info-action">
                          <el-button
                            v-if="!userInfo.two_factor_enabled"
                            type="primary"
                            @click="enableTwoFactor"
                          >
                            启用
                          </el-button>
                          <el-button
                            v-else
                            type="danger"
                            @click="disableTwoFactor"
                          >
                            禁用
                          </el-button>
                        </div>
                      </div>
                    </div>
                  </div>
                  
                  <el-divider />
                  
                  <!-- 登录设备 -->
                  <div class="security-section">
                    <h4>登录设备</h4>
                    <div class="devices-list">
                      <div
                        v-for="device in loginDevices"
                        :key="device.id"
                        class="device-item"
                      >
                        <div class="device-info">
                          <div class="device-icon">
                            <el-icon>
                              <Monitor v-if="device.type === 'desktop'" />
                              <Cellphone v-else-if="device.type === 'mobile'" />
                              <Platform v-else />
                            </el-icon>
                          </div>
                          <div class="device-details">
                            <h5>{{ device.name }}</h5>
                            <p>{{ device.location }} • {{ formatDate(device.last_active) }}</p>
                            <div class="device-status">
                              <el-tag
                                :type="device.is_current ? 'success' : 'info'"
                                size="small"
                              >
                                {{ device.is_current ? '当前设备' : '其他设备' }}
                              </el-tag>
                            </div>
                          </div>
                        </div>
                        <div class="device-actions" v-if="!device.is_current">
                          <el-button
                            size="small"
                            type="danger"
                            text
                            @click="revokeDevice(device)"
                          >
                            移除
                          </el-button>
                        </div>
                      </div>
                    </div>
                    <el-button
                      type="danger"
                      @click="revokeAllDevices"
                      style="margin-top: 16px"
                    >
                      移除所有其他设备
                    </el-button>
                  </div>
                </el-card>
              </el-tab-pane>
              
              <!-- 通知设置 -->
              <el-tab-pane label="通知设置" name="notifications">
                <el-card shadow="never">
                  <template #header>
                    <div class="section-header">
                      <h3>通知设置</h3>
                      <p>管理您接收通知的方式</p>
                    </div>
                  </template>
                  
                  <el-form :model="notificationSettings" label-width="150px">
                    <div class="notification-section">
                      <h4>邮件通知</h4>
                      <el-form-item label="系统通知">
                        <el-switch
                          v-model="notificationSettings.email.system"
                          active-text="开启"
                          inactive-text="关闭"
                        />
                        <div class="form-tip">接收系统重要通知和更新</div>
                      </el-form-item>
                      
                      <el-form-item label="训练完成">
                        <el-switch
                          v-model="notificationSettings.email.training"
                          active-text="开启"
                          inactive-text="关闭"
                        />
                        <div class="form-tip">模型训练完成时发送邮件通知</div>
                      </el-form-item>
                      
                      <el-form-item label="部署状态">
                        <el-switch
                          v-model="notificationSettings.email.deployment"
                          active-text="开启"
                          inactive-text="关闭"
                        />
                        <div class="form-tip">部署状态变更时发送邮件通知</div>
                      </el-form-item>
                      
                      <el-form-item label="安全警报">
                        <el-switch
                          v-model="notificationSettings.email.security"
                          active-text="开启"
                          inactive-text="关闭"
                        />
                        <div class="form-tip">账户安全相关事件通知</div>
                      </el-form-item>
                    </div>
                    
                    <el-divider />
                    
                    <div class="notification-section">
                      <h4>浏览器通知</h4>
                      <el-form-item label="桌面通知">
                        <el-switch
                          v-model="notificationSettings.browser.desktop"
                          active-text="开启"
                          inactive-text="关闭"
                        />
                        <div class="form-tip">在桌面显示通知消息</div>
                      </el-form-item>
                      
                      <el-form-item label="声音提醒">
                        <el-switch
                          v-model="notificationSettings.browser.sound"
                          active-text="开启"
                          inactive-text="关闭"
                        />
                        <div class="form-tip">通知时播放提示音</div>
                      </el-form-item>
                    </div>
                    
                    <el-divider />
                    
                    <div class="notification-section">
                      <h4>通知频率</h4>
                      <el-form-item label="汇总频率">
                        <el-radio-group v-model="notificationSettings.frequency">
                          <el-radio value="immediate">立即通知</el-radio>
                          <el-radio value="hourly">每小时汇总</el-radio>
                          <el-radio value="daily">每日汇总</el-radio>
                        </el-radio-group>
                      </el-form-item>
                      
                      <el-form-item label="免打扰时间">
                        <el-time-picker
                          v-model="notificationSettings.quietHours.start"
                          placeholder="开始时间"
                          format="HH:mm"
                          style="width: 120px; margin-right: 8px"
                        />
                        <span>至</span>
                        <el-time-picker
                          v-model="notificationSettings.quietHours.end"
                          placeholder="结束时间"
                          format="HH:mm"
                          style="width: 120px; margin-left: 8px"
                        />
                        <div class="form-tip">在此时间段内不会发送通知</div>
                      </el-form-item>
                    </div>
                    
                    <el-form-item>
                      <el-button
                        type="primary"
                        @click="updateNotificationSettings"
                        :loading="updating.notifications"
                      >
                        保存设置
                      </el-button>
                    </el-form-item>
                  </el-form>
                </el-card>
              </el-tab-pane>
              
              <!-- 隐私设置 -->
              <el-tab-pane label="隐私设置" name="privacy">
                <el-card shadow="never">
                  <template #header>
                    <div class="section-header">
                      <h3>隐私设置</h3>
                      <p>控制您的信息可见性</p>
                    </div>
                  </template>
                  
                  <el-form :model="privacySettings" label-width="150px">
                    <div class="privacy-section">
                      <h4>个人信息可见性</h4>
                      <el-form-item label="个人资料">
                        <el-radio-group v-model="privacySettings.profile.visibility">
                          <el-radio value="public">公开</el-radio>
                <el-radio value="private">私密</el-radio>
                <el-radio value="friends">仅好友</el-radio>
                        </el-radio-group>
                        <div class="form-tip">控制其他用户是否可以查看您的个人资料</div>
                      </el-form-item>
                      
                      <el-form-item label="邮箱地址">
                        <el-switch
                          v-model="privacySettings.profile.showEmail"
                          active-text="显示"
                          inactive-text="隐藏"
                        />
                        <div class="form-tip">是否在个人资料中显示邮箱地址</div>
                      </el-form-item>
                      
                      <el-form-item label="手机号码">
                        <el-switch
                          v-model="privacySettings.profile.showPhone"
                          active-text="显示"
                          inactive-text="隐藏"
                        />
                        <div class="form-tip">是否在个人资料中显示手机号码</div>
                      </el-form-item>
                    </div>
                    
                    <el-divider />
                    
                    <div class="privacy-section">
                      <h4>活动记录</h4>
                      <el-form-item label="在线状态">
                        <el-switch
                          v-model="privacySettings.activity.showOnlineStatus"
                          active-text="显示"
                          inactive-text="隐藏"
                        />
                        <div class="form-tip">是否显示您的在线状态</div>
                      </el-form-item>
                      
                      <el-form-item label="最后登录时间">
                        <el-switch
                          v-model="privacySettings.activity.showLastLogin"
                          active-text="显示"
                          inactive-text="隐藏"
                        />
                        <div class="form-tip">是否显示您的最后登录时间</div>
                      </el-form-item>
                      
                      <el-form-item label="项目活动">
                        <el-radio-group v-model="privacySettings.activity.projectVisibility">
                          <el-radio value="public">公开</el-radio>
                          <el-radio value="private">私密</el-radio>
                        </el-radio-group>
                        <div class="form-tip">控制您的项目和模型是否对其他用户可见</div>
                      </el-form-item>
                    </div>
                    
                    <el-divider />
                    
                    <div class="privacy-section">
                      <h4>数据使用</h4>
                      <el-form-item label="使用分析">
                        <el-switch
                          v-model="privacySettings.data.allowAnalytics"
                          active-text="允许"
                          inactive-text="拒绝"
                        />
                        <div class="form-tip">允许收集匿名使用数据以改进服务</div>
                      </el-form-item>
                      
                      <el-form-item label="个性化推荐">
                        <el-switch
                          v-model="privacySettings.data.allowPersonalization"
                          active-text="允许"
                          inactive-text="拒绝"
                        />
                        <div class="form-tip">基于您的使用习惯提供个性化推荐</div>
                      </el-form-item>
                    </div>
                    
                    <el-form-item>
                      <el-button
                        type="primary"
                        @click="updatePrivacySettings"
                        :loading="updating.privacy"
                      >
                        保存设置
                      </el-button>
                    </el-form-item>
                  </el-form>
                </el-card>
              </el-tab-pane>
              
              <!-- 账户管理 -->
              <el-tab-pane label="账户管理" name="account">
                <el-card shadow="never">
                  <template #header>
                    <div class="section-header">
                      <h3>账户管理</h3>
                      <p>管理您的账户状态和数据</p>
                    </div>
                  </template>
                  
                  <div class="account-section">
                    <h4>数据导出</h4>
                    <p>您可以导出您的个人数据，包括个人信息、项目数据等。</p>
                    <el-button @click="exportData" :loading="exporting">
                      <el-icon><Download /></el-icon>
                      导出我的数据
                    </el-button>
                  </div>
                  
                  <el-divider />
                  
                  <div class="account-section">
                    <h4>账户停用</h4>
                    <p>停用账户后，您将无法登录，但数据会被保留。您可以随时重新激活账户。</p>
                    <el-button type="warning" @click="deactivateAccount">
                      <el-icon><Lock /></el-icon>
                      停用账户
                    </el-button>
                  </div>
                  
                  <el-divider />
                  
                  <div class="account-section danger-section">
                    <h4>删除账户</h4>
                    <p class="danger-text">
                      <el-icon><WarningFilled /></el-icon>
                      删除账户是不可逆的操作，将永久删除您的所有数据，包括模型、训练记录等。
                    </p>
                    <el-button type="danger" @click="deleteAccount">
                      <el-icon><Delete /></el-icon>
                      删除账户
                    </el-button>
                  </div>
                </el-card>
              </el-tab-pane>
            </el-tabs>
          </div>
        </el-col>
      </el-row>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox, type FormInstance, type FormRules } from 'element-plus'
import {
  User,
  Camera,
  Calendar,
  Clock,
  Location,
  Monitor,
  Cellphone,
  Platform,
  Download,
  Lock,
  Delete,
  WarningFilled
} from '@element-plus/icons-vue'
import { useUserStore } from '@/stores/user'

const router = useRouter()
const userStore = useUserStore()

// 响应式数据
const activeTab = ref('basic')
const basicFormRef = ref<FormInstance>()
const passwordFormRef = ref<FormInstance>()
const exporting = ref(false)

const updating = reactive({
  basic: false,
  password: false,
  notifications: false,
  privacy: false
})

// 用户信息
const userInfo = reactive({
  id: '1',
  username: 'john_doe',
  email: 'john@example.com',
  avatar: '',
  real_name: 'John Doe',
  phone: '13800138000',
  gender: 'male',
  birthday: new Date('1990-01-01'),
  location: '北京市',
  occupation: 'AI工程师',
  bio: '专注于机器学习和深度学习研究',
  website: 'https://johndoe.com',
  created_at: '2024-01-01T00:00:00Z',
  last_login: '2024-01-21T10:30:00Z',
  two_factor_enabled: false
})

// 用户统计
const userStats = reactive({
  models: 15,
  trainings: 8,
  deployments: 5
})

// 基本信息表单
const basicForm = reactive({
  username: '',
  email: '',
  realName: '',
  phone: '',
  gender: 'male',
  birthday: null,
  location: '',
  occupation: '',
  bio: '',
  website: ''
})

// 密码表单
const passwordForm = reactive({
  currentPassword: '',
  newPassword: '',
  confirmPassword: ''
})

// 通知设置
const notificationSettings = reactive({
  email: {
    system: true,
    training: true,
    deployment: true,
    security: true
  },
  browser: {
    desktop: true,
    sound: false
  },
  frequency: 'immediate',
  quietHours: {
    start: null,
    end: null
  }
})

// 隐私设置
const privacySettings = reactive({
  profile: {
    visibility: 'public',
    showEmail: false,
    showPhone: false
  },
  activity: {
    showOnlineStatus: true,
    showLastLogin: true,
    projectVisibility: 'public'
  },
  data: {
    allowAnalytics: true,
    allowPersonalization: true
  }
})

// 登录设备
const loginDevices = ref([
  {
    id: '1',
    name: 'Chrome on Windows',
    type: 'desktop',
    location: '北京市',
    last_active: '2024-01-21T10:30:00Z',
    is_current: true
  },
  {
    id: '2',
    name: 'Safari on iPhone',
    type: 'mobile',
    location: '上海市',
    last_active: '2024-01-20T15:45:00Z',
    is_current: false
  },
  {
    id: '3',
    name: 'Firefox on MacBook',
    type: 'laptop',
    location: '深圳市',
    last_active: '2024-01-19T09:20:00Z',
    is_current: false
  }
])

// 表单验证规则
const basicRules: FormRules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' }
  ],
  email: [
    { required: true, message: '请输入邮箱地址', trigger: 'blur' },
    { type: 'email', message: '请输入正确的邮箱地址', trigger: 'blur' }
  ]
}

const passwordRules: FormRules = {
  currentPassword: [
    { required: true, message: '请输入当前密码', trigger: 'blur' }
  ],
  newPassword: [
    { required: true, message: '请输入新密码', trigger: 'blur' },
    { min: 6, message: '密码长度不能少于 6 个字符', trigger: 'blur' }
  ],
  confirmPassword: [
    { required: true, message: '请确认新密码', trigger: 'blur' },
    {
      validator: (rule, value, callback) => {
        if (value !== passwordForm.newPassword) {
          callback(new Error('两次输入密码不一致'))
        } else {
          callback()
        }
      },
      trigger: 'blur'
    }
  ]
}

// 方法
const formatDate = (date: string) => {
  return new Date(date).toLocaleString('zh-CN')
}

const beforeAvatarUpload = (file: File) => {
  const isImage = file.type.startsWith('image/')
  const isLt2M = file.size / 1024 / 1024 < 2
  
  if (!isImage) {
    ElMessage.error('只能上传图片文件!')
    return false
  }
  if (!isLt2M) {
    ElMessage.error('图片大小不能超过 2MB!')
    return false
  }
  return true
}

const handleAvatarSuccess = (response: any, file: File) => {
  userInfo.avatar = URL.createObjectURL(file)
  ElMessage.success('头像更新成功')
}

const updateBasicInfo = async () => {
  if (!basicFormRef.value) return
  
  try {
    await basicFormRef.value.validate()
    updating.basic = true
    
    // 这里应该调用实际的API更新用户信息
    await new Promise(resolve => setTimeout(resolve, 1000))
    
    // 更新本地数据
    Object.assign(userInfo, basicForm)
    
    ElMessage.success('个人信息更新成功')
  } catch (error: any) {
    console.error('更新个人信息失败:', error)
    ElMessage.error('更新失败，请稍后重试')
  } finally {
    updating.basic = false
  }
}

const resetBasicForm = () => {
  Object.assign(basicForm, {
    username: userInfo.username,
    email: userInfo.email,
    realName: userInfo.real_name,
    phone: userInfo.phone,
    gender: userInfo.gender,
    birthday: userInfo.birthday,
    location: userInfo.location,
    occupation: userInfo.occupation,
    bio: userInfo.bio,
    website: userInfo.website
  })
}

const updatePassword = async () => {
  if (!passwordFormRef.value) return
  
  try {
    await passwordFormRef.value.validate()
    updating.password = true
    
    // 这里应该调用实际的API更新密码
    await new Promise(resolve => setTimeout(resolve, 1000))
    
    // 清空表单
    passwordForm.currentPassword = ''
    passwordForm.newPassword = ''
    passwordForm.confirmPassword = ''
    
    ElMessage.success('密码更新成功')
  } catch (error: any) {
    console.error('更新密码失败:', error)
    ElMessage.error('更新失败，请稍后重试')
  } finally {
    updating.password = false
  }
}

const enableTwoFactor = async () => {
  try {
    await ElMessageBox.confirm(
      '启用双因子认证后，登录时需要额外的验证码。确定要启用吗？',
      '启用双因子认证',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'info'
      }
    )
    
    // 这里应该调用实际的API启用双因子认证
    userInfo.two_factor_enabled = true
    ElMessage.success('双因子认证已启用')
  } catch (error: any) {
    if (error !== 'cancel') {
      ElMessage.error('启用失败，请稍后重试')
    }
  }
}

const disableTwoFactor = async () => {
  try {
    await ElMessageBox.confirm(
      '禁用双因子认证会降低账户安全性。确定要禁用吗？',
      '禁用双因子认证',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    // 这里应该调用实际的API禁用双因子认证
    userInfo.two_factor_enabled = false
    ElMessage.success('双因子认证已禁用')
  } catch (error: any) {
    if (error !== 'cancel') {
      ElMessage.error('禁用失败，请稍后重试')
    }
  }
}

const revokeDevice = async (device: any) => {
  try {
    await ElMessageBox.confirm(
      `确定要移除设备 "${device.name}" 吗？`,
      '移除设备',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    // 这里应该调用实际的API移除设备
    const index = loginDevices.value.findIndex(d => d.id === device.id)
    if (index > -1) {
      loginDevices.value.splice(index, 1)
    }
    
    ElMessage.success('设备已移除')
  } catch (error: any) {
    if (error !== 'cancel') {
      ElMessage.error('移除失败，请稍后重试')
    }
  }
}

const revokeAllDevices = async () => {
  try {
    await ElMessageBox.confirm(
      '确定要移除所有其他设备吗？这将强制其他设备重新登录。',
      '移除所有设备',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    // 这里应该调用实际的API移除所有其他设备
    loginDevices.value = loginDevices.value.filter(d => d.is_current)
    
    ElMessage.success('所有其他设备已移除')
  } catch (error: any) {
    if (error !== 'cancel') {
      ElMessage.error('移除失败，请稍后重试')
    }
  }
}

const updateNotificationSettings = async () => {
  updating.notifications = true
  try {
    // 这里应该调用实际的API更新通知设置
    await new Promise(resolve => setTimeout(resolve, 1000))
    
    ElMessage.success('通知设置已保存')
  } catch (error: any) {
    console.error('更新通知设置失败:', error)
    ElMessage.error('保存失败，请稍后重试')
  } finally {
    updating.notifications = false
  }
}

const updatePrivacySettings = async () => {
  updating.privacy = true
  try {
    // 这里应该调用实际的API更新隐私设置
    await new Promise(resolve => setTimeout(resolve, 1000))
    
    ElMessage.success('隐私设置已保存')
  } catch (error: any) {
    console.error('更新隐私设置失败:', error)
    ElMessage.error('保存失败，请稍后重试')
  } finally {
    updating.privacy = false
  }
}

const exportData = async () => {
  exporting.value = true
  try {
    // 这里应该调用实际的API导出数据
    await new Promise(resolve => setTimeout(resolve, 3000))
    
    ElMessage.success('数据导出已开始，完成后将发送下载链接到您的邮箱')
  } catch (error: any) {
    console.error('导出数据失败:', error)
    ElMessage.error('导出失败，请稍后重试')
  } finally {
    exporting.value = false
  }
}

const deactivateAccount = async () => {
  try {
    await ElMessageBox.confirm(
      '停用账户后，您将无法登录，但数据会被保留。您可以随时联系管理员重新激活账户。确定要停用吗？',
      '停用账户',
      {
        confirmButtonText: '确定停用',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    // 这里应该调用实际的API停用账户
    ElMessage.success('账户已停用')
    
    // 退出登录
    userStore.logout()
    router.push('/login')
  } catch (error: any) {
    if (error !== 'cancel') {
      ElMessage.error('停用失败，请稍后重试')
    }
  }
}

const deleteAccount = async () => {
  try {
    await ElMessageBox.confirm(
      '删除账户是不可逆的操作，将永久删除您的所有数据，包括模型、训练记录等。请输入您的用户名确认删除。',
      '删除账户',
      {
        confirmButtonText: '确定删除',
        cancelButtonText: '取消',
        type: 'error',
        beforeClose: async (action, instance, done) => {
          if (action === 'confirm') {
            const { value } = await ElMessageBox.prompt(
              '请输入您的用户名以确认删除:',
              '确认删除',
              {
                confirmButtonText: '删除',
                cancelButtonText: '取消',
                inputPattern: new RegExp(`^${userInfo.username}$`),
                inputErrorMessage: '用户名不匹配'
              }
            )
            
            if (value === userInfo.username) {
              done()
            }
          } else {
            done()
          }
        }
      }
    )
    
    // 这里应该调用实际的API删除账户
    ElMessage.success('账户已删除')
    
    // 退出登录
    userStore.logout()
    router.push('/login')
  } catch (error: any) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败，请稍后重试')
    }
  }
}

const loadUserData = async () => {
  try {
    // 这里应该调用实际的API加载用户数据
    // const response = await userApi.getProfile()
    // Object.assign(userInfo, response.data)
    
    // 初始化表单数据
    resetBasicForm()
  } catch (error) {
    console.error('加载用户数据失败:', error)
  }
}

onMounted(() => {
  loadUserData()
})
</script>

<style lang="scss" scoped>
.profile-page {
  padding: 20px;
  
  .page-header {
    margin-bottom: 20px;
    
    .header-content {
      .header-left {
        .page-title {
          display: flex;
          align-items: center;
          gap: 8px;
          font-size: 24px;
          font-weight: 600;
          color: var(--el-text-color-primary);
          margin: 0 0 8px 0;
        }
        
        .page-description {
          color: var(--el-text-color-regular);
          margin: 0;
        }
      }
    }
  }
  
  .profile-container {
    .profile-card {
      .profile-info {
        text-align: center;
        
        .avatar-section {
          margin-bottom: 20px;
          
          .profile-avatar {
            margin-bottom: 12px;
            border: 3px solid var(--el-border-color-light);
          }
          
          .upload-btn {
            font-size: 12px;
          }
        }
        
        .user-details {
          .username {
            font-size: 20px;
            font-weight: 600;
            color: var(--el-text-color-primary);
            margin: 0 0 8px 0;
          }
          
          .email {
            color: var(--el-text-color-regular);
            margin: 0 0 16px 0;
          }
          
          .user-meta {
            margin-bottom: 20px;
            
            .meta-item {
              display: flex;
              align-items: center;
              justify-content: center;
              gap: 6px;
              font-size: 12px;
              color: var(--el-text-color-secondary);
              margin-bottom: 8px;
              
              &:last-child {
                margin-bottom: 0;
              }
            }
          }
          
          .user-stats {
            display: flex;
            justify-content: space-around;
            padding: 16px 0;
            border-top: 1px solid var(--el-border-color-light);
            
            .stat-item {
              text-align: center;
              
              .stat-value {
                font-size: 20px;
                font-weight: 600;
                color: var(--el-color-primary);
                margin-bottom: 4px;
              }
              
              .stat-label {
                font-size: 12px;
                color: var(--el-text-color-secondary);
              }
            }
          }
        }
      }
    }
    
    .profile-settings {
      .section-header {
        h3 {
          font-size: 18px;
          font-weight: 600;
          color: var(--el-text-color-primary);
          margin: 0 0 8px 0;
        }
        
        p {
          color: var(--el-text-color-regular);
          margin: 0;
        }
      }
      
      .form-tip {
        font-size: 12px;
        color: var(--el-text-color-secondary);
        margin-top: 4px;
      }
      
      .security-section {
        margin-bottom: 24px;
        
        h4 {
          font-size: 16px;
          font-weight: 600;
          color: var(--el-text-color-primary);
          margin: 0 0 16px 0;
        }
        
        .two-factor-section {
          .two-factor-info {
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            padding: 16px;
            background: var(--el-fill-color-lighter);
            border-radius: 6px;
            
            .info-content {
              flex: 1;
              
              h5 {
                font-size: 14px;
                font-weight: 600;
                color: var(--el-text-color-primary);
                margin: 0 0 8px 0;
              }
              
              p {
                font-size: 12px;
                color: var(--el-text-color-regular);
                margin: 0;
              }
            }
            
            .info-action {
              margin-left: 16px;
            }
          }
        }
        
        .devices-list {
          .device-item {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 16px;
            border: 1px solid var(--el-border-color-light);
            border-radius: 6px;
            margin-bottom: 12px;
            
            &:last-child {
              margin-bottom: 0;
            }
            
            .device-info {
              display: flex;
              align-items: center;
              gap: 12px;
              
              .device-icon {
                width: 40px;
                height: 40px;
                border-radius: 6px;
                background: var(--el-fill-color-light);
                display: flex;
                align-items: center;
                justify-content: center;
                
                .el-icon {
                  font-size: 20px;
                  color: var(--el-text-color-secondary);
                }
              }
              
              .device-details {
                h5 {
                  font-size: 14px;
                  font-weight: 600;
                  color: var(--el-text-color-primary);
                  margin: 0 0 4px 0;
                }
                
                p {
                  font-size: 12px;
                  color: var(--el-text-color-secondary);
                  margin: 0 0 8px 0;
                }
                
                .device-status {
                  .el-tag {
                    font-size: 10px;
                  }
                }
              }
            }
          }
        }
      }
      
      .notification-section {
        margin-bottom: 24px;
        
        h4 {
          font-size: 16px;
          font-weight: 600;
          color: var(--el-text-color-primary);
          margin: 0 0 16px 0;
        }
      }
      
      .privacy-section {
        margin-bottom: 24px;
        
        h4 {
          font-size: 16px;
          font-weight: 600;
          color: var(--el-text-color-primary);
          margin: 0 0 16px 0;
        }
      }
      
      .account-section {
        margin-bottom: 24px;
        
        h4 {
          font-size: 16px;
          font-weight: 600;
          color: var(--el-text-color-primary);
          margin: 0 0 12px 0;
        }
        
        p {
          color: var(--el-text-color-regular);
          margin: 0 0 16px 0;
        }
        
        &.danger-section {
          .danger-text {
            display: flex;
            align-items: center;
            gap: 8px;
            color: var(--el-color-danger);
            
            .el-icon {
              font-size: 16px;
            }
          }
        }
      }
    }
  }
}

// 响应式设计
@media (max-width: 768px) {
  .profile-page {
    padding: 16px;
    
    .profile-container {
      .profile-card {
        margin-bottom: 20px;
      }
      
      .profile-settings {
        :deep(.el-tabs__content) {
          padding: 16px;
        }
        
        .security-section {
          .two-factor-section {
            .two-factor-info {
              flex-direction: column;
              gap: 12px;
              
              .info-action {
                margin-left: 0;
                align-self: flex-start;
              }
            }
          }
          
          .devices-list {
            .device-item {
              flex-direction: column;
              align-items: flex-start;
              gap: 12px;
              
              .device-actions {
                align-self: flex-end;
              }
            }
          }
        }
      }
    }
  }
}

// 暗色主题
.dark {
  .profile-page {
    .profile-container {
      .profile-settings {
        .security-section {
          .two-factor-section {
            .two-factor-info {
              background: var(--el-fill-color-dark);
            }
          }
          
          .devices-list {
            .device-item {
              border-color: var(--el-border-color);
              
              .device-info {
                .device-icon {
                  background: var(--el-fill-color-dark);
                }
              }
            }
          }
        }
      }
    }
  }
}
</style>