<template>
  <div class="resource-type-page">
    <div class="page-header">
      <h2>资源类型管理</h2>
      <p class="desc">维护资源类型的基础信息与字段配置</p>
    </div>

    <div class="toolbar">
      <el-input v-model="keyword" placeholder="搜索名称或描述" clearable class="toolbar-input" @keyup.enter="fetchList" />
      <el-button type="primary" @click="openCreateDialog">新建类型</el-button>
    </div>

    <el-card class="list-card">
      <el-table :data="items" v-loading="loading" stripe>
        <el-table-column prop="id" label="ID" min-width="220" />
        <el-table-column prop="name" label="名称" min-width="160" />
        <el-table-column prop="describe" label="描述" min-width="220" />
        <el-table-column label="操作" width="260" fixed="right">
          <template #default="{ row }">
            <el-button size="small" type="primary" link @click="openEditDialog(row)">编辑</el-button>
            <el-divider direction="vertical" />
            <el-button size="small" type="primary" link @click="openFieldsDialog(row)">字段管理</el-button>
            <el-divider direction="vertical" />
            <el-popconfirm title="确认删除该类型？" @confirm="handleDelete(row)">
              <template #reference>
                <el-button size="small" type="danger" link>删除</el-button>
              </template>
            </el-popconfirm>
          </template>
        </el-table-column>
      </el-table>

      <div class="pagination">
        <el-pagination
          background
          layout="prev, pager, next, jumper"
          :total="total"
          :page-size="size"
          :current-page="page"
          @current-change="handlePageChange"
        />
      </div>
    </el-card>

    <!-- 新建/编辑类型 -->
    <el-dialog v-model="typeDialog.visible" :title="typeDialog.isEdit ? '编辑类型' : '新建类型'" width="700px">
      <el-form :model="typeDialog.form" label-width="100px">
        <el-form-item label="名称">
          <el-input v-model="typeDialog.form.name" placeholder="请输入类型名称" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input
            v-model="typeDialog.form.describe"
            type="textarea"
            :autosize="{ minRows: 4, maxRows: 10 }"
            placeholder="请输入描述"
          />
        </el-form-item>
        <!-- 字段管理区块已移除：编辑弹窗仅保留基本信息 -->
      </el-form>
      <template #footer>
        <el-button @click="typeDialog.visible = false">取消</el-button>
        <el-button type="primary" @click="submitType">保存</el-button>
      </template>
    </el-dialog>

    <!-- 字段管理 -->
    <el-drawer v-model="fieldsDialog.visible" title="字段管理" direction="rtl" size="720px">
       <div class="field-editor">
         <div class="field-toolbar">
           <el-button type="primary" size="small" @click="addField(fieldsDialog.form)">新增字段</el-button>
         </div>
         <el-table :data="fieldsDialog.form.metadata || []" size="small" style="width: 100%">
           <el-table-column prop="key" label="key" min-width="140">
             <template #default="{ row }">
               <el-input v-model="row.key" placeholder="字段唯一key" />
             </template>
           </el-table-column>
           <!-- 移除 label 列 -->
           <el-table-column prop="type" label="类型" min-width="160">
             <template #default="{ row }">
               <el-select v-model="row.type" placeholder="类型">
                 <el-option label="string" value="string" />
                 <el-option label="text" value="text" />
                 <el-option label="number" value="number" />
                 <el-option label="integer" value="integer" />
                 <el-option label="float" value="float" />
                 <el-option label="double" value="double" />
                 <el-option label="decimal" value="decimal" />
                 <el-option label="bigint" value="bigint" />
                 <el-option label="boolean" value="boolean" />
                 <el-option label="date" value="date" />
                 <el-option label="time" value="time" />
                 <el-option label="datetime" value="datetime" />
                 <el-option label="uuid" value="uuid" />
                 <el-option label="email" value="email" />
                 <el-option label="url" value="url" />
                 <el-option label="json" value="json" />
                 <el-option label="enum" value="enum" />
                 <el-option label="object" value="object" />
                 <el-option label="array" value="array" />
               </el-select>
             </template>
           </el-table-column>
           <el-table-column prop="required" label="必填" width="80">
             <template #default="{ row }">
               <el-switch v-model="row.required" />
             </template>
           </el-table-column>
           <el-table-column prop="description" label="说明" min-width="180">
             <template #default="{ row }">
               <el-input v-model="row.description" placeholder="用途说明" />
             </template>
           </el-table-column>
           <el-table-column label="操作" width="100">
             <template #default="{ $index }">
               <el-button size="small" type="danger" link @click="removeField(fieldsDialog.form, $index)">删除</el-button>
             </template>
           </el-table-column>
         </el-table>
       </div>
       <template #footer>
         <el-button @click="fieldsDialog.visible = false">取消</el-button>
         <el-button type="primary" @click="saveFields">保存</el-button>
       </template>
    </el-drawer>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { listResourceTypes, createResourceType, updateResourceType, deleteResourceType } from '@/api/resourceType'
