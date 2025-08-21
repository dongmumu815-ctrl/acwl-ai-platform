<template>
  <div class="task-create">
    <el-page-header @back="goBack" content="创建任务">
      <template #extra>
        <el-space>
          <el-button @click="saveDraft">保存草稿</el-button>
          <el-button type="primary" @click="saveTask" :loading="saving">保存任务</el-button>
        </el-space>
      </template>
    </el-page-header>

    <div class="create-content">
      <el-form
        ref="formRef"
        :model="taskForm"
        :rules="formRules"
        label-width="120px"
        size="default"
      >
        <el-row :gutter="20">
          <el-col :span="16">
            <!-- 基本信息 -->
            <el-card class="form-card">
              <template #header>
                <span>基本信息</span>
              </template>
              
              <el-form-item label="任务名称" prop="name">
                <el-input
                  v-model="taskForm.name"
                  placeholder="请输入任务名称"
                  maxlength="100"
                  show-word-limit
                />
              </el-form-item>
              
              <el-form-item label="任务描述" prop="description">
                <el-input
                  v-model="taskForm.description"
                  type="textarea"
                  :rows="3"
                  placeholder="请输入任务描述"
                  maxlength="500"
                  show-word-limit
                />
              </el-form-item>
              
              <el-row :gutter="20">
                <el-col :span="12">
                  <el-form-item label="所属项目" prop="project_id">
                    <el-select v-model="taskForm.project_id" placeholder="选择项目" style="width: 100%">
                      <el-option
                        v-for="project in projects"
                        :key="project.id"
                        :label="project.name"
                        :value="project.id"
                      />
                    </el-select>
                  </el-form-item>
                </el-col>
                <el-col :span="12">
                  <el-form-item label="任务类型" prop="task_type">
                    <el-select v-model="taskForm.task_type" placeholder="选择任务类型" style="width: 100%" @change="handleTaskTypeChange">
                      <el-option label="HTTP请求" value="http" />
                      <el-option label="脚本执行" value="script" />
                      <el-option label="数据处理" value="data" />
                      <el-option label="文件操作" value="file" />
                    </el-select>
                  </el-form-item>
                </el-col>
              </el-row>
              
              <el-row :gutter="20">
                <el-col :span="8">
                  <el-form-item label="优先级" prop="priority">
                    <el-select v-model="taskForm.priority" placeholder="选择优先级" style="width: 100%">
                      <el-option label="低" value="low" />
                      <el-option label="中" value="medium" />
                      <el-option label="高" value="high" />
                    </el-select>
                  </el-form-item>
                </el-col>
                <el-col :span="8">
                  <el-form-item label="超时时间" prop="timeout">
                    <el-input-number
                      v-model="taskForm.timeout"
                      :min="1"
                      :max="3600"
                      placeholder="秒"
                      style="width: 100%"
                    />
                  </el-form-item>
                </el-col>
                <el-col :span="8">
                  <el-form-item label="重试次数" prop="retry_count">
                    <el-input-number
                      v-model="taskForm.retry_count"
                      :min="0"
                      :max="10"
                      style="width: 100%"
                    />
                  </el-form-item>
                </el-col>
              </el-row>
              
              <el-form-item label="标签">
                <el-tag
                  v-for="tag in taskForm.tags"
                  :key="tag"
                  closable
                  @close="removeTag(tag)"
                  style="margin-right: 8px; margin-bottom: 8px"
                >
                  {{ tag }}
                </el-tag>
                <el-input
                  v-if="tagInputVisible"
                  ref="tagInputRef"
                  v-model="tagInputValue"
                  size="small"
                  style="width: 100px"
                  @keyup.enter="addTag"
                  @blur="addTag"
                />
                <el-button v-else size="small" @click="showTagInput">+ 添加标签</el-button>
              </el-form-item>
            </el-card>

            <!-- 任务配置 -->
            <el-card class="form-card">
              <template #header>
                <span>任务配置</span>
              </template>
              
              <!-- HTTP请求配置 -->
              <div v-if="taskForm.task_type === 'http'">
                <el-form-item label="请求方法" prop="config.method">
                  <el-select v-model="taskForm.config.method" placeholder="选择请求方法" style="width: 200px">
                    <el-option label="GET" value="GET" />
                    <el-option label="POST" value="POST" />
                    <el-option label="PUT" value="PUT" />
                    <el-option label="DELETE" value="DELETE" />
                    <el-option label="PATCH" value="PATCH" />
                  </el-select>
                </el-form-item>
                
                <el-form-item label="请求URL" prop="config.url">
                  <el-input v-model="taskForm.config.url" placeholder="https://api.example.com/endpoint" />
                </el-form-item>
                
                <el-form-item label="请求头">
                  <div class="key-value-editor">
                    <div v-for="(header, index) in taskForm.config.headers" :key="index" class="key-value-row">
                      <el-input v-model="header.key" placeholder="Header名称" style="width: 200px" />
                      <el-input v-model="header.value" placeholder="Header值" style="width: 300px; margin-left: 10px" />
                      <el-button type="danger" text @click="removeHeader(index)" style="margin-left: 10px">
                        <el-icon><Delete /></el-icon>
                      </el-button>
                    </div>
                    <el-button type="primary" text @click="addHeader">
                      <el-icon><Plus /></el-icon>
                      添加请求头
                    </el-button>
                  </div>
                </el-form-item>
                
                <el-form-item label="请求体" v-if="['POST', 'PUT', 'PATCH'].includes(taskForm.config.method)">
                  <el-input
                    v-model="taskForm.config.body"
                    type="textarea"
                    :rows="6"
                    placeholder="请输入JSON格式的请求体"
                  />
                </el-form-item>
              </div>
              
              <!-- 脚本执行配置 -->
              <div v-if="taskForm.task_type === 'script'">
                <el-form-item label="脚本类型" prop="config.script_type">
                  <el-select v-model="taskForm.config.script_type" placeholder="选择脚本类型" style="width: 200px">
                    <el-option label="Python" value="python" />
                    <el-option label="Shell" value="shell" />
                    <el-option label="PowerShell" value="powershell" />
                    <el-option label="JavaScript" value="javascript" />
                  </el-select>
                </el-form-item>
                
                <el-form-item label="脚本内容" prop="config.script_content">
                  <el-input
                    v-model="taskForm.config.script_content"
                    type="textarea"
                    :rows="10"
                    placeholder="请输入脚本内容"
                  />
                </el-form-item>
                
                <el-form-item label="环境变量">
                  <div class="key-value-editor">
                    <div v-for="(env, index) in taskForm.config.env_vars" :key="index" class="key-value-row">
                      <el-input v-model="env.key" placeholder="变量名" style="width: 200px" />
                      <el-input v-model="env.value" placeholder="变量值" style="width: 300px; margin-left: 10px" />
                      <el-button type="danger" text @click="removeEnvVar(index)" style="margin-left: 10px">
                        <el-icon><Delete /></el-icon>
                      </el-button>
                    </div>
                    <el-button type="primary" text @click="addEnvVar">
                      <el-icon><Plus /></el-icon>
                      添加环境变量
                    </el-button>
                  </div>
                </el-form-item>
              </div>
              
              <!-- 数据处理配置 -->
              <div v-if="taskForm.task_type === 'data'">
                <el-form-item label="数据源" prop="config.data_source">
                  <el-input v-model="taskForm.config.data_source" placeholder="数据源路径或URL" />
                </el-form-item>
                
                <el-form-item label="处理规则" prop="config.processing_rules">
                  <el-input
                    v-model="taskForm.config.processing_rules"
                    type="textarea"
                    :rows="6"
                    placeholder="请输入JSON格式的处理规则"
                  />
                </el-form-item>
                
                <el-form-item label="输出格式" prop="config.output_format">
                  <el-select v-model="taskForm.config.output_format" placeholder="选择输出格式" style="width: 200px">
                    <el-option label="JSON" value="json" />
                    <el-option label="CSV" value="csv" />
                    <el-option label="XML" value="xml" />
                    <el-option label="TXT" value="txt" />
                  </el-select>
                </el-form-item>
              </div>
              
              <!-- 文件操作配置 -->
              <div v-if="taskForm.task_type === 'file'">
                <el-form-item label="操作类型" prop="config.operation">
                  <el-select v-model="taskForm.config.operation" placeholder="选择操作类型" style="width: 200px">
                    <el-option label="复制" value="copy" />
                    <el-option label="移动" value="move" />
                    <el-option label="删除" value="delete" />
                    <el-option label="压缩" value="compress" />
                    <el-option label="解压" value="extract" />
                  </el-select>
                </el-form-item>
                
                <el-form-item label="源路径" prop="config.source_path">
                  <el-input v-model="taskForm.config.source_path" placeholder="源文件或目录路径" />
                </el-form-item>
                
                <el-form-item label="目标路径" prop="config.target_path" v-if="['copy', 'move', 'compress', 'extract'].includes(taskForm.config.operation)">
                  <el-input v-model="taskForm.config.target_path" placeholder="目标文件或目录路径" />
                </el-form-item>
              </div>
            </el-card>
          </el-col>

          <el-col :span="8">
            <!-- 执行设置 -->
            <el-card class="form-card">
              <template #header>
                <span>执行设置</span>
              </template>
              
              <el-form-item label="状态">
                <el-radio-group v-model="taskForm.status">
                  <el-radio label="draft">草稿</el-radio>
                  <el-radio label="active">激活</el-radio>
                </el-radio-group>
              </el-form-item>
              
              <el-form-item label="失败处理">
                <el-select v-model="taskForm.failure_action" placeholder="选择失败处理方式" style="width: 100%">
                  <el-option label="停止执行" value="stop" />
                  <el-option label="继续执行" value="continue" />
                  <el-option label="重试" value="retry" />
                </el-select>
              </el-form-item>
              
              <el-form-item label="通知设置">
                <el-checkbox-group v-model="taskForm.notifications">
                  <el-checkbox label="success">成功时通知</el-checkbox>
                  <el-checkbox label="failure">失败时通知</el-checkbox>
                </el-checkbox-group>
              </el-form-item>
            </el-card>

            <!-- 预览 -->
            <el-card class="form-card">
              <template #header>
                <span>配置预览</span>
              </template>
              <el-input
                :model-value="JSON.stringify(taskForm, null, 2)"
                type="textarea"
                :rows="15"
                readonly
                placeholder="任务配置预览"
              />
            </el-card>
          </el-col>
        </el-row>
      </el-form>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Plus, Delete } from '@element-plus/icons-vue'
