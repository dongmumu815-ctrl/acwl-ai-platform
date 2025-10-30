<template>
  <div class="user-form">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="header-left">
        <el-button @click="handleBack">
          <el-icon><ArrowLeft /></el-icon>
          返回
        </el-button>
        <div class="header-info">
          <h1 class="page-title">{{ isEdit ? '编辑用户' : '新建用户' }}</h1>
          <p class="page-description">
            {{ isEdit ? '修改用户基本信息和权限设置' : '创建新的系统用户账户' }}
          </p>
        </div>
      </div>
      <div class="header-right">
        <el-button @click="handleCancel">取消</el-button>
        <el-button
          type="primary"
          :loading="saving"
          @click="handleSave"
        >
          {{ isEdit ? '保存' : '创建' }}
        </el-button>
      </div>
    </div>

    <!-- 表单内容 -->
    <div class="form-content">
      <el-row :gutter="24">
        <!-- 左侧表单 -->
        <el-col :span="16">
          <el-card title="基本信息">
            <el-form
              ref="formRef"
              :model="formData"
              :rules="formRules"
              label-width="100px"
              label-position="left"
            >
              <!-- 头像上传 -->
              <el-form-item label="头像">
                <div class="avatar-upload">
                  <el-upload
                    class="avatar-uploader"
                    :show-file-list="false"
                    :before-upload="beforeAvatarUpload"
                    :http-request="handleAvatarUpload"
                  >
                    <el-avatar
                      v-if="formData.avatar"
                      :src="formData.avatar"
                      :size="80"
                      fit="cover"
                    />
                    <div v-else class="avatar-placeholder">
                      <el-icon><Plus /></el-icon>
                      <div>上传头像</div>
                    </div>
                  </el-upload>
                  <div class="avatar-tips">
                    <p>支持 JPG、PNG 格式</p>
                    <p>建议尺寸：200x200 像素</p>
                    <p>文件大小不超过 2MB</p>
                  </div>
                </div>
              </el-form-item>

              <!-- 用户名 -->
              <el-form-item label="用户名" prop="username">
                <el-input
                  v-model="formData.username"
                  placeholder="请输入用户名"
                  :disabled="isEdit"
                  maxlength="50"
                  show-word-limit
                />
                <div class="field-tip">
                  用户名用于登录，创建后不可修改
                </div>
              </el-form-item>

              <!-- 邮箱 -->
              <el-form-item label="邮箱" prop="email">
                <el-input
                  v-model="formData.email"
                  placeholder="请输入邮箱地址"
                  type="email"
                  maxlength="100"
                />
              </el-form-item>

              <!-- 姓名 -->
              <el-form-item label="姓名" prop="full_name">
                <el-input
                  v-model="formData.full_name"
                  placeholder="请输入真实姓名"
                  maxlength="50"
                  show-word-limit
                />
              </el-form-item>

              <!-- 手机号 -->
              <el-form-item label="手机号" prop="phone">
                <el-input
                  v-model="formData.phone"
                  placeholder="请输入手机号码"
                  maxlength="20"
                />
              </el-form-item>

              <!-- 部门 -->
              <el-form-item label="部门" prop="department">
                <el-select
                  v-model="formData.department"
                  placeholder="请选择部门"
                  filterable
                  allow-create
                  style="width: 100%"
                >
                  <el-option
                    v-for="dept in departments"
                    :key="dept"
                    :label="dept"
                    :value="dept"
                  />
                </el-select>
              </el-form-item>

              <!-- 职位 -->
              <el-form-item label="职位" prop="position">
                <el-input
                  v-model="formData.position"
                  placeholder="请输入职位"
                  maxlength="50"
                />
              </el-form-item>

              <!-- 密码设置（仅新建时显示） -->
              <template v-if="!isEdit">
                <el-form-item label="密码" prop="password">
                  <el-input
                    v-model="formData.password"
                    type="password"
                    placeholder="请输入密码"
                    show-password
                    maxlength="50"
                  />
                  <div class="field-tip">
                    密码长度至少8位，包含字母、数字和特殊字符
                  </div>
                </el-form-item>

                <el-form-item label="确认密码" prop="confirm_password">
                  <el-input
                    v-model="formData.confirm_password"
                    type="password"
                    placeholder="请再次输入密码"
                    show-password
                    maxlength="50"
                  />
                </el-form-item>
              </template>

              <!-- 状态设置 -->
              <el-form-item label="账户状态">
                <el-switch
                  v-model="formData.is_active"
                  active-text="启用"
                  inactive-text="禁用"
                />
              </el-form-item>

              <!-- 超级管理员 -->
              <el-form-item label="超级管理员">
                <el-switch
                  v-model="formData.is_superuser"
                  active-text="是"
                  inactive-text="否"
                />
                <div class="field-tip">
                  超级管理员拥有系统所有权限
                </div>
              </el-form-item>
            </el-form>
          </el-card>
        </el-col>

        <!-- 右侧权限设置 -->
        <el-col :span="8">
          <el-card title="权限设置">
            <!-- 角色分配 -->
            <div class="permission-section">
              <h4>角色分配</h4>
              <el-select
                v-model="selectedRoles"
                multiple
                placeholder="请选择角色"
                style="width: 100%"
                @change="handleRoleChange"
              >
                <el-option
                  v-for="role in availableRoles"
                  :key="role.id"
                  :label="role.name"
                  :value="role.id"
                >
                  <div class="role-option">
                    <span class="role-name">{{ role.name }}</span>
                    <span class="role-desc">{{ role.description }}</span>
                  </div>
                </el-option>
              </el-select>
            </div>

            <!-- 权限预览 -->
            <div v-if="effectivePermissions.length" class="permission-section">
              <h4>有效权限</h4>
              <div class="permissions-list">
                <el-tag
                  v-for="permission in effectivePermissions"
                  :key="permission.id"
                  size="small"
                  class="permission-tag"
                >
                  {{ permission.name }}
                </el-tag>
              </div>
            </div>

            <!-- 额外权限 -->
            <div class="permission-section">
              <h4>额外权限</h4>
              <el-select
                v-model="selectedPermissions"
                multiple
                placeholder="选择额外权限"
                style="width: 100%"
                filterable
              >
                <el-option
                  v-for="permission in availablePermissions"
                  :key="permission.id"
                  :label="permission.name"
                  :value="permission.id"
                >
                  <div class="permission-option">
                    <span class="permission-name">{{ permission.name }}</span>
                    <span class="permission-code">{{ permission.code }}</span>
                  </div>
                </el-option>
              </el-select>
              <div class="field-tip">
                额外权限将在角色权限基础上叠加
              </div>
            </div>
          </el-card>

          <!-- 用户偏好设置 -->
          <el-card title="偏好设置" style="margin-top: 16px">
            <el-form label-width="80px">
              <el-form-item label="主题">
                <el-select v-model="formData.preferences.theme" style="width: 100%">
                  <el-option label="浅色" value="light" />
                  <el-option label="深色" value="dark" />
                  <el-option label="自动" value="auto" />
                </el-select>
              </el-form-item>

              <el-form-item label="语言">
                <el-select v-model="formData.preferences.language" style="width: 100%">
                  <el-option label="中文" value="zh-CN" />
                  <el-option label="English" value="en-US" />
                </el-select>
              </el-form-item>

              <el-form-item label="时区">
                <el-select v-model="formData.preferences.timezone" style="width: 100%">
                  <el-option label="北京时间" value="Asia/Shanghai" />
                  <el-option label="UTC" value="UTC" />
                </el-select>
              </el-form-item>

              <el-form-item label="分页大小">
                <el-input-number
                  v-model="formData.preferences.page_size"
                  :min="10"
                  :max="100"
                  :step="10"
                  style="width: 100%"
                />
              </el-form-item>
            </el-form>
          </el-card>
        </el-col>
      </el-row>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import type { FormInstance, FormRules, UploadRequestOptions } from 'element-plus'
