<template>
  <div class="profile-container">
    <!-- 页面标题 -->
    <div class="page-header">
      <h1 class="page-title">
        <el-icon><User /></el-icon>
        个人资料
      </h1>
      <p class="page-description">管理您的个人信息和账户设置</p>
    </div>

    <el-row :gutter="20">
      <!-- 左侧个人信息 -->
      <el-col :span="8">
        <el-card class="profile-card">
          <div class="profile-header">
            <div class="avatar-section">
              <el-avatar :size="80" :src="userInfo.avatar" class="user-avatar">
                <el-icon><User /></el-icon>
              </el-avatar>
              <el-button type="primary" size="small" @click="showAvatarDialog = true" class="change-avatar-btn">
                <el-icon><Camera /></el-icon>
                更换头像
              </el-button>
            </div>
            <div class="user-basic-info">
              <h3 class="username">{{ userInfo.username }}</h3>
              <p class="user-role">
                <el-tag :type="getRoleType(userInfo.role)">{{ userInfo.roleName }}</el-tag>
              </p>
              <p class="user-email">{{ userInfo.email }}</p>
            </div>
          </div>
          
          <el-divider />
          
          <div class="profile-stats">
            <div class="stat-item">
              <div class="stat-value">{{ userInfo.loginCount }}</div>
              <div class="stat-label">登录次数</div>
            </div>
            <div class="stat-item">
              <div class="stat-value">{{ formatDate(userInfo.lastLogin) }}</div>
              <div class="stat-label">最后登录</div>
            </div>
            <div class="stat-item">
              <div class="stat-value">{{ formatDate(userInfo.createTime) }}</div>
              <div class="stat-label">注册时间</div>
            </div>
          </div>
        </el-card>
        
        <!-- 安全设置 -->
        <el-card class="security-card" style="margin-top: 20px;">
          <template #header>
            <div class="card-header">
              <el-icon><Lock /></el-icon>
              <span>安全设置</span>
            </div>
          </template>
          
          <div class="security-items">
            <div class="security-item">
              <div class="security-info">
                <div class="security-title">登录密码</div>
                <div class="security-desc">定期更换密码可以提高账户安全性</div>
              </div>
              <el-button type="primary" link @click="showPasswordDialog = true">
                修改密码
              </el-button>
            </div>
            
            <el-divider />
            
            <div class="security-item">
              <div class="security-info">
                <div class="security-title">两步验证</div>
                <div class="security-desc">{{ userInfo.twoFactorEnabled ? '已启用' : '未启用' }}</div>
              </div>
              <el-switch
                v-model="userInfo.twoFactorEnabled"
                @change="handleTwoFactorChange"
              />
            </div>
            
            <el-divider />
            
            <div class="security-item">
              <div class="security-info">
                <div class="security-title">登录日志</div>
                <div class="security-desc">查看最近的登录记录</div>
              </div>
              <el-button type="primary" link @click="showLoginLogDialog = true">
                查看日志
              </el-button>
            </div>
          </div>
        </el-card>
      </el-col>
      
      <!-- 右侧详细信息 -->
      <el-col :span="16">
        <el-card>
          <template #header>
            <div class="card-header">
              <el-icon><Edit /></el-icon>
              <span>基本信息</span>
              <el-button type="primary" @click="toggleEdit" class="edit-btn">
                <el-icon><component :is="isEditing ? 'Check' : 'Edit'" /></el-icon>
                {{ isEditing ? '保存' : '编辑' }}
              </el-button>
            </div>
          </template>
          
          <el-form
            ref="profileFormRef"
            :model="profileForm"
            :rules="profileRules"
            label-width="120px"
            :disabled="!isEditing"
          >
            <el-row :gutter="20">
              <el-col :span="12">
                <el-form-item label="用户名" prop="username">
                  <el-input v-model="profileForm.username" placeholder="请输入用户名" />
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="真实姓名" prop="realName">
                  <el-input v-model="profileForm.realName" placeholder="请输入真实姓名" />
                </el-form-item>
              </el-col>
            </el-row>
            
            <el-row :gutter="20">
              <el-col :span="12">
                <el-form-item label="邮箱" prop="email">
                  <el-input v-model="profileForm.email" placeholder="请输入邮箱" />
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="手机号" prop="phone">
                  <el-input v-model="profileForm.phone" placeholder="请输入手机号" />
                </el-form-item>
              </el-col>
            </el-row>
            
            <el-row :gutter="20">
              <el-col :span="12">
                <el-form-item label="性别" prop="gender">
                  <el-select v-model="profileForm.gender" placeholder="请选择性别">
                    <el-option label="男" value="male" />
                    <el-option label="女" value="female" />
                    <el-option label="保密" value="secret" />
                  </el-select>
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="生日" prop="birthday">
                  <el-date-picker
                    v-model="profileForm.birthday"
                    type="date"
                    placeholder="请选择生日"
                    style="width: 100%"
                  />
                </el-form-item>
              </el-col>
            </el-row>
            
            <el-form-item label="部门" prop="department">
              <el-input v-model="profileForm.department" placeholder="请输入部门" />
            </el-form-item>
            
            <el-form-item label="职位" prop="position">
              <el-input v-model="profileForm.position" placeholder="请输入职位" />
            </el-form-item>
            
            <el-form-item label="个人简介" prop="bio">
              <el-input
                v-model="profileForm.bio"
                type="textarea"
                :rows="4"
                placeholder="请输入个人简介"
              />
            </el-form-item>
            
            <el-form-item label="地址" prop="address">
              <el-input v-model="profileForm.address" placeholder="请输入地址" />
            </el-form-item>
          </el-form>
        </el-card>
        
        <!-- 偏好设置 -->
        <el-card style="margin-top: 20px;">
          <template #header>
            <div class="card-header">
              <el-icon><Setting /></el-icon>
              <span>偏好设置</span>
            </div>
          </template>
          
          <el-form label-width="120px">
            <el-form-item label="语言">
              <el-select v-model="preferences.language" @change="handleLanguageChange">
                <el-option label="简体中文" value="zh-CN" />
                <el-option label="English" value="en-US" />
              </el-select>
            </el-form-item>
            
            <el-form-item label="时区">
              <el-select v-model="preferences.timezone" @change="handleTimezoneChange">
                <el-option label="北京时间 (UTC+8)" value="Asia/Shanghai" />
                <el-option label="纽约时间 (UTC-5)" value="America/New_York" />
                <el-option label="伦敦时间 (UTC+0)" value="Europe/London" />
              </el-select>
            </el-form-item>
            
            <el-form-item label="主题">
              <el-radio-group v-model="preferences.theme" @change="handleThemeChange">
                <el-radio label="light">浅色主题</el-radio>
                <el-radio label="dark">深色主题</el-radio>
                <el-radio label="auto">跟随系统</el-radio>
              </el-radio-group>
            </el-form-item>
            
            <el-form-item label="邮件通知">
              <el-switch
                v-model="preferences.emailNotification"
                @change="handleNotificationChange"
              />
            </el-form-item>
            
            <el-form-item label="桌面通知">
              <el-switch
                v-model="preferences.desktopNotification"
                @change="handleNotificationChange"
              />
            </el-form-item>
          </el-form>
        </el-card>
      </el-col>
    </el-row>

    <!-- 更换头像对话框 -->
    <el-dialog v-model="showAvatarDialog" title="更换头像" width="500px">
      <div class="avatar-upload">
        <el-upload
          class="avatar-uploader"
          action="#"
          :show-file-list="false"
          :before-upload="beforeAvatarUpload"
          :http-request="handleAvatarUpload"
        >
          <img v-if="newAvatar" :src="newAvatar" class="avatar-preview" />
          <el-icon v-else class="avatar-uploader-icon"><Plus /></el-icon>
        </el-upload>
        <div class="upload-tips">
          <p>支持 JPG、PNG 格式，文件大小不超过 2MB</p>
          <p>建议上传 200x200 像素的正方形图片</p>
        </div>
      </div>
      
      <template #footer>
        <el-button @click="showAvatarDialog = false">取消</el-button>
        <el-button type="primary" @click="confirmAvatarChange" :disabled="!newAvatar">
          确认更换
        </el-button>
      </template>
    </el-dialog>

    <!-- 修改密码对话框 -->
    <el-dialog v-model="showPasswordDialog" title="修改密码" width="400px">
      <el-form
        ref="passwordFormRef"
        :model="passwordForm"
        :rules="passwordRules"
        label-width="100px"
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
        <el-form-item label="确认密码" prop="confirmPassword">
          <el-input
            v-model="passwordForm.confirmPassword"
            type="password"
            placeholder="请再次输入新密码"
            show-password
          />
        </el-form-item>
      </el-form>
      
      <template #footer>
        <el-button @click="showPasswordDialog = false">取消</el-button>
        <el-button type="primary" @click="handlePasswordChange">确认修改</el-button>
      </template>
    </el-dialog>

    <!-- 登录日志对话框 -->
    <el-dialog v-model="showLoginLogDialog" title="登录日志" width="800px">
      <el-table :data="loginLogs" stripe>
        <el-table-column prop="loginTime" label="登录时间" width="180">
          <template #default="{ row }">
            {{ formatDate(row.loginTime) }}
          </template>
        </el-table-column>
        <el-table-column prop="ip" label="IP地址" width="150" />
        <el-table-column prop="location" label="登录地点" width="200" />
        <el-table-column prop="device" label="设备" width="150" />
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="row.status === 'success' ? 'success' : 'danger'">
              {{ row.status === 'success' ? '成功' : '失败' }}
            </el-tag>
          </template>
        </el-table-column>
      </el-table>
      
      <template #footer>
        <el-button @click="showLoginLogDialog = false">关闭</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Check, Edit, Plus } from '@element-plus/icons-vue'

