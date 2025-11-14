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
            
            <el-table-column label="角色" width="200">
              <template #default="{ row }">
                <template v-for="r in getRoles(row)" :key="r">
                  <el-tag :type="getRoleType(r)" size="small" style="margin-right:4px">{{ getRoleText(r) }}</el-tag>
                </template>
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
                    <template v-if="getRoles(user).length > 0">
                      <el-tag
                        v-for="r in getRoles(user)"
                        :key="r"
                        :type="getRoleType(r)"
                        size="small"
                        class="role-tag"
                      >
                        {{ getRoleText(r) }}
                      </el-tag>
                    </template>
                    <template v-else>
                      <el-tag
                        :type="getRoleType('guest')"
                        size="small"
                        class="role-tag"
                      >
                        {{ getRoleText('guest') }}
                      </el-tag>
                    </template>
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
            :total="filters.status ? filteredUsers.length : totalCount"
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
        
        <el-form-item label="角色" prop="roles">
          <el-select
            v-model="userForm.roles"
            multiple
            filterable
            collapse-tags
            placeholder="请选择角色（可多选）"
            style="width: 100%"
          >
            <el-option
              v-for="opt in roleOptions"
              :key="opt.code"
              :label="opt.name"
              :value="opt.code"
            />
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
import { roleApi } from '@/api/roles'
import { authApi, userApi } from '@/api/auth'

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
// 总记录条数（后端分页返回）
const totalCount = ref(0)

