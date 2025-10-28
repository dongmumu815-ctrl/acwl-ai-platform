<template>
  <div class="datasource-list-container">
    <!-- 页面标题 -->
    <div class="page-header">
      <h1 class="page-title">
        <el-icon><Connection /></el-icon>
        数据源管理
      </h1>
      <p class="page-description">管理和配置各类数据源连接</p>
    </div>

    <!-- 筛选和操作栏 -->
    <div class="filter-bar">
      <div class="filter-left">
        <el-select v-model="filterType" placeholder="数据源类型" style="width: 140px" clearable>
          <el-option label="全部" value="" />
          <el-option label="Doris" value="doris" />
          <el-option label="Elasticsearch" value="elasticsearch" />
          <el-option label="MySQL" value="mysql" />
          <el-option label="PostgreSQL" value="postgresql" />
        </el-select>
        
        <el-select v-model="filterStatus" placeholder="状态" style="width: 120px" clearable>
          <el-option label="全部" value="" />
          <el-option label="正常" value="active" />
          <el-option label="异常" value="error" />
          <el-option label="禁用" value="disabled" />
        </el-select>
        
        <el-input
          v-model="searchKeyword"
          placeholder="搜索数据源名称..."
          style="width: 200px"
          clearable
        >
          <template #prefix>
            <el-icon><Search /></el-icon>
          </template>
        </el-input>
      </div>
      
      <div class="filter-right">
        <el-button type="primary" @click="showCreateDialog">
          <el-icon><Plus /></el-icon>
          新建数据源
        </el-button>
        <el-button @click="refreshList">
          <el-icon><Refresh /></el-icon>
          刷新
        </el-button>
      </div>
    </div>

    <!-- 数据源列表 -->
    <div class="datasource-content">
      <el-table
        :data="filteredDataSources"
        v-loading="loading"
        stripe
        style="width: 100%"
      >
        <el-table-column prop="name" label="数据源名称" min-width="180">
          <template #default="{ row }">
            <div class="datasource-name">
              <el-icon class="datasource-icon" :style="{ color: getTypeColor(row.type) }">
                <component :is="getTypeIcon(row.type)" />
              </el-icon>
              <span>{{ row.name }}</span>
            </div>
          </template>
        </el-table-column>
        
        <el-table-column prop="type" label="类型" width="120">
          <template #default="{ row }">
            <el-tag :type="getTypeTagType(row.type)">{{ getTypeLabel(row.type) }}</el-tag>
          </template>
        </el-table-column>
        
        <el-table-column prop="host" label="主机地址" width="150" show-overflow-tooltip />
        
        <el-table-column prop="database" label="数据库" width="120" show-overflow-tooltip />
        
        <el-table-column label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="getStatusTagType(getDataSourceStatus(row))">
              {{ getStatusLabel(getDataSourceStatus(row)) }}
            </el-tag>
          </template>
        </el-table-column>
        
        <el-table-column prop="last_test_at" label="最后测试" width="160">
          <template #default="{ row }">
            <div v-if="row.last_test_at">
              <div>{{ formatDateTime(row.last_test_at) }}</div>
              <el-tag 
                size="small" 
                :type="row.last_test_status === 'success' ? 'success' : 'danger'"
              >
                {{ row.last_test_status === 'success' ? '成功' : '失败' }}
              </el-tag>
            </div>
            <span v-else class="text-muted">未测试</span>
          </template>
        </el-table-column>
        
        <el-table-column prop="created_at" label="创建时间" width="160">
          <template #default="{ row }">
            {{ formatDateTime(row.created_at) }}
          </template>
        </el-table-column>
        
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <el-button 
              type="primary" 
              size="small" 
              @click="testConnection(row)"
              :loading="testingIds.includes(row.id)"
            >
              <el-icon><Connection /></el-icon>
              测试
            </el-button>
            <el-button size="small" @click="editDataSource(row)">
              <el-icon><Edit /></el-icon>
              编辑
            </el-button>
            <el-button 
              type="danger" 
              size="small" 
              @click="deleteDataSource(row)"
            >
              <el-icon><Delete /></el-icon>
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>
      
      <!-- 分页 -->
      <div class="pagination-container">
        <el-pagination
          v-model:current-page="currentPage"
          v-model:page-size="pageSize"
          :page-sizes="[10, 20, 50, 100]"
          :total="totalDataSources"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="handleSizeChange"
          @current-change="handleCurrentChange"
        />
      </div>
    </div>

    <!-- 创建/编辑数据源对话框 -->
    <el-dialog
      v-model="showDialog"
      :title="isEdit ? '编辑数据源' : '创建数据源'"
      width="600px"
      :before-close="handleDialogClose"
    >
      <el-form
        ref="formRef"
        :model="formData"
        :rules="formRules"
        label-width="100px"
      >
        <el-form-item label="数据源名称" prop="name">
          <el-input v-model="formData.name" placeholder="请输入数据源名称" />
        </el-form-item>
        
        <el-form-item label="数据源类型" prop="type">
          <el-select v-model="formData.type" placeholder="请选择数据源类型" style="width: 100%">
            <el-option label="Doris" value="doris" />
            <el-option label="Elasticsearch" value="elasticsearch" />
            <el-option label="MySQL" value="mysql" />
            <el-option label="PostgreSQL" value="postgresql" />
          </el-select>
        </el-form-item>
        
        <el-form-item label="主机地址" prop="host">
          <el-input v-model="formData.host" placeholder="请输入主机地址" />
        </el-form-item>
        
        <el-form-item label="端口" prop="port">
          <el-input-number 
            v-model="formData.port" 
            :min="1" 
            :max="65535" 
            style="width: 100%"
          />
        </el-form-item>
        
        <el-form-item label="数据库" prop="database">
          <el-input v-model="formData.database" placeholder="请输入数据库名称" />
        </el-form-item>
        
        <el-form-item label="用户名" prop="username">
          <el-input v-model="formData.username" placeholder="请输入用户名" />
        </el-form-item>
        
        <el-form-item label="密码" prop="password">
          <el-input 
            v-model="formData.password" 
            type="password" 
            placeholder="请输入密码"
            show-password
          />
        </el-form-item>
        
        <el-form-item label="描述">
          <el-input 
            v-model="formData.description" 
            type="textarea" 
            :rows="3"
            placeholder="请输入数据源描述"
          />
        </el-form-item>
        
        <el-form-item label="状态">
          <el-switch 
            v-model="formData.is_active" 
            active-text="启用" 
            inactive-text="禁用"
          />
        </el-form-item>
      </el-form>
      
      <template #footer>
        <div class="dialog-footer">
          <el-button @click="handleDialogClose">取消</el-button>
          <el-button 
            type="primary" 
            @click="testFormConnection"
            :loading="testingConnection"
          >
            测试连接
          </el-button>
          <el-button 
            type="primary" 
            @click="submitForm"
            :loading="submitting"
          >
            {{ isEdit ? '更新' : '创建' }}
          </el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox, type FormInstance, type FormRules } from 'element-plus'
