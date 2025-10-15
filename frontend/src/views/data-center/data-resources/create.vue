<template>
  <div class="create-resource-container">
    <!-- 页面标题 -->
    <div class="page-header">
      <h1 class="page-title">
        <el-icon><Plus /></el-icon>
        新增数据资源
      </h1>
      <p class="page-description">创建新的数据资源</p>
    </div>

    <!-- 表单内容 -->
    <el-card>
      <el-form
        ref="formRef"
        :model="form"
        :rules="rules"
        label-width="120px"
        size="large"
      >
        <!-- 基本信息 -->
        <div class="form-section">
          <h3 class="section-title">基本信息</h3>
          
          <el-form-item label="资源名称" prop="name">
            <el-input
              v-model="form.name"
              placeholder="请输入资源名称"
              maxlength="100"
              show-word-limit
            />
          </el-form-item>

          <el-form-item label="资源类型" prop="type">
            <el-select
              v-model="form.type"
              placeholder="请选择资源类型"
              style="width: 100%"
            >
              <el-option
                v-for="type in resourceTypes"
                :key="type.value"
                :label="type.label"
                :value="type.value"
              />
            </el-select>
          </el-form-item>

          <el-form-item label="资源描述" prop="description">
            <el-input
              v-model="form.description"
              type="textarea"
              :rows="4"
              placeholder="请输入资源描述"
              maxlength="500"
              show-word-limit
            />
          </el-form-item>

          <el-form-item label="关键词" prop="keywords">
            <el-tag
              v-for="tag in form.keywords"
              :key="tag"
              closable
              @close="removeKeyword(tag)"
              style="margin-right: 8px; margin-bottom: 8px;"
            >
              {{ tag }}
            </el-tag>
            <el-input
              v-if="keywordInputVisible"
              ref="keywordInputRef"
              v-model="keywordInputValue"
              size="small"
              style="width: 120px; margin-right: 8px;"
              @keyup.enter="handleKeywordConfirm"
              @blur="handleKeywordConfirm"
            />
            <el-button
              v-else
              size="small"
              @click="showKeywordInput"
            >
              + 添加关键词
            </el-button>
          </el-form-item>
        </div>

        <!-- 文件上传 -->
        <div class="form-section">
          <h3 class="section-title">文件上传</h3>
          
          <el-form-item label="上传方式" prop="uploadType">
            <el-radio-group v-model="form.uploadType">
              <el-radio value="file">本地文件</el-radio>
              <el-radio value="url">网络链接</el-radio>
            </el-radio-group>
          </el-form-item>

          <el-form-item v-if="form.uploadType === 'file'" label="选择文件" prop="file">
            <el-upload
              ref="uploadRef"
              class="upload-demo"
              drag
              :auto-upload="false"
              :on-change="handleFileChange"
              :on-remove="handleFileRemove"
              :file-list="fileList"
              multiple
            >
              <el-icon class="el-icon--upload"><UploadFilled /></el-icon>
              <div class="el-upload__text">
                将文件拖到此处，或<em>点击上传</em>
              </div>
              <template #tip>
                <div class="el-upload__tip">
                  支持 PDF、DOC、DOCX、TXT、XLS、XLSX 等格式，单个文件不超过 100MB
                </div>
              </template>
            </el-upload>
          </el-form-item>

          <el-form-item v-if="form.uploadType === 'url'" label="网络链接" prop="url">
            <el-input
              v-model="form.url"
              placeholder="请输入文件的网络链接地址"
            />
          </el-form-item>
        </div>

        <!-- 分类和标签 -->
        <div class="form-section">
          <h3 class="section-title">分类和标签</h3>
          
          <el-form-item label="所属分类" prop="category">
            <el-cascader
              v-model="form.category"
              :options="categoryOptions"
              :props="{ checkStrictly: true }"
              placeholder="请选择分类"
              style="width: 100%"
            />
          </el-form-item>

          <el-form-item label="标签" prop="tags">
            <el-select
              v-model="form.tags"
              multiple
              filterable
              allow-create
              placeholder="请选择或创建标签"
              style="width: 100%"
            >
              <el-option
                v-for="tag in availableTags"
                :key="tag.value"
                :label="tag.label"
                :value="tag.value"
              />
            </el-select>
          </el-form-item>
        </div>

        <!-- 访问控制 -->
        <div class="form-section">
          <h3 class="section-title">访问控制</h3>
          
          <el-form-item label="访问权限" prop="accessLevel">
            <el-radio-group v-model="form.accessLevel">
              <el-radio value="public">公开</el-radio>
              <el-radio value="internal">内部</el-radio>
              <el-radio value="private">私有</el-radio>
            </el-radio-group>
          </el-form-item>

          <el-form-item v-if="form.accessLevel !== 'public'" label="授权用户" prop="authorizedUsers">
            <el-select
              v-model="form.authorizedUsers"
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

          <el-form-item label="下载权限" prop="downloadPermission">
            <el-switch
              v-model="form.downloadPermission"
              active-text="允许下载"
              inactive-text="禁止下载"
            />
          </el-form-item>
        </div>

        <!-- 元数据 -->
        <div class="form-section">
          <h3 class="section-title">元数据</h3>
          
          <el-form-item label="作者" prop="author">
            <el-input
              v-model="form.author"
              placeholder="请输入作者"
            />
          </el-form-item>

          <el-form-item label="出版社/机构" prop="publisher">
            <el-input
              v-model="form.publisher"
              placeholder="请输入出版社或机构"
            />
          </el-form-item>

          <el-form-item label="出版日期" prop="publishDate">
            <el-date-picker
              v-model="form.publishDate"
              type="date"
              placeholder="请选择出版日期"
              format="YYYY-MM-DD"
              value-format="YYYY-MM-DD"
              style="width: 100%"
            />
          </el-form-item>

          <el-form-item label="版本号" prop="version">
            <el-input
              v-model="form.version"
              placeholder="请输入版本号，如：v1.0"
            />
          </el-form-item>

          <el-form-item label="语言" prop="language">
            <el-select
              v-model="form.language"
              placeholder="请选择语言"
              style="width: 100%"
            >
              <el-option label="中文" value="zh" />
              <el-option label="英文" value="en" />
              <el-option label="日文" value="ja" />
              <el-option label="其他" value="other" />
            </el-select>
          </el-form-item>
        </div>

        <!-- 发布设置 -->
        <div class="form-section">
          <h3 class="section-title">发布设置</h3>
          
          <el-form-item label="发布状态" prop="status">
            <el-radio-group v-model="form.status">
              <el-radio value="draft">保存为草稿</el-radio>
              <el-radio value="published">立即发布</el-radio>
              <el-radio value="scheduled">定时发布</el-radio>
            </el-radio-group>
          </el-form-item>

          <el-form-item v-if="form.status === 'scheduled'" label="发布时间" prop="publishTime">
            <el-date-picker
              v-model="form.publishTime"
              type="datetime"
              placeholder="请选择发布时间"
              format="YYYY-MM-DD HH:mm:ss"
              value-format="YYYY-MM-DD HH:mm:ss"
              style="width: 100%"
            />
          </el-form-item>
        </div>

        <!-- 操作按钮 -->
        <div class="form-actions">
          <el-button @click="handleCancel">取消</el-button>
          <el-button @click="handlePreview">预览</el-button>
          <el-button type="primary" @click="handleSubmit" :loading="submitting">
            {{ form.status === 'draft' ? '保存草稿' : '发布资源' }}
          </el-button>
        </div>
      </el-form>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import type { FormInstance, UploadFile } from 'element-plus'
