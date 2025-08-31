<template>
  <el-dialog
    v-model="visible"
    :title="dialogTitle"
    width="800px"
    :close-on-click-modal="false"
    :close-on-press-escape="false"
    @close="handleClose"
  >
    <div v-if="loading" class="modal-loading">
      <el-skeleton :rows="8" animated />
    </div>
    <el-form
      v-else
      ref="formRef"
      :model="formData"
      :rules="formRules"
      label-width="100px"
      label-position="left"
    >
      <!-- 基本信息 -->
      <el-card class="config-section" shadow="never">
        <template #header>
          <div class="section-header">
            <el-icon><Setting /></el-icon>
            <span>基本信息</span>
          </div>
        </template>
        
        <el-form-item label="节点标题" prop="title">
          <el-input
            v-model="formData.title"
            placeholder="请输入节点标题"
            maxlength="100"
            show-word-limit
          />
        </el-form-item>
        
        <el-form-item label="节点类型" prop="node_type">
          <el-select
            v-model="formData.node_type"
            placeholder="请选择节点类型"
            :disabled="isEdit"
            @change="handleNodeTypeChange"
          >
            <el-option
              v-for="type in nodeTypes"
              :key="type.value"
              :label="type.label"
              :value="type.value"
            >
              <div class="node-type-option">
                <el-icon :color="type.color">
                  <component :is="type.icon" />
                </el-icon>
                <span>{{ type.label }}</span>
                <span class="type-desc">{{ type.description }}</span>
              </div>
            </el-option>
          </el-select>
          <div class="form-help-text">
            选择合适的节点类型来定义节点的功能和行为
          </div>
        </el-form-item>
        
        <el-form-item label="排序" prop="sort_order">
          <el-input-number
            v-model="formData.sort_order"
            :min="1"
            :max="999"
            controls-position="right"
          />
        </el-form-item>
        
        <el-form-item label="状态">
          <el-switch
            v-model="formData.is_active"
            active-text="启用"
            inactive-text="禁用"
          />
        </el-form-item>
        
        <el-form-item label="风险等级" prop="risk_level">
          <el-select
            v-model="formData.risk_level"
            placeholder="请选择风险等级"
            clearable
          >
            <el-option label="安全" value="safe">
              <el-tag type="success" size="small">安全</el-tag>
            </el-option>
            <el-option label="低风险" value="low">
              <el-tag type="info" size="small">低风险</el-tag>
            </el-option>
            <el-option label="中等风险" value="medium">
              <el-tag type="warning" size="small">中等风险</el-tag>
            </el-option>
            <el-option label="高风险" value="high">
              <el-tag type="danger" size="small">高风险</el-tag>
            </el-option>
            <el-option label="严重风险" value="critical">
              <el-tag type="danger" size="small" effect="dark">严重风险</el-tag>
            </el-option>
          </el-select>
          <div class="form-help-text">
            设置节点的风险等级，用于安全评估和风险控制
          </div>
        </el-form-item>
      </el-card>
      
      <!-- 条件配置 -->
      <el-card v-if="formData.node_type === 'CONDITION'" class="config-card" shadow="never">
        <template #header>
          <div class="card-header">
            <el-icon><QuestionFilled /></el-icon>
            <span>条件配置</span>
          </div>
        </template>
        
        <div class="config-description">
          配置条件判断逻辑和相关参数
        </div>
        
        <el-form-item label="指令类型" prop="condition_type">
          <el-select v-model="formData.condition_type" placeholder="请选择条件类型">
            <el-option label="AI分类判断" value="AI_CLASSIFICATION" />
            <el-option label="文本匹配" value="TEXT_MATCH" />
            <el-option label="正则表达式" value="REGEX" />
            <el-option label="关键词检测" value="KEYWORD" />
            <el-option label="情感分析" value="SENTIMENT_ANALYSIS" />
            <el-option label="内容安全检测" value="CONTENT_SAFETY" />
            <el-option label="自定义函数" value="CUSTOM_FUNCTION" />
          </el-select>
          <div class="form-help-text">
            选择适合的条件类型来定义判断逻辑
          </div>
        </el-form-item>
        
        <el-form-item label="指令文本" prop="condition_text">
          <el-input
            v-model="formData.condition_text"
            type="textarea"
            :rows="3"
            placeholder="请输入条件描述或判断文本"
          />
          <div class="form-help-text">
            描述具体的判断条件，如分类标签、匹配文本等
          </div>
        </el-form-item>
        
        <el-form-item label="关键词" prop="keywords">
          <el-select
            v-model="formData.keywords"
            multiple
            filterable
            allow-create
            default-first-option
            placeholder="请输入关键词，按回车添加"
            style="width: 100%"
          >
          </el-select>
          <div class="form-help-text">
            用于条件匹配的关键词列表，支持多个关键词
          </div>
        </el-form-item>
        

      </el-card>
    </el-form>
    
    <template #footer>
      <div class="dialog-footer">
        <el-button @click="handleClose">取消</el-button>
        <el-button type="primary" :loading="submitting" @click="handleSubmit">
          {{ isEdit ? '更新' : '创建' }}
        </el-button>
      </div>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, reactive, computed, watch, nextTick } from 'vue'
