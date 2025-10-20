<template>
  <div class="explorer-container">
    <!-- 主内容区域 -->
    <div class="explorer-content" v-if="datasources.length > 0">
      <el-container>
        <!-- 左侧边栏 -->
        <el-aside width="300px" class="table-sidebar">
          <!-- 数据库选择器 -->
          <div class="database-selector-sidebar">
            <label>选择数据库</label>
            <el-select
              v-model="selectedDatasource"
              placeholder="请选择数据库"
              @change="onDatasourceChange"
              style="width: 100%; margin-top: 8px;"
              size="default"
              value-key="id"
            >
              <el-option
                v-for="ds in datasources"
                :key="ds.id"
                :label="`${ds.name} (${ds.db_type.toUpperCase()})`"
                :value="ds"
              />
            </el-select>
          </div>
          
          <!-- Oracle模式和表列表 -->
          <el-card class="table-list-card" v-if="selectedDatasource">
            <template #header>
              <div class="card-header">
                <span>{{ isOracleDatabase ? '模式和数据表' : '数据表' }}</span>
                <el-button size="small" @click="refreshSchemas">
                  <el-icon><Refresh /></el-icon>
                </el-button>
              </div>
            </template>
            
            <!-- 数据库模式选择 -->
            <div v-if="isOracleDatabase" class="schema-selector">
              <label>选择模式 (Schema)</label>
              <el-select
                v-model="selectedSchema"
                placeholder="请选择模式"
                @change="onSchemaChange"
                style="width: 100%; margin-top: 8px;"
                size="small"
                filterable
                v-loading="schemasLoading"
              >
                <el-option
                  v-for="schema in schemas"
                  :key="schema.username"
                  :label="schema.username"
                  :value="schema.username"
                />
              </el-select>
            </div>
            
            <!-- 表搜索 -->
            <div class="table-search" v-if="!isOracleDatabase || selectedSchema">
              <el-input
                v-model="tableSearchText"
                placeholder="搜索表名"
                prefix-icon="Search"
                size="small"
              />
            </div>
            
            <!-- 表列表 -->
            <div class="table-list" v-loading="tablesLoading" v-if="!isOracleDatabase || selectedSchema" :style="{ height: tableListHeight + 'px' }">
              <VirtualList
                :data="filteredTables"
                :item-height="50"
                :height="tableListHeight"
                :buffer="20"
                :item-key="'table_name'"
                @item-click="selectTable"
              >
                <template #default="{ item: table }">
                  <div
                    :class="['table-item', { active: selectedTable === table.table_name }]"
                  >
                    <el-icon class="table-icon">
                      <Grid v-if="table.table_type === 'TABLE'" />
                      <View v-else />
                    </el-icon>
                    <span class="table-name">{{ table.table_name }}</span>
                    <el-tag size="small" :type="table.table_type === 'TABLE' ? 'primary' : 'success'">
                      {{ table.table_type }}
                    </el-tag>
                  </div>
                </template>
              </VirtualList>
            </div>
            
            <!-- Schema选择提示信息 -->
            <div v-if="isOracleDatabase && !selectedSchema" class="oracle-hint">
              <el-empty description="请先选择一个模式 (Schema) 来查看表和视图" :image-size="80" />
            </div>
          </el-card>
        </el-aside>

        <!-- 右侧内容区域 -->
        <el-main class="main-content">
          <el-tabs v-model="activeTab" type="border-card">
            <!-- 表详情标签页 -->
            <el-tab-pane label="表详情" name="detail" v-if="selectedTable">
              <div v-loading="tableDetailLoading">
                <el-descriptions :title="selectedTable" :column="2" border>
                  <el-descriptions-item label="表类型">{{ tableDetail?.table_type }}</el-descriptions-item>
                  <el-descriptions-item label="行数">{{ tableDetail?.row_count || 'N/A' }}</el-descriptions-item>
                  <el-descriptions-item label="备注" :span="2">{{ tableDetail?.table_comment || '无' }}</el-descriptions-item>
                </el-descriptions>
                
                <div style="display: flex; justify-content: space-between; align-items: center; margin-top: 20px;">
                  <h3>列信息</h3>
                  <div>
                    <el-button type="primary" size="small" @click="showCreateTableDialog">
                      <el-icon><Plus /></el-icon>
                      新建表
                    </el-button>
                    <el-button type="success" size="small" @click="showAddColumnDialog">
                      <el-icon><Plus /></el-icon>
                      添加列
                    </el-button>
                  </div>
                </div>
                <el-table :data="tableDetail?.columns" stripe>
                  <el-table-column prop="column_name" label="列名" width="200" />
                  <el-table-column prop="data_type" label="数据类型" width="150" />
                  <el-table-column label="是否为空" width="100">
                    <template #default="{ row }">
                      <el-tag :type="row.is_nullable ? 'info' : 'warning'">
                        {{ row.is_nullable ? '是' : '否' }}
                      </el-tag>
                    </template>
                  </el-table-column>
                  <el-table-column label="主键" width="80">
                    <template #default="{ row }">
                      <el-icon v-if="row.is_primary_key" color="#f56c6c"><Key /></el-icon>
                    </template>
                  </el-table-column>
                  <el-table-column prop="column_default" label="默认值" width="120" />
                  <el-table-column prop="column_comment" label="备注" />
                  <el-table-column label="操作" width="150" fixed="right">
                    <template #default="{ row }">
                      <el-button type="primary" size="small" @click="editColumn(row)">
                        <el-icon><Edit /></el-icon>
                      </el-button>
                      <el-button type="danger" size="small" @click="deleteColumn(row)" :disabled="row.is_primary_key">
                        <el-icon><Delete /></el-icon>
                      </el-button>
                    </template>
                  </el-table-column>
                </el-table>
              </div>
            </el-tab-pane>

            <!-- 数据预览标签页 -->
            <el-tab-pane label="数据预览" name="data" v-if="selectedTable">
              <div class="data-preview">
                <div class="data-toolbar">
                  <el-button @click="loadTableData" :loading="tableDataLoading">
                    <el-icon><Refresh /></el-icon>
                    刷新数据
                  </el-button>
                  <span class="data-info">
                    已加载 {{ allTableData.length }} 条记录
                    <span v-if="tableDataTotal > allTableData.length">
                      / 共 {{ tableDataTotal }} 条
                    </span>
                  </span>
                </div>
                
                <VirtualTable
                  ref="virtualTableRef"
                  :data="tableData"
                  :columns="tableDataColumns"
                  :height="500"
                  :item-height="40"
                  :column-width="150"
                  :buffer="10"
                  :loading="tableDataLoading"
                  :total-count="tableDataTotal"
                  :key="`table-data-${selectedTable}-${tableData.length}`"
                  @load-more="handleLoadMoreData"
                  style="margin-top: 10px;"
                />
              </div>
            </el-tab-pane>

            <!-- SQL查询标签页 -->
            <el-tab-pane label="SQL查询" name="sql">
              <div class="sql-workspace">
                <!-- SQL标签页管理 -->
                <div class="sql-tabs-container">
                  <el-tabs 
                    v-model="activeSqlTab" 
                    type="card" 
                    closable 
                    @tab-remove="removeSqlTab"
                    @tab-click="switchSqlTab"
                  >
                    <el-tab-pane
                      v-for="tab in sqlTabs"
                      :key="tab.id"
                      :label="tab.name"
                      :name="tab.id"
                    >
                      <div class="sql-query">
                        <div class="sql-toolbar">
                          <el-button type="primary" @click="executeSQL(tab.id)" :loading="tab.executing">
                            <el-icon><CaretRight /></el-icon>
                            执行
                          </el-button>
                          <el-button type="success" @click="exportResult(tab.id)" :disabled="!canExport(tab)">
                            <el-icon><Download /></el-icon>
                            导出
                          </el-button>
                          <el-button @click="formatSQL(tab.id)">
                            <el-icon><MagicStick /></el-icon>
                            格式化
                          </el-button>
                          <el-button @click="clearSQL(tab.id)">
                            <el-icon><Delete /></el-icon>
                            清空
                          </el-button>
                          <el-button @click="showSaveDialog(tab.id)">
                            <el-icon><DocumentAdd /></el-icon>
                            保存
                          </el-button>
                          <el-button @click="showHistoryDialog">
                            <el-icon><Clock /></el-icon>
                            历史
                          </el-button>
                          <el-divider direction="vertical" />
                          <span class="tab-info">{{ tab.name }}</span>
                        </div>
                        
                        <!-- SQL编辑器 -->
                        <div class="sql-editor-container">
                          <div class="sql-editor" :style="{ height: tab.editorHeight + 'px' }">
                            <VueMonacoEditor
                              :key="tab.id"
                              :height="tab.editorHeight + 'px'"
                              language="sql"
                              theme="vs-dark"
                              v-model:value="tab.sqlContent"
                              :options="{
                                minimap: { enabled: false },
                                scrollBeyondLastLine: false,
                                fontSize: 14,
                                wordWrap: 'on',
                                automaticLayout: true
                              }"
                              @mount="(editor) => onEditorMount(editor, tab.id)"
                            />
                          </div>
                          <!-- 拖拽手柄 -->
                          <div 
                            class="resize-handle"
                            @mousedown="startResize($event, tab.id)"
                          >
                            <div class="resize-line"></div>
                          </div>
                        </div>
                        
                        <!-- 执行结果 -->
                        <div class="sql-result" v-if="tab.result">
                          <div class="result-header">
                            <div class="result-info">
                              <span v-if="tab.result.success" class="success-info">
                                <el-icon><SuccessFilled /></el-icon>
                                执行成功，返回 {{ tab.result.row_count }} 行，耗时 {{ (tab.result.execution_time * 1000).toFixed(2) }}ms
                              </span>
                              <span v-else class="error-info">
                                <el-icon><CircleCloseFilled /></el-icon>
                                执行失败：{{ tab.result.error_message }}
                              </span>
                            </div>
                            <div class="result-actions">
                              <el-button size="small" @click="exportResult(tab.id)" :disabled="!canExport(tab)">
                                <el-icon><Download /></el-icon>
                                导出
                              </el-button>
                            </div>
                          </div>
                          
                          <VirtualTable
                            v-if="tab.result.success && tab.result.data && tab.result.data.length > 0"
                            :data="tab.result.data"
                            :columns="tab.result.columns || []"
                            :height="300"
                            :item-height="40"
                            :column-width="150"
                            :buffer="5"
                            :loading="tab.executing || false"
                            :total-count="tab.result.data.length"
                            :key="`sql-result-${tab.id}-${tab.result.data.length}`"
                            style="margin-top: 10px;"
                          />
                        </div>
                      </div>
                    </el-tab-pane>
                  </el-tabs>
                  
                  <!-- 添加新标签按钮 -->
                  <el-button 
                    class="add-sql-tab" 
                    size="small" 
                    @click="addSqlTab"
                    circle
                  >
                    <el-icon><Plus /></el-icon>
                  </el-button>
                </div>
              </div>
            </el-tab-pane>
          </el-tabs>
        </el-main>
      </el-container>
    </div>

    <!-- 空状态 -->
    <el-empty v-else description="暂无可用数据库，请先配置数据源" />

    <!-- 保存SQL对话框 -->
    <el-dialog title="保存SQL" v-model="saveDialogVisible" width="500px">
      <el-form :model="saveForm" label-width="80px">
        <el-form-item label="名称">
          <el-input v-model="saveForm.name" placeholder="请输入SQL名称" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input
            v-model="saveForm.description"
            type="textarea"
            :rows="3"
            placeholder="请输入描述"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="saveDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="saveSQL" :loading="savingSql">保存</el-button>
      </template>
    </el-dialog>

    <!-- SQL历史对话框 -->
    <el-dialog title="SQL历史" v-model="historyDialogVisible" width="800px">
      <div class="history-dialog-content">
        <div class="history-info" v-if="sqlHistory.length > 0">
          <span>共 {{ sqlHistoryPagination.total }} 条记录</span>
        </div>
        <el-table :data="paginatedSqlHistory" v-loading="historyLoading" height="400">
          <el-table-column prop="name" label="名称" width="200" />
          <el-table-column prop="description" label="描述" />
          <el-table-column prop="created_at" label="创建时间" width="180">
            <template #default="{ row }">
              {{ formatDate(row.created_at) }}
            </template>
          </el-table-column>
          <el-table-column label="操作" width="150">
            <template #default="{ row }">
              <el-button size="small" @click="loadHistorySQL(row)">加载</el-button>
              <el-button size="small" type="danger" @click="deleteHistory(row)">删除</el-button>
            </template>
          </el-table-column>
        </el-table>
        <el-pagination
          v-if="sqlHistoryPagination.total > sqlHistoryPagination.pageSize"
          v-model:current-page="sqlHistoryPagination.currentPage"
          v-model:page-size="sqlHistoryPagination.pageSize"
          :page-sizes="[10, 20, 50, 100]"
          :total="sqlHistoryPagination.total"
          layout="total, sizes, prev, pager, next, jumper"
          style="margin-top: 20px; text-align: center;"
        />
      </div>
    </el-dialog>

    <!-- 添加列对话框 -->
    <el-dialog
      v-model="addColumnDialogVisible"
      title="添加列"
      width="500px"
      :close-on-click-modal="false"
    >
      <el-form :model="addColumnForm" label-width="80px">
        <el-form-item label="列名" required>
          <el-input v-model="addColumnForm.name" placeholder="请输入列名" />
        </el-form-item>
        <el-form-item label="数据类型" required>
          <el-select v-model="addColumnForm.type" placeholder="请选择数据类型" filterable allow-create>
            <el-option
              v-for="type in commonDataTypes"
              :key="type"
              :label="type"
              :value="type"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="允许为空">
          <el-switch v-model="addColumnForm.nullable" />
        </el-form-item>
        <el-form-item label="默认值">
          <el-input v-model="addColumnForm.default" placeholder="请输入默认值" />
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="addColumnForm.comment" placeholder="请输入备注" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="addColumnDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleAddColumn" :loading="tableStructureLoading">确定</el-button>
      </template>
    </el-dialog>

    <!-- 编辑列对话框 -->
    <el-dialog
      v-model="editColumnDialogVisible"
      title="编辑列"
      width="500px"
      :close-on-click-modal="false"
    >
      <el-form :model="editColumnForm" label-width="80px">
        <el-form-item label="列名" required>
          <el-input v-model="editColumnForm.name" placeholder="请输入列名" :disabled="editColumnForm.is_primary_key" />
        </el-form-item>
        <el-form-item label="数据类型" required>
          <el-select v-model="editColumnForm.type" placeholder="请选择数据类型" filterable allow-create>
            <el-option
              v-for="type in commonDataTypes"
              :key="type"
              :label="type"
              :value="type"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="允许为空">
          <el-switch v-model="editColumnForm.nullable" :disabled="editColumnForm.is_primary_key" />
        </el-form-item>
        <el-form-item label="默认值">
          <el-input v-model="editColumnForm.default" placeholder="请输入默认值" />
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="editColumnForm.comment" placeholder="请输入备注" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="editColumnDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleEditColumn" :loading="tableStructureLoading">确定</el-button>
      </template>
    </el-dialog>

    <!-- 新建表对话框 -->
    <el-dialog
      v-model="createTableDialogVisible"
      title="新建表"
      width="800px"
      :close-on-click-modal="false"
    >
      <el-form :model="createTableForm" label-width="80px">
        <el-form-item label="表名" required>
          <el-input v-model="createTableForm.name" placeholder="请输入表名" />
        </el-form-item>
        <el-form-item label="创建模式">
          <el-radio-group v-model="createTableForm.mode">
            <el-radio label="wizard">向导模式</el-radio>
            <el-radio label="sql">SQL模式</el-radio>
          </el-radio-group>
        </el-form-item>
        
        <!-- 向导模式 -->
        <div v-if="createTableForm.mode === 'wizard'">
          <el-form-item label="列定义">
            <div class="table-columns-editor">
              <div class="columns-header">
                <el-button type="primary" size="small" @click="addTableColumn">
                  <el-icon><Plus /></el-icon>
                  添加列
                </el-button>
              </div>
              <el-table :data="createTableForm.columns" border>
                <el-table-column label="列名" width="150">
                  <template #default="{ row, $index }">
                    <el-input v-model="row.name" placeholder="列名" size="small" />
                  </template>
                </el-table-column>
                <el-table-column label="数据类型" width="150">
                  <template #default="{ row, $index }">
                    <el-select v-model="row.type" placeholder="类型" size="small" filterable allow-create>
                      <el-option
                        v-for="type in commonDataTypes"
                        :key="type"
                        :label="type"
                        :value="type"
                      />
                    </el-select>
                  </template>
                </el-table-column>
                <el-table-column label="允许为空" width="80">
                  <template #default="{ row, $index }">
                    <el-switch v-model="row.nullable" size="small" :disabled="row.is_primary_key" />
                  </template>
                </el-table-column>
                <el-table-column label="主键" width="60">
                  <template #default="{ row, $index }">
                    <el-switch v-model="row.is_primary_key" size="small" />
                  </template>
                </el-table-column>
                <el-table-column label="默认值" width="120">
                  <template #default="{ row, $index }">
                    <el-input v-model="row.default" placeholder="默认值" size="small" />
                  </template>
                </el-table-column>
                <el-table-column label="备注">
                  <template #default="{ row, $index }">
                    <el-input v-model="row.comment" placeholder="备注" size="small" />
                  </template>
                </el-table-column>
                <el-table-column label="操作" width="80">
                  <template #default="{ row, $index }">
                    <el-button type="danger" size="small" @click="removeTableColumn($index)" :disabled="createTableForm.columns.length <= 1">
                      <el-icon><Delete /></el-icon>
                    </el-button>
                  </template>
                </el-table-column>
              </el-table>
            </div>
          </el-form-item>
        </div>
        
        <!-- SQL模式 -->
        <div v-if="createTableForm.mode === 'sql'">
          <el-form-item label="DDL语句">
            <el-input
              v-model="createTableForm.sqlContent"
              type="textarea"
              :rows="10"
              placeholder="请输入CREATE TABLE语句"
            />
          </el-form-item>
        </div>
      </el-form>
      <template #footer>
        <el-button @click="createTableDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleCreateTable" :loading="tableStructureLoading">创建</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, onUnmounted, nextTick } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Refresh, Grid, View, Key, CaretRight, Delete, 
  DocumentAdd, Clock, Search, Plus, MagicStick,
  SuccessFilled, CircleCloseFilled, Download, Edit
} from '@element-plus/icons-vue'
import { datasourceAPI, explorerAPI } from '@/api'
import { VueMonacoEditor } from '@guolao/vue-monaco-editor'
import { format } from 'sql-formatter'
import VirtualTable from '@/components/VirtualTable.vue'
import VirtualList from '@/components/VirtualList.vue'

