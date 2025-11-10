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
                <el-icon color="#F56C6C"><Download /></el-icon>
              </div>
              <div class="stats-info">
                <div class="stats-number">{{ formatNumber(overviewStats.totalDownloads) }}</div>
                <div class="stats-label">总下载量</div>
                <div class="stats-change" :class="getChangeClass(overviewStats.downloadsChange)">
                  <el-icon><component :is="getChangeIcon(overviewStats.downloadsChange)" /></el-icon>
                  {{ Math.abs(overviewStats.downloadsChange) }}%
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
                <el-select v-model="trendChartType" size="small" style="width: 120px">
                  <el-option label="访问量" value="views" />
                  <el-option label="下载量" value="downloads" />
                  <el-option label="用户数" value="users" />
                </el-select>
              </div>
            </template>
            <div ref="trendChartRef" class="chart-container"></div>
          </el-card>
        </el-col>
        
        <!-- 资源类型分布 -->
        <el-col :span="12">
          <el-card>
            <template #header>
              <span>资源类型分布</span>
            </template>
            <div ref="typeChartRef" class="chart-container"></div>
          </el-card>
        </el-col>
      </el-row>
      
      <el-row :gutter="20" style="margin-top: 20px">
        <!-- 热门资源排行 -->
        <el-col :span="12">
          <el-card>
            <template #header>
              <div class="card-header">
                <span>热门资源排行</span>
                <el-select v-model="rankingType" size="small" style="width: 120px">
                  <el-option label="访问量" value="views" />
                  <el-option label="下载量" value="downloads" />
                </el-select>
              </div>
            </template>
            <div class="ranking-list">
              <div
                v-for="(item, index) in topResources"
                :key="item.id"
                class="ranking-item"
              >
                <div class="ranking-number" :class="getRankingClass(index)">
                  {{ index + 1 }}
                </div>
                <div class="resource-info">
                  <div class="resource-name">{{ item.name }}</div>
                  <div class="resource-meta">
                    <el-tag type="info" size="small">{{ item.type }}</el-tag>
                    <span class="resource-category">{{ item.category }}</span>
                  </div>
                </div>
                <div class="resource-stats">
                  <div class="stat-value">{{ formatNumber(item.value) }}</div>
                  <div class="stat-label">{{ rankingType === 'views' ? '访问' : '下载' }}</div>
                </div>
              </div>
            </div>
          </el-card>
        </el-col>
        
        <!-- 用户活跃度 -->
        <el-col :span="12">
          <el-card>
            <template #header>
              <span>用户活跃度</span>
            </template>
            <div ref="userActivityChartRef" class="chart-container"></div>
          </el-card>
        </el-col>
      </el-row>
    </div>

    <!-- 详细统计表格 -->
    <div class="table-section">
      <el-card>
        <template #header>
          <div class="card-header">
            <span>详细统计</span>
            <div class="header-actions">
              <el-input
                v-model="searchKeyword"
                placeholder="搜索资源名称"
                style="width: 200px"
                clearable
                size="small"
              >
                <template #prefix>
                  <el-icon><Search /></el-icon>
                </template>
              </el-input>
              <el-select v-model="tableFilter" placeholder="筛选类型" size="small" style="width: 120px">
                <el-option label="全部" value="" />
                <el-option label="数据库" value="database" />
                <el-option label="API" value="api" />
                <el-option label="文件" value="file" />
              </el-select>
            </div>
          </div>
        </template>
        
        <el-table
          :data="filteredTableData"
          stripe
          border
          style="width: 100%"
          v-loading="tableLoading"
        >
          <el-table-column prop="name" label="资源名称" min-width="200" show-overflow-tooltip />
          <el-table-column prop="type" label="类型" width="100">
            <template #default="{ row }">
              <el-tag type="info" size="small">{{ row.type }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="category" label="分类" width="120" />
          <el-table-column prop="views" label="访问量" width="100" sortable>
            <template #default="{ row }">
              {{ formatNumber(row.views) }}
            </template>
          </el-table-column>
          <el-table-column prop="downloads" label="下载量" width="100" sortable>
            <template #default="{ row }">
              {{ formatNumber(row.downloads) }}
            </template>
          </el-table-column>
          <el-table-column prop="uniqueUsers" label="独立用户" width="100" sortable>
            <template #default="{ row }">
              {{ row.uniqueUsers }}
            </template>
          </el-table-column>
          <el-table-column prop="avgDuration" label="平均使用时长" width="120">
            <template #default="{ row }">
              {{ formatDuration(row.avgDuration) }}
            </template>
          </el-table-column>
          <el-table-column prop="lastAccess" label="最后访问" width="180">
            <template #default="{ row }">
              {{ formatDate(row.lastAccess) }}
            </template>
          </el-table-column>
          <el-table-column label="操作" width="120" fixed="right">
            <template #default="{ row }">
              <el-button size="small" type="primary" link @click="viewDetails(row)">
                <el-icon><View /></el-icon>
                详情
              </el-button>
            </template>
          </el-table-column>
        </el-table>
        
        <!-- 分页 -->
        <div class="pagination-wrapper">
          <el-pagination
            v-model:current-page="currentPage"
            v-model:page-size="pageSize"
            :page-sizes="[10, 20, 50, 100]"
            :total="totalCount"
            layout="total, sizes, prev, pager, next, jumper"
            @size-change="handleSizeChange"
            @current-change="handleCurrentChange"
          />
        </div>
      </el-card>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted, nextTick } from 'vue'
