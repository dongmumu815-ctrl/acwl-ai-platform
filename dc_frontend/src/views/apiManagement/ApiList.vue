<template>
  <div class="api-management">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="header-content">
        <div class="header-left">
          <h1 class="page-title">
            <el-icon><Connection /></el-icon>
            API管理
          </h1>
          <p class="page-description">管理自定义API接口配置和调用统计</p>
        </div>
        <div class="header-right">
          <el-button type="primary" @click="showCreateDialog">
            <el-icon><Plus /></el-icon>
            创建API
          </el-button>
          <el-button @click="loadApis">
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
              <el-icon><Connection /></el-icon>
            </div>
            <div class="stat-content">
              <div class="stat-value">{{ apiStats.total }}</div>
              <div class="stat-label">总API数</div>
            </div>
          </div>
        </el-col>
        
        <el-col :xs="12" :sm="6">
          <div class="stat-card">
            <div class="stat-icon active">
              <el-icon><CircleCheck /></el-icon>
            </div>
            <div class="stat-content">
              <div class="stat-value">{{ apiStats.active }}</div>
              <div class="stat-label">激活API</div>
            </div>
          </div>
        </el-col>
        
        <el-col :xs="12" :sm="6">
          <div class="stat-card">
            <div class="stat-icon api-calls">
              <el-icon><DataLine /></el-icon>
            </div>
            <div class="stat-content">
              <div class="stat-value">{{ formatNumber(apiStats.totalCalls) }}</div>
              <div class="stat-label">总调用次数</div>
            </div>
          </div>
        </el-col>
        
        <el-col :xs="12" :sm="6">
          <div class="stat-card">
            <div class="stat-icon recent">
              <el-icon><Clock /></el-icon>
            </div>
            <div class="stat-content">
              <div class="stat-value">{{ apiStats.recentActive }}</div>
              <div class="stat-label">近期活跃</div>
            </div>
          </div>
        </el-col>
      </el-row>
    </div>

    <!-- 搜索和筛选 -->
    <div class="filter-section">
      <el-card shadow="never">
        <el-form inline>
          <el-form-item label="搜索">
            <el-input
              v-model="searchQuery"
              placeholder="搜索API名称或代码"
              clearable
              style="width: 280px"
              @input="handleSearch"
            >
              <template #prefix>
                <el-icon><Search /></el-icon>
              </template>
            </el-input>
          </el-form-item>
          
          <el-form-item label="客户">
            <el-select
              v-model="customerFilter"
              placeholder="按客户筛选"
              clearable
              filterable
              style="width: 200px"
              @change="handleSearch"
            >
              <el-option label="全部" value="" />
              <el-option
                v-for="customer in customers"
                :key="customer.id"
                :label="`${customer.name} (${customer.company || ''})`"
                :value="customer.id"
              />
            </el-select>
          </el-form-item>
          
          <el-form-item label="状态">
            <el-select
              v-model="statusFilter"
              placeholder="状态筛选"
              clearable
              style="width: 120px"
              @change="handleSearch"
            >
              <el-option label="全部" value="" />
              <el-option label="激活" value="true" />
              <el-option label="禁用" value="false" />
            </el-select>
          </el-form-item>
          
          <el-form-item label="方法">
            <el-select
              v-model="methodFilter"
              placeholder="请求方法"
              clearable
              style="width: 120px"
              @change="handleSearch"
            >
              <el-option label="全部" value="" />
              <el-option label="GET" value="GET" />
              <el-option label="POST" value="POST" />
              <el-option label="PUT" value="PUT" />
              <el-option label="DELETE" value="DELETE" />
            </el-select>
          </el-form-item>
        </el-form>
      </el-card>
    </div>

    <!-- 列表/卡片视图 -->
    <div class="page-card" v-if="viewMode === 'list'">
      <el-card shadow="never">
        <template #header>
          <div class="card-header">
            <span>API列表</span>
            <div class="header-actions">
              <span class="total-count">共 {{ filteredApis.length }} 条记录</span>
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

        <el-table
          :data="filteredApis"
          v-loading="loading"
          style="width: 100%"
          @sort-change="handleSortChange"
          stripe
          :header-cell-style="{ background: '#f8f9fa', color: '#606266' }"
        >
          <el-table-column prop="id" label="ID" min-width="80" sortable />
          <el-table-column prop="api_name" label="API名称" min-width="180" sortable>
            <template #default="{ row }">
              <div class="api-name-cell">
                <el-tag :type="getMethodTagType(row.http_method)" size="small">{{ row.http_method }}</el-tag>
                <span class="api-name">{{ row.api_name }}</span>
                <span class="api-code">{{ row.api_code }}</span>
              </div>
            </template>
          </el-table-column>
          <el-table-column prop="customer.name" label="客户" min-width="140">
            <template #default="{ row }">
              {{ row.customer?.name || '-' }}
            </template>
          </el-table-column>
          <el-table-column prop="endpoint_url" label="接口地址" min-width="220" show-overflow-tooltip />
          <el-table-column label="格式" min-width="160">
            <template #default="{ row }">
              <div class="format-tags">
                <el-tag size="small" type="success">RES: {{ row.response_format.toUpperCase() }}</el-tag>
              </div>
            </template>
          </el-table-column>
          <el-table-column prop="total_calls" label="调用次数" min-width="120" sortable>
            <template #default="{ row }">
              <div class="api-stats">
                <div class="stats-number">{{ formatNumber(row.total_calls || 0) }}</div>
                <div class="stats-label">总调用</div>
              </div>
            </template>
          </el-table-column>
          <el-table-column prop="last_called_at" label="最后调用" min-width="160">
            <template #default="{ row }">
              <div class="last-active">
                <div class="active-time">{{ row.last_called_at ? formatDate(row.last_called_at) : '从未调用' }}</div>
              </div>
            </template>
          </el-table-column>
          <el-table-column prop="is_active" label="状态" min-width="100">
            <template #default="{ row }">
              <el-tag 
                :type="row.is_active ? 'success' : 'danger'" 
                effect="light"
                size="small"
              >
                {{ row.is_active ? '激活' : '禁用' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="created_at" label="创建时间" min-width="160" sortable>
            <template #default="{ row }">
              <div class="create-time">
                <div class="time-date">{{ formatDate(row.created_at) }}</div>
              </div>
            </template>
          </el-table-column>
          <el-table-column label="操作" min-width="428" fixed="right">
            <template #default="{ row }">
              <div class="action-buttons">
                <el-button size="small" type="primary" @click="showEditDialog(row)">
                  <el-icon><Edit /></el-icon>
                  编辑
                </el-button>
                <el-button size="small" type="info" @click="manageFields(row)">
                  <el-icon><Setting /></el-icon>
                  字段
                </el-button>
                <el-button size="small" type="success" @click="testApi(row)">
                  <el-icon><VideoPlay /></el-icon>
                  测试
                </el-button>
                <el-button size="small" @click="viewLogs(row)">
                  <el-icon><View /></el-icon>
                  查看日志
                </el-button>
                <el-dropdown @command="(command) => handleDocumentCommand(command, row)" size="small">
                  <el-button size="small" type="info">
                    <el-icon><Document /></el-icon>
                    文档
                    <el-icon class="el-icon--right"><ArrowDown /></el-icon>
                  </el-button>
                  <template #dropdown>
                    <el-dropdown-menu>
                      <el-dropdown-item command="markdown">
                        <el-icon><Document /></el-icon>
                        Markdown文档
                      </el-dropdown-item>
                      <el-dropdown-item command="json">
                        <el-icon><DataBoard /></el-icon>
                        JSON文档
                      </el-dropdown-item>
                    </el-dropdown-menu>
                  </template>
                </el-dropdown>
                <el-button size="small" type="warning" @click="copyApi(row)">
                  <el-icon><CopyDocument /></el-icon>
                  复制
                </el-button>
                <el-button size="small" type="danger" @click="deleteApi(row)">
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
            :total="pagination.total"
            :page-sizes="[10, 20, 50, 100]"
            layout="total, sizes, prev, pager, next, jumper"
            @size-change="handleSizeChange"
            @current-change="handleCurrentChange"
          />
        </div>
      </el-card>
    </div>

    <div class="page-card" v-else>
      <el-card shadow="never">
        <template #header>
          <div class="card-header">
            <span>API列表</span>
            <div class="header-actions">
              <span class="total-count">共 {{ filteredApis.length }} 条记录</span>
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

        <div class="grid-view">
          <el-row :gutter="20">
            <el-col
              v-for="api in filteredApis"
              :key="api.id"
              :xs="24"
              :sm="12"
              :md="8"
              :lg="6"
            >
              <div class="api-card">
                <div class="api-card-header">
                  <div class="api-method">
                    <el-tag :type="getMethodTagType(api.http_method)" size="small" effect="light">
                      {{ api.http_method }}
                    </el-tag>
                  </div>
                  <div class="api-status">
                    <el-tag :type="api.is_active ? 'success' : 'danger'" size="small" effect="light">
                      {{ api.is_active ? '激活' : '禁用' }}
                    </el-tag>
                  </div>
                </div>
                
                <div class="api-card-content">
                  <h3 class="api-name">{{ api.api_name }}</h3>
                  <p class="api-code">{{ api.api_code }}</p>
                  <p class="api-endpoint" v-if="api.endpoint_url">{{ api.endpoint_url }}</p>
                  
                  <div class="api-meta">
                    <div class="meta-item">
                      <span class="config-label">客户:</span>
                      <span>{{ api.customer?.name || '-' }}</span>
                    </div>
                    <div class="meta-item">
                      <span class="config-label">响应:</span>
                      <el-tag size="small" type="success">{{ api.response_format.toUpperCase() }}</el-tag>
                    </div>
                  </div>
                  
                  <div class="api-activity">
                    <div class="meta-item">
                      <el-icon><DataLine /></el-icon>
                      <span>{{ formatNumber(api.total_calls || 0) }} 次调用</span>
                    </div>
                    <div class="meta-item" v-if="api.last_called_at">
                      <el-icon><Clock /></el-icon>
                      <span>最后调用: {{ formatDate(api.last_called_at) }}</span>
                    </div>
                  </div>
                </div>
                
                <div class="api-card-actions">
                  <el-button size="small" type="primary" @click="showEditDialog(api)">
                    <el-icon><Edit /></el-icon>
                    编辑
                  </el-button>
                  <el-dropdown trigger="click">
                    <el-button size="small" text>
                      <el-icon><MoreFilled /></el-icon>
                    </el-button>
                    <template #dropdown>
                      <el-dropdown-menu>
                        <el-dropdown-item @click="manageFields(api)">
                          <el-icon><Setting /></el-icon>
                          字段
                        </el-dropdown-item>
                        <el-dropdown-item @click="testApi(api)">
                          <el-icon><VideoPlay /></el-icon>
                          测试
                        </el-dropdown-item>
                        <el-dropdown-item @click="viewLogs(api)">
                          <el-icon><View /></el-icon>
                          日志
                        </el-dropdown-item>
                        <el-dropdown-item @click="copyApi(api)">
                          <el-icon><CopyDocument /></el-icon>
                          复制
                        </el-dropdown-item>
                        <el-dropdown-item divided @click="deleteApi(api)">
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

      <!-- 分页 -->
      <div class="pagination-wrapper">
        <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.pageSize"
          :total="pagination.total"
          :page-sizes="[10, 20, 50, 100]"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="handleSizeChange"
          @current-change="handleCurrentChange"
        />
      </div>
      </el-card>
    </div>

    <!-- 创建/编辑API对话框 -->
    <el-dialog
      v-model="dialogVisible"
      :title="isEdit ? '编辑API' : '创建API'"
      width="700px"
      @close="resetForm"
    >
      <el-form
        ref="formRef"
        :model="form"
        :rules="formRules"
        label-width="120px"
      >
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="API名称" prop="api_name">
              <el-input v-model="form.api_name" placeholder="请输入API名称" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="API代码" prop="api_code">
              <el-input v-model="form.api_code" placeholder="请输入API代码" />
            </el-form-item>
          </el-col>
        </el-row>
        
        <el-form-item label="所属客户" prop="customer_id">
          <el-select
            v-model="form.customer_id"
            placeholder="请选择客户"
            style="width: 100%"
            filterable
          >
            <el-option
              v-for="customer in customers"
              :key="customer.id"
              :label="`${customer.name} (${customer.company || ''})`"
              :value="customer.id"
            />
          </el-select>
        </el-form-item>
        
        <el-form-item label="资源类型" prop="resource_type_id">
          <el-select
            v-model="form.resource_type_id"
            placeholder="请选择资源类型"
            style="width: 100%"
            filterable
            clearable
          >
            <el-option
              v-for="resourceType in resourceTypes"
              :key="resourceType.id"
              :label="resourceType.name"
              :value="String(resourceType.id)"
            >
              <div style="display: flex; justify-content: space-between;">
                <span>{{ resourceType.name }}</span>
                <span style="color: #8492a6; font-size: 13px;">{{ resourceType.describe }}</span>
              </div>
            </el-option>
          </el-select>
        </el-form-item>
        
        <el-form-item label="描述" prop="api_description">
          <el-input
            v-model="form.api_description"
            type="textarea"
            :rows="3"
            placeholder="请输入API描述"
          />
        </el-form-item>
        
        <el-row :gutter="20">
          <el-col :span="8">
            <el-form-item label="请求方法" prop="http_method">
              <el-select v-model="form.http_method" style="width: 100%" disabled>
                <el-option label="GET" value="GET" />
                <el-option label="POST" value="POST" />
                <el-option label="PUT" value="PUT" />
                <el-option label="DELETE" value="DELETE" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="响应格式" prop="response_format">
              <el-select v-model="form.response_format" style="width: 100%">
                <el-option label="JSON" value="json" />
                <el-option label="XML" value="xml" />
                <el-option label="Text" value="text" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>
        
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

    <!-- 复制API对话框 -->
    <el-dialog
      v-model="copyDialogVisible"
      title="复制API"
      width="600px"
    >
      <div v-if="selectedApi">
        <el-alert
          title="复制说明"
          type="info"
          :closable="false"
          style="margin-bottom: 20px;"
        >
          <template #default>
            <p>将复制API "{{ selectedApi.api_name }}" 的所有配置和字段定义到指定客户。</p>
            <p>复制后的API将拥有独立的配置，修改不会影响原API。</p>
          </template>
        </el-alert>
        
        <el-form
          ref="copyFormRef"
          :model="copyForm"
          :rules="copyFormRules"
          label-width="120px"
        >
          <el-form-item label="目标客户" prop="target_customer_id">
            <el-select 
              v-model="copyForm.target_customer_id" 
              placeholder="请选择目标客户"
              style="width: 100%;"
              filterable
              :loading="customersLoading"
            >
              <el-option
                v-for="customer in customers"
                :key="customer.id"
                :label="`${customer.name} (${customer.company || ''})`"
                :value="customer.id"
              />
            </el-select>
          </el-form-item>
          
          <el-form-item label="新API代码" prop="new_api_code">
            <el-input 
              v-model="copyForm.new_api_code" 
              placeholder="请输入新的API代码，如：user_list_v2"
            />
            <div style="font-size: 12px; color: #909399; margin-top: 4px;">
              💡 API代码必须以字母开头，只能包含字母、数字、下划线，长度3-50字符
            </div>
          </el-form-item>
          
          <el-form-item label="新API名称" prop="new_api_name">
            <el-input 
              v-model="copyForm.new_api_name" 
              placeholder="请输入新的API名称"
            />
          </el-form-item>
        </el-form>
      </div>

      <template #footer>
        <div class="dialog-footer">
          <el-button @click="copyDialogVisible = false">取消</el-button>
          <el-button type="primary" @click="submitCopy" :loading="copying">
            {{ copying ? '复制中...' : '确定复制' }}
          </el-button>
        </div>
      </template>
    </el-dialog>

    <!-- Markdown文档预览对话框 -->
    <el-dialog
      v-model="markdownDialogVisible"
      :title="`${currentApiItem?.api_name || ''} - Markdown文档`"
      width="80%"
      top="5vh"
    >
      <div class="document-preview">
        <div class="document-actions">
          <el-button 
            size="small" 
            type="primary" 
            @click="copyToClipboard(markdownContent, 'Markdown')"
          >
            <el-icon><CopyDocument /></el-icon>
            复制内容
          </el-button>
          <el-button 
            size="small" 
            type="success" 
            @click="downloadDocument(markdownContent, `${currentApiItem?.api_code || 'api'}_doc.md`, 'markdown')"
          >
            <el-icon><Download /></el-icon>
            下载文档
          </el-button>
        </div>
        
        <div class="markdown-preview">
          <el-scrollbar height="500px">
            <div class="markdown-content" v-html="renderMarkdown(markdownContent)"></div>
          </el-scrollbar>
        </div>
        
        <!-- 隐藏的textarea用于复制 -->
        <textarea 
          ref="markdownTextarea" 
          v-model="markdownContent" 
          style="position: absolute; left: -9999px; opacity: 0;"
        ></textarea>
      </div>
    </el-dialog>

    <!-- JSON文档预览对话框 -->
    <el-dialog
      v-model="jsonDialogVisible"
      :title="`${currentApiItem?.api_name || ''} - JSON文档`"
      width="80%"
      top="5vh"
    >
      <div class="document-preview">
        <div class="document-actions">
          <el-button 
            size="small" 
            type="primary" 
            @click="copyToClipboard(jsonContent, 'JSON')"
          >
            <el-icon><CopyDocument /></el-icon>
            复制内容
          </el-button>
          <el-button 
            size="small" 
            type="success" 
            @click="downloadDocument(jsonContent, `${currentApiItem?.api_code || 'api'}_openapi.json`, 'json')"
          >
            <el-icon><Download /></el-icon>
            下载文档
          </el-button>
          <el-button 
            size="small" 
            type="info" 
            @click="openSwaggerUI()"
          >
            <el-icon><View /></el-icon>
            Swagger UI
          </el-button>
        </div>
        
        <div class="json-preview">
          <el-scrollbar height="500px">
            <pre class="json-content">{{ jsonContent }}</pre>
          </el-scrollbar>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import type { FormInstance, FormRules } from 'element-plus'
import { CopyDocument, Download, View } from '@element-plus/icons-vue'
import { marked } from 'marked'
import { formatDate } from '@/utils/date'
import {
  getApis,
  createApi,
  updateApi,
  deleteApi as deleteApiRequest,
  copyApi as copyApiRequest,
  testApiConnection,
  getResourceTypes
} from '@/api/apiManagement'
import { getCustomers } from '@/api/apiManagement'
import type { CustomApi, CustomApiCreate, CustomApiUpdate, Customer, ResourceType } from '@/types/apiManagement'

/**
 * 路由
 */
const router = useRouter()

/**
 * 响应式数据
 */
const loading = ref(false)
const apis = ref<CustomApi[]>([])
const customers = ref<Customer[]>([])
const resourceTypes = ref<ResourceType[]>([])
const searchQuery = ref('')
const customerFilter = ref<number | ''>('')
const statusFilter = ref('')
const methodFilter = ref('')
const viewMode = ref<'grid' | 'list'>('list')
const dialogVisible = ref(false)
const copyDialogVisible = ref(false)
const isEdit = ref(false)
const submitting = ref(false)
const copying = ref(false)
const customersLoading = ref(false)
const selectedApi = ref<CustomApi | null>(null)
const formRef = ref<FormInstance>()
const copyFormRef = ref<FormInstance>()

// 分页数据
const pagination = reactive({
  page: 1,
  pageSize: 20,
  total: 0
})

// 表单数据
const form = reactive<CustomApiCreate & { is_active?: boolean; id?: number }>({
  customer_id: undefined as any,
  api_name: '',
  api_code: '',
  api_description: '',
  http_method: 'POST',
  response_format: 'json',
  resource_type_id: undefined as any,
  is_active: true
})

// 复制表单数据
const copyForm = reactive({
  target_customer_id: '',
  new_api_code: '',
  new_api_name: '',
  sourceId: 0
})

// 表单验证规则
const formRules: FormRules = {
  api_name: [
    { required: true, message: '请输入API名称', trigger: 'blur' },
    { min: 2, max: 50, message: '长度在 2 到 50 个字符', trigger: 'blur' }
  ],
  api_code: [
    { required: true, message: '请输入API代码', trigger: 'blur' },
    { min: 2, max: 30, message: '长度在 2 到 30 个字符', trigger: 'blur' },
    { pattern: /^[a-zA-Z0-9_]+$/, message: '只能包含字母、数字和下划线', trigger: 'blur' }
  ],
  customer_id: [
    { required: true, message: '请选择客户', trigger: 'change' },
    { 
      validator: (rule: any, value: any, callback: any) => {
        if (value === undefined || value === null || value === '' || value === 0) {
          callback(new Error('请选择客户'))
        } else {
          callback()
        }
      }, 
      trigger: 'change' 
    }
  ],
  http_method: [
    { required: true, message: '请选择请求方法', trigger: 'change' }
  ]
}

// 复制表单验证规则
const copyFormRules: FormRules = {
  target_customer_id: [
    { required: true, message: '请选择目标客户', trigger: 'change' }
  ],
  new_api_code: [
    { required: true, message: '请输入新API代码', trigger: 'blur' },
    { 
      pattern: /^[a-zA-Z][a-zA-Z0-9_]{2,49}$/, 
      message: 'API代码必须以字母开头，只能包含字母、数字、下划线，长度3-50字符', 
      trigger: 'blur' 
    }
  ],
  new_api_name: [
    { required: true, message: '请输入新API名称', trigger: 'blur' }
  ]
}

/**
 * 计算属性
 */
const filteredApis = computed(() => {
  let result = apis.value

  // 搜索过滤
  if (searchQuery.value) {
    const query = searchQuery.value.toLowerCase()
    result = result.filter(api =>
      api.api_name.toLowerCase().includes(query) ||
      api.api_code.toLowerCase().includes(query)
    )
  }

  // 客户过滤
  if (customerFilter.value) {
    result = result.filter(api => api.customer_id === customerFilter.value)
  }

  // 状态过滤
  if (statusFilter.value !== '') {
    const isActive = statusFilter.value === 'true'
    result = result.filter(api => api.is_active === isActive)
  }

  // 方法过滤
  if (methodFilter.value) {
    result = result.filter(api => api.http_method === methodFilter.value)
  }

  return result
})

// 统计数据
const apiStats = computed(() => {
  const total = apis.value.length
  const active = apis.value.filter(a => a.is_active).length
  const totalCalls = apis.value.reduce((sum, a) => sum + (a.total_calls || 0), 0)
  const thirtyDaysAgo = new Date()
  thirtyDaysAgo.setDate(thirtyDaysAgo.getDate() - 30)
  const recentActive = apis.value.filter(a => 
    a.last_called_at && new Date(a.last_called_at) > thirtyDaysAgo
  ).length
  return { total, active, totalCalls, recentActive }
})

/**
 * 生命周期钩子
 */
onMounted(() => {
  loadApis()
  loadCustomers()
})

/**
 * 方法定义
 */

/**
 * 加载API列表
 */
const loadApis = async () => {
  try {
    loading.value = true
    const response = await getApis({
      page: pagination.page,
      page_size: pagination.pageSize
    })

    if (response.success) {
      apis.value = response.data.items
      pagination.total = response.data.total
    } else {
      ElMessage.error(response.message || '加载API列表失败')
    }
  } catch (error) {
    console.error('加载API列表失败:', error)
    ElMessage.error('加载API列表失败')
  } finally {
    loading.value = false
  }
}

/**
 * 加载客户列表
 */
const loadCustomers = async () => {
  customersLoading.value = true
  try {
    const response = await getCustomers({ page_size: 1000 })
    if (response.success) {
      customers.value = response.data.items
    }
  } catch (error) {
    console.error('加载客户列表失败:', error)
  } finally {
    customersLoading.value = false
  }
}

/**
 * 加载资源类型列表
 */
const loadResourceTypes = async () => {
  try {
    const response = await getResourceTypes()
    if (response.success) {
      resourceTypes.value = response.data.resource_types
    }
  } catch (error) {
    console.error('加载资源类型列表失败:', error)
  }
}

/**
 * 获取请求方法标签类型
 */
const getMethodTagType = (
  method: string
): 'success' | 'primary' | 'warning' | 'danger' | 'info' => {
  const types: Record<string, 'success' | 'primary' | 'warning' | 'danger' | 'info'> = {
    GET: 'success',
    POST: 'primary',
    PUT: 'warning',
    DELETE: 'danger'
  }
  return types[method] || 'info'
}

/**
 * 格式化数字
 */
const formatNumber = (num: number): string => {
  return (num || 0).toLocaleString()
}

/**
 * 显示创建对话框
 */
const showCreateDialog = () => {
  isEdit.value = false
  dialogVisible.value = true
  resetForm()
  loadResourceTypes() // 加载资源类型列表
}

/**
 * 显示编辑对话框
 */
const showEditDialog = (api: CustomApi) => {
  isEdit.value = true
  dialogVisible.value = true
  loadResourceTypes() // 加载资源类型列表
  
  // 填充表单数据
  Object.assign(form, {
    customer_id: api.customer_id,
    api_name: api.api_name,
    api_code: api.api_code,
    api_description: api.description || '', // 使用后端返回的description字段
    http_method: api.http_method,
    response_format: api.response_format,
    // 资源类型ID统一为字符串，避免选择器匹配失败
    resource_type_id: api.resource_type_id != null ? String(api.resource_type_id) : undefined,
    is_active: api.is_active
  })
  
  form.id = api.id
}

/**
 * 重置表单
 */
const resetForm = () => {
  if (formRef.value) {
    formRef.value.resetFields()
  }
  
  Object.assign(form, {
    customer_id: undefined as any,
    api_name: '',
    api_code: '',
    api_description: '',
    http_method: 'POST',
    response_format: 'json',
    resource_type_id: undefined as any,
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
      // 更新API
      const updateData: CustomApiUpdate = {
        api_name: form.api_name,
        api_description: form.api_description,
        http_method: form.http_method,
        response_format: form.response_format,
        resource_type_id: form.resource_type_id,
        is_active: form.is_active
      }

      const response = await updateApi(form.id, updateData)
      if (response.success) {
        ElMessage.success('API更新成功')
        dialogVisible.value = false
        loadApis()
      } else {
        ElMessage.error(response.message || 'API更新失败')
      }
    } else {
      // 创建API - 验证必填字段
      if (!form.customer_id || form.customer_id === 0) {
        ElMessage.error('请选择客户')
        return
      }

      const createData: CustomApiCreate = {
        customer_id: form.customer_id,
        api_name: form.api_name,
        api_code: form.api_code,
        api_description: form.api_description,
        http_method: form.http_method,
        response_format: form.response_format,
        resource_type_id: form.resource_type_id
      }

      console.log('创建API数据:', createData)
      const response = await createApi(createData)
      if (response.success) {
        ElMessage.success('API创建成功')
        dialogVisible.value = false
        loadApis()
      } else {
        ElMessage.error(response.message || 'API创建失败')
      }
    }
  } catch (error) {
    console.error('提交表单失败:', error)
  } finally {
    submitting.value = false
  }
}

/**
 * 管理API字段
 */
const manageFields = (api: CustomApi) => {
  router.push(`/api-management/apis/${api.id}/fields`)
}

const viewLogs = (api: CustomApi) => {
  router.push(`/api-management/apis/${api.id}/logs`)
}
/**
 * 测试API
 */
const testApi = async (api: CustomApi) => {
  try {
    const response = await testApiConnection(api.id)
    if (response.success) {
      const result = response.data
      ElMessage.success(`测试成功！响应时间: ${result.response_time}ms`)
    } else {
      ElMessage.error(response.message || 'API测试失败')
    }
  } catch (error) {
    console.error('API测试失败:', error)
    ElMessage.error('API测试失败')
  }
}

/**
 * 复制API
 */
const copyApi = async (api: CustomApi) => {
  selectedApi.value = api
  
  // 重置复制表单
  copyForm.target_customer_id = ''
  copyForm.new_api_code = `${api.api_code}_copy`
  copyForm.new_api_name = `${api.api_name} - 副本`
  copyForm.sourceId = api.id
  
  // 加载客户列表
  await loadCustomers()
  
  copyDialogVisible.value = true
}

/**
 * 提交复制
 */
const submitCopy = async () => {
  if (!copyFormRef.value) return

  try {
    await copyFormRef.value.validate()
    copying.value = true

    const response = await copyApiRequest(copyForm.sourceId, {
      target_customer_id: copyForm.target_customer_id,
      new_api_code: copyForm.new_api_code,
      new_api_name: copyForm.new_api_name
    })

    ElMessage.success('API复制成功')
    copyDialogVisible.value = false
    loadApis()
  } catch (error) {
    console.error('API复制失败:', error)
    const errorMessage = error.response?.data?.detail || 'API复制失败'
    ElMessage.error(errorMessage)
  } finally {
    copying.value = false
  }
}

/**
 * 删除API
 */
const deleteApi = async (api: CustomApi) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除API "${api.api_name}" 吗？此操作不可恢复。`,
      '确认删除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )

    const response = await deleteApiRequest(api.id)
    if (response.success) {
      ElMessage.success('API删除成功')
      loadApis()
    } else {
      ElMessage.error(response.message || 'API删除失败')
    }
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除API失败:', error)
      ElMessage.error('API删除失败')
    }
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
  console.log('排序:', prop, order)
}

/**
 * 分页大小改变
 */
const handleSizeChange = (size: number) => {
  pagination.pageSize = size
  pagination.page = 1
  loadApis()
}

/**
 * 当前页改变
 */
const handleCurrentChange = (page: number) => {
  pagination.page = page
  loadApis()
}

/**
 * 文档生成相关数据
 */
const markdownDialogVisible = ref(false)
const jsonDialogVisible = ref(false)
const markdownContent = ref('')
const jsonContent = ref('')
const currentApiItem = ref<CustomApi | null>(null)

/**
 * 处理文档生成命令
 */
const handleDocumentCommand = async (command: string, apiItem: CustomApi) => {
  currentApiItem.value = apiItem
  
  try {
    if (command === 'markdown') {
      await generateMarkdownDoc(apiItem)
    } else if (command === 'json') {
      await generateJsonDoc(apiItem)
    }
  } catch (error) {
    console.error('生成文档失败:', error)
    ElMessage.error('生成文档失败')
  }
}

/**
 * 生成Markdown文档
 */
const generateMarkdownDoc = async (apiItem: CustomApi) => {
  try {
    const response = await fetch(`/api/v1/admin/apis/${apiItem.id}/documentation?format=markdown`, {
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('token')}`
      }
    })
    
    if (!response.ok) {
      throw new Error('生成Markdown文档失败')
    }
    
    const result = await response.json()
    if (result.success) {
      markdownContent.value = result.data.documentation
      markdownDialogVisible.value = true
    } else {
      throw new Error(result.message || '生成Markdown文档失败')
    }
  } catch (error) {
    console.error('生成Markdown文档失败:', error)
    ElMessage.error('生成Markdown文档失败')
  }
}

