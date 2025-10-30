<template>
  <div class="servers-page">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="header-content">
        <div class="header-left">
          <h1 class="page-title">
            <el-icon><Monitor /></el-icon>
            服务器管理
          </h1>
          <p class="page-description">管理和监控部署服务器资源</p>
        </div>
        <div class="header-right">
          <el-button type="primary" @click="showCreateDialog">
            <el-icon><Plus /></el-icon>
            添加服务器
          </el-button>
          <el-button @click="refreshServers">
            <el-icon><Refresh /></el-icon>
            刷新
          </el-button>
        </div>
      </div>
    </div>

    <!-- 统计卡片 -->
    <div class="stats-section">
      <el-row :gutter="20">
        <el-col :xs="12" :sm="6">
          <div class="stat-card">
            <div class="stat-icon total">
              <el-icon><Monitor /></el-icon>
            </div>
            <div class="stat-content">
              <div class="stat-value">{{ stats.total }}</div>
              <div class="stat-label">总服务器</div>
            </div>
          </div>
        </el-col>
        
        <el-col :xs="12" :sm="6">
          <div class="stat-card">
            <div class="stat-icon online">
              <el-icon><CircleCheckFilled /></el-icon>
            </div>
            <div class="stat-content">
              <div class="stat-value">{{ stats.online }}</div>
              <div class="stat-label">在线</div>
            </div>
          </div>
        </el-col>
        
        <el-col :xs="12" :sm="6">
          <div class="stat-card">
            <div class="stat-icon offline">
              <el-icon><CircleCloseFilled /></el-icon>
            </div>
            <div class="stat-content">
              <div class="stat-value">{{ stats.offline }}</div>
              <div class="stat-label">离线</div>
            </div>
          </div>
        </el-col>
        
        <el-col :xs="12" :sm="6">
          <div class="stat-card">
            <div class="stat-icon gpus">
              <el-icon><VideoCamera /></el-icon>
            </div>
            <div class="stat-content">
              <div class="stat-value">{{ stats.totalGpus }}</div>
              <div class="stat-label">GPU总数</div>
            </div>
          </div>
        </el-col>
      </el-row>
    </div>

    <!-- 搜索和筛选 -->
    <div class="search-section">
      <el-row :gutter="20">
        <el-col :xs="24" :sm="8">
          <el-input
            v-model="searchQuery"
            placeholder="搜索服务器名称、IP地址..."
            @input="handleSearch"
            clearable
          >
            <template #prefix>
              <el-icon><Search /></el-icon>
            </template>
          </el-input>
        </el-col>
        <el-col :xs="12" :sm="4">
          <el-select
            v-model="filterType"
            placeholder="服务器类型"
            @change="handleFilter"
            clearable
          >
            <el-option label="物理机" value="physical" />
            <el-option label="虚拟机" value="virtual" />
            <el-option label="云服务器" value="cloud" />
          </el-select>
        </el-col>
        <el-col :xs="12" :sm="4">
          <el-select
            v-model="filterStatus"
            placeholder="状态"
            @change="handleFilter"
            clearable
          >
            <el-option label="在线" value="online" />
            <el-option label="离线" value="offline" />
            <el-option label="维护中" value="maintenance" />
          </el-select>
        </el-col>
        <!-- 搜索与重置按钮区域（已移除搜索按钮，仅保留重置） -->
        <el-col :xs="24" :sm="8">
          <div class="search-actions">
            <el-button @click="resetSearch">
              <el-icon><Refresh /></el-icon>
              重置
            </el-button>
          </div>
        </el-col>
      </el-row>
    </div>

    <!-- 服务器列表 -->
    <div class="servers-section">
      <el-card shadow="never">
        <template #header>
          <div class="card-header">
            <span>服务器列表</span>
            <div class="header-actions">
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
          <div class="servers-grid">
            <div
              v-for="server in servers"
              :key="server.id"
              class="server-card"
              @click="viewServerDetail(server)"
            >
            <div class="server-header">
              <div class="server-info">
                <div class="server-name">{{ server.name }}</div>
                <div class="server-ip">{{ server.ip_address }}</div>
              </div>
              <div class="server-status" :class="server.status">
                <el-icon v-if="server.status === 'online'">
                  <CircleCheckFilled />
                </el-icon>
                <el-icon v-else-if="server.status === 'offline'">
                  <CircleCloseFilled />
                </el-icon>
                <el-icon v-else>
                  <WarningFilled />
                </el-icon>
                {{ getStatusText(server.status) }}
              </div>
            </div>
            
            <div class="server-details">
              <div class="detail-item">
                <span class="label">类型:</span>
                <span class="value">{{ getTypeText(server.server_type) }}</span>
              </div>
              <div class="detail-item">
                <span class="label">系统:</span>
                <span class="value">{{ server.os_info || '未知' }}</span>
              </div>
              <div class="detail-item">
                <span class="label">CPU:</span>
                <span class="value">{{ server.total_cpu_cores || 0 }} 核</span>
              </div>
              <div class="detail-item">
                <span class="label">内存:</span>
                <span class="value">{{ server.total_memory || '未知' }}</span>
              </div>
              <div class="detail-item">
                <span class="label">GPU:</span>
                <span class="value">{{ server.gpu_resources?.length || 0 }} 个</span>
              </div>
              <div class="detail-item">
                <span class="label">部署:</span>
                <span class="value">{{ server.deployment_count || 0 }} 个</span>
              </div>
            </div>
            
            <div class="server-actions" @click.stop>
              <el-button
                size="small"
                @click="testConnection(server)"
                :loading="server.testing"
              >
                <el-icon><Connection /></el-icon>
                测试连接
              </el-button>
              <el-button
                size="small"
                @click="viewGpus(server)"
              >
                <el-icon><VideoCamera /></el-icon>
                GPU资源
              </el-button>
              <el-dropdown @command="handleServerAction">
                <el-button size="small">
                  <el-icon><MoreFilled /></el-icon>
                </el-button>
                <template #dropdown>
                  <el-dropdown-menu>
                    <el-dropdown-item :command="{action: 'edit', server}">
                      <el-icon><Edit /></el-icon>
                      编辑
                    </el-dropdown-item>
                    <el-dropdown-item :command="{action: 'monitor', server}">
                      <el-icon><TrendCharts /></el-icon>
                      监控
                    </el-dropdown-item>
                    <el-dropdown-item :command="{action: 'scan', server}">
                      <el-icon><Search /></el-icon>
                      扫描GPU
                    </el-dropdown-item>
                    <el-dropdown-item
                      divided
                      :command="{action: 'delete', server}"
                    >
                      <el-icon><Delete /></el-icon>
                      删除
                    </el-dropdown-item>
                  </el-dropdown-menu>
                </template>
              </el-dropdown>
            </div>
          </div>
        </div>
        </div>
        
        <!-- 列表视图 -->
        <div v-else class="list-view">
          <el-table
            :data="servers"
            style="width: 100%"
          >
            <el-table-column prop="name" label="服务器名称" sortable>
              <template #default="{ row }">
                <div class="server-name-cell">
                  <div class="server-info">
                    <div class="name">{{ row.name }}</div>
                    <div class="ip">{{ row.ip_address }}</div>
                  </div>
                </div>
              </template>
            </el-table-column>
            
            <el-table-column prop="server_type" label="类型" width="120">
              <template #default="{ row }">
                <el-tag size="small">{{ getTypeText(row.server_type) }}</el-tag>
              </template>
            </el-table-column>
            
            <el-table-column prop="status" label="状态" width="100">
              <template #default="{ row }">
                <el-tag
                  :type="row.status === 'online' ? 'success' : row.status === 'offline' ? 'danger' : 'warning'"
                  size="small"
                >
                  {{ getStatusText(row.status) }}
                </el-tag>
              </template>
            </el-table-column>
            
            <el-table-column prop="os_info" label="操作系统" width="150">
              <template #default="{ row }">
                {{ row.os_info || '未知' }}
              </template>
            </el-table-column>
            
            <el-table-column prop="total_cpu_cores" label="CPU" width="80">
              <template #default="{ row }">
                {{ row.total_cpu_cores || 0 }} 核
              </template>
            </el-table-column>
            
            <el-table-column prop="total_memory" label="内存" width="100">
              <template #default="{ row }">
                {{ row.total_memory || '未知' }}
              </template>
            </el-table-column>
            
            <el-table-column prop="gpu_count" label="GPU" width="80">
              <template #default="{ row }">
                {{ row.gpu_count || 0 }} 个
              </template>
            </el-table-column>
            
            <el-table-column prop="deployment_count" label="部署" width="80">
              <template #default="{ row }">
                {{ row.deployment_count || 0 }} 个
              </template>
            </el-table-column>
            
            <el-table-column label="操作" width="250" fixed="right">
              <template #default="{ row }">
                <el-button
                  size="small"
                  @click="testConnection(row)"
                  :loading="row.testing"
                >
                  <el-icon><Connection /></el-icon>
                  测试连接
                </el-button>
                <el-button
                  size="small"
                  @click="viewGpus(row)"
                >
                  <el-icon><VideoCamera /></el-icon>
                  GPU资源
                </el-button>
                <el-dropdown @command="handleServerAction">
                  <el-button size="small">
                    <el-icon><MoreFilled /></el-icon>
                  </el-button>
                  <template #dropdown>
                    <el-dropdown-menu>
                      <el-dropdown-item :command="{action: 'edit', server: row}">
                        <el-icon><Edit /></el-icon>
                        编辑
                      </el-dropdown-item>
                      <el-dropdown-item :command="{action: 'monitor', server: row}">
                        <el-icon><TrendCharts /></el-icon>
                        监控
                      </el-dropdown-item>
                      <el-dropdown-item :command="{action: 'scan', server: row}">
                        <el-icon><Search /></el-icon>
                        扫描GPU
                      </el-dropdown-item>
                      <el-dropdown-item
                        divided
                        :command="{action: 'delete', server: row}"
                      >
                        <el-icon><Delete /></el-icon>
                        删除
                      </el-dropdown-item>
                    </el-dropdown-menu>
                  </template>
                </el-dropdown>
              </template>
            </el-table-column>
          </el-table>
        </div>
        
        <!-- 分页 -->
        <div class="pagination-wrapper">
          <el-pagination
            v-model:current-page="pagination.currentPage"
            v-model:page-size="pagination.pageSize"
            :page-sizes="[12, 24, 48]"
            :total="pagination.total"
            layout="total, sizes, prev, pager, next, jumper"
            @size-change="handleSizeChange"
            @current-change="handleCurrentChange"
          />
        </div>
      </el-card>
    </div>

    <!-- 创建/编辑服务器对话框 -->
    <el-dialog
      v-model="dialogVisible"
      :title="dialogMode === 'create' ? '添加服务器' : '编辑服务器'"
      width="600px"
      @close="resetForm"
    >
      <el-form
        ref="formRef"
        :model="formData"
        :rules="formRules"
        label-width="100px"
      >
        <el-form-item label="服务器名称" prop="name">
          <el-input v-model="formData.name" placeholder="请输入服务器名称" />
        </el-form-item>
        
        <el-form-item label="IP地址或域名" prop="ip_address">
          <el-input v-model="formData.ip_address" placeholder="请输入IP或域名" />
        </el-form-item>
        
        <el-form-item label="SSH端口" prop="ssh_port">
          <el-input-number
            v-model="formData.ssh_port"
            :min="1"
            :max="65535"
            style="width: 100%"
          />
        </el-form-item>
        
        <el-form-item label="SSH用户名" prop="ssh_username">
          <el-input v-model="formData.ssh_username" placeholder="请输入SSH用户名" />
        </el-form-item>

        <el-form-item label="SSH密码" prop="ssh_password">
          <el-input 
            v-model="formData.ssh_password" 
            type="password" 
            placeholder="请输入SSH密码" 
            show-password 
          />
        </el-form-item>
        
        <el-form-item label="SSH密钥路径" prop="ssh_key_path">
          <el-input v-model="formData.ssh_key_path" placeholder="如: ~/.ssh/id_rsa" />
        </el-form-item>
        
        <el-form-item label="服务器类型" prop="server_type">
          <el-select v-model="formData.server_type" style="width: 100%">
            <el-option label="物理机" value="physical" />
            <el-option label="虚拟机" value="virtual" />
            <el-option label="云服务器" value="cloud" />
          </el-select>
        </el-form-item>
        
        <el-form-item label="操作系统" prop="os_info">
          <el-input v-model="formData.os_info" placeholder="如: Ubuntu 22.04 LTS" />
        </el-form-item>
        
        <el-form-item label="总内存" prop="total_memory">
          <el-input v-model="formData.total_memory" placeholder="如: 128GB" />
        </el-form-item>
        
        <el-form-item label="总存储" prop="total_storage">
          <el-input v-model="formData.total_storage" placeholder="如: 2TB" />
        </el-form-item>
        
        <el-form-item label="CPU核心数" prop="total_cpu_cores">
          <el-input-number
            v-model="formData.total_cpu_cores"
            :min="1"
            style="width: 100%"
          />
        </el-form-item>
      </el-form>
      
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="dialogVisible = false">取消</el-button>
          <el-button type="primary" @click="submitForm" :loading="submitting">
            {{ dialogMode === 'create' ? '创建' : '更新' }}
          </el-button>
        </span>
      </template>
    </el-dialog>

    <!-- GPU资源对话框 -->
    <el-dialog
      v-model="gpuDialogVisible"
      title="GPU资源管理"
      width="800px"
    >
      <div class="gpu-section">
        <div class="gpu-header">
          <h4>{{ currentServer?.name }} - GPU资源</h4>
          <el-button size="small" @click="scanGpus">
            <el-icon><Refresh /></el-icon>
            扫描GPU
          </el-button>
        </div>
        
        <div v-if="gpuResources.length === 0" class="no-gpus">
          <el-empty description="暂无GPU资源" />
        </div>
        
        <div v-else class="gpu-list">
          <div
            v-for="gpu in gpuResources"
            :key="gpu.id"
            class="gpu-item"
          >
            <div class="gpu-info">
              <div class="gpu-name">{{ gpu.gpu_name }}</div>
              <div class="gpu-details">
                <span>类型: {{ gpu.gpu_type || '未知' }}</span>
                <span>显存: {{ gpu.memory_size || '未知' }}</span>
                <span>CUDA: {{ gpu.cuda_version || '未知' }}</span>
                <span>设备ID: {{ gpu.device_id || '未知' }}</span>
              </div>
            </div>
            <div class="gpu-status">
              <el-tag :type="gpu.is_available ? 'success' : 'danger'">
                {{ gpu.is_available ? '可用' : '占用中' }}
              </el-tag>
            </div>
          </div>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox, ElTable } from 'element-plus'
