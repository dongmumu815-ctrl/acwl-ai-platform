<template>
  <div class="training-create-page">
    <div class="page-header">
      <div class="header-left">
        <el-button link @click="router.back()">
          <el-icon><Back /></el-icon> 返回
        </el-button>
        <h1 class="page-title">创建训练任务</h1>
      </div>
    </div>

    <el-card class="wizard-card" shadow="never">
      <el-steps :active="currentStep" finish-status="success" align-center class="wizard-steps">
        <el-step title="基础信息" description="选择模态与框架" />
        <el-step title="数据与参数" description="配置数据集与超参" />
        <el-step title="计算资源" description="分配 GPU 算力" />
        <el-step title="确认并创建" description="核对配置信息" />
      </el-steps>

      <div class="step-content">
        <!-- 步骤 1: 基础信息 -->
        <el-form
          v-show="currentStep === 0"
          ref="step1FormRef"
          :model="formData"
          :rules="step1Rules"
          label-width="120px"
          label-position="top"
          class="wizard-form"
        >
          <el-form-item label="任务名称" prop="name">
            <el-input v-model="formData.name" placeholder="请输入训练任务名称" />
          </el-form-item>
          
          <el-form-item label="任务描述" prop="description">
            <el-input
              v-model="formData.description"
              type="textarea"
              :rows="3"
              placeholder="简要描述本次训练任务的目标"
            />
          </el-form-item>

          <el-row :gutter="20">
            <el-col :span="12">
              <el-form-item label="任务类型" prop="trainingMode">
                <el-radio-group v-model="formData.trainingMode" class="mode-selector">
                  <el-radio-button value="full_training">
                    <div class="radio-content">
                      <el-icon><Cpu /></el-icon>
                      <span>全量训练</span>
                    </div>
                  </el-radio-button>
                  <el-radio-button value="fine_tuning">
                    <div class="radio-content">
                      <el-icon><MagicStick /></el-icon>
                      <span>模型微调</span>
                    </div>
                  </el-radio-button>
                </el-radio-group>
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item label="领域/模态" prop="domain">
                <el-select v-model="formData.domain" placeholder="请选择模态" @change="handleDomainChange">
                  <el-option label="计算机视觉 (CV)" value="cv">
                    <div class="select-option">
                      <el-icon><Picture /></el-icon> 计算机视觉 (CV)
                    </div>
                  </el-option>
                  <el-option label="自然语言处理 (NLP)" value="nlp">
                    <div class="select-option">
                      <el-icon><ChatDotRound /></el-icon> 自然语言处理 (NLP)
                    </div>
                  </el-option>
                  <el-option label="语音处理 (Audio)" value="audio">
                    <div class="select-option">
                      <el-icon><Headset /></el-icon> 语音处理 (Audio)
                    </div>
                  </el-option>
                </el-select>
              </el-form-item>
            </el-col>
          </el-row>

          <el-form-item label="算法/框架" prop="framework">
            <div class="framework-grid">
              <div 
                v-for="fw in availableFrameworks" 
                :key="fw.value"
                class="framework-card"
                :class="{ active: formData.framework === fw.value }"
                @click="formData.framework = fw.value"
              >
                <div class="fw-icon">{{ fw.icon }}</div>
                <div class="fw-info">
                  <h4>{{ fw.label }}</h4>
                  <p>{{ fw.desc }}</p>
                </div>
                <div class="fw-check" v-if="formData.framework === fw.value">
                  <el-icon><Select /></el-icon>
                </div>
              </div>
              <div v-if="availableFrameworks.length === 0" class="empty-frameworks">
                请先选择左侧的“领域/模态”
              </div>
            </div>
          </el-form-item>
        </el-form>

        <!-- 步骤 2: 数据与参数 -->
        <el-form
          v-show="currentStep === 1"
          ref="step2FormRef"
          :model="formData"
          :rules="step2Rules"
          label-width="120px"
          label-position="top"
          class="wizard-form"
        >
          <el-divider content-position="left">选择数据集</el-divider>
          <el-form-item label="训练数据集" prop="datasetId">
            <el-select v-model="formData.datasetId" placeholder="请选择用于训练的数据集" class="w-full">
              <el-option v-for="ds in mockDatasets" :key="ds.id" :label="ds.name" :value="ds.id">
                <span style="float: left">{{ ds.name }}</span>
                <span style="float: right; color: var(--el-text-color-secondary); font-size: 13px">
                  {{ ds.type }}
                </span>
              </el-option>
            </el-select>
          </el-form-item>

          <el-divider content-position="left">基础超参数</el-divider>
          <el-row :gutter="20">
            <el-col :span="8">
              <el-form-item label="Epochs">
                <el-input-number v-model="formData.epochs" :min="1" :max="1000" class="w-full" />
              </el-form-item>
            </el-col>
            <el-col :span="8">
              <el-form-item label="Batch Size">
                <el-select v-model="formData.batchSize" class="w-full">
                  <el-option label="4" :value="4" />
                  <el-option label="8" :value="8" />
                  <el-option label="16" :value="16" />
                  <el-option label="32" :value="32" />
                  <el-option label="64" :value="64" />
                </el-select>
              </el-form-item>
            </el-col>
            <el-col :span="8">
              <el-form-item label="Learning Rate">
                <el-input v-model="formData.learningRate" type="number" step="0.0001" />
              </el-form-item>
            </el-col>
          </el-row>

          <el-divider content-position="left">动态框架参数 ({{ currentFrameworkName }})</el-divider>
          
          <!-- YOLO 参数 -->
          <template v-if="formData.framework === 'yolo'">
            <el-row :gutter="20">
              <el-col :span="8">
                <el-form-item label="输入尺寸 (img_size)">
                  <el-input-number v-model="formData.yoloParams.imgSize" :min="320" :max="1280" :step="32" class="w-full" />
                </el-form-item>
              </el-col>
              <el-col :span="8">
                <el-form-item label="IOU 阈值">
                  <el-slider v-model="formData.yoloParams.iou" :min="0" :max="1" :step="0.01" />
                </el-form-item>
              </el-col>
              <el-col :span="8">
                <el-form-item label="Mosaic 数据增强">
                  <el-switch v-model="formData.yoloParams.mosaic" />
                </el-form-item>
              </el-col>
            </el-row>
          </template>

          <!-- BERT 参数 -->
          <template v-if="formData.framework === 'bert'">
            <el-row :gutter="20">
              <el-col :span="8">
                <el-form-item label="最大序列长度">
                  <el-input-number v-model="formData.bertParams.maxSeqLength" :min="16" :max="512" :step="16" class="w-full" />
                </el-form-item>
              </el-col>
              <el-col :span="8">
                <el-form-item label="Warmup Steps">
                  <el-input-number v-model="formData.bertParams.warmupSteps" :min="0" :step="100" class="w-full" />
                </el-form-item>
              </el-col>
              <el-col :span="8">
                <el-form-item label="Weight Decay">
                  <el-input v-model="formData.bertParams.weightDecay" type="number" step="0.01" />
                </el-form-item>
              </el-col>
            </el-row>
          </template>

          <!-- LLaMA 参数 -->
          <template v-if="formData.framework === 'llm'">
            <el-row :gutter="20">
              <el-col :span="8">
                <el-form-item label="LoRA Rank (r)">
                  <el-select v-model="formData.llmParams.loraRank" class="w-full">
                    <el-option label="8" :value="8" />
                    <el-option label="16" :value="16" />
                    <el-option label="32" :value="32" />
                    <el-option label="64" :value="64" />
                  </el-select>
                </el-form-item>
              </el-col>
              <el-col :span="8">
                <el-form-item label="LoRA Alpha">
                  <el-input-number v-model="formData.llmParams.loraAlpha" :min="16" :max="128" :step="16" class="w-full" />
                </el-form-item>
              </el-col>
              <el-col :span="8">
                <el-form-item label="混合精度 (FP16)">
                  <el-switch v-model="formData.llmParams.fp16" />
                </el-form-item>
              </el-col>
            </el-row>
          </template>
        </el-form>

        <!-- 步骤 3: 计算资源 -->
        <el-form
          v-show="currentStep === 2"
          ref="step3FormRef"
          :model="formData"
          :rules="step3Rules"
          label-width="120px"
          label-position="top"
          class="wizard-form"
        >
          <el-alert title="系统将根据选择的资源自动进行分布式训练调度" type="info" show-icon class="mb-4" />
          
          <el-form-item label="计算集群 / 节点" prop="nodeId">
            <el-select v-model="formData.nodeId" placeholder="选择执行训练的计算节点" class="w-full">
              <el-option label="默认集群 (Auto-Scaling)" value="auto" />
              <el-option label="GPU-Cluster-A (A100 * 8)" value="cluster-a" />
              <el-option label="GPU-Cluster-B (V100 * 4)" value="cluster-b" />
            </el-select>
          </el-form-item>

          <el-form-item label="GPU 分配数量" prop="gpuCount">
            <el-slider 
              v-model="formData.gpuCount" 
              :min="1" 
              :max="8" 
              show-stops 
              :marks="{ 1: '1卡', 2: '2卡', 4: '4卡', 8: '8卡' }" 
            />
          </el-form-item>
        </el-form>

        <!-- 步骤 4: 确认 -->
        <div v-show="currentStep === 3" class="confirm-section wizard-form">
          <el-descriptions title="基础信息" :column="2" border class="mb-4">
            <el-descriptions-item label="任务名称">{{ formData.name }}</el-descriptions-item>
            <el-descriptions-item label="任务类型">
              <el-tag size="small">{{ formData.trainingMode === 'full_training' ? '全量训练' : '模型微调' }}</el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="模态领域">{{ formatDomain(formData.domain) }}</el-descriptions-item>
            <el-descriptions-item label="算法框架">{{ currentFrameworkName }}</el-descriptions-item>
          </el-descriptions>

          <el-descriptions title="超参数与资源" :column="3" border>
            <el-descriptions-item label="Epochs">{{ formData.epochs }}</el-descriptions-item>
            <el-descriptions-item label="Batch Size">{{ formData.batchSize }}</el-descriptions-item>
            <el-descriptions-item label="Learning Rate">{{ formData.learningRate }}</el-descriptions-item>
            <el-descriptions-item label="GPU 节点">{{ formData.nodeId }}</el-descriptions-item>
            <el-descriptions-item label="GPU 数量">{{ formData.gpuCount }} 卡</el-descriptions-item>
          </el-descriptions>
        </div>
      </div>

      <div class="wizard-actions">
        <el-button v-if="currentStep > 0" @click="prevStep">上一步</el-button>
        <el-button v-if="currentStep < 3" type="primary" @click="nextStep">下一步</el-button>
        <el-button v-if="currentStep === 3" type="success" :loading="submitting" @click="submitTraining">
          确认创建并启动
        </el-button>
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import {
  Back,
  Cpu,
  MagicStick,
  Picture,
  ChatDotRound,
  Headset,
  Select
} from '@element-plus/icons-vue'