/**
 * 生成JSON文档
 */
const generateJsonDoc = async (apiItem: CustomApi) => {
  try {
    const response = await fetch(`/api/v1/admin/apis/${apiItem.id}/documentation?format=json`, {
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('token')}`
      }
    })
    
    if (!response.ok) {
      throw new Error('生成JSON文档失败')
    }
    
    const result = await response.json()
    if (result.success) {
      jsonContent.value = JSON.stringify(JSON.parse(result.data.documentation), null, 2)
      jsonDialogVisible.value = true
    } else {
      throw new Error(result.message || '生成JSON文档失败')
    }
  } catch (error) {
    console.error('生成JSON文档失败:', error)
    ElMessage.error('生成JSON文档失败')
  }
}

/**
 * 复制内容到剪贴板
 */
const copyToClipboard = async (content: string, type: string) => {
  try {
    await navigator.clipboard.writeText(content)
    ElMessage.success(`${type}内容已复制到剪贴板`)
  } catch (error) {
    console.error('复制失败:', error)
    ElMessage.error('复制失败')
  }
}

/**
  * 下载文档
  */
 const downloadDocument = (content: string, filename: string, type: string) => {
   try {
     const blob = new Blob([content], { type: `text/${type}` })
     const url = URL.createObjectURL(blob)
     const link = document.createElement('a')
     link.href = url
     link.download = filename
     document.body.appendChild(link)
     link.click()
     document.body.removeChild(link)
     URL.revokeObjectURL(url)
     ElMessage.success('文档下载成功')
   } catch (error) {
     console.error('下载失败:', error)
     ElMessage.error('下载失败')
   }
 }

 /**
  * 渲染Markdown内容
  */
 const renderMarkdown = (content: string): string => {
   if (!content) return ''
   
   try {
     // 使用marked.js进行专业的Markdown渲染
     return marked(content)
   } catch (error) {
     console.error('Markdown渲染失败:', error)
     // 降级到简单渲染
     return content
       .replace(/\n/g, '<br>')
       .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
       .replace(/\*(.*?)\*/g, '<em>$1</em>')
       .replace(/^# (.*$)/gm, '<h1>$1</h1>')
       .replace(/^## (.*$)/gm, '<h2>$1</h2>')
       .replace(/^### (.*$)/gm, '<h3>$1</h3>')
   }
 }

 /**
  * 打开Swagger UI
  */
 const openSwaggerUI = () => {
   if (!currentApiItem.value) return
   
   const token = localStorage.getItem('token')
   const url = `/api/v1/admin/apis/${currentApiItem.value.id}/docs?token=${token}`
   window.open(url, '_blank')
 }
</script>

<style scoped lang="scss">
.api-management {
  .page-header {
    margin-bottom: 20px;
    
    .header-content {
      display: flex;
      justify-content: space-between;
      align-items: center;
      
      .header-left {
        .page-title {
          display: flex;
          align-items: center;
          gap: 8px;
          margin: 0 0 8px 0;
          font-size: 24px;
          font-weight: 600;
          color: var(--el-text-color-primary);
        }
        
        .page-description {
          margin: 0;
          color: var(--el-text-color-regular);
        }
      }
      
      .header-right {
        display: flex;
        gap: 12px;
      }
    }
  }
  
  .pagination-wrapper {
    display: flex;
    justify-content: center;
    margin-top: 20px;
    padding: 20px;
  }
}

/* 统计卡片 */
.stats-cards {
  margin-bottom: 20px;
  
  .stat-card {
    display: flex;
    align-items: center;
    gap: 12px;
    background: #fff;
    border: 1px solid #ebeef5;
    border-radius: 8px;
    padding: 16px;
  }
  
  .stat-icon {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 40px;
    height: 40px;
    border-radius: 8px;
    
    &.total { background: #ecf5ff; color: #409eff; }
    &.active { background: #f0f9eb; color: #67c23a; }
    &.api-calls { background: #fdf6ec; color: #e6a23c; }
    &.recent { background: #fef0f0; color: #f56c6c; }
  }
  
  .stat-content {
    .stat-value {
      font-size: 20px;
      font-weight: 600;
      color: #303133;
    }
    .stat-label {
      font-size: 12px;
      color: #909399;
    }
  }
}

/* 筛选区域 */
.filter-section {
  margin-bottom: 20px;
}

/* 列表/卡片卡头样式对齐 CustomerList */
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

/* 列表视图样式增强 */
.api-name-cell {
  display: flex;
  align-items: center;
  gap: 8px;
}

.api-name {
  font-weight: 600;
  color: #303133;
}

.api-code {
  color: #909399;
  font-size: 12px;
}

.format-tags {
  display: flex;
  gap: 6px;
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

.action-buttons {
  display: flex;
  gap: 8px;
  align-items: center;
}

.action-buttons .el-button { margin: 0; }

/* 卡片视图样式 */
.grid-view {}

.api-card {
  border: 1px solid #ebeef5;
  border-radius: 8px;
  background: #fff;
  padding: 16px;
}

.api-card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.api-card-content {
  .api-name {
    margin: 0 0 6px 0;
    font-size: 16px;
    font-weight: 600;
    color: #303133;
  }
  .api-code {
    margin: 0 0 6px 0;
    font-size: 12px;
    color: #909399;
  }
  .api-endpoint {
    margin: 0 10px 12px 0;
    font-size: 12px;
    color: #606266;
  }
}

.api-meta {
  display: flex;
  gap: 12px;
  align-items: center;
  margin-bottom: 12px;
}

.meta-item {
  display: flex;
  gap: 6px;
  align-items: center;
  font-size: 13px;
  color: #606266;
}

.config-label {
  font-size: 12px;
  color: #909399;
}

.api-activity {
  display: flex;
  gap: 12px;
  align-items: center;
  margin-bottom: 12px;
}

.api-card-actions {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

/* 文档预览样式 */
.document-preview {
  .document-actions {
    display: flex;
    gap: 12px;
    margin-bottom: 16px;
    padding-bottom: 12px;
    border-bottom: 1px solid #ebeef5;
  }

  .markdown-preview {
    border: 1px solid #ebeef5;
    border-radius: 6px;
    background: #fafafa;
  }

  .markdown-content {
    padding: 16px;
    line-height: 1.6;
    color: #303133;

    h1, h2, h3 {
      margin: 16px 0 8px 0;
      color: #303133;
    }

    h1 {
      font-size: 24px;
      border-bottom: 2px solid #409eff;
      padding-bottom: 8px;
    }

    h2 {
      font-size: 20px;
      border-bottom: 1px solid #dcdfe6;
      padding-bottom: 6px;
    }

    h3 {
      font-size: 16px;
    }

    ul {
      margin: 8px 0;
      padding-left: 20px;
    }

    li {
      margin: 4px 0;
    }

    strong {
      color: #409eff;
      font-weight: 600;
    }

    em {
      color: #67c23a;
      font-style: italic;
    }
  }

  .json-preview {
    border: 1px solid #ebeef5;
    border-radius: 6px;
    background: #fafafa;
  }

  .json-content {
    padding: 16px;
    margin: 0;
    font-family: 'Courier New', monospace;
    font-size: 13px;
    line-height: 1.5;
    color: #303133;
    background: transparent;
    white-space: pre-wrap;
    word-wrap: break-word;
  }
}
</style>