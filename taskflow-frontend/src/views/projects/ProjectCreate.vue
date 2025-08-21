<template>
  <div class="project-create">
    <el-page-header @back="goBack" content="创建项目">
      <template #extra>
        <el-space>
          <el-button @click="saveDraft">保存草稿</el-button>
          <el-button type="primary" @click="saveProject" :loading="saving">创建项目</el-button>
        </el-space>
      </template>
    </el-page-header>

    <div class="create-content">
      <el-form
        ref="formRef"
        :model="projectForm"
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
              
              <el-form-item label="项目名称" prop="name">
                <el-input
                  v-model="projectForm.name"
                  placeholder="请输入项目名称"
                  maxlength="100"
                  show-word-limit
                />
              </el-form-item>
              
              <el-form-item label="项目描述" prop="description">
                <el-input
                  v-model="projectForm.description"
                  type="textarea"
                  :rows="4"
                  placeholder="请输入项目描述"
                  maxlength="500"
                  show-word-limit
                />
              </el-form-item>
              
              <el-row :gutter="20">
                <el-col :span="12">
                  <el-form-item label="项目负责人" prop="owner_id">
                    <el-select v-model="projectForm.owner_id" placeholder="选择负责人" style="width: 100%" filterable>
                      <el-option
                        v-for="user in users"
                        :key="user.id"
                        :label="user.name"
                        :value="user.id"
                      >
                        <div class="user-option">
                          <el-avatar :size="24" :src="user.avatar">
                            {{ user.name?.charAt(0) }}
                          </el-avatar>
                          <span class="user-name">{{ user.name }}</span>
                          <span class="user-email">{{ user.email }}</span>
                        </div>
                      </el-option>
                    </el-select>
                  </el-form-item>
                </el-col>
                <el-col :span="12">
                  <el-form-item label="项目状态" prop="status">
                    <el-radio-group v-model="projectForm.status">
                      <el-radio label="active">激活</el-radio>
                      <el-radio label="inactive">停用</el-radio>
                    </el-radio-group>
                  </el-form-item>
                </el-col>
              </el-row>
              
              <el-form-item label="项目标签">
                <el-tag
                  v-for="tag in projectForm.tags"
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

            <!-- 项目设置 -->
            <el-card class="form-card">
              <template #header>
                <span>项目设置</span>
              </template>
              
              <el-form-item label="工作流设置">
                <el-row :gutter="20">
                  <el-col :span="8">
                    <el-form-item label="最大并发数" label-width="100px">
                      <el-input-number
                        v-model="projectForm.settings.max_concurrent_workflows"
                        :min="1"
                        :max="100"
                        style="width: 100%"
                      />
                    </el-form-item>
                  </el-col>
                  <el-col :span="8">
                    <el-form-item label="默认超时" label-width="100px">
                      <el-input-number
                        v-model="projectForm.settings.default_timeout"
                        :min="60"
                        :max="86400"
                        style="width: 100%"
                      />
                      <div class="form-tip">秒</div>
                    </el-form-item>
                  </el-col>
                  <el-col :span="8">
                    <el-form-item label="重试次数" label-width="100px">
                      <el-input-number
                        v-model="projectForm.settings.default_retry_count"
                        :min="0"
                        :max="10"
                        style="width: 100%"
                      />
                    </el-form-item>
                  </el-col>
                </el-row>
              </el-form-item>
              
              <el-form-item label="通知设置">
                <el-checkbox-group v-model="projectForm.settings.notifications">
                  <el-checkbox label="workflow_success">工作流成功时通知</el-checkbox>
                  <el-checkbox label="workflow_failure">工作流失败时通知</el-checkbox>
                  <el-checkbox label="task_failure">任务失败时通知</el-checkbox>
                  <el-checkbox label="daily_report">每日报告</el-checkbox>
                </el-checkbox-group>
              </el-form-item>
              
              <el-form-item label="通知邮箱">
                <el-input
                  v-model="projectForm.settings.notification_emails"
                  placeholder="多个邮箱用逗号分隔"
                  type="textarea"
                  :rows="2"
                />
                <div class="form-tip">多个邮箱地址用逗号分隔</div>
              </el-form-item>
              
              <el-form-item label="数据保留">
                <el-row :gutter="20">
                  <el-col :span="12">
                    <el-form-item label="执行记录" label-width="100px">
                      <el-input-number
                        v-model="projectForm.settings.execution_retention_days"
                        :min="7"
                        :max="365"
                        style="width: 100%"
                      />
                      <div class="form-tip">天</div>
                    </el-form-item>
                  </el-col>
                  <el-col :span="12">
                    <el-form-item label="日志文件" label-width="100px">
                      <el-input-number
                        v-model="projectForm.settings.log_retention_days"
                        :min="7"
                        :max="365"
                        style="width: 100%"
                      />
                      <div class="form-tip">天</div>
                    </el-form-item>
                  </el-col>
                </el-row>
              </el-form-item>
            </el-card>

            <!-- 权限设置 -->
            <el-card class="form-card">
              <template #header>
                <span>权限设置</span>
              </template>
              
              <el-form-item label="项目可见性">
                <el-radio-group v-model="projectForm.visibility">
                  <el-radio label="public">公开 - 所有用户可见</el-radio>
                  <el-radio label="private">私有 - 仅项目成员可见</el-radio>
                </el-radio-group>
              </el-form-item>
              
              <el-form-item label="项目成员" v-if="projectForm.visibility === 'private'">
                <div class="member-list">
                  <div v-for="(member, index) in projectForm.members" :key="index" class="member-item">
                    <el-select v-model="member.user_id" placeholder="选择用户" style="width: 200px" filterable>
                      <el-option
                        v-for="user in users"
                        :key="user.id"
                        :label="user.name"
                        :value="user.id"
                      >
                        <div class="user-option">
                          <el-avatar :size="20" :src="user.avatar">
                            {{ user.name?.charAt(0) }}
                          </el-avatar>
                          <span class="user-name">{{ user.name }}</span>
                        </div>
                      </el-option>
                    </el-select>
                    <el-select v-model="member.role" placeholder="选择角色" style="width: 120px; margin-left: 10px">
                      <el-option label="管理员" value="admin" />
                      <el-option label="编辑者" value="editor" />
                      <el-option label="查看者" value="viewer" />
                    </el-select>
                    <el-button type="danger" text @click="removeMember(index)" style="margin-left: 10px">
                      <el-icon><Delete /></el-icon>
                    </el-button>
                  </div>
                  <el-button type="primary" text @click="addMember">
                    <el-icon><Plus /></el-icon>
                    添加成员
                  </el-button>
                </div>
              </el-form-item>
            </el-card>
          </el-col>

          <el-col :span="8">
            <!-- 项目模板 -->
            <el-card class="form-card">
              <template #header>
                <span>项目模板</span>
              </template>
              
              <div class="template-list">
                <div
                  v-for="template in templates"
                  :key="template.id"
                  class="template-item"
                  :class="{ active: selectedTemplate === template.id }"
                  @click="selectTemplate(template)"
                >
                  <div class="template-icon">
                    <el-icon :size="24"><component :is="template.icon" /></el-icon>
                  </div>
                  <div class="template-info">
                    <div class="template-name">{{ template.name }}</div>
                    <div class="template-description">{{ template.description }}</div>
                  </div>
                </div>
              </div>
            </el-card>

            <!-- 配置预览 -->
            <el-card class="form-card">
              <template #header>
                <span>配置预览</span>
              </template>
              <el-input
                :model-value="JSON.stringify(projectForm, null, 2)"
                type="textarea"
                :rows="20"
                readonly
                placeholder="项目配置预览"
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
import { Plus, Delete, Folder, DataAnalysis, Setting, Monitor } from '@element-plus/icons-vue'
import { useProjectStore } from '@/stores/project'
import { useUserStore } from '@/stores/user'

