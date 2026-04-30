<template>
  <div class="training-create-page">
    <div class="page-header">
      <div class="header-left">
        <el-button link @click="router.back()">
          <el-icon><Back /></el-icon> 返回
        </el-button>
        <h1 class="page-title">{{ isEdit ? '编辑微调任务' : '创建微调任务' }}</h1>
      </div>
    </div>

    <el-card class="form-card" shadow="never">
      <el-form
        ref="formRef"
        :model="formData"
        :rules="rules"
        label-width="140px"
        label-position="top"
      >

        <el-divider content-position="left">服务器配置</el-divider>

        <el-row :gutter="20">
          <el-col :span="24">
            <el-form-item label="选择服务器" prop="selectedServerId">
              <el-select
                v-model="selectedServerId"
                filterable
                placeholder="从服务器资源池选择"
                @change="handleServerSelect"
                class="w-full"
                clearable
              >
                <el-option
                  v-for="server in availableServers"
                  :key="server.id"
                  :label="`${server.name} (${server.ip_address})`"
                  :value="server.id"
                >
                  <span>{{ server.name }}</span>
                  <span style="color: #999; font-size: 12px; margin-left: 8px;">
                    {{ server.ip_address }} | {{ server.gpu_count || 0 }} GPU
                  </span>
                </el-option>
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>

        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="服务器 IP" prop="server_ip">
              <el-input v-model="formData.server_ip" placeholder="GPU 服务器 IP 地址" :disabled="!!selectedServerId" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="SSH 端口" prop="ssh_port">
              <el-input-number v-model="formData.ssh_port" :min="1" :max="65535" class="w-full" :disabled="!!selectedServerId" />
            </el-form-item>
          </el-col>
        </el-row>

        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="SSH 用户名" prop="ssh_username">
              <el-input v-model="formData.ssh_username" placeholder="SSH 用户名" :disabled="!!selectedServerId" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="SSH 密码" prop="ssh_password">
              <el-input v-model="formData.ssh_password" type="password" placeholder="SSH 密码" show-password />
            </el-form-item>
          </el-col>
        </el-row>

        <el-divider content-position="left">基本信息</el-divider>

        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="任务名称" prop="job_name">
              <el-input v-model="formData.job_name" placeholder="请输入微调任务名称" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="基础模型" prop="base_model_name">
              <el-select
                v-model="formData.base_model_name"
                filterable
                allow-create
                default-first-option
                placeholder="选择或输入基础模型"
                class="w-full"
                @change="handleBaseModelChange"
              >
                <el-option
                  v-for="model in baseModelOptions"
                  :key="model.value"
                  :label="model.label"
                  :value="model.value"
                />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>

        <el-row :gutter="20">
          <el-col :span="8">
            <el-form-item label="模型类型 (model_type)" prop="model_type">
              <el-input v-model="formData.model_type" placeholder="如: qwen2" />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="模板类型 (template)" prop="template">
              <el-input v-model="formData.template" placeholder="如: qwen2_5" />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="微调方法" prop="method">
              <el-select v-model="formData.method" placeholder="请选择微调方法" class="w-full">
                <el-option label="LoRA" value="lora" />
                <el-option label="QLoRA" value="qlora" />
                <el-option label="全量微调" value="full" />
                <el-option label="Adaptor" value="adaptor" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>

        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="微调后模型名称" prop="fine_tuned_model_name">
              <el-input v-model="formData.fine_tuned_model_name" placeholder="微调后的模型名称（可选）" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="数据集名称" prop="dataset_name">
              <el-input v-model="formData.dataset_name" placeholder="请输入数据集名称" />
            </el-form-item>
          </el-col>
        </el-row>

        <el-row :gutter="20">
          <el-col :span="24">
            <el-form-item label="数据集来源" prop="datasetSource">
              <el-radio-group v-model="datasetSource" @change="handleDatasetSourceChange">
                <el-radio value="server">服务器已有</el-radio>
                <el-radio value="upload">本地上传</el-radio>
                <el-radio value="manage">数据集管理</el-radio>
              </el-radio-group>
            </el-form-item>
          </el-col>
        </el-row>

        <el-row :gutter="20" v-if="datasetSource === 'server'">
          <el-col :span="24">
            <el-form-item label="数据集路径" prop="dataset_path">
              <el-input v-model="formData.dataset_path" placeholder="如: /data/modelscope/ms-swift/dataset/train.jsonl" />
            </el-form-item>
          </el-col>
        </el-row>

        <el-row :gutter="20" v-if="datasetSource === 'upload'">
          <el-col :span="24">
            <el-form-item label="上传本地数据集">
              <el-upload
                ref="uploadRef"
                :auto-upload="false"
                :limit="1"
                :on-change="handleFileChange"
                :file-list="fileList"
                accept=".json,.jsonl,.txt,.csv"
              >
                <template #trigger>
                  <el-button type="primary">选择文件</el-button>
                </template>
                <template #tip>
                  <div class="el-upload__tip">支持 .json, .jsonl, .txt, .csv 格式文件</div>
                </template>
              </el-upload>
            </el-form-item>
          </el-col>
        </el-row>

        <el-row :gutter="20" v-if="datasetSource === 'manage'">
          <el-col :span="24">
            <el-form-item label="选择数据集">
              <el-select
                v-model="selectedDatasetId"
                filterable
                placeholder="搜索并选择数据集"
                @change="handleDatasetSelect"
                class="w-full"
              >
                <el-option
                  v-for="ds in availableDatasets"
                  :key="ds.id"
                  :label="ds.name"
                  :value="ds.id"
                >
                  <span>{{ ds.name }}</span>
                  <span style="color: #999; font-size: 12px; margin-left: 8px;">
                    {{ ds.type || '未知类型' }}
                  </span>
                </el-option>
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>

        <el-row :gutter="20" v-if="datasetSource === 'upload' || datasetSource === 'manage'">
          <el-col :span="24">
            <el-form-item label="服务器配置（用于上传）">
              <el-alert
                v-if="!formData.server_ip"
                type="warning"
                :closable="false"
                show-icon
              >
                请先填写"服务器配置"中的服务器IP、SSH端口、用户名和密码
              </el-alert>
              <template v-else>
                <el-tag type="success" size="small">
                  将上传到: {{ formData.server_ip }}:{{ formData.ssh_port || 22 }}
                </el-tag>
              </template>
            </el-form-item>
          </el-col>
        </el-row>

        <el-divider content-position="left">训练参数</el-divider>

        <el-row :gutter="20">
          <el-col :span="8">
            <el-form-item label="训练轮次 (Epochs)" prop="total_epochs">
              <el-input-number v-model="formData.total_epochs" :min="1" :max="100" class="w-full" />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="学习率" prop="learning_rate">
              <el-input-number v-model="formData.learning_rate" :min="0" :max="1" :precision="6" :step="0.0001" class="w-full" />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="最大序列长度" prop="max_length">
              <el-input-number v-model="formData.max_length" :min="64" :max="32768" :step="128" class="w-full" />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="验证集拆分比例" prop="split_dataset_ratio">
              <el-input-number v-model="formData.split_dataset_ratio" :min="0" :max="1" :precision="2" :step="0.01" class="w-full" />
            </el-form-item>
          </el-col>
        </el-row>

        <el-row :gutter="20">
          <el-col :span="8">
            <el-form-item label="梯度累积步数" prop="gradient_accumulation_steps">
              <el-input-number v-model="formData.gradient_accumulation_steps" :min="1" :max="64" class="w-full" />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="评估步数 (eval_steps)" prop="eval_steps">
              <el-input-number v-model="formData.eval_steps" :min="1" :step="100" class="w-full" />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="LoRA Rank（秩）" prop="lora_rank">
              <el-input-number v-model="formData.lora_rank" :min="1" :max="256" :step="1" class="w-full" />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="LoRA Alpha（缩放因子）" prop="lora_alpha">
              <el-input-number v-model="formData.lora_alpha" :min="1" :max="512" :step="1" class="w-full" />
            </el-form-item>
          </el-col>
        </el-row>

        <el-row :gutter="20">
          <el-col :span="8">
            <el-form-item label="Conda 环境" prop="conda_env">
              <el-input v-model="formData.conda_env" placeholder="如: msswift" />
            </el-form-item>
          </el-col>
        </el-row>

        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="任务类型 (task_type)" prop="task_type">
              <el-select v-model="formData.task_type" placeholder="选择任务类型" class="w-full" clearable>
                <el-option label="Causal LM (causal_lm)" value="causal_lm" />
                <el-option label="序列分类 (seq_cls)" value="seq_cls" />
                <el-option label="Embedding (embedding)" value="embedding" />
                <el-option label="Reranker (reranker)" value="reranker" />
                <el-option label="生成式Reranker (generative_reranker)" value="generative_reranker" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="标签数量 (num_labels)" prop="num_labels">
              <el-input-number v-model="formData.num_labels" :min="2" :max="1000" class="w-full" placeholder="分类任务标签数" />
            </el-form-item>
          </el-col>
        </el-row>

        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="模型输出路径" prop="output_path">
              <el-input v-model="formData.output_path" placeholder="输出路径（可选）" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="数据类型" prop="torch_dtype">
              <el-select v-model="formData.torch_dtype" placeholder="选择数据类型" class="w-full">
                <el-option label="bfloat16 (推荐)" value="bfloat16" />
                <el-option label="float16" value="float16" />
                <el-option label="float32" value="float32" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="GPU 选择 (CUDA_VISIBLE_DEVICES)" prop="cuda_devices">
              <el-input v-model="formData.cuda_devices" placeholder="如: 0,1,2,3 或留空使用所有GPU" />
            </el-form-item>
          </el-col>
        </el-row>

        <el-row :gutter="20">
          <el-col :span="24">
            <el-form-item label="系统提示词 (System Prompt)" prop="system_prompt">
              <el-input
                v-model="formData.system_prompt"
                type="textarea"
                :rows="2"
                placeholder='如: 你是一个文本分析专家。'
              />
            </el-form-item>
          </el-col>
        </el-row>

        <el-row :gutter="20">
          <el-col :span="24">
            <el-form-item label="自定义训练参数 (JSON)" prop="training_params">
              <el-input
                v-model="formData.training_params"
                type="textarea"
                :rows="3"
                placeholder='如: {"learning_rate": 0.0001, "batch_size": 4}'
              />
            </el-form-item>
          </el-col>
        </el-row>

        <!-- <el-divider content-position="left">备注</el-divider>

        <el-row :gutter="20">
          <el-col :span="24">
            <el-form-item label="备注信息" prop="remarks">
              <el-input
                v-model="formData.remarks"
                type="textarea"
                :rows="2"
                placeholder="其他备注信息（可选）"
              />
            </el-form-item>
          </el-col>
        </el-row> -->

        <div class="form-actions">
          <el-button @click="router.back()">取消</el-button>
          <el-button type="primary" :loading="submitting" @click="submitForm">
            创建任务
          </el-button>
        </div>
      </el-form>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Back } from '@element-plus/icons-vue'