const selectedDatasource = ref(null)
const selectedTable = ref('')
const activeTab = ref('detail')
const tableSearchText = ref('')
const tableDataLimit = ref(100)
const virtualTableRef = ref(null)

// Oracle模式相关
const selectedSchema = ref('')
const schemas = ref([])
const schemasLoading = ref(false)

const datasources = ref([])
const tables = ref([])
const tableDetail = ref(null)
const tableData = ref([])
const tableDataColumns = ref([])
const allTableData = ref([]) // 存储所有已加载的表格数据
const tableDataTotal = ref(0) // 表格数据总数
const tableDataOffset = ref(0) // 当前数据偏移量
const tableDataPageSize = ref(1000) // 每次加载的数据量
const sqlHistory = ref([])
const sqlHistoryPagination = reactive({
  currentPage: 1,
  pageSize: 20,
  total: 0
})
const paginatedSqlHistory = computed(() => {
  const start = (sqlHistoryPagination.currentPage - 1) * sqlHistoryPagination.pageSize
  const end = start + sqlHistoryPagination.pageSize
  return sqlHistory.value.slice(start, end)
})

// 判断是否需要显示Schema选择器（所有数据库都支持）
const isOracleDatabase = computed(() => {
  return selectedDatasource.value && ['oracle', 'mysql', 'doris'].includes(selectedDatasource.value.db_type)
})