import { getServers, createServer, updateServer, deleteServer, getServerStats, getServerGpuResources, scanServerGpus, testServerConnection } from '@/api/servers'

import {
  Monitor,
  Plus,
  Refresh,
  Search,
  CircleCheckFilled,
  CircleCloseFilled,
  WarningFilled,
  VideoCamera,
  Connection,
  MoreFilled,
  Edit,
  Delete,
  TrendCharts,
  Grid,
  List
} from '@element-plus/icons-vue'

// 路由实例
const router = useRouter()

// 响应式数据
const searchQuery = ref('')
const filterType = ref('')
const filterStatus = ref('')
const dialogVisible = ref(false)
const gpuDialogVisible = ref(false)
const dialogMode = ref<'create' | 'edit'>('create')
const submitting = ref(false)
const currentServer = ref<any>(null)
const serverId = ref<number>(0)
const viewMode = ref('grid')

// 分页
const pagination = reactive({
  currentPage: 1,
  pageSize: 12,
  total: 0
})

// 统计数据
const stats = reactive({
  total: 0,
  online: 0,
  offline: 0,
  totalGpus: 0
})

// 服务器列表
const servers = ref<any[]>([])
const gpuResources = ref<any[]>([])

// 表单数据
const formData = reactive({
  name: '',
  ip_address: '',
  ssh_port: 22,
  ssh_username: '',
  ssh_password:'',
  ssh_key_path: '',
  server_type: 'physical',
  os_info: '',
  total_memory: '',
  total_storage: '',
  total_cpu_cores: null
})

