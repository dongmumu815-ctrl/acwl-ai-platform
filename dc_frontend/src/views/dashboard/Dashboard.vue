<template>
  <div class="dashboard-container">
    <!-- 欢迎区域 -->
    <div class="welcome-section">
      <div class="welcome-content">
        <h1 class="welcome-title">
          <el-icon><Odometer /></el-icon>
          欢迎使用 ACWL AI 数据平台
        </h1>
        <p class="welcome-subtitle">智能数据管理，助力业务决策</p>
      </div>
      <div class="welcome-actions">
        <el-button type="primary" size="large" @click="goToDataCenter">
          <el-icon><DataBoard /></el-icon>
          进入数据中心
        </el-button>
        <el-button size="large" @click="viewQuickStart">
          <el-icon><Guide /></el-icon>
          快速开始
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
              <el-button :type="trendPeriod === '7d' ? 'primary' : ''" @click="trendPeriod = '7d'">7天</el-button>
              <el-button :type="trendPeriod === '30d' ? 'primary' : ''" @click="trendPeriod = '30d'">30天</el-button>
              <el-button :type="trendPeriod === '90d' ? 'primary' : ''" @click="trendPeriod = '90d'">90天</el-button>
            </el-button-group>
          </div>
          <div class="chart-content" ref="trendChartRef"></div>
        </div>

        <!-- 数据分布图 -->
        <div class="chart-card">
          <div class="chart-header">
            <h3>数据类型分布</h3>
            <el-button size="small" @click="refreshDistribution">
              <el-icon><Refresh /></el-icon>
            </el-button>
          </div>
          <div class="chart-content" ref="distributionChartRef"></div>
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
import { ref, onMounted, nextTick } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { useUserStore } from '@/stores/user'

const router = useRouter()
const route = useRoute()
const userStore = useUserStore()

// 图表引用
const trendChartRef = ref<HTMLElement>()
const distributionChartRef = ref<HTMLElement>()

// 响应式数据
const trendPeriod = ref('7d')

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
 * 格式化时间
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
 * 跳转到数据中心
 */
const goToDataCenter = () => {
  console.log('=== 跳转数据中心调试信息 ===');
  console.log('当前路由:', route.path);
  console.log('用户权限:', userStore.userPermissions);
  console.log('准备跳转到数据中心页面');
  console.log('目标路由:', '/data-center');
  console.log('========================');
  router.push('/data-center')
}

/**
 * 查看快速开始
 */
const viewQuickStart = () => {
  console.log('=== 快速开始调试信息 ===');
  console.log('当前路由:', route.path);
  console.log('用户信息:', userStore.userInfo);
  console.log('点击快速开始按钮');
  console.log('========================');
  ElMessage.info('快速开始指南即将推出')
}

/**
 * 处理快捷操作
 */
const handleAction = (action: any) => {
  console.log('=== 快捷操作调试信息 ===');
  console.log('点击的操作:', action);
  console.log('操作key:', action.key);
  console.log('操作标题:', action.title);
  console.log('当前路由:', route.path);
  console.log('用户权限:', userStore.userPermissions);
  console.log('========================');
  
  switch (action.key) {
    case 'upload':
      console.log('准备跳转到数据上传页面');
      ElMessage.info('跳转到数据上传页面')
      break
    case 'query':
      console.log('准备跳转到数据查询页面');
      ElMessage.info('跳转到数据查询页面')
      break
    case 'export':
      console.log('准备跳转到报表导出页面');
      ElMessage.info('跳转到报表导出页面')
      break
    case 'settings':
      console.log('准备跳转到系统设置页面');
      ElMessage.info('跳转到系统设置页面')
      break
    default:
      console.log('执行默认操作:', action.title);
      ElMessage.info(`执行操作: ${action.title}`)
  }
}

/**
 * 刷新分布图
 */
const refreshDistribution = () => {
  ElMessage.success('数据分布图已刷新')
  // 这里应该重新加载图表数据
}

/**
 * 初始化图表
 */
const initCharts = () => {
  // 这里应该使用实际的图表库（如 ECharts）来初始化图表
  // 由于没有引入图表库，这里只是占位
  console.log('初始化图表')
}

/**
 * 组件挂载时初始化
 */
onMounted(() => {
  nextTick(() => {
    initCharts()
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
        display: flex;
        align-items: center;
        justify-content: center;
        color: var(--el-text-color-placeholder);
        background: var(--el-fill-color-lighter);
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