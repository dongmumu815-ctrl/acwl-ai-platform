<template>
  <div class="dashboard">
    <!-- 欢迎区域 -->
    <div class="welcome-section">
      <el-card class="welcome-card" shadow="never">
        <div class="welcome-content">
          <div class="welcome-text">
            <h1 class="welcome-title">
              欢迎回来，{{ userStore.displayName }}！
            </h1>
            <p class="welcome-subtitle">
              今天是 {{ currentDate }}，祝您工作愉快
            </p>
          </div>
          <div class="welcome-actions">
            <el-button type="primary" @click="$router.push('/models')">
              <el-icon><Plus /></el-icon>
              创建模型
            </el-button>
            <el-button @click="$router.push('/deployments')">
              <el-icon><VideoPlay /></el-icon>
              部署管理
            </el-button>
          </div>
        </div>
      </el-card>
    </div>
    
    <!-- 统计卡片 -->
    <div class="stats-section">
      <el-row :gutter="20">
        <el-col :xs="12" :sm="6" :md="6" :lg="6">
          <el-card class="stats-card" shadow="hover">
            <div class="stats-content">
              <div class="stats-icon models">
                <el-icon><Box /></el-icon>
              </div>
              <div class="stats-info">
                <div class="stats-number">{{ stats.totalModels }}</div>
                <div class="stats-label">总模型数</div>
              </div>
            </div>
          </el-card>
        </el-col>
        
        <el-col :xs="12" :sm="6" :md="6" :lg="6">
          <el-card class="stats-card" shadow="hover">
            <div class="stats-content">
              <div class="stats-icon deployments">
                <el-icon><VideoPlay /></el-icon>
              </div>
              <div class="stats-info">
                <div class="stats-number">{{ stats.activeDeployments }}</div>
                <div class="stats-label">活跃部署</div>
              </div>
            </div>
          </el-card>
        </el-col>
        
        <el-col :xs="12" :sm="6" :md="6" :lg="6">
          <el-card class="stats-card" shadow="hover">
            <div class="stats-content">
              <div class="stats-icon datasets">
                <el-icon><FolderOpened /></el-icon>
              </div>
              <div class="stats-info">
                <div class="stats-number">{{ stats.totalDatasets }}</div>
                <div class="stats-label">数据集</div>
              </div>
            </div>
          </el-card>
        </el-col>
        
        <el-col :xs="12" :sm="6" :md="6" :lg="6">
          <el-card class="stats-card" shadow="hover">
            <div class="stats-content">
              <div class="stats-icon gpu">
                <el-icon><Monitor /></el-icon>
              </div>
              <div class="stats-info">
                <div class="stats-number">{{ stats.availableGpus }}</div>
                <div class="stats-label">可用GPU</div>
              </div>
            </div>
          </el-card>
        </el-col>
      </el-row>
    </div>
    
    <!-- 主要内容区域 -->
    <el-row :gutter="20" class="main-content">
      <!-- 左侧内容 -->
      <el-col :xs="24" :sm="24" :md="16" :lg="16">
        <!-- 最近活动 -->
        <el-card class="activity-card" shadow="never">
          <template #header>
            <div class="card-header">
              <span class="card-title">最近活动</span>
              <el-link type="primary" @click="$router.push('/logs')">
                查看全部
              </el-link>
            </div>
          </template>
          
          <div class="activity-list">
            <div
              v-for="activity in recentActivities"
              :key="activity.id"
              class="activity-item"
            >
              <div class="activity-icon" :class="activity.type">
                <el-icon>
                  <component :is="getActivityIcon(activity.type)" />
                </el-icon>
              </div>
              <div class="activity-content">
                <div class="activity-title">{{ activity.title }}</div>
                <div class="activity-description">{{ activity.description }}</div>
                <div class="activity-time">{{ formatTime(activity.createdAt) }}</div>
              </div>
            </div>
            
            <div v-if="recentActivities.length === 0" class="empty-state">
              <el-empty description="暂无活动记录" />
            </div>
          </div>
        </el-card>
        
        <!-- 资源使用情况 -->
        <el-card class="resource-card" shadow="never">
          <template #header>
            <div class="card-header">
              <span class="card-title">资源使用情况</span>
              <el-button text @click="refreshResourceStats">
                <el-icon><Refresh /></el-icon>
                刷新
              </el-button>
            </div>
          </template>
          
          <div class="resource-stats">
            <div class="resource-item">
              <div class="resource-label">CPU 使用率</div>
              <el-progress
                :percentage="resourceStats.cpuUsage"
                :color="getProgressColor(resourceStats.cpuUsage)"
                :show-text="true"
              />
            </div>
            
            <div class="resource-item">
              <div class="resource-label">内存使用率</div>
              <el-progress
                :percentage="resourceStats.memoryUsage"
                :color="getProgressColor(resourceStats.memoryUsage)"
                :show-text="true"
              />
            </div>
            
            <div class="resource-item">
              <div class="resource-label">GPU 使用率</div>
              <el-progress
                :percentage="resourceStats.gpuUsage"
                :color="getProgressColor(resourceStats.gpuUsage)"
                :show-text="true"
              />
            </div>
            
            <div class="resource-item">
              <div class="resource-label">存储使用率</div>
              <el-progress
                :percentage="resourceStats.storageUsage"
                :color="getProgressColor(resourceStats.storageUsage)"
                :show-text="true"
              />
            </div>
          </div>
        </el-card>
      </el-col>
      
      <!-- 右侧内容 -->
      <el-col :xs="24" :sm="24" :md="8" :lg="8">
        <!-- 快速操作 -->
        <el-card class="quick-actions-card" shadow="never">
          <template #header>
            <span class="card-title">快速操作</span>
          </template>
          
          <div class="quick-actions">
            <div class="action-item" @click="$router.push('/models/create')">
              <div class="action-icon">
                <el-icon><Plus /></el-icon>
              </div>
              <div class="action-text">
                <div class="action-title">创建模型</div>
                <div class="action-description">上传或创建新的AI模型</div>
              </div>
            </div>
            
            <div class="action-item" @click="$router.push('/deployments/create')">
              <div class="action-icon">
                <el-icon><VideoPlay /></el-icon>
              </div>
              <div class="action-text">
                <div class="action-title">部署服务</div>
                <div class="action-description">将模型部署为API服务</div>
              </div>
            </div>
            
            <div class="action-item" @click="$router.push('/datasets/upload')">
              <div class="action-icon">
                <el-icon><Upload /></el-icon>
              </div>
              <div class="action-text">
                <div class="action-title">上传数据集</div>
                <div class="action-description">上传训练或测试数据</div>
              </div>
            </div>
            
            <div class="action-item" @click="$router.push('/fine-tuning/create')">
              <div class="action-icon">
                <el-icon><Setting /></el-icon>
              </div>
              <div class="action-text">
                <div class="action-title">模型微调</div>
                <div class="action-description">对现有模型进行微调</div>
              </div>
            </div>
          </div>
        </el-card>
        
        <!-- 系统状态 -->
        <el-card class="system-status-card" shadow="never">
          <template #header>
            <span class="card-title">系统状态</span>
          </template>
          
          <div class="system-status">
            <div class="status-item">
              <div class="status-label">API 服务</div>
              <el-tag :type="systemStatus.apiStatus === 'healthy' ? 'success' : 'danger'" size="small">
                {{ systemStatus.apiStatus === 'healthy' ? '正常' : '异常' }}
              </el-tag>
            </div>
            
            <div class="status-item">
              <div class="status-label">数据库</div>
              <el-tag :type="systemStatus.dbStatus === 'healthy' ? 'success' : 'danger'" size="small">
                {{ systemStatus.dbStatus === 'healthy' ? '正常' : '异常' }}
              </el-tag>
            </div>
            
            <div class="status-item">
              <div class="status-label">GPU 集群</div>
              <el-tag :type="systemStatus.gpuStatus === 'healthy' ? 'success' : 'warning'" size="small">
                {{ systemStatus.gpuStatus === 'healthy' ? '正常' : '部分异常' }}
              </el-tag>
            </div>
            
            <div class="status-item">
              <div class="status-label">存储服务</div>
              <el-tag :type="systemStatus.storageStatus === 'healthy' ? 'success' : 'danger'" size="small">
                {{ systemStatus.storageStatus === 'healthy' ? '正常' : '异常' }}
              </el-tag>
            </div>
          </div>
        </el-card>
        
        <!-- 最新公告 -->
        <el-card class="announcement-card" shadow="never">
          <template #header>
            <span class="card-title">最新公告</span>
          </template>
          
          <div class="announcements">
            <div
              v-for="announcement in announcements"
              :key="announcement.id"
              class="announcement-item"
            >
              <div class="announcement-title">{{ announcement.title }}</div>
              <div class="announcement-content">{{ announcement.content }}</div>
              <div class="announcement-time">{{ formatTime(announcement.createdAt) }}</div>
            </div>
            
            <div v-if="announcements.length === 0" class="empty-state">
              <el-empty description="暂无公告" :image-size="60" />
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import {
  Plus,
  VideoPlay,
  Box,
  FolderOpened,
  Monitor,
  Refresh,
  Upload,
  Setting,
  User,
  Document,
  Warning
} from '@element-plus/icons-vue'
import { useUserStore } from '@/stores/user'
import { useAppStore } from '@/stores/app'