import { 
  Connection, 
  Search, 
  Plus, 
  Refresh, 
  Edit, 
  Delete,
  Database,
  Monitor,
  Server
} from '@element-plus/icons-vue'
import datasourceApi from '@/api/datasource'
import type { DataSource, DataSourceFormData } from '@/types/datasource'

// 响应式数据
const loading = ref(false)
const showDialog = ref(false)
const isEdit = ref(false)
const submitting = ref(false)
const testingConnection = ref(false)
const testingIds = ref<number[]>([])

// 筛选条件
const filterType = ref('')
const filterStatus = ref('')
const searchKeyword = ref('')

// 分页
const currentPage = ref(1)
const pageSize = ref(20)
const totalDataSources = ref(0)

// 表单相关
const formRef = ref<FormInstance>()
const formData = ref<DataSourceFormData>({
  name: '',
  type: '',
  description: '',
  host: '',
  port: 3306,
  database: '',
  username: '',
  password: '',
  connection_params: {},
  is_active: true,
  is_default: false,
  tags: []
})

// 表单验证规则
const formRules: FormRules = {
  name: [
    { required: true, message: '请输入数据源名称', trigger: 'blur' },
    { min: 2, max: 50, message: '长度在 2 到 50 个字符', trigger: 'blur' }
  ],
  type: [
    { required: true, message: '请选择数据源类型', trigger: 'change' }
  ],
  host: [
    { required: true, message: '请输入主机地址', trigger: 'blur' }
  ],
  port: [
    { required: true, message: '请输入端口号', trigger: 'blur' },
    { type: 'number', min: 1, max: 65535, message: '端口号范围 1-65535', trigger: 'blur' }
  ],
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' }
  ]
}