import { fineTuningApi, type FineTuningJobCreate, FineTuningMethod, type FineTuningJob, type FineTuningJobUpdate } from '@/api/training'
import { getDatasets, type Dataset } from '@/api/datasets'
import { getServers, type ServerResponse, getServerWithPassword } from '@/api/servers'
import { getToken } from '@/utils/auth'

const router = useRouter()
const route = useRoute()
const formRef = ref()
const submitting = ref(false)

const isEdit = computed(() => !!route.params.id)
const jobId = computed(() => route.params.id as string | undefined)

const datasetSource = ref<'server' | 'upload' | 'manage'>('server')
const uploadRef = ref()
const fileList = ref<any[]>([])
const selectedFile = ref<File | null>(null)
const selectedDatasetId = ref<number | null>(null)
const availableDatasets = ref<Dataset[]>([])
const uploading = ref(false)

const selectedServerId = ref<number | null>(null)
const availableServers = ref<ServerResponse[]>([])

const loadAvailableServers = async () => {
  try {
    const response = await getServers({ page: 1, size: 100 })
    availableServers.value = response.items || []
  } catch (error) {
    console.error('加载服务器列表失败:', error)
  }
}

const handleServerSelect = async (serverId: number | null) => {
  if (!serverId) {
    formData.server_ip = ''
    formData.ssh_port = 22
    formData.ssh_username = ''
    formData.ssh_password = ''
    return
  }

  try {
    const serverWithPassword = await getServerWithPassword(serverId)
    const server = serverWithPassword.data || serverWithPassword
    formData.server_ip = server.ip_address
    formData.ssh_port = server.ssh_port
    formData.ssh_username = server.ssh_username
    formData.ssh_password = server.ssh_password || ''
  } catch (error) {
    console.error('获取服务器详情失败:', error)
    ElMessage.error('获取服务器详情失败')
  }
}