const userStore = useUserStore()
const appStore = useAppStore()

// 当前日期
const currentDate = computed(() => {
  return new Date().toLocaleDateString('zh-CN', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
    weekday: 'long'
  })
})

// 统计数据
const stats = reactive({
  totalModels: 0,
  activeDeployments: 0,
  totalDatasets: 0,
  availableGpus: 0
})

// 最近活动
const recentActivities = ref([
  {
    id: 1,
    type: 'model',
    title: '模型创建成功',
    description: 'GPT-3.5-turbo 模型已成功创建',
    createdAt: new Date(Date.now() - 1000 * 60 * 30) // 30分钟前
  },
  {
    id: 2,
    type: 'deployment',
    title: '服务部署完成',
    description: 'ChatBot API 服务已成功部署',
    createdAt: new Date(Date.now() - 1000 * 60 * 60 * 2) // 2小时前
  },
  {
    id: 3,
    type: 'dataset',
    title: '数据集上传完成',
    description: '训练数据集 training_data_v2.json 上传成功',
    createdAt: new Date(Date.now() - 1000 * 60 * 60 * 4) // 4小时前
  }
])

// 资源使用情况
const resourceStats = reactive({
  cpuUsage: 45,
  memoryUsage: 68,
  gpuUsage: 32,
  storageUsage: 78
})