// 表单验证规则
const validateIpOrDomain = (rule: any, value: string, callback: (error?: Error) => void) => {
  const v = (value || '').trim()
  const hasProtocol = v.includes('://')
  const hasSlash = v.includes('/')
  const hasPort = v.includes(':')
  const ipv4 = /^(25[0-5]|2[0-4]\d|1\d{2}|[1-9]?\d)(\.(25[0-5]|2[0-4]\d|1\d{2}|[1-9]?\d)){3}$/
  const hostname = /^(localhost|(?:[a-zA-Z0-9-]{1,63}\.)+[a-zA-Z]{2,63})$/
  if (!v) return callback(new Error('请输入IP或域名'))
  if (hasProtocol || hasSlash || hasPort) return callback(new Error('请不要包含协议、路径或端口'))
  if (ipv4.test(v) || hostname.test(v)) return callback()
  return callback(new Error('请输入有效的IP或域名'))
}

const formRules = {
  name: [{ required: true, message: '请输入服务器名称', trigger: 'blur' }],
  ip_address: [
    { required: true, message: '请输入IP或域名', trigger: 'blur' },
    { validator: validateIpOrDomain, trigger: 'blur' }
  ],
  ssh_port: [{ required: true, message: '请输入SSH端口', trigger: 'blur' }],
  server_type: [{ required: true, message: '请选择服务器类型', trigger: 'change' }]
}