import { ElMessage } from 'element-plus'
import { useRouter } from 'vue-router'
import * as echarts from 'echarts'
import {
  ArrowUp,
  ArrowDown
} from '@element-plus/icons-vue'

// 路由
const router = useRouter()

// 图表引用
const trendChartRef = ref()
const typeChartRef = ref()
const userActivityChartRef = ref()

// 响应式数据
const tableLoading = ref(false)
const selectedRange = ref('7d')
const customDateRange = ref([])
const trendChartType = ref('views')
const rankingType = ref('views')
const searchKeyword = ref('')
const tableFilter = ref('')
const currentPage = ref(1)
const pageSize = ref(20)
const totalCount = ref(0)

// 快速时间范围选项
const quickRanges = [
  { label: '今天', value: '1d' },
  { label: '近7天', value: '7d' },
  { label: '近30天', value: '30d' },
  { label: '近90天', value: '90d' }
]

// 概览统计数据
const overviewStats = reactive({
  totalResources: 1248,
  resourcesChange: 12.5,
  totalViews: 89654,
  viewsChange: 8.3,
  activeUsers: 456,
  usersChange: -2.1,
  totalDownloads: 23456,
  downloadsChange: 15.7
})

// 热门资源数据
const topResources = ref([
  {
    id: 1,
    name: '用户行为分析数据',
    type: '数据库',
    category: '用户数据',
    value: 15678
  },
  {
    id: 2,
    name: '订单统计API',
    type: 'API',
    category: '业务接口',
    value: 12345
  },
  {
    id: 3,
    name: '产品销售报表',
    type: '文件',
    category: '报表文件',
    value: 9876
  },
  {
    id: 4,
    name: '平台信息数据库',
    type: '数据库',
    category: '客户数据',
    value: 8765
  },
  {
    id: 5,
    name: '财务数据接口',
    type: 'API',
    category: '财务接口',
    value: 7654
  }
])

// 详细统计表格数据
const tableData = ref([
  {
    id: 1,
    name: '用户行为分析数据',
    type: 'database',
    category: '用户数据',
    views: 15678,
    downloads: 3456,
    uniqueUsers: 234,
    avgDuration: 1800,
    lastAccess: '2024-01-20 15:30:00'
  },
  {
    id: 2,
    name: '订单统计API',
    type: 'api',
    category: '业务接口',
    views: 12345,
    downloads: 0,
    uniqueUsers: 189,
    avgDuration: 300,
    lastAccess: '2024-01-20 14:45:00'
  },
  {
    id: 3,
    name: '产品销售报表',
    type: 'file',
    category: '报表文件',
    views: 9876,
    downloads: 2345,
    uniqueUsers: 156,
    avgDuration: 600,
    lastAccess: '2024-01-20 13:20:00'
  },
  {
    id: 4,
    name: '平台信息数据库',
    type: 'database',
    category: '客户数据',
    views: 8765,
    downloads: 1234,
    uniqueUsers: 123,
    avgDuration: 2400,
    lastAccess: '2024-01-20 12:10:00'
  },
  {
    id: 5,
    name: '财务数据接口',
    type: 'api',
    category: '财务接口',
    views: 7654,
    downloads: 0,
    uniqueUsers: 98,
    avgDuration: 450,
    lastAccess: '2024-01-20 11:30:00'
  }
])

/**
 * 计算属性
 */
const filteredTableData = computed(() => {
  let result = tableData.value
  
  // 类型筛选
  if (tableFilter.value) {
    result = result.filter(item => item.type === tableFilter.value)
  }
  
  // 关键词搜索
  if (searchKeyword.value) {
    const keyword = searchKeyword.value.toLowerCase()
    result = result.filter(item => 
      item.name.toLowerCase().includes(keyword)
    )
  }
  
  totalCount.value = result.length
  
  // 分页
  const start = (currentPage.value - 1) * pageSize.value
  const end = start + pageSize.value
  return result.slice(start, end)
})

/**
 * 格式化数字
 */