// 系统状态
const systemStatus = reactive({
  apiStatus: 'healthy',
  dbStatus: 'healthy',
  gpuStatus: 'healthy',
  storageStatus: 'healthy'
})

// 公告
const announcements = ref([
  {
    id: 1,
    title: '系统维护通知',
    content: '系统将于本周六凌晨2:00-4:00进行维护升级',
    createdAt: new Date(Date.now() - 1000 * 60 * 60 * 24) // 1天前
  },
  {
    id: 2,
    title: '新功能发布',
    content: '模型微调功能已上线，支持更多自定义参数',
    createdAt: new Date(Date.now() - 1000 * 60 * 60 * 24 * 3) // 3天前
  }
])

// 获取活动图标
const getActivityIcon = (type: string) => {
  const iconMap: Record<string, any> = {
    model: Box,
    deployment: VideoPlay,
    dataset: FolderOpened,
    user: User,
    system: Setting,
    warning: Warning
  }
  return iconMap[type] || Document
}

// 获取进度条颜色
const getProgressColor = (percentage: number) => {
  if (percentage < 50) return '#67c23a'
  if (percentage < 80) return '#e6a23c'
  return '#f56c6c'
}

// 格式化时间
const formatTime = (date: Date) => {
  const now = new Date()
  const diff = now.getTime() - date.getTime()
  const minutes = Math.floor(diff / (1000 * 60))
  const hours = Math.floor(diff / (1000 * 60 * 60))
  const days = Math.floor(diff / (1000 * 60 * 60 * 24))
  
  if (minutes < 60) {
    return `${minutes}分钟前`
  } else if (hours < 24) {
    return `${hours}小时前`
  } else {
    return `${days}天前`
  }
}

