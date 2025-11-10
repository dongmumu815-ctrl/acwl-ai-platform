<template>
  <div>
    <h1 style="margin-bottom: 20px;">仪表板</h1>
    
    <!-- 统计卡片 -->
    <el-row :gutter="20" style="margin-bottom: 20px;">
      <el-col :span="6">
        <div class="stat-card">
          <div class="stat-number">{{ stats.totalCustomers }}</div>
          <div class="stat-label">总平台数</div>
        </div>
      </el-col>
      <el-col :span="6">
        <div class="stat-card">
          <div class="stat-number">{{ stats.totalBatches }}</div>
          <div class="stat-label">总批次数</div>
        </div>
      </el-col>
      <el-col :span="6">
        <div class="stat-card">
          <div class="stat-number">{{ stats.totalUploads }}</div>
          <div class="stat-label">总上传数</div>
        </div>
      </el-col>
      <el-col :span="6">
        <div class="stat-card">
          <div class="stat-number">{{ stats.totalApis }}</div>
          <div class="stat-label">API接口数</div>
        </div>
      </el-col>
    </el-row>
    
    <!-- 图表区域 -->
    <el-row :gutter="20">
      <el-col :span="12">
        <div class="page-card">
          <div class="page-header">
            <h3>批次状态分布</h3>
          </div>
          <div class="page-content">
            <v-chart
              class="chart"
              :option="batchStatusOption"
              style="height: 300px;"
            />
          </div>
        </div>
      </el-col>
      <el-col :span="12">
        <div class="page-card">
          <div class="page-header">
            <h3>最近7天上传趋势</h3>
          </div>
          <div class="page-content">
            <v-chart
              class="chart"
              :option="uploadTrendOption"
              style="height: 300px;"
            />
          </div>
        </div>
      </el-col>
    </el-row>
    
    <!-- 最近活动 -->
    <div class="page-card" style="margin-top: 20px;">
      <div class="page-header">
        <h3>最近活动</h3>
      </div>
      <div class="page-content">
        <el-table :data="recentActivities" style="width: 100%">
          <el-table-column prop="time" label="时间" width="180" />
          <el-table-column prop="type" label="类型" width="120">
            <template #default="{ row }">
              <el-tag :type="getActivityTagType(row.type)">{{ row.type }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="description" label="描述" />
          <el-table-column prop="user" label="操作用户" width="120" />
        </el-table>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { PieChart, LineChart } from 'echarts/charts'
import {
  TitleComponent,
  TooltipComponent,
  LegendComponent,
  GridComponent
} from 'echarts/components'
import VChart from 'vue-echarts'
import api from '@/utils/api'
import dayjs from 'dayjs'

// 注册ECharts组件
use([
  CanvasRenderer,
  PieChart,
  LineChart,
  TitleComponent,
  TooltipComponent,
  LegendComponent,
  GridComponent
])

// 统计数据
const stats = ref({
  totalCustomers: 0,
  totalBatches: 0,
  totalUploads: 0,
  totalApis: 0
})

// 最近活动
const recentActivities = ref([])

// 批次状态分布图表配置
const batchStatusOption = ref({
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
      name: '批次状态',
      type: 'pie',
      radius: '50%',
      data: [
        { value: 0, name: '待处理' },
        { value: 0, name: '处理中' },
        { value: 0, name: '已完成' },
        { value: 0, name: '失败' }
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
})

// 上传趋势图表配置
const uploadTrendOption = ref({
  tooltip: {
    trigger: 'axis'
  },
  xAxis: {
    type: 'category',
    data: []
  },
  yAxis: {
    type: 'value'
  },
  series: [
    {
      name: '上传数量',
      type: 'line',
      data: [],
      smooth: true,
      itemStyle: {
        color: '#1890ff'
      }
    }
  ]
})

// 获取活动标签类型
const getActivityTagType = (type) => {
  const typeMap = {
    '数据上传': 'success',
    '批次创建': 'primary',
    '客户注册': 'info',
    '系统配置': 'warning'
  }
  return typeMap[type] || 'default'
}

// 加载统计数据
const loadStats = async () => {
  try {
    const response = await api.get('/admin/stats')
    stats.value.totalCustomers = response.data.data.total_customers
    // stats.value.totalBatches = response.data.data.totalBatches
    stats.value.totalUploads = response.data.data.total_api_calls
    stats.value.totalApis = response.data.data.total_apis
    console.log(response.data.data)
    console.log("*"*50)
    console.log(stats)
    
    // 更新批次状态图表数据
    if (response.data.batchStats) {
      batchStatusOption.value.series[0].data = [
        { value: response.data.batchStats.pending || 0, name: '待处理' },
        { value: response.data.batchStats.processing || 0, name: '处理中' },
        { value: response.data.batchStats.completed || 0, name: '已完成' },
        { value: response.data.batchStats.failed || 0, name: '失败' }
      ]
    }
    
    // 更新上传趋势图表数据
    if (response.data.uploadTrend) {
      const dates = []
      const counts = []
      
      for (let i = 6; i >= 0; i--) {
        const date = dayjs().subtract(i, 'day').format('MM-DD')
        dates.push(date)
        counts.push(response.data.uploadTrend[date] || 0)
      }
      
      uploadTrendOption.value.xAxis.data = dates
      uploadTrendOption.value.series[0].data = counts
    }
  } catch (error) {
    console.error('加载统计数据失败:', error)
  }
}

// 加载最近活动
const loadRecentActivities = async () => {
  try {
    // 模拟数据，实际应该从API获取
    recentActivities.value = [
      {
        time: dayjs().subtract(1, 'hour').format('YYYY-MM-DD HH:mm:ss'),
        type: '数据上传',
        description: '客户 test_user 上传了新的数据文件',
        user: 'test_user'
      },
      {
        time: dayjs().subtract(2, 'hour').format('YYYY-MM-DD HH:mm:ss'),
        type: '批次创建',
        description: '创建了新的数据处理批次',
        user: 'admin'
      },
      {
        time: dayjs().subtract(3, 'hour').format('YYYY-MM-DD HH:mm:ss'),
        type: '客户注册',
        description: '新客户 new_customer 注册成功',
        user: 'system'
      },
      {
        time: dayjs().subtract(1, 'day').format('YYYY-MM-DD HH:mm:ss'),
        type: '系统配置',
        description: '更新了系统配置参数',
        user: 'admin'
      }
    ]
  } catch (error) {
    console.error('加载最近活动失败:', error)
  }
}

// 组件挂载时加载数据
onMounted(() => {
  loadStats()
  loadRecentActivities()
})
</script>

<style scoped>
.stat-card {
  background: #fff;
  border-radius: 8px;
  padding: 20px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  text-align: center;
  transition: transform 0.3s ease;
}

.stat-card:hover {
  transform: translateY(-2px);
}

.stat-number {
  font-size: 32px;
  font-weight: bold;
  color: #1890ff;
  margin-bottom: 8px;
}

.stat-label {
  color: #666;
  font-size: 14px;
}

.page-card {
  background: #fff;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.page-header {
  padding: 20px;
  border-bottom: 1px solid #f0f0f0;
}

.page-header h3 {
  margin: 0;
  color: #333;
}

.page-content {
  padding: 20px;
}

.chart {
  width: 100%;
}
</style>