const formatNumber = (num: number) => {
  if (num >= 10000) {
    return (num / 10000).toFixed(1) + 'w'
  } else if (num >= 1000) {
    return (num / 1000).toFixed(1) + 'k'
  }
  return num.toString()
}

/**
 * 格式化时长
 */
const formatDuration = (seconds: number) => {
  const hours = Math.floor(seconds / 3600)
  const minutes = Math.floor((seconds % 3600) / 60)
  
  if (hours > 0) {
    return `${hours}h ${minutes}m`
  } else if (minutes > 0) {
    return `${minutes}m`
  } else {
    return `${seconds}s`
  }
}

/**
 * 格式化日期
 */
const formatDate = (dateStr: string) => {
  if (!dateStr) return '-'
  return new Date(dateStr).toLocaleString('zh-CN')
}

/**
 * 获取变化趋势样式类
 */
const getChangeClass = (change: number) => {
  return change > 0 ? 'positive' : 'negative'
}

/**
 * 获取变化趋势图标
 */
const getChangeIcon = (change: number) => {
  return change > 0 ? ArrowUp : ArrowDown
}

/**
 * 获取排行榜样式类
 */
const getRankingClass = (index: number) => {
  if (index === 0) return 'first'
  if (index === 1) return 'second'
  if (index === 2) return 'third'
  return ''
}

/**
 * 选择快速时间范围
 */
const selectQuickRange = (range: string) => {
  selectedRange.value = range
  customDateRange.value = []
  refreshData()
}

/**
 * 处理自定义时间范围变化
 */
const handleCustomRangeChange = (value: any) => {
  if (value && value.length === 2) {
    selectedRange.value = 'custom'
    refreshData()
  }
}

/**
 * 刷新数据
 */
const refreshData = () => {
  tableLoading.value = true
  
  // 模拟数据刷新
  setTimeout(() => {
    tableLoading.value = false
    ElMessage.success('数据已刷新')
    
    // 重新初始化图表
    nextTick(() => {
      initCharts()
    })
  }, 1000)
}

/**
 * 导出报告
 */
const exportReport = () => {
  ElMessage.success('报告导出功能开发中...')
}

/**
 * 处理分页大小变化
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
 * 查看详情
 */
const viewDetails = (row: any) => {
  console.log('=== 统计页面查看详情调试信息 ===');
  console.log('点击查看详情的数据行:', row);
  console.log('资源ID:', row.id);
  console.log('资源名称:', row.name);
  console.log('当前路由:', route.path);
  console.log('准备跳转到ResourceDetail页面');
  console.log('目标路由参数:', { name: 'ResourceDetail', params: { id: row.id } });
  console.log('========================');
  router.push({
    name: 'ResourceDetail',
    params: { id: row.id }
  })
}

/**
 * 初始化图表
 */
const initCharts = () => {
  initTrendChart()
  initTypeChart()
  initUserActivityChart()
}

/**
 * 初始化趋势图表
 */
const initTrendChart = () => {
  if (!trendChartRef.value) return
  
  const chart = echarts.init(trendChartRef.value)
  
  const option = {
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
      boundaryGap: false,
      data: ['01-14', '01-15', '01-16', '01-17', '01-18', '01-19', '01-20']
    },
    yAxis: {
      type: 'value'
    },
    series: [
      {
        name: '访问量',
        type: 'line',
        stack: 'Total',
        smooth: true,
        data: [1200, 1320, 1010, 1340, 1290, 1330, 1320]
      },
      {
        name: '下载量',
        type: 'line',
        stack: 'Total',
        smooth: true,
        data: [220, 182, 191, 234, 290, 330, 310]
      }
    ]
  }
  
  chart.setOption(option)
  
  // 响应式调整
  window.addEventListener('resize', () => {
    chart.resize()
  })
}

/**
 * 初始化类型分布图表
 */
const initTypeChart = () => {
  if (!typeChartRef.value) return
  
  const chart = echarts.init(typeChartRef.value)
  
  const option = {
    tooltip: {
      trigger: 'item'
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
          { value: 1048, name: '数据库' },
          { value: 735, name: 'API接口' },
          { value: 580, name: '文件资源' },
          { value: 484, name: '缓存数据' },
          { value: 300, name: '其他' }
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
  
  chart.setOption(option)
  
  // 响应式调整
  window.addEventListener('resize', () => {
    chart.resize()
  })
}

/**
 * 初始化用户活跃度图表
 */
const initUserActivityChart = () => {
  if (!userActivityChartRef.value) return
  
  const chart = echarts.init(userActivityChartRef.value)
  
  const option = {
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'shadow'
      }
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      data: ['00:00', '04:00', '08:00', '12:00', '16:00', '20:00']
    },
    yAxis: {
      type: 'value'
    },
    series: [
      {
        name: '活跃用户数',
        type: 'bar',
        data: [12, 8, 45, 78, 65, 32],
        itemStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: '#83bff6' },
            { offset: 0.5, color: '#188df0' },
            { offset: 1, color: '#188df0' }
          ])
        }
      }
    ]
  }
  
  chart.setOption(option)
  
  // 响应式调整
  window.addEventListener('resize', () => {
    chart.resize()
  })
}

