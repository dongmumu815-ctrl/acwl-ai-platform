<template>
  <div>
    <div class="page-card">
      <div class="page-header">
        <h2>管理员管理</h2>
        <el-button type="primary" @click="showAddDialog">
          <el-icon><Plus /></el-icon>
          添加管理员
        </el-button>
      </div>
      
      <div class="page-content">
        <!-- 搜索栏 -->
        <div class="table-toolbar">
          <el-input
            v-model="searchQuery"
            placeholder="搜索管理员用户名或邮箱"
            style="width: 300px;"
            clearable
          >
            <template #prefix>
              <el-icon><Search /></el-icon>
            </template>
          </el-input>
          <el-button @click="loadAdmins">刷新</el-button>
        </div>
        
        <!-- 管理员表格 -->
        <el-table
          :data="filteredAdmins"
          style="width: 100%"
          v-loading="loading"
        >
          <el-table-column prop="id" label="ID" width="80" />
          <el-table-column prop="username" label="用户名" width="150" />
          <el-table-column prop="email" label="邮箱" width="200" />
          <el-table-column prop="real_name" label="姓名" width="150" />
          <el-table-column prop="role" label="角色" width="120">
            <template #default="{ row }">
              <el-tag :type="getRoleTagType(row.role)">{{ getRoleText(row.role) }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="is_active" label="状态" width="100">
            <template #default="{ row }">
              <el-tag :type="row.is_active ? 'success' : 'danger'">
                {{ row.is_active ? '启用' : '禁用' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="last_login_at" label="最后登录" width="180">
            <template #default="{ row }">
              {{ row.last_login_at ? formatDate(row.last_login_at) : '从未登录' }}
            </template>
          </el-table-column>
          <el-table-column prop="created_at" label="创建时间" width="180">
            <template #default="{ row }">
              {{ formatDate(row.created_at) }}
            </template>
          </el-table-column>
          <el-table-column label="操作" width="200" fixed="right">
            <template #default="{ row }">
              <el-button size="small" @click="showEditDialog(row)">编辑</el-button>
              <el-button
                size="small"
                :type="row.is_active ? 'warning' : 'success'"
                @click="toggleAdminStatus(row)"
                :disabled="row.id === currentUserId"
              >
                {{ row.is_active ? '禁用' : '启用' }}
              </el-button>
              <el-button
                size="small"
                type="danger"
                @click="deleteAdmin(row)"
                :disabled="row.id === currentUserId"
              >
                删除
              </el-button>
            </template>
          </el-table-column>
        </el-table>
        
        <!-- 分页 -->
        <div style="margin-top: 20px; text-align: right;">
          <el-pagination
            v-model:current-page="currentPage"
            v-model:page-size="pageSize"
            :page-sizes="[10, 20, 50, 100]"
            :total="total"
            layout="total, sizes, prev, pager, next, jumper"
            @size-change="handleSizeChange"
            @current-change="handleCurrentChange"
          />
        </div>
      </div>
    </div>
    
    <!-- 添加/编辑管理员对话框 -->
    <el-dialog
      v-model="dialogVisible"
      :title="dialogTitle"
      width="600px"
      @close="resetForm"
    >
      <el-form
        ref="adminFormRef"
        :model="adminForm"
        :rules="adminRules"
        label-width="100px"
      >
        <el-form-item label="用户名" prop="username">
          <el-input
            v-model="adminForm.username"
            :disabled="isEdit"
            placeholder="请输入用户名"
          />
        </el-form-item>
        
        <el-form-item label="密码" prop="password" v-if="!isEdit">
          <el-input
            v-model="adminForm.password"
            type="password"
            placeholder="请输入密码"
            show-password
          />
        </el-form-item>
        
        <el-form-item label="确认密码" prop="confirmPassword" v-if="!isEdit">
          <el-input
            v-model="adminForm.confirmPassword"
            type="password"
            placeholder="请再次输入密码"
            show-password
          />
        </el-form-item>
        
        <el-form-item label="邮箱" prop="email">
          <el-input
            v-model="adminForm.email"
            placeholder="请输入邮箱地址"
          />
        </el-form-item>
        
        <el-form-item label="姓名" prop="real_name">
          <el-input
            v-model="adminForm.real_name"
            placeholder="请输入真实姓名"
          />
        </el-form-item>
        
        <el-form-item label="角色" prop="is_superuser">
          <el-select v-model="adminForm.is_superuser" placeholder="请选择角色" style="width: 100%;">
            <el-option label="超级管理员" :value="true" />
            <el-option label="管理员" :value="false" />
          </el-select>
        </el-form-item>
        
        <el-form-item label="状态" prop="is_active">
          <el-switch
            v-model="adminForm.is_active"
            active-text="启用"
            inactive-text="禁用"
          />
        </el-form-item>
        
        <el-form-item label="手机号" prop="phone">
          <el-input
            v-model="adminForm.phone"
            placeholder="请输入手机号码"
          />
        </el-form-item>
        
        <el-form-item label="部门" prop="department">
          <el-input
            v-model="adminForm.department"
            placeholder="请输入部门"
          />
        </el-form-item>
        
        <el-form-item label="描述" prop="description">
          <el-input
            v-model="adminForm.description"
            type="textarea"
            :rows="3"
            placeholder="请输入描述信息"
          />
        </el-form-item>
      </el-form>
      
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="dialogVisible = false">取消</el-button>
          <el-button type="primary" @click="saveAdmin" :loading="saving">
            {{ saving ? '保存中...' : '保存' }}
          </el-button>
        </span>
      </template>
    </el-dialog>
    
    <!-- 修改密码对话框 -->
    <el-dialog
      v-model="passwordDialogVisible"
      title="修改密码"
      width="500px"
      @close="resetPasswordForm"
    >
      <el-form
        ref="passwordFormRef"
        :model="passwordForm"
        :rules="passwordRules"
        label-width="100px"
      >
        <el-form-item label="新密码" prop="password">
          <el-input
            v-model="passwordForm.password"
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
        <span class="dialog-footer">
          <el-button @click="passwordDialogVisible = false">取消</el-button>
          <el-button type="primary" @click="changePassword" :loading="changingPassword">
            {{ changingPassword ? '修改中...' : '修改密码' }}
          </el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useAuthStore } from '@/stores/auth'
import api from '@/utils/api'
import dayjs from 'dayjs'

const authStore = useAuthStore()

// 响应式数据
const loading = ref(false)
const saving = ref(false)
const changingPassword = ref(false)
const admins = ref([])
const searchQuery = ref('')
const currentPage = ref(1)
const pageSize = ref(20)
const total = ref(0)

// 对话框相关
const dialogVisible = ref(false)
const passwordDialogVisible = ref(false)
const isEdit = ref(false)
const adminFormRef = ref()
const passwordFormRef = ref()

// 当前用户ID（防止自己操作自己）
const currentUserId = computed(() => authStore.userInfo?.id)

// 管理员表单
const adminForm = reactive({
  id: null,
  username: '',
  password: '',
  confirmPassword: '',
  email: '',
  real_name: '',
  is_superuser: false,
  is_active: true,
  phone: '',
  department: '',
  description: ''
})

// 密码表单
const passwordForm = reactive({
  id: null,
  password: '',
  confirmPassword: ''
})

// 表单验证规则
const adminRules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 3, max: 20, message: '用户名长度在 3 到 20 个字符', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, max: 20, message: '密码长度在 6 到 20 个字符', trigger: 'blur' }
  ],
  confirmPassword: [
    { required: true, message: '请再次输入密码', trigger: 'blur' },
    {
      validator: (rule, value, callback) => {
        if (value !== adminForm.password) {
          callback(new Error('两次输入的密码不一致'))
        } else {
          callback()
        }
      },
      trigger: 'blur'
    }
  ],
  email: [
    { required: true, message: '请输入邮箱地址', trigger: 'blur' },
    { type: 'email', message: '请输入正确的邮箱地址', trigger: 'blur' }
  ],
  real_name: [
    { required: true, message: '请输入真实姓名', trigger: 'blur' }
  ],
  is_superuser: [
    { required: true, message: '请选择角色', trigger: 'change' }
  ]
}

