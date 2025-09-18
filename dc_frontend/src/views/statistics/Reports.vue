<template>
  <div class="reports-container">
    <!-- 页面标题 -->
    <div class="page-header">
      <h1 class="page-title">
        <el-icon><Document /></el-icon>
        报表管理
      </h1>
      <p class="page-description">生成和管理各类数据报表</p>
    </div>

    <!-- 操作栏 -->
    <div class="action-bar">
      <div class="action-left">
        <el-button type="primary" @click="generateReport">
          <el-icon><Plus /></el-icon>
          生成报表
        </el-button>
        <el-button @click="refreshReports">
          <el-icon><Refresh /></el-icon>
          刷新
        </el-button>
      </div>
      
      <div class="action-right">
        <el-input
          v-model="searchKeyword"
          placeholder="搜索报表..."
          style="width: 200px"
          clearable
        >
          <template #prefix>
            <el-icon><Search /></el-icon>
          </template>
        </el-input>
      </div>
    </div>

    <!-- 报表列表 -->
    <div class="reports-content">
      <el-table
        :data="filteredReports"
        v-loading="loading"
        stripe
        style="width: 100%"
      >
        <el-table-column prop="name" label="报表名称" min-width="200">
          <template #default="{ row }">
            <div class="report-name">
              <el-icon class="report-icon"><Document /></el-icon>
              <span>{{ row.name }}</span>
            </div>
          </template>
        </el-table-column>
        
        <el-table-column prop="type" label="报表类型" width="120">
          <template #default="{ row }">
            <el-tag :type="getReportTypeTag(row.type)">{{ row.type }}</el-tag>
          </template>
        </el-table-column>
        
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="getStatusTag(row.status)">{{ row.status }}</el-tag>
          </template>
        </el-table-column>
        
        <el-table-column prop="createdAt" label="创建时间" width="180">
          <template #default="{ row }">
            {{ formatDate(row.createdAt) }}
          </template>
        </el-table-column>
        
        <el-table-column prop="size" label="文件大小" width="120">
          <template #default="{ row }">
            {{ formatFileSize(row.size) }}
          </template>
        </el-table-column>
        
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <el-button
              type="primary"
              size="small"
              @click="downloadReport(row)"
              :disabled="row.status !== '已完成'"
            >
              下载
            </el-button>
            <el-button
              type="info"
              size="small"
              @click="viewReport(row)"
              :disabled="row.status !== '已完成'"
            >
              预览
            </el-button>
            <el-button
              type="danger"
              size="small"
              @click="deleteReport(row)"
            >
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <!-- 分页 -->
    <div class="pagination-container">
      <el-pagination
        v-model:current-page="currentPage"
        v-model:page-size="pageSize"
        :page-sizes="[10, 20, 50, 100]"
        :total="totalReports"
        layout="total, sizes, prev, pager, next, jumper"
        @size-change="handleSizeChange"
        @current-change="handleCurrentChange"
      />
    </div>

    <!-- 生成报表对话框 -->
    <el-dialog
      v-model="generateDialogVisible"
      title="生成报表"
      width="500px"
    >
      <el-form :model="reportForm" label-width="100px">
        <el-form-item label="报表名称">
          <el-input v-model="reportForm.name" placeholder="请输入报表名称" />
        </el-form-item>
        
        <el-form-item label="报表类型">
          <el-select v-model="reportForm.type" placeholder="请选择报表类型">
            <el-option label="数据统计" value="数据统计" />
            <el-option label="访问分析" value="访问分析" />
            <el-option label="用户报告" value="用户报告" />
            <el-option label="系统监控" value="系统监控" />
          </el-select>
        </el-form-item>
        
        <el-form-item label="时间范围">
          <el-date-picker
            v-model="reportForm.dateRange"
            type="daterange"
            range-separator="至"
            start-placeholder="开始日期"
            end-placeholder="结束日期"
            format="YYYY-MM-DD"
            value-format="YYYY-MM-DD"
          />
        </el-form-item>
        
        <el-form-item label="输出格式">
          <el-radio-group v-model="reportForm.format">
            <el-radio label="PDF">PDF</el-radio>
            <el-radio label="Excel">Excel</el-radio>
            <el-radio label="CSV">CSV</el-radio>
          </el-radio-group>
        </el-form-item>
      </el-form>
      
      <template #footer>
        <el-button @click="generateDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="confirmGenerate">生成</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'

// 响应式数据
const loading = ref(false)
const searchKeyword = ref('')
const currentPage = ref(1)
const pageSize = ref(20)
const totalReports = ref(0)
const generateDialogVisible = ref(false)

// 报表数据
const reports = ref([
  {
    id: 1,
    name: '2024年第一季度数据统计报表',
    type: '数据统计',
    status: '已完成',
    createdAt: '2024-01-15 10:30:00',
    size: 2048576
  },
  {
    id: 2,
    name: '用户访问行为分析报告',
    type: '访问分析',
    status: '生成中',
    createdAt: '2024-01-14 15:20:00',
    size: 0
  },
  {
    id: 3,
    name: '系统性能监控月报',
    type: '系统监控',
    status: '已完成',
    createdAt: '2024-01-13 09:15:00',
    size: 1536000
  }
])

