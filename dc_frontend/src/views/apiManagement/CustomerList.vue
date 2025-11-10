<template>
  <div class="customer-management">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="header-content">
        <div class="header-left">
          <h1 class="page-title">
            <el-icon><UserFilled /></el-icon>
            平台管理
          </h1>
          <p class="page-description">管理API接口平台信息和权限配置</p>
        </div>
        <div class="header-right">
          <el-button type="primary" @click="showCreateDialog">
            <el-icon><Plus /></el-icon>
            添加平台
          </el-button>
          <el-button @click="loadCustomers">
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
              <el-icon><UserFilled /></el-icon>
            </div>
            <div class="stat-content">
              <div class="stat-value">{{ customerStats.total }}</div>
              <div class="stat-label">总平台数</div>
            </div>
          </div>
        </el-col>
        
        <el-col :xs="12" :sm="6">
          <div class="stat-card">
            <div class="stat-icon active">
              <el-icon><CircleCheck /></el-icon>
            </div>
            <div class="stat-content">
              <div class="stat-value">{{ customerStats.active }}</div>
              <div class="stat-label">活跃平台</div>
            </div>
          </div>
        </el-col>
        
        <el-col :xs="12" :sm="6">
          <div class="stat-card">
            <div class="stat-icon api-calls">
              <el-icon><DataLine /></el-icon>
            </div>
            <div class="stat-content">
              <div class="stat-value">{{ formatNumber(customerStats.totalApiCalls) }}</div>
              <div class="stat-label">总API调用</div>
            </div>
          </div>
        </el-col>
        
        <el-col :xs="12" :sm="6">
          <div class="stat-card">
            <div class="stat-icon recent">
              <el-icon><Clock /></el-icon>
            </div>
            <div class="stat-content">
              <div class="stat-value">{{ customerStats.recentActive }}</div>
              <div class="stat-label">近期活跃</div>
            </div>
          </div>
        </el-col>
      </el-row>
    </div>

    <!-- 搜索和筛选 -->
    <div class="filter-section">
      <el-card shadow="never">
        <el-form :model="filters" inline>
          <el-form-item label="搜索">
            <el-input
              v-model="searchQuery"
              placeholder="搜索平台名称、邮箱或公司"
              clearable
              style="width: 280px"
              @input="handleSearch"
            >
              <template #prefix>
                <el-icon><Search /></el-icon>
              </template>
            </el-input>
          </el-form-item>
          
          <el-form-item label="状态">
            <el-select
              v-model="statusFilter"
              placeholder="选择状态"
              clearable
              style="width: 120px"
              @change="handleSearch"
            >
              <el-option label="全部" value="" />
              <el-option label="激活" value="true" />
              <el-option label="禁用" value="false" />
            </el-select>
          </el-form-item>
          
          <el-form-item label="公司">
            <el-select
              v-model="companyFilter"
              placeholder="选择公司"
              clearable
              style="width: 150px"
              @change="handleSearch"
            >
              <el-option label="全部" value="" />
              <el-option 
                v-for="company in uniqueCompanies" 
                :key="company" 
                :label="company" 
                :value="company" 
              />
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

    <!-- 客户表格 -->
    <div class="customers-list">
      <el-card shadow="never">
        <template #header>
          <div class="card-header">
            <span>客户列表</span>
            <div class="header-actions">
              <span class="total-count">共 {{ filteredCustomers.length }} 条记录</span>
              <el-radio-group v-model="viewMode" size="small" style="margin-left: 20px">
                <el-radio-button value="grid">
                  <el-icon><Grid /></el-icon>
                </el-radio-button>
                <el-radio-button value="list">
                  <el-icon><List /></el-icon>
                </el-radio-button>
              </el-radio-group>
            </div>
          </div>
        </template>
        
        <!-- 卡片视图 -->
        <div v-if="viewMode === 'grid'" class="grid-view">
          <el-row :gutter="20">
            <el-col
              v-for="customer in paginatedCustomers"
              :key="customer.id"
              :xs="24"
              :sm="12"
              :md="8"
              :lg="6"
            >
              <div class="customer-card">
                <div class="customer-card-header">
                  <div class="customer-avatar">
                    <el-icon><UserFilled /></el-icon>
                  </div>
                  <div class="customer-status">
                    <el-tag 
                      :type="customer.is_active ? 'success' : 'danger'" 
                      size="small"
                      effect="light"
                    >
                      {{ customer.is_active ? '激活' : '禁用' }}
                    </el-tag>
                  </div>
                </div>
                
                <div class="customer-card-content">
                  <h3 class="customer-name">{{ customer.name }}</h3>
                  <p class="customer-email">{{ customer.email }}</p>
                  <p class="customer-company" v-if="customer.company">{{ customer.company }}</p>
                  
                  <div class="customer-meta">
                    <div class="meta-item">
                      <el-icon><Phone /></el-icon>
                      <span>{{ customer.phone || '未设置' }}</span>
                    </div>
                    <div class="meta-item">
                      <el-icon><Calendar /></el-icon>
                      <span>{{ formatDate(customer.created_at) }}</span>
                    </div>
                    <div class="meta-item">
                      <el-icon><DataLine /></el-icon>
                      <span>{{ formatNumber(customer.total_api_calls) }} 次调用</span>
                    </div>
                  </div>
                  
                  <div class="customer-config">
                    <div class="config-row">
                      <div class="config-item">
                        <span class="config-label">App ID:</span>
                        <el-text class="app-id" @click="copyToClipboard(customer.app_id)" type="primary">
                          {{ customer.app_id.substring(0, 8) }}...
                        </el-text>
                      </div>
                    </div>
                    <div class="config-row">
                      <div class="config-item">
                        <span class="config-label">限制:</span>
                        <el-tag size="small" type="info">{{ customer.rate_limit }}/分钟</el-tag>
                      </div>
                      <div class="config-item">
                        <span class="config-label">最大:</span>
                        <el-tag size="small" type="warning">{{ customer.max_apis }} APIs</el-tag>
                      </div>
                    </div>
                  </div>
                  
                  <div class="customer-activity" v-if="customer.last_api_call_at">
                    <div class="activity-label">最后活跃:</div>
                    <div class="activity-time">{{ getRelativeTime(customer.last_api_call_at) }}</div>
                  </div>
                </div>
                
                <div class="customer-card-actions">
                  <el-button size="small" type="primary" @click="showEditDialog(customer)">
                    <el-icon><Edit /></el-icon>
                    编辑
                  </el-button>
                  <el-dropdown trigger="click">
                    <el-button size="small" text>
                      <el-icon><MoreFilled /></el-icon>
                    </el-button>
                    <template #dropdown>
                      <el-dropdown-menu>
                        <el-dropdown-item @click="resetSecret(customer)">
                          <el-icon><Key /></el-icon>
                        重置密钥
                      </el-dropdown-item>
                      <el-dropdown-item @click="resetPassword(customer)">
                        <el-icon><Lock /></el-icon>
                        重置密码
                      </el-dropdown-item>
                      <el-dropdown-item
                        divided
                        @click="deleteCustomer(customer)"
                        >
                          <el-icon><Delete /></el-icon>
                          删除
                        </el-dropdown-item>
                      </el-dropdown-menu>
                    </template>
                  </el-dropdown>
                </div>
              </div>
            </el-col>
          </el-row>
        </div>
        
        <!-- 列表视图 -->
        <div v-else class="list-view">
          <el-table
          :data="paginatedCustomers"
          v-loading="loading"
          style="width: 100%"
          @sort-change="handleSortChange"
          stripe
          :header-cell-style="{ background: '#f8f9fa', color: '#606266' }"
        >
          <el-table-column prop="id" label="ID" min-width="80" sortable />
          
          <el-table-column prop="name" label="平台信息" min-width="250" sortable>
            <template #default="{ row }">
              <div class="customer-info">
                <div class="customer-avatar">
                  <el-icon><UserFilled /></el-icon>
                </div>
                <div class="customer-details">
                  <div class="customer-name">{{ row.name }}</div>
                  <div class="customer-email">{{ row.email }}</div>
                  <div class="customer-company" v-if="row.company">{{ row.company }}</div>
                </div>
              </div>
            </template>
          </el-table-column>
          
          <el-table-column prop="phone" label="联系方式" min-width="130">
            <template #default="{ row }">
              <div v-if="row.phone" class="contact-info">
                <el-icon><Phone /></el-icon>
                {{ row.phone }}
              </div>
              <span v-else class="no-data">-</span>
            </template>
          </el-table-column>
          
          <el-table-column prop="app_id" label="App ID" min-width="140">
            <template #default="{ row }">
              <div class="app-id-cell">
                <el-text class="app-id" @click="copyToClipboard(row.app_id)" type="primary">
                  {{ row.app_id }}
                </el-text>
                <el-icon class="copy-icon" @click="copyToClipboard(row.app_id)">
                  <CopyDocument />
                </el-icon>
              </div>
            </template>
          </el-table-column>
          
          <el-table-column label="API配置" min-width="180">
            <template #default="{ row }">
              <div class="api-config">
                <div class="config-item">
                  <span class="config-label">限制:</span>
                  <el-tag size="small" type="info">{{ row.rate_limit }}/分钟</el-tag>
                </div>
                <div class="config-item">
                  <span class="config-label">最大:</span>
                  <el-tag size="small" type="warning">{{ row.max_apis }} APIs</el-tag>
                </div>
              </div>
            </template>
          </el-table-column>
          
          <el-table-column prop="total_api_calls" label="调用统计" min-width="120" sortable>
            <template #default="{ row }">
              <div class="api-stats">
                <div class="stats-number">{{ formatNumber(row.total_api_calls) }}</div>
                <div class="stats-label">总调用</div>
              </div>
            </template>
          </el-table-column>
          
          <el-table-column prop="last_api_call_at" label="最后活跃" min-width="150" sortable>
            <template #default="{ row }">
              <div v-if="row.last_api_call_at" class="last-active">
                <div class="active-time">{{ formatDate(row.last_api_call_at) }}</div>
                <div class="active-label">{{ getRelativeTime(row.last_api_call_at) }}</div>
              </div>
              <span v-else class="no-data">从未调用</span>
            </template>
          </el-table-column>
          
          <el-table-column prop="is_active" label="状态" min-width="100">
            <template #default="{ row }">
              <el-tag 
                :type="row.is_active ? 'success' : 'danger'" 
                effect="light"
                size="small"
              >
                <el-icon>
                  <CircleCheck v-if="row.is_active" />
                  <CircleClose v-else />
                </el-icon>
                {{ row.is_active ? '激活' : '禁用' }}
              </el-tag>
            </template>
          </el-table-column>
          
          <el-table-column prop="created_at" label="创建时间" min-width="150" sortable>
            <template #default="{ row }">
              <div class="create-time">
                <div class="time-date">{{ formatDate(row.created_at) }}</div>
                <div class="time-relative">{{ getRelativeTime(row.created_at) }}</div>
              </div>
            </template>
          </el-table-column>
          
          <el-table-column label="操作" min-width="350" fixed="right">
            <template #default="{ row }">
              <div class="action-buttons">
                <el-button size="small" type="primary" @click="showEditDialog(row)">
                  <el-icon><Edit /></el-icon>
                  编辑
                </el-button>
                <el-button size="small" type="warning" @click="resetSecret(row)">
                  <el-icon><Key /></el-icon>
                  重置密钥
                </el-button>
                <el-button size="small" type="info" @click="resetPassword(row)">
                  <el-icon><Lock /></el-icon>
                  重置密码
                </el-button>
                <el-button size="small" type="danger" @click="deleteCustomer(row)">
                  <el-icon><Delete /></el-icon>
                  删除
                </el-button>
              </div>
            </template>
          </el-table-column>
        </el-table>
        
        <!-- 分页 -->
        <div class="pagination-wrapper">
          <el-pagination
             v-model:current-page="pagination.page"
             v-model:page-size="pagination.pageSize"
             :total="filteredCustomers.length"
             :page-sizes="[10, 20, 50, 100]"
             layout="total, sizes, prev, pager, next, jumper"
             @size-change="handleSizeChange"
             @current-change="handleCurrentChange"
           />
        </div>
        </div>
      </el-card>
    </div>

    <!-- 创建/编辑客户对话框 -->
    <el-dialog
      v-model="dialogVisible"
      :title="isEdit ? '编辑客户' : '添加平台'"
      width="600px"
      @close="resetForm"
    >
      <el-form
        ref="formRef"
        :model="form"
        :rules="formRules"
        label-width="120px"
      >
        <el-form-item label="客户名称" prop="name">
          <el-input v-model="form.name" placeholder="请输入客户名称" />
        </el-form-item>
        <el-form-item label="邮箱" prop="email">
          <el-input v-model="form.email" placeholder="请输入邮箱地址" />
        </el-form-item>
        <el-form-item label="电话" prop="phone">
          <el-input v-model="form.phone" placeholder="请输入电话号码" />
        </el-form-item>
        <el-form-item label="公司" prop="company">
          <el-input v-model="form.company" placeholder="请输入公司名称" />
        </el-form-item>
        <el-form-item label="调用限制" prop="rate_limit">
          <el-input-number
            v-model="form.rate_limit"
            :min="1"
            :max="10000"
            placeholder="每分钟最大调用次数"
            style="width: 100%"
          />
        </el-form-item>
        <el-form-item label="最大API数" prop="max_apis">
          <el-input-number
            v-model="form.max_apis"
            :min="1"
            :max="100"
            placeholder="最大可创建API数量"
            style="width: 100%"
          />
        </el-form-item>
        <el-form-item v-if="isEdit" label="状态" prop="is_active">
          <el-switch
            v-model="form.is_active"
            active-text="激活"
            inactive-text="禁用"
          />
        </el-form-item>
      </el-form>

      <template #footer>
        <div class="dialog-footer">
          <el-button @click="dialogVisible = false">取消</el-button>
          <el-button type="primary" @click="submitForm" :loading="submitting">
            {{ isEdit ? '更新' : '创建' }}
          </el-button>
        </div>
      </template>
    </el-dialog>

    <!-- 密钥显示对话框 -->
    <el-dialog
      v-model="secretDialogVisible"
      title="客户密钥信息"
      width="500px"
    >
      <div class="secret-info">
        <el-alert
          title="请妥善保管密钥信息"
          type="warning"
          :closable="false"
          style="margin-bottom: 20px"
        />
        <el-form label-width="100px">
          <el-form-item label="App ID:">
            <el-input
              :value="currentSecret.app_id"
              readonly
              style="width: 300px"
            >
              <template #append>
                <el-button @click="copyToClipboard(currentSecret.app_id)">
                  <el-icon><CopyDocument /></el-icon>
                </el-button>
              </template>
            </el-input>
          </el-form-item>
          <el-form-item label="App Secret:">
            <el-input
              :value="currentSecret.app_secret"
              readonly
              style="width: 300px"
            >
              <template #append>
                <el-button @click="copyToClipboard(currentSecret.app_secret)">
                  <el-icon><CopyDocument /></el-icon>
                </el-button>
              </template>
            </el-input>
          </el-form-item>
        </el-form>
      </div>

      <template #footer>
        <div class="dialog-footer">
          <el-button type="primary" @click="secretDialogVisible = false">确定</el-button>
        </div>
      </template>
    </el-dialog>

    <!-- 密码显示对话框 -->
    <el-dialog
      v-model="passwordDialogVisible"
      title="客户密码信息"
      width="500px"
    >
      <div class="secret-info">
        <el-alert
          title="请妥善保管密码信息，离开页面后不可再查看"
          type="warning"
          :closable="false"
          style="margin-bottom: 20px"
        />
        <el-form label-width="100px">
          <el-form-item label="密码:">
            <el-input
              :value="currentPassword"
              readonly
              style="width: 300px"
            >
              <template #append>
                <el-button @click="copyToClipboard(String(currentPassword))">
                  <el-icon><CopyDocument /></el-icon>
                </el-button>
              </template>
            </el-input>
          </el-form-item>
        </el-form>
      </div>
      <template #footer>
        <div class="dialog-footer">
          <el-button type="primary" @click="passwordDialogVisible = false">确定</el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import type { FormInstance, FormRules } from 'element-plus'
