<template>
  <div class="center-table-management">
    <!-- 页面头部 -->
    <div class="page-header">
      <h2>中心表管理</h2>
      <!-- <p class="page-description">数据源: 10.20.1.201 | 模式: cepiec-warehouse | 表: cpc_dw_publication</p> -->
    </div>

    <!-- 主要内容 -->
    <div class="content-wrapper">
      <el-card class="main-card">
        <template #header>
          <div class="card-header">
            <span>表结构详情</span>
            <div class="header-actions">
              <el-button @click="loadTableDetail" :loading="tableDetailLoading">
                <el-icon><Refresh /></el-icon>
                刷新数据
              </el-button>
              <!--  <el-button type="primary" @click="loadTableData" :loading="tableDataLoading">
                <el-icon><Search /></el-icon>
                查看数据
              </el-button> -->
            </div>
          </div>
        </template>

        <!-- 表基本信息 -->
        <div v-if="tableDetail" class="table-info-section" style="margin-bottom: 20px;">
          <el-descriptions :column="3" border>
            <el-descriptions-item label="表名称">{{ tableDetail.table_name }}</el-descriptions-item>
            <el-descriptions-item label="表类型">{{ tableDetail.table_type }}</el-descriptions-item>
            <el-descriptions-item label="行数">{{ tableDetail.row_count || 'N/A' }}</el-descriptions-item>
            <el-descriptions-item label="表注释" :span="3">{{ tableDetail.table_comment || '无注释' }}</el-descriptions-item>
          </el-descriptions>
        </div>

        <!-- 列信息表格 -->
        <div v-if="tableDetail" class="columns-section">
          <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px;">
            <h3 style="margin: 0;">列信息 ({{ filteredColumns?.length || 0 }} 列)</h3>
            <el-button type="primary" @click="showAddFieldDialog">
              <el-icon><Plus /></el-icon>
              新增列
            </el-button>
          </div>
          <el-table
            :data="filteredColumns"
            border
            stripe
            style="width: 100%"
            :loading="tableDetailLoading"
          >
            <el-table-column prop="column_name" label="列名" width="200" />
            <el-table-column prop="data_type" label="数据类型" width="150" />
            <el-table-column prop="is_nullable" label="允许空值" width="100">
              <template #default="{ row }">
                <el-tag :type="row.is_nullable ? 'success' : 'danger'">
                  {{ row.is_nullable ? '是' : '否' }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="is_primary_key" label="主键" width="80">
              <template #default="{ row }">
                <el-icon v-if="row.is_primary_key" color="#f56c6c"><Key /></el-icon>
              </template>
            </el-table-column>
            <el-table-column prop="column_default" label="默认值" width="120" />
            <el-table-column prop="column_comment" label="列注释" min-width="200" />
            <el-table-column label="操作" width="180" fixed="right">
              <template #default="{ row }">
                <el-button size="small" @click="showEditFieldDialog(row)">
                  <el-icon><Edit /></el-icon>
                  编辑
                </el-button>
                <el-button 
                  size="small" 
                  type="danger" 
                  @click="showDeleteFieldDialog(row)"
                  :disabled="row.is_primary_key"
                  style="margin-left: 8px;"
                >
                  <el-icon><Delete /></el-icon>
                  删除
                </el-button>
              </template>
            </el-table-column>
          </el-table>
        </div>

        <!-- 加载状态 -->
        <div v-if="!tableDetail && !tableDetailLoading" class="empty-state">
          <el-empty description="点击刷新数据按钮加载表详情" />
        </div>
      </el-card>

      <!-- 表数据对话框 -->
      <el-dialog
        v-model="dataDialogVisible"
        title="表数据预览"
        width="90%"
        :close-on-click-modal="false"
      >
        <div class="data-toolbar">
          <div class="data-info">
            <span>共 {{ tableData.length }} 条记录</span>
          </div>
          <div>
            <el-button @click="loadTableData" :loading="tableDataLoading">
              <el-icon><Refresh /></el-icon>
              刷新
            </el-button>
          </div>
        </div>

        <el-table
          :data="paginatedTableData"
          border
          stripe
          style="width: 100%; margin-top: 16px;"
          :loading="tableDataLoading"
          max-height="400"
        >
          <el-table-column
            v-for="column in tableDataColumns"
            :key="column"
            :prop="column"
            :label="column"
            min-width="120"
            show-overflow-tooltip
          />
        </el-table>

        <div class="pagination-section" style="margin-top: 16px;">
          <el-pagination
            v-model:current-page="dataTablePagination.currentPage"
            v-model:page-size="dataTablePagination.pageSize"
            :page-sizes="[10, 20, 50, 100]"
            :total="tableData.length"
            layout="total, sizes, prev, pager, next, jumper"
            @size-change="handleDataSizeChange"
            @current-change="handleDataCurrentChange"
          />
        </div>
      </el-dialog>

       <!-- 字段编辑对话框 -->
       <el-dialog
         v-model="editFieldDialogVisible"
         title="编辑字段"
         width="600px"
         :close-on-click-modal="false"
       >
         <el-form
           ref="editFieldFormRef"
           :model="editFieldForm"
           :rules="editFieldRules"
           label-width="120px"
         >
           <el-form-item label="字段名称">
             <el-input v-model="editFieldForm.column_name" disabled />
           </el-form-item>
           <el-form-item label="数据类型">
             <el-input v-model="editFieldForm.data_type" disabled />
           </el-form-item>
           <el-form-item label="字段注释" prop="column_comment">
             <el-input
               v-model="editFieldForm.column_comment"
               type="textarea"
               :rows="3"
               placeholder="请输入字段注释"
             />
           </el-form-item>
           <el-form-item label="默认值" prop="column_default">
             <el-input
               v-model="editFieldForm.column_default"
               placeholder="请输入默认值"
             />
           </el-form-item>
           <el-form-item label="允许空值">
             <el-switch
               v-model="editFieldForm.is_nullable"
               active-text="是"
               inactive-text="否"
             />
           </el-form-item>
         </el-form>
         
         <template #footer>
           <div class="dialog-footer">
             <el-button @click="editFieldDialogVisible = false">取消</el-button>
             <el-button type="primary" @click="submitEditField" :loading="editFieldLoading">
               保存
             </el-button>
           </div>
         </template>
       </el-dialog>

       <!-- 删除字段确认对话框 -->
       <el-dialog
         v-model="deleteFieldDialogVisible"
         title="删除字段确认"
         width="500px"
         :close-on-click-modal="false"
       >
         <div class="delete-confirmation">
           <el-icon color="#f56c6c" size="48px" style="margin-bottom: 16px;">
             <WarningFilled />
           </el-icon>
           <p style="font-size: 16px; margin-bottom: 16px;">
             确定要删除字段 <strong>{{ deleteFieldInfo.column_name }}</strong> 吗？
           </p>
           <p style="color: #f56c6c; font-size: 14px; margin-bottom: 0;">
             此操作不可逆，删除后该字段的所有数据将丢失！
           </p>
         </div>
         
         <template #footer>
           <div class="dialog-footer">
             <el-button @click="deleteFieldDialogVisible = false">取消</el-button>
             <el-button type="danger" @click="submitDeleteField" :loading="deleteFieldLoading">
               确认删除
             </el-button>
           </div>
         </template>
       </el-dialog>

       <!-- 新增字段对话框 -->
       <el-dialog
         v-model="addFieldDialogVisible"
         title="新增字段"
         width="600px"
         :close-on-click-modal="false"
       >
         <el-form
           ref="addFieldFormRef"
           :model="addFieldForm"
           :rules="addFieldRules"
           label-width="120px"
         >
           <el-form-item label="字段名称" prop="column_name">
             <el-input
               v-model="addFieldForm.column_name"
               placeholder="请输入字段名称"
             />
           </el-form-item>
           <el-form-item label="数据类型" prop="data_type">
             <el-select
               v-model="addFieldForm.data_type"
               placeholder="请选择数据类型"
               style="width: 100%"
             >
               <el-option label="VARCHAR(255)" value="VARCHAR(255)" />
               <el-option label="INT" value="INT" />
               <el-option label="BIGINT" value="BIGINT" />
               <el-option label="DECIMAL(10,2)" value="DECIMAL(10,2)" />
               <el-option label="TEXT" value="TEXT" />
               <el-option label="DATE" value="DATE" />
               <el-option label="DATETIME" value="DATETIME" />
               <el-option label="TIMESTAMP" value="TIMESTAMP" />
               <el-option label="BOOLEAN" value="BOOLEAN" />
             </el-select>
           </el-form-item>
           <el-form-item label="字段注释" prop="column_comment">
             <el-input
               v-model="addFieldForm.column_comment"
               type="textarea"
               :rows="3"
               placeholder="请输入字段注释"
             />
           </el-form-item>
           <el-form-item label="默认值" prop="column_default">
             <el-input
               v-model="addFieldForm.column_default"
               placeholder="请输入默认值（可选）"
             />
           </el-form-item>
           <el-form-item label="允许空值">
             <el-switch
               v-model="addFieldForm.is_nullable"
               active-text="是"
               inactive-text="否"
             />
           </el-form-item>
         </el-form>
         
         <template #footer>
           <div class="dialog-footer">
             <el-button @click="addFieldDialogVisible = false">取消</el-button>
             <el-button type="primary" @click="submitAddField" :loading="addFieldLoading">
               保存
             </el-button>
           </div>
         </template>
       </el-dialog>
      </div>
    </div>
  </template>

<script setup lang="ts">
import { ref, reactive, onMounted, computed } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import type { FormInstance } from 'element-plus'
import { Search, Refresh, Plus, Delete, Key, Edit, WarningFilled } from '@element-plus/icons-vue'
import { dataInsightAPI } from '@/api/dataInsight'
import type { DataSource, TableInfo, TableDetail, TableColumn, TableDataRequest, FieldUpdateRequest } from '@/api/dataInsight'

const route = useRoute()

// 硬编码的数据源信息
const HARDCODED_DATASOURCE = {
  id: 8, // 使用整数ID而不是IP地址
  name: '10.20.1.201',
  db_type: 'oracle',
  host: '10.20.1.201'
} as DataSource

const HARDCODED_SCHEMA = 'cepiec-warehouse'
const HARDCODED_TABLE = 'cpc_dw_publication'

// 响应式数据
const loading = ref(false)
const tableDetailLoading = ref(false)
const tableDataLoading = ref(false)
const editFieldLoading = ref(false)
const deleteFieldLoading = ref(false)
const addFieldLoading = ref(false)

// 表相关
const tableDetail = ref<TableDetail | null>(null)

// 表数据相关
const tableData = ref<any[]>([])
const tableDataColumns = ref<string[]>([])

// 对话框状态
const dataDialogVisible = ref(false)
const editFieldDialogVisible = ref(false)
const deleteFieldDialogVisible = ref(false)
const addFieldDialogVisible = ref(false)

// 字段编辑相关
const editFieldFormRef = ref<FormInstance>()
const editFieldForm = reactive({
  column_name: '',
  data_type: '',
  column_comment: '',
  column_default: '',
  is_nullable: false
})

// 删除字段相关
const deleteFieldInfo = reactive({
  column_name: '',
  data_type: ''
})

// 新增字段相关
const addFieldFormRef = ref<FormInstance>()
const addFieldForm = reactive({
  column_name: '',
  data_type: '',
  column_comment: '',
  column_default: '',
  is_nullable: true
})

const addFieldRules = {
  column_name: [
    { required: true, message: '请输入字段名称', trigger: 'blur' },
    { pattern: /^[a-zA-Z_][a-zA-Z0-9_]*$/, message: '字段名称只能包含字母、数字和下划线，且不能以数字开头', trigger: 'blur' },
    { max: 64, message: '字段名称长度不能超过64个字符', trigger: 'blur' }
  ],
  data_type: [
    { required: true, message: '请选择数据类型', trigger: 'change' }
  ],
  column_comment: [
    { max: 500, message: '字段注释长度不能超过500个字符', trigger: 'blur' }
  ]
}

const editFieldRules = {
  column_comment: [
    { max: 500, message: '字段注释长度不能超过500个字符', trigger: 'blur' }
  ]
}

// 表数据分页
const dataTablePagination = reactive({
  currentPage: 1,
  pageSize: 20
})

// 计算属性
const filteredColumns = computed(() => {
  if (!tableDetail.value?.columns) return []
  // 过滤掉列名为 batch_id 的列
  return tableDetail.value.columns.filter(column => column.column_name !== 'batch_id')
})

const paginatedTableData = computed(() => {
  const start = (dataTablePagination.currentPage - 1) * dataTablePagination.pageSize
  const end = start + dataTablePagination.pageSize
  return tableData.value.slice(start, end)
})

// 方法定义
const loadTableDetail = async () => {
  try {
    tableDetailLoading.value = true
    const response = await dataInsightAPI.explorer.getTableDetail(
      HARDCODED_DATASOURCE.id,
      HARDCODED_TABLE,
      HARDCODED_SCHEMA
    )
    tableDetail.value = response
    ElMessage.success('表详情加载成功')
  } catch (error) {
    console.error('获取表详情失败:', error)
    ElMessage.error('获取表详情失败')
  } finally {
    tableDetailLoading.value = false
  }
}

const loadTableData = async () => {
  try {
    tableDataLoading.value = true
    const params: TableDataRequest = {
      datasource_id: HARDCODED_DATASOURCE.id,
      table_name: HARDCODED_TABLE,
      schema: HARDCODED_SCHEMA,
      limit: 100
    }
    
    const response = await dataInsightAPI.explorer.getTableData(params)
    tableData.value = response.data || []
    tableDataColumns.value = response.columns || []
    dataTablePagination.currentPage = 1
    dataDialogVisible.value = true
    ElMessage.success(`成功加载 ${tableData.value.length} 条记录`)
  } catch (error) {
    console.error('获取表数据失败:', error)
    ElMessage.error('获取表数据失败')
  } finally {
    tableDataLoading.value = false
  }
}

// 字段编辑相关方法
const showEditFieldDialog = (column: TableColumn) => {
  console.log('showEditFieldDialog called with:', column)
  editFieldForm.column_name = column.column_name
  editFieldForm.data_type = column.data_type
  editFieldForm.column_comment = column.column_comment || ''
  editFieldForm.column_default = column.column_default || ''
  editFieldForm.is_nullable = column.is_nullable
  editFieldDialogVisible.value = true
}

const submitEditField = async () => {
  if (!editFieldFormRef.value) return
  
  try {
    await editFieldFormRef.value.validate()
    editFieldLoading.value = true
    
    // 构建表结构修改请求（符合后端TableStructureRequest格式）
    const updateRequest = {
      datasource_id: HARDCODED_DATASOURCE.id,
      table_name: tableDetail.value?.table_name || '',
      schema: HARDCODED_SCHEMA,
      operation_type: 'modify_column',
      column_data: {
        original_name: editFieldForm.column_name,
        name: editFieldForm.column_name, // 保持列名不变
        type: editFieldForm.data_type,
        comment: editFieldForm.column_comment,
        default: editFieldForm.column_default,
        nullable: editFieldForm.is_nullable
      }
    }

    // 调用API更新字段
    const response = await dataInsightAPI.explorer.updateField(updateRequest)
    
    if (response.success) {
      ElMessage.success('字段更新成功')
      
      // 更新本地数据
      if (tableDetail.value && tableDetail.value.columns) {
        const columnIndex = tableDetail.value.columns.findIndex(
          col => col.column_name === editFieldForm.column_name
        )
        if (columnIndex !== -1) {
          tableDetail.value.columns[columnIndex] = {
            ...tableDetail.value.columns[columnIndex],
            column_comment: editFieldForm.column_comment,
            column_default: editFieldForm.column_default,
            is_nullable: editFieldForm.is_nullable
          }
        }
      }
      
      // 关闭编辑对话框
      editFieldDialogVisible.value = false
    } else {
      ElMessage.error(response.message || '字段更新失败')
    }
  } catch (error) {
    console.error('字段更新失败:', error)
    ElMessage.error('字段更新失败，请稍后重试')
  } finally {
    editFieldLoading.value = false
  }
}

// 显示删除字段对话框
const showDeleteFieldDialog = (column: TableColumn) => {
  deleteFieldInfo.column_name = column.column_name
  deleteFieldInfo.data_type = column.data_type
  deleteFieldDialogVisible.value = true
}

// 提交删除字段
const submitDeleteField = async () => {
  try {
    deleteFieldLoading.value = true
    
    // 构建表结构删除请求（符合后端TableStructureRequest格式）
    const deleteRequest = {
      datasource_id: HARDCODED_DATASOURCE.id,
      table_name: tableDetail.value?.table_name || '',
      schema: HARDCODED_SCHEMA,
      operation_type: 'drop_column',
      column_data: {
        name: deleteFieldInfo.column_name
      }
    }

    // 调用API删除字段
    const response = await dataInsightAPI.explorer.updateField(deleteRequest)
    
    if (response.success) {
      ElMessage.success('字段删除成功')
      
      // 更新本地数据 - 从列表中移除删除的字段
      if (tableDetail.value && tableDetail.value.columns) {
        tableDetail.value.columns = tableDetail.value.columns.filter(
          col => col.column_name !== deleteFieldInfo.column_name
        )
      }
      
      // 关闭删除对话框
      deleteFieldDialogVisible.value = false
    } else {
      ElMessage.error(response.message || '字段删除失败')
    }
  } catch (error) {
    console.error('字段删除失败:', error)
    ElMessage.error('字段删除失败，请稍后重试')
  } finally {
    deleteFieldLoading.value = false
  }
}

// 显示新增字段对话框
const showAddFieldDialog = () => {
  // 重置表单
  addFieldForm.column_name = ''
  addFieldForm.data_type = ''
  addFieldForm.column_comment = ''
  addFieldForm.column_default = ''
  addFieldForm.is_nullable = true
  addFieldDialogVisible.value = true
}

// 提交新增字段
const submitAddField = async () => {
  if (!addFieldFormRef.value) return
  
  try {
    await addFieldFormRef.value.validate()
    addFieldLoading.value = true
    
    // 构建表结构新增请求（符合后端TableStructureRequest格式）
    const addRequest = {
      datasource_id: HARDCODED_DATASOURCE.id,
      table_name: tableDetail.value?.table_name || '',
      schema: HARDCODED_SCHEMA,
      operation_type: 'add_column',
      column_data: {
        name: addFieldForm.column_name,
        type: addFieldForm.data_type,
        comment: addFieldForm.column_comment,
        default: addFieldForm.column_default || null,
        nullable: addFieldForm.is_nullable
      }
    }

    // 调用API新增字段
    const response = await dataInsightAPI.explorer.updateField(addRequest)
    
    if (response.success) {
      ElMessage.success('字段新增成功')
      
      // 更新本地数据 - 添加新字段到列表
      if (tableDetail.value && tableDetail.value.columns) {
        const newColumn = {
          column_name: addFieldForm.column_name,
          data_type: addFieldForm.data_type,
          column_comment: addFieldForm.column_comment,
          column_default: addFieldForm.column_default,
          is_nullable: addFieldForm.is_nullable,
          is_primary_key: false
        }
        tableDetail.value.columns.push(newColumn)
      }
      
      // 关闭新增对话框
      addFieldDialogVisible.value = false
    } else {
      ElMessage.error(response.message || '字段新增失败')
    }
  } catch (error) {
    console.error('字段新增失败:', error)
    ElMessage.error('字段新增失败，请稍后重试')
  } finally {
    addFieldLoading.value = false
  }
}

const handleDataSizeChange = (size: number) => {
  dataTablePagination.pageSize = size
  dataTablePagination.currentPage = 1
}

const handleDataCurrentChange = (page: number) => {
  dataTablePagination.currentPage = page
}

// 生命周期 - 页面加载时自动获取表详情
onMounted(() => {
  loadTableDetail()
})
</script>

<style scoped lang="scss">
.center-table-management {
  padding: 20px;

  .page-header {
    margin-bottom: 20px;

    h2 {
      margin: 0 0 8px 0;
      color: #303133;
      font-size: 24px;
      font-weight: 600;
    }

    .page-description {
      margin: 0;
      color: #606266;
      font-size: 14px;
    }
  }

  .content-wrapper {
    .main-card {
      .card-header {
        display: flex;
        justify-content: space-between;
        align-items: center;

        .header-actions {
          display: flex;
          gap: 12px;
        }
      }

      .datasource-section {
        padding: 16px;
        background-color: #f8f9fa;
        border-radius: 6px;
      }

      .search-section {
        margin-bottom: 20px;
        padding: 16px;
        background-color: #f8f9fa;
        border-radius: 6px;
      }

      .table-section {
        margin-bottom: 20px;
      }

      .pagination-section {
        display: flex;
        justify-content: flex-end;
      }

      .empty-state {
        text-align: center;
        padding: 40px 0;
      }
    }
  }

  .data-toolbar {
    display: flex;
    justify-content: space-between;
    align-items: center;

    .data-info {
      color: #606266;
      font-size: 14px;
    }
  }
}
</style>