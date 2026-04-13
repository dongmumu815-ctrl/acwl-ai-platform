<template>
  <el-dialog
    v-model="visible"
    :title="isEdit ? '编辑智能体' : '创建智能体'"
    width="95%"
    :before-close="handleClose"
    :close-on-click-modal="false"
    class="agent-edit-dialog"
  >
    <!-- 三栏布局容器 -->
    <div class="three-column-layout">
      <!-- 左侧：系统提示词编辑器 -->
      <div class="left-panel">
        <div class="panel-header">
          <h3 class="panel-title">系统提示词</h3>
          <div class="panel-actions">
            <el-button size="small" @click="formatPrompt">格式化</el-button>
            <el-button size="small" @click="clearPrompt">清空</el-button>
          </div>
        </div>
        <div class="code-editor-container">
          <codemirror
            v-model="formData.system_prompt"
            :style="{ height: '100%' }"
            :autofocus="true"
            :indent-with-tab="true"
            :tab-size="2"
            :extensions="extensions"
            @ready="handleReady"
            @change="handleChange"
          />
        </div>
        <div class="prompt-tips">
          <el-alert
            title="提示词编写建议"
            type="info"
            :closable="false"
            show-icon
          >
            <template #default>
              <ul class="tips-list">
                <li>明确定义智能体的角色和职责</li>
                <li>设置清晰的行为规范和限制</li>
                <li>使用具体的示例来说明期望的回答风格</li>
                <li>可以使用变量如 {user_input} 来引用用户输入</li>
              </ul>
            </template>
          </el-alert>
        </div>
      </div>

      <!-- 中间：配置面板 -->
      <div class="middle-panel">
        <el-tabs v-model="activeConfigTab" class="config-tabs">
          <!-- 基本信息标签页 -->
          <el-tab-pane label="基本信息" name="basic">
            <el-form
              ref="formRef"
              :model="formData"
              :rules="formRules"
              label-width="100px"
              class="config-form"
            >
              <el-form-item label="智能体名称" prop="name">
                <el-input
                  v-model="formData.name"
                  placeholder="请输入智能体名称"
                  maxlength="100"
                  show-word-limit
                />
              </el-form-item>
              <!-- 暂时注释掉智能体类型选择，默认都是chat模型
              <el-form-item label="类型" prop="agent_type">
                <el-select v-model="formData.agent_type" placeholder="请选择类型" style="width: 100%">
                  <el-option label="自定义" value="CUSTOM" />
                </el-select>
              </el-form-item> -->
              <el-form-item label="描述" prop="description">
                <el-input
                  v-model="formData.description"
                  type="textarea"
                  :rows="3"
                  placeholder="请输入智能体描述"
                  maxlength="500"
                  show-word-limit
                />
              </el-form-item>
              <el-form-item label="类型" prop="agent_type">
                <el-select v-model="formData.agent_type" placeholder="请选择类型" style="width: 100%">
                  <el-option label="自定义" value="CUSTOM" />
                  <el-option label="审读" value="REVIEW" />
                </el-select>
              </el-form-item>
              <!-- 当选择审读类型时显示指令集选择器 -->
              <el-form-item v-if="formData.agent_type === 'REVIEW'" label="关联指令集" prop="instruction_set_id">
                <el-select 
                  v-model="formData.instruction_set_id" 
                  placeholder="请选择指令集" 
                  style="width: 100%"
                  filterable
                  clearable
                >
                  <el-option
                    v-for="instructionSet in availableInstructionSets"
                    :key="instructionSet.id"
                    :label="instructionSet.name"
                    :value="instructionSet.id"
                  >
                    <span>{{ instructionSet.name }}</span>
                    <span style="float: right; color: #8492a6; font-size: 13px">{{ instructionSet.description }}</span>
                  </el-option>
                </el-select>
              </el-form-item>
              <el-row :gutter="20">
                <el-col :span="12">
                  <el-form-item label="状态" prop="status">
                    <el-select v-model="formData.status" placeholder="请选择状态" style="width: 100%">
                      <el-option label="草稿" value="DRAFT" />
                      <el-option label="活跃" value="ACTIVE" />
                      <el-option label="已停用" value="INACTIVE" />
                    </el-select>
                  </el-form-item>
                </el-col>
                <el-col :span="12">
                  <el-form-item label="可见性">
                    <el-switch
                      v-model="formData.is_public"
                      active-text="公开"
                      inactive-text="私有"
                    />
                  </el-form-item>
                </el-col>
              </el-row>
              <el-form-item label="标签">
                <el-select
                  v-model="formData.tags"
                  multiple
                  filterable
                  allow-create
                  placeholder="请输入标签"
                  style="width: 100%"
                >
                  <el-option
                    v-for="tag in commonTags"
                    :key="tag"
                    :label="tag"
                    :value="tag"
                  />
                </el-select>
              </el-form-item>
            </el-form>
          </el-tab-pane>

          <!-- 模型配置标签页 -->
          <el-tab-pane label="模型配置" name="model">
            <el-form
              :model="formData"
              label-width="100px"
              class="config-form"
            >
              <el-form-item label="模型配置" prop="model_service_config_id">
                <el-select
                  v-model="formData.model_service_config_id"
                  placeholder="请选择模型配置"
                  filterable
                  style="width: 100%"
                >
                  <el-option
                    v-for="model in availableModels"
                    :key="model.value"
                    :label="model.label"
                    :value="model.value"
                  />
                </el-select>
              </el-form-item>
              <el-form-item label="记忆功能">
                <el-switch
                  v-model="formData.memory_enabled"
                  active-text="启用"
                  inactive-text="禁用"
                />
              </el-form-item>
              
              <el-divider content-position="left">模型参数</el-divider>
              
              <el-row :gutter="16">
                <el-col :span="12">
                  <el-form-item label="温度">
                    <el-input-number
                      v-model="formData.model_config.temperature"
                      :min="0"
                      :max="2"
                      :step="0.1"
                      :precision="1"
                      placeholder="0.7"
                      style="width: 100%"
                    />
                  </el-form-item>
                </el-col>
                <el-col :span="12">
                  <el-form-item label="最大Token数">
                    <el-input-number
                      v-model="formData.model_config.max_tokens"
                      :min="1"
                      :max="32000"
                      placeholder="2048"
                      style="width: 100%"
                    />
                  </el-form-item>
                </el-col>
                <!-- <el-col :span="12">
                  <el-form-item label="Top-p">
                    <el-input-number
                      v-model="formData.model_config.top_p"
                      :min="0"
                      :max="1"
                      :step="0.1"
                      :precision="1"
                      placeholder="0.9"
                      style="width: 100%"
                    />
                  </el-form-item>
                </el-col> -->
                <!-- <el-col :span="12">
                  <el-form-item label="频率惩罚">
                    <el-input-number
                      v-model="formData.model_config.frequency_penalty"
                      :min="-2"
                      :max="2"
                      :step="0.1"
                      :precision="1"
                      placeholder="0"
                      style="width: 100%"
                    />
                  </el-form-item>
                </el-col>
                <el-col :span="12">
                  <el-form-item label="存在惩罚">
                    <el-input-number
                      v-model="formData.model_config.presence_penalty"
                      :min="-2"
                      :max="2"
                      :step="0.1"
                      :precision="1"
                      placeholder="0"
                      style="width: 100%"
                    />
                  </el-form-item>
                </el-col> -->
                <!-- <el-col :span="12">
                  <el-form-item label="Top-k">
                    <el-input-number
                      v-model="formData.model_config.top_k"
                      :min="1"
                      :max="100"
                      placeholder="40"
                      style="width: 100%"
                    />
                  </el-form-item>
                </el-col> -->
              </el-row>
            </el-form>
          </el-tab-pane>

          <!-- 工具配置标签页 -->
          <el-tab-pane label="工具配置" name="tools">
            <el-form
              :model="formData"
              label-width="100px"
              class="config-form"
            >
              <el-form-item label="可用工具">
                <el-select
                  v-model="formData.tools"
                  multiple
                  placeholder="请选择工具"
                  :loading="loadingTools"
                  style="width: 100%"
                >
                  <el-option
                    v-for="tool in availableTools"
                    :key="tool.value"
                    :label="tool.label"
                    :value="tool.value"
                  >
                    <span style="float: left">{{ tool.label }}</span>
                    <span style="float: right; color: #8492a6; font-size: 13px">
                      {{ tool.description }}
                    </span>
                  </el-option>
                </el-select>
              </el-form-item>
              
              <!-- 工具参数配置 -->
              <div v-if="formData.tools && formData.tools.length > 0">
                <el-divider content-position="left">工具参数配置</el-divider>
                <el-form-item label="工具配置">
                  <el-input
                    v-model="toolConfigText"
                    type="textarea"
                    :rows="6"
                    placeholder="请输入工具配置（JSON格式）"
                    @blur="parseToolConfig"
                  />
                  <div class="form-tip">
                    请输入有效的JSON格式配置，例如：{"search": {"max_results": 10}}
                  </div>
                </el-form-item>
              </div>
              
              <el-form-item label="用户提示词模板">
                <el-input
                  v-model="formData.user_prompt_template"
                  type="textarea"
                  :rows="4"
                  placeholder="请输入用户提示词模板，可使用 {input} 作为用户输入占位符"
                  maxlength="1000"
                  show-word-limit
                />
              </el-form-item>
            </el-form>
          </el-tab-pane>

          <!-- 知识库配置标签页 -->
          <el-tab-pane label="知识库" name="knowledge">
            <el-form
              :model="formData"
              label-width="100px"
              class="config-form"
            >
              <el-form-item label="关联知识库">
                <el-select
                  v-model="formData.knowledge_bases"
                  multiple
                  placeholder="请选择知识库"
                  style="width: 100%"
                >
                  <el-option
                    v-for="kb in availableKnowledgeBases"
                    :key="kb.id"
                    :label="kb.name"
                    :value="kb.id"
                  >
                    <span style="float: left">{{ kb.name }}</span>
                    <span style="float: right; color: #8492a6; font-size: 13px">
                      {{ kb.description }}
                    </span>
                  </el-option>
                </el-select>
              </el-form-item>
              
              <el-form-item label="检索设置">
                <el-row :gutter="16">
                  <el-col :span="12">
                    <el-form-item label="相似度阈值">
                      <el-input-number
                        v-model="formData.retrieval_config.similarity_threshold"
                        :min="0"
                        :max="1"
                        :step="0.1"
                        :precision="2"
                        placeholder="0.7"
                        style="width: 100%"
                      />
                    </el-form-item>
                  </el-col>
                  <el-col :span="12">
                    <el-form-item label="最大检索数量">
                      <el-input-number
                        v-model="formData.retrieval_config.max_results"
                        :min="1"
                        :max="20"
                        placeholder="5"
                        style="width: 100%"
                      />
                    </el-form-item>
                  </el-col>
                </el-row>
              </el-form-item>
            </el-form>
          </el-tab-pane>

          <!-- 权限配置标签页 -->
          <el-tab-pane label="权限配置" name="permissions">
            <el-form
              :model="formData"
              label-width="100px"
              class="config-form"
            >
              <el-form-item label="允许使用的用户">
                <el-select
                  v-model="formData.allowed_users"
                  multiple
                  filterable
                  allow-create
                  placeholder="请选择或输入用户ID（留空表示根据可见性设置）"
                  style="width: 100%"
                >
                  <!-- 这里可以从用户列表API获取选项 -->
                </el-select>
                <div class="form-tip">
                  如果设置为公开，所有用户都可以使用；如果设置为私有且未指定用户，则只有创建者可以使用
                </div>
              </el-form-item>
              
              <el-form-item label="元数据">
                <el-input
                  v-model="metadataText"
                  type="textarea"
                  :rows="6"
                  placeholder="请输入元数据（JSON格式）"
                  @blur="parseMetadata"
                />
                <div class="form-tip">
                  请输入有效的JSON格式，用于存储额外的配置信息
                </div>
              </el-form-item>
            </el-form>
          </el-tab-pane>
        </el-tabs>
      </div>

      <!-- 右侧：聊天预览调试 -->
      <div class="right-panel">
        <div class="panel-header">
          <h3 class="panel-title">预览调试</h3>
          <div class="panel-actions">
            <el-button size="small" @click="clearChat">清空对话</el-button>
            <el-button size="small" type="primary" @click="testAgent" :disabled="!canTest">测试</el-button>
          </div>
        </div>
        
        <!-- 聊天消息区域 -->
        <div class="chat-container">
          <div class="chat-messages" ref="chatMessages">
            <div v-if="chatMessagesList.length === 0" class="empty-chat">
              <el-empty description="开始测试智能体" />
            </div>
            <div
              v-for="(message, index) in chatMessagesList"
              :key="index"
              :class="['message', message.role]"
            >
              <div class="message-content">
                <!-- 思考过程（仅助手消息显示） -->
                <div v-if="message.role === 'assistant' && message.thinking" class="message-thinking">
                  <el-collapse>
                    <el-collapse-item title="💭 思考过程" name="thinking">
                      <div class="thinking-content">{{ message.thinking }}</div>
                    </el-collapse-item>
                  </el-collapse>
                </div>
                
                <!-- 工具调用（仅助手消息显示） -->
                <div v-if="message.role === 'assistant' && message.tool_calls && message.tool_calls.length > 0" class="message-tools">
                  <el-collapse>
                    <el-collapse-item title="🔧 工具调用" name="tools">
                      <div v-for="(tool, toolIndex) in message.tool_calls" :key="toolIndex" class="tool-call">
                        <div class="tool-name">{{ tool.name }}</div>
                        <div class="tool-args">参数: {{ JSON.stringify(tool.arguments, null, 2) }}</div>
                        <div v-if="tool.result" class="tool-result">结果: {{ JSON.stringify(tool.result, null, 2) }}</div>
                        <div v-if="tool.error" class="tool-error">错误: {{ tool.error }}</div>
                      </div>
                    </el-collapse-item>
                  </el-collapse>
                </div>
                
                <!-- 消息内容 -->
                <div class="message-text">{{ message.content }}</div>
                
                <!-- 图片内容 -->
                <div v-if="message.images && message.images.length > 0" class="message-images">
                  <div class="message-images-grid">
                    <div 
                      v-for="(image, imgIndex) in message.images" 
                      :key="imgIndex" 
                      class="message-image-item"
                    >
                      <img 
                        :src="image.data" 
                        :alt="image.name"
                        @click="previewImage(image.data)"
                        class="message-image"
                      />
                    </div>
                  </div>
                </div>
                
                <div class="message-time">{{ formatTime(message.timestamp) }}</div>
              </div>
            </div>
            <div v-if="isTestingAgent" class="message assistant">
              <div class="message-content">
                <div class="message-text">
                  <el-icon class="is-loading"><Loading /></el-icon>
                  正在思考中...
                </div>
              </div>
            </div>
          </div>
          
          <!-- 输入区域 -->
          <div class="chat-input">
            <!-- 图片预览区域 -->
            <div v-if="selectedImages.length > 0" class="image-preview-container">
              <div class="image-preview-list">
                <div 
                  v-for="(image, index) in selectedImages" 
                  :key="index" 
                  class="image-preview-item"
                >
                  <img 
                    :src="image.url" 
                    :alt="image.name"
                    @click="previewImage(image.url)"
                    class="preview-thumbnail"
                  />
                  <div class="image-info">
                    <span class="image-size">{{ formatFileSize(image.compressedSize || image.file.size) }}</span>
                  </div>
                  <el-button 
                    type="danger" 
                    size="small" 
                    circle 
                    class="remove-image-btn"
                    @click="removeImage(index)"
                  >
                    <el-icon><Close /></el-icon>
                  </el-button>
                </div>
              </div>
            </div>
            
            <el-input
              v-model="testMessage"
              type="textarea"
              :rows="3"
              placeholder="输入测试消息..."
              @keydown.ctrl.enter="sendTestMessage"
              @paste="handlePaste"
              :disabled="isTestingAgent"
            />
            <div class="input-actions">
              <div class="input-left-actions">
                <el-upload
                  ref="uploadRef"
                  :auto-upload="false"
                  :show-file-list="false"
                  accept="image/*"
                  multiple
                  :on-change="handleImageSelect"
                  :disabled="isTestingAgent"
                >
                  <el-button size="small" :disabled="isTestingAgent">
                    <el-icon><Picture /></el-icon>
                    上传图片
                  </el-button>
                </el-upload>
                <span class="input-tip">Ctrl + Enter 发送</span>
              </div>
              <el-button
                type="primary"
                size="small"
                @click="sendTestMessage"
                :disabled="(!testMessage.trim() && selectedImages.length === 0) || isTestingAgent"
              >
                发送
              </el-button>
            </div>
          </div>
          
          <!-- 图片预览对话框 -->
          <el-dialog
            v-model="imagePreviewVisible"
            title="图片预览"
            width="60%"
            center
          >
            <div class="image-preview-dialog">
              <img :src="currentPreviewImage" alt="预览图片" class="preview-image" />
            </div>
          </el-dialog>
        </div>
      </div>
    </div>

    <template #footer>
      <div class="dialog-footer">
        <el-button @click="handleClose">取消</el-button>
        <el-button type="primary" @click="handleSubmit" :loading="loading">
          {{ isEdit ? '更新' : '创建' }}
        </el-button>
      </div>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref, reactive, computed, watch, nextTick, onMounted, onUnmounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Codemirror } from 'vue-codemirror'
