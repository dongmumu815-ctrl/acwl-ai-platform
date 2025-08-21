<template>
  <div class="create-deployment-page">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="header-content">
        <div class="header-left">
          <el-button @click="goBack" text>
            <el-icon><ArrowLeft /></el-icon>
            返回
          </el-button>
          <h1 class="page-title">
            <el-icon><Plus /></el-icon>
            创建部署
          </h1>
          <p class="page-description">配置并部署您的AI模型</p>
        </div>
      </div>
    </div>

    <!-- 步骤指示器 -->
    <div class="steps-section">
      <el-steps :active="currentStep" align-center>
        <el-step title="基本信息" description="配置部署基本信息" />
        <el-step title="模型选择" description="选择要部署的模型" />
        <el-step title="服务器配置" description="选择服务器和GPU资源" />
        <el-step title="部署配置" description="配置运行参数" />
        <el-step title="确认部署" description="确认配置并创建部署" />
      </el-steps>
    </div>

    <!-- 表单内容 -->
    <div class="form-section">
      <el-card shadow="never">
        <!-- 步骤1: 基本信息 -->
        <div v-if="currentStep === 0" class="step-content">
          <h3 class="step-title">基本信息</h3>
          <el-form
            ref="basicFormRef"
            :model="formData.basic"
            :rules="basicRules"
            label-width="120px"
            class="step-form"
          >
            <el-row :gutter="20">
              <el-col :span="12">
                <el-form-item label="部署名称" prop="name">
                  <el-input
                    v-model="formData.basic.name"
                    placeholder="请输入部署名称"
                    maxlength="50"
                    show-word-limit
                  />
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="环境" prop="environment">
                  <el-select v-model="formData.basic.environment" style="width: 100%">
                    <el-option label="开发环境" value="development" />
                    <el-option label="测试环境" value="testing" />
                    <el-option label="生产环境" value="production" />
                  </el-select>
                </el-form-item>
              </el-col>
            </el-row>
            
            <el-form-item label="描述" prop="description">
              <el-input
                v-model="formData.basic.description"
                type="textarea"
                :rows="3"
                placeholder="请输入部署描述（可选）"
                maxlength="200"
                show-word-limit
              />
            </el-form-item>
            
            <el-form-item label="标签">
              <el-tag
                v-for="tag in formData.basic.tags"
                :key="tag"
                closable
                @close="removeTag(tag)"
                style="margin-right: 8px; margin-bottom: 8px;"
              >
                {{ tag }}
              </el-tag>
              <el-input
                v-if="tagInputVisible"
                ref="tagInputRef"
                v-model="tagInputValue"
                size="small"
                style="width: 100px;"
                @keyup.enter="addTag"
                @blur="addTag"
              />
              <el-button
                v-else
                size="small"
                @click="showTagInput"
              >
                + 添加标签
              </el-button>
            </el-form-item>
          </el-form>
        </div>

        <!-- 步骤2: 模型选择 -->
        <div v-if="currentStep === 1" class="step-content">
          <h3 class="step-title">模型选择</h3>
          <div class="model-selection">
            <div class="search-section">
              <el-input
                v-model="modelSearchQuery"
                placeholder="搜索模型名称或描述..."
                clearable
                style="width: 300px; margin-bottom: 20px;"
              >
                <template #prefix>
                  <el-icon><Search /></el-icon>
                </template>
              </el-input>
            </div>
            
            <div class="model-grid">
              <div
                v-for="model in filteredModels"
                :key="model.id"
                class="model-card"
                :class="{ selected: formData.model.id === model.id }"
                @click="selectModel(model)"
              >
                <div class="model-header">
                  <div class="model-info">
                    <h4 class="model-name">{{ model.name }}</h4>
                    <p class="model-description">{{ model.description }}</p>
                  </div>
                  <div class="model-status">
                    <el-tag :type="model.status === 'ready' ? 'success' : 'warning'" size="small">
                      {{ model.status === 'ready' ? '就绪' : '训练中' }}
                    </el-tag>
                  </div>
                </div>
                
                <div class="model-details">
                  <div class="detail-item">
                    <span class="label">类型:</span>
                    <span class="value">{{ model.type }}</span>
                  </div>
                  <div class="detail-item">
                    <span class="label">框架:</span>
                    <span class="value">{{ model.framework }}</span>
                  </div>
                  <div class="detail-item">
                    <span class="label">大小:</span>
                    <span class="value">{{ model.size }}</span>
                  </div>
                  <div class="detail-item">
                    <span class="label">创建时间:</span>
                    <span class="value">{{ formatDate(model.created_at) }}</span>
                  </div>
                </div>
                
                <div class="model-requirements" v-if="model.requirements">
                  <div class="requirement-item">
                    <el-icon><Cpu /></el-icon>
                    <span>CPU: {{ model.requirements.cpu }}</span>
                  </div>
                  <div class="requirement-item">
                    <el-icon><Monitor /></el-icon>
                    <span>内存: {{ model.requirements.memory }}</span>
                  </div>
                  <div class="requirement-item" v-if="model.requirements.gpu">
                    <el-icon><VideoCamera /></el-icon>
                    <span>GPU: {{ model.requirements.gpu }}</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- 步骤3: 服务器配置 -->
        <div v-if="currentStep === 2" class="step-content">
          <h3 class="step-title">服务器配置</h3>
          
          <!-- 服务器选择 -->
          <div class="server-selection">
            <h4 class="section-title">
              <el-icon><Monitor /></el-icon>
              选择服务器
            </h4>
            
            <div class="server-grid">
              <div
                v-for="server in availableServers"
                :key="server.id"
                class="server-card"
                :class="{ 
                  selected: formData.server.id === server.id,
                  disabled: server.status !== 'online'
                }"
                @click="selectServer(server)"
              >
                <div class="server-header">
                  <div class="server-info">
                    <h4 class="server-name">{{ server.name }}</h4>
                    <p class="server-ip">{{ server.ip_address }}</p>
                  </div>
                  <div class="server-status" :class="server.status">
                    <el-icon v-if="server.status === 'online'">
                      <CircleCheckFilled />
                    </el-icon>
                    <el-icon v-else>
                      <CircleCloseFilled />
                    </el-icon>
                    {{ getServerStatusText(server.status) }}
                  </div>
                </div>
                
                <div class="server-specs">
                  <div class="spec-item">
                    <span class="label">CPU:</span>
                    <span class="value">{{ server.total_cpu_cores }} 核</span>
                  </div>
                  <div class="spec-item">
                    <span class="label">内存:</span>
                    <span class="value">{{ server.total_memory }}</span>
                  </div>
                  <div class="spec-item">
                    <span class="label">GPU:</span>
                    <span class="value">{{ server.gpu_count }} 个</span>
                  </div>
                  <div class="spec-item">
                    <span class="label">可用GPU:</span>
                    <span class="value">{{ server.available_gpu_count }} 个</span>
                  </div>
                </div>
                
                <div class="server-usage">
                  <div class="usage-item">
                    <span class="usage-label">CPU使用率</span>
                    <el-progress
                      :percentage="server.cpu_usage"
                      :stroke-width="4"
                      :show-text="false"
                      :color="getUsageColor(server.cpu_usage)"
                    />
                    <span class="usage-value">{{ server.cpu_usage }}%</span>
                  </div>
                  <div class="usage-item">
                    <span class="usage-label">内存使用率</span>
                    <el-progress
                      :percentage="server.memory_usage"
                      :stroke-width="4"
                      :show-text="false"
                      :color="getUsageColor(server.memory_usage)"
                    />
                    <span class="usage-value">{{ server.memory_usage }}%</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
          
          <!-- GPU选择 -->
          <div v-if="formData.server.id" class="gpu-selection">
            <h4 class="section-title">
              <el-icon><VideoCamera /></el-icon>
              选择GPU资源
            </h4>
            
            <div class="gpu-grid">
              <div
                v-for="gpu in serverGpus"
                :key="gpu.id"
                class="gpu-card"
                :class="{ 
                  selected: formData.gpus.some(g => g.id === gpu.id),
                  disabled: !gpu.is_available
                }"
                @click="toggleGpu(gpu)"
              >
                <div class="gpu-header">
                  <div class="gpu-info">
                    <h5 class="gpu-name">{{ gpu.gpu_name }}</h5>
                    <p class="gpu-type">{{ gpu.gpu_type }}</p>
                  </div>
                  <div class="gpu-status">
                    <el-tag :type="gpu.is_available ? 'success' : 'danger'" size="small">
                      {{ gpu.is_available ? '可用' : '占用中' }}
                    </el-tag>
                  </div>
                </div>
                
                <div class="gpu-specs">
                  <div class="spec-item">
                    <span class="label">显存:</span>
                    <span class="value">{{ gpu.memory_size }}</span>
                  </div>
                  <div class="spec-item">
                    <span class="label">CUDA:</span>
                    <span class="value">{{ gpu.cuda_version }}</span>
                  </div>
                  <div class="spec-item">
                    <span class="label">设备ID:</span>
                    <span class="value">{{ gpu.device_id }}</span>
                  </div>
                </div>
                
                <div v-if="formData.gpus.some(g => g.id === gpu.id)" class="gpu-config">
                  <el-form-item label="显存限制" size="small">
                    <el-input-number
                      v-model="getGpuConfig(gpu.id).memory_limit"
                      :min="1"
                      :max="parseInt(gpu.memory_size)"
                      size="small"
                      style="width: 100%"
                    />
                    <span class="unit">GB</span>
                  </el-form-item>
                </div>
              </div>
            </div>
            
            <div v-if="formData.gpus.length === 0" class="no-gpu-selected">
              <el-empty description="请选择至少一个GPU资源" />
            </div>
          </div>
        </div>

        <!-- 步骤4: 部署配置 -->
        <div v-if="currentStep === 3" class="step-content">
          <h3 class="step-title">部署配置</h3>
          <el-form
            ref="deployFormRef"
            :model="formData.deploy"
            :rules="deployRules"
            label-width="150px"
            class="step-form"
          >
            <el-row :gutter="20">
              <el-col :span="12">
                <el-form-item label="部署类型" prop="deployment_type">
                  <el-select v-model="formData.deploy.deployment_type" style="width: 100%">
                    <el-option label="Docker容器" value="docker" />
                    <el-option label="Kubernetes" value="k8s" />
                    <el-option label="直接部署" value="direct" />
                  </el-select>
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="端口" prop="port">
                  <el-input-number
                    v-model="formData.deploy.port"
                    :min="1024"
                    :max="65535"
                    style="width: 100%"
                  />
                </el-form-item>
              </el-col>
            </el-row>
            
            <el-row :gutter="20">
              <el-col :span="12">
                <el-form-item label="最大并发请求" prop="max_concurrent_requests">
                  <el-input-number
                    v-model="formData.deploy.max_concurrent_requests"
                    :min="1"
                    :max="1000"
                    style="width: 100%"
                  />
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="重启策略" prop="restart_policy">
                  <el-select v-model="formData.deploy.restart_policy" style="width: 100%">
                    <el-option label="总是重启" value="always" />
                    <el-option label="失败时重启" value="on-failure" />
                    <el-option label="不重启" value="no" />
                  </el-select>
                </el-form-item>
              </el-col>
            </el-row>
            
            <el-form-item label="环境变量">
              <div class="env-vars">
                <div
                  v-for="(env, index) in formData.deploy.env_vars"
                  :key="index"
                  class="env-var-item"
                >
                  <el-input
                    v-model="env.key"
                    placeholder="变量名"
                    style="width: 200px; margin-right: 8px;"
                  />
                  <el-input
                    v-model="env.value"
                    placeholder="变量值"
                    style="width: 200px; margin-right: 8px;"
                  />
                  <el-button
                    type="danger"
                    size="small"
                    @click="removeEnvVar(index)"
                  >
                    删除
                  </el-button>
                </div>
                <el-button
                  type="primary"
                  size="small"
                  @click="addEnvVar"
                >
                  添加环境变量
                </el-button>
              </div>
            </el-form-item>
            
            <el-form-item label="健康检查">
              <el-switch
                v-model="formData.deploy.health_check.enabled"
                active-text="启用"
                inactive-text="禁用"
              />
            </el-form-item>
            
            <div v-if="formData.deploy.health_check.enabled" class="health-check-config">
              <el-row :gutter="20">
                <el-col :span="8">
                  <el-form-item label="检查路径">
                    <el-input
                      v-model="formData.deploy.health_check.path"
                      placeholder="/health"
                    />
                  </el-form-item>
                </el-col>
                <el-col :span="8">
                  <el-form-item label="检查间隔(秒)">
                    <el-input-number
                      v-model="formData.deploy.health_check.interval"
                      :min="5"
                      :max="300"
                      style="width: 100%"
                    />
                  </el-form-item>
                </el-col>
                <el-col :span="8">
                  <el-form-item label="超时时间(秒)">
                    <el-input-number
                      v-model="formData.deploy.health_check.timeout"
                      :min="1"
                      :max="60"
                      style="width: 100%"
                    />
                  </el-form-item>
                </el-col>
              </el-row>
            </div>
          </el-form>
        </div>

        <!-- 步骤5: 确认部署 -->
        <div v-if="currentStep === 4" class="step-content">
          <h3 class="step-title">确认部署</h3>
          <div class="deployment-summary">
            <el-descriptions :column="2" border>
              <el-descriptions-item label="部署名称">
                {{ formData.basic.name }}
              </el-descriptions-item>
              <el-descriptions-item label="环境">
                {{ getEnvironmentText(formData.basic.environment) }}
              </el-descriptions-item>
              <el-descriptions-item label="模型">
                {{ formData.model.name }}
              </el-descriptions-item>
              <el-descriptions-item label="服务器">
                {{ formData.server.name }} ({{ formData.server.ip_address }})
              </el-descriptions-item>
              <el-descriptions-item label="GPU资源">
                <div>
                  <el-tag
                    v-for="gpu in formData.gpus"
                    :key="gpu.id"
                    style="margin-right: 8px; margin-bottom: 4px;"
                  >
                    {{ gpu.gpu_name }} ({{ getGpuConfig(gpu.id).memory_limit }}GB)
                  </el-tag>
                </div>
              </el-descriptions-item>
              <el-descriptions-item label="部署类型">
                {{ getDeploymentTypeText(formData.deploy.deployment_type) }}
              </el-descriptions-item>
              <el-descriptions-item label="端口">
                {{ formData.deploy.port }}
              </el-descriptions-item>
              <el-descriptions-item label="最大并发">
                {{ formData.deploy.max_concurrent_requests }}
              </el-descriptions-item>
            </el-descriptions>
            
            <div v-if="formData.basic.description" class="description-section">
              <h4>描述</h4>
              <p>{{ formData.basic.description }}</p>
            </div>
            
            <div v-if="formData.basic.tags.length > 0" class="tags-section">
              <h4>标签</h4>
              <el-tag
                v-for="tag in formData.basic.tags"
                :key="tag"
                style="margin-right: 8px;"
              >
                {{ tag }}
              </el-tag>
            </div>
          </div>
        </div>

        <!-- 操作按钮 -->
        <div class="form-actions">
          <el-button
            v-if="currentStep > 0"
            @click="prevStep"
          >
            上一步
          </el-button>
          <el-button
            v-if="currentStep < 4"
            type="primary"
            @click="nextStep"
            :disabled="!canProceed"
          >
            下一步
          </el-button>
          <el-button
            v-if="currentStep === 4"
            type="primary"
            @click="createDeployment"
            :loading="creating"
          >
            创建部署
          </el-button>
          <el-button @click="goBack">
            取消
          </el-button>
        </div>
      </el-card>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  ArrowLeft,
  Plus,
  Search,
  Monitor,
  VideoCamera,
  Cpu,
  CircleCheckFilled,
  CircleCloseFilled
} from '@element-plus/icons-vue'

