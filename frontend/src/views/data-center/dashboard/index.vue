<template>
  <div class="dashboard-container">
    <!-- 欢迎区域 -->
    <div class="welcome-section">
      <div class="welcome-content">
        <h1 class="welcome-title">
          <el-icon><Odometer /></el-icon>
          欢迎使用 CEPIEC 数据中台
        </h1>
        <p class="welcome-subtitle">智能数据管理，助力业务决策</p>
      </div>
      <div class="welcome-actions">
        <el-button type="primary" size="large" @click="goToDataResources">
          <el-icon><DataBoard /></el-icon>
          数据资源管理
        </el-button>
        <el-button size="large" @click="goToStatistics">
          <el-icon><TrendCharts /></el-icon>
          数据统计
        </el-button>
      </div>
    </div>

    <!-- 统计卡片 -->
    <div class="stats-grid">
      <div class="stat-card" v-for="stat in stats" :key="stat.key">
        <div class="stat-icon" :style="{ backgroundColor: stat.color }">
          <el-icon :size="24">
            <component :is="stat.icon" />
          </el-icon>
        </div>
        <div class="stat-content">
          <div class="stat-value">{{ stat.value }}</div>
          <div class="stat-label">{{ stat.label }}</div>
          <div class="stat-trend" :class="stat.trend.type">
            <el-icon>
              <component :is="stat.trend.icon" />
            </el-icon>
            <span>{{ stat.trend.value }}</span>
          </div>
        </div>
      </div>
    </div>

    <!-- 图表区域 -->
    <div class="charts-section">
      <div class="chart-row">
        <!-- 数据趋势图 -->
        <div class="chart-card">
          <div class="chart-header">
            <h3>数据增长趋势</h3>
            <el-button-group size="small">
              <el-button :type="trendPeriod === '7d' ? 'primary' : ''" @click="changeTrendPeriod('7d')">7天</el-button>
              <el-button :type="trendPeriod === '30d' ? 'primary' : ''" @click="changeTrendPeriod('30d')">30天</el-button>
              <el-button :type="trendPeriod === '90d' ? 'primary' : ''" @click="changeTrendPeriod('90d')">90天</el-button>
            </el-button-group>
          </div>
          <div class="chart-content" ref="trendChartRef">
            <v-chart 
              class="chart" 
              :option="trendChartOption" 
              autoresize
            />
          </div>
        </div>

        <!-- 数据分布图 -->
        <div class="chart-card">
          <div class="chart-header">
            <h3>数据类型分布</h3>
            <el-button size="small" @click="refreshDistribution">
              <el-icon><Refresh /></el-icon>
            </el-button>
          </div>
          <div class="chart-content" ref="distributionChartRef">
            <v-chart 
              class="chart" 
              :option="distributionChartOption" 
              autoresize
            />
          </div>
        </div>
      </div>
    </div>

    <!-- 快捷操作 -->
    <div class="quick-actions">
      <h3 class="section-title">
        <el-icon><Lightning /></el-icon>
        快捷操作
      </h3>
      <div class="actions-grid">
        <div class="action-item" v-for="action in quickActions" :key="action.key" @click="handleAction(action)">
          <div class="action-icon" :style="{ backgroundColor: action.color }">
            <el-icon :size="20">
              <component :is="action.icon" />
            </el-icon>
          </div>
          <div class="action-content">
            <div class="action-title">{{ action.title }}</div>
            <div class="action-desc">{{ action.description }}</div>
          </div>
        </div>
      </div>
    </div>

    <!-- 最近活动 -->
    <div class="recent-activities">
      <h3 class="section-title">
        <el-icon><Clock /></el-icon>
        最近活动
      </h3>
      <div class="activity-list">
        <div class="activity-item" v-for="activity in recentActivities" :key="activity.id">
          <div class="activity-icon" :style="{ backgroundColor: activity.color }">
            <el-icon>
              <component :is="activity.icon" />
            </el-icon>
          </div>
          <div class="activity-content">
            <div class="activity-title">{{ activity.title }}</div>
            <div class="activity-time">{{ formatTime(activity.time) }}</div>
          </div>
          <div class="activity-status">
            <el-tag :type="activity.status.type" size="small">{{ activity.status.text }}</el-tag>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, nextTick, computed } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { 
  Odometer, 
  DataBoard, 
  TrendCharts, 
  User, 
  Connection, 
  Coin, 
  Upload, 
  Search, 
  Download, 
  Setting, 
  Lightning, 
  Clock, 
  Refresh, 
  ArrowUp, 
  ArrowDown,
  Delete
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

const router = useRouter()

// 图表引用
const trendChartRef = ref<HTMLElement>()
const distributionChartRef = ref<HTMLElement>()

// 响应式数据
const trendPeriod = ref('90d')

// 统计数据
const stats = ref([
  {
    key: 'totalData',
    label: '总数据量',
    value: '1.2M',
    icon: 'DataBoard',
    color: '#409EFF',
    trend: { type: 'up', value: '+12.5%', icon: 'ArrowUp' }
  },
  {
    key: 'activeUsers',
    label: '活跃用户',
    value: '2,847',
    icon: 'User',
    color: '#67C23A',
    trend: { type: 'up', value: '+8.2%', icon: 'ArrowUp' }
  },
  {
    key: 'apiCalls',
    label: 'API调用',
    value: '45.6K',
    icon: 'Connection',
    color: '#E6A23C',
    trend: { type: 'down', value: '-2.1%', icon: 'ArrowDown' }
  },
  {
    key: 'storage',
    label: '存储使用',
    value: '78.5GB',
    icon: 'Coin',
    color: '#F56C6C',
    trend: { type: 'up', value: '+15.3%', icon: 'ArrowUp' }
  }
])

// 快捷操作
const quickActions = ref([
  {
    key: 'upload',
    title: '上传数据',
    description: '批量上传数据文件',
    icon: 'Upload',
    color: '#409EFF'
  },
  {
    key: 'query',
    title: '数据查询',
    description: '快速查询数据',
    icon: 'Search',
    color: '#67C23A'
  },
  {
    key: 'export',
    title: '导出报表',
    description: '生成数据报表',
    icon: 'Download',
    color: '#E6A23C'
  },
  {
    key: 'settings',
    title: '系统设置',
    description: '配置系统参数',
    icon: 'Setting',
    color: '#909399'
  }
])

// 最近活动
const recentActivities = ref([
  {
    id: 1,
    title: '用户数据导入完成',
    time: new Date(Date.now() - 5 * 60 * 1000),
    icon: 'Upload',
    color: '#67C23A',
    status: { type: 'success', text: '成功' }
  },
  {
    id: 2,
    title: '系统备份任务执行',
    time: new Date(Date.now() - 15 * 60 * 1000),
    icon: 'Coin',
    color: '#409EFF',
    status: { type: 'success', text: '完成' }
  },
  {
    id: 3,
    title: '数据清理任务失败',
    time: new Date(Date.now() - 30 * 60 * 1000),
    icon: 'Delete',
    color: '#F56C6C',
    status: { type: 'danger', text: '失败' }
  },
  {
    id: 4,
    title: '新用户注册',
    time: new Date(Date.now() - 45 * 60 * 1000),
    icon: 'User',
    color: '#E6A23C',
    status: { type: 'info', text: '待审核' }
  }
])

/**
 * 生成静态数据 - 从2025年9月开始的日增量数据
 * @param days 天数
 * @returns 包含日期和各系统数据的对象
 */
const generateStaticData = (days: number) => {
  const startDate = new Date('2025-09-01')
  const dates: string[] = []
  const erpData: number[] = []
  const aixueshuData: number[] = []
  const processingData: number[] = []
  
  for (let i = 0; i < days; i++) {
    const currentDate = new Date(startDate)
    currentDate.setDate(startDate.getDate() + i)
    dates.push(currentDate.toLocaleDateString('zh-CN', { month: '2-digit', day: '2-digit' }))
    
    // 生成模拟数据，带有一定的随机性和趋势
    const baseErp = 1200 + i * 15 + Math.random() * 200 - 100
    const baseAixueshu = 800 + i * 12 + Math.random() * 150 - 75
    const baseProcessing = 600 + i * 8 + Math.random() * 100 - 50
    
    erpData.push(Math.max(0, Math.round(baseErp)))
    aixueshuData.push(Math.max(0, Math.round(baseAixueshu)))
    processingData.push(Math.max(0, Math.round(baseProcessing)))
  }
  
  return { dates, erpData, aixueshuData, processingData }
}

/**
 * 根据时间周期获取数据
 */
const getTrendData = computed(() => {
  const dayMap = {
    '7d': 7,
    '30d': 30,
    '90d': 90
  }
  return generateStaticData(dayMap[trendPeriod.value as keyof typeof dayMap])
})

/**
 * 趋势图表配置
 */
const trendChartOption = computed(() => {
  const data = getTrendData.value
  
  return {
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'cross',
        label: {
          backgroundColor: '#6a7985'
        }
      }
    },
    legend: {
      data: ['ERP系统', '爱学术平台', '加工平台'],
      top: 10
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      containLabel: true
    },
    xAxis: [
      {
        type: 'category',
        boundaryGap: false,
        data: data.dates,
        axisLabel: {
          rotate: 45
        }
      }
    ],
    yAxis: [
      {
        type: 'value',
        name: '数据增量',
        axisLabel: {
          formatter: '{value}'
        }
      }
    ],
    series: [
      {
        name: 'ERP系统',
        type: 'line',
        stack: 'Total',
        smooth: true,
        lineStyle: {
          width: 3
        },
        areaStyle: {
          opacity: 0.3
        },
        emphasis: {
          focus: 'series'
        },
        data: data.erpData,
        itemStyle: {
          color: '#409EFF'
        }
      },
      {
        name: '爱学术平台',
        type: 'bar',
        data: data.aixueshuData,
        itemStyle: {
          color: '#67C23A'
        }
      },
      {
        name: '加工平台',
        type: 'line',
        smooth: true,
        lineStyle: {
          width: 2,
          type: 'dashed'
        },
        emphasis: {
          focus: 'series'
        },
        data: data.processingData,
        itemStyle: {
          color: '#E6A23C'
        }
      }
    ]
  }
})