import { ElMessage } from 'element-plus'
import {
  Setting,
  QuestionFilled,
  VideoPlay,
  Connection
} from '@element-plus/icons-vue'
import { instructionNodeApi } from '@/api/instruction-set'
import type {
  InstructionTreeNode,
  InstructionNodeCreate,
  InstructionNodeUpdate,
  InstructionNodeFormData,
  NodeType,
  ConditionType,
  RiskLevel
} from '@/types/instruction-set'

// Props
interface Props {
  modelValue: boolean
  node?: InstructionTreeNode | null
  parentNode?: InstructionTreeNode | null
  instructionSetId: number
}

const props = withDefaults(defineProps<Props>(), {
  node: null,
  parentNode: null
})

// Emits
const emit = defineEmits<{
  'update:modelValue': [value: boolean]
  submit: []
}>()

// 响应式数据
const formRef = ref()
const loading = ref(false)
const submitting = ref(false)

// 计算属性
const visible = computed({
  get: () => props.modelValue,
  set: (value) => emit('update:modelValue', value)
})

const isEdit = computed(() => !!props.node?.id)

const dialogTitle = computed(() => {
  return isEdit.value ? '编辑节点' : '创建节点'
})

// 表单数据
const formData = reactive<InstructionNodeFormData & { id?: number; parent_id?: number | null }>({
  title: '',
  description: '',
  node_type: 'CONDITION' as NodeType,
  parent_id: null,
  condition_text: '',
  condition_type: 'AI_CLASSIFICATION' as ConditionType,
  keywords: [],
  metadata: {},
  sort_order: 0,
  is_active: true,
  risk_level: undefined
})

// 表单验证规则
const formRules = {
  title: [
    { required: true, message: '请输入节点标题', trigger: 'blur' },
    { min: 1, max: 100, message: '标题长度在 1 到 100 个字符', trigger: 'blur' }
  ],
  node_type: [
    { required: true, message: '请选择节点类型', trigger: 'change' }
  ],
  condition_type: [
    { required: true, message: '请选择条件类型', trigger: 'change' }
  ],
  keywords: [
    { type: 'array', message: '关键词必须是数组格式', trigger: 'change' }
  ],
  sort_order: [
    { required: true, message: '请输入排序', trigger: 'blur' },
    { type: 'number', min: 1, max: 999, message: '排序必须在 1 到 999 之间', trigger: 'blur' }
  ]
}

// 节点类型选项 - 目前只允许选择CONDITION类型
const nodeTypes = [
  {
    value: 'CONDITION',
    label: '条件节点',
    description: '用于判断条件',
    icon: QuestionFilled,
    color: '#409eff'
  }
  // 其他节点类型暂时保留但不可选择
  // {
  //   value: 'EXECUTOR',
  //   label: '执行器节点',
  //   description: '执行器根节点，协调整个流程',
  //   icon: Setting,
  //   color: '#f56c6c'
  // },
  // {
  //   value: 'ACTION',
  //   label: '动作节点',
  //   description: '执行具体动作',
  //   icon: VideoPlay,
  //   color: '#67c23a'
  // },
  // {
  //   value: 'BRANCH',
  //   label: '分支节点',
  //   description: '控制流程分支',
  //   icon: Connection,
  //   color: '#e6a23c'
  // },
  // {
  //   value: 'AGGREGATOR',
  //   label: '聚合器节点',
  //   description: '聚合多个节点的结果',
  //   icon: Connection,
  //   color: '#909399'
  // },
  // {
  //   value: 'CLASSIFIER',
  //   label: '分类器节点',
  //   description: '对内容进行分类',
  //   icon: Setting,
  //   color: '#606266'
  // },
  // {
  //   value: 'RESULT',
  //   label: '结果节点',
  //   description: '输出最终结果',
  //   icon: VideoPlay,
  //   color: '#67c23a'
  // }
]

