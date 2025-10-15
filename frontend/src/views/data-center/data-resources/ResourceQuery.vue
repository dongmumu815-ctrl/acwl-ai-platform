<template>
  <div class="resource-query">
    <div class="page-header">
      <el-button @click="handleBack" style="margin-right: 16px;">
        <el-icon><ArrowLeft /></el-icon>
        返回
      </el-button>
      <div>
        <h1>数据查询 - {{ resource?.display_name }}</h1>
        <p>对 {{ resource?.name }} 进行数据查询</p>
      </div>
    </div>

    <div class="query-container">
      <el-row :gutter="20">
        <el-col :span="24">
          <!-- 查询编辑器 -->
          <el-card title="SQL查询" class="query-card">
            <template #extra>
              <el-button-group>
                <el-button @click="handleFormat">格式化</el-button>
                <el-button @click="handleClear">清空</el-button>
                <el-button type="primary" :loading="executing" @click="handleExecute">
                  <el-icon><CaretRight /></el-icon>
                  执行查询
                </el-button>
              </el-button-group>
            </template>
            
            <div class="query-editor">
              <el-input
                v-model="queryText"
                type="textarea"
                :rows="8"
                placeholder="请输入SQL查询语句..."
                class="sql-textarea"
              />
            </div>
            
            <div class="query-info">
              <el-row :gutter="16">
                <el-col :span="8">
                  <el-form-item label="限制行数:">
                    <el-input-number v-model="queryParams.limit" :min="1" :max="10000" />
                  </el-form-item>
                </el-col>
                <el-col :span="8">
                  <el-form-item label="偏移量:">
                    <el-input-number v-model="queryParams.offset" :min="0" />
                  </el-form-item>
                </el-col>
                <el-col :span="8">
                  <el-form-item label="导出格式:">
                    <el-select v-model="queryParams.format">
                      <el-option label="JSON" value="json" />
                      <el-option label="CSV" value="csv" />
                      <el-option label="Excel" value="excel" />
                    </el-select>
                  </el-form-item>
                </el-col>
              </el-row>
            </div>
          </el-card>
        </el-col>
      </el-row>

      <el-row :gutter="20" style="margin-top: 20px;">
        <el-col :span="18">
          <!-- 查询结果 -->
          <el-card title="查询结果" class="result-card">
            <template #extra>
              <div v-if="queryResult">
                <span style="margin-right: 16px;">
                  共 {{ queryResult.total_count }} 行，
                  执行时间: {{ queryResult.execution_time }}ms
                </span>
                <el-button @click="handleExport">导出结果</el-button>
              </div>
            </template>
            
            <div v-loading="executing" class="result-content">
              <div v-if="!queryResult && !executing" class="empty-result">
                <el-empty description="暂无查询结果" />
              </div>
              
              <div v-else-if="queryResult" class="result-table">
                <el-table
                  :data="queryResult.data"
                  stripe
                  border
                  max-height="400"
                  style="width: 100%"
                >
                  <el-table-column
                    v-for="(column, index) in queryResult.columns"
                    :key="index"
                    :prop="index.toString()"
                    :label="column"
                    min-width="120"
                    show-overflow-tooltip
                  >
                    <template #default="{ row }">
                      {{ formatCellValue(row[index]) }}
                    </template>
                  </el-table-column>
                </el-table>
              </div>
            </div>
          </el-card>
        </el-col>

        <el-col :span="6">
          <!-- 查询历史 -->
          <el-card title="查询历史" class="history-card">
            <div class="history-list">
              <div
                v-for="(history, index) in queryHistory"
                :key="index"
                class="history-item"
                @click="handleLoadHistory(history)"
              >
                <div class="history-query">{{ truncateQuery(history.query) }}</div>
                <div class="history-meta">
                  <span>{{ history.result_count }} 行</span>
                  <span>{{ history.execution_time }}ms</span>
                </div>
                <div class="history-time">{{ formatDate(history.created_at) }}</div>
              </div>
              
              <div v-if="!queryHistory.length" class="empty-history">
                <el-empty description="暂无查询历史" />
              </div>
            </div>
          </el-card>

          <!-- 表结构 -->
          <el-card title="表结构" class="schema-card" style="margin-top: 20px;">
            <div class="schema-list">
              <div
                v-for="field in resource?.fields"
                :key="field.name"
                class="schema-item"
                @click="handleInsertField(field.name)"
              >
                <div class="field-name">{{ field.name }}</div>
                <div class="field-type">{{ field.type }}</div>
                <div v-if="field.description" class="field-desc">{{ field.description }}</div>
              </div>
            </div>
          </el-card>
        </el-col>
      </el-row>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { ArrowLeft, CaretRight } from '@element-plus/icons-vue'