import { javascript } from '@codemirror/lang-javascript'
import { oneDark } from '@codemirror/theme-one-dark'
import { Loading, Picture, Close } from '@element-plus/icons-vue'
import { modelApi } from '@/api/models'
import { modelServiceConfigApi } from '@/api/model-service-configs'
import { chatWithAgent, getAgentTools } from '@/api/agents'
import { instructionSetApi } from '@/api/instruction-set'

// Props
const props = defineProps({
  modelValue: {
    type: Boolean,
    default: false
  },
  agent: {
    type: Object,
    default: null
  }
})

// Emits
const emit = defineEmits(['update:modelValue', 'submit'])

// 响应式数据
const formRef = ref()
const loading = ref(false)
const toolConfigText = ref('')
const metadataText = ref('')
const chatMessages = ref() // 聊天消息容器的DOM引用
const activeConfigTab = ref('basic')

// 聊天相关数据
const testMessage = ref('')
const chatMessagesList = ref([])
const isTestingAgent = ref(false)
// 为每个智能体维护独立的聊天记录
const agentChatHistory = ref(new Map())
// 图片上传相关
const selectedImages = ref([])
const imagePreviewVisible = ref(false)
const currentPreviewImage = ref('')

// CodeMirror编辑器实例
const cmView = ref(null)

