<template>
  <div class="es-query-builder">
    <!-- 查询类型选择 -->
    <div class="query-type-selector">
      <el-radio-group v-model="queryType" @change="onQueryTypeChange">
        <el-radio-button label="visual">可视化查询</el-radio-button>
        <el-radio-button label="dsl">DSL查询</el-radio-button>
      </el-radio-group>
    </div>

    <!-- 可视化查询构建器 -->
    <div v-if="queryType === 'visual'" class="visual-query-builder">
      <!-- 索引选择 -->
      <div class="query-section">
        <label class="section-label">索引选择:</label>
        <el-select
          v-model="visualQuery.indices"
          multiple
          placeholder="请选择索引"
          @change="onIndicesChange"
          style="width: 100%"
        >
          <el-option
            v-for="index in availableIndices"
            :key="index"
            :label="index"
            :value="index"
          />
        </el-select>
      </div>

      <!-- 字段选择 -->
      <div class="query-section">
        <label class="section-label">返回字段:</label>
        <el-select
          v-model="visualQuery.fields"
          multiple
          placeholder="请选择字段（留空返回所有字段）"
          style="width: 100%"
        >
          <el-option
            v-for="field in availableFields"
            :key="field.name"
            :label="`${field.name} (${field.type})`"
            :value="field.name"
          />
        </el-select>
      </div>

      <!-- 查询条件 -->
      <div class="query-section">
        <div class="section-header">
          <label class="section-label">查询条件:</label>
          <el-button type="primary" size="small" @click="addCondition">
            <el-icon><Plus /></el-icon>
            添加条件
          </el-button>
        </div>
        
        <div v-if="visualQuery.conditions.length === 0" class="empty-conditions">
          <el-text type="info">暂无查询条件，将返回所有文档</el-text>
        </div>
        
        <div v-else class="conditions-list">
          <div
            v-for="(condition, index) in visualQuery.conditions"
            :key="index"
            class="condition-item"
          >
            <!-- 逻辑操作符 -->
            <div v-if="index > 0" class="logic-operator">
              <el-select v-model="condition.logic" size="small" style="width: 80px">
                <el-option label="AND" value="must" />
                <el-option label="OR" value="should" />
                <el-option label="NOT" value="must_not" />
              </el-select>
            </div>
            
            <!-- 条件配置 -->
            <div class="condition-config">
              <!-- 字段选择 -->
              <el-select
                v-model="condition.field"
                placeholder="选择字段"
                size="small"
                style="width: 150px"
              >
                <el-option
                  v-for="field in availableFields"
                  :key="field.name"
                  :label="field.name"
                  :value="field.name"
                />
              </el-select>
              
              <!-- 操作符选择 -->
              <el-select
                v-model="condition.operator"
                size="small"
                style="width: 120px"
              >
                <el-option label="等于" value="term" />
                <el-option label="包含" value="match" />
                <el-option label="范围" value="range" />
                <el-option label="存在" value="exists" />
                <el-option label="前缀" value="prefix" />
                <el-option label="通配符" value="wildcard" />
              </el-select>
              
              <!-- 值输入 -->
              <div v-if="condition.operator === 'range'" class="range-inputs">
                <el-input
                  v-model="condition.value.gte"
                  placeholder="最小值"
                  size="small"
                  style="width: 100px"
                />
                <span class="range-separator">至</span>
                <el-input
                  v-model="condition.value.lte"
                  placeholder="最大值"
                  size="small"
                  style="width: 100px"
                />
              </div>
              <el-input
                v-else-if="condition.operator !== 'exists'"
                v-model="condition.value"
                placeholder="输入值"
                size="small"
                style="width: 200px"
              />
            </div>
            
            <!-- 删除按钮 -->
            <el-button
              type="danger"
              size="small"
              @click="removeCondition(index)"
              :icon="Delete"
            />
          </div>
        </div>
      </div>

      <!-- 排序设置 -->
      <div class="query-section">
        <div class="section-header">
          <label class="section-label">排序设置:</label>
          <el-button type="primary" size="small" @click="addSort">
            <el-icon><Plus /></el-icon>
            添加排序
          </el-button>
        </div>
        
        <div v-if="visualQuery.sort.length === 0" class="empty-sort">
          <el-text type="info">暂无排序设置</el-text>
        </div>
        
        <div v-else class="sort-list">
          <div
            v-for="(sortItem, index) in visualQuery.sort"
            :key="index"
            class="sort-item"
          >
            <el-select
              v-model="sortItem.field"
              placeholder="选择字段"
              size="small"
              style="width: 150px"
            >
              <el-option
                v-for="field in availableFields"
                :key="field.name"
                :label="field.name"
                :value="field.name"
              />
            </el-select>
            
            <el-select
              v-model="sortItem.order"
              size="small"
              style="width: 100px"
            >
              <el-option label="升序" value="asc" />
              <el-option label="降序" value="desc" />
            </el-select>
            
            <el-button
              type="danger"
              size="small"
              @click="removeSort(index)"
              :icon="Delete"
            />
          </div>
        </div>
      </div>

      <!-- 聚合查询设置 -->
      <div class="query-section">
        <div class="section-header">
          <label class="section-label">聚合查询:</label>
          <el-button type="primary" size="small" @click="addAggregation">
            <el-icon><Plus /></el-icon>
            添加聚合
          </el-button>
        </div>
        
        <div v-if="visualQuery.aggregations.length === 0" class="empty-aggregations">
          <el-text type="info">暂无聚合查询</el-text>
        </div>
        
        <div v-else class="aggregations-list">
          <div
            v-for="(agg, index) in visualQuery.aggregations"
            :key="index"
            class="aggregation-item"
          >
            <!-- 聚合名称 -->
            <el-input
              v-model="agg.name"
              placeholder="聚合名称"
              size="small"
              style="width: 120px"
            />
            
            <!-- 聚合类型 -->
            <el-select
              v-model="agg.type"
              placeholder="聚合类型"
              size="small"
              style="width: 120px"
              @change="onAggregationTypeChange(agg)"
            >
              <el-option label="计数" value="value_count" />
              <el-option label="求和" value="sum" />
              <el-option label="平均值" value="avg" />
              <el-option label="最大值" value="max" />
              <el-option label="最小值" value="min" />
              <el-option label="分组" value="terms" />
              <el-option label="日期直方图" value="date_histogram" />
              <el-option label="数值直方图" value="histogram" />
              <el-option label="范围聚合" value="range" />
            </el-select>
            
            <!-- 字段选择 -->
            <el-select
              v-model="agg.field"
              placeholder="选择字段"
              size="small"
              style="width: 150px"
            >
              <el-option
                v-for="field in availableFields"
                :key="field.name"
                :label="field.name"
                :value="field.name"
              />
            </el-select>
            
            <!-- 聚合参数配置 -->
            <div class="aggregation-params">
              <!-- Terms聚合参数 -->
              <template v-if="agg.type === 'terms'">
                <el-input-number
                  v-model="agg.params.size"
                  placeholder="返回数量"
                  :min="1"
                  :max="10000"
                  size="small"
                  style="width: 100px"
                />
                <span class="param-label">条数</span>
              </template>
              
              <!-- 日期直方图参数 -->
              <template v-if="agg.type === 'date_histogram'">
                <el-select
                  v-model="agg.params.calendar_interval"
                  placeholder="时间间隔"
                  size="small"
                  style="width: 100px"
                >
                  <el-option label="1分钟" value="1m" />
                  <el-option label="5分钟" value="5m" />
                  <el-option label="1小时" value="1h" />
                  <el-option label="1天" value="1d" />
                  <el-option label="1周" value="1w" />
                  <el-option label="1月" value="1M" />
                </el-select>
              </template>
              
              <!-- 数值直方图参数 -->
              <template v-if="agg.type === 'histogram'">
                <el-input-number
                  v-model="agg.params.interval"
                  placeholder="间隔"
                  :min="1"
                  size="small"
                  style="width: 100px"
                />
                <span class="param-label">间隔</span>
              </template>
              
              <!-- 范围聚合参数 -->
              <template v-if="agg.type === 'range'">
                <el-button size="small" @click="addRange(agg)">添加范围</el-button>
                <div v-for="(range, rangeIndex) in agg.params.ranges" :key="rangeIndex" class="range-config">
                  <el-input-number
                    v-model="range.from"
                    placeholder="起始值"
                    size="small"
                    style="width: 80px"
                  />
                  <span>-</span>
                  <el-input-number
                    v-model="range.to"
                    placeholder="结束值"
                    size="small"
                    style="width: 80px"
                  />
                  <el-button
                    type="danger"
                    size="small"
                    @click="removeRange(agg, rangeIndex)"
                    :icon="Delete"
                  />
                </div>
              </template>
            </div>
            
            <!-- 删除聚合 -->
            <el-button
              type="danger"
              size="small"
              @click="removeAggregation(index)"
              :icon="Delete"
            />
          </div>
        </div>
      </div>

      <!-- 分页设置 -->
      <div class="query-section">
        <label class="section-label">分页设置:</label>
        <div class="pagination-config">
          <el-input-number
            v-model="visualQuery.from"
            :min="0"
            :step="1"
            size="small"
            controls-position="right"
            style="width: 120px"
          />
          <span class="pagination-label">起始位置</span>
          
          <el-input-number
            v-model="visualQuery.size"
            :min="1"
            :max="10000"
            :step="1"
            size="small"
            controls-position="right"
            style="width: 120px"
          />
          <span class="pagination-label">返回数量</span>
        </div>
      </div>
      
      <!-- 可视化查询操作 -->
      <div class="query-section">
        <div class="visual-actions">
          <el-button @click="convertVisualToDSL">转换为DSL</el-button>
          <el-button @click="clearVisualQuery">清空查询</el-button>
          <el-button 
            type="success" 
            @click="openAddToResourcePackage"
            :disabled="!selectedIndex || returnFields.length === 0"
          >
            <el-icon><FolderAdd /></el-icon>
            添加到资源包
          </el-button>
        </div>
      </div>
    </div>

    <!-- DSL查询编辑器 -->
    <div v-else class="dsl-query-builder">
      <div class="query-section">
        <label class="section-label">Elasticsearch DSL查询:</label>
        <div class="dsl-editor">
          <el-input
            v-model="dslQuery"
            type="textarea"
            :rows="15"
            placeholder="请输入Elasticsearch DSL查询语句..."
            class="dsl-textarea"
          />
        </div>
        
        <div class="dsl-actions">
          <el-button @click="formatDSL">格式化</el-button>
          <el-button @click="validateDSL">验证语法</el-button>
          <el-button @click="convertDSLToVisual">转换为可视化</el-button>
          <el-button type="primary" @click="loadTemplate">加载模板</el-button>
          <el-button 
            type="success" 
            @click="openAddToResourcePackage"
            :disabled="!selectedIndex || !dslQuery.trim()"
          >
            <el-icon><FolderAdd /></el-icon>
            添加到资源包
          </el-button>
        </div>
      </div>
    </div>

    <!-- 查询预览 -->
    <div class="query-preview">
      <div class="section-header">
        <label class="section-label">查询预览:</label>
        <el-button size="small" @click="copyQuery">
          <el-icon><DocumentCopy /></el-icon>
          复制查询
        </el-button>
      </div>
      
      <el-input
        :value="generatedQuery"
        type="textarea"
        :rows="8"
        readonly
        class="query-preview-textarea"
      />
    </div>
    
    <!-- 添加到资源包对话框 -->
    <el-dialog
      v-model="resourcePackageVisible"
      title="添加到资源包"
      width="600px"
      :close-on-click-modal="false"
    >
      <el-form :model="resourcePackageForm" label-width="100px">
        <el-form-item label="资源包名称" required>
          <el-input
            v-model="resourcePackageForm.name"
            placeholder="请输入资源包名称"
            maxlength="100"
            show-word-limit
          />
        </el-form-item>
        <el-form-item label="描述">
          <el-input
            v-model="resourcePackageForm.description"
            type="textarea"
            :rows="3"
            placeholder="请输入资源包描述"
            maxlength="500"
            show-word-limit
          />
        </el-form-item>
        <el-form-item label="数据源">
          <el-input
            :value="selectedIndex"
            readonly
            placeholder="当前选择的索引"
          />
        </el-form-item>
        <el-form-item label="查询字段">
          <div class="field-tags">
            <el-tag
              v-for="field in returnFields"
              :key="field"
              type="info"
              size="small"
              style="margin-right: 8px; margin-bottom: 4px;"
            >
              {{ field }}
            </el-tag>
          </div>
        </el-form-item>
        <el-form-item label="查询条件">
          <div class="condition-summary">
            <span v-if="queryType === 'visual' && visualQuery.conditions.length === 0" class="text-muted">
              无查询条件
            </span>
            <span v-else-if="queryType === 'visual'" class="text-info">
              {{ visualQuery.conditions.length }} 个查询条件
            </span>
            <span v-else class="text-info">
              DSL查询
            </span>
          </div>
        </el-form-item>
        <el-form-item label="限制条数">
          <el-input-number
            v-model="resourcePackageForm.limitConfig"
            :min="1"
            :max="10000"
            style="width: 200px"
          />
        </el-form-item>
        <el-form-item label="标签">
          <el-select
            v-model="resourcePackageForm.tags"
            multiple
            filterable
            allow-create
            placeholder="请选择或输入标签"
            style="width: 100%"
          >
            <el-option
              v-for="tag in queryTags"
              :key="tag"
              :label="tag"
              :value="tag"
            />
          </el-select>
        </el-form-item>
      </el-form>
      
      <template #footer>
        <div class="dialog-footer">
          <el-button @click="resourcePackageVisible = false">取消</el-button>
          <el-button type="primary" @click="confirmAddToResourcePackage" :loading="creatingResourcePackage">
            创建资源包
          </el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, watch, nextTick } from 'vue'
