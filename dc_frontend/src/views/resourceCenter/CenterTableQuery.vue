<template>
  <div class="center-table-query">
    <div class="page-header">
      <h2>中心表查询</h2>
      <p class="page-description">查询和浏览数据中心表的数据内容</p>
    </div>

    <div class="content-wrapper">
      <!-- 查询配置区域 -->
      <el-card class="query-config-card">
        <template #header>
          <div class="card-header">
            <span>查询配置</span>
          </div>
        </template>

        <el-form :model="queryForm" label-width="100px">
          <el-row :gutter="20">
            <el-col :span="8">
              <el-form-item label="选择表">
                <el-select
                  v-model="queryForm.selectedTable"
                  placeholder="请选择要查询的表"
                  style="width: 100%"
                  @change="handleTableChange"
                >
                  <el-option
                    v-for="table in availableTables"
                    :key="table.value"
                    :label="table.label"
                    :value="table.value"
                  />
                </el-select>
              </el-form-item>
            </el-col>
            <el-col :span="8">
              <el-form-item label="查询条件">
                <el-input
                  v-model="queryForm.condition"
                  placeholder="请输入查询条件 (SQL WHERE 子句)"
                  clearable
                />
              </el-form-item>
            </el-col>
            <el-col :span="8">
              <el-form-item label="限制条数">
                <el-input-number
                  v-model="queryForm.limit"
                  :min="1"
                  :max="1000"
                  style="width: 100%"
                />
              </el-form-item>
            </el-col>
          </el-row>

          <el-row>
            <el-col :span="24">
              <el-form-item label="选择字段">
                <el-checkbox-group v-model="queryForm.selectedFields">
                  <el-checkbox
                    v-for="field in tableFields"
                    :key="field.name"
                    :label="field.name"
                  >
                    {{ field.label }} ({{ field.type }})
                  </el-checkbox>
                </el-checkbox-group>
              </el-form-item>
            </el-col>
          </el-row>

          <el-row>
            <el-col :span="24">
              <el-form-item>
                <el-button
                  type="primary"
                  :loading="queryLoading"
                  @click="handleQuery"
                >
                  执行查询
                </el-button>
                <el-button @click="handleReset">重置</el-button>
                <el-button
                  type="success"
                  :disabled="!queryResult.length"
                  @click="handleExport"
                >
                  导出结果
                </el-button>
              </el-form-item>
            </el-col>
          </el-row>
        </el-form>
      </el-card>

      <!-- SQL预览区域 -->
      <el-card v-if="generatedSQL" class="sql-preview-card">
        <template #header>
          <div class="card-header">
            <span>生成的SQL语句</span>
            <el-button size="small" @click="copySQLToClipboard">
              复制SQL
            </el-button>
          </div>
        </template>
        <div class="sql-content">
          <pre><code>{{ generatedSQL }}</code></pre>
        </div>
      </el-card>

      <!-- 查询结果区域 -->
      <el-card v-if="queryResult.length" class="result-card">
        <template #header>
          <div class="card-header">
            <span>查询结果 ({{ queryResult.length }} 条记录)</span>
            <div class="result-actions">
              <el-button size="small" @click="handleRefreshQuery">
                刷新
              </el-button>
            </div>
          </div>
        </template>

        <div class="result-table">
          <el-table
            :data="queryResult"
            stripe
            border
            style="width: 100%"
            max-height="500"
          >
            <el-table-column
              v-for="column in resultColumns"
              :key="column.prop"
              :prop="column.prop"
              :label="column.label"
              :width="column.width"
              show-overflow-tooltip
            />
          </el-table>
        </div>
      </el-card>

      <!-- 空状态 -->
      <el-empty
        v-if="!queryResult.length && !queryLoading"
        description="请选择表并执行查询"
        :image-size="120"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'

// 查询表单
const queryForm = reactive({
  selectedTable: '',
  condition: '',
  limit: 100,
  selectedFields: [] as string[]
})

// 可用表列表
const availableTables = ref([
  { label: '用户中心表 (user_center_table)', value: 'user_center_table' },
  { label: '产品中心表 (product_center_table)', value: 'product_center_table' },
  { label: '订单中心表 (order_center_table)', value: 'order_center_table' }
])

// 表字段信息
const tableFields = ref([])

// 查询结果
const queryResult = ref([])
const queryLoading = ref(false)

// 结果表格列配置
const resultColumns = ref([])

// 生成的SQL语句
const generatedSQL = computed(() => {
  if (!queryForm.selectedTable || !queryForm.selectedFields.length) {
    return ''
  }

  const fields = queryForm.selectedFields.join(', ')
  let sql = `SELECT ${fields} FROM ${queryForm.selectedTable}`
  
  if (queryForm.condition) {
    sql += ` WHERE ${queryForm.condition}`
  }
  
  sql += ` LIMIT ${queryForm.limit}`
  
  return sql
})

