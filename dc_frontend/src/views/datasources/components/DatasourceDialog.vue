<template>
  <el-dialog
    v-model="visible"
    :title="dialogTitle"
    width="800px"
    :close-on-click-modal="false"
    @close="handleClose"
  >
    <el-form
      ref="formRef"
      :model="form"
      :rules="rules"
      label-width="120px"
      @submit.prevent
    >
      <el-row :gutter="20">
        <el-col :span="12">
          <el-form-item label="数据源名称" prop="name">
            <el-input
              v-model="form.name"
              placeholder="请输入数据源名称"
              maxlength="100"
              show-word-limit
            />
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="数据源类型" prop="datasource_type">
            <el-select
              v-model="form.datasource_type"
              placeholder="选择数据源类型"
              style="width: 100%"
              @change="handleTypeChange"
            >
              <el-option
                v-for="template in templates"
                :key="template.datasource_type"
                :label="getDatasourceTypeLabel(template.datasource_type)"
                :value="template.datasource_type"
              >
                <div class="template-option">
                  <span>{{ getDatasourceTypeLabel(template.datasource_type) }}</span>
                  <span class="template-desc">{{ template.description }}</span>
                </div>
              </el-option>
            </el-select>
          </el-form-item>
        </el-col>
      </el-row>

      <el-form-item label="描述">
        <el-input
          v-model="form.description"
          type="textarea"
          :rows="2"
          placeholder="请输入数据源描述"
          maxlength="500"
          show-word-limit
        />
      </el-form-item>

      <el-divider content-position="left">连接配置</el-divider>

      <el-row :gutter="20">
        <el-col :span="14">
          <el-form-item label="主机地址" prop="host">
            <el-input
              v-model="form.host"
              placeholder="请输入主机地址或IP"
            />
          </el-form-item>
        </el-col>
        <el-col :span="10">
          <el-form-item label="端口" prop="port">
            <el-input-number
              v-model="form.port"
              :min="1"
              :max="65535"
              style="width: 100%"
              placeholder="端口号"
            />
          </el-form-item>
        </el-col>
      </el-row>

      <el-row :gutter="20">
        <el-col :span="12">
          <el-form-item label="数据库名称">
            <el-input
              v-model="form.database"
              placeholder="请输入数据库名称"
            />
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="用户名">
            <el-input
              v-model="form.username"
              placeholder="请输入用户名"
            />
          </el-form-item>
        </el-col>
      </el-row>

      <el-form-item label="密码">
        <el-input
          v-model="form.password"
          type="password"
          placeholder="请输入密码"
          show-password
        />
      </el-form-item>

      <el-divider content-position="left">高级配置</el-divider>

      <!-- 连接参数 -->
      <el-form-item label="连接参数">
        <div class="params-container">
          <div
            v-for="(param, index) in connectionParams"
            :key="index"
            class="param-item"
          >
            <el-input
              v-model="param.key"
              placeholder="参数名"
              style="width: 200px; margin-right: 10px"
            />
            <el-input
              v-model="param.value"
              placeholder="参数值"
              style="width: 200px; margin-right: 10px"
            />
            <el-button
              type="danger"
              size="small"
              @click="removeParam(index)"
              :icon="Delete"
            />
          </div>
          <el-button
            type="primary"
            size="small"
            @click="addParam"
            :icon="Plus"
          >
            添加参数
          </el-button>
        </div>
      </el-form-item>

      <!-- 连接池配置 -->
      <el-form-item label="连接池配置">
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="池大小">
              <el-input-number
                v-model="form.pool_config.pool_size"
                :min="1"
                :max="100"
                style="width: 100%"
              />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="最大溢出">
              <el-input-number
                v-model="form.pool_config.max_overflow"
                :min="0"
                :max="100"
                style="width: 100%"
              />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="超时时间">
              <el-input-number
                v-model="form.pool_config.pool_timeout"
                :min="1"
                :max="300"
                style="width: 100%"
              />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="回收时间">
              <el-input-number
                v-model="form.pool_config.pool_recycle"
                :min="60"
                :max="86400"
                style="width: 100%"
              />
            </el-form-item>
          </el-col>
        </el-row>
      </el-form-item>

      <el-form-item label="启用状态">
        <el-switch
          v-model="form.is_enabled"
          active-text="启用"
          inactive-text="停用"
        />
      </el-form-item>
    </el-form>

    <template #footer>
      <div class="dialog-footer">
        <el-button @click="handleClose">取消</el-button>
        <el-button
          type="info"
          @click="handleTest"
          :loading="testing"
          :disabled="!canTest"
        >
          测试连接
        </el-button>
        <el-button
          type="primary"
          @click="handleSubmit"
          :loading="submitting"
        >
          {{ mode === 'create' ? '创建' : '更新' }}
        </el-button>
      </div>
    </template>

    <!-- 测试结果对话框 -->
    <TestResultDialog
      v-model="testDialogVisible"
      :test-result="testResult"
    />
  </el-dialog>