const router = useRouter()
const currentStep = ref(0)
const submitting = ref(false)

const step1FormRef = ref()
const step2FormRef = ref()
const step3FormRef = ref()

// 框架配置数据
const frameworkMap: Record<string, any[]> = {
  cv: [
    { value: 'yolo', label: 'YOLO 系列', desc: '用于目标检测、图像分割', icon: '🎯' },
    { value: 'resnet', label: 'ResNet', desc: '经典的图像分类网络', icon: '🖼️' },
  ],
  nlp: [
    { value: 'bert', label: 'BERT 系列', desc: '适合文本分类、NER', icon: '📖' },
    { value: 'llm', label: 'LLaMA / Qwen', desc: '大语言模型指令微调', icon: '🧠' },
  ],
  audio: [
    { value: 'whisper', label: 'Whisper', desc: '强大的语音识别模型', icon: '🎙️' }
  ]
}

// 模拟数据集
const mockDatasets = [
  { id: 'd1', name: 'COCO 2017 检测集', type: 'CV' },
  { id: 'd2', name: '中文情感分析语料', type: 'NLP' },
  { id: 'd3', name: 'Alpaca 指令微调集', type: 'NLP' },
]

// 表单数据
const formData = reactive({
  // 基础信息
  name: '',
  description: '',
  trainingMode: 'fine_tuning',
  domain: '',
  framework: '',
  
  // 数据与参数
  datasetId: '',
  epochs: 100,
  batchSize: 16,
  learningRate: 0.001,
  
  // 动态参数
  yoloParams: {
    imgSize: 640,
    iou: 0.45,
    mosaic: true
  },
  bertParams: {
    maxSeqLength: 256,
    warmupSteps: 500,
    weightDecay: 0.01
  },
  llmParams: {
    loraRank: 16,
    loraAlpha: 32,
    fp16: true
  },

  // 资源
  nodeId: 'auto',
  gpuCount: 1
})

