<template>
  <div class="logs-page">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="header-content">
        <div class="header-left">
          <h1 class="page-title">
            <el-icon><Document /></el-icon>
            系统日志
          </h1>
          <p class="page-description">查看和分析系统运行日志</p>
        </div>
        <div class="header-right">
          <el-button @click="exportLogs" :loading="exporting">
            <el-icon><Download /></el-icon>
            导出日志
          </el-button>
          <el-button @click="loadLogs">
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
                <el-icon><Document /></el-icon>
              </div>
              <div class="stat-info">
                <div class="stat-value">{{ formatNumber(stats.total) }}</div>
                <div class="stat-label">总日志数</div>
              </div>
            </div>
          </el-card>
        </el-col>
        
        <el-col :xs="12" :sm="6">
          <el-card shadow="hover" class="stat-card">
            <div class="stat-content">
              <div class="stat-icon error">
                <el-icon><WarningFilled /></el-icon>
              </div>
              <div class="stat-info">
                <div class="stat-value">{{ stats.errors }}</div>
                <div class="stat-label">错误日志</div>
              </div>
            </div>
          </el-card>
        </el-col>
        
        <el-col :xs="12" :sm="6">
          <el-card shadow="hover" class="stat-card">
            <div class="stat-content">
              <div class="stat-icon warning">
                <el-icon><Warning /></el-icon>
              </div>
              <div class="stat-info">
                <div class="stat-value">{{ stats.warnings }}</div>
                <div class="stat-label">警告日志</div>
              </div>
            </div>
          </el-card>
        </el-col>
        
        <el-col :xs="12" :sm="6">
          <el-card shadow="hover" class="stat-card">
            <div class="stat-content">
              <div class="stat-icon today">
                <el-icon><Calendar /></el-icon>
              </div>
              <div class="stat-info">
                <div class="stat-value">{{ formatNumber(stats.today) }}</div>
                <div class="stat-label">今日日志</div>
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
              placeholder="搜索日志内容"
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
              v-model="filters.level"
              placeholder="日志级别"
              clearable
              @change="handleFilter"
            >
              <el-option label="全部" value="" />
              <el-option label="DEBUG" value="debug" />
              <el-option label="INFO" value="info" />
              <el-option label="WARN" value="warn" />
              <el-option label="ERROR" value="error" />
              <el-option label="FATAL" value="fatal" />
            </el-select>
          </el-col>
          
          <el-col :xs="12" :sm="4" :md="3">
            <el-select
              v-model="filters.module"
              placeholder="模块"
              clearable
              @change="handleFilter"
            >
              <el-option label="全部" value="" />
              <el-option label="API" value="api" />
              <el-option label="训练" value="training" />
              <el-option label="部署" value="deployment" />
              <el-option label="用户" value="user" />
              <el-option label="系统" value="system" />
              <el-option label="数据库" value="database" />
            </el-select>
          </el-col>
          
          <el-col :xs="24" :sm="8" :md="6">
            <el-date-picker
              v-model="filters.dateRange"
              type="datetimerange"
              range-separator="至"
              start-placeholder="开始时间"
              end-placeholder="结束时间"
              format="YYYY-MM-DD HH:mm:ss"
              value-format="YYYY-MM-DD HH:mm:ss"
              @change="handleFilter"
              style="width: 100%"
            />
          </el-col>
          
          <el-col :xs="12" :sm="4" :md="3">
            <el-button @click="resetFilters">
              <el-icon><RefreshLeft /></el-icon>
              重置
            </el-button>
          </el-col>
          
          <el-col :xs="12" :sm="4" :md="3">
            <el-button @click="toggleAutoRefresh" :type="autoRefresh ? 'primary' : 'default'">
              <el-icon><Timer /></el-icon>
              {{ autoRefresh ? '停止' : '自动' }}
            </el-button>
          </el-col>
        </el-row>
      </el-card>
    </div>
    
    <!-- 日志列表 -->
    <div class="logs-list">
      <el-card shadow="never">
        <div class="list-header">
          <h3>日志列表</h3>
          <div class="list-actions">
            <el-button-group>
              <el-button
                :type="viewMode === 'table' ? 'primary' : 'default'"
                @click="viewMode = 'table'"
              >
                <el-icon><List /></el-icon>
                表格
              </el-button>
              <el-button
                :type="viewMode === 'raw' ? 'primary' : 'default'"
                @click="viewMode = 'raw'"
              >
                <el-icon><Document /></el-icon>
                原始
              </el-button>
            </el-button-group>
          </div>
        </div>
        
        <!-- 表格视图 -->
        <div v-if="viewMode === 'table'" class="table-view">
          <el-table
            :data="filteredLogs"
            v-loading="loading"
            stripe
            :row-class-name="getRowClassName"
            @row-click="viewLogDetail"
            style="cursor: pointer"
          >
            <el-table-column prop="timestamp" label="时间" width="180" sortable>
              <template #default="{ row }">
                {{ formatDate(row.timestamp) }}
              </template>
            </el-table-column>
            
            <el-table-column prop="level" label="级别" width="80">
              <template #default="{ row }">
                <el-tag
                  :type="getLevelTagType(row.level)"
                  size="small"
                >
                  {{ row.level.toUpperCase() }}
                </el-tag>
              </template>
            </el-table-column>
            
            <el-table-column prop="module" label="模块" width="100">
              <template #default="{ row }">
                <el-tag size="small" effect="plain">
                  {{ getModuleLabel(row.module) }}
                </el-tag>
              </template>
            </el-table-column>
            
            <el-table-column prop="message" label="消息" min-width="300">
              <template #default="{ row }">
                <div class="log-message">
                  <span class="message-text">{{ row.message }}</span>
                  <div v-if="row.user" class="message-meta">
                    <el-icon><User /></el-icon>
                    {{ row.user }}
                  </div>
                </div>
              </template>
            </el-table-column>
            
            <el-table-column prop="source" label="来源" width="120">
              <template #default="{ row }">
                {{ row.source || '-' }}
              </template>
            </el-table-column>
            
            <el-table-column prop="request_id" label="请求ID" width="120">
              <template #default="{ row }">
                <code v-if="row.request_id" class="request-id">
                  {{ row.request_id.slice(0, 8) }}...
                </code>
                <span v-else>-</span>
              </template>
            </el-table-column>
            
            <el-table-column label="操作" width="100" fixed="right">
              <template #default="{ row }">
                <el-button
                  size="small"
                  @click.stop="viewLogDetail(row)"
                >
                  详情
                </el-button>
              </template>
            </el-table-column>
          </el-table>
        </div>
        
        <!-- 原始日志视图 -->
        <div v-else class="raw-view">
          <div class="raw-logs" ref="rawLogsRef">
            <div
              v-for="log in filteredLogs"
              :key="log.id"
              :class="['log-line', `log-${log.level}`]"
              @click="viewLogDetail(log)"
            >
              <span class="log-timestamp">{{ formatDate(log.timestamp) }}</span>
              <span class="log-level">[{{ log.level.toUpperCase() }}]</span>
              <span class="log-module">[{{ getModuleLabel(log.module) }}]</span>
              <span class="log-message">{{ log.message }}</span>
              <span v-if="log.request_id" class="log-request-id">({{ log.request_id }})</span>
            </div>
          </div>
        </div>
        
        <!-- 分页 -->
        <div class="pagination-wrapper" v-if="filteredLogs.length > 0">
          <el-pagination
            v-model:current-page="pagination.currentPage"
            v-model:page-size="pagination.pageSize"
            :page-sizes="[50, 100, 200, 500]"
            :total="pagination.total"
            layout="total, sizes, prev, pager, next, jumper"
            @size-change="handleSizeChange"
            @current-change="handleCurrentChange"
          />
        </div>
      </el-card>
    </div>
    
    <!-- 日志详情对话框 -->
    <el-dialog
      v-model="detailDialogVisible"
      title="日志详情"
      width="800px"
      top="5vh"
    >
      <div v-if="selectedLog" class="log-detail">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="时间">
            {{ formatDate(selectedLog.timestamp) }}
          </el-descriptions-item>
          <el-descriptions-item label="级别">
            <el-tag
              :type="getLevelTagType(selectedLog.level)"
              size="small"
            >
              {{ selectedLog.level.toUpperCase() }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="模块">
            {{ getModuleLabel(selectedLog.module) }}
          </el-descriptions-item>
          <el-descriptions-item label="来源">
            {{ selectedLog.source || '-' }}
          </el-descriptions-item>
          <el-descriptions-item label="用户">
            {{ selectedLog.user || '-' }}
          </el-descriptions-item>
          <el-descriptions-item label="请求ID">
            <code v-if="selectedLog.request_id">{{ selectedLog.request_id }}</code>
            <span v-else>-</span>
          </el-descriptions-item>
          <el-descriptions-item label="IP地址">
            {{ selectedLog.ip || '-' }}
          </el-descriptions-item>
          <el-descriptions-item label="用户代理">
            {{ selectedLog.user_agent || '-' }}
          </el-descriptions-item>
        </el-descriptions>
        
        <div class="log-message-detail">
          <h4>消息内容</h4>
          <div class="message-content">
            {{ selectedLog.message }}
          </div>
        </div>
        
        <div v-if="selectedLog.stack_trace" class="stack-trace">
          <h4>堆栈跟踪</h4>
          <pre class="stack-content">{{ selectedLog.stack_trace }}</pre>
        </div>
        
        <div v-if="selectedLog.context" class="log-context">
          <h4>上下文信息</h4>
          <pre class="context-content">{{ JSON.stringify(selectedLog.context, null, 2) }}</pre>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted, onUnmounted, nextTick } from 'vue'
