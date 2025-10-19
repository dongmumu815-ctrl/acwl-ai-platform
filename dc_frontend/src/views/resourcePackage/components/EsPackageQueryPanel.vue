<template>
  <div class="es-package-query-panel">
    <!-- 标题与操作 -->
    <el-card class="header-card">
      <template #header>
        <div class="card-header">
          <span class="card-title">Elasticsearch 查询</span>
          <div class="header-actions">
            <el-button size="small" @click="resetConditions">重置</el-button>
            <el-button type="primary" size="small" :loading="loading" @click="executeQuery">执行查询</el-button>
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
      <div class="query-builder">
        <div class="qb-header">
          <span class="section-title">查询条件</span>
          <el-button size="small" @click="addCondition" :disabled="availableFieldNames.length === 0">
            <el-icon><Plus /></el-icon>
            添加条件
          </el-button>
        </div>
        <div v-if="conditions.length === 0" class="empty-hint">
          <el-empty description="暂无查询条件，点击上方“添加条件”进行配置" :image-size="60" />
        </div>
        <div v-else class="conditions">
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
    <el-card class="results-card" v-loading="loading">
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
            <el-table :data="records" border stripe :size="compactMode ? 'small' : 'default'" style="width: 100%">
              <el-table-column type="index" label="#" width="60" />
              <el-table-column v-for="col in displayFields" :key="col" :prop="col" :label="col" min-width="160" :show-overflow-tooltip="!wrapLongText">
                <template #default="{ row }">
                  <span class="cell" :class="{ wrap: wrapLongText }" :title="formatCell(row[col])">{{ formatText(formatCell(row[col]), 160) }}</span>
                </template>
              </el-table-column>
            </el-table>
          </template>

          <template v-else>
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
                        <span class="v" :class="{ wrap: wrapLongText }" :title="formatCell(row[f])">{{ formatText(formatCell(row[f]), chunk.wide ? WIDE_MAX_CHARS : DEFAULT_MAX_CHARS) }}</span>
                      </div>
                    </div>
                  </template>
                </div>
              </el-card>
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
  </div>
  
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Lock, Plus, Delete, CopyDocument } from '@element-plus/icons-vue'
import { templateApi } from '@/api/template'
import { executeESQuery, getESFieldMapping } from '@/api/esQuery'
import { dataResourceApi } from '@/api/dataResource'

const props = defineProps<{ packageData: any }>()

const loading = ref(false)
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

const viewMode = ref<'list' | 'card'>('list')
const compactMode = ref(false)
const wrapLongText = ref(false)
const results = ref<any | null>(null)
const records = computed<any[]>(() => {
  const hits = results.value?.hits?.hits || []
  return hits.map((h: any) => h._source)
})

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

function formatText(text: string, max: number): string {
  if (!text) return ''
  return text.length > max ? text.slice(0, max - 1) + '…' : text
}

function copyRow(row: Record<string, any>) {
  try {
    navigator.clipboard.writeText(JSON.stringify(row, null, 2))
    ElMessage.success('复制成功')
  } catch (e) {
    ElMessage.error('复制失败')
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
}
.card-title {
  font-weight: 600;
  color: #303133;
  font-size: 16px;
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

.result-pane { }
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
</style>