<template>
  <div class="user-import">
    <!-- 导入步骤 -->
    <el-steps :active="currentStep" align-center class="import-steps">
      <el-step title="下载模板" description="下载用户导入模板" />
      <el-step title="上传文件" description="上传填写好的文件" />
      <el-step title="数据验证" description="验证导入数据" />
      <el-step title="导入完成" description="完成用户导入" />
    </el-steps>

    <!-- 步骤1：下载模板 -->
    <div v-if="currentStep === 0" class="step-content">
      <div class="template-section">
        <el-alert
          title="导入说明"
          type="info"
          :closable="false"
          show-icon
        >
          <template #default>
            <ul class="import-rules">
              <li>请先下载用户导入模板，按照模板格式填写用户信息</li>
              <li>必填字段：用户名、邮箱、姓名</li>
              <li>用户名必须唯一，不能与现有用户重复</li>
              <li>邮箱格式必须正确，且不能重复</li>
              <li>密码字段为空时，系统将自动生成随机密码</li>
              <li>支持的文件格式：Excel (.xlsx, .xls) 和 CSV (.csv)</li>
              <li>单次最多导入 1000 个用户</li>
            </ul>
          </template>
        </el-alert>

        <div class="template-actions">
          <el-button type="primary" @click="downloadTemplate('excel')">
            <el-icon><Download /></el-icon>
            下载 Excel 模板
          </el-button>
          <el-button @click="downloadTemplate('csv')">
            <el-icon><Download /></el-icon>
            下载 CSV 模板
          </el-button>
        </div>

        <div class="step-actions">
          <el-button type="primary" @click="nextStep">
            下一步
          </el-button>
        </div>
      </div>
    </div>

    <!-- 步骤2：上传文件 -->
    <div v-if="currentStep === 1" class="step-content">
      <div class="upload-section">
        <el-upload
          ref="uploadRef"
          class="upload-area"
          drag
          :auto-upload="false"
          :limit="1"
          :accept="'.xlsx,.xls,.csv'"
          :on-change="handleFileChange"
          :on-exceed="handleExceed"
        >
          <el-icon class="el-icon--upload"><UploadFilled /></el-icon>
          <div class="el-upload__text">
            将文件拖到此处，或<em>点击上传</em>
          </div>
          <template #tip>
            <div class="el-upload__tip">
              支持 .xlsx, .xls, .csv 格式文件，文件大小不超过 10MB
            </div>
          </template>
        </el-upload>

        <div v-if="uploadFile" class="file-info">
          <el-card>
            <div class="file-details">
              <el-icon><Document /></el-icon>
              <span class="file-name">{{ uploadFile.name }}</span>
              <span class="file-size">({{ formatFileSize(uploadFile.size) }})</span>
              <el-button
                type="danger"
                size="small"
                text
                @click="removeFile"
              >
                <el-icon><Delete /></el-icon>
              </el-button>
            </div>
          </el-card>
        </div>

        <div class="step-actions">
          <el-button @click="prevStep">上一步</el-button>
          <el-button
            type="primary"
            :disabled="!uploadFile"
            :loading="validating"
            @click="validateFile"
          >
            验证数据
          </el-button>
        </div>
      </div>
    </div>

    <!-- 步骤3：数据验证 -->
    <div v-if="currentStep === 2" class="step-content">
      <div class="validation-section">
        <div v-if="validating" class="validation-loading">
          <el-loading-spinner />
          <p>正在验证数据，请稍候...</p>
        </div>

        <div v-else-if="validationResult" class="validation-result">
          <!-- 验证统计 -->
          <div class="validation-stats">
            <el-row :gutter="20">
              <el-col :span="6">
                <el-statistic title="总记录数" :value="validationResult.total" />
              </el-col>
              <el-col :span="6">
                <el-statistic
                  title="有效记录"
                  :value="validationResult.valid"
                  class="valid-stat"
                />
              </el-col>
              <el-col :span="6">
                <el-statistic
                  title="错误记录"
                  :value="validationResult.errors"
                  class="error-stat"
                />
              </el-col>
              <el-col :span="6">
                <el-statistic
                  title="警告记录"
                  :value="validationResult.warnings"
                  class="warning-stat"
                />
              </el-col>
            </el-row>
          </div>

          <!-- 错误列表 -->
          <div v-if="validationResult.error_details?.length" class="error-list">
            <h4>错误详情</h4>
            <el-table
              :data="validationResult.error_details"
              max-height="300"
              stripe
            >
              <el-table-column prop="row" label="行号" width="80" />
              <el-table-column prop="field" label="字段" width="120" />
              <el-table-column prop="value" label="值" width="150" />
              <el-table-column prop="message" label="错误信息" min-width="200" />
            </el-table>
          </div>

          <!-- 警告列表 -->
          <div v-if="validationResult.warning_details?.length" class="warning-list">
            <h4>警告详情</h4>
            <el-table
              :data="validationResult.warning_details"
              max-height="200"
              stripe
            >
              <el-table-column prop="row" label="行号" width="80" />
              <el-table-column prop="field" label="字段" width="120" />
              <el-table-column prop="value" label="值" width="150" />
              <el-table-column prop="message" label="警告信息" min-width="200" />
            </el-table>
          </div>

          <!-- 预览数据 -->
          <div v-if="validationResult.preview_data?.length" class="preview-data">
            <h4>数据预览（前10条）</h4>
            <el-table
              :data="validationResult.preview_data"
              max-height="300"
              stripe
            >
              <el-table-column prop="username" label="用户名" width="120" />
              <el-table-column prop="email" label="邮箱" width="180" />
              <el-table-column prop="full_name" label="姓名" width="120" />
              <el-table-column prop="department" label="部门" width="120" />
              <el-table-column prop="position" label="职位" width="120" />
              <el-table-column prop="phone" label="手机" width="130" />
            </el-table>
          </div>
        </div>

        <div class="step-actions">
          <el-button @click="prevStep">上一步</el-button>
          <el-button
            type="primary"
            :disabled="!canImport"
            @click="nextStep"
          >
            开始导入
          </el-button>
        </div>
      </div>
    </div>

    <!-- 步骤4：导入完成 -->
    <div v-if="currentStep === 3" class="step-content">
      <div class="import-section">
        <div v-if="importing" class="import-progress">
          <el-progress
            :percentage="importProgress"
            :status="importStatus"
            stroke-width="8"
          />
          <p class="progress-text">{{ importProgressText }}</p>
        </div>

        <div v-else-if="importResult" class="import-result">
          <el-result
            :icon="importResult.success ? 'success' : 'error'"
            :title="importResult.success ? '导入成功' : '导入失败'"
            :sub-title="importResult.message"
          >
            <template #extra>
              <div v-if="importResult.success" class="import-stats">
                <el-descriptions :column="2" border>
                  <el-descriptions-item label="成功导入">
                    {{ importResult.imported }} 个用户
                  </el-descriptions-item>
                  <el-descriptions-item label="跳过记录">
                    {{ importResult.skipped }} 个
                  </el-descriptions-item>
                  <el-descriptions-item label="失败记录">
                    {{ importResult.failed }} 个
                  </el-descriptions-item>
                  <el-descriptions-item label="总耗时">
                    {{ importResult.duration }}ms
                  </el-descriptions-item>
                </el-descriptions>
              </div>

              <div class="result-actions">
                <el-button v-if="importResult.success" type="primary" @click="handleSuccess">
                  完成
                </el-button>
                <el-button v-else @click="resetImport">
                  重新导入
                </el-button>
                <el-button @click="$emit('close')">
                  关闭
                </el-button>
              </div>
            </template>
          </el-result>
        </div>

        <div v-else class="import-confirm">
          <el-alert
            title="确认导入"
            type="warning"
            :closable="false"
            show-icon
          >
            <template #default>
              <p>即将导入 {{ validationResult?.valid }} 个有效用户记录。</p>
              <p v-if="validationResult?.errors > 0">
                注意：{{ validationResult.errors }} 个错误记录将被跳过。
              </p>
              <p>导入过程不可撤销，请确认后继续。</p>
            </template>
          </el-alert>

          <div class="step-actions">
            <el-button @click="prevStep">上一步</el-button>
            <el-button
              type="primary"
              @click="startImport"
            >
              确认导入
            </el-button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { ElMessage } from 'element-plus'
