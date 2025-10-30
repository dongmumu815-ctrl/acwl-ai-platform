<template>
  <div class="environments-page">
    <el-card class="mb-3" shadow="never">
      <div class="toolbar">
        <el-input v-model="search" placeholder="搜索环境名称或描述" clearable style="max-width: 280px" @keyup.enter="fetchList" />
        <el-button type="primary" class="ml-2" @click="fetchList">
          <el-icon><Search /></el-icon>
          查询
        </el-button>
        <el-button type="success" class="ml-2" @click="openCreate">
          <el-icon><Plus /></el-icon>
          新建环境
        </el-button>
      </div>
    </el-card>

    <el-card shadow="never">
      <el-table :data="items" v-loading="loading" border style="width: 100%">
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="name" label="环境名称" min-width="180" />
        <el-table-column label="配置" min-width="220">
          <template #default="{ row }">
            <el-tooltip placement="top" :content="formatShortJSON(row.config)">
              <span class="ellipsis">{{ formatShortJSON(row.config) }}</span>
            </el-tooltip>
          </template>
        </el-table-column>
        <el-table-column prop="description" label="描述" min-width="220">
          <template #default="{ row }">
            <span class="ellipsis">{{ row.description || '-' }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="updated_at" label="更新时间" width="180">
          <template #default="{ row }">
            {{ formatDate(row.updated_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="220" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" link @click="openEdit(row)">编辑</el-button>
            <el-button type="danger" link @click="confirmDelete(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>

      <div class="mt-3 flex-row-end">
        <el-pagination
          background
          layout="prev, pager, next, jumper"
          :total="total"
          :page-size="size"
          :current-page="page"
          @current-change="onPageChange"
          @size-change="onSizeChange"
        />
      </div>
    </el-card>

    <el-dialog :title="dialogTitle" v-model="dialogVisible" width="640px">
      <el-form :model="form" :rules="rules" ref="formRef" label-width="100px">
        <el-form-item label="环境名称" prop="name">
          <el-input v-model="form.name" placeholder="请输入环境名称" maxlength="100" show-word-limit />
        </el-form-item>
        <el-form-item label="环境配置" prop="config">
          <el-input
            v-model="configText"
            type="textarea"
            :placeholder="placeholderExample"
            :rows="8"
          />
          <div class="hint">配置以 JSON 形式保存，提交时会自动解析。</div>
        </el-form-item>
        <el-form-item label="描述" prop="description">
          <el-input v-model="form.description" type="textarea" :rows="4" placeholder="可选" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitLoading" @click="submitForm">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, watch } from 'vue'
import { ElMessage, ElMessageBox, type FormInstance, type FormRules } from 'element-plus'
import { Search, Plus } from '@element-plus/icons-vue'
import { getEnvironments, createEnvironment, updateEnvironment, deleteEnvironment, type Environment } from '@/api/environments'

const loading = ref(false)
const items = ref<Environment[]>([])
const total = ref(0)
const page = ref(1)
const size = ref(10)
const search = ref('')

const dialogVisible = ref(false)
const dialogTitle = ref('新建环境')
const submitLoading = ref(false)
const formRef = ref<FormInstance>()

const form = reactive<{ id?: number; name: string; config?: Record<string, any> | null; description?: string | null }>({
  name: '',
  config: null,
  description: ''
})

const configText = ref('')

const placeholderExample = 'JSON 格式，如 {\n  "region": "cn",\n  "endpoint": "..."\n}'

const rules: FormRules = {
  name: [{ required: true, message: '请输入环境名称', trigger: 'blur' }]
}

function formatShortJSON(obj?: Record<string, any> | null) {
  if (!obj || Object.keys(obj).length === 0) return '-'
  try {
    const text = JSON.stringify(obj)
    return text.length > 80 ? text.slice(0, 77) + '...' : text
  } catch (e) {
    return '-'
  }
}

function formatDate(iso: string) {
  if (!iso) return '-'
  const d = new Date(iso)
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')} ${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}`
}

async function fetchList() {
  loading.value = true
  try {
    const resp = await getEnvironments({ page: page.value, size: size.value, search: search.value || undefined })
    items.value = resp.items || []
    total.value = resp.total || 0
  } catch (e: any) {
    ElMessage.error(e?.message || '获取环境列表失败')
  } finally {
    loading.value = false
  }
}

function onPageChange(p: number) {
  page.value = p
  fetchList()
}
function onSizeChange(s: number) {
  size.value = s
  fetchList()
}

function resetForm() {
  form.id = undefined
  form.name = ''
  form.config = null
  form.description = ''
  configText.value = ''
}

function openCreate() {
  dialogTitle.value = '新建环境'
  resetForm()
  dialogVisible.value = true
}

function openEdit(row: Environment) {
  dialogTitle.value = '编辑环境'
  form.id = row.id
  form.name = row.name
  form.config = row.config || null
  form.description = row.description || ''
  configText.value = row.config ? JSON.stringify(row.config, null, 2) : ''
  dialogVisible.value = true
}

async function submitForm() {
  if (!formRef.value) return
  await formRef.value.validate(async (valid) => {
    if (!valid) return
    submitLoading.value = true
    try {
      let parsedConfig: Record<string, any> | null = null
      if (configText.value && configText.value.trim().length > 0) {
        try {
          parsedConfig = JSON.parse(configText.value)
        } catch (e) {
          ElMessage.error('环境配置不是合法的 JSON')
          submitLoading.value = false
          return
        }
      }

      const payload = {
        name: form.name,
        config: parsedConfig,
        description: form.description || null
      }

      if (!form.id) {
        await createEnvironment(payload)
        ElMessage.success('创建成功')
      } else {
        await updateEnvironment(form.id, payload)
        ElMessage.success('更新成功')
      }
      dialogVisible.value = false
      fetchList()
    } catch (e: any) {
      ElMessage.error(e?.message || '保存失败')
    } finally {
      submitLoading.value = false
    }
  })
}

async function confirmDelete(row: Environment) {
  try {
    await ElMessageBox.confirm(`确认删除环境【${row.name}】？`, '删除确认', {
      type: 'warning'
    })
    await deleteEnvironment(row.id)
    ElMessage.success('删除成功')
    fetchList()
  } catch (e) {
    // 取消或失败
  }
}

onMounted(() => {
  fetchList()
})
</script>

<style scoped>
.environments-page {
  padding: 12px;
}
.toolbar {
  display: flex;
  align-items: center;
}
.ml-2 { margin-left: 8px; }
.mt-3 { margin-top: 12px; }
.flex-row-end { display: flex; justify-content: flex-end; }
.ellipsis {
  display: inline-block;
  max-width: 100%;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.hint {
  color: var(--el-text-color-secondary);
  font-size: 12px;
  margin-top: 6px;
}
</style>