const formRef = ref()

// 计算属性
const filteredServers = computed(() => {
  return servers.value.filter(server => {
    const matchesSearch = !searchQuery.value || 
      server.name.toLowerCase().includes(searchQuery.value.toLowerCase()) ||
      server.ip_address.includes(searchQuery.value)
    
    const matchesType = !filterType.value || server.server_type === filterType.value
    const matchesStatus = !filterStatus.value || server.status === filterStatus.value
    
    return matchesSearch && matchesType && matchesStatus
  })
})

// 方法
// 新增：独立统计数据获取方法，保证与列表查询解耦
const fetchStats = async () => {
  try {
    const statsResponse = await getServerStats()
    console.log('服务器统计数据:', statsResponse)
    const s = (statsResponse && (statsResponse as any).data) ? (statsResponse as any).data : statsResponse
    stats.total = (s as any)?.total ?? 0
    stats.online = (s as any)?.online ?? 0
    stats.offline = (s as any)?.offline ?? 0
    stats.totalGpus = (s as any)?.total_gpus ?? 0
  } catch (error) {
    console.error('获取服务器统计数据失败:', error)
  }
}

const loadServers = async (opts?: { fetchStats?: boolean }) => {
  try {
    // 根据选项决定是否刷新统计
    if ((opts?.fetchStats ?? true) === true) {
      await fetchStats()
    }

    // 获取分页列表数据（携带查询参数）
    const params = {
      page: pagination.currentPage,
      size: pagination.pageSize,
      search: (searchQuery.value?.trim() || undefined),
      server_type: (filterType.value || undefined),
      status: (filterStatus.value || undefined)
    }
    console.log('列表查询参数:', params)

    const response = await getServers(params)
    console.log('服务器列表数据:', response)

    // 适配多种可能的API响应结构
    let serverList = []
    if (response.data?.items) {
      serverList = response.data.items
    } else if (Array.isArray(response.data)) {
      serverList = response.data
    } else if (response.items) {
      serverList = response.items
    } else if (response.data?.data) {
      serverList = response.data.data
    }

    console.log('解析后的服务器列表:', serverList)
    servers.value = serverList || []

    // 如果有分页信息，使用分页总数
    pagination.total = response.data?.total || response.total || serverList?.length || 0
  } catch (error) {
    ElMessage.error('加载服务器列表失败')
    console.error('加载服务器列表错误:', error)
  }
}