import { 
  UserFilled, 
  Plus, 
  Refresh, 
  Search, 
  RefreshLeft,
  CircleCheck, 
  CircleClose,
  DataLine, 
  Clock, 
  Phone,
  CopyDocument,
  Edit, 
  Key, 
  Delete,
  Grid,
  List,
  Calendar,
  Setting,
  MoreFilled,
  Lock
} from '@element-plus/icons-vue'
import { formatDate } from '@/utils/date'
import {
  getCustomers,
  createCustomer,
  updateCustomer,
  deleteCustomer as deleteCustomerApi,
  resetCustomerSecret
  , resetCustomerPassword
} from '@/api/apiManagement'
import type { Customer, CustomerCreate, CustomerUpdate } from '@/types/apiManagement'

/**
 * 响应式数据
 */
const loading = ref(false)
const customers = ref<Customer[]>([])
const searchQuery = ref('')
const statusFilter = ref('')
const companyFilter = ref('')
const dialogVisible = ref(false)
const secretDialogVisible = ref(false)
const passwordDialogVisible = ref(false)
const isEdit = ref(false)
const submitting = ref(false)
const formRef = ref<FormInstance>()
const viewMode = ref('list')

// 筛选数据
const filters = reactive({
  search: '',
  status: '',
  company: ''
})