import {
  Plus,
  UploadFilled
} from '@element-plus/icons-vue'

const router = useRouter()

// 表单引用
const formRef = ref<FormInstance>()
const uploadRef = ref()
const keywordInputRef = ref()

// 响应式数据
const submitting = ref(false)
const keywordInputVisible = ref(false)
const keywordInputValue = ref('')
const fileList = ref<UploadFile[]>([])

// 表单数据
const form = reactive({
  name: '',
  type: '',
  description: '',
  keywords: [] as string[],
  uploadType: 'file',
  file: null,
  url: '',
  category: [],
  tags: [],
  accessLevel: 'public',
  authorizedUsers: [],
  downloadPermission: true,
  author: '',
  publisher: '',
  publishDate: '',
  version: '',
  language: 'zh',
  status: 'published',
  publishTime: ''
})

// 表单验证规则
const rules = {
  name: [
    { required: true, message: '请输入资源名称', trigger: 'blur' },
    { min: 2, max: 100, message: '长度在 2 到 100 个字符', trigger: 'blur' }
  ],
  type: [
    { required: true, message: '请选择资源类型', trigger: 'change' }
  ],
  description: [
    { required: true, message: '请输入资源描述', trigger: 'blur' },
    { min: 10, max: 500, message: '长度在 10 到 500 个字符', trigger: 'blur' }
  ],
  uploadType: [
    { required: true, message: '请选择上传方式', trigger: 'change' }
  ],
  url: [
    { required: true, message: '请输入网络链接', trigger: 'blur' },
    { type: 'url', message: '请输入正确的网络链接', trigger: 'blur' }
  ],
  category: [
    { required: true, message: '请选择分类', trigger: 'change' }
  ],
  accessLevel: [
    { required: true, message: '请选择访问权限', trigger: 'change' }
  ],
  status: [
    { required: true, message: '请选择发布状态', trigger: 'change' }
  ],
  publishTime: [
    { required: true, message: '请选择发布时间', trigger: 'change' }
  ]
}