import { ElMessage } from 'element-plus'
import { Plus, Delete, DocumentCopy, FolderAdd } from '@element-plus/icons-vue'
import { resourcePackageApi, PackageType } from '@/api/resourcePackage'

/**
 * ES查询构建器组件的属性定义
 */
interface Props {
  /** 可用的索引列表 */
  availableIndices?: string[]
  /** 可用的字段列表 */
  availableFields?: Array<{
    name: string
    type: string
    index: string
  }>
  /** 初始查询配置 */
  initialQuery?: any
}

/**
 * ES查询构建器组件的事件定义
 */
interface Emits {
  /** 查询变化事件 */
  (e: 'query-change', query: any): void
  /** 索引变化事件 */
  (e: 'indices-change', indices: string[]): void
  /** 添加到资源包事件 */
  (e: 'add-to-resource-package', data: any): void
}

const props = withDefaults(defineProps<Props>(), {
  availableIndices: () => [],
  availableFields: () => [],
  initialQuery: () => ({})
})

const emit = defineEmits<Emits>()

// 查询类型：visual（可视化）或 dsl（DSL查询）
const queryType = ref<'visual' | 'dsl'>('visual')

// 资源包相关状态
const resourcePackageVisible = ref(false)
const creatingResourcePackage = ref(false)