/**
 * 获取评分类型标签
 */
const getScoreTypeLabel = (scoreType: string): string => {
  const labels: Record<string, string> = {
    'ACCURACY': '准确性',
    'CONFIDENCE': '置信度',
    'PERFORMANCE': '性能',
    'RELEVANCE': '相关性',
    'SAFETY': '安全性'
  }
  return labels[scoreType] || scoreType
}



/**
 * 监听对话框显示状态
 */
watch(
  () => props.modelValue,
  (newVal) => {
    if (newVal) {
      initForm()
    }
  }
)

/**
 * 初始化表单
 */
const initForm = async () => {
  if (isEdit.value && props.node) {
    // 编辑模式，加载节点详情
    loading.value = true
    try {
      const response = await instructionNodeApi.getInstructionNode(props.node.id)
      if (response.success && response.data) {
        // 直接使用后端返回的扁平化数据结构
        Object.assign(formData, {
          id: response.data.id,
          title: response.data.title || '',
          description: response.data.description || '',
          node_type: response.data.node_type || 'CONDITION',
          parent_id: response.data.parent_id || null,
          sort_order: response.data.sort_order || 1,
          condition_text: response.data.condition_text || '',
          condition_type: response.data.condition_type || 'AI_CLASSIFICATION',
          keywords: response.data.keywords ? response.data.keywords.split(',').map(k => k.trim()).filter(k => k) : [],
          metadata: response.data.metadata || {},
          is_active: response.data.is_active !== undefined ? response.data.is_active : true,
          risk_level: response.data.risk_level || undefined
        })
      }
    } catch (error) {
      console.error('加载节点详情失败:', error)
      ElMessage.error('加载节点详情失败')
    } finally {
      loading.value = false
    }
  } else {
    // 创建模式，重置表单
    Object.assign(formData, {
      title: '',
      description: '',
      node_type: 'CONDITION' as NodeType,
      parent_id: props.parentNode?.id || null,
      sort_order: 1,
      condition_text: '',
      condition_type: 'AI_CLASSIFICATION' as ConditionType,
      keywords: [],
      metadata: {},
      is_active: true,
      risk_level: undefined
    })
  }
  
  // 重置表单验证
  await nextTick()
  formRef.value?.clearValidate()
}

/**
 * 节点类型变更处理
 */
const handleNodeTypeChange = (nodeType: NodeType) => {
  // 现在使用扁平化结构，根据节点类型设置默认值
  switch (nodeType) {
    case 'CONDITION':
      formData.condition_type = 'AI_CLASSIFICATION'
      break
    // 其他节点类型可以根据需要添加默认值设置
  }
}


 
 /**
  * 提交表单
  */
const handleSubmit = async () => {
  try {
    // 表单验证
    await formRef.value?.validate()
    
    submitting.value = true
    
    if (isEdit.value && props.node) {
      // 更新节点
      const updateData: InstructionNodeUpdate = {
        title: formData.title,
        description: formData.description,
        keywords: Array.isArray(formData.keywords) ? formData.keywords.join(',') : formData.keywords,
        sort_order: formData.sort_order,
        is_active: formData.is_active,
        condition_text: formData.condition_text,
        condition_type: formData.condition_type,
        risk_level: formData.risk_level,
        metadata: formData.metadata
      }
      
      const response = await instructionNodeApi.updateInstructionNode(props.node.id, updateData)
      if (response.success) {
        ElMessage.success('更新成功')
        emit('submit')
      }
    } else {
      // 创建节点
      const createData: InstructionNodeCreate = {
        instruction_set_id: props.instructionSetId,
        title: formData.title,
        description: formData.description,
        keywords: Array.isArray(formData.keywords) ? formData.keywords.join(',') : formData.keywords,
        node_type: formData.node_type,
        parent_id: formData.parent_id,
        sort_order: formData.sort_order,
        is_active: formData.is_active,
        condition_text: formData.condition_text,
        condition_type: formData.condition_type,
        risk_level: formData.risk_level,
        metadata: formData.metadata
      }
      
      const response = await instructionNodeApi.createInstructionNode(props.instructionSetId, createData)
      if (response.success) {
        ElMessage.success('创建成功')
        emit('submit')
      }
    }
  } catch (error) {
    if (error !== 'validation failed') {
      console.error('提交失败:', error)
      ElMessage.error('提交失败')
    }
  } finally {
    submitting.value = false
  }
}