/**
 * 数据分布图表配置
 */
const distributionChartOption = computed(() => {
  return {
    title: {
      text: '数据类型分布',
      left: 'center',
      textStyle: {
        fontSize: 16,
        fontWeight: 'bold'
      }
    },
    tooltip: {
      trigger: 'item',
      formatter: '{a} <br/>{b}: {c} ({d}%)'
    },
    legend: {
      orient: 'vertical',
      left: 'left',
      top: 'middle'
    },
    series: [
      {
        name: '数据类型',
        type: 'pie',
        radius: ['40%', '70%'],
        center: ['60%', '50%'],
        avoidLabelOverlap: false,
        itemStyle: {
          borderRadius: 10,
          borderColor: '#fff',
          borderWidth: 2
        },
        label: {
          show: false,
          position: 'center'
        },
        emphasis: {
          label: {
            show: true,
            fontSize: 20,
            fontWeight: 'bold'
          }
        },
        labelLine: {
          show: false
        },
        data: [
          { 
            value: 42, 
            name: '图书', 
            itemStyle: { color: '#5470c6' }
          },
          { 
            value: 28, 
            name: '期刊文章', 
            itemStyle: { color: '#91cc75' }
          },
          { 
            value: 15, 
            name: '会议录', 
            itemStyle: { color: '#fac858' }
          },
          { 
            value: 10, 
            name: '学术论文', 
            itemStyle: { color: '#ee6666' }
          },
          { 
            value: 5, 
            name: '教材', 
            itemStyle: { color: '#73c0de' }
          }
        ]
      }
    ]
  }
})

