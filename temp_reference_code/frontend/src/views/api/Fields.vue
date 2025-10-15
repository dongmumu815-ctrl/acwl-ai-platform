<template>
  <div>
    <div class="page-card">
      <div class="page-header">
        <h2>API字段管理 - {{ apiInfo?.api_name }}</h2>
        <div>
          <el-button @click="loadFields">刷新</el-button>
          <el-button type="primary" @click="showCreateDialog">
            <el-icon><Plus /></el-icon>
            添加字段
          </el-button>
        </div>
      </div>
      
      <div class="page-content">
        <!-- API基本信息 -->
        <el-card class="api-info-card" v-if="apiInfo">
          <template #header>
            <span>API信息</span>
          </template>
          <el-descriptions :column="3" border>
            <el-descriptions-item label="API名称">{{ apiInfo.api_name }}</el-descriptions-item>
            <el-descriptions-item label="API代码">{{ apiInfo.api_code }}</el-descriptions-item>
            <el-descriptions-item label="请求方法">
              <el-tag :type="getMethodTagType(apiInfo.http_method)">{{ apiInfo.http_method }}</el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="状态">
              <el-tag :type="apiInfo.status ? 'success' : 'danger'">
                {{ apiInfo.status ? '启用' : '禁用' }}
              </el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="创建时间" :span="2">
              {{ formatDate(apiInfo.created_at) }}
            </el-descriptions-item>
          </el-descriptions>
        </el-card>

        <!-- 字段列表 -->
        <el-table
          :data="fields"
          style="width: 100%; margin-top: 20px;"
          v-loading="loading"
          row-key="id"
        >
          <el-table-column prop="sort_order" label="排序" width="80" />
          <el-table-column prop="field_name" label="字段名" width="150" />
          <el-table-column prop="field_label" label="字段标签" width="150" />
          <el-table-column prop="field_type" label="字段类型" width="120">
            <template #default="{ row }">
              <el-tag :type="getFieldTypeTagType(row.field_type)">{{ getFieldTypeLabel(row.field_type) }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="is_required" label="必填" width="80">
            <template #default="{ row }">
              <el-tag :type="row.is_required ? 'danger' : 'info'">{{ row.is_required ? '是' : '否' }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="default_value" label="默认值" width="120" show-overflow-tooltip />
          <el-table-column prop="description" label="描述" show-overflow-tooltip />
          <el-table-column label="验证规则" width="200">
            <template #default="{ row }">
              <div class="validation-rules">
                <span v-if="row.max_length" class="rule-item">最大长度: {{ row.max_length }}</span>
                <span v-if="row.min_length" class="rule-item">最小长度: {{ row.min_length }}</span>
                <span v-if="row.max_value" class="rule-item">最大值: {{ row.max_value }}</span>
                <span v-if="row.min_value" class="rule-item">最小值: {{ row.min_value }}</span>
                <span v-if="row.validation_regex" class="rule-item">正则: {{ row.validation_regex }}</span>
              </div>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="200" fixed="right">
            <template #default="{ row }">
              <el-button size="small" @click="showEditDialog(row)">编辑</el-button>
              <el-button size="small" type="danger" @click="deleteField(row)">删除</el-button>
            </template>
          </el-table-column>
        </el-table>
      </div>
    </div>

    <!-- 字段创建/编辑对话框 -->
    <el-dialog
      v-model="formDialogVisible"
      :title="isEditing ? '编辑字段' : '创建字段'"
      width="800px"
      @close="resetForm"
    >
      <el-form :model="fieldForm" :rules="fieldFormRules" ref="fieldFormRef" label-width="120px">
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="字段名" prop="field_name">
              <el-input v-model="fieldForm.field_name" placeholder="请输入字段名，如：username" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="字段标签" prop="field_label">
              <el-input v-model="fieldForm.field_label" placeholder="请输入字段标签，如：用户名" />
            </el-form-item>
          </el-col>
        </el-row>
        
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="字段类型" prop="field_type">
              <el-select v-model="fieldForm.field_type" placeholder="请选择字段类型" style="width: 100%">
                <el-option label="字符串" value="string" />
                <el-option label="整数" value="int" />
                <el-option label="浮点数" value="float" />
                <el-option label="布尔值" value="boolean" />
                <el-option label="日期" value="date" />
                <el-option label="日期时间" value="datetime" />
                <el-option label="JSON" value="json" />
                <el-option label="文件" value="file" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="是否必填">
              <el-switch v-model="fieldForm.is_required" />
            </el-form-item>
          </el-col>
        </el-row>
        
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="默认值">
              <el-input v-model="fieldForm.default_value" placeholder="请输入默认值" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="排序顺序">
              <el-input-number v-model="fieldForm.sort_order" :min="0" style="width: 100%" />
            </el-form-item>
          </el-col>
        </el-row>
        
        <el-form-item label="描述">
          <el-input v-model="fieldForm.description" type="textarea" :rows="3" placeholder="请输入字段描述" />
        </el-form-item>
        
        <!-- 验证规则 -->
        <el-divider content-position="left">验证规则</el-divider>
        
        <el-row :gutter="20" v-if="['string'].includes(fieldForm.field_type)">
          <el-col :span="12">
            <el-form-item label="最小长度">
              <el-input-number v-model="fieldForm.min_length" :min="0" style="width: 100%" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="最大长度">
              <el-input-number v-model="fieldForm.max_length" :min="1" style="width: 100%" />
            </el-form-item>
          </el-col>
        </el-row>
        
        <el-row :gutter="20" v-if="['int', 'float'].includes(fieldForm.field_type)">
          <el-col :span="12">
            <el-form-item label="最小值">
              <el-input-number v-model="fieldForm.min_value" style="width: 100%" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="最大值">
              <el-input-number v-model="fieldForm.max_value" style="width: 100%" />
            </el-form-item>
          </el-col>
        </el-row>
        
        <el-form-item label="允许的值" v-if="['string'].includes(fieldForm.field_type)">
          <el-input v-model="allowedValuesText" type="textarea" :rows="2" 
                   placeholder="请输入允许的值，每行一个，如：\n选项1\n选项2\n选项3" />
        </el-form-item>
        
        <el-form-item label="验证正则">
          <el-input v-model="fieldForm.validation_regex" placeholder="请输入验证正则表达式" />
        </el-form-item>
        
        <el-form-item label="验证失败提示">
          <el-input v-model="fieldForm.validation_message" placeholder="请输入验证失败时的提示信息" />
        </el-form-item>
      </el-form>
      
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="formDialogVisible = false">取消</el-button>
          <el-button type="primary" @click="submitForm" :loading="submitting">
            {{ isEditing ? '更新' : '创建' }}
          </el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import api from '@/utils/api'

const route = useRoute()
const router = useRouter()

// 响应式数据
const loading = ref(false)
const submitting = ref(false)
const formDialogVisible = ref(false)
const isEditing = ref(false)
const apiInfo = ref(null)
const fields = ref([])
const currentField = ref(null)

// 表单数据
const fieldForm = reactive({
  field_name: '',
  field_label: '',
  field_type: 'string',
  is_required: false,
  default_value: '',
  description: '',
  sort_order: 0,
  max_length: null,
  min_length: null,
  max_value: null,
  min_value: null,
  allowed_values: [],
  validation_regex: '',
  validation_message: ''
})

// 允许的值文本（用于界面显示）
const allowedValuesText = ref('')

// 监听允许的值文本变化
watch(allowedValuesText, (newVal) => {
  if (newVal) {
    fieldForm.allowed_values = newVal.split('\n').filter(v => v.trim())
  } else {
    fieldForm.allowed_values = []
  }
})

// 表单验证规则
const fieldFormRules = {
  field_name: [
    { required: true, message: '请输入字段名', trigger: 'blur' },
    { pattern: /^[a-zA-Z][a-zA-Z0-9_]*$/, message: '字段名只能包含字母、数字和下划线，且以字母开头', trigger: 'blur' }
  ],
  field_label: [
    { required: true, message: '请输入字段标签', trigger: 'blur' }
  ],
  field_type: [
    { required: true, message: '请选择字段类型', trigger: 'change' }
  ]
}

const fieldFormRef = ref()

// 获取API ID
const apiId = computed(() => route.params.id)

// 加载API信息
const loadApiInfo = async () => {
  try {
    const response = await api.get(`/admin/apis/${apiId.value}`)
    apiInfo.value = response.data.data
  } catch (error) {
    console.error('加载API信息失败:', error)
    ElMessage.error('加载API信息失败')
  }
}

// 加载字段列表
const loadFields = async () => {
  loading.value = true
  try {
    const response = await api.get(`/admin/apis/${apiId.value}/fields`)
    fields.value = response.data.data || []
  } catch (error) {
    console.error('加载字段列表失败:', error)
    ElMessage.error('加载字段列表失败')
  } finally {
    loading.value = false
  }
}

// 显示创建对话框
const showCreateDialog = () => {
  isEditing.value = false
  resetForm()
  formDialogVisible.value = true
}

// 显示编辑对话框
const showEditDialog = (field) => {
  isEditing.value = true
  currentField.value = field
  
  // 填充表单数据
  Object.keys(fieldForm).forEach(key => {
    if (field[key] !== undefined) {
      fieldForm[key] = field[key]
    }
  })
  
  // 处理允许的值
  if (field.allowed_values && Array.isArray(field.allowed_values)) {
    allowedValuesText.value = field.allowed_values.join('\n')
  }
  
  formDialogVisible.value = true
}

// 重置表单
const resetForm = () => {
  Object.keys(fieldForm).forEach(key => {
    if (key === 'field_type') {
      fieldForm[key] = 'string'
    } else if (key === 'is_required') {
      fieldForm[key] = false
    } else if (key === 'sort_order') {
      fieldForm[key] = 0
    } else if (key === 'allowed_values') {
      fieldForm[key] = []
    } else {
      fieldForm[key] = ''
    }
  })
  allowedValuesText.value = ''
  currentField.value = null
  
  if (fieldFormRef.value) {
    fieldFormRef.value.clearValidate()
  }
}

// 提交表单
const submitForm = async () => {
  if (!fieldFormRef.value) return
  
  try {
    await fieldFormRef.value.validate()
  } catch (error) {
    return
  }
  
  submitting.value = true
  
  try {
    const formData = { ...fieldForm }
    
    // 清理空值
    Object.keys(formData).forEach(key => {
      if (formData[key] === '' || formData[key] === null) {
        delete formData[key]
      }
    })
    
    if (isEditing.value) {
      await api.put(`/admin/apis/${apiId.value}/fields/${currentField.value.id}`, formData)
      ElMessage.success('字段更新成功')
    } else {
      await api.post(`/admin/apis/${apiId.value}/fields`, formData)
      ElMessage.success('字段创建成功')
    }
    
    formDialogVisible.value = false
    loadFields()
  } catch (error) {
    console.error('提交失败:', error)
    ElMessage.error(error.response?.data?.detail || '操作失败')
  } finally {
    submitting.value = false
  }
}

// 删除字段
const deleteField = async (field) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除字段 "${field.field_label}" 吗？此操作不可恢复。`,
      '确认删除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    await api.delete(`/admin/apis/${apiId.value}/fields/${field.id}`)
    ElMessage.success('字段删除成功')
    loadFields()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除字段失败:', error)
      ElMessage.error('删除字段失败')
    }
  }
}

// 获取请求方法标签类型
const getMethodTagType = (method) => {
  const types = {
    'GET': 'success',
    'POST': 'primary',
    'PUT': 'warning',
    'DELETE': 'danger',
    'PATCH': 'info'
  }
  return types[method] || 'info'
}

// 获取字段类型标签类型
const getFieldTypeTagType = (type) => {
  const types = {
    'string': 'primary',
    'int': 'success',
    'float': 'success',
    'boolean': 'warning',
    'date': 'info',
    'datetime': 'info',
    'json': 'danger',
    'file': 'warning'
  }
  return types[type] || 'info'
}

// 获取字段类型标签
const getFieldTypeLabel = (type) => {
  const labels = {
    'string': '字符串',
    'int': '整数',
    'float': '浮点数',
    'boolean': '布尔值',
    'date': '日期',
    'datetime': '日期时间',
    'json': 'JSON',
    'file': '文件'
  }
  return labels[type] || type
}

// 格式化日期
const formatDate = (dateString) => {
  if (!dateString) return ''
  return new Date(dateString).toLocaleString('zh-CN')
}

// 组件挂载时加载数据
onMounted(() => {
  if (!apiId.value) {
    ElMessage.error('API ID 不存在')
    router.push('/apis')
    return
  }
  
  loadApiInfo()
  loadFields()
})
</script>

<style scoped>
.page-card {
  background: #fff;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.page-header {
  padding: 20px;
  border-bottom: 1px solid #f0f0f0;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.page-header h2 {
  margin: 0;
  color: #333;
}

.page-content {
  padding: 20px;
}

.api-info-card {
  margin-bottom: 20px;
}

.validation-rules {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.rule-item {
  font-size: 12px;
  color: #666;
  background: #f5f5f5;
  padding: 2px 6px;
  border-radius: 3px;
  display: inline-block;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}
</style>