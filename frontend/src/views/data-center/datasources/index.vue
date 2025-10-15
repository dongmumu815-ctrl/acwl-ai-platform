<template>
  <div class="datasources-container">
    <!-- 页面标题 -->
    <div class="page-header">
      <h1 class="page-title">
        <el-icon><Connection /></el-icon>
        数据源管理
      </h1>
      <p class="page-description">管理和配置各种数据源连接</p>
    </div>

    <!-- 搜索和筛选 -->
    <div class="search-section">
      <el-card>
        <el-form :model="searchForm" inline>
          <el-form-item label="数据源名称">
            <el-input
              v-model="searchForm.name"
              placeholder="请输入数据源名称"
              clearable
              style="width: 200px"
            />
          </el-form-item>
          <el-form-item label="数据源类型">
            <el-select
              v-model="searchForm.type"
              placeholder="请选择数据源类型"
              clearable
              style="width: 150px"
            >
              <el-option
                v-for="type in datasourceTypes"
                :key="type.value"
                :label="type.label"
                :value="type.value"
              />
            </el-select>
          </el-form-item>
          <el-form-item label="连接状态">
            <el-select
              v-model="searchForm.status"
              placeholder="请选择连接状态"
              clearable
              style="width: 120px"
            >
              <el-option label="已连接" value="connected" />
              <el-option label="未连接" value="disconnected" />
              <el-option label="连接中" value="connecting" />
              <el-option label="连接失败" value="failed" />
            </el-select>
          </el-form-item>
          <el-form-item>
            <el-button type="primary" @click="handleSearch">
              <el-icon><Search /></el-icon>
              搜索
            </el-button>
            <el-button @click="handleReset">
              <el-icon><Refresh /></el-icon>
              重置
            </el-button>
          </el-form-item>
        </el-form>
      </el-card>
    </div>

    <!-- 操作栏 -->
    <div class="action-bar">
      <div class="left-actions">
        <el-button type="primary" @click="handleCreate">
          <el-icon><Plus /></el-icon>
          新增数据源
        </el-button>
        <el-button @click="handleBatchTest" :disabled="!selectedDatasources.length">
          <el-icon><Connection /></el-icon>
          批量测试连接
        </el-button>
        <el-button 
          type="danger" 
          @click="handleBatchDelete" 
          :disabled="!selectedDatasources.length"
        >
          <el-icon><Delete /></el-icon>
          批量删除
        </el-button>
      </div>
      <div class="right-actions">
        <el-button @click="handleRefresh">
          <el-icon><Refresh /></el-icon>
          刷新
        </el-button>
      </div>
    </div>

    <!-- 数据表格 -->
    <div class="table-section">
      <el-card>
        <el-table
          v-loading="loading"
          :data="tableData"
          @selection-change="handleSelectionChange"
          stripe
          style="width: 100%"
        >
          <el-table-column type="selection" width="55" />
          <el-table-column prop="id" label="ID" width="80" />
          <el-table-column prop="name" label="数据源名称" min-width="200">
            <template #default="{ row }">
              <div class="datasource-name">
                <el-icon class="datasource-icon">
                  <component :is="getDatasourceIcon(row.type)" />
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
          <el-table-column prop="host" label="主机地址" width="150" />
          <el-table-column prop="port" label="端口" width="80" />
          <el-table-column prop="database" label="数据库" width="120" />
          <el-table-column prop="status" label="连接状态" width="120">
            <template #default="{ row }">
              <el-tag :type="getStatusTagType(row.status)">
                <el-icon class="status-icon">
                  <component :is="getStatusIcon(row.status)" />
                </el-icon>
                {{ getStatusLabel(row.status) }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="lastConnected" label="最后连接时间" width="180" />
          <el-table-column prop="createdAt" label="创建时间" width="180" />
          <el-table-column label="操作" width="250" fixed="right">
            <template #default="{ row }">
              <el-button size="small" @click="handleTest(row)">
                <el-icon><Connection /></el-icon>
                测试连接
              </el-button>
              <el-button size="small" @click="handleView(row)">
                <el-icon><View /></el-icon>
                查看
              </el-button>
              <el-button size="small" type="primary" @click="handleEdit(row)">
                <el-icon><Edit /></el-icon>
                编辑
              </el-button>
              <el-button size="small" type="danger" @click="handleDelete(row)">
                <el-icon><Delete /></el-icon>
                删除
              </el-button>
            </template>
          </el-table-column>
        </el-table>

        <!-- 分页 -->
        <div class="pagination-wrapper">
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
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Connection,
  Search,
  Refresh,
  Plus,
  Delete,
  View,
  Edit,
  CircleCheck,
  CircleClose,
  Loading,
  Warning,
  Coin,
  DataBoard,
  Files,
  Monitor,
  Document
} from '@element-plus/icons-vue'