import { ElMessage } from 'element-plus'
import {
  Document,
  Download,
  Refresh,
  WarningFilled,
  Warning,
  Calendar,
  Search,
  RefreshLeft,
  Timer,
  List,
  User
} from '@element-plus/icons-vue'

// 响应式数据
const loading = ref(false)
const exporting = ref(false)
const viewMode = ref('table')
const detailDialogVisible = ref(false)
const selectedLog = ref(null)
const autoRefresh = ref(false)
const refreshTimer = ref(null)
const rawLogsRef = ref(null)

// 统计数据
const stats = reactive({
  total: 15678,
  errors: 23,
  warnings: 156,
  today: 2345
})

// 筛选条件
const filters = reactive({
  search: '',
  level: '',
  module: '',
  dateRange: null
})

// 分页
const pagination = reactive({
  currentPage: 1,
  pageSize: 50,
  total: 0
})

// 日志列表
const logs = ref([
  {
    id: '1',
    timestamp: '2024-01-21T10:30:15.123Z',
    level: 'info',
    module: 'api',
    message: '用户登录成功',
    source: 'auth.py:45',
    user: 'john_doe',
    request_id: 'req_1234567890abcdef',
    ip: '10.0.0.1',
    user_agent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    context: {
      user_id: '123',
      session_id: 'sess_abc123'
    }
  },
  {
    id: '2',
    timestamp: '2024-01-21T10:29:45.456Z',
    level: 'error',
    module: 'training',
    message: '模型训练失败: GPU内存不足',
    source: 'trainer.py:156',
    user: 'admin',
    request_id: 'req_2345678901bcdefg',
    ip: '10.0.0.2',
    user_agent: 'Python/3.9 requests/2.28.1',
    stack_trace: `Traceback (most recent call last):
  File "trainer.py", line 156, in train_model
    model.fit(X_train, y_train)
  File "torch/nn/modules/module.py", line 1194, in _call_impl
    return forward_call(*input, **kwargs)
RuntimeError: CUDA out of memory. Tried to allocate 2.00 GiB`,
    context: {
      model_id: 'model_456',
      gpu_id: 0,
      memory_used: '6.5GB',
      memory_total: '8GB'
    }
  },
  {
    id: '3',
    timestamp: '2024-01-21T10:28:30.789Z',
    level: 'warn',
    module: 'deployment',
    message: '部署服务响应时间过长',
    source: 'deploy.py:89',
    user: 'system',
    request_id: 'req_3456789012cdefgh',
    ip: '10.0.0.3',
    user_agent: 'Kubernetes/1.25.0',
    context: {
      service_name: 'model-api',
      response_time: '5.2s',
      threshold: '3.0s'
    }
  },
  {
    id: '4',
    timestamp: '2024-01-21T10:27:12.345Z',
    level: 'debug',
    module: 'database',
    message: 'SQL查询执行完成',
    source: 'db.py:234',
    user: null,
    request_id: 'req_4567890123defghi',
    ip: null,
    user_agent: null,
    context: {
      query: 'SELECT * FROM models WHERE status = "active"',
      execution_time: '0.045s',
      rows_returned: 15
    }
  },
  {
    id: '5',
    timestamp: '2024-01-21T10:26:55.678Z',
    level: 'info',
    module: 'user',
    message: '新用户注册',
    source: 'user.py:67',
    user: null,
    request_id: 'req_5678901234efghij',
    ip: '203.0.113.45',
    user_agent: 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15',
    context: {
      username: 'new_user_123',
      email: 'user@example.com',
      registration_source: 'web'
    }
  },
  {
    id: '6',
    timestamp: '2024-01-21T10:25:40.901Z',
    level: 'fatal',
    module: 'system',
    message: '系统启动失败: 配置文件损坏',
    source: 'main.py:12',
    user: null,
    request_id: null,
    ip: null,
    user_agent: null,
    stack_trace: `Traceback (most recent call last):
  File "main.py", line 12, in <module>
    config = load_config("config.yaml")
  File "config.py", line 45, in load_config
    return yaml.safe_load(file)
yaml.scanner.ScannerError: mapping values are not allowed here`,
    context: {
      config_file: 'config.yaml',
      error_line: 23
    }
  }
])

