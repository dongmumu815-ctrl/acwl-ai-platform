<template>
  <div class="access-statistics">
    <div class="page-header">
      <h1 class="page-title">
        <el-icon><TrendCharts /></el-icon>
        访问统计
      </h1>
      <p class="page-description">数据资源访问情况统计分析</p>
    </div>

    <!-- 统计卡片 -->
    <div class="stats-cards">
      <el-row :gutter="20">
        <el-col :xs="24" :sm="12" :md="6">
          <div class="stat-card">
            <div class="stat-icon today">
              <el-icon><View /></el-icon>
            </div>
            <div class="stat-content">
              <div class="stat-value">{{ todayVisits }}</div>
              <div class="stat-label">今日访问</div>
            </div>
          </div>
        </el-col>
        
        <el-col :xs="24" :sm="12" :md="6">
          <div class="stat-card">
            <div class="stat-icon week">
              <el-icon><Calendar /></el-icon>
            </div>
            <div class="stat-content">
              <div class="stat-value">{{ weekVisits }}</div>
              <div class="stat-label">本周访问</div>
            </div>
          </div>
        </el-col>
        
        <el-col :xs="24" :sm="12" :md="6">
          <div class="stat-card">
            <div class="stat-icon month">
              <el-icon><DataAnalysis /></el-icon>
            </div>
            <div class="stat-content">
              <div class="stat-value">{{ monthVisits }}</div>
              <div class="stat-label">本月访问</div>
            </div>
          </div>
        </el-col>
        
        <el-col :xs="24" :sm="12" :md="6">
          <div class="stat-card">
            <div class="stat-icon total">
              <el-icon><Odometer /></el-icon>
            </div>
            <div class="stat-content">
              <div class="stat-value">{{ totalVisits }}</div>
              <div class="stat-label">总访问量</div>
            </div>
          </div>
        </el-col>
      </el-row>
    </div>

    <!-- 图表区域 -->
    <div class="charts-section">
      <el-row :gutter="20">
        <el-col :xs="24" :lg="12">
          <el-card class="chart-card">
            <template #header>
              <div class="card-header">
                <span>访问趋势</span>
                <el-button type="primary" size="small" @click="refreshChart">
                  <el-icon><Refresh /></el-icon>
                  刷新
                </el-button>
              </div>
            </template>
            <div class="chart-container">
              <div class="chart-placeholder">
                <el-icon><TrendCharts /></el-icon>
                <p>访问趋势图表</p>
                <p class="chart-desc">显示最近30天的访问趋势变化</p>
              </div>
            </div>
          </el-card>
        </el-col>
        
        <el-col :xs="24" :lg="12">
          <el-card class="chart-card">
            <template #header>
              <div class="card-header">
                <span>热门资源</span>
                <el-button type="primary" size="small" @click="refreshChart">
                  <el-icon><Refresh /></el-icon>
                  刷新
                </el-button>
              </div>
            </template>
            <div class="chart-container">
              <div class="chart-placeholder">
                <el-icon><PieChart /></el-icon>
                <p>热门资源分布</p>
                <p class="chart-desc">显示最受欢迎的数据资源访问分布</p>
              </div>
            </div>
          </el-card>
        </el-col>
      </el-row>
    </div>

    <!-- 详细数据表格 -->
    <el-card class="table-card">
      <template #header>
        <div class="card-header">
          <span>访问详情</span>
          <div class="header-actions">
            <el-date-picker
              v-model="dateRange"
              type="daterange"
              range-separator="至"
              start-placeholder="开始日期"
              end-placeholder="结束日期"
              size="small"
              @change="handleDateChange"
            />
            <el-button type="primary" size="small" @click="exportData">
              <el-icon><Download /></el-icon>
              导出
            </el-button>
          </div>
        </div>
      </template>
      
      <el-table :data="accessData" stripe>
        <el-table-column prop="resource" label="资源名称" min-width="200" />
        <el-table-column prop="visits" label="访问次数" width="120" align="center" />
        <el-table-column prop="uniqueVisitors" label="独立访客" width="120" align="center" />
        <el-table-column prop="avgDuration" label="平均时长" width="120" align="center" />
        <el-table-column prop="lastAccess" label="最后访问" width="180" align="center" />
        <el-table-column label="操作" width="120" align="center">
          <template #default="{ row }">
            <el-button type="primary" size="small" text @click="viewDetails(row)">
              查看详情
            </el-button>
          </template>
        </el-table-column>
      </el-table>
      
      <div class="table-pagination">
        <el-pagination
          v-model:current-page="currentPage"
          v-model:page-size="pageSize"
          :total="total"
          :page-sizes="[10, 20, 50, 100]"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="handleSizeChange"
          @current-change="handleCurrentChange"
        />
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'

