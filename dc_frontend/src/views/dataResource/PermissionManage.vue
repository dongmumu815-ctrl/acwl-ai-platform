<template>
  <div class="permission-manage-container">
    <!-- 页面标题 -->
    <div class="page-header">
      <h1 class="page-title">
        <el-icon><Lock /></el-icon>
        权限管理
      </h1>
      <p class="page-description">管理数据资源的访问权限和用户授权</p>
    </div>

    <!-- 操作栏 -->
    <div class="action-bar">
      <div class="left-actions">
        <el-button type="primary" @click="showCreateDialog">
          <el-icon><Plus /></el-icon>
          新建权限
        </el-button>
        <el-button @click="batchRevoke" :disabled="selectedPermissions.length === 0">
          <el-icon><Remove /></el-icon>
          批量撤销
        </el-button>
        <el-button @click="exportPermissions">
          <el-icon><Download /></el-icon>
          导出权限
        </el-button>
      </div>
      
      <div class="right-actions">
        <el-select
          v-model="filterType"
          placeholder="权限类型"
          style="width: 120px"
          clearable
          @change="handleFilter"
        >
          <el-option label="读取" value="read" />
          <el-option label="写入" value="write" />
          <el-option label="删除" value="delete" />
          <el-option label="管理" value="admin" />
        </el-select>
        
        <el-select
          v-model="filterStatus"
          placeholder="状态筛选"
          style="width: 120px"
          clearable
          @change="handleFilter"
        >
          <el-option label="有效" value="active" />
          <el-option label="已撤销" value="revoked" />
          <el-option label="已过期" value="expired" />
        </el-select>
        
        <el-input
          v-model="searchKeyword"
          placeholder="搜索用户或资源"
          style="width: 250px"
          clearable
          @input="handleSearch"
        >
          <template #prefix>
            <el-icon><Search /></el-icon>
          </template>
        </el-input>
        
        <el-button @click="refreshPermissions">
          <el-icon><Refresh /></el-icon>
          刷新
        </el-button>
      </div>
    </div>

    <!-- 权限统计 -->
    <div class="stats-section">
      <el-row :gutter="20">
        <el-col :span="6">
          <el-card class="stats-card">
            <div class="stats-content">
              <div class="stats-icon">
                <el-icon color="#409EFF"><Lock /></el-icon>
              </div>
              <div class="stats-info">
                <div class="stats-number">{{ totalPermissions }}</div>
                <div class="stats-label">总权限数</div>
              </div>
            </div>
          </el-card>
        </el-col>
        <el-col :span="6">
          <el-card class="stats-card">
            <div class="stats-content">
              <div class="stats-icon">
                <el-icon color="#67C23A"><CircleCheck /></el-icon>
              </div>
              <div class="stats-info">
                <div class="stats-number">{{ activePermissions }}</div>
                <div class="stats-label">有效权限</div>
              </div>
            </div>
          </el-card>
        </el-col>
        <el-col :span="6">
          <el-card class="stats-card">
            <div class="stats-content">
              <div class="stats-icon">
                <el-icon color="#E6A23C"><Warning /></el-icon>
              </div>
              <div class="stats-info">
                <div class="stats-number">{{ expiredPermissions }}</div>
                <div class="stats-label">已过期</div>
              </div>
            </div>
          </el-card>
        </el-col>
        <el-col :span="6">
          <el-card class="stats-card">
            <div class="stats-content">
              <div class="stats-icon">
                <el-icon color="#F56C6C"><CircleClose /></el-icon>
              </div>
              <div class="stats-info">
                <div class="stats-number">{{ revokedPermissions }}</div>
                <div class="stats-label">已撤销</div>
              </div>
            </div>
          </el-card>
        </el-col>
      </el-row>
    </div>

    <!-- 权限列表 -->
    <div class="permission-list-section">
      <el-card>
        <template #header>
          <div class="card-header">
            <span>权限列表</span>
            <div class="header-actions">
              <el-button size="small" @click="toggleExpandAll">
                <el-icon><Expand /></el-icon>
                {{ expandAll ? '收起全部' : '展开全部' }}
              </el-button>
            </div>
          </div>
        </template>
        
        <el-table
          :data="filteredPermissions"
          stripe
          border
          style="width: 100%"
          @selection-change="handleSelectionChange"
          v-loading="loading"
          :expand-row-keys="expandedRows"
          row-key="id"
        >
          <el-table-column type="selection" width="55" />
          <el-table-column type="expand" width="50">
            <template #default="{ row }">
              <div class="expand-content">
                <div class="permission-details">
                  <h4>权限详情</h4>
                  <el-descriptions :column="2" border>
                    <el-descriptions-item label="权限ID">{{ row.id }}</el-descriptions-item>
                    <el-descriptions-item label="创建时间">{{ formatDate(row.createdAt) }}</el-descriptions-item>
                    <el-descriptions-item label="授权人">{{ row.grantedBy }}</el-descriptions-item>
                    <el-descriptions-item label="最后访问">{{ formatDate(row.lastAccess) }}</el-descriptions-item>
                    <el-descriptions-item label="访问次数">{{ row.accessCount }}</el-descriptions-item>
                    <el-descriptions-item label="权限来源">{{ getSourceLabel(row.source) }}</el-descriptions-item>
                  </el-descriptions>
                  
                  <div v-if="row.conditions && row.conditions.length > 0" class="permission-conditions">
                    <h5>访问条件</h5>
                    <el-tag
                      v-for="condition in row.conditions"
                      :key="condition"
                      type="info"
                      size="small"
                      style="margin-right: 8px; margin-bottom: 4px;"
                    >
                      {{ condition }}
                    </el-tag>
                  </div>
                  
                  <div v-if="row.notes" class="permission-notes">
                    <h5>备注</h5>
                    <p>{{ row.notes }}</p>
                  </div>
                </div>
              </div>
            </template>
          </el-table-column>
          
          <el-table-column prop="userName" label="用户" min-width="120">
            <template #default="{ row }">
              <div class="user-cell">
                <el-avatar :size="24" :src="row.userAvatar">
                  {{ row.userName.charAt(0) }}
                </el-avatar>
                <span class="user-name">{{ row.userName }}</span>
              </div>
            </template>
          </el-table-column>
          
          <el-table-column prop="resourceName" label="资源" min-width="200" show-overflow-tooltip>
            <template #default="{ row }">
              <div class="resource-cell">
                <el-icon class="resource-icon">
                  <component :is="getResourceIcon(row.resourceType)" />
                </el-icon>
                <span>{{ row.resourceName }}</span>
              </div>
            </template>
          </el-table-column>
          
          <el-table-column prop="permissionType" label="权限类型" width="100">
            <template #default="{ row }">
              <el-tag :type="getPermissionTypeColor(row.permissionType)" size="small">
                {{ getPermissionTypeLabel(row.permissionType) }}
              </el-tag>
            </template>
          </el-table-column>
          
          <el-table-column prop="status" label="状态" width="80">
            <template #default="{ row }">
              <el-tag :type="getStatusColor(row.status)" size="small">
                {{ getStatusLabel(row.status) }}
              </el-tag>
            </template>
          </el-table-column>
          
          <el-table-column prop="expiresAt" label="过期时间" width="180">
            <template #default="{ row }">
              <span :class="{ 'expired-time': isExpired(row.expiresAt) }">
                {{ row.expiresAt ? formatDate(row.expiresAt) : '永久' }}
              </span>
            </template>
          </el-table-column>
          
          <el-table-column prop="grantedAt" label="授权时间" width="180">
            <template #default="{ row }">
              {{ formatDate(row.grantedAt) }}
            </template>
          </el-table-column>
          
          <el-table-column label="操作" width="200" fixed="right">
            <template #default="{ row }">
              <el-button
                size="small"
                type="primary"
                link
                @click="showEditDialog(row)"
                :disabled="row.status === 'revoked'"
              >
                <el-icon><Edit /></el-icon>
                编辑
              </el-button>
              <el-button
                size="small"
                type="warning"
                link
                @click="revokePermission(row)"
                :disabled="row.status === 'revoked'"
              >
                <el-icon><Remove /></el-icon>
                撤销
              </el-button>
              <el-button
                size="small"
                type="info"
                link
                @click="viewAccessLog(row)"
              >
                <el-icon><View /></el-icon>
                日志
              </el-button>
            </template>
          </el-table-column>
        </el-table>
        
        <!-- 分页 -->
        <div class="pagination-wrapper">
          <el-pagination
            v-model:current-page="currentPage"
            v-model:page-size="pageSize"
            :page-sizes="[10, 20, 50, 100]"
            :total="totalCount"
            layout="total, sizes, prev, pager, next, jumper"
            @size-change="handleSizeChange"
            @current-change="handleCurrentChange"
          />
        </div>
      </el-card>
    </div>

    <!-- 创建/编辑权限对话框 -->
    <el-dialog
      v-model="permissionDialogVisible"
      :title="isEditMode ? '编辑权限' : '新建权限'"
      width="600px"
      @close="resetPermissionForm"
    >
      <el-form
        ref="permissionFormRef"
        :model="permissionForm"
        :rules="permissionRules"
        label-width="100px"
      >
        <el-form-item label="用户" prop="userId">
          <el-select
            v-model="permissionForm.userId"
            placeholder="请选择用户"
            style="width: 100%"
            filterable
            remote
            :remote-method="searchUsers"
            :loading="userLoading"
          >
            <el-option
              v-for="user in users"
              :key="user.id"
              :label="user.name"
              :value="user.id"
            >
              <div class="user-option">
                <el-avatar :size="20" :src="user.avatar">
                  {{ user.name.charAt(0) }}
                </el-avatar>
                <span>{{ user.name }}</span>
                <span class="user-email">{{ user.email }}</span>
              </div>
            </el-option>
          </el-select>
        </el-form-item>
        
        <el-form-item label="资源" prop="resourceId">
          <el-select
            v-model="permissionForm.resourceId"
            placeholder="请选择资源"
            style="width: 100%"
            filterable
            remote
            :remote-method="searchResources"
            :loading="resourceLoading"
          >
            <el-option
              v-for="resource in resources"
              :key="resource.id"
              :label="resource.name"
              :value="resource.id"
            >
              <div class="resource-option">
                <el-icon class="resource-icon">
                  <component :is="getResourceIcon(resource.type)" />
                </el-icon>
                <span>{{ resource.name }}</span>
                <el-tag type="info" size="small">{{ resource.category }}</el-tag>
              </div>
            </el-option>
          </el-select>
        </el-form-item>
        
        <el-form-item label="权限类型" prop="permissionType">
          <el-select
            v-model="permissionForm.permissionType"
            placeholder="请选择权限类型"
            style="width: 100%"
          >
            <el-option label="读取" value="read" />
            <el-option label="写入" value="write" />
            <el-option label="删除" value="delete" />
            <el-option label="管理" value="admin" />
          </el-select>
        </el-form-item>
        
        <el-form-item label="过期时间" prop="expiresAt">
          <el-radio-group v-model="permissionForm.expireType" @change="handleExpireTypeChange">
            <el-radio value="never">永不过期</el-radio>
            <el-radio value="custom">自定义时间</el-radio>
          </el-radio-group>
          
          <el-date-picker
            v-if="permissionForm.expireType === 'custom'"
            v-model="permissionForm.expiresAt"
            type="datetime"
            placeholder="选择过期时间"
            style="width: 100%; margin-top: 8px;"
            :disabled-date="disabledDate"
          />
        </el-form-item>
        
        <el-form-item label="访问条件">
          <el-checkbox-group v-model="permissionForm.conditions">
            <el-checkbox value="ip_limit">IP限制</el-checkbox>
            <el-checkbox value="time_limit">时间限制</el-checkbox>
            <el-checkbox value="device_limit">设备限制</el-checkbox>
            <el-checkbox value="location_limit">地理位置限制</el-checkbox>
          </el-checkbox-group>
        </el-form-item>
        
        <el-form-item label="备注">
          <el-input
            v-model="permissionForm.notes"
            type="textarea"
            :rows="3"
            placeholder="请输入备注信息"
            maxlength="200"
            show-word-limit
          />
        </el-form-item>
      </el-form>
      
      <template #footer>
        <div class="dialog-footer">
          <el-button @click="permissionDialogVisible = false">取消</el-button>
          <el-button type="primary" @click="submitPermissionForm" :loading="submitting">
            {{ isEditMode ? '更新' : '创建' }}
          </el-button>
        </div>
      </template>
    </el-dialog>

    <!-- 访问日志对话框 -->
    <el-dialog
      v-model="logDialogVisible"
      title="访问日志"
      width="900px"
    >
      <div class="log-content" v-if="currentPermission">
        <div class="log-header">
          <div class="permission-info">
            <span class="user-name">{{ currentPermission.userName }}</span>
            <el-icon><ArrowRight /></el-icon>
            <span class="resource-name">{{ currentPermission.resourceName }}</span>
            <el-tag :type="getPermissionTypeColor(currentPermission.permissionType)" size="small">
              {{ getPermissionTypeLabel(currentPermission.permissionType) }}
            </el-tag>
          </div>
          <div class="log-stats">
            <span>总访问次数: {{ currentPermission.accessCount }}</span>
          </div>
        </div>
        
        <el-table
          :data="accessLogs"
          stripe
          style="width: 100%"
          max-height="400"
        >
          <el-table-column prop="accessTime" label="访问时间" width="180">
            <template #default="{ row }">
              {{ formatDate(row.accessTime) }}
            </template>
          </el-table-column>
          <el-table-column prop="action" label="操作" width="100">
            <template #default="{ row }">
              <el-tag :type="getActionColor(row.action)" size="small">
                {{ getActionLabel(row.action) }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="ipAddress" label="IP地址" width="120" />
          <el-table-column prop="userAgent" label="用户代理" min-width="200" show-overflow-tooltip />
          <el-table-column prop="result" label="结果" width="80">
            <template #default="{ row }">
              <el-tag :type="row.result === 'success' ? 'success' : 'danger'" size="small">
                {{ row.result === 'success' ? '成功' : '失败' }}
              </el-tag>
            </template>
          </el-table-column>
        </el-table>
      </div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useRouter } from 'vue-router'