// CodeMirror扩展配置
const extensions = ref([javascript(), oneDark])

// 计算属性
const visible = computed({
  get: () => props.modelValue,
  set: (value) => emit('update:modelValue', value)
})

const isEdit = computed(() => {
  console.log('isEdit computed - props.agent:', props.agent)
  console.log('isEdit computed - props.agent?.id:', props.agent?.id)
  const result = !!props.agent?.id
  console.log('isEdit computed - result:', result)
  return result
})

/**
 * 计算是否可以测试智能体
 */
const canTest = computed(() => {
  return formData.name && formData.system_prompt && formData.model_service_config_id
})

// 表单数据
const defaultFormData = {
  name: '',
  description: '',
  agent_type: 'CUSTOM',
  instruction_set_id: null, // 关联的指令集ID，仅用于REVIEW类型
  status: 'DRAFT',
  is_public: false,
  model_service_config_id: null,
  memory_enabled: true,
  system_prompt: '',
  user_prompt_template: '',
  tools: [],
  tool_config: {},
  knowledge_bases: [],
  retrieval_config: {
    similarity_threshold: 0.7,
    max_results: 5
  },
  allowed_users: [],
  tags: [],
  metadata: {},
  model_config: {
    temperature: 0.7,
    max_tokens: 2048,
    top_p: 0.9,
    frequency_penalty: 0,
    presence_penalty: 0,
    top_k: 40
  }
}

