<template>
  <div class="resource-create-container">
    <!-- 页面标题 -->
    <div class="page-header">
      <div class="header-left">
        <el-button @click="goBack" class="back-btn">
          <el-icon><ArrowLeft /></el-icon>
          返回
        </el-button>
        <div class="title-section">
          <h1 class="page-title">
            <el-icon><Plus /></el-icon>
            {{ isEdit ? '编辑资源' : '创建资源' }}
          </h1>
          <p class="page-description">{{ isEdit ? '修改数据资源信息' : '添加新的数据资源到系统中' }}</p>
        </div>
      </div>
      <div class="header-actions">
        <el-button @click="saveDraft" :disabled="saving">
          <el-icon><Document /></el-icon>
          保存草稿
        </el-button>
        <el-button type="primary" @click="submitForm" :loading="saving">
          <el-icon><Check /></el-icon>
          {{ isEdit ? '更新资源' : '创建资源' }}
        </el-button>
      </div>
    </div>

    <!-- 创建表单 -->
    <div class="form-container">
      <el-form
        ref="formRef"
        :model="formData"
        :rules="formRules"
        label-width="120px"
        class="resource-form"
      >
        <!-- 基本信息 -->
        <el-card class="form-section">
          <template #header>
            <div class="section-header">
              <el-icon><InfoFilled /></el-icon>
              <span>基本信息</span>
            </div>
          </template>
          
          <el-row :gutter="20">
            <el-col :span="12">
              <el-form-item label="资源名称" prop="name">
                <el-input
                  v-model="formData.name"
                  placeholder="请输入资源名称"
                  maxlength="100"
                  show-word-limit
                />
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item label="资源类型" prop="type">
                <el-select v-model="formData.type" placeholder="请选择资源类型" style="width: 100%">
                  <el-option label="数据库" value="database" />
                  <el-option label="API接口" value="api" />
                  <el-option label="文件存储" value="file" />
                  <el-option label="消息队列" value="queue" />
                  <el-option label="缓存" value="cache" />
                  <el-option label="其他" value="other" />
                </el-select>
              </el-form-item>
            </el-col>
          </el-row>
          
          <el-row :gutter="20">
            <el-col :span="12">
              <el-form-item label="所属分类" prop="category">
                <el-cascader
                  v-model="formData.category"
                  :options="categoryOptions"
                  :props="{ expandTrigger: 'hover' }"
                  placeholder="请选择资源分类"
                  style="width: 100%"
                  clearable
                />
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item label="优先级" prop="priority">
                <el-select v-model="formData.priority" placeholder="请选择优先级" style="width: 100%">
                  <el-option label="高" value="high" />
                  <el-option label="中" value="medium" />
                  <el-option label="低" value="low" />
                </el-select>
              </el-form-item>
            </el-col>
          </el-row>
          
          <el-form-item label="资源描述" prop="description">
            <el-input
              v-model="formData.description"
              type="textarea"
              :rows="4"
              placeholder="请输入资源描述"
              maxlength="500"
              show-word-limit
            />
          </el-form-item>
          
          <el-row :gutter="20">
            <el-col :span="12">
              <el-form-item label="标签">
                <el-select
                  v-model="formData.tags"
                  multiple
                  filterable
                  allow-create
                  placeholder="请选择或输入标签"
                  style="width: 100%"
                >
                  <el-option
                    v-for="tag in availableTags"
                    :key="tag"
                    :label="tag"
                    :value="tag"
                  />
                </el-select>
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item label="状态" prop="status">
                <el-radio-group v-model="formData.status">
                  <el-radio label="active">启用</el-radio>
                  <el-radio label="inactive">禁用</el-radio>
                  <el-radio label="testing">测试中</el-radio>
                </el-radio-group>
              </el-form-item>
            </el-col>
          </el-row>
        </el-card>

        <!-- 连接配置 -->
        <el-card class="form-section">
          <template #header>
            <div class="section-header">
              <el-icon><Connection /></el-icon>
              <span>连接配置</span>
            </div>
          </template>
          
          <el-row :gutter="20">
            <el-col :span="12">
              <el-form-item label="连接地址" prop="connection.host">
                <el-input
                  v-model="formData.connection.host"
                  placeholder="请输入主机地址或域名"
                />
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item label="端口" prop="connection.port">
                <el-input-number
                  v-model="formData.connection.port"
                  :min="1"
                  :max="65535"
                  placeholder="端口号"
                  style="width: 100%"
                />
              </el-form-item>
            </el-col>
          </el-row>
          
          <el-row :gutter="20">
            <el-col :span="12">
              <el-form-item label="用户名" prop="connection.username">
                <el-input
                  v-model="formData.connection.username"
                  placeholder="请输入用户名"
                  autocomplete="off"
                />
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item label="密码" prop="connection.password">
                <el-input
                  v-model="formData.connection.password"
                  type="password"
                  placeholder="请输入密码"
                  show-password
                  autocomplete="new-password"
                />
              </el-form-item>
            </el-col>
          </el-row>
          
          <el-row :gutter="20">
            <el-col :span="12">
              <el-form-item label="数据库名" v-if="formData.type === 'database'">
                <el-input
                  v-model="formData.connection.database"
                  placeholder="请输入数据库名"
                />
              </el-form-item>
              <el-form-item label="API路径" v-else-if="formData.type === 'api'">
                <el-input
                  v-model="formData.connection.path"
                  placeholder="请输入API路径"
                />
              </el-form-item>
              <el-form-item label="存储路径" v-else-if="formData.type === 'file'">
                <el-input
                  v-model="formData.connection.path"
                  placeholder="请输入存储路径"
                />
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item label="连接超时">
                <el-input-number
                  v-model="formData.connection.timeout"
                  :min="1000"
                  :max="60000"
                  :step="1000"
                  placeholder="毫秒"
                  style="width: 100%"
                />
              </el-form-item>
            </el-col>
          </el-row>
          
          <el-form-item label="连接参数">
            <div class="connection-params">
              <div
                v-for="(param, index) in formData.connection.params"
                :key="index"
                class="param-item"
              >
                <el-input
                  v-model="param.key"
                  placeholder="参数名"
                  style="width: 200px; margin-right: 8px"
                />
                <el-input
                  v-model="param.value"
                  placeholder="参数值"
                  style="width: 200px; margin-right: 8px"
                />
                <el-button
                  type="danger"
                  size="small"
                  @click="removeParam(index)"
                >
                  <el-icon><Delete /></el-icon>
                </el-button>
              </div>
              <el-button
                type="primary"
                size="small"
                @click="addParam"
                class="add-param-btn"
              >
                <el-icon><Plus /></el-icon>
                添加参数
              </el-button>
            </div>
          </el-form-item>
          
          <el-form-item>
            <el-button @click="testConnection" :loading="testing">
              <el-icon><Connection /></el-icon>
              测试连接
            </el-button>
            <span v-if="connectionStatus" class="connection-status">
              <el-icon v-if="connectionStatus === 'success'" class="success"><SuccessFilled /></el-icon>
              <el-icon v-else class="error"><CircleCloseFilled /></el-icon>
              {{ connectionStatusText }}
            </span>
          </el-form-item>
        </el-card>

        <!-- 权限设置 -->
        <el-card class="form-section">
          <template #header>
            <div class="section-header">
              <el-icon><Lock /></el-icon>
              <span>权限设置</span>
            </div>
          </template>
          
          <el-row :gutter="20">
            <el-col :span="12">
              <el-form-item label="访问级别" prop="access.level">
                <el-select v-model="formData.access.level" placeholder="请选择访问级别" style="width: 100%">
                  <el-option label="公开" value="public" />
                  <el-option label="内部" value="internal" />
                  <el-option label="受限" value="restricted" />
                  <el-option label="私有" value="private" />
                </el-select>
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item label="数据敏感度">
                <el-select v-model="formData.access.sensitivity" placeholder="请选择敏感度" style="width: 100%">
                  <el-option label="公开" value="public" />
                  <el-option label="内部" value="internal" />
                  <el-option label="机密" value="confidential" />
                  <el-option label="绝密" value="secret" />
                </el-select>
              </el-form-item>
            </el-col>
          </el-row>
          
          <el-form-item label="授权用户">
            <el-select
              v-model="formData.access.users"
              multiple
              filterable
              placeholder="请选择授权用户"
              style="width: 100%"
            >
              <el-option
                v-for="user in availableUsers"
                :key="user.id"
                :label="user.name"
                :value="user.id"
              />
            </el-select>
          </el-form-item>
          
          <el-form-item label="授权角色">
            <el-select
              v-model="formData.access.roles"
              multiple
              filterable
              placeholder="请选择授权角色"
              style="width: 100%"
            >
              <el-option
                v-for="role in availableRoles"
                :key="role.id"
                :label="role.name"
                :value="role.id"
              />
            </el-select>
          </el-form-item>
          
          <el-form-item label="权限说明">
            <el-input
              v-model="formData.access.description"
              type="textarea"
              :rows="3"
              placeholder="请输入权限说明"
              maxlength="200"
              show-word-limit
            />
          </el-form-item>
        </el-card>

        <!-- 监控配置 -->
        <el-card class="form-section">
          <template #header>
            <div class="section-header">
              <el-icon><Monitor /></el-icon>
              <span>监控配置</span>
            </div>
          </template>
          
          <el-row :gutter="20">
            <el-col :span="12">
              <el-form-item label="启用监控">
                <el-switch
                  v-model="formData.monitoring.enabled"
                  active-text="启用"
                  inactive-text="禁用"
                />
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item label="监控间隔">
                <el-select
                  v-model="formData.monitoring.interval"
                  placeholder="请选择监控间隔"
                  style="width: 100%"
                  :disabled="!formData.monitoring.enabled"
                >
                  <el-option label="1分钟" value="1m" />
                  <el-option label="5分钟" value="5m" />
                  <el-option label="15分钟" value="15m" />
                  <el-option label="30分钟" value="30m" />
                  <el-option label="1小时" value="1h" />
                </el-select>
              </el-form-item>
            </el-col>
          </el-row>
          
          <el-form-item label="监控指标">
            <el-checkbox-group
              v-model="formData.monitoring.metrics"
              :disabled="!formData.monitoring.enabled"
            >
              <el-checkbox label="availability">可用性</el-checkbox>
              <el-checkbox label="performance">性能</el-checkbox>
              <el-checkbox label="capacity">容量</el-checkbox>
              <el-checkbox label="security">安全性</el-checkbox>
            </el-checkbox-group>
          </el-form-item>
          
          <el-form-item label="告警通知">
            <el-checkbox-group
              v-model="formData.monitoring.alerts"
              :disabled="!formData.monitoring.enabled"
            >
              <el-checkbox label="email">邮件</el-checkbox>
              <el-checkbox label="sms">短信</el-checkbox>
              <el-checkbox label="webhook">Webhook</el-checkbox>
            </el-checkbox-group>
          </el-form-item>
        </el-card>
      </el-form>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox, type FormInstance, type FormRules } from 'element-plus'

