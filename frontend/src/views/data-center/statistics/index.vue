<template>
  <div class="statistics-container">
    <!-- 页面标题 -->
    <div class="page-header">
      <h1 class="page-title">
        <el-icon><TrendCharts /></el-icon>
        数据统计
      </h1>
      <p class="page-description">查看数据资源的使用统计和分析报告</p>
    </div>

    <!-- 时间范围选择 -->
    <div class="time-range-section">
      <el-card>
        <div class="time-range-controls">
          <div class="quick-select">
            <span class="label">快速选择：</span>
            <el-button-group>
              <el-button
                v-for="range in quickRanges"
                :key="range.value"
                :type="selectedRange === range.value ? 'primary' : 'default'"
                size="small"
                @click="selectQuickRange(range.value)"
              >
                {{ range.label }}
              </el-button>
            </el-button-group>
          </div>
          
          <div class="custom-range">
            <span class="label">自定义时间：</span>
            <el-date-picker
              v-model="customDateRange"
              type="datetimerange"
              range-separator="至"
              start-placeholder="开始时间"
              end-placeholder="结束时间"
              format="YYYY-MM-DD HH:mm:ss"
              value-format="YYYY-MM-DD HH:mm:ss"
              @change="handleCustomRangeChange"
            />
          </div>
          
          <div class="actions">
            <el-button type="primary" @click="refreshData">
              <el-icon><Refresh /></el-icon>
              刷新数据
            </el-button>
            <el-button @click="exportReport">
              <el-icon><Download /></el-icon>
              导出报告
            </el-button>
          </div>
        </div>
      </el-card>
    </div>

    <!-- 概览统计 -->
    <div class="overview-section">
      <el-row :gutter="20">
        <el-col :span="6">
          <el-card class="stats-card">
            <div class="stats-content">
              <div class="stats-icon">
                <el-icon color="#409EFF"><DataBoard /></el-icon>
              </div>
              <div class="stats-info">
                <div class="stats-number">{{ overviewStats.totalResources }}</div>
                <div class="stats-label">总资源数</div>
                <div class="stats-change" :class="getChangeClass(overviewStats.resourcesChange)">
                  <el-icon><component :is="getChangeIcon(overviewStats.resourcesChange)" /></el-icon>
                  {{ Math.abs(overviewStats.resourcesChange) }}%
                </div>
              </div>
            </div>
          </el-card>
        </el-col>
        <el-col :span="6">
          <el-card class="stats-card">
            <div class="stats-content">
              <div class="stats-icon">
                <el-icon color="#67C23A"><View /></el-icon>
              </div>
              <div class="stats-info">
                <div class="stats-number">{{ formatNumber(overviewStats.totalViews) }}</div>
                <div class="stats-label">总访问量</div>
                <div class="stats-change" :class="getChangeClass(overviewStats.viewsChange)">
                  <el-icon><component :is="getChangeIcon(overviewStats.viewsChange)" /></el-icon>
                  {{ Math.abs(overviewStats.viewsChange) }}%
                </div>
              </div>
            </div>
          </el-card>
        </el-col>
        <el-col :span="6">
          <el-card class="stats-card">
            <div class="stats-content">
              <div class="stats-icon">
                <el-icon color="#E6A23C"><User /></el-icon>
              </div>
              <div class="stats-info">
                <div class="stats-number">{{ overviewStats.activeUsers }}</div>
                <div class="stats-label">活跃用户</div>
                <div class="stats-change" :class="getChangeClass(overviewStats.usersChange)">
                  <el-icon><component :is="getChangeIcon(overviewStats.usersChange)" /></el-icon>
                  {{ Math.abs(overviewStats.usersChange) }}%
                </div>
              </div>
            </div>
          </el-card>
        </el-col>
        <el-col :span="6">
          <el-card class="stats-card">
            <div class="stats-content">
              <div class="stats-icon">
                <el-icon color="#F56C6C"><Coin /></el-icon>
              </div>
              <div class="stats-info">
                <div class="stats-number">{{ formatSize(overviewStats.totalSize) }}</div>
                <div class="stats-label">存储使用</div>
                <div class="stats-change" :class="getChangeClass(overviewStats.sizeChange)">
                  <el-icon><component :is="getChangeIcon(overviewStats.sizeChange)" /></el-icon>
                  {{ Math.abs(overviewStats.sizeChange) }}%
                </div>
              </div>
            </div>
          </el-card>
        </el-col>
      </el-row>
    </div>

    <!-- 图表区域 -->
    <div class="charts-section">
      <el-row :gutter="20">
        <!-- 访问趋势图 -->
        <el-col :span="12">
          <el-card>
            <template #header>
              <div class="card-header">
                <span>访问趋势</span>
                <el-button-group size="small">
                  <el-button :type="trendType === 'day' ? 'primary' : ''" @click="changeTrendType('day')">按天</el-button>
                  <el-button :type="trendType === 'week' ? 'primary' : ''" @click="changeTrendType('week')">按周</el-button>
                  <el-button :type="trendType === 'month' ? 'primary' : ''" @click="changeTrendType('month')">按月</el-button>
                </el-button-group>
              </div>
            </template>
            <div class="chart-container">
              <v-chart class="chart" :option="trendChartOption" autoresize />
            </div>
          </el-card>
        </el-col>

        <!-- 资源类型分布 -->
        <el-col :span="12">
          <el-card>
            <template #header>
              <div class="card-header">
                <span>资源类型分布</span>
                <el-button size="small" @click="refreshTypeDistribution">
                  <el-icon><Refresh /></el-icon>
                </el-button>
              </div>
            </template>
            <div class="chart-container">
              <v-chart class="chart" :option="typeDistributionOption" autoresize />
            </div>
          </el-card>
        </el-col>
      </el-row>

      <el-row :gutter="20" style="margin-top: 20px;">
        <!-- 热门资源排行 -->
        <el-col :span="12">
          <el-card>
            <template #header>
              <div class="card-header">
                <span>热门资源排行</span>
                <el-button size="small" @click="refreshHotResources">
                  <el-icon><Refresh /></el-icon>
                </el-button>
              </div>
            </template>
            <div class="hot-resources-list">
              <div 
                v-for="(resource, index) in hotResources" 
                :key="resource.id"
                class="hot-resource-item"
              >
                <div class="rank" :class="`rank-${index + 1}`">{{ index + 1 }}</div>
                <div class="resource-info">
                  <div class="resource-name">{{ resource.name }}</div>
                  <div class="resource-type">{{ resource.type }}</div>
                </div>
                <div class="resource-stats">
                  <div class="views">{{ formatNumber(resource.views) }} 次访问</div>
                  <div class="downloads">{{ formatNumber(resource.downloads) }} 次下载</div>
                </div>
              </div>
            </div>
          </el-card>
        </el-col>

        <!-- 用户活跃度 -->
        <el-col :span="12">
          <el-card>
            <template #header>
              <div class="card-header">
                <span>用户活跃度</span>
                <el-button size="small" @click="refreshUserActivity">
                  <el-icon><Refresh /></el-icon>
                </el-button>
              </div>
            </template>
            <div class="chart-container">
              <v-chart class="chart" :option="userActivityOption" autoresize />
            </div>
          </el-card>
        </el-col>
      </el-row>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { 
  TrendCharts, 
  DataBoard, 
  View, 
  User, 
  Coin, 
  Refresh, 
  Download,
  ArrowUp,
  ArrowDown
} from '@element-plus/icons-vue'
import VChart from 'vue-echarts'
import { use } from 'echarts/core'
import {
  CanvasRenderer
} from 'echarts/renderers'
import {
  LineChart,
  BarChart,
  PieChart
} from 'echarts/charts'
import {
  TitleComponent,
  TooltipComponent,
  LegendComponent,
  GridComponent
} from 'echarts/components'