const formData = reactive({ ...defaultFormData })

// 表单验证规则
const formRules = {
  name: [
    { required: true, message: '请输入智能体名称', trigger: 'blur' },
    { min: 2, max: 100, message: '名称长度在 2 到 100 个字符', trigger: 'blur' }
  ],
  agent_type: [
    { required: true, message: '请选择类型', trigger: 'change' }
  ],
  instruction_set_id: [
    {
      validator: (rule, value, callback) => {
        if (formData.agent_type === 'REVIEW' && !value) {
          callback(new Error('审读类型必须选择关联的指令集'))
        } else {
          callback()
        }
      },
      trigger: 'change'
    }
  ],
  status: [
    { required: true, message: '请选择状态', trigger: 'change' }
  ],
  model_service_config_id: [
    { required: true, message: '请选择模型配置', trigger: 'change' }
  ],
  system_prompt: [
    { required: true, message: '请输入系统提示词', trigger: 'blur' },
    { min: 10, max: 2000, message: '系统提示词长度在 10 到 2000 个字符', trigger: 'blur' }
  ]
}

// 可用模型列表
const availableModels = ref([])
const loadingModels = ref(false)

// 可用指令集列表
const availableInstructionSets = ref([])
const loadingInstructionSets = ref(false)
const loadingTools = ref(false)

/**
 * 加载可用模型列表
 */
const loadAvailableModels = async () => {
  try {
    loadingModels.value = true
    const response = await modelServiceConfigApi.getAgentConfigs()
    console.log('response', response)
    availableModels.value = response.map(config => ({
      label: config.provider_display_name + ' - ' + config.model_name,
      value: config.model_id, // 使用model_id作为value，对应model_service_config_id
      provider: config.provider,
      model_name: config.model_name,
      config_id: config.model_id,
      display_name: config.label
    }))
  } catch (error) {
    console.error('加载模型服务配置失败:', error)
    ElMessage.error('加载模型服务配置失败，请稍后重试')
    // 如果API调用失败，使用默认的模型列表作为备选
    availableModels.value = [
      { label: 'GPT-4', value: 'gpt-4' },
      { label: 'GPT-3.5 Turbo', value: 'gpt-3.5-turbo' },
      { label: 'Claude-3 Sonnet', value: 'claude-3-sonnet' },
      { label: 'Claude-3 Haiku', value: 'claude-3-haiku' },
      { label: 'Gemini Pro', value: 'gemini-pro' },
      { label: 'Llama 2', value: 'llama-2' }
    ]
  } finally {
    loadingModels.value = false
  }
}

/**
 * 加载可用指令集列表
 */
const loadAvailableInstructionSets = async () => {
  try {
    loadingInstructionSets.value = true
    const response = await instructionSetApi.getInstructionSets({
      status: 'ACTIVE', // 只获取活跃状态的指令集
      page: 1,
      page_size: 100 // 获取足够多的指令集
    })
    availableInstructionSets.value = response.data || []
  } catch (error) {
    console.error('加载指令集列表失败:', error)
    ElMessage.error('加载指令集列表失败，请稍后重试')
    availableInstructionSets.value = []
  } finally {
    loadingInstructionSets.value = false
  }
}

// 可用工具列表
const availableTools = ref([])

/**
 * 加载可用技能列表（用于绑定到智能体）
 */
const loadAvailableTools = async () => {
  try {
    loadingTools.value = true
    const allItems = []
    let page = 1
    const size = 100
    let totalPages = 1

    while (page <= totalPages) {
      const response = await getAgentTools({
        page,
        size,
        is_enabled: true
      })
      const items = Array.isArray(response?.items) ? response.items : []
      allItems.push(...items)
      totalPages = Number(response?.pages || 1)
      page += 1
    }

    availableTools.value = allItems.map((tool) => ({
      label: tool.display_name || tool.name,
      value: tool.name,
      description: tool.description || '暂无描述'
    }))
  } catch (error) {
    console.error('加载技能列表失败:', error)
    ElMessage.error('加载技能列表失败，请稍后重试')
    availableTools.value = []
  } finally {
    loadingTools.value = false
  }
}

// 常用标签
const commonTags = ref([
  '助手', '客服', '编程', '写作', '翻译', '分析', '教育', '娱乐',
  '工具', '自动化', '数据处理', '内容生成', '问答', '推荐'
])

// 可用知识库列表
const availableKnowledgeBases = ref([
  { id: 1, name: '技术文档库', description: '包含技术相关文档' },
  { id: 2, name: '产品手册库', description: '产品使用手册和说明' },
  { id: 3, name: '常见问题库', description: 'FAQ和常见问题解答' },
  { id: 4, name: '法律法规库', description: '相关法律法规文档' }
])

/**
 * 监听对话框显示状态，加载模型配置
 */
