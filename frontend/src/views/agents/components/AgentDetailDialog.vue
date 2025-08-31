<template>
  <el-dialog
    v-model="visible"
    title="智能体详情"
    width="800px"
    :before-close="handleClose"
  >
    <div v-if="agent" class="agent-detail">
      <!-- 基本信息 -->
      <div class="detail-section">
        <h3 class="section-title">基本信息</h3>
        <el-row :gutter="20">
          <el-col :span="12">
            <div class="detail-item">
              <label>名称：</label>
              <span>{{ agent.name }}</span>
            </div>
          </el-col>
          <el-col :span="12">
            <div class="detail-item">
              <label>类型：</label>
              <el-tag>{{ getAgentTypeLabel(agent.agent_type) }}</el-tag>
            </div>
          </el-col>

          <el-col :span="12">
            <div class="detail-item">
              <label>状态：</label>
              <el-tag :type="getStatusType(agent.status)">{{ getStatusLabel(agent.status) }}</el-tag>
            </div>
          </el-col>
          <el-col :span="12">
            <div class="detail-item">
              <label>可见性：</label>
              <el-tag :type="agent.is_public ? 'success' : 'info'">
                {{ agent.is_public ? '公开' : '私有' }}
              </el-tag>
            </div>
          </el-col>
          <el-col :span="24">
            <div class="detail-item">
              <label>描述：</label>
              <span>{{ agent.description || '暂无描述' }}</span>
            </div>
          </el-col>
        </el-row>
      </div>

      <!-- 模型配置 -->
      <div class="detail-section">
        <h3 class="section-title">模型配置</h3>
        <el-row :gutter="20">
          <el-col :span="12">
            <div class="detail-item">
              <label>模型：</label>
              <span>{{ agent.model_name || '未指定' }}</span>
            </div>
          </el-col>
          <el-col :span="12">
            <div class="detail-item">
              <label>记忆功能：</label>
              <el-tag :type="agent.memory_enabled ? 'success' : 'info'">
                {{ agent.memory_enabled ? '已启用' : '未启用' }}
              </el-tag>
            </div>
          </el-col>
        </el-row>
        
        <!-- 模型参数 -->
        <div v-if="agent.model_config" class="config-section">
          <h4>模型参数</h4>
          <el-descriptions :column="2" border>
            <el-descriptions-item
              v-for="(value, key) in agent.model_config"
              :key="key"
              :label="getConfigLabel(key)"
            >
              {{ formatConfigValue(key, value) }}
            </el-descriptions-item>
          </el-descriptions>
        </div>
      </div>

      <!-- 提示词配置 -->
      <div class="detail-section">
        <h3 class="section-title">提示词配置</h3>
        <div class="prompt-section">
          <h4>系统提示词</h4>
          <div class="prompt-content">
            {{ agent.system_prompt || '暂无系统提示词' }}
          </div>
        </div>
        <div class="prompt-section">
          <h4>用户提示词模板</h4>
          <div class="prompt-content">
            {{ agent.user_prompt_template || '暂无用户提示词模板' }}
          </div>
        </div>
      </div>

      <!-- 工具配置 -->
      <div class="detail-section">
        <h3 class="section-title">工具配置</h3>
        <div v-if="agent.tools && agent.tools.length > 0">
          <el-tag
            v-for="tool in agent.tools"
            :key="tool"
            class="tool-tag"
            type="primary"
          >
            {{ tool }}
          </el-tag>
        </div>
        <div v-else class="no-data">
          暂无配置工具
        </div>
        
        <!-- 工具参数 -->
        <div v-if="agent.tool_config" class="config-section">
          <h4>工具参数</h4>
          <el-descriptions :column="1" border>
            <el-descriptions-item
              v-for="(value, key) in agent.tool_config"
              :key="key"
              :label="key"
            >
              <pre>{{ JSON.stringify(value, null, 2) }}</pre>
            </el-descriptions-item>
          </el-descriptions>
        </div>
      </div>

      <!-- 指令集配置 -->
      <div v-if="agent.category === 'review' && agent.instruction_set_id" class="detail-section">
        <h3 class="section-title">指令集配置</h3>
        <div class="instruction-set-info">
          <div class="detail-item">
            <label>关联指令集：</label>
            <el-tag type="warning">{{ instructionSetName || '加载中...' }}</el-tag>
          </div>
          <div v-if="instructionSetDescription" class="detail-item">
            <label>指令集描述：</label>
            <span>{{ instructionSetDescription }}</span>
          </div>
        </div>
      </div>

      <!-- 权限配置 -->
      <div class="detail-section">
        <h3 class="section-title">权限配置</h3>
        <el-row :gutter="20">
          <el-col :span="24">
            <div class="detail-item">
              <label>允许使用的用户：</label>
              <div v-if="agent.allowed_users && agent.allowed_users.length > 0">
                <el-tag
                  v-for="userId in agent.allowed_users"
                  :key="userId"
                  class="user-tag"
                >
                  用户ID: {{ userId }}
                </el-tag>
              </div>
              <span v-else>{{ agent.is_public ? '所有用户' : '仅创建者' }}</span>
            </div>
          </el-col>
        </el-row>
      </div>

      <!-- 标签和元数据 -->
      <div class="detail-section">
        <h3 class="section-title">标签和元数据</h3>
        <el-row :gutter="20">
          <el-col :span="24">
            <div class="detail-item">
              <label>标签：</label>
              <div v-if="agent.tags && agent.tags.length > 0">
                <el-tag
                  v-for="tag in agent.tags"
                  :key="tag"
                  class="tag-item"
                  type="info"
                >
                  {{ tag }}
                </el-tag>
              </div>
              <span v-else>暂无标签</span>
            </div>
          </el-col>
          <el-col :span="24" v-if="agent.metadata">
            <div class="detail-item">
              <label>元数据：</label>
              <pre class="metadata-content">{{ JSON.stringify(agent.metadata, null, 2) }}</pre>
            </div>
          </el-col>
        </el-row>
      </div>

      <!-- 使用统计 -->
      <div class="detail-section">
        <h3 class="section-title">使用统计</h3>
        <el-row :gutter="20">
          <el-col :span="8">
            <div class="stat-item">
              <div class="stat-value">{{ agent.usage_count }}</div>
              <div class="stat-label">使用次数</div>
            </div>
          </el-col>
          <el-col :span="8">
            <div class="stat-item">
              <div class="stat-value">{{ formatDate(agent.last_used_at) || '从未使用' }}</div>
              <div class="stat-label">最后使用时间</div>
            </div>
          </el-col>
          <el-col :span="8">
            <div class="stat-item">
              <div class="stat-value">{{ formatDate(agent.created_at) }}</div>
              <div class="stat-label">创建时间</div>
            </div>
          </el-col>
        </el-row>
      </div>

      <!-- 创建信息 -->
      <div class="detail-section">
        <h3 class="section-title">创建信息</h3>
        <el-row :gutter="20">
          <el-col :span="12">
            <div class="detail-item">
              <label>创建者：</label>
              <span>{{ agent.creator_name || '未知' }}</span>
            </div>
          </el-col>
          <el-col :span="12">
            <div class="detail-item">
              <label>更新者：</label>
              <span>{{ agent.updater_name || '未知' }}</span>
            </div>
          </el-col>
          <el-col :span="12">
            <div class="detail-item">
              <label>创建时间：</label>
              <span>{{ formatDate(agent.created_at) }}</span>
            </div>
          </el-col>
          <el-col :span="12">
            <div class="detail-item">
              <label>更新时间：</label>
              <span>{{ formatDate(agent.updated_at) }}</span>
            </div>
          </el-col>
        </el-row>
      </div>
    </div>

    <template #footer>
      <div class="dialog-footer">
        <el-button @click="handleClose">关闭</el-button>
        <el-button type="primary" @click="handleEdit">编辑</el-button>

      </div>
    </template>
  </el-dialog>