// 资源类型选项
const resourceTypes = ref([
  { label: '图书', value: 'book' },
  { label: '期刊文章', value: 'article' },
  { label: '会议录', value: 'conference' },
  { label: '学术论文', value: 'paper' },
  { label: '教材', value: 'textbook' },
  { label: '数据集', value: 'dataset' },
  { label: '软件工具', value: 'software' },
  { label: '多媒体', value: 'multimedia' }
])

// 分类选项
const categoryOptions = ref([
  {
    value: 'computer-science',
    label: '计算机科学',
    children: [
      { value: 'ai', label: '人工智能' },
      { value: 'ml', label: '机器学习' },
      { value: 'cv', label: '计算机视觉' },
      { value: 'nlp', label: '自然语言处理' }
    ]
  },
  {
    value: 'mathematics',
    label: '数学',
    children: [
      { value: 'statistics', label: '统计学' },
      { value: 'algebra', label: '代数' },
      { value: 'analysis', label: '数学分析' }
    ]
  },
  {
    value: 'physics',
    label: '物理学',
    children: [
      { value: 'quantum', label: '量子物理' },
      { value: 'classical', label: '经典物理' }
    ]
  }
])

// 可用标签
const availableTags = ref([
  { label: '机器学习', value: 'machine-learning' },
  { label: '深度学习', value: 'deep-learning' },
  { label: '神经网络', value: 'neural-network' },
  { label: '数据挖掘', value: 'data-mining' },
  { label: '算法', value: 'algorithm' },
  { label: '编程', value: 'programming' }
])

// 可用用户
const availableUsers = ref([
  { id: 1, name: '张三' },
  { id: 2, name: '李四' },
  { id: 3, name: '王五' },
  { id: 4, name: '赵六' }
])

/**
 * 移除关键词
 * @param tag 要移除的关键词
 */
const removeKeyword = (tag: string) => {
  form.keywords.splice(form.keywords.indexOf(tag), 1)
}

/**
 * 显示关键词输入框
 */