// 计算属性
const filteredLogs = computed(() => {
  let result = [...logs.value]
  
  // 搜索过滤
  if (filters.search) {
    const search = filters.search.toLowerCase()
    result = result.filter(log => 
      log.message.toLowerCase().includes(search) ||
      log.module.toLowerCase().includes(search) ||
      (log.user && log.user.toLowerCase().includes(search)) ||
      (log.source && log.source.toLowerCase().includes(search))
    )
  }
  
  // 级别过滤
  if (filters.level) {
    result = result.filter(log => log.level === filters.level)
  }
  
  // 模块过滤
  if (filters.module) {
    result = result.filter(log => log.module === filters.module)
  }
  
  // 时间范围过滤
  if (filters.dateRange && filters.dateRange.length === 2) {
    const [start, end] = filters.dateRange
    result = result.filter(log => {
      const logTime = new Date(log.timestamp)
      return logTime >= new Date(start) && logTime <= new Date(end)
    })
  }
  
  // 按时间倒序排序
  result.sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime())
  
  pagination.total = result.length
  
  // 分页
  const start = (pagination.currentPage - 1) * pagination.pageSize
  const end = start + pagination.pageSize
  return result.slice(start, end)
})

// 方法
const formatNumber = (num: number) => {
  return num.toLocaleString()
}