</template>

<script setup>
import { computed, ref, watch } from 'vue'
import { formatDate } from '@/utils/date'
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
const emit = defineEmits(['update:modelValue', 'edit'])

// 响应式数据
const instructionSetName = ref('')
const instructionSetDescription = ref('')

// 计算属性
const visible = computed({
  get: () => props.modelValue,
  set: (value) => emit('update:modelValue', value)
})

// 监听智能体变化，加载指令集信息
watch(() => props.agent, async (newAgent) => {
  if (newAgent && newAgent.category === 'review' && newAgent.instruction_set_id) {
    await loadInstructionSet(newAgent.instruction_set_id)
  } else {
    instructionSetName.value = ''
    instructionSetDescription.value = ''
  }
}, { immediate: true })

/**
 * 加载指令集信息
 */
const loadInstructionSet = async (instructionSetId) => {
  try {
    const response = await instructionSetApi.getInstructionSet(instructionSetId)
    instructionSetName.value = response.name
    instructionSetDescription.value = response.description
  } catch (error) {
    console.error('加载指令集信息失败:', error)
    instructionSetName.value = '加载失败'
    instructionSetDescription.value = ''
  }
}

/**
 * 关闭对话框
 */
const handleClose = () => {
  visible.value = false
}

/**
 * 处理编辑
 */