const tablesLoading = ref(false)
const tableDetailLoading = ref(false)
const tableDataLoading = ref(false)
const historyLoading = ref(false)
const savingSql = ref(false)

const saveDialogVisible = ref(false)
const historyDialogVisible = ref(false)
const currentSaveTabId = ref(null)

// SQL标签页管理
const sqlTabs = ref([])
const activeSqlTab = ref('')
const sqlTabCounter = ref(0)
const monacoEditorRefs = new Map()

const saveForm = reactive({
  name: '',
  description: ''
})

// 表结构编辑相关
const addColumnDialogVisible = ref(false)
const editColumnDialogVisible = ref(false)
const createTableDialogVisible = ref(false)
const currentEditColumn = ref(null)
const tableStructureLoading = ref(false)

// 添加列表单
const addColumnForm = reactive({
  name: '',
  type: '',
  nullable: true,
  default: '',
  comment: '',
  is_primary_key: false
})

// 编辑列表单
const editColumnForm = reactive({
  name: '',
  type: '',
  nullable: true,
  default: '',
  comment: '',
  is_primary_key: false
})

// 新建表表单
const createTableForm = reactive({
  name: '',
  columns: [{
    name: 'id',
    type: 'INT',
    nullable: false,
    default: '',
    comment: '主键ID',
    is_primary_key: true
  }],
  mode: 'wizard', // wizard 或 sql
  sqlContent: '' // SQL模式的DDL语句
})

