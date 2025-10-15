<template>
  <div class="datasource-create">
    <div class="page-header">
      <h1>{{ isEdit ? '编辑数据源' : '新增数据源' }}</h1>
      <p>{{ isEdit ? '修改数据源连接信息' : '创建新的数据源连接' }}</p>
    </div>

    <div class="content-container">
      <el-card>
        <el-form
          ref="formRef"
          :model="formData"
          :rules="formRules"
          label-width="120px"
          size="large"
        >
          <!-- 基本信息 -->
          <div class="form-section">
            <h3>基本信息</h3>
            
            <el-form-item label="数据源名称" prop="name">
              <el-input
                v-model="formData.name"
                placeholder="请输入数据源名称（英文标识）"
                :disabled="isEdit"
              />
              <div class="form-tip">
                数据源的唯一标识，只能包含字母、数字和下划线
              </div>
            </el-form-item>
            
            <el-form-item label="显示名称" prop="display_name">
              <el-input
                v-model="formData.display_name"
                placeholder="请输入显示名称"
              />
            </el-form-item>
            
            <el-form-item label="描述信息" prop="description">
              <el-input
                v-model="formData.description"
                type="textarea"
                :rows="3"
                placeholder="请输入数据源描述"
              />
            </el-form-item>
            
            <el-form-item label="数据源类型" prop="type">
              <el-select
                v-model="formData.type"
                placeholder="请选择数据源类型"
                style="width: 100%"
                @change="handleTypeChange"
              >
                <el-option
                  v-for="type in datasourceTypes"
                  :key="type.value"
                  :label="type.label"
                  :value="type.value"
                >
                  <div class="type-option">
                    <span>{{ type.label }}</span>
                    <span class="type-desc">{{ type.description }}</span>
                  </div>
                </el-option>
              </el-select>
            </el-form-item>
          </div>

          <!-- 连接配置 -->
          <div class="form-section">
            <h3>连接配置</h3>
            
            <el-form-item label="主机地址" prop="host">
              <el-input
                v-model="formData.host"
                placeholder="请输入主机地址或IP"
              />
            </el-form-item>
            
            <el-form-item label="端口" prop="port">
              <el-input-number
                v-model="formData.port"
                :min="1"
                :max="65535"
                placeholder="请输入端口号"
                style="width: 100%"
              />
            </el-form-item>
            
            <el-form-item
              v-if="formData.type !== 'elasticsearch'"
              label="数据库名"
              prop="database"
            >
              <el-input
                v-model="formData.database"
                placeholder="请输入数据库名称"
              />
            </el-form-item>
            
            <el-form-item label="用户名" prop="username">
              <el-input
                v-model="formData.username"
                placeholder="请输入用户名"
              />
            </el-form-item>
            
            <el-form-item label="密码" prop="password">
              <el-input
                v-model="formData.password"
                type="password"
                placeholder="请输入密码"
                show-password
              />
            </el-form-item>
          </div>

          <!-- 高级配置 -->
          <div class="form-section">
            <h3>高级配置</h3>
            
            <el-form-item label="连接超时">
              <el-input-number
                v-model="formData.connection_timeout"
                :min="1"
                :max="300"
                placeholder="连接超时时间（秒）"
                style="width: 100%"
              />
              <div class="form-tip">
                连接超时时间，默认30秒
              </div>
            </el-form-item>
            
            <el-form-item label="查询超时">
              <el-input-number
                v-model="formData.query_timeout"
                :min="1"
                :max="3600"
                placeholder="查询超时时间（秒）"
                style="width: 100%"
              />
              <div class="form-tip">
                查询超时时间，默认300秒
              </div>
            </el-form-item>
            
            <el-form-item label="最大连接数">
              <el-input-number
                v-model="formData.max_connections"
                :min="1"
                :max="100"
                placeholder="最大连接数"
                style="width: 100%"
              />
              <div class="form-tip">
                连接池最大连接数，默认10
              </div>
            </el-form-item>
            
            <el-form-item label="启用SSL">
              <el-switch
                v-model="formData.ssl_enabled"
                active-text="启用"
                inactive-text="禁用"
              />
            </el-form-item>
            
            <el-form-item label="启用状态">
              <el-switch
                v-model="formData.is_active"
                active-text="启用"
                inactive-text="禁用"
              />
            </el-form-item>
          </div>

          <!-- 连接字符串预览 -->
          <div class="form-section" v-if="connectionString">
            <h3>连接字符串预览</h3>
            <el-input
              :value="connectionString"
              type="textarea"
              :rows="2"
              readonly
              placeholder="连接字符串将在填写配置后自动生成"
            />
          </div>

          <!-- 操作按钮 -->
          <div class="form-actions">
            <el-button @click="handleCancel">取消</el-button>
            <el-button @click="handleTest" :loading="testing">
              <el-icon><Connection /></el-icon>
              测试连接
            </el-button>
            <el-button
              type="primary"
              @click="handleSubmit"
              :loading="submitting"
            >
              {{ isEdit ? '更新' : '创建' }}
            </el-button>
          </div>
        </el-form>
      </el-card>
    </div>

    <!-- 测试连接对话框 -->
    <el-dialog
      v-model="testDialogVisible"
      title="测试连接结果"
      width="500px"
    >
      <div v-if="testResult" class="test-result">
        <div class="result-header">
          <el-icon :class="testResult.success ? 'success-icon' : 'error-icon'">
            <CircleCheck v-if="testResult.success" />
            <CircleClose v-else />
          </el-icon>
          <span :class="testResult.success ? 'success-text' : 'error-text'">
            {{ testResult.success ? '连接成功' : '连接失败' }}
          </span>
        </div>
        
        <div class="result-details">
          <el-descriptions :column="1" border>
            <el-descriptions-item label="响应时间">
              {{ testResult.response_time }}ms
            </el-descriptions-item>
            <el-descriptions-item label="测试时间">
              {{ formatDate(testResult.test_time) }}
            </el-descriptions-item>
            <el-descriptions-item label="详细信息" v-if="testResult.message">
              {{ testResult.message }}
            </el-descriptions-item>
            <el-descriptions-item label="错误信息" v-if="testResult.error">
              <el-text type="danger">{{ testResult.error }}</el-text>
            </el-descriptions-item>
          </el-descriptions>
        </div>
      </div>
      
      <template #footer>
        <el-button @click="testDialogVisible = false">关闭</el-button>
        <el-button type="primary" @click="handleTest" :loading="testing">
          重新测试
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Connection,
  CircleCheck,
  CircleClose
} from '@element-plus/icons-vue'
import type { FormInstance, FormRules } from 'element-plus'
import type { DatasourceCreateRequest, DatasourceTestResult } from '@/types/datasource'