const router = useRouter()
const projectStore = useProjectStore()
const userStore = useUserStore()

const formRef = ref()
const saving = ref(false)
const users = ref([])
const selectedTemplate = ref(null)

// 标签输入相关
const tagInputVisible = ref(false)
const tagInputValue = ref('')
const tagInputRef = ref()

// 项目表单数据
const projectForm = reactive({
  name: '',
  description: '',
  owner_id: '',
  status: 'active',
  visibility: 'public',
  tags: [],
  members: [],
  settings: {
    max_concurrent_workflows: 10,
    default_timeout: 3600,
    default_retry_count: 3,
    notifications: ['workflow_failure', 'task_failure'],
    notification_emails: '',
    execution_retention_days: 30,
    log_retention_days: 7
  }
})

// 项目模板
const templates = ref([
  {
    id: 'blank',
    name: '空白项目',
    description: '从零开始创建项目',
    icon: 'Folder',
    config: {}
  },
  {
    id: 'data_processing',
    name: '数据处理',
    description: '数据ETL和分析项目',
    icon: 'DataAnalysis',
    config: {
      settings: {
        max_concurrent_workflows: 5,
        default_timeout: 7200,
        notifications: ['workflow_failure', 'daily_report']
      }
    }
  },
  {
    id: 'automation',
    name: '自动化运维',
    description: '系统监控和自动化运维',
    icon: 'Setting',
    config: {
      settings: {
        max_concurrent_workflows: 20,
        default_timeout: 1800,
        notifications: ['workflow_failure', 'task_failure']
      }
    }
  },
  {
    id: 'monitoring',
    name: '监控告警',
    description: '系统监控和告警处理',
    icon: 'Monitor',
    config: {
      settings: {
        max_concurrent_workflows: 50,
        default_timeout: 300,
        notifications: ['workflow_failure', 'task_failure', 'daily_report']
      }
    }
  }
])