const router = useRouter()

// 响应式数据
const currentStep = ref(0)
const creating = ref(false)
const modelSearchQuery = ref('')
const tagInputVisible = ref(false)
const tagInputValue = ref('')
const tagInputRef = ref()

// 表单数据
const formData = reactive({
  basic: {
    name: '',
    environment: 'development',
    description: '',
    tags: [] as string[]
  },
  model: {
    id: '',
    name: '',
    type: '',
    framework: '',
    requirements: null
  },
  server: {
    id: '',
    name: '',
    ip_address: ''
  },
  gpus: [] as any[],
  deploy: {
    deployment_type: 'docker',
    port: 8080,
    max_concurrent_requests: 10,
    restart_policy: 'always',
    env_vars: [] as { key: string; value: string }[],
    health_check: {
      enabled: true,
      path: '/health',
      interval: 30,
      timeout: 10
    }
  }
})

// 表单验证规则
const basicRules = {
  name: [
    { required: true, message: '请输入部署名称', trigger: 'blur' },
    { min: 3, max: 50, message: '长度在 3 到 50 个字符', trigger: 'blur' }
  ],
  environment: [
    { required: true, message: '请选择环境', trigger: 'change' }
  ]
}

const deployRules = {
  deployment_type: [
    { required: true, message: '请选择部署类型', trigger: 'change' }
  ],
  port: [
    { required: true, message: '请输入端口', trigger: 'blur' }
  ],
  max_concurrent_requests: [
    { required: true, message: '请输入最大并发请求数', trigger: 'blur' }
  ],
  restart_policy: [
    { required: true, message: '请选择重启策略', trigger: 'change' }
  ]
}

