<template>
  <div>
    <div class="page-card">
      <div class="page-header">
        <h2>API管理</h2>
        <el-button @click="loadApis">刷新</el-button>
      </div>
      
      <div class="page-content">
        <!-- 搜索栏 -->
        <div class="table-toolbar">
          <el-input
            v-model="searchQuery"
            placeholder="搜索API名称或API代码"
            style="width: 300px;"
            clearable
          >
            <template #prefix>
              <el-icon><Search /></el-icon>
            </template>
          </el-input>
          
          <el-select
            v-model="customerFilter"
            placeholder="按客户筛选"
            style="width: 250px; margin-left: 10px;"
            clearable
            filterable
            :loading="customersLoading"
          >
            <el-option
              v-for="customer in customers"
              :key="customer.id"
              :label="`${customer.name} (${customer.company})`"
              :value="customer.id"
            />
          </el-select>
          
          <el-button type="success" @click="showCreateDialog" style="margin-left: 10px;">
           <el-icon><Plus /></el-icon> 创建API
         </el-button>
        </div>
        
        <!-- API表格 -->
        <el-table
          :data="filteredApis"
          style="width: 100%"
          v-loading="loading"
        >
          <el-table-column prop="id" label="ID" width="80" />
          <el-table-column prop="name" label="API名称" width="200" />
          <el-table-column prop="endpoint" label="API代码" width="250" show-overflow-tooltip />
          <el-table-column prop="method" label="请求方法" width="100">
            <template #default="{ row }">
              <el-tag :type="getMethodTagType(row.method)">{{ row.method }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="description" label="描述" show-overflow-tooltip />
          <el-table-column prop="is_active" label="状态" width="100">
            <template #default="{ row }">
              <el-tag :type="row.is_active ? 'success' : 'danger'">
                {{ row.is_active ? '启用' : '禁用' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="created_at" label="创建时间" width="180">
            <template #default="{ row }">
              {{ formatDate(row.created_at) }}
            </template>
          </el-table-column>
          <el-table-column label="操作" width="500" fixed="right">
            <template #default="{ row }">
              <el-button size="small" @click="viewApiDetail(row)">详情</el-button>
              <el-button size="small" @click="editApi(row)">编辑</el-button>
              <el-button size="small" @click="manageFields(row)">字段管理</el-button>
              <el-button size="small" @click="toggleApiStatus(row)">
                {{ row.is_active ? '禁用' : '启用' }}
              </el-button>
              <el-button size="small" @click="viewApiLogs(row)">日志</el-button>
              <el-button size="small" @click="testApi(row)">测试</el-button>
              <el-dropdown size="small" @command="(command) => handleDocumentCommand(command, row)">
                 <el-button size="small" type="info">
                   文档 <el-icon class="el-icon--right"><ArrowDown /></el-icon>
                 </el-button>
                <template #dropdown>
                  <el-dropdown-menu>
                    <el-dropdown-item command="markdown">Markdown文档</el-dropdown-item>
                    <!--el-dropdown-item command="html">HTML文档</el-dropdown-item-->
                    <el-dropdown-item command="json">JSON文档</el-dropdown-item>
                  </el-dropdown-menu>
                </template>
              </el-dropdown>
              <el-button size="small" type="primary" @click="copyApi(row)">复制</el-button>
              <el-button size="small" type="danger" @click="deleteApi(row)">删除</el-button>
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
    
    <!-- API详情对话框 -->
    <el-dialog
      v-model="detailDialogVisible"
      title="API详情"
      width="800px"
    >
      <div v-if="selectedApi">
        <el-descriptions title="基本信息" :column="2" border>
          <el-descriptions-item label="API名称">{{ selectedApi.name }}</el-descriptions-item>
          <el-descriptions-item label="API代码">{{ selectedApi.endpoint }}</el-descriptions-item>
          <el-descriptions-item label="请求方法">
            <el-tag :type="getMethodTagType(selectedApi.method)">{{ selectedApi.method }}</el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="状态">
            <el-tag :type="selectedApi.is_active ? 'success' : 'danger'">
              {{ selectedApi.is_active ? '启用' : '禁用' }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="创建时间" :span="2">
            {{ formatDate(selectedApi.created_at) }}
          </el-descriptions-item>
          <el-descriptions-item label="描述" :span="2">
            {{ selectedApi.description || '无' }}
          </el-descriptions-item>
        </el-descriptions>
        
        <!-- 请求参数 -->
        <div style="margin-top: 20px;" v-if="selectedApi.request_schema">
          <h3>请求参数</h3>
          <el-input
            :model-value="JSON.stringify(selectedApi.request_schema, null, 2)"
            type="textarea"
            :rows="8"
            readonly
            style="font-family: monospace;"
          />
        </div>
        
        <!-- 响应格式 -->
        <div style="margin-top: 20px;" v-if="selectedApi.response_schema">
          <h3>响应格式</h3>
          <el-input
            :model-value="JSON.stringify(selectedApi.response_schema, null, 2)"
            type="textarea"
            :rows="8"
            readonly
            style="font-family: monospace;"
          />
        </div>
      </div>
    </el-dialog>
    
    <!-- API日志对话框 -->
    <el-dialog
      v-model="logsDialogVisible"
      title="API调用日志"
      width="1000px"
    >
      <div style="margin-bottom: 16px;">
        <el-button @click="loadApiLogs">刷新日志</el-button>
      </div>
      
      <el-table
        :data="apiLogs"
        style="width: 100%"
        v-loading="logsLoading"
      >
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="customer_name" label="客户" width="120" />
        <el-table-column prop="request_method" label="方法" width="80">
          <template #default="{ row }">
            <el-tag :type="getMethodTagType(row.request_method)" size="small">
              {{ row.request_method }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="request_path" label="请求路径" width="200" show-overflow-tooltip />
        <el-table-column prop="status_code" label="状态码" width="100">
          <template #default="{ row }">
            <el-tag :type="getStatusCodeTagType(row.status_code)" size="small">
              {{ row.status_code }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="response_time" label="响应时间" width="100">
          <template #default="{ row }">
            {{ row.response_time }}ms
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="调用时间" width="180">
          <template #default="{ row }">
            {{ formatDate(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column prop="error_message" label="错误信息" show-overflow-tooltip>
          <template #default="{ row }">
            {{ row.error_message || '-' }}
          </template>
        </el-table-column>
      </el-table>
      
      <!-- 日志分页 -->
      <div style="margin-top: 20px; text-align: right;">
        <el-pagination
          v-model:current-page="logsCurrentPage"
          v-model:page-size="logsPageSize"
          :page-sizes="[10, 20, 50, 100]"
          :total="logsTotal"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="handleLogsSizeChange"
          @current-change="handleLogsCurrentChange"
        />
      </div>
    </el-dialog>
    
    <!-- API创建/编辑对话框 -->
    <el-dialog
      v-model="formDialogVisible"
      :title="isEditing ? '编辑API' : '创建API'"
      width="600px"
    >
      <el-form :model="apiForm" :rules="apiFormRules" ref="apiFormRef" label-width="100px">
        <el-form-item label="所属客户" prop="customer_id">
          <el-select 
            v-model="apiForm.customer_id" 
            placeholder="请选择客户"
            style="width: 100%;"
            filterable
            :loading="customersLoading"
          >
            <el-option
              v-for="customer in customers"
              :key="customer.id"
              :label="`${customer.name} (${customer.company})`"
              :value="customer.id"
            />
          </el-select>
        </el-form-item>
        
        <el-form-item label="API名称" prop="name">
          <el-input v-model="apiForm.name" placeholder="请输入API名称" />
        </el-form-item>
        
        <el-form-item label="API代码" prop="endpoint">
          <el-input v-model="apiForm.endpoint" placeholder="请输入API代码，如：user_list（只能包含字母、数字、下划线和连字符）" />
        </el-form-item>
        
        <el-form-item label="请求方法" prop="method">
          <el-select v-model="apiForm.method" placeholder="请选择请求方法">
            <el-option label="GET" value="GET" />
            <el-option label="POST" value="POST" />
            <el-option label="PUT" value="PUT" />
            <el-option label="DELETE" value="DELETE" />
            <el-option label="PATCH" value="PATCH" />
          </el-select>
        </el-form-item>
        
        <el-form-item label="描述">
          <el-input v-model="apiForm.description" type="textarea" :rows="3" placeholder="请输入API描述" />
        </el-form-item>
        
        <el-form-item label="状态">
          <el-switch v-model="apiForm.is_active" active-text="启用" inactive-text="禁用" />
        </el-form-item>
        
        <el-form-item label="连接任务类型">
          <el-select 
            v-model="apiForm.link_read_id" 
            placeholder="请选择连接任务类型（可选）"
            style="width: 100%;"
            filterable
            clearable
            :loading="linkTypesLoading"
          >
            <el-option
              v-for="linkType in linkTypes"
              :key="linkType.id"
              :label="`${linkType.name} - ${linkType.link_menu_name}`"
              :value="linkType.id"
            />
          </el-select>
        </el-form-item>
        
        <el-form-item label="请求参数">
          <el-input
            v-model="apiForm.request_schema_str"
            type="textarea"
            :rows="6"
            placeholder="请输入JSON格式的请求参数schema（可选）"
          />
        </el-form-item>
        
        <el-form-item label="响应格式">
          <el-input
            v-model="apiForm.response_schema_str"
            type="textarea"
            :rows="6"
            placeholder="请输入JSON格式的响应schema（可选）"
          />
        </el-form-item>
      </el-form>
      
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="formDialogVisible = false">取消</el-button>
          <el-button type="primary" @click="submitApiForm" :loading="submitting">
            {{ submitting ? '保存中...' : '确定' }}
          </el-button>
        </span>
      </template>
    </el-dialog>
    
    <!-- API测试对话框 -->
    <el-dialog
      v-model="testDialogVisible"
      title="API测试"
      width="800px"
    >
      <div v-if="selectedApi">
        <el-form :model="testForm" label-width="100px">
          <el-form-item label="请求URL">
            <el-input :model-value="getTestUrl()" readonly />
          </el-form-item>
          
          <el-form-item label="请求方法">
            <el-tag :type="getMethodTagType(selectedApi.method)">{{ selectedApi.method }}</el-tag>
          </el-form-item>
          
          <el-form-item label="请求头" v-if="selectedApi.method !== 'GET'">
            <el-input
              v-model="testForm.headers"
              type="textarea"
              :rows="3"
              placeholder='{ "Content-Type": "application/json" }'
            />
            <div style="font-size: 12px; color: #909399; margin-top: 4px;">
              💡 请求头已根据API方法自动生成，您可以根据需要修改
            </div>
          </el-form-item>
          
          <el-form-item label="请求参数" v-if="selectedApi.method !== 'GET'">
            <el-input
              v-model="testForm.body"
              type="textarea"
              :rows="8"
              placeholder="请输入JSON格式的请求参数"
            />
            <div style="font-size: 12px; color: #909399; margin-top: 4px;" v-if="selectedApi.request_schema">
              💡 请求参数已根据API Schema自动生成示例数据，您可以根据需要修改
            </div>
            <div style="font-size: 12px; color: #909399; margin-top: 4px;" v-else>
              ℹ️ 该API暂无Schema定义，请手动输入请求参数
            </div>
          </el-form-item>
          
          <el-form-item>
            <el-button type="primary" @click="executeTest" :loading="testing">
              {{ testing ? '测试中...' : '发送请求' }}
            </el-button>
            <el-button @click="regenerateTestData">重新生成示例</el-button>
            <el-button @click="clearTestResult">清空结果</el-button>
          </el-form-item>
        </el-form>
        
        <!-- 测试结果 -->
        <div v-if="testResult" style="margin-top: 20px;">
          <h3>响应结果</h3>
          <el-alert
            :title="`状态码: ${testResult.status}`"
            :type="testResult.status < 400 ? 'success' : 'error'"
            style="margin-bottom: 16px;"
          />
          <el-input
            :model-value="JSON.stringify(testResult.data, null, 2)"
            type="textarea"
            :rows="12"
            readonly
            style="font-family: monospace;"
          />
        </div>
      </div>
    </el-dialog>

    <!-- API复制对话框 -->
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
            <p>将复制API "{{ selectedApi.name }}" 的所有配置和字段定义到指定客户。</p>
            <p>复制后的API将拥有独立的配置，修改不会影响原API。</p>
          </template>
        </el-alert>
        
        <el-form :model="copyForm" :rules="copyFormRules" ref="copyFormRef" label-width="120px">
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
                :label="`${customer.name} (${customer.company})`"
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
        <span class="dialog-footer">
          <el-button @click="copyDialogVisible = false">取消</el-button>
          <el-button type="primary" @click="submitCopyForm" :loading="copying">
            {{ copying ? '复制中...' : '确定复制' }}
          </el-button>
        </span>
      </template>
    </el-dialog>

    <!-- Markdown 文档预览对话框 -->
    <el-dialog
      v-model="markdownDialogVisible"
      :title="selectedApi ? `${selectedApi.name} - Markdown文档` : 'Markdown文档'"
      width="80%"
      top="5vh"
    >
      <div style="margin-bottom: 16px; display: flex; gap: 12px;">
        <el-button type="primary" @click="copyMarkdownContent">
          <el-icon><DocumentCopy /></el-icon>
          复制内容
        </el-button>
        <el-button @click="downloadMarkdown">
          <el-icon><Download /></el-icon>
          下载文件
        </el-button>
      </div>
      
      <!-- Markdown 渲染显示 -->
      <div 
        v-html="renderedMarkdown"
        class="markdown-content"
        style="max-height: 600px; overflow-y: auto; border: 1px solid #dcdfe6; border-radius: 4px; padding: 16px; background-color: #fafafa;"
      ></div>
      
      <!-- 原始 Markdown 文本（隐藏，用于复制） -->
      <el-input
        v-model="markdownContent"
        type="textarea"
        :rows="1"
        readonly
        style="display: none;"
      />
      
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="markdownDialogVisible = false">关闭</el-button>
          <el-button type="primary" @click="copyMarkdownContent">
            复制内容
          </el-button>
        </span>
      </template>
    </el-dialog>

    <!-- JSON 文档预览对话框 -->
    <el-dialog
      v-model="jsonDialogVisible"
      :title="selectedApi ? `${selectedApi.name} - JSON文档 (OpenAPI 3.0+)` : 'JSON文档'"
      width="80%"
      top="5vh"
    >
      <div style="margin-bottom: 16px; display: flex; gap: 12px;">
        <el-button type="primary" @click="copyJsonContent">
          <el-icon><DocumentCopy /></el-icon>
          复制内容
        </el-button>
        <el-button @click="downloadJson">
          <el-icon><Download /></el-icon>
          下载文件
        </el-button>
      </div>
      
      <!-- JSON 内容显示 -->
      <el-input
        v-model="jsonContent"
        type="textarea"
        :rows="25"
        readonly
        style="font-family: 'Consolas', 'Monaco', 'Courier New', monospace; font-size: 13px;"
      />
      
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="jsonDialogVisible = false">关闭</el-button>
          <el-button type="primary" @click="copyJsonContent">
            复制内容
          </el-button>
        </span>
      </template>
    </el-dialog>

    <!-- HTML 文档预览对话框 -->
    <el-dialog
      v-model="htmlDialogVisible"
      :title="selectedApi ? `${selectedApi.name} - HTML文档` : 'HTML文档'"
      width="80%"
      top="5vh"
    >
      <div style="margin-bottom: 16px; display: flex; gap: 12px;">
        <el-button type="primary" @click="copyHtmlContent">
          <el-icon><DocumentCopy /></el-icon>
          复制源码
        </el-button>
        <el-button @click="downloadHtml">
          <el-icon><Download /></el-icon>
          下载文件
        </el-button>
      </div>
      
      <!-- HTML 预览和源码切换 -->
      <el-tabs type="border-card">
        <el-tab-pane label="预览" name="preview">
          <div 
            v-html="htmlContent"
            style="max-height: 600px; overflow-y: auto; border: 1px solid #dcdfe6; border-radius: 4px; padding: 16px; background-color: #fff;"
          ></div>
        </el-tab-pane>
        <el-tab-pane label="源码" name="source">
          <el-input
            v-model="htmlContent"
            type="textarea"
            :rows="25"
            readonly
            style="font-family: 'Consolas', 'Monaco', 'Courier New', monospace; font-size: 13px;"
          />
        </el-tab-pane>
      </el-tabs>
      
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="htmlDialogVisible = false">关闭</el-button>
          <el-button type="primary" @click="copyHtmlContent">
            复制源码
          </el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
 import { ref, reactive, computed, onMounted } from 'vue'
 import { useRouter } from 'vue-router'
 import { ElMessage, ElMessageBox } from 'element-plus'
 import { Plus, ArrowDown, DocumentCopy, Download } from '@element-plus/icons-vue'
 import api from '@/utils/api'
 import dayjs from 'dayjs'
 import { marked } from 'marked'

// 路由
const router = useRouter()

// 响应式数据
const loading = ref(false)
const logsLoading = ref(false)
const testing = ref(false)
const submitting = ref(false)
const apis = ref([])
const apiLogs = ref([])
const searchQuery = ref('')
const customerFilter = ref('')
const currentPage = ref(1)
const pageSize = ref(20)
const total = ref(0)

// 日志分页
const logsCurrentPage = ref(1)
const logsPageSize = ref(20)
const logsTotal = ref(0)

// 对话框状态
const detailDialogVisible = ref(false)
const logsDialogVisible = ref(false)
const testDialogVisible = ref(false)
const formDialogVisible = ref(false)
const copyDialogVisible = ref(false)
const markdownDialogVisible = ref(false)
const jsonDialogVisible = ref(false)
const htmlDialogVisible = ref(false)
const selectedApi = ref(null)
const isEditing = ref(false)
const apiFormRef = ref(null)
const copyFormRef = ref(null)
const copying = ref(false)
const customersLoading = ref(false)
const customers = ref([])
const linkTypesLoading = ref(false)
const linkTypes = ref([])
const markdownContent = ref('')
const jsonContent = ref('')
const htmlContent = ref('')

// API表单
const apiForm = reactive({
  customer_id: '',
  name: '',
  endpoint: '',
  method: 'GET',
  description: '',
  is_active: true,
  request_schema_str: '',
  response_schema_str: '',
  link_read_id: ''
})

// 表单验证规则
const apiFormRules = {
  customer_id: [
    { required: true, message: '请选择客户', trigger: 'change' }
  ],
  name: [
    { required: true, message: '请输入API名称', trigger: 'blur' }
  ],
  endpoint: [
    { required: true, message: '请输入API代码', trigger: 'blur' },
    { 
      pattern: /^[a-zA-Z][a-zA-Z0-9_-]{2,49}$/, 
      message: 'API代码必须以字母开头，只能包含字母、数字、下划线和连字符，长度3-50字符', 
      trigger: 'blur' 
    }
  ],
  method: [
    { required: true, message: '请选择请求方法', trigger: 'change' }
  ]
}

// 复制表单
const copyForm = reactive({
  target_customer_id: '',
  new_api_code: '',
  new_api_name: ''
})

// 复制表单验证规则
const copyFormRules = {
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

// 测试表单
const testForm = reactive({
  headers: '{}',
  body: '{}'
})

// 测试结果
const testResult = ref(null)

// 计算属性
const filteredApis = computed(() => {
  let filtered = apis.value
  
  // 按搜索关键词筛选
  if (searchQuery.value) {
    const query = searchQuery.value.toLowerCase()
    filtered = filtered.filter(api => 
      api.name.toLowerCase().includes(query) ||
      api.endpoint.toLowerCase().includes(query)
    )
  }
  
  // 按客户筛选
  if (customerFilter.value) {
    filtered = filtered.filter(api => api.customer_id === customerFilter.value)
  }
  
  return filtered
})

/**
 * 渲染 Markdown 内容为 HTML
 */
const renderedMarkdown = computed(() => {
  if (!markdownContent.value) return ''
  
  try {
    // 配置 marked 选项
    marked.setOptions({
      breaks: true,
      gfm: true,
      headerIds: false,
      mangle: false
    })
    
    return marked(markdownContent.value)
  } catch (error) {
    console.error('Markdown 渲染失败:', error)
    return markdownContent.value
  }
})

// 获取请求方法标签类型
const getMethodTagType = (method) => {
  const typeMap = {
    'GET': 'success',
    'POST': 'primary',
    'PUT': 'warning',
    'DELETE': 'danger',
    'PATCH': 'info'
  }
  return typeMap[method] || 'default'
}

// 获取状态码标签类型
const getStatusCodeTagType = (statusCode) => {
  if (statusCode >= 200 && statusCode < 300) return 'success'
  if (statusCode >= 300 && statusCode < 400) return 'info'
  if (statusCode >= 400 && statusCode < 500) return 'warning'
  if (statusCode >= 500) return 'danger'
  return 'default'
}

// 格式化日期
const formatDate = (dateString) => {
  return dayjs(dateString).format('YYYY-MM-DD HH:mm:ss')
}

// 获取测试URL
const getTestUrl = () => {
  if (!selectedApi.value) return ''
  return `${window.location.origin}/api/v1${selectedApi.value.endpoint}`
}

// 加载API列表
const loadApis = async () => {
  // 防止重复请求
  if (loading.value) {
    console.log('[loadApis] Request blocked - already loading')
    return
  }
  
  console.log('[loadApis] Starting API request at:', new Date().toISOString())
  loading.value = true
  try {
    const response = await api.get('/admin/apis', {
      params: {
        page: currentPage.value,
        size: pageSize.value
      }
    })
    
    // 根据后端返回的数据结构调整
    if (response.data && response.data.data) {
      // 映射后端字段到前端期望的字段
      apis.value = response.data.data.map(item => ({
        id: item.id,
        customer_id: item.customer_id,
        name: item.api_name,
        endpoint: item.api_code,
        method: item.http_method,
        description: item.api_description,
        is_active: item.status,
        created_at: item.created_at,
        request_schema: item.request_schema,
        response_schema: item.response_schema,
        link_read_id: item.link_read_id
      }))
      total.value = response.data.pagination?.total || response.data.data.length
    } else {
      apis.value = []
      total.value = 0
    }
  } catch (error) {
    console.error('加载API列表失败:', error)
    ElMessage.error('加载API列表失败')
  } finally {
    loading.value = false
  }
}

// 分页处理
const handleSizeChange = (val) => {
  pageSize.value = val
  currentPage.value = 1
  loadApis()
}

const handleCurrentChange = (val) => {
  currentPage.value = val
  loadApis()
}

// 查看API详情
const viewApiDetail = (api) => {
  selectedApi.value = api
  detailDialogVisible.value = true
}

// 查看API日志
const viewApiLogs = (api) => {
  selectedApi.value = api
  logsDialogVisible.value = true
  loadApiLogs()
}

// 加载API日志
const loadApiLogs = async () => {
  if (!selectedApi.value) return
  
  logsLoading.value = true
  try {
    const response = await api.get(`/admin/apis/${selectedApi.value.id}/logs`, {
      params: {
        page: logsCurrentPage.value,
        size: logsPageSize.value
      }
    })
    
    // 根据实际返回的数据结构调整
    if (response.data && response.data.data) {
      apiLogs.value = response.data.data || []
      logsTotal.value = response.data.pagination?.total || response.data.total || 0
    } else {
      // 兼容旧的数据结构
      apiLogs.value = response.data.items || []
      logsTotal.value = response.data.total || 0
    }
  } catch (error) {
    console.error('加载API日志失败:', error)
    ElMessage.error('加载API日志失败')
  } finally {
    logsLoading.value = false
  }
}

// 日志分页处理
const handleLogsSizeChange = (val) => {
  logsPageSize.value = val
  logsCurrentPage.value = 1
  loadApiLogs()
}

const handleLogsCurrentChange = (val) => {
  logsCurrentPage.value = val
  loadApiLogs()
}

/**
 * 根据API schema生成示例数据
 * @param {Object} schema - JSON Schema对象
 * @returns {any} 生成的示例数据
 */
const generateExampleFromSchema = (schema) => {
  if (!schema || typeof schema !== 'object') return {}
  
  /**
   * 根据字段名生成智能示例值
   * @param {string} fieldName - 字段名
   * @param {Object} prop - 字段属性
   * @returns {any} 示例值
   */
  const getSmartExample = (fieldName, prop) => {
    const lowerName = fieldName.toLowerCase()
    
    // 根据字段名推断合适的示例值
    if (prop.type === 'string') {
      if (lowerName.includes('email')) return 'user@example.com'
      if (lowerName.includes('phone')) return '13800138000'
      if (lowerName.includes('name')) return '张三'
      if (lowerName.includes('title')) return '示例标题'
      if (lowerName.includes('description')) return '这是一个示例描述'
      if (lowerName.includes('url') || lowerName.includes('link')) return 'https://example.com'
      if (lowerName.includes('address')) return '北京市朝阳区'
      if (lowerName.includes('code')) return 'EXAMPLE001'
      if (lowerName.includes('id')) return 'example-id-123'
    }
    
    if (prop.type === 'integer' || prop.type === 'number') {
      if (lowerName.includes('age')) return 25
      if (lowerName.includes('price') || lowerName.includes('amount')) return 100
      if (lowerName.includes('count') || lowerName.includes('num')) return 10
      if (lowerName.includes('id')) return 1
    }
    
    return null
  }
  
  const generateValue = (prop, fieldName = '') => {
    if (!prop || typeof prop !== 'object') return null
    
    // 优先使用已定义的示例值
    if (prop.example !== undefined) return prop.example
    if (prop.default !== undefined) return prop.default
    
    switch (prop.type) {
      case 'string':
        if (prop.format === 'email') return 'user@example.com'
        if (prop.format === 'date') return '2024-01-01'
        if (prop.format === 'date-time') return '2024-01-01T00:00:00Z'
        if (prop.format === 'uri') return 'https://example.com'
        if (prop.enum && prop.enum.length > 0) return prop.enum[0]
        
        // 尝试智能生成
        const smartExample = getSmartExample(fieldName, prop)
        if (smartExample !== null) return smartExample
        
        return '示例文本'
      
      case 'number':
      case 'integer':
        const smartNumber = getSmartExample(fieldName, prop)
        if (smartNumber !== null) return smartNumber
        return prop.minimum !== undefined ? prop.minimum : 0
      
      case 'boolean':
        return true
      
      case 'array':
        if (prop.items) {
          return [generateValue(prop.items, fieldName)]
        }
        return []
      
      case 'object':
        if (prop.properties) {
          const obj = {}
          Object.keys(prop.properties).forEach(key => {
            obj[key] = generateValue(prop.properties[key], key)
          })
          return obj
        }
        return {}
      
      default:
        return null
    }
  }
  
  if (schema.type === 'object' && schema.properties) {
    const result = {}
    const required = schema.required || []
    
    // 优先生成必填字段
    required.forEach(key => {
      if (schema.properties[key]) {
        result[key] = generateValue(schema.properties[key], key)
      }
    })
    
    // 生成部分可选字段（避免生成过多字段）
    const optionalFields = Object.keys(schema.properties).filter(key => !required.includes(key))
    const maxOptionalFields = Math.min(3, optionalFields.length) // 最多生成3个可选字段
    
    optionalFields.slice(0, maxOptionalFields).forEach(key => {
      result[key] = generateValue(schema.properties[key], key)
    })
    
    return result
  }
  
  return generateValue(schema)
}

/**
 * 根据API方法生成默认请求头
 * @param {string} method - HTTP方法
 * @returns {Object} 默认请求头
 */
const generateDefaultHeaders = (method) => {
  const headers = {}
  
  // 根据HTTP方法设置Content-Type
  if (method !== 'GET' && method !== 'DELETE') {
    headers['Content-Type'] = 'application/json'
  }
  
  // 添加常用的请求头
  headers['Accept'] = 'application/json'
  
  // 可以根据需要添加其他默认头
  // headers['Authorization'] = 'Bearer your-token-here'
  // headers['X-Requested-With'] = 'XMLHttpRequest'
  
  return headers
}

// 测试API
const testApi = (api) => {
  selectedApi.value = api
  testDialogVisible.value = true
  testResult.value = null
  
  // 自动生成请求头
  const defaultHeaders = generateDefaultHeaders(api.method)
  testForm.headers = JSON.stringify(defaultHeaders, null, 2)
  
  // 自动生成请求参数
  if (api.method !== 'GET' && api.request_schema) {
    try {
      const exampleData = generateExampleFromSchema(api.request_schema)
      testForm.body = JSON.stringify(exampleData, null, 2)
    } catch (error) {
      console.warn('生成示例数据失败:', error)
      testForm.body = '{}'
    }
  } else {
    testForm.body = '{}'
  }
}

// 执行测试
const executeTest = async () => {
  if (!selectedApi.value) return
  
  testing.value = true
  try {
    let headers = {}
    let data = null
    
    // 解析请求头
    try {
      headers = JSON.parse(testForm.headers)
    } catch (error) {
      ElMessage.error('请求头格式错误，请输入有效的JSON')
      return
    }
    
    // 解析请求体
    if (selectedApi.value.method !== 'GET') {
      try {
        data = JSON.parse(testForm.body)
      } catch (error) {
        ElMessage.error('请求参数格式错误，请输入有效的JSON')
        return
      }
    }
    
    // 发送请求
    const config = {
      method: selectedApi.value.method.toLowerCase(),
      url: selectedApi.value.endpoint,
      headers,
      data
    }
    
    const response = await api(config)
    testResult.value = {
      status: response.status,
      data: response.data
    }
    
    ElMessage.success('API测试成功')
  } catch (error) {
    console.error('API测试失败:', error)
    testResult.value = {
      status: error.response?.status || 0,
      data: error.response?.data || { error: error.message }
    }
    ElMessage.error('API测试失败')
  } finally {
    testing.value = false
  }
}

// 清空测试结果
const clearTestResult = () => {
  testResult.value = null
}

/**
 * 重新生成测试数据
 */
const regenerateTestData = () => {
  if (!selectedApi.value) return
  
  // 重新生成请求头
  const defaultHeaders = generateDefaultHeaders(selectedApi.value.method)
  testForm.headers = JSON.stringify(defaultHeaders, null, 2)
  
  // 重新生成请求参数
  if (selectedApi.value.method !== 'GET' && selectedApi.value.request_schema) {
    try {
      const exampleData = generateExampleFromSchema(selectedApi.value.request_schema)
      testForm.body = JSON.stringify(exampleData, null, 2)
    } catch (error) {
      console.warn('生成示例数据失败:', error)
      testForm.body = '{}'
    }
  } else {
    testForm.body = '{}'
  }
  
  ElMessage.success('示例数据已重新生成')
}

// 显示创建对话框
const showCreateDialog = async () => {
  isEditing.value = false
  resetApiForm()
  await Promise.all([loadCustomers(), loadLinkTypes()])
  formDialogVisible.value = true
}

// 编辑API
const editApi = async (api) => {
  isEditing.value = true
  selectedApi.value = api
  
  // 填充表单数据
  apiForm.customer_id = api.customer_id || ''
  apiForm.name = api.name
  apiForm.endpoint = api.endpoint
  apiForm.method = api.method
  apiForm.description = api.description || ''
  apiForm.is_active = api.is_active
  apiForm.request_schema_str = api.request_schema ? JSON.stringify(api.request_schema, null, 2) : ''
  apiForm.response_schema_str = api.response_schema ? JSON.stringify(api.response_schema, null, 2) : ''
  
  // 处理link_read_id的类型兼容性
  // 后端返回的可能是字符串类型，需要转换为数字类型以匹配linkTypes中的id
  if (api.link_read_id) {
    // 尝试转换为数字，如果转换失败则保持原值
    const numericId = Number(api.link_read_id)
    apiForm.link_read_id = !isNaN(numericId) ? numericId : api.link_read_id
  } else {
    apiForm.link_read_id = ''
  }
  
  await Promise.all([loadCustomers(), loadLinkTypes()])
  formDialogVisible.value = true
}

// 管理字段
const manageFields = (api) => {
  router.push({
    name: 'ApiFields',
    params: { id: api.id }
  })
}

// 重置表单
const resetApiForm = () => {
  apiForm.customer_id = ''
  apiForm.name = ''
  apiForm.endpoint = ''
  apiForm.method = 'GET'
  apiForm.description = ''
  apiForm.is_active = true
  apiForm.request_schema_str = ''
  apiForm.response_schema_str = ''
  apiForm.link_read_id = ''
  
  if (apiFormRef.value) {
    apiFormRef.value.clearValidate()
  }
}

// 提交表单
const submitApiForm = async () => {
  if (!apiFormRef.value) return
  
  try {
    await apiFormRef.value.validate()
  } catch (error) {
    return
  }
  
  submitting.value = true
  try {
    const formData = {
      api_name: apiForm.name,
      api_code: apiForm.endpoint,
      http_method: apiForm.method,
      api_description: apiForm.description,
      status: apiForm.is_active,
      customer_id: apiForm.customer_id,
      link_read_id: apiForm.link_read_id || null
    }
    
    // 解析schema
    if (apiForm.request_schema_str.trim()) {
      try {
        formData.request_schema = JSON.parse(apiForm.request_schema_str)
      } catch (error) {
        ElMessage.error('请求参数schema格式错误')
        return
      }
    }
    
    if (apiForm.response_schema_str.trim()) {
      try {
        formData.response_schema = JSON.parse(apiForm.response_schema_str)
      } catch (error) {
        ElMessage.error('响应格式schema格式错误')
        return
      }
    }
    
    if (isEditing.value) {
      await api.put(`/admin/apis/${selectedApi.value.id}`, formData)
      ElMessage.success('API更新成功')
    } else {
      await api.post('/admin/apis', formData)
      ElMessage.success('API创建成功')
    }
    
    formDialogVisible.value = false
    loadApis()
  } catch (error) {
    console.error('保存API失败:', error)
    ElMessage.error(isEditing.value ? 'API更新失败' : 'API创建失败')
  } finally {
    submitting.value = false
  }
}

// 切换API状态
 const toggleApiStatus = async (apiItem) => {
   try {
     await api.patch(`/admin/apis/${apiItem.id}/status`)
     
     ElMessage.success(`API已${apiItem.is_active ? '禁用' : '启用'}`)
     loadApis()
   } catch (error) {
     console.error('切换API状态失败:', error)
     ElMessage.error('切换API状态失败')
   }
 }

// 删除API
const deleteApi = async (apiItem) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除API "${apiItem.name}" 吗？此操作不可恢复。`,
      '确认删除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    await api.delete(`/admin/apis/${apiItem.id}`)
    ElMessage.success('API删除成功')
    loadApis()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除API失败:', error)
      ElMessage.error('删除API失败')
    }
  }
}

/**
 * 加载客户列表
 */
const loadCustomers = async () => {
  // 防止重复请求
  if (customersLoading.value) {
    console.log('[loadCustomers] Request blocked - already loading')
    return
  }
  
  console.log('[loadCustomers] Starting customers request at:', new Date().toISOString())
  customersLoading.value = true
  try {
    const response = await api.get('/admin/customers')
    customers.value = response.data.data || []
  } catch (error) {
    console.error('加载客户列表失败:', error)
    ElMessage.error('加载客户列表失败')
  } finally {
    customersLoading.value = false
  }
}

/**
 * 加载连接任务类型列表
 */
const loadLinkTypes = async () => {
  linkTypesLoading.value = true
  try {
    const response = await api.get('/admin/get_api_link')
    if (response.data && response.data.success && response.data.data) {
      // 确保id字段为数字类型，以保持与apiForm.link_read_id的类型一致性
      linkTypes.value = response.data.data.map(item => ({
        ...item,
        id: Number(item.id) || item.id // 尝试转换为数字，失败则保持原值
      }))
    } else {
      linkTypes.value = []
    }
  } catch (error) {
    console.error('加载连接任务类型失败:', error)
    ElMessage.error('加载连接任务类型失败')
    linkTypes.value = []
  } finally {
    linkTypesLoading.value = false
  }
}

/**
 * 复制API
 * @param {Object} apiItem - 要复制的API对象
 */
const copyApi = async (apiItem) => {
  selectedApi.value = apiItem
  
  // 重置复制表单
  copyForm.target_customer_id = ''
  copyForm.new_api_code = `${apiItem.endpoint}_copy`
  copyForm.new_api_name = `${apiItem.name} - 副本`
  
  // 加载客户列表
  await loadCustomers()
  
  copyDialogVisible.value = true
}

/**
 * 提交复制表单
 */
const submitCopyForm = async () => {
  if (!copyFormRef.value) return
  
  try {
    await copyFormRef.value.validate()
  } catch (error) {
    return
  }
  
  copying.value = true
  try {
    const response = await api.post(`/admin/apis/${selectedApi.value.id}/copy`, {
      target_customer_id: copyForm.target_customer_id,
      new_api_code: copyForm.new_api_code,
      new_api_name: copyForm.new_api_name
    })
    
    ElMessage.success('API复制成功')
    copyDialogVisible.value = false
    loadApis()
  } catch (error) {
    console.error('复制API失败:', error)
    const errorMessage = error.response?.data?.detail || 'API复制失败'
    ElMessage.error(errorMessage)
  } finally {
    copying.value = false
  }
}

/**
 * 处理文档生成命令
 * @param {string} format - 文档格式 (markdown/html/json)
 * @param {Object} apiItem - API对象
 */
const handleDocumentCommand = async (format, apiItem) => {
  try {
    ElMessage.info(`正在生成${format.toUpperCase()}文档...`)
    
    const response = await api.get(`/admin/apis/${apiItem.id}/documentation`, {
      params: { format },
      responseType: format === 'html' ? 'text' : 'json'
    })
    
    let content
    
    if (format === 'markdown') {
      content = response.data.data.documentation
      
      // 显示 Markdown 预览窗口
      markdownContent.value = content
      selectedApi.value = apiItem
      markdownDialogVisible.value = true
      ElMessage.success('Markdown文档生成成功！')
      return
    } else if (format === 'html') {
      content = response.data.data.documentation
      
      // 显示 HTML 预览窗口
      htmlContent.value = content
      selectedApi.value = apiItem
      htmlDialogVisible.value = true
      ElMessage.success('HTML文档生成成功！')
      return
    } else if (format === 'json') {
      // 在新窗口中打开 Swagger UI 文档，需要传递认证token
      const token = localStorage.getItem('admin_token')
      if (!token) {
        ElMessage.error('未找到认证信息，请重新登录')
        return
      }
      
      // 将token作为URL参数传递
      const docsUrl = `/api/v1/admin/apis/${apiItem.id}/docs?token=${encodeURIComponent(token)}`
      window.open(docsUrl, '_blank')
      ElMessage.success('正在新窗口中打开API文档！')
      return
    }
  } catch (error) {
    console.error('生成API文档失败:', error)
    const errorMessage = error.response?.data?.detail || `生成${format.toUpperCase()}文档失败`
    ElMessage.error(errorMessage)
  }
}

/**
 * 复制 Markdown 内容到剪贴板
 */
const copyMarkdownContent = async () => {
  try {
    await navigator.clipboard.writeText(markdownContent.value)
    ElMessage.success('Markdown内容已复制到剪贴板！')
  } catch (error) {
    console.error('复制失败:', error)
    ElMessage.error('复制失败，请手动选择文本复制')
  }
}

/**
 * 下载 Markdown 文件
 */
const downloadMarkdown = () => {
  if (!selectedApi.value || !markdownContent.value) return
  
  const blob = new Blob([markdownContent.value], { type: 'text/markdown' })
  const url = window.URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = `${selectedApi.value.endpoint}_api_doc.md`
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  window.URL.revokeObjectURL(url)
  
  ElMessage.success('Markdown文档下载成功！')
}

/**
 * 复制 JSON 内容到剪贴板
 */
const copyJsonContent = async () => {
  try {
    await navigator.clipboard.writeText(jsonContent.value)
    ElMessage.success('JSON内容已复制到剪贴板！')
  } catch (error) {
    console.error('复制失败:', error)
    ElMessage.error('复制失败，请手动选择文本复制')
  }
}

/**
 * 下载 JSON 文件
 */
const downloadJson = () => {
  if (!selectedApi.value || !jsonContent.value) return
  
  const blob = new Blob([jsonContent.value], { type: 'application/json' })
  const url = window.URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = `${selectedApi.value.endpoint}_api_doc.json`
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  window.URL.revokeObjectURL(url)
  
  ElMessage.success('JSON文档下载成功！')
}

/**
 * 复制 HTML 内容到剪贴板
 */
const copyHtmlContent = async () => {
  try {
    await navigator.clipboard.writeText(htmlContent.value)
    ElMessage.success('HTML内容已复制到剪贴板！')
  } catch (error) {
    console.error('复制失败:', error)
    ElMessage.error('复制失败，请手动选择文本复制')
  }
}

/**
 * 下载 HTML 文件
 */
const downloadHtml = () => {
  if (!selectedApi.value || !htmlContent.value) return
  
  const blob = new Blob([htmlContent.value], { type: 'text/html' })
  const url = window.URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = `${selectedApi.value.endpoint}_api_doc.html`
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  window.URL.revokeObjectURL(url)
  
  ElMessage.success('HTML文档下载成功！')
}

// 组件挂载时加载数据
onMounted(() => {
  console.log('[List.vue] onMounted called at:', new Date().toISOString())
  loadApis()
  loadCustomers()
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

/* Markdown 内容样式 */
.markdown-content {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Oxygen', 'Ubuntu', 'Cantarell', 'Fira Sans', 'Droid Sans', 'Helvetica Neue', sans-serif;
  line-height: 1.6;
  color: #333;
}

.markdown-content h1 {
  font-size: 2em;
  font-weight: 600;
  margin: 0 0 16px 0;
  padding-bottom: 8px;
  border-bottom: 2px solid #eaecef;
  color: #24292e;
}

.markdown-content h2 {
  font-size: 1.5em;
  font-weight: 600;
  margin: 24px 0 16px 0;
  padding-bottom: 8px;
  border-bottom: 1px solid #eaecef;
  color: #24292e;
}

.markdown-content h3 {
  font-size: 1.25em;
  font-weight: 600;
  margin: 20px 0 12px 0;
  color: #24292e;
}

.markdown-content p {
  margin: 0 0 16px 0;
}

.markdown-content ul, .markdown-content ol {
  margin: 0 0 16px 0;
  padding-left: 2em;
}

.markdown-content li {
  margin: 4px 0;
}

.markdown-content strong {
  font-weight: 600;
  color: #24292e;
}

.markdown-content code {
  background-color: rgba(27, 31, 35, 0.05);
  border-radius: 3px;
  font-size: 85%;
  margin: 0;
  padding: 0.2em 0.4em;
  font-family: 'SFMono-Regular', 'Consolas', 'Liberation Mono', 'Menlo', monospace;
}

.markdown-content pre {
  background-color: #f6f8fa;
  border-radius: 6px;
  font-size: 85%;
  line-height: 1.45;
  overflow: auto;
  padding: 16px;
  margin: 0 0 16px 0;
}

.markdown-content pre code {
  background-color: transparent;
  border: 0;
  display: inline;
  line-height: inherit;
  margin: 0;
  max-width: auto;
  overflow: visible;
  padding: 0;
  word-wrap: normal;
}

.markdown-content table {
  border-collapse: collapse;
  border-spacing: 0;
  width: 100%;
  margin: 0 0 16px 0;
}

.markdown-content table th,
.markdown-content table td {
  border: 1px solid #dfe2e5;
  padding: 6px 13px;
  text-align: left;
}

.markdown-content table th {
  background-color: #f6f8fa;
  font-weight: 600;
}

.markdown-content table tr:nth-child(2n) {
  background-color: #f6f8fa;
}

.markdown-content blockquote {
  border-left: 4px solid #dfe2e5;
  color: #6a737d;
  margin: 0 0 16px 0;
  padding: 0 16px;
}
</style>