import {
  Coin,
  Document,
  Connection,
  Folder
} from '@element-plus/icons-vue'

// 路由
const router = useRouter()

// 响应式数据
const permissionFormRef = ref()
const loading = ref(false)
const submitting = ref(false)
const userLoading = ref(false)
const resourceLoading = ref(false)
const permissionDialogVisible = ref(false)
const logDialogVisible = ref(false)
const isEditMode = ref(false)
const expandAll = ref(false)
const expandedRows = ref([])
const searchKeyword = ref('')
const filterType = ref('')
const filterStatus = ref('')
const currentPage = ref(1)
const pageSize = ref(20)
const totalCount = ref(0)
const selectedPermissions = ref([])
const currentPermission = ref(null)

// 权限表单
const permissionForm = reactive({
  id: '',
  userId: '',
  resourceId: '',
  permissionType: '',
  expireType: 'never',
  expiresAt: null,
  conditions: [],
  notes: ''
})

// 表单验证规则
const permissionRules = {
  userId: [
    { required: true, message: '请选择用户', trigger: 'change' }
  ],
  resourceId: [
    { required: true, message: '请选择资源', trigger: 'change' }
  ],
  permissionType: [
    { required: true, message: '请选择权限类型', trigger: 'change' }
  ]
}

// 用户数据
const users = ref([
  {
    id: 1,
    name: '张三',
    email: 'zhangsan@example.com',
    avatar: ''
  },
  {
    id: 2,
    name: '李四',
    email: 'lisi@example.com',
    avatar: ''
  },
  {
    id: 3,
    name: '王五',
    email: 'wangwu@example.com',
    avatar: ''
  }
])

