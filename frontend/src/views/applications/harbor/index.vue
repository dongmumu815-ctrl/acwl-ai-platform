<template>
  <div class="harbor-page">
    <div class="page-header">
      <div class="header-left">
        <h2>Harbor 仓库配置</h2>
        <p class="description">管理 Docker 镜像仓库连接配置，用于拉取和管理应用镜像。</p>
      </div>
      <div class="header-right">
        <el-button type="primary" @click="handleAdd">
          <el-icon><Plus /></el-icon>
          添加配置
        </el-button>
      </div>
    </div>

    <div class="table-container">
      <el-table :data="tableData" v-loading="loading" style="width: 100%">
        <el-table-column prop="name" label="配置名称" min-width="150" />
        <el-table-column prop="url" label="Harbor 地址" min-width="200">
          <template #default="{ row }">
            <el-link :href="row.url" target="_blank" type="primary">{{ row.url }}</el-link>
          </template>
        </el-table-column>
        <el-table-column prop="username" label="用户名" min-width="120" />
        <el-table-column prop="project" label="默认项目" min-width="120" />
        <el-table-column prop="is_default" label="默认仓库" width="100">
          <template #default="{ row }">
            <el-tag v-if="row.is_default" type="success">是</el-tag>
            <el-tag v-else type="info">否</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="insecure_registry" label="Insecure Registry" width="140">
          <template #default="{ row }">
            <el-tag v-if="row.insecure_registry" type="warning">是</el-tag>
            <el-tag v-else type="info">否</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="description" label="描述" min-width="200" show-overflow-tooltip />
        <el-table-column prop="updated_at" label="更新时间" width="180">
          <template #default="{ row }">
            {{ formatDateTime(row.updated_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="220" fixed="right">
          <template #default="{ row }">
            <el-button link type="success" @click="handleTest(row)">测试</el-button>
            <el-button link type="primary" @click="handleEdit(row)">编辑</el-button>
            <el-button link type="danger" @click="handleDelete(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>

      <div class="pagination-container">
        <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.size"
          :total="pagination.total"
          :page-sizes="[10, 20, 50, 100]"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="fetchData"
          @current-change="fetchData"
        />
      </div>
    </div>

    <!-- Dialog -->
    <el-dialog
      v-model="dialogVisible"
      :title="dialogType === 'create' ? '添加 Harbor 配置' : '编辑 Harbor 配置'"
      width="500px"
    >
      <el-form ref="formRef" :model="form" :rules="rules" label-width="100px">
        <el-form-item label="配置名称" prop="name">
          <el-input v-model="form.name" placeholder="请输入配置名称" />
        </el-form-item>
        <el-form-item label="Harbor 地址" prop="url">
          <el-input v-model="form.url" placeholder="http://harbor.example.com" />
        </el-form-item>
        <el-form-item label="用户名" prop="username">
          <el-input v-model="form.username" placeholder="请输入用户名" />
        </el-form-item>
        <el-form-item label="密码" prop="password">
          <el-input v-model="form.password" type="password" show-password placeholder="请输入密码" />
        </el-form-item>
        <el-form-item label="默认项目" prop="project">
          <el-input v-model="form.project" placeholder="library" />
        </el-form-item>
        <el-form-item label="默认仓库" prop="is_default">
          <el-switch v-model="form.is_default" />
        </el-form-item>
        <el-form-item label="Insecure Registry" prop="insecure_registry">
          <el-switch v-model="form.insecure_registry" />
          <div style="font-size: 12px; color: #999; margin-left: 10px;">
            启用后将自动配置 Docker daemon.json 并重启 Docker 服务，支持 HTTP 协议
          </div>
        </el-form-item>
        <el-form-item label="描述" prop="description">
          <el-input v-model="form.description" type="textarea" :rows="3" />
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button type="success" :loading="testing" @click="handleTestDialog">测试连接</el-button>
          <el-button @click="dialogVisible = false">取消</el-button>
          <el-button type="primary" :loading="submitting" @click="handleSubmit">
            确定
          </el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox, ElLoading } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import { getHarborConfigs, createHarborConfig, updateHarborConfig, deleteHarborConfig, testHarborConnection } from '@/api/application'
import type { HarborConfig, HarborConfigForm } from '@/api/application'
import { formatDateTime } from "@/utils/date";

const loading = ref(false)
const testing = ref(false)
const tableData = ref<HarborConfig[]>([])
const pagination = reactive({
  page: 1,
  size: 20,
  total: 0
})

const dialogVisible = ref(false)
const dialogType = ref<'create' | 'edit'>('create')
const submitting = ref(false)
const formRef = ref()
const currentId = ref<number | null>(null)

const form = reactive<HarborConfigForm>({
  name: '',
  url: '',
  username: '',
  password: '',
  project: '',
  is_default: false,
  insecure_registry: false,
  description: ''
})

const rules = {
  name: [{ required: true, message: '请输入配置名称', trigger: 'blur' }],
  url: [{ required: true, message: '请输入 Harbor 地址', trigger: 'blur' }]
}

const fetchData = async () => {
  loading.value = true
  try {
    const res = await getHarborConfigs({
      page: pagination.page,
      size: pagination.size
    })
    tableData.value = res.items
    pagination.total = res.total
  } catch (error) {
    console.error(error)
  } finally {
    loading.value = false
  }
}

const handleAdd = () => {
  dialogType.value = 'create'
  currentId.value = null
  Object.assign(form, {
    name: '',
    url: '',
    username: '',
    password: '',
    project: '',
    is_default: false,
    insecure_registry: false,
    description: ''
  })
  dialogVisible.value = true
}

const handleEdit = (row: HarborConfig) => {
  dialogType.value = 'edit'
  currentId.value = row.id
  Object.assign(form, {
    name: row.name,
    url: row.url,
    username: row.username,
    password: row.password, // Usually empty from backend for security, but user might want to update it
    project: row.project,
    is_default: row.is_default,
    insecure_registry: row.insecure_registry,
    description: row.description
  })
  dialogVisible.value = true
}

const handleDelete = async (row: HarborConfig) => {
  try {
    await ElMessageBox.confirm('确定要删除该配置吗？', '提示', {
      type: 'warning'
    })
    await deleteHarborConfig(row.id)
    ElMessage.success('删除成功')
    fetchData()
  } catch (error) {
    if (error !== 'cancel') {
      console.error(error)
    }
  }
}

const handleTest = async (row: HarborConfig) => {
  const loadingInstance = ElLoading.service({
    target: document.querySelector('.el-table__body-wrapper') as HTMLElement,
    text: '测试连接中...',
    background: 'rgba(255, 255, 255, 0.7)'
  })
  try {
    const res = await testHarborConnection({
      id: row.id,
      url: row.url,
      username: row.username || '',
      // 密码不需要传，后端会自己查
      project: row.project || undefined
    })
    if (res.success) {
      ElMessage.success(res.message)
    } else {
      ElMessage.error(res.message)
    }
  } catch (error) {
    console.error(error)
    ElMessage.error('测试连接失败')
  } finally {
    loadingInstance.close()
  }
}

const handleTestDialog = async () => {
  if (!form.url || !form.username) {
    ElMessage.warning('请填写Harbor地址和用户名')
    return
  }
  
  testing.value = true
  try {
    const res = await testHarborConnection({
      id: currentId.value || undefined, // 如果是编辑模式，传入 ID
      url: form.url,
      username: form.username || '',
      password: form.password, // 如果用户输入了新密码，或者是新增模式，这里会有值
      project: form.project || undefined
    })
    if (res.success) {
      ElMessage.success(res.message)
    } else {
      ElMessage.error(res.message)
    }
  } catch (error) {
    console.error(error)
    ElMessage.error('测试连接失败')
  } finally {
    testing.value = false
  }
}

const handleSubmit = async () => {
  if (!formRef.value) return
  await formRef.value.validate(async (valid: boolean) => {
    if (valid) {
      submitting.value = true
      try {
        if (dialogType.value === 'create') {
          await createHarborConfig(form)
          ElMessage.success('创建成功')
        } else {
          await updateHarborConfig(currentId.value!, form)
          ElMessage.success('更新成功')
        }
        dialogVisible.value = false
        fetchData()
      } catch (error) {
        console.error(error)
      } finally {
        submitting.value = false
      }
    }
  })
}

onMounted(() => {
  fetchData()
})
</script>

<style scoped>
.harbor-page {
  padding: 20px;
  background-color: #fff;
  height: 100%;
  display: flex;
  flex-direction: column;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 20px;
}

.header-left h2 {
  margin: 0 0 8px 0;
  font-size: 20px;
  font-weight: 500;
}

.description {
  color: #666;
  font-size: 14px;
  margin: 0;
}

.table-container {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.pagination-container {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
}
</style>