// 可视化查询配置
const visualQuery = ref({
  indices: [] as string[],
  fields: [] as string[],
  conditions: [] as Array<{
    logic: 'must' | 'should' | 'must_not'
    field: string
    operator: 'term' | 'match' | 'range' | 'exists' | 'prefix' | 'wildcard'
    value: any
  }>,
  sort: [] as Array<{
    field: string
    order: 'asc' | 'desc'
  }>,
  aggregations: [] as Array<{
    name: string
    type: 'value_count' | 'sum' | 'avg' | 'max' | 'min' | 'terms' | 'date_histogram' | 'histogram' | 'range'
    field: string
    params: any
  }>,
  from: 0,
  size: 10
})

// DSL查询字符串
const dslQuery = ref('')

// 资源包表单
const resourcePackageForm = reactive({
  name: '',
  description: '',
  limitConfig: 1000,
  tags: [] as string[]
})

// 查询标签
const queryTags = ref<string[]>(['常用查询', '报表查询', '数据分析', '业务查询'])

/**
 * 生成的查询语句
 */
const generatedQuery = computed(() => {
  if (queryType.value === 'dsl') {
    try {
      return JSON.stringify(JSON.parse(dslQuery.value), null, 2)
    } catch {
      return dslQuery.value
    }
  }
  
  // 构建可视化查询的DSL
  const query: any = {
    query: {},
    from: visualQuery.value.from,
    size: visualQuery.value.size
  }
  
  // 构建查询条件
  if (visualQuery.value.conditions.length === 0) {
    query.query = { match_all: {} }
  } else {
    const boolQuery: any = {
      must: [],
      should: [],
      must_not: []
    }
    
    visualQuery.value.conditions.forEach(condition => {
      const conditionQuery = buildConditionQuery(condition)
      if (conditionQuery) {
        boolQuery[condition.logic || 'must'].push(conditionQuery)
      }
    })
    
    // 清理空的查询数组
    Object.keys(boolQuery).forEach(key => {
      if (boolQuery[key].length === 0) {
        delete boolQuery[key]
      }
    })
    
    query.query = { bool: boolQuery }
  }
  
  // 添加字段选择
  if (visualQuery.value.fields.length > 0) {
    query._source = visualQuery.value.fields
  }
  
  // 添加排序
  if (visualQuery.value.sort.length > 0) {
    query.sort = visualQuery.value.sort.map(sortItem => ({
      [sortItem.field]: { order: sortItem.order }
    }))
  }
  
  // 添加聚合查询
  if (visualQuery.value.aggregations.length > 0) {
    query.aggs = {}
    visualQuery.value.aggregations.forEach(agg => {
      if (agg.name && agg.field) {
        query.aggs[agg.name] = buildAggregationQuery(agg)
      }
    })
  }
  
  return JSON.stringify(query, null, 2)
})

