<template>
  <div class="es-package-query-panel">
    <!-- 标题与操作 -->
    <el-card class="header-card">
      <template #header>
        <div class="card-header">
          <span class="card-title">Elasticsearch 高级查询</span>
          <div class="header-search">
            <el-select 
              v-model="defaultSearchField" 
              size="small" 
              style="width: 150px" 
              filterable 
              placeholder="选择字段"
              :disabled="availableFieldNames.length === 0"
            >
              <el-option v-for="f in availableFieldNames" :key="f" :label="f" :value="f" />
            </el-select>
            <el-input
              v-model="defaultSearchValue"
              size="small"
              placeholder="输入搜索关键词"
              style="width: 200px"
              clearable
              @keyup.enter="executeQuery"
              @input="() => { console.log('Search value changed:', defaultSearchValue) }"
            >
              <template #prefix>
                <el-icon><Search /></el-icon>
              </template>
            </el-input>
          </div>
          <div class="header-actions">
            <el-button size="small" @click="resetConditions">重置</el-button>
            <el-button type="primary" size="small" :loading="loading" @click="executeQuery">执行查询</el-button>
            <el-button type="success" size="small" :loading="downloadLoading" @click="openDownloadDialog">下载资源包</el-button>
            <el-button size="small" @click="addCondition" :disabled="availableFieldNames.length === 0">
              <el-icon><Plus /></el-icon>
              添加条件
            </el-button>
          </div>
        </div>
      </template>

      <!-- 限定条件展示（来自模板） -->
      <div class="locked-conditions" v-if="fixedConditions.length">
        <span class="section-title">限定条件</span>
        <div class="condition-list">
          <el-tag
            v-for="(cond, idx) in fixedConditions"
            :key="idx"
            type="warning"
            class="condition-tag"
          >
            <el-icon style="margin-right: 4px"><Lock /></el-icon>
            {{ formatFixedCondition(cond) }}
          </el-tag>
        </div>
      </div>

      <!-- 动态查询条件编辑器：所有返回字段都可查询，并可选择查询类型 -->
      <div class="query-builder" v-if="conditions.length > 0">
        <div class="qb-header">
          <span class="section-title">查询条件</span>
        </div>
        <div class="conditions">
          <div v-for="(c, i) in conditions" :key="i" class="condition-item">
            <el-select v-model="c.logic" size="small" style="width: 90px">
              <el-option label="AND" value="must" />
              <el-option label="OR" value="should" />
              <el-option label="NOT" value="must_not" />
            </el-select>

            <el-select v-model="c.field" size="small" style="width: 180px" filterable :disabled="availableFieldNames.length===0">
              <el-option v-for="f in availableFieldNames" :key="f" :label="f" :value="f" />
            </el-select>

            <el-select v-model="c.type" size="small" style="width: 140px">
              <el-option label="匹配 (match)" value="match" />
              <el-option label="精确 (term)" value="term" />
              <el-option label="范围 (range)" value="range" />
              <el-option label="存在 (exists)" value="exists" />
              <el-option label="通配符 (wildcard)" value="wildcard" />
              <el-option label="前缀 (prefix)" value="prefix" />
            </el-select>

            <template v-if="c.type === 'range'">
              <el-input v-model="c.value.gte" size="small" placeholder="最小值" style="width: 120px" />
              <span class="dash">-</span>
              <el-input v-model="c.value.lte" size="small" placeholder="最大值" style="width: 120px" />
            </template>
            <template v-else-if="c.type === 'exists'">
              <el-tag size="small" type="info">字段存在</el-tag>
            </template>
            <template v-else>
              <el-input v-model="c.value" size="small" placeholder="查询值" style="width: 260px" />
            </template>

            <el-button @click="removeCondition(i)" size="small" type="danger" plain>
              <el-icon><Delete /></el-icon>
            </el-button>
          </div>
        </div>
      </div>
    </el-card>

    <!-- 结果展示：左右两栏 -->
    <el-card class="results-card" :class="{ 'fullscreen-mode': isFullscreen }" v-loading="loading">
      <template #header>
        <div class="results-header">
          <span class="card-title">查询结果</span>
          <div class="view-switch">
            <el-radio-group v-model="viewMode" size="small">
              <el-radio-button label="list">列表</el-radio-button>
              <el-radio-button label="card">卡片</el-radio-button>
            </el-radio-group>
            <div class="display-toggles">
              <el-switch v-model="compactMode" size="small" active-text="紧凑" inactive-text="常规" />
              <el-switch v-model="wrapLongText" size="small" active-text="自动换行" inactive-text="省略" />
              <el-button 
                @click="toggleFullscreen" 
                size="small" 
                :type="isFullscreen ? 'primary' : 'default'"
                :icon="FullScreen"
              >
                {{ isFullscreen ? '退出全屏' : '全屏显示' }}
              </el-button>
            </div>
          </div>
        </div>
      </template>

      <div v-if="!results" class="no-data">
        <el-empty description="暂无结果，配置条件后点击执行查询" />
      </div>

      <div v-else class="results-grid">
        <!-- 左侧聚合结果 20% -->
        <div class="agg-pane">
          <div class="agg-header">聚合结果</div>
          <div v-if="!results.aggregations" class="agg-empty">
            <el-empty description="无聚合数据" :image-size="60" />
          </div>
          <div v-else class="aggregations">
            <div v-for="(agg, aggName) in normalizedAggs" :key="aggName" class="agg-card">
              <div class="agg-title">{{ aggName }}</div>
              <div class="agg-body">
                <template v-if="agg.type === 'terms'">
                  <div
                    v-for="bucket in agg.buckets.slice(0, 20)"
                    :key="bucket.key"
                    class="agg-row clickable"
                    @click="onAggBucketClick(aggName as string, bucket)"
                  >
                    <span class="agg-key" :title="String(bucket.key)">{{ formatText(String(bucket.key), 40) }}</span>
                    <span class="agg-count">{{ bucket.doc_count }}</span>
                  </div>
                </template>
                <template v-else-if="['sum','avg','max','min','value_count'].includes(agg.type)">
                  <div class="agg-row"><span class="agg-key">值</span><span class="agg-count">{{ agg.value }}</span></div>
                </template>
                <template v-else>
                  <pre class="agg-json">{{ JSON.stringify(agg.raw, null, 2) }}</pre>
                </template>
              </div>
            </div>
          </div>
        </div>

        <!-- 右侧查询结果 80% -->
        <div class="result-pane">
          <template v-if="viewMode === 'list'">
            <div class="table-container">
              <el-table :data="processedRecords" border stripe :size="compactMode ? 'small' : 'default'" style="width: 100%" @sort-change="onSortChange" @row-click="openRowDetail">
                <el-table-column type="index" label="#" width="60" />
                <el-table-column v-for="col in displayFields" :key="col" :prop="col" :label="col" min-width="160" :show-overflow-tooltip="!wrapLongText" sortable="custom">
                  <template #default="{ row }">
                    <span 
                      class="cell" 
                      :class="{ wrap: wrapLongText }" 
                      :title="formatCell(row[col])"
                      v-html="formatTextWithHighlight(formatCell(row[col]), 160, defaultSearchValue)"
                    ></span>
                  </template>
                </el-table-column>
              </el-table>
              <el-dialog v-model="detailVisible" title="数据详情" width="600px">
                <el-descriptions column="1" border>
                  <el-descriptions-item v-for="f in displayFields" :key="f" :label="f">
                    <span v-if="typeof selectedRow?.[f] === 'object'">{{ JSON.stringify(selectedRow?.[f], null, 2) }}</span>
                    <span v-else>{{ selectedRow?.[f] }}</span>
                  </el-descriptions-item>
                </el-descriptions>
                <template #footer>
                  <span class="dialog-footer">
                    <el-button @click="detailVisible = false">关闭</el-button>
                    <el-button
                      v-if="selectedRow && selectedRow['pdf_url'] && selectedRow['pdf_url'] !== 'null'"
                      type="primary"
                      @click="openPdf"
                    >
                      打开全文
                    </el-button>
                  </span>
                </template>
              </el-dialog>

              <!-- PDF 预览弹窗 -->
              <el-dialog v-model="pdfDialogVisible" title="全文预览" width="80%">
                <PdfViewer :src="pdfUrl || ''" />
              </el-dialog>
            </div>
          </template>

          <template v-else>
            <div class="cards-container">
              <div class="cards" :class="{ compact: compactMode }">
                <el-card v-for="(row, idx) in records" :key="idx" class="result-card" shadow="hover">
                  <div class="card-content">
                    <el-tooltip content="复制" placement="top">
                      <el-button size="small" circle class="card-copy-btn" @click="copyRow(row)">
                        <el-icon><CopyDocument /></el-icon>
                      </el-button>
                    </el-tooltip>
                    <!-- 短字段优先，多个短字段一行；一致的字段顺序 -->
                    <template v-for="chunk in buildCardChunks(row)">
                      <div class="card-row" :class="{ wide: chunk.wide }">
                        <div v-for="f in chunk.fields" :key="f" class="kv">
                          <span class="k">{{ f }}</span>
                          <span 
                            class="v" 
                            :class="{ wrap: wrapLongText }" 
                            :title="formatCell(row[f])"
                            v-html="formatTextWithHighlight(formatCell(row[f]), chunk.wide ? WIDE_MAX_CHARS : DEFAULT_MAX_CHARS, defaultSearchValue)"
                          ></span>
                        </div>
                      </div>
                    </template>
                  </div>
                </el-card>
              </div>
            </div>
          </template>
          <div class="pager" v-if="results">
            <el-pagination
              v-model:current-page="currentPage"
              v-model:page-size="pageSize"
              :page-sizes="[10, 20, 50, 100]"
              layout="total, sizes, prev, pager, next, jumper"
              :total="totalHits"
              @current-change="executeQuery"
              @size-change="onPageSizeChange"
            />
          </div>
        </div>
      </div>
    </el-card>

    <!-- 资源包下载弹窗 -->
    <el-dialog v-model="downloadDialogVisible" title="下载资源包" width="520px">
      <div class="download-info">
        <div class="info-row">
          <span class="label">最新生成时间：</span>
          <span class="value">{{ formatTime(dialogData.excel_time) || '暂无' }}</span>
        </div>
        <div class="info-row">
          <span class="label">最新下载时间：</span>
          <span class="value">{{ formatTime(dialogData.download_time) || '暂无' }}</span>
        </div>
        <!-- 历史文件选择 -->
        <div class="info-row">
          <span class="label">历史文件：</span>
          <el-select v-model="selectedFileId" placeholder="选择历史Excel" filterable style="width: 260px" :loading="historyLoading">
            <el-option v-for="f in historyFiles" :key="f.id" :label="formatHistoryLabel(f)" :value="f.id" />
          </el-select>
          <el-button size="small" type="success" :disabled="!selectedFileId" :loading="historyDownloadLoading" @click="handleDownloadHistory">下载资源包</el-button>
        </div>
      </div>
      <template #footer>
        <div class="dialog-footer">
          <el-button @click="downloadDialogVisible = false">取消</el-button>
          <el-button type="primary" :loading="generateLoading" @click="handleGenerateExcel">生成资源包</el-button>
          <el-button type="success" :disabled="!dialogData.download_url" :loading="latestDownloadLoading" @click="handleDownloadLatest">
            下载最新资源包
          </el-button>
        </div>
      </template>
    </el-dialog>
  </div>
  
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Lock, Plus, Delete, CopyDocument, Search, FullScreen } from '@element-plus/icons-vue'
import { templateApi } from '@/api/template'
import { executeESQuery, getESFieldMapping } from '@/api/esQuery'
import { dataResourceApi } from '@/api/dataResource'
import { resourcePackageApi } from '@/api/resourcePackage'
import type { ResourcePackageFile } from '@/api/resourcePackage'
import PdfViewer from '@/components/PdfViewer.vue'