/**
 * 切换趋势周期
 * @param period 时间周期
 */
const changeTrendPeriod = (period: string) => {
  trendPeriod.value = period
  ElMessage.success(`已切换到${period === '7d' ? '7天' : period === '30d' ? '30天' : '90天'}视图`)
}

/**
 * 格式化时间
 * @param time 时间对象
 * @returns 格式化后的时间字符串
 */
const formatTime = (time: Date) => {
  const now = new Date()
  const diff = now.getTime() - time.getTime()
  const minutes = Math.floor(diff / (1000 * 60))
  
  if (minutes < 1) return '刚刚'
  if (minutes < 60) return `${minutes}分钟前`
  
  const hours = Math.floor(minutes / 60)
  if (hours < 24) return `${hours}小时前`
  
  const days = Math.floor(hours / 24)
  return `${days}天前`
}

/**
 * 跳转到数据资源管理
 */
const goToDataResources = () => {
  router.push('/data-center/data-resources')
}

/**
 * 跳转到数据统计
 */
const goToStatistics = () => {
  router.push('/data-center/statistics')
}

/**
 * 处理快捷操作
 * @param action 操作对象
 */
const handleAction = (action: any) => {
  switch (action.key) {
    case 'upload':
      router.push('/data-center/data-resources/create')
      break
    case 'query':
      router.push('/data-center/data-resources/query')
      break
    case 'export':
      ElMessage.info('导出功能开发中...')
      break
    case 'settings':
      ElMessage.info('系统设置功能开发中...')
      break
    default:
      ElMessage.info(`执行操作: ${action.title}`)
  }
}

/**
 * 刷新分布图
 */
const refreshDistribution = () => {
  ElMessage.success('数据分布图已刷新')
}

/**
 * 组件挂载时初始化
 */
onMounted(() => {
  nextTick(() => {
    console.log('数据中心Dashboard初始化完成')
  })
})
</script>

<style lang="scss" scoped>
.dashboard-container {
  padding: 20px;
  background: var(--el-bg-color-page);
  min-height: 100vh;
}

