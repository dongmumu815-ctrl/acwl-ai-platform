<template>
  <div class="executor-groups-container">
    <div class="page-header">
      <div class="header-left">
        <h2>执行器分组管理</h2>
        <span class="subtitle">管理执行器节点的逻辑分组和负载均衡策略</span>
      </div>
      <el-button type="primary" @click="handleCreate">
        <el-icon><Plus /></el-icon>创建分组
      </el-button>
    </div>

    <el-card class="content-card" shadow="hover">
      <!-- 搜索栏 -->
      <div class="filter-bar">
        <el-input
          v-model="queryParams.group_name"
          placeholder="搜索分组名称"
          clearable
          @clear="handleSearch"
          @keyup.enter="handleSearch"
          style="width: 200px"
        >
          <template #prefix>
            <el-icon><Search /></el-icon>
          </template>
        </el-input>
        <el-select v-model="queryParams.group_type" placeholder="分组类型" clearable style="width: 160px">
           <el-option label="默认" value="DEFAULT" />
           <el-option label="计算密集型" value="compute" />
           <el-option label="GPU" value="GPU" />
           <el-option label="内存密集型" value="MEMORY_INTENSIVE" />
           <el-option label="IO密集型" value="io_intensive" />
        </el-select>
        <el-button type="primary" @click="handleSearch">查询</el-button>
        <el-button @click="resetQuery">重置</el-button>
      </div>

      <!-- 表格 -->
      <el-table
        v-loading="loading"
        :data="groupList"
        style="width: 100%"
        border
      >
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="group_name" label="分组名称" min-width="150" show-overflow-tooltip />
        <el-table-column prop="group_type" label="类型" width="120">
          <template #default="{ row }">
            <el-tag :type="getGroupTypeTag(row.group_type)">{{ row.group_type }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="max_concurrent_tasks" label="最大并发" width="100" align="center" />
        <el-table-column prop="load_balance_strategy" label="负载均衡" width="150" show-overflow-tooltip />
        <el-table-column prop="is_active" label="状态" width="100" align="center">
          <template #default="{ row }">
            <el-tag :type="row.is_active ? 'success' : 'info'">
              {{ row.is_active ? '启用' : '禁用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="180">
          <template #default="{ row }">
            {{ formatDate(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="handleEdit(row)">编辑</el-button>
            <el-button link type="danger" @click="handleDelete(row)">删除</el-button>
            <!-- 预留：查看节点 -->
            <!-- <el-button link type="primary" @click="viewNodes(row)">节点</el-button> -->
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

    <!-- 弹窗 -->
    <el-dialog
      v-model="dialogVisible"
      :title="dialogType === 'create' ? '创建分组' : '编辑分组'"
      width="500px"
      @close="resetForm"
    >
      <el-form
        ref="formRef"
        :model="formData"
        :rules="rules"
        label-width="100px"
      >
        <el-form-item label="分组名称" prop="group_name">
          <el-input v-model="formData.group_name" placeholder="请输入分组名称" :disabled="dialogType === 'edit'" />
        </el-form-item>
        <el-form-item label="显示名称" prop="group_display_name">
          <el-input v-model="formData.group_display_name" placeholder="请输入显示名称" />
        </el-form-item>
        <el-form-item label="分组类型" prop="group_type">
          <el-select v-model="formData.group_type" placeholder="请选择类型" style="width: 100%">
             <el-option label="默认" value="DEFAULT" />
             <el-option label="计算密集型" value="compute" />
             <el-option label="GPU" value="GPU" />
             <el-option label="内存密集型" value="MEMORY_INTENSIVE" />
             <el-option label="IO密集型" value="io_intensive" />
          </el-select>
        </el-form-item>
        <el-form-item label="负载均衡" prop="load_balance_strategy">
          <el-select v-model="formData.load_balance_strategy" placeholder="请选择策略" style="width: 100%">
            <el-option label="轮询 (Round Robin)" value="ROUND_ROBIN" />
            <el-option label="最少连接" value="LEAST_CONNECTIONS" />
            <el-option label="最小负载" value="LEAST_LOAD" />
            <el-option label="随机" value="RANDOM" />
          </el-select>
        </el-form-item>
        <el-form-item label="最大并发" prop="max_concurrent_tasks">
          <el-input-number v-model="formData.max_concurrent_tasks" :min="1" :max="1000" />
        </el-form-item>
        <el-form-item label="状态" prop="is_active">
          <el-switch v-model="formData.is_active" active-text="启用" inactive-text="禁用" />
        </el-form-item>
        <el-form-item label="描述" prop="group_description">
          <el-input v-model="formData.group_description" type="textarea" :rows="3" placeholder="请输入描述" />
        </el-form-item>
        
        <el-form-item label="关联执行器">
          <el-transfer
            v-model="formData.executor_ids"
            :data="executorTransferData"
            :titles="['可选执行器', '已关联执行器']"
            filterable
            filter-placeholder="搜索节点"
          >
            <template #default="{ option }">
              <span class="transfer-item">
                {{ option.label }}
                <el-tag size="small" :type="option.statusType" style="margin-left: 5px; transform: scale(0.8);">{{ option.statusText }}</el-tag>
              </span>
            </template>
          </el-transfer>
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="dialogVisible = false">取消</el-button>
          <el-button type="primary" @click="submitForm" :loading="submitting">确定</el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Search, Refresh } from '@element-plus/icons-vue'
import { getExecutorGroups, createExecutorGroup, updateExecutorGroup, deleteExecutorGroup, getExecutorNodes, getExecutorGroupNodes } from '@/api/resource'
import dayjs from 'dayjs'

const loading = ref(false)
const submitting = ref(false)
const dialogVisible = ref(false)
const dialogType = ref('create') // 'create' or 'edit'
const formRef = ref(null)

// 执行器列表相关
const executorTransferData = ref([])

const queryParams = reactive({
  page: 1,
  size: 20,
  group_name: '',
  group_type: ''
})

const total = ref(0)
const groupList = ref([])

const formData = reactive({
  id: null,
  group_name: '',
  group_display_name: '',
  group_type: 'DEFAULT',
  load_balance_strategy: 'ROUND_ROBIN',
  max_concurrent_tasks: 10,
  is_active: true,
  group_description: '',
  executor_ids: []
})

const rules = {
  group_name: [
    { required: true, message: '请输入分组名称', trigger: 'blur' },
    { min: 2, max: 50, message: '长度在 2 到 50 个字符', trigger: 'blur' }
  ],
  group_type: [
    { required: true, message: '请选择分组类型', trigger: 'change' }
  ]
}

const getGroupTypeTag = (type) => {
  const map = {
    'DEFAULT': '',
    'GPU': 'warning',
    'compute': 'success',
    'MEMORY_INTENSIVE': 'danger',
    'io_intensive': 'info'
  }
  return map[type] || 'info'
}

const formatDate = (date) => {
  if (!date) return '-'
  return dayjs(date).format('YYYY-MM-DD HH:mm:ss')
}

const fetchExecutorList = async () => {
  try {
    const res = await getExecutorNodes({ page: 1, size: 1000 })
    executorTransferData.value = res.items.map(node => ({
      key: node.id,
      label: node.node_name,
      statusType: node.status === 'online' ? 'success' : 'info',
      statusText: node.status
    }))
  } catch (error) {
    console.error('获取执行器列表失败', error)
    ElMessage.error('获取执行器列表失败')
  }
}

const fetchData = async () => {
  loading.value = true
  try {
    const res = await getExecutorGroups(queryParams)
    groupList.value = res.items
    total.value = res.total
  } catch (error) {
    console.error('获取分组列表失败:', error)
  } finally {
    loading.value = false
  }
}

const handleSearch = () => {
  queryParams.page = 1
  fetchData()
}

const resetQuery = () => {
  queryParams.group_name = ''
  queryParams.group_type = ''
  handleSearch()
}

const handleCreate = async () => {
  dialogType.value = 'create'
  formData.id = null
  formData.group_name = ''
  formData.group_display_name = ''
  formData.group_type = 'DEFAULT'
  formData.load_balance_strategy = 'ROUND_ROBIN'
  formData.max_concurrent_tasks = 10
  formData.is_active = true
  formData.group_description = ''
  formData.executor_ids = []
  
  await fetchExecutorList()
  dialogVisible.value = true
}

const handleEdit = async (row) => {
  dialogType.value = 'edit'
  Object.assign(formData, row)
  formData.executor_ids = [] // 先清空
  
  await fetchExecutorList()
  dialogVisible.value = true
  
  // 获取已关联的节点
  try {
    const res = await getExecutorGroupNodes(row.id, { page: 1, size: 1000 })
    formData.executor_ids = res.items.map(node => node.id)
  } catch (error) {
    console.error('获取分组关联节点失败', error)
    ElMessage.error('获取分组关联节点失败')
  }
}

const handleDelete = async (row) => {
  try {
    await ElMessageBox.confirm(`确定要删除分组 "${row.group_name}" 吗？`, '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    
    await deleteExecutorGroup(row.id)
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
        if (dialogType.value === 'create') {
          await createExecutorGroup(formData)
          ElMessage.success('创建成功')
        } else {
          await updateExecutorGroup(formData.id, formData)
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
.executor-groups-container {
  padding: 24px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}

.header-left h2 {
  margin: 0;
  font-size: 24px;
  font-weight: 600;
  color: #1f2937;
}

.subtitle {
  color: #6b7280;
  font-size: 14px;
  margin-top: 4px;
  display: block;
}

.content-card {
  border-radius: 8px;
}

.filter-bar {
  display: flex;
  gap: 12px;
  margin-bottom: 20px;
}

.pagination-container {
  display: flex;
  justify-content: flex-end;
  margin-top: 20px;
}
</style>