const formatDate = (date: string) => {
  return new Date(date).toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
    fractionalSecondDigits: 3
  })
}

const getLevelTagType = (level: string) => {
  const types = {
    debug: 'info',
    info: 'success',
    warn: 'warning',
    error: 'danger',
    fatal: 'danger'
  }
  return types[level] || 'info'
}

const getModuleLabel = (module: string) => {
  const labels = {
    api: 'API',
    training: '训练',
    deployment: '部署',
    user: '用户',
    system: '系统',
    database: '数据库'
  }
  return labels[module] || module
}

const getRowClassName = ({ row }) => {
  return `log-row-${row.level}`
}

const handleSearch = () => {
  pagination.currentPage = 1
}

const handleFilter = () => {
  pagination.currentPage = 1
}

const resetFilters = () => {
  filters.search = ''
  filters.level = ''
  filters.module = ''
  filters.dateRange = null
  pagination.currentPage = 1
}

const handleSizeChange = (size: number) => {
  pagination.pageSize = size
  pagination.currentPage = 1
}

const handleCurrentChange = (page: number) => {
  pagination.currentPage = page
  
  // 原始日志视图自动滚动到顶部
  if (viewMode.value === 'raw') {
    nextTick(() => {
      if (rawLogsRef.value) {
        rawLogsRef.value.scrollTop = 0
      }
    })
  }
}

const viewLogDetail = (log: any) => {
  selectedLog.value = log
  detailDialogVisible.value = true
}