import {
  ArrowLeft,
  Plus
} from '@element-plus/icons-vue'
import type {
  User,
  UserRole,
  UserPermission,
  RegisterRequest,
  UserUpdateRequest
} from '@/types/user'
import {
  getUserDetail,
  createUser,
  updateUser,
  getRoles,
  getPermissions,
  uploadAvatar
} from '@/api/user'
import { validateEmail, validatePhone, validatePassword } from '@/utils/validate'

const route = useRoute()
const router = useRouter()

// 响应式数据
const formRef = ref<FormInstance>()
const saving = ref(false)
const isEdit = computed(() => !!route.params.id)
const userId = computed(() => Number(route.params.id))

// 表单数据
const formData = reactive<RegisterRequest & UserUpdateRequest & {
  preferences: {
    theme: 'light' | 'dark' | 'auto'
    language: string
    timezone: string
    page_size: number
  }
}>({
  username: '',
  email: '',
  password: '',
  confirm_password: '',
  full_name: '',
  phone: '',
  department: '',
  position: '',
  avatar: '',
  is_active: true,
  is_superuser: false,
  preferences: {
    theme: 'light',
    language: 'zh-CN',
    timezone: 'Asia/Shanghai',
    page_size: 20
  }
})

// 权限相关数据
const selectedRoles = ref<number[]>([])
const selectedPermissions = ref<number[]>([])
const availableRoles = ref<UserRole[]>([])
const availablePermissions = ref<UserPermission[]>([])