import { useTaskStore } from '@/stores/task'
import { useProjectStore } from '@/stores/project'

const router = useRouter()
const taskStore = useTaskStore()
const projectStore = useProjectStore()

const formRef = ref()
const saving = ref(false)
const projects = ref([])

// 标签输入相关
const tagInputVisible = ref(false)
const tagInputValue = ref('')
const tagInputRef = ref()

// 任务表单数据
const taskForm = reactive({
  name: '',
  description: '',
  project_id: '',
  task_type: '',
  priority: 'medium',
  timeout: 300,
  retry_count: 0,
  status: 'draft',
  failure_action: 'stop',
  notifications: [],
  tags: [],
  config: {
    // HTTP配置
    method: 'GET',
    url: '',
    headers: [],
    body: '',
    // 脚本配置
    script_type: '',
    script_content: '',
    env_vars: [],
    // 数据处理配置
    data_source: '',
    processing_rules: '',
    output_format: 'json',
    // 文件操作配置
    operation: '',
    source_path: '',
    target_path: ''
  }
})

// 表单验证规则
const formRules = {
  name: [
    { required: true, message: '请输入任务名称', trigger: 'blur' },
    { min: 2, max: 100, message: '任务名称长度在 2 到 100 个字符', trigger: 'blur' }
  ],
  project_id: [
    { required: true, message: '请选择所属项目', trigger: 'change' }
  ],
  task_type: [
    { required: true, message: '请选择任务类型', trigger: 'change' }
  ],
  priority: [
    { required: true, message: '请选择优先级', trigger: 'change' }
  ],
  timeout: [
    { required: true, message: '请输入超时时间', trigger: 'blur' },
    { type: 'number', min: 1, max: 3600, message: '超时时间在 1 到 3600 秒之间', trigger: 'blur' }
  ],
  'config.url': [
    { required: true, message: '请输入请求URL', trigger: 'blur' },
    { type: 'url', message: '请输入有效的URL', trigger: 'blur' }
  ],
  'config.script_content': [
    { required: true, message: '请输入脚本内容', trigger: 'blur' }
  ],
  'config.data_source': [
    { required: true, message: '请输入数据源', trigger: 'blur' }
  ],
  'config.source_path': [
    { required: true, message: '请输入源路径', trigger: 'blur' }
  ]
}