const basicFormRef = ref()
const deployFormRef = ref()

// 模拟数据
const models = ref([
  {
    id: '1',
    name: 'ChatGPT-3.5-Turbo',
    description: '强大的对话AI模型，适用于聊天机器人和问答系统',
    type: 'Language Model',
    framework: 'PyTorch',
    size: '13GB',
    status: 'ready',
    created_at: '2024-01-15T10:30:00Z',
    requirements: {
      cpu: '4核',
      memory: '16GB',
      gpu: '1x A100'
    }
  },
  {
    id: '2',
    name: 'BERT-Base-Chinese',
    description: '中文文本分类和情感分析模型',
    type: 'Classification',
    framework: 'TensorFlow',
    size: '1.2GB',
    status: 'ready',
    created_at: '2024-01-10T08:20:00Z',
    requirements: {
      cpu: '2核',
      memory: '8GB'
    }
  },
  {
    id: '3',
    name: 'ResNet-50',
    description: '图像分类和特征提取模型',
    type: 'Computer Vision',
    framework: 'PyTorch',
    size: '98MB',
    status: 'ready',
    created_at: '2024-01-08T14:15:00Z',
    requirements: {
      cpu: '2核',
      memory: '4GB',
      gpu: '1x RTX 3080'
    }
  }
])