// 资源数据
const resources = ref([
  {
    id: 1,
    name: '用户数据库',
    type: 'database',
    category: '数据库'
  },
  {
    id: 2,
    name: '订单API',
    type: 'api',
    category: 'API接口'
  },
  {
    id: 3,
    name: '日志文件',
    type: 'file',
    category: '文件'
  }
])

// 权限数据
const permissions = ref([
  {
    id: 1,
    userName: '张三',
    userAvatar: '',
    resourceName: '用户数据库',
    resourceType: 'database',
    permissionType: 'read',
    status: 'active',
    grantedAt: '2024-01-15 10:30:00',
    expiresAt: '2024-12-31 23:59:59',
    grantedBy: '管理员',
    lastAccess: '2024-01-20 14:30:00',
    accessCount: 156,
    source: 'manual',
    conditions: ['IP限制', '时间限制'],
    notes: '用于数据分析'
  },
  {
    id: 2,
    userName: '李四',
    userAvatar: '',
    resourceName: '订单API',
    resourceType: 'api',
    permissionType: 'write',
    status: 'active',
    grantedAt: '2024-01-15 11:00:00',
    expiresAt: null,
    grantedBy: '系统管理员',
    lastAccess: '2024-01-20 15:45:00',
    accessCount: 89,
    source: 'auto',
    conditions: [],
    notes: ''
  },
  {
    id: 3,
    userName: '王五',
    userAvatar: '',
    resourceName: '日志文件',
    resourceType: 'file',
    permissionType: 'read',
    status: 'expired',
    grantedAt: '2024-01-10 09:00:00',
    expiresAt: '2024-01-20 09:00:00',
    grantedBy: '部门主管',
    lastAccess: '2024-01-19 16:20:00',
    accessCount: 23,
    source: 'manual',
    conditions: ['设备限制'],
    notes: '临时访问权限'
  },
  {
    id: 4,
    userName: '张三',
    userAvatar: '',
    resourceName: '配置文件',
    resourceType: 'file',
    permissionType: 'admin',
    status: 'revoked',
    grantedAt: '2024-01-12 14:00:00',
    expiresAt: null,
    grantedBy: '系统管理员',
    lastAccess: '2024-01-18 10:15:00',
    accessCount: 45,
    source: 'manual',
    conditions: [],
    notes: '权限已被撤销'
  }
])