// 路由相关
const route = useRoute()
const router = useRouter()

// 响应式数据
const formRef = ref<FormInstance>()
const saving = ref(false)
const testing = ref(false)
const connectionStatus = ref<'success' | 'error' | null>(null)
const connectionStatusText = ref('')

// 判断是否为编辑模式
const isEdit = computed(() => route.params.id !== undefined)

// 表单数据
const formData = reactive({
  name: '',
  type: '',
  category: [],
  priority: 'medium',
  description: '',
  tags: [],
  status: 'active',
  connection: {
    host: '',
    port: null,
    username: '',
    password: '',
    database: '',
    path: '',
    timeout: 5000,
    params: []
  },
  access: {
    level: 'internal',
    sensitivity: 'internal',
    users: [],
    roles: [],
    description: ''
  },
  monitoring: {
    enabled: true,
    interval: '5m',
    metrics: ['availability', 'performance'],
    alerts: ['email']
  }
})

// 表单验证规则
const formRules: FormRules = {
  name: [
    { required: true, message: '请输入资源名称', trigger: 'blur' },
    { min: 2, max: 100, message: '长度在 2 到 100 个字符', trigger: 'blur' }
  ],
  type: [
    { required: true, message: '请选择资源类型', trigger: 'change' }
  ],
  category: [
    { required: true, message: '请选择资源分类', trigger: 'change' }
  ],
  priority: [
    { required: true, message: '请选择优先级', trigger: 'change' }
  ],
  description: [
    { required: true, message: '请输入资源描述', trigger: 'blur' },
    { min: 10, max: 500, message: '长度在 10 到 500 个字符', trigger: 'blur' }
  ],
  'connection.host': [
    { required: true, message: '请输入连接地址', trigger: 'blur' }
  ],
  'connection.port': [
    { required: true, message: '请输入端口号', trigger: 'blur' },
    { type: 'number', min: 1, max: 65535, message: '端口号范围 1-65535', trigger: 'blur' }
  ],
  'access.level': [
    { required: true, message: '请选择访问级别', trigger: 'change' }
  ]
}

