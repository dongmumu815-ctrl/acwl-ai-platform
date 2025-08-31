<template>
  <el-drawer
      v-model="visible"
      size="1200px"
      direction="rtl"
      :before-close="handleClose"
      class="chat-drawer"
      :modal="true"
      :close-on-click-modal="false"
      :close-on-press-escape="true"
      destroy-on-close
    >
    <template #header>
      <div class="drawer-header">
        <div class="header-content">
          <h3 class="drawer-title">与 {{ agent?.name || '智能体' }} 聊天</h3>
          <span class="chat-info-item">模型: {{ agent?.model_name || '未知' }}</span>
          <span class="chat-info-item">消息数: {{ messages.length }}</span>
        </div>
      </div>
    </template>
    <div class="chat-container">
      <!-- 聊天消息区域 -->
      <div ref="messagesContainer" class="messages-container">
        <div v-if="messages.length === 0" class="empty-messages">
          <el-empty description="开始与智能体对话吧！" />
        </div>
        
        <div
          v-for="message in messages"
          :key="message.id"
          :class="['message-item', message.role]"
        >
          <div class="message-avatar">
            <el-avatar v-if="message.role === 'user'" :size="32">
              <el-icon><User /></el-icon>
            </el-avatar>
            <el-avatar v-else :size="32" class="agent-avatar">
              <el-icon><ChatDotRound /></el-icon>
            </el-avatar>
          </div>
          
          <div class="message-content">
            <div class="message-header">
              <span class="message-sender">
                {{ message.role === 'user' ? '用户' : agent?.name || '智能体' }}
              </span>
              <span class="message-time">
                {{ formatTime(message.timestamp) }}
              </span>
            </div>
            
            <div class="message-text">
              <div v-if="message.role === 'assistant' && message.thinking" class="thinking-section">
                <el-collapse>
                  <el-collapse-item title="思考过程" name="thinking">
                    <pre class="thinking-content">{{ message.thinking }}</pre>
                  </el-collapse-item>
                </el-collapse>
              </div>
              
              <!-- 审读结果特殊显示 -->
              <div v-if="isReviewAgent && message.role === 'assistant' && message.reviewResult" class="review-result">
                <div class="review-header">
                  <el-icon><Lock /></el-icon>
                  <span>内容审读结果</span>
                </div>
                
                <div class="review-summary">
                  <el-tag 
                    :type="getReviewTagType(message.reviewResult.risk_level)"
                    size="large"
                    class="risk-tag"
                  >
                    {{ getRiskLevelText(message.reviewResult.risk_level) }}
                  </el-tag>
                  <span class="confidence">置信度: {{ (message.reviewResult.confidence * 100).toFixed(1) }}%</span>
                </div>
                
                <div v-if="message.reviewResult.flagged_content && message.reviewResult.flagged_content.length > 0" class="flagged-content">
                  <div class="flagged-header">检测到的问题内容：</div>
                  <div 
                    v-for="(item, index) in message.reviewResult.flagged_content"
                    :key="index"
                    class="flagged-item"
                  >
                    <el-tag size="small" type="warning">{{ item.category }}</el-tag>
                    <span class="flagged-text">"{{ item.content }}"</span>
                    <span class="flagged-reason">{{ item.reason }}</span>
                  </div>
                </div>
                
                <div v-if="message.reviewResult.suggestions && message.reviewResult.suggestions.length > 0" class="suggestions">
                  <div class="suggestions-header">建议：</div>
                  <ul class="suggestions-list">
                    <li v-for="(suggestion, index) in message.reviewResult.suggestions" :key="index">
                      {{ suggestion }}
                    </li>
                  </ul>
                </div>
                
                <!-- 增强版审读详细信息 -->
                <div v-if="message.reviewResult.total_matched_count !== undefined" class="enhanced-review-details">
                  <el-collapse>
                    <el-collapse-item title="详细检测信息" name="details">
                      <div class="detection-stats">
                        <div class="stat-item">
                          <span class="stat-label">命中节点数：</span>
                          <el-tag size="small" type="info">{{ message.reviewResult.total_matched_count }}</el-tag>
                        </div>
                        <div v-if="message.reviewResult.execution_path && message.reviewResult.execution_path.length > 0" class="stat-item">
                          <span class="stat-label">执行路径：</span>
                          <div class="execution-path">
                            <el-tag 
                              v-for="(step, index) in message.reviewResult.execution_path" 
                              :key="index"
                              size="small"
                              class="path-step"
                            >
                              {{ step.node_title || step.node_id }}
                            </el-tag>
                          </div>
                        </div>
                      </div>
                      
                      <div v-if="message.reviewResult.tree_structure" class="tree-structure">
                        <div class="tree-header">检测树结构：</div>
                        <pre class="tree-content">{{ JSON.stringify(message.reviewResult.tree_structure, null, 2) }}</pre>
                      </div>
                    </el-collapse-item>
                  </el-collapse>
                </div>
              </div>
              
              <!-- 异步任务状态显示 -->
              <div v-if="message.taskId && message.taskStatus !== 'completed'" class="task-status">
                <div class="task-header">
                  <el-icon><Loading /></el-icon>
                  <span>任务处理中...</span>
                </div>
                
                <el-progress 
                  :percentage="message.taskProgress || 0"
                  :status="message.taskStatus === 'failed' ? 'exception' : undefined"
                  class="task-progress"
                />
                
                <div class="task-actions">
                  <el-button 
                    size="small" 
                    type="primary" 
                    @click="checkTaskStatus(message)"
                    :loading="message.checkingStatus"
                  >
                    刷新状态
                  </el-button>
                  <el-button 
                    size="small" 
                    type="danger" 
                    @click="cancelTask(message)"
                    :disabled="message.taskStatus === 'completed' || message.taskStatus === 'failed'"
                  >
                    取消任务
                  </el-button>
                </div>
              </div>
              
              <!-- 消息内容 -->
              <div class="message-body">
                <!-- 如果消息包含图片 -->
                <div v-if="typeof message.content === 'object' && message.content.images" class="message-with-images">
                  <!-- 显示图片 -->
                  <div v-if="message.content.images.length > 0" class="message-images">
                    <div 
                      v-for="(image, index) in message.content.images" 
                      :key="index" 
                      class="message-image-item"
                    >
                      <img 
                        :src="image.url" 
                        :alt="image.name"
                        @click="previewImage(image.url)"
                        class="message-image"
                      />
                      <div class="image-name">{{ image.name }}</div>
                    </div>
                  </div>
                  <!-- 显示文本内容 -->
                  <div v-if="message.content.text" class="message-text-content" v-html="formatMessage(message.content.text)"></div>
                </div>
                <!-- 普通文本消息 -->
                <div v-else v-html="formatMessage(message.content)"></div>
              </div>
              
              <!-- 工具调用信息 -->
              <div v-if="message.tool_calls && message.tool_calls.length > 0" class="tool-calls">
                <div class="tool-calls-header">
                  <el-icon><Tools /></el-icon>
                  <span>工具调用</span>
                </div>
                <div
                  v-for="toolCall in message.tool_calls"
                  :key="toolCall.id"
                  class="tool-call-item"
                >
                  <div class="tool-call-name">{{ toolCall.name }}</div>
                  <div class="tool-call-args">
                    <pre>{{ JSON.stringify(toolCall.args, null, 2) }}</pre>
                  </div>
                  <div v-if="toolCall.result" class="tool-call-result">
                    <strong>结果：</strong>
                    <pre>{{ JSON.stringify(toolCall.result, null, 2) }}</pre>
                  </div>
                </div>
              </div>
            </div>
            
            <!-- 消息操作 -->
            <div class="message-actions">
              <el-button
                v-if="message.role === 'assistant'"
                size="small"
                text
                @click="copyMessage(message.content)"
              >
                <el-icon><CopyDocument /></el-icon>
                复制
              </el-button>
              <el-button
                v-if="message.role === 'assistant'"
                size="small"
                text
                @click="regenerateMessage(message)"
              >
                <el-icon><Refresh /></el-icon>
                重新生成
              </el-button>
            </div>
          </div>
        </div>
        
        <!-- 正在输入指示器 -->
        <div v-if="isTyping" class="typing-indicator">
          <div class="message-avatar">
            <el-avatar :size="32" class="agent-avatar">
              <el-icon><ChatDotRound /></el-icon>
            </el-avatar>
          </div>
          <div class="typing-content">
            <div class="typing-dots">
              <span></span>
              <span></span>
              <span></span>
            </div>
          </div>
        </div>
      </div>
      
      <!-- 输入区域 -->
      <div class="input-container">
        <div class="input-wrapper">
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
            v-model="inputMessage"
            type="textarea"
            :rows="3"
            placeholder="输入您的消息..."
            :disabled="isTyping"
            @keydown.ctrl.enter="sendMessage"
            @keydown.meta.enter="sendMessage"
            @paste="handlePaste"
            class="message-input"
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
                :disabled="isTyping"
              >
                <el-button size="small" :disabled="isTyping">
                  <el-icon><Picture /></el-icon>
                  上传图片
                </el-button>
              </el-upload>
              <span class="input-tip">Ctrl + Enter 发送</span>
            </div>
            <div class="input-buttons">
              <el-button
                size="small"
                @click="clearMessages"
                :disabled="messages.length === 0 || isTyping"
              >
                清空对话
              </el-button>
              <el-button
                type="primary"
                size="small"
                @click="sendMessage"
                :loading="isTyping"
                :disabled="(!inputMessage.trim() && selectedImages.length === 0) || isTyping"
              >
                发送
              </el-button>
            </div>
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


  </el-drawer>