// 表单验证规则
const formRules = {
  name: [
    { required: true, message: '请输入项目名称', trigger: 'blur' },
    { min: 2, max: 100, message: '项目名称长度在 2 到 100 个字符', trigger: 'blur' }
  ],
  owner_id: [
    { required: true, message: '请选择项目负责人', trigger: 'change' }
  ]
}

/**
 * 获取用户列表
 */
const fetchUsers = async () => {
  try {
    const result = await userStore.getUserList({ page: 1, size: 100 })
    users.value = result.items || []
  } catch (error) {
    console.error('获取用户列表失败:', error)
  }
}

/**
 * 选择项目模板
 */
const selectTemplate = (template) => {
  selectedTemplate.value = template.id
  
  // 应用模板配置
  if (template.config.settings) {
    Object.assign(projectForm.settings, template.config.settings)
  }
}

/**
 * 添加标签
 */
const addTag = () => {
  if (tagInputValue.value && !projectForm.tags.includes(tagInputValue.value)) {
    projectForm.tags.push(tagInputValue.value)
  }
  tagInputVisible.value = false
  tagInputValue.value = ''
}

/**
 * 移除标签
 */
const removeTag = (tag) => {
  const index = projectForm.tags.indexOf(tag)
  if (index > -1) {
    projectForm.tags.splice(index, 1)
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
 * 添加成员
 */
const addMember = () => {
  projectForm.members.push({
    user_id: '',
    role: 'viewer'
  })
}

/**
 * 移除成员
 */
const removeMember = (index) => {
  projectForm.members.splice(index, 1)
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
    projectForm.status = 'inactive'
    await saveProject()
  } catch (error) {
    console.error('保存草稿失败:', error)
  }
}

/**
 * 保存项目
 */
const saveProject = async () => {
  try {
    await formRef.value?.validate()
    saving.value = true
    
    // 处理通知邮箱
    if (projectForm.settings.notification_emails) {
      projectForm.settings.notification_emails = projectForm.settings.notification_emails
        .split(',')
        .map(email => email.trim())
        .filter(email => email)
        .join(',')
    }
    
    // 清理空的成员
    projectForm.members = projectForm.members.filter(member => member.user_id)
    
    await projectStore.createProject(projectForm)
    ElMessage.success('项目创建成功')
    router.push('/projects')
  } catch (error) {
    if (error !== false) { // 表单验证失败时不显示错误消息
      ElMessage.error('项目创建失败')
    }
  } finally {
    saving.value = false
  }
}

onMounted(() => {
  fetchUsers()
  // 默认选择空白模板
  selectTemplate(templates.value[0])
})
</script>

<style scoped>
.project-create {
  padding: 20px;
}

.create-content {
  margin-top: 20px;
}

.form-card {
  margin-bottom: 20px;
}

.form-tip {
  font-size: 12px;
  color: var(--el-text-color-regular);
  margin-top: 4px;
}

.user-option {
  display: flex;
  align-items: center;
  gap: 8px;
}

.user-name {
  font-weight: 500;
}

.user-email {
  font-size: 12px;
  color: var(--el-text-color-regular);
}

.member-list {
  border: 1px solid var(--el-border-color);
  border-radius: 4px;
  padding: 12px;
  background: var(--el-fill-color-lighter);
}

.member-item {
  display: flex;
  align-items: center;
  margin-bottom: 12px;
}

.member-item:last-child {
  margin-bottom: 0;
}

.template-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.template-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  border: 1px solid var(--el-border-color-lighter);
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
}

.template-item:hover {
  border-color: var(--el-color-primary);
  background: var(--el-fill-color-lighter);
}

.template-item.active {
  border-color: var(--el-color-primary);
  background: var(--el-color-primary-light-9);
}

.template-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 40px;
  height: 40px;
  background: var(--el-color-primary-light-8);
  border-radius: 8px;
  color: var(--el-color-primary);
}

.template-info {
  flex: 1;
}

.template-name {
  font-weight: 500;
  font-size: 14px;
  margin-bottom: 4px;
}

.template-description {
  font-size: 12px;
  color: var(--el-text-color-regular);
}
</style>