// 访问日志数据
const accessLogs = ref([])

/**
 * 计算属性
 */
const totalPermissions = computed(() => permissions.value.length)
const activePermissions = computed(() => permissions.value.filter(p => p.status === 'active').length)
const expiredPermissions = computed(() => permissions.value.filter(p => p.status === 'expired').length)
const revokedPermissions = computed(() => permissions.value.filter(p => p.status === 'revoked').length)

const filteredPermissions = computed(() => {
  let result = permissions.value
  
  // 权限类型筛选
  if (filterType.value) {
    result = result.filter(p => p.permissionType === filterType.value)
  }
  
  // 状态筛选
  if (filterStatus.value) {
    result = result.filter(p => p.status === filterStatus.value)
  }
  
  // 关键词搜索
  if (searchKeyword.value) {
    const keyword = searchKeyword.value.toLowerCase()
    result = result.filter(p => 
      p.userName.toLowerCase().includes(keyword) ||
      p.resourceName.toLowerCase().includes(keyword)
    )
  }
  
  totalCount.value = result.length
  
  // 分页
  const start = (currentPage.value - 1) * pageSize.value
  const end = start + pageSize.value
  return result.slice(start, end)
})

/**
 * 获取权限类型标签
 */
const getPermissionTypeLabel = (type: string) => {
  const typeMap: Record<string, string> = {
    read: '读取',
    write: '写入',
    delete: '删除',
    admin: '管理'
  }
  return typeMap[type] || type
}