const handleEdit = () => {
  emit('edit', props.agent)
  handleClose()
}



/**
 * 获取智能体类型标签
 */
const getAgentTypeLabel = (type) => {
  const typeMap = {
    CHAT: '聊天助手',
    CODE: '代码助手',
    DOCUMENT: '文档助手',
    ANALYSIS: '分析助手',
    WORKFLOW: '工作流助手',
    CUSTOM: '自定义'
  }
  return typeMap[type] || type
}

/**
 * 获取状态类型
 */
const getStatusType = (status) => {
  const statusTypeMap = {
    DRAFT: 'info',
    draft: 'info',
    ACTIVE: 'success',
    active: 'success',
    INACTIVE: 'warning',
    inactive: 'warning'
  }
  return statusTypeMap[status] || 'info'
}

/**
 * 获取状态标签
 */
const getStatusLabel = (status) => {
  const statusMap = {
    DRAFT: '草稿',
    draft: '草稿',
    ACTIVE: '活跃',
    active: '活跃',
    INACTIVE: '已停用',
    inactive: '已停用'
  }
  return statusMap[status] || status
}



/**
 * 获取配置标签
 */
const getConfigLabel = (key) => {
  const labelMap = {
    temperature: '温度',
    max_tokens: '最大Token数',
    top_p: 'Top-p',
    top_k: 'Top-k',
    frequency_penalty: '频率惩罚',
    presence_penalty: '存在惩罚',
    stop_sequences: '停止序列'
  }
  return labelMap[key] || key
}

/**
 * 格式化配置值
 */
const formatConfigValue = (key, value) => {
  if (Array.isArray(value)) {
    return value.join(', ')
  }
  if (typeof value === 'object') {
    return JSON.stringify(value)
  }
  return value
}
</script>

<style scoped>
.agent-detail {
  max-height: 600px;
  overflow-y: auto;
}

.detail-section {
  margin-bottom: 24px;
  padding-bottom: 16px;
  border-bottom: 1px solid #ebeef5;
}

.detail-section:last-child {
  border-bottom: none;
  margin-bottom: 0;
}

.section-title {
  margin: 0 0 16px 0;
  font-size: 16px;
  font-weight: 600;
  color: #303133;
  border-left: 3px solid #409eff;
  padding-left: 8px;
}

.detail-item {
  margin-bottom: 12px;
  display: flex;
  align-items: flex-start;
}

.detail-item label {
  min-width: 100px;
  font-weight: 500;
  color: #606266;
  margin-right: 8px;
}

.detail-item span {
  flex: 1;
  color: #303133;
}

.config-section {
  margin-top: 16px;
}

.config-section h4 {
  margin: 0 0 12px 0;
  font-size: 14px;
  font-weight: 500;
  color: #606266;
}

.prompt-section {
  margin-bottom: 16px;
}

.prompt-section h4 {
  margin: 0 0 8px 0;
  font-size: 14px;
  font-weight: 500;
  color: #606266;
}

.prompt-content {
  background-color: #f5f7fa;
  border: 1px solid #dcdfe6;
  border-radius: 4px;
  padding: 12px;
  font-family: 'Courier New', monospace;
  font-size: 12px;
  line-height: 1.5;
  white-space: pre-wrap;
  word-break: break-all;
  max-height: 200px;
  overflow-y: auto;
}

.tool-tag {
  margin-right: 8px;
  margin-bottom: 8px;
}

.user-tag {
  margin-right: 8px;
  margin-bottom: 8px;
}

.tag-item {
  margin-right: 8px;
  margin-bottom: 8px;
}

.metadata-content {
  background-color: #f5f7fa;
  border: 1px solid #dcdfe6;
  border-radius: 4px;
  padding: 12px;
  font-family: 'Courier New', monospace;
  font-size: 12px;
  line-height: 1.5;
  max-height: 200px;
  overflow-y: auto;
  margin: 0;
}

.stat-item {
  text-align: center;
  padding: 16px;
  background-color: #f5f7fa;
  border-radius: 8px;
}

.stat-value {
  font-size: 24px;
  font-weight: 600;
  color: #409eff;
  margin-bottom: 4px;
}

.stat-label {
  font-size: 12px;
  color: #909399;
}

.no-data {
  color: #909399;
  font-style: italic;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}

:deep(.el-descriptions__label) {
  font-weight: 500;
  color: #606266;
}

:deep(.el-descriptions__content) {
  color: #303133;
}

:deep(.el-descriptions__content pre) {
  margin: 0;
  font-family: 'Courier New', monospace;
  font-size: 12px;
  white-space: pre-wrap;
  word-break: break-all;
}
</style>