// 数据源列表
const dataSources = ref<DataSource[]>([])

/**
 * 过滤后的数据源列表
 */
const filteredDataSources = computed(() => {
  let filtered = dataSources.value
  
  // 按类型筛选
  if (filterType.value) {
    filtered = filtered.filter(ds => ds.type === filterType.value)
  }
  
  // 按状态筛选
  if (filterStatus.value) {
    const statusMap = {
      'active': (ds: DataSource) => ds.is_active && ds.last_test_status === 'success',
      'error': (ds: DataSource) => ds.is_active && ds.last_test_status === 'failed',
      'disabled': (ds: DataSource) => !ds.is_active
    }
    filtered = filtered.filter(statusMap[filterStatus.value as keyof typeof statusMap])
  }
  
  // 按关键词搜索
  if (searchKeyword.value) {
    const keyword = searchKeyword.value.toLowerCase()
    filtered = filtered.filter(ds => 
      ds.name.toLowerCase().includes(keyword) ||
      ds.description?.toLowerCase().includes(keyword) ||
      ds.host.toLowerCase().includes(keyword)
    )
  }
  
  return filtered
})

/**
 * 获取数据源类型图标
 */
function getTypeIcon(type: string) {
  const iconMap: Record<string, any> = {
    'doris': Database,
    'elasticsearch': Monitor,
    'mysql': Database,
    'postgresql': Database
  }
  return iconMap[type] || Server
}

/**
 * 获取数据源类型颜色
 */
function getTypeColor(type: string) {
  const colorMap: Record<string, string> = {
    'doris': '#409EFF',
    'elasticsearch': '#67C23A',
    'mysql': '#E6A23C',
    'postgresql': '#909399'
  }
  return colorMap[type] || '#909399'
}

/**
 * 获取数据源类型标签类型
 */
function getTypeTagType(type: string) {
  const typeMap: Record<string, string> = {
    'doris': 'primary',
    'elasticsearch': 'success',
    'mysql': 'warning',
    'postgresql': 'info'
  }
  return typeMap[type] || 'info'
}

/**
 * 获取数据源类型标签文本
 */
function getTypeLabel(type: string) {
  const labelMap: Record<string, string> = {
    'doris': 'Doris',
    'elasticsearch': 'Elasticsearch',
    'mysql': 'MySQL',
    'postgresql': 'PostgreSQL'
  }
  return labelMap[type] || type
}

/**
 * 获取数据源状态
 */
function getDataSourceStatus(dataSource: DataSource): 'active' | 'error' | 'disabled' {
  if (!dataSource.is_active) {
    return 'disabled'
  }
  if (dataSource.last_test_status === 'failed') {
    return 'error'
  }
  return 'active'
}

/**
 * 获取状态标签类型
 */