let isLoadingModels = false
watch(visible, async (newVisible) => {
  if (newVisible && !isLoadingModels) {
    isLoadingModels = true
    try {
      await Promise.all([
        loadAvailableModels(),
        loadAvailableInstructionSets(),
        loadAvailableTools()
      ])
    } finally {
      isLoadingModels = false
    }
  }
})

/**
 * 监听agent变化，初始化表单数据
 */
watch(
  () => props.agent,
  (newAgent) => {
    if (newAgent) {
      // 映射API返回的字段到表单字段
      Object.assign(formData, {
        ...defaultFormData,
        name: newAgent.name || '',
        description: newAgent.description || '',
        agent_type: newAgent.agent_type || 'CUSTOM',
        instruction_set_id: newAgent.instruction_set_id || null, // 指令集关联字段，仅用于REVIEW类型
        status: newAgent.status || 'DRAFT',
        is_public: newAgent.is_public || false,
        model_service_config_id: newAgent.model_service_config_id || null,
        memory_enabled: newAgent.memory_enabled !== false,
        system_prompt: newAgent.system_prompt || '',
        user_prompt_template: newAgent.user_prompt_template || '',
        tools: newAgent.tools || [],
        tool_config: newAgent.tool_config || {},
        knowledge_bases: newAgent.knowledge_bases || [],
        retrieval_config: {
          ...defaultFormData.retrieval_config,
          ...(newAgent.retrieval_config || {})
        },
        allowed_users: newAgent.allowed_users || [],
        tags: newAgent.tags || [],
        metadata: newAgent.meta_data || newAgent.metadata || {},
        model_config: {
          ...defaultFormData.model_config,
          ...(newAgent.model_params || newAgent.model_config || {})
        }
      })
      
      // 初始化文本字段
      toolConfigText.value = newAgent.tool_config 
        ? JSON.stringify(newAgent.tool_config, null, 2) 
        : ''
      metadataText.value = (newAgent.meta_data || newAgent.metadata)
        ? JSON.stringify(newAgent.meta_data || newAgent.metadata, null, 2) 
        : ''
      
      // 加载该智能体的聊天记录
      loadAgentChatHistory(newAgent.id)
    } else {
      // 重置表单
      Object.assign(formData, defaultFormData)
      toolConfigText.value = ''
      metadataText.value = ''
      // 清空聊天记录
      chatMessagesList.value = []
    }
  },
  { immediate: true }
)

/**
 * 解析工具配置
 */
const parseToolConfig = () => {
  if (!toolConfigText.value.trim()) {
    formData.tool_config = {}
    return
  }
  
  try {
    formData.tool_config = JSON.parse(toolConfigText.value)
  } catch (error) {
    ElMessage.warning('工具配置格式不正确，请检查JSON格式')
    toolConfigText.value = JSON.stringify(formData.tool_config, null, 2)
  }
}

/**
 * 解析元数据
 */
const parseMetadata = () => {
  if (!metadataText.value.trim()) {
    formData.metadata = {}
    return
  }
  
  try {
    formData.metadata = JSON.parse(metadataText.value)
  } catch (error) {
    ElMessage.warning('元数据格式不正确，请检查JSON格式')
    metadataText.value = JSON.stringify(formData.metadata, null, 2)
  }
}

/**
 * 关闭对话框
 */
const handleClose = () => {
  visible.value = false
  // 重置表单
  nextTick(() => {
    formRef.value?.resetFields()
  })
}

/**
 * 提交表单
 */
const handleSubmit = async () => {
  try {
    await formRef.value.validate()
    
    // 解析JSON字段
    parseToolConfig()
    parseMetadata()
    
    loading.value = true
    
    // 根据model_service_config_id查找对应的模型配置
    console.log("model:",formData.model_service_config_id)
    const selectedModel = availableModels.value.find(model => model.value === formData.model_service_config_id)
    if (!selectedModel) {
      ElMessage.error('请选择有效的模型配置')
      loading.value = false
      return
    }
    
    // 准备提交数据
    const submitData = {
      ...formData,
      // 将model_name转换为model_service_config_id
      model_service_config_id: selectedModel.config_id,
      // 清理空值
      allowed_users: (formData.allowed_users || []).filter(Boolean),
      tags: (formData.tags || []).filter(Boolean)
    }
    
    // 如果是编辑模式，添加id字段
    if (isEdit.value && props.agent?.id) {
      submitData.id = props.agent.id
    }
    
    // 移除model_name字段，因为后端不需要
    delete submitData.model_name
    
    emit('submit', submitData)
    
  } catch (error) {
    console.error('表单验证失败:', error)
  } finally {
    loading.value = false
  }
}

/**
 * CodeMirror编辑器准备就绪回调
 */
const handleReady = (payload) => {
  cmView.value = payload.view
}

/**
 * CodeMirror内容变化回调
 */
const handleChange = (value) => {
  formData.system_prompt = value
}

/**
 * 格式化提示词
 */
const formatPrompt = () => {
  // CodeMirror的格式化功能
  if (cmView.value) {
    const { state } = cmView.value
    const formatted = state.doc.toString().replace(/\n\s*\n/g, '\n\n')
    formData.system_prompt = formatted
  }
}

/**
 * 清空提示词
 */
const clearPrompt = () => {
  formData.system_prompt = ''
}

/**
 * 加载智能体的聊天记录
 */
const loadAgentChatHistory = (agentId) => {
  if (!agentId) {
    chatMessagesList.value = []
    return
  }
  
  // 从Map中获取该智能体的聊天记录
  const history = agentChatHistory.value.get(agentId) || []
  chatMessagesList.value = [...history]
}

/**
 * 保存智能体的聊天记录
 */
const saveAgentChatHistory = (agentId) => {
  if (!agentId) return
  
  // 将当前聊天记录保存到Map中
  agentChatHistory.value.set(agentId, [...chatMessagesList.value])
}

/**
 * 清空聊天记录
 */
const clearChat = () => {
  chatMessagesList.value = []
  // 清空选中的图片
  clearSelectedImages()
  // 如果有当前智能体ID，也清空其保存的记录
  if (props.agent?.id) {
    agentChatHistory.value.delete(props.agent.id)
  }
}

/**
 * 测试智能体
 */