const props = defineProps<{ packageData: any }>()

const loading = ref(false)
const downloadLoading = ref(false)
const generateLoading = ref(false)
const latestDownloadLoading = ref(false)
const downloadDialogVisible = ref(false)
const dialogData = reactive<{ excel_time?: string; download_time?: string; download_url?: string }>({
  excel_time: undefined,
  download_time: undefined,
  download_url: undefined
})

// 历史文件相关状态
const historyFiles = ref<ResourcePackageFile[]>([])
const selectedFileId = ref<number | null>(null)
const historyLoading = ref(false)
const historyDownloadLoading = ref(false)
const templateDetail = ref<any | null>(null)
const fixedConditions = ref<any[]>([])
const sourceFields = ref<string[]>([])
const availableFields = ref<Array<{ name: string; type?: string }>>([])
const availableFieldNames = computed(() => sourceFields.value.length > 0 
  ? sourceFields.value 
  : availableFields.value.map(f => f.name))
const selectedIndices = ref<string[]>([])

type Logic = 'must' | 'should' | 'must_not'
type Cond = { field: string; type: string; value: any; logic: Logic }
const conditions = reactive<Cond[]>([])

// 默认搜索相关状态
const defaultSearchField = ref<string>('')
const defaultSearchValue = ref<string>('')

