<template>
  <div class="environment-list-container">
    <div class="page-header">
      <div class="header-left">
        <h2>环境配置管理</h2>
        <span class="subtitle">管理系统运行环境配置和参数</span>
      </div>
      <el-button type="primary" @click="handleCreate">
        <el-icon><Plus /></el-icon>创建环境
      </el-button>
    </div>

    <el-card class="content-card" shadow="hover">
      <!-- 搜索栏 -->
      <div class="filter-bar">
        <el-input
          v-model="queryParams.search"
          placeholder="搜索环境名称"
          clearable
          @clear="handleSearch"
          @keyup.enter="handleSearch"
          style="width: 200px"
        >
          <template #prefix>
            <el-icon><Search /></el-icon>
          </template>
        </el-input>
        <el-button type="primary" @click="handleSearch">查询</el-button>
        <el-button @click="resetQuery">重置</el-button>
      </div>

      <!-- 表格 -->
      <el-table
        v-loading="loading"
        :data="envList"
        style="width: 100%"
        border
      >
        <el-table-column prop="id" label="ID" width="80" align="center" />
        <el-table-column prop="name" label="环境名称" min-width="150" show-overflow-tooltip />
        <el-table-column prop="description" label="描述" min-width="200" show-overflow-tooltip />
        <el-table-column prop="created_at" label="创建时间" width="180">
          <template #default="{ row }">
            {{ formatDate(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column prop="updated_at" label="更新时间" width="180">
          <template #default="{ row }">
            {{ formatDate(row.updated_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="200" fixed="right" align="center">
          <template #default="{ row }">
            <el-button link type="primary" @click="handleEdit(row)">编辑</el-button>
            <el-button link type="danger" @click="handleDelete(row)">删除</el-button>
            <el-button link type="primary" @click="handleViewConfig(row)">查看配置</el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
      <div class="pagination-container">
        <el-pagination
          v-model:current-page="queryParams.page"
          v-model:page-size="queryParams.size"
          :total="total"
          :page-sizes="[10, 20, 50, 100]"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="handleSearch"
          @current-change="handleSearch"
        />
      </div>
    </el-card>

    <!-- 编辑/创建弹窗 -->
    <el-dialog
      v-model="dialogVisible"
      :title="dialogType === 'create' ? '创建环境' : '编辑环境'"
      width="600px"
      @close="resetForm"
    >
      <el-form
        ref="formRef"
        :model="formData"
        :rules="rules"
        label-width="100px"
      >
        <el-form-item label="环境名称" prop="name">
          <el-input v-model="formData.name" placeholder="请输入环境名称" :disabled="dialogType === 'edit'" />
        </el-form-item>
        <el-form-item label="描述" prop="description">
          <el-input v-model="formData.description" type="textarea" :rows="3" placeholder="请输入环境描述" />
        </el-form-item>
        <el-form-item label="配置(JSON)" prop="configStr">
          <el-input 
            v-model="formData.configStr" 
            type="textarea" 
            :rows="10" 
            placeholder="请输入JSON格式的配置"
            font-family="monospace"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="dialogVisible = false">取消</el-button>
          <el-button type="primary" @click="submitForm" :loading="submitting">确定</el-button>
        </span>
      </template>
    </el-dialog>

    <!-- 查看配置弹窗 -->
    <el-dialog
      v-model="configDialogVisible"
      title="环境配置详情"
      width="600px"
    >
      <pre class="json-viewer">{{ currentConfig }}</pre>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="configDialogVisible = false">关闭</el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Search } from '@element-plus/icons-vue'
import { getEnvironments, createEnvironment, updateEnvironment, deleteEnvironment } from '@/api/resource'
import dayjs from 'dayjs'

const loading = ref(false)
const submitting = ref(false)
const dialogVisible = ref(false)
const configDialogVisible = ref(false)
const dialogType = ref('create') // 'create' or 'edit'
const formRef = ref(null)
const currentConfig = ref('')

const queryParams = reactive({
  page: 1,
  size: 20,
  search: ''
})

const total = ref(0)
const envList = ref([])

const formData = reactive({
  id: null,
  name: '',
  description: '',
  configStr: '{}'
})

const validateJson = (rule, value, callback) => {
  if (!value) {
    callback()
    return
  }
  try {
    JSON.parse(value)
    callback()
  } catch (e) {
    callback(new Error('请输入有效的JSON格式'))
  }
}

const rules = {
  name: [
    { required: true, message: '请输入环境名称', trigger: 'blur' },
    { min: 2, max: 100, message: '长度在 2 到 100 个字符', trigger: 'blur' }
  ],
  configStr: [
    { validator: validateJson, trigger: 'blur' }
  ]
}

const formatDate = (date) => {
  if (!date) return '-'
  return dayjs(date).format('YYYY-MM-DD HH:mm:ss')
}

const fetchData = async () => {
  loading.value = true
  try {
    const res = await getEnvironments(queryParams)
    envList.value = res.items
    total.value = res.total
  } catch (error) {
    console.error('获取环境列表失败:', error)
  } finally {
    loading.value = false
  }
}

const handleSearch = () => {
  queryParams.page = 1
  fetchData()
}

const resetQuery = () => {
  queryParams.search = ''
  handleSearch()
}

const handleCreate = () => {
  dialogType.value = 'create'
  formData.id = null
  formData.name = ''
  formData.description = ''
  formData.configStr = '{\n  \n}'
  dialogVisible.value = true
}

const handleEdit = (row) => {
  dialogType.value = 'edit'
  formData.id = row.id
  formData.name = row.name
  formData.description = row.description
  // Format JSON for better readability
  try {
    formData.configStr = JSON.stringify(row.config || {}, null, 2)
  } catch (e) {
    formData.configStr = '{}'
  }
  dialogVisible.value = true
}

const handleViewConfig = (row) => {
  try {
    currentConfig.value = JSON.stringify(row.config || {}, null, 2)
  } catch (e) {
    currentConfig.value = '{}'
  }
  configDialogVisible.value = true
}

const handleDelete = async (row) => {
  try {
    await ElMessageBox.confirm(`确定要删除环境 "${row.name}" 吗？`, '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    
    await deleteEnvironment(row.id)
    ElMessage.success('删除成功')
    fetchData()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除失败:', error)
    }
  }
}

const submitForm = async () => {
  if (!formRef.value) return
  
  await formRef.value.validate(async (valid) => {
    if (valid) {
      submitting.value = true
      try {
        const payload = {
          name: formData.name,
          description: formData.description,
          config: JSON.parse(formData.configStr || '{}')
        }

        if (dialogType.value === 'create') {
          await createEnvironment(payload)
          ElMessage.success('创建成功')
        } else {
          await updateEnvironment(formData.id, payload)
          ElMessage.success('更新成功')
        }
        dialogVisible.value = false
        fetchData()
      } catch (error) {
        console.error('提交失败:', error)
      } finally {
        submitting.value = false
      }
    }
  })
}

const resetForm = () => {
  if (formRef.value) {
    formRef.value.resetFields()
  }
}

onMounted(() => {
  fetchData()
})
</script>

<style scoped>
.environment-list-container {
  padding: 20px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.header-left h2 {
  margin: 0;
  font-size: 24px;
  color: #303133;
}

.subtitle {
  font-size: 14px;
  color: #909399;
  margin-top: 5px;
  display: block;
}

.content-card {
  margin-bottom: 20px;
}

.filter-bar {
  margin-bottom: 20px;
  display: flex;
  gap: 10px;
}

.pagination-container {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
}

.json-viewer {
  background-color: #f5f7fa;
  padding: 15px;
  border-radius: 4px;
  overflow: auto;
  max-height: 400px;
  font-family: monospace;
  white-space: pre-wrap;
}
</style>