const router = useRouter()

// 响应式数据
const loading = ref(false)
const selectedDatasources = ref<any[]>([])

// 搜索表单
const searchForm = reactive({
  name: '',
  type: '',
  status: ''
})

// 分页数据
const pagination = reactive({
  currentPage: 1,
  pageSize: 20,
  total: 0
})

// 数据源类型选项
const datasourceTypes = ref([
  { label: 'MySQL', value: 'mysql' },
  { label: 'PostgreSQL', value: 'postgresql' },
  { label: 'MongoDB', value: 'mongodb' },
  { label: 'Redis', value: 'redis' },
  { label: 'Elasticsearch', value: 'elasticsearch' },
  { label: 'Oracle', value: 'oracle' },
  { label: 'SQL Server', value: 'sqlserver' },
  { label: 'ClickHouse', value: 'clickhouse' }
])

// 表格数据
const tableData = ref([
  {
    id: 1,
    name: '主数据库',
    type: 'mysql',
    host: '192.168.1.100',
    port: 3306,
    database: 'main_db',
    status: 'connected',
    lastConnected: '2024-01-20 15:30:00',
    createdAt: '2024-01-15 10:30:00'
  },
  {
    id: 2,
    name: '用户数据库',
    type: 'postgresql',
    host: '192.168.1.101',
    port: 5432,
    database: 'user_db',
    status: 'connected',
    lastConnected: '2024-01-20 14:20:00',
    createdAt: '2024-01-14 14:20:00'
  },
  {
    id: 3,
    name: '缓存数据库',
    type: 'redis',
    host: '192.168.1.102',
    port: 6379,
    database: '0',
    status: 'disconnected',
    lastConnected: '2024-01-19 16:45:00',
    createdAt: '2024-01-13 09:15:00'
  },
  {
    id: 4,
    name: '文档数据库',
    type: 'mongodb',
    host: '192.168.1.103',
    port: 27017,
    database: 'docs_db',
    status: 'connecting',
    lastConnected: '2024-01-20 10:15:00',
    createdAt: '2024-01-12 16:45:00'
  },
  {
    id: 5,
    name: '搜索引擎',
    type: 'elasticsearch',
    host: '192.168.1.104',
    port: 9200,
    database: 'search_index',
    status: 'failed',
    lastConnected: '2024-01-18 12:30:00',
    createdAt: '2024-01-11 11:30:00'
  }
])

/**
 * 获取数据源图标
 * @param type 数据源类型
 * @returns 图标组件名
 */
const getDatasourceIcon = (type: string) => {
  const iconMap: Record<string, string> = {
    mysql: 'Coin',
    postgresql: 'DataBoard',
    mongodb: 'Files',
    redis: 'Monitor',
    elasticsearch: 'Document',
    oracle: 'Coin',
    sqlserver: 'DataBoard',
    clickhouse: 'Files'
  }
  return iconMap[type] || 'Connection'
}

/**
 * 获取类型标签样式
 * @param type 数据源类型
 * @returns 标签样式
 */
const getTypeTagType = (type: string) => {
  const typeMap: Record<string, string> = {
    mysql: 'primary',
    postgresql: 'success',
    mongodb: 'warning',
    redis: 'danger',
    elasticsearch: 'info',
    oracle: 'primary',
    sqlserver: 'success',
    clickhouse: 'warning'
  }
  return typeMap[type] || 'info'
}

/**
 * 获取类型标签文本
 * @param type 数据源类型
 * @returns 标签文本
 */
const getTypeLabel = (type: string) => {
  const typeMap: Record<string, string> = {
    mysql: 'MySQL',
    postgresql: 'PostgreSQL',
    mongodb: 'MongoDB',
    redis: 'Redis',
    elasticsearch: 'Elasticsearch',
    oracle: 'Oracle',
    sqlserver: 'SQL Server',
    clickhouse: 'ClickHouse'
  }
  return typeMap[type] || type
}

/**
 * 获取状态图标
 * @param status 连接状态
 * @returns 图标组件名
 */
const getStatusIcon = (status: string) => {
  const iconMap: Record<string, string> = {
    connected: 'CircleCheck',
    disconnected: 'CircleClose',
    connecting: 'Loading',
    failed: 'Warning'
  }
  return iconMap[status] || 'CircleClose'
}

/**
 * 获取状态标签样式
 * @param status 连接状态
 * @returns 标签样式
 */