const viewMode = ref<'list' | 'card'>('list')
const compactMode = ref(false)
const wrapLongText = ref(false)
const isFullscreen = ref(false)
const results = ref<any | null>(null)
const records = computed<any[]>(() => {
  const hits = results.value?.hits?.hits || []
  return hits.map((h: any) => h._source)
})
// 全字段搜索与列排序
const sortState = ref<{ field: string | null; order: 'ascending' | 'descending' | null }>({ field: null, order: null })
const processedRecords = computed<any[]>(() => {
  let data = records.value || []
  const { field, order } = sortState.value
  if (field && order) {
    data = [...data].sort((a: Record<string, any>, b: Record<string, any>) => {
      const va = a?.[field]
      const vb = b?.[field]
      const na = typeof va === 'number' ? va : Number.isFinite(Number(va)) ? Number(va) : null
      const nb = typeof vb === 'number' ? vb : Number.isFinite(Number(vb)) ? Number(vb) : null
      let cmp = 0
      if (na !== null && nb !== null) cmp = na - nb
      else cmp = String(formatCell(va)).localeCompare(String(formatCell(vb)), 'zh-CN', { numeric: true, sensitivity: 'base' })
      return order === 'ascending' ? cmp : -cmp
    })
  }
  return data
})
// 表格排序事件
const onSortChange = (payload: { prop: string; order: 'ascending' | 'descending' | null }) => {
  sortState.value = { field: payload?.prop || null, order: payload?.order || null }
}
// 行详情
const detailVisible = ref(false)
const selectedRow = ref<Record<string, any> | null>(null)
const pdfDialogVisible = ref(false)
const pdfUrl = ref<string | null>(null)
const openRowDetail = (row: Record<string, any>) => {
  selectedRow.value = row
  detailVisible.value = true
}
const openPdf = () => {
  const url = selectedRow.value?.['pdf_url']
  if (url && url !== 'null') {
    pdfUrl.value = String(url)
    pdfDialogVisible.value = true
  } else {
    ElMessage.warning('未找到有效的 pdf_url 字段')
  }
}

// 分页
const currentPage = ref(1)
const pageSize = ref(20)
const totalHits = computed<number>(() => {
  const total = results.value?.hits?.total
  if (typeof total === 'number') return total
  if (typeof total?.value === 'number') return total.value
  return records.value.length
})