/**
 * 组件挂载时初始化
 */
onMounted(() => {
  // 初始化数据
  totalCount.value = tableData.value.length
  
  // 初始化图表
  nextTick(() => {
    initCharts()
  })
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
  margin-bottom: 20px;
  
  .time-range-controls {
    display: flex;
    align-items: center;
    gap: 24px;
    flex-wrap: wrap;
    
    .label {
      font-weight: 500;
      color: var(--el-text-color-regular);
      white-space: nowrap;
    }
    
    .quick-select {
      display: flex;
      align-items: center;
      gap: 12px;
    }
    
    .custom-range {
      display: flex;
      align-items: center;
      gap: 12px;
    }
    
    .actions {
      margin-left: auto;
      display: flex;
      gap: 12px;
    }
  }
}

.overview-section {
  margin-bottom: 20px;
  
  .stats-card {
    .stats-content {
      display: flex;
      align-items: center;
      gap: 16px;
      
      .stats-icon {
        font-size: 32px;
      }
      
      .stats-info {
        flex: 1;
        
        .stats-number {
          font-size: 24px;
          font-weight: 600;
          color: var(--el-text-color-primary);
          line-height: 1;
        }
        
        .stats-label {
          font-size: 14px;
          color: var(--el-text-color-secondary);
          margin: 4px 0;
        }
        
        .stats-change {
          display: flex;
          align-items: center;
          gap: 4px;
          font-size: 12px;
          font-weight: 500;
          
          &.positive {
            color: var(--el-color-success);
          }
          
          &.negative {
            color: var(--el-color-danger);
          }
        }
      }
    }
  }
}

.charts-section {
  margin-bottom: 20px;
  
  .card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
  }
  
  .chart-container {
    height: 300px;
    width: 100%;
  }
  
  .ranking-list {
    .ranking-item {
      display: flex;
      align-items: center;
      padding: 12px 0;
      border-bottom: 1px solid var(--el-border-color-lighter);
      
      &:last-child {
        border-bottom: none;
      }
      
      .ranking-number {
        width: 32px;
        height: 32px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: 600;
        font-size: 14px;
        margin-right: 12px;
        background: var(--el-bg-color-page);
        color: var(--el-text-color-secondary);
        
        &.first {
          background: #FFD700;
          color: #fff;
        }
        
        &.second {
          background: #C0C0C0;
          color: #fff;
        }
        
        &.third {
          background: #CD7F32;
          color: #fff;
        }
      }
      
      .resource-info {
        flex: 1;
        
        .resource-name {
          font-weight: 500;
          color: var(--el-text-color-primary);
          margin-bottom: 4px;
        }
        
        .resource-meta {
          display: flex;
          align-items: center;
          gap: 8px;
          
          .resource-category {
            font-size: 12px;
            color: var(--el-text-color-secondary);
          }
        }
      }
      
      .resource-stats {
        text-align: right;
        
        .stat-value {
          font-size: 16px;
          font-weight: 600;
          color: var(--el-color-primary);
        }
        
        .stat-label {
          font-size: 12px;
          color: var(--el-text-color-secondary);
        }
      }
    }
  }
}

.table-section {
  .card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    
    .header-actions {
      display: flex;
      gap: 12px;
      align-items: center;
    }
  }
  
  .pagination-wrapper {
    margin-top: 20px;
    text-align: center;
  }
}

// 响应式设计
@media (max-width: 1200px) {
  .time-range-controls {
    .actions {
      margin-left: 0 !important;
    }
  }
  
  .overview-section {
    .el-col {
      margin-bottom: 16px;
    }
  }
  
  .charts-section {
    .el-col {
      margin-bottom: 20px;
    }
  }
}

@media (max-width: 768px) {
  .statistics-container {
    padding: 16px;
  }
  
  .time-range-controls {
    flex-direction: column;
    align-items: stretch !important;
    gap: 16px !important;
    
    .quick-select,
    .custom-range,
    .actions {
      justify-content: center;
    }
  }
  
  .overview-section {
    .el-col {
      span: 12 !important;
    }
  }
  
  .charts-section {
    .el-col {
      span: 24 !important;
    }
  }
  
  .table-section {
    .card-header {
      flex-direction: column;
      gap: 12px;
      align-items: stretch;
      
      .header-actions {
        justify-content: center;
      }
    }
    
    .el-table {
      font-size: 12px;
    }
  }
}
</style>