/**
 * 路由实例
 */
const router = useRouter()
const route = useRoute()

/**
 * 是否为编辑模式
 */
const isEdit = computed(() => route.name === 'DatasourceEdit')

/**
 * 表单引用
 */
const formRef = ref<FormInstance>()

/**
 * 响应式数据
 */
const submitting = ref(false)
const testing = ref(false)
const testDialogVisible = ref(false)
const testResult = ref<DatasourceTestResult | null>(null)

/**
 * 数据源类型选项
 */
const datasourceTypes = [
  {
    value: 'mysql',
    label: 'MySQL',
    description: 'MySQL关系型数据库',
    defaultPort: 3306
  },
  {
    value: 'doris',
    label: 'Apache Doris',
    description: 'Doris分析型数据库',
    defaultPort: 9030
  },
  {
    value: 'elasticsearch',
    label: 'Elasticsearch',
    description: 'Elasticsearch搜索引擎',
    defaultPort: 9200
  },
  {
    value: 'clickhouse',
    label: 'ClickHouse',
    description: 'ClickHouse列式数据库',
    defaultPort: 8123
  }
]

/**
 * 表单数据
 */
const formData = reactive<DatasourceCreateRequest>({
  name: '',
  display_name: '',
  description: '',
  type: '',
  host: '',
  port: 3306,
  database: '',
  username: '',
  password: '',
  connection_timeout: 30,
  query_timeout: 300,
  max_connections: 10,
  ssl_enabled: false,
  is_active: true
})

/**
 * 表单验证规则
 */
const formRules: FormRules = {
  name: [
    { required: true, message: '请输入数据源名称', trigger: 'blur' },
    { pattern: /^[a-zA-Z][a-zA-Z0-9_]*$/, message: '名称只能包含字母、数字和下划线，且以字母开头', trigger: 'blur' }
  ],
  display_name: [
    { required: true, message: '请输入显示名称', trigger: 'blur' }
  ],
  type: [
    { required: true, message: '请选择数据源类型', trigger: 'change' }
  ],
  host: [
    { required: true, message: '请输入主机地址', trigger: 'blur' }
  ],
  port: [
    { required: true, message: '请输入端口号', trigger: 'blur' },
    { type: 'number', min: 1, max: 65535, message: '端口号必须在1-65535之间', trigger: 'blur' }
  ],
  database: [
    { required: true, message: '请输入数据库名称', trigger: 'blur' }
  ],
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' }
  ]
}

/**
 * 连接字符串预览
 */
const connectionString = computed(() => {
  if (!formData.type || !formData.host || !formData.port) {
    return ''
  }
  
  const { type, host, port, database, username } = formData
  
  switch (type) {
    case 'mysql':
      return `mysql://${username}:***@${host}:${port}/${database}`
    case 'doris':
      return `mysql://${username}:***@${host}:${port}/${database}`
    case 'elasticsearch':
      return `http://${username}:***@${host}:${port}`
    case 'clickhouse':
      return `clickhouse://${username}:***@${host}:${port}/${database}`
    default:
      return ''
  }
})

/**
 * 处理数据源类型变更
 */