const handleSearch = () => {
  pagination.currentPage = 1
  // 只刷新列表，不刷新统计
  loadServers({ fetchStats: false })
}

const handleFilter = () => {
  pagination.currentPage = 1
  // 只刷新列表，不刷新统计
  loadServers({ fetchStats: false })
}

const refreshServers = () => {
  // 刷新按钮完整刷新统计与列表
  loadServers({ fetchStats: true })
}

// 生命周期
onMounted(() => {
  // 首次进入页面，获取统计与列表
  loadServers({ fetchStats: true })
})

const showCreateDialog = () => {
  dialogMode.value = 'create'
  resetForm()
  dialogVisible.value = true
}

const resetForm = () => {
  Object.assign(formData, {
    name: '',
    ip_address: '',
    ssh_port: 22,
    ssh_username: '',
    ssh_password: '',
    ssh_key_path: '',
    server_type: 'physical',
    os_info: '',
    total_memory: '',
    total_storage: '',
    total_cpu_cores: null
  })
  formRef.value?.clearValidate()
}

const submitForm = async () => {
  try {
    await formRef.value?.validate()
    submitting.value = true
    
    if (dialogMode.value === 'create') {
      await createServer(formData) // 传递 reactive 对象本身
    } else {
      await updateServer(serverId.value, formData)
    }
    
    ElMessage.success(dialogMode.value === 'create' 
      ? '服务器创建成功' 
      : '服务器更新成功'
    )
    dialogVisible.value = false
    loadServers() // 刷新列表
  } catch (error) {
    ElMessage.error('操作失败：' + (error.response?.data?.message || error.message))
  } finally {
    submitting.value = false
  }
}