// 计算属性
const availableFrameworks = computed(() => {
  return formData.domain ? frameworkMap[formData.domain] || [] : []
})

const currentFrameworkName = computed(() => {
  const fw = availableFrameworks.value.find(f => f.value === formData.framework)
  return fw ? fw.label : formData.framework
})

const formatDomain = (d: string) => {
  const map: Record<string, string> = { cv: '计算机视觉', nlp: '自然语言处理', audio: '语音处理' }
  return map[d] || d
}

// 验证规则
const step1Rules = {
  name: [{ required: true, message: '请输入任务名称', trigger: 'blur' }],
  domain: [{ required: true, message: '请选择模态', trigger: 'change' }],
  framework: [{ required: true, message: '请选择算法框架', trigger: 'change' }]
}

const step2Rules = {
  datasetId: [{ required: true, message: '请选择数据集', trigger: 'change' }]
}

const step3Rules = {
  nodeId: [{ required: true, message: '请选择计算节点', trigger: 'change' }]
}

// 方法
const handleDomainChange = () => {
  formData.framework = '' // 清空框架选择
}

const validateCurrentStep = async () => {
  try {
    if (currentStep.value === 0) {
      return await step1FormRef.value?.validate()
    } else if (currentStep.value === 1) {
      return await step2FormRef.value?.validate()
    } else if (currentStep.value === 2) {
      return await step3FormRef.value?.validate()
    }
    return true
  } catch (error) {
    return false
  }
}

