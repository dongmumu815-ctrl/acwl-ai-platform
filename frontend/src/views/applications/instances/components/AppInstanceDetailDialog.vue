<template>
  <el-dialog
    v-model="visible"
    title="应用实例详情"
    width="900px"
    destroy-on-close
    @open="fetchDetail"
  >
    <div v-loading="loading" class="detail-container">
      <div v-if="instance" class="header-info">
        <div class="app-icon">
          <el-image v-if="instance.template?.icon" :src="instance.template.icon" style="width: 64px; height: 64px" />
          <div v-else class="default-icon">{{ instance.name.charAt(0).toUpperCase() }}</div>
        </div>
        <div class="basic-info">
          <div class="flex justify-between items-start">
            <h3>{{ instance.name }}</h3>
            <div class="actions">
              <template v-if="!isEdit">
                <el-button type="primary" link @click="startEdit">编辑部署</el-button>
              </template>
              <template v-else>
                <el-button type="default" size="small" @click="cancelEdit">取消</el-button>
                <el-button type="primary" size="small" @click="saveEdit">保存变更</el-button>
              </template>
            </div>
          </div>
          <p class="text-gray">
            模板: {{ instance.template?.display_name || instance.template?.name || '未知' }} 
            <el-tag size="small" type="info">v{{ instance.template?.version || 'latest' }}</el-tag>
          </p>
          <div class="status-row">
            <el-tag :type="getStatusType(instance.status)">{{ instance.status }}</el-tag>
            <span class="time-info">创建于: {{ formatDateTime(instance.created_at) }}</span>
          </div>
        </div>
      </div>

      <el-tabs v-if="instance" v-model="activeTab" class="mt-4">
        <el-tab-pane label="部署详情" name="deployments">
          <div v-if="isEdit" class="mb-2">
            <el-button type="primary" plain size="small" @click="openAddNode">
              <el-icon><Plus /></el-icon> 添加节点
            </el-button>
            <el-alert title="保存后将自动触发：新增节点的安装、移除节点的卸载以及现有节点的配置更新。" type="info" show-icon :closable="false" class="mt-2" />
          </div>
          
          <el-table :data="isEdit ? editDeployments : (instance.deployments || [])" border stripe>
            <el-table-column label="服务器ID" prop="server_id" width="100" />
            <el-table-column label="服务器名称" min-width="120">
              <template #default="{ row }">
                <span v-if="isEdit">{{ getServerName(row.server_id) }}</span>
                <span v-else>
                  <template v-if="row.server">
                    {{ row.server.name }} ({{ row.server.ip_address }})
                  </template>
                  <template v-else>
                    {{ row.server_id }}
                  </template>
                </span>
              </template>
            </el-table-column>
            <el-table-column label="角色" prop="role" width="100">
              <template #default="{ row }">
                <el-input v-if="isEdit" v-model="row.role" size="small" />
                <span v-else>{{ row.role }}</span>
              </template>
            </el-table-column>
            <el-table-column label="状态" prop="status" width="100">
              <template #default="{ row }">
                <el-popover
                  v-if="row.status === 'error' && row.error_message"
                  placement="top"
                  title="错误详情"
                  :width="400"
                  trigger="hover"
                >
                  <template #reference>
                    <el-tag :type="getStatusType(row.status)" size="small" style="cursor: pointer">
                      {{ row.status }} <el-icon><Warning /></el-icon>
                    </el-tag>
                  </template>
                  <div class="error-log">
                    {{ row.error_message }}
                  </div>
                </el-popover>
                <el-tag v-else :type="getStatusType(row.status)" size="small">{{ row.status }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column label="资源限制" min-width="180">
              <template #default="{ row }">
                <div v-if="isEdit" class="flex gap-2">
                  <el-input v-model="row.cpu_limit" placeholder="CPU" size="small" style="width: 80px" />
                  <el-input v-model="row.mem_limit" placeholder="Mem" size="small" style="width: 80px" />
                </div>
                <div v-else class="resource-tags">
                  <el-tag v-if="row.cpu_limit" size="small" type="info" effect="plain">CPU: {{ row.cpu_limit }}</el-tag>
                  <el-tag v-if="row.mem_limit" size="small" type="info" effect="plain">Mem: {{ row.mem_limit }}</el-tag>
                </div>
              </template>
            </el-table-column>
            <el-table-column v-if="isEdit" label="操作" width="80" fixed="right">
              <template #default="{ $index }">
                <el-button type="danger" link size="small" @click="removeDeployment($index)">移除</el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-tab-pane>

        <el-tab-pane label="配置信息" name="config">
          <div class="config-viewer">
            <h4>实例配置</h4>
            <pre class="code-block">{{ JSON.stringify(instance.config, null, 2) }}</pre>
            
            <h4 class="mt-4">描述</h4>
            <p>{{ instance.description || '无描述' }}</p>
          </div>
        </el-tab-pane>
      </el-tabs>
    </div>
    
    <template #footer>
      <span class="dialog-footer">
        <el-button @click="visible = false">关闭</el-button>
        <el-button type="primary" @click="fetchDetail" :loading="loading">刷新</el-button>
      </span>
    </template>

    <!-- 添加节点弹窗 -->
    <el-dialog
      v-model="addNodeDialogVisible"
      title="添加部署节点"
      width="500px"
      append-to-body
    >
      <el-form :model="newNodeForm" label-width="100px">
        <el-form-item label="选择服务器" required>
          <el-select v-model="newNodeForm.server_id" placeholder="请选择服务器" style="width: 100%" filterable>
            <el-option
              v-for="server in serverList"
              :key="server.id"
              :label="`${server.name} (${server.ip_address})`"
              :value="server.id"
              :disabled="editDeployments.some(d => d.server_id === server.id)"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="节点角色">
          <el-input v-model="newNodeForm.role" placeholder="例如: worker, master" />
        </el-form-item>
        <el-form-item label="CPU限制">
          <el-input v-model="newNodeForm.cpu_limit" placeholder="例如: 2.0, 500m" />
        </el-form-item>
        <el-form-item label="内存限制">
          <el-input v-model="newNodeForm.mem_limit" placeholder="例如: 1G, 512M" />
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="addNodeDialogVisible = false">取消</el-button>
          <el-button type="primary" @click="confirmAddNode">确定</el-button>
        </span>
      </template>
    </el-dialog>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { getAppInstance, updateAppInstance, type AppInstance } from '@/api/application'
import { getServers } from '@/api/servers'
import { formatDateTime } from '@/utils/date'
import { ElMessage } from 'element-plus'
import { Plus, Warning } from '@element-plus/icons-vue'

const props = defineProps<{
  modelValue: boolean
  instanceId?: number
}>()

const emit = defineEmits(['update:modelValue'])

const visible = computed({
  get: () => props.modelValue,
  set: (val) => emit('update:modelValue', val)
})

const loading = ref(false)
const instance = ref<AppInstance | null>(null)
const activeTab = ref('deployments')

// Edit Mode State
const isEdit = ref(false)
const editDeployments = ref<any[]>([])
const serverList = ref<any[]>([])
const addNodeDialogVisible = ref(false)
const newNodeForm = ref({
  server_id: undefined as number | undefined,
  role: 'default',
  cpu_limit: '',
  mem_limit: ''
})

const getStatusType = (status: string) => {
  switch (status) {
    case 'running': return 'success'
    case 'installing': return 'primary'
    case 'stopped': return 'info'
    case 'error': return 'danger'
    default: return 'info'
  }
}

const fetchDetail = async () => {
  if (!props.instanceId) return
  
  loading.value = true
  // Reset edit mode on refresh
  isEdit.value = false
  
  try {
    const res = await getAppInstance(props.instanceId)
    instance.value = res
  } catch (error) {
    console.error(error)
    ElMessage.error('获取详情失败')
  } finally {
    loading.value = false
  }
}

// Edit Actions
const startEdit = async () => {
  if (!instance.value) return
  editDeployments.value = JSON.parse(JSON.stringify(instance.value.deployments || []))
  isEdit.value = true
  
  // Load servers if empty
  if (serverList.value.length === 0) {
    try {
      const res = await getServers({ page: 1, size: 100 })
      serverList.value = res.items || []
    } catch (e) {
      console.error(e)
    }
  }
}

const cancelEdit = () => {
  isEdit.value = false
  editDeployments.value = []
}

const saveEdit = async () => {
  if (!instance.value) return
  loading.value = true
  try {
    const deployments = editDeployments.value.map(d => ({
      server_id: d.server_id,
      role: d.role,
      cpu_limit: d.cpu_limit,
      mem_limit: d.mem_limit,
      ports: d.ports
    }))
    
    await updateAppInstance(instance.value.id, { deployments })
    ElMessage.success('更新成功，后台正在重新部署')
    isEdit.value = false
    await fetchDetail()
  } catch (e) {
    console.error(e)
    ElMessage.error('更新失败')
  } finally {
    loading.value = false
  }
}

const removeDeployment = (index: number) => {
  editDeployments.value.splice(index, 1)
}

const openAddNode = () => {
  newNodeForm.value = { server_id: undefined, role: 'default', cpu_limit: '', mem_limit: '' }
  addNodeDialogVisible.value = true
}

const confirmAddNode = () => {
  if (!newNodeForm.value.server_id) {
    ElMessage.warning('请选择服务器')
    return
  }
  if (editDeployments.value.some(d => d.server_id === newNodeForm.value.server_id)) {
    ElMessage.warning('该服务器已存在')
    return
  }
  
  editDeployments.value.push({
    ...newNodeForm.value,
    status: 'pending',
    container_id: ''
  })
  addNodeDialogVisible.value = false
}

const getServerName = (id: number) => {
  const s = serverList.value.find(s => s.id === id)
  return s ? `${s.name} (${s.ip_address})` : `Server ${id}`
}

const getPortInfo = (row: any) => {
  if (!instance.value) return '-'
  
  // 1. 优先使用部署记录中的端口信息 (如果有)
  if (row.ports && Object.keys(row.ports).length > 0) {
     // 尝试解析 ports，假设格式为 { "容器端口": "主机端口" } 或类似
     // 这里我们简单处理，展示键值对
     return Object.entries(row.ports)
       .map(([k, v]) => `${v}:${k}`)
       .join(', ')
  }

  // 2. 尝试从配置中解析
  const config = instance.value.config || {}
  
  // 获取当前部署的 server_id
  const serverId = row.server_id
  
  // 确定生效的配置
  let effectiveConfig: any = { ...config }
  
  // 处理 global/overrides 结构
  if ('global' in config || 'overrides' in config) {
    const globalConfig = config.global || {}
    // @ts-ignore
    const overrideConfig = (config.overrides || {})[String(serverId)] || {}
    effectiveConfig = { ...globalConfig, ...overrideConfig }
  }
  
  // 查找可能的端口字段
  // 目前已知 Harbor 模板使用了 http_port
  if (effectiveConfig.http_port) {
    return `${effectiveConfig.http_port}:80`
  }
  
  // 也可以查找其他常见的端口字段
  if (effectiveConfig.port) {
    return `${effectiveConfig.port}`
  }

  return '-'
}
</script>

<style scoped>
.detail-container {
  min-height: 300px;
}

.header-info {
  display: flex;
  gap: 20px;
  padding-bottom: 20px;
  border-bottom: 1px solid #eee;
}

.app-icon {
  width: 64px;
  height: 64px;
  border-radius: 8px;
  overflow: hidden;
  background-color: #f5f7fa;
  display: flex;
  align-items: center;
  justify-content: center;
}

.default-icon {
  font-size: 32px;
  color: #909399;
  font-weight: bold;
}

.basic-info h3 {
  margin: 0 0 8px 0;
  font-size: 18px;
}

.text-gray {
  color: #666;
  margin: 0 0 8px 0;
  font-size: 14px;
}

.status-row {
  display: flex;
  align-items: center;
  gap: 12px;
}

.time-info {
  font-size: 12px;
  color: #999;
}

.mt-4 {
  margin-top: 16px;
}

.code-block {
  background-color: #f5f7fa;
  padding: 12px;
  border-radius: 4px;
  font-family: monospace;
  font-size: 13px;
  overflow-x: auto;
  border: 1px solid #ebeef5;
}

.resource-tags {
  display: flex;
  gap: 4px;
  flex-wrap: wrap;
}

.error-log {
  white-space: pre-wrap;
  word-break: break-all;
  max-height: 200px;
  overflow-y: auto;
  font-family: monospace;
  font-size: 12px;
  color: #f56c6c;
}

.font-mono {
  font-family: monospace;
}
</style>