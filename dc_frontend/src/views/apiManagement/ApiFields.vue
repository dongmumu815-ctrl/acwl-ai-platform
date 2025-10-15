<template>
  <div class="api-fields">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="header-content">
        <div class="header-left">
          <el-button @click="goBack" size="small">
            <el-icon><ArrowLeft /></el-icon>
            返回
          </el-button>
          <div class="title-section">
            <h1 class="page-title">
              <el-icon><Setting /></el-icon>
              API字段配置
            </h1>
            <p class="page-description" v-if="apiInfo">
              {{ apiInfo.api_name }} ({{ apiInfo.api_code }})
            </p>
          </div>
        </div>
        <div class="header-right">
          <el-button type="primary" @click="showCreateDialog">
            <el-icon><Plus /></el-icon>
            添加字段
          </el-button>
          <el-button @click="loadFields">
            <el-icon><Refresh /></el-icon>
            刷新
          </el-button>
        </div>
      </div>
    </div>

    <!-- API信息卡片 -->
    <div class="page-card" v-if="apiInfo">
      <div class="api-info">
        <el-row :gutter="20">
          <el-col :span="6">
            <div class="info-item">
              <span class="label">API名称:</span>
              <span class="value">{{ apiInfo.api_name }}</span>
            </div>
          </el-col>
          <el-col :span="6">
            <div class="info-item">
              <span class="label">API代码:</span>
              <span class="value">{{ apiInfo.api_code }}</span>
            </div>
          </el-col>
          <el-col :span="6">
            <div class="info-item">
              <span class="label">请求方法:</span>
              <el-tag :type="getMethodTagType(apiInfo.http_method)">
                {{ apiInfo.http_method }}
              </el-tag>
            </div>
          </el-col>
          <el-col :span="6">
            <div class="info-item">
              <span class="label">状态:</span>
              <el-tag :type="apiInfo.is_active ? 'success' : 'danger'">
                {{ apiInfo.is_active ? '激活' : '禁用' }}
              </el-tag>
            </div>
          </el-col>
        </el-row>
      </div>
    </div>

    <!-- 字段列表 -->
    <div class="page-card">
      <div class="card-header">
        <h3>字段列表</h3>
        <div class="header-actions">
          <el-button size="small" @click="saveFieldsOrder" :loading="saving">
            <el-icon><Check /></el-icon>
            保存排序
          </el-button>
        </div>
      </div>

      <el-table
        :data="fields"
        v-loading="loading"
        style="width: 100%"
        row-key="id"
        @sort-change="handleSortChange"
      >
        <el-table-column label="排序" width="60">
          <template #default="{ $index }">
            <span class="drag-handle">{{ $index + 1 }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="field_name" label="字段名称" width="150" sortable />
        <el-table-column prop="field_type" label="字段类型" width="120">
          <template #default="{ row }">
            <el-tag :type="getFieldTypeTagType(row.field_type)">
              {{ getFieldTypeLabel(row.field_type) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="is_required" label="是否必填" width="100">
          <template #default="{ row }">
            <el-tag :type="row.is_required ? 'danger' : 'info'" size="small">
              {{ row.is_required ? '必填' : '可选' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="default_value" label="默认值" width="120" show-overflow-tooltip />
        <el-table-column prop="description" label="描述" min-width="200" show-overflow-tooltip />
        <el-table-column prop="validation_rules" label="验证规则" width="150" show-overflow-tooltip />
        <el-table-column prop="field_order" label="排序" width="80" sortable />
        <el-table-column prop="created_at" label="创建时间" width="150">
          <template #default="{ row }">
            {{ formatDate(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="150" fixed="right">
          <template #default="{ row }">
            <el-button size="small" @click="showEditDialog(row)">
              <el-icon><Edit /></el-icon>
              编辑
            </el-button>
            <el-button size="small" type="danger" @click="deleteField(row)">
              <el-icon><Delete /></el-icon>
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <!-- 创建/编辑字段对话框 -->
    <el-dialog
      v-model="dialogVisible"
      :title="isEdit ? '编辑字段' : '添加字段'"
      width="600px"
      @close="resetForm"
    >
      <el-form
        ref="formRef"
        :model="form"
        :rules="formRules"
        label-width="120px"
      >
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="字段名称" prop="field_name">
              <el-input v-model="form.field_name" placeholder="请输入字段名称" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="字段类型" prop="field_type">
              <el-select v-model="form.field_type" style="width: 100%">
                <el-option label="字符串" value="string" />
                <el-option label="数字" value="number" />
                <el-option label="布尔值" value="boolean" />
                <el-option label="日期" value="date" />
                <el-option label="数组" value="array" />
                <el-option label="对象" value="object" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>
        
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="是否必填" prop="is_required">
              <el-switch
                v-model="form.is_required"
                active-text="必填"
                inactive-text="可选"
              />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="排序" prop="field_order">
              <el-input-number
                v-model="form.field_order"
                :min="1"
                :max="999"
                style="width: 100%"
              />
            </el-form-item>
          </el-col>
        </el-row>
        
        <el-form-item label="默认值" prop="default_value">
          <el-input v-model="form.default_value" placeholder="请输入默认值" />
        </el-form-item>
        
        <el-form-item label="描述" prop="description">
          <el-input
            v-model="form.description"
            type="textarea"
            :rows="3"
            placeholder="请输入字段描述"
          />
        </el-form-item>
        
        <el-form-item label="验证规则" prop="validation_rules">
          <el-input
            v-model="form.validation_rules"
            type="textarea"
            :rows="2"
            placeholder="请输入验证规则（JSON格式）"
          />
        </el-form-item>
      </el-form>

      <template #footer>
        <div class="dialog-footer">
          <el-button @click="dialogVisible = false">取消</el-button>
          <el-button type="primary" @click="submitForm" :loading="submitting">
            {{ isEdit ? '更新' : '创建' }}
          </el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import type { FormInstance, FormRules } from 'element-plus'
import { formatDate } from '@/utils/date'
import {
  getApi,
  getApiFields,
  createApiField,
  updateApiField,
  deleteApiField,
  updateFieldsOrder
} from '@/api/apiManagement'
import type { CustomApi, ApiField, ApiFieldCreate, ApiFieldUpdate } from '@/types/apiManagement'

/**
 * 路由
 */
const route = useRoute()
const router = useRouter()

/**
 * 响应式数据
 */
const loading = ref(false)
const saving = ref(false)
const apiInfo = ref<CustomApi | null>(null)
const fields = ref<ApiField[]>([])
const dialogVisible = ref(false)
const isEdit = ref(false)
const submitting = ref(false)
const formRef = ref<FormInstance>()

// 表单数据
const form = reactive<ApiFieldCreate & { id?: number }>({
  field_name: '',
  field_type: 'string',
  is_required: false,
  default_value: '',
  description: '',
  validation_rules: '',
  field_order: 1
})

// 表单验证规则
const formRules: FormRules = {
  field_name: [
    { required: true, message: '请输入字段名称', trigger: 'blur' },
    { min: 1, max: 50, message: '长度在 1 到 50 个字符', trigger: 'blur' },
    { pattern: /^[a-zA-Z][a-zA-Z0-9_]*$/, message: '必须以字母开头，只能包含字母、数字和下划线', trigger: 'blur' }
  ],
  field_type: [
    { required: true, message: '请选择字段类型', trigger: 'change' }
  ],
  field_order: [
    { required: true, message: '请输入排序', trigger: 'blur' }
  ]
}

/**
 * 生命周期钩子
 */
onMounted(() => {
  const apiId = route.params.id as string
  if (apiId) {
    loadApiInfo(parseInt(apiId))
    loadFields(parseInt(apiId))
  }
})

/**
 * 方法定义
 */

/**
 * 加载API信息
 */
const loadApiInfo = async (apiId: number) => {
  try {
    const response = await getApi(apiId)
    if (response.success) {
      apiInfo.value = response.data
    } else {
      ElMessage.error(response.message || '加载API信息失败')
    }
  } catch (error) {
    console.error('加载API信息失败:', error)
    ElMessage.error('加载API信息失败')
  }
}

/**
 * 加载字段列表
 */
const loadFields = async (apiId?: number) => {
  const id = apiId || parseInt(route.params.id as string)
  
  try {
    loading.value = true
    const response = await getApiFields(id)

    if (response.success) {
      // 处理分页响应结构，获取items数组
      const items = response.data.items || response.data || []
      // 兼容后端返回的sort_order和前端期望的field_order
      fields.value = items.sort((a, b) => {
        const orderA = a.sort_order || a.field_order || 0
        const orderB = b.sort_order || b.field_order || 0
        return orderA - orderB
      })
    } else {
      ElMessage.error(response.message || '加载字段列表失败')
    }
  } catch (error) {
    console.error('加载字段列表失败:', error)
    ElMessage.error('加载字段列表失败')
  } finally {
    loading.value = false
  }
}

/**
 * 获取请求方法标签类型
 */
const getMethodTagType = (method: string) => {
  const types: Record<string, string> = {
    GET: 'success',
    POST: 'primary',
    PUT: 'warning',
    DELETE: 'danger'
  }
  return types[method] || 'info'
}

/**
 * 获取字段类型标签类型
 */
const getFieldTypeTagType = (type: string) => {
  const types: Record<string, string> = {
    string: 'primary',
    number: 'success',
    boolean: 'warning',
    date: 'info',
    array: 'danger',
    object: ''
  }
  return types[type] || 'info'
}

/**
 * 获取字段类型标签
 */
const getFieldTypeLabel = (type: string) => {
  const labels: Record<string, string> = {
    string: '字符串',
    number: '数字',
    boolean: '布尔值',
    date: '日期',
    array: '数组',
    object: '对象'
  }
  return labels[type] || type
}

/**
 * 返回上一页
 */
const goBack = () => {
  router.back()
}

/**
 * 显示创建对话框
 */
const showCreateDialog = () => {
  isEdit.value = false
  dialogVisible.value = true
  resetForm()
  
  // 设置默认排序为最大值+1
  const maxOrder = Math.max(...fields.value.map(f => f.field_order), 0)
  form.field_order = maxOrder + 1
}

/**
 * 显示编辑对话框
 */
const showEditDialog = (field: ApiField) => {
  isEdit.value = true
  dialogVisible.value = true
  
  // 填充表单数据
  Object.assign(form, {
    field_name: field.field_name,
    field_type: field.field_type,
    is_required: field.is_required,
    default_value: field.default_value,
    description: field.description,
    validation_rules: field.validation_rules,
    field_order: field.field_order
  })
  
  form.id = field.id
}

/**
 * 重置表单
 */
const resetForm = () => {
  if (formRef.value) {
    formRef.value.resetFields()
  }
  
  Object.assign(form, {
    field_name: '',
    field_type: 'string',
    is_required: false,
    default_value: '',
    description: '',
    validation_rules: '',
    field_order: 1
  })
  
  delete form.id
}

/**
 * 提交表单
 */
const submitForm = async () => {
  if (!formRef.value) return

  try {
    await formRef.value.validate()
    submitting.value = true

    const apiId = parseInt(route.params.id as string)

    if (isEdit.value && form.id) {
      // 更新字段
      const updateData: ApiFieldUpdate = {
        field_name: form.field_name,
        field_type: form.field_type,
        is_required: form.is_required,
        default_value: form.default_value,
        description: form.description,
        validation_rules: form.validation_rules,
        field_order: form.field_order
      }

      const response = await updateApiField(apiId, form.id, updateData)
      if (response.success) {
        ElMessage.success('字段更新成功')
        dialogVisible.value = false
        // 强制重新加载字段列表
        await loadFields(apiId)
      } else {
        ElMessage.error(response.message || '字段更新失败')
      }
    } else {
      // 创建字段
      const createData: ApiFieldCreate = {
        field_name: form.field_name,
        field_type: form.field_type,
        is_required: form.is_required,
        default_value: form.default_value,
        description: form.description,
        validation_rules: form.validation_rules,
        field_order: form.field_order
      }

      const response = await createApiField(apiId, createData)
      if (response.success) {
        ElMessage.success('字段创建成功')
        dialogVisible.value = false
        // 强制重新加载字段列表
        await loadFields(apiId)
      } else {
        ElMessage.error(response.message || '字段创建失败')
      }
    }
  } catch (error) {
    console.error('提交表单失败:', error)
  } finally {
    submitting.value = false
  }
}

/**
 * 删除字段
 */
const deleteField = async (field: ApiField) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除字段 "${field.field_name}" 吗？此操作不可恢复。`,
      '确认删除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )

    const apiId = parseInt(route.params.id as string)
    const response = await deleteApiField(apiId, field.id)
    
    if (response.success) {
      ElMessage.success('字段删除成功')
      // 强制重新加载字段列表
      const apiId = parseInt(route.params.id as string)
      await loadFields(apiId)
    } else {
      ElMessage.error(response.message || '字段删除失败')
    }
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除字段失败:', error)
      ElMessage.error('字段删除失败')
    }
  }
}

/**
 * 保存字段排序
 */
const saveFieldsOrder = async () => {
  try {
    saving.value = true
    const apiId = parseInt(route.params.id as string)
    
    const fieldsOrder = fields.value.map((field, index) => ({
      id: field.id,
      field_order: index + 1
    }))

    const response = await updateFieldsOrder(apiId, fieldsOrder)
    if (response.success) {
      ElMessage.success('排序保存成功')
      // 强制重新加载字段列表
      await loadFields(apiId)
    } else {
      ElMessage.error(response.message || '排序保存失败')
    }
  } catch (error) {
    console.error('保存排序失败:', error)
    ElMessage.error('排序保存失败')
  } finally {
    saving.value = false
  }
}

/**
 * 排序处理
 */
const handleSortChange = ({ prop, order }: { prop: string; order: string }) => {
  console.log('排序:', prop, order)
}
</script>

<style scoped lang="scss">
.api-fields {
  .page-header {
    margin-bottom: 20px;
    
    .header-content {
      display: flex;
      justify-content: space-between;
      align-items: center;
      
      .header-left {
        display: flex;
        align-items: center;
        gap: 16px;
        
        .title-section {
          .page-title {
            display: flex;
            align-items: center;
            gap: 8px;
            margin: 0 0 4px 0;
            font-size: 24px;
            font-weight: 600;
            color: var(--el-text-color-primary);
          }
          
          .page-description {
            margin: 0;
            color: var(--el-text-color-regular);
            font-size: 14px;
          }
        }
      }
      
      .header-right {
        display: flex;
        gap: 12px;
      }
    }
  }
  
  .api-info {
    padding: 20px;
    
    .info-item {
      display: flex;
      align-items: center;
      gap: 8px;
      margin-bottom: 12px;
      
      .label {
        font-weight: 500;
        color: var(--el-text-color-regular);
        min-width: 80px;
      }
      
      .value {
        color: var(--el-text-color-primary);
      }
    }
  }
  
  .card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 20px 20px 0 20px;
    
    h3 {
      margin: 0;
      font-size: 16px;
      font-weight: 600;
    }
    
    .header-actions {
      display: flex;
      gap: 8px;
    }
  }
  
  .drag-handle {
    cursor: move;
    color: var(--el-text-color-regular);
  }
}
</style>