/**
 * 获取权限类型颜色
 */
const getPermissionTypeColor = (type: string) => {
  const colorMap: Record<string, string> = {
    read: 'info',
    write: 'warning',
    delete: 'danger',
    admin: 'success'
  }
  return colorMap[type] || 'info'
}

/**
 * 获取状态标签
 */
const getStatusLabel = (status: string) => {
  const statusMap: Record<string, string> = {
    active: '有效',
    expired: '已过期',
    revoked: '已撤销'
  }
  return statusMap[status] || status
}

/**
 * 获取状态颜色
 */
const getStatusColor = (status: string) => {
  const colorMap: Record<string, string> = {
    active: 'success',
    expired: 'warning',
    revoked: 'danger'
  }
  return colorMap[status] || 'info'
}

/**
 * 获取来源标签
 */
const getSourceLabel = (source: string) => {
  const sourceMap: Record<string, string> = {
    manual: '手动授权',
    auto: '自动授权',
    inherit: '继承权限'
  }
  return sourceMap[source] || source
}

/**
 * 获取资源图标
 */
const getResourceIcon = (type: string) => {
  const iconMap: Record<string, any> = {
    database: Coin,
    api: Connection,
    file: Document,
    folder: Folder
  }
  return iconMap[type] || Document
}

/**
 * 获取操作标签
 */
