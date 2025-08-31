<template>
  <div class="users-page">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="header-content">
        <div class="header-left">
          <h1 class="page-title">
            <el-icon><User /></el-icon>
            用户管理
          </h1>
          <p class="page-description">管理系统用户和权限设置</p>
        </div>
        <div class="header-right">
          <el-button type="primary" @click="showCreateDialog">
            <el-icon><Plus /></el-icon>
            添加用户
          </el-button>
          <el-button @click="refreshUsers">
            <el-icon><Refresh /></el-icon>
            刷新
          </el-button>
        </div>
      </div>
    </div>
    
    <!-- 统计卡片 -->
    <div class="stats-cards">
      <el-row :gutter="20">
        <el-col :xs="12" :sm="6">
          <div class="stat-card">
            <div class="stat-icon total">
              <el-icon><User /></el-icon>
            </div>
            <div class="stat-content">
              <div class="stat-value">{{ stats.total }}</div>
              <div class="stat-label">总用户数</div>
            </div>
          </div>
        </el-col>
        
        <el-col :xs="12" :sm="6">
          <div class="stat-card">
            <div class="stat-icon active">
              <el-icon><CircleCheck /></el-icon>
            </div>
            <div class="stat-content">
              <div class="stat-value">{{ stats.active }}</div>
              <div class="stat-label">活跃用户</div>
            </div>
          </div>
        </el-col>
        
        <el-col :xs="12" :sm="6">
          <div class="stat-card">
            <div class="stat-icon admin">
              <el-icon><UserFilled /></el-icon>
            </div>
            <div class="stat-content">
              <div class="stat-value">{{ stats.admin }}</div>
              <div class="stat-label">管理员</div>
            </div>
          </div>
        </el-col>
        
        <el-col :xs="12" :sm="6">
          <div class="stat-card">
            <div class="stat-icon online">
              <el-icon><Connection /></el-icon>
            </div>
            <div class="stat-content">
              <div class="stat-value">{{ stats.online }}</div>
              <div class="stat-label">在线用户</div>
            </div>
          </div>
        </el-col>
      </el-row>
    </div>
    
    <!-- 筛选和搜索 -->
    <div class="filter-section">
      <el-card shadow="never">
        <el-form :model="filters" inline>
          <el-form-item label="搜索">
            <el-input
              v-model="filters.search"
              placeholder="搜索用户名或邮箱"
              clearable
              style="width: 250px"
              @input="handleSearch"
            >
              <template #prefix>
                <el-icon><Search /></el-icon>
              </template>
            </el-input>
          </el-form-item>
          
          <el-form-item label="角色">
            <el-select
              v-model="filters.role"
              placeholder="选择角色"
              clearable
              style="width: 120px"
              @change="handleFilter"
            >
              <el-option label="全部" value="" />
              <el-option label="管理员" value="admin" />
              <el-option label="普通用户" value="user" />
              <el-option label="访客" value="guest" />
            </el-select>
          </el-form-item>
          
          <el-form-item label="状态">
            <el-select
              v-model="filters.status"
              placeholder="选择状态"
              clearable
              style="width: 120px"
              @change="handleFilter"
            >
              <el-option label="全部" value="" />
              <el-option label="活跃" value="active" />
              <el-option label="禁用" value="disabled" />
              <el-option label="待激活" value="pending" />
            </el-select>
          </el-form-item>
          
          <el-form-item label="排序">
            <el-select
              v-model="filters.sortBy"
              style="width: 150px"
              @change="handleSort"
            >
              <el-option label="注册时间" value="created_at" />
              <el-option label="最后登录" value="last_login" />
              <el-option label="用户名" value="username" />
              <el-option label="邮箱" value="email" />
            </el-select>
          </el-form-item>
          
          <el-form-item>
            <el-button @click="resetFilters">
              <el-icon><RefreshLeft /></el-icon>
              重置
            </el-button>
          </el-form-item>
        </el-form>
      </el-card>
    </div>
    
    <!-- 用户列表 -->
    <div class="users-list">
      <el-card shadow="never">
        <template #header>
          <div class="card-header">
            <span>用户列表</span>
            <div class="header-actions">
              <el-radio-group v-model="viewMode" size="small">
                <el-radio-button value="table">
                  <el-icon><List /></el-icon>
                </el-radio-button>
                <el-radio-button value="card">
                  <el-icon><Grid /></el-icon>
                </el-radio-button>
              </el-radio-group>
            </div>
          </div>
        </template>
        
        <!-- 表格视图 -->
        <div v-if="viewMode === 'table'" class="table-view">
          <el-table
            :data="paginatedUsers"
            style="width: 100%"
            @sort-change="handleTableSort"
          >
            <el-table-column type="selection" width="55" />
            
            <el-table-column prop="username" label="用户" sortable>
              <template #default="{ row }">
                <div class="user-cell">
                  <el-avatar
                    :size="40"
                    :src="row.avatar"
                    class="user-avatar"
                  >
                    {{ row.username.charAt(0).toUpperCase() }}
                  </el-avatar>
                  <div class="user-info">
                    <div class="username">{{ row.username }}</div>
                    <div class="email">{{ row.email }}</div>
                  </div>
                  <div class="online-status" v-if="row.is_online">
                    <el-icon class="online-dot"><CircleCheckFilled /></el-icon>
                  </div>
                </div>
              </template>
            </el-table-column>
            
            <el-table-column prop="role" label="角色" width="100">
              <template #default="{ row }">
                <el-tag
                  :type="getRoleType(row.role)"
                  size="small"
                >
                  {{ getRoleText(row.role) }}
                </el-tag>
              </template>
            </el-table-column>
            
            <el-table-column prop="status" label="状态" width="100">
              <template #default="{ row }">
                <el-tag
                  :type="getStatusType(row.status)"
                  size="small"
                >
                  {{ getStatusText(row.status) }}
                </el-tag>
              </template>
            </el-table-column>
            
            <el-table-column prop="department" label="部门" width="120">
              <template #default="{ row }">
                {{ row.department || 'N/A' }}
              </template>
            </el-table-column>
            
            <el-table-column prop="last_login" label="最后登录" width="180" sortable>
              <template #default="{ row }">
                {{ row.last_login ? formatDate(row.last_login) : '从未登录' }}
              </template>
            </el-table-column>
            
            <el-table-column prop="created_at" label="注册时间" width="180" sortable>
              <template #default="{ row }">
                {{ formatDate(row.created_at) }}
              </template>
            </el-table-column>
            
            <el-table-column label="操作" width="200" fixed="right">
              <template #default="{ row }">
                <el-button size="small" @click="viewUser(row)">
                  查看
                </el-button>
                <el-button
                  size="small"
                  type="primary"
                  @click="editUser(row)"
                >
                  编辑
                </el-button>
                <el-dropdown trigger="click">
                  <el-button size="small" text>
                    <el-icon><MoreFilled /></el-icon>
                  </el-button>
                  <template #dropdown>
                    <el-dropdown-menu>
                      <el-dropdown-item @click="resetPassword(row)">
                        <el-icon><Key /></el-icon>
                        重置密码
                      </el-dropdown-item>
                      <el-dropdown-item
                        @click="toggleUserStatus(row)"
                        :class="{ 'danger-item': row.status === 'active' }"
                      >
                        <el-icon><Switch /></el-icon>
                        {{ row.status === 'active' ? '禁用用户' : '启用用户' }}
                      </el-dropdown-item>
                      <el-dropdown-item @click="viewUserActivity(row)">
                        <el-icon><View /></el-icon>
                        查看活动
                      </el-dropdown-item>
                      <el-dropdown-item
                        divided
                        @click="deleteUser(row)"
                        class="danger-item"
                      >
                        <el-icon><Delete /></el-icon>
                        删除用户
                      </el-dropdown-item>
                    </el-dropdown-menu>
                  </template>
                </el-dropdown>
              </template>
            </el-table-column>
          </el-table>
        </div>
        
        <!-- 卡片视图 -->
        <div v-else class="card-view">
          <el-row :gutter="20">
            <el-col
              v-for="user in paginatedUsers"
              :key="user.id"
              :xs="24"
              :sm="12"
              :md="8"
              :lg="6"
            >
              <div class="user-card">
                <div class="user-header">
                  <el-avatar
                    :size="60"
                    :src="user.avatar"
                    class="user-avatar"
                  >
                    {{ user.username.charAt(0).toUpperCase() }}
                  </el-avatar>
                  <div class="online-indicator" v-if="user.is_online">
                    <el-icon class="online-dot"><CircleCheckFilled /></el-icon>
                  </div>
                </div>
                
                <div class="user-content">
                  <h3 class="username">{{ user.username }}</h3>
                  <p class="email">{{ user.email }}</p>
                  
                  <div class="user-tags">
                    <el-tag
                      :type="getRoleType(user.role)"
                      size="small"
                      class="role-tag"
                    >
                      {{ getRoleText(user.role) }}
                    </el-tag>
                    <el-tag
                      :type="getStatusType(user.status)"
                      size="small"
                      class="status-tag"
                    >
                      {{ getStatusText(user.status) }}
                    </el-tag>
                  </div>
                  
                  <div class="user-meta">
                    <div class="meta-item" v-if="user.department">
                      <el-icon><OfficeBuilding /></el-icon>
                      <span>{{ user.department }}</span>
                    </div>
                    <div class="meta-item">
                      <el-icon><Calendar /></el-icon>
                      <span>{{ formatDate(user.created_at) }}</span>
                    </div>
                    <div class="meta-item" v-if="user.last_login">
                      <el-icon><Clock /></el-icon>
                      <span>{{ formatDate(user.last_login) }}</span>
                    </div>
                  </div>
                  
                  <!-- 用户统计 -->
                  <div class="user-stats" v-if="user.stats">
                    <div class="stat-item">
                      <div class="stat-value">{{ user.stats.models || 0 }}</div>
                      <div class="stat-label">模型</div>
                    </div>
                    <div class="stat-item">
                      <div class="stat-value">{{ user.stats.trainings || 0 }}</div>
                      <div class="stat-label">训练</div>
                    </div>
                    <div class="stat-item">
                      <div class="stat-value">{{ user.stats.deployments || 0 }}</div>
                      <div class="stat-label">部署</div>
                    </div>
                  </div>
                </div>
                
                <div class="user-actions">
                  <el-button size="small" @click="viewUser(user)">
                    查看
                  </el-button>
                  <el-button
                    size="small"
                    type="primary"
                    @click="editUser(user)"
                  >
                    编辑
                  </el-button>
                  <el-dropdown trigger="click">
                    <el-button size="small" text>
                      <el-icon><MoreFilled /></el-icon>
                    </el-button>
                    <template #dropdown>
                      <el-dropdown-menu>
                        <el-dropdown-item @click="resetPassword(user)">
                          <el-icon><Key /></el-icon>
                          重置密码
                        </el-dropdown-item>
                        <el-dropdown-item
                          @click="toggleUserStatus(user)"
                          :class="{ 'danger-item': user.status === 'active' }"
                        >
                          <el-icon><Switch /></el-icon>
                          {{ user.status === 'active' ? '禁用用户' : '启用用户' }}
                        </el-dropdown-item>
                        <el-dropdown-item @click="viewUserActivity(user)">
                          <el-icon><View /></el-icon>
                          查看活动
                        </el-dropdown-item>
                        <el-dropdown-item
                          divided
                          @click="deleteUser(user)"
                          class="danger-item"
                        >
                          <el-icon><Delete /></el-icon>
                          删除用户
                        </el-dropdown-item>
                      </el-dropdown-menu>
                    </template>
                  </el-dropdown>
                </div>
              </div>
            </el-col>
          </el-row>
        </div>
        
        <!-- 分页 -->
        <div class="pagination-wrapper">
          <el-pagination
            v-model:current-page="pagination.currentPage"
            v-model:page-size="pagination.pageSize"
            :page-sizes="[10, 20, 50, 100]"
            :total="filteredUsers.length"
            layout="total, sizes, prev, pager, next, jumper"
            @size-change="handleSizeChange"
            @current-change="handleCurrentChange"
          />
        </div>
      </el-card>
    </div>
    
    <!-- 创建/编辑用户对话框 -->
    <el-dialog
      v-model="userDialogVisible"
      :title="isEditing ? '编辑用户' : '添加用户'"
      width="600px"
      :before-close="handleCloseUserDialog"
    >
      <el-form
        ref="userFormRef"
        :model="userForm"
        :rules="userRules"
        label-width="100px"
      >
        <el-form-item label="用户名" prop="username">
          <el-input
            v-model="userForm.username"
            placeholder="请输入用户名"
            :disabled="isEditing"
          />
        </el-form-item>
        
        <el-form-item label="邮箱" prop="email">
          <el-input
            v-model="userForm.email"
            placeholder="请输入邮箱地址"
            type="email"
          />
        </el-form-item>
        
        <el-form-item label="密码" prop="password" v-if="!isEditing">
          <el-input
            v-model="userForm.password"
            placeholder="请输入密码"
            type="password"
            show-password
          />
        </el-form-item>
        
        <el-form-item label="确认密码" prop="confirmPassword" v-if="!isEditing">
          <el-input
            v-model="userForm.confirmPassword"
            placeholder="请确认密码"
            type="password"
            show-password
          />
        </el-form-item>
        
        <el-form-item label="角色" prop="role">
          <el-select
            v-model="userForm.role"
            placeholder="请选择角色"
            style="width: 100%"
          >
            <el-option label="管理员" value="admin" />
            <el-option label="普通用户" value="user" />
            <el-option label="访客" value="guest" />
          </el-select>
        </el-form-item>
        
        <el-form-item label="部门">
          <el-input
            v-model="userForm.department"
            placeholder="请输入部门"
          />
        </el-form-item>
        
        <el-form-item label="手机号">
          <el-input
            v-model="userForm.phone"
            placeholder="请输入手机号"
          />
        </el-form-item>
        
        <el-form-item label="状态" prop="status">
          <el-radio-group v-model="userForm.status">
            <el-radio value="active">活跃</el-radio>
            <el-radio value="disabled">禁用</el-radio>
            <el-radio value="pending">待激活</el-radio>
          </el-radio-group>
        </el-form-item>
        
        <el-form-item label="备注">
          <el-input
            v-model="userForm.remark"
            type="textarea"
            :rows="3"
            placeholder="请输入备注信息"
          />
        </el-form-item>
      </el-form>
      
      <template #footer>
        <div class="dialog-footer">
          <el-button @click="userDialogVisible = false">取消</el-button>
          <el-button
            type="primary"
            @click="submitUser"
            :loading="submitting"
          >
            {{ isEditing ? '更新' : '创建' }}
          </el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox, type FormInstance, type FormRules } from 'element-plus'
