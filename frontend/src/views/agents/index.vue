<template>
  <div class="agents-page">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="header-content">
        <div class="header-left">
          <h1 class="page-title">
            <el-icon><Avatar /></el-icon>
            智能体管理
          </h1>
          <p class="page-description">创建和管理您的AI智能体</p>
        </div>
        <div class="header-right">
          <el-button type="primary" @click="handleCreate">
            <el-icon><Plus /></el-icon>
            创建智能体
          </el-button>
          <el-button @click="refreshAgents">
            <el-icon><Refresh /></el-icon>
            刷新
          </el-button>
        </div>
      </div>
    </div>
    
    <!-- 统计卡片 -->
    <div class="stats-cards">
      <el-row :gutter="20">
        <el-col :xs="12" :sm="6">
          <div class="stat-card">
            <div class="stat-icon total">
              <el-icon><Avatar /></el-icon>
            </div>
            <div class="stat-content">
              <div class="stat-value">{{ stats.total }}</div>
              <div class="stat-label">总智能体数</div>
            </div>
          </div>
        </el-col>
        
        <el-col :xs="12" :sm="6">
          <div class="stat-card">
            <div class="stat-icon active">
              <el-icon><VideoPlay /></el-icon>
            </div>
            <div class="stat-content">
              <div class="stat-value">{{ stats.active }}</div>
              <div class="stat-label">活跃中</div>
            </div>
          </div>
        </el-col>
        
        <el-col :xs="12" :sm="6">
          <div class="stat-card">
            <div class="stat-icon public">
              <el-icon><Share /></el-icon>
            </div>
            <div class="stat-content">
              <div class="stat-value">{{ stats.public }}</div>
              <div class="stat-label">公开智能体</div>
            </div>
          </div>
        </el-col>
        
        <el-col :xs="12" :sm="6">
          <div class="stat-card">
            <div class="stat-icon usage">
              <el-icon><TrendCharts /></el-icon>
            </div>
            <div class="stat-content">
              <div class="stat-value">{{ formatNumber(stats.totalUsage) }}</div>
              <div class="stat-label">总使用次数</div>
            </div>
          </div>
        </el-col>
      </el-row>
    </div>

    <!-- 筛选和搜索 -->
    <div class="filter-section">
      <el-card shadow="never">
        <el-form :model="searchForm" inline>
          <el-form-item label="搜索">
            <el-input
              v-model="searchForm.search"
              placeholder="搜索智能体名称或描述"
              clearable
              style="width: 250px"
              @input="handleSearch"
            >
              <template #prefix>
                <el-icon><Search /></el-icon>
              </template>
            </el-input>
          </el-form-item>
          
          <el-form-item label="类型">
            <el-select
              v-model="searchForm.agent_type"
              placeholder="选择类型"
              clearable
              style="width: 140px"
              @change="handleFilter"
            >
              <el-option label="全部" value="" />
              <el-option label="聊天" value="CHAT" />
              <el-option label="代码" value="CODE" />
              <el-option label="文档" value="DOCUMENT" />
              <el-option label="分析" value="ANALYSIS" />
              <el-option label="工作流" value="WORKFLOW" />
              <el-option label="审读" value="REVIEW" />
              <el-option label="自定义" value="CUSTOM" />
            </el-select>
          </el-form-item>
          

          
          <el-form-item label="状态">
            <el-select
              v-model="searchForm.status"
              placeholder="选择状态"
              clearable
              style="width: 120px"
              @change="handleFilter"
            >
              <el-option label="全部" value="" />
              <el-option label="草稿" value="draft" />
              <el-option label="活跃" value="active" />
              <el-option label="已停用" value="inactive" />
            </el-select>
          </el-form-item>
          
          <el-form-item label="可见性">
            <el-select
              v-model="searchForm.is_public"
              placeholder="选择可见性"
              clearable
              style="width: 120px"
              @change="handleFilter"
            >
              <el-option label="全部" value="" />
              <el-option label="公开" :value="true" />
              <el-option label="私有" :value="false" />
            </el-select>
          </el-form-item>
          
          <el-form-item label="排序">
            <el-select
              v-model="searchForm.sortBy"
              style="width: 150px"
              @change="handleSort"
            >
              <el-option label="创建时间" value="created_at" />
              <el-option label="更新时间" value="updated_at" />
              <el-option label="智能体名称" value="name" />
              <el-option label="使用次数" value="usage_count" />
            </el-select>
          </el-form-item>
          
          <el-form-item>
            <el-button @click="resetFilters">
              <el-icon><RefreshLeft /></el-icon>
              重置
            </el-button>
          </el-form-item>
        </el-form>
      </el-card>
    </div>

    <!-- 智能体列表 -->
    <div class="agents-list">
      <el-card shadow="never">
        <template #header>
          <div class="card-header">
            <span>智能体列表</span>
            <div class="header-actions">
              <el-button
                v-if="selectedAgents.length > 0"
                type="danger"
                size="small"
                @click="handleBatchDelete"
              >
                批量删除
              </el-button>
              <el-radio-group v-model="viewMode" size="small">
                <el-radio-button value="grid">
                  <el-icon><Grid /></el-icon>
                </el-radio-button>
                <el-radio-button value="list">
                  <el-icon><List /></el-icon>
                </el-radio-button>
              </el-radio-group>
            </div>
          </div>
        </template>
        
        <!-- 网格视图 -->
        <div v-if="viewMode === 'grid'" class="grid-view">
          <el-row :gutter="20">
            <el-col
              v-for="agent in paginatedAgents"
              :key="agent.id"
              :xs="24"
              :sm="12"
              :md="8"
              :lg="6"
            >
              <div class="agent-card">
                <div class="agent-header">
                  <div class="agent-info">
                    <div class="agent-avatar">
                      <el-avatar :size="40" :src="getAgentAvatar(agent)" />
                    </div>
                    <div class="agent-basic">
                      <h3 class="agent-name">{{ agent.name }}</h3>
                      <p class="agent-description">{{ agent.description || '暂无描述' }}</p>
                    </div>
                  </div>
                  <div class="agent-status">
                    <el-tag
                      :type="getStatusType(agent.status)"
                      size="small"
                    >
                      {{ getStatusLabel(agent.status) }}
                    </el-tag>
                  </div>
                </div>
                
                <div class="agent-content">
                  <div class="agent-meta">
                    <div class="meta-item">
                      <el-icon><Calendar /></el-icon>
                      <span>{{ formatDate(agent.created_at) }}</span>
                    </div>
                    <div class="meta-item">
                      <el-icon><User /></el-icon>
                      <span>{{ agent.creator_name }}</span>
                    </div>
                    <div class="meta-item">
                      <el-icon><ChatDotRound /></el-icon>
                      <span>{{ agent.usage_count || 0 }}次使用</span>
                    </div>
                  </div>
                  
                  <!-- 智能体详情 -->
                  <div class="agent-details">
                    <div class="detail-item">
                      <div class="detail-label">
                        <el-icon><Box /></el-icon>
                        <span>类型</span>
                      </div>
                      <div class="detail-value">
                        <el-tag :type="getAgentTypeConfig(agent.agent_type).type" size="small">
                          {{ getAgentTypeLabel(agent.agent_type) }}
                        </el-tag>
                      </div>
                    </div>
                    
                    <div class="detail-item" v-if="agent.model_name">
                      <div class="detail-label">
                        <el-icon><Cpu /></el-icon>
                        <span>模型</span>
                      </div>
                      <div class="detail-value">
                        {{ agent.model_name }}
                      </div>
                    </div>
                    
                    <div class="detail-item">
                      <div class="detail-label">
                        <el-icon><View /></el-icon>
                        <span>可见性</span>
                      </div>
                      <div class="detail-value">
                        <el-tag :type="agent.is_public ? 'success' : 'info'" size="small">
                          {{ agent.is_public ? '公开' : '私有' }}
                        </el-tag>
                      </div>
                    </div>
                  </div>
                </div>
                
                <div class="agent-actions">
                  <el-button size="small" @click="handleView(agent)">
                    查看
                  </el-button>
                  <el-button type="primary" size="small" @click="handleChat(agent)">
                    <el-icon><ChatDotRound /></el-icon>
                    对话
                  </el-button>
                  <el-button type="warning" size="small" @click="handleEdit(agent)">
                    编辑
                  </el-button>
                  <el-dropdown trigger="click">
                    <el-button size="small" text>
                      <el-icon><MoreFilled /></el-icon>
                    </el-button>
                    <template #dropdown>
                      <el-dropdown-menu>
                        <el-dropdown-item @click="handleView(agent)">
                          <el-icon><View /></el-icon>
                          查看详情
                        </el-dropdown-item>
                        <el-dropdown-item @click="handleEdit(agent)">
                          <el-icon><Edit /></el-icon>
                          编辑智能体
                        </el-dropdown-item>
                        <el-dropdown-item @click="handleDuplicate(agent)">
                          <el-icon><CopyDocument /></el-icon>
                          复制智能体
                        </el-dropdown-item>
                        <el-dropdown-item @click="handleExport(agent)">
                          <el-icon><Download /></el-icon>
                          导出智能体
                        </el-dropdown-item>
                        <el-dropdown-item
                          divided
                          @click="handleDelete(agent)"
                        >
                          <el-icon><Delete /></el-icon>
                          删除智能体
                        </el-dropdown-item>
                      </el-dropdown-menu>
                    </template>
                  </el-dropdown>
                </div>
              </div>
            </el-col>
          </el-row>
        </div>
        
        <!-- 列表视图 -->
        <div v-else class="list-view">
          <el-table
            v-loading="loading"
            :data="paginatedAgents"
            @selection-change="handleSelectionChange"
            stripe
          >
            <el-table-column type="selection" width="55" />
            <el-table-column prop="name" label="名称" min-width="150">
              <template #default="{ row }">
                <div class="agent-name">
                  <el-avatar :size="32" :src="getAgentAvatar(row)" />
                  <div class="name-info">
                    <el-link type="primary" @click="handleView(row)">
                      {{ row.name }}
                    </el-link>
                    <div class="type">{{ getAgentTypeLabel(row.agent_type) }}</div>
                  </div>
                </div>
              </template>
            </el-table-column>
            <el-table-column prop="description" label="描述" min-width="200" show-overflow-tooltip />
            <el-table-column prop="agent_type" label="类型" width="150">
              <template #default="{ row }">
                <div class="type-info">
                  <el-tag :type="getAgentTypeConfig(row.agent_type).type" size="small">
                    {{ getAgentTypeLabel(row.agent_type) }}
                  </el-tag>
                </div>
              </template>
            </el-table-column>
            <el-table-column prop="model_name" label="模型" width="120" />
            <el-table-column prop="status" label="状态" width="100">
              <template #default="{ row }">
                <el-tag :type="getStatusType(row.status)">{{ getStatusLabel(row.status) }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="is_public" label="可见性" width="80">
              <template #default="{ row }">
                <el-tag :type="row.is_public ? 'success' : 'info'">
                  {{ row.is_public ? '公开' : '私有' }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="usage_count" label="使用次数" width="100">
              <template #default="{ row }">
                {{ row.usage_count || 0 }}次
              </template>
            </el-table-column>
            <el-table-column prop="creator_name" label="创建者" width="100" />
            <el-table-column prop="created_at" label="创建时间" width="160">
              <template #default="{ row }">
                {{ formatDateTime(row.created_at) }}
              </template>
            </el-table-column>
            <el-table-column label="操作" width="200" fixed="right">
              <template #default="{ row }">
                <el-button type="primary" size="small" @click="handleView(row)">查看</el-button>
                <el-button type="warning" size="small" @click="handleEdit(row)">编辑</el-button>
                <el-button type="danger" size="small" @click="handleDelete(row)">删除</el-button>
              </template>
            </el-table-column>
          </el-table>
        </div>
        
        <!-- 分页 -->
        <div class="pagination-wrapper">
          <el-pagination
            v-model:current-page="pagination.page"
            v-model:page-size="pagination.size"
            :total="filteredAgents.length"
            :page-sizes="[10, 20, 50, 100]"
            layout="total, sizes, prev, pager, next, jumper"
            @size-change="handleSizeChange"
            @current-change="handleCurrentChange"
          />
        </div>
      </el-card>
    </div>

    <!-- 智能体详情对话框 -->
    <AgentDetailDialog
      ref="detailDialogRef"
      v-model="detailDialogVisible"
      :agent="selectedAgent"
      @edit="handleEditFromDetail"
    />

    <!-- 智能体编辑对话框 -->
    <AgentEditDialog
      ref="editDialogRef"
      v-model="editDialogVisible"
      :agent="selectedAgent"
      @submit="handleAgentSubmit"
    />

    <!-- 智能体聊天对话框 -->
    <AgentChatDialog
      v-model="chatDialogVisible"
      :agent="selectedAgent"
    />

  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { 
  Plus, Search, ArrowDown, Avatar, Refresh, VideoPlay, Share, TrendCharts,
  RefreshLeft, Grid, List, Calendar, User, ChatDotRound, Box, Cpu, View,
  MoreFilled, Edit, CopyDocument, Download, Delete
} from '@element-plus/icons-vue'
import { formatDate, formatDateTime } from '@/utils/date'
import AgentDetailDialog from './components/AgentDetailDialog.vue'
import AgentEditDialog from './components/AgentEditDialog.vue'
import AgentChatDialog from './components/AgentChatDialog.vue'
import { getAgents, getAgent, createAgent, updateAgent, deleteAgent, cloneAgent, exportAgent } from '@/api/agents'
import type { Agent, AgentCreate, AgentUpdate, AgentFilterParams } from '@/types/agent'

// 响应式数据
const loading = ref(false)
const agentList = ref<Agent[]>([])
const selectedAgents = ref<Agent[]>([])
const selectedAgent = ref<Agent | null>(null)
const detailDialogVisible = ref(false)
const editDialogVisible = ref(false)
const chatDialogVisible = ref(false)
const viewMode = ref('grid')

// 对话框引用
const detailDialogRef = ref()
const editDialogRef = ref()

// 搜索表单
const searchForm = reactive<AgentFilterParams & { sortBy: string }>({
  search: '',
  agent_type: undefined,
  status: undefined,
  is_public: undefined,
  sortBy: 'created_at'
})

// 分页信息
const pagination = reactive({
  page: 1,
  size: 20,
  total: 0
})

// 统计数据
const stats = reactive({
  total: 0,
  active: 0,
  public: 0,
  totalUsage: 0
})

// 筛选后的智能体列表
const filteredAgents = computed(() => {
  let filtered = agentList.value
  
  // 搜索过滤
  if (searchForm.search) {
    const searchLower = searchForm.search.toLowerCase()
    filtered = filtered.filter(agent => 
      agent.name.toLowerCase().includes(searchLower) ||
      (agent.description && agent.description.toLowerCase().includes(searchLower))
    )
  }
  
  // 类型过滤
  if (searchForm.agent_type) {
    filtered = filtered.filter(agent => agent.agent_type === searchForm.agent_type)
  }
  

  
  // 状态过滤
  if (searchForm.status) {
    filtered = filtered.filter(agent => agent.status === searchForm.status)
  }
  
  // 可见性过滤
  if (searchForm.is_public !== undefined && searchForm.is_public !== '') {
    filtered = filtered.filter(agent => agent.is_public === searchForm.is_public)
  }
  
  // 排序
  filtered.sort((a, b) => {
    const field = searchForm.sortBy
    if (field === 'name') {
      return a.name.localeCompare(b.name)
    } else if (field === 'usage_count') {
      return (b.usage_count || 0) - (a.usage_count || 0)
    } else {
      return new Date(b[field]).getTime() - new Date(a[field]).getTime()
    }
  })
  
  return filtered
})

// 分页后的智能体列表
const paginatedAgents = computed(() => {
  const start = (pagination.page - 1) * pagination.size
  const end = start + pagination.size
  return filteredAgents.value.slice(start, end)
})

// 更新统计数据
const updateStats = () => {
  stats.total = agentList.value.length
  stats.active = agentList.value.filter(a => a.status === 'active').length
  stats.public = agentList.value.filter(a => a.is_public).length
  stats.totalUsage = agentList.value.reduce((sum, a) => sum + (a.usage_count || 0), 0)
}

/**
 * 加载智能体列表
 */
const loadAgents = async () => {
  try {
    loading.value = true
    // 映射前端参数到后端期望的参数格式
    const params = {
      page: 1,
      size: 100, // 后端限制最大为100
      search: searchForm.search,
      agent_type: searchForm.agent_type,
      status: searchForm.status,
      is_public: searchForm.is_public,
      order_by: searchForm.sortBy || 'created_at',
      order_desc: true
    }
    
    const response = await getAgents(params)
    agentList.value = response.items || []
    updateStats()
  } catch (error) {
    console.error('加载智能体列表失败:', error)
    ElMessage.error('加载智能体列表失败')
  } finally {
    loading.value = false
  }
}

/**
 * 处理搜索
 */
const handleSearch = () => {
  pagination.page = 1
}

/**
 * 处理筛选
 */
const handleFilter = () => {
  pagination.page = 1
}

/**
 * 处理排序
 */
const handleSort = () => {
  pagination.page = 1
}

/**
 * 重置筛选
 */
const resetFilters = () => {
  Object.assign(searchForm, {
    search: '',
    agent_type: undefined,
    status: undefined,
    is_public: undefined,
    sortBy: 'created_at'
  })
  pagination.page = 1
}

/**
 * 刷新智能体列表
 */
const refreshAgents = () => {
  loadAgents()
}

/**
 * 格式化数字
 */
const formatNumber = (num: number) => {
  return new Intl.NumberFormat('zh-CN').format(num)
}

/**
 * 分页大小改变
 */
const handleSizeChange = (size: number) => {
  pagination.size = size
  pagination.page = 1
}

/**
 * 当前页改变
 */
const handleCurrentChange = (page: number) => {
  pagination.page = page
}

/**
 * 处理创建智能体
 */
const handleCreate = () => {
  selectedAgent.value = null
  editDialogVisible.value = true
}

/**
 * 处理查看智能体
 */
const handleView = (agent: Agent) => {
  selectedAgent.value = agent
  detailDialogVisible.value = true
}

/**
 * 处理编辑智能体
 */
const handleEdit = async (agent: Agent) => {
  try {
    loading.value = true
    console.log('handleEdit - 传入的 agent:', agent)
    console.log('handleEdit - agent.id:', agent.id)
    // 获取完整的智能体详细信息
    const response = await getAgent(agent.id)
    console.log('handleEdit - API 响应:', response)
    console.log('handleEdit - response.data:', response.data)
    selectedAgent.value = response
    console.log('handleEdit - selectedAgent.value:', selectedAgent.value)
    editDialogVisible.value = true
  } catch (error) {
    console.error('获取智能体详情失败:', error)
    ElMessage.error('获取智能体详情失败，请重试')
  } finally {
    loading.value = false
  }
}

/**
 * 处理与智能体对话
 */
const handleChat = (agent: Agent) => {
  selectedAgent.value = agent
  chatDialogVisible.value = true
}



/**
 * 处理智能体提交（创建/更新）
 */
const handleAgentSubmit = async (agentData: AgentCreate | (AgentUpdate & { id: number })) => {
  try {
    if ('id' in agentData && agentData.id) {
      // 更新智能体
      await updateAgent(agentData.id, agentData)
      ElMessage.success('智能体更新成功')
    } else {
      // 创建智能体
      await createAgent(agentData as AgentCreate)
       ElMessage.success('智能体创建成功')
     }
     
     editDialogVisible.value = false
     loadAgents()
  } catch (error) {
    console.error('保存智能体失败:', error)
    ElMessage.error('保存失败，请重试')
  }
}

/**
 * 从详情对话框编辑
 */
const handleEditFromDetail = async (agent: Agent) => {
  try {
    detailDialogVisible.value = false
    loading.value = true
    // 获取完整的智能体详细信息
    const response = await getAgent(agent.id)
    selectedAgent.value = response.data
    editDialogVisible.value = true
  } catch (error) {
    console.error('获取智能体详情失败:', error)
    ElMessage.error('获取智能体详情失败，请重试')
  } finally {
    loading.value = false
  }
}



/**
 * 处理选择变化
 */
const handleSelectionChange = (selection: Agent[]) => {
  selectedAgents.value = selection
}

/**
 * 处理复制智能体
 */
const handleDuplicate = async (agent: Agent) => {
  try {
    await cloneAgent(agent.id)
     ElMessage.success('智能体复制成功')
     loadData()
  } catch (error) {
    console.error('复制智能体失败:', error)
    ElMessage.error('复制智能体失败')
  }
}

/**
 * 处理导出智能体
 */
const handleExport = async (agent: Agent) => {
  try {
    const response = await exportAgent(agent.id)
    
    // 创建下载链接
    const blob = new Blob([response.data], { type: 'application/json' })
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `agent_${agent.name}_${agent.id}.json`
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    window.URL.revokeObjectURL(url)
    
    ElMessage.success('智能体导出成功')
  } catch (error) {
    console.error('导出失败:', error)
    ElMessage.error('导出失败')
  }
}

/**
 * 处理删除智能体
 */
const handleDelete = async (agent: Agent) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除智能体 "${agent.name}" 吗？此操作不可恢复。`,
      '确认删除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    await deleteAgent(agent.id)
    ElMessage.success('智能体删除成功')
    loadAgents()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除智能体失败:', error)
      ElMessage.error('删除智能体失败')
    }
  }
}

/**
 * 批量删除
 */
const handleBatchDelete = async () => {
  try {
    await ElMessageBox.confirm(
      `确定要删除选中的 ${selectedAgents.value.length} 个智能体吗？此操作不可恢复。`,
      '确认批量删除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    // 这里应该调用批量删除API，暂时逐个删除
    for (const agent of selectedAgents.value) {
      await deleteAgent(agent.id)
    }
    
    ElMessage.success('批量删除成功')
    loadAgents()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('批量删除失败:', error)
      ElMessage.error('批量删除失败')
    }
  }
}

/**
 * 获取智能体头像
 */
const getAgentAvatar = (agent: Agent) => {
  // 这里可以根据智能体类型或其他属性返回不同的头像
  return `https://api.dicebear.com/7.x/bottts/svg?seed=${agent.name}`
}

/**
 * 获取智能体类型标签
 */
const getAgentTypeLabel = (type: string) => {
  const typeMap = {
    CHAT: '聊天助手',
    CODE: '代码助手',
    DOCUMENT: '文档助手',
    ANALYSIS: '分析助手',
    WORKFLOW: '工作流助手',
    CUSTOM: '自定义'
  }
  return typeMap[type] || type
}

/**
 * 获取智能体类型配置
 */
const getAgentTypeConfig = (type: string) => {
  const typeConfigMap = {
    CHAT: { type: 'primary', label: '聊天助手' },
    CODE: { type: 'success', label: '代码助手' },
    DOCUMENT: { type: 'info', label: '文档助手' },
    ANALYSIS: { type: 'warning', label: '分析助手' },
    WORKFLOW: { type: 'danger', label: '工作流助手' },
    CUSTOM: { type: '', label: '自定义' }
  }
  return typeConfigMap[type] || { type: '', label: type }
}

/**
 * 获取状态类型
 */
const getStatusType = (status: string) => {
  const statusTypeMap = {
    DRAFT: 'info',
    draft: 'info',
    ACTIVE: 'success',
    active: 'success',
    INACTIVE: 'warning',
    inactive: 'warning'
  }
  return statusTypeMap[status] || 'info'
}



/**
 * 获取状态标签
 */
const getStatusLabel = (status: string) => {
  const statusMap = {
    DRAFT: '草稿',
    draft: '草稿',
    ACTIVE: '活跃',
    active: '活跃',
    INACTIVE: '已停用',
    inactive: '已停用'
  }
  return statusMap[status] || status
}

// 组件挂载时加载数据
onMounted(() => {
  loadAgents()
})
</script>

<style scoped>
.agents-page {
  padding: 24px;
  background-color: var(--el-bg-color-page);
  min-height: 100vh;
}

/* 页面头部 */
.page-header {
  margin-bottom: 24px;
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 24px;
  background: var(--el-bg-color);
  border-radius: 12px;
  box-shadow: var(--el-box-shadow-light);
  border: 1px solid var(--el-border-color-lighter);
}

.header-left {
  flex: 1;
}

.page-title {
  margin: 0 0 8px 0;
  font-size: 28px;
  font-weight: 600;
  color: var(--el-text-color-primary);
  display: flex;
  align-items: center;
  gap: 12px;
}

.page-title .el-icon {
  font-size: 32px;
  color: var(--el-color-primary);
}

.page-description {
  margin: 0;
  color: var(--el-text-color-regular);
  font-size: 14px;
}

.header-right {
  display: flex;
  gap: 12px;
}

/* 统计卡片 */
.stats-cards {
  margin-bottom: 24px;
}

.stat-card {
  display: flex;
  align-items: center;
  padding: 20px;
  background: var(--el-bg-color);
  border-radius: 12px;
  box-shadow: var(--el-box-shadow-light);
  border: 1px solid var(--el-border-color-lighter);
  transition: all 0.3s ease;
  height: 100%;
}

.stat-card:hover {
  transform: translateY(-2px);
  box-shadow: var(--el-box-shadow);
}

.stat-icon {
  width: 48px;
  height: 48px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-right: 16px;
  font-size: 24px;
  color: white;
}

.stat-icon.total {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.stat-icon.active {
  background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
}

.stat-icon.public {
  background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
}

.stat-icon.usage {
  background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%);
}

.stat-content {
  flex: 1;
}

.stat-value {
  font-size: 24px;
  font-weight: 600;
  color: var(--el-text-color-primary);
  margin-bottom: 4px;
}

.stat-label {
  font-size: 14px;
  color: var(--el-text-color-regular);
}

/* 筛选区域 */
.filter-section {
  margin-bottom: 24px;
}

.filter-section .el-card {
  border-radius: 12px;
  border: 1px solid var(--el-border-color-lighter);
}

/* 智能体列表 */
.agents-list .el-card {
  border-radius: 12px;
  border: 1px solid var(--el-border-color-lighter);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-weight: 600;
  color: var(--el-text-color-primary);
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 12px;
}

/* 网格视图 */
.grid-view {
  margin-bottom: 24px;
}

.agent-card {
  background: var(--el-bg-color);
  border: 1px solid var(--el-border-color-lighter);
  border-radius: 12px;
  padding: 20px;
  transition: all 0.3s ease;
  height: 100%;
  display: flex;
  flex-direction: column;
}

.agent-card:hover {
  transform: translateY(-2px);
  box-shadow: var(--el-box-shadow);
  border-color: var(--el-color-primary-light-7);
}

.agent-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 16px;
}