// 响应式数据
const isEditing = ref(false)
const showAvatarDialog = ref(false)
const showPasswordDialog = ref(false)
const showLoginLogDialog = ref(false)
const newAvatar = ref('')

// 表单引用
const profileFormRef = ref()
const passwordFormRef = ref()

// 用户信息
const userInfo = reactive({
  id: 1,
  username: 'admin',
  realName: '管理员',
  email: 'admin@example.com',
  phone: '13800138000',
  avatar: '',
  role: 'admin',
  roleName: '系统管理员',
  loginCount: 156,
  lastLogin: '2024-01-20 15:30:00',
  createTime: '2023-01-01 10:00:00',
  twoFactorEnabled: false
})

// 个人资料表单
const profileForm = reactive({
  username: userInfo.username,
  realName: userInfo.realName,
  email: userInfo.email,
  phone: userInfo.phone,
  gender: 'male',
  birthday: null,
  department: '技术部',
  position: '系统管理员',
  bio: '负责系统的日常维护和管理工作',
  address: '北京市朝阳区'
})

// 密码修改表单
const passwordForm = reactive({
  currentPassword: '',
  newPassword: '',
  confirmPassword: ''
})

// 偏好设置
const preferences = reactive({
  language: 'zh-CN',
  timezone: 'Asia/Shanghai',
  theme: 'light',
  emailNotification: true,
  desktopNotification: false
})

