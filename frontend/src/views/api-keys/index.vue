<template>
  <div class="api-keys-page">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="header-content">
        <div class="header-left">
          <h1 class="page-title">
            <el-icon><Key /></el-icon>
            API 密钥管理
          </h1>
          <p class="page-description">管理您的 API 访问密钥，用于程序化访问平台服务</p>
        </div>
        <div class="header-right">
          <el-button type="primary" @click="showCreateDialog">
            <el-icon><Plus /></el-icon>
            创建密钥
          </el-button>
          <el-button @click="loadApiKeys">
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
          <el-card shadow="hover" class="stat-card">
            <div class="stat-content">
              <div class="stat-icon total">
                <el-icon><Key /></el-icon>
              </div>
              <div class="stat-info">
                <div class="stat-value">{{ stats.total }}</div>
                <div class="stat-label">总密钥数</div>
              </div>
            </div>
          </el-card>
        </el-col>
        
        <el-col :xs="12" :sm="6">
          <el-card shadow="hover" class="stat-card">
            <div class="stat-content">
              <div class="stat-icon active">
                <el-icon><CircleCheck /></el-icon>
              </div>
              <div class="stat-info">
                <div class="stat-value">{{ stats.active }}</div>
                <div class="stat-label">活跃密钥</div>
              </div>
            </div>
          </el-card>
        </el-col>
        
        <el-col :xs="12" :sm="6">
          <el-card shadow="hover" class="stat-card">
            <div class="stat-content">
              <div class="stat-icon expired">
                <el-icon><Clock /></el-icon>
              </div>
              <div class="stat-info">
                <div class="stat-value">{{ stats.expired }}</div>
                <div class="stat-label">已过期</div>
              </div>
            </div>
          </el-card>
        </el-col>
        
        <el-col :xs="12" :sm="6">
          <el-card shadow="hover" class="stat-card">
            <div class="stat-content">
              <div class="stat-icon requests">
                <el-icon><DataLine /></el-icon>
              </div>
              <div class="stat-info">
                <div class="stat-value">{{ formatNumber(stats.totalRequests) }}</div>
                <div class="stat-label">总请求数</div>
              </div>
            </div>
          </el-card>
        </el-col>
      </el-row>
    </div>
    
    <!-- 筛选和搜索 -->
    <div class="filter-section">
      <el-card shadow="never">
        <el-row :gutter="20" class="filter-row">
          <el-col :xs="24" :sm="8" :md="6">
            <el-input
              v-model="filters.search"
              placeholder="搜索密钥名称或描述"
              clearable
              @input="handleSearch"
            >
              <template #prefix>
                <el-icon><Search /></el-icon>
              </template>
            </el-input>
          </el-col>
          
          <el-col :xs="12" :sm="4" :md="3">
            <el-select
              v-model="filters.status"
              placeholder="状态"
              clearable
              @change="handleFilter"
            >
              <el-option label="全部" value="" />
              <el-option label="活跃" value="active" />
              <el-option label="已禁用" value="disabled" />
              <el-option label="已过期" value="expired" />
            </el-select>
          </el-col>
          
          <el-col :xs="12" :sm="4" :md="3">
            <el-select
              v-model="filters.scope"
              placeholder="权限范围"
              clearable
              @change="handleFilter"
            >
              <el-option label="全部" value="" />
              <el-option label="只读" value="read" />
              <el-option label="读写" value="write" />
              <el-option label="管理员" value="admin" />
            </el-select>
          </el-col>
          
          <el-col :xs="12" :sm="4" :md="3">
            <el-select
              v-model="filters.sortBy"
              placeholder="排序"
              @change="handleFilter"
            >
              <el-option label="创建时间" value="created_at" />
              <el-option label="最后使用" value="last_used" />
              <el-option label="请求次数" value="request_count" />
              <el-option label="名称" value="name" />
            </el-select>
          </el-col>
          
          <el-col :xs="12" :sm="4" :md="3">
            <el-button @click="resetFilters">
              <el-icon><RefreshLeft /></el-icon>
              重置
            </el-button>
          </el-col>
        </el-row>
      </el-card>
    </div>
    
    <!-- API 密钥列表 -->
    <div class="api-keys-list">
      <el-card shadow="never">
        <div class="list-header">
          <h3>API 密钥列表</h3>
          <div class="list-actions">
            <el-button-group>
              <el-button
                :type="viewMode === 'table' ? 'primary' : 'default'"
                @click="viewMode = 'table'"
              >
                <el-icon><List /></el-icon>
              </el-button>
              <el-button
                :type="viewMode === 'card' ? 'primary' : 'default'"
                @click="viewMode = 'card'"
              >
                <el-icon><Grid /></el-icon>
              </el-button>
            </el-button-group>
          </div>
        </div>
        
        <!-- 表格视图 -->
        <div v-if="viewMode === 'table'" class="table-view">
          <el-table
            :data="filteredApiKeys"
            v-loading="loading"
            stripe
            @sort-change="handleSortChange"
          >
            <el-table-column prop="name" label="密钥名称" sortable min-width="150">
              <template #default="{ row }">
                <div class="key-name">
                  <strong>{{ row.name }}</strong>
                  <div class="key-description">{{ row.description }}</div>
                </div>
              </template>
            </el-table-column>
            
            <el-table-column prop="key_preview" label="密钥" min-width="200">
              <template #default="{ row }">
                <div class="key-preview">
                  <code>{{ row.key_preview }}</code>
                  <el-button
                    size="small"
                    text
                    @click="copyKey(row)"
                    class="copy-btn"
                  >
                    <el-icon><CopyDocument /></el-icon>
                  </el-button>
                </div>
              </template>
            </el-table-column>
            
            <el-table-column prop="scope" label="权限范围" width="120">
              <template #default="{ row }">
                <el-tag
                  :type="getScopeTagType(row.scope)"
                  size="small"
                >
                  {{ getScopeLabel(row.scope) }}
                </el-tag>
              </template>
            </el-table-column>
            
            <el-table-column prop="status" label="状态" width="100">
              <template #default="{ row }">
                <el-tag
                  :type="getStatusTagType(row.status)"
                  size="small"
                >
                  {{ getStatusLabel(row.status) }}
                </el-tag>
              </template>
            </el-table-column>
            
            <el-table-column prop="request_count" label="请求次数" width="120" sortable>
              <template #default="{ row }">
                {{ formatNumber(row.request_count) }}
              </template>
            </el-table-column>
            
            <el-table-column prop="last_used" label="最后使用" width="150" sortable>
              <template #default="{ row }">
                {{ row.last_used ? formatDate(row.last_used) : '从未使用' }}
              </template>
            </el-table-column>
            
            <el-table-column prop="expires_at" label="过期时间" width="150">
              <template #default="{ row }">
                {{ row.expires_at ? formatDate(row.expires_at) : '永不过期' }}
              </template>
            </el-table-column>
            
            <el-table-column label="操作" width="200" fixed="right">
              <template #default="{ row }">
                <div class="action-buttons">
                  <el-button
                    size="small"
                    @click="viewKeyDetails(row)"
                  >
                    查看
                  </el-button>
                  <el-button
                    size="small"
                    @click="editKey(row)"
                  >
                    编辑
                  </el-button>
                  <el-dropdown trigger="click">
                    <el-button size="small">
                      更多
                      <el-icon><ArrowDown /></el-icon>
                    </el-button>
                    <template #dropdown>
                      <el-dropdown-menu>
                        <el-dropdown-item @click="regenerateKey(row)">
                          <el-icon><Refresh /></el-icon>
                          重新生成
                        </el-dropdown-item>
                        <el-dropdown-item
                          @click="toggleKeyStatus(row)"
                          :divided="true"
                        >
                          <el-icon><Switch /></el-icon>
                          {{ row.status === 'active' ? '禁用' : '启用' }}
                        </el-dropdown-item>
                        <el-dropdown-item
                          @click="deleteKey(row)"
                          class="danger-item"
                        >
                          <el-icon><Delete /></el-icon>
                          删除
                        </el-dropdown-item>
                      </el-dropdown-menu>
                    </template>
                  </el-dropdown>
                </div>
              </template>
            </el-table-column>
          </el-table>
        </div>
        
        <!-- 卡片视图 -->
        <div v-else class="card-view">
          <el-row :gutter="20">
            <el-col
              v-for="key in filteredApiKeys"
              :key="key.id"
              :xs="24"
              :sm="12"
              :md="8"
              :lg="6"
            >
              <div class="api-key-card">
                <el-card shadow="hover">
                  <div class="card-header">
                    <div class="key-info">
                      <h4 class="key-name">{{ key.name }}</h4>
                      <p class="key-description">{{ key.description }}</p>
                    </div>
                    <div class="key-status">
                      <el-tag
                        :type="getStatusTagType(key.status)"
                        size="small"
                      >
                        {{ getStatusLabel(key.status) }}
                      </el-tag>
                    </div>
                  </div>
                  
                  <div class="card-content">
                    <div class="key-preview">
                      <label>密钥:</label>
                      <div class="key-value">
                        <code>{{ key.key_preview }}</code>
                        <el-button
                          size="small"
                          text
                          @click="copyKey(key)"
                        >
                          <el-icon><CopyDocument /></el-icon>
                        </el-button>
                      </div>
                    </div>
                    
                    <div class="key-meta">
                      <div class="meta-item">
                        <label>权限:</label>
                        <el-tag
                          :type="getScopeTagType(key.scope)"
                          size="small"
                        >
                          {{ getScopeLabel(key.scope) }}
                        </el-tag>
                      </div>
                      
                      <div class="meta-item">
                        <label>请求次数:</label>
                        <span>{{ formatNumber(key.request_count) }}</span>
                      </div>
                      
                      <div class="meta-item">
                        <label>最后使用:</label>
                        <span>{{ key.last_used ? formatDate(key.last_used) : '从未使用' }}</span>
                      </div>
                      
                      <div class="meta-item" v-if="key.expires_at">
                        <label>过期时间:</label>
                        <span>{{ formatDate(key.expires_at) }}</span>
                      </div>
                    </div>
                  </div>
                  
                  <div class="card-actions">
                    <el-button size="small" @click="viewKeyDetails(key)">
                      查看
                    </el-button>
                    <el-button size="small" @click="editKey(key)">
                      编辑
                    </el-button>
                    <el-dropdown trigger="click">
                      <el-button size="small">
                        <el-icon><MoreFilled /></el-icon>
                      </el-button>
                      <template #dropdown>
                        <el-dropdown-menu>
                          <el-dropdown-item @click="regenerateKey(key)">
                            重新生成
                          </el-dropdown-item>
                          <el-dropdown-item @click="toggleKeyStatus(key)">
                            {{ key.status === 'active' ? '禁用' : '启用' }}
                          </el-dropdown-item>
                          <el-dropdown-item
                            @click="deleteKey(key)"
                            class="danger-item"
                          >
                            删除
                          </el-dropdown-item>
                        </el-dropdown-menu>
                      </template>
                    </el-dropdown>
                  </div>
                </el-card>
              </div>
            </el-col>
          </el-row>
        </div>
        
        <!-- 分页 -->
        <div class="pagination-wrapper" v-if="filteredApiKeys.length > 0">
          <el-pagination
            v-model:current-page="pagination.currentPage"
            v-model:page-size="pagination.pageSize"
            :page-sizes="[10, 20, 50, 100]"
            :total="pagination.total"
            layout="total, sizes, prev, pager, next, jumper"
            @size-change="handleSizeChange"
            @current-change="handleCurrentChange"
          />
        </div>
      </el-card>
    </div>
    
    <!-- 创建/编辑密钥对话框 -->
    <el-dialog
      v-model="dialogVisible"
      :title="isEditing ? '编辑 API 密钥' : '创建 API 密钥'"
      width="600px"
      @close="resetForm"
    >
      <el-form
        ref="formRef"
        :model="form"
        :rules="formRules"
        label-width="100px"
      >
        <el-form-item label="密钥名称" prop="name">
          <el-input
            v-model="form.name"
            placeholder="请输入密钥名称"
            maxlength="50"
            show-word-limit
          />
        </el-form-item>
        
        <el-form-item label="描述">
          <el-input
            v-model="form.description"
            type="textarea"
            :rows="3"
            placeholder="请输入密钥描述"
            maxlength="200"
            show-word-limit
          />
        </el-form-item>
        
        <el-form-item label="权限范围" prop="scope">
          <el-radio-group v-model="form.scope">
            <el-radio value="read">只读</el-radio>
            <el-radio value="write">读写</el-radio>
            <el-radio value="admin">管理员</el-radio>
          </el-radio-group>
          <div class="form-tip">
            <p><strong>只读:</strong> 只能查看数据，不能修改</p>
            <p><strong>读写:</strong> 可以查看和修改数据</p>
            <p><strong>管理员:</strong> 拥有所有权限，包括用户管理</p>
          </div>
        </el-form-item>
        
        <el-form-item label="过期时间">
          <el-radio-group v-model="form.expiryType" @change="handleExpiryTypeChange">
            <el-radio value="never">永不过期</el-radio>
            <el-radio value="custom">自定义</el-radio>
          </el-radio-group>
          <el-date-picker
            v-if="form.expiryType === 'custom'"
            v-model="form.expiresAt"
            type="datetime"
            placeholder="选择过期时间"
            style="width: 100%; margin-top: 8px"
            :disabled-date="disabledDate"
          />
        </el-form-item>
        
        <el-form-item label="IP 白名单">
          <el-input
            v-model="form.ipWhitelist"
            placeholder="多个IP用逗号分隔，留空表示不限制"
          />
          <div class="form-tip">
            例如: 192.168.1.1, 10.0.0.0/8
          </div>
        </el-form-item>
        
        <el-form-item label="请求限制">
          <el-row :gutter="10">
            <el-col :span="12">
              <el-input-number
                v-model="form.rateLimit"
                :min="0"
                :max="10000"
                placeholder="每分钟请求数"
                style="width: 100%"
              />
            </el-col>
            <el-col :span="12">
              <el-input-number
                v-model="form.dailyLimit"
                :min="0"
                :max="1000000"
                placeholder="每日请求数"
                style="width: 100%"
              />
            </el-col>
          </el-row>
          <div class="form-tip">
            设置为 0 表示不限制
          </div>
        </el-form-item>
      </el-form>
      
      <template #footer>
        <div class="dialog-footer">
          <el-button @click="dialogVisible = false">取消</el-button>
          <el-button
            type="primary"
            @click="submitForm"
            :loading="submitting"
          >
            {{ isEditing ? '保存' : '创建' }}
          </el-button>
        </div>
      </template>
    </el-dialog>
    
    <!-- 密钥详情对话框 -->
    <el-dialog
      v-model="detailDialogVisible"
      title="API 密钥详情"
      width="800px"
    >
      <div v-if="selectedKey" class="key-details">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="密钥名称">
            {{ selectedKey.name }}
          </el-descriptions-item>
          <el-descriptions-item label="状态">
            <el-tag
              :type="getStatusTagType(selectedKey.status)"
              size="small"
            >
              {{ getStatusLabel(selectedKey.status) }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="权限范围">
            <el-tag
              :type="getScopeTagType(selectedKey.scope)"
              size="small"
            >
              {{ getScopeLabel(selectedKey.scope) }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="创建时间">
            {{ formatDate(selectedKey.created_at) }}
          </el-descriptions-item>
          <el-descriptions-item label="最后使用">
            {{ selectedKey.last_used ? formatDate(selectedKey.last_used) : '从未使用' }}
          </el-descriptions-item>
          <el-descriptions-item label="过期时间">
            {{ selectedKey.expires_at ? formatDate(selectedKey.expires_at) : '永不过期' }}
          </el-descriptions-item>
          <el-descriptions-item label="请求次数">
            {{ formatNumber(selectedKey.request_count) }}
          </el-descriptions-item>
          <el-descriptions-item label="今日请求">
            {{ formatNumber(selectedKey.today_requests || 0) }}
          </el-descriptions-item>
          <el-descriptions-item label="IP 白名单" :span="2">
            {{ selectedKey.ip_whitelist || '无限制' }}
          </el-descriptions-item>
          <el-descriptions-item label="描述" :span="2">
            {{ selectedKey.description || '无描述' }}
          </el-descriptions-item>
        </el-descriptions>
        
        <!-- 使用统计图表 -->
        <div class="usage-chart" style="margin-top: 20px">
          <h4>使用统计 (最近7天)</h4>
          <div class="chart-placeholder">
            <el-empty description="图表功能开发中" />
          </div>
        </div>
      </div>
    </el-dialog>
    
    <!-- 新密钥显示对话框 -->
    <el-dialog
      v-model="newKeyDialogVisible"
      title="新 API 密钥已创建"
      width="600px"
      :close-on-click-modal="false"
      :close-on-press-escape="false"
    >
      <div class="new-key-content">
        <el-alert
          title="重要提示"
          type="warning"
          :closable="false"
          show-icon
        >
          <p>请立即复制并保存您的 API 密钥。出于安全考虑，我们不会再次显示完整密钥。</p>
        </el-alert>
        
        <div class="key-display">
          <label>您的新 API 密钥:</label>
          <div class="key-value">
            <el-input
              :model-value="newApiKey"
              readonly
              type="textarea"
              :rows="3"
            />
            <el-button
              type="primary"
              @click="copyNewKey"
              style="margin-top: 8px"
            >
              <el-icon><CopyDocument /></el-icon>
              复制密钥
            </el-button>
          </div>
        </div>
        
        <div class="usage-example">
          <h4>使用示例:</h4>
          <el-tabs type="border-card">
            <el-tab-pane label="cURL">
              <pre><code>curl -H "Authorization: Bearer {{ newApiKey }}" \
     -H "Content-Type: application/json" \
     https://api.example.com/v1/models</code></pre>
            </el-tab-pane>
            <el-tab-pane label="Python">
              <pre><code>import requests

headers = {
    'Authorization': 'Bearer {{ newApiKey }}',
    'Content-Type': 'application/json'
}

response = requests.get('https://api.example.com/v1/models', headers=headers)</code></pre>
            </el-tab-pane>
            <el-tab-pane label="JavaScript">
              <pre><code>const response = await fetch('https://api.example.com/v1/models', {
  headers: {
    'Authorization': 'Bearer {{ newApiKey }}',
    'Content-Type': 'application/json'
  }
});</code></pre>
            </el-tab-pane>
          </el-tabs>
        </div>
      </div>
      
      <template #footer>
        <div class="dialog-footer">
          <el-button type="primary" @click="newKeyDialogVisible = false">
            我已保存密钥
          </el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox, type FormInstance, type FormRules } from 'element-plus'
import {
  Key,
  Plus,
  Refresh,
  CircleCheck,
  Clock,
  DataLine,
  Search,
  RefreshLeft,
  List,
  Grid,
  CopyDocument,
  ArrowDown,
  Switch,
  Delete,
  MoreFilled
} from '@element-plus/icons-vue'

// 响应式数据
const loading = ref(false)
const viewMode = ref('table')
const dialogVisible = ref(false)
const detailDialogVisible = ref(false)
const newKeyDialogVisible = ref(false)
const isEditing = ref(false)
const submitting = ref(false)
const formRef = ref<FormInstance>()
const selectedKey = ref(null)
const newApiKey = ref('')

// 统计数据
const stats = reactive({
  total: 12,
  active: 8,
  expired: 2,
  totalRequests: 156789
})

// 筛选条件
const filters = reactive({
  search: '',
  status: '',
  scope: '',
  sortBy: 'created_at'
})

// 分页
const pagination = reactive({
  currentPage: 1,
  pageSize: 10,
  total: 0
})

// 表单数据
const form = reactive({
  id: '',
  name: '',
  description: '',
  scope: 'read',
  expiryType: 'never',
  expiresAt: null,
  ipWhitelist: '',
  rateLimit: 100,
  dailyLimit: 10000
})

// API 密钥列表
const apiKeys = ref([
  {
    id: '1',
    name: '生产环境密钥',
    description: '用于生产环境的API访问',
    key_preview: 'ak_prod_1234...abcd',
    scope: 'write',
    status: 'active',
    request_count: 45678,
    today_requests: 234,
    last_used: '2024-01-21T10:30:00Z',
    expires_at: null,
    created_at: '2024-01-01T00:00:00Z',
    ip_whitelist: '192.168.1.0/24'
  },
  {
    id: '2',
    name: '测试环境密钥',
    description: '用于测试和开发',
    key_preview: 'ak_test_5678...efgh',
    scope: 'read',
    status: 'active',
    request_count: 12345,
    today_requests: 56,
    last_used: '2024-01-20T15:45:00Z',
    expires_at: '2024-12-31T23:59:59Z',
    created_at: '2024-01-05T00:00:00Z',
    ip_whitelist: null
  },
  {
    id: '3',
    name: '临时密钥',
    description: '临时使用的密钥',
    key_preview: 'ak_temp_9012...ijkl',
    scope: 'read',
    status: 'expired',
    request_count: 567,
    today_requests: 0,
    last_used: '2024-01-10T09:20:00Z',
    expires_at: '2024-01-15T23:59:59Z',
    created_at: '2024-01-10T00:00:00Z',
    ip_whitelist: null
  },
  {
    id: '4',
    name: '监控密钥',
    description: '用于系统监控和告警',
    key_preview: 'ak_monitor_3456...mnop',
    scope: 'admin',
    status: 'active',
    request_count: 98765,
    today_requests: 123,
    last_used: '2024-01-21T11:15:00Z',
    expires_at: null,
    created_at: '2023-12-01T00:00:00Z',
    ip_whitelist: '10.0.0.0/8'
  },
  {
    id: '5',
    name: '第三方集成',
    description: '用于第三方系统集成',
    key_preview: 'ak_3rd_7890...qrst',
    scope: 'write',
    status: 'disabled',
    request_count: 23456,
    today_requests: 0,
    last_used: '2024-01-18T14:30:00Z',
    expires_at: '2024-06-30T23:59:59Z',
    created_at: '2024-01-15T00:00:00Z',
    ip_whitelist: '203.0.113.0/24'
  }
])

// 计算属性
const filteredApiKeys = computed(() => {
  let result = [...apiKeys.value]
  
  // 搜索过滤
  if (filters.search) {
    const search = filters.search.toLowerCase()
    result = result.filter(key => 
      key.name.toLowerCase().includes(search) ||
      key.description.toLowerCase().includes(search)
    )
  }
  
  // 状态过滤
  if (filters.status) {
    result = result.filter(key => key.status === filters.status)
  }
  
  // 权限范围过滤
  if (filters.scope) {
    result = result.filter(key => key.scope === filters.scope)
  }
  
  // 排序
  result.sort((a, b) => {
    const field = filters.sortBy
    if (field === 'created_at' || field === 'last_used') {
      return new Date(b[field] || 0).getTime() - new Date(a[field] || 0).getTime()
    }
    if (field === 'request_count') {
      return b[field] - a[field]
    }
    if (field === 'name') {
      return a[field].localeCompare(b[field])
    }
    return 0
  })
  
  pagination.total = result.length
  
  // 分页
  const start = (pagination.currentPage - 1) * pagination.pageSize
  const end = start + pagination.pageSize
  return result.slice(start, end)
})

// 表单验证规则
const formRules: FormRules = {
  name: [
    { required: true, message: '请输入密钥名称', trigger: 'blur' },
    { min: 2, max: 50, message: '长度在 2 到 50 个字符', trigger: 'blur' }
  ],
  scope: [
    { required: true, message: '请选择权限范围', trigger: 'change' }
  ]
}

// 方法
const formatNumber = (num: number) => {
  return num.toLocaleString()
}

const formatDate = (date: string) => {
  return new Date(date).toLocaleString('zh-CN')
}

const getScopeLabel = (scope: string) => {
  const labels = {
    read: '只读',
    write: '读写',
    admin: '管理员'
  }
  return labels[scope] || scope
}

const getScopeTagType = (scope: string) => {
  const types = {
    read: 'info',
    write: 'success',
    admin: 'danger'
  }
  return types[scope] || 'info'
}

const getStatusLabel = (status: string) => {
  const labels = {
    active: '活跃',
    disabled: '已禁用',
    expired: '已过期'
  }
  return labels[status] || status
}

const getStatusTagType = (status: string) => {
  const types = {
    active: 'success',
    disabled: 'warning',
    expired: 'danger'
  }
  return types[status] || 'info'
}

const disabledDate = (time: Date) => {
  return time.getTime() < Date.now()
}

const handleSearch = () => {
  pagination.currentPage = 1
}

const handleFilter = () => {
  pagination.currentPage = 1
}

const resetFilters = () => {
  filters.search = ''
  filters.status = ''
  filters.scope = ''
  filters.sortBy = 'created_at'
  pagination.currentPage = 1
}

const handleSortChange = ({ prop, order }) => {
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

const showCreateDialog = () => {
  isEditing.value = false
  resetForm()
  dialogVisible.value = true
}

const editKey = (key: any) => {
  isEditing.value = true
  Object.assign(form, {
    id: key.id,
    name: key.name,
    description: key.description,
    scope: key.scope,
    expiryType: key.expires_at ? 'custom' : 'never',
    expiresAt: key.expires_at ? new Date(key.expires_at) : null,
    ipWhitelist: key.ip_whitelist || '',
    rateLimit: 100,
    dailyLimit: 10000
  })
  dialogVisible.value = true
}

const resetForm = () => {
  if (formRef.value) {
    formRef.value.resetFields()
  }
  Object.assign(form, {
    id: '',
    name: '',
    description: '',
    scope: 'read',
    expiryType: 'never',
    expiresAt: null,
    ipWhitelist: '',
    rateLimit: 100,
    dailyLimit: 10000
  })
}

const handleExpiryTypeChange = (type: string) => {
  if (type === 'never') {
    form.expiresAt = null
  }
}

const submitForm = async () => {
  if (!formRef.value) return
  
  try {
    await formRef.value.validate()
    submitting.value = true
    
    // 这里应该调用实际的API
    await new Promise(resolve => setTimeout(resolve, 1000))
    
    if (isEditing.value) {
      // 更新现有密钥
      const index = apiKeys.value.findIndex(k => k.id === form.id)
      if (index > -1) {
        Object.assign(apiKeys.value[index], {
          name: form.name,
          description: form.description,
          scope: form.scope,
          expires_at: form.expiryType === 'custom' ? form.expiresAt?.toISOString() : null,
          ip_whitelist: form.ipWhitelist || null
        })
      }
      ElMessage.success('密钥更新成功')
    } else {
      // 创建新密钥
      const newKey = {
        id: Date.now().toString(),
        name: form.name,
        description: form.description,
        key_preview: `ak_${Date.now().toString(36)}_${'*'.repeat(8)}`,
        scope: form.scope,
        status: 'active',
        request_count: 0,
        today_requests: 0,
        last_used: null,
        expires_at: form.expiryType === 'custom' ? form.expiresAt?.toISOString() : null,
        created_at: new Date().toISOString(),
        ip_whitelist: form.ipWhitelist || null
      }
      
      apiKeys.value.unshift(newKey)
      
      // 显示新密钥
      newApiKey.value = `ak_${Date.now().toString(36)}_${'a'.repeat(32)}`
      newKeyDialogVisible.value = true
      
      ElMessage.success('密钥创建成功')
    }
    
    dialogVisible.value = false
    loadApiKeys()
  } catch (error: any) {
    console.error('提交表单失败:', error)
    ElMessage.error('操作失败，请稍后重试')
  } finally {
    submitting.value = false
  }
}

const viewKeyDetails = (key: any) => {
  selectedKey.value = key
  detailDialogVisible.value = true
}

const copyKey = async (key: any) => {
  try {
    await navigator.clipboard.writeText(key.key_preview)
    ElMessage.success('密钥已复制到剪贴板')
  } catch (error) {
    ElMessage.error('复制失败，请手动复制')
  }
}

const copyNewKey = async () => {
  try {
    await navigator.clipboard.writeText(newApiKey.value)
    ElMessage.success('密钥已复制到剪贴板')
  } catch (error) {
    ElMessage.error('复制失败，请手动复制')
  }
}

const regenerateKey = async (key: any) => {
  try {
    await ElMessageBox.confirm(
      '重新生成密钥后，旧密钥将立即失效。确定要继续吗？',
      '重新生成密钥',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    // 这里应该调用实际的API重新生成密钥
    key.key_preview = `ak_${Date.now().toString(36)}_${'*'.repeat(8)}`
    
    // 显示新密钥
    newApiKey.value = `ak_${Date.now().toString(36)}_${'b'.repeat(32)}`
    newKeyDialogVisible.value = true
    
    ElMessage.success('密钥重新生成成功')
  } catch (error: any) {
    if (error !== 'cancel') {
      ElMessage.error('重新生成失败，请稍后重试')
    }
  }
}

const toggleKeyStatus = async (key: any) => {
  const action = key.status === 'active' ? '禁用' : '启用'
  
  try {
    await ElMessageBox.confirm(
      `确定要${action}密钥 "${key.name}" 吗？`,
      `${action}密钥`,
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    // 这里应该调用实际的API
    key.status = key.status === 'active' ? 'disabled' : 'active'
    
    ElMessage.success(`密钥已${action}`)
    loadApiKeys()
  } catch (error: any) {
    if (error !== 'cancel') {
      ElMessage.error(`${action}失败，请稍后重试`)
    }
  }
}

const deleteKey = async (key: any) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除密钥 "${key.name}" 吗？此操作不可撤销。`,
      '删除密钥',
      {
        confirmButtonText: '确定删除',
        cancelButtonText: '取消',
        type: 'error'
      }
    )
    
    // 这里应该调用实际的API
    const index = apiKeys.value.findIndex(k => k.id === key.id)
    if (index > -1) {
      apiKeys.value.splice(index, 1)
    }
    
    ElMessage.success('密钥已删除')
    loadApiKeys()
  } catch (error: any) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败，请稍后重试')
    }
  }
}

const loadApiKeys = async () => {
  loading.value = true
  try {
    // 这里应该调用实际的API加载数据
    await new Promise(resolve => setTimeout(resolve, 500))
    
    // 更新统计数据
    stats.total = apiKeys.value.length
    stats.active = apiKeys.value.filter(k => k.status === 'active').length
    stats.expired = apiKeys.value.filter(k => k.status === 'expired').length
    stats.totalRequests = apiKeys.value.reduce((sum, k) => sum + k.request_count, 0)
  } catch (error) {
    console.error('加载API密钥失败:', error)
    ElMessage.error('加载失败，请稍后重试')
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  loadApiKeys()
})
</script>

<style lang="scss" scoped>
.api-keys-page {
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
      .stat-content {
        display: flex;
        align-items: center;
        gap: 16px;
        
        .stat-icon {
          width: 48px;
          height: 48px;
          border-radius: 8px;
          display: flex;
          align-items: center;
          justify-content: center;
          
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
          
          &.expired {
            background: linear-gradient(135deg, #ffecd2 0%, #fcb69f 100%);
          }
          
          &.requests {
            background: linear-gradient(135deg, #a8edea 0%, #fed6e3 100%);
          }
        }
        
        .stat-info {
          .stat-value {
            font-size: 24px;
            font-weight: 600;
            color: var(--el-text-color-primary);
            margin-bottom: 4px;
          }
          
          .stat-label {
            font-size: 14px;
            color: var(--el-text-color-secondary);
          }
        }
      }
    }
  }
  
  .filter-section {
    margin-bottom: 20px;
    
    .filter-row {
      align-items: center;
    }
  }
  
  .api-keys-list {
    .list-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 20px;
      
      h3 {
        font-size: 18px;
        font-weight: 600;
        color: var(--el-text-color-primary);
        margin: 0;
      }
    }
    
    .table-view {
      .key-name {
        strong {
          display: block;
          margin-bottom: 4px;
        }
        
        .key-description {
          font-size: 12px;
          color: var(--el-text-color-secondary);
        }
      }
      
      .key-preview {
        display: flex;
        align-items: center;
        gap: 8px;
        
        code {
          background: var(--el-fill-color-light);
          padding: 4px 8px;
          border-radius: 4px;
          font-family: 'Courier New', monospace;
          font-size: 12px;
        }
        
        .copy-btn {
          padding: 4px;
        }
      }
      
      .action-buttons {
        display: flex;
        gap: 8px;
        flex-wrap: wrap;
      }
    }
    
    .card-view {
      .api-key-card {
        margin-bottom: 20px;
        
        .card-header {
          display: flex;
          justify-content: space-between;
          align-items: flex-start;
          margin-bottom: 16px;
          
          .key-info {
            flex: 1;
            
            .key-name {
              font-size: 16px;
              font-weight: 600;
              color: var(--el-text-color-primary);
              margin: 0 0 8px 0;
            }
            
            .key-description {
              font-size: 12px;
              color: var(--el-text-color-secondary);
              margin: 0;
            }
          }
        }
        
        .card-content {
          margin-bottom: 16px;
          
          .key-preview {
            margin-bottom: 12px;
            
            label {
              display: block;
              font-size: 12px;
              color: var(--el-text-color-secondary);
              margin-bottom: 4px;
            }
            
            .key-value {
              display: flex;
              align-items: center;
              gap: 8px;
              
              code {
                background: var(--el-fill-color-light);
                padding: 4px 8px;
                border-radius: 4px;
                font-family: 'Courier New', monospace;
                font-size: 12px;
                flex: 1;
              }
            }
          }
          
          .key-meta {
            .meta-item {
              display: flex;
              justify-content: space-between;
              align-items: center;
              margin-bottom: 8px;
              
              &:last-child {
                margin-bottom: 0;
              }
              
              label {
                font-size: 12px;
                color: var(--el-text-color-secondary);
              }
              
              span {
                font-size: 12px;
                color: var(--el-text-color-primary);
              }
            }
          }
        }
        
        .card-actions {
          display: flex;
          justify-content: space-between;
          align-items: center;
        }
      }
    }
    
    .pagination-wrapper {
      margin-top: 20px;
      text-align: center;
    }
  }
  
  .form-tip {
    font-size: 12px;
    color: var(--el-text-color-secondary);
    margin-top: 4px;
    
    p {
      margin: 2px 0;
    }
  }
  
  .key-details {
    .usage-chart {
      h4 {
        font-size: 16px;
        font-weight: 600;
        color: var(--el-text-color-primary);
        margin: 0 0 16px 0;
      }
      
      .chart-placeholder {
        height: 200px;
        display: flex;
        align-items: center;
        justify-content: center;
        background: var(--el-fill-color-lighter);
        border-radius: 6px;
      }
    }
  }
  
  .new-key-content {
    .key-display {
      margin: 20px 0;
      
      label {
        display: block;
        font-weight: 600;
        margin-bottom: 8px;
      }
    }
    
    .usage-example {
      margin-top: 20px;
      
      h4 {
        font-size: 16px;
        font-weight: 600;
        color: var(--el-text-color-primary);
        margin: 0 0 16px 0;
      }
      
      pre {
        background: var(--el-fill-color-light);
        padding: 12px;
        border-radius: 6px;
        overflow-x: auto;
        
        code {
          font-family: 'Courier New', monospace;
          font-size: 12px;
          line-height: 1.5;
        }
      }
    }
  }
}

// 响应式设计
@media (max-width: 768px) {
  .api-keys-page {
    padding: 16px;
    
    .page-header {
      .header-content {
        flex-direction: column;
        gap: 16px;
        
        .header-right {
          align-self: stretch;
          
          .el-button {
            flex: 1;
          }
        }
      }
    }
    
    .filter-section {
      .filter-row {
        .el-col {
          margin-bottom: 12px;
          
          &:last-child {
            margin-bottom: 0;
          }
        }
      }
    }
    
    .api-keys-list {
      .table-view {
        .action-buttons {
          flex-direction: column;
          
          .el-button {
            width: 100%;
          }
        }
      }
    }
  }
}

// 暗色主题
.dark {
  .api-keys-page {
    .new-key-content {
      .usage-example {
        pre {
          background: var(--el-fill-color-dark);
        }
      }
    }
  }
}

// 危险操作样式
:deep(.danger-item) {
  color: var(--el-color-danger) !important;
}
</style>