// 密码验证规则
const passwordRules = {
  password: [
    { required: true, message: '请输入新密码', trigger: 'blur' },
    { min: 6, max: 20, message: '密码长度在 6 到 20 个字符', trigger: 'blur' }
  ],
  confirmPassword: [
    { required: true, message: '请再次输入新密码', trigger: 'blur' },
    {
      validator: (rule, value, callback) => {
        if (value !== passwordForm.password) {
          callback(new Error('两次输入的密码不一致'))
        } else {
          callback()
        }
      },
      trigger: 'blur'
    }
  ]
}

// 计算属性
const dialogTitle = computed(() => isEdit.value ? '编辑管理员' : '添加管理员')

const filteredAdmins = computed(() => {
  if (!searchQuery.value) return admins.value
  
  const query = searchQuery.value.toLowerCase()
  return admins.value.filter(admin => 
    admin.username.toLowerCase().includes(query) ||
    admin.email.toLowerCase().includes(query) ||
    (admin.real_name && admin.real_name.toLowerCase().includes(query))
  )
})

// 获取角色标签类型
const getRoleTagType = (role) => {
  const typeMap = {
    'super_admin': 'danger',
    'admin': 'primary',
    'operator': 'success'
  }
  return typeMap[role] || 'default'
}

// 获取角色文本
const getRoleText = (role) => {
  const textMap = {
    'super_admin': '超级管理员',
    'admin': '管理员',
    'operator': '操作员'
  }
  return textMap[role] || role
}

