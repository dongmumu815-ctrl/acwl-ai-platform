<template>
  <div class="workflow-executions">
    <el-page-header :icon="null" content="工作流实例">
      <template #extra>
        <el-button @click="handleRefresh">
          <el-icon><Refresh /></el-icon>
          刷新
        </el-button>
      </template>
    </el-page-header>

    <div class="executions-content">
      <!-- 筛选条件 -->
      <el-card class="filter-card">
        <el-form :model="filterForm" inline>
          <el-form-item label="工作流ID">
            <el-input v-model="filterForm.workflow_id" placeholder="工作流ID" clearable style="width: 150px" />
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
          :data="executionList"
          stripe
          @row-click="viewExecutionDetail"
          style="cursor: pointer"
        >
          <el-table-column prop="id" label="执行ID" width="100" />
          <el-table-column prop="instance_name" label="实例名称" min-width="200" show-overflow-tooltip />
          <el-table-column prop="workflow_id" label="工作流ID" width="100" />
          <el-table-column label="状态" width="100">
            <template #default="{ row }">
              <el-tag :type="getStatusType(row.status)">{{ getStatusText(row.status) }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="triggered_by" label="触发方式" width="100">
            <template #default="{ row }">
              <el-tag size="small" :type="getTriggerType(row.triggered_by)">{{ getTriggerText(row.triggered_by) }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="actual_start_time" label="开始时间" width="180">
            <template #default="{ row }">
              {{ formatTime(row.actual_start_time) }}
            </template>
          </el-table-column>
          <el-table-column prop="actual_end_time" label="结束时间" width="180">
            <template #default="{ row }">
              {{ formatTime(row.actual_end_time) }}
            </template>
          </el-table-column>
          <el-table-column label="执行时长" width="100">
            <template #default="{ row }">
              {{ getDuration(row.actual_start_time, row.actual_end_time) }}
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
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Search, Refresh } from '@element-plus/icons-vue'
import { useWorkflowStore } from '@/stores/workflow'
import { formatTime } from '@/utils'
import { formatDistance } from 'date-fns'
import { zhCN } from 'date-fns/locale'

const router = useRouter()
const workflowStore = useWorkflowStore()

const loading = ref(false)
const executionList = ref([])

const filterForm = reactive({
  workflow_id: '',
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
    
    const params = {
      page: pagination.page,
      size: pagination.size,
      workflow_id: filterForm.workflow_id || undefined,
      status: filterForm.status || undefined,
      scheduled_start: filterForm.dateRange?.[0],
      scheduled_end: filterForm.dateRange?.[1]
    }
    
    const result = await workflowStore.getAllWorkflowExecutions(params)
    executionList.value = result.items || []
    pagination.total = result.total || 0
  } catch (error) {
    ElMessage.error('获取执行历史失败')
  } finally {
    loading.value = false
  }
}

/**
 * 刷新
 */
const handleRefresh = () => {
  fetchExecutions()
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
  filterForm.workflow_id = ''
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
  router.push(`/workflows/${row.workflow_id}/executions/${row.id}`)
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
    'scheduled': 'success',
    'event': 'warning',
    'api': 'info',
    'dependency': 'warning'
  }
  return typeMap[triggerType] || 'info'
}

/**
 * 获取触发文本
 */
const getTriggerText = (triggerType) => {
  const textMap = {
    'manual': '手动触发',
    'scheduled': '调度触发',
    'event': '事件触发',
    'api': 'API触发',
    'dependency': '依赖触发'
  }
  return textMap[triggerType] || triggerType
}

/**
 * 获取执行时长
 */
const getDuration = (start, end) => {
  if (!start || !end) return '-'
  return formatDistance(new Date(start), new Date(end), { locale: zhCN })
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

.pagination-container {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
}

.error-text {
  color: #F56C6C;
}

.success-text {
  color: #67C23A;
}
</style>