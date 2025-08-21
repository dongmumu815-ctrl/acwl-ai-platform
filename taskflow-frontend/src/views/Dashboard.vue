<template>
  <div class="dashboard">
    <!-- 页面头部 -->
    <div class="dashboard-header">
      <h1>工作流管理仪表盘</h1>
      <p>欢迎回来，{{ userStore.userInfo?.username || '用户' }}！</p>
    </div>
    
    <!-- 统计卡片 -->
    <div class="stats-grid">
      <el-card class="stat-card" shadow="hover">
        <div class="stat-content">
          <div class="stat-icon workflow">
            <el-icon><Operation /></el-icon>
          </div>
          <div class="stat-info">
            <h3>{{ stats.totalWorkflows }}</h3>
            <p>工作流总数</p>
          </div>
        </div>
      </el-card>
      
      <el-card class="stat-card" shadow="hover">
        <div class="stat-content">
          <div class="stat-icon task">
            <el-icon><List /></el-icon>
          </div>
          <div class="stat-info">
            <h3>{{ stats.totalTasks }}</h3>
            <p>任务总数</p>
          </div>
        </div>
      </el-card>
      
      <el-card class="stat-card" shadow="hover">
        <div class="stat-content">
          <div class="stat-icon running">
            <el-icon><VideoPlay /></el-icon>
          </div>
          <div class="stat-info">
            <h3>{{ stats.runningWorkflows }}</h3>
            <p>运行中</p>
          </div>
        </div>
      </el-card>
      
      <el-card class="stat-card" shadow="hover">
        <div class="stat-content">
          <div class="stat-icon project">
            <el-icon><Folder /></el-icon>
          </div>
          <div class="stat-info">
            <h3>{{ stats.totalProjects }}</h3>
            <p>项目总数</p>
          </div>
        </div>
      </el-card>
    </div>
    
    <!-- 内容区域 -->
    <div class="dashboard-content">
      <!-- 最近工作流 -->
      <div class="content-section">
        <el-card class="section-card" shadow="never">
          <template #header>
            <div class="section-header">
              <h3>最近工作流</h3>
              <el-button type="primary" link @click="$router.push({ name: 'WorkflowList' })">
                查看全部
              </el-button>
            </div>
          </template>
          
          <el-table
            :data="recentWorkflows"
            style="width: 100%"
            :show-header="false"
            class="recent-table"
          >
            <el-table-column prop="name" label="名称">
              <template #default="{ row }">
                <div class="workflow-item">
                  <div class="workflow-info">
                    <h4>{{ row.name }}</h4>
                    <p>{{ row.description }}</p>
                  </div>
                  <div class="workflow-status">
                    <el-tag
                      :type="getStatusType(row.status)"
                      size="small"
                    >
                      {{ getStatusText(row.status) }}
                    </el-tag>
                  </div>
                </div>
              </template>
            </el-table-column>
          </el-table>
          
          <div v-if="!recentWorkflows.length" class="empty-state">
            <el-empty description="暂无工作流" />
          </div>
        </el-card>
      </div>
      
      <!-- 执行历史 -->
      <div class="content-section">
        <el-card class="section-card" shadow="never">
          <template #header>
            <div class="section-header">
              <h3>最近执行</h3>
              <el-button type="primary" link @click="$router.push({ name: 'Monitoring' })">
                查看全部
              </el-button>
            </div>
          </template>
          
          <el-table
            :data="recentExecutions"
            style="width: 100%"
            :show-header="false"
            class="recent-table"
          >
            <el-table-column prop="workflow_name" label="工作流">
              <template #default="{ row }">
                <div class="execution-item">
                  <div class="execution-info">
                    <h4>{{ row.workflow_name }}</h4>
                    <p>{{ formatTime(row.start_time) }}</p>
                  </div>
                  <div class="execution-status">
                    <el-tag
                      :type="getExecutionStatusType(row.status)"
                      size="small"
                    >
                      {{ getExecutionStatusText(row.status) }}
                    </el-tag>
                  </div>
                </div>
              </template>
            </el-table-column>
          </el-table>
          
          <div v-if="!recentExecutions.length" class="empty-state">
            <el-empty description="暂无执行记录" />
          </div>
        </el-card>
      </div>
    </div>
    
    <!-- 快速操作 -->
    <div class="quick-actions">
      <el-card class="action-card" shadow="never">
        <template #header>
          <h3>快速操作</h3>
        </template>
        
        <div class="action-buttons">
          <el-button
            type="primary"
            size="large"
            @click="handleCreateWorkflow"
          >
            <el-icon><Plus /></el-icon>
            创建工作流
          </el-button>
          
          <el-button
            type="success"
            size="large"
            @click="handleCreateTask"
          >
            <el-icon><DocumentAdd /></el-icon>
            创建任务
          </el-button>
          
          <el-button
            type="info"
            size="large"
            @click="$router.push({ name: 'ProjectCreate' })"
          >
            <el-icon><FolderAdd /></el-icon>
            创建项目
          </el-button>
        </div>
      </el-card>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore, useWorkflowStore } from '@/stores'