const handleDatasetSourceChange = (value: 'server' | 'upload' | 'manage') => {
  if (value === 'manage') {
    loadAvailableDatasets()
  }
  if (value === 'server') {
    formData.dataset_path = ''
  }
}

const loadAvailableDatasets = async () => {
  try {
    const response = await getDatasets({ page: 1, size: 100 })
    availableDatasets.value = response.items.filter(ds => ds.storage_path)
  } catch (error) {
    console.error('加载数据集列表失败:', error)
    ElMessage.error('加载数据集列表失败')
  }
}

const handleFileChange = (file: any) => {
  selectedFile.value = file.raw
  fileList.value = [file]
  if (file.name) {
    formData.dataset_path = file.name
  }
}

const handleDatasetSelect = async (datasetId: number) => {
  selectedDatasetId.value = datasetId
  const dataset = availableDatasets.value.find(ds => ds.id === datasetId)
  if (dataset) {
    formData.dataset_name = dataset.name
  }
}

const uploadDatasetToServer = async (): Promise<string | null> => {
  if (!formData.server_ip || !formData.ssh_username || !formData.ssh_password) {
    ElMessage.error('请先填写服务器配置（IP、用户名、密码）')
    return null
  }

  uploading.value = true
  try {
    let datasetId: number
    let filename: string

    if (datasetSource.value === 'upload') {
      if (!selectedFile.value) {
        ElMessage.error('请先选择要上传的文件')
        return null
      }

      const formDataToSend = new FormData()
      formDataToSend.append('file', selectedFile.value)
      formDataToSend.append('server_ip', formData.server_ip)
      formDataToSend.append('ssh_port', String(formData.ssh_port || 22))
      formDataToSend.append('ssh_username', formData.ssh_username)
      formDataToSend.append('ssh_password', formData.ssh_password)

      const response = await fetch('/api/v1/fine-tuning/upload-dataset-file', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${getToken()}`
        },
        body: formDataToSend
      })

      if (!response.ok) {
        throw new Error('上传失败')
      }

      const result = await response.json()
      return result.dataset_path
    } else if (datasetSource.value === 'manage') {
      if (!selectedDatasetId.value) {
        ElMessage.error('请先选择数据集')
        return null
      }

      const result = await fineTuningApi.uploadDataset({
        server_ip: formData.server_ip,
        ssh_port: formData.ssh_port || 22,
        ssh_username: formData.ssh_username,
        ssh_password: formData.ssh_password,
        dataset_id: selectedDatasetId.value
      })

      if (result.success) {
        return result.dataset_path
      } else {
        throw new Error('上传失败')
      }
    }

    return null
  } catch (error: any) {
    console.error('上传数据集失败:', error)
    ElMessage.error(error.message || '上传数据集失败')
    return null
  } finally {
    uploading.value = false
  }
}

const baseModelOptions = [
  { label: 'Qwen/Qwen2.5-0.5B-Instruct', value: 'Qwen/Qwen2.5-0.5B-Instruct', model_type: 'qwen2', template: 'qwen2_5' },
  { label: 'Qwen/Qwen2.5-1.5B-Instruct', value: 'Qwen/Qwen2.5-1.5B-Instruct', model_type: 'qwen2', template: 'qwen2_5' },
  { label: 'Qwen/Qwen2.5-3B-Instruct', value: 'Qwen/Qwen2.5-3B-Instruct', model_type: 'qwen2', template: 'qwen2_5' },
  { label: 'Qwen/Qwen2.5-7B-Instruct', value: 'Qwen/Qwen2.5-7B-Instruct', model_type: 'qwen2', template: 'qwen2_5' },
  { label: 'Qwen/Qwen2.5-14B-Instruct', value: 'Qwen/Qwen2.5-14B-Instruct', model_type: 'qwen2', template: 'qwen2_5' },
  { label: 'Qwen/Qwen2.5-32B-Instruct', value: 'Qwen/Qwen2.5-32B-Instruct', model_type: 'qwen2', template: 'qwen2_5' },
  { label: 'Qwen/Qwen2.5-72B-Instruct', value: 'Qwen/Qwen2.5-72B-Instruct', model_type: 'qwen2', template: 'qwen2_5' },
  { label: 'Qwen/Qwen2-7B-Instruct', value: 'Qwen/Qwen2-7B-Instruct', model_type: 'qwen2', template: 'qwen2' },
  { label: 'Qwen/Qwen2-72B-Instruct', value: 'Qwen/Qwen2-72B-Instruct', model_type: 'qwen2', template: 'qwen2' },
  { label: 'Qwen/Qwen2-110B-Instruct', value: 'Qwen/Qwen2-110B-Instruct', model_type: 'qwen2', template: 'qwen2' },
  { label: 'Qwen/Qwen2.5-0.5B', value: 'Qwen/Qwen2.5-0.5B', model_type: 'qwen2', template: 'qwen2_5' },
  { label: 'Qwen/Qwen2.5-1.5B', value: 'Qwen/Qwen2.5-1.5B', model_type: 'qwen2', template: 'qwen2_5' },
  { label: 'Qwen/Qwen2.5-3B', value: 'Qwen/Qwen2.5-3B', model_type: 'qwen2', template: 'qwen2_5' },
  { label: 'Qwen/Qwen2.5-7B', value: 'Qwen/Qwen2.5-7B', model_type: 'qwen2', template: 'qwen2_5' },
  { label: 'Qwen/Qwen2.5-14B', value: 'Qwen/Qwen2.5-14B', model_type: 'qwen2', template: 'qwen2_5' },
  { label: 'Qwen/Qwen2.5-32B', value: 'Qwen/Qwen2.5-32B', model_type: 'qwen2', template: 'qwen2_5' },
  { label: 'Qwen/Qwen2.5-72B', value: 'Qwen/Qwen2.5-72B', model_type: 'qwen2', template: 'qwen2_5' },
  { label: 'Llama-2-7b-hf', value: 'Llama-2-7b-hf', model_type: 'llama2', template: 'llama2' },
  { label: 'Llama-2-13b-hf', value: 'Llama-2-13b-hf', model_type: 'llama2', template: 'llama2' },
  { label: 'Llama-2-70b-hf', value: 'Llama-2-70b-hf', model_type: 'llama2', template: 'llama2' },
  { label: 'Llama-3-8B', value: 'Llama-3-8B', model_type: 'llama3', template: 'llama3' },
  { label: 'Llama-3-70B', value: 'Llama-3-70B', model_type: 'llama3', template: 'llama3' },
  { label: 'Llama-3.1-8B', value: 'Llama-3.1-8B', model_type: 'llama3', template: 'llama3' },
  { label: 'Llama-3.1-70B', value: 'Llama-3.1-70B', model_type: 'llama3', template: 'llama3' },
  { label: 'Yi-6B', value: 'Yi-6B', model_type: 'yi', template: 'yi' },
  { label: 'Yi-34B', value: 'Yi-34B', model_type: 'yi', template: 'yi' },
  { label: 'InternLM2-7B', value: 'InternLM2-7B', model_type: 'internlm2', template: 'internlm2' },
  { label: 'InternLM2-20B', value: 'InternLM2-20B', model_type: 'internlm2', template: 'internlm2' },
  { label: 'InternLM2.5-7B', value: 'InternLM2.5-7B', model_type: 'internlm2', template: 'internlm2' },
  { label: 'InternLM2.5-20B', value: 'InternLM2.5-20B', model_type: 'internlm2', template: 'internlm2' },
  { label: 'chatglm3-6b', value: 'chatglm3-6b', model_type: 'glm4', template: 'glm4' },
  { label: 'chatglm4-9b', value: 'chatglm4-9b', model_type: 'glm4', template: 'glm4' },
  { label: 'Baichuan2-7B', value: 'Baichuan2-7B', model_type: 'baichuan2', template: 'baichuan2' },
  { label: 'Baichuan2-13B', value: 'Baichuan2-13B', model_type: 'baichuan2', template: 'baichuan2' },
  { label: 'DeepSeek-7B', value: 'DeepSeek-7B', model_type: 'deepseek', template: 'deepseek' },
  { label: 'DeepSeek-67B', value: 'DeepSeek-67B', model_type: 'deepseek', template: 'deepseek' },
  { label: 'DeepSeek-V2-16B', value: 'DeepSeek-V2-16B', model_type: 'deepseek2', template: 'deepseek2' },
  { label: 'DeepSeek-V2.5-14B', value: 'DeepSeek-V2.5-14B', model_type: 'deepseek2', template: 'deepseek2' },
  { label: 'ModernBERT-base', value: 'ModernBERT-base', model_type: 'modernbert', template: 'modernbert' },
  { label: 'ModernBERT-large', value: 'ModernBERT-large', model_type: 'modernbert', template: 'modernbert' },
]

const handleBaseModelChange = (modelValue: string) => {
  const selectedModel = baseModelOptions.find(m => m.value === modelValue)
  if (selectedModel) {
    formData.model_type = selectedModel.model_type
    formData.template = selectedModel.template
  }
}

const formData = reactive<FineTuningJobCreate & {
  ssh_port: number
  conda_env: string
  total_epochs: number
}>({
  job_name: '',
  base_model_name: '',
  model_type: '',
  template: '',
  fine_tuned_model_name: '',
  method: FineTuningMethod.QLORA,
  dataset_name: '',
  dataset_path: '',
  system_prompt: '',
  training_params: '',
  conda_env: 'msswift',
  total_epochs: 3,
  output_path: '',
  remarks: '',
  server_ip: '',
  ssh_port: 22,
  ssh_username: '',
  ssh_password: '',
  torch_dtype: 'bfloat16',
  max_length: 1024,
  split_dataset_ratio: 0,
  gradient_accumulation_steps: 16,
  learning_rate: 0.0001,
  eval_steps: 500,
  lora_rank: 8,
  lora_alpha: 32,
  use_chat_template: true,
  task_type: '',
  num_labels: undefined,
  cuda_devices: ''
})

onMounted(async () => {
  loadAvailableServers()

  if (isEdit.value && jobId.value) {
    try {
      const job = await fineTuningApi.getJob(parseInt(jobId.value))
      if (job) {
        Object.assign(formData, {
          job_name: job.job_name,
          base_model_name: job.base_model_name,
          model_type: job.model_type || '',
          template: job.template || '',
          fine_tuned_model_name: job.fine_tuned_model_name || '',
          method: job.method,
          dataset_name: job.dataset_name,
          dataset_path: job.dataset_path || '',
          system_prompt: job.system_prompt || '',
          training_params: job.training_params || '',
          conda_env: job.conda_env || 'msswift',
          total_epochs: job.total_epochs,
          output_path: job.output_path || '',
          remarks: job.remarks || '',
          server_ip: job.server_ip || '',
          ssh_port: job.ssh_port || 22,
          ssh_username: job.ssh_username || '',
          ssh_password: job.ssh_password || '',
          torch_dtype: job.torch_dtype || 'bfloat16',
          max_length: job.max_length || 1024,
          split_dataset_ratio: job.split_dataset_ratio ?? 0,
          gradient_accumulation_steps: job.gradient_accumulation_steps || 16,
          learning_rate: job.learning_rate || 0.0001,
          eval_steps: job.eval_steps || 500,
          lora_rank: job.lora_rank || 8,
          lora_alpha: job.lora_alpha || 32,
          use_chat_template: job.use_chat_template ?? true,
          task_type: job.task_type || '',
          num_labels: job.num_labels,
          cuda_devices: job.cuda_devices || ''
        })
      }
    } catch (error) {
      console.error('加载任务详情失败:', error)
      ElMessage.error('加载任务详情失败')
    }
  }
})

const rules = {
  job_name: [
    { required: true, message: '请输入任务名称', trigger: 'blur' }
  ],
  base_model_name: [
    { required: true, message: '请选择或输入基础模型', trigger: 'change' }
  ],
  method: [
    { required: true, message: '请选择微调方法', trigger: 'change' }
  ],
  dataset_name: [
    { required: true, message: '请输入数据集名称', trigger: 'blur' }
  ],
  server_ip: [
    { required: true, message: '请输入服务器 IP', trigger: 'blur' }
  ],
  ssh_username: [
    { required: true, message: '请输入 SSH 用户名', trigger: 'blur' }
  ],
  ssh_password: [
    { required: true, message: '请输入 SSH 密码', trigger: 'blur' }
  ]
}

const submitForm = async () => {
  try {
    await formRef.value.validate()
  } catch {
    return
  }

  if (datasetSource.value === 'upload' || datasetSource.value === 'manage') {
    if (!formData.server_ip || !formData.ssh_username || !formData.ssh_password) {
      ElMessage.error('请先填写服务器配置（IP、用户名、密码）')
      return
    }
  }

  if (datasetSource.value === 'server' && !formData.dataset_path) {
    ElMessage.error('请输入数据集路径')
    return
  }

  submitting.value = true
  try {
    if (datasetSource.value !== 'server') {
      const uploadedPath = await uploadDatasetToServer()
      if (!uploadedPath) {
        submitting.value = false
        return
      }
      formData.dataset_path = uploadedPath
    }

    const submitData: FineTuningJobCreate | FineTuningJobUpdate = {
      job_name: formData.job_name,
      base_model_name: formData.base_model_name,
      model_type: formData.model_type || undefined,
      template: formData.template || undefined,
      fine_tuned_model_name: formData.fine_tuned_model_name || undefined,
      method: formData.method,
      dataset_name: formData.dataset_name,
      dataset_path: formData.dataset_path || undefined,
      system_prompt: formData.system_prompt || undefined,
      training_params: formData.training_params || undefined,
      conda_env: formData.conda_env,
      total_epochs: formData.total_epochs,
      output_path: formData.output_path || undefined,
      remarks: formData.remarks || undefined,
      server_ip: formData.server_ip,
      ssh_port: formData.ssh_port,
      ssh_username: formData.ssh_username,
      ssh_password: formData.ssh_password,
      torch_dtype: formData.torch_dtype,
      max_length: formData.max_length,
      split_dataset_ratio: formData.split_dataset_ratio || undefined,
      gradient_accumulation_steps: formData.gradient_accumulation_steps,
      learning_rate: formData.learning_rate,
      eval_steps: formData.eval_steps,
      lora_rank: formData.lora_rank || undefined,
      lora_alpha: formData.lora_alpha || undefined,
      use_chat_template: formData.use_chat_template,
      task_type: formData.task_type || undefined,
      num_labels: formData.num_labels,
      cuda_devices: formData.cuda_devices || undefined
    }

    if (isEdit.value && jobId.value) {
      await fineTuningApi.updateJob(parseInt(jobId.value), submitData)
      ElMessage.success('微调任务更新成功')
    } else {
      await fineTuningApi.createJob(submitData as FineTuningJobCreate)
      ElMessage.success('微调任务创建成功')
    }
    router.push('/training/jobs')
  } catch (error) {
    console.error(isEdit.value ? '更新微调任务失败:' : '创建微调任务失败:', error)
    ElMessage.error(isEdit.value ? '更新失败，请稍后重试' : '创建失败，请稍后重试')
  } finally {
    submitting.value = false
  }
}
</script>

<style lang="scss" scoped>
.training-create-page {
  padding: 20px;

  .page-header {
    margin-bottom: 20px;

    .header-left {
      display: flex;
      align-items: center;
      gap: 16px;

      .page-title {
        margin: 0;
        font-size: 20px;
        font-weight: 600;
      }
    }
  }

  .form-card {
    max-width: 900px;
  }

  .w-full {
    width: 100%;
  }

  .form-actions {
    display: flex;
    justify-content: flex-end;
    gap: 12px;
    margin-top: 24px;
    padding-top: 24px;
    border-top: 1px solid var(--el-border-color);
  }
}
</style>