// 选项数据
const categoryOptions = ref([
  {
    value: 'database',
    label: '数据库',
    children: [
      { value: 'mysql', label: 'MySQL' },
      { value: 'postgresql', label: 'PostgreSQL' },
      { value: 'mongodb', label: 'MongoDB' },
      { value: 'redis', label: 'Redis' }
    ]
  },
  {
    value: 'api',
    label: 'API服务',
    children: [
      { value: 'rest', label: 'REST API' },
      { value: 'graphql', label: 'GraphQL' },
      { value: 'soap', label: 'SOAP' },
      { value: 'rpc', label: 'RPC' }
    ]
  },
  {
    value: 'storage',
    label: '存储服务',
    children: [
      { value: 'file', label: '文件存储' },
      { value: 'object', label: '对象存储' },
      { value: 'block', label: '块存储' }
    ]
  },
  {
    value: 'message',
    label: '消息服务',
    children: [
      { value: 'kafka', label: 'Kafka' },
      { value: 'rabbitmq', label: 'RabbitMQ' },
      { value: 'redis', label: 'Redis Pub/Sub' }
    ]
  }
])

const availableTags = ref([
  '生产环境', '测试环境', '开发环境',
  '核心业务', '辅助系统', '第三方接口',
  '高可用', '高性能', '安全',
  '实时数据', '历史数据', '分析数据'
])