import {
  User,
  Plus,
  Refresh,
  CircleCheck,
  UserFilled,
  Connection,
  Search,
  RefreshLeft,
  List,
  Grid,
  CircleCheckFilled,
  MoreFilled,
  Key,
  Switch,
  View,
  Delete,
  OfficeBuilding,
  Calendar,
  Clock
} from '@element-plus/icons-vue'

const router = useRouter()

// 响应式数据
const viewMode = ref('table')
const userDialogVisible = ref(false)
const isEditing = ref(false)
const userFormRef = ref<FormInstance>()
const submitting = ref(false)

// 统计数据
const stats = reactive({
  total: 0,
  active: 0,
  admin: 0,
  online: 0
})

// 筛选条件
const filters = reactive({
  search: '',
  role: '',
  status: '',
  sortBy: 'created_at'
})

// 分页
const pagination = reactive({
  currentPage: 1,
  pageSize: 20
})

// 用户列表
const users = ref<any[]>([])

// 用户表单
const userForm = reactive({
  id: '',
  username: '',
  email: '',
  password: '',
  confirmPassword: '',
  role: 'user',
  department: '',
  phone: '',
  status: 'active',
  remark: ''
})

// 表单验证规则
const userRules: FormRules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 3, max: 20, message: '用户名长度在 3 到 20 个字符', trigger: 'blur' }
  ],
  email: [
    { required: true, message: '请输入邮箱地址', trigger: 'blur' },
    { type: 'email', message: '请输入正确的邮箱地址', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, message: '密码长度不能少于 6 个字符', trigger: 'blur' }
  ],
  confirmPassword: [
    { required: true, message: '请确认密码', trigger: 'blur' },
    {
      validator: (rule, value, callback) => {
        if (value !== userForm.password) {
          callback(new Error('两次输入密码不一致'))
        } else {
          callback()
        }
      },
      trigger: 'blur'
    }
  ],
  role: [
    { required: true, message: '请选择角色', trigger: 'change' }
  ],
  status: [
    { required: true, message: '请选择状态', trigger: 'change' }
  ]
}

