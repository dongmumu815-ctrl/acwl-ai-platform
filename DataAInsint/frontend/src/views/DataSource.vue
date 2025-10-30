<template>
  <div class="datasource-container">
    <div class="page-header">
      <h2>数据源配置</h2>
      <el-button type="primary" @click="showCreateDialog">
        <el-icon><Plus /></el-icon>
        新增数据源
      </el-button>
    </div>

    <!-- 数据源列表 -->
    <el-card class="datasource-list">
      <el-table :data="datasources" v-loading="loading" stripe>
        <el-table-column prop="name" label="名称" width="250" />
        <el-table-column prop="db_type" label="数据库类型" width="150">
          <template #default="{ row }">
            <el-tag :type="getDbTypeColor(row.db_type)">{{ row.db_type.toUpperCase() }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="host" label="主机" width="200" />
        <el-table-column prop="port" label="端口" width="100" />
        <el-table-column prop="database_name" label="数据库" width="200" />
        <el-table-column prop="username" label="用户名" width="150" />
        <el-table-column prop="created_at" label="创建时间" width="200">
          <template #default="{ row }">
            {{ formatDate(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="150" fixed="right">
          <template #default="{ row }">
            <el-button size="small" type="primary" @click="editDatasource(row)">编辑</el-button>
            <el-button size="small" type="danger" @click="deleteDatasource(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 创建/编辑对话框 -->
    <el-dialog
      :title="dialogTitle"
      v-model="dialogVisible"
      width="600px"
      :close-on-click-modal="false"
    >
      <el-form
        ref="formRef"
        :model="form"
        :rules="rules"
        label-width="100px"
      >
        <el-form-item label="名称" prop="name">
          <el-input v-model="form.name" placeholder="请输入数据源名称" />
        </el-form-item>
        <el-form-item label="数据库类型" prop="db_type">
          <el-select v-model="form.db_type" placeholder="请选择数据库类型" @change="onDbTypeChange">
            <el-option label="Oracle" value="oracle" />
            <el-option label="MySQL" value="mysql" />
            <el-option label="Doris" value="doris" />
          </el-select>
        </el-form-item>
        <el-form-item label="主机" prop="host">
          <el-input v-model="form.host" placeholder="请输入主机地址" />
        </el-form-item>
        <el-form-item label="端口" prop="port">
          <el-input-number v-model="form.port" :min="1" :max="65535" />
        </el-form-item>
        <el-form-item label="数据库" prop="database_name">
          <el-input v-model="form.database_name" placeholder="请输入数据库名称" />
        </el-form-item>
        <el-form-item v-if="form.db_type === 'oracle'" label="连接类型" prop="oracle_connection_type">
          <el-select v-model="form.oracle_connection_type" placeholder="请选择Oracle连接类型">
            <el-option label="Service Name" value="service_name" />
            <el-option label="SID" value="sid" />
          </el-select>
        </el-form-item>
        <el-form-item label="用户名" prop="username">
          <el-input v-model="form.username" placeholder="请输入用户名" />
        </el-form-item>
        <el-form-item label="密码" prop="password">
          <el-input
            v-model="form.password"
            type="password"
            placeholder="请输入密码"
            show-password
          />
        </el-form-item>
      </el-form>
      
      <template #footer>
        <div class="dialog-footer">
          <el-button @click="dialogVisible = false">取消</el-button>
          <el-button type="info" @click="testConnectionInDialog" :loading="testLoading">
            测试连接
          </el-button>
          <el-button type="primary" @click="submitForm" :loading="submitLoading">
            确定
          </el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import { datasourceAPI } from '@/api'

const loading = ref(false)
const dialogVisible = ref(false)
const dialogTitle = ref('新增数据源')
const isEdit = ref(false)
const editId = ref(null)
const testLoading = ref(false)
const submitLoading = ref(false)
const formRef = ref()

const datasources = ref([])

const form = reactive({
  name: '',
  db_type: '',
  host: '',
  port: 3306,
  database_name: '',
  username: '',
  password: '',
  oracle_connection_type: 'service_name'
})

const rules = {
  name: [{ required: true, message: '请输入数据源名称', trigger: 'blur' }],
  db_type: [{ required: true, message: '请选择数据库类型', trigger: 'change' }],
  host: [{ required: true, message: '请输入主机地址', trigger: 'blur' }],
  port: [{ required: true, message: '请输入端口', trigger: 'blur' }],
  database_name: [{ required: true, message: '请输入数据库名称', trigger: 'blur' }],
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }]
}

// 获取数据源列表
const fetchDatasources = async () => {
  loading.value = true
  try {
    datasources.value = await datasourceAPI.getList()
  } catch (error) {
    console.error('获取数据源列表失败:', error)
  } finally {
    loading.value = false
  }
}

// 显示创建对话框
const showCreateDialog = () => {
  dialogTitle.value = '新增数据源'
  isEdit.value = false
  resetForm()
  dialogVisible.value = true
}

// 编辑数据源
const editDatasource = (row) => {
  dialogTitle.value = '编辑数据源'
  isEdit.value = true
  editId.value = row.id
  Object.assign(form, {
    name: row.name,
    db_type: row.db_type,
    host: row.host,
    port: row.port,
    database_name: row.database_name,
    username: row.username,
    password: '', // 编辑时不显示密码
    oracle_connection_type: row.oracle_connection_type || 'service_name'
  })
  dialogVisible.value = true
}

// 重置表单
const resetForm = () => {
  Object.assign(form, {
    name: '',
    db_type: '',
    host: '',
    port: 3306,
    database_name: '',
    username: '',
    password: '',
    oracle_connection_type: 'service_name'
  })
  formRef.value?.clearValidate()
}

// 数据库类型改变时设置默认端口
const onDbTypeChange = (dbType) => {
  const defaultPorts = {
    oracle: 1521,
    mysql: 3306,
    doris: 9030
  }
  
  if (defaultPorts[dbType]) {
    form.port = defaultPorts[dbType]
  }
}

// 对话框中测试连接
const testConnectionInDialog = async () => {
  if (!formRef.value) return
  
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return
  
  testLoading.value = true
  try {
    const result = await datasourceAPI.testConnection(form)
    
    if (result.success) {
      ElMessage.success('连接成功')
    } else {
      ElMessage.error(`连接失败: ${result.message}`)
    }
  } catch (error) {
    console.error('测试连接失败:', error)
  } finally {
    testLoading.value = false
  }
}

// 提交表单
const submitForm = async () => {
  if (!formRef.value) return
  
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return
  
  submitLoading.value = true
  try {
    if (isEdit.value) {
      // 编辑时，如果密码为空则不更新密码
      const updateData = { ...form }
      if (!updateData.password) {
        delete updateData.password
      }
      await datasourceAPI.update(editId.value, updateData)
      ElMessage.success('更新成功')
    } else {
      await datasourceAPI.create(form)
      ElMessage.success('创建成功')
    }
    
    dialogVisible.value = false
    fetchDatasources()
  } catch (error) {
    console.error('提交失败:', error)
  } finally {
    submitLoading.value = false
  }
}

// 删除数据源
const deleteDatasource = async (row) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除数据源 "${row.name}" 吗？`,
      '确认删除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    await datasourceAPI.delete(row.id)
    ElMessage.success('删除成功')
    fetchDatasources()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除失败:', error)
    }
  }
}

// 获取数据库类型颜色
const getDbTypeColor = (type) => {
  const colors = {
    oracle: 'danger',
    mysql: 'primary',
    doris: 'success'
  }
  return colors[type.toLowerCase()] || 'info'
}

// 格式化日期
const formatDate = (dateString) => {
  return new Date(dateString).toLocaleString('zh-CN')
}

onMounted(() => {
  fetchDatasources()
})
</script>

<style scoped>
.datasource-container {
  padding: 20px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.page-header h2 {
  margin: 0;
  color: #303133;
}

.datasource-list {
  margin-top: 20px;
}

.dialog-footer {
  text-align: right;
}
</style>