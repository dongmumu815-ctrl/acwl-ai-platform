<template>
  <div class="instances-page">
    <div class="page-header">
      <div class="header-left">
        <h2>已安装应用</h2>
        <p class="description">管理已部署的应用实例，查看运行状态和执行维护操作。</p>
      </div>
      <div class="header-right">
        <el-button @click="fetchData">
          <el-icon><Refresh /></el-icon>
          刷新
        </el-button>
      </div>
    </div>

    <div class="table-container">
      <el-table :data="tableData" v-loading="loading" style="width: 100%" row-key="id">
        <el-table-column type="expand">
          <template #default="{ row }">
            <div class="deployments-list">
              <h4>部署节点详情</h4>
              <el-table :data="row.deployments" border size="small">
                <el-table-column label="服务器ID" prop="server_id" width="100" />
                <!-- In a real app, we would join server name here. For now just ID is shown unless we map it -->
                <el-table-column label="角色" prop="role" width="120" />
                <el-table-column label="状态" prop="status" width="120">
                  <template #default="{ row: dRow }">
                    <el-tag :type="getStatusType(dRow.status)">{{ dRow.status }}</el-tag>
                  </template>
                </el-table-column>
                <el-table-column label="资源限制">
                  <template #default="{ row: dRow }">
                    <span v-if="dRow.cpu_limit">CPU: {{ dRow.cpu_limit }}</span>
                    <span v-if="dRow.mem_limit" style="margin-left: 8px">Mem: {{ dRow.mem_limit }}</span>
                  </template>
                </el-table-column>
                <el-table-column label="容器ID" prop="container_id" min-width="180">
                  <template #default="{ row: dRow }">
                    <div v-if="dRow.container_id">
                      <div v-for="(id, idx) in dRow.container_id.split(',')" :key="idx" class="mb-1 last:mb-0">
                        <template v-if="id.includes(':')">
                          <el-tag size="small" type="info" class="mr-1">{{ id.split(':')[0] }}</el-tag>
                          <span class="text-xs font-mono">{{ id.split(':')[1] }}</span>
                        </template>
                        <template v-else>
                          <span class="text-xs font-mono">{{ id }}</span>
                        </template>
                      </div>
                    </div>
                  </template>
                </el-table-column>
              </el-table>
            </div>
          </template>
        </el-table-column>
        
        <el-table-column prop="name" label="实例名称" min-width="150">
          <template #default="{ row }">
            <span style="font-weight: 500">{{ row.name }}</span>
          </template>
        </el-table-column>
        
        <el-table-column label="应用模板" min-width="150">
          <template #default="{ row }">
            <div v-if="row.template" class="template-info">
              <el-image v-if="row.template.icon" :src="row.template.icon" class="small-icon" />
              <span>{{ row.template.display_name || row.template.name }} (v{{ row.template.version }})</span>
            </div>
            <span v-else class="text-gray">未知模板</span>
          </template>
        </el-table-column>
        
        <el-table-column prop="status" label="状态" width="120">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)">{{ row.status }}</el-tag>
          </template>
        </el-table-column>
        
        <el-table-column label="部署规模" width="120">
          <template #default="{ row }">
            <el-tag effect="plain" type="info">{{ row.deployments?.length || 0 }} 节点</el-tag>
          </template>
        </el-table-column>
        
        <el-table-column prop="created_at" label="创建时间" width="180">
          <template #default="{ row }">
            {{ formatDateTime(row.created_at) }}
          </template>
        </el-table-column>
        
        <el-table-column label="操作" width="150" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="handleDetail(row)">详情</el-button>
            <el-button link type="danger" @click="handleDelete(row)">卸载</el-button>
          </template>
        </el-table-column>
      </el-table>

      <div class="pagination-container">
        <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.size"
          :total="pagination.total"
          :page-sizes="[10, 20, 50, 100]"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="fetchData"
          @current-change="fetchData"
        />
      </div>
    </div>

    <!-- 详情弹窗 -->
    <AppInstanceDetailDialog
      v-model="detailVisible"
      :instance-id="currentInstanceId"
    />

    <!-- 卸载确认弹窗 -->
    <el-dialog
      v-model="uninstallDialogVisible"
      title="确认卸载应用"
      width="400px"
      :close-on-click-modal="false"
    >
      <div class="uninstall-confirm-content">
        <p class="warning-text">
          <el-icon class="warning-icon"><WarningFilled /></el-icon>
          确定要卸载应用 "{{ uninstallInstance?.name }}" 吗？
        </p>
        <p class="desc-text">此操作将停止并删除所有关联的容器。</p>
        
        <div class="clean-data-option">
          <el-checkbox v-model="uninstallCleanData">
            同时清理数据目录 (危险)
          </el-checkbox>
          <p class="option-desc" v-if="uninstallCleanData">
            将会删除服务器上的数据挂载目录，此操作不可恢复！
          </p>
        </div>
      </div>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="uninstallDialogVisible = false">取消</el-button>
          <el-button type="danger" @click="confirmUninstall" :loading="uninstallLoading">
            确定卸载
          </el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Refresh, WarningFilled } from '@element-plus/icons-vue'