</template>

<script setup>
import { ref, reactive, computed, watch, nextTick } from 'vue'
import { ElMessage } from 'element-plus'
import { Plus, Delete } from '@element-plus/icons-vue'
import TestResultDialog from './TestResultDialog.vue'
import {
  getDatasourceTemplates,
  createDatasource,
  updateDatasource,
  testTempDatasourceConnection,
  testDatasourceConnection,
  DatasourceType,
  getDatasourceTypeLabel as getTypeLabel,
  DATASOURCE_TYPES,
  getDefaultPort
} from '@/api/datasourceV2'

// Props
const props = defineProps({
  modelValue: {
    type: Boolean,
    default: false
  },
  datasource: {
    type: Object,
    default: null
  },
  mode: {
    type: String,
    default: 'create' // create | edit
  }
})

// Emits
const emit = defineEmits(['update:modelValue', 'success'])

// 响应式数据
const formRef = ref()
const visible = ref(false)
const submitting = ref(false)
const testing = ref(false)
const testDialogVisible = ref(false)
const testResult = ref(null)
const templates = ref([])
const connectionParams = ref([])

// 表单数据
const form = reactive({
  name: '',
  description: '',
  datasource_type: '',
  host: '',
  port: 3306,
  database: '',
  username: '',
  password: '',
  connection_params: {},
  pool_config: {
    pool_size: 5,
    max_overflow: 10,
    pool_timeout: 30,
    pool_recycle: 3600
  },
  is_enabled: true
})

// 表单验证规则
const rules = {
  name: [
    { required: true, message: '请输入数据源名称', trigger: 'blur' },
    { min: 1, max: 100, message: '长度在 1 到 100 个字符', trigger: 'blur' }
  ],
  datasource_type: [
    { required: true, message: '请选择数据源类型', trigger: 'change' }
  ],
  host: [
    { required: true, message: '请输入主机地址', trigger: 'blur' }
  ],
  port: [
    { required: true, message: '请输入端口号', trigger: 'blur' },
    { type: 'number', min: 1, max: 65535, message: '端口号范围 1-65535', trigger: 'blur' }
  ]
}

// 计算属性
const dialogTitle = computed(() => {
  return props.mode === 'create' ? '新建数据源' : '编辑数据源'
})

const canTest = computed(() => {
  return form.host && form.port && form.datasource_type
})

// 监听器
watch(() => props.modelValue, (val) => {
  visible.value = val
  if (val) {
    loadTemplates()
    initForm()
  }
})

watch(visible, (val) => {
  emit('update:modelValue', val)
})

// 方法
/**
 * 加载数据源模板
 * 优先从后端API获取，如果失败则使用前端定义的数据源类型
 */
const loadTemplates = async () => {
  try {
    const response = await getDatasourceTemplates()
    templates.value = response
  } catch (error) {
    console.error('Load templates error:', error)
    // 如果API调用失败，使用前端定义的数据源类型作为备选
    templates.value = DATASOURCE_TYPES.map(type => ({
      datasource_type: type.value,
      description: `${type.label} 数据库连接`,
      default_port: getDefaultPort(type.value),
      default_params: {}
    }))
  }
}