.agent-info {
  display: flex;
  gap: 12px;
  flex: 1;
}

.agent-avatar {
  flex-shrink: 0;
}

.agent-basic {
  flex: 1;
  min-width: 0;
}

.agent-name {
  margin: 0 0 8px 0;
  font-size: 16px;
  font-weight: 600;
  color: var(--el-text-color-primary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.agent-description {
  margin: 0;
  font-size: 14px;
  color: var(--el-text-color-regular);
  line-height: 1.4;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.agent-status {
  flex-shrink: 0;
}

.agent-content {
  flex: 1;
  margin-bottom: 16px;
}

.agent-meta {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-bottom: 16px;
}

.meta-item {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: var(--el-text-color-regular);
}

.meta-item .el-icon {
  font-size: 14px;
  color: var(--el-text-color-placeholder);
}

.agent-details {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.detail-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.detail-label {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: var(--el-text-color-regular);
}

.detail-label .el-icon {
  font-size: 14px;
  color: var(--el-text-color-placeholder);
}

.detail-value {
  font-size: 12px;
}

.agent-actions {
  display: flex;
  gap: 8px;
  padding-top: 16px;
  border-top: 1px solid var(--el-border-color-lighter);
}

.agent-actions .el-button {
  flex: 1;
}

/* 列表视图 */
.list-view .agent-name {
  display: flex;
  align-items: center;
  gap: 12px;
}

.list-view .name-info {
  display: flex;
  flex-direction: column;
}

.list-view .name-info .el-link {
  font-weight: 500;
  margin-bottom: 2px;
}

.list-view .type {
  font-size: 12px;
  color: var(--el-text-color-regular);
}

/* 分页 */
.pagination-wrapper {
  margin-top: 24px;
  display: flex;
  justify-content: center;
}

/* 暗色主题适配 */
.dark .stat-card,
.dark .agent-card {
  background: var(--el-bg-color-overlay);
  border-color: var(--el-border-color);
}

.dark .agent-card:hover {
  border-color: var(--el-color-primary-light-3);
}

/* 响应式设计 */
@media (max-width: 1200px) {
  .agents-page {
    padding: 16px;
  }
}

@media (max-width: 768px) {
  .agents-page {
    padding: 12px;
  }
  
  .header-content {
    flex-direction: column;
    align-items: flex-start;
    gap: 16px;
    padding: 20px;
  }
  
  .header-right {
    width: 100%;
    justify-content: flex-end;
  }
  
  .page-title {
    font-size: 24px;
  }
  
  .stat-card {
    padding: 16px;
  }
  
  .stat-icon {
    width: 40px;
    height: 40px;
    font-size: 20px;
  }
  
  .stat-value {
    font-size: 20px;
  }
  
  .agent-card {
    padding: 16px;
  }
  
  .filter-section .el-form {
    flex-direction: column;
  }
  
  .filter-section .el-form-item {
    margin-bottom: 16px;
    margin-right: 0;
  }
}

@media (max-width: 480px) {
  .header-actions {
    flex-direction: column;
    width: 100%;
    gap: 8px;
  }
  
  .agent-actions {
    flex-direction: column;
  }
  
  .agent-actions .el-button {
    width: 100%;
  }
}

:deep(.el-table) {
  border: none;
}

:deep(.el-table__header) {
  background-color: var(--el-fill-color-lighter);
}

:deep(.el-table th) {
  background-color: var(--el-fill-color-lighter);
  border-bottom: 1px solid var(--el-border-color-lighter);
}

:deep(.el-table td) {
  border-bottom: 1px solid var(--el-border-color-lighter);
}

:deep(.el-table__row:hover > td) {
  background-color: var(--el-fill-color-light);
}
</style>