// 用户表单
const userForm = reactive({
  id: '',
  username: '',
  email: '',
  password: '',
  confirmPassword: '',
  roles: ['user'],
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
  roles: [
    {
      validator: (rule, value, callback) => {
        if (!Array.isArray(value) || value.length === 0) {
          callback(new Error('请选择至少一个角色'))
        } else {
          callback()
        }
      },
      trigger: 'change'
    }
  ],
  status: [
    { required: true, message: '请选择状态', trigger: 'change' }
  ]
}

// 计算属性
const filteredUsers = computed(() => {
  // 后端已处理搜索与角色筛选，这里仅进行状态与本地排序处理
  let result = [...users.value]

  if (filters.status) {
    result = result.filter(user => user.status === filters.status)
  }

  // 本地排序（仅对当前页数据进行展示排序）
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
  // 后端分页已生效，此处直接返回过滤后的当前页数据
  return filteredUsers.value
})

// 方法
const formatDate = (date: string) => {
  return new Date(date).toLocaleString('zh-CN')
}

/**
 * 获取用户的角色列表（函数级注释）
 *
 * - 兼容用户对象包含单角色字段 `role` 或多角色数组 `roles`
 * - 当不存在任何角色时返回空数组
 */
const getRoles = (user: any): string[] => {
  if (!user) return []
  if (Array.isArray(user.roles)) return user.roles
  if (typeof user.role === 'string' && user.role) return [user.role]
  return []
}

/**
 * 解析主角色（函数级注释）
 *
 * - 输入为选择的角色代码列表（可能来源于后端不同命名，如 ADMIN）
 * - 优先返回 `admin`，其次返回 `user`
 * - 匹配规则：大小写不敏感；包含关键字 `admin`/`user` 即命中
 */
const resolvePrimaryRole = (codes: string[]): string => {
  const norm = (s: string) => (s || '').toLowerCase()
  const hasAdmin = codes.some(c => norm(c) === 'admin')
  if (hasAdmin) return 'admin'
  const hasUser = codes.some(c => norm(c) === 'user')
  if (hasUser) return 'user'
  return ''
}

/**
 * 角色类型样式映射（函数级注释）
 *
 * - admin 使用高亮 danger
 * - user 使用 primary
 * - 其他自定义角色统一使用 info
 */
const getRoleType = (role: string) => {
  const r = (role || '').toLowerCase()
  if (r === 'admin') return 'danger'
  if (r === 'user') return 'primary'
  return 'info'
}

/**
 * 角色显示文本（函数级注释）
 *
 * - 优先从后端加载的 `roleOptions` 中取名称
 * - 若未命中，回退显示代码本身
 */
const getRoleText = (role: string) => {
  const found = roleOptions.value.find(r => r.code === role)
  return found?.name || role
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

/**
 * 搜索触发（函数级注释）
 * 将页码重置为1并请求后端列表接口
 */
const handleSearch = () => {
  pagination.currentPage = 1
  refreshUsers()
}

/**
 * 过滤触发（函数级注释）
 * 包含角色/状态变更；统一重置页码并请求后端列表接口
 */
const handleFilter = () => {
  pagination.currentPage = 1
  refreshUsers()
}

/**
 * 排序选项变化（函数级注释）
 * 仅影响本地展示排序，同时重置页码并刷新列表
 */
const handleSort = () => {
  pagination.currentPage = 1
  refreshUsers()
}

const resetFilters = () => {
  filters.search = ''
  filters.role = ''
  filters.status = ''
  filters.sortBy = 'created_at'
  pagination.currentPage = 1
  refreshUsers()
}

/**
 * 表格排序变化（函数级注释）
 * 同步排序字段并刷新后端数据（后端不处理排序，主要影响本地展示）
 */
const handleTableSort = ({ prop, order }: any) => {
  if (order) {
    filters.sortBy = prop
  }
  refreshUsers()
}

/**
 * 分页大小变化（函数级注释）
 * 更新每页大小并重新请求后端数据
 */
const handleSizeChange = (size: number) => {
  pagination.pageSize = size
  pagination.currentPage = 1
  refreshUsers()
}

/**
 * 页码变化（函数级注释）
 * 更新当前页并重新请求后端数据
 */
const handleCurrentChange = (page: number) => {
  pagination.currentPage = page
  refreshUsers()
}

/**
 * 刷新用户列表（函数级注释）
 *
 * - 对接后端用户查询接口 `/users/`
 * - 传递分页、搜索与角色筛选参数
 * - 兼容不同响应结构（直接对象或 { data } 包裹）
 * - 更新本地列表与统计数据
 */
const refreshUsers = async () => {
  try {
    const params = {
      page: pagination.currentPage,
      size: pagination.pageSize,
      search: (filters.search?.trim() || undefined),
      role: (filters.role || undefined),
      status: (filters.status || undefined)
    }

    const resp = await userApi.getUsers(params as any)
    const data = (resp && (resp as any).data) ? (resp as any).data : resp

    const items = (data as any)?.items ?? (Array.isArray(data) ? data : [])
    users.value = items
    totalCount.value = (data as any)?.total ?? items.length

    /**
     * 依据服务端角色数据丰富用户的多角色（函数级注释）
     *
     * - 为列表中的每个用户拉取当前角色集合并写入 `roles` 数组
     * - 这样表格与卡片视图即可显示自定义且多选的角色
     */
    try {
      for (const u of users.value) {
        try {
          const rResp = await roleApi.getUserRoles(Number(u.id))
          const rData = (rResp as any)?.data || rResp
          u.roles = Array.isArray(rData) ? rData.map((r: any) => r.code) : []
        } catch (e) {
          console.warn('加载用户角色失败:', e)
        }
      }
    } catch (e) {
      console.warn('批量加载用户角色失败:', e)
    }

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
  stats.admin = users.value.filter(u => getRoles(u).includes('admin')).length
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
  userForm.roles = ['user']
  userForm.department = ''
  userForm.phone = ''
  userForm.status = 'active'
  userForm.remark = ''
}

const handleCloseUserDialog = () => {
  resetUserForm()
  userDialogVisible.value = false
}

/**
 * 提交用户信息（创建/更新）
 *
 * 创建流程：
 * - 调用后端注册接口 `/auth/register` 创建用户
 * - 若选择了 `admin` 或 `user` 主角色，调用 `/users/{id}` 更新角色
 * - 将新用户插入本地列表并更新统计
 *
 * 更新流程：
 * - 本地更新演示（可根据后端需求扩展为实际接口调用）
 */
const submitUser = async () => {
  if (!userFormRef.value) return
  
  try {
    await userFormRef.value.validate()
    submitting.value = true
    
    if (isEditing.value) {
      /**
       * 更新用户信息（函数级注释）
       *
       * - 将角色、邮箱、部门、手机号、状态、备注提交至服务端
       * - 仅允许角色为 `admin` 或 `user`，其余角色不提交
       * - 成功后同步本地列表并刷新统计
       */
      /**
       * 选择主角色（优先 admin，其次 user）
       * 保证多选时也能正确上传角色（函数级注释）
       */
      const selectedRoles = Array.isArray(userForm.roles) ? userForm.roles : []
      const primaryRole = resolvePrimaryRole(selectedRoles)

      const payload: any = {
        email: userForm.email || undefined,
        department: userForm.department || undefined,
        phone: userForm.phone || undefined,
        status: userForm.status || undefined,
        remark: userForm.remark || undefined
      }
      // 仅当选择了允许的主角色时才更新角色字段
      if (primaryRole) {
        payload.role = primaryRole
      }

      const updatedUser = await userApi.updateUser(Number(userForm.id), payload)
      await syncUserRoles(Number(userForm.id), selectedRoles)

      const index = users.value.findIndex(u => String(u.id) === String(userForm.id))
      if (index > -1) {
        const finalRole = (updatedUser as any)?.role ?? (payload.role || '')
        users.value[index] = { ...users.value[index], ...userForm, role: finalRole }
      }

      updateStats()
      ElMessage.success('用户更新成功')
    } else {
      // 调用后端注册接口创建用户
      const registerPayload = {
        username: userForm.username,
        email: userForm.email,
        password: userForm.password,
        // 后端字段为 confirm_password，这里进行映射
        confirm_password: userForm.confirmPassword
      }

      const resp = await authApi.register(registerPayload as any)
      const createdUser = (resp as any)?.user ?? resp

      // 根据选择的主角色更新后端角色（仅支持 admin/user）
      /**
       * 选择主角色（优先 admin，其次 user）
       * 保证多选时也能正确上传角色（函数级注释）
       */
      const selectedRoles = Array.isArray(userForm.roles) ? userForm.roles : []
      const primaryRole = resolvePrimaryRole(selectedRoles)
      let finalRole: string = createdUser?.role || 'user'

      /**
       * 注册后补充用户详细信息（函数级注释）
       * 将角色、部门、手机号、状态、备注一次性更新到服务端
       */
      try {
        const updatePayload: any = {
          department: userForm.department || undefined,
          phone: userForm.phone || undefined,
          status: userForm.status || 'active',
          remark: userForm.remark || undefined
        }
        if (primaryRole && ['admin', 'user'].includes(primaryRole)) {
          updatePayload.role = primaryRole
        }

        const updatedUser = await userApi.updateUser(createdUser.id, updatePayload)
        await syncUserRoles(Number(createdUser.id), selectedRoles)
        finalRole = (updatedUser as any)?.role ?? finalRole
      } catch (e) {
        console.warn('更新用户详细信息失败，保留默认角色与本地显示字段', e)
      }

      // 合并后端返回与表单信息，插入到本地列表
      const newUser = {
        id: String(createdUser.id),
        username: createdUser.username,
        email: createdUser.email,
        role: finalRole,
        roles: selectedRoles,
        status: userForm.status,
        department: userForm.department || '',
        phone: userForm.phone || '',
        avatar: '',
        is_online: false,
        last_login: null,
        created_at: createdUser.created_at || new Date().toISOString(),
        stats: { models: 0, trainings: 0, deployments: 0 },
        remark: userForm.remark || ''
      }

      users.value.unshift(newUser)
      ElMessage.success('用户创建成功')
    }
    
    updateStats()
    handleCloseUserDialog()
  } catch (error: any) {
    console.error('提交用户信息失败:', error)
    const serverMsg = error?.response?.data?.detail || error?.message || '操作失败，请稍后重试'
    ElMessage.error(serverMsg)
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
  // 同步已有用户的角色到多选字段
  userForm.roles = getRoles(user)
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
    
    /**
     * 重置用户密码（函数级注释）
     *
     * - 触发后端忘记密码流程，向该用户邮箱发送重置邮件
     * - 若后端返回错误（例如接口未提供或权限限制），进行友好提示
     */
    try {
      await authApi.forgotPassword(user.email)
      ElMessage.success('已发送密码重置邮件到用户邮箱')
    } catch (e) {
      console.error('重置密码接口调用失败:', e)
      ElMessage.error('重置密码失败，后端未提供重置接口或权限不足')
    }
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
    
    /**
     * 切换用户状态（函数级注释）
     *
     * - 使用更新接口提交新的状态：active/disabled
     * - 成功后同步本地数据并更新统计
     */
    const newStatus = user.status === 'active' ? 'disabled' : 'active'
    await userApi.updateUser(Number(user.id), { status: newStatus } as any)

    user.status = newStatus
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
    
    /**
     * 删除用户（函数级注释）
     *
     * - 调用后端删除接口 `/users/{id}`
     * - 成功后从本地列表移除并更新统计
     */
    await userApi.deleteUser(Number(user.id))
    
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

// 角色选项列表（默认静态，后端加载后覆盖）
const roleOptions = ref<Array<{ code: string; name: string; id?: number }>>([
  { code: 'admin', name: '管理员' },
  { code: 'user', name: '普通用户' },
  { code: 'guest', name: '访客' }
])

/**
 * 加载角色选项（函数级注释）
 * 包含 `code/name/id`，用于后续角色分配接口使用
 */
const loadRoleOptions = async () => {
  try {
    const resp = await roleApi.getRoles({ size: 100 })
    const items = resp?.data?.items || []
    roleOptions.value = items.map((r: any) => ({ code: r.code, name: r.name, id: r.id }))
  } catch (e) {
    console.warn('加载角色列表失败，使用内置默认选项', e)
  }
}

/**
 * 同步用户多角色到服务端（函数级注释）
 *
 * - 根据选择的角色代码计算增删差异
 * - 调用 `/roles/assign-user` 与 `/roles/remove-user` 完成同步
 */
const syncUserRoles = async (userId: number, selectedRoleCodes: string[]) => {
  try {
    // 确保拥有最新角色映射
    await loadRoleOptions()
    const codeToId = new Map(roleOptions.value.map(r => [r.code, r.id]))

    // 获取当前服务端角色列表
    const currentResp = await roleApi.getUserRoles(userId)
    const currentRoles = ((currentResp as any)?.data || currentResp) as Array<any>
    const currentIds = new Set<number>((currentRoles || []).map(r => r.id))

    // 目标角色ID集合
    const targetIds = new Set<number>()
    for (const code of selectedRoleCodes) {
      const id = codeToId.get(code)
      if (id) targetIds.add(id)
    }

    // 计算需要新增与移除的角色
    const toAdd: number[] = []
    const toRemove: number[] = []
    for (const id of targetIds) {
      if (!currentIds.has(id)) toAdd.push(id)
    }
    for (const id of currentIds) {
      if (!targetIds.has(id)) toRemove.push(id)
    }

    // 执行新增与移除
    for (const roleId of toAdd) {
      await roleApi.assignRole({ user_id: userId, role_id: roleId })
    }
    for (const roleId of toRemove) {
      await roleApi.removeRole(userId, roleId)
    }
  } catch (e) {
    console.warn('同步用户角色失败:', e)
  }
}

onMounted(() => {
  refreshUsers()
  loadRoleOptions()
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