const initForm = () => {
  if (props.mode === 'edit' && props.datasource) {
    // 编辑模式，填充表单
    Object.assign(form, {
      ...props.datasource,
      database: props.datasource.database_name,
      password: '' // 密码不回显
    })
    
    // 初始化连接参数
    connectionParams.value = Object.entries(props.datasource.connection_params || {}).map(
      ([key, value]) => ({ key, value })
    )
  } else {
    // 创建模式，重置表单
    Object.assign(form, {
      name: '',
      description: '',
      datasource_type: '',
      host: '',
      port: 3306,
      database: '',
      username: '',
      password: '',
      connection_params: {},
      pool_config: {
        pool_size: 5,
        max_overflow: 10,
        pool_timeout: 30,
        pool_recycle: 3600
      },
      is_enabled: true
    })
    connectionParams.value = []
  }
  
  // 清除验证
  nextTick(() => {
    formRef.value?.clearValidate()
  })
}

const handleTypeChange = (type) => {
  // 根据数据源类型设置默认端口
  const template = templates.value.find(t => t.datasource_type === type)
  if (template && template.default_port) {
    form.port = template.default_port
  }
  
  // 设置默认连接参数
  if (template && template.default_params) {
    connectionParams.value = Object.entries(template.default_params).map(
      ([key, value]) => ({ key, value })
    )
  }
}

const addParam = () => {
  connectionParams.value.push({ key: '', value: '' })
}

const removeParam = (index) => {
  connectionParams.value.splice(index, 1)
}

const buildConnectionParams = () => {
  const params = {}
  connectionParams.value.forEach(param => {
    if (param.key && param.value) {
      params[param.key] = param.value
    }
  })
  return params
}

const handleTest = async () => {
  try {
    // 先验证必填字段
    await formRef.value.validateField(['host', 'port', 'datasource_type'])
    
    testing.value = true
    
    // 构建测试数据
    const testData = {
      ...form,
      connection_params: buildConnectionParams()
    }
    
    // 如果是编辑模式，使用现有数据源ID测试
    if (props.mode === 'edit' && props.datasource) {
      const response = await testDatasourceConnection(props.datasource.id, {
        timeout: 10
      })
      testResult.value = response
    } else {
      // 创建模式，使用临时测试API
      const response = await testTempDatasourceConnection({
        name: form.name,
        datasource_type: form.datasource_type,
        host: form.host,
        port: form.port,
        database: form.database,
        username: form.username,
        password: form.password,
        description: form.description,
        connection_params: buildConnectionParams(),
        pool_config: form.pool_config,
        is_enabled: true
      }, {
        timeout: 10
      })
      testResult.value = response
    }
    
    testDialogVisible.value = true
  } catch (error) {
    if (error.errors) {
      // 验证错误
      return
    }
    ElMessage.error('测试连接失败')
    console.error('Test connection error:', error)
  } finally {
    testing.value = false
  }
}

const handleSubmit = async () => {
  try {
    await formRef.value.validate()
    
    submitting.value = true
    
    const submitData = {
      ...form,
      connection_params: buildConnectionParams()
    }
    
    if (props.mode === 'create') {
      await createDatasource(submitData)
      ElMessage.success('创建成功')
    } else {
      await updateDatasource(props.datasource.id, submitData)
      ElMessage.success('更新成功')
    }
    
    emit('success')
    handleClose()
  } catch (error) {
    ElMessage.error(props.mode === 'create' ? '创建失败' : '更新失败')
    console.error('Submit error:', error)
  } finally {
    submitting.value = false
  }
}

const handleClose = () => {
  visible.value = false
}

// 工具方法
const getDatasourceTypeLabel = getTypeLabel
</script>

<style scoped>
.template-option {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.template-desc {
  font-size: 12px;
  color: #909399;
}

.params-container {
  border: 1px solid #dcdfe6;
  border-radius: 4px;
  padding: 15px;
  background-color: #fafafa;
}

.param-item {
  display: flex;
  align-items: center;
  margin-bottom: 10px;
}

.param-item:last-child {
  margin-bottom: 0;
}

.dialog-footer {
  text-align: right;
}

:deep(.el-form-item) {
  margin-bottom: 18px;
}

:deep(.el-form-item__label) {
  font-weight: 500;
}

:deep(.el-divider__text) {
  font-weight: 500;
  color: #303133;
}
</style>