import {
  Download,
  UploadFilled,
  Document,
  Delete
} from '@element-plus/icons-vue'
import type { UploadFile, UploadFiles, UploadInstance } from 'element-plus'
import {
  downloadUserTemplate,
  validateUserImport,
  importUsers
} from '@/api/user'

interface ValidationResult {
  total: number
  valid: number
  errors: number
  warnings: number
  error_details?: Array<{
    row: number
    field: string
    value: string
    message: string
  }>
  warning_details?: Array<{
    row: number
    field: string
    value: string
    message: string
  }>
  preview_data?: Array<{
    username: string
    email: string
    full_name: string
    department?: string
    position?: string
    phone?: string
  }>
}

interface ImportResult {
  success: boolean
  message: string
  imported: number
  skipped: number
  failed: number
  duration: number
}

const emit = defineEmits<{
  success: []
  close: []
}>()

// 响应式数据
const currentStep = ref(0)
const uploadRef = ref<UploadInstance>()
const uploadFile = ref<File | null>(null)
const validating = ref(false)
const validationResult = ref<ValidationResult | null>(null)
const importing = ref(false)
const importProgress = ref(0)
const importStatus = ref<'success' | 'exception' | undefined>()
const importProgressText = ref('')
const importResult = ref<ImportResult | null>(null)

