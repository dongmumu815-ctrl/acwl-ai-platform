<template>
  <div class="statistics-dashboard">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="header-left">
        <h1 class="page-title">统计分析</h1>
        <p class="page-description">数据资源使用情况统计与分析</p>
      </div>
      <div class="header-right">
        <el-date-picker
          v-model="dateRange"
          type="daterange"
          range-separator="至"
          start-placeholder="开始日期"
          end-placeholder="结束日期"
          format="YYYY-MM-DD"
          value-format="YYYY-MM-DD"
          @change="handleDateChange"
        />
        <el-button @click="refreshData">
          <el-icon><Refresh /></el-icon>
          刷新
        </el-button>
      </div>
    </div>

    <!-- 统计卡片 -->
    <div class="stats-cards">
      <el-row :gutter="16">
        <el-col :xs="24" :sm="12" :md="6">
          <div class="stat-card">
            <div class="stat-icon resource">
              <el-icon><Coin /></el-icon>
            </div>
            <div class="stat-content">
              <div class="stat-value">{{ statsData.totalResources }}</div>
              <div class="stat-label">总资源数</div>
              <div class="stat-change" :class="getChangeClass(statsData.resourcesChange)">
                <el-icon><ArrowUp v-if="statsData.resourcesChange > 0" /><ArrowDown v-else /></el-icon>
                {{ Math.abs(statsData.resourcesChange) }}%
              </div>
            </div>
          </div>
        </el-col>
        
        <el-col :xs="24" :sm="12" :md="6">
          <div class="stat-card">
            <div class="stat-icon access">
              <el-icon><View /></el-icon>
            </div>
            <div class="stat-content">
              <div class="stat-value">{{ formatNumber(statsData.totalAccess) }}</div>
              <div class="stat-label">总访问量</div>
              <div class="stat-change" :class="getChangeClass(statsData.accessChange)">
                <el-icon><ArrowUp v-if="statsData.accessChange > 0" /><ArrowDown v-else /></el-icon>
                {{ Math.abs(statsData.accessChange) }}%
              </div>
            </div>
          </div>
        </el-col>
        
        <el-col :xs="24" :sm="12" :md="6">
          <div class="stat-card">
            <div class="stat-icon user">
              <el-icon><User /></el-icon>
            </div>
            <div class="stat-content">
              <div class="stat-value">{{ statsData.activeUsers }}</div>
              <div class="stat-label">活跃用户</div>
              <div class="stat-change" :class="getChangeClass(statsData.usersChange)">
                <el-icon><ArrowUp v-if="statsData.usersChange > 0" /><ArrowDown v-else /></el-icon>
                {{ Math.abs(statsData.usersChange) }}%
              </div>
            </div>
          </div>
        </el-col>
        
        <el-col :xs="24" :sm="12" :md="6">
          <div class="stat-card">
            <div class="stat-icon storage">
              <el-icon><Coin /></el-icon>
            </div>
            <div class="stat-content">
              <div class="stat-value">{{ formatBytes(statsData.totalStorage) }}</div>
              <div class="stat-label">存储使用</div>
              <div class="stat-change" :class="getChangeClass(statsData.storageChange)">
                <el-icon><ArrowUp v-if="statsData.storageChange > 0" /><ArrowDown v-else /></el-icon>
                {{ Math.abs(statsData.storageChange) }}%
              </div>
            </div>
          </div>
        </el-col>
      </el-row>
    </div>

    <!-- 图表区域 -->
    <div class="charts-container">
      <el-row :gutter="16">
        <!-- 访问趋势图 -->
        <el-col :xs="24" :lg="12">
          <el-card class="chart-card" shadow="never">
            <template #header>
              <div class="card-header">
                <span class="card-title">访问趋势</span>
                <el-select v-model="accessTrendType" size="small" style="width: 100px">
                  <el-option label="日" value="day" />
                  <el-option label="周" value="week" />
                  <el-option label="月" value="month" />
                </el-select>
              </div>
            </template>
            <div ref="accessTrendChart" class="chart" style="height: 300px"></div>
          </el-card>
        </el-col>
        
        <!-- 资源类型分布 -->
        <el-col :xs="24" :lg="12">
          <el-card class="chart-card" shadow="never">
            <template #header>
              <span class="card-title">资源类型分布</span>
            </template>
            <div ref="resourceTypeChart" class="chart" style="height: 300px"></div>
          </el-card>
        </el-col>
      </el-row>
      
      <el-row :gutter="16" style="margin-top: 16px">
        <!-- 热门资源排行 -->
        <el-col :xs="24" :lg="12">
          <el-card class="chart-card" shadow="never">
            <template #header>
              <span class="card-title">热门资源排行</span>
            </template>
            <div class="popular-resources">
              <div 
                v-for="(resource, index) in popularResources" 
                :key="resource.id"
                class="resource-item"
              >
                <div class="rank">{{ index + 1 }}</div>
                <div class="resource-info">
                  <div class="resource-name">{{ resource.name }}</div>
                  <div class="resource-type">{{ getResourceTypeLabel(resource.type) }}</div>
                </div>
                <div class="access-count">{{ formatNumber(resource.accessCount) }}</div>
              </div>
            </div>
          </el-card>
        </el-col>
        
        <!-- 用户活跃度 -->
        <el-col :xs="24" :lg="12">
          <el-card class="chart-card" shadow="never">
            <template #header>
              <span class="card-title">用户活跃度</span>
            </template>
            <div ref="userActivityChart" class="chart" style="height: 300px"></div>
          </el-card>
        </el-col>
      </el-row>
    </div>

    <!-- 详细数据表格 -->
    <div class="data-table">
      <el-card shadow="never">
        <template #header>
          <div class="card-header">
            <span class="card-title">访问记录</span>
            <div class="header-actions">
              <el-input
                v-model="searchKeyword"
                placeholder="搜索资源名称"
                style="width: 200px"
                clearable
              >
                <template #prefix>
                  <el-icon><Search /></el-icon>
                </template>
              </el-input>
              <el-button @click="exportData">
                <el-icon><Download /></el-icon>
                导出
              </el-button>
            </div>
          </div>
        </template>
        
        <el-table
          :data="accessRecords"
          v-loading="tableLoading"
          stripe
          style="width: 100%"
        >
          <el-table-column prop="resourceName" label="资源名称" min-width="200" />
          <el-table-column prop="resourceType" label="资源类型" width="120">
            <template #default="{ row }">
              <el-tag size="small">{{ getResourceTypeLabel(row.resourceType) }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="userName" label="访问用户" width="120" />
          <el-table-column prop="accessTime" label="访问时间" width="180">
            <template #default="{ row }">
              {{ formatDateTime(row.accessTime) }}
            </template>
          </el-table-column>
          <el-table-column prop="accessType" label="访问类型" width="100">
            <template #default="{ row }">
              <el-tag 
                :type="getAccessTypeTagType(row.accessType)" 
                size="small"
              >
                {{ getAccessTypeLabel(row.accessType) }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="duration" label="访问时长" width="100">
            <template #default="{ row }">
              {{ formatDuration(row.duration) }}
            </template>
          </el-table-column>
          <el-table-column prop="status" label="状态" width="80">
            <template #default="{ row }">
              <el-tag 
                :type="row.status === 'success' ? 'success' : 'danger'" 
                size="small"
              >
                {{ row.status === 'success' ? '成功' : '失败' }}
              </el-tag>
            </template>
          </el-table-column>
        </el-table>
        
        <div class="pagination">
          <el-pagination
            v-model:current-page="pagination.page"
            v-model:page-size="pagination.size"
            :total="pagination.total"
            :page-sizes="[10, 20, 50, 100]"
            layout="total, sizes, prev, pager, next, jumper"
            @size-change="handleSizeChange"
            @current-change="handlePageChange"
          />
        </div>
      </el-card>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, onUnmounted, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { 
  Coin, 
  View, 
  User, 
  Refresh, 
  Search, 
  Download,
  ArrowUp,
  ArrowDown
} from '@element-plus/icons-vue'
import * as echarts from 'echarts'
import type { ECharts } from 'echarts'
import { 
  getStatistics, 
  getAccessTrend, 
  getResourceTypeDistribution,
  getPopularResources,
  getUserActivity,
  getAccessRecords,
  exportStatistics
} from '@/api/statistics'
import type { 
  StatisticsData, 
  AccessRecord, 
  PopularResource 
} from '@/types/statistics'

// 图表实例
const accessTrendChart = ref<HTMLElement>()
const resourceTypeChart = ref<HTMLElement>()
const userActivityChart = ref<HTMLElement>()
let accessTrendChartInstance: ECharts | null = null
let resourceTypeChartInstance: ECharts | null = null
let userActivityChartInstance: ECharts | null = null

// 状态
const loading = ref(false)
const tableLoading = ref(false)
const searchKeyword = ref('')
const dateRange = ref<[string, string]>([
  new Date(Date.now() - 30 * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
  new Date().toISOString().split('T')[0]
])
const accessTrendType = ref('day')

// 数据
const statsData = reactive<StatisticsData>({
  totalResources: 0,
  totalAccess: 0,
  activeUsers: 0,
  totalStorage: 0,
  resourcesChange: 0,
  accessChange: 0,
  usersChange: 0,
  storageChange: 0
})

const popularResources = ref<PopularResource[]>([])
const accessRecords = ref<AccessRecord[]>([])

// 分页
const pagination = reactive({
  page: 1,
  size: 20,
  total: 0
})

/**
 * 初始化图表
 */
const initCharts = () => {
  // 访问趋势图
  if (accessTrendChart.value) {
    accessTrendChartInstance = echarts.init(accessTrendChart.value)
  }
  
  // 资源类型分布图
  if (resourceTypeChart.value) {
    resourceTypeChartInstance = echarts.init(resourceTypeChart.value)
  }
  
  // 用户活跃度图
  if (userActivityChart.value) {
    userActivityChartInstance = echarts.init(userActivityChart.value)
  }
  
  // 监听窗口大小变化
  window.addEventListener('resize', handleResize)
}

/**
 * 处理窗口大小变化
 */
const handleResize = () => {
  accessTrendChartInstance?.resize()
  resourceTypeChartInstance?.resize()
  userActivityChartInstance?.resize()
}

/**
 * 加载统计数据
 */
const loadStatistics = async () => {
  try {
    loading.value = true
    const response = await getStatistics({
      startDate: dateRange.value[0],
      endDate: dateRange.value[1]
    })
    Object.assign(statsData, response.data)
  } catch (error) {
    console.error('加载统计数据失败:', error)
    ElMessage.error('加载统计数据失败')
  } finally {
    loading.value = false
  }
}

/**
 * 加载访问趋势数据
 */
const loadAccessTrend = async () => {
  try {
    const response = await getAccessTrend({
      startDate: dateRange.value[0],
      endDate: dateRange.value[1],
      type: accessTrendType.value
    })
    
    const option = {
      tooltip: {
        trigger: 'axis',
        axisPointer: {
          type: 'cross'
        }
      },
      legend: {
        data: ['访问量', '用户数']
      },
      xAxis: {
        type: 'category',
        data: response.data.dates
      },
      yAxis: [
        {
          type: 'value',
          name: '访问量',
          position: 'left'
        },
        {
          type: 'value',
          name: '用户数',
          position: 'right'
        }
      ],
      series: [
        {
          name: '访问量',
          type: 'line',
          data: response.data.accessCounts,
          smooth: true,
          itemStyle: {
            color: '#409EFF'
          }
        },
        {
          name: '用户数',
          type: 'line',
          yAxisIndex: 1,
          data: response.data.userCounts,
          smooth: true,
          itemStyle: {
            color: '#67C23A'
          }
        }
      ]
    }
    
    accessTrendChartInstance?.setOption(option)
  } catch (error) {
    console.error('加载访问趋势失败:', error)
  }
}

/**
 * 加载资源类型分布
 */
const loadResourceTypeDistribution = async () => {
  try {
    const response = await getResourceTypeDistribution()
    
    const option = {
      tooltip: {
        trigger: 'item',
        formatter: '{a} <br/>{b}: {c} ({d}%)'
      },
      legend: {
        orient: 'vertical',
        left: 'left'
      },
      series: [
        {
          name: '资源类型',
          type: 'pie',
          radius: '50%',
          data: response.data.map((item: any) => ({
            value: item.count,
            name: getResourceTypeLabel(item.type)
          })),
          emphasis: {
            itemStyle: {
              shadowBlur: 10,
              shadowOffsetX: 0,
              shadowColor: 'rgba(0, 0, 0, 0.5)'
            }
          }
        }
      ]
    }
    
    resourceTypeChartInstance?.setOption(option)
  } catch (error) {
    console.error('加载资源类型分布失败:', error)
  }
}

/**
 * 加载用户活跃度
 */
const loadUserActivity = async () => {
  try {
    const response = await getUserActivity({
      startDate: dateRange.value[0],
      endDate: dateRange.value[1]
    })
    
    const option = {
      tooltip: {
        trigger: 'axis'
      },
      xAxis: {
        type: 'category',
        data: response.data.hours
      },
      yAxis: {
        type: 'value',
        name: '活跃用户数'
      },
      series: [
        {
          name: '活跃用户数',
          type: 'bar',
          data: response.data.counts,
          itemStyle: {
            color: '#E6A23C'
          }
        }
      ]
    }
    
    userActivityChartInstance?.setOption(option)
  } catch (error) {
    console.error('加载用户活跃度失败:', error)
  }
}

/**
 * 加载热门资源
 */
const loadPopularResources = async () => {
  try {
    const response = await getPopularResources({
      startDate: dateRange.value[0],
      endDate: dateRange.value[1],
      limit: 10
    })
    popularResources.value = response.data
  } catch (error) {
    console.error('加载热门资源失败:', error)
  }
}

/**
 * 加载访问记录
 */
const loadAccessRecords = async () => {
  try {
    tableLoading.value = true
    const response = await getAccessRecords({
      page: pagination.page,
      size: pagination.size,
      keyword: searchKeyword.value,
      startDate: dateRange.value[0],
      endDate: dateRange.value[1]
    })
    
    accessRecords.value = response.data.records
    pagination.total = response.data.total
  } catch (error) {
    console.error('加载访问记录失败:', error)
    ElMessage.error('加载访问记录失败')
  } finally {
    tableLoading.value = false
  }
}

/**
 * 刷新所有数据
 */
const refreshData = async () => {
  await Promise.all([
    loadStatistics(),
    loadAccessTrend(),
    loadResourceTypeDistribution(),
    loadUserActivity(),
    loadPopularResources(),
    loadAccessRecords()
  ])
}

/**
 * 处理日期范围变化
 */
const handleDateChange = () => {
  refreshData()
}

/**
 * 处理分页大小变化
 */
const handleSizeChange = (size: number) => {
  pagination.size = size
  pagination.page = 1
  loadAccessRecords()
}

/**
 * 处理页码变化
 */
const handlePageChange = (page: number) => {
  pagination.page = page
  loadAccessRecords()
}

/**
 * 导出数据
 */
const exportData = async () => {
  try {
    await exportStatistics({
      startDate: dateRange.value[0],
      endDate: dateRange.value[1],
      keyword: searchKeyword.value
    })
    ElMessage.success('导出成功')
  } catch (error) {
    console.error('导出失败:', error)
    ElMessage.error('导出失败')
  }
}

// 工具函数
const formatNumber = (num: number): string => {
  if (num >= 1000000) {
    return (num / 1000000).toFixed(1) + 'M'
  } else if (num >= 1000) {
    return (num / 1000).toFixed(1) + 'K'
  }
  return num.toString()
}

const formatBytes = (bytes: number): string => {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB', 'TB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

const formatDateTime = (dateTime: string): string => {
  return new Date(dateTime).toLocaleString('zh-CN')
}

const formatDuration = (seconds: number): string => {
  if (seconds < 60) {
    return `${seconds}秒`
  } else if (seconds < 3600) {
    return `${Math.floor(seconds / 60)}分钟`
  } else {
    return `${Math.floor(seconds / 3600)}小时`
  }
}

const getChangeClass = (change: number): string => {
  return change > 0 ? 'positive' : change < 0 ? 'negative' : 'neutral'
}

const getResourceTypeLabel = (type: string): string => {
  const labels: Record<string, string> = {
    database: '数据库',
    api: 'API接口',
    file: '文件',
    other: '其他'
  }
  return labels[type] || type
}

const getAccessTypeLabel = (type: string): string => {
  const labels: Record<string, string> = {
    view: '查看',
    download: '下载',
    query: '查询',
    edit: '编辑'
  }
  return labels[type] || type
}

const getAccessTypeTagType = (type: string): string => {
  const types: Record<string, string> = {
    view: 'info',
    download: 'success',
    query: 'warning',
    edit: 'danger'
  }
  return types[type] || 'info'
}

// 监听访问趋势类型变化
watch(accessTrendType, () => {
  loadAccessTrend()
})

// 监听搜索关键词变化
watch(searchKeyword, () => {
  pagination.page = 1
  loadAccessRecords()
}, { debounce: 500 })

// 生命周期
onMounted(async () => {
  initCharts()
  await refreshData()
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  accessTrendChartInstance?.dispose()
  resourceTypeChartInstance?.dispose()
  userActivityChartInstance?.dispose()
})
</script>

<style lang="scss" scoped>
@use "@/styles/variables.scss" as *;

.statistics-dashboard {
  height: 100%;
  display: flex;
  flex-direction: column;
  background-color: $bg-color;

  .page-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: $spacing-lg;
    background: $bg-color-white;
    border-bottom: 1px solid $border-color-light;
    margin-bottom: $spacing-md;

    .header-left {
      .page-title {
        margin: 0 0 $spacing-xs 0;
        font-size: $font-size-xl;
        font-weight: 600;
        color: $text-color-primary;
      }

      .page-description {
        margin: 0;
        color: $text-color-regular;
        font-size: $font-size-sm;
      }
    }

    .header-right {
      display: flex;
      gap: $spacing-sm;
      align-items: center;
    }
  }

  .stats-cards {
    padding: 0 $spacing-lg;
    margin-bottom: $spacing-lg;

    .stat-card {
      display: flex;
      align-items: center;
      padding: $spacing-lg;
      background: $bg-color-white;
      border-radius: $border-radius-base;
      box-shadow: $box-shadow-light;
      transition: all 0.3s;

      &:hover {
        box-shadow: $box-shadow-base;
        transform: translateY(-2px);
      }

      .stat-icon {
        width: 60px;
        height: 60px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        margin-right: $spacing-lg;
        font-size: 24px;
        color: white;

        &.resource {
          background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        }

        &.access {
          background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        }

        &.user {
          background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
        }

        &.storage {
          background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%);
        }
      }

      .stat-content {
        flex: 1;

        .stat-value {
          font-size: 28px;
          font-weight: 600;
          color: $text-color-primary;
          margin-bottom: $spacing-xs;
        }

        .stat-label {
          font-size: $font-size-sm;
          color: $text-color-regular;
          margin-bottom: $spacing-xs;
        }

        .stat-change {
          display: flex;
          align-items: center;
          gap: $spacing-xs;
          font-size: $font-size-sm;
          font-weight: 500;

          &.positive {
            color: $color-success;
          }

          &.negative {
            color: $color-danger;
          }

          &.neutral {
            color: $text-color-regular;
          }
        }
      }
    }
  }

  .charts-container {
    padding: 0 $spacing-lg;
    margin-bottom: $spacing-lg;

    .chart-card {
      .card-header {
        display: flex;
        justify-content: space-between;
        align-items: center;

        .card-title {
          font-size: $font-size-lg;
          font-weight: 600;
          color: $text-color-primary;
        }
      }

      .chart {
        width: 100%;
      }
    }

    .popular-resources {
      .resource-item {
        display: flex;
        align-items: center;
        padding: $spacing-md 0;
        border-bottom: 1px solid $border-color-lighter;

        &:last-child {
          border-bottom: none;
        }

        .rank {
          width: 30px;
          height: 30px;
          border-radius: 50%;
          background: $color-primary;
          color: white;
          display: flex;
          align-items: center;
          justify-content: center;
          font-weight: 600;
          margin-right: $spacing-md;
        }

        .resource-info {
          flex: 1;

          .resource-name {
            font-weight: 500;
            color: $text-color-primary;
            margin-bottom: $spacing-xs;
          }

          .resource-type {
            font-size: $font-size-sm;
            color: $text-color-regular;
          }
        }

        .access-count {
          font-size: $font-size-lg;
          font-weight: 600;
          color: $color-primary;
        }
      }
    }
  }

  .data-table {
    flex: 1;
    padding: 0 $spacing-lg $spacing-lg;
    overflow: hidden;

    .el-card {
      height: 100%;
      display: flex;
      flex-direction: column;

      :deep(.el-card__body) {
        flex: 1;
        display: flex;
        flex-direction: column;
        overflow: hidden;
      }
    }

    .card-header {
      display: flex;
      justify-content: space-between;
      align-items: center;

      .card-title {
        font-size: $font-size-lg;
        font-weight: 600;
        color: $text-color-primary;
      }

      .header-actions {
        display: flex;
        gap: $spacing-sm;
        align-items: center;
      }
    }

    .pagination {
      display: flex;
      justify-content: center;
      margin-top: $spacing-lg;
    }
  }
}

// 响应式设计
@media (max-width: 768px) {
  .statistics-dashboard {
    .page-header {
      flex-direction: column;
      gap: $spacing-md;
      align-items: stretch;
    }

    .stats-cards {
      padding: 0 $spacing-md;

      .stat-card {
        .stat-icon {
          width: 50px;
          height: 50px;
          font-size: 20px;
          margin-right: $spacing-md;
        }

        .stat-content {
          .stat-value {
            font-size: 24px;
          }
        }
      }
    }

    .charts-container {
      padding: 0 $spacing-md;

      .chart {
        height: 250px !important;
      }
    }

    .data-table {
      padding: 0 $spacing-md $spacing-md;

      .card-header {
        flex-direction: column;
        gap: $spacing-md;
        align-items: stretch;
      }
    }
  }
}

// 暗色主题适配
.dark {
  .statistics-dashboard {
    background-color: $dark-bg-color;

    .page-header {
      background: $dark-bg-color-light;
      border-bottom-color: $dark-border-color;

      .page-title {
        color: $dark-text-color-primary;
      }

      .page-description {
        color: $dark-text-color-regular;
      }
    }

    .stats-cards {
      .stat-card {
        background: $dark-bg-color-light;

        .stat-content {
          .stat-value {
            color: $dark-text-color-primary;
          }

          .stat-label {
            color: $dark-text-color-regular;
          }
        }
      }
    }

    .charts-container {
      .card-title {
        color: $dark-text-color-primary;
      }

      .popular-resources {
        .resource-item {
          border-bottom-color: $dark-border-color;

          .resource-info {
            .resource-name {
              color: $dark-text-color-primary;
            }

            .resource-type {
              color: $dark-text-color-regular;
            }
          }
        }
      }
    }

    .data-table {
      .card-title {
        color: $dark-text-color-primary;
      }
    }
  }
}
</style>