const getActionLabel = (action: string) => {
  const actionMap: Record<string, string> = {
    read: '读取',
    write: '写入',
    delete: '删除',
    query: '查询',
    download: '下载'
  }
  return actionMap[action] || action
}

/**
 * 获取操作颜色
 */
const getActionColor = (action: string) => {
  const colorMap: Record<string, string> = {
    read: 'info',
    write: 'warning',
    delete: 'danger',
    query: 'primary',
    download: 'success'
  }
  return colorMap[action] || 'info'
}

/**
 * 检查是否过期
 */
const isExpired = (expiresAt: string) => {
  if (!expiresAt) return false
  return new Date(expiresAt) < new Date()
}

/**
 * 格式化日期
 */
const formatDate = (dateStr: string) => {
  if (!dateStr) return '-'
  return new Date(dateStr).toLocaleString('zh-CN')
}

/**
 * 禁用过去的日期
 */
const disabledDate = (time: Date) => {
  return time.getTime() < Date.now()
}

/**
 * 切换展开全部
 */
const toggleExpandAll = () => {
  expandAll.value = !expandAll.value
  if (expandAll.value) {
    expandedRows.value = filteredPermissions.value.map(p => p.id)
  } else {
    expandedRows.value = []
  }
}

/**
 * 处理筛选
 */
const handleFilter = () => {
  currentPage.value = 1
}

/**
 * 处理搜索
 */
const handleSearch = () => {
  currentPage.value = 1
}

/**
 * 刷新权限
 */
const refreshPermissions = () => {
  loading.value = true
  // 模拟刷新
  setTimeout(() => {
    loading.value = false
    ElMessage.success('权限数据已刷新')
  }, 1000)
}

/**
 * 处理选择变化
 */
const handleSelectionChange = (selection: any[]) => {
  selectedPermissions.value = selection
}

/**
 * 处理分页大小变化
 */
const handleSizeChange = (size: number) => {
  pageSize.value = size
  currentPage.value = 1
}

/**
 * 处理当前页变化
 */
const handleCurrentChange = (page: number) => {
  currentPage.value = page
}

/**
 * 搜索用户
 */
const searchUsers = (query: string) => {
  if (query) {
    userLoading.value = true
    // 模拟搜索
    setTimeout(() => {
      userLoading.value = false
    }, 500)
  }
}

/**
 * 搜索资源
 */
const searchResources = (query: string) => {
  if (query) {
    resourceLoading.value = true
    // 模拟搜索
    setTimeout(() => {
      resourceLoading.value = false
    }, 500)
  }
}