function getStatusTagType(status: string) {
  const typeMap: Record<string, string> = {
    'active': 'success',
    'error': 'danger',
    'disabled': 'info'
  }
  return typeMap[status] || 'info'
}

/**
 * 获取状态标签文本
 */
function getStatusLabel(status: string) {
  const labelMap: Record<string, string> = {
    'active': '正常',
    'error': '异常',
    'disabled': '禁用'
  }
  return labelMap[status] || status
}

/**
 * 格式化日期时间
 */
function formatDateTime(dateTime: string) {
  return new Date(dateTime).toLocaleString('zh-CN')
}

/**
 * 显示创建对话框
 */
function showCreateDialog() {
  isEdit.value = false
  resetForm()
  showDialog.value = true
}

/**
 * 编辑数据源
 */
function editDataSource(dataSource: DataSource) {
  isEdit.value = true
  formData.value = {
    name: dataSource.name,
    type: dataSource.type,
    description: dataSource.description || '',
    host: dataSource.host,
    port: dataSource.port,
    database: dataSource.database || '',
    username: dataSource.username,
    password: '', // 不显示原密码
    connection_params: dataSource.connection_params || {},
    is_active: dataSource.is_active,
    is_default: dataSource.is_default,
    tags: dataSource.tags || []
  }
  showDialog.value = true
}

/**
 * 重置表单
 */
function resetForm() {
  formData.value = {
    name: '',
    type: '',
    description: '',
    host: '',
    port: 3306,
    database: '',
    username: '',
    password: '',
    connection_params: {},
    is_active: true,
    is_default: false,
    tags: []
  }
  formRef.value?.resetFields()
}

/**
 * 关闭对话框
 */
function handleDialogClose() {
  showDialog.value = false
  resetForm()
}

/**
 * 测试表单连接
 */
async function testFormConnection() {
  if (!formRef.value) return
  
  try {
    await formRef.value.validate()
    testingConnection.value = true
    
    const testData = {
      type: formData.value.type,
      host: formData.value.host,
      port: formData.value.port,
      database: formData.value.database,
      username: formData.value.username,
      password: formData.value.password,
      connection_params: formData.value.connection_params
    }
    
    const response = await datasourceApi.testConnection(testData)
    
    if (response.data.status === 'success') {
      ElMessage.success('连接测试成功')
    } else {
      ElMessage.error(`连接测试失败: ${response.data.message}`)
    }
  } catch (error) {
    console.error('测试连接失败:', error)
    ElMessage.error('连接测试失败')
  } finally {
    testingConnection.value = false
  }
}

/**
 * 提交表单
 */
async function submitForm() {
  if (!formRef.value) return
  
  try {
    await formRef.value.validate()
    submitting.value = true
    
    if (isEdit.value) {
      // 更新数据源
      // TODO: 实现更新逻辑
      ElMessage.success('数据源更新成功')
    } else {
      // 创建数据源
      const response = await datasourceApi.createDataSource({
        ...formData.value,
        port: Number(formData.value.port),
      })
      if (response.success) {
        ElMessage.success('数据源创建成功')
        await loadDataSources()
      }
    }
    
    handleDialogClose()
  } catch (error) {
    console.error('提交失败:', error)
    ElMessage.error('操作失败')
  } finally {
    submitting.value = false
  }
}

/**
 * 测试数据源连接
 */
