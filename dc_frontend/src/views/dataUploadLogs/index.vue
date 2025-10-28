<template>
  <div class="data-upload-logs">
    <div class="page-header">
      <div class="left">
        <h2>数据上传日志</h2>

      </div>
      <div class="actions">
        <el-button type="primary" @click="loadLogs" :loading="loading">刷新</el-button>
      </div>
    </div>

    <el-card class="table-card" shadow="never">
      <el-table :data="logs" v-loading="loading" stripe height="560px">
        <el-table-column prop="batch_id" label="批次号" min-width="200" />
        <el-table-column prop="data_source_name" label="数据源" min-width="160" />
        <el-table-column prop="platform_name" label="平台" min-width="160" />
        <el-table-column prop="target_table_name" label="目标表" min-width="200" />
        <el-table-column prop="need_review" label="需审读" width="90">
          <template #default="{ row }">
            <el-tag :type="row.need_review === 1 ? 'warning' : 'success'" size="small">
              {{ row.need_review === 1 ? '是' : '否' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="resource_type" label="资源类型" width="110">
          <template #default="{ row }">
            <el-tag size="small">{{ row.resource_type }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="sync_status" label="状态" width="110">
          <template #default="{ row }">
            <el-tag :type="statusTagType(row.sync_status)" size="small">{{ statusLabel(row.sync_status) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="sync_start_time" label="开始时间" min-width="160" />
        <el-table-column prop="sync_end_time" label="结束时间" min-width="160" />
        <el-table-column prop="total_data_count" label="总量" width="100" />
        <el-table-column prop="success_data_count" label="成功" width="100" />
        <el-table-column prop="failed_data_count" label="失败" width="100" />
        <el-table-column prop="retry_upload" label="重传" width="90">
          <template #default="{ row }">
            <el-tag :type="row.retry_upload === 1 ? 'info' : 'default'" size="small">
              {{ row.retry_upload === 1 ? '是' : '否' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="encryption_method" label="加密" width="120" />
        <el-table-column prop="operator" label="操作人" width="120" />
        <el-table-column prop="failure_reason" label="失败原因" min-width="240" show-overflow-tooltip />
        <el-table-column prop="create_time" label="创建时间" min-width="160" />
        <el-table-column prop="update_time" label="更新时间" min-width="160" />
      </el-table>

      <div class="table-footer">
        <el-pagination
          background
          layout="total, sizes, prev, pager, next"
          :total="pagination.total"
          :page-sizes="[10, 20, 50, 100]"
          :page-size="pagination.pageSize"
          :current-page="pagination.page"
          @current-change="onPageChange"
          @size-change="onPageSizeChange"
        />
      </div>

      <div v-if="logs.length === 0 && !loading" class="empty">
        <el-empty description="暂无数据上传日志" />
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { dataUploadLogsApi } from '@/api/dataUploadLogs'
import type { DataUploadLog } from '@/api/dataUploadLogs'

const loading = ref(false)
const logs = ref<DataUploadLog[]>([])
const pagination = ref({
  page: 1,
  pageSize: 20,
  total: 0
})

const statusTagType = (status: string) => {
  switch (status) {
    case 'success': return 'success'
    case 'failed': return 'danger'
    case 'running': return 'warning'
    default: return 'info'
  }
}

const statusLabel = (status: string) => {
  switch (status) {
    case 'success': return '成功'
    case 'failed': return '失败'
    case 'running': return '进行中'
    default: return status
  }
}

async function loadLogs() {
  loading.value = true
  try {
    const res = await dataUploadLogsApi.getLogs({
      page: pagination.value.page,
      page_size: pagination.value.pageSize,
      sort_by: 'sync_start_time',
      order: 'desc'
    })

    const data = (res as any).data ?? res
    const rawItems = data?.items ?? data?.data?.items ?? []
    const total = data?.total ?? data?.data?.total ?? 0
    const page = data?.page ?? data?.data?.page ?? pagination.value.page
    const size = data?.size ?? data?.data?.size ?? pagination.value.pageSize

    logs.value = rawItems
    pagination.value.total = total
    pagination.value.page = page
    pagination.value.pageSize = size
  } catch (err: any) {
    ElMessage.error(err?.message || '加载数据上传日志失败')
  } finally {
    loading.value = false
  }
}

function onPageChange(page: number) {
  pagination.value.page = page
  loadLogs()
}

function onPageSizeChange(size: number) {
  pagination.value.pageSize = size
  pagination.value.page = 1
  loadLogs()
}

onMounted(loadLogs)
</script>

<style scoped>
.data-upload-logs {
  padding: 16px;
}
.page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
}
.page-header .desc {
  color: var(--el-text-color-secondary);
  font-size: 13px;
}
.table-card {
  margin-top: 8px;
}
.table-footer {
  display: flex;
  justify-content: flex-end;
  padding: 12px 0;
}
.empty {
  padding: 24px 0;
}
</style>