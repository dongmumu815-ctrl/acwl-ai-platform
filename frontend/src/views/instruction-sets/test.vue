<template>
  <div class="instruction-test-page">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="header-left">
        <el-button
          type="text"
          @click="$router.go(-1)"
        >
          <el-icon><ArrowLeft /></el-icon>
          返回
        </el-button>
        <div class="header-info">
          <h2 class="page-title">
            <el-icon><VideoPlay /></el-icon>
            指令集测试
          </h2>
          <div v-if="instructionSet" class="instruction-info">
            <span class="instruction-name">{{ instructionSet.name }}</span>
            <el-tag :type="instructionSet.status === 'active' ? 'success' : 'info'" size="small">
              {{ instructionSet.status === 'active' ? '已启用' : '已禁用' }}
            </el-tag>
          </div>
        </div>
      </div>
      <div class="header-actions">
        <el-button @click="handleViewDetail">
          <el-icon><View /></el-icon>
          查看详情
        </el-button>
      </div>
    </div>

    <!-- 测试区域 -->
    <div class="test-content">
      <el-row :gutter="24">
        <!-- 测试输入 -->
        <el-col :span="12">
          <el-card class="test-input-card" shadow="never">
            <template #header>
              <div class="card-header">
                <el-icon><Edit /></el-icon>
                <span>测试输入</span>
              </div>
            </template>
            
            <el-form :model="testForm" label-width="80px">
              <el-form-item label="测试内容">
                <el-input
                  v-model="testForm.content"
                  type="textarea"
                  :rows="8"
                  placeholder="请输入要测试的内容..."
                  maxlength="5000"
                  show-word-limit
                />
              </el-form-item>
              
              <el-form-item label="测试模式">
                <el-radio-group v-model="testForm.mode">
                  <el-radio value="normal">正常模式</el-radio>
                <el-radio value="debug">调试模式</el-radio>
                </el-radio-group>
              </el-form-item>
              
              <el-form-item label="超时设置">
                <el-input-number
                  v-model="testForm.timeout"
                  :min="1"
                  :max="300"
                  controls-position="right"
                >
                  <template #append>秒</template>
                </el-input-number>
              </el-form-item>
              
              <el-form-item>
                <el-button
                  type="primary"
                  :loading="testing"
                  :disabled="!testForm.content.trim()"
                  @click="handleRunTest"
                >
                  <el-icon><VideoPlay /></el-icon>
                  {{ testing ? '执行中...' : '开始测试' }}
                </el-button>
                <el-button @click="handleClearInput">
                  <el-icon><Delete /></el-icon>
                  清空
                </el-button>
              </el-form-item>
            </el-form>
          </el-card>
        </el-col>
        
        <!-- 测试结果 -->
        <el-col :span="12">
          <el-card class="test-result-card" shadow="never">
            <template #header>
              <div class="card-header">
                <el-icon><Document /></el-icon>
                <span>测试结果</span>
                <div class="header-actions">
                  <el-button
                    v-if="testResult"
                    size="small"
                    @click="handleExportResult"
                  >
                    <el-icon><Download /></el-icon>
                    导出
                  </el-button>
                </div>
              </div>
            </template>
            
            <div v-if="testing" class="result-loading">
              <el-skeleton :rows="6" animated />
              <div class="loading-text">正在执行指令集...</div>
            </div>
            
            <div v-else-if="!testResult" class="result-empty">
              <el-empty description="暂无测试结果">
                <span>请在左侧输入测试内容并点击开始测试</span>
              </el-empty>
            </div>
            
            <div v-else class="result-content">
              <!-- 执行摘要 -->
              <div class="result-summary">
                <div class="summary-item">
                  <span class="label">执行结果:</span>
                  <el-tag
                    :type="testResult.success ? 'success' : 'danger'"
                    size="large"
                  >
                    {{ testResult.success ? '通过' : '拒绝' }}
                  </el-tag>
                </div>
                <div class="summary-item">
                  <span class="label">执行时间:</span>
                  <span class="value">{{ testResult.execution_time }}ms</span>
                </div>
                <div class="summary-item">
                  <span class="label">执行节点:</span>
                  <span class="value">{{ testResult.executed_nodes || 0 }} 个</span>
                </div>
              </div>
              
              <!-- 执行详情 -->
              <div v-if="testResult.details" class="result-details">
                <h4>执行详情</h4>
                <el-timeline>
                  <el-timeline-item
                    v-for="(step, index) in testResult.details"
                    :key="index"
                    :type="getStepType(step.status)"
                    :icon="getStepIcon(step.status)"
                  >
                    <div class="step-content">
                      <div class="step-header">
                        <span class="step-title">{{ step.node_title }}</span>
                        <el-tag size="small" :type="getNodeTypeTag(step.node_type)">
                          {{ getNodeTypeText(step.node_type) }}
                        </el-tag>
                      </div>
                      <div class="step-description">{{ step.description }}</div>
                      <div v-if="step.result" class="step-result">
                        <strong>结果:</strong> {{ step.result }}
                      </div>
                      <div v-if="step.error" class="step-error">
                        <el-alert
                          :title="step.error"
                          type="error"
                          :closable="false"
                          show-icon
                        />
                      </div>
                      <div class="step-meta">
                        <span>执行时间: {{ step.execution_time }}ms</span>
                      </div>
                    </div>
                  </el-timeline-item>
                </el-timeline>
              </div>
              
              <!-- 最终结果 -->
              <div v-if="testResult.final_result" class="final-result">
                <h4>最终结果</h4>
                <el-alert
                  :title="testResult.final_result.message"
                  :type="testResult.success ? 'success' : 'error'"
                  :description="testResult.final_result.reason"
                  show-icon
                  :closable="false"
                />
              </div>
            </div>
          </el-card>
        </el-col>
      </el-row>
    </div>

    <!-- 测试历史 -->
    <div class="test-history">
      <el-card shadow="never">
        <template #header>
          <div class="card-header">
            <el-icon><Clock /></el-icon>
            <span>测试历史</span>
            <div class="header-actions">
              <el-button size="small" @click="handleClearHistory">
                <el-icon><Delete /></el-icon>
                清空历史
              </el-button>
            </div>
          </div>
        </template>
        
        <div v-if="testHistory.length === 0" class="history-empty">
          <el-empty description="暂无测试历史" />
        </div>
        
        <el-collapse v-else v-model="activeHistoryItems">
          <el-collapse-item
            v-for="(item, index) in testHistory"
            :key="index"
            :name="index"
          >
            <template #title>
              <div class="history-item-title">
                <div class="title-left">
                  <el-tag
                    :type="item.success ? 'success' : 'danger'"
                    size="small"
                  >
                    {{ item.success ? '通过' : '拒绝' }}
                  </el-tag>
                  <span class="test-time">{{ formatTime(item.timestamp) }}</span>
                </div>
                <div class="title-right">
                  <span class="execution-time">{{ item.execution_time }}ms</span>
                  <el-button
                    size="small"
                    type="text"
                    @click.stop="handleRerunTest(item)"
                  >
                    <el-icon><Refresh /></el-icon>
                    重新测试
                  </el-button>
                </div>
              </div>
            </template>
            
            <div class="history-item-content">
              <div class="test-input">
                <h5>测试内容:</h5>
                <div class="input-content">{{ item.input }}</div>
              </div>
              
              <div v-if="item.final_result" class="test-result">
                <h5>测试结果:</h5>
                <el-alert
                  :title="item.final_result.message"
                  :type="item.success ? 'success' : 'error'"
                  :description="item.final_result.reason"
                  show-icon
                  :closable="false"
                />
              </div>
            </div>
          </el-collapse-item>
        </el-collapse>
      </el-card>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  ArrowLeft,
  VideoPlay,
  View,
  Edit,
  Document,
  Download,
  Delete,
  Clock,
  Refresh,
  CircleCheck,
  CircleClose,
  Warning
} from '@element-plus/icons-vue'
import { instructionSetApi } from '@/api/instruction-set'
import type {
  InstructionSet,
  InstructionTestRequest,
  InstructionTestResult,
  NodeType
} from '@/types/instruction-set'