// 按字段值长度构建一致的字段顺序
const fieldOrder = ref<string[]>([])
const displayFields = computed<string[]>(() => {
  // 收集所有潜在字段（来源于映射或当前记录）
  const allFields = new Set<string>()
  if (sourceFields.value.length) {
    sourceFields.value.forEach(f => allFields.add(f))
  } else {
    records.value.forEach(r => Object.keys(r || {}).forEach(k => allFields.add(k)))
  }

  // 如果有全局排序，先按排序排列，再补充未参与排序的剩余字段
  if (fieldOrder.value.length) {
    const ordered = [...fieldOrder.value]
    const leftover = Array.from(allFields).filter(f => !fieldOrder.value.includes(f))
    return ordered.concat(leftover)
  }
  // 否则直接使用全部字段集合
  return Array.from(allFields)
})

// 规范化聚合结果，便于左侧展示
const normalizedAggs = computed<Record<string, any>>(() => {
  const aggs = results.value?.aggregations
  if (!aggs) return {}
  const out: Record<string, any> = {}
  const tplQuery = templateDetail.value?.query || templateDetail.value?.query_content
  Object.entries(aggs).forEach(([name, cfg]: [string, any]) => {
    if (cfg?.buckets && Array.isArray(cfg.buckets)) {
      const field = tplQuery?.aggs?.[name]?.terms?.field
      out[name] = { type: 'terms', buckets: cfg.buckets, field, raw: cfg }
    } else if (cfg?.value !== undefined) {
      // sum/avg/max/min/value_count
      const type = cfg.meta?.type || 'metric'
      out[name] = { type, value: cfg.value, raw: cfg }
    } else {
      out[name] = { type: 'unknown', raw: cfg }
    }
  })
  return out
})

onMounted(async () => {
  await initFromTemplate()
})

async function initFromTemplate() {
  try {
    if (!props.packageData?.template_id) return
    const resp: any = await templateApi.getByType(props.packageData.template_id, 'es')
    const detail = resp?.data || resp
    templateDetail.value = detail

    // 解析 indices
    const indices = detail?.indices || detail?.config?.indices || []
    if (Array.isArray(indices)) selectedIndices.value = indices

    // 如果模板未提供索引，尝试从资源回退
    await ensureIndicesFromResource()

    // 解析 query/_source
    const q = detail?.query || detail?.query_content || null
    if (q && Array.isArray(q._source)) {
      sourceFields.value = q._source
    }

    // 解析模板条件（锁定为限定条件）
    const conditionsCfg = detail?.config?.conditions || []
    fixedConditions.value = conditionsCfg.filter((c: any) => c.locked || c.lockType === 'locked')

    // 如未提供_source，尝试加载字段映射
    if (availableFieldNames.value.length === 0 && props.packageData?.datasource_id && selectedIndices.value.length) {
      const fieldsResp = await getESFieldMapping(props.packageData.datasource_id, selectedIndices.value)
      const fields = (fieldsResp?.data || []) as Array<{ name: string; type?: string }>
      availableFields.value = fields
    }
  } catch (e) {
    console.error('加载ES模板详情失败:', e)
  }
}

/**
 * 从关联数据资源回退解析ES索引
 * 优先使用 packageData.resource_id，其次尝试 data_resource_id
 */
async function ensureIndicesFromResource() {
  try {
    if (selectedIndices.value.length) return
    const resId = props.packageData?.resource_id || props.packageData?.data_resource_id
    if (!resId) return
    const resp = await dataResourceApi.getResourceDetail(Number(resId))
    const resource: any = resp?.data || resp
    const idx = resource?.index_name || resource?.table_name
    if (idx) {
      selectedIndices.value = [idx]
    }
  } catch (e) {
    console.warn('从数据资源解析索引失败:', e)
  }
}

function addCondition() {
  const field = availableFieldNames.value[0]
  if (!field) {
    ElMessage.warning('暂无可用字段')
    return
  }
  conditions.push({ field, type: 'match', value: '', logic: 'must' })
}

function removeCondition(i: number) {
  conditions.splice(i, 1)
}

function resetConditions() {
  conditions.splice(0, conditions.length)
  defaultSearchField.value = ''
  defaultSearchValue.value = ''
  results.value = null
  fieldOrder.value = []
}

function formatFixedCondition(cond: any): string {
  const name = cond?.name || cond?.field || ''
  const op = cond?.operator || cond?.type || 'match'
  if (op === 'range') {
    const gte = cond?.default_value?.min ?? cond?.min ?? cond?.gte
    const lte = cond?.default_value?.max ?? cond?.max ?? cond?.lte
    return `${name} ∈ [${gte ?? ''} - ${lte ?? ''}]`
  }
  const val = cond?.default_value ?? cond?.value ?? ''
  return `${name} ${op} ${val}`
}

