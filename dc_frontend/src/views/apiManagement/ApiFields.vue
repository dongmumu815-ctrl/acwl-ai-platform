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
          <el-button @click="openCenterDrawer">
            从资源类型添加
          </el-button>
          <el-button @click="loadFields()">
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
        <el-row :gutter="20" style="margin-top: 8px;">
          <el-col :span="6">
            <div class="info-item">
              <span class="label">资源类型:</span>
              <span class="value">
                <template v-if="resourceTypeName">
                  {{ resourceTypeName }}
                </template>
                <template v-else>
                  未配置
                </template>
              </span>
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
        <el-table-column prop="sort_order" label="排序" width="80" sortable />
        <el-table-column prop="created_at" label="创建时间" width="150">
          <template #default="{ row }">
            {{ formatDate(row.created_at) }}
          </template>
        </el-table-column>
        <!-- 是否上传勾选 -->
        <el-table-column prop="is_upload" label="是否上传" width="120" fixed="right">
          <template #default="{ row }">
            <el-checkbox
              v-model="row.is_upload"
              :true-value="1"
              :false-value="0"
              @change="onUploadChange(row, $event)"
            >上传</el-checkbox>
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
            <el-form-item label="排序" prop="sort_order">
              <el-input-number
                v-model="form.sort_order"
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

    <!-- 资源类型字段选择抽屉 -->
    <el-drawer
      v-model="centerDrawerVisible"
      title="从资源类型选择字段"
      direction="rtl"
      size="800px"
    >
      <div class="panel-header">
        <h4>资源类型字段</h4>
        <el-button @click="loadResourceTypeFields" :loading="centerFieldsLoading" size="small">
          <el-icon><Refresh /></el-icon>
          刷新字段
        </el-button>
      </div>
      <div class="center-fields-list">
        <el-table
          :data="centerTableFields"
          @selection-change="handleCenterFieldSelection"
          v-loading="centerFieldsLoading"
          size="small"
        >
          <el-table-column type="selection" width="55" :selectable="selectableCenterField" />
          <el-table-column prop="column_name" label="字段名" width="150" />
          <el-table-column prop="data_type" label="数据类型" width="120" />
          <el-table-column prop="column_comment" label="字段说明" show-overflow-tooltip>
            <template #default="{ row }">
              {{ row.column_comment || '-' }}
            </template>
          </el-table-column>
          <el-table-column label="状态" width="100">
            <template #default="{ row }">
              <el-tag :type="isExistingCenterField(row) ? 'info' : 'success'" size="small">
                {{ isExistingCenterField(row) ? '已存在' : '可添加' }}
              </el-tag>
            </template>
          </el-table-column>
        </el-table>
      </div>
      <template #footer>
        <el-button @click="centerDrawerVisible = false">取消</el-button>
        <el-button type="primary" @click="addSelectedFields" :disabled="selectedCenterFields.length === 0" :loading="addingFromCenter">
          添加选中字段 ({{ selectedCenterFields.length }})
        </el-button>
      </template>
    </el-drawer>
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
  deleteApiField
} from '@/api/apiManagement'
import type { CustomApi, ApiField, ApiFieldCreate, ApiFieldUpdate } from '@/types/apiManagement'
import { getResourceType } from '@/api/resourceType'

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
const resourceTypeName = ref('')
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
  sort_order: 1
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
  sort_order: [
    { required: true, message: '请输入排序', trigger: 'blur' }
  ]
}

// 新增：中心表字段选择相关
interface CenterTableField {
  column_name: string
  data_type: string
  column_comment: string
  is_nullable: boolean
}

const centerDrawerVisible = ref(false)
const centerTableFields = ref<CenterTableField[]>([])
const selectedCenterFields = ref<CenterTableField[]>([])
const centerFieldsLoading = ref(false)
const addingFromCenter = ref(false)