/**
 * 构建单个查询条件
 */
function buildConditionQuery(condition: any) {
  if (!condition.field) return null
  
  switch (condition.operator) {
    case 'term':
      return { term: { [condition.field]: condition.value } }
    case 'match':
      return { match: { [condition.field]: condition.value } }
    case 'range':
      const rangeQuery: any = {}
      if (condition.value?.gte !== undefined && condition.value.gte !== '') {
        rangeQuery.gte = condition.value.gte
      }
      if (condition.value?.lte !== undefined && condition.value.lte !== '') {
        rangeQuery.lte = condition.value.lte
      }
      return Object.keys(rangeQuery).length > 0 ? { range: { [condition.field]: rangeQuery } } : null
    case 'exists':
      return { exists: { field: condition.field } }
    case 'prefix':
      return { prefix: { [condition.field]: condition.value } }
    case 'wildcard':
      return { wildcard: { [condition.field]: condition.value } }
    default:
      return null
  }
}

/**
 * 构建聚合查询
 * @param agg 聚合配置
 */
function buildAggregationQuery(agg: any) {
  const aggQuery: any = {}
  
  switch (agg.type) {
    case 'value_count':
    case 'sum':
    case 'avg':
    case 'max':
    case 'min':
      aggQuery[agg.type] = { field: agg.field }
      break
    case 'terms':
      aggQuery.terms = {
        field: agg.field,
        size: agg.params?.size || 10
      }
      break
    case 'date_histogram':
      aggQuery.date_histogram = {
        field: agg.field,
        calendar_interval: agg.params?.calendar_interval || '1d'
      }
      break
    case 'histogram':
      aggQuery.histogram = {
        field: agg.field,
        interval: agg.params?.interval || 1
      }
      break
    case 'range':
      aggQuery.range = {
        field: agg.field,
        ranges: agg.params?.ranges || [{ from: 0, to: 100 }]
      }
      break
  }
  
  return aggQuery
}