// 登录日志
const loginLogs = ref([
  {
    id: 1,
    loginTime: '2024-01-20 15:30:00',
    ip: '192.168.1.100',
    location: '北京市',
    device: 'Chrome 120.0',
    status: 'success'
  },
  {
    id: 2,
    loginTime: '2024-01-20 09:15:00',
    ip: '192.168.1.100',
    location: '北京市',
    device: 'Chrome 120.0',
    status: 'success'
  },
  {
    id: 3,
    loginTime: '2024-01-19 18:45:00',
    ip: '192.168.1.101',
    location: '上海市',
    device: 'Firefox 121.0',
    status: 'failed'
  }
])

// 表单验证规则
const profileRules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 3, max: 20, message: '用户名长度在 3 到 20 个字符', trigger: 'blur' }
  ],
  email: [
    { required: true, message: '请输入邮箱', trigger: 'blur' },
    { type: 'email', message: '请输入正确的邮箱格式', trigger: 'blur' }
  ],
  phone: [
    { pattern: /^1[3-9]\d{9}$/, message: '请输入正确的手机号', trigger: 'blur' }
  ]
}

const passwordRules = {
  currentPassword: [
    { required: true, message: '请输入当前密码', trigger: 'blur' }
  ],
  newPassword: [
    { required: true, message: '请输入新密码', trigger: 'blur' },
    { min: 6, max: 20, message: '密码长度在 6 到 20 个字符', trigger: 'blur' }
  ],
  confirmPassword: [
    { required: true, message: '请确认新密码', trigger: 'blur' },
    {
      validator: (rule: any, value: string, callback: Function) => {
        if (value !== passwordForm.newPassword) {
          callback(new Error('两次输入的密码不一致'))
        } else {
          callback()
        }
      },
      trigger: 'blur'
    }
  ]
}