// 注册必要的组件
use([
  CanvasRenderer,
  LineChart,
  BarChart,
  PieChart,
  TitleComponent,
  TooltipComponent,
  LegendComponent,
  GridComponent
])

// 响应式数据
const selectedRange = ref('7d')
const customDateRange = ref<[string, string] | null>(null)
const trendType = ref('day')

// 快速时间范围选项
const quickRanges = ref([
  { label: '今天', value: '1d' },
  { label: '7天', value: '7d' },
  { label: '30天', value: '30d' },
  { label: '90天', value: '90d' }
])

// 概览统计数据
const overviewStats = ref({
  totalResources: 12847,
  resourcesChange: 12.5,
  totalViews: 2847592,
  viewsChange: 8.2,
  activeUsers: 1847,
  usersChange: -2.1,
  totalSize: 78.5 * 1024 * 1024 * 1024, // 78.5GB in bytes
  sizeChange: 15.3
})

// 热门资源数据
const hotResources = ref([
  {
    id: 1,
    name: '机器学习基础教程',
    type: '教材',
    views: 15847,
    downloads: 2847
  },
  {
    id: 2,
    name: '深度学习论文集',
    type: '学术论文',
    views: 12456,
    downloads: 1956
  },
  {
    id: 3,
    name: '数据科学期刊2024',
    type: '期刊文章',
    views: 9876,
    downloads: 1234
  },
  {
    id: 4,
    name: 'AI会议录2024',
    type: '会议录',
    views: 8765,
    downloads: 987
  },
  {
    id: 5,
    name: '计算机视觉图书',
    type: '图书',
    views: 7654,
    downloads: 876
  }
])

