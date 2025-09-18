<template>
  <div class="usage-statistics">
    <div class="page-header">
      <h1 class="page-title">
        <el-icon><DataAnalysis /></el-icon>
        使用统计
      </h1>
      <p class="page-description">数据资源使用情况统计分析</p>
    </div>

    <!-- 统计概览 -->
    <div class="overview-section">
      <el-row :gutter="20">
        <el-col :xs="24" :sm="12" :lg="6">
          <div class="overview-card">
            <div class="card-icon active-users">
              <el-icon><User /></el-icon>
            </div>
            <div class="card-content">
              <div class="card-value">{{ activeUsers }}</div>
              <div class="card-label">活跃用户</div>
              <div class="card-trend positive">
                <el-icon><ArrowUp /></el-icon>
                +12.5%
              </div>
            </div>
          </div>
        </el-col>
        
        <el-col :xs="24" :sm="12" :lg="6">
          <div class="overview-card">
            <div class="card-icon data-queries">
              <el-icon><Search /></el-icon>
            </div>
            <div class="card-content">
              <div class="card-value">{{ dataQueries }}</div>
              <div class="card-label">数据查询</div>
              <div class="card-trend positive">
                <el-icon><ArrowUp /></el-icon>
                +8.3%
              </div>
            </div>
          </div>
        </el-col>
        
        <el-col :xs="24" :sm="12" :lg="6">
          <div class="overview-card">
            <div class="card-icon downloads">
              <el-icon><Download /></el-icon>
            </div>
            <div class="card-content">
              <div class="card-value">{{ downloads }}</div>
              <div class="card-label">下载次数</div>
              <div class="card-trend negative">
                <el-icon><ArrowDown /></el-icon>
                -3.2%
              </div>
            </div>
          </div>
        </el-col>
        
        <el-col :xs="24" :sm="12" :lg="6">
          <div class="overview-card">
            <div class="card-icon storage">
              <el-icon><FolderOpened /></el-icon>
            </div>
            <div class="card-content">
              <div class="card-value">{{ storageUsed }}</div>
              <div class="card-label">存储使用</div>
              <div class="card-trend positive">
                <el-icon><ArrowUp /></el-icon>
                +5.7%
              </div>
            </div>
          </div>
        </el-col>
      </el-row>
    </div>

    <!-- 使用趋势图表 -->
    <div class="charts-section">
      <el-row :gutter="20">
        <el-col :xs="24" :lg="16">
          <el-card class="chart-card">
            <template #header>
              <div class="card-header">
                <span>使用趋势</span>
                <div class="header-controls">
                  <el-radio-group v-model="trendPeriod" size="small">
                    <el-radio-button label="7d">7天</el-radio-button>
                    <el-radio-button label="30d">30天</el-radio-button>
                    <el-radio-button label="90d">90天</el-radio-button>
                  </el-radio-group>
                  <el-button type="primary" size="small" @click="refreshTrend">
                    <el-icon><Refresh /></el-icon>
                  </el-button>
                </div>
              </div>
            </template>
            <div class="chart-container">
              <div class="chart-placeholder">
                <el-icon><TrendCharts /></el-icon>
                <p>使用趋势图表</p>
                <p class="chart-desc">显示用户活跃度、查询次数等趋势变化</p>
              </div>
            </div>
          </el-card>
        </el-col>
        
        <el-col :xs="24" :lg="8">
          <el-card class="chart-card">
            <template #header>
              <div class="card-header">
                <span>资源类型分布</span>
                <el-button type="primary" size="small" @click="refreshDistribution">
                  <el-icon><Refresh /></el-icon>
                </el-button>
              </div>
            </template>
            <div class="chart-container">
              <div class="chart-placeholder">
                <el-icon><PieChart /></el-icon>
                <p>资源类型分布</p>
                <p class="chart-desc">不同类型数据资源的使用分布</p>
              </div>
            </div>
          </el-card>
        </el-col>
      </el-row>
    </div>

    <!-- 热门资源排行 -->
    <div class="ranking-section">
      <el-row :gutter="20">
        <el-col :xs="24" :lg="12">
          <el-card class="ranking-card">
            <template #header>
              <div class="card-header">
                <span>热门资源排行</span>
                <el-button type="primary" size="small" @click="refreshRanking">
                  <el-icon><Refresh /></el-icon>
                </el-button>
              </div>
            </template>
            <div class="ranking-list">
              <div
                v-for="(item, index) in hotResources"
                :key="item.id"
                class="ranking-item"
              >
                <div class="ranking-number" :class="`rank-${index + 1}`">
                  {{ index + 1 }}
                </div>
                <div class="ranking-content">
                  <div class="resource-name">{{ item.name }}</div>
                  <div class="resource-stats">
                    <span class="stat-item">
                      <el-icon><View /></el-icon>
                      {{ item.views }}
                    </span>
                    <span class="stat-item">
                      <el-icon><Download /></el-icon>
                      {{ item.downloads }}
                    </span>
                  </div>
                </div>
                <div class="ranking-trend">
                  <el-icon v-if="item.trend > 0" class="trend-up"><ArrowUp /></el-icon>
                  <el-icon v-else class="trend-down"><ArrowDown /></el-icon>
                  {{ Math.abs(item.trend) }}%
                </div>
              </div>
            </div>
          </el-card>
        </el-col>
        
        <el-col :xs="24" :lg="12">
          <el-card class="ranking-card">
            <template #header>
              <div class="card-header">
                <span>活跃用户排行</span>
                <el-button type="primary" size="small" @click="refreshUserRanking">
                  <el-icon><Refresh /></el-icon>
                </el-button>
              </div>
            </template>
            <div class="ranking-list">
              <div
                v-for="(user, index) in activeUsersList"
                :key="user.id"
                class="ranking-item"
              >
                <div class="ranking-number" :class="`rank-${index + 1}`">
                  {{ index + 1 }}
                </div>
                <div class="ranking-content">
                  <div class="user-info">
                    <el-avatar :size="32" :src="user.avatar" />
                    <div class="user-details">
                      <div class="user-name">{{ user.name }}</div>
                      <div class="user-department">{{ user.department }}</div>
                    </div>
                  </div>
                </div>
                <div class="ranking-score">
                  <div class="score-value">{{ user.score }}</div>
                  <div class="score-label">活跃度</div>
                </div>
              </div>
            </div>
          </el-card>
        </el-col>
      </el-row>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'