const testConnection = async (server: any) => {
  server.testing = true
  try {
    // 调用API测试连接
    const response = await testServerConnection(server.id)
    
    // 直接使用响应中的数据，不需要通过response.data访问
    if (response.status === 'success') {
      ElMessage.success(response.message || '连接测试成功')
      server.status = 'online'
    } else {
      ElMessage.error(`连接测试失败: ${response.message || '未知错误'}`)
      server.status = 'offline'
    }
  } catch (error: any) {
    ElMessage.error(`连接测试失败: ${error.response?.data?.message || error.message || '未知错误'}`)
    server.status = 'offline'
  } finally {
    server.testing = false
  }
}

const viewGpus = (server: any) => {
  currentServer.value = server
  loadGpuResources(server.id)
  gpuDialogVisible.value = true
}

const loadGpuResources = async (serverId: number) => {
  try {
    const res: any = await getServerGpuResources(serverId)
    const list = Array.isArray(res?.data) ? res.data : (Array.isArray(res) ? res : [])
    gpuResources.value = list || []
  } catch (error: any) {
    console.error('加载GPU资源失败:', error)
    ElMessage.error(error?.response?.data?.message || '加载GPU资源失败')
  }
}

const scanGpus = async () => {
  try {
    const serverId = currentServer.value?.id
    if (!serverId) {
      ElMessage.warning('请先选择服务器')
      return
    }
    const res: any = await scanServerGpus(serverId)
    const list = Array.isArray(res?.data) ? res.data : (Array.isArray(res) ? res : [])
    gpuResources.value = list || []
    ElMessage.success('GPU扫描完成')
  } catch (error: any) {
    console.error('GPU扫描失败:', error)
    ElMessage.error(error?.response?.data?.message || 'GPU扫描失败')
  }
}

const handleServerAction = async ({ action, server }: any) => {
  switch (action) {
    case 'edit':
      dialogMode.value = 'edit'
      serverId.value = server.id
      Object.assign(formData, server)
      dialogVisible.value = true
      break
    case 'monitor':
      // 跳转到监控页面
      router.push('/monitoring')
      break
    case 'scan':
      currentServer.value = server
      await scanGpus()
      break
    case 'delete':
      try {
        await ElMessageBox.confirm('确定要删除这个服务器吗？', '确认删除', {
          type: 'warning'
        })
        await deleteServer(server.id)
        ElMessage.success('服务器删除成功')
        loadServers()
      } catch (error) {
        if (error !== 'cancel') {
          ElMessage.error('删除服务器失败')
        }
      }
      break
  }
}

const viewServerDetail = (server: any) => {
  // TODO: 跳转到服务器详情页面
  console.log('查看服务器详情:', server)
}

// 新增：重置搜索与筛选
const resetSearch = () => {
  searchQuery.value = ''
  filterType.value = ''
  filterStatus.value = ''
  pagination.currentPage = 1
  loadServers()
}

const handleSizeChange = (size: number) => {
  pagination.pageSize = size
  loadServers({ fetchStats: false })
}

const handleCurrentChange = (page: number) => {
  pagination.currentPage = page
  loadServers({ fetchStats: false })
}

const getStatusText = (status: string) => {
  const statusMap: Record<string, string> = {
    online: '在线',
    offline: '离线',
    maintenance: '维护中'
  }
  return statusMap[status] || status
}

const getTypeText = (type: string) => {
  const typeMap: Record<string, string> = {
    physical: '物理机',
    virtual: '虚拟机',
    cloud: '云服务器'
  }
  return typeMap[type] || type
}

// 生命周期（已上移并统一为加载统计+列表）
</script>

<style scoped>
.servers-page {
  padding: 20px;
}