// 计算属性
const filteredUsers = computed(() => {
  let result = [...users.value]
  
  // 搜索过滤
  if (filters.search) {
    const search = filters.search.toLowerCase()
    result = result.filter(user => 
      user.username.toLowerCase().includes(search) ||
      user.email.toLowerCase().includes(search)
    )
  }
  
  // 角色过滤
  if (filters.role) {
    result = result.filter(user => user.role === filters.role)
  }
  
  // 状态过滤
  if (filters.status) {
    result = result.filter(user => user.status === filters.status)
  }
  
  // 排序
  result.sort((a, b) => {
    const field = filters.sortBy
    if (field === 'created_at' || field === 'last_login') {
      return new Date(b[field] || 0).getTime() - new Date(a[field] || 0).getTime()
    } else if (field === 'username' || field === 'email') {
      return a[field].localeCompare(b[field])
    }
    return 0
  })
  
  return result
})

const paginatedUsers = computed(() => {
  const start = (pagination.currentPage - 1) * pagination.pageSize
  const end = start + pagination.pageSize
  return filteredUsers.value.slice(start, end)
})

// 方法
const formatDate = (date: string) => {
  return new Date(date).toLocaleString('zh-CN')
}

const getRoleType = (role: string) => {
  const roleMap: Record<string, string> = {
    admin: 'danger',
    user: 'primary',
    guest: 'info'
  }
  return roleMap[role] || 'info'
}