// 刷新资源统计
const refreshResourceStats = () => {
  // 模拟刷新数据
  resourceStats.cpuUsage = Math.floor(Math.random() * 100)
  resourceStats.memoryUsage = Math.floor(Math.random() * 100)
  resourceStats.gpuUsage = Math.floor(Math.random() * 100)
  resourceStats.storageUsage = Math.floor(Math.random() * 100)
  
  ElMessage.success('资源统计已刷新')
}

// 加载统计数据
const loadStats = async () => {
  try {
    // 这里应该调用实际的API
    // const response = await dashboardApi.getStats()
    // Object.assign(stats, response.data)
    
    // 模拟数据
    stats.totalModels = 12
    stats.activeDeployments = 5
    stats.totalDatasets = 8
    stats.availableGpus = 4
  } catch (error) {
    console.error('加载统计数据失败:', error)
  }
}

onMounted(() => {
  loadStats()
  appStore.setPageTitle('仪表板')
})
</script>

<style lang="scss" scoped>
.dashboard {
  padding: 20px;
  
  .welcome-section {
    margin-bottom: 20px;
    
    .welcome-card {
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      border: none;
      
      :deep(.el-card__body) {
        padding: 30px;
      }
      
      .welcome-content {
        display: flex;
        justify-content: space-between;
        align-items: center;
        color: white;
        
        .welcome-text {
          .welcome-title {
            font-size: 28px;
            font-weight: 600;
            margin: 0 0 8px 0;
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
          
          .el-button {
            border-color: rgba(255, 255, 255, 0.3);
            
            &.el-button--primary {
              background: rgba(255, 255, 255, 0.2);
              border-color: rgba(255, 255, 255, 0.3);
              
              &:hover {
                background: rgba(255, 255, 255, 0.3);
              }
            }
            
            &:not(.el-button--primary) {
              background: transparent;
              color: white;
              
              &:hover {
                background: rgba(255, 255, 255, 0.1);
              }
            }
          }
        }
      }
    }
  }
  
  .stats-section {
    margin-bottom: 20px;
    
    .stats-card {
      .stats-content {
        display: flex;
        align-items: center;
        gap: 16px;
        
        .stats-icon {
          width: 60px;
          height: 60px;
          border-radius: 12px;
          display: flex;
          align-items: center;
          justify-content: center;
          font-size: 24px;
          color: white;
          
          &.models {
            background: linear-gradient(135deg, #667eea, #764ba2);
          }
          
          &.deployments {
            background: linear-gradient(135deg, #f093fb, #f5576c);
          }
          
          &.datasets {
            background: linear-gradient(135deg, #4facfe, #00f2fe);
          }
          
          &.gpu {
            background: linear-gradient(135deg, #43e97b, #38f9d7);
          }
        }
        
        .stats-info {
          .stats-number {
            font-size: 32px;
            font-weight: 600;
            color: var(--el-text-color-primary);
            line-height: 1;
          }
          
          .stats-label {
            font-size: 14px;
            color: var(--el-text-color-regular);
            margin-top: 4px;
          }
        }
      }
    }
  }
  
  .main-content {
    .card-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      
      .card-title {
        font-size: 16px;
        font-weight: 600;
        color: var(--el-text-color-primary);
      }
    }
    
    .activity-card,
    .resource-card {
      margin-bottom: 20px;
      
      .activity-list {
        .activity-item {
          display: flex;
          gap: 12px;
          padding: 16px 0;
          border-bottom: 1px solid var(--el-border-color-lighter);
          
          &:last-child {
            border-bottom: none;
          }
          
          .activity-icon {
            width: 40px;
            height: 40px;
            border-radius: 8px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 18px;
            color: white;
            
            &.model {
              background: #667eea;
            }
            
            &.deployment {
              background: #f093fb;
            }
            
            &.dataset {
              background: #4facfe;
            }
          }
          
          .activity-content {
            flex: 1;
            
            .activity-title {
              font-size: 14px;
              font-weight: 500;
              color: var(--el-text-color-primary);
              margin-bottom: 4px;
            }
            
            .activity-description {
              font-size: 13px;
              color: var(--el-text-color-regular);
              margin-bottom: 4px;
            }
            
            .activity-time {
              font-size: 12px;
              color: var(--el-text-color-placeholder);
            }
          }
        }
      }
      
      .resource-stats {
        .resource-item {
          margin-bottom: 20px;
          
          &:last-child {
            margin-bottom: 0;
          }
          
          .resource-label {
            font-size: 14px;
            color: var(--el-text-color-regular);
            margin-bottom: 8px;
          }
        }
      }
    }
    
    .quick-actions-card,
    .system-status-card,
    .announcement-card {
      margin-bottom: 20px;
      
      .quick-actions {
        .action-item {
          display: flex;
          align-items: center;
          gap: 12px;
          padding: 16px;
          border-radius: 8px;
          cursor: pointer;
          transition: all 0.3s ease;
          margin-bottom: 8px;
          
          &:last-child {
            margin-bottom: 0;
          }
          
          &:hover {
            background: var(--el-color-primary-light-9);
          }
          
          .action-icon {
            width: 40px;
            height: 40px;
            border-radius: 8px;
            background: var(--el-color-primary-light-8);
            display: flex;
            align-items: center;
            justify-content: center;
            color: var(--el-color-primary);
            font-size: 18px;
          }
          
          .action-text {
            .action-title {
              font-size: 14px;
              font-weight: 500;
              color: var(--el-text-color-primary);
              margin-bottom: 2px;
            }
            
            .action-description {
              font-size: 12px;
              color: var(--el-text-color-regular);
            }
          }
        }
      }
      
      .system-status {
        .status-item {
          display: flex;
          justify-content: space-between;
          align-items: center;
          padding: 12px 0;
          border-bottom: 1px solid var(--el-border-color-lighter);
          
          &:last-child {
            border-bottom: none;
          }
          
          .status-label {
            font-size: 14px;
            color: var(--el-text-color-regular);
          }
        }
      }
      
      .announcements {
        .announcement-item {
          padding: 16px 0;
          border-bottom: 1px solid var(--el-border-color-lighter);
          
          &:last-child {
            border-bottom: none;
          }
          
          .announcement-title {
            font-size: 14px;
            font-weight: 500;
            color: var(--el-text-color-primary);
            margin-bottom: 4px;
          }
          
          .announcement-content {
            font-size: 13px;
            color: var(--el-text-color-regular);
            margin-bottom: 4px;
            line-height: 1.4;
          }
          
          .announcement-time {
            font-size: 12px;
            color: var(--el-text-color-placeholder);
          }
        }
      }
    }
  }
  
  .empty-state {
    text-align: center;
    padding: 40px 0;
  }
}

// 响应式设计
@media (max-width: 768px) {
  .dashboard {
    padding: 12px;
    
    .welcome-section {
      .welcome-card {
        :deep(.el-card__body) {
          padding: 20px;
        }
        
        .welcome-content {
          flex-direction: column;
          gap: 20px;
          text-align: center;
          
          .welcome-actions {
            justify-content: center;
          }
        }
      }
    }
    
    .main-content {
      .activity-card,
      .resource-card,
      .quick-actions-card,
      .system-status-card,
      .announcement-card {
        margin-bottom: 16px;
      }
    }
  }
}

// 暗色主题
.dark {
  .dashboard {
    .welcome-section {
      .welcome-card {
        background: linear-gradient(135deg, #2c3e50 0%, #34495e 100%);
      }
    }
  }
}
</style>