// 常用数据类型
const commonDataTypes = computed(() => {
  if (!selectedDatasource.value) return []
  
  const dbType = selectedDatasource.value.db_type.toLowerCase()
  
  if (dbType === 'mysql') {
    return ['INT', 'BIGINT', 'VARCHAR(255)', 'TEXT', 'DECIMAL(10,2)', 'DATETIME', 'TIMESTAMP', 'BOOLEAN']
  } else if (dbType === 'oracle') {
    return ['NUMBER', 'NUMBER(10)', 'VARCHAR2(255)', 'CLOB', 'DATE', 'TIMESTAMP', 'CHAR(1)']
  } else if (dbType === 'doris') {
    return ['INT', 'BIGINT', 'VARCHAR(255)', 'STRING', 'DECIMAL(10,2)', 'DATETIME', 'BOOLEAN']
  }
  
  return ['VARCHAR(255)', 'INT', 'TEXT', 'DATETIME']
})

// 过滤后的表列表
const filteredTables = computed(() => {
  if (!tableSearchText.value) return tables.value
  return tables.value.filter(table => 
    table.table_name.toLowerCase().includes(tableSearchText.value.toLowerCase())
  )
})

// 窗口高度响应式变量
const windowHeight = ref(window.innerHeight)

// 计算表列表的自适应高度
const tableListHeight = computed(() => {
  // 计算左侧面板的可用高度
  // 总高度 - 数据库选择器高度 - 卡片头部高度 - Schema选择器高度(如果有) - 搜索框高度 - 内边距
  let availableHeight = windowHeight.value - 60 // 减去顶部导航栏高度
  availableHeight -= 80 // 减去数据库选择器区域高度
  availableHeight -= 60 // 减去卡片头部高度
  
  if (isOracleDatabase.value && selectedSchema.value) {
    availableHeight -= 80 // 减去Schema选择器高度
  }
  
  availableHeight -= 50 // 减去搜索框高度
  availableHeight -= 40 // 减去各种内边距
  
  // 确保最小高度为200px
  const finalHeight = Math.max(200, availableHeight)
  console.log('tableListHeight calculated:', finalHeight, 'windowHeight:', windowHeight.value)
  return finalHeight
})

// 获取数据源列表
const fetchDatasources = async () => {
  try {
    datasources.value = await datasourceAPI.getList()
  } catch (error) {
    console.error('获取数据源列表失败:', error)
  }
}

// 数据源变化
const onDatasourceChange = async () => {
  selectedTable.value = ''
  tables.value = []
  tableDetail.value = null
  tableData.value = []
  
  // 重置表数据状态
  allTableData.value = []
  tableDataColumns.value = []
  tableDataOffset.value = 0
  tableDataTotal.value = 0
  
  // 重置Oracle模式相关状态
  selectedSchema.value = ''
  schemas.value = []
  
  // 清空SQL标签页
  sqlTabs.value = []
  activeSqlTab.value = null
  monacoEditorRefs.clear()
  
  if (selectedDatasource.value) {
    if (isOracleDatabase.value) {
      // 支持Schema的数据库先获取模式列表
      await fetchSchemas()
    } else {
      // 其他数据库直接获取表列表
      await fetchTables()
    }
    // 创建默认SQL标签页
    addSqlTab()
  }
}

// 获取数据库模式列表
const fetchSchemas = async () => {
  if (!selectedDatasource.value || !isOracleDatabase.value) return
  
  schemasLoading.value = true
  try {
    schemas.value = await explorerAPI.getSchemas(selectedDatasource.value)
  } catch (error) {
    console.error('获取模式列表失败:', error)
    ElMessage.error('获取模式列表失败')
  } finally {
    schemasLoading.value = false
  }
}

// 获取表列表
const fetchTables = async () => {
  if (!selectedDatasource.value) return
  
  // 支持Schema的数据库需要先选择模式
  if (isOracleDatabase.value && !selectedSchema.value) {
    tables.value = []
    return
  }
  
  tablesLoading.value = true
  try {
    if (isOracleDatabase.value) {
      // 支持Schema的数据库根据模式获取表
      tables.value = await explorerAPI.getTablesBySchema(selectedDatasource.value, selectedSchema.value)
    } else {
      // 其他数据库直接获取表
      tables.value = await explorerAPI.getTables(selectedDatasource.value)
    }
  } catch (error) {
    console.error('获取表列表失败:', error)
    ElMessage.error('获取表列表失败')
  } finally {
    tablesLoading.value = false
  }
}

// 刷新模式和表列表
const refreshSchemas = async () => {
  if (isOracleDatabase.value) {
    await fetchSchemas()
    if (selectedSchema.value) {
      await fetchTables()
    }
  } else {
    await fetchTables()
  }
}

// 模式变化处理
const onSchemaChange = async () => {
  selectedTable.value = ''
  tableDetail.value = null
  tableData.value = []
  tableDataColumns.value = []
  
  // 重置表数据状态
  allTableData.value = []
  tableDataOffset.value = 0
  tableDataTotal.value = 0
  
  await fetchTables()
}

// 选择表
const selectTable = async (table) => {
  selectedTable.value = table.table_name
  activeTab.value = 'detail'
  
  // 重置表数据状态
  allTableData.value = []
  tableData.value = []
  tableDataColumns.value = []
  tableDataOffset.value = 0
  tableDataTotal.value = 0
  
  await loadTableDetail()
}