// 路由
const route = useRoute()
const router = useRouter()

// 响应式数据
const instructionSet = ref<InstructionSet | null>(null)
const loading = ref(false)
const testing = ref(false)
const activeHistoryItems = ref<number[]>([])

// 测试表单
const testForm = reactive<InstructionTestRequest>({
  content: '',
  mode: 'normal',
  timeout: 30
})

// 测试结果
const testResult = ref<InstructionTestResult | null>(null)

// 测试历史
const testHistory = ref<Array<InstructionTestResult & { input: string; timestamp: number }>>([])

/**
 * 页面初始化
 */
onMounted(() => {
  loadInstructionSet()
  loadTestHistory()
})

/**
 * 加载指令集信息
 */
const loadInstructionSet = async () => {
  const id = Number(route.params.id)
  if (!id) {
    ElMessage.error('指令集ID无效')
    router.push('/instruction-sets')
    return
  }
  
  loading.value = true
  try {
    const response = await instructionSetApi.getInstructionSet(id)
    if (response.success && response.data) {
      instructionSet.value = response.data
    } else {
      ElMessage.error('加载指令集失败')
      router.push('/instruction-sets')
    }
  } catch (error) {
    console.error('加载指令集失败:', error)
    ElMessage.error('加载指令集失败')
    router.push('/instruction-sets')
  } finally {
    loading.value = false
  }
}