import type { DataResource, DataResourceQueryRequest, DataResourceQueryResponse, DataResourceQueryHistory } from '@/types/data-resource'

/**
 * 路由实例
 */
const route = useRoute()
const router = useRouter()

/**
 * 响应式数据
 */
const resource = ref<DataResource | null>(null)
const queryText = ref('')
const executing = ref(false)
const queryResult = ref<DataResourceQueryResponse | null>(null)
const queryHistory = ref<DataResourceQueryHistory[]>([])

/**
 * 查询参数
 */
const queryParams = reactive<DataResourceQueryRequest>({
  query: '',
  limit: 100,
  offset: 0,
  format: 'json'
})

/**
 * 获取资源详情
 */
const fetchResourceDetail = async () => {
  const id = route.params.id as string
  
  try {
    // TODO: 调用API获取详情
    // const response = await dataResourceApi.getDetail(Number(id))
    // resource.value = response.data
    
    // 模拟数据
    resource.value = {
      id: Number(id),
      name: 'user_behavior',
      display_name: '用户行为数据',
      description: '用户行为分析数据表',
      resource_type: 'doris_table',
      status: 'active',
      category_id: 1,
      tags: [],
      connection_config: { host: 'localhost', port: 9030 },
      table_name: 'user_behavior',
      fields: [
        {
          name: 'user_id',
          type: 'BIGINT',
          description: '用户ID',
          is_nullable: false,
          is_primary_key: true,
          is_index: true
        },
        {
          name: 'action_type',
          type: 'VARCHAR(50)',
          description: '操作类型',
          is_nullable: false,
          is_primary_key: false,
          is_index: true
        },
        {
          name: 'timestamp',
          type: 'DATETIME',
          description: '操作时间',
          is_nullable: false,
          is_primary_key: false,
          is_index: true
        }
      ],
      created_by: 1,
      created_at: '2024-01-01T00:00:00Z',
      updated_at: '2024-01-01T00:00:00Z',
      is_public: true,
      access_count: 0,
      favorite_count: 0
    }
  } catch (error) {
    ElMessage.error('获取资源详情失败')
  }
}

/**
 * 获取查询历史
 */
const fetchQueryHistory = async () => {
  try {
    // TODO: 调用API获取查询历史
    // const response = await dataResourceApi.getQueryHistory(Number(route.params.id))
    // queryHistory.value = response.data
    
    // 模拟数据
    queryHistory.value = [
      {
        id: 1,
        resource_id: Number(route.params.id),
        user_id: 1,
        query: 'SELECT * FROM user_behavior LIMIT 10',
        result_count: 10,
        execution_time: 150,
        created_at: '2024-01-01T10:00:00Z'
      }
    ]
  } catch (error) {
    ElMessage.error('获取查询历史失败')
  }
}

/**
 * 执行查询
 */
const handleExecute = async () => {
  if (!queryText.value.trim()) {
    ElMessage.warning('请输入查询语句')
    return
  }
  
  executing.value = true
  queryParams.query = queryText.value
  
  try {
    // TODO: 调用查询API
    // const response = await dataResourceApi.query(Number(route.params.id), queryParams)
    // queryResult.value = response.data
    
    // 模拟数据
    await new Promise(resolve => setTimeout(resolve, 1000))
    queryResult.value = {
      columns: ['user_id', 'action_type', 'timestamp'],
      data: [
        [1001, 'login', '2024-01-01 10:00:00'],
        [1002, 'view_page', '2024-01-01 10:01:00'],
        [1003, 'click_button', '2024-01-01 10:02:00']
      ],
      total_count: 3,
      execution_time: 150,
      query_id: 'query_123'
    }
    
    ElMessage.success('查询执行成功')
    fetchQueryHistory()
  } catch (error) {
    ElMessage.error('查询执行失败')
  } finally {
    executing.value = false
  }
}

/**
 * 格式化查询
 */