function buildDSL(): any {
  const bool = { must: [] as any[], should: [] as any[], must_not: [] as any[] }

  // 固定条件
  fixedConditions.value.forEach((cond: any) => {
    const field = cond?.name || cond?.field
    const op = cond?.operator || cond?.type || 'match'
    const val = cond?.default_value ?? cond?.value
    if (!field) return
    switch (op) {
      case 'term':
        bool.must.push({ term: { [field]: val } })
        break
      case 'match':
        bool.must.push({ match: { [field]: val } })
        break
      case 'prefix':
        bool.must.push({ prefix: { [field]: val } })
        break
      case 'wildcard':
        bool.must.push({ wildcard: { [field]: val } })
        break
      case 'exists':
        bool.must.push({ exists: { field } })
        break
      case 'range':
        const gte = cond?.default_value?.min ?? cond?.min ?? cond?.gte
        const lte = cond?.default_value?.max ?? cond?.max ?? cond?.lte
        const range: any = {}
        if (gte !== undefined) range.gte = gte
        if (lte !== undefined) range.lte = lte
        bool.must.push({ range: { [field]: range } })
        break
      default:
        bool.must.push({ match: { [field]: val } })
        break
    }
  })

  // 默认搜索条件（如果有输入值）
  if (defaultSearchValue.value && defaultSearchValue.value.trim()) {
    if (defaultSearchField.value) {
      // 指定字段搜索，使用match查询
      bool.must.push({ match: { [defaultSearchField.value]: defaultSearchValue.value.trim() } })
    } else {
      // 未指定字段时，对所有可用字段进行multi_match查询
      if (availableFieldNames.value.length > 0) {
        bool.must.push({
          multi_match: {
            query: defaultSearchValue.value.trim(),
            fields: availableFieldNames.value,
            type: 'best_fields'
          }
        })
      }
    }
  }

  // 动态条件
  conditions.forEach((c) => {
    if (!c.field) return
    let clause: any = {}
    switch (c.type) {
      case 'term':
        clause = { term: { [c.field]: c.value } }
        break
      case 'match':
        clause = { match: { [c.field]: c.value } }
        break
      case 'prefix':
        clause = { prefix: { [c.field]: c.value } }
        break
      case 'wildcard':
        clause = { wildcard: { [c.field]: c.value } }
        break
      case 'exists':
        clause = { exists: { field: c.field } }
        break
      case 'range':
        const range: any = {}
        if (c.value?.gte !== undefined) range.gte = c.value.gte
        if (c.value?.lte !== undefined) range.lte = c.value.lte
        clause = { range: { [c.field]: range } }
        break
    }
    if (Object.keys(clause).length) {
      bool[c.logic].push(clause)
    }
  })

  const query: any = { query: {} }
  if (bool.must.length || bool.should.length || bool.must_not.length) {
    query.query = { bool }
  } else {
    query.query = { match_all: {} }
  }
  if (availableFieldNames.value.length) {
    query._source = availableFieldNames.value
  }
  // 保持分页基础配置
  query.size = pageSize.value
  query.from = (currentPage.value - 1) * pageSize.value
  // 默认按 update_time 倒序（存在该字段时）
  if (availableFieldNames.value.includes('update_time')) {
    query.sort = [{ update_time: { order: 'desc' } }]
  }

  // 如果模板定义了聚合，沿用之（便于左侧展示）
  const tplQuery = templateDetail.value?.query || templateDetail.value?.query_content
  if (tplQuery?.aggs) {
    query.aggs = tplQuery.aggs
  }
  return query
}

async function executeQuery() {
  try {
    if (!props.packageData?.datasource_id) {
      ElMessage.error('缺少数据源ID')
      return
    }
    if (!selectedIndices.value.length) {
      ElMessage.error('缺少索引信息，无法执行查询')
      return
    }

    loading.value = true
    const dsl = buildDSL()
    const req: any = {
      datasourceId: props.packageData.datasource_id,
      index: selectedIndices.value,
      query: dsl.query,
      size: dsl.size,
      from: dsl.from
    }
    if (dsl.sort) req.sort = dsl.sort
    if (dsl._source) req._source = dsl._source
    if (dsl.aggs) req.aggs = dsl.aggs
    const resp = await executeESQuery(req)
    results.value = resp?.data || resp

    // 计算全局字段顺序（基于值长度的升序）
    computeFieldOrder()
  } catch (e) {
    console.error('执行ES查询失败:', e)
    ElMessage.error('执行ES查询失败')
  } finally {
    loading.value = false
  }
}

function computeFieldOrder() {
  // 仅基于当前页前10行，空值不参与平均值统计，但需要识别“全为空”的字段以置前
  const topN = records.value.slice(0, Math.min(10, records.value.length))
  const lenStats: Record<string, { total: number; count: number }> = {}
  const allFieldsSet = new Set<string>()

  // 收集所有出现过的字段（或映射提供的字段）
  if (sourceFields.value.length) {
    sourceFields.value.forEach(f => allFieldsSet.add(f))
  }
  topN.forEach((row) => {
    Object.keys(row || {}).forEach(k => allFieldsSet.add(k))
    Object.entries(row || {}).forEach(([k, v]) => {
      if (isEmptyValue(v)) return
      const l = getValueLength(v)
      if (!lenStats[k]) lenStats[k] = { total: 0, count: 0 }
      lenStats[k].total += l
      lenStats[k].count += 1
    })
  })

  const allFields = Array.from(allFieldsSet)
  const nonEmptyFields = Object.keys(lenStats)
  const emptyFields = allFields.filter(f => !nonEmptyFields.includes(f))

  const entries = Object.entries(lenStats).map(([k, s]) => ({ field: k, avg: s.total / (s.count || 1) }))
  // 按平均长度升序：短字段优先（在“空字段”之后）
  entries.sort((a, b) => a.avg - b.avg)

  fieldOrder.value = emptyFields.concat(entries.map(e => e.field))
}

function isEmptyValue(v: any): boolean {
  if (v === null || v === undefined) return true
  if (typeof v === 'string') return v.trim().length === 0
  if (Array.isArray(v)) return v.length === 0
  if (typeof v === 'object') return Object.keys(v).length === 0
  return false
}

