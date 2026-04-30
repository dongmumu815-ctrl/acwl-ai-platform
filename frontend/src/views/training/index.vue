<template>
  <div class="training-page">
    <div class="page-header">
      <div class="header-content">
        <div class="header-left">
          <h1 class="page-title">
            <el-icon><TrendCharts /></el-icon>
            微调任务管理
          </h1>
          <p class="page-description">管理和监控您的模型微调任务</p>
        </div>
        <div class="header-right">
          <el-button type="primary" @click="createTraining">
            <el-icon><Plus /></el-icon>
            创建微调任务
          </el-button>
          <el-button @click="refreshTrainings">
            <el-icon><Refresh /></el-icon>
            刷新
          </el-button>
        </div>
      </div>
    </div>

    <div class="stats-cards">
      <el-row :gutter="20">
        <el-col :xs="12" :sm="6">
          <div class="stat-card">
            <div class="stat-icon total">
              <el-icon><TrendCharts /></el-icon>
            </div>
            <div class="stat-content">
              <div class="stat-value">{{ stats.total }}</div>
              <div class="stat-label">总任务数</div>
            </div>
          </div>
        </el-col>
        <el-col :xs="12" :sm="6">
          <div class="stat-card">
            <div class="stat-icon running">
              <el-icon><Loading /></el-icon>
            </div>
            <div class="stat-content">
              <div class="stat-value">{{ stats.running }}</div>
              <div class="stat-label">运行中</div>
            </div>
          </div>
        </el-col>
        <el-col :xs="12" :sm="6">
          <div class="stat-card">
            <div class="stat-icon completed">
              <el-icon><CircleCheck /></el-icon>
            </div>
            <div class="stat-content">
              <div class="stat-value">{{ stats.completed }}</div>
              <div class="stat-label">已完成</div>
            </div>
          </div>
        </el-col>
        <el-col :xs="12" :sm="6">
          <div class="stat-card">
            <div class="stat-icon failed">
              <el-icon><CircleClose /></el-icon>
            </div>
            <div class="stat-content">
              <div class="stat-value">{{ stats.failed }}</div>
              <div class="stat-label">失败</div>
            </div>
          </div>
        </el-col>
      </el-row>
    </div>

    <div class="filter-section">
      <el-card shadow="never">
        <el-form :model="filters" inline>
          <el-form-item label="搜索">
            <el-input
              v-model="filters.search"
              placeholder="搜索任务名称"
              clearable
              style="width: 200px"
              @input="handleSearch"
            >
              <template #prefix>
                <el-icon><Search /></el-icon>
              </template>
            </el-input>
          </el-form-item>

          <el-form-item label="状态">
            <el-select
              v-model="filters.status"
              placeholder="选择状态"
              clearable
              style="width: 120px"
              @change="handleFilter"
            >
              <el-option label="全部" value="" />
              <el-option label="等待中" value="pending" />
              <el-option label="队列中" value="queued" />
              <el-option label="运行中" value="running" />
              <el-option label="已完成" value="completed" />
              <el-option label="已失败" value="failed" />
              <el-option label="已取消" value="cancelled" />
            </el-select>
          </el-form-item>

          <el-form-item label="微调方法">
            <el-select
              v-model="filters.method"
              placeholder="选择方法"
              clearable
              style="width: 120px"
              @change="handleFilter"
            >
              <el-option label="全部" value="" />
              <el-option label="LoRA" value="lora" />
              <el-option label="QLoRA" value="qlora" />
              <el-option label="全量" value="full" />
              <el-option label="Adaptor" value="adaptor" />
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

    <div class="training-list">
      <el-card shadow="never">
        <el-table
          v-loading="loading"
          :data="paginatedTrainings"
          style="width: 100%"
        >
          <!-- <el-table-column prop="job_id" label="任务ID" width="200">
            <template #default="{ row }">
              <span class="job-id">{{ row.job_id }}</span>
            </template>
          </el-table-column> -->

          <el-table-column prop="job_name" label="任务名称" width="250">
            <template #default="{ row }">
              <div class="job-name-cell">
                <span class="name">{{ row.job_name }}</span>
                <span class="model-name" v-if="row.base_model_name">
                  基础模型: {{ row.base_model_name }}
                </span>
              </div>
            </template>
          </el-table-column>

          <el-table-column prop="method" label="方法" width="100">
            <template #default="{ row }">
              <el-tag size="small">{{ getMethodText(row.method) }}</el-tag>
            </template>
          </el-table-column>

          <el-table-column prop="dataset_name" label="数据集" width="150">
            <template #default="{ row }">
              {{ row.dataset_name }}
            </template>
          </el-table-column>

          <el-table-column prop="status" label="状态" width="100">
            <template #default="{ row }">
              <el-tag
                :type="getStatusType(row.status)"
                :class="{ 'status-running': row.status === 'running' }"
              >
                {{ getStatusText(row.status) }}
              </el-tag>
            </template>
          </el-table-column>

          <el-table-column prop="progress" label="进度" width="100">
            <template #default="{ row }">
              <div class="progress-cell">
                <el-progress
                  :percentage="row.progress"
                  :status="getProgressStatus(row.status)"
                  :stroke-width="8"
                  :show-text="false"
                />
                <span class="progress-text">{{ row.progress }}%</span>
              </div>
            </template>
          </el-table-column>

          <el-table-column prop="total_epochs" label="Epochs" width="90">
            <template #default="{ row }">
              {{ row.current_epoch || 0 }} / {{ row.total_epochs }}
            </template>
          </el-table-column>

          <el-table-column prop="created_at" label="创建时间" width="160">
            <template #default="{ row }">
              {{ formatDate(row.created_at) }}
            </template>
          </el-table-column>

          <el-table-column label="操作" width="380" fixed="right">
            <template #default="{ row }">
              <el-button
                v-if="row.status === 'pending' || row.status === 'failed'"
                type="primary"
                size="small"
                @click="startTraining(row)"
              >
                启动
              </el-button>
              <el-button
                v-if="row.status === 'pending'"
                type="default"
                size="small"
                @click="editTraining(row)"
              >
                编辑
              </el-button>
              <el-button
                v-if="row.status === 'running' || row.status === 'queued'"
                type="warning"
                size="small"
                @click="cancelTraining(row)"
              >
                取消
              </el-button>
              <el-button
                size="small"
                @click="viewLogs(row)"
              >
                日志
              </el-button>
              <el-button
                size="small"
                type="info"
                @click="viewCommand(row)"
              >
                命令
              </el-button>
              <el-button
                size="small"
                type="success"
                @click="viewCurves(row)"
              >
                曲线
              </el-button>
              <el-button
                size="small"
                type="warning"
                @click="viewChat(row)"
              >
                测试
              </el-button>
              <el-button
                size="small"
                type="danger"
                @click="deleteTraining(row)"
              >
                删除
              </el-button>
            </template>
          </el-table-column>
        </el-table>

        <div class="pagination-wrapper">
          <el-pagination
            v-model:current-page="pagination.currentPage"
            v-model:page-size="pagination.pageSize"
            :page-sizes="[10, 20, 50, 100]"
            :total="filteredTrainings.length"
            layout="total, sizes, prev, pager, next, jumper"
            @size-change="handleSizeChange"
            @current-change="handleCurrentChange"
          />
        </div>
      </el-card>
    </div>

    <el-drawer v-model="logDrawerVisible" title="任务日志" direction="rtl" size="80%" :with-header="true">
      <template #title>
        <span>任务日志 - {{ currentLogJob?.job_name }}</span>
        <el-button type="primary" size="small" style="margin-left: 16px" @click="refreshLogs">
          刷新
        </el-button>
      </template>
      <div class="log-content">
        <pre ref="logPreRef">{{ logContent }}</pre>
      </div>
    </el-drawer>

    <el-drawer v-model="commandDrawerVisible" title="运行命令" direction="rtl" size="50%" :with-header="true">
      <template #title>
        <span>运行命令 - {{ currentCommandJob?.job_name }}</span>
      </template>
      <div class="command-content">
        <pre>{{ commandContent }}</pre>
        <el-button type="primary" @click="copyCommand">复制命令</el-button>
      </div>
    </el-drawer>

    <el-drawer v-model="curvesDrawerVisible" title="训练曲线" direction="rtl" size="60%" :with-header="true">
      <template #title>
        <span>训练曲线 - {{ currentCurvesJob?.job_name }}</span>
        <el-button type="primary" size="small" style="margin-left: 16px" @click="refreshCurves">
          刷新
        </el-button>
      </template>
      <div class="curves-content">
        <div class="curve-chart" ref="lossChartRef"></div>
        <div class="curve-chart" ref="accChartRef"></div>
        <div class="curve-chart" ref="lrChartRef"></div>
        <div class="curve-chart" ref="epochChartRef"></div>
        <div class="curve-chart" ref="gradNormChartRef"></div>
      </div>
    </el-drawer>

    <el-drawer v-model="chatDrawerVisible" title="模型对话测试" direction="rtl" size="50%" :with-header="true">
      <template #title>
        <span>模型对话 - {{ currentChatJob?.job_name }}</span>
        <el-tag v-if="currentChatJob?.model_status === 'running'" type="success" style="margin-left: 8px">服务运行中</el-tag>
        <el-tag v-else type="danger" style="margin-left: 8px">服务已停止</el-tag>
        <el-button
          v-if="currentChatJob?.model_status !== 'running' && currentChatJob?.status === 'completed'"
          type="success"
          size="small"
          style="margin-left: 16px"
          @click="startModelService"
        >
          启动服务
        </el-button>
        <el-button
          v-if="currentChatJob?.model_status === 'running'"
          type="warning"
          size="small"
          style="margin-left: 16px"
          @click="stopModelService"
        >
          停止服务
        </el-button>
      </template>
      <div class="chat-container">
        <template v-if="currentChatJob?.model_status === 'running'">
          <el-alert
            title="模型服务已启动"
            type="success"
            :closable="false"
            style="margin-bottom: 16px"
          >
            <template #default>
              <p>服务地址: {{ `http://${currentChatJob?.server_ip}:${currentChatJob?.model_service_port}` }}</p>
            </template>
          </el-alert>
          <div class="chat-messages" ref="chatMessagesRef">
            <div v-for="(msg, index) in chatMessages" :key="index" :class="['chat-message', msg.role]">
              <div class="message-avatar">{{ msg.role === 'user' ? '我' : 'AI' }}</div>
              <div class="message-content">{{ msg.content }}</div>
            </div>
          </div>
          <div class="chat-input">
            <el-input
              v-model="chatInput"
              type="textarea"
              :rows="4"
              resize="none"
              placeholder="输入消息... (Enter发送, Shift+Enter换行)"
              @keydown.enter="handleEnterKey"
            />
            <el-button type="primary" @click="sendChatMessage" :loading="chatLoading">发送</el-button>
          </div>
        </template>
        <template v-else>
          <el-alert
            title="模型服务未启动"
            type="warning"
            :closable="false"
            style="margin-bottom: 16px"
          >
            请先启动模型服务后再进行对话测试
          </el-alert>
        </template>
      </div>
    </el-drawer>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted, onUnmounted, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  TrendCharts,
  Plus,
  Refresh,
  Loading,
  CircleCheck,
  CircleClose,
  Monitor,
  Search,
  RefreshLeft
} from '@element-plus/icons-vue'
import { fineTuningApi, type FineTuningJob, FineTuningStatus, FineTuningMethod } from '@/api/training'
import * as echarts from 'echarts'