/**
 * 获取项目列表
 */
const fetchProjects = async () => {
  try {
    const result = await projectStore.getProjectList({ page: 1, size: 100 })
    projects.value = result.items || []
  } catch (error) {
    console.error('获取项目列表失败:', error)
  }
}

/**
 * 任务类型改变处理
 */
const handleTaskTypeChange = (taskType) => {
  // 重置配置
  taskForm.config = {
    method: 'GET',
    url: '',
    headers: [],
    body: '',
    script_type: '',
    script_content: '',
    env_vars: [],
    data_source: '',
    processing_rules: '',
    output_format: 'json',
    operation: '',
    source_path: '',
    target_path: ''
  }
  
  // 根据任务类型初始化默认配置
  if (taskType === 'http') {
    taskForm.config.headers = [{ key: 'Content-Type', value: 'application/json' }]
  } else if (taskType === 'script') {
    taskForm.config.env_vars = []
  }
}

/**
 * 添加标签
 */
const addTag = () => {
  if (tagInputValue.value && !taskForm.tags.includes(tagInputValue.value)) {
    taskForm.tags.push(tagInputValue.value)
  }
  tagInputVisible.value = false
  tagInputValue.value = ''
}

/**
 * 移除标签
 */
const removeTag = (tag) => {
  const index = taskForm.tags.indexOf(tag)
  if (index > -1) {
    taskForm.tags.splice(index, 1)
  }
}