const availableUsers = ref([
  { id: 1, name: '张三' },
  { id: 2, name: '李四' },
  { id: 3, name: '王五' },
  { id: 4, name: '赵六' }
])

const availableRoles = ref([
  { id: 1, name: '系统管理员' },
  { id: 2, name: '数据管理员' },
  { id: 3, name: '业务用户' },
  { id: 4, name: '只读用户' }
])

/**
 * 返回上一页
 */
const goBack = () => {
  router.back()
}

/**
 * 添加连接参数
 */
const addParam = () => {
  formData.connection.params.push({ key: '', value: '' })
}

/**
 * 移除连接参数
 */
const removeParam = (index: number) => {
  formData.connection.params.splice(index, 1)
}

/**
 * 测试连接
 */
const testConnection = async () => {
  if (!formData.connection.host || !formData.connection.port) {
    ElMessage.warning('请先填写连接地址和端口')
    return
  }
  
  testing.value = true
  connectionStatus.value = null
  
  try {
    // 模拟测试连接
    await new Promise(resolve => setTimeout(resolve, 2000))
    
    // 随机成功或失败
    const success = Math.random() > 0.3
    
    if (success) {
      connectionStatus.value = 'success'
      connectionStatusText.value = '连接成功'
      ElMessage.success('连接测试成功')
    } else {
      connectionStatus.value = 'error'
      connectionStatusText.value = '连接失败：无法连接到目标服务器'
      ElMessage.error('连接测试失败')
    }
  } catch (error) {
    connectionStatus.value = 'error'
    connectionStatusText.value = '连接失败：网络错误'
    ElMessage.error('连接测试失败')
  } finally {
    testing.value = false
  }
}

/**
 * 保存草稿
 */
const saveDraft = async () => {
  saving.value = true
  
  try {
    // 模拟保存草稿
    await new Promise(resolve => setTimeout(resolve, 1000))
    ElMessage.success('草稿已保存')
  } catch (error) {
    ElMessage.error('保存草稿失败')
  } finally {
    saving.value = false
  }
}

/**
 * 提交表单
 */
const submitForm = async () => {
  if (!formRef.value) return
  
  try {
    await formRef.value.validate()
    
    saving.value = true
    
    // 模拟提交
    await new Promise(resolve => setTimeout(resolve, 2000))
    
    ElMessage.success(isEdit.value ? '资源更新成功' : '资源创建成功')
    
    // 跳转到资源列表
    router.push('/data-resource')
  } catch (error) {
    if (error !== false) {
      ElMessage.error('表单验证失败，请检查输入')
    }
  } finally {
    saving.value = false
  }
}