.page-header {
  margin-bottom: 24px;
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.page-title {
  margin: 0;
  font-size: 24px;
  font-weight: 600;
  color: #1f2937;
  display: flex;
  align-items: center;
  gap: 8px;
}

.page-description {
  margin: 4px 0 0 0;
  color: #6b7280;
  font-size: 14px;
}

.header-right {
  display: flex;
  gap: 12px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-weight: 600;
}

.header-actions {
  display: flex;
  gap: 12px;
}

.stats-section {
  margin-bottom: 24px;
}

.stat-card {
  background: white;
  border-radius: 12px;
  padding: 20px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  display: flex;
  align-items: center;
  gap: 16px;
  transition: all 0.3s ease;
}

.stat-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.stat-icon {
  width: 48px;
  height: 48px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
  color: white;
}

.stat-icon.total {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.stat-icon.online {
  background: linear-gradient(135deg, #4ade80 0%, #22c55e 100%);
}

.stat-icon.offline {
  background: linear-gradient(135deg, #f87171 0%, #ef4444 100%);
}

.stat-icon.gpus {
  background: linear-gradient(135deg, #fbbf24 0%, #f59e0b 100%);
}

.stat-content {
  flex: 1;
}

.stat-value {
  font-size: 28px;
  font-weight: 700;
  color: #1f2937;
  line-height: 1;
}

.stat-label {
  font-size: 14px;
  color: #6b7280;
  margin-top: 4px;
}

.search-section {
  margin-bottom: 24px;
}

.servers-section {
  margin-bottom: 24px;
}

.grid-view .servers-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(400px, 1fr));
  gap: 20px;
  margin-bottom: 24px;
}

.list-view {
  margin-bottom: 24px;
}

.server-name-cell {
  display: flex;
  align-items: center;
}

.server-name-cell .server-info .name {
  font-weight: 600;
  color: #1f2937;
  margin-bottom: 2px;
}

.server-name-cell .server-info .ip {
  font-size: 12px;
  color: #6b7280;
}

.server-card {
  background: white;
  border-radius: 12px;
  padding: 20px;
  border: 1px solid #e5e7eb;
  transition: all 0.3s ease;
  cursor: pointer;
}

.server-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  border-color: #3b82f6;
}

.server-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 16px;
}

.server-name {
  font-size: 18px;
  font-weight: 600;
  color: #1f2937;
  margin-bottom: 4px;
}

.server-ip {
  font-size: 14px;
  color: #6b7280;
  font-family: 'Monaco', 'Menlo', monospace;
}

.server-status {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  font-weight: 500;
  padding: 4px 8px;
  border-radius: 6px;
}

.server-status.online {
  color: #059669;
  background: #d1fae5;
}

.server-status.offline {
  color: #dc2626;
  background: #fee2e2;
}

.server-status.maintenance {
  color: #d97706;
  background: #fef3c7;
}

.server-details {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 8px;
  margin-bottom: 16px;
}

.detail-item {
  display: flex;
  justify-content: space-between;
  font-size: 14px;
}

.detail-item .label {
  color: #6b7280;
}

.detail-item .value {
  color: #1f2937;
  font-weight: 500;
}

.server-actions {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.pagination-wrapper {
  display: flex;
  justify-content: center;
  margin-top: 24px;
}

.gpu-section {
  max-height: 400px;
  overflow-y: auto;
}

.gpu-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  padding-bottom: 12px;
  border-bottom: 1px solid #e5e7eb;
}

.gpu-header h4 {
  margin: 0;
  color: #1f2937;
}

.no-gpus {
  text-align: center;
  padding: 40px 0;
}

.gpu-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.gpu-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px;
  background: #f9fafb;
  border-radius: 8px;
  border: 1px solid #e5e7eb;
}

.gpu-info {
  flex: 1;
}

.gpu-name {
  font-weight: 600;
  color: #1f2937;
  margin-bottom: 4px;
}

.gpu-details {
  display: flex;
  gap: 16px;
  font-size: 12px;
  color: #6b7280;
}

.gpu-status {
  margin-left: 16px;
}

@media (max-width: 768px) {
  .servers-grid {
    grid-template-columns: 1fr;
  }
  
  .server-details {
    grid-template-columns: 1fr;
  }
  
  .gpu-details {
    flex-direction: column;
    gap: 4px;
  }
}
</style>