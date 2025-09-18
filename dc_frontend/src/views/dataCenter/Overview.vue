<template>
  <div class="data-center-overview">
    <!-- 页面标题 -->
    <div class="page-header">
      <h1 class="page-title">
        <el-icon class="title-icon"><DataBoard /></el-icon>
        数据中心概览
      </h1>
      <p class="page-description">实时监控数据资源状态，掌握系统运行情况</p>
    </div>

    <!-- 统计卡片 -->
    <el-row :gutter="20" class="stats-cards">
      <el-col :xs="24" :sm="12" :md="6">
        <el-card class="stat-card">
          <div class="stat-content">
            <div class="stat-icon primary">
              <el-icon><FolderOpened /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ stats.totalResources }}</div>
              <div class="stat-label">数据资源总数</div>
            </div>
          </div>
        </el-card>
      </el-col>
      
      <el-col :xs="24" :sm="12" :md="6">
        <el-card class="stat-card">
          <div class="stat-content">
            <div class="stat-icon success">
              <el-icon><User /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ stats.totalUsers }}</div>
              <div class="stat-label">注册用户数</div>
            </div>
          </div>
        </el-card>
      </el-col>
      
      <el-col :xs="24" :sm="12" :md="6">
        <el-card class="stat-card">
          <div class="stat-content">
            <div class="stat-icon warning">
              <el-icon><View /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ stats.todayViews }}</div>
              <div class="stat-label">今日访问量</div>
            </div>
          </div>
        </el-card>
      </el-col>
      
      <el-col :xs="24" :sm="12" :md="6">
        <el-card class="stat-card">
          <div class="stat-content">
            <div class="stat-icon info">
              <el-icon><Download /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ stats.todayDownloads }}</div>
              <div class="stat-label">今日下载量</div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 图表区域 -->
    <el-row :gutter="20" class="charts-section">
      <el-col :xs="24" :lg="12">
        <el-card class="chart-card">
          <template #header>
            <div class="card-header">
              <span>访问趋势</span>
              <el-button type="text" @click="refreshChart">刷新</el-button>
            </div>
          </template>
          <div class="chart-container">
            <div class="chart-placeholder">
              <el-icon class="chart-icon"><TrendCharts /></el-icon>
              <p>访问趋势图表</p>
            </div>
          </div>
        </el-card>
      </el-col>
      
      <el-col :xs="24" :lg="12">
        <el-card class="chart-card">
          <template #header>
            <div class="card-header">
              <span>资源分布</span>
              <el-button type="text" @click="refreshChart">刷新</el-button>
            </div>
          </template>
          <div class="chart-container">
            <div class="chart-placeholder">
              <el-icon class="chart-icon"><PieChart /></el-icon>
              <p>资源分布图表</p>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 快速操作 -->
    <el-card class="quick-actions">
      <template #header>
        <span>快速操作</span>
      </template>
      <div class="actions-grid">
        <el-button type="primary" @click="$router.push('/data-center/resources')">
          <el-icon><Plus /></el-icon>
          新建资源
        </el-button>
        <el-button @click="$router.push('/data-center/users')">
          <el-icon><UserFilled /></el-icon>
          用户管理
        </el-button>
        <el-button @click="$router.push('/data-center/statistics')">
          <el-icon><DataAnalysis /></el-icon>
          查看统计
        </el-button>
        <el-button @click="$router.push('/data-center/system/settings')">
          <el-icon><Setting /></el-icon>
          系统设置
        </el-button>
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'

// 统计数据
const stats = ref({
  totalResources: 0,
  totalUsers: 0,
  todayViews: 0,
  todayDownloads: 0
})

/**
 * 加载统计数据
 */
const loadStats = async () => {
  try {
    // 模拟数据加载
    await new Promise(resolve => setTimeout(resolve, 500))
    
    stats.value = {
      totalResources: 1248,
      totalUsers: 356,
      todayViews: 2847,
      todayDownloads: 156
    }
  } catch (error) {
    console.error('加载统计数据失败:', error)
    ElMessage.error('加载统计数据失败')
  }
}

/**
 * 刷新图表
 */
const refreshChart = () => {
  ElMessage.success('图表已刷新')
}

// 组件挂载时加载数据
onMounted(() => {
  loadStats()
})
</script>

<style lang="scss" scoped>
.data-center-overview {
  .page-header {
    margin-bottom: 24px;
    
    .page-title {
      display: flex;
      align-items: center;
      font-size: 24px;
      font-weight: 600;
      color: var(--el-text-color-primary);
      margin: 0 0 8px 0;
      
      .title-icon {
        margin-right: 8px;
        color: var(--el-color-primary);
      }
    }
    
    .page-description {
      color: var(--el-text-color-regular);
      margin: 0;
    }
  }
  
  .stats-cards {
    margin-bottom: 24px;
    
    .stat-card {
      .stat-content {
        display: flex;
        align-items: center;
        
        .stat-icon {
          width: 48px;
          height: 48px;
          border-radius: 8px;
          display: flex;
          align-items: center;
          justify-content: center;
          margin-right: 16px;
          
          .el-icon {
            font-size: 24px;
            color: white;
          }
          
          &.primary {
            background: var(--el-color-primary);
          }
          
          &.success {
            background: var(--el-color-success);
          }
          
          &.warning {
            background: var(--el-color-warning);
          }
          
          &.info {
            background: var(--el-color-info);
          }
        }
        
        .stat-info {
          .stat-value {
            font-size: 28px;
            font-weight: 600;
            color: var(--el-text-color-primary);
            line-height: 1;
          }
          
          .stat-label {
            font-size: 14px;
            color: var(--el-text-color-regular);
            margin-top: 4px;
          }
        }
      }
    }
  }
  
  .charts-section {
    margin-bottom: 24px;
    
    .chart-card {
      .card-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
      }
      
      .chart-container {
        height: 300px;
        
        .chart-placeholder {
          height: 100%;
          display: flex;
          flex-direction: column;
          align-items: center;
          justify-content: center;
          color: var(--el-text-color-placeholder);
          
          .chart-icon {
            font-size: 48px;
            margin-bottom: 16px;
          }
        }
      }
    }
  }
  
  .quick-actions {
    .actions-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
      gap: 16px;
      
      .el-button {
        height: 48px;
        
        .el-icon {
          margin-right: 8px;
        }
      }
    }
  }
}

// 响应式设计
@media (max-width: 768px) {
  .data-center-overview {
    .stats-cards {
      .el-col {
        margin-bottom: 16px;
      }
    }
    
    .charts-section {
      .el-col {
        margin-bottom: 16px;
      }
    }
    
    .quick-actions {
      .actions-grid {
        grid-template-columns: 1fr;
      }
    }
  }
}
</style>