// 加载表详情
const loadTableDetail = async () => {
  if (!selectedDatasource.value || !selectedTable.value) return
  
  tableDetailLoading.value = true
  try {
    tableDetail.value = await explorerAPI.getTableDetail(
      selectedDatasource.value, 
      selectedTable.value,
      selectedSchema.value // 传递当前选中的schema
    )
  } catch (error) {
    console.error('获取表详情失败:', error)
  } finally {
    tableDetailLoading.value = false
  }
}

// 加载表数据（初始加载）
const loadTableData = async () => {
  if (!selectedDatasource.value || !selectedTable.value) return
  
  // 重置数据状态
  allTableData.value = []
  tableData.value = []
  tableDataColumns.value = []
  tableDataOffset.value = 0
  tableDataTotal.value = 0
  
  // 确保在下一个tick中加载数据，让Vue有时间更新DOM
  await nextTick()
  await loadMoreTableData()
}

// 加载更多表数据
const loadMoreTableData = async (params = {}) => {
  if (!selectedDatasource.value || !selectedTable.value) return
  
  tableDataLoading.value = true
  try {
    const requestParams = {
      datasource_id: selectedDatasource.value.id,
      table_name: selectedTable.value,
      limit: params.limit || tableDataPageSize.value,
      offset: params.offset || tableDataOffset.value
    }
    
    // 如果选择了schema，添加到参数中
    if (selectedSchema.value) {
      requestParams.schema = selectedSchema.value
    }
    
    const result = await explorerAPI.getTableData(requestParams)
    
    if (result.success) {
      const newData = result.data || []
      
      // 如果是第一次加载，设置列信息和总数
      if (tableDataOffset.value === 0) {
        tableDataColumns.value = result.columns || []
        // 优先使用后端返回的total_count字段
        if (result.total_count !== null && result.total_count !== undefined) {
          tableDataTotal.value = result.total_count
        } else {
          tableDataTotal.value = result.total || newData.length
        }
        allTableData.value = [...newData]
      } else {
        // 追加新数据
        allTableData.value.push(...newData)
      }
      
      // 更新偏移量
      tableDataOffset.value += newData.length
      
      // 更新显示数据（用于虚拟表格）
      // 使用nextTick确保数据更新后触发重新渲染
      await nextTick()
      tableData.value = [...allTableData.value]
      
      // 确保VirtualTable正确渲染
      if (virtualTableRef.value) {
        await nextTick()
        virtualTableRef.value.forceUpdate()
        // 只有首次加载时才滚动到顶部
        if (tableDataOffset.value <= newData.length) {
          virtualTableRef.value.scrollToTop()
        }
      }
      
    } else {
      ElMessage.error(`加载数据失败: ${result.error_message}`)
    }
  } catch (error) {
    console.error('加载表数据失败:', error)
    ElMessage.error('加载表数据失败')
  } finally {
    tableDataLoading.value = false
  }
}

// 处理VirtualTable的loadMore回调
const handleLoadMoreData = (params) => {
  console.log('Explorer: Received load-more event with params:', params)
  loadMoreTableData(params)
}

// SQL标签页管理
const addSqlTab = () => {
  sqlTabCounter.value++
  const tabId = `sql-${sqlTabCounter.value}`
  const newTab = {
    id: tabId,
    name: `查询${sqlTabCounter.value}`,
    executing: false,
    result: null,
    saved: false,
    sqlContent: '',
    editorHeight: 300 // 默认编辑器高度
  }
  
  sqlTabs.value.push(newTab)
  activeSqlTab.value = tabId
}

const removeSqlTab = (tabId) => {
  const index = sqlTabs.value.findIndex(tab => tab.id === tabId)
  if (index === -1) return
  
  // 清理编辑器引用
  monacoEditorRefs.delete(tabId)
  
  sqlTabs.value.splice(index, 1)
  
  // 如果删除的是当前活动标签，切换到其他标签
  if (activeSqlTab.value === tabId) {
    if (sqlTabs.value.length > 0) {
      activeSqlTab.value = sqlTabs.value[Math.max(0, index - 1)].id
    } else {
      activeSqlTab.value = ''
    }
  }
  
  // 如果没有标签了，创建一个新的
  if (sqlTabs.value.length === 0) {
    addSqlTab()
  }
}

const switchSqlTab = (tab) => {
  activeSqlTab.value = tab.paneName
}

// Monaco Editor挂载处理
const onEditorMount = (editor, tabId) => {
  monacoEditorRefs.set(tabId, editor)
}

// 执行SQL
const executeSQL = async (tabId) => {
  if (!selectedDatasource.value) return
  
  const tab = sqlTabs.value.find(t => t.id === tabId)
  if (!tab) return
  
  const sql = tab.sqlContent.trim()
  if (!sql) {
    ElMessage.warning('请输入SQL语句')
    return
  }
  
  tab.executing = true
  try {
    tab.result = await explorerAPI.executeSQL({
      datasource_id: selectedDatasource.value.id,
      sql: sql,
      schema: selectedSchema.value || null
    })
  } catch (error) {
    console.error('执行SQL失败:', error)
    tab.result = {
      success: false,
      error_message: error.message || '执行失败'
    }
  } finally {
    tab.executing = false
  }
}

// 格式化SQL
const formatSQL = async (tabId) => {
  const tab = sqlTabs.value.find(t => t.id === tabId)
  const editor = monacoEditorRefs.get(tabId)
  if (!tab || !editor) return
  
  try {
    const currentSQL = tab.sqlContent
    if (!currentSQL || !currentSQL.trim()) {
      ElMessage.warning('请先输入SQL语句')
      return
    }
    
    // 根据当前数据源类型确定SQL方言
    let language = 'sql'
    if (selectedDatasource.value) {
      const dbType = selectedDatasource.value.db_type?.toLowerCase()
      switch (dbType) {
        case 'mysql':
          language = 'mysql'
          break
        case 'postgresql':
        case 'postgres':
          language = 'postgresql'
          break
        case 'sqlite':
          language = 'sqlite'
          break
        case 'oracle':
          language = 'plsql'
          break
        case 'sqlserver':
        case 'mssql':
          language = 'tsql'
          break
        default:
          language = 'sql'
      }
    }
    
    // 使用sql-formatter进行格式化
    const formattedSQL = format(currentSQL, {
      language: language,
      tabWidth: 2,
      keywordCase: 'upper',
      identifierCase: 'lower',
      functionCase: 'upper',
      dataTypeCase: 'upper',
      linesBetweenQueries: 2
    })
    
    // 更新编辑器内容
    if (editor && editor.setValue) {
      editor.setValue(formattedSQL)
    }
    tab.sqlContent = formattedSQL
    
    ElMessage.success('SQL格式化完成')
  } catch (error) {
    console.error('SQL格式化失败:', error)
    ElMessage.error('SQL格式化失败，请检查SQL语法')
  }
}