/**
 * 生成趋势图表数据
 * @param type 趋势类型
 * @returns 图表数据
 */
const generateTrendData = (type: string) => {
  const now = new Date()
  const data: { date: string; views: number; downloads: number }[] = []
  
  let days = 7
  if (selectedRange.value === '30d') days = 30
  else if (selectedRange.value === '90d') days = 90
  else if (selectedRange.value === '1d') days = 1
  
  for (let i = days - 1; i >= 0; i--) {
    const date = new Date(now.getTime() - i * 24 * 60 * 60 * 1000)
    const dateStr = date.toLocaleDateString('zh-CN', { month: '2-digit', day: '2-digit' })
    
    // 生成模拟数据
    const baseViews = 1000 + Math.random() * 500
    const baseDownloads = 200 + Math.random() * 100
    
    data.push({
      date: dateStr,
      views: Math.round(baseViews),
      downloads: Math.round(baseDownloads)
    })
  }
  
  return data
}

/**
 * 访问趋势图表配置
 */
const trendChartOption = computed(() => {
  const data = generateTrendData(trendType.value)
  
  return {
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'cross'
      }
    },
    legend: {
      data: ['访问量', '下载量']
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      data: data.map(item => item.date)
    },
    yAxis: [
      {
        type: 'value',
        name: '访问量',
        position: 'left'
      },
      {
        type: 'value',
        name: '下载量',
        position: 'right'
      }
    ],
    series: [
      {
        name: '访问量',
        type: 'line',
        data: data.map(item => item.views),
        smooth: true,
        itemStyle: {
          color: '#409EFF'
        }
      },
      {
        name: '下载量',
        type: 'bar',
        yAxisIndex: 1,
        data: data.map(item => item.downloads),
        itemStyle: {
          color: '#67C23A'
        }
      }
    ]
  }
})

/**
 * 资源类型分布图表配置
 */