const toggleAutoRefresh = () => {
  autoRefresh.value = !autoRefresh.value
  
  if (autoRefresh.value) {
    startAutoRefresh()
  } else {
    stopAutoRefresh()
  }
}

const startAutoRefresh = () => {
  refreshTimer.value = setInterval(() => {
    loadLogs(false)
  }, 5000) // 每5秒刷新一次
}

const stopAutoRefresh = () => {
  if (refreshTimer.value) {
    clearInterval(refreshTimer.value)
    refreshTimer.value = null
  }
}

const loadLogs = async (showLoading = true) => {
  if (showLoading) {
    loading.value = true
  }
  
  try {
    // 这里应该调用实际的API加载日志数据
    await new Promise(resolve => setTimeout(resolve, 500))
    
    // 模拟新日志数据
    if (!showLoading) {
      // 自动刷新时添加新日志
      const newLog = {
        id: Date.now().toString(),
        timestamp: new Date().toISOString(),
        level: ['info', 'warn', 'error'][Math.floor(Math.random() * 3)],
        module: ['api', 'training', 'deployment'][Math.floor(Math.random() * 3)],
        message: '这是一条新的日志消息',
        source: 'auto_refresh.py:1',
        user: 'system',
        request_id: `req_${Date.now()}`,
        ip: '127.0.0.1',
        user_agent: 'Auto Refresh',
        context: {
          auto_generated: true
        }
      }
      logs.value.unshift(newLog)
      
      // 限制日志数量
      if (logs.value.length > 1000) {
        logs.value = logs.value.slice(0, 1000)
      }
    }
    
    // 更新统计数据
    stats.total = logs.value.length
    stats.errors = logs.value.filter(l => l.level === 'error' || l.level === 'fatal').length
    stats.warnings = logs.value.filter(l => l.level === 'warn').length
    
    const today = new Date().toDateString()
    stats.today = logs.value.filter(l => new Date(l.timestamp).toDateString() === today).length
  } catch (error) {
    console.error('加载日志失败:', error)
    ElMessage.error('加载失败，请稍后重试')
  } finally {
    if (showLoading) {
      loading.value = false
    }
  }
}

const exportLogs = async () => {
  exporting.value = true
  try {
    // 这里应该调用实际的API导出日志
    await new Promise(resolve => setTimeout(resolve, 2000))
    
    // 模拟导出
    const dataStr = JSON.stringify(filteredLogs.value, null, 2)
    const dataBlob = new Blob([dataStr], { type: 'application/json' })
    const url = URL.createObjectURL(dataBlob)
    
    const link = document.createElement('a')
    link.href = url
    link.download = `logs_${new Date().toISOString().slice(0, 10)}.json`
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    
    URL.revokeObjectURL(url)
    
    ElMessage.success('日志导出成功')
  } catch (error) {
    console.error('导出日志失败:', error)
    ElMessage.error('导出失败，请稍后重试')
  } finally {
    exporting.value = false
  }
}

onMounted(() => {
  loadLogs()
})

onUnmounted(() => {
  stopAutoRefresh()
})
</script>