// 统计数据
const activeUsers = ref(1567)
const dataQueries = ref(8934)
const downloads = ref(2341)
const storageUsed = ref('2.3TB')

// 趋势周期
const trendPeriod = ref('30d')

// 热门资源数据
const hotResources = ref([
  {
    id: 1,
    name: '用户行为分析数据集',
    views: 2341,
    downloads: 567,
    trend: 12.5
  },
  {
    id: 2,
    name: '销售业绩统计报表',
    views: 1987,
    downloads: 432,
    trend: 8.3
  },
  {
    id: 3,
    name: '市场调研数据',
    views: 1654,
    downloads: 298,
    trend: -3.2
  },
  {
    id: 4,
    name: '产品使用情况分析',
    views: 1432,
    downloads: 234,
    trend: 15.7
  },
  {
    id: 5,
    name: '客户满意度调查',
    views: 1298,
    downloads: 189,
    trend: 5.4
  }
])

// 活跃用户数据
const activeUsersList = ref([
  {
    id: 1,
    name: '张三',
    department: '数据分析部',
    avatar: '/avatar1.png',
    score: 95
  },
  {
    id: 2,
    name: '李四',
    department: '市场部',
    avatar: '/avatar2.png',
    score: 87
  },
  {
    id: 3,
    name: '王五',
    department: '产品部',
    avatar: '/avatar3.png',
    score: 82
  },
  {
    id: 4,
    name: '赵六',
    department: '运营部',
    avatar: '/avatar4.png',
    score: 78
  },
  {
    id: 5,
    name: '钱七',
    department: '技术部',
    avatar: '/avatar5.png',
    score: 75
  }
])

/**
 * 刷新趋势图表
 */
const refreshTrend = () => {
  ElMessage.success('趋势图表已刷新')
}

/**
 * 刷新分布图表
 */
const refreshDistribution = () => {
  ElMessage.success('分布图表已刷新')
}

/**
 * 刷新资源排行
 */
const refreshRanking = () => {
  ElMessage.success('资源排行已刷新')
}

/**
 * 刷新用户排行
 */
const refreshUserRanking = () => {
  ElMessage.success('用户排行已刷新')
}

/**
 * 组件挂载时加载数据
 */
onMounted(() => {
  // 加载统计数据
})
</script>