const typeDistributionOption = computed(() => {
  return {
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
        data: [
          { value: 4200, name: '图书', itemStyle: { color: '#5470c6' } },
          { value: 2800, name: '期刊文章', itemStyle: { color: '#91cc75' } },
          { value: 1500, name: '会议录', itemStyle: { color: '#fac858' } },
          { value: 1000, name: '学术论文', itemStyle: { color: '#ee6666' } },
          { value: 500, name: '教材', itemStyle: { color: '#73c0de' } }
        ],
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
})

/**
 * 用户活跃度图表配置
 */
const userActivityOption = computed(() => {
  const hours = Array.from({ length: 24 }, (_, i) => `${i}:00`)
  const activityData = hours.map(() => Math.floor(Math.random() * 100) + 20)
  
  return {
    tooltip: {
      trigger: 'axis'
    },
    xAxis: {
      type: 'category',
      data: hours
    },
    yAxis: {
      type: 'value',
      name: '活跃用户数'
    },
    series: [
      {
        name: '活跃用户',
        type: 'line',
        data: activityData,
        smooth: true,
        areaStyle: {
          opacity: 0.3
        },
        itemStyle: {
          color: '#E6A23C'
        }
      }
    ]
  }
})

/**
 * 选择快速时间范围
 * @param range 时间范围
 */
const selectQuickRange = (range: string) => {
  selectedRange.value = range
  customDateRange.value = null
  ElMessage.success(`已切换到${quickRanges.value.find(r => r.value === range)?.label}视图`)
}

/**
 * 处理自定义时间范围变化
 * @param value 时间范围值
 */
const handleCustomRangeChange = (value: [string, string] | null) => {
  if (value) {
    selectedRange.value = 'custom'
    ElMessage.success('已应用自定义时间范围')
  }
}

/**
 * 切换趋势类型
 * @param type 趋势类型
 */
const changeTrendType = (type: string) => {
  trendType.value = type
  ElMessage.success(`已切换到${type === 'day' ? '按天' : type === 'week' ? '按周' : '按月'}视图`)
}

/**
 * 获取变化趋势的样式类
 * @param change 变化值
 * @returns 样式类名
 */
const getChangeClass = (change: number) => {
  return change >= 0 ? 'positive' : 'negative'
}

/**
 * 获取变化趋势的图标
 * @param change 变化值
 * @returns 图标组件名
 */
const getChangeIcon = (change: number) => {
  return change >= 0 ? 'ArrowUp' : 'ArrowDown'
}

/**
 * 格式化数字
 * @param num 数字
 * @returns 格式化后的字符串
 */
const formatNumber = (num: number) => {
  if (num >= 1000000) {
    return (num / 1000000).toFixed(1) + 'M'
  } else if (num >= 1000) {
    return (num / 1000).toFixed(1) + 'K'
  }
  return num.toString()
}

/**
 * 格式化文件大小
 * @param bytes 字节数
 * @returns 格式化后的大小字符串
 */
const formatSize = (bytes: number) => {
  const units = ['B', 'KB', 'MB', 'GB', 'TB']
  let size = bytes
  let unitIndex = 0
  
  while (size >= 1024 && unitIndex < units.length - 1) {
    size /= 1024
    unitIndex++
  }
  
  return `${size.toFixed(1)}${units[unitIndex]}`
}

/**
 * 刷新数据
 */
const refreshData = () => {
  ElMessage.success('数据已刷新')
}

/**
 * 导出报告
 */
const exportReport = () => {
  ElMessage.info('导出功能开发中...')
}

/**
 * 刷新类型分布
 */
const refreshTypeDistribution = () => {
  ElMessage.success('资源类型分布已刷新')
}

/**
 * 刷新热门资源
 */
const refreshHotResources = () => {
  ElMessage.success('热门资源排行已刷新')
}

/**
 * 刷新用户活跃度
 */
const refreshUserActivity = () => {
  ElMessage.success('用户活跃度数据已刷新')
}

/**
 * 组件挂载时初始化
 */
onMounted(() => {
  console.log('数据统计页面初始化完成')
})
</script>

<style lang="scss" scoped>
.statistics-container {
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

.time-range-section {
  margin-bottom: 24px;
  
  .time-range-controls {
    display: flex;
    align-items: center;
    gap: 24px;
    flex-wrap: wrap;
    
    .label {
      font-weight: 500;
      color: var(--el-text-color-primary);
    }
    
    .quick-select,
    .custom-range {
      display: flex;
      align-items: center;
      gap: 8px;
    }
    
    .actions {
      margin-left: auto;
    }
  }
}

.overview-section {
  margin-bottom: 24px;
  
  .stats-card {
    .stats-content {
      display: flex;
      align-items: center;
      
      .stats-icon {
        font-size: 32px;
        margin-right: 16px;
      }
      
      .stats-info {
        flex: 1;
        
        .stats-number {
          font-size: 24px;
          font-weight: 600;
          color: var(--el-text-color-primary);
          margin-bottom: 4px;
        }
        
        .stats-label {
          font-size: 14px;
          color: var(--el-text-color-secondary);
          margin-bottom: 8px;
        }
        
        .stats-change {
          display: flex;
          align-items: center;
          font-size: 12px;
          
          &.positive {
            color: var(--el-color-success);
          }
          
          &.negative {
            color: var(--el-color-danger);
          }
          
          .el-icon {
            margin-right: 4px;
          }
        }
      }
    }
  }
}

.charts-section {
  .card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
  }
  
  .chart-container {
    height: 300px;
    
    .chart {
      width: 100%;
      height: 100%;
    }
  }
}

.hot-resources-list {
  .hot-resource-item {
    display: flex;
    align-items: center;
    padding: 12px 0;
    border-bottom: 1px solid var(--el-border-color-lighter);
    
    &:last-child {
      border-bottom: none;
    }
    
    .rank {
      width: 32px;
      height: 32px;
      border-radius: 50%;
      display: flex;
      align-items: center;
      justify-content: center;
      font-weight: 600;
      color: white;
      margin-right: 12px;
      
      &.rank-1 {
        background: #FFD700;
      }
      
      &.rank-2 {
        background: #C0C0C0;
      }
      
      &.rank-3 {
        background: #CD7F32;
      }
      
      &:not(.rank-1):not(.rank-2):not(.rank-3) {
        background: var(--el-color-info);
      }
    }
    
    .resource-info {
      flex: 1;
      
      .resource-name {
        font-size: 14px;
        font-weight: 500;
        color: var(--el-text-color-primary);
        margin-bottom: 4px;
      }
      
      .resource-type {
        font-size: 12px;
        color: var(--el-text-color-secondary);
      }
    }
    
    .resource-stats {
      text-align: right;
      
      .views,
      .downloads {
        font-size: 12px;
        color: var(--el-text-color-secondary);
      }
    }
  }
}

// 响应式设计
@media (max-width: 768px) {
  .statistics-container {
    padding: 16px;
  }
  
  .time-range-controls {
    flex-direction: column;
    align-items: flex-start !important;
    gap: 16px !important;
    
    .actions {
      margin-left: 0 !important;
    }
  }
  
  .overview-section {
    :deep(.el-col) {
      margin-bottom: 16px;
    }
  }
  
  .charts-section {
    :deep(.el-col) {
      margin-bottom: 16px;
    }
  }
}
</style>