// 部门列表
const departments = ref<string[]>([
  '技术部',
  '产品部',
  '运营部',
  '市场部',
  '人事部',
  '财务部'
])

// 表单验证规则
const formRules: FormRules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 3, max: 50, message: '用户名长度在 3 到 50 个字符', trigger: 'blur' },
    {
      pattern: /^[a-zA-Z0-9_]+$/,
      message: '用户名只能包含字母、数字和下划线',
      trigger: 'blur'
    }
  ],
  email: [
    { required: true, message: '请输入邮箱地址', trigger: 'blur' },
    { validator: validateEmail, trigger: 'blur' }
  ],
  full_name: [
    { required: true, message: '请输入姓名', trigger: 'blur' },
    { min: 2, max: 50, message: '姓名长度在 2 到 50 个字符', trigger: 'blur' }
  ],
  phone: [
    { validator: validatePhone, trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { validator: validatePassword, trigger: 'blur' }
  ],
  confirm_password: [
    { required: true, message: '请确认密码', trigger: 'blur' },
    {
      validator: (rule, value, callback) => {
        if (value !== formData.password) {
          callback(new Error('两次输入的密码不一致'))
        } else {
          callback()
        }
      },
      trigger: 'blur'
    }
  ]
}

// 计算有效权限
const effectivePermissions = computed(() => {
  const rolePermissions = availableRoles.value
    .filter(role => selectedRoles.value.includes(role.id))
    .flatMap(role => role.permissions)
  
  const extraPermissions = availablePermissions.value
    .filter(permission => selectedPermissions.value.includes(permission.id))
  
  // 去重
  const allPermissions = [...rolePermissions, ...extraPermissions]
  const uniquePermissions = allPermissions.filter(
    (permission, index, self) => 
      index === self.findIndex(p => p.id === permission.id)
  )
  
  return uniquePermissions
})

/**
 * 加载用户数据（编辑模式）
 */
const loadUserData = async () => {
  if (!isEdit.value) return
  
  try {
    const response = await getUserDetail(userId.value.toString())
    const user = response.data
    
    // 填充表单数据
    Object.assign(formData, {
      username: user.username,
      email: user.email,
      full_name: user.full_name,
      phone: user.phone,
      department: user.department,
      position: user.position,
      avatar: user.avatar,
      is_active: user.is_active,
      role: user.role || 'user'
    })
  } catch (error) {
    console.error('加载用户数据失败:', error)
    ElMessage.error('加载用户数据失败')
  }
}

/**
 * 加载角色和权限数据
 */
const loadRolesAndPermissions = async () => {
  try {
    const [rolesRes, permissionsRes] = await Promise.all([
      getRoles(),
      getPermissions()
    ])
    
    availableRoles.value = rolesRes.data
    availablePermissions.value = permissionsRes.data
  } catch (error) {
    ElMessage.error('加载权限数据失败')
  }
}

/**
 * 处理角色变化
 */
const handleRoleChange = () => {
  // 角色变化时可以做一些处理，比如自动添加某些权限
}

/**
 * 头像上传前验证
 */
const beforeAvatarUpload = (file: File) => {
  const isImage = file.type.startsWith('image/')
  const isLt2M = file.size / 1024 / 1024 < 2
  
  if (!isImage) {
    ElMessage.error('只能上传图片文件')
    return false
  }
  if (!isLt2M) {
    ElMessage.error('图片大小不能超过 2MB')
    return false
  }
  return true
}

/**
 * 处理头像上传
 */
const handleAvatarUpload = async (options: UploadRequestOptions) => {
  try {
    const formData = new FormData()
    formData.append('file', options.file)
    
    const response = await uploadAvatar(formData)
    formData.avatar = response.data.url
    ElMessage.success('头像上传成功')
  } catch (error) {
    ElMessage.error('头像上传失败')
  }
}

/**
 * 处理保存
 */