import { formatDistanceToNow } from 'date-fns'
import { zhCN } from 'date-fns/locale'
import { ElMessage } from 'element-plus'


/**
 * 仪表盘页面组件
 */
const router = useRouter()
const userStore = useUserStore()
const workflowStore = useWorkflowStore()

// 统计数据
const stats = reactive({
  totalWorkflows: 0,
  totalTasks: 0,
  runningWorkflows: 0,
  totalProjects: 0
})

// 最近工作流
const recentWorkflows = ref([])

// 最近执行记录
const recentExecutions = ref([])

/**
 * 获取状态类型
 */
const getStatusType = (status) => {
  const statusMap = {
    'active': 'success',
    'inactive': 'info',
    'error': 'danger'
  }
  return statusMap[status] || 'info'
}

/**
 * 获取状态文本
 */
const getStatusText = (status) => {
  const statusMap = {
    'active': '活跃',
    'inactive': '未激活',
    'error': '错误'
  }
  return statusMap[status] || '未知'
}

/**
 * 获取执行状态类型
 */
const getExecutionStatusType = (status) => {
  const statusMap = {
    'running': 'warning',
    'success': 'success',
    'failed': 'danger',
    'pending': 'info'
  }
  return statusMap[status] || 'info'
}

/**
 * 获取执行状态文本
 */
const getExecutionStatusText = (status) => {
  const statusMap = {
    'running': '运行中',
    'success': '成功',
    'failed': '失败',
    'pending': '等待中'
  }
  return statusMap[status] || '未知'
}

/**
 * 格式化时间
 */
const formatTime = (time) => {
  if (!time) return ''
  return formatDistanceToNow(new Date(time), {
    addSuffix: true,
    locale: zhCN
  })
}

/**
 * 加载仪表盘数据
 */
const loadDashboardData = async () => {
  try {
    // 模拟数据，实际应该调用API
    stats.totalWorkflows = 12
    stats.totalTasks = 45
    stats.runningWorkflows = 3
    stats.totalProjects = 8
    
    recentWorkflows.value = [
      {
        id: 1,
        name: '数据处理流程',
        description: '处理用户数据的工作流',
        status: 'active'
      },
      {
        id: 2,
        name: '报表生成',
        description: '自动生成日报表',
        status: 'active'
      },
      {
        id: 3,
        name: '数据备份',
        description: '定期备份重要数据',
        status: 'inactive'
      }
    ]
    
    recentExecutions.value = [
      {
        id: 1,
        workflow_name: '数据处理流程',
        status: 'success',
        start_time: new Date(Date.now() - 1000 * 60 * 30) // 30分钟前
      },
      {
        id: 2,
        workflow_name: '报表生成',
        status: 'running',
        start_time: new Date(Date.now() - 1000 * 60 * 10) // 10分钟前
      },
      {
        id: 3,
        workflow_name: '数据备份',
        status: 'failed',
        start_time: new Date(Date.now() - 1000 * 60 * 60) // 1小时前
      }
    ]
  } catch (error) {
    console.error('加载仪表盘数据失败:', error)
  }
}

/**
 * 检查登录状态和token
 */
const checkAuthStatus = () => {
  console.log('=== 认证状态检查 ===')
  console.log('userStore.isLoggedIn:', userStore.isLoggedIn)
  console.log('userStore.token:', userStore.token)
  console.log('Cookie token:', document.cookie.split(';').find(c => c.trim().startsWith('token=')))
  console.log('userStore.userInfo:', userStore.userInfo)
}