const availableServers = ref([
  {
    id: 1,
    name: 'GPU-Server-01',
    ip_address: '10.20.1.201',
    status: 'online',
    total_cpu_cores: 32,
    total_memory: '128GB',
    gpu_count: 2,
    available_gpu_count: 1,
    cpu_usage: 45,
    memory_usage: 62
  },
  {
    id: 2,
    name: 'GPU-Server-02',
    ip_address: '10.20.1.202',
    status: 'online',
    total_cpu_cores: 64,
    total_memory: '256GB',
    gpu_count: 4,
    available_gpu_count: 3,
    cpu_usage: 30,
    memory_usage: 45
  },
  {
    id: 3,
    name: 'Cloud-Server-01',
    ip_address: '10.20.1.203',
    status: 'offline',
    total_cpu_cores: 16,
    total_memory: '64GB',
    gpu_count: 1,
    available_gpu_count: 0,
    cpu_usage: 0,
    memory_usage: 0
  }
])

const serverGpus = ref<any[]>([])

// 计算属性
const filteredModels = computed(() => {
  if (!modelSearchQuery.value) return models.value
  return models.value.filter(model => 
    model.name.toLowerCase().includes(modelSearchQuery.value.toLowerCase()) ||
    model.description.toLowerCase().includes(modelSearchQuery.value.toLowerCase())
  )
})