</template>

<script setup>
import { ref, reactive, computed, watch, nextTick, onUnmounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { User, ChatDotRound, Tools, CopyDocument, Refresh, Lock, Loading, Picture, Close } from '@element-plus/icons-vue'
import { useClipboard } from '@vueuse/core'
import { chatWithAgent as chatWithAgentAPI, getTaskStatus, cancelTask as cancelTaskAPI } from '@/api/agents'

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
const emit = defineEmits(['update:modelValue'])

// 响应式数据
const messagesContainer = ref()
const inputMessage = ref('')
const isTyping = ref(false)
const messages = reactive([])
const conversationId = ref(null)
// 为每个智能体维护独立的聊天记录和会话ID
const agentChatHistory = ref(new Map())
const agentConversationIds = ref(new Map())

// 图片相关
const selectedImages = ref([])
const uploadRef = ref()
const imagePreviewVisible = ref(false)
const currentPreviewImage = ref('')

// 剪贴板
const { copy } = useClipboard()

// 计算属性
const isReviewAgent = computed(() => {
  return props.agent?.agent_type === 'REVIEW'
})

// 计算属性
const visible = computed({
  get: () => props.modelValue,
  set: (value) => emit('update:modelValue', value)
})

/**
 * 监听对话框显示状态
 */
watch(visible, (newVisible) => {
  if (newVisible && props.agent) {
    initializeChat()
  }
})

/**
 * 监听智能体变化，切换聊天记录
 */
watch(
  () => props.agent?.id,
  (newAgentId, oldAgentId) => {
    if (newAgentId !== oldAgentId) {
      // 停止之前的轮询
      stopAllPolling()
      loadAgentChatHistory(newAgentId)
    }
  },
  { immediate: true }
)

/**
 * 组件销毁时清理轮询
 */
onUnmounted(() => {
  stopAllPolling()
})

/**
 * 加载智能体的聊天记录
 */
const loadAgentChatHistory = (agentId) => {
  if (!agentId) {
    messages.splice(0)
    conversationId.value = null
    return
  }
  
  // 从Map中获取该智能体的聊天记录和会话ID
  const history = agentChatHistory.value.get(agentId) || []
  const savedConversationId = agentConversationIds.value.get(agentId) || null
  
  messages.splice(0, messages.length, ...history)
  conversationId.value = savedConversationId
}

/**
 * 保存智能体的聊天记录
 */
const saveAgentChatHistory = (agentId) => {
  if (!agentId) return
  
  // 将当前聊天记录和会话ID保存到Map中
  agentChatHistory.value.set(agentId, [...messages])
  if (conversationId.value) {
    agentConversationIds.value.set(agentId, conversationId.value)
  }
}

/**
 * 初始化聊天
 */
const initializeChat = () => {
  if (!props.agent?.id) {
    messages.splice(0)
    conversationId.value = null
    inputMessage.value = ''
    return
  }
  
  // 加载该智能体的聊天记录
  loadAgentChatHistory(props.agent.id)
  inputMessage.value = ''
  
  // 如果没有聊天记录，添加欢迎消息
  if (messages.length === 0 && props.agent?.system_prompt) {
    addMessage({
      role: 'assistant',
      content: `你好！我是 ${props.agent.name}。${props.agent.description || '很高兴为您服务！'}`,
      timestamp: new Date()
    })
    // 保存欢迎消息
    saveAgentChatHistory(props.agent.id)
  }
}

/**
 * 添加消息
 */
const addMessage = (message) => {
  const messageWithId = {
    id: Date.now() + Math.random(),
    ...message
  }
  messages.push(messageWithId)
  
  // 滚动到底部
  nextTick(() => {
    scrollToBottom()
  })
}

/**
 * 发送消息
 */
const sendMessage = async () => {
  if ((!inputMessage.value.trim() && selectedImages.value.length === 0) || isTyping.value) {
    return
  }
  
  const userMessage = inputMessage.value.trim()
  const images = [...selectedImages.value]
  
  inputMessage.value = ''
  selectedImages.value = []
  
  // 处理图片数据，转换为Base64字符串数组
  let processedImages = []
  if (images.length > 0) {
    try {
      processedImages = await Promise.all(
        images.map(async (image) => {
          // 如果url已经是base64格式，提取纯base64字符串
          if (image.url.startsWith('data:')) {
            return image.url.split(',')[1]
          }
          // 否则转换文件为base64
          return await convertImageToBase64(image.file)
        })
      )
    } catch (error) {
      ElMessage.error('图片处理失败，请重试')
      return
    }
  }
  
  // 构建消息内容
  let messageContent = userMessage
  if (images.length > 0) {
    messageContent = {
      text: userMessage,
      images: images.map(img => ({
        name: img.name,
        url: img.url,
        size: img.compressedSize
      }))
    }
  }
  
  // 添加用户消息
  addMessage({
    role: 'user',
    content: messageContent,
    timestamp: new Date()
  })
  
  // 保存用户消息
  saveAgentChatHistory(props.agent.id)
  
  // 开始输入状态
  isTyping.value = true
  
  try {
    // 调用聊天API
    const response = await chatWithAgent({
      agent_id: props.agent.id,
      message: userMessage,
      images: processedImages.length > 0 ? processedImages : undefined,
      conversation_id: conversationId.value
    })
    
    // 更新会话ID
    if (response.conversation_id) {
      conversationId.value = response.conversation_id
    }
    
    // 添加助手回复
    const assistantMessage = {
      role: 'assistant',
      content: response.message,
      thinking: response.thinking,
      tool_calls: response.tool_calls,
      reviewResult: response.reviewResult,
      taskId: response.taskId,
      taskStatus: response.taskStatus,
      taskProgress: response.taskProgress,
      checkingStatus: false,
      timestamp: new Date()
    }
    
    addMessage(assistantMessage)
    
    // 如果是异步任务，启动轮询
    if (response.taskId && response.taskStatus === 'pending') {
      startTaskPolling(assistantMessage)
    }
    
    // 保存助手回复
    saveAgentChatHistory(props.agent.id)
    
  } catch (error) {
    console.error('发送消息失败:', error)
    ElMessage.error('发送消息失败，请重试')
    
    // 添加错误消息
    addMessage({
      role: 'assistant',
      content: '抱歉，我遇到了一些问题，请稍后重试。',
      timestamp: new Date()
    })
    
    // 保存错误消息
    saveAgentChatHistory(props.agent.id)
  } finally {
    isTyping.value = false
  }
}

/**
 * 与智能体聊天API调用
 */
const chatWithAgent = async (data) => {
  try {
    // 构建请求数据
    const requestData = {
      message: data.message,
      session_id: data.conversation_id
    }
    
    // 如果有图片，添加到请求数据中
    if (data.images && data.images.length > 0) {
      requestData.images = data.images
    }
    
    // 调用真实的API
    const response = await chatWithAgentAPI(data.agent_id, requestData)
    
    // 处理审读Agent的特殊响应
    let reviewResult = null
    let taskId = null
    let taskStatus = null
    
    if (isReviewAgent.value && response.metadata) {
      // 检查是否是异步任务
      if (response.metadata.task_id) {
        taskId = response.metadata.task_id
        taskStatus = 'pending'
      }
      // 检查是否有审读结果
      else if (response.metadata.review_result) {
        reviewResult = response.metadata.review_result
      }
      // 处理增强版审读结果
      else if (response.metadata.comprehensive_result) {
        const comprehensiveResult = response.metadata.comprehensive_result
        const overallResult = response.metadata.overall_result
        const matchedNodes = response.metadata.matched_nodes || []
        
        // 转换为前端期望的格式
        reviewResult = {
          risk_level: overallResult.risk_level.toUpperCase(),
          confidence: overallResult.confidence,
          flagged_content: matchedNodes.map(node => ({
            category: node.description,
            content: node.sensitive_excerpt || '检测到敏感内容',
            reason: node.reasons ? node.reasons.join('; ') : '匹配检测规则'
          })),
          suggestions: overallResult.evidence || [],
          execution_path: response.metadata.execution_path || [],
          total_matched_count: response.metadata.total_matched_count || 0,
          tree_structure: response.metadata.tree_structure
        }
      }
    }
    
    return {
      message: response.message,
      thinking: response.metadata?.thinking || '',
      tool_calls: response.metadata?.tool_calls || [],
      conversation_id: response.session_id,
      reviewResult,
      taskId,
      taskStatus,
      taskProgress: 0
    }
  } catch (error) {
    console.error('API调用失败:', error)
    throw error
  }
}

/**
 * 获取风险等级对应的标签类型
 */
const getReviewTagType = (riskLevel) => {
  switch (riskLevel) {
    case 'LOW':
      return 'success'
    case 'MEDIUM':
      return 'warning'
    case 'HIGH':
      return 'danger'
    default:
      return 'info'
  }
}

/**
 * 获取风险等级文本
 */
const getRiskLevelText = (riskLevel) => {
  switch (riskLevel) {
    case 'LOW':
      return '低风险'
    case 'MEDIUM':
      return '中风险'
    case 'HIGH':
      return '高风险'
    default:
      return '未知'
  }
}

/**
 * 检查任务状态
 */
const checkTaskStatus = async (message) => {
  if (!message.taskId) return
  
  message.checkingStatus = true
  
  try {
    const response = await getTaskStatus(message.taskId)
    
    // 更新任务状态
    message.taskStatus = response.status
    message.taskProgress = response.progress
    
    // 如果任务完成，更新消息内容
    if (response.status === 'completed' && response.result) {
      if (response.result.review_result) {
        message.reviewResult = response.result.review_result
      }
      if (response.result.message) {
        message.content = response.result.message
      }
    }
    
    // 如果任务失败，显示错误信息
    if (response.status === 'failed' && response.error) {
      message.content = `任务执行失败: ${response.error}`
    }
    
  } catch (error) {
    console.error('检查任务状态失败:', error)
    ElMessage.error('检查任务状态失败')
  } finally {
    message.checkingStatus = false
  }
}

/**
 * 取消任务
 */
const cancelTask = async (message) => {
  if (!message.taskId) return
  
  try {
    await ElMessageBox.confirm(
      '确定要取消这个任务吗？',
      '确认取消',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    await cancelTaskAPI(message.taskId)
    message.taskStatus = 'cancelled'
    message.content = '任务已取消'
    
    // 停止轮询
    if (message.pollingTimer) {
      clearInterval(message.pollingTimer)
      message.pollingTimer = null
    }
    
    ElMessage.success('任务已取消')
    
  } catch (error) {
    if (error !== 'cancel') {
      console.error('取消任务失败:', error)
      ElMessage.error('取消任务失败')
    }
  }
}

/**
 * 启动任务状态轮询
 */
const startTaskPolling = (message) => {
  if (!message.taskId || message.pollingTimer) return
  
  // 立即检查一次
  checkTaskStatus(message)
  
  // 每3秒轮询一次
  message.pollingTimer = setInterval(async () => {
    if (message.taskStatus === 'completed' || 
        message.taskStatus === 'failed' || 
        message.taskStatus === 'cancelled') {
      clearInterval(message.pollingTimer)
      message.pollingTimer = null
      return
    }
    
    await checkTaskStatus(message)
  }, 3000)
}

/**
 * 停止所有轮询
 */
const stopAllPolling = () => {
  messages.forEach(message => {
    if (message.pollingTimer) {
      clearInterval(message.pollingTimer)
      message.pollingTimer = null
    }
  })
}

/**
 * 重新生成消息
 */
const regenerateMessage = async (message) => {
  const messageIndex = messages.findIndex(m => m.id === message.id)
  if (messageIndex === -1) return
  
  // 找到对应的用户消息
  const userMessageIndex = messageIndex - 1
  if (userMessageIndex < 0 || messages[userMessageIndex].role !== 'user') {
    ElMessage.warning('无法找到对应的用户消息')
    return
  }
  
  const userMessage = messages[userMessageIndex].content
  
  // 删除当前助手消息
  messages.splice(messageIndex, 1)
  
  // 重新发送
  isTyping.value = true
  
  try {
    const response = await chatWithAgent({
      agent_id: props.agent.id,
      message: userMessage,
      conversation_id: conversationId.value
    })
    
    // 添加新的回复
    addMessage({
      role: 'assistant',
      content: response.message,
      thinking: response.thinking,
      tool_calls: response.tool_calls,
      timestamp: new Date()
    })
    
  } catch (error) {
    console.error('重新生成失败:', error)
    ElMessage.error('重新生成失败，请重试')
  } finally {
    isTyping.value = false
  }
}

/**
 * 复制消息
 */
const copyMessage = async (content) => {
  try {
    await copy(content)
    ElMessage.success('已复制到剪贴板')
  } catch (error) {
    console.error('复制失败:', error)
    ElMessage.error('复制失败')
  }
}

/**
 * 清空对话
 */
const clearMessages = async () => {
  try {
    await ElMessageBox.confirm(
      '确定要清空所有对话记录吗？',
      '确认清空',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    messages.splice(0)
    conversationId.value = null
    
    // 清空该智能体的保存记录
    if (props.agent?.id) {
      agentChatHistory.value.delete(props.agent.id)
      agentConversationIds.value.delete(props.agent.id)
    }
    
    ElMessage.success('对话已清空')
    
  } catch {
    // 用户取消
  }
}

/**
 * 滚动到底部
 */
const scrollToBottom = () => {
  if (messagesContainer.value) {
    messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
  }
}

/**
 * 格式化消息内容
 */
const formatMessage = (content) => {
  // 简单的Markdown渲染
  return content
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.*?)\*/g, '<em>$1</em>')
    .replace(/`(.*?)`/g, '<code>$1</code>')
    .replace(/\n/g, '<br>')
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
  try {
    // 检查文件类型
    if (!file.raw.type.startsWith('image/')) {
      ElMessage.error('请选择图片文件')
      return
    }
    
    // 检查文件大小（限制为10MB）
    const maxSize = 10 * 1024 * 1024
    if (file.raw.size > maxSize) {
      ElMessage.error('图片大小不能超过10MB')
      return
    }
    
    // 直接转换为base64，不进行压缩
    const base64 = await fileToBase64(file.raw)
    
    const imageData = {
      file: file.raw,
      name: file.name,
      url: base64,
      compressedSize: file.raw.size
    }
    
    selectedImages.value.push(imageData)
    
  } catch (error) {
    console.error('处理图片失败:', error)
    ElMessage.error('处理图片失败，请重试')
  }
}

/**
 * 处理粘贴事件
 */
const handlePaste = async (event) => {
  const items = event.clipboardData?.items
  if (!items) return
  
  for (let i = 0; i < items.length; i++) {
    const item = items[i]
    if (item.type.indexOf('image') !== -1) {
      event.preventDefault()
      const file = item.getAsFile()
      if (file) {
        await handleImageSelect({ raw: file, name: `粘贴图片_${Date.now()}.png` })
      }
    }
  }
}

/**
 * 移除图片
 */
const removeImage = (index) => {
  selectedImages.value.splice(index, 1)
}

/**
 * 预览图片
 */
const previewImage = (url) => {
  currentPreviewImage.value = url
  imagePreviewVisible.value = true
}



/**
 * 文件转base64
 */
const fileToBase64 = (file) => {
  return new Promise((resolve, reject) => {
    const reader = new FileReader()
    reader.onload = () => resolve(reader.result)
    reader.onerror = reject
    reader.readAsDataURL(file)
  })
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
 * 格式化文件大小
 */
const formatFileSize = (bytes) => {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

/**
 * 关闭对话框
 */
const handleClose = () => {
  visible.value = false
  // 清空选中的图片
  selectedImages.value = []
}
</script>

<style scoped>
.chat-drawer :deep(.el-drawer__body) {
  padding: 0;
  display: flex;
  flex-direction: column;
}

.chat-container {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.messages-container {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
  background-color: #f5f7fa;
}

.empty-messages {
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
}

.message-item {
  display: flex;
  margin-bottom: 20px;
  align-items: flex-start;
}

.message-item.user {
  flex-direction: row-reverse;
}

.message-item.user .message-content {
  margin-right: 12px;
  margin-left: 0;
}

.message-item.assistant .message-content {
  margin-left: 12px;
}

.message-avatar {
  flex-shrink: 0;
}

.agent-avatar {
  background-color: #409eff;
}

.message-content {
  flex: 1;
  max-width: calc(100% - 60px);
}

.message-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.message-sender {
  font-weight: 500;
  color: #303133;
  font-size: 14px;
}

.message-time {
  font-size: 12px;
  color: #909399;
}

.message-text {
  background-color: white;
  border-radius: 12px;
  padding: 12px 16px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.message-item.user .message-text {
  background-color: #409eff;
  color: white;
}

.message-body {
  line-height: 1.6;
  word-wrap: break-word;
}

.thinking-section {
  margin-bottom: 12px;
}

.thinking-content {
  font-size: 12px;
  color: #606266;
  background-color: #f5f7fa;
  padding: 8px;
  border-radius: 4px;
  margin: 0;
  white-space: pre-wrap;
}

/* 审读结果样式 */
.review-result {
  margin-bottom: 16px;
  padding: 16px;
  background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
  border-radius: 8px;
  border: 1px solid #dee2e6;
}

.review-header {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: bold;
  color: #495057;
  margin-bottom: 12px;
  font-size: 14px;
}

.review-summary {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 16px;
}

.risk-tag {
  font-weight: bold;
}

.confidence {
  font-size: 12px;
  color: #6c757d;
  background-color: #f8f9fa;
  padding: 4px 8px;
  border-radius: 4px;
}

.flagged-content {
  margin-bottom: 16px;
}

.flagged-header {
  font-weight: bold;
  color: #dc3545;
  margin-bottom: 8px;
  font-size: 13px;
}

.flagged-item {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
  padding: 8px;
  background-color: #fff3cd;
  border-radius: 4px;
  border-left: 3px solid #ffc107;
}

.flagged-text {
  font-style: italic;
  color: #856404;
  flex: 1;
}

.flagged-reason {
  font-size: 12px;
  color: #6c757d;
}

.suggestions {
  margin-top: 12px;
}

.suggestions-header {
  font-weight: bold;
  color: #28a745;
  margin-bottom: 8px;
  font-size: 13px;
}

.suggestions-list {
  margin: 0;
  padding-left: 16px;
}

.suggestions-list li {
  margin-bottom: 4px;
  color: #495057;
  font-size: 13px;
}

/* 增强版审读详细信息样式 */
.enhanced-review-details {
  margin-top: 16px;
  border-top: 1px solid #dee2e6;
  padding-top: 16px;
}

.detection-stats {
  margin-bottom: 16px;
}

.stat-item {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}

.stat-label {
  font-weight: 500;
  color: #495057;
  font-size: 13px;
  min-width: 80px;
}

.execution-path {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
}

.path-step {
  font-size: 11px;
}

.tree-structure {
  margin-top: 12px;
}

.tree-header {
  font-weight: 500;
  color: #495057;
  margin-bottom: 8px;
  font-size: 13px;
}

.tree-content {
  background-color: #f8f9fa;
  border: 1px solid #dee2e6;
  border-radius: 4px;
  padding: 12px;
  font-size: 11px;
  max-height: 300px;
  overflow-y: auto;
  color: #495057;
  line-height: 1.4;
}

/* 异步任务状态样式 */
.task-status {
  margin-bottom: 16px;
  padding: 16px;
  background-color: #e3f2fd;
  border-radius: 8px;
  border: 1px solid #bbdefb;
}

.task-header {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: bold;
  color: #1976d2;
  margin-bottom: 12px;
  font-size: 14px;
}

.task-progress {
  margin-bottom: 12px;
}

.task-actions {
  display: flex;
  gap: 8px;
}

.tool-calls {
  margin-top: 12px;
  border-top: 1px solid #ebeef5;
  padding-top: 12px;
}

.tool-calls-header {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  color: #606266;
  margin-bottom: 8px;
}

.tool-call-item {
  background-color: #f5f7fa;
  border-radius: 6px;
  padding: 8px;
  margin-bottom: 8px;
}

.tool-call-name {
  font-weight: 500;
  color: #409eff;
  margin-bottom: 4px;
}

.tool-call-args,
.tool-call-result {
  font-size: 12px;
}

.tool-call-args pre,
.tool-call-result pre {
  margin: 4px 0 0 0;
  white-space: pre-wrap;
  word-break: break-all;
}

.message-actions {
  margin-top: 8px;
  display: flex;
  gap: 8px;
  opacity: 0;
  transition: opacity 0.2s;
}

.message-item:hover .message-actions {
  opacity: 1;
}

.typing-indicator {
  display: flex;
  align-items: flex-start;
  margin-bottom: 20px;
}

.typing-content {
  margin-left: 12px;
  background-color: white;
  border-radius: 12px;
  padding: 12px 16px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.typing-dots {
  display: flex;
  gap: 4px;
}

.typing-dots span {
  width: 6px;
  height: 6px;
  background-color: #c0c4cc;
  border-radius: 50%;
  animation: typing 1.4s infinite;
}

.typing-dots span:nth-child(2) {
  animation-delay: 0.2s;
}

.typing-dots span:nth-child(3) {
  animation-delay: 0.4s;
}

@keyframes typing {
  0%, 60%, 100% {
    transform: translateY(0);
    opacity: 0.5;
  }
  30% {
    transform: translateY(-10px);
    opacity: 1;
  }
}

.input-container {
  border-top: 1px solid #ebeef5;
  background-color: white;
  padding: 16px 20px;
}

.input-wrapper {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.message-input {
  resize: none;
}

.input-actions {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.input-tips {
  font-size: 12px;
  color: #909399;
}

.input-buttons {
  display: flex;
  gap: 8px;
}

/* 自定义头部样式 */

.drawer-header {
  margin: 0;
}

.header-content {
  display: flex;
  align-items: center;
  gap: 20px;
}

.drawer-title {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
  color: #303133;
}

.chat-info-item {
  font-size: 14px;
  opacity: 0.9;
  white-space: nowrap;
}

.chat-info {
  display: flex;
  gap: 16px;
  font-size: 12px;
  color: #909399;
}

/* 图片相关样式 */
.image-preview-container {
  background-color: #f5f7fa;
  border-radius: 8px;
  padding: 12px;
  margin-bottom: 8px;
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
  background-color: white;
  border: 1px solid #dcdfe6;
}

.preview-thumbnail {
  width: 100%;
  height: 60px;
  object-fit: cover;
  cursor: pointer;
  transition: transform 0.2s;
}

.preview-thumbnail:hover {
  transform: scale(1.05);
}

.image-info {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  background: rgba(0, 0, 0, 0.7);
  color: white;
  font-size: 10px;
  padding: 2px 4px;
  text-align: center;
}

.remove-image-btn {
  position: absolute;
  top: -6px;
  right: -6px;
  width: 20px;
  height: 20px;
  min-height: 20px;
  padding: 0;
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

/* 消息中的图片样式 */
.message-images {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 8px;
}

.message-image-item {
  max-width: 200px;
}

.message-image {
  width: 100%;
  max-width: 200px;
  height: auto;
  border-radius: 6px;
  cursor: pointer;
  transition: transform 0.2s;
  border: 1px solid #dcdfe6;
}

.message-image:hover {
  transform: scale(1.02);
}

.image-name {
  font-size: 12px;
  color: #909399;
  margin-top: 4px;
  text-align: center;
  word-break: break-all;
}

.message-text-content {
  margin-top: 8px;
}

/* 图片预览对话框样式 */
.image-preview-dialog {
  text-align: center;
}

.preview-image {
  max-width: 100%;
  max-height: 70vh;
  object-fit: contain;
  border-radius: 6px;
}

/* 滚动条样式 */
.messages-container::-webkit-scrollbar {
  width: 6px;
}

.messages-container::-webkit-scrollbar-track {
  background: #f1f1f1;
  border-radius: 3px;
}

.messages-container::-webkit-scrollbar-thumb {
  background: #c1c1c1;
  border-radius: 3px;
}

.messages-container::-webkit-scrollbar-thumb:hover {
  background: #a8a8a8;
}

:deep(.el-collapse-item__header) {
  font-size: 12px;
  padding: 8px 0;
}

:deep(.el-collapse-item__content) {
  padding: 8px 0;
}

/* 抽屉样式定制 */
.chat-drawer :deep(.el-drawer__header) {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 16px 20px;
  margin: 0;
  border-bottom: none;
}

.chat-drawer :deep(.el-drawer__title) {
  color: white;
  font-weight: 600;
  font-size: 18px;
}

.chat-drawer :deep(.el-drawer__close-btn) {
  color: white;
  font-size: 20px;
}

.chat-drawer :deep(.el-drawer__close-btn):hover {
  color: #f0f0f0;
}

.chat-drawer .chat-container {
  height: calc(100vh - 80px);
}

/* 响应式设计 */
@media (max-width: 1400px) {
  .chat-drawer {
    --el-drawer-size: 1000px;
  }
}

@media (max-width: 1200px) {
  .chat-drawer {
    --el-drawer-size: 900px;
  }
}

@media (max-width: 1000px) {
  .chat-drawer {
    --el-drawer-size: 100%;
  }
}
</style>