const showKeywordInput = () => {
  keywordInputVisible.value = true
  nextTick(() => {
    keywordInputRef.value?.focus()
  })
}

/**
 * 确认添加关键词
 */
const handleKeywordConfirm = () => {
  if (keywordInputValue.value && !form.keywords.includes(keywordInputValue.value)) {
    form.keywords.push(keywordInputValue.value)
  }
  keywordInputVisible.value = false
  keywordInputValue.value = ''
}

/**
 * 处理文件变化
 * @param file 文件对象
 * @param fileList 文件列表
 */
const handleFileChange = (file: UploadFile, fileList: UploadFile[]) => {
  // 验证文件大小
  if (file.size && file.size > 100 * 1024 * 1024) {
    ElMessage.error('文件大小不能超过 100MB')
    return false
  }
  
  // 验证文件类型
  const allowedTypes = [
    'application/pdf',
    'application/msword',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    'text/plain',
    'application/vnd.ms-excel',
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
  ]
  
  if (file.raw && !allowedTypes.includes(file.raw.type)) {
    ElMessage.error('不支持的文件格式')
    return false
  }
  
  console.log('文件上传:', file.name)
}

/**
 * 处理文件移除
 * @param file 文件对象
 * @param fileList 文件列表
 */
const handleFileRemove = (file: UploadFile, fileList: UploadFile[]) => {
  console.log('文件移除:', file.name)
}

/**
 * 处理取消
 */
const handleCancel = () => {
  ElMessageBox.confirm(
    '确定要取消创建吗？未保存的数据将丢失。',
    '取消确认',
    {
      confirmButtonText: '确定',
      cancelButtonText: '继续编辑',
      type: 'warning'
    }
  ).then(() => {
    router.back()
  }).catch(() => {
    // 用户选择继续编辑
  })
}

/**
 * 处理预览
 */
const handlePreview = () => {
  formRef.value?.validate((valid) => {
    if (valid) {
      ElMessage.info('预览功能开发中...')
    } else {
      ElMessage.error('请完善表单信息')
    }
  })
}

/**
 * 处理提交
 */
const handleSubmit = () => {
  formRef.value?.validate((valid) => {
    if (valid) {
      // 验证上传方式对应的文件
      if (form.uploadType === 'file' && fileList.value.length === 0) {
        ElMessage.error('请选择要上传的文件')
        return
      }
      
      if (form.uploadType === 'url' && !form.url) {
        ElMessage.error('请输入网络链接')
        return
      }
      
      submitting.value = true
      
      // 模拟提交
      setTimeout(() => {
        submitting.value = false
        ElMessage.success(form.status === 'draft' ? '草稿保存成功' : '资源发布成功')
        router.push('/data-center/data-resources')
      }, 2000)
    } else {
      ElMessage.error('请完善表单信息')
    }
  })
}
</script>

<style lang="scss" scoped>
.create-resource-container {
  padding: 20px;
  background: var(--el-bg-color-page);
  min-height: 100vh;
}

.page-header {
  margin-bottom: 24px;
  
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

.form-section {
  margin-bottom: 32px;
  
  .section-title {
    font-size: 16px;
    font-weight: 600;
    color: var(--el-text-color-primary);
    margin: 0 0 16px 0;
    padding-bottom: 8px;
    border-bottom: 1px solid var(--el-border-color-lighter);
  }
}

.upload-demo {
  width: 100%;
  
  :deep(.el-upload-dragger) {
    width: 100%;
  }
}

.form-actions {
  display: flex;
  justify-content: center;
  gap: 16px;
  padding-top: 24px;
  border-top: 1px solid var(--el-border-color-lighter);
}

// 响应式设计
@media (max-width: 768px) {
  .create-resource-container {
    padding: 16px;
  }
  
  .form-actions {
    flex-direction: column;
    
    .el-button {
      width: 100%;
    }
  }
}
</style>