const router = useRouter()

const viewMode = ref('list')
let refreshTimer: NodeJS.Timeout | null = null

const stats = reactive({
  total: 0,
  running: 0,
  completed: 0,
  failed: 0
})

const filters = reactive({
  search: '',
  status: '',
  method: ''
})

const pagination = reactive({
  currentPage: 1,
  pageSize: 20,
  total: 0
})

const trainings = ref<FineTuningJob[]>([])
const loading = ref(false)
const logDrawerVisible = ref(false)
const logContent = ref('')
const currentLogJob = ref<FineTuningJob | null>(null)
const logPreRef = ref<HTMLPreElement | null>(null)
const commandDrawerVisible = ref(false)
const commandContent = ref('')
const currentCommandJob = ref<FineTuningJob | null>(null)

const curvesDrawerVisible = ref(false)
const currentCurvesJob = ref<FineTuningJob | null>(null)
const chatDrawerVisible = ref(false)
const currentChatJob = ref<FineTuningJob | null>(null)
const chatMessages = ref<{ role: string; content: string }[]>([])
const chatInput = ref('')
const chatLoading = ref(false)
const chatMessagesRef = ref<HTMLDivElement | null>(null)
const lossChartRef = ref<HTMLDivElement | null>(null)
const accChartRef = ref<HTMLDivElement | null>(null)
const lrChartRef = ref<HTMLDivElement | null>(null)
const epochChartRef = ref<HTMLDivElement | null>(null)
const gradNormChartRef = ref<HTMLDivElement | null>(null)
let lossChart: echarts.ECharts | null = null
let accChart: echarts.ECharts | null = null
let lrChart: echarts.ECharts | null = null
let epochChart: echarts.ECharts | null = null
let gradNormChart: echarts.ECharts | null = null