// 分页数据
const pagination = reactive({
  page: 1,
  pageSize: 20
})

// 表单数据
const form = reactive<CustomerCreate & { is_active?: boolean; id?: number }>({
  name: '',
  email: '',
  phone: '',
  company: '',
  rate_limit: 100,
  max_apis: 10,
  is_active: true
})

// 统计数据
const customerStats = computed(() => {
  const total = customers.value.length
  const active = customers.value.filter(c => c.is_active).length
  const totalApiCalls = customers.value.reduce((sum, c) => sum + (c.total_api_calls || 0), 0)
  
  // 计算近期活跃平台（最近30天有API调用）
  const thirtyDaysAgo = new Date()
  thirtyDaysAgo.setDate(thirtyDaysAgo.getDate() - 30)
  const recentActive = customers.value.filter(c => 
    c.last_api_call_at && new Date(c.last_api_call_at) > thirtyDaysAgo
  ).length
  
  return {
    total,
    active,
    totalApiCalls,
    recentActive
  }
})

// 获取唯一公司列表
const uniqueCompanies = computed(() => {
  const companies = customers.value
    .map(c => c.company)
    .filter(Boolean)
    .filter((company, index, arr) => arr.indexOf(company) === index)
  return companies.sort()
})

// 当前密钥信息
const currentSecret = reactive({
  app_id: '',
  app_secret: ''
})
const currentPassword = ref('')