/**
 * 关闭对话框
 */
const handleClose = () => {
  visible.value = false
}
</script>

<style scoped>
.modal-loading {
  padding: 20px;
}

.config-section {
  margin-bottom: 16px;
}

.config-section:last-child {
  margin-bottom: 0;
}

.section-header {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 600;
}

.node-type-option {
  display: flex;
  align-items: center;
  gap: 8px;
  width: 100%;
}

.type-desc {
  margin-left: auto;
  font-size: 12px;
  color: var(--el-text-color-placeholder);
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}

/* 表单样式优化 */
:deep(.el-form-item__label) {
  font-weight: 500;
}

:deep(.el-card__header) {
  padding: 12px 16px;
  background-color: var(--el-fill-color-lighter);
}

:deep(.el-card__body) {
  padding: 16px;
}

/* 权重配置样式 */
.weight-config {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.weight-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 12px;
  background-color: #f5f7fa;
  border-radius: 6px;
}

.weight-label {
  font-weight: 500;
  color: #606266;
  min-width: 80px;
}

/* 分类器配置样式 */
.category-config {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.category-item {
   display: flex;
   align-items: center;
   gap: 8px;
   padding: 8px;
   background-color: #f8f9fa;
   border-radius: 4px;
 }
 
 /* 早停条件配置样式 */
 .early-stop-config {
   display: flex;
   flex-direction: column;
   gap: 12px;
 }
 
 .early-stop-item {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 8px;
    background-color: #f0f9ff;
    border: 1px solid #e1f5fe;
    border-radius: 4px;
  }
  
  /* 验证规则配置样式 */
   .validation-rules {
     display: flex;
     flex-direction: column;
     gap: 12px;
   }
   
   .validation-rule {
     display: flex;
     align-items: center;
     gap: 8px;
     padding: 8px;
     background-color: #fff7e6;
     border: 1px solid #ffd591;
     border-radius: 4px;
   }
   
   /* 用户界面优化样式 */
   .config-description {
     font-size: 13px;
     color: #666;
     margin-bottom: 16px;
     padding: 8px 12px;
     background-color: #f8f9fa;
     border-left: 3px solid #409eff;
     border-radius: 4px;
   }
   
   .form-help-text {
     font-size: 12px;
     color: #909399;
     margin-top: 4px;
     line-height: 1.4;
   }
   
   h4 {
     display: flex;
     align-items: center;
     gap: 8px;
     margin: 20px 0 12px 0;
     font-size: 16px;
     font-weight: 600;
     color: #303133;
   }
   
   /* 复杂条件构建器样式 */
.complex-condition-builder {
  border: 1px solid #e4e7ed;
  border-radius: 6px;
  padding: 16px;
  background-color: #fafafa;
}

.condition-group {
  margin-bottom: 16px;
  padding: 12px;
  border: 1px solid #dcdfe6;
  border-radius: 4px;
  background-color: #ffffff;
}

.condition-group:last-child {
  margin-bottom: 0;
}

.group-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 12px;
  padding-bottom: 8px;
  border-bottom: 1px solid #f0f0f0;
}

.condition-items {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.condition-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px;
  background-color: #f8f9fa;
  border-radius: 4px;
}

/* 响应式设计 */
@media (max-width: 768px) {
  :deep(.el-dialog) {
    width: 95% !important;
    margin: 5vh auto;
  }
  
  :deep(.el-form--label-left .el-form-item__label) {
    text-align: left;
    width: 100% !important;
    margin-bottom: 8px;
  }
  
  :deep(.el-form-item__content) {
    margin-left: 0 !important;
  }
  
  .condition-item {
    flex-direction: column;
    align-items: stretch;
  }
  
  .condition-item > * {
    margin-bottom: 8px;
  }
  
  .condition-item > *:last-child {
    margin-bottom: 0;
  }
}
</style>