function getValueLength(v: any): number {
  if (v === null || v === undefined) return 0
  if (typeof v === 'string') return v.length
  if (typeof v === 'number') return String(v).length
  if (Array.isArray(v)) return JSON.stringify(v).length
  if (typeof v === 'object') return JSON.stringify(v).length
  return String(v).length
}

function formatCell(v: any): string {
  if (v === null || v === undefined) return '-'
  if (typeof v === 'string') return v
  try { return JSON.stringify(v) } catch { return String(v) }
}

function formatTime(t?: string): string {
  if (!t) return ''
  try {
    const d = new Date(t)
    if (isNaN(d.getTime())) return String(t)
    return d.toLocaleString()
  } catch {
    return String(t || '')
  }
}

function formatText(text: string, max: number): string {
  if (!text) return ''
  return text.length > max ? text.slice(0, max - 1) + '…' : text
}

// 高亮搜索关键词的函数
function highlightText(text: string, keyword: string): string {
  if (!text || !keyword) return text
  
  // 转义特殊字符，避免正则表达式错误
  const escapedKeyword = keyword.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
  const regex = new RegExp(`(${escapedKeyword})`, 'gi')
  
  return text.replace(regex, '<span class="highlight">$1</span>')
}

// 带高亮的格式化文本函数
function formatTextWithHighlight(text: string, max: number, keyword?: string): string {
  if (!text) return ''
  
  // 先截断文本
  const truncatedText = text.length > max ? text.slice(0, max - 1) + '…' : text
  
  // 如果有搜索关键词，则高亮显示
  if (keyword && keyword.trim()) {
    console.log('Highlighting keyword:', keyword.trim(), 'in text:', truncatedText.substring(0, 50))
    return highlightText(truncatedText, keyword.trim())
  }
  
  return truncatedText
}

function copyRow(row: Record<string, any>) {
  try {
    navigator.clipboard.writeText(JSON.stringify(row, null, 2))
    ElMessage.success('复制成功')
  } catch (e) {
    ElMessage.error('复制失败')
  }
}

// 全屏切换函数
function toggleFullscreen() {
  isFullscreen.value = !isFullscreen.value
  
  if (isFullscreen.value) {
    // 进入全屏模式
    document.body.style.overflow = 'hidden'
  } else {
    // 退出全屏模式
    document.body.style.overflow = ''
  }
}

function onAggBucketClick(aggName: string, bucket: any) {
  const agg = normalizedAggs.value[aggName]
  const field = agg?.field
  if (!field) {
    ElMessage.warning('无法添加筛选：未找到聚合字段')
    return
  }
  conditions.push({ field, type: 'term', value: bucket.key, logic: 'must' })
  executeQuery()
}

// 长内容阈值（达到或超过则整行展示）
const LONG_THRESHOLD = 100
// 文本截断阈值：普通行与宽行分别使用不同上限
const DEFAULT_MAX_CHARS = 160
const WIDE_MAX_CHARS = 500

// 构建卡片行分块：遵循全局顺序，长内容占满一行，其余三等分
function buildCardChunks(row: Record<string, any>): Array<{ fields: string[]; wide?: boolean }> {
  const orderedFields = displayFields.value.filter(f => row && f in row)
  const chunks: Array<{ fields: string[]; wide?: boolean }> = []
  let currentRow: string[] = []

  orderedFields.forEach((f) => {
    const len = getValueLength(row[f])
    const isLong = len >= LONG_THRESHOLD

    if (isLong) {
      // 先推送当前累积行
      if (currentRow.length) {
        chunks.push({ fields: currentRow })
        currentRow = []
      }
      // 长内容独占一行
      chunks.push({ fields: [f], wide: true })
    } else {
      currentRow.push(f)
      if (currentRow.length >= 3) {
        chunks.push({ fields: currentRow })
        currentRow = []
      }
    }
  })

  if (currentRow.length) {
    chunks.push({ fields: currentRow })
  }
  return chunks
}

function onPageSizeChange(size: number) {
  pageSize.value = size
  currentPage.value = 1
  executeQuery()
}