// 清空SQL
const clearSQL = (tabId) => {
  const tab = sqlTabs.value.find(t => t.id === tabId)
  if (!tab) return
  
  tab.sqlContent = ''
}

// 显示保存对话框
const showSaveDialog = (tabId) => {
  const tab = sqlTabs.value.find(t => t.id === tabId)
  if (!tab) return
  
  const sql = tab.sqlContent.trim()
  if (!sql) {
    ElMessage.warning('请输入SQL语句')
    return
  }
  
  currentSaveTabId.value = tabId
  saveForm.name = ''
  saveForm.description = ''
  saveDialogVisible.value = true
}

// 保存SQL
const saveSQL = async () => {
  if (!selectedDatasource.value || !currentSaveTabId.value) return
  
  const tab = sqlTabs.value.find(t => t.id === currentSaveTabId.value)
  if (!tab) return
  
  const sql = tab.sqlContent.trim()
  if (!sql) {
    ElMessage.warning('请输入SQL语句')
    return
  }
  
  savingSql.value = true
  try {
    await explorerAPI.saveSQLHistory({
      datasource_id: selectedDatasource.value.id,
      sql_content: sql,
      name: saveForm.name,
      description: saveForm.description
    })
    
    // 更新标签状态
    const tab = sqlTabs.value.find(t => t.id === currentSaveTabId.value)
    if (tab) {
      tab.saved = true
      tab.name = saveForm.name || tab.name
    }
    
    ElMessage.success('保存成功')
    saveDialogVisible.value = false
  } catch (error) {
    console.error('保存SQL失败:', error)
  } finally {
    savingSql.value = false
  }
}

// 判断是否可以导出（SQL包含SELECT语句）
const canExport = (tab) => {
  if (!tab || !tab.sqlContent) return false
  const sql = tab.sqlContent.trim()
  return sql && sql.toLowerCase().includes('select')
}