/**
 * 显示标签输入
 */
const showTagInput = () => {
  tagInputVisible.value = true
  nextTick(() => {
    tagInputRef.value?.focus()
  })
}

/**
 * 添加请求头
 */
const addHeader = () => {
  taskForm.config.headers.push({ key: '', value: '' })
}

/**
 * 移除请求头
 */
const removeHeader = (index) => {
  taskForm.config.headers.splice(index, 1)
}

/**
 * 添加环境变量
 */
const addEnvVar = () => {
  taskForm.config.env_vars.push({ key: '', value: '' })
}

/**
 * 移除环境变量
 */
const removeEnvVar = (index) => {
  taskForm.config.env_vars.splice(index, 1)
}

/**
 * 返回上一页
 */
const goBack = () => {
  router.back()
}

/**
 * 保存草稿
 */
const saveDraft = async () => {
  try {
    taskForm.status = 'draft'
    await saveTask()
  } catch (error) {
    console.error('保存草稿失败:', error)
  }
}

/**
 * 保存任务
 */
const saveTask = async () => {
  try {
    await formRef.value?.validate()
    saving.value = true
    
    // 清理空的配置项
    const cleanConfig = { ...taskForm.config }
    if (cleanConfig.headers) {
      cleanConfig.headers = cleanConfig.headers.filter(h => h.key && h.value)
    }
    if (cleanConfig.env_vars) {
      cleanConfig.env_vars = cleanConfig.env_vars.filter(e => e.key && e.value)
    }
    
    const taskData = {
      ...taskForm,
      config: cleanConfig
    }
    
    await taskStore.createTask(taskData)
    ElMessage.success('任务创建成功')
    router.push('/tasks')
  } catch (error) {
    if (error !== false) { // 表单验证失败时不显示错误消息
      ElMessage.error('任务创建失败')
    }
  } finally {
    saving.value = false
  }
}

onMounted(() => {
  fetchProjects()
})
</script>

<style scoped>
.task-create {
  padding: 20px;
}

.create-content {
  margin-top: 20px;
}

.form-card {
  margin-bottom: 20px;
}

.key-value-editor {
  border: 1px solid var(--el-border-color);
  border-radius: 4px;
  padding: 12px;
  background: var(--el-fill-color-lighter);
}

.key-value-row {
  display: flex;
  align-items: center;
  margin-bottom: 8px;
}

.key-value-row:last-child {
  margin-bottom: 0;
}
</style>