// 表单验证规则
const formRules: FormRules = {
  name: [
    { required: true, message: '请输入客户名称', trigger: 'blur' },
    { min: 2, max: 50, message: '长度在 2 到 50 个字符', trigger: 'blur' }
  ],
  email: [
    { required: true, message: '请输入邮箱地址', trigger: 'blur' },
    { type: 'email', message: '请输入正确的邮箱地址', trigger: 'blur' }
  ],
  rate_limit: [
    { required: true, message: '请设置调用限制', trigger: 'blur' }
  ],
  max_apis: [
    { required: true, message: '请设置最大API数', trigger: 'blur' }
  ]
}

/**
 * 计算属性
 */
const filteredCustomers = computed(() => {
  let result = customers.value

  // 搜索过滤
  if (searchQuery.value) {
    const query = searchQuery.value.toLowerCase()
    result = result.filter(customer =>
      customer.name.toLowerCase().includes(query) ||
      customer.email.toLowerCase().includes(query) ||
      (customer.company && customer.company.toLowerCase().includes(query))
    )
  }

  // 状态过滤
  if (statusFilter.value !== '') {
    const isActive = statusFilter.value === 'true'
    result = result.filter(customer => customer.is_active === isActive)
  }

  // 公司过滤
  if (companyFilter.value) {
    result = result.filter(customer => customer.company === companyFilter.value)
  }

  return result
})