const filteredTrainings = computed(() => {
  let result = [...trainings.value]

  if (filters.search) {
    const search = filters.search.toLowerCase()
    result = result.filter(training =>
      training.job_name.toLowerCase().includes(search) ||
      training.job_id.toLowerCase().includes(search) ||
      training.fine_tuned_model_name?.toLowerCase().includes(search) ||
      training.dataset_name.toLowerCase().includes(search)
    )
  }

  if (filters.status) {
    result = result.filter(training => training.status === filters.status)
  }

  if (filters.method) {
    result = result.filter(training => training.method === filters.method)
  }

  return result
})

const paginatedTrainings = computed(() => {
  const start = (pagination.currentPage - 1) * pagination.pageSize
  const end = start + pagination.pageSize
  return filteredTrainings.value.slice(start, end)
})

const formatDate = (date: string) => {
  return new Date(date).toLocaleString('zh-CN')
}

const getStatusType = (status: string) => {
  const statusMap: Record<string, string> = {
    pending: 'info',
    queued: 'info',
    running: 'warning',
    completed: 'success',
    failed: 'danger',
    cancelled: 'info',
    preparing: 'info'
  }
  return statusMap[status] || 'info'
}

const getStatusText = (status: string) => {
  const statusMap: Record<string, string> = {
    pending: '等待中',
    queued: '队列中',
    running: '运行中',
    completed: '已完成',
    failed: '已失败',
    cancelled: '已取消',
    preparing: '准备中'
  }
  return statusMap[status] || '未知'
}