const testAgent = () => {
  if (!canTest.value) {
    ElMessage.warning('请先完善智能体的基本配置')
    return
  }
  
  // 添加系统消息
  chatMessagesList.value.push({
    role: 'system',
    content: `智能体 "${formData.name}" 已准备就绪，可以开始对话了。`,
    timestamp: new Date()
  })
  
  // 保存聊天记录
  if (props.agent?.id) {
    saveAgentChatHistory(props.agent.id)
  }
  
  scrollToBottom()
}

/**
 * 发送测试消息
 */
const sendTestMessage = async () => {
  if ((!testMessage.value.trim() && selectedImages.value.length === 0) || isTestingAgent.value) return
  
  // 处理图片数据
  let images = []
  if (selectedImages.value.length > 0) {
    try {
      // 将图片转换为包含data和name属性的对象数组，用于在聊天区域显示
      images = await Promise.all(
        selectedImages.value.map(async (image) => {
          const base64Data = await convertImageToBase64(image.file)
          return {
            data: `data:image/jpeg;base64,${base64Data}`,
            name: image.name
          }
        })
      )
    } catch (error) {
      ElMessage.error('图片处理失败，请重试')
      return
    }
  }
  
  const userMessage = {
    role: 'user',
    content: testMessage.value || '',
    images: images,
    timestamp: new Date()
  }
  
  chatMessagesList.value.push(userMessage)
  const currentMessage = testMessage.value
  // 为API调用准备纯Base64字符串数组
  const currentImages = images.map(img => {
    // 从data URL中提取纯Base64字符串
    return img.data.split(',')[1]
  })
  
  // 清空输入
  testMessage.value = ''
  clearSelectedImages()
  isTestingAgent.value = true
  
  // 保存用户消息
  if (props.agent?.id) {
    saveAgentChatHistory(props.agent.id)
  }
  
  scrollToBottom()
  
  try {
    // 如果是编辑模式且有智能体ID，使用真实API
    if (isEdit.value && props.agent?.id) {
      // 构建消息数据，支持多模态内容
      const messageData = {
        message: currentMessage,
        session_id: undefined, // 测试模式不需要保持会话
        context: {
          previous_messages: chatMessagesList.value.slice(0, -1).map(msg => ({
            role: msg.role,
            content: msg.content,
            images: msg.images ? msg.images.map(img => {
              // 如果是对象格式，提取Base64字符串；如果已经是字符串，直接使用
              return typeof img === 'string' ? img : img.data.split(',')[1]
            }) : []
          }))
        }
      }
      
      // 如果有图片，添加到消息数据中
      if (currentImages.length > 0) {
        messageData.images = currentImages
      }
      
      const response = await chatWithAgent(props.agent.id, messageData)
      
      const assistantMessage = {
         role: 'assistant',
         content: response.message,
         timestamp: new Date(),
         thinking: response.metadata?.thinking,
         tool_calls: response.metadata?.tool_calls
       }
      
      chatMessagesList.value.push(assistantMessage)
    } else {
      // 创建模式或没有ID时，显示配置预览
      await new Promise(resolve => setTimeout(resolve, 1000))
      
      // 获取选中模型的显示名称
      const selectedModel = availableModels.value.find(model => model.value === formData.model_service_config_id)
      const modelDisplayName = selectedModel ? selectedModel.label : '未选择'
      
      const assistantMessage = {
        role: 'assistant',
        content: `这是配置预览模式。当前智能体配置：\n- 模型：${modelDisplayName}\n- 温度：${formData.model_config.temperature}\n- 系统提示词长度：${formData.system_prompt?.length || 0} 字符\n\n请先保存智能体后进行真实对话测试。`,
        timestamp: new Date()
      }
      
      chatMessagesList.value.push(assistantMessage)
    }
    
    // 保存聊天记录
    if (props.agent?.id) {
      saveAgentChatHistory(props.agent.id)
    }
    
  } catch (error) {
    console.error('测试失败:', error)
    ElMessage.error('测试失败：' + (error.response?.data?.detail || error.message || '请检查配置'))
    
    // 添加错误消息到聊天记录
    const errorMessage = {
      role: 'assistant',
      content: '抱歉，测试过程中遇到了问题。请检查智能体配置或稍后重试。',
      timestamp: new Date()
    }
    
    chatMessagesList.value.push(errorMessage)
    
    // 保存聊天记录（包括错误消息）
    if (props.agent?.id) {
      saveAgentChatHistory(props.agent.id)
    }
  } finally {
    isTestingAgent.value = false
    scrollToBottom()
  }
}

/**
 * 滚动到聊天底部
 */
const scrollToBottom = () => {
  nextTick(() => {
    if (chatMessages.value) {
      chatMessages.value.scrollTop = chatMessages.value.scrollHeight
    }
  })
}

/**
 * 格式化时间
 */
const formatTime = (timestamp) => {
  return new Date(timestamp).toLocaleTimeString('zh-CN', {
    hour: '2-digit',
    minute: '2-digit'
  })
}

/**
 * 处理图片选择
 */
const handleImageSelect = async (file) => {
  // 验证文件格式
  if (!validateImageFormat(file.raw)) {
    ElMessage.error('不支持的图片格式，请选择 JPEG、PNG、GIF 或 WebP 格式的图片')
    return
  }
  
  // 验证文件大小（限制为10MB）
  if (file.raw.size > 10 * 1024 * 1024) {
    ElMessage.error(`图片大小不能超过10MB，当前大小：${formatFileSize(file.raw.size)}`)
    return
  }
  
  try {
    // 直接使用原始文件，不进行压缩
    const processedFile = file.raw
    
    // 创建图片预览URL
    const imageUrl = URL.createObjectURL(processedFile)
    
    // 添加到选中图片列表
    selectedImages.value.push({
      file: processedFile,
      url: imageUrl,
      name: file.name,
      originalSize: file.raw.size,
      compressedSize: processedFile.size
    })
    
  } catch (error) {
    console.error('图片处理失败:', error)
    ElMessage.error('图片处理失败，请重试')
  }
}

/**
 * 移除图片
 */
const removeImage = (index) => {
  const image = selectedImages.value[index]
  // 释放URL对象
  URL.revokeObjectURL(image.url)
  selectedImages.value.splice(index, 1)
}

/**
 * 预览图片
 */
const previewImage = (imageUrl) => {
  currentPreviewImage.value = imageUrl
  imagePreviewVisible.value = true
}

/**
 * 清空选中的图片
 */
const clearSelectedImages = () => {
  selectedImages.value.forEach(image => {
    URL.revokeObjectURL(image.url)
  })
  selectedImages.value = []
}