// 分页后的客户数据
const paginatedCustomers = computed(() => {
  const start = (pagination.page - 1) * pagination.pageSize
  const end = start + pagination.pageSize
  return filteredCustomers.value.slice(start, end)
})

/**
 * 工具函数
 */

/**
 * 格式化数字显示
 */
const formatNumber = (num: number): string => {
  if (num >= 1000000) {
    return (num / 1000000).toFixed(1) + 'M'
  } else if (num >= 1000) {
    return (num / 1000).toFixed(1) + 'K'
  }
  return num.toString()
}

/**
 * 获取相对时间
 */
const getRelativeTime = (dateString: string): string => {
  const date = new Date(dateString)
  const now = new Date()
  const diffInSeconds = Math.floor((now.getTime() - date.getTime()) / 1000)
  
  if (diffInSeconds < 60) {
    return '刚刚'
  } else if (diffInSeconds < 3600) {
    return `${Math.floor(diffInSeconds / 60)}分钟前`
  } else if (diffInSeconds < 86400) {
    return `${Math.floor(diffInSeconds / 3600)}小时前`
  } else if (diffInSeconds < 2592000) {
    return `${Math.floor(diffInSeconds / 86400)}天前`
  } else {
    return `${Math.floor(diffInSeconds / 2592000)}个月前`
  }
}

/**
 * 生命周期钩子
 */
onMounted(() => {
  loadCustomers()
})

/**
 * 方法定义
 */

/**
 * 加载客户列表
 */
const loadCustomers = async () => {
  try {
    loading.value = true
    const response = await getCustomers()

    if (response.success) {
      customers.value = response.data.items || response.data
    } else {
      ElMessage.error(response.message || '加载客户列表失败')
    }
  } catch (error) {
    console.error('加载客户列表失败:', error)
    ElMessage.error('加载客户列表失败')
  } finally {
    loading.value = false
  }
}

/**
 * 重置筛选条件
 */
const resetFilters = () => {
  searchQuery.value = ''
  statusFilter.value = ''
  companyFilter.value = ''
  pagination.page = 1
}