/**
 * 查询类型变化处理
 */
function onQueryTypeChange() {
  if (queryType.value === 'dsl') {
    // 从可视化查询转换为DSL
    convertVisualToDSL()
  } else {
    // 从DSL转换为可视化查询
    convertDSLToVisual()
  }
  emitQueryChange()
}

/**
 * 将可视化查询转换为DSL
 */
function convertVisualToDSL() {
  try {
    const query: any = {
      from: visualQuery.value.from || 0,
      size: visualQuery.value.size || 10
    }
    
    // 构建查询条件
    if (visualQuery.value.conditions.length === 0) {
      query.query = { match_all: {} }
    } else {
      const boolQuery: any = {
        must: [],
        should: [],
        must_not: []
      }
      
      visualQuery.value.conditions.forEach(condition => {
        const conditionQuery = buildConditionQuery(condition)
        if (conditionQuery) {
          const logic = condition.logic || 'must'
          boolQuery[logic].push(conditionQuery)
        }
      })
      
      // 清理空的查询数组
      Object.keys(boolQuery).forEach(key => {
        if (boolQuery[key].length === 0) {
          delete boolQuery[key]
        }
      })
      
      query.query = { bool: boolQuery }
    }
    
    // 添加字段选择
    if (visualQuery.value.fields.length > 0) {
      query._source = visualQuery.value.fields
    }
    
    // 添加排序
    if (visualQuery.value.sort.length > 0) {
      query.sort = visualQuery.value.sort.map(sortItem => ({
        [sortItem.field]: { order: sortItem.order }
      }))
    }
    
    // 添加聚合查询
    if (visualQuery.value.aggregations.length > 0) {
      query.aggs = {}
      visualQuery.value.aggregations.forEach(agg => {
        if (agg.name && agg.field) {
          query.aggs[agg.name] = buildAggregationQuery(agg)
        }
      })
    }
    
    dslQuery.value = JSON.stringify(query, null, 2)
  } catch (error) {
    console.error('转换为DSL失败:', error)
    ElMessage.error('转换为DSL失败')
  }
}