.welcome-section {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 32px;
  background: linear-gradient(135deg, #409EFF 0%, #67C23A 100%);
  border-radius: 12px;
  color: white;
  margin-bottom: 24px;
  
  .welcome-content {
    .welcome-title {
      display: flex;
      align-items: center;
      font-size: 28px;
      font-weight: 600;
      margin: 0 0 8px 0;
      
      .el-icon {
        margin-right: 12px;
      }
    }
    
    .welcome-subtitle {
      font-size: 16px;
      opacity: 0.9;
      margin: 0;
    }
  }
  
  .welcome-actions {
    display: flex;
    gap: 12px;
  }
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 20px;
  margin-bottom: 24px;
  
  .stat-card {
    display: flex;
    align-items: center;
    padding: 24px;
    background: var(--el-bg-color);
    border-radius: 8px;
    border: 1px solid var(--el-border-color-light);
    transition: all 0.3s;
    
    &:hover {
      transform: translateY(-2px);
      box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
    }
    
    .stat-icon {
      width: 48px;
      height: 48px;
      border-radius: 8px;
      display: flex;
      align-items: center;
      justify-content: center;
      color: white;
      margin-right: 16px;
    }
    
    .stat-content {
      flex: 1;
      
      .stat-value {
        font-size: 24px;
        font-weight: 600;
        color: var(--el-text-color-primary);
        margin-bottom: 4px;
      }
      
      .stat-label {
        font-size: 14px;
        color: var(--el-text-color-secondary);
        margin-bottom: 8px;
      }
      
      .stat-trend {
        display: flex;
        align-items: center;
        font-size: 12px;
        
        &.up {
          color: var(--el-color-success);
        }
        
        &.down {
          color: var(--el-color-danger);
        }
        
        .el-icon {
          margin-right: 4px;
        }
      }
    }
  }
}

.charts-section {
  margin-bottom: 24px;
  
  .chart-row {
    display: grid;
    grid-template-columns: 2fr 1fr;
    gap: 20px;
    
    .chart-card {
      background: var(--el-bg-color);
      border-radius: 8px;
      border: 1px solid var(--el-border-color-light);
      overflow: hidden;
      
      .chart-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 20px 24px 16px;
        border-bottom: 1px solid var(--el-border-color-light);
        
        h3 {
          margin: 0;
          font-size: 16px;
          font-weight: 600;
          color: var(--el-text-color-primary);
        }
      }
      
      .chart-content {
        height: 300px;
        padding: 20px;
        
        .chart {
          width: 100%;
          height: 100%;
        }
      }
    }
  }
}

.quick-actions,
.recent-activities {
  background: var(--el-bg-color);
  border-radius: 8px;
  border: 1px solid var(--el-border-color-light);
  padding: 24px;
  margin-bottom: 24px;
  
  .section-title {
    display: flex;
    align-items: center;
    font-size: 18px;
    font-weight: 600;
    color: var(--el-text-color-primary);
    margin: 0 0 20px 0;
    
    .el-icon {
      margin-right: 8px;
      color: var(--el-color-primary);
    }
  }
}

.actions-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 16px;
  
  .action-item {
    display: flex;
    align-items: center;
    padding: 16px;
    border: 1px solid var(--el-border-color-light);
    border-radius: 6px;
    cursor: pointer;
    transition: all 0.3s;
    
    &:hover {
      border-color: var(--el-color-primary);
      background: var(--el-color-primary-light-9);
    }
    
    .action-icon {
      width: 40px;
      height: 40px;
      border-radius: 6px;
      display: flex;
      align-items: center;
      justify-content: center;
      color: white;
      margin-right: 12px;
    }
    
    .action-content {
      .action-title {
        font-size: 14px;
        font-weight: 500;
        color: var(--el-text-color-primary);
        margin-bottom: 4px;
      }
      
      .action-desc {
        font-size: 12px;
        color: var(--el-text-color-secondary);
      }
    }
  }
}

.activity-list {
  .activity-item {
    display: flex;
    align-items: center;
    padding: 12px 0;
    border-bottom: 1px solid var(--el-border-color-lighter);
    
    &:last-child {
      border-bottom: none;
    }
    
    .activity-icon {
      width: 32px;
      height: 32px;
      border-radius: 50%;
      display: flex;
      align-items: center;
      justify-content: center;
      color: white;
      margin-right: 12px;
    }
    
    .activity-content {
      flex: 1;
      
      .activity-title {
        font-size: 14px;
        color: var(--el-text-color-primary);
        margin-bottom: 4px;
      }
      
      .activity-time {
        font-size: 12px;
        color: var(--el-text-color-secondary);
      }
    }
  }
}

// 响应式设计
@media (max-width: 768px) {
  .dashboard-container {
    padding: 16px;
  }
  
  .welcome-section {
    flex-direction: column;
    text-align: center;
    gap: 20px;
    
    .welcome-actions {
      justify-content: center;
    }
  }
  
  .charts-section .chart-row {
    grid-template-columns: 1fr;
  }
  
  .stats-grid {
    grid-template-columns: 1fr;
  }
  
  .actions-grid {
    grid-template-columns: 1fr;
  }
}
</style>