/**
 * 加载测试历史
 */
const loadTestHistory = () => {
  const id = Number(route.params.id)
  const historyKey = `instruction_test_history_${id}`
  const history = localStorage.getItem(historyKey)
  if (history) {
    try {
      testHistory.value = JSON.parse(history)
    } catch (error) {
      console.error('解析测试历史失败:', error)
    }
  }
}

/**
 * 保存测试历史
 */
const saveTestHistory = (result: InstructionTestResult, input: string) => {
  const id = Number(route.params.id)
  const historyKey = `instruction_test_history_${id}`
  
  const historyItem = {
    ...result,
    input,
    timestamp: Date.now()
  }
  
  testHistory.value.unshift(historyItem)
  
  // 只保留最近20条记录
  if (testHistory.value.length > 20) {
    testHistory.value = testHistory.value.slice(0, 20)
  }
  
  localStorage.setItem(historyKey, JSON.stringify(testHistory.value))
}

/**
 * 执行测试
 */
const handleRunTest = async () => {
  if (!instructionSet.value) {
    ElMessage.error('指令集信息未加载')
    return
  }
  
  if (!testForm.content.trim()) {
    ElMessage.warning('请输入测试内容')
    return
  }
  
  testing.value = true
  testResult.value = null
  
  try {
    const response = await instructionSetApi.executeInstructionSet(
      instructionSet.value.id,
      testForm
    )
    
    if (response && response.data) {
      testResult.value = response.data
      saveTestHistory(response.data, testForm.content)
      ElMessage.success('测试执行完成')
    } else {
      ElMessage.error('测试执行失败')
    }
  } catch (error) {
    console.error('测试执行失败:', error)
    ElMessage.error('测试执行失败')
  } finally {
    testing.value = false
  }
}

/**
 * 清空输入
 */
const handleClearInput = () => {
  testForm.content = ''
  testResult.value = null
}

/**
 * 查看详情
 */
const handleViewDetail = () => {
  if (instructionSet.value) {
    router.push(`/instruction-sets/${instructionSet.value.id}`)
  }
}

/**
 * 导出结果
 */
const handleExportResult = () => {
  if (!testResult.value) return
  
  const data = {
    instruction_set: instructionSet.value?.name,
    test_input: testForm.content,
    test_result: testResult.value,
    export_time: new Date().toISOString()
  }
  
  const blob = new Blob([JSON.stringify(data, null, 2)], {
    type: 'application/json'
  })
  
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `test_result_${Date.now()}.json`
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
  URL.revokeObjectURL(url)
  
  ElMessage.success('导出成功')
}

/**
 * 清空历史
 */