// 统计数据
const todayVisits = ref(1234)
const weekVisits = ref(8567)
const monthVisits = ref(32145)
const totalVisits = ref(156789)

// 日期范围
const dateRange = ref<[Date, Date] | null>(null)

// 表格数据
const accessData = ref([
  {
    resource: '用户行为数据集',
    visits: 1234,
    uniqueVisitors: 567,
    avgDuration: '5分32秒',
    lastAccess: '2024-01-15 14:30:25'
  },
  {
    resource: '销售数据分析',
    visits: 987,
    uniqueVisitors: 432,
    avgDuration: '3分45秒',
    lastAccess: '2024-01-15 13:22:18'
  },
  {
    resource: '市场调研报告',
    visits: 756,
    uniqueVisitors: 298,
    avgDuration: '7分12秒',
    lastAccess: '2024-01-15 12:15:42'
  }
])

// 分页数据
const currentPage = ref(1)
const pageSize = ref(20)
const total = ref(100)

/**
 * 刷新图表数据
 */
const refreshChart = () => {
  ElMessage.success('图表数据已刷新')
}

/**
 * 处理日期范围变化
 */
const handleDateChange = (dates: [Date, Date] | null) => {
  console.log('日期范围变化:', dates)
  // 这里可以根据日期范围重新加载数据
}

/**
 * 导出数据
 */
const exportData = () => {
  ElMessage.success('数据导出功能开发中')
}

/**
 * 查看详情
 */
const viewDetails = (row: any) => {
  console.log('查看详情:', row)
  ElMessage.info(`查看 ${row.resource} 的详细访问信息`)
}

/**
 * 处理页面大小变化
 */
const handleSizeChange = (size: number) => {
  pageSize.value = size
  // 重新加载数据
}

/**
 * 处理当前页变化
 */
const handleCurrentChange = (page: number) => {
  currentPage.value = page
  // 重新加载数据
}

/**
 * 组件挂载时加载数据
 */
onMounted(() => {
  // 加载统计数据
})
</script>

<style lang="scss" scoped>
.access-statistics {
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
  
  .stats-cards {
    margin-bottom: 24px;
    
    .stat-card {
      display: flex;
      align-items: center;
      background: var(--el-bg-color);
      border-radius: 8px;
      padding: 20px;
      box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
      transition: transform 0.3s, box-shadow 0.3s;
      
      &:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 16px rgba(0, 0, 0, 0.15);
      }
      
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
        
        &.today {
          background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        }
        
        &.week {
          background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        }
        
        &.month {
          background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
        }
        
        &.total {
          background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%);
        }
      }
      
      .stat-content {
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
  
  .charts-section {
    margin-bottom: 24px;
    
    .chart-card {
      height: 400px;
      
      .card-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
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
  
  .table-card {
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
    
    .table-pagination {
      display: flex;
      justify-content: center;
      margin-top: 20px;
    }
  }
}

// 响应式设计
@media (max-width: 768px) {
  .access-statistics {
    padding: 16px;
    
    .stats-cards {
      .stat-card {
        padding: 16px;
        
        .stat-icon {
          width: 40px;
          height: 40px;
          margin-right: 12px;
          
          .el-icon {
            font-size: 20px;
          }
        }
        
        .stat-content {
          .stat-value {
            font-size: 24px;
          }
        }
      }
    }
    
    .table-card {
      .card-header {
        flex-direction: column;
        gap: 12px;
        align-items: stretch;
        
        .header-actions {
          justify-content: space-between;
        }
      }
    }
  }
}
</style>