const getMethodText = (method: string) => {
  const methodMap: Record<string, string> = {
    lora: 'LoRA',
    qlora: 'QLoRA',
    full: '全量',
    adaptor: 'Adaptor'
  }
  return methodMap[method] || method
}

const getProgressStatus = (status: string) => {
  if (status === 'completed') return 'success'
  if (status === 'failed') return 'exception'
  return undefined
}

const handleSearch = () => {
  pagination.currentPage = 1
}

const handleFilter = () => {
  pagination.currentPage = 1
}

const handleSizeChange = (size: number) => {
  pagination.pageSize = size
  pagination.currentPage = 1
}

const handleCurrentChange = (page: number) => {
  pagination.currentPage = page
}

const resetFilters = () => {
  filters.search = ''
  filters.status = ''
  filters.method = ''
  pagination.currentPage = 1
  refreshTrainings()
}

const refreshTrainings = async () => {
  loading.value = true
  try {
    const params = {
      skip: (pagination.currentPage - 1) * pagination.pageSize,
      limit: pagination.pageSize,
      search: filters.search || undefined,
      status: filters.status as FineTuningStatus || undefined,
      method: filters.method as FineTuningMethod || undefined
    }

    const [jobsRes, statsRes] = await Promise.all([
      fineTuningApi.getJobs(params),
      fineTuningApi.getStats()
    ])

    trainings.value = jobsRes.items
    pagination.total = jobsRes.total

    stats.total = statsRes.total_jobs
    stats.running = statsRes.running_jobs
    stats.completed = statsRes.completed_jobs
    stats.failed = statsRes.failed_jobs
  } catch (error) {
    console.error('刷新任务列表失败:', error)
    ElMessage.error('刷新失败，请稍后重试')
  } finally {
    loading.value = false
  }
}

const createTraining = () => {
  router.push('/training/create')
}

const startTraining = async (training: FineTuningJob) => {
  try {
    await ElMessageBox.confirm(
      `确定要启动微调任务 "${training.job_name}" 吗？`,
      '确认启动',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'info'
      }
    )

    await fineTuningApi.startJob(training.id)
    ElMessage.success('任务已启动')
    refreshTrainings()
  } catch (error: any) {
    if (error !== 'cancel') {
      console.error('启动任务失败:', error)
      ElMessage.error('启动失败，请稍后重试')
    }
  }
}