import { getAppInstances, deleteAppInstance } from '@/api/application'
import type { AppInstance } from '@/api/application'
import { formatDateTime } from '@/utils/date'
import AppInstanceDetailDialog from './components/AppInstanceDetailDialog.vue'

const loading = ref(false)
const tableData = ref<AppInstance[]>([])
const pagination = reactive({
  page: 1,
  size: 20,
  total: 0
})
const detailVisible = ref(false)
const currentInstanceId = ref<number | undefined>(undefined)

const uninstallDialogVisible = ref(false)
const uninstallInstance = ref<AppInstance | null>(null)
const uninstallCleanData = ref(false)
const uninstallLoading = ref(false)

const getStatusType = (status: string) => {
  switch (status) {
    case 'running': return 'success'
    case 'installing': return 'primary'
    case 'stopped': return 'info'
    case 'error': return 'danger'
    default: return 'info'
  }
}

const fetchData = async () => {
  loading.value = true
  try {
    const res = await getAppInstances({
      page: pagination.page,
      size: pagination.size
    })
    tableData.value = res.items
    pagination.total = res.total
  } catch (error) {
    console.error(error)
  } finally {
    loading.value = false
  }
}

const handleDetail = (row: AppInstance) => {
  currentInstanceId.value = row.id
  detailVisible.value = true
}

const handleDelete = (row: AppInstance) => {
  uninstallInstance.value = row
  uninstallCleanData.value = false
  uninstallDialogVisible.value = true
}

const confirmUninstall = async () => {
  if (!uninstallInstance.value) return
  
  uninstallLoading.value = true
  try {
    await deleteAppInstance(uninstallInstance.value.id, uninstallCleanData.value)
    ElMessage.success('卸载任务已提交')
    uninstallDialogVisible.value = false
    fetchData()
  } catch (error) {
    console.error(error)
  } finally {
    uninstallLoading.value = false
  }
}

onMounted(() => {
  fetchData()
})
</script>

<style scoped>
.instances-page {
  padding: 20px;
  background-color: #fff;
  height: 100%;
  display: flex;
  flex-direction: column;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 20px;
}

.header-left h2 {
  margin: 0 0 8px 0;
  font-size: 20px;
  font-weight: 500;
}

.description {
  color: #666;
  font-size: 14px;
  margin: 0;
}

.table-container {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.pagination-container {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
}

.deployments-list {
  padding: 10px 20px 20px;
  background-color: #f8f9fa;
}

.deployments-list h4 {
  margin: 0 0 10px 0;
  font-size: 14px;
  color: #606266;
}

.template-info {
  display: flex;
  align-items: center;
  gap: 8px;
}

.small-icon {
  width: 20px;
  height: 20px;
}

.text-gray {
  color: #909399;
}

.uninstall-confirm-content {
  padding: 10px 0;
}
.warning-text {
  display: flex;
  align-items: center;
  font-size: 16px;
  color: #303133;
  margin-bottom: 10px;
}
.warning-icon {
  color: #E6A23C;
  margin-right: 8px;
  font-size: 20px;
}
.desc-text {
  color: #606266;
  margin-bottom: 20px;
  padding-left: 28px;
}
.clean-data-option {
  margin-top: 20px;
  padding: 15px;
  background-color: #fef0f0;
  border-radius: 4px;
  border: 1px solid #fde2e2;
}
.option-desc {
  font-size: 12px;
  color: #f56c6c;
  margin-top: 5px;
  margin-left: 24px;
}
</style>