import type { ResourceTypeItem, ResourceField } from '@/types/resourceType'

const loading = ref(false)
const items = ref<ResourceTypeItem[]>([])
const page = ref(1)
const size = ref(10)
const total = ref(0)
const keyword = ref('')

const typeDialog = reactive({
  visible: false,
  isEdit: false,
  form: { name: '', describe: '', metadata: [] as ResourceField[] } as Partial<ResourceTypeItem>
})

const fieldsDialog = reactive({
  visible: false,
  form: { id: '', name: '', describe: '', metadata: [] as ResourceField[] } as Partial<ResourceTypeItem>
})

const fetchList = async () => {
  loading.value = true
  try {
    const res = await listResourceTypes({ page: page.value, page_size: size.value, name: keyword.value || undefined })
    if (res.success) {
      const data = res.data
      items.value = (data.items || []) as ResourceTypeItem[]
      total.value = data.total || 0
      page.value = data.page || 1
      size.value = data.page_size || 10
    } else {
      ElMessage.error(res.message || '获取列表失败')
    }
  } catch (e: any) {
    ElMessage.error(e?.message || '请求失败')
  } finally {
    loading.value = false
  }
}

const handlePageChange = (p: number) => {
  page.value = p
  fetchList()
}

const openCreateDialog = () => {
  typeDialog.visible = true
  typeDialog.isEdit = false
  typeDialog.form = { name: '', describe: '', metadata: [] }
}

const openEditDialog = (row: ResourceTypeItem) => {
  typeDialog.visible = true
  typeDialog.isEdit = true
  typeDialog.form = { id: row.id, name: row.name, describe: row.describe, metadata: (row.metadata || []).map(f => ({ ...f })) }
}

const submitType = async () => {
  if (!typeDialog.form.name) {
    ElMessage.warning('请填写名称')
    return
  }
  try {
    if (typeDialog.isEdit && typeDialog.form.id) {
      const res = await updateResourceType(typeDialog.form.id, {
        name: typeDialog.form.name,
        describe: typeDialog.form.describe,
        metadata: typeDialog.form.metadata as ResourceField[]
      })
      if (!res.success) throw new Error(res.message)
      ElMessage.success('更新成功')
    } else {
      const res = await createResourceType({
        name: typeDialog.form.name!,
        describe: typeDialog.form.describe,
        metadata: typeDialog.form.metadata as ResourceField[]
      })
      if (!res.success) throw new Error(res.message)
      ElMessage.success('创建成功')
    }
    typeDialog.visible = false
    fetchList()
  } catch (e: any) {
    ElMessage.error(e?.message || '保存失败')
  }
}

const openFieldsDialog = (row: ResourceTypeItem) => {
  fieldsDialog.visible = true
  fieldsDialog.form = {
    id: row.id,
    name: row.name,
    describe: row.describe,
    metadata: (row.metadata || []).map(f => ({ ...f }))
  }
}

const saveFields = async () => {
  if (!fieldsDialog.form.id) return
  try {
    const res = await updateResourceType(fieldsDialog.form.id, {
      metadata: fieldsDialog.form.metadata as ResourceField[]
    })
    if (!res.success) throw new Error(res.message)
    ElMessage.success('字段保存成功')
    fieldsDialog.visible = false
    fetchList()
  } catch (e: any) {
    ElMessage.error(e?.message || '保存失败')
  }
}

const addField = (form: Partial<ResourceTypeItem>) => {
  if (!form.metadata) form.metadata = []
  form.metadata.push({ key: '', type: 'string', required: false, description: '' })
}

const removeField = (form: Partial<ResourceTypeItem>, index: number) => {
  form.metadata = (form.metadata || []).filter((_, i) => i !== index)
}

onMounted(() => {
  fetchList()
})
</script>

<style scoped>
.resource-type-page {
  padding: 16px;
}
.page-header {
  margin-bottom: 16px;
}
.page-header h2 {
  margin: 0 0 8px;
  font-size: 20px;
}
.page-header .desc {
  margin: 0;
  color: var(--el-text-color-secondary);
}
.toolbar {
  display: flex;
  gap: 12px;
  align-items: center;
  margin-bottom: 12px;
}
.toolbar-input {
  width: 280px;
}
.list-card {
  border-radius: 8px;
}
.pagination {
  display: flex;
  justify-content: flex-end;
  padding: 12px 8px 0;
}
.field-editor {
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.field-toolbar {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 4px;
}
.field-toolbar .hint {
  color: var(--el-text-color-secondary);
}
</style>