const getStatusTagType = (status: string) => {
  const statusMap: Record<string, string> = {
    connected: 'success',
    disconnected: 'info',
    connecting: 'warning',
    failed: 'danger'
  }
  return statusMap[status] || 'info'
}

/**
 * 获取状态标签文本
 * @param status 连接状态
 * @returns 标签文本
 */
const getStatusLabel = (status: string) => {
  const statusMap: Record<string, string> = {
    connected: '已连接',
    disconnected: '未连接',
    connecting: '连接中',
    failed: '连接失败'
  }
  return statusMap[status] || status
}

/**
 * 处理搜索
 */
const handleSearch = () => {
  loading.value = true
  // 模拟搜索
  setTimeout(() => {
    loading.value = false
    ElMessage.success('搜索完成')
  }, 1000)
}

/**
 * 处理重置
 */
const handleReset = () => {
  Object.assign(searchForm, {
    name: '',
    type: '',
    status: ''
  })
  handleSearch()
}

/**
 * 处理新增
 */
const handleCreate = () => {
  router.push('/data-center/datasources/create')
}

/**
 * 处理批量测试连接
 */
const handleBatchTest = () => {
  ElMessage.info('正在测试连接...')
  // 模拟批量测试
  setTimeout(() => {
    ElMessage.success(`已完成 ${selectedDatasources.value.length} 个数据源的连接测试`)
  }, 2000)
}

/**
 * 处理批量删除
 */
const handleBatchDelete = () => {
  ElMessageBox.confirm(
    `确定要删除选中的 ${selectedDatasources.value.length} 个数据源吗？`,
    '批量删除',
    {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    }
  ).then(() => {
    ElMessage.success('删除成功')
    selectedDatasources.value = []
  }).catch(() => {
    ElMessage.info('已取消删除')
  })
}

/**
 * 处理刷新
 */
const handleRefresh = () => {
  loading.value = true
  setTimeout(() => {
    loading.value = false
    ElMessage.success('数据已刷新')
  }, 1000)
}

/**
 * 处理测试连接
 * @param row 行数据
 */
const handleTest = (row: any) => {
  ElMessage.info(`正在测试 ${row.name} 的连接...`)
  // 模拟测试连接
  setTimeout(() => {
    const success = Math.random() > 0.3 // 70% 成功率
    if (success) {
      ElMessage.success('连接测试成功')
      row.status = 'connected'
      row.lastConnected = new Date().toLocaleString()
    } else {
      ElMessage.error('连接测试失败')
      row.status = 'failed'
    }
  }, 2000)
}

/**
 * 处理查看
 * @param row 行数据
 */
const handleView = (row: any) => {
  router.push(`/data-center/datasources/detail/${row.id}`)
}

/**
 * 处理编辑
 * @param row 行数据
 */
const handleEdit = (row: any) => {
  router.push(`/data-center/datasources/edit/${row.id}`)
}

/**
 * 处理删除
 * @param row 行数据
 */
const handleDelete = (row: any) => {
  ElMessageBox.confirm(
    `确定要删除数据源 "${row.name}" 吗？`,
    '删除确认',
    {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    }
  ).then(() => {
    ElMessage.success('删除成功')
  }).catch(() => {
    ElMessage.info('已取消删除')
  })
}

/**
 * 处理选择变化
 * @param selection 选中的行
 */
const handleSelectionChange = (selection: any[]) => {
  selectedDatasources.value = selection
}

/**
 * 处理页面大小变化
 * @param size 页面大小
 */
const handleSizeChange = (size: number) => {
  pagination.pageSize = size
  handleSearch()
}

/**
 * 处理当前页变化
 * @param page 当前页
 */
const handleCurrentChange = (page: number) => {
  pagination.currentPage = page
  handleSearch()
}

/**
 * 组件挂载时初始化
 */
onMounted(() => {
  pagination.total = tableData.value.length
  console.log('数据源管理页面初始化完成')
})
</script>

<style lang="scss" scoped>
.datasources-container {
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

.search-section {
  margin-bottom: 16px;
}

.action-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  
  .left-actions {
    display: flex;
    gap: 8px;
  }
}

.table-section {
  .datasource-name {
    display: flex;
    align-items: center;
    
    .datasource-icon {
      margin-right: 8px;
      color: var(--el-color-primary);
    }
  }
  
  .status-icon {
    margin-right: 4px;
  }
  
  .pagination-wrapper {
    display: flex;
    justify-content: center;
    margin-top: 20px;
  }
}

// 响应式设计
@media (max-width: 768px) {
  .datasources-container {
    padding: 16px;
  }
  
  .action-bar {
    flex-direction: column;
    gap: 16px;
    align-items: flex-start;
  }
}
</style>