/**
 * 处理粘贴事件，支持粘贴图片
 */
const handlePaste = async (event) => {
  const clipboardData = event.clipboardData || window.clipboardData
  if (!clipboardData) return
  
  const items = clipboardData.items
  if (!items) return
  
  // 遍历剪贴板项目，查找图片
  for (let i = 0; i < items.length; i++) {
    const item = items[i]
    
    // 检查是否为图片类型
    if (item.type.indexOf('image') !== -1) {
      event.preventDefault() // 阻止默认粘贴行为
      
      const file = item.getAsFile()
      if (!file) continue
      
      try {
        // 验证图片格式
        if (!validateImageFormat(file)) {
          ElMessage.error('不支持的图片格式，请选择 JPEG、PNG、GIF 或 WebP 格式的图片')
          continue
        }
        
        // 验证文件大小（限制为10MB）
        if (file.size > 10 * 1024 * 1024) {
          ElMessage.error(`图片大小不能超过10MB，当前大小：${formatFileSize(file.size)}`)
          continue
        }
        
        // 直接使用原始文件，不进行压缩
        const processedFile = file
        
        // 创建图片预览URL
        const imageUrl = URL.createObjectURL(processedFile)
        
        // 生成文件名
        const timestamp = new Date().getTime()
        const fileName = `pasted-image-${timestamp}.${processedFile.type.split('/')[1] || 'png'}`
        
        // 添加到选中图片列表
        selectedImages.value.push({
          file: processedFile,
          url: imageUrl,
          name: fileName,
          originalSize: file.size,
          compressedSize: processedFile.size
        })
        
        ElMessage.success('图片粘贴成功')
        
      } catch (error) {
        console.error('粘贴图片处理失败:', error)
        ElMessage.error('粘贴图片处理失败，请重试')
      }
      
      break // 只处理第一个图片
    }
  }
}

/**
 * 将图片转换为Base64
 */
const convertImageToBase64 = (file) => {
  return new Promise((resolve, reject) => {
    const reader = new FileReader()
    reader.onload = () => {
      // 提取纯Base64字符串，去掉data:image/xxx;base64,前缀
      const base64 = reader.result.split(',')[1]
      resolve(base64)
    }
    reader.onerror = reject
    reader.readAsDataURL(file)
  })
}



/**
 * 验证图片格式
 */
const validateImageFormat = (file) => {
  const allowedTypes = ['image/jpeg', 'image/jpg', 'image/png', 'image/gif', 'image/webp']
  return allowedTypes.includes(file.type.toLowerCase())
}

/**
 * 获取图片文件大小的可读格式
 */