// 导出结果
const exportResult = async (tabId) => {
  const tab = sqlTabs.value.find(t => t.id === tabId)
  if (!tab) return
  
  if (!selectedDatasource.value) {
    ElMessage.warning('请先选择数据源')
    return
  }
  
  const sql = tab.sqlContent.trim()
  if (!sql) {
    ElMessage.warning('请输入SQL语句')
    return
  }
  
  // 检查SQL是否包含SELECT语句（不区分大小写）
  if (!sql.toLowerCase().includes('select')) {
    ElMessage.warning('只有包含SELECT的SQL语句才能导出')
    return
  }
  
  try {
    ElMessage.info('正在导出数据，请稍候...')
    
    // 调用服务端导出接口
    const response = await explorerAPI.exportSQLResult({
      datasource_id: selectedDatasource.value.id,
      sql: sql,
      limit: 10000, // 导出时限制10000行
      schema: selectedSchema.value || null
    })
    
    // 创建下载链接
    const blob = new Blob([response.data], { type: 'text/csv;charset=utf-8;' })
    const link = document.createElement('a')
    link.href = URL.createObjectURL(blob)
    
    // 从响应头获取文件名，如果没有则使用默认名称
    const contentDisposition = response.headers['content-disposition']
    let filename = `sql_result_${new Date().getTime()}.csv`
    if (contentDisposition) {
      const filenameMatch = contentDisposition.match(/filename=(.+)/)
      if (filenameMatch) {
        filename = filenameMatch[1].replace(/"/g, '')
      }
    }
    
    link.download = filename
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    URL.revokeObjectURL(link.href)
    
    ElMessage.success('导出成功')
  } catch (error) {
    console.error('导出失败:', error)
    ElMessage.error('导出失败，请重试')
  }
}

// 显示历史对话框
const showHistoryDialog = async () => {
  if (!selectedDatasource.value) return
  
  historyDialogVisible.value = true
  await loadSQLHistory()
}

// 加载SQL历史
const loadSQLHistory = async () => {
  if (!selectedDatasource.value) return
  
  historyLoading.value = true
  try {
    sqlHistory.value = await explorerAPI.getSQLHistory(selectedDatasource.value)
    sqlHistoryPagination.total = sqlHistory.value.length
    sqlHistoryPagination.currentPage = 1
  } catch (error) {
    console.error('加载SQL历史失败:', error)
  } finally {
    historyLoading.value = false
  }
}

// 加载历史SQL
const loadHistorySQL = (history) => {
  if (!activeSqlTab.value) {
    addSqlTab()
  }
  
  const tab = sqlTabs.value.find(t => t.id === activeSqlTab.value)
  if (tab) {
    tab.sqlContent = history.sql_content
    
    // 更新标签名称
    if (history.name) {
      tab.name = history.name
    }
  }
  
  historyDialogVisible.value = false
}

// 删除历史
const deleteHistory = async (history) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除SQL "${history.name || '未命名'}" 吗？`,
      '确认删除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    await explorerAPI.deleteSQLHistory(history.id)
    ElMessage.success('删除成功')
    loadSQLHistory()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除失败:', error)
    }
  }
}

// 格式化日期
const formatDate = (dateString) => {
  return new Date(dateString).toLocaleString('zh-CN')
}

// 拖拽调整编辑器高度
const isResizing = ref(false)
const currentResizeTabId = ref(null)
const startY = ref(0)
const startHeight = ref(0)

const startResize = (event, tabId) => {
  isResizing.value = true
  currentResizeTabId.value = tabId
  startY.value = event.clientY
  
  const tab = sqlTabs.value.find(t => t.id === tabId)
  if (tab) {
    startHeight.value = tab.editorHeight
  }
  
  document.addEventListener('mousemove', handleResize)
  document.addEventListener('mouseup', stopResize)
  document.body.style.cursor = 'ns-resize'
  document.body.style.userSelect = 'none'
  
  event.preventDefault()
}

const handleResize = (event) => {
  if (!isResizing.value || !currentResizeTabId.value) return
  
  const deltaY = event.clientY - startY.value
  const newHeight = Math.max(200, Math.min(600, startHeight.value + deltaY))
  
  const tab = sqlTabs.value.find(t => t.id === currentResizeTabId.value)
  if (tab) {
    tab.editorHeight = newHeight
    
    // 触发Monaco编辑器重新布局
    nextTick(() => {
      const editor = monacoEditorRefs.get(currentResizeTabId.value)
      if (editor) {
        editor.layout()
      }
    })
  }
}

const stopResize = () => {
  isResizing.value = false
  currentResizeTabId.value = null
  
  document.removeEventListener('mousemove', handleResize)
  document.removeEventListener('mouseup', stopResize)
  document.body.style.cursor = ''
  document.body.style.userSelect = ''
}

// 窗口大小变化监听
const handleWindowResize = () => {
  // 更新窗口高度，触发tableListHeight重新计算
  windowHeight.value = window.innerHeight
}

onMounted(async () => {
  await fetchDatasources()
  // 添加窗口大小变化监听
  window.addEventListener('resize', handleWindowResize)
})

// 表结构编辑方法
const showAddColumnDialog = () => {
  if (!selectedTable.value || !selectedDatasource.value) {
    ElMessage.warning('请先选择表')
    return
  }
  
  // 重置表单
  Object.assign(addColumnForm, {
    name: '',
    type: commonDataTypes.value[0] || 'VARCHAR(255)',
    nullable: true,
    default: '',
    comment: '',
    is_primary_key: false
  })
  
  addColumnDialogVisible.value = true
}

const showCreateTableDialog = () => {
  if (!selectedDatasource.value) {
    ElMessage.warning('请先选择数据源')
    return
  }
  
  // 重置表单
  Object.assign(createTableForm, {
    name: '',
    columns: [{
      name: 'id',
      type: commonDataTypes.value[0] || 'INT',
      nullable: false,
      default: '',
      comment: '主键ID',
      is_primary_key: true
    }],
    mode: 'wizard'
  })
  
  createTableDialogVisible.value = true
}

const editColumn = (column) => {
  currentEditColumn.value = column
  
  // 填充编辑表单
  Object.assign(editColumnForm, {
    name: column.column_name,
    type: column.data_type,
    nullable: column.is_nullable,
    default: column.column_default || '',
    comment: column.column_comment || '',
    is_primary_key: column.is_primary_key
  })
  
  editColumnDialogVisible.value = true
}

const deleteColumn = async (column) => {
  if (!selectedTable.value || !selectedDatasource.value) return
  
  try {
    await ElMessageBox.confirm(
      `确定要删除列 "${column.column_name}" 吗？此操作不可撤销！`,
      '确认删除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    tableStructureLoading.value = true
    
    const response = await explorerAPI.modifyTableStructure({
      datasource_id: selectedDatasource.value.id,
      table_name: selectedTable.value,
      operation_type: 'drop_column',
      column_data: {
        name: column.column_name
      },
      schema: selectedSchema.value
    })
    
    if (response.success) {
      ElMessage.success('删除列成功')
      await loadTableDetail()
    } else {
      // 显示后端返回的友好错误信息
      const errorMessage = response.message || response.error_message || '删除列失败'
      ElMessage.error(errorMessage)
    }
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除列失败:', error)
      // 网络错误或其他异常
      ElMessage.error('网络错误或服务异常，请稍后重试')
    }
  } finally {
    tableStructureLoading.value = false
  }
}

const handleAddColumn = async () => {
  if (!selectedTable.value || !selectedDatasource.value) return
  
  // 基本验证
  if (!addColumnForm.name.trim()) {
    ElMessage.warning('请输入列名')
    return
  }
  
  if (!addColumnForm.type.trim()) {
    ElMessage.warning('请选择数据类型')
    return
  }
  
  try {
    tableStructureLoading.value = true
    
    const response = await explorerAPI.modifyTableStructure({
      datasource_id: selectedDatasource.value.id,
      table_name: selectedTable.value,
      operation_type: 'add_column',
      column_data: {
        name: addColumnForm.name,
        type: addColumnForm.type,
        nullable: addColumnForm.nullable,
        default: addColumnForm.default,
        comment: addColumnForm.comment
      },
      schema: selectedSchema.value
    })
    
    if (response.success) {
      ElMessage.success('添加列成功')
      addColumnDialogVisible.value = false
      await loadTableDetail()
    } else {
      // 显示后端返回的友好错误信息
      const errorMessage = response.message || response.error_message || '添加列失败'
      ElMessage.error(errorMessage)
      
      // 如果是列名重复错误，可以高亮列名输入框
      if (errorMessage.includes('列名已存在') || errorMessage.includes('重复')) {
        // 可以在这里添加表单验证状态
        console.warn('列名重复错误:', errorMessage)
      }
    }
  } catch (error) {
    console.error('添加列失败:', error)
    // 网络错误或其他异常
    ElMessage.error('网络错误或服务异常，请稍后重试')
  } finally {
    tableStructureLoading.value = false
  }
}

const handleEditColumn = async () => {
  if (!selectedTable.value || !selectedDatasource.value || !currentEditColumn.value) return
  
  // 基本验证
  if (!editColumnForm.name.trim()) {
    ElMessage.warning('请输入列名')
    return
  }
  
  if (!editColumnForm.type.trim()) {
    ElMessage.warning('请选择数据类型')
    return
  }
  
  try {
    tableStructureLoading.value = true
    
    const response = await explorerAPI.modifyTableStructure({
      datasource_id: selectedDatasource.value.id,
      table_name: selectedTable.value,
      operation_type: 'modify_column',
      column_data: {
        original_name: currentEditColumn.value.column_name, // 原始列名
        name: editColumnForm.name, // 新列名
        type: editColumnForm.type,
        nullable: editColumnForm.nullable,
        default: editColumnForm.default,
        comment: editColumnForm.comment
      },
      schema: selectedSchema.value
    })
    
    if (response.success) {
      ElMessage.success('修改列成功')
      editColumnDialogVisible.value = false
      await loadTableDetail()
    } else {
      // 显示后端返回的友好错误信息
      const errorMessage = response.message || response.error_message || '修改列失败'
      ElMessage.error(errorMessage)
      
      // 如果是列名重复错误，可以高亮列名输入框
      if (errorMessage.includes('列名已存在') || errorMessage.includes('重复')) {
        console.warn('列名重复错误:', errorMessage)
      }
    }
  } catch (error) {
    console.error('修改列失败:', error)
    // 网络错误或其他异常
    ElMessage.error('网络错误或服务异常，请稍后重试')
  } finally {
    tableStructureLoading.value = false
  }
}

const addTableColumn = () => {
  createTableForm.columns.push({
    name: '',
    type: commonDataTypes.value[0] || 'VARCHAR(255)',
    nullable: true,
    default: '',
    comment: '',
    is_primary_key: false
  })
}

const removeTableColumn = (index) => {
  if (createTableForm.columns.length > 1) {
    createTableForm.columns.splice(index, 1)
  }
}

const handleCreateTable = async () => {
  if (!selectedDatasource.value) return
  
  try {
    tableStructureLoading.value = true
    
    if (createTableForm.mode === 'wizard') {
      // 将前端字段格式转换为后端API期望的格式
      const formattedColumns = createTableForm.columns.map(col => ({
        column_name: col.name,
        data_type: col.type,
        nullable: col.nullable,
        default: col.default || null,
        comment: col.comment || null,
        is_primary_key: col.is_primary_key || false
      }))
      
      const response = await explorerAPI.createTable({
        datasource_id: selectedDatasource.value.id,
        table_name: createTableForm.name,
        columns: formattedColumns,
        schema: selectedSchema.value
      })
      
      if (response.success) {
        ElMessage.success('创建表成功')
        createTableDialogVisible.value = false
        await fetchTables()
      } else {
        ElMessage.error(response.error_message || '创建表失败')
      }
    } else {
      // SQL模式处理
      const response = await explorerAPI.executeDDL({
        datasource_id: selectedDatasource.value.id,
        ddl_sql: createTableForm.sqlContent
      })
      
      if (response.success) {
        ElMessage.success('执行DDL成功')
        createTableDialogVisible.value = false
        await fetchTables()
      } else {
        ElMessage.error(response.error_message || '执行DDL失败')
      }
    }
  } catch (error) {
    console.error('创建表失败:', error)
    ElMessage.error('创建表失败')
  } finally {
    tableStructureLoading.value = false
  }
}

// 组件卸载时清理事件监听器
onUnmounted(() => {
  if (isResizing.value) {
    document.removeEventListener('mousemove', handleResize)
    document.removeEventListener('mouseup', stopResize)
    document.body.style.cursor = ''
    document.body.style.userSelect = ''
  }
  // 清理窗口大小变化监听器
  window.removeEventListener('resize', handleWindowResize)
})
</script>

<style scoped>
.explorer-container {
  height: calc(100vh - 60px);
  display: flex;
  flex-direction: column;
}

.explorer-content {
  flex: 1;
  overflow: hidden;
  height: 100vh;
}

.table-sidebar {
  border-right: 1px solid #e4e7ed;
  background: white;
  display: flex;
  flex-direction: column;
}

.database-selector-sidebar {
  padding: 20px;
  border-bottom: 1px solid #e4e7ed;
  background: #fafafa;
}

.database-selector-sidebar label {
  font-weight: 500;
  color: #303133;
  font-size: 14px;
  display: block;
}

.table-list-card {
  flex: 1;
  border: none;
  border-radius: 0;
  margin: 0;
  display: flex;
  flex-direction: column;
}

.table-list-card :deep(.el-card__body) {
  flex: 1;
  display: flex;
  flex-direction: column;
  padding: 16px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.schema-selector {
  margin-bottom: 15px;
  padding: 12px;
  background: #f8f9fa;
  border-radius: 6px;
  border: 1px solid #e9ecef;
}

.schema-selector label {
  font-size: 14px;
  font-weight: 500;
  color: #495057;
  display: block;
  margin-bottom: 8px;
}

.oracle-hint {
  padding: 20px;
  text-align: center;
  color: #6c757d;
}

.table-search {
  margin-bottom: 10px;
}

.table-list {
  border: 1px solid #dcdfe6;
  border-radius: 4px;
  position: relative;
  overflow: hidden;
}

.table-list :deep(.virtual-list) {
  height: 100% !important;
  border-radius: 4px;
  overflow-y: auto !important;
}

.table-item {
  display: flex;
  align-items: center;
  padding: 12px 16px;
  cursor: pointer;
  border-bottom: 1px solid #ebeef5;
  transition: background-color 0.2s;
  height: 100%;
  box-sizing: border-box;
}

.table-item:hover {
  background-color: #f5f7fa;
}

.table-item.active {
  background-color: #ecf5ff;
  border-color: #409eff;
}

.table-icon {
  margin-right: 8px;
  font-size: 16px;
}

.table-name {
  flex: 1;
  margin-right: 8px;
  font-size: 14px;
}

.main-content {
  background: white;
  padding: 0;
}

/* 为表详情标签页添加内边距 */
.main-content .el-tab-pane[aria-labelledby="tab-detail"] {
  padding: 20px;
}

.data-preview {
  padding: 20px;
}

.data-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}

.data-info {
  color: #909399;
  font-size: 14px;
}

.sql-workspace {
  padding: 20px;
  height: calc(100vh - 200px);
}

.sql-tabs-container {
  position: relative;
  height: 100%;
}

.add-sql-tab {
  position: absolute;
  top: 8px;
  right: 10px;
  z-index: 10;
}

.sql-query {
  height: calc(100% - 60px);
  display: flex;
  flex-direction: column;
}

.sql-toolbar {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 15px;
  padding: 10px;
  background: #f8f9fa;
  border-radius: 6px;
  border: 1px solid #e9ecef;
}

.tab-info {
  color: #6c757d;
  font-size: 14px;
  margin-left: auto;
}

.sql-editor-container {
  margin-bottom: 20px;
}

.sql-editor {
  border: 1px solid #dcdfe6;
  border-radius: 6px 6px 0 0;
  overflow: hidden;
  transition: height 0.1s ease;
}

.resize-handle {
  height: 8px;
  background: #f5f7fa;
  border: 1px solid #dcdfe6;
  border-top: none;
  border-radius: 0 0 6px 6px;
  cursor: ns-resize;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: background-color 0.2s ease;
}

.resize-handle:hover {
  background: #e4e7ed;
}

.resize-line {
  width: 30px;
  height: 2px;
  background: #c0c4cc;
  border-radius: 1px;
  position: relative;
}

.resize-line::before {
  content: '';
  position: absolute;
  top: -2px;
  left: 0;
  right: 0;
  height: 2px;
  background: #c0c4cc;
  border-radius: 1px;
}

.resize-handle:hover .resize-line,
.resize-handle:hover .resize-line::before {
  background: #909399;
}

.sql-result {
  flex: 1;
  overflow: hidden;
}

.result-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 6px 10px;
  background: #f8f9fa;
  border-bottom: 1px solid #e9ecef;
}

.result-info {
  display: flex;
  align-items: center;
  gap: 8px;
}

.result-actions {
  display: flex;
  gap: 8px;
}

.success-info {
  color: #67c23a;
  display: flex;
  align-items: center;
  gap: 3px;
  font-size: 12px;
  line-height: 1.2;
}

.error-info {
  color: #f56c6c;
  display: flex;
  align-items: center;
  gap: 3px;
  font-size: 12px;
  line-height: 1.2;
}

.sql-tabs :deep(.el-tabs__header) {
  margin: 0;
}

.sql-tabs :deep(.el-tabs__content) {
  height: calc(100% - 40px);
}

.sql-tabs :deep(.el-tab-pane) {
  height: 100%;
}

.history-dialog-content {
  padding: 0;
}

.history-info {
  margin-bottom: 15px;
  color: #909399;
  font-size: 14px;
}

/* 表结构编辑相关样式 */
.table-columns-editor {
  width: 100%;
}

.columns-header {
  margin-bottom: 10px;
  display: flex;
  justify-content: flex-end;
}

.table-columns-editor .el-table {
  margin-top: 10px;
}

.table-columns-editor .el-input,
.table-columns-editor .el-select {
  width: 100%;
}

.table-columns-editor .el-switch {
  --el-switch-on-color: #409eff;
  --el-switch-off-color: #dcdfe6;
}
</style>