/**
 * 格式化日期
 */
const formatDate = (dateStr: string) => {
  if (!dateStr) return '-'
  return new Date(dateStr).toLocaleString('zh-CN')
}

/**
 * 获取角色类型
 */
const getRoleType = (role: string) => {
  const roleTypes: Record<string, string> = {
    admin: 'danger',
    manager: 'warning',
    user: 'info'
  }
  return roleTypes[role] || 'info'
}

/**
 * 切换编辑模式
 */
const toggleEdit = async () => {
  if (isEditing.value) {
    // 保存操作
    try {
      await profileFormRef.value?.validate()
      await saveProfile()
      isEditing.value = false
    } catch (error) {
      console.error('表单验证失败:', error)
    }
  } else {
    // 进入编辑模式
    isEditing.value = true
  }
}

/**
 * 保存个人资料
 */
const saveProfile = async () => {
  try {
    // 这里应该调用API保存数据
    // await updateProfile(profileForm)
    
    // 更新用户信息
    Object.assign(userInfo, profileForm)
    
    ElMessage.success('个人资料保存成功')
  } catch (error) {
    ElMessage.error('保存失败，请重试')
    throw error
  }
}

/**
 * 头像上传前验证
 */
const beforeAvatarUpload = (file: File) => {
  const isJPG = file.type === 'image/jpeg' || file.type === 'image/png'
  const isLt2M = file.size / 1024 / 1024 < 2

  if (!isJPG) {
    ElMessage.error('头像只能是 JPG 或 PNG 格式!')
  }
  if (!isLt2M) {
    ElMessage.error('头像大小不能超过 2MB!')
  }
  return isJPG && isLt2M
}

/**
 * 处理头像上传
 */
const handleAvatarUpload = (options: any) => {
  const file = options.file
  const reader = new FileReader()
  reader.onload = (e) => {
    newAvatar.value = e.target?.result as string
  }
  reader.readAsDataURL(file)
}

/**
 * 确认更换头像
 */
const confirmAvatarChange = async () => {
  try {
    // 这里应该调用API上传头像
    // await uploadAvatar(newAvatar.value)
    
    userInfo.avatar = newAvatar.value
    showAvatarDialog.value = false
    newAvatar.value = ''
    
    ElMessage.success('头像更换成功')
  } catch (error) {
    ElMessage.error('头像上传失败，请重试')
  }
}

/**
 * 处理密码修改
 */
const handlePasswordChange = async () => {
  try {
    await passwordFormRef.value?.validate()
    
    // 这里应该调用API修改密码
    // await changePassword(passwordForm)
    
    showPasswordDialog.value = false
    Object.assign(passwordForm, {
      currentPassword: '',
      newPassword: '',
      confirmPassword: ''
    })
    
    ElMessage.success('密码修改成功')
  } catch (error) {
    console.error('密码修改失败:', error)
  }
}

/**
 * 处理两步验证切换
 */
const handleTwoFactorChange = async (enabled: boolean) => {
  try {
    if (enabled) {
      await ElMessageBox.confirm(
        '启用两步验证后，登录时需要额外的验证码。是否继续？',
        '确认启用',
        {
          confirmButtonText: '确定',
          cancelButtonText: '取消',
          type: 'warning'
        }
      )
    }
    
    // 这里应该调用API更新设置
    // await updateTwoFactor(enabled)
    
    ElMessage.success(`两步验证已${enabled ? '启用' : '关闭'}`)
  } catch (error) {
    // 恢复原状态
    userInfo.twoFactorEnabled = !enabled
  }
}