const cancelTraining = async (training: FineTuningJob) => {
  try {
    await ElMessageBox.confirm(
      `确定要取消微调任务 "${training.job_name}" 吗？`,
      '确认取消',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )

    await fineTuningApi.cancelJob(training.id)
    ElMessage.success('任务已取消')
    refreshTrainings()
  } catch (error: any) {
    if (error !== 'cancel') {
      console.error('取消任务失败:', error)
      ElMessage.error('取消失败，请稍后重试')
    }
  }
}

const deleteTraining = async (training: FineTuningJob) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除微调任务 "${training.job_name}" 吗？此操作不可恢复。`,
      '确认删除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )

    await fineTuningApi.deleteJob(training.id)
    ElMessage.success('任务删除成功')
    refreshTrainings()
  } catch (error: any) {
    if (error !== 'cancel') {
      console.error('删除任务失败:', error)
      ElMessage.error('删除失败，请稍后重试')
    }
  }
}

const viewLogs = async (training: FineTuningJob) => {
  try {
    currentLogJob.value = training
    logDrawerVisible.value = true
    const res = await fineTuningApi.getJobLogs(training.job_id)
    logContent.value = (res.log_content || '暂无日志').replace(/\r\n/g, '\n').replace(/\r/g, '\n')
    nextTick(() => {
      if (logPreRef.value) {
        logPreRef.value.scrollTop = logPreRef.value.scrollHeight
      }
    })
  } catch (error) {
    console.error('获取日志失败:', error)
    ElMessage.error('获取日志失败，请稍后重试')
  }
}

const refreshLogs = async () => {
  if (!currentLogJob.value) return
  try {
    const res = await fineTuningApi.getJobLogs(currentLogJob.value.job_id)
    logContent.value = (res.log_content || '暂无日志').replace(/\r\n/g, '\n').replace(/\r/g, '\n')
    nextTick(() => {
      if (logPreRef.value) {
        logPreRef.value.scrollTop = logPreRef.value.scrollHeight
      }
    })
  } catch (error) {
    console.error('刷新日志失败:', error)
    ElMessage.error('刷新日志失败，请稍后重试')
  }
}

const editTraining = (training: FineTuningJob) => {
  router.push(`/training/edit/${training.id}`)
}

const viewCommand = (training: FineTuningJob) => {
  currentCommandJob.value = training
  commandDrawerVisible.value = true
  const cudaDevices = training.cuda_devices
  const condaActivate = '/data/softs/miniconda3/bin/activate'
  const swiftArgs = buildSwiftArgs(training)
  if (cudaDevices) {
    commandContent.value = `export CUDA_VISIBLE_DEVICES=${cudaDevices} && source ${condaActivate} ${training.conda_env || 'msswift'} && swift sft \\\n  ${swiftArgs}`
  } else {
    commandContent.value = `source ${condaActivate} ${training.conda_env || 'msswift'} && swift sft \\\n  ${swiftArgs}`
  }
}

const viewCurves = async (training: FineTuningJob) => {
  currentCurvesJob.value = training
  curvesDrawerVisible.value = true
  await loadCurvesData(training.job_id)
}

const refreshCurves = async () => {
  if (!currentCurvesJob.value) return
  await loadCurvesData(currentCurvesJob.value.job_id)
}

const viewChat = async (training: FineTuningJob) => {
  currentChatJob.value = training
  chatDrawerVisible.value = true
  try {
    const freshJob = await fineTuningApi.getJob(training.id)
    if (freshJob) {
      currentChatJob.value = freshJob
    }
  } catch (error) {
    console.error('获取任务详情失败:', error)
  }
}

const startModelService = async () => {
  if (!currentChatJob.value) return
  try {
    const res = await fineTuningApi.startModelService(currentChatJob.value.id)
    ElMessage.success(res.message)
    currentChatJob.value.model_status = 'running'
    currentChatJob.value.model_service_port = res.port
    await refreshTrainings()
  } catch (error: any) {
    ElMessage.error(error.message || '启动模型服务失败')
  }
}

const stopModelService = async () => {
  if (!currentChatJob.value) return
  try {
    const res = await fineTuningApi.stopModelService(currentChatJob.value.id)
    ElMessage.success(res.message)
    currentChatJob.value.model_status = 'stopped'
    await refreshTrainings()
  } catch (error: any) {
    ElMessage.error(error.message || '停止模型服务失败')
  }
}

const handleEnterKey = (e: KeyboardEvent) => {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault()
    sendChatMessage()
  }
}

const sendChatMessage = async () => {
  if (!chatInput.value.trim() || !currentChatJob.value) return

  const userMessage = chatInput.value.trim()
  chatInput.value = ''

  chatMessages.value.push({
    role: 'user',
    content: userMessage
  })

  chatLoading.value = true

  try {
    const res = await fineTuningApi.chatWithModel(
      currentChatJob.value.id,
      userMessage,
      currentChatJob.value.system_prompt || undefined
    )

    chatMessages.value.push({
      role: 'assistant',
      content: res.response
    })
  } catch (error: any) {
    ElMessage.error(error.message || '发送消息失败')
    chatMessages.value.push({
      role: 'assistant',
      content: `错误: ${error.message || '未知错误'}`
    })
  } finally {
    chatLoading.value = false
    nextTick(() => {
      if (chatMessagesRef.value) {
        chatMessagesRef.value.scrollTop = chatMessagesRef.value.scrollHeight
      }
    })
  }
}

const loadCurvesData = async (jobId: string) => {
  try {
    const res = await fineTuningApi.getJobCurves(jobId)
    const curves = res.curves

    nextTick(() => {
      initLossChart(curves.loss)
      const accData = curves.acc && curves.acc.length > 0 ? curves.acc : (curves.token_acc || [])
      const accTitle = curves.acc && curves.acc.length > 0 ? '准确率 (Accuracy)' : 'Token准确率 (Token Accuracy)'
      initAccChart(accData, accTitle)
      initLRChart(curves.learning_rate)
      initEpochChart(curves.epoch)
      initGradNormChart(curves.grad_norm)
    })
  } catch (error) {
    console.error('获取训练曲线失败:', error)
    ElMessage.error('获取训练曲线失败')
  }
}

const initLossChart = (data: { step: number; value: number }[]) => {
  if (!lossChartRef.value) return
  if (!lossChart) {
    lossChart = echarts.init(lossChartRef.value)
  }
  const option = {
    title: { text: '损失函数 (loss)', left: 'center', textStyle: { fontSize: 14 } },
    tooltip: { trigger: 'axis' },
    grid: { left: '10%', right: '10%', bottom: '15%' },
    xAxis: { type: 'value', name: 'Step', nameLocation: 'center', nameGap: 30 },
    yAxis: { type: 'value', name: 'Loss', nameLocation: 'center', nameGap: 40 },
    series: [{
      data: data.map(d => [d.step, d.value]),
      type: 'line',
      smooth: true,
      showSymbol: false
    }]
  }
  lossChart.setOption(option)
}

const initAccChart = (data: { step: number; value: number }[], title: string = '准确率 (Accuracy)') => {
  if (!accChartRef.value) return
  if (!accChart) {
    accChart = echarts.init(accChartRef.value)
  }
  const option = {
    title: { text: title, left: 'center', textStyle: { fontSize: 14 } },
    tooltip: { trigger: 'axis' },
    grid: { left: '10%', right: '10%', bottom: '15%' },
    xAxis: { type: 'value', name: 'Step', nameLocation: 'center', nameGap: 30 },
    yAxis: { type: 'value', name: 'Accuracy', nameLocation: 'center', nameGap: 40 },
    series: [{
      data: data.map(d => [d.step, d.value]),
      type: 'line',
      smooth: true,
      showSymbol: false
    }]
  }
  accChart.setOption(option)
}

const initLRChart = (data: { step: number; value: number }[]) => {
  if (!lrChartRef.value) return
  if (!lrChart) {
    lrChart = echarts.init(lrChartRef.value)
  }
  const option = {
    title: { text: '学习率 (Learning Rate)', left: 'center', textStyle: { fontSize: 14 } },
    tooltip: { trigger: 'axis' },
    grid: { left: '10%', right: '10%', bottom: '15%' },
    xAxis: { type: 'value', name: 'Step', nameLocation: 'center', nameGap: 30 },
    yAxis: { type: 'value', name: 'LR', nameLocation: 'center', nameGap: 40 },
    series: [{
      data: data.map(d => [d.step, d.value]),
      type: 'line',
      smooth: true,
      showSymbol: false
    }]
  }
  lrChart.setOption(option)
}

const initEpochChart = (data: { step: number; value: number }[]) => {
  if (!epochChartRef.value) return
  if (!epochChart) {
    epochChart = echarts.init(epochChartRef.value)
  }
  const option = {
    title: { text: '训练轮次 (Epoch)', left: 'center', textStyle: { fontSize: 14 } },
    tooltip: { trigger: 'axis' },
    grid: { left: '10%', right: '10%', bottom: '15%' },
    xAxis: { type: 'value', name: 'Step', nameLocation: 'center', nameGap: 30 },
    yAxis: { type: 'value', name: 'Epoch', nameLocation: 'center', nameGap: 40 },
    series: [{
      data: data.map(d => [d.step, d.value]),
      type: 'line',
      smooth: true,
      showSymbol: false
    }]
  }
  epochChart.setOption(option)
}

const initGradNormChart = (data: { step: number; value: number }[]) => {
  if (!gradNormChartRef.value) return
  if (!gradNormChart) {
    gradNormChart = echarts.init(gradNormChartRef.value)
  }
  const option = {
    title: { text: '梯度范数 (Grad Norm)', left: 'center', textStyle: { fontSize: 14 } },
    tooltip: { trigger: 'axis' },
    grid: { left: '10%', right: '10%', bottom: '15%' },
    xAxis: { type: 'value', name: 'Step', nameLocation: 'center', nameGap: 30 },
    yAxis: { type: 'value', name: 'Grad Norm', nameLocation: 'center', nameGap: 40 },
    series: [{
      data: data.map(d => [d.step, d.value]),
      type: 'line',
      smooth: true,
      showSymbol: false
    }]
  }
  gradNormChart.setOption(option)
}

const buildSwiftArgs = (job: FineTuningJob): string => {
  const args: string[] = [
    `--model '${job.base_model_name}'`,
    `--model_type '${job.model_type || 'qwen2'}'`,
    `--template '${job.template || 'qwen2_5'}'`,
    `--dataset '${job.dataset_path || job.dataset_name}'`,
    `--torch_dtype '${job.torch_dtype || 'bfloat16'}'`,
    `--max_length '${job.max_length || 1024}'`,
    `--split_dataset_ratio '${job.split_dataset_ratio ?? 0}'`,
    `--learning_rate '${job.learning_rate || 1e-4}'`,
    `--gradient_accumulation_steps '${job.gradient_accumulation_steps || 16}'`,
    `--eval_steps '${job.eval_steps || 500}'`,
    `--lora_rank '${job.lora_rank || 8}'`,
    `--lora_alpha '${job.lora_alpha || 32}'`,
    `--num_train_epochs '${job.total_epochs}'`,
    `--use_chat_template 'True'`,
    `--ignore_args_error True`
  ]

  if (job.system_prompt) {
    args.push(`--system '${job.system_prompt}'`)
  }
  if (job.task_type) {
    args.push(`--task_type '${job.task_type}'`)
  }
  if (job.num_labels) {
    args.push(`--num_labels '${job.num_labels}'`)
  }

  const methodMap: Record<string, string> = {
    lora: 'lora',
    qlora: 'qlora',
    full: 'full',
    adaptor: 'adaptor'
  }
  const sftType = methodMap[job.method] || 'lora'
  args.push(`--sft_type '${sftType}'`)

  return args.join(' \\\n  ')
}

const copyCommand = async () => {
  try {
    await navigator.clipboard.writeText(commandContent.value)
    ElMessage.success('命令已复制到剪贴板')
  } catch (error) {
    console.error('复制失败:', error)
    ElMessage.error('复制失败，请手动复制')
  }
}

const startAutoRefresh = () => {
  refreshTimer = setInterval(() => {
    const runningCount = trainings.value.filter(t =>
      t.status === FineTuningStatus.RUNNING || t.status === FineTuningStatus.QUEUED
    ).length
    if (runningCount > 0) {
      refreshTrainings()
    }
  }, 30000)
}

const stopAutoRefresh = () => {
  if (refreshTimer) {
    clearInterval(refreshTimer)
    refreshTimer = null
  }
}

onMounted(() => {
  refreshTrainings()
  startAutoRefresh()
})

onUnmounted(() => {
  stopAutoRefresh()
})
</script>

<style lang="scss" scoped>
.training-page {
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
      display: flex;
      align-items: center;
      padding: 20px;
      background: var(--el-bg-color);
      border-radius: 8px;
      box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);

      .stat-icon {
        width: 60px;
        height: 60px;
        border-radius: 8px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 24px;
        margin-right: 16px;

        &.total {
          background: #e6f7ff;
          color: #1890ff;
        }

        &.running {
          background: #fff7e6;
          color: #fa8c16;
        }

        &.completed {
          background: #f6ffed;
          color: #52c41a;
        }

        &.failed {
          background: #fff1f0;
          color: #ff4d4f;
        }
      }

      .stat-content {
        .stat-value {
          font-size: 28px;
          font-weight: 600;
          color: var(--el-text-color-primary);
        }

        .stat-label {
          font-size: 14px;
          color: var(--el-text-color-secondary);
        }
      }
    }
  }

  .filter-section {
    margin-bottom: 20px;
  }

  .training-list {
    .pagination-wrapper {
      margin-top: 20px;
      display: flex;
      justify-content: flex-end;
    }
  }

  .job-id {
    font-family: monospace;
    font-size: 12px;
    color: var(--el-text-color-secondary);
  }

  .job-name-cell {
    display: flex;
    flex-direction: column;
    gap: 4px;

    .name {
      font-weight: 500;
    }

    .model-name {
      font-size: 12px;
      color: var(--el-text-color-secondary);
    }
  }

  .progress-cell {
    display: flex;
    align-items: center;
    gap: 8px;

    .progress-text {
      font-size: 12px;
      color: var(--el-text-color-secondary);
      min-width: 35px;
    }
  }

  .status-running {
    animation: pulse 1.5s infinite;
  }

  @keyframes pulse {
    0%, 100% {
      opacity: 1;
    }
    50% {
      opacity: 0.7;
    }
  }
}

.log-content {
  pre {
    background: var(--el-bg-color-page);
    padding: 16px;
    border-radius: 4px;
    overflow: auto;
    max-height: calc(100vh - 140px);
    font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
    font-size: 13px;
    line-height: 1.5;
    white-space: pre-wrap;
    word-break: break-all;
    word-wrap: break-word;
  }
}

.command-content {
  pre {
    background: var(--el-bg-color-page);
    padding: 16px;
    border-radius: 4px;
    overflow: auto;
    max-height: calc(100vh - 200px);
    font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
    font-size: 13px;
    line-height: 1.5;
    white-space: pre-wrap;
    word-break: break-all;
  }
  .el-button {
    margin-top: 16px;
  }
}

.curves-content {
  .curve-chart {
    width: 100%;
    height: 350px;
    margin-bottom: 20px;
    background: var(--el-bg-color-page);
    border-radius: 4px;
    padding: 16px;
  }
}

.chat-container {
  display: flex;
  flex-direction: column;
  height: 100%;

  .chat-messages {
    flex: 1;
    overflow-y: auto;
    padding: 16px;
    background: var(--el-bg-color-page);
    border-radius: 4px;
    margin-bottom: 16px;

    .chat-message {
      display: flex;
      margin-bottom: 16px;

      &.user {
        flex-direction: row-reverse;

        .message-avatar {
          margin-left: 12px;
        }

        .message-content {
          background: var(--el-color-primary-light-9);
        }
      }

      &.assistant {
        .message-avatar {
          margin-right: 12px;
        }

        .message-content {
          background: var(--el-color-success-light-9);
        }
      }

      .message-avatar {
        width: 32px;
        height: 32px;
        border-radius: 50%;
        background: var(--el-color-primary);
        color: white;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 14px;
        flex-shrink: 0;
      }

      .message-content {
        max-width: 70%;
        padding: 10px 14px;
        border-radius: 8px;
        line-height: 1.5;
      }
    }
  }

  .chat-input {
    display: flex;
    gap: 12px;

    .el-textarea {
      flex: 1;
    }
  }
}
</style>