const canProceed = computed(() => {
  switch (currentStep.value) {
    case 0:
      return formData.basic.name && formData.basic.environment
    case 1:
      return formData.model.id
    case 2:
      return formData.server.id && formData.gpus.length > 0
    case 3:
      return formData.deploy.deployment_type && formData.deploy.port
    default:
      return true
  }
})

// 方法
const goBack = () => {
  router.push('/deployments')
}

const nextStep = async () => {
  // 验证当前步骤
  if (currentStep.value === 0) {
    try {
      await basicFormRef.value?.validate()
    } catch (error) {
      return
    }
  } else if (currentStep.value === 3) {
    try {
      await deployFormRef.value?.validate()
    } catch (error) {
      return
    }
  }
  
  if (currentStep.value < 4) {
    currentStep.value++
  }
}

const prevStep = () => {
  if (currentStep.value > 0) {
    currentStep.value--
  }
}

const selectModel = (model: any) => {
  formData.model = { ...model }
}

const selectServer = async (server: any) => {
  if (server.status !== 'online') {
    ElMessage.warning('服务器离线，无法选择')
    return
  }
  
  formData.server = { ...server }
  formData.gpus = [] // 清空已选择的GPU
  
  // 加载服务器的GPU资源
  await loadServerGpus(server.id)
}

