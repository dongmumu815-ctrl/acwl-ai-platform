<template>
  <div class="task-instance-list">
    <div class="page-header">
      <div class="header-left">
        <h2>任务执行记录</h2>
        <p>查看所有任务的执行历史和状态</p>
      </div>
    </div>

    <div class="instances-content">
      <!-- 筛选条件 -->
      <el-card class="filter-card">
        <el-form :model="filterForm" inline>
          <el-form-item label="任务定义ID">
            <el-input 
              v-model="filterForm.taskDefinitionId" 
              placeholder="请输入任务定义ID" 
              clearable 
              style="width: 150px"
            />
          </el-form-item>
          <el-form-item label="状态">
            <el-select v-model="filterForm.status" placeholder="选择状态" clearable style="width: 120px">
              <el-option label="全部" value="" />
              <el-option label="等待中" value="pending" />
              <el-option label="运行中" value="running" />
              <el-option label="成功" value="success" />
              <el-option label="失败" value="failed" />
              <el-option label="已取消" value="cancelled" />
            </el-select>
          </el-form-item>
          <el-form-item label="时间范围">
            <el-date-picker
              v-model="filterForm.dateRange"
              type="datetimerange"
              range-separator="至"
              start-placeholder="开始时间"
              end-placeholder="结束时间"
              format="YYYY-MM-DD HH:mm:ss"
              value-format="YYYY-MM-DD HH:mm:ss"
              style="width: 350px"
            />
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

      <!-- 执行列表 -->
      <el-card class="list-card">
        <el-table
          v-loading="loading"
          :data="instanceList"
          stripe
          style="width: 100%"
        >
          <el-table-column prop="id" label="实例ID" width="100" />
          <el-table-column prop="instance_name" label="实例名称" min-width="200" show-overflow-tooltip />
          <el-table-column prop="task_definition_id" label="任务定义ID" width="120" />
          <el-table-column label="状态" width="100">
            <template #default="{ row }">
              <el-tag :type="getStatusType(row.status)">{{ getStatusText(row.status) }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="triggered_by" label="触发方式" width="120">
            <template #default="{ row }">
              <el-tag size="small" type="info">{{ row.triggered_by }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="actual_start_time" label="开始时间" width="180">
            <template #default="{ row }">
              {{ row.actual_start_time ? formatTime(row.actual_start_time) : '-' }}
            </template>
          </el-table-column>
          <el-table-column prop="actual_end_time" label="结束时间" width="180">
            <template #default="{ row }">
              {{ row.actual_end_time ? formatTime(row.actual_end_time) : '-' }}
            </template>
          </el-table-column>
          <el-table-column label="执行时长" width="120">
            <template #default="{ row }">
              {{ getDuration(row.actual_start_time, row.actual_end_time) }}
            </template>
          </el-table-column>
          <el-table-column label="操作" width="180" fixed="right">
            <template #default="{ row }">
              <el-button
                type="primary"
                size="small"
                text
                @click="viewInstanceLog(row)"
              >
                日志
              </el-button>
              <el-button
                type="primary"
                size="small"
                text
                @click="viewInstanceDetail(row)"
              >
                详情
              </el-button>
            </template>
          </el-table-column>
        </el-table>

        <!-- 分页 -->
        <div class="pagination-container">
          <el-pagination
            v-model:current-page="pagination.page"
            v-model:page-size="pagination.size"
            :total="pagination.total"
            :page-sizes="[10, 20, 50, 100]"
            layout="total, sizes, prev, pager, next, jumper"
            @size-change="handleSizeChange"
            @current-change="handleCurrentChange"
          />
        </div>
      </el-card>
    </div>

    <!-- 日志查看对话框 -->
    <el-dialog
      v-model="logDialogVisible"
      title="任务执行日志"
      width="70%"
      destroy-on-close
    >
      <div class="log-container" v-loading="logLoading">
        <pre v-if="currentLog">{{ currentLog }}</pre>
        <el-empty v-else description="暂无日志" />
      </div>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="logDialogVisible = false">关闭</el-button>
          <el-button type="primary" @click="refreshLog">刷新</el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Search, Refresh } from '@element-plus/icons-vue'
import { useTaskStore } from '@/stores/task'
import { formatTime, formatDuration } from '@/utils'

const router = useRouter()
const taskStore = useTaskStore()

const loading = ref(false)
const instanceList = ref([])

const filterForm = reactive({
  taskDefinitionId: '',
  status: '',
  dateRange: []
})

const pagination = reactive({
  page: 1,
  size: 20,
  total: 0
})

/**
 * 获取状态类型
 */
const getStatusType = (status) => {
  const map = {
    pending: 'info',
    running: 'primary',
    success: 'success',
    failed: 'danger',
    cancelled: 'warning'
  }
  return map[status] || 'info'
}

/**
 * 获取状态文本
 */
const getStatusText = (status) => {
  const map = {
    pending: '等待中',
    running: '运行中',
    success: '成功',
    failed: '失败',
    cancelled: '已取消'
  }
  return map[status] || status
}

/**
 * 获取执行时长
 */
const getDuration = (start, end) => {
  if (!start || !end) return '-'
  const startTime = new Date(start).getTime()
  const endTime = new Date(end).getTime()
  return formatDuration(endTime - startTime)
}

/**
 * 获取实例列表
 */
const fetchInstances = async () => {
  try {
    loading.value = true
    const params = {
      page: pagination.page,
      size: pagination.size,
      task_definition_id: filterForm.taskDefinitionId || undefined,
      status: filterForm.status || undefined,
      start_time: filterForm.dateRange?.[0],
      end_time: filterForm.dateRange?.[1]
    }
    
    const result = await taskStore.getAllTaskInstances(params)
    instanceList.value = result.items || []
    pagination.total = result.total || 0
  } catch (error) {
    ElMessage.error('获取任务实例列表失败')
  } finally {
    loading.value = false
  }
}

/**
 * 搜索
 */
const handleSearch = () => {
  pagination.page = 1
  fetchInstances()
}

/**
 * 重置
 */
const handleReset = () => {
  filterForm.taskDefinitionId = ''
  filterForm.status = ''
  filterForm.dateRange = []
  pagination.page = 1
  fetchInstances()
}

/**
 * 页面大小改变
 */
const handleSizeChange = (size) => {
  pagination.size = size
  pagination.page = 1
  fetchInstances()
}

/**
 * 当前页改变
 */
const handleCurrentChange = (page) => {
  pagination.page = page
  fetchInstances()
}

// 日志相关
const logDialogVisible = ref(false)
const logLoading = ref(false)
const currentLog = ref('')
const currentInstanceId = ref(null)

// 模拟日志数据 (待后端实现)
const mockLog = `[2024-01-20 10:00:00] INFO: Starting task execution...
[2024-01-20 10:00:01] INFO: Initializing environment...
[2024-01-20 10:00:02] INFO: Running script...
[2024-01-20 10:00:05] INFO: Task completed successfully.`

const viewInstanceLog = async (row) => {
  currentInstanceId.value = row.id
  logDialogVisible.value = true
  currentLog.value = '' // 清空旧日志
  await refreshLog()
}

const refreshLog = async () => {
  if (!currentInstanceId.value) return
  
  logLoading.value = true
  try {
    let content = ''
    let offset = 0
    let hasMore = true
    const MAX_SIZE = 100 * 1024 // 限制前端最大显示 100KB
    
    // 循环读取直到读完或达到限制
    while (hasMore && content.length < MAX_SIZE) {
      const res = await taskStore.getTaskInstanceLogFile(currentInstanceId.value, {
        start: offset,
        length: 10240 // 每次读取 10KB
      })
      
      if (res.content) {
        content += res.content
      }
      
      // 如果没有读取到内容，防止死循环
      if (res.length === 0) {
        break
      }
      
      offset += res.length
      hasMore = res.has_more
    }
    
    currentLog.value = content || '暂无日志内容'
    
    if (hasMore) {
      currentLog.value += '\n\n... (日志过长，仅显示前100KB)'
    }
  } catch (error) {
    console.error('获取日志失败', error)
    currentLog.value = `获取日志失败: ${error.message || '未知错误'}`
  } finally {
    logLoading.value = false
  }
}

/**
 * 查看实例详情
 */
const viewInstanceDetail = (row) => {
  // 暂时复用任务详情页的执行历史tab，或者跳转到专门的实例详情页
  // 这里我们假设跳转到任务详情页并定位到该实例
  router.push(`/tasks/${row.task_definition_id}`)
}

onMounted(() => {
  fetchInstances()
})
</script>

<style scoped>
.task-instance-list {
  padding: 20px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.filter-card {
  margin-bottom: 20px;
}

.list-card {
  min-height: 500px;
}

.pagination-container {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
}

.log-container {
  background-color: #1e1e1e;
  color: #d4d4d4;
  padding: 15px;
  border-radius: 4px;
  height: 500px;
  overflow-y: auto;
  font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
  font-size: 14px;
  white-space: pre-wrap;
  word-wrap: break-word;
}
</style>