const getRoleText = (role: string) => {
  const roleMap: Record<string, string> = {
    admin: '管理员',
    user: '普通用户',
    guest: '访客'
  }
  return roleMap[role] || role
}

const getStatusType = (status: string) => {
  const statusMap: Record<string, string> = {
    active: 'success',
    disabled: 'danger',
    pending: 'warning'
  }
  return statusMap[status] || 'info'
}

const getStatusText = (status: string) => {
  const statusMap: Record<string, string> = {
    active: '活跃',
    disabled: '禁用',
    pending: '待激活'
  }
  return statusMap[status] || status
}

const handleSearch = () => {
  pagination.currentPage = 1
}

const handleFilter = () => {
  pagination.currentPage = 1
}

const handleSort = () => {
  pagination.currentPage = 1
}

const resetFilters = () => {
  filters.search = ''
  filters.role = ''
  filters.status = ''
  filters.sortBy = 'created_at'
  pagination.currentPage = 1
}

const handleTableSort = ({ prop, order }: any) => {
  if (order) {
    filters.sortBy = prop
  }
}

const handleSizeChange = (size: number) => {
  pagination.pageSize = size
  pagination.currentPage = 1
}

const handleCurrentChange = (page: number) => {
  pagination.currentPage = page
}

const refreshUsers = async () => {
  try {
    // 这里应该调用实际的API
    // const response = await userApi.getUsers()
    // users.value = response.data
    
    // 模拟数据
    users.value = [
      {
        id: '1',
        username: 'admin',
        email: 'admin@acwl.ai',
        role: 'admin',
        status: 'active',
        department: '技术部',
        phone: '13800138000',
        avatar: '',
        is_online: true,
        last_login: '2024-01-21T10:30:00Z',
        created_at: '2024-01-01T00:00:00Z',
        stats: {
          models: 15,
          trainings: 8,
          deployments: 5
        },
        remark: '系统管理员'
      },
      {
        id: '2',
        username: 'john_doe',
        email: 'john@example.com',
        role: 'user',
        status: 'active',
        department: '算法部',
        phone: '13800138001',
        avatar: '',
        is_online: false,
        last_login: '2024-01-20T15:45:00Z',
        created_at: '2024-01-05T10:20:00Z',
        stats: {
          models: 8,
          trainings: 12,
          deployments: 3
        },
        remark: '算法工程师'
      },
      {
        id: '3',
        username: 'jane_smith',
        email: 'jane@example.com',
        role: 'user',
        status: 'active',
        department: '产品部',
        phone: '13800138002',
        avatar: '',
        is_online: true,
        last_login: '2024-01-21T09:15:00Z',
        created_at: '2024-01-08T14:30:00Z',
        stats: {
          models: 3,
          trainings: 5,
          deployments: 2
        },
        remark: '产品经理'
      },
      {
        id: '4',
        username: 'guest_user',
        email: 'guest@example.com',
        role: 'guest',
        status: 'pending',
        department: '',
        phone: '',
        avatar: '',
        is_online: false,
        last_login: null,
        created_at: '2024-01-20T16:45:00Z',
        stats: {
          models: 0,
          trainings: 0,
          deployments: 0
        },
        remark: '访客用户'
      },
      {
        id: '5',
        username: 'disabled_user',
        email: 'disabled@example.com',
        role: 'user',
        status: 'disabled',
        department: '测试部',
        phone: '13800138003',
        avatar: '',
        is_online: false,
        last_login: '2024-01-15T12:00:00Z',
        created_at: '2024-01-10T09:00:00Z',
        stats: {
          models: 2,
          trainings: 1,
          deployments: 0
        },
        remark: '已禁用用户'
      }
    ]
    
    // 更新统计数据
    updateStats()
    
    ElMessage.success('用户列表已刷新')
  } catch (error) {
    console.error('刷新用户列表失败:', error)
    ElMessage.error('刷新失败，请稍后重试')
  }
}