const handleSave = async () => {
  if (!formRef.value) return
  
  try {
    const valid = await formRef.value.validate()
    if (!valid) return
    
    saving.value = true
    
    const userData = {
      username: formData.username,
      email: formData.email,
      full_name: formData.full_name,
      phone: formData.phone,
      department: formData.department,
      position: formData.position,
      avatar: formData.avatar,
      is_active: formData.is_active,
      role: formData.role || 'user'
    }
    
    if (isEdit.value) {
      await updateUser(userId.value.toString(), userData)
      ElMessage.success('用户更新成功')
    } else {
      const createData = {
        ...userData,
        password: formData.password
      }
      await createUser(createData)
      ElMessage.success('用户创建成功')
    }
    
    router.push('/users/list')
  } catch (error) {
    console.error('保存用户失败:', error)
    ElMessage.error(isEdit.value ? '用户更新失败' : '用户创建失败')
  } finally {
    saving.value = false
  }
}

/**
 * 处理取消
 */
const handleCancel = async () => {
  try {
    await ElMessageBox.confirm(
      '确定要取消吗？未保存的更改将丢失。',
      '确认取消',
      {
        type: 'warning'
      }
    )
    router.push('/user')
  } catch (error) {
    // 用户取消
  }
}

/**
 * 处理返回
 */
const handleBack = () => {
  router.back()
}

// 组件挂载时加载数据
onMounted(() => {
  loadRolesAndPermissions()
  if (isEdit.value) {
    loadUserData()
  }
})
</script>

<style lang="scss" scoped>
@use "@/styles/variables.scss" as *;

.user-form {
  padding: $spacing-lg;
  background-color: var(--el-bg-color-page);
  min-height: 100vh;

  .page-header {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    margin-bottom: $spacing-lg;

    .header-left {
      display: flex;
      align-items: flex-start;
      gap: $spacing-md;

      .header-info {
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
    }

    .header-right {
      display: flex;
      gap: $spacing-sm;
    }
  }

  .form-content {
    .avatar-upload {
      display: flex;
      gap: $spacing-lg;
      align-items: flex-start;

      .avatar-uploader {
        :deep(.el-upload) {
          border: 1px dashed var(--el-border-color);
          border-radius: 6px;
          cursor: pointer;
          position: relative;
          overflow: hidden;
          transition: var(--el-transition-duration-fast);
          width: 80px;
          height: 80px;
          display: flex;
          align-items: center;
          justify-content: center;

          &:hover {
            border-color: var(--el-color-primary);
          }
        }

        .avatar-placeholder {
          display: flex;
          flex-direction: column;
          align-items: center;
          justify-content: center;
          font-size: $font-size-sm;
          color: var(--el-text-color-regular);
          text-align: center;

          .el-icon {
            font-size: $font-size-lg;
            margin-bottom: $spacing-xs;
          }
        }
      }

      .avatar-tips {
        font-size: $font-size-sm;
        color: var(--el-text-color-secondary);
        line-height: 1.4;

        p {
          margin: 0 0 $spacing-xs 0;
        }
      }
    }

    .field-tip {
      font-size: $font-size-sm;
      color: var(--el-text-color-secondary);
      margin-top: $spacing-xs;
    }

    .permission-section {
      margin-bottom: $spacing-lg;

      h4 {
        margin: 0 0 $spacing-md 0;
        font-size: $font-size-md;
        font-weight: 600;
        color: var(--el-text-color-primary);
      }

      .role-option,
      .permission-option {
        display: flex;
        flex-direction: column;
        gap: $spacing-xs;

        .role-name,
        .permission-name {
          font-weight: 500;
        }

        .role-desc,
        .permission-code {
          font-size: $font-size-sm;
          color: var(--el-text-color-secondary);
        }
      }

      .permissions-list {
        display: flex;
        flex-wrap: wrap;
        gap: $spacing-xs;

        .permission-tag {
          margin: 0;
        }
      }
    }
  }
}

// 响应式设计
@media (max-width: 1200px) {
  .user-form {
    .form-content {
      :deep(.el-col) {
        width: 100%;
        margin-bottom: $spacing-lg;
      }
    }
  }
}

@media (max-width: 768px) {
  .user-form {
    padding: $spacing-md;

    .page-header {
      flex-direction: column;
      gap: $spacing-md;

      .header-left {
        flex-direction: column;
        gap: $spacing-sm;
      }

      .header-right {
        width: 100%;
        justify-content: center;
      }
    }

    .avatar-upload {
      flex-direction: column;
      text-align: center;
    }
  }
}

// 暗色主题适配
@media (prefers-color-scheme: dark) {
  .user-form {
    background-color: var(--el-bg-color-page);
  }
}
</style>