const handleTypeChange = (type: string) => {
  const typeConfig = datasourceTypes.find(t => t.value === type)
  if (typeConfig) {
    formData.port = typeConfig.defaultPort
  }
  
  // 清空数据库名称（Elasticsearch不需要）
  if (type === 'elasticsearch') {
    formData.database = ''
  }
}

/**
 * 处理测试连接
 */
const handleTest = async () => {
  if (!formRef.value) return
  
  try {
    await formRef.value.validate()
  } catch (error) {
    ElMessage.warning('请先完善表单信息')
    return
  }
  
  testing.value = true
  testResult.value = null
  testDialogVisible.value = true
  
  try {
    // TODO: 调用测试连接API
    // const response = await datasourceApi.testConnection(formData)
    // testResult.value = response.data
    
    // 模拟测试结果
    await new Promise(resolve => setTimeout(resolve, 2000))
    const success = Math.random() > 0.3 // 70%成功率
    testResult.value = {
      success,
      response_time: Math.floor(Math.random() * 500) + 50,
      test_time: new Date().toISOString(),
      message: success ? '连接正常' : '连接失败',
      error: success ? undefined : '无法连接到数据库服务器，请检查配置信息'
    }
  } catch (error) {
    testResult.value = {
      success: false,
      response_time: 0,
      test_time: new Date().toISOString(),
      message: '测试失败',
      error: '网络错误或服务器不可达'
    }
  } finally {
    testing.value = false
  }
}

/**
 * 处理提交
 */
const handleSubmit = async () => {
  if (!formRef.value) return
  
  try {
    await formRef.value.validate()
  } catch (error) {
    return
  }
  
  submitting.value = true
  
  try {
    if (isEdit.value) {
      // TODO: 调用更新API
      // await datasourceApi.update(route.params.id as string, formData)
      ElMessage.success('更新成功')
    } else {
      // TODO: 调用创建API
      // await datasourceApi.create(formData)
      ElMessage.success('创建成功')
    }
    
    router.push('/datasources')
  } catch (error) {
    ElMessage.error(isEdit.value ? '更新失败' : '创建失败')
  } finally {
    submitting.value = false
  }
}

/**
 * 处理取消
 */
const handleCancel = async () => {
  try {
    await ElMessageBox.confirm(
      '确定要取消吗？未保存的更改将丢失。',
      '确认取消',
      {
        confirmButtonText: '确定',
        cancelButtonText: '继续编辑',
        type: 'warning'
      }
    )
    
    router.push('/datasources')
  } catch (error) {
    // 用户取消
  }
}

/**
 * 格式化日期
 */
const formatDate = (date: string) => {
  return new Date(date).toLocaleString()
}

/**
 * 获取数据源详情（编辑模式）
 */
const fetchDatasourceDetail = async () => {
  if (!isEdit.value) return
  
  const id = route.params.id as string
  
  try {
    // TODO: 调用获取详情API
    // const response = await datasourceApi.getDetail(id)
    // Object.assign(formData, response.data)
    
    // 模拟数据
    Object.assign(formData, {
      name: 'main_mysql',
      display_name: '主数据库',
      description: '主要的MySQL数据库',
      type: 'mysql',
      host: 'localhost',
      port: 3306,
      database: 'acwl_ai',
      username: 'root',
      password: '',
      connection_timeout: 30,
      query_timeout: 300,
      max_connections: 10,
      ssl_enabled: false,
      is_active: true
    })
  } catch (error) {
    ElMessage.error('获取数据源详情失败')
    router.push('/datasources')
  }
}

/**
 * 组件挂载时获取数据
 */
onMounted(() => {
  if (isEdit.value) {
    fetchDatasourceDetail()
  }
})
</script>

<style scoped>
.datasource-create {
  padding: 20px;
}

.page-header {
  margin-bottom: 20px;
}

.page-header h1 {
  margin: 0 0 8px 0;
  font-size: 24px;
  font-weight: 600;
}

.page-header p {
  margin: 0;
  color: #666;
}

.content-container {
  max-width: 800px;
}

.form-section {
  margin-bottom: 32px;
  padding-bottom: 24px;
  border-bottom: 1px solid #eee;
}

.form-section:last-child {
  border-bottom: none;
}

.form-section h3 {
  margin: 0 0 20px 0;
  font-size: 16px;
  font-weight: 600;
  color: #333;
}

.form-tip {
  margin-top: 4px;
  font-size: 12px;
  color: #999;
}

.type-option {
  display: flex;
  flex-direction: column;
}

.type-desc {
  font-size: 12px;
  color: #999;
}

.form-actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  margin-top: 32px;
  padding-top: 24px;
  border-top: 1px solid #eee;
}

.test-result {
  padding: 20px;
}

.result-header {
  display: flex;
  align-items: center;
  margin-bottom: 20px;
  font-size: 16px;
  font-weight: 600;
}

.success-icon {
  color: #67c23a;
  margin-right: 8px;
}

.error-icon {
  color: #f56c6c;
  margin-right: 8px;
}

.success-text {
  color: #67c23a;
}

.error-text {
  color: #f56c6c;
}
</style>