<style lang="scss" scoped>
.usage-statistics {
  padding: 20px;
  
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
      color: var(--el-text-color-regular);
      margin: 0;
    }
  }
  
  .overview-section {
    margin-bottom: 24px;
    
    .overview-card {
      display: flex;
      align-items: center;
      background: var(--el-bg-color);
      border-radius: 12px;
      padding: 24px;
      box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
      transition: all 0.3s;
      
      &:hover {
        transform: translateY(-4px);
        box-shadow: 0 8px 24px rgba(0, 0, 0, 0.15);
      }
      
      .card-icon {
        width: 56px;
        height: 56px;
        border-radius: 12px;
        display: flex;
        align-items: center;
        justify-content: center;
        margin-right: 20px;
        
        .el-icon {
          font-size: 28px;
          color: white;
        }
        
        &.active-users {
          background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        }
        
        &.data-queries {
          background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        }
        
        &.downloads {
          background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
        }
        
        &.storage {
          background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%);
        }
      }
      
      .card-content {
        flex: 1;
        
        .card-value {
          font-size: 32px;
          font-weight: 700;
          color: var(--el-text-color-primary);
          line-height: 1;
          margin-bottom: 4px;
        }
        
        .card-label {
          font-size: 14px;
          color: var(--el-text-color-regular);
          margin-bottom: 8px;
        }
        
        .card-trend {
          display: flex;
          align-items: center;
          font-size: 12px;
          font-weight: 500;
          
          .el-icon {
            margin-right: 4px;
            font-size: 14px;
          }
          
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
  
  .charts-section {
    margin-bottom: 24px;
    
    .chart-card {
      height: 400px;
      
      .card-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        
        .header-controls {
          display: flex;
          gap: 12px;
          align-items: center;
        }
      }
      
      .chart-container {
        height: 320px;
        display: flex;
        align-items: center;
        justify-content: center;
        
        .chart-placeholder {
          text-align: center;
          color: var(--el-text-color-placeholder);
          
          .el-icon {
            font-size: 48px;
            margin-bottom: 16px;
          }
          
          p {
            margin: 8px 0;
            
            &.chart-desc {
              font-size: 12px;
            }
          }
        }
      }
    }
  }
  
  .ranking-section {
    .ranking-card {
      .card-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
      }
      
      .ranking-list {
        .ranking-item {
          display: flex;
          align-items: center;
          padding: 16px 0;
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
            margin-right: 16px;
            
            &.rank-1 {
              background: linear-gradient(135deg, #ffd700, #ffed4e);
              color: #8b6914;
            }
            
            &.rank-2 {
              background: linear-gradient(135deg, #c0c0c0, #e8e8e8);
              color: #666;
            }
            
            &.rank-3 {
              background: linear-gradient(135deg, #cd7f32, #daa520);
              color: #5d4e37;
            }
            
            &:not(.rank-1):not(.rank-2):not(.rank-3) {
              background: var(--el-fill-color);
              color: var(--el-text-color-regular);
            }
          }
          
          .ranking-content {
            flex: 1;
            
            .resource-name {
              font-weight: 500;
              color: var(--el-text-color-primary);
              margin-bottom: 4px;
            }
            
            .resource-stats {
              display: flex;
              gap: 16px;
              
              .stat-item {
                display: flex;
                align-items: center;
                font-size: 12px;
                color: var(--el-text-color-regular);
                
                .el-icon {
                  margin-right: 4px;
                  font-size: 14px;
                }
              }
            }
            
            .user-info {
              display: flex;
              align-items: center;
              gap: 12px;
              
              .user-details {
                .user-name {
                  font-weight: 500;
                  color: var(--el-text-color-primary);
                  margin-bottom: 2px;
                }
                
                .user-department {
                  font-size: 12px;
                  color: var(--el-text-color-regular);
                }
              }
            }
          }
          
          .ranking-trend {
            display: flex;
            align-items: center;
            font-size: 12px;
            font-weight: 500;
            
            .el-icon {
              margin-right: 2px;
              
              &.trend-up {
                color: var(--el-color-success);
              }
              
              &.trend-down {
                color: var(--el-color-danger);
              }
            }
          }
          
          .ranking-score {
            text-align: center;
            
            .score-value {
              font-size: 18px;
              font-weight: 600;
              color: var(--el-color-primary);
              line-height: 1;
            }
            
            .score-label {
              font-size: 12px;
              color: var(--el-text-color-regular);
              margin-top: 2px;
            }
          }
        }
      }
    }
  }
}

// 响应式设计
@media (max-width: 768px) {
  .usage-statistics {
    padding: 16px;
    
    .overview-section {
      .overview-card {
        padding: 16px;
        
        .card-icon {
          width: 48px;
          height: 48px;
          margin-right: 16px;
          
          .el-icon {
            font-size: 24px;
          }
        }
        
        .card-content {
          .card-value {
            font-size: 24px;
          }
        }
      }
    }
    
    .charts-section {
      .chart-card {
        .card-header {
          flex-direction: column;
          gap: 12px;
          align-items: stretch;
          
          .header-controls {
            justify-content: space-between;
          }
        }
      }
    }
  }
}
</style>