/**
 * 加载资源数据（编辑模式）
 */
const loadResourceData = async () => {
  if (!isEdit.value) return
  
  const resourceId = route.params.id
  
  try {
    // 模拟加载数据
    await new Promise(resolve => setTimeout(resolve, 1000))
    
    // 模拟数据
    Object.assign(formData, {
      name: '用户数据库',
      type: 'database',
      category: ['database', 'mysql'],
      priority: 'high',
      description: '存储用户基本信息和账户数据的主数据库',
      tags: ['生产环境', '核心业务', '高可用'],
      status: 'active',
      connection: {
        host: 'db.example.com',
        port: 3306,
        username: 'admin',
        password: '******',
        database: 'user_db',
        path: '',
        timeout: 5000,
        params: [
          { key: 'charset', value: 'utf8mb4' },
          { key: 'timezone', value: '+08:00' }
        ]
      },
      access: {
        level: 'restricted',
        sensitivity: 'confidential',
        users: [1, 2],
        roles: [1, 2],
        description: '仅限核心开发团队访问'
      },
      monitoring: {
        enabled: true,
        interval: '5m',
        metrics: ['availability', 'performance', 'capacity'],
        alerts: ['email', 'webhook']
      }
    })
  } catch (error) {
    ElMessage.error('加载资源数据失败')
  }
}

/**
 * 组件挂载时初始化
 */
onMounted(() => {
  loadResourceData()
})
</script>

<style lang="scss" scoped>
.resource-create-container {
  padding: 20px;
  background: var(--el-bg-color-page);
  min-height: 100vh;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 24px;
  
  .header-left {
    display: flex;
    align-items: flex-start;
    gap: 16px;
    
    .back-btn {
      margin-top: 4px;
    }
    
    .title-section {
      .page-title {
        display: flex;
        align-items: center;
        font-size: 24px;
        font-weight: 600;
        color: var(--el-text-color-primary);
        margin: 0 0 8px 0;
        
        .el-icon {
          margin-right: 8px;
          color: var(--el-color-primary);
        }
      }
      
      .page-description {
        color: var(--el-text-color-secondary);
        margin: 0;
      }
    }
  }
  
  .header-actions {
    display: flex;
    gap: 12px;
  }
}

.form-container {
  max-width: 1200px;
}

.resource-form {
  .form-section {
    margin-bottom: 20px;
    
    .section-header {
      display: flex;
      align-items: center;
      gap: 8px;
      font-weight: 600;
      color: var(--el-text-color-primary);
    }
  }
}

.connection-params {
  .param-item {
    display: flex;
    align-items: center;
    margin-bottom: 8px;
  }
  
  .add-param-btn {
    margin-top: 8px;
  }
}

.connection-status {
  margin-left: 12px;
  display: flex;
  align-items: center;
  gap: 4px;
  
  .el-icon {
    &.success {
      color: var(--el-color-success);
    }
    
    &.error {
      color: var(--el-color-error);
    }
  }
}

// 响应式设计
@media (max-width: 1200px) {
  .form-container {
    max-width: 100%;
  }
  
  .resource-form {
    .el-row {
      .el-col {
        margin-bottom: 16px;
      }
    }
  }
}

@media (max-width: 768px) {
  .resource-create-container {
    padding: 16px;
  }
  
  .page-header {
    flex-direction: column;
    gap: 16px;
    align-items: stretch;
    
    .header-left {
      flex-direction: column;
      gap: 12px;
      
      .back-btn {
        align-self: flex-start;
        margin-top: 0;
      }
    }
    
    .header-actions {
      justify-content: center;
    }
  }
  
  .resource-form {
    .el-col {
      span: 24 !important;
    }
  }
  
  .connection-params {
    .param-item {
      flex-direction: column;
      align-items: stretch;
      gap: 8px;
      
      .el-input {
        width: 100% !important;
        margin-right: 0 !important;
      }
      
      .el-button {
        align-self: center;
        margin-top: 8px;
      }
    }
  }
}
</style>