/**
 * 分页大小改变处理
 */
const handleSizeChange = (size: number) => {
  pagination.pageSize = size
  pagination.page = 1
}

/**
 * 当前页改变处理
 */
const handleCurrentChange = (page: number) => {
  pagination.page = page
}

/**
 * 显示创建对话框
 */
const showCreateDialog = () => {
  isEdit.value = false
  dialogVisible.value = true
  resetForm()
}

/**
 * 显示编辑对话框
 */
const showEditDialog = (customer: Customer) => {
  isEdit.value = true
  dialogVisible.value = true
  
  // 填充表单数据
  Object.assign(form, {
    name: customer.name,
    email: customer.email,
    phone: customer.phone,
    company: customer.company,
    rate_limit: customer.rate_limit,
    max_apis: customer.max_apis,
    is_active: customer.is_active
  })
  
  form.id = customer.id
}

/**
 * 重置表单
 */
const resetForm = () => {
  if (formRef.value) {
    formRef.value.resetFields()
  }
  
  Object.assign(form, {
    name: '',
    email: '',
    phone: '',
    company: '',
    rate_limit: 100,
    max_apis: 10,
    is_active: true
  })
  
  delete form.id
}

/**
 * 提交表单
 */
const submitForm = async () => {
  if (!formRef.value) return

  try {
    await formRef.value.validate()
    submitting.value = true

    if (isEdit.value && form.id) {
      // 更新客户
      const updateData: CustomerUpdate = {
        name: form.name,
        email: form.email,
        phone: form.phone,
        company: form.company,
        rate_limit: form.rate_limit,
        max_apis: form.max_apis,
        is_active: form.is_active
      }

      const response = await updateCustomer(form.id, updateData)
      if (response.success) {
        ElMessage.success('客户更新成功')
        dialogVisible.value = false
        loadCustomers()
      } else {
        ElMessage.error(response.message || '客户更新失败')
      }
    } else {
      // 创建客户
      const createData: CustomerCreate = {
        name: form.name,
        email: form.email,
        phone: form.phone,
        company: form.company,
        rate_limit: form.rate_limit,
        max_apis: form.max_apis
      }

      const response = await createCustomer(createData)
      if (response.success) {
        ElMessage.success('客户创建成功')
        dialogVisible.value = false
        loadCustomers()
      } else {
        ElMessage.error(response.message || '客户创建失败')
      }
    }
  } catch (error) {
    console.error('提交表单失败:', error)
  } finally {
    submitting.value = false
  }
}

/**
 * 删除客户
 */