// 格式化日期
const formatDate = (dateString) => {
  return dayjs(dateString).format('YYYY-MM-DD HH:mm:ss')
}

// 加载管理员列表
const loadAdmins = async () => {
  loading.value = true
  try {
    const response = await api.get('/admin/admins', {
      params: {
        page: currentPage.value,
        size: pageSize.value
      }
    })
    
    admins.value = response.data.data || []
    total.value = response.data.pagination?.total || 0
  } catch (error) {
    console.error('加载管理员列表失败:', error)
    ElMessage.error('加载管理员列表失败')
  } finally {
    loading.value = false
  }
}

// 分页处理
const handleSizeChange = (val) => {
  pageSize.value = val
  currentPage.value = 1
  loadAdmins()
}

const handleCurrentChange = (val) => {
  currentPage.value = val
  loadAdmins()
}

// 显示添加对话框
const showAddDialog = () => {
  isEdit.value = false
  dialogVisible.value = true
}

// 显示编辑对话框
const showEditDialog = (admin) => {
  isEdit.value = true
  Object.assign(adminForm, {
    ...admin,
    password: '',
    confirmPassword: ''
  })
  dialogVisible.value = true
}

// 重置表单
const resetForm = () => {
  if (adminFormRef.value) {
    adminFormRef.value.resetFields()
  }
  Object.assign(adminForm, {
    id: null,
    username: '',
    password: '',
    confirmPassword: '',
    email: '',
    real_name: '',
    is_superuser: false,
    is_active: true,
    phone: '',
    department: '',
    description: ''
  })
}

// 重置密码表单
const resetPasswordForm = () => {
  if (passwordFormRef.value) {
    passwordFormRef.value.resetFields()
  }
  Object.assign(passwordForm, {
    id: null,
    password: '',
    confirmPassword: ''
  })
}

// 保存管理员
const saveAdmin = async () => {
  if (!adminFormRef.value) return
  
  try {
    const valid = await adminFormRef.value.validate()
    if (!valid) return
    
    saving.value = true
    
    const data = { ...adminForm }
    // 将confirmPassword改为confirm_password以匹配后端API
    if (!isEdit.value && data.confirmPassword) {
      data.confirm_password = data.confirmPassword
    }
    delete data.confirmPassword
    
    if (isEdit.value) {
      // 编辑管理员（不包含密码）
      delete data.password
      await api.put(`/admin/admins/${adminForm.id}`, data)
      ElMessage.success('管理员更新成功')
    } else {
      // 添加管理员
      await api.post('/admin/admins', data)
      ElMessage.success('管理员添加成功')
    }
    
    dialogVisible.value = false
    loadAdmins()
  } catch (error) {
    console.error('保存管理员失败:', error)
    ElMessage.error('保存管理员失败')
  } finally {
    saving.value = false
  }
}

// 切换管理员状态
const toggleAdminStatus = async (admin) => {
  try {
    const action = admin.is_active ? '禁用' : '启用'
    await ElMessageBox.confirm(`确定要${action}管理员 "${admin.username}" 吗？`, '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    
    await api.put(`/admin/admins/${admin.id}`, {
      ...admin,
      is_active: !admin.is_active
    })
    
    ElMessage.success(`管理员${action}成功`)
    loadAdmins()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('切换管理员状态失败:', error)
      ElMessage.error('操作失败')
    }
  }
}

// 删除管理员
const deleteAdmin = async (admin) => {
  try {
    await ElMessageBox.confirm(`确定要删除管理员 "${admin.username}" 吗？此操作不可恢复！`, '警告', {
      confirmButtonText: '确定删除',
      cancelButtonText: '取消',
      type: 'error'
    })
    
    await api.delete(`/admin/admins/${admin.id}`)
    ElMessage.success('管理员删除成功')
    loadAdmins()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除管理员失败:', error)
      ElMessage.error('删除管理员失败')
    }
  }
}

// 修改密码
const changePassword = async () => {
  if (!passwordFormRef.value) return
  
  try {
    const valid = await passwordFormRef.value.validate()
    if (!valid) return
    
    changingPassword.value = true
    
    await api.put(`/admin/admins/${passwordForm.id}/password`, {
      password: passwordForm.password
    })
    
    ElMessage.success('密码修改成功')
    passwordDialogVisible.value = false
  } catch (error) {
    console.error('修改密码失败:', error)
    ElMessage.error('修改密码失败')
  } finally {
    changingPassword.value = false
  }
}

// 组件挂载时加载数据
onMounted(() => {
  loadAdmins()
})
</script>

<style scoped>
.page-card {
  background: #fff;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.page-header {
  padding: 20px;
  border-bottom: 1px solid #f0f0f0;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.page-header h2 {
  margin: 0;
  color: #333;
}

.page-content {
  padding: 20px;
}

.table-toolbar {
  margin-bottom: 16px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}
</style>