/**
 * 将DSL转换为可视化查询
 */
function convertDSLToVisual() {
  try {
    if (!dslQuery.value.trim()) {
      return
    }
    
    const parsedDSL = JSON.parse(dslQuery.value)
    
    // 重置可视化查询
    visualQuery.value = {
      indices: visualQuery.value.indices, // 保持索引选择
      fields: [],
      conditions: [],
      sort: [],
      aggregations: [],
      from: 0,
      size: 10
    }
    
    // 解析字段选择
    if (parsedDSL._source) {
      visualQuery.value.fields = Array.isArray(parsedDSL._source) ? parsedDSL._source : []
    }
    
    // 解析分页
    if (parsedDSL.from !== undefined) {
      visualQuery.value.from = parsedDSL.from
    }
    if (parsedDSL.size !== undefined) {
      visualQuery.value.size = parsedDSL.size
    }
    
    // 解析排序
    if (parsedDSL.sort && Array.isArray(parsedDSL.sort)) {
      visualQuery.value.sort = parsedDSL.sort.map(sortItem => {
        const field = Object.keys(sortItem)[0]
        const order = sortItem[field].order || 'asc'
        return { field, order }
      })
    }
    
    // 解析查询条件
    if (parsedDSL.query) {
      parseQueryConditions(parsedDSL.query)
    }
    
    // 解析聚合
    if (parsedDSL.aggs) {
      parseAggregations(parsedDSL.aggs)
    }
    
    ElMessage.success('DSL转换为可视化查询成功')
  } catch (error) {
    console.error('DSL转换失败:', error)
    ElMessage.error('DSL格式错误，无法转换为可视化查询')
  }
}

/**
 * 解析查询条件
 */
function parseQueryConditions(query: any, logic: string = 'must') {
  if (query.match_all) {
    // match_all查询，不添加条件
    return
  }
  
  if (query.bool) {
    // 布尔查询
    Object.keys(query.bool).forEach(boolType => {
      const conditions = query.bool[boolType]
      if (Array.isArray(conditions)) {
        conditions.forEach(condition => {
          parseQueryConditions(condition, boolType)
        })
      }
    })
    return
  }
  
  // 解析具体查询类型
  const conditionTypes = ['term', 'match', 'range', 'exists', 'prefix', 'wildcard', 'terms', 'match_phrase']
  
  for (const type of conditionTypes) {
    if (query[type]) {
      const condition: any = {
        logic: logic,
        operator: type
      }
      
      if (type === 'exists') {
        condition.field = query[type].field
        condition.value = ''
      } else {
        const field = Object.keys(query[type])[0]
        condition.field = field
        
        if (type === 'range') {
          const rangeValue = query[type][field]
          condition.value = {
            gte: rangeValue.gte || '',
            lte: rangeValue.lte || ''
          }
        } else if (type === 'terms') {
          condition.operator = 'term' // 简化为term操作
          condition.value = Array.isArray(query[type][field]) ? query[type][field][0] : query[type][field]
        } else {
          condition.value = query[type][field]
        }
      }
      
      visualQuery.value.conditions.push(condition)
      break
    }
  }
}

/**
 * 解析聚合查询
 */
function parseAggregations(aggs: any) {
  Object.keys(aggs).forEach(aggName => {
    const aggConfig = aggs[aggName]
    const aggTypes = ['terms', 'sum', 'avg', 'max', 'min', 'value_count', 'date_histogram', 'histogram', 'range']
    
    for (const type of aggTypes) {
      if (aggConfig[type]) {
        const aggregation: any = {
          name: aggName,
          type: type,
          field: aggConfig[type].field || '',
          params: {}
        }
        
        // 解析聚合参数
        if (type === 'terms' && aggConfig[type].size) {
          aggregation.params.size = aggConfig[type].size
        } else if (type === 'date_histogram' && aggConfig[type].calendar_interval) {
          aggregation.params.calendar_interval = aggConfig[type].calendar_interval
        } else if (type === 'histogram' && aggConfig[type].interval) {
          aggregation.params.interval = aggConfig[type].interval
        } else if (type === 'range' && aggConfig[type].ranges) {
          aggregation.params.ranges = aggConfig[type].ranges
        }
        
        visualQuery.value.aggregations.push(aggregation)
        break
      }
    }
  })
}

/**
 * 索引变化处理
 */