const updateStats = () => {
  stats.total = users.value.length
  stats.active = users.value.filter(u => u.status === 'active').length
  stats.admin = users.value.filter(u => u.role === 'admin').length
  stats.online = users.value.filter(u => u.is_online).length
}

const showCreateDialog = () => {
  isEditing.value = false
  resetUserForm()
  userDialogVisible.value = true
}

const resetUserForm = () => {
  userForm.id = ''
  userForm.username = ''
  userForm.email = ''
  userForm.password = ''
  userForm.confirmPassword = ''
  userForm.role = 'user'
  userForm.department = ''
  userForm.phone = ''
  userForm.status = 'active'
  userForm.remark = ''
}

const handleCloseUserDialog = () => {
  resetUserForm()
  userDialogVisible.value = false
}

const submitUser = async () => {
  if (!userFormRef.value) return
  
  try {
    await userFormRef.value.validate()
    submitting.value = true
    
    if (isEditing.value) {
      // 这里应该调用实际的API更新用户
      // await userApi.updateUser(userForm.id, userForm)
      
      const index = users.value.findIndex(u => u.id === userForm.id)
      if (index > -1) {
        users.value[index] = { ...users.value[index], ...userForm }
      }
      
      ElMessage.success('用户更新成功')
    } else {
      // 这里应该调用实际的API创建用户
      // await userApi.createUser(userForm)
      
      const newUser = {
        ...userForm,
        id: Date.now().toString(),
        avatar: '',
        is_online: false,
        last_login: null,
        created_at: new Date().toISOString(),
        stats: {
          models: 0,
          trainings: 0,
          deployments: 0
        }
      }
      users.value.unshift(newUser)
      
      ElMessage.success('用户创建成功')
    }
    
    updateStats()
    handleCloseUserDialog()
  } catch (error: any) {
    console.error('提交用户信息失败:', error)
    ElMessage.error('操作失败，请稍后重试')
  } finally {
    submitting.value = false
  }
}