const nextStep = async () => {
  const isValid = await validateCurrentStep()
  if (isValid) {
    currentStep.value++
  }
}

const prevStep = () => {
  if (currentStep.value > 0) {
    currentStep.value--
  }
}

const submitTraining = () => {
  submitting.value = true
  // 模拟提交 API
  setTimeout(() => {
    ElMessage.success('训练任务创建成功并已启动调度')
    submitting.value = false
    router.push('/training/jobs')
  }, 1500)
}
</script>

<style scoped lang="scss">
.training-create-page {
  padding: 20px;
}

.page-header {
  margin-bottom: 24px;
  .header-left {
    display: flex;
    align-items: center;
    gap: 16px;
  }
  .page-title {
    margin: 0;
    font-size: 20px;
    font-weight: 600;
  }
}

.wizard-card {
  max-width: 1000px;
  margin: 0 auto;
}

.wizard-steps {
  margin-bottom: 40px;
  padding: 20px 40px;
  background-color: var(--el-fill-color-light);
  border-radius: 8px;
}

.step-content {
  min-height: 400px;
}

.wizard-form {
  max-width: 800px;
  margin: 0 auto;
}

.mode-selector {
  display: flex;
  width: 100%;
  :deep(.el-radio-button) {
    flex: 1;
    .el-radio-button__inner {
      width: 100%;
      padding: 12px 20px;
    }
  }
  .radio-content {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 8px;
    font-size: 15px;
  }
}

.select-option {
  display: flex;
  align-items: center;
  gap: 8px;
}

.framework-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
  gap: 16px;
  width: 100%;
}

.empty-frameworks {
  grid-column: 1 / -1;
  padding: 40px;
  text-align: center;
  color: var(--el-text-color-secondary);
  background-color: var(--el-fill-color-light);
  border-radius: 8px;
  border: 1px dashed var(--el-border-color);
}

.framework-card {
  position: relative;
  display: flex;
  align-items: center;
  padding: 16px;
  border: 1px solid var(--el-border-color);
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.3s;
  background-color: var(--el-bg-color);

  &:hover {
    border-color: var(--el-color-primary-light-3);
    transform: translateY(-2px);
    box-shadow: var(--el-box-shadow-light);
  }

  &.active {
    border-color: var(--el-color-primary);
    background-color: var(--el-color-primary-light-9);
  }

  .fw-icon {
    font-size: 32px;
    margin-right: 16px;
  }

  .fw-info {
    flex: 1;
    h4 {
      margin: 0 0 4px 0;
      font-size: 15px;
      color: var(--el-text-color-primary);
    }
    p {
      margin: 0;
      font-size: 12px;
      color: var(--el-text-color-secondary);
      line-height: 1.4;
    }
  }

  .fw-check {
    position: absolute;
    top: -1px;
    right: -1px;
    width: 24px;
    height: 24px;
    background-color: var(--el-color-primary);
    color: white;
    border-radius: 0 8px 0 8px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 14px;
  }
}

.w-full {
  width: 100%;
}

.wizard-actions {
  margin-top: 40px;
  padding-top: 20px;
  border-top: 1px solid var(--el-border-color-light);
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}

.mb-4 {
  margin-bottom: 16px;
}
</style>