// 计算属性
const canImport = computed(() => {
  return validationResult.value && validationResult.value.valid > 0
})

/**
 * 下载模板文件
 */
const downloadTemplate = async (format: 'excel' | 'csv') => {
  try {
    await downloadUserTemplate(format)
    ElMessage.success('模板下载成功')
  } catch (error) {
    ElMessage.error('模板下载失败')
  }
}

/**
 * 处理文件变化
 */
const handleFileChange = (file: UploadFile, files: UploadFiles) => {
  uploadFile.value = file.raw || null
}

/**
 * 处理文件超出限制
 */
const handleExceed = () => {
  ElMessage.warning('只能上传一个文件')
}

/**
 * 移除文件
 */
const removeFile = () => {
  uploadFile.value = null
  uploadRef.value?.clearFiles()
}

/**
 * 格式化文件大小
 */
const formatFileSize = (size: number): string => {
  if (size < 1024) {
    return `${size} B`
  } else if (size < 1024 * 1024) {
    return `${(size / 1024).toFixed(1)} KB`
  } else {
    return `${(size / (1024 * 1024)).toFixed(1)} MB`
  }
}

/**
 * 验证文件
 */
const validateFile = async () => {
  if (!uploadFile.value) {
    ElMessage.error('请先上传文件')
    return
  }

  try {
    validating.value = true
    const formData = new FormData()
    formData.append('file', uploadFile.value)
    
    const response = await validateUserImport(formData)
    validationResult.value = response.data
    
    if (validationResult.value.errors === 0) {
      ElMessage.success('数据验证通过')
    } else {
      ElMessage.warning(`发现 ${validationResult.value.errors} 个错误，请检查后重新上传`)
    }
    
    nextStep()
  } catch (error) {
    ElMessage.error('文件验证失败')
  } finally {
    validating.value = false
  }
}

/**
 * 开始导入
 */