const deleteCustomer = async (customer: Customer) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除客户 "${customer.name}" 吗？此操作不可恢复。`,
      '确认删除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )

    const response = await deleteCustomerApi(customer.id)
    if (response.success) {
      ElMessage.success('客户删除成功')
      loadCustomers()
    } else {
      ElMessage.error(response.message || '客户删除失败')
    }
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除客户失败:', error)
      ElMessage.error('客户删除失败')
    }
  }
}

/**
 * 重置客户密钥
 */
const resetSecret = async (customer: Customer) => {
  try {
    await ElMessageBox.confirm(
      `确定要重置客户 "${customer.name}" 的密钥吗？旧密钥将失效。`,
      '确认重置密钥',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )

    const response = await resetCustomerSecret(customer.id)
    if (response.success) {
      currentSecret.app_id = customer.app_id
      currentSecret.app_secret = response.data.app_secret
      secretDialogVisible.value = true
      ElMessage.success('密钥重置成功')
    } else {
      ElMessage.error(response.message || '密钥重置失败')
    }
  } catch (error) {
    if (error !== 'cancel') {
      console.error('重置密钥失败:', error)
      ElMessage.error('密钥重置失败')
    }
  }
}

// 生成强密码
const generateRandomPassword = (length = 12) => {
  const upper = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
  const lower = 'abcdefghijklmnopqrstuvwxyz'
  const digits = '0123456789'
  const symbols = '!@#$%^&*()-_=+[]{};:,.<>?'
  const all = upper + lower + digits + symbols

  let password = ''
  password += upper[Math.floor(Math.random() * upper.length)]
  password += lower[Math.floor(Math.random() * lower.length)]
  password += digits[Math.floor(Math.random() * digits.length)]
  password += symbols[Math.floor(Math.random() * symbols.length)]
  for (let i = password.length; i < length; i++) {
    password += all[Math.floor(Math.random() * all.length)]
  }
  return password.split('').sort(() => Math.random() - 0.5).join('')
}

// 重置客户密码（调用服务端并展示一次性密码）
const resetPassword = async (customer: Customer) => {
  try {
    await ElMessageBox.confirm(
      `确定要为客户 "${customer.name}" 重置密码吗？`,
      '确认重置密码',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )

    const response = await resetCustomerPassword(customer.id)
    if (response.success) {
      currentPassword.value = response.data.password
      passwordDialogVisible.value = true
      ElMessage.success('密码重置成功')
    } else {
      ElMessage.error(response.message || '密码重置失败')
    }
  } catch (error) {
    if (error !== 'cancel') {
      console.error('重置密码失败:', error)
      ElMessage.error('重置密码失败')
    }
  }
}

/**
 * 复制到剪贴板
 */
const copyToClipboard = async (text: string) => {
  try {
    await navigator.clipboard.writeText(text)
    ElMessage.success('已复制到剪贴板')
  } catch (error) {
    console.error('复制失败:', error)
    ElMessage.error('复制失败')
  }
}

/**
 * 搜索处理
 */
const handleSearch = () => {
  // 搜索逻辑已在计算属性中处理
}

/**
 * 排序处理
 */
const handleSortChange = ({ prop, order }: { prop: string; order: string }) => {
  // 这里可以实现服务端排序
  console.log('排序:', prop, order)
}


</script>

<style scoped lang="scss">
.customer-management {
  padding: 24px;
  background: #f5f7fa;
  min-height: 100vh;
}

/* 页面头部 */
.page-header {
  margin-bottom: 24px;
  
  .header-content {
    display: flex;
    justify-content: space-between;
    align-items: center;
    
    .header-left {
      .page-title {
        display: flex;
        align-items: center;
        gap: 12px;
        margin: 0 0 8px 0;
        font-size: 28px;
        font-weight: 700;
        color: #303133;
        
        .el-icon {
          font-size: 32px;
          color: #409eff;
        }
      }
      
      .page-description {
        margin: 0;
        font-size: 16px;
        color: #606266;
        line-height: 1.5;
      }
    }
    
    .header-right {
      display: flex;
      gap: 12px;
      align-items: center;
    }
  }
}

/* 卡片视图样式 */
.grid-view {
  margin-bottom: 20px;
}

.customer-card {
  background: #fff;
  border: 1px solid #e4e7ed;
  border-radius: 8px;
  padding: 20px;
  margin-bottom: 20px;
  transition: all 0.3s ease;
  height: 100%;
  display: flex;
  flex-direction: column;
}

.customer-card:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  border-color: #409eff;
}

.customer-card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.customer-avatar {
  width: 40px;
  height: 40px;
  background: linear-gradient(135deg, #409eff, #67c23a);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-size: 18px;
}

.customer-card-content {
  flex: 1;
  margin-bottom: 16px;
}

.customer-name {
  font-size: 18px;
  font-weight: 600;
  color: #303133;
  margin: 0 0 8px 0;
  line-height: 1.4;
}

.customer-email {
  color: #606266;
  font-size: 14px;
  margin: 0 0 4px 0;
}

.customer-company {
  color: #909399;
  font-size: 13px;
  margin: 0 0 16px 0;
  font-style: italic;
}

.customer-meta {
  margin-bottom: 16px;
}

.meta-item {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
  font-size: 13px;
  color: #606266;
}

.meta-item .el-icon {
  color: #909399;
  font-size: 14px;
}

.customer-config {
  background: #f8f9fa;
  border-radius: 6px;
  padding: 12px;
  margin-bottom: 16px;
}

.config-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.config-row:last-child {
  margin-bottom: 0;
}

.config-item {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
}

.config-label {
  color: #909399;
  font-weight: 500;
}

.app-id {
  cursor: pointer;
  font-family: monospace;
  font-size: 11px;
}

.app-id:hover {
  text-decoration: underline;
}

.customer-activity {
  background: #f0f9ff;
  border: 1px solid #e1f5fe;
  border-radius: 4px;
  padding: 8px 12px;
  margin-bottom: 16px;
}

.activity-label {
  font-size: 11px;
  color: #909399;
  margin-bottom: 4px;
}

.activity-time {
  font-size: 12px;
  color: #409eff;
  font-weight: 500;
}

.customer-card-actions {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-top: 16px;
  border-top: 1px solid #f0f0f0;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .customer-card {
    padding: 16px;
  }
  
  .customer-name {
    font-size: 16px;
  }
  
  .config-row {
    flex-direction: column;
    align-items: flex-start;
    gap: 8px;
  }
}

/* 统计卡片 */
.stats-cards {
  margin-bottom: 24px;
  
  .stat-card {
    background: white;
    border-radius: 12px;
    padding: 24px;
    box-shadow: 0 2px 12px rgba(0, 0, 0, 0.04);
    border: 1px solid #ebeef5;
    display: flex;
    align-items: center;
    gap: 16px;
    transition: all 0.3s ease;
    
    &:hover {
      box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
      transform: translateY(-2px);
    }
  }
  
  .stat-icon {
    width: 56px;
    height: 56px;
    border-radius: 12px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 24px;
    color: white;
    
    &.total {
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    }
    
    &.active {
      background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
    }
    
    &.api-calls {
      background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
    }
    
    &.recent {
      background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%);
    }
  }
  
  .stat-content {
    flex: 1;
  }
  
  .stat-value {
    font-size: 32px;
    font-weight: 700;
    color: #303133;
    line-height: 1;
    margin-bottom: 4px;
  }
  
  .stat-label {
    font-size: 14px;
    color: #909399;
    font-weight: 500;
  }
}

/* 筛选区域 */
.filter-section {
  margin-bottom: 24px;
}

/* 客户列表 */
.customers-list {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-weight: 600;
  color: #303133;
}

.header-actions {
  display: flex;
  gap: 12px;
  align-items: center;
}

.total-count {
  font-size: 14px;
  color: #909399;
}

/* 表格样式 */
.customer-info {
  display: flex;
  align-items: center;
  gap: 12px;
}

.customer-avatar {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-size: 18px;
}

.customer-details {
  flex: 1;
}

.customer-name {
  font-weight: 600;
  color: #303133;
  margin-bottom: 4px;
  font-size: 14px;
}

.customer-email {
  font-size: 13px;
  color: #909399;
  margin-bottom: 2px;
}

.customer-company {
  font-size: 12px;
  color: #c0c4cc;
}

.contact-info {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  color: #606266;
}

.app-id-cell {
  display: flex;
  align-items: center;
  gap: 8px;
}

.app-id {
  cursor: pointer;
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
  font-size: 12px;
  
  &:hover {
    text-decoration: underline;
  }
}

.copy-icon {
  cursor: pointer;
  color: #909399;
  font-size: 14px;
  
  &:hover {
    color: #409eff;
  }
}

.api-config {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.config-item {
  display: flex;
  align-items: center;
  gap: 6px;
}

.config-label {
  font-size: 12px;
  color: #909399;
  min-width: 30px;
}

.api-stats {
  text-align: center;
}

.stats-number {
  font-weight: 600;
  color: #303133;
  font-size: 16px;
  margin-bottom: 2px;
}

.stats-label {
  font-size: 12px;
  color: #909399;
}

.last-active, .create-time {
  text-align: center;
}

.active-time, .time-date {
  font-size: 13px;
  color: #606266;
  margin-bottom: 2px;
}

.active-label, .time-relative {
  font-size: 12px;
  color: #c0c4cc;
}

.no-data {
  color: #c0c4cc;
  font-style: italic;
  font-size: 13px;
}

.action-buttons {
  display: flex;
  gap: 8px;
  align-items: center;
  flex-wrap: nowrap;
}

.action-buttons .el-button {
  margin: 0;
}

/* 分页 */
.pagination-wrapper {
  margin-top: 24px;
  display: flex;
  justify-content: center;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .customer-management {
    padding: 16px;
  }
  
  .header-content {
    flex-direction: column;
    gap: 16px;
  }
  
  .header-right {
    width: 100%;
    justify-content: flex-start;
  }
  
  .page-title {
    font-size: 24px;
  }
  
  .stat-card {
    padding: 16px;
  }
  
  .stat-value {
    font-size: 24px;
  }
}

/* Element Plus 样式覆盖 */
:deep(.el-card__body) {
  padding: 24px;
}

:deep(.el-form--inline .el-form-item) {
  margin-right: 16px;
  margin-bottom: 16px;
}

:deep(.el-table .el-table__cell) {
  padding: 12px 0;
}

:deep(.el-tag) {
  border: none;
  font-weight: 500;
}

:deep(.el-button--small) {
  padding: 6px 12px;
  font-size: 12px;
}

/* 修复 el-scrollbar 内部视图宽度问题 */
:deep(.el-scrollbar__view) {
  width: 100% !important;
}

/* 对话框样式 */
.secret-info {
  .el-form-item {
    margin-bottom: 20px;
  }
}
</style>