function onIndicesChange() {
  emit('indices-change', visualQuery.value.indices)
  emitQueryChange()
}

/**
 * 添加查询条件
 */
function addCondition() {
  visualQuery.value.conditions.push({
    logic: 'must',
    field: '',
    operator: 'term',
    value: ''
  })
}

/**
 * 移除查询条件
 */
function removeCondition(index: number) {
  visualQuery.value.conditions.splice(index, 1)
  emitQueryChange()
}

/**
 * 添加排序
 */
function addSort() {
  visualQuery.value.sort.push({
    field: '',
    order: 'asc'
  })
}

/**
 * 移除排序
 */
function removeSort(index: number) {
  visualQuery.value.sort.splice(index, 1)
  emitQueryChange()
}

/**
 * 添加聚合查询
 */
function addAggregation() {
  visualQuery.value.aggregations.push({
    name: `agg_${Date.now()}`,
    type: 'value_count',
    field: '',
    params: {}
  })
  emitQueryChange()
}

/**
 * 移除聚合查询
 * @param index 聚合查询索引
 */
function removeAggregation(index: number) {
  visualQuery.value.aggregations.splice(index, 1)
  emitQueryChange()
}

/**
 * 聚合类型变化处理
 * @param agg 聚合配置
 */
function onAggregationTypeChange(agg: any) {
  // 根据聚合类型设置默认参数
  switch (agg.type) {
    case 'terms':
      agg.params = { size: 10 }
      break
    case 'date_histogram':
      agg.params = { calendar_interval: '1d' }
      break
    case 'histogram':
      agg.params = { interval: 1 }
      break
    case 'range':
      agg.params = { ranges: [{ from: 0, to: 100 }] }
      break
    default:
      agg.params = {}
  }
  
  emitQueryChange()
}

/**
 * 格式化DSL查询
 */
function formatDSL() {
  try {
    const parsed = JSON.parse(dslQuery.value)
    dslQuery.value = JSON.stringify(parsed, null, 2)
    ElMessage.success('DSL格式化成功')
  } catch (error) {
    ElMessage.error('DSL格式错误，无法格式化')
  }
}

/**
 * 验证DSL语法
 */
function validateDSL() {
  try {
    JSON.parse(dslQuery.value)
    ElMessage.success('DSL语法正确')
  } catch (error) {
    ElMessage.error('DSL语法错误')
  }
}

/**
 * 加载查询模板
 */
function loadTemplate() {
  const template = {
    query: {
      bool: {
        must: [
          { match: { "field_name": "value" } }
        ]
      }
    },
    from: 0,
    size: 10
  }
  
  dslQuery.value = JSON.stringify(template, null, 2)
  emitQueryChange()
}

/**
 * 复制查询语句
 */
function copyQuery() {
  navigator.clipboard.writeText(generatedQuery.value).then(() => {
    ElMessage.success('查询语句已复制到剪贴板')
  }).catch(() => {
    ElMessage.error('复制失败')
  })
}

/**
 * 清空可视化查询
 */
function clearVisualQuery() {
  visualQuery.value = {
    indices: [],
    fields: [],
    conditions: [],
    sort: [],
    aggregations: [],
    from: 0,
    size: 10
  }
  emitQueryChange()
  ElMessage.success('可视化查询已清空')
}

/**
 * 添加范围
 */
function addRange(agg: any) {
  if (!agg.params.ranges) {
    agg.params.ranges = []
  }
  agg.params.ranges.push({ from: 0, to: 100 })
  emitQueryChange()
}

/**
 * 移除范围
 */
function removeRange(agg: any, rangeIndex: number) {
  agg.params.ranges.splice(rangeIndex, 1)
  emitQueryChange()
}

/**
 * 发送查询变化事件
 */
function emitQueryChange() {
  // 防止递归更新，添加防抖机制
  if (emitQueryChange._isEmitting) {
    return
  }
  
  emitQueryChange._isEmitting = true
  
  nextTick(() => {
    const query = queryType.value === 'dsl' 
      ? { type: 'dsl', query: dslQuery.value }
      : { type: 'visual', query: visualQuery.value }
    
    emit('query-change', query)
    emitQueryChange._isEmitting = false
  })
}

/**
 * 加载查询（供外部调用）
 */
const loadQuery = (query: any) => {
  if (!query) return
  
  queryType.value = query.type || 'visual'
  if (query.type === 'visual') {
    Object.assign(visualQuery.value, query.query)
  } else {
    dslQuery.value = typeof query.query === 'string' ? query.query : JSON.stringify(query.query, null, 2)
  }
  emitQueryChange()
}

