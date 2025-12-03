<template>
  <div class="data-upload-logs">
    <div class="page-header">
      <div class="left">
        <h2>数据上传日志</h2>

      </div>
      <div class="actions">
        <el-date-picker
          v-model="searchRange"
          type="datetimerange"
          range-separator="至"
          start-placeholder="开始时间"
          end-placeholder="结束时间"
          value-format="YYYY-MM-DD HH:mm:ss"
          unlink-panels
          clearable
          style="width: 380px; margin-right: 12px"
          @change="handleSearch"
          @clear="handleSearch"
        />
        <el-input
          v-model="searchBatch"
          placeholder="按批次号搜索"
          clearable
          style="width: 260px; margin-right: 12px"
          @keyup.enter="handleSearch"
          @clear="onClearSearch"
        >
          <template #prefix>
            <el-icon><Search /></el-icon>
          </template>
        </el-input>
        <el-button type="primary" @click="handleSearch" :loading="loading" style="margin-right: 8px">搜索</el-button>
        <el-button @click="loadLogs" :loading="loading">刷新</el-button>
      </div>
    </div>

    <el-card class="table-card" shadow="never">
      <el-table :data="logs" v-loading="loading" stripe height="560px" @row-click="onRowClick">
        <el-table-column prop="batch_id" label="源平台批次号" min-width="200" />
        <!-- <el-table-column prop="data_source_name" label="数据源" min-width="160" /> -->
        <el-table-column prop="platform_name" label="平台" min-width="160" />
        <!-- <el-table-column prop="target_table_name" label="目标表" min-width="200" /> -->
        <el-table-column prop="need_review" label="需审读" width="90">
          <template #default="{ row }">
            <el-tag :type="row.need_review === 1 ? 'warning' : 'success'" size="small">
              {{ row.need_review === 1 ? '是' : '否' }}
            </el-tag>
          </template>
        </el-table-column>
        <!-- <el-table-column prop="resource_type" label="资源类型" width="110">
          <template #default="{ row }">
            <el-tag size="small">{{ row.resource_type }}</el-tag>
          </template>
        </el-table-column> -->
        <el-table-column prop="sync_status" label="状态" width="110">
          <template #default="{ row }">
            <el-tag :type="statusTagType(row.sync_status)" size="small">{{ statusLabel(row.sync_status) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="total_data_count" label="总量" width="90" />
        <el-table-column prop="success_data_count" label="成功" width="90" />
        <el-table-column prop="failed_data_count" label="失败" width="90" />
        <el-table-column prop="sync_start_time" label="开始时间" min-width="160" />
        <el-table-column prop="sync_end_time" label="结束时间" min-width="160" />
        <!-- <el-table-column prop="retry_upload" label="重传" width="90">
          <template #default="{ row }">
            <el-tag :type="row.retry_upload === 1 ? 'info' : 'default'" size="small">
              {{ row.retry_upload === 1 ? '是' : '否' }}
            </el-tag>
          </template>
        </el-table-column> -->
        <!-- <el-table-column prop="encryption_method" label="加密" width="120" /> -->
        <!-- <el-table-column prop="operator" label="操作人" width="120" /> -->
        <!-- <el-table-column prop="failure_reason" label="失败原因" min-width="240" show-overflow-tooltip /> -->
        <!-- <el-table-column prop="create_time" label="创建时间" min-width="160" />
        <el-table-column prop="update_time" label="更新时间" min-width="160" /> -->
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

    <!-- 明细抽屉 -->
    <el-drawer v-model="drawerVisible" title="批次明细" direction="rtl" size="80%" :with-header="true">
      <template #header>
        <div style="display:flex;align-items:center;gap:12px;">
          <span>批次号：{{ detailBatchId || '-' }}</span>
          <el-tag v-if="detailTableName" type="info">{{ detailTableName }}</el-tag>
          <el-input
            v-model="detailSearch"
            placeholder="搜索全部字段"
            clearable
            style="width: 280px;"
            @keyup.enter="onSearchDetails"
          >
            <template #prefix>
              <el-icon><Search /></el-icon>
            </template>
          </el-input>
          <el-button type="primary" size="small" @click="onSearchDetails" :loading="detailLoading">查询</el-button>
          <el-button size="small" @click="refreshDetails" :loading="detailLoading">刷新</el-button>
        </div>
      </template>
      <div>
        <el-table :data="filteredDetailItems" v-loading="detailLoading" height="480px" stripe>
          <el-table-column
            v-for="col in visibleDetailColumns"
            :key="col"
            :prop="col"
            :label="columnLabel(col)"
            :formatter="getFormatter(col)"
            show-overflow-tooltip
          />
        </el-table>
        <div class="table-footer">
          <el-pagination
            background
            layout="total, sizes, prev, pager, next"
            :total="detailTotal"
            :page-sizes="[50, 100, 200, 500]"
            :page-size="detailLimit"
            :current-page="detailPage"
            @current-change="onDetailPageChange"
            @size-change="onDetailPageSizeChange"
          />
        </div>
      </div>
    </el-drawer>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
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

// 搜索 - 批次号
const searchBatch = ref('')
// 搜索 - 时间范围（开始、结束）
const searchRange = ref<[string, string] | null>(null)

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
      order: 'desc',
      batch_id: searchBatch.value.trim() || undefined,
      start_time: searchRange.value?.[0],
      end_time: searchRange.value?.[1],
      // 服务端排除指定数据源，避免前端过滤导致分页不一致
      exclude_data_source_name: 'cpc_rc_data',
      exclude_platform_name: 'internal_migration'
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

function handleSearch() {
  pagination.value.page = 1
  loadLogs()
}

function onClearSearch() {
  pagination.value.page = 1
  loadLogs()
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

// 明细抽屉状态与方法
const drawerVisible = ref(false)
const detailLoading = ref(false)
const detailItems = ref<any[]>([])
const detailColumns = ref<string[]>([])
const detailTableName = ref<string>('')
const detailBatchId = ref<string>('')
const detailTotal = ref(0)
const detailLimit = ref(200)
const detailOffset = ref(0)
const detailPage = ref(1)
const detailSearch = ref('')

async function loadBatchDetails(batchId: string) {
  detailLoading.value = true
  detailBatchId.value = batchId
  try {
    const res = await dataUploadLogsApi.getBatchDetails(batchId, { limit: detailLimit.value, offset: detailOffset.value, q: detailSearch.value.trim() || undefined })
    const data = (res as any).data ?? res
    const items = data?.items ?? data?.data?.items ?? []
    const tableName = data?.table_name ?? data?.data?.table_name ?? ''
    const total = data?.count ?? data?.data?.count ?? items.length
    const limit = data?.limit ?? data?.data?.limit ?? detailLimit.value
    const offset = data?.offset ?? data?.data?.offset ?? detailOffset.value

    detailItems.value = items
    detailColumns.value = items.length ? Object.keys(items[0]) : []
    detailTableName.value = tableName
    detailTotal.value = total
    detailLimit.value = limit
    detailOffset.value = offset
    detailPage.value = Math.floor(offset / limit) + 1
  } catch (err: any) {
    ElMessage.error(err?.message || '加载批次明细失败')
  } finally {
    detailLoading.value = false
  }
}

function onRowClick(row: DataUploadLog) {
  // 需审读为“否”时不允许查看明细
  if (Number(row.need_review) !== 1) {
    ElMessage.warning('该上传批次无需审读，没有详细审读结果')
    return
  }
  drawerVisible.value = true
  detailOffset.value = 0
  detailPage.value = 1
  loadBatchDetails(row.batch_id)
}

function onDetailPageChange(page: number) {
  detailPage.value = page
  detailOffset.value = (page - 1) * detailLimit.value
  if (detailBatchId.value) {
    loadBatchDetails(detailBatchId.value)
  }
}

function onDetailPageSizeChange(size: number) {
  detailLimit.value = size
  detailPage.value = 1
  detailOffset.value = 0
  if (detailBatchId.value) {
    loadBatchDetails(detailBatchId.value)
  }
}

function refreshDetails() {
  if (detailBatchId.value) {
    loadBatchDetails(detailBatchId.value)
  }
}

function onSearchDetails() {
  // 回车或清空时，重置到第一页并携带 q 请求服务端进行全量搜索
  detailPage.value = 1
  detailOffset.value = 0
  if (detailBatchId.value) {
    loadBatchDetails(detailBatchId.value)
  }
}

// 列名映射（期刊文章表 cpc_rc_periodical_articles）
const columnLabelMap: Record<string, string> = {
  id: '编号',
  task_id: '数据批次标识',
  task_code: '批次编码(可读性标识)',
  data_source: '数据来源',
  source_system_id: '源系统ID',
  source_id: '来源ID',
  create_time: '创建时间',
  source_pid: '来源系统期刊ID',
  source_pcode: '来源系统期刊代码',
  source_acode: '来源系统文章代码',
  doi: 'DOI标识符',
  periodical_id: '期刊审读ID',
  periodical_name: '期刊名称',
  periodical_name_cn: '期刊中文名称',
  publisher: '出版社名称',
  volume: '卷号',
  issue: '期号',
  publish_date: '出版日期',
  online_date: '在线日期',
  title: '标题',
  title_cn: '标题中文名称',
  subtitle: '副标题',
  subtitle_cn: '副标题中文名称',
  content_summary: '内容简介',
  content_summary2: '内容简介2',
  chapter_title: '章节',
  issn: 'ISSN',
  url: 'URL',
  submit_remark: '送审备注',
  order_code: '销售订单号',
  customer_name: '订购方名称',
  author_names: '作者信息(STRING格式)',
  authors_info: '作者信息(JSON格式)',
  author: '作者',
  author_summary: '作者简介',
  author_link: '关联作者图谱',
  author_id: '关联作者库ID',
  keywords: '关键词',
  keywords2: '关键词2',
  summary: '摘要',
  language: '语言',
  start_page: '起始页码',
  end_page: '截止页码',
  article_type: '文章类型',
  content_type: '内容类型',
  subject_category: '学科分类',
  clc_classification: '中图分类',
  deway_classification: '杜威分类',
  edu_classification: '教育部学科分类',
  clc_classification_code: '中图分类CODE',
  deway_classification_code: '杜威分类CODE',
  edu_classification_code: '教育部学科分类CODE',
  last_readcheck_time: '最近审读时间',
  last_readcheck_user_id: '最近审读人ID',
  last_readcheck_user_name: '最近审读人姓名',
  sensitive_score: '敏感度评分',
  human_pass_first_user_id: '一审操作人',
  human_pass_first_time: '一审完成时间',
  human_pass_second_user_id: '二审操作人',
  human_pass_second: '二审人工审读结果',
  human_pass_second_time: '二审完成时间',
  human_pass_third_user_id: '三审操作人',
  human_pass_third: '三审人工审读结果',
  human_pass_third_time: '三审完成时间',
  remark_first: '一审备注',
  remark_second: '二审备注',
  remark_third: '三审备注',
  machine_pass: '机审结果',
  machine_result: '敏感词结果过滤结果',
  machine_result_time: '机器审读结果更新时间',
  ai_pass: 'AI审读结果',
  ai_result: 'AI审读结果描述',
  ai_description: 'AI审读结论',
  ai_result_time: 'AI审读结果更新时间',
  screenshot_result: '图片审读结果',
  final_pass: '最终审读结果',
  final_pass_remark: '备注',
  final_pass_time: '最终审读时间',
  full_sensitive_level: '全文敏感等级',
  abstract_sensitive: '摘要敏感状态',
  author_sensitive: '作者敏感状态',
  article_check_log: '文章审读日志',
  fulltext_check_log: '全文审读日志',
  author_check_log: '作者审读日志',
  abstract_check_log: '摘要审读日志',
  read_standard_rules: '关联审读标准细则',
  tenant_id: '租户编号',
  create_dept: '创建部门',
  create_by: '创建者',
  update_by: '更新者',
  update_time: '更新时间',
  human_pass_first: '一审人工审读结果',
  file_path: '全文路径',
  xml_path: 'xml地址',
  owner_id: '所属人id',
  file_path_md: '解析后地址',
  screenshot_path: '解析后图片路径',
  ai_translate_path: 'ai翻译后的地址',
  is_upload: '是否上传至向量数据库',
  return_date: '回送时间'
}

function columnLabel(key: string): string {
  return columnLabelMap[key] ?? key
}

// final_pass 值映射
const finalPassMap: Record<number, string> = {
  1: '订单通过',
  2: '重点审读',
  3: '删除',
  5: '限阅',
  6: '全文禁发',
  7: '需实物审读',
  16: '撤订',
  17: '禁止发行',
  11: '可订',
  12: '禁订',
  13: '可作为新增数据库报备',
  14: '可试作为新增数据库报备',
  15: '不建议作为新增数据库报备',
  10: '需样书审读',
  9: '无需实物审读',
  4: '不通过',
  8: '疑似',
  18: '通过',
  19: '实物通过',
  20: '高度疑似',
  21: '含有违反',
  22: '含有少量违反',
  23: '未发现违反',
  0: '未处理'
}

function formatterFinalPass(_row: any, _column: any, cellValue: any) {
  const n = Number(cellValue)
  if (Number.isNaN(n)) return cellValue
  return finalPassMap[n] ?? cellValue
}

function getFormatter(col: string) {
  if (col === 'final_pass') return formatterFinalPass
  return undefined as any
}

// 停用输入即时匹配：仅在回车或点击查询时从服务端检索
const filteredDetailItems = computed(() => detailItems.value)

// 仅显示有数据的列（至少一行非空）
const visibleDetailColumns = computed(() => {
  const items = filteredDetailItems.value
  const cols = detailColumns.value
  if (!items.length) return cols
  return cols.filter((c) => {
    for (const row of items) {
      const v = row?.[c]
      if (v === null || v === undefined) continue
      if (typeof v === 'string') {
        if (v.trim().length > 0) return true
      } else if (Array.isArray(v)) {
        if (v.length > 0) return true
      } else if (typeof v === 'object') {
        if (Object.keys(v).length > 0) return true
      } else {
        // number, boolean, date 等认为存在值
        return true
      }
    }
    return false
  })
})
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