// 报表表单
const reportForm = ref({
  name: '',
  type: '',
  dateRange: [],
  format: 'PDF'
})

/**
 * 过滤后的报表列表
 */
const filteredReports = computed(() => {
  if (!searchKeyword.value) {
    return reports.value
  }
  return reports.value.filter(report => 
    report.name.toLowerCase().includes(searchKeyword.value.toLowerCase())
  )
})

/**
 * 获取报表类型标签样式
 */
const getReportTypeTag = (type: string) => {
  const typeMap: Record<string, string> = {
    '数据统计': 'primary',
    '访问分析': 'success',
    '用户报告': 'warning',
    '系统监控': 'info'
  }
  return typeMap[type] || 'default'
}

/**
 * 获取状态标签样式
 */
const getStatusTag = (status: string) => {
  const statusMap: Record<string, string> = {
    '已完成': 'success',
    '生成中': 'warning',
    '失败': 'danger'
  }
  return statusMap[status] || 'default'
}

/**
 * 格式化日期
 */
const formatDate = (dateStr: string) => {
  return new Date(dateStr).toLocaleString('zh-CN')
}

/**
 * 格式化文件大小
 */
const formatFileSize = (bytes: number) => {
  if (bytes === 0) return '-'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

/**
 * 生成报表
 */
const generateReport = () => {
  generateDialogVisible.value = true
  // 重置表单
  reportForm.value = {
    name: '',
    type: '',
    dateRange: [],
    format: 'PDF'
  }
}

/**
 * 确认生成报表
 */
const confirmGenerate = () => {
  if (!reportForm.value.name || !reportForm.value.type) {
    ElMessage.warning('请填写完整的报表信息')
    return
  }
  
  // 模拟生成报表
  const newReport = {
    id: Date.now(),
    name: reportForm.value.name,
    type: reportForm.value.type,
    status: '生成中',
    createdAt: new Date().toLocaleString('zh-CN'),
    size: 0
  }
  
  reports.value.unshift(newReport)
  generateDialogVisible.value = false
  ElMessage.success('报表生成任务已提交')
  
  // 模拟生成完成
  setTimeout(() => {
    const report = reports.value.find(r => r.id === newReport.id)
    if (report) {
      report.status = '已完成'
      report.size = Math.floor(Math.random() * 5000000) + 1000000
      ElMessage.success(`报表 "${report.name}" 生成完成`)
    }
  }, 3000)
}

/**
 * 刷新报表列表
 */
const refreshReports = () => {
  loading.value = true
  // 模拟刷新
  setTimeout(() => {
    loading.value = false
    ElMessage.success('报表列表已刷新')
  }, 1000)
}

/**
 * 下载报表
 */
const downloadReport = (report: any) => {
  ElMessage.success(`开始下载报表: ${report.name}`)
  // 这里应该实现实际的下载逻辑
}

/**
 * 预览报表
 */
const viewReport = (report: any) => {
  ElMessage.info(`预览报表: ${report.name}`)
  // 这里应该实现报表预览逻辑
}

/**
 * 删除报表
 */
const deleteReport = (report: any) => {
  ElMessageBox.confirm(
    `确定要删除报表 "${report.name}" 吗？`,
    '确认删除',
    {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    }
  ).then(() => {
    const index = reports.value.findIndex(r => r.id === report.id)
    if (index > -1) {
      reports.value.splice(index, 1)
      ElMessage.success('报表删除成功')
    }
  }).catch(() => {
    // 用户取消删除
  })
}

/**
 * 处理页面大小变化
 */
const handleSizeChange = (size: number) => {
  pageSize.value = size
  currentPage.value = 1
}

/**
 * 处理当前页变化
 */
const handleCurrentChange = (page: number) => {
  currentPage.value = page
}

/**
 * 组件挂载时加载数据
 */
onMounted(() => {
  totalReports.value = reports.value.length
})
</script>

<style lang="scss" scoped>
.reports-container {
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

.action-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  padding: 16px;
  background: var(--el-bg-color);
  border-radius: 8px;
  border: 1px solid var(--el-border-color-light);
  
  .action-left {
    display: flex;
    gap: 12px;
  }
}

.reports-content {
  background: var(--el-bg-color);
  border-radius: 8px;
  border: 1px solid var(--el-border-color-light);
  overflow: hidden;
  
  .report-name {
    display: flex;
    align-items: center;
    
    .report-icon {
      margin-right: 8px;
      color: var(--el-color-primary);
    }
  }
}

.pagination-container {
  display: flex;
  justify-content: center;
  margin-top: 20px;
  padding: 16px;
  background: var(--el-bg-color);
  border-radius: 8px;
  border: 1px solid var(--el-border-color-light);
}

// 响应式设计
@media (max-width: 768px) {
  .reports-container {
    padding: 16px;
  }
  
  .action-bar {
    flex-direction: column;
    gap: 12px;
    align-items: stretch;
    
    .action-left {
      justify-content: center;
    }
    
    .action-right {
      display: flex;
      justify-content: center;
    }
  }
}
</style>