const startImport = async () => {
  if (!uploadFile.value || !validationResult.value) {
    return
  }

  try {
    importing.value = true
    importProgress.value = 0
    importProgressText.value = '正在导入用户数据...'
    
    const formData = new FormData()
    formData.append('file', uploadFile.value)
    
    // 模拟进度更新
    const progressInterval = setInterval(() => {
      if (importProgress.value < 90) {
        importProgress.value += Math.random() * 10
        importProgressText.value = `正在导入用户数据... ${Math.floor(importProgress.value)}%`
      }
    }, 500)
    
    const response = await importUsers(formData)
    
    clearInterval(progressInterval)
    importProgress.value = 100
    importStatus.value = response.data.success ? 'success' : 'exception'
    importProgressText.value = response.data.success ? '导入完成' : '导入失败'
    
    setTimeout(() => {
      importResult.value = response.data
      importing.value = false
    }, 1000)
  } catch (error) {
    importing.value = false
    importStatus.value = 'exception'
    ElMessage.error('导入失败')
  }
}

/**
 * 处理导入成功
 */
const handleSuccess = () => {
  emit('success')
}

/**
 * 重置导入
 */
const resetImport = () => {
  currentStep.value = 1
  uploadFile.value = null
  validationResult.value = null
  importResult.value = null
  uploadRef.value?.clearFiles()
}

/**
 * 下一步
 */
const nextStep = () => {
  if (currentStep.value < 3) {
    currentStep.value++
  }
}

/**
 * 上一步
 */
const prevStep = () => {
  if (currentStep.value > 0) {
    currentStep.value--
  }
}
</script>

<style lang="scss" scoped>
@import '@/styles/variables.scss';

.user-import {
  .import-steps {
    margin-bottom: $spacing-xl;
  }

  .step-content {
    min-height: 400px;
  }

  .template-section {
    .import-rules {
      margin: 0;
      padding-left: $spacing-lg;
      
      li {
        margin-bottom: $spacing-xs;
        color: var(--el-text-color-regular);
      }
    }

    .template-actions {
      display: flex;
      gap: $spacing-md;
      justify-content: center;
      margin: $spacing-xl 0;
    }
  }

  .upload-section {
    .upload-area {
      margin-bottom: $spacing-lg;
    }

    .file-info {
      margin-bottom: $spacing-lg;

      .file-details {
        display: flex;
        align-items: center;
        gap: $spacing-sm;

        .file-name {
          font-weight: 500;
          color: var(--el-text-color-primary);
        }

        .file-size {
          color: var(--el-text-color-regular);
          font-size: $font-size-sm;
        }
      }
    }
  }

  .validation-section {
    .validation-loading {
      text-align: center;
      padding: $spacing-xl;

      p {
        margin-top: $spacing-md;
        color: var(--el-text-color-regular);
      }
    }

    .validation-stats {
      margin-bottom: $spacing-xl;

      .valid-stat {
        :deep(.el-statistic__content) {
          color: var(--el-color-success);
        }
      }

      .error-stat {
        :deep(.el-statistic__content) {
          color: var(--el-color-danger);
        }
      }

      .warning-stat {
        :deep(.el-statistic__content) {
          color: var(--el-color-warning);
        }
      }
    }

    .error-list,
    .warning-list,
    .preview-data {
      margin-bottom: $spacing-lg;

      h4 {
        margin: 0 0 $spacing-md 0;
        color: var(--el-text-color-primary);
      }
    }
  }

  .import-section {
    .import-progress {
      text-align: center;
      padding: $spacing-xl;

      .progress-text {
        margin-top: $spacing-md;
        color: var(--el-text-color-regular);
      }
    }

    .import-confirm {
      text-align: center;
    }

    .import-stats {
      margin-bottom: $spacing-lg;
    }

    .result-actions {
      display: flex;
      gap: $spacing-md;
      justify-content: center;
    }
  }

  .step-actions {
    display: flex;
    gap: $spacing-md;
    justify-content: center;
    margin-top: $spacing-xl;
    padding-top: $spacing-lg;
    border-top: 1px solid var(--el-border-color-lighter);
  }
}

// 响应式设计
@media (max-width: 768px) {
  .user-import {
    .template-actions {
      flex-direction: column;
      align-items: center;
    }

    .step-actions {
      flex-direction: column;
    }

    .result-actions {
      flex-direction: column;
    }
  }
}
</style>