<style lang="scss" scoped>
.logs-page {
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
          
          &.error {
            background: linear-gradient(135deg, #ff6b6b 0%, #ee5a24 100%);
          }
          
          &.warning {
            background: linear-gradient(135deg, #feca57 0%, #ff9ff3 100%);
          }
          
          &.today {
            background: linear-gradient(135deg, #48dbfb 0%, #0abde3 100%);
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
  
  .logs-list {
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
      .log-message {
        .message-text {
          display: block;
          margin-bottom: 4px;
        }
        
        .message-meta {
          display: flex;
          align-items: center;
          gap: 4px;
          font-size: 12px;
          color: var(--el-text-color-secondary);
        }
      }
      
      .request-id {
        background: var(--el-fill-color-light);
        padding: 2px 6px;
        border-radius: 4px;
        font-family: 'Courier New', monospace;
        font-size: 11px;
      }
    }
    
    .raw-view {
      .raw-logs {
        background: #1e1e1e;
        color: #d4d4d4;
        padding: 16px;
        border-radius: 6px;
        font-family: 'Courier New', monospace;
        font-size: 12px;
        line-height: 1.5;
        max-height: 600px;
        overflow-y: auto;
        
        .log-line {
          margin-bottom: 4px;
          cursor: pointer;
          padding: 2px 4px;
          border-radius: 2px;
          
          &:hover {
            background: rgba(255, 255, 255, 0.1);
          }
          
          .log-timestamp {
            color: #569cd6;
            margin-right: 8px;
          }
          
          .log-level {
            margin-right: 8px;
            font-weight: bold;
          }
          
          .log-module {
            color: #4ec9b0;
            margin-right: 8px;
          }
          
          .log-message {
            color: #d4d4d4;
          }
          
          .log-request-id {
            color: #808080;
            margin-left: 8px;
          }
          
          &.log-debug .log-level {
            color: #808080;
          }
          
          &.log-info .log-level {
            color: #4fc3f7;
          }
          
          &.log-warn .log-level {
            color: #ffb74d;
          }
          
          &.log-error .log-level {
            color: #f44336;
          }
          
          &.log-fatal .log-level {
            color: #d32f2f;
            background: rgba(211, 47, 47, 0.1);
          }
        }
      }
    }
    
    .pagination-wrapper {
      margin-top: 20px;
      text-align: center;
    }
  }
  
  .log-detail {
    .log-message-detail {
      margin: 20px 0;
      
      h4 {
        font-size: 16px;
        font-weight: 600;
        color: var(--el-text-color-primary);
        margin: 0 0 12px 0;
      }
      
      .message-content {
        background: var(--el-fill-color-light);
        padding: 12px;
        border-radius: 6px;
        border-left: 4px solid var(--el-color-primary);
        font-family: 'Courier New', monospace;
        white-space: pre-wrap;
        word-break: break-word;
      }
    }
    
    .stack-trace {
      margin: 20px 0;
      
      h4 {
        font-size: 16px;
        font-weight: 600;
        color: var(--el-text-color-primary);
        margin: 0 0 12px 0;
      }
      
      .stack-content {
        background: #1e1e1e;
        color: #d4d4d4;
        padding: 12px;
        border-radius: 6px;
        font-family: 'Courier New', monospace;
        font-size: 12px;
        line-height: 1.5;
        overflow-x: auto;
        white-space: pre;
      }
    }
    
    .log-context {
      margin: 20px 0;
      
      h4 {
        font-size: 16px;
        font-weight: 600;
        color: var(--el-text-color-primary);
        margin: 0 0 12px 0;
      }
      
      .context-content {
        background: var(--el-fill-color-light);
        padding: 12px;
        border-radius: 6px;
        font-family: 'Courier New', monospace;
        font-size: 12px;
        line-height: 1.5;
        overflow-x: auto;
        white-space: pre;
      }
    }
  }
}

// 表格行样式
:deep(.el-table) {
  .log-row-debug {
    background-color: rgba(144, 202, 249, 0.05);
  }
  
  .log-row-info {
    background-color: rgba(129, 199, 132, 0.05);
  }
  
  .log-row-warn {
    background-color: rgba(255, 183, 77, 0.05);
  }
  
  .log-row-error {
    background-color: rgba(244, 67, 54, 0.05);
  }
  
  .log-row-fatal {
    background-color: rgba(211, 47, 47, 0.1);
  }
}

// 响应式设计
@media (max-width: 768px) {
  .logs-page {
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
    
    .logs-list {
      .raw-view {
        .raw-logs {
          font-size: 10px;
          padding: 12px;
        }
      }
    }
  }
}

// 暗色主题
.dark {
  .logs-page {
    .logs-list {
      .raw-view {
        .raw-logs {
          background: #0d1117;
          color: #c9d1d9;
          
          .log-line {
            &:hover {
              background: rgba(255, 255, 255, 0.05);
            }
            
            .log-timestamp {
              color: #79c0ff;
            }
            
            .log-module {
              color: #7ee787;
            }
            
            .log-message {
              color: #c9d1d9;
            }
            
            .log-request-id {
              color: #8b949e;
            }
          }
        }
      }
    }
    
    .log-detail {
      .stack-trace {
        .stack-content {
          background: #0d1117;
          color: #c9d1d9;
        }
      }
    }
  }
}
</style>