const loadServerGpus = async (serverId: number) => {
  try {
    // TODO: 调用API获取服务器GPU资源
    // 模拟数据
    const gpuData = {
      1: [
        {
          id: 1,
          gpu_name: 'NVIDIA A100',
          gpu_type: 'A100',
          memory_size: '80GB',
          cuda_version: '12.1',
          device_id: '0',
          is_available: true
        },
        {
          id: 2,
          gpu_name: 'NVIDIA A100',
          gpu_type: 'A100',
          memory_size: '80GB',
          cuda_version: '12.1',
          device_id: '1',
          is_available: false
        }
      ],
      2: [
        {
          id: 3,
          gpu_name: 'NVIDIA A100',
          gpu_type: 'A100',
          memory_size: '80GB',
          cuda_version: '12.1',
          device_id: '0',
          is_available: true
        },
        {
          id: 4,
          gpu_name: 'NVIDIA A100',
          gpu_type: 'A100',
          memory_size: '80GB',
          cuda_version: '12.1',
          device_id: '1',
          is_available: true
        },
        {
          id: 5,
          gpu_name: 'NVIDIA RTX 4090',
          gpu_type: 'RTX 4090',
          memory_size: '24GB',
          cuda_version: '12.1',
          device_id: '2',
          is_available: true
        },
        {
          id: 6,
          gpu_name: 'NVIDIA RTX 4090',
          gpu_type: 'RTX 4090',
          memory_size: '24GB',
          cuda_version: '12.1',
          device_id: '3',
          is_available: false
        }
      ]
    }
    
    serverGpus.value = gpuData[serverId as keyof typeof gpuData] || []
  } catch (error) {
    ElMessage.error('加载GPU资源失败')
  }
}

const toggleGpu = (gpu: any) => {
  if (!gpu.is_available) {
    ElMessage.warning('该GPU正在被占用，无法选择')
    return
  }
  
  const index = formData.gpus.findIndex(g => g.id === gpu.id)
  if (index > -1) {
    formData.gpus.splice(index, 1)
  } else {
    formData.gpus.push({
      ...gpu,
      memory_limit: parseInt(gpu.memory_size) // 默认使用全部显存
    })
  }
}

const getGpuConfig = (gpuId: number) => {
  return formData.gpus.find(g => g.id === gpuId) || { memory_limit: 0 }
}

const addTag = () => {
  if (tagInputValue.value && !formData.basic.tags.includes(tagInputValue.value)) {
    formData.basic.tags.push(tagInputValue.value)
  }
  tagInputVisible.value = false
  tagInputValue.value = ''
}

const removeTag = (tag: string) => {
  const index = formData.basic.tags.indexOf(tag)
  if (index > -1) {
    formData.basic.tags.splice(index, 1)
  }
}

const showTagInput = () => {
  tagInputVisible.value = true
  nextTick(() => {
    tagInputRef.value?.focus()
  })
}

const addEnvVar = () => {
  formData.deploy.env_vars.push({ key: '', value: '' })
}

const removeEnvVar = (index: number) => {
  formData.deploy.env_vars.splice(index, 1)
}