/**
 * 显示创建对话框
 */
const showCreateDialog = () => {
  isEditMode.value = false
  resetPermissionForm()
  permissionDialogVisible.value = true
}

/**
 * 显示编辑对话框
 */
const showEditDialog = (permission: any) => {
  isEditMode.value = true
  
  Object.assign(permissionForm, {
    id: permission.id,
    userId: permission.userId,
    resourceId: permission.resourceId,
    permissionType: permission.permissionType,
    expireType: permission.expiresAt ? 'custom' : 'never',
    expiresAt: permission.expiresAt ? new Date(permission.expiresAt) : null,
    conditions: permission.conditions || [],
    notes: permission.notes || ''
  })
  
  permissionDialogVisible.value = true
}

/**
 * 重置表单
 */
const resetPermissionForm = () => {
  Object.assign(permissionForm, {
    id: '',
    userId: '',
    resourceId: '',
    permissionType: '',
    expireType: 'never',
    expiresAt: null,
    conditions: [],
    notes: ''
  })
  
  permissionFormRef.value?.clearValidate()
}

/**
 * 处理过期类型变化
 */
const handleExpireTypeChange = (value: string) => {
  if (value === 'never') {
    permissionForm.expiresAt = null
  }
}

/**
 * 提交表单
 */
const submitPermissionForm = () => {
  permissionFormRef.value?.validate((valid: boolean) => {
    if (!valid) return
    
    submitting.value = true
    
    // 模拟提交
    setTimeout(() => {
      if (isEditMode.value) {
        ElMessage.success('权限更新成功')
      } else {
        ElMessage.success('权限创建成功')
      }
      
      permissionDialogVisible.value = false
      submitting.value = false
      
      // 这里应该刷新权限数据
      refreshPermissions()
    }, 1000)
  })
}

/**
 * 撤销权限
 */
const revokePermission = (permission: any) => {
  ElMessageBox.confirm(
    `确定要撤销用户 "${permission.userName}" 对资源 "${permission.resourceName}" 的权限吗？`,
    '确认撤销',
    {
      confirmButtonText: '确定撤销',
      cancelButtonText: '取消',
      type: 'warning'
    }
  ).then(() => {
    ElMessage.success('权限已撤销')
    // 这里应该刷新权限数据
    refreshPermissions()
  }).catch(() => {
    // 取消撤销
  })
}

/**
 * 批量撤销
 */
const batchRevoke = () => {
  const activePermissions = selectedPermissions.value.filter(p => p.status === 'active')
  
  if (activePermissions.length === 0) {
    ElMessage.warning('所选权限都不是有效状态，无法撤销')
    return
  }
  
  ElMessageBox.confirm(
    `确定要撤销选中的 ${activePermissions.length} 个权限吗？`,
    '确认批量撤销',
    {
      confirmButtonText: '确定撤销',
      cancelButtonText: '取消',
      type: 'warning'
    }
  ).then(() => {
    ElMessage.success(`已撤销 ${activePermissions.length} 个权限`)
    selectedPermissions.value = []
    // 这里应该刷新权限数据
    refreshPermissions()
  }).catch(() => {
    // 取消撤销
  })
}

/**
 * 导出权限
 */
const exportPermissions = () => {
  ElMessage.success('导出功能开发中...')
}

/**
 * 查看访问日志
 */
const viewAccessLog = (permission: any) => {
  currentPermission.value = permission
  
  // 模拟加载访问日志
  accessLogs.value = [
    {
      id: 1,
      accessTime: '2024-01-20 14:30:00',
      action: 'read',
      ipAddress: '192.168.1.100',
      userAgent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
      result: 'success'
    },
    {
      id: 2,
      accessTime: '2024-01-20 14:25:00',
      action: 'query',
      ipAddress: '192.168.1.100',
      userAgent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
      result: 'success'
    },
    {
      id: 3,
      accessTime: '2024-01-20 14:20:00',
      action: 'read',
      ipAddress: '192.168.1.101',
      userAgent: 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
      result: 'failed'
    }
  ]
  
  logDialogVisible.value = true
}