async function downloadResourcePackage() {
  try {
    if (!props.packageData?.id) {
      ElMessage.error('缺少资源包ID')
      return
    }
    if (!selectedIndices.value.length) {
      ElMessage.error('缺少索引信息，无法下载')
      return
    }

    downloadLoading.value = true
    
    // 构建查询数据
    const dsl = buildDSL()
    const queryData = {
      index: selectedIndices.value,
      query: dsl.query,
      _source: dsl._source
    }

    // 调用下载API
    const response = await fetch(`/api/v1/resource-packages/${props.packageData.id}/download`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${localStorage.getItem('token')}`
      },
      body: JSON.stringify(queryData)
    })

    const result = await response.json()
    
    if (!response.ok) {
      throw new Error(result.message || '下载失败')
    }

    if (result.success) {
      const hasNew = !!(result.data && result.data.has_new_data)
      if (hasNew) {
        // 有新数据，自动下载文件
        const downloadUrl = result.data.download_url
        const filename = result.data.filename
        
        if (downloadUrl) {
          // 优先使用 window.open 触发浏览器下载，避免跨域导致的 download 属性失效
          window.open(downloadUrl, '_blank')

          // 回退方案：创建临时链接尝试触发下载（跨域可能忽略 download）
          try {
            const link = document.createElement('a')
            link.href = downloadUrl
            link.download = filename || ''
            document.body.appendChild(link)
            link.click()
            document.body.removeChild(link)
          } catch (e) {
            console.warn('下载链接触发失败，已尝试回退方案:', e)
          }
          
          ElMessage.success('Excel文件生成成功，正在下载...')
        } else {
          ElMessage.error('未返回下载链接')
        }
      } else {
        // 无新数据
        ElMessage.warning(result.message || '无最新数据，无需下载资源包')
      }
    } else {
      throw new Error(result.message || '下载失败')
    }
    
  } catch (error) {
    console.error('下载资源包失败:', error)
    ElMessage.error(error.message || '下载失败，请稍后重试')
  } finally {
    downloadLoading.value = false
  }
}

// 打开下载弹窗
function openDownloadDialog() {
  dialogData.excel_time = props.packageData?.excel_time
  dialogData.download_time = props.packageData?.download_time
  dialogData.download_url = props.packageData?.download_url
  downloadDialogVisible.value = true
  fetchHistoryFiles()
}

async function fetchHistoryFiles() {
  try {
    if (!props.packageData?.id) return
    historyLoading.value = true
    const resp = await resourcePackageApi.listFiles(props.packageData.id, 1, 50)
    if (resp.success) {
      historyFiles.value = resp.data?.items || []
    } else {
      historyFiles.value = []
    }
  } catch (e) {
    console.warn('加载历史文件失败:', e)
    historyFiles.value = []
  } finally {
    historyLoading.value = false
  }
}

function formatHistoryLabel(f: ResourcePackageFile): string {
  const t = f.generated_at ? new Date(f.generated_at).toLocaleString() : ''
  return `${f.filename} (${t})`
}

async function handleDownloadHistory() {
  try {
    if (!props.packageData?.id || !selectedFileId.value) {
      ElMessage.error('请选择需要下载的历史文件')
      return
    }
    historyDownloadLoading.value = true
    const resp = await resourcePackageApi.downloadFile(props.packageData.id, selectedFileId.value)
    if (!resp.success) {
      throw new Error(resp.message || '下载失败')
    }
    const url = resp.data?.download_url
    const filename = resp.data?.filename || ''
    if (url) {
      window.open(url, '_blank')
      try {
        const link = document.createElement('a')
        link.href = url
        link.download = filename
        document.body.appendChild(link)
        link.click()
        document.body.removeChild(link)
      } catch (e) {
        console.warn('下载链接触发失败，已尝试回退方案:', e)
      }
      ElMessage.success('正在下载历史文件...')
    } else {
      ElMessage.error('未返回下载链接')
    }
  } catch (e: any) {
    console.error('下载历史文件失败:', e)
    ElMessage.error(e.message || '下载失败，请稍后重试')
  } finally {
    historyDownloadLoading.value = false
  }
}

async function handleGenerateExcel() {
  try {
    if (!props.packageData?.id) {
      ElMessage.error('缺少资源包ID')
      return
    }
    if (!selectedIndices.value) {
      ElMessage.error('缺少索引信息，无法生成Excel')
      return
    }
    generateLoading.value = true
    const dsl = buildDSL()
    const payload: any = {
      index: selectedIndices.value,
      query: dsl.query
    }
    if (dsl._source) payload._source = dsl._source

    const resp = await resourcePackageApi.generateExcel(props.packageData.id, payload)
    if (resp?.success) {
      const hasNew = resp?.data?.has_new_data
      if (hasNew === false) {
        ElMessage.warning(resp?.message || '无最新数据，无需生成')
        // 不更新 excel_time，保持原值
      } else {
        // 更新弹窗中的下载链接
        const data = resp.data || {}
        if (data.download_url) dialogData.download_url = data.download_url
        // 仅在有新数据时刷新弹窗时间为本地当前时间
        dialogData.excel_time = new Date().toISOString()
        ElMessage.success('Excel文件生成成功')
      }
    } else {
      ElMessage.error(resp?.message || '生成Excel失败，请稍后重试')
    }
  } catch (e: any) {
    console.error('生成Excel失败:', e)
    ElMessage.error(e?.message || '生成Excel失败，请稍后重试')
  } finally {
    generateLoading.value = false
  }
}

async function handleDownloadLatest() {
  try {
    if (!props.packageData?.id) {
      ElMessage.error('缺少资源包ID')
      return
    }
    if (!dialogData.download_url) {
      ElMessage.error('暂无可下载的最新资源包，请先生成Excel')
      return
    }
    latestDownloadLoading.value = true
    const resp = await resourcePackageApi.downloadLatest(props.packageData.id)
    if (!resp.success) {
      throw new Error(resp.message || '下载失败')
    }
    const url = resp.data?.download_url || dialogData.download_url
    const filename = resp.data?.filename || ''
    if (url) {
      window.open(url, '_blank')
      try {
        const link = document.createElement('a')
        link.href = url
        link.download = filename
        document.body.appendChild(link)
        link.click()
        document.body.removeChild(link)
      } catch (e) {
        console.warn('下载链接触发失败，已尝试回退方案:', e)
      }
      // 更新最新下载时间（若后端返回）
      if (resp.data?.download_time) dialogData.download_time = resp.data.download_time
      // 使用本地当前时间作为显示值
      dialogData.download_time = new Date().toISOString()
      ElMessage.success('正在下载最新资源包...')
    } else {
      ElMessage.error('未返回下载链接')
    }
  } catch (e: any) {
    console.error('下载最新资源包失败:', e)
    ElMessage.error(e.message || '下载失败，请稍后重试')
  } finally {
    latestDownloadLoading.value = false
  }
}
</script>

<style scoped>
.es-package-query-panel {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 16px;
}

.card-title {
  font-weight: 600;
  font-size: 16px;
  color: #303133;
}

.header-search {
  display: flex;
  align-items: center;
  gap: 8px;
}

.header-actions {
  display: flex;
  gap: 8px;
}

.section-title {
  font-weight: 600;
  font-size: 13px;
  color: #606266;
}

.locked-conditions {
  margin-bottom: 8px;
}
.condition-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 6px;
}
.condition-tag {
  margin: 0;
}

.default-search {
  margin-bottom: 8px;
}
.search-controls {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 6px;
}

.query-builder {
  margin-top: 8px;
}
.qb-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}
.conditions {
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.condition-item {
  display: flex;
  align-items: center;
  gap: 8px;
}
.dash { margin: 0 6px; color: #909399; }

.results-card { }
.results-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.view-switch { display: flex; align-items: center; }
.display-toggles { display: flex; align-items: center; gap: 10px; margin-left: 12px; }

.results-grid {
  display: grid;
  grid-template-columns: 1fr 4fr; /* 20% / 80% */
  gap: 16px;
}

.agg-pane {
  border-right: 1px solid #ebeef5;
  padding-right: 8px;
}
.agg-header {
  font-weight: 600;
  color: #606266;
  margin-bottom: 8px;
}
.agg-empty { padding: 8px 0; }
.aggregations { display: flex; flex-direction: column; gap: 10px; }
.agg-card { border: 1px solid #ebeef5; border-radius: 6px; padding: 8px; }
.agg-title { font-weight: 600; margin-bottom: 6px; color: #303133; }
.agg-row { display: flex; justify-content: space-between; font-size: 12px; padding: 2px 0; }
.agg-row.clickable { cursor: pointer; padding: 4px 6px; border-radius: 4px; }
.agg-row.clickable:hover { background: #f5f7fa; }
.agg-key { color: #606266; max-width: 70%; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.agg-count { color: #303133; }
.agg-json { font-size: 12px; background: #f9fafc; padding: 8px; border-radius: 4px; overflow: auto; }

/* 表格容器样式 */
.table-container {
  width: 100%;
  height: 650px;
  overflow: auto;
  border: 1px solid #e4e7ed;
  border-radius: 4px;
}

.table-container .el-table {
  height: 100%;
}

/* 卡片容器样式 */
.cards-container {
  width: 100%;
  height: 650px;
  overflow-y: auto;
  padding: 8px;
}

.result-pane {
  flex: 1;
  padding: 16px;
  overflow: hidden;
}
.cards { display: flex; flex-direction: column; gap: 12px; }
.result-card { width: 100%; position: relative; }
.card-content { display: flex; flex-direction: column; gap: 6px; padding-bottom: 36px; }
.card-row { display: grid; grid-template-columns: repeat(3, 1fr); gap: 8px; }
.card-row.wide { grid-template-columns: 1fr; }
.kv { display: flex; gap: 6px; font-size: 13px; }
.k { color: #606266; min-width: 70px; background: #f5f7fa; padding: 0 6px; border-radius: 4px; }
.v { color: #303133; word-break: break-word; }
.v.wrap { white-space: pre-wrap; }
.cell { display: inline-block; max-width: 100%; }
.cell.wrap { white-space: pre-wrap; }
.cards.compact .kv { font-size: 12px; }
.cards.compact .card-row { gap: 6px; }

/* 卡片复制按钮固定在右下角 */
.card-copy-btn {
  position: absolute;
  right: 10px;
  bottom: 10px;
}

.no-data { padding: 20px; }
.pager { margin-top: 12px; display: flex; justify-content: flex-end; }

@media (max-width: 1024px) {
  .results-grid { grid-template-columns: 1fr 3fr; }
  .card-row { grid-template-columns: repeat(2, 1fr); }
}

@media (max-width: 768px) {
  .results-grid { grid-template-columns: 1fr; }
  .agg-pane { border-right: none; padding-right: 0; }
  .card-row { grid-template-columns: 1fr; }
}
.download-info { margin: 8px 0 4px; }
.info-row { display: flex; margin-bottom: 6px; align-items: center; }
.info-row .label { color: #606266; width: 220px; }
.info-row .value { color: #303133; }

/* 搜索关键词高亮样式 */
:deep(.highlight) {
  background-color: #fff3cd !important;
  color: #856404 !important;
  padding: 1px 2px !important;
  border-radius: 2px !important;
  font-weight: 500 !important;
}

/* 全屏模式样式 */
.results-card.fullscreen-mode {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  width: 100vw !important;
  height: 100vh !important;
  z-index: 9999;
  margin: 0;
  border-radius: 0;
}

.results-card.fullscreen-mode :deep(.el-card__body) {
  height: calc(100vh - 60px);
  overflow: auto;
}

.results-card.fullscreen-mode .results-grid {
  height: 100%;
}

.results-card.fullscreen-mode .table-container {
  height: calc(100vh - 160px);
}

.results-card.fullscreen-mode .cards-container {
  height: calc(100vh - 160px);
}
</style>