/**
 * 处理创建工作流按钮点击
 */
const handleCreateWorkflow = () => {
  console.log('=== 创建工作流按钮被点击 ===')
  console.log('userStore.isLoggedIn:', userStore.isLoggedIn)
  console.log('userStore.token:', userStore.token)
  
  // 暂时跳过认证检查，直接测试路由跳转
  console.log('尝试跳转到 WorkflowCreate 路由')
  try {
    router.push({ name: 'WorkflowCreate' })
    console.log('路由跳转命令已执行')
  } catch (error) {
    console.error('路由跳转失败:', error)
    ElMessage.error('跳转失败: ' + error.message)
  }
}

/**
 * 处理创建任务按钮点击
 */
const handleCreateTask = () => {
  console.log('=== 创建任务按钮被点击 ===')
  console.log('userStore.isLoggedIn:', userStore.isLoggedIn)
  console.log('userStore.token:', userStore.token)
  
  // 暂时跳过认证检查，直接测试路由跳转
  console.log('尝试跳转到 TaskCreate 路由')
  try {
    router.push({ name: 'TaskCreate' })
    console.log('路由跳转命令已执行')
  } catch (error) {
    console.error('路由跳转失败:', error)
    ElMessage.error('跳转失败: ' + error.message)
  }
}

/**
 * 组件挂载时加载数据
 */
onMounted(() => {

  loadDashboardData()
  checkAuthStatus()

})
</script>

<style scoped>
.dashboard {
  padding: 24px;
  background: #f5f5f5;
  min-height: 100vh;
}

.dashboard-header {
  margin-bottom: 24px;
}

.dashboard-header h1 {
  margin: 0 0 8px;
  font-size: 28px;
  font-weight: 600;
  color: #1f2937;
}

.dashboard-header p {
  margin: 0;
  font-size: 16px;
  color: #6b7280;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 24px;
  margin-bottom: 24px;
}

.stat-card {
  border: none;
  border-radius: 12px;
}

.stat-content {
  display: flex;
  align-items: center;
  gap: 16px;
}

.stat-icon {
  width: 60px;
  height: 60px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
  color: white;
}

.stat-icon.workflow {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.stat-icon.task {
  background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
}

.stat-icon.running {
  background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
}

.stat-icon.project {
  background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%);
}

.stat-info h3 {
  margin: 0 0 4px;
  font-size: 32px;
  font-weight: 700;
  color: #1f2937;
}

.stat-info p {
  margin: 0;
  font-size: 14px;
  color: #6b7280;
}

.dashboard-content {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 24px;
  margin-bottom: 24px;
}

.section-card {
  border: none;
  border-radius: 12px;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.section-header h3 {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
  color: #1f2937;
}

.recent-table {
  margin-top: 16px;
}

.workflow-item,
.execution-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 0;
}

.workflow-info h4,
.execution-info h4 {
  margin: 0 0 4px;
  font-size: 16px;
  font-weight: 500;
  color: #1f2937;
}

.workflow-info p,
.execution-info p {
  margin: 0;
  font-size: 14px;
  color: #6b7280;
}

.empty-state {
  padding: 40px 0;
}

.quick-actions {
  max-width: 600px;
}

.action-card {
  border: none;
  border-radius: 12px;
}

.action-card h3 {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
  color: #1f2937;
}

.action-buttons {
  display: flex;
  gap: 16px;
  margin-top: 16px;
}

.action-buttons .el-button {
  flex: 1;
  height: 48px;
  border-radius: 8px;
}

/* 响应式设计 */
@media (max-width: 1024px) {
  .dashboard-content {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 768px) {
  .dashboard {
    padding: 16px;
  }
  
  .stats-grid {
    grid-template-columns: repeat(2, 1fr);
    gap: 16px;
  }
  
  .action-buttons {
    flex-direction: column;
  }
}

@media (max-width: 480px) {
  .stats-grid {
    grid-template-columns: 1fr;
  }
  
  .stat-content {
    gap: 12px;
  }
  
  .stat-icon {
    width: 48px;
    height: 48px;
    font-size: 20px;
  }
  
  .stat-info h3 {
    font-size: 24px;
  }
}
</style>