const handleClearHistory = async () => {
  try {
    await ElMessageBox.confirm(
      '确定要清空所有测试历史吗？',
      '确认清空',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    testHistory.value = []
    const id = Number(route.params.id)
    const historyKey = `instruction_test_history_${id}`
    localStorage.removeItem(historyKey)
    
    ElMessage.success('清空成功')
  } catch (error) {
    // 用户取消
  }
}

/**
 * 重新测试
 */
const handleRerunTest = (item: any) => {
  testForm.content = item.input
  testForm.mode = item.mode || 'normal'
  testForm.timeout = item.timeout || 30
  handleRunTest()
}

/**
 * 获取步骤类型
 */
const getStepType = (status: string) => {
  const typeMap: Record<string, string> = {
    success: 'success',
    error: 'danger',
    warning: 'warning',
    info: 'info'
  }
  return typeMap[status] || 'info'
}

/**
 * 获取步骤图标
 */
const getStepIcon = (status: string) => {
  const iconMap: Record<string, any> = {
    success: CircleCheck,
    error: CircleClose,
    warning: Warning
  }
  return iconMap[status]
}

/**
 * 获取节点类型标签
 */
const getNodeTypeTag = (nodeType: NodeType) => {
  const tagMap: Record<NodeType, string> = {
    condition: 'primary',
    action: 'success',
    branch: 'warning'
  }
  return tagMap[nodeType] || 'info'
}

/**
 * 获取节点类型文本
 */
const getNodeTypeText = (nodeType: NodeType) => {
  const textMap: Record<NodeType, string> = {
    condition: '条件',
    action: '动作',
    branch: '分支'
  }
  return textMap[nodeType] || nodeType
}

/**
 * 格式化时间
 */
const formatTime = (timestamp: number) => {
  return new Date(timestamp).toLocaleString('zh-CN')
}
</script>

<style scoped>
.instruction-test-page {
  padding: 24px;
  background-color: var(--el-bg-color-page);
  min-height: 100vh;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
  padding-bottom: 16px;
  border-bottom: 1px solid var(--el-border-color-lighter);
}

.header-left {
  display: flex;
  align-items: center;
  gap: 16px;
}

.header-info {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.page-title {
  display: flex;
  align-items: center;
  gap: 8px;
  margin: 0;
  font-size: 20px;
  font-weight: 600;
  color: var(--el-text-color-primary);
}

.instruction-info {
  display: flex;
  align-items: center;
  gap: 8px;
}

.instruction-name {
  font-size: 14px;
  color: var(--el-text-color-regular);
}

.header-actions {
  display: flex;
  gap: 12px;
}

.test-content {
  margin-bottom: 24px;
}

.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  font-weight: 600;
}

.card-header .header-actions {
  margin-left: auto;
}

.test-input-card,
.test-result-card {
  height: 600px;
}

.test-input-card :deep(.el-card__body),
.test-result-card :deep(.el-card__body) {
  height: calc(100% - 60px);
  overflow: auto;
}

.result-loading {
  text-align: center;
  padding: 40px 20px;
}

.loading-text {
  margin-top: 16px;
  color: var(--el-text-color-regular);
}

.result-empty {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 100%;
}

.result-content {
  height: 100%;
  overflow: auto;
}

.result-summary {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 16px;
  margin-bottom: 24px;
  padding: 16px;
  background-color: var(--el-fill-color-lighter);
  border-radius: 6px;
}

.summary-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.summary-item .label {
  font-size: 12px;
  color: var(--el-text-color-regular);
}

.summary-item .value {
  font-weight: 600;
  color: var(--el-text-color-primary);
}

.result-details {
  margin-bottom: 24px;
}

.result-details h4 {
  margin: 0 0 16px 0;
  font-size: 16px;
  font-weight: 600;
  color: var(--el-text-color-primary);
}

.step-content {
  padding: 8px 0;
}

.step-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}

.step-title {
  font-weight: 600;
  color: var(--el-text-color-primary);
}

.step-description {
  margin-bottom: 8px;
  color: var(--el-text-color-regular);
}

.step-result {
  margin-bottom: 8px;
  padding: 8px 12px;
  background-color: var(--el-fill-color-lighter);
  border-radius: 4px;
  font-size: 14px;
}

.step-error {
  margin-bottom: 8px;
}

.step-meta {
  font-size: 12px;
  color: var(--el-text-color-placeholder);
}

.final-result h4 {
  margin: 0 0 16px 0;
  font-size: 16px;
  font-weight: 600;
  color: var(--el-text-color-primary);
}

.test-history {
  margin-top: 24px;
}

.history-empty {
  padding: 40px;
  text-align: center;
}

.history-item-title {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
}

.title-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.title-right {
  display: flex;
  align-items: center;
  gap: 12px;
}

.test-time {
  font-size: 14px;
  color: var(--el-text-color-regular);
}

.execution-time {
  font-size: 12px;
  color: var(--el-text-color-placeholder);
}

.history-item-content {
  padding: 16px 0;
}

.test-input,
.test-result {
  margin-bottom: 16px;
}

.test-input h5,
.test-result h5 {
  margin: 0 0 8px 0;
  font-size: 14px;
  font-weight: 600;
  color: var(--el-text-color-primary);
}

.input-content {
  padding: 12px;
  background-color: var(--el-fill-color-lighter);
  border-radius: 4px;
  font-size: 14px;
  line-height: 1.5;
  white-space: pre-wrap;
  word-break: break-word;
}

/* 响应式设计 */
@media (max-width: 1200px) {
  .test-content .el-col {
    margin-bottom: 24px;
  }
  
  .test-input-card,
  .test-result-card {
    height: auto;
    min-height: 400px;
  }
}

@media (max-width: 768px) {
  .instruction-test-page {
    padding: 16px;
  }
  
  .page-header {
    flex-direction: column;
    align-items: stretch;
    gap: 16px;
  }
  
  .header-left {
    flex-direction: column;
    align-items: stretch;
    gap: 12px;
  }
  
  .result-summary {
    grid-template-columns: 1fr;
  }
  
  .history-item-title {
    flex-direction: column;
    align-items: stretch;
    gap: 8px;
  }
  
  .title-right {
    justify-content: space-between;
  }
}
</style>