// 获取表字段信息
const fetchTableFields = async (tableName: string) => {
  try {
    // TODO: 调用API获取表字段信息
    // 模拟数据
    const mockFields = {
      user_center_table: [
        { name: 'id', label: 'ID', type: 'INT' },
        { name: 'username', label: '用户名', type: 'VARCHAR' },
        { name: 'email', label: '邮箱', type: 'VARCHAR' },
        { name: 'create_time', label: '创建时间', type: 'DATETIME' }
      ],
      product_center_table: [
        { name: 'id', label: 'ID', type: 'INT' },
        { name: 'product_name', label: '产品名称', type: 'VARCHAR' },
        { name: 'price', label: '价格', type: 'DECIMAL' },
        { name: 'category', label: '分类', type: 'VARCHAR' }
      ],
      order_center_table: [
        { name: 'id', label: 'ID', type: 'INT' },
        { name: 'order_no', label: '订单号', type: 'VARCHAR' },
        { name: 'user_id', label: '用户ID', type: 'INT' },
        { name: 'total_amount', label: '总金额', type: 'DECIMAL' }
      ]
    }

    tableFields.value = mockFields[tableName] || []
    queryForm.selectedFields = tableFields.value.map(field => field.name)
  } catch (error) {
    ElMessage.error('获取表字段信息失败')
  }
}

// 表选择改变
const handleTableChange = (tableName: string) => {
  if (tableName) {
    fetchTableFields(tableName)
  } else {
    tableFields.value = []
    queryForm.selectedFields = []
  }
}

// 执行查询
const handleQuery = async () => {
  if (!queryForm.selectedTable) {
    ElMessage.warning('请选择要查询的表')
    return
  }

  if (!queryForm.selectedFields.length) {
    ElMessage.warning('请选择要查询的字段')
    return
  }

  queryLoading.value = true
  try {
    // TODO: 调用API执行查询
    // 模拟数据
    const mockData = {
      user_center_table: [
        { id: 1, username: 'admin', email: 'admin@example.com', create_time: '2024-01-15 10:30:00' },
        { id: 2, username: 'user1', email: 'user1@example.com', create_time: '2024-01-16 14:20:00' }
      ],
      product_center_table: [
        { id: 1, product_name: '产品A', price: 99.99, category: '电子产品' },
        { id: 2, product_name: '产品B', price: 199.99, category: '家居用品' }
      ],
      order_center_table: [
        { id: 1, order_no: 'ORD001', user_id: 1, total_amount: 299.98 },
        { id: 2, order_no: 'ORD002', user_id: 2, total_amount: 99.99 }
      ]
    }

    queryResult.value = mockData[queryForm.selectedTable] || []
    
    // 生成表格列配置
    resultColumns.value = queryForm.selectedFields.map(fieldName => {
      const field = tableFields.value.find(f => f.name === fieldName)
      return {
        prop: fieldName,
        label: field?.label || fieldName,
        width: fieldName === 'id' ? 80 : undefined
      }
    })

    ElMessage.success(`查询完成，共 ${queryResult.value.length} 条记录`)
  } catch (error) {
    ElMessage.error('查询失败')
  } finally {
    queryLoading.value = false
  }
}

// 重置表单
const handleReset = () => {
  Object.assign(queryForm, {
    selectedTable: '',
    condition: '',
    limit: 100,
    selectedFields: []
  })
  tableFields.value = []
  queryResult.value = []
  resultColumns.value = []
}

// 刷新查询
const handleRefreshQuery = () => {
  handleQuery()
}

// 导出结果
const handleExport = () => {
  ElMessage.info('导出功能待实现')
}

// 复制SQL到剪贴板
const copySQLToClipboard = async () => {
  try {
    await navigator.clipboard.writeText(generatedSQL.value)
    ElMessage.success('SQL已复制到剪贴板')
  } catch {
    ElMessage.error('复制失败')
  }
}

onMounted(() => {
  // 初始化
})
</script>

<style scoped lang="scss">
.center-table-query {
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
    .query-config-card,
    .sql-preview-card,
    .result-card {
      margin-bottom: 20px;

      .card-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
      }
    }

    .sql-preview-card {
      .sql-content {
        background-color: #f8f9fa;
        border-radius: 6px;
        padding: 16px;

        pre {
          margin: 0;
          font-family: 'Courier New', monospace;
          font-size: 14px;
          line-height: 1.5;
          color: #303133;
        }
      }
    }

    .result-card {
      .result-actions {
        display: flex;
        gap: 8px;
      }

      .result-table {
        :deep(.el-table) {
          font-size: 14px;
        }
      }
    }
  }
}
</style>