const handleFormat = () => {
  // 简单的SQL格式化
  queryText.value = queryText.value
    .replace(/\s+/g, ' ')
    .replace(/\s*,\s*/g, ',\n  ')
    .replace(/\s+FROM\s+/gi, '\nFROM ')
    .replace(/\s+WHERE\s+/gi, '\nWHERE ')
    .replace(/\s+ORDER\s+BY\s+/gi, '\nORDER BY ')
    .replace(/\s+GROUP\s+BY\s+/gi, '\nGROUP BY ')
    .replace(/\s+LIMIT\s+/gi, '\nLIMIT ')
}

/**
 * 清空查询
 */
const handleClear = () => {
  queryText.value = ''
  queryResult.value = null
}

/**
 * 导出结果
 */
const handleExport = () => {
  if (!queryResult.value) return
  
  // TODO: 实现导出功能
  ElMessage.success('导出功能开发中...')
}

/**
 * 加载历史查询
 */
const handleLoadHistory = (history: DataResourceQueryHistory) => {
  queryText.value = history.query
}

/**
 * 插入字段名
 */
const handleInsertField = (fieldName: string) => {
  const textarea = document.querySelector('.sql-textarea textarea') as HTMLTextAreaElement
  if (textarea) {
    const start = textarea.selectionStart
    const end = textarea.selectionEnd
    const text = queryText.value
    queryText.value = text.substring(0, start) + fieldName + text.substring(end)
    
    // 设置光标位置
    setTimeout(() => {
      textarea.focus()
      textarea.setSelectionRange(start + fieldName.length, start + fieldName.length)
    }, 0)
  }
}

/**
 * 返回上一页
 */
const handleBack = () => {
  router.back()
}

/**
 * 截断查询文本
 */
const truncateQuery = (query: string) => {
  return query.length > 50 ? query.substring(0, 50) + '...' : query
}

/**
 * 格式化单元格值
 */
const formatCellValue = (value: any) => {
  if (value === null || value === undefined) return '-'
  if (typeof value === 'string' && value.length > 100) {
    return value.substring(0, 100) + '...'
  }
  return value
}

/**
 * 格式化日期
 */
const formatDate = (date: string) => {
  return new Date(date).toLocaleString()
}

/**
 * 组件挂载时获取数据
 */
onMounted(() => {
  fetchResourceDetail()
  fetchQueryHistory()
  
  // 设置默认查询
  queryText.value = `SELECT * FROM ${route.params.id === '1' ? 'user_behavior' : 'table_name'} LIMIT 10`
})
</script>

<style scoped>
.resource-query {
  padding: 20px;
}

.page-header {
  display: flex;
  align-items: flex-start;
  margin-bottom: 20px;
}

.page-header h1 {
  margin: 0 0 8px 0;
  font-size: 24px;
  font-weight: 600;
}

.page-header p {
  margin: 0;
  color: #666;
}

.query-container {
  min-height: 600px;
}

.query-card,
.result-card,
.history-card,
.schema-card {
  margin-bottom: 20px;
}

.query-editor {
  margin-bottom: 16px;
}

.sql-textarea :deep(.el-textarea__inner) {
  font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
  font-size: 14px;
  line-height: 1.5;
}

.query-info {
  padding: 16px;
  background: #f5f5f5;
  border-radius: 4px;
}

.result-content {
  min-height: 300px;
}

.empty-result {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 300px;
}

.result-table {
  max-height: 400px;
  overflow: auto;
}

.history-list {
  max-height: 300px;
  overflow-y: auto;
}

.history-item {
  padding: 12px;
  border-bottom: 1px solid #eee;
  cursor: pointer;
  transition: background-color 0.2s;
}

.history-item:hover {
  background-color: #f5f5f5;
}

.history-query {
  font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
  font-size: 12px;
  margin-bottom: 4px;
  color: #333;
}

.history-meta {
  display: flex;
  justify-content: space-between;
  font-size: 11px;
  color: #666;
  margin-bottom: 4px;
}

.history-time {
  font-size: 11px;
  color: #999;
}

.empty-history {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 200px;
}

.schema-list {
  max-height: 300px;
  overflow-y: auto;
}

.schema-item {
  padding: 8px;
  border-bottom: 1px solid #eee;
  cursor: pointer;
  transition: background-color 0.2s;
}

.schema-item:hover {
  background-color: #f5f5f5;
}

.field-name {
  font-weight: 600;
  color: #333;
  margin-bottom: 2px;
}

.field-type {
  font-size: 12px;
  color: #666;
  margin-bottom: 2px;
}

.field-desc {
  font-size: 11px;
  color: #999;
}
</style>