const createDeployment = async () => {
  try {
    creating.value = true
    
    // TODO: 调用API创建部署
    const deploymentData = {
      ...formData.basic,
      model_id: formData.model.id,
      server_id: formData.server.id,
      gpu_ids: formData.gpus.map(g => ({ id: g.id, memory_limit: g.memory_limit })),
      ...formData.deploy
    }
    
    console.log('创建部署:', deploymentData)
    
    // 模拟API调用
    await new Promise(resolve => setTimeout(resolve, 2000))
    
    ElMessage.success('部署创建成功')
    router.push('/deployments')
  } catch (error) {
    console.error('创建部署失败:', error)
    ElMessage.error('创建部署失败，请稍后重试')
  } finally {
    creating.value = false
  }
}

const formatDate = (date: string) => {
  return new Date(date).toLocaleDateString('zh-CN')
}

const getServerStatusText = (status: string) => {
  const statusMap: Record<string, string> = {
    online: '在线',
    offline: '离线',
    maintenance: '维护中'
  }
  return statusMap[status] || status
}

const getEnvironmentText = (environment: string) => {
  const envMap: Record<string, string> = {
    development: '开发环境',
    testing: '测试环境',
    production: '生产环境'
  }
  return envMap[environment] || environment
}

const getDeploymentTypeText = (type: string) => {
  const typeMap: Record<string, string> = {
    docker: 'Docker容器',
    k8s: 'Kubernetes',
    direct: '直接部署'
  }
  return typeMap[type] || type
}

const getUsageColor = (usage: number) => {
  if (usage >= 80) return '#f56c6c'
  if (usage >= 60) return '#e6a23c'
  return '#67c23a'
}

// 生命周期
onMounted(() => {
  // 初始化数据
})
</script>

<style scoped>
.create-deployment-page {
  padding: 20px;
  max-width: 1200px;
  margin: 0 auto;
}

.page-header {
  margin-bottom: 24px;
}

.header-content {
  display: flex;
  align-items: center;
}

.page-title {
  margin: 0 0 0 12px;
  font-size: 24px;
  font-weight: 600;
  color: #1f2937;
  display: flex;
  align-items: center;
  gap: 8px;
}

.page-description {
  margin: 4px 0 0 32px;
  color: #6b7280;
  font-size: 14px;
}

.steps-section {
  margin-bottom: 32px;
}

.form-section {
  margin-bottom: 24px;
}

.step-content {
  padding: 24px 0;
}

.step-title {
  margin: 0 0 24px 0;
  font-size: 20px;
  font-weight: 600;
  color: #1f2937;
}

.step-form {
  max-width: 800px;
}

.section-title {
  margin: 24px 0 16px 0;
  font-size: 16px;
  font-weight: 600;
  color: #1f2937;
  display: flex;
  align-items: center;
  gap: 8px;
}

/* 模型选择样式 */
.model-selection {
  max-width: 100%;
}

.model-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(400px, 1fr));
  gap: 16px;
}

.model-card {
  border: 2px solid #e5e7eb;
  border-radius: 12px;
  padding: 20px;
  cursor: pointer;
  transition: all 0.3s ease;
  background: white;
}

.model-card:hover {
  border-color: #3b82f6;
  box-shadow: 0 4px 12px rgba(59, 130, 246, 0.15);
}

.model-card.selected {
  border-color: #3b82f6;
  background: #eff6ff;
}

.model-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 16px;
}

.model-name {
  margin: 0 0 4px 0;
  font-size: 18px;
  font-weight: 600;
  color: #1f2937;
}

.model-description {
  margin: 0;
  font-size: 14px;
  color: #6b7280;
  line-height: 1.5;
}

.model-details {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 8px;
  margin-bottom: 16px;
}

.detail-item {
  display: flex;
  justify-content: space-between;
  font-size: 14px;
}

.detail-item .label {
  color: #6b7280;
}

.detail-item .value {
  color: #1f2937;
  font-weight: 500;
}

.model-requirements {
  display: flex;
  gap: 16px;
  flex-wrap: wrap;
}

.requirement-item {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  color: #6b7280;
  background: #f3f4f6;
  padding: 4px 8px;
  border-radius: 6px;
}

/* 服务器选择样式 */
.server-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
  gap: 16px;
  margin-bottom: 24px;
}