const formatFileSize = (bytes) => {
  if (bytes === 0) return '0 Bytes'
  const k = 1024
  const sizes = ['Bytes', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

/**
 * 组件挂载时初始化
 */
onMounted(() => {
  // loadAvailableModels() 已移至 watch visible 中处理
})

/**
 * 组件卸载时清理
 */
onUnmounted(() => {
  cmView.value = null
})
</script>

<style scoped>
.agent-edit-dialog {
  --dialog-width: 95%;
}

.three-column-layout {
  display: flex;
  height: 70vh;
  border: 1px solid #e4e7ed;
  border-radius: 6px;
  overflow: hidden;
}

/* 左侧面板 - 系统提示词编辑器 */
.left-panel {
  width: 35%;
  border-right: 1px solid #e4e7ed;
  display: flex;
  flex-direction: column;
}

.panel-header {
  padding: 12px 16px;
  background: #f8f9fa;
  border-bottom: 1px solid #e4e7ed;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.panel-title {
  font-size: 14px;
  font-weight: 600;
  color: #303133;
  margin: 0;
}

.panel-actions {
  display: flex;
  gap: 8px;
}

.code-editor-container {
  flex: 1;
  position: relative;
  min-height: 300px;
}

/* CodeMirror样式覆盖 */
:deep(.cm-editor) {
  height: 100%;
  min-height: 300px;
  border: none;
  outline: none;
  font-size: 14px;
}

:deep(.cm-focused) {
  outline: none;
}

:deep(.cm-scroller) {
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
}



.prompt-tips {
  padding: 12px;
  background: #f8f9fa;
  border-top: 1px solid #e4e7ed;
}

.tips-list {
  margin: 0;
  padding-left: 16px;
  font-size: 12px;
  line-height: 1.6;
}

.tips-list li {
  margin-bottom: 4px;
}

/* 中间面板 - 配置选项 */
.middle-panel {
  width: 40%;
  border-right: 1px solid #e4e7ed;
  display: flex;
  flex-direction: column;
}

.config-tabs {
  flex: 1;
  display: flex;
  flex-direction: column;
}

:deep(.el-tabs) {
  height: 100%;
  display: flex;
  flex-direction: column;
}

:deep(.el-tabs__content) {
  flex: 1;
  overflow-y: auto;
  padding: 0;
}

:deep(.el-tabs__header) {
  margin: 0;
  background: #f8f9fa;
  border-bottom: 1px solid #e4e7ed;
}

:deep(.el-tabs__nav-wrap) {
  padding: 0 16px;
}

.config-form {
  padding: 16px;
}

.form-tip {
  font-size: 12px;
  color: #909399;
  margin-top: 4px;
  line-height: 1.4;
}

/* 右侧面板 - 聊天预览 */
.right-panel {
  width: 25%;
  display: flex;
  flex-direction: column;
  height: 100%; /* 确保右侧面板占满父元素高度 */
}

.chat-container {
  flex: 1;
  display: flex;
  flex-direction: column;
  height: 100%; /* 确保容器占满父元素高度 */
  overflow: hidden; /* 防止容器本身产生滚动条 */
}

.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
  background: #fafafa;
  min-height: 0; /* 允许flex收缩 */
  height: 0; /* 配合flex: 1使用，确保正确计算高度 */
}

.empty-chat {
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
}

.message {
  margin-bottom: 16px;
  display: flex;
}

.message.user {
  justify-content: flex-end;
}

.message.assistant {
  justify-content: flex-start;
}

.message.system {
  justify-content: center;
}

.message-content {
  max-width: 80%;
  padding: 8px 12px;
  border-radius: 8px;
  font-size: 14px;
  line-height: 1.4;
  word-wrap: break-word;
}

.message.user .message-content {
  background: #409eff;
  color: white;
}

.message.assistant .message-content {
  background: white;
  color: #303133;
  border: 1px solid #e4e7ed;
}

.message.system .message-content {
  background: #f0f9ff;
  color: #606266;
  border: 1px solid #b3d8ff;
  font-style: italic;
}

.message-text {
  margin-bottom: 4px;
  white-space: pre-wrap;
  word-wrap: break-word;
}

.message-time {
  font-size: 12px;
  color: #909399;
}

.chat-input {
  padding: 16px;
  border-top: 1px solid #e4e7ed;
  background: white;
}

.input-actions {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 8px;
}

.input-left-actions {
  display: flex;
  align-items: center;
  gap: 12px;
}

.input-tip {
  font-size: 12px;
  color: #909399;
}

/* 图片预览相关样式 */
.image-preview-container {
  margin-bottom: 12px;
  padding: 8px;
  background: #f8f9fa;
  border-radius: 6px;
  border: 1px solid #e4e7ed;
}

.image-preview-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.image-preview-item {
  position: relative;
  width: 80px;
  height: 80px;
  border-radius: 6px;
  overflow: hidden;
  border: 1px solid #e4e7ed;
  margin-bottom: 24px;
}

.preview-thumbnail {
  width: 100%;
  height: 100%;
  object-fit: cover;
  cursor: pointer;
  transition: transform 0.2s;
}

.preview-thumbnail:hover {
  transform: scale(1.05);
}

.image-info {
  position: absolute;
  bottom: -20px;
  left: 0;
  right: 0;
  text-align: center;
}

.image-size {
  font-size: 10px;
  color: #909399;
  background: rgba(255, 255, 255, 0.9);
  padding: 1px 4px;
  border-radius: 2px;
  white-space: nowrap;
}

.remove-image-btn {
  position: absolute;
  top: -8px;
  right: -8px;
  width: 20px;
  height: 20px;
  min-height: 20px;
  padding: 0;
  background: #f56c6c;
  border: 1px solid #fff;
}

.image-preview-dialog {
  text-align: center;
}

.preview-image {
  max-width: 100%;
  max-height: 70vh;
  object-fit: contain;
}

/* 消息中的图片样式 */
.message-images {
  margin-top: 8px;
  margin-bottom: 8px;
}

.message-images-grid {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  max-width: 300px;
}

.message-image-item {
  border-radius: 8px;
  overflow: hidden;
  border: 1px solid #e4e7ed;
  max-width: 150px;
}

.message-image {
  width: 100%;
  height: auto;
  max-height: 150px;
  object-fit: cover;
  cursor: pointer;
  transition: transform 0.2s;
  display: block;
}

.message-image:hover {
  transform: scale(1.02);
}

/* 用户消息中的图片样式调整 */
.message.user .message-image-item {
  border-color: rgba(255, 255, 255, 0.3);
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  padding: 16px 20px;
  border-top: 1px solid #e4e7ed;
  background: #fafafa;
}

/* 自定义滚动条 */
.chat-messages::-webkit-scrollbar,
:deep(.el-tabs__content)::-webkit-scrollbar {
  width: 6px;
}

.chat-messages::-webkit-scrollbar-track,
:deep(.el-tabs__content)::-webkit-scrollbar-track {
  background: #f1f1f1;
  border-radius: 3px;
}

.chat-messages::-webkit-scrollbar-thumb,
:deep(.el-tabs__content)::-webkit-scrollbar-thumb {
  background: #c1c1c1;
  border-radius: 3px;
}

.chat-messages::-webkit-scrollbar-thumb:hover,
:deep(.el-tabs__content)::-webkit-scrollbar-thumb:hover {
  background: #a8a8a8;
}

/* 响应式设计 */
@media (max-width: 1200px) {
  .left-panel {
    width: 30%;
  }
  
  .middle-panel {
    width: 45%;
  }
  
  .right-panel {
    width: 25%;
  }
}

/* 表单样式 */
:deep(.el-form-item__label) {
  font-weight: 500;
  color: #606266;
}

/* 思考过程和工具调用样式 */
.message-thinking {
  margin-bottom: 12px;
}

.thinking-content {
  background: #f8f9fa;
  padding: 12px;
  border-radius: 6px;
  font-size: 13px;
  color: #666;
  white-space: pre-wrap;
  border-left: 3px solid #409eff;
}

.message-tools {
  margin-bottom: 12px;
}

.tool-call {
  background: #f5f7fa;
  padding: 12px;
  border-radius: 6px;
  margin-bottom: 8px;
  border-left: 3px solid #67c23a;
}

.tool-call:last-child {
  margin-bottom: 0;
}

.tool-name {
  font-weight: 600;
  color: #409eff;
  margin-bottom: 6px;
  font-size: 14px;
}

.tool-args,
.tool-result {
  background: white;
  padding: 8px;
  border-radius: 4px;
  margin: 6px 0;
  font-family: 'Courier New', monospace;
  font-size: 12px;
  color: #333;
  white-space: pre-wrap;
  border: 1px solid #e4e7ed;
}

.tool-result {
  border-left: 3px solid #67c23a;
}

.tool-error {
  background: #fef0f0;
  padding: 8px;
  border-radius: 4px;
  margin: 6px 0;
  font-family: 'Courier New', monospace;
  font-size: 12px;
  color: #f56c6c;
  white-space: pre-wrap;
  border: 1px solid #fbc4c4;
  border-left: 3px solid #f56c6c;
}

/* 折叠面板样式优化 */
:deep(.el-collapse-item__header) {
  font-size: 13px;
  font-weight: 500;
  padding: 8px 12px;
  background: #f8f9fa;
  border-radius: 4px;
}

:deep(.el-collapse-item__content) {
  padding: 0;
}

:deep(.el-collapse-item__wrap) {
  border: none;
}

:deep(.el-collapse) {
  border: none;
}

:deep(.el-collapse-item) {
  border: none;
}

:deep(.el-textarea__inner) {
  font-family: inherit;
}

:deep(.el-select .el-input__inner) {
  cursor: pointer;
}

/* 加载状态 */
.is-loading {
  animation: rotating 2s linear infinite;
}

@keyframes rotating {
  0% {
    transform: rotate(0deg);
  }
  100% {
    transform: rotate(360deg);
  }
}
</style>