const viewUser = (user: any) => {
  router.push(`/users/${user.id}`)
}

const editUser = (user: any) => {
  isEditing.value = true
  Object.assign(userForm, user)
  userDialogVisible.value = true
}

const resetPassword = async (user: any) => {
  try {
    await ElMessageBox.confirm(
      `确定要重置用户 "${user.username}" 的密码吗？`,
      '确认重置密码',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    // 这里应该调用实际的API
    // await userApi.resetPassword(user.id)
    
    ElMessage.success('密码重置成功，新密码已发送到用户邮箱')
  } catch (error: any) {
    if (error !== 'cancel') {
      console.error('重置密码失败:', error)
      ElMessage.error('重置失败，请稍后重试')
    }
  }
}

const toggleUserStatus = async (user: any) => {
  const action = user.status === 'active' ? '禁用' : '启用'
  
  try {
    await ElMessageBox.confirm(
      `确定要${action}用户 "${user.username}" 吗？`,
      `确认${action}`,
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    // 这里应该调用实际的API
    // await userApi.toggleUserStatus(user.id)
    
    user.status = user.status === 'active' ? 'disabled' : 'active'
    updateStats()
    
    ElMessage.success(`用户${action}成功`)
  } catch (error: any) {
    if (error !== 'cancel') {
      console.error(`${action}用户失败:`, error)
      ElMessage.error(`${action}失败，请稍后重试`)
    }
  }
}

const viewUserActivity = (user: any) => {
  router.push(`/users/${user.id}/activity`)
}

const deleteUser = async (user: any) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除用户 "${user.username}" 吗？此操作不可恢复。`,
      '确认删除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    // 这里应该调用实际的API
    // await userApi.deleteUser(user.id)
    
    const index = users.value.findIndex(u => u.id === user.id)
    if (index > -1) {
      users.value.splice(index, 1)
      updateStats()
    }
    
    ElMessage.success('用户删除成功')
  } catch (error: any) {
    if (error !== 'cancel') {
      console.error('删除用户失败:', error)
      ElMessage.error('删除失败，请稍后重试')
    }
  }
}

onMounted(() => {
  refreshUsers()
})
</script>

<style lang="scss" scoped>
.users-page {
  padding: 20px;
  
  .page-header {
    margin-bottom: 20px;
    
    .header-content {
      display: flex;
      justify-content: space-between;
      align-items: flex-start;
      
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
      
      .header-right {
        display: flex;
        gap: 12px;
      }
    }
  }
  
  .stats-cards {
    margin-bottom: 20px;
    
    .stat-card {
      display: flex;
      align-items: center;
      padding: 20px;
      background: white;
      border-radius: 8px;
      box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
      
      .stat-icon {
        width: 48px;
        height: 48px;
        border-radius: 8px;
        display: flex;
        align-items: center;
        justify-content: center;
        margin-right: 16px;
        
        .el-icon {
          font-size: 24px;
          color: white;
        }
        
        &.total {
          background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        }
        
        &.active {
          background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        }
        
        &.admin {
          background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
        }
        
        &.online {
          background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%);
        }
      }
      
      .stat-content {
        .stat-value {
          font-size: 24px;
          font-weight: 600;
          color: var(--el-text-color-primary);
          margin-bottom: 4px;
        }
        
        .stat-label {
          font-size: 14px;
          color: var(--el-text-color-regular);
        }
      }
    }
  }
  
  .filter-section {
    margin-bottom: 20px;
    
    :deep(.el-card__body) {
      padding: 16px 20px;
    }
  }
  
  .users-list {
    .card-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      
      .header-actions {
        display: flex;
        align-items: center;
        gap: 12px;
      }
    }
    
    .table-view {
      .user-cell {
        display: flex;
        align-items: center;
        gap: 12px;
        position: relative;
        
        .user-avatar {
          flex-shrink: 0;
        }
        
        .user-info {
          flex: 1;
          
          .username {
            font-weight: 600;
            color: var(--el-text-color-primary);
            margin-bottom: 2px;
          }
          
          .email {
            font-size: 12px;
            color: var(--el-text-color-secondary);
          }
        }
        
        .online-status {
          position: absolute;
          top: 0;
          right: 0;
          
          .online-dot {
            color: #67c23a;
            font-size: 12px;
          }
        }
      }
    }
    
    .card-view {
      .user-card {
        background: white;
        border: 1px solid var(--el-border-color-light);
        border-radius: 8px;
        padding: 20px;
        transition: all 0.3s ease;
        height: 100%;
        display: flex;
        flex-direction: column;
        position: relative;
        
        &:hover {
          box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
          transform: translateY(-2px);
        }
        
        .user-header {
          display: flex;
          justify-content: center;
          margin-bottom: 16px;
          position: relative;
          
          .user-avatar {
            border: 3px solid var(--el-border-color-light);
          }
          
          .online-indicator {
            position: absolute;
            top: 0;
            right: 0;
            
            .online-dot {
              color: #67c23a;
              font-size: 16px;
            }
          }
        }
        
        .user-content {
          flex: 1;
          text-align: center;
          
          .username {
            font-size: 18px;
            font-weight: 600;
            color: var(--el-text-color-primary);
            margin: 0 0 8px 0;
          }
          
          .email {
            font-size: 14px;
            color: var(--el-text-color-regular);
            margin: 0 0 16px 0;
          }
          
          .user-tags {
            display: flex;
            justify-content: center;
            gap: 8px;
            margin-bottom: 16px;
            
            .role-tag,
            .status-tag {
              font-size: 12px;
            }
          }
          
          .user-meta {
            margin-bottom: 16px;
            
            .meta-item {
              display: flex;
              align-items: center;
              justify-content: center;
              gap: 4px;
              font-size: 12px;
              color: var(--el-text-color-secondary);
              margin-bottom: 6px;
              
              &:last-child {
                margin-bottom: 0;
              }
              
              .el-icon {
                font-size: 14px;
              }
            }
          }
          
          .user-stats {
            display: flex;
            justify-content: space-around;
            margin-bottom: 16px;
            
            .stat-item {
              text-align: center;
              
              .stat-value {
                font-size: 18px;
                font-weight: 600;
                color: var(--el-color-primary);
                margin-bottom: 2px;
              }
              
              .stat-label {
                font-size: 12px;
                color: var(--el-text-color-secondary);
              }
            }
          }
        }
        
        .user-actions {
          display: flex;
          justify-content: space-between;
          align-items: center;
          gap: 8px;
          
          .el-button {
            flex: 1;
            
            &:last-child {
              flex: none;
              width: auto;
            }
          }
        }
      }
    }
    
    .pagination-wrapper {
      display: flex;
      justify-content: center;
      margin-top: 20px;
    }
  }
}

:deep(.el-dropdown-menu__item) {
  &.danger-item {
    color: var(--el-color-danger);
    
    &:hover {
      background-color: var(--el-color-danger-light-9);
      color: var(--el-color-danger);
    }
  }
}

// 响应式设计
@media (max-width: 768px) {
  .users-page {
    padding: 16px;
    
    .page-header {
      .header-content {
        flex-direction: column;
        gap: 16px;
        
        .header-right {
          width: 100%;
          justify-content: flex-end;
        }
      }
    }
    
    .filter-section {
      :deep(.el-form) {
        .el-form-item {
          margin-bottom: 16px;
          
          .el-input,
          .el-select {
            width: 100% !important;
          }
        }
      }
    }
    
    .users-list {
      .card-view {
        .user-card {
          .user-actions {
            flex-direction: column;
            
            .el-button {
              width: 100%;
            }
          }
        }
      }
    }
  }
}

// 暗色主题
.dark {
  .users-page {
    .stats-cards {
      .stat-card {
        background: var(--el-bg-color-page);
        border: 1px solid var(--el-border-color);
      }
    }
    
    .users-list {
      .card-view {
        .user-card {
          background: var(--el-bg-color-page);
          border-color: var(--el-border-color);
        }
      }
    }
  }
}
</style>