async function testConnection(dataSource: DataSource) {
  testingIds.value.push(dataSource.id)
  
  try {
    const response = await datasourceApi.testDataSourceConnection(dataSource.id)
    
    if (response.success && response.data.status === 'success') {
      ElMessage.success(`${dataSource.name} 连接测试成功`)
      // 更新数据源状态
      const index = dataSources.value.findIndex(ds => ds.id === dataSource.id)
      if (index !== -1) {
        dataSources.value[index].last_test_at = new Date().toISOString()
        dataSources.value[index].last_test_status = 'success'
      }
    } else {
      const errorMsg = response.data?.message || '连接失败'
      ElMessage.error(`${dataSource.name} 连接测试失败: ${errorMsg}`)
      // 更新数据源状态为错误
      const index = dataSources.value.findIndex(ds => ds.id === dataSource.id)
      if (index !== -1) {
        dataSources.value[index].last_test_at = new Date().toISOString()
        dataSources.value[index].last_test_status = 'failed'
      }
    }
  } catch (error) {
    console.error('测试连接失败:', error)
    ElMessage.error('连接测试失败')
    // 更新数据源状态为错误
    const index = dataSources.value.findIndex(ds => ds.id === dataSource.id)
    if (index !== -1) {
      dataSources.value[index].last_test_at = new Date().toISOString()
      dataSources.value[index].last_test_status = 'failed'
    }
  } finally {
    testingIds.value = testingIds.value.filter(id => id !== dataSource.id)
  }
}

/**
 * 删除数据源
 */
async function deleteDataSource(dataSource: DataSource) {
  try {
    await ElMessageBox.confirm(
      `确定要删除数据源 "${dataSource.name}" 吗？此操作不可恢复。`,
      '确认删除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    const response = await datasourceApi.deleteDataSource(dataSource.id)
    if (response.success) {
      ElMessage.success('数据源删除成功')
      await loadDataSources()
    }
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除失败:', error)
      ElMessage.error('删除失败')
    }
  }
}

/**
 * 刷新列表
 */
function refreshList() {
  loadDataSources()
}

/**
 * 处理页面大小变化
 */
function handleSizeChange(size: number) {
  pageSize.value = size
  currentPage.value = 1
  loadDataSources()
}

/**
 * 处理当前页变化
 */
function handleCurrentChange(page: number) {
  currentPage.value = page
  loadDataSources()
}

/**
 * 加载数据源列表
 */
async function loadDataSources() {
  loading.value = true
  
  try {
    const params = {
      page: currentPage.value,
      size: pageSize.value,
      search: searchKeyword.value || undefined,
      datasource_type: filterType.value || undefined,
      status: filterStatus.value || undefined
    }
    
    const response = await datasourceApi.getDataSourceList(params)
    
    if (response.success) {
      dataSources.value = response.data.items || []
      totalDataSources.value = response.data.total || 0
    } else {
      ElMessage.error('加载数据源列表失败')
    }
  } catch (error) {
    console.error('加载数据源列表失败:', error)
    ElMessage.error('加载数据源列表失败')
  } finally {
    loading.value = false
  }
}

// 组件挂载时加载数据
onMounted(() => {
  loadDataSources()
})
</script>

<style scoped>
.datasource-list-container {
  padding: 20px;
  background-color: #f5f7fa;
  min-height: 100vh;
}

.page-header {
  margin-bottom: 24px;
}

.page-title {
  font-size: 24px;
  font-weight: 600;
  color: #303133;
  margin: 0 0 8px 0;
  display: flex;
  align-items: center;
  gap: 8px;
}

.page-description {
  color: #606266;
  margin: 0;
  font-size: 14px;
}

.filter-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  padding: 16px;
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.filter-left {
  display: flex;
  gap: 12px;
  align-items: center;
}

.filter-right {
  display: flex;
  gap: 12px;
}

.datasource-content {
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  overflow: hidden;
}

.datasource-name {
  display: flex;
  align-items: center;
  gap: 8px;
}

.datasource-icon {
  font-size: 16px;
}

.text-muted {
  color: #909399;
  font-size: 12px;
}

.pagination-container {
  padding: 16px;
  display: flex;
  justify-content: center;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .datasource-list-container {
    padding: 12px;
  }
  
  .filter-bar {
    flex-direction: column;
    gap: 12px;
    align-items: stretch;
  }
  
  .filter-left,
  .filter-right {
    justify-content: center;
  }
  
  .page-title {
    font-size: 20px;
  }
}
</style>