.server-card {
  border: 2px solid #e5e7eb;
  border-radius: 12px;
  padding: 20px;
  cursor: pointer;
  transition: all 0.3s ease;
  background: white;
}

.server-card:hover:not(.disabled) {
  border-color: #3b82f6;
  box-shadow: 0 4px 12px rgba(59, 130, 246, 0.15);
}

.server-card.selected {
  border-color: #3b82f6;
  background: #eff6ff;
}

.server-card.disabled {
  opacity: 0.6;
  cursor: not-allowed;
  background: #f9fafb;
}

.server-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 16px;
}

.server-name {
  margin: 0 0 4px 0;
  font-size: 16px;
  font-weight: 600;
  color: #1f2937;
}

.server-ip {
  margin: 0;
  font-size: 14px;
  color: #6b7280;
  font-family: 'Monaco', 'Menlo', monospace;
}

.server-status {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  font-weight: 500;
  padding: 4px 8px;
  border-radius: 6px;
}

.server-status.online {
  color: #059669;
  background: #d1fae5;
}

.server-status.offline {
  color: #dc2626;
  background: #fee2e2;
}

.server-specs {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 8px;
  margin-bottom: 16px;
}

.spec-item {
  display: flex;
  justify-content: space-between;
  font-size: 14px;
}

.spec-item .label {
  color: #6b7280;
}

.spec-item .value {
  color: #1f2937;
  font-weight: 500;
}

.server-usage {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.usage-item {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
}

.usage-label {
  width: 60px;
  color: #6b7280;
}

.usage-value {
  width: 35px;
  text-align: right;
  color: #1f2937;
  font-weight: 500;
}

/* GPU选择样式 */
.gpu-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 16px;
}

.gpu-card {
  border: 2px solid #e5e7eb;
  border-radius: 12px;
  padding: 16px;
  cursor: pointer;
  transition: all 0.3s ease;
  background: white;
}

.gpu-card:hover:not(.disabled) {
  border-color: #3b82f6;
  box-shadow: 0 4px 12px rgba(59, 130, 246, 0.15);
}

.gpu-card.selected {
  border-color: #3b82f6;
  background: #eff6ff;
}

.gpu-card.disabled {
  opacity: 0.6;
  cursor: not-allowed;
  background: #f9fafb;
}

.gpu-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 12px;
}

.gpu-name {
  margin: 0 0 4px 0;
  font-size: 14px;
  font-weight: 600;
  color: #1f2937;
}

.gpu-type {
  margin: 0;
  font-size: 12px;
  color: #6b7280;
}

.gpu-specs {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 6px;
  margin-bottom: 12px;
}

.gpu-config {
  padding-top: 12px;
  border-top: 1px solid #e5e7eb;
}

.gpu-config .unit {
  margin-left: 8px;
  font-size: 12px;
  color: #6b7280;
}

.no-gpu-selected {
  text-align: center;
  padding: 40px 0;
}

/* 环境变量样式 */
.env-vars {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.env-var-item {
  display: flex;
  align-items: center;
  gap: 8px;
}

.health-check-config {
  margin-top: 16px;
  padding: 16px;
  background: #f9fafb;
  border-radius: 8px;
}

/* 确认部署样式 */
.deployment-summary {
  max-width: 800px;
}

.description-section,
.tags-section {
  margin-top: 24px;
}

.description-section h4,
.tags-section h4 {
  margin: 0 0 12px 0;
  font-size: 16px;
  font-weight: 600;
  color: #1f2937;
}

.description-section p {
  margin: 0;
  color: #6b7280;
  line-height: 1.6;
}

/* 操作按钮 */
.form-actions {
  display: flex;
  gap: 12px;
  justify-content: flex-end;
  margin-top: 32px;
  padding-top: 24px;
  border-top: 1px solid #e5e7eb;
}

@media (max-width: 768px) {
  .model-grid,
  .server-grid,
  .gpu-grid {
    grid-template-columns: 1fr;
  }
  
  .model-details,
  .server-specs,
  .gpu-specs {
    grid-template-columns: 1fr;
  }
  
  .env-var-item {
    flex-direction: column;
    align-items: stretch;
  }
  
  .form-actions {
    flex-direction: column;
  }
}
</style>