/**
 * 组件挂载时初始化
 */
onMounted(() => {
  // 初始化数据
  totalCount.value = permissions.value.length
})
</script>

<style lang="scss" scoped>
.permission-manage-container {
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

.action-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  padding: 16px;
  background: var(--el-bg-color);
  border-radius: 8px;
  border: 1px solid var(--el-border-color-lighter);
  
  .left-actions,
  .right-actions {
    display: flex;
    gap: 12px;
    align-items: center;
  }
}

.stats-section {
  margin-bottom: 20px;
  
  .stats-card {
    .stats-content {
      display: flex;
      align-items: center;
      gap: 16px;
      
      .stats-icon {
        font-size: 32px;
      }
      
      .stats-info {
        .stats-number {
          font-size: 24px;
          font-weight: 600;
          color: var(--el-text-color-primary);
          line-height: 1;
        }
        
        .stats-label {
          font-size: 14px;
          color: var(--el-text-color-secondary);
          margin-top: 4px;
        }
      }
    }
  }
}

.permission-list-section {
  .card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
  }
  
  .user-cell {
    display: flex;
    align-items: center;
    gap: 8px;
    
    .user-name {
      font-weight: 500;
    }
  }
  
  .resource-cell {
    display: flex;
    align-items: center;
    gap: 8px;
    
    .resource-icon {
      color: var(--el-color-primary);
    }
  }
  
  .expired-time {
    color: var(--el-color-danger);
    font-weight: 500;
  }
  
  .expand-content {
    padding: 20px;
    background: var(--el-bg-color-page);
    
    .permission-details {
      h4 {
        margin: 0 0 16px 0;
        color: var(--el-text-color-primary);
      }
      
      h5 {
        margin: 16px 0 8px 0;
        color: var(--el-text-color-regular);
        font-size: 14px;
      }
      
      .permission-conditions {
        margin-top: 16px;
      }
      
      .permission-notes {
        margin-top: 16px;
        
        p {
          margin: 0;
          color: var(--el-text-color-secondary);
          line-height: 1.5;
        }
      }
    }
  }
  
  .pagination-wrapper {
    margin-top: 20px;
    text-align: center;
  }
}

.user-option,
.resource-option {
  display: flex;
  align-items: center;
  gap: 8px;
  
  .user-email {
    margin-left: auto;
    font-size: 12px;
    color: var(--el-text-color-secondary);
  }
  
  .resource-icon {
    color: var(--el-color-primary);
  }
}

.log-content {
  .log-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 20px;
    padding: 16px;
    background: var(--el-bg-color-page);
    border-radius: 8px;
    
    .permission-info {
      display: flex;
      align-items: center;
      gap: 8px;
      
      .user-name,
      .resource-name {
        font-weight: 500;
      }
    }
    
    .log-stats {
      font-size: 14px;
      color: var(--el-text-color-secondary);
    }
  }
}

.dialog-footer {
  text-align: right;
}

// 响应式设计
@media (max-width: 1200px) {
  .action-bar {
    flex-direction: column;
    gap: 16px;
    align-items: stretch;
    
    .left-actions,
    .right-actions {
      justify-content: center;
      flex-wrap: wrap;
    }
  }
  
  .stats-section {
    .el-col {
      margin-bottom: 16px;
    }
  }
}

@media (max-width: 768px) {
  .permission-manage-container {
    padding: 16px;
  }
  
  .action-bar {
    .left-actions,
    .right-actions {
      gap: 8px;
    }
    
    .el-input,
    .el-select {
      width: 100% !important;
    }
  }
  
  .stats-section {
    .el-col {
      span: 12 !important;
    }
  }
  
  .permission-list-section {
    .el-table {
      font-size: 12px;
    }
  }
  
  .expand-content {
    padding: 12px !important;
  }
}
</style>