// 监听查询变化
watch([visualQuery, dslQuery], () => {
  emitQueryChange()
}, { deep: true })

// 监听初始查询变化
watch(() => props.initialQuery, (newQuery) => {
  if (newQuery) {
    loadQuery(newQuery)
  }
}, { immediate: true })

/**
 * 组件初始化
 */
onMounted(async () => {
  // 如果传入了初始数据源ID，设置为默认选中
  if (props.initialDatasourceId) {
    queryConfig.datasourceId = props.initialDatasourceId
    // 触发数据源变更，加载对应的索引列表
    await onDatasourceChange()
    
    // 如果传入了初始索引，设置为默认选中
    if (props.initialIndices && props.initialIndices.length > 0) {
      queryConfig.index = props.initialIndices
      // 加载索引字段
      await onIndexChange()
    }
  }
})

/**
 * 打开添加到资源包对话框
 */
const openAddToResourcePackage = () => {
  if (!selectedIndex || (queryType.value === 'visual' && returnFields.length === 0) || (queryType.value === 'dsl' && !dslQuery.value.trim())) {
    ElMessage.warning('请先配置查询条件')
    return
  }
  
  // 重置表单
  resourcePackageForm.name = ''
  resourcePackageForm.description = ''
  resourcePackageForm.limitConfig = 1000
  resourcePackageForm.tags = []
  
  resourcePackageVisible.value = true
}

/**
 * 确认添加到资源包
 */
const confirmAddToResourcePackage = async () => {
  if (!resourcePackageForm.name.trim()) {
    ElMessage.warning('请输入资源包名称')
    return
  }
  
  try {
    creatingResourcePackage.value = true
    
    // 构建资源包数据
    const packageData = {
      name: resourcePackageForm.name,
      description: resourcePackageForm.description,
      packageType: PackageType.ES_QUERY,
      datasourceId: selectedIndex, // ES使用索引名作为数据源标识
      queryFields: queryType.value === 'visual' ? returnFields : [],
      queryConditions: queryType.value === 'visual' ? visualQuery.conditions : [],
      limitConfig: resourcePackageForm.limitConfig,
      tags: resourcePackageForm.tags,
      esQuery: generatedQuery.value
    }
    
    await resourcePackageApi.create(packageData)
    
    ElMessage.success('资源包创建成功')
    resourcePackageVisible.value = false
    
    // 触发事件通知父组件
    emit('add-to-resource-package', packageData)
    
  } catch (error) {
    console.error('创建资源包失败:', error)
    ElMessage.error('创建资源包失败')
  } finally {
    creatingResourcePackage.value = false
  }
}

// 暴露方法给父组件
defineExpose({
  loadQuery
})
</script>

<style scoped>
.es-query-builder {
  padding: 20px;
  background: #fff;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.query-type-selector {
  margin-bottom: 20px;
  text-align: center;
}

.query-section {
  margin-bottom: 20px;
}

.section-label {
  display: block;
  margin-bottom: 8px;
  font-weight: 600;
  color: #333;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.empty-conditions,
.empty-sort {
  padding: 20px;
  text-align: center;
  background: #f5f7fa;
  border-radius: 4px;
}

.conditions-list,
.sort-list {
  space-y: 12px;
}

.condition-item,
.sort-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  background: #f8f9fa;
  border-radius: 6px;
  margin-bottom: 8px;
}

.logic-operator {
  min-width: 80px;
}

.condition-config {
  display: flex;
  align-items: center;
  gap: 8px;
  flex: 1;
}

.range-inputs {
  display: flex;
  align-items: center;
  gap: 8px;
}

.range-separator {
  color: #666;
  font-size: 12px;
}

.pagination-config {
  display: flex;
  align-items: center;
  gap: 12px;
}

.pagination-label {
  color: #666;
  font-size: 14px;
}

.dsl-editor {
  margin-bottom: 12px;
}

.dsl-textarea {
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
}

.dsl-actions {
  display: flex;
  gap: 8px;
}

.visual-actions {
  text-align: right;
  padding-top: 10px;
}

.visual-actions .el-button {
  margin-left: 10px;
}

.query-preview {
  margin-top: 20px;
  padding-top: 20px;
  border-top: 1px solid #e4e7ed;
}

.query-preview-textarea {
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
  background: #f5f7fa;
}
</style>