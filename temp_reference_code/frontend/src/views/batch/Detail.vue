<template>
  <div>
    <!-- 批次基本信息 -->
    <div class="page-card mb-20">
      <div class="page-header">
        <div style="display: flex; align-items: center; gap: 16px;">
          <el-button @click="$router.go(-1)">
            <el-icon><ArrowLeft /></el-icon>
            返回
          </el-button>
          <h2>批次详情</h2>
        </div>
        <div style="display: flex; gap: 12px;">
          <el-button
            type="primary"
            @click="processBatch"
            :disabled="batch.status === 'processing' || batch.status === 'completed'"
            :loading="processing"
          >
            {{ processing ? '处理中...' : '开始处理' }}
          </el-button>
          <el-button @click="refreshBatch">刷新</el-button>
        </div>
      </div>
      
      <div class="page-content">
        <el-row :gutter="20" v-if="batch.id">
          <el-col :span="12">
            <el-descriptions title="基本信息" :column="1" border>
              <el-descriptions-item label="批次ID">{{ batch.batch_id }}</el-descriptions-item>
              <el-descriptions-item label="批次名称">{{ batch.batch_name || batch.name }}</el-descriptions-item>
              <el-descriptions-item label="描述">{{ batch.description }}</el-descriptions-item>
              <el-descriptions-item label="状态">
                <el-tag :type="getStatusTagType(batch.status)">
                  {{ getStatusText(batch.status) }}
                </el-tag>
              </el-descriptions-item>
              <el-descriptions-item label="创建时间">{{ formatDate(batch.created_at) }}</el-descriptions-item>
              <el-descriptions-item label="更新时间">{{ formatDate(batch.updated_at) }}</el-descriptions-item>
            </el-descriptions>
          </el-col>
          
          <el-col :span="12">
            <el-descriptions title="处理统计" :column="1" border>
              <el-descriptions-item label="总数据量">{{ batch.total_count || 0 }}</el-descriptions-item>
              <el-descriptions-item label="已处理">{{ batch.completed_count || 0 }}</el-descriptions-item>
              <el-descriptions-item label="待处理">{{ batch.pending_count || 0 }}</el-descriptions-item>
              <el-descriptions-item label="失败数量">{{ batch.failed_count || 0 }}</el-descriptions-item>
              <el-descriptions-item label="处理进度">
                <el-progress
                  :percentage="getProgress(batch)"
                  :status="getProgressStatus(batch.status)"
                  :stroke-width="12"
                />
              </el-descriptions-item>
              <el-descriptions-item label="处理时长" v-if="batch.processing_time">
                {{ formatDuration(batch.processing_time) }}
              </el-descriptions-item>
            </el-descriptions>
          </el-col>
        </el-row>
        
        <!-- 处理配置 -->
        <div style="margin-top: 20px;" v-if="batch.config">
          <h3>处理配置</h3>
          <el-input
            :model-value="JSON.stringify(batch.config, null, 2)"
            type="textarea"
            :rows="8"
            readonly
            style="font-family: monospace;"
          />
        </div>
      </div>
    </div>
    
    <!-- 批次数据列表 -->
    <div class="page-card">
      <div class="page-header">
        <h3>批次数据</h3>
        <div style="display: flex; gap: 12px;">
          <el-button @click="showUploadDialog">
            <el-icon><Upload /></el-icon>
            上传数据
          </el-button>
          <el-button @click="loadBatchData">刷新数据</el-button>
        </div>
      </div>
      
      <div class="page-content">
        <!-- 数据筛选 -->
        <div class="table-toolbar">
          <div style="display: flex; gap: 16px; align-items: center;">
            <el-input
              v-model="dataSearchQuery"
              placeholder="搜索文件名"
              style="width: 300px;"
              clearable
            >
              <template #prefix>
                <el-icon><Search /></el-icon>
              </template>
            </el-input>
            
            <el-select
              v-model="dataStatusFilter"
              placeholder="筛选状态"
              style="width: 150px;"
              clearable
            >
              <el-option label="成功" value="success" />
              <el-option label="错误" value="error" />
            </el-select>
          </div>
        </div>
        
        <!-- 数据表格 -->
        <el-table
          :data="filteredBatchData"
          style="width: 100%"
          v-loading="dataLoading"
        >
          <el-table-column prop="id" label="ID" width="80" />
          <el-table-column prop="batch_id" label="批次ID" width="150" show-overflow-tooltip />
          <el-table-column prop="api_id" label="API ID" width="80" />
          <el-table-column prop="http_method" label="请求方法" width="100">
            <template #default="{ row }">
              <el-tag :type="getMethodTagType(row.http_method)">
                {{ row.http_method }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="request_url" label="请求URL" width="300" show-overflow-tooltip />
          <el-table-column prop="response_status" label="响应状态" width="100">
            <template #default="{ row }">
              <el-tag :type="getStatusTagType(row.response_status)">
                {{ row.response_status }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="processing_time" label="处理时间" width="120">
            <template #default="{ row }">
              {{ row.processing_time ? row.processing_time.toFixed(3) + 's' : '-' }}
            </template>
          </el-table-column>
          <el-table-column prop="created_at" label="创建时间" width="180">
            <template #default="{ row }">
              {{ formatDate(row.created_at) }}
            </template>
          </el-table-column>
          <el-table-column prop="file_path" label="文件路径" show-overflow-tooltip>
            <template #default="{ row }">
              {{ row.file_path || '-' }}
            </template>
          </el-table-column>
          <el-table-column label="操作" width="120" fixed="right">
            <template #default="{ row }">
              <el-button size="small" @click="downloadFile(row)">下载</el-button>
            </template>
          </el-table-column>
        </el-table>
        
        <!-- 分页 -->
        <div style="margin-top: 20px; text-align: right;">
          <el-pagination
            v-model:current-page="dataCurrentPage"
            v-model:page-size="dataPageSize"
            :page-sizes="[10, 20, 50, 100]"
            :total="dataTotal"
            layout="total, sizes, prev, pager, next, jumper"
            @size-change="handleDataSizeChange"
            @current-change="handleDataCurrentChange"
          />
        </div>
      </div>
    </div>
    
    <!-- 上传数据对话框 -->
    <el-dialog
      v-model="uploadDialogVisible"
      title="上传数据到批次"
      width="500px"
    >
      <el-upload
        ref="uploadRef"
        :action="uploadUrl"
        :headers="uploadHeaders"
        :data="{ batch_id: batchId }"
        :on-success="handleUploadSuccess"
        :on-error="handleUploadError"
        :before-upload="beforeUpload"
        drag
        multiple
      >
        <el-icon class="el-icon--upload"><upload-filled /></el-icon>
        <div class="el-upload__text">
          将文件拖到此处，或<em>点击上传</em>
        </div>
        <template #tip>
          <div class="el-upload__tip">
            支持多文件上传，单个文件大小不超过100MB
          </div>
        </template>
      </el-upload>
      
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="uploadDialogVisible = false">关闭</el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import api from '@/utils/api'
import dayjs from 'dayjs'

const route = useRoute()
const batchId = route.params.id

// 响应式数据
const batch = ref({})
const batchData = ref([])
const loading = ref(false)
const dataLoading = ref(false)
const processing = ref(false)

// 数据筛选
const dataSearchQuery = ref('')
const dataStatusFilter = ref('')
const dataCurrentPage = ref(1)
const dataPageSize = ref(20)
const dataTotal = ref(0)

// 上传对话框
const uploadDialogVisible = ref(false)
const uploadRef = ref()

// 上传配置
const uploadUrl = '/api/v1/data/upload'
const uploadHeaders = computed(() => {
  const token = localStorage.getItem('admin_token')
  return token ? { Authorization: `Bearer ${token}` } : {}
})

// 计算属性
const filteredBatchData = computed(() => {
  let result = batchData.value
  
  // 按搜索关键词过滤
  if (dataSearchQuery.value) {
    const query = dataSearchQuery.value.toLowerCase()
    result = result.filter(item => 
      (item.request_url && item.request_url.toLowerCase().includes(query)) ||
      (item.http_method && item.http_method.toLowerCase().includes(query)) ||
      (item.file_path && item.file_path.toLowerCase().includes(query))
    )
  }
  
  // 按状态过滤（这里可以根据响应状态码进行筛选）
  if (dataStatusFilter.value) {
    if (dataStatusFilter.value === 'success') {
      result = result.filter(item => item.response_status >= 200 && item.response_status < 300)
    } else if (dataStatusFilter.value === 'error') {
      result = result.filter(item => item.response_status >= 400)
    }
  }
  
  return result
})

// 获取HTTP方法标签类型
const getMethodTagType = (method) => {
  const typeMap = {
    'GET': 'info',
    'POST': 'success',
    'PUT': 'warning',
    'DELETE': 'danger',
    'PATCH': 'warning'
  }
  console.log("请求类型：", typeMap[method])
  return typeMap[method] || 'default'
}

// 获取状态标签类型
const getStatusTagType = (status) => {
  if (status >= 200 && status < 300) return 'success'
  if (status >= 400 && status < 500) return 'warning'
  if (status >= 500) return 'danger'
  return 'info'
}

// 获取状态文本
const getStatusText = (status) => {
  const textMap = {
    'pending': '待处理',
    'processing': '处理中',
    'completed': '已完成',
    'failed': '失败'
  }
  return textMap[status] || status
}

// 获取进度百分比
const getProgress = (batch) => {
  if (!batch.total_count || batch.total_count === 0) return 0
  return Math.round((batch.completed_count / batch.total_count) * 100)
}

// 获取进度条状态
const getProgressStatus = (status) => {
  if (status === 'completed') return 'success'
  if (status === 'failed') return 'exception'
  return null
}

// 格式化日期
const formatDate = (dateString) => {
  if (!dateString) return '-'
  return dayjs(dateString).format('YYYY-MM-DD HH:mm:ss')
}

// 格式化时长
const formatDuration = (seconds) => {
  if (!seconds) return '-'
  const hours = Math.floor(seconds / 3600)
  const minutes = Math.floor((seconds % 3600) / 60)
  const secs = seconds % 60
  
  if (hours > 0) {
    return `${hours}小时${minutes}分钟${secs}秒`
  } else if (minutes > 0) {
    return `${minutes}分钟${secs}秒`
  } else {
    return `${secs}秒`
  }
}

// 格式化文件大小
const formatFileSize = (bytes) => {
  if (!bytes) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

// 加载批次详情
const loadBatch = async () => {
  loading.value = true
  try {
    const response = await api.get(`/admin/batches/${batchId}`)
    batch.value = response.data.data
  } catch (error) {
    console.error('加载批次详情失败:', error)
    ElMessage.error('加载批次详情失败')
  } finally {
    loading.value = false
  }
}

// 加载批次数据
const loadBatchData = async () => {
  dataLoading.value = true
  try {
    const response = await api.get(`/batch/${batch.value.batch_id || batchId}/data`, {
      params: {
        page: dataCurrentPage.value,
        size: dataPageSize.value
      }
    })
    
    batchData.value = response.data.data.items || []
    dataTotal.value = response.data.data.total || 0
  } catch (error) {
    console.error('加载批次数据失败:', error)
    ElMessage.error('加载批次数据失败')
  } finally {
    dataLoading.value = false
  }
}

// 刷新批次信息
const refreshBatch = () => {
  loadBatch()
  loadBatchData()
}

// 处理批次
const processBatch = async () => {
  try {
    await ElMessageBox.confirm(`确定要开始处理批次 "${batch.value.batch_name || batch.value.name}" 吗？`, '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    
    processing.value = true
    await api.post(`/batch/${batch.value.batch_id}/process`)
    ElMessage.success('批次处理已开始')
    
    // 刷新批次状态
    setTimeout(() => {
      loadBatch()
    }, 1000)
  } catch (error) {
    if (error !== 'cancel') {
      console.error('处理批次失败:', error)
      ElMessage.error('处理批次失败')
    }
  } finally {
    processing.value = false
  }
}

// 数据分页处理
const handleDataSizeChange = (val) => {
  dataPageSize.value = val
  dataCurrentPage.value = 1
  loadBatchData()
}

const handleDataCurrentChange = (val) => {
  dataCurrentPage.value = val
  loadBatchData()
}

// 显示上传对话框
const showUploadDialog = () => {
  uploadDialogVisible.value = true
}

// 上传前检查
const beforeUpload = (file) => {
  const isLt100M = file.size / 1024 / 1024 < 100
  if (!isLt100M) {
    ElMessage.error('文件大小不能超过 100MB!')
  }
  return isLt100M
}

// 上传成功
const handleUploadSuccess = (response, file) => {
  ElMessage.success(`文件 ${file.name} 上传成功`)
  loadBatchData()
  loadBatch() // 刷新批次统计
}

// 上传失败
const handleUploadError = (error, file) => {
  console.error('上传失败:', error)
  ElMessage.error(`文件 ${file.name} 上传失败`)
}

// 下载文件
const downloadFile = async (fileData) => {
  try {
    const response = await api.get(`/data/${fileData.id}/download`, {
      responseType: 'blob'
    })
    
    // 创建下载链接
    const url = window.URL.createObjectURL(new Blob([response.data]))
    const link = document.createElement('a')
    link.href = url
    link.setAttribute('download', fileData.filename)
    document.body.appendChild(link)
    link.click()
    link.remove()
    window.URL.revokeObjectURL(url)
  } catch (error) {
    console.error('下载文件失败:', error)
    ElMessage.error('下载文件失败')
  }
}

// 组件挂载时加载数据
onMounted(() => {
  loadBatch()
  loadBatchData()
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

.page-header h2,
.page-header h3 {
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

.mb-20 {
  margin-bottom: 20px;
}
</style>