/**
 * 处理语言变化
 */
const handleLanguageChange = (language: string) => {
  // 这里应该调用API保存偏好设置
  ElMessage.success('语言设置已保存')
}

/**
 * 处理时区变化
 */
const handleTimezoneChange = (timezone: string) => {
  // 这里应该调用API保存偏好设置
  ElMessage.success('时区设置已保存')
}

/**
 * 处理主题变化
 */
const handleThemeChange = (theme: string) => {
  // 这里应该调用API保存偏好设置并应用主题
  ElMessage.success('主题设置已保存')
}

/**
 * 处理通知设置变化
 */
const handleNotificationChange = () => {
  // 这里应该调用API保存偏好设置
  ElMessage.success('通知设置已保存')
}

/**
 * 组件挂载时初始化
 */
onMounted(() => {
  // 加载用户数据
  // loadUserProfile()
})
</script>

<style lang="scss" scoped>
.profile-container {
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

.profile-card {
  .profile-header {
    text-align: center;
    
    .avatar-section {
      position: relative;
      display: inline-block;
      margin-bottom: 16px;
      
      .user-avatar {
        border: 3px solid var(--el-color-primary-light-8);
      }
      
      .change-avatar-btn {
        position: absolute;
        bottom: -5px;
        right: -5px;
        border-radius: 50%;
        width: 32px;
        height: 32px;
        padding: 0;
      }
    }
    
    .user-basic-info {
      .username {
        font-size: 20px;
        font-weight: 600;
        color: var(--el-text-color-primary);
        margin: 0 0 8px 0;
      }
      
      .user-role {
        margin: 0 0 8px 0;
      }
      
      .user-email {
        color: var(--el-text-color-secondary);
        margin: 0;
      }
    }
  }
  
  .profile-stats {
    display: flex;
    justify-content: space-around;
    
    .stat-item {
      text-align: center;
      
      .stat-value {
        font-size: 16px;
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

.security-card {
  .card-header {
    display: flex;
    align-items: center;
    gap: 8px;
    font-weight: 600;
  }
  
  .security-items {
    .security-item {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 12px 0;
      
      .security-info {
        .security-title {
          font-weight: 500;
          color: var(--el-text-color-primary);
          margin-bottom: 4px;
        }
        
        .security-desc {
          font-size: 12px;
          color: var(--el-text-color-secondary);
          margin: 0;
        }
      }
    }
  }
}

.card-header {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 600;
  
  .edit-btn {
    margin-left: auto;
  }
}

.avatar-upload {
  text-align: center;
  
  .avatar-uploader {
    :deep(.el-upload) {
      border: 1px dashed var(--el-border-color);
      border-radius: 6px;
      cursor: pointer;
      position: relative;
      overflow: hidden;
      transition: var(--el-transition-duration-fast);
      
      &:hover {
        border-color: var(--el-color-primary);
      }
    }
  }
  
  .avatar-uploader-icon {
    font-size: 28px;
    color: #8c939d;
    width: 178px;
    height: 178px;
    line-height: 178px;
    text-align: center;
  }
  
  .avatar-preview {
    width: 178px;
    height: 178px;
    display: block;
  }
  
  .upload-tips {
    margin-top: 16px;
    
    p {
      font-size: 12px;
      color: var(--el-text-color-secondary);
      margin: 4px 0;
    }
  }
}

// 响应式设计
@media (max-width: 1200px) {
  .profile-container {
    .el-col {
      margin-bottom: 20px;
    }
  }
}

@media (max-width: 768px) {
  .profile-container {
    padding: 16px;
    
    .el-col {
      span: 24 !important;
    }
  }
  
  .profile-stats {
    flex-direction: column;
    gap: 16px;
  }
  
  .security-item {
    flex-direction: column !important;
    align-items: flex-start !important;
    gap: 12px;
  }
}
</style>