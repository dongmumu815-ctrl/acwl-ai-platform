<template>
  <div class="workflow-executions">
    <el-page-header @back="goBack" :content="`${workflowName} - 执行历史`">
      <template #extra>
        <el-button type="primary" @click="executeWorkflow" :loading="executing">
          <el-icon><VideoPlay /></el-icon>
          执行工作流
        </el-button>
      </template>
    </el-page-header>

    <div class="executions-content">
      <!-- 筛选条件 -->
      <el-card class="filter-card">
        <el-form :model="filterForm" inline>
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
          :data="executionList"
          stripe
          @row-click="viewExecutionDetail"
          style="cursor: pointer"
        >
          <el-table-column prop="id" label="执行ID" width="100" />
          <el-table-column label="状态" width="100">
            <template #default="{ row }">
              <el-tag :type="getStatusType(row.status)">{{ getStatusText(row.status) }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="trigger_type" label="触发方式" width="100">
            <template #default="{ row }">
              <el-tag size="small" :type="getTriggerType(row.trigger_type)">{{ getTriggerText(row.trigger_type) }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="started_at" label="开始时间" width="180">
            <template #default="{ row }">
              {{ formatTime(row.started_at) }}
            </template>
          </el-table-column>
          <el-table-column prop="finished_at" label="结束时间" width="180">
            <template #default="{ row }">
              {{ formatTime(row.finished_at) }}
            </template>
          </el-table-column>
          <el-table-column label="执行时长" width="100">
            <template #default="{ row }">
              {{ getDuration(row.started_at, row.finished_at) }}
            </template>
          </el-table-column>
          <el-table-column prop="progress" label="进度" width="120">
            <template #default="{ row }">
              <el-progress
                :percentage="row.progress || 0"
                :status="getProgressStatus(row.status)"
                :stroke-width="6"
              />
            </template>
          </el-table-column>
          <el-table-column prop="error_message" label="错误信息" min-width="200" show-overflow-tooltip>
            <template #default="{ row }">
              <span v-if="row.error_message" class="error-text">{{ row.error_message }}</span>
              <span v-else class="success-text">-</span>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="150" fixed="right">
            <template #default="{ row }">
              <el-button
                type="primary"
                size="small"
                text
                @click.stop="viewExecutionDetail(row)"
              >
                查看详情
              </el-button>
              <el-button
                v-if="row.status === 'running'"
                type="danger"
                size="small"
                text
                @click.stop="cancelExecution(row)"
              >
                取消执行
              </el-button>
              <el-button
                v-if="['failed', 'cancelled'].includes(row.status)"
                type="warning"
                size="small"
                text
                @click.stop="retryExecution(row)"
              >
                重新执行
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
  </div>
</template>

<script setup>
import { ref, onMounted, reactive } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { VideoPlay, Search, Refresh } from '@element-plus/icons-vue'
import { useWorkflowStore } from '@/stores/workflow'
import { formatTime } from '@/utils'

const route = useRoute()
const router = useRouter()
const workflowStore = useWorkflowStore()

const loading = ref(false)
const executing = ref(false)
const workflowName = ref('')
const executionList = ref([])

const filterForm = reactive({
  status: '',
  dateRange: []
})

const pagination = reactive({
  page: 1,
  size: 20,
  total: 0
})

/**
 * 获取执行列表
 */
const fetchExecutions = async () => {
  try {
    loading.value = true
    const workflowId = route.params.id
    
    const params = {
      page: pagination.page,
      size: pagination.size,
      status: filterForm.status,
      start_time: filterForm.dateRange?.[0],
      end_time: filterForm.dateRange?.[1]
    }
    
    const result = await workflowStore.getWorkflowExecutions(workflowId, params)
    executionList.value = result.items || []
    pagination.total = result.total || 0
    
    // 获取工作流名称
    if (!workflowName.value) {
      const workflow = await workflowStore.getWorkflowDetail(workflowId)
      workflowName.value = workflow.name
    }
  } catch (error) {
    ElMessage.error('获取执行历史失败')
  } finally {
    loading.value = false
  }
}

/**
 * 返回上一页
 */
const goBack = () => {
  router.back()
}

/**
 * 执行工作流
 */
const executeWorkflow = async () => {
  try {
    executing.value = true
    const workflowId = route.params.id
    await workflowStore.executeWorkflow(workflowId)
    ElMessage.success('工作流执行成功')
    // 刷新列表
    fetchExecutions()
  } catch (error) {
    ElMessage.error('工作流执行失败')
  } finally {
    executing.value = false
  }
}

/**
 * 搜索
 */
const handleSearch = () => {
  pagination.page = 1
  fetchExecutions()
}

/**
 * 重置
 */
const handleReset = () => {
  filterForm.status = ''
  filterForm.dateRange = []
  pagination.page = 1
  fetchExecutions()
}

/**
 * 页面大小改变
 */
const handleSizeChange = (size) => {
  pagination.size = size
  pagination.page = 1
  fetchExecutions()
}

/**
 * 当前页改变
 */
const handleCurrentChange = (page) => {
  pagination.page = page
  fetchExecutions()
}

/**
 * 查看执行详情
 */
const viewExecutionDetail = (row) => {
  const workflowId = route.params.id
  router.push(`/workflows/${workflowId}/executions/${row.id}`)
}

/**
 * 取消执行
 */
const cancelExecution = async (row) => {
  try {
    await ElMessageBox.confirm('确定要取消这次执行吗？', '确认取消', {
      type: 'warning'
    })
    
    await workflowStore.cancelExecution(row.id)
    ElMessage.success('执行已取消')
    fetchExecutions()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('取消执行失败')
    }
  }
}

/**
 * 重新执行
 */
const retryExecution = async (row) => {
  try {
    const workflowId = route.params.id
    await workflowStore.executeWorkflow(workflowId)
    ElMessage.success('重新执行成功')
    fetchExecutions()
  } catch (error) {
    ElMessage.error('重新执行失败')
  }
}

/**
 * 获取状态类型
 */
const getStatusType = (status) => {
  const statusMap = {
    'pending': 'info',
    'running': 'warning',
    'success': 'success',
    'failed': 'danger',
    'cancelled': 'info'
  }
  return statusMap[status] || 'info'
}

/**
 * 获取状态文本
 */
const getStatusText = (status) => {
  const statusMap = {
    'pending': '等待中',
    'running': '运行中',
    'success': '成功',
    'failed': '失败',
    'cancelled': '已取消'
  }
  return statusMap[status] || status
}

/**
 * 获取触发类型
 */
const getTriggerType = (triggerType) => {
  const typeMap = {
    'manual': 'primary',
    'schedule': 'success',
    'event': 'warning'
  }
  return typeMap[triggerType] || 'info'
}

/**
 * 获取触发文本
 */
const getTriggerText = (triggerType) => {
  const typeMap = {
    'manual': '手动',
    'schedule': '定时',
    'event': '事件'
  }
  return typeMap[triggerType] || triggerType
}

/**
 * 获取进度状态
 */
const getProgressStatus = (status) => {
  const statusMap = {
    'success': 'success',
    'failed': 'exception',
    'cancelled': 'exception'
  }
  return statusMap[status]
}

/**
 * 计算执行时长
 */
const getDuration = (startTime, endTime) => {
  if (!startTime || !endTime) return '-'
  
  const start = new Date(startTime)
  const end = new Date(endTime)
  const duration = Math.floor((end - start) / 1000)
  
  if (duration < 60) {
    return `${duration}秒`
  } else if (duration < 3600) {
    return `${Math.floor(duration / 60)}分${duration % 60}秒`
  } else {
    const hours = Math.floor(duration / 3600)
    const minutes = Math.floor((duration % 3600) / 60)
    return `${hours}时${minutes}分`
  }
}

onMounted(() => {
  fetchExecutions()
})
</script>

<style scoped>
.workflow-executions {
  padding: 20px;
}

.executions-content {
  margin-top: 20px;
}

.filter-card {
  margin-bottom: 20px;
}

.list-card {
  margin-bottom: 20px;
}

.error-text {
  color: var(--el-color-danger);
}

.success-text {
  color: var(--el-text-color-placeholder);
}

.pagination-container {
  display: flex;
  justify-content: center;
  margin-top: 20px;
}

:deep(.el-table__row) {
  cursor: pointer;
}

:deep(.el-table__row:hover) {
  background-color: var(--el-table-row-hover-bg-color);
}
</style>