// 资源类型字段选择依赖于当前 API 的 resource_type_id

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
      // 加载资源类型名称
      try {
        const rid = apiInfo.value?.resource_type_id
        if (rid) {
          const rtResp = await getResourceType(String(rid))
          if (rtResp?.success && rtResp.data) {
            resourceTypeName.value = rtResp.data.name || ''
          } else {
            resourceTypeName.value = ''
          }
        } else {
          resourceTypeName.value = ''
        }
      } catch (e) {
        resourceTypeName.value = ''
      }
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
  const id = typeof apiId === 'number' ? apiId : parseInt(route.params.id as string)
  
  try {
    loading.value = true
    const response = await getApiFields(id)

    if (response.success) {
      // 处理分页响应结构，获取items数组
      const items = response.data.items || response.data || []
      // 归一化 is_upload 类型，确保为数字 0/1，避免 '1'/'0' 导致复选框不勾选
      const normalized = items.map((item: any) => ({
        ...item,
        is_upload:
          item?.is_upload === undefined || item?.is_upload === null
            ? 0
            : typeof item.is_upload === 'string'
              ? Number(item.is_upload)
              : item.is_upload
      }))
      // 根据后端返回的 sort_order 排序
      fields.value = normalized.sort((a, b) => {
        const orderA = a.sort_order || 0
        const orderB = b.sort_order || 0
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
  const maxOrder = Math.max(...fields.value.map(f => f.sort_order || 0), 0)
  form.sort_order = maxOrder + 1
}

// 打开资源类型字段选择抽屉
const openCenterDrawer = () => {
  if (!apiInfo.value?.resource_type_id) {
    ElMessage.warning('请先在 API 基础信息中选择资源类型')
    return
  }
  centerDrawerVisible.value = true
  if (centerTableFields.value.length === 0) {
    loadResourceTypeFields()
  }
}

// 加载资源类型字段（基于当前API的 resource_type_id）
const loadResourceTypeFields = async () => {
  try {
    centerFieldsLoading.value = true
    const rtid = apiInfo.value?.resource_type_id
    if (!rtid) {
      ElMessage.warning('当前 API 未配置资源类型，无法加载字段')
      return
    }
    const response = await getResourceType(String(rtid))
    if (response?.success && response.data) {
      const meta = (response.data.metadata || []) as any[]
      centerTableFields.value = meta.map((m: any) => ({
        column_name: m.key,
        data_type: m.type || 'string',
        column_comment: m.description || '',
        is_nullable: !(m.required === true)
      }))
    } else {
      centerTableFields.value = []
      ElMessage.warning(response?.message || '资源类型未包含字段元数据')
    }
  } catch (e: any) {
    console.error('加载资源类型字段失败:', e)
    ElMessage.error(e?.message || '加载资源类型字段失败')
  } finally {
    centerFieldsLoading.value = false
  }
}

// 新增：处理中心表字段选择
const handleCenterFieldSelection = (selection: CenterTableField[]) => {
  selectedCenterFields.value = selection
}

// 新增：中心表字段是否可选择（已存在则禁选）
const selectableCenterField = (row: CenterTableField) => {
  return !fields.value.some(f => f.field_name === row.column_name)
}

// 新增：判断中心表字段在当前API中是否已存在
const isExistingCenterField = (row: CenterTableField) => {
  return fields.value.some(f => f.field_name === row.column_name)
}
// 将资源类型字段的类型映射为 API 字段类型
const mapDataTypeToApiFieldType = (dataType: string): ApiFieldCreate['field_type'] => {
  const t = (dataType || '').toLowerCase()
  if (t === 'integer' || t === 'number' || t.includes('int') || t.includes('decimal') || t.includes('float') || t.includes('double') || t.includes('numeric')) {
    return 'number'
  }
  if (t === 'boolean' || t.includes('bool')) {
    return 'boolean'
  }
  if (t === 'date' || t.includes('date') || t.includes('time')) {
    return 'date'
  }
  if (t === 'array') {
    return 'array'
  }
  if (t === 'object') {
    return 'object'
  }
  return 'string'
}

// 新增：批量添加选中中心表字段到当前API
const addSelectedFields = async () => {
  if (selectedCenterFields.value.length === 0) {
    ElMessage.warning('请先选择要添加的字段')
    return
  }
  const existingNames = new Set(fields.value.map(f => f.field_name))
  const unique = selectedCenterFields.value.filter(f => !existingNames.has(f.column_name))
  if (unique.length === 0) {
    ElMessage.warning('所选字段已存在，无需重复添加')
    return
  }

  const apiId = parseInt(route.params.id as string)
  let order = Math.max(...fields.value.map(f => f.sort_order || 0), 0)

  try {
    addingFromCenter.value = true
    for (const f of unique) {
      const createData: ApiFieldCreate = {
        field_name: f.column_name,
        field_type: mapDataTypeToApiFieldType(f.data_type),
        is_required: !f.is_nullable,
        description: f.column_comment || '',
        sort_order: ++order
      }
      const resp = await createApiField(apiId, createData)
      if (!resp.success) {
        ElMessage.error(resp.message || `添加字段失败：${f.column_name}`)
      }
    }
    ElMessage.success(`成功添加 ${unique.length} 个字段`)
    centerDrawerVisible.value = false
    await loadFields(apiId)
  } catch (e) {
    console.error('批量添加字段失败:', e)
    ElMessage.error('批量添加字段失败')
  } finally {
    addingFromCenter.value = false
    selectedCenterFields.value = []
  }
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
    sort_order: field.sort_order
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
    sort_order: 1
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
        sort_order: form.sort_order
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
        sort_order: form.sort_order
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
    
    // 逐字段更新排序到后端
    const updates = fields.value.map((field, index) =>
      updateApiField(apiId, field.id, { sort_order: index + 1 })
    )

    const results = await Promise.all(updates)
    const failed = results.filter(r => !r.success)
    if (failed.length === 0) {
      ElMessage.success('排序保存成功')
      await loadFields(apiId)
    } else {
      ElMessage.error(`部分字段排序保存失败：${failed.length} 项`)
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

/**
 * 勾选是否上传状态并同步更新到后端
 */
const onUploadChange = async (field: ApiField, value: number | boolean) => {
  const apiId = parseInt(route.params.id as string)
  const newVal = typeof value === 'boolean' ? (value ? 1 : 0) : value
  const prev = field.is_upload ?? 0
  try {
    const resp = await updateApiField(apiId, field.id, { is_upload: newVal })
    if (resp.success) {
      ElMessage.success('上传状态已更新')
      field.is_upload = newVal
    } else {
      // 回滚界面状态
      field.is_upload = prev
      ElMessage.error(resp.message || '更新上传状态失败')
    }
  } catch (e) {
    field.is_upload = prev
    console.error('更新上传状态失败:', e)
    ElMessage.error('更新上传状态失败')
  }
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

// 新增：中心表字段抽屉样式
.panel-header {
  padding: 16px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-bottom: 1px solid var(--el-border-color-light);
}
.center-fields-list {
  padding: 16px;
}
</style>