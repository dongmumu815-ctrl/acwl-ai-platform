<template>
  <div class="workflow-create">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="header-content">
        <h1>创建工作流</h1>
        <p>设计和配置您的工作流程</p>
      </div>
      <div class="header-actions">
        <el-button @click="$router.back()">
          <el-icon><ArrowLeft /></el-icon>
          返回
        </el-button>
        <el-button type="primary" :loading="saving" @click="handleSave">
          <el-icon><Check /></el-icon>
          保存工作流
        </el-button>
      </div>
    </div>
    
    <div class="create-content">
      <!-- 基本信息 -->
      <el-card class="info-card" shadow="never">
        <template #header>
          <h3>基本信息</h3>
        </template>
        
        <el-form
          ref="workflowFormRef"
          :model="workflowForm"
          :rules="workflowRules"
          label-width="100px"
          class="workflow-form"
        >
          <el-row :gutter="24">
            <el-col :span="12">
              <el-form-item label="工作流名称" prop="name">
                <el-input
                  v-model="workflowForm.name"
                  placeholder="请输入工作流名称"
                  clearable
                />
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item label="所属项目">
                <el-input
                  :value="projectStore.currentProject?.name || '未选择项目'"
                  readonly
                  style="width: 100%"
                >
                  <template #prepend>
                    <el-icon><FolderOpened /></el-icon>
                  </template>
                </el-input>
              </el-form-item>
            </el-col>
          </el-row>
          
          <el-form-item label="描述" prop="description">
            <el-input
              v-model="workflowForm.description"
              type="textarea"
              :rows="3"
              placeholder="请输入工作流描述"
            />
          </el-form-item>
          
          <el-row :gutter="24">
            <el-col :span="8">
              <el-form-item label="状态" prop="status">
                <el-select
                  v-model="workflowForm.status"
                  placeholder="请选择状态"
                  style="width: 100%"
                >
                  <el-option label="活跃" value="active" />
                  <el-option label="未激活" value="inactive" />
                </el-select>
              </el-form-item>
            </el-col>
            <el-col :span="8">
              <el-form-item label="优先级" prop="priority">
                <el-select
                  v-model="workflowForm.priority"
                  placeholder="请选择优先级"
                  style="width: 100%"
                >
                  <el-option label="低" value="low" />
                  <el-option label="中" value="medium" />
                  <el-option label="高" value="high" />
                  <el-option label="紧急" value="urgent" />
                </el-select>
              </el-form-item>
            </el-col>
            <el-col :span="8">
              <el-form-item label="超时时间" prop="timeout">
                <el-input-number
                  v-model="workflowForm.timeout"
                  :min="0"
                  :max="86400"
                  placeholder="秒"
                  style="width: 100%"
                />
              </el-form-item>
            </el-col>
          </el-row>
          
          <el-form-item label="标签">
            <el-tag
              v-for="tag in workflowForm.tags"
              :key="tag"
              closable
              @close="removeTag(tag)"
              class="tag-item"
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
            <el-button
              v-else
              size="small"
              @click="showTagInput"
            >
              + 添加标签
            </el-button>
          </el-form-item>
        </el-form>
      </el-card>
      

    </div>
    

  </div>
</template>

<script setup>
import { ref, reactive, nextTick, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useWorkflowStore, useProjectStore } from '@/stores'
import { ElMessage } from 'element-plus'
import { FolderOpened } from '@element-plus/icons-vue'

/**
 * 工作流创建页面组件
 */
const router = useRouter()
const workflowStore = useWorkflowStore()
const projectStore = useProjectStore()

// 表单引用
const workflowFormRef = ref()
const tagInputRef = ref()

// 保存状态
const saving = ref(false)

// 标签输入
const tagInputVisible = ref(false)
const tagInputValue = ref('')

// 工作流表单
const workflowForm = reactive({
  name: '',
  description: '',
  status: 'active',
  priority: 'medium',
  timeout: 3600,
  tags: []
})

// 工作流表单验证规则
const workflowRules = {
  name: [
    { required: true, message: '请输入工作流名称', trigger: 'blur' },
    { min: 2, max: 50, message: '名称长度在 2 到 50 个字符', trigger: 'blur' }
  ],
  status: [
    { required: true, message: '请选择状态', trigger: 'change' }
  ],
  priority: [
    { required: true, message: '请选择优先级', trigger: 'change' }
  ]
}



/**
 * 检查当前项目
 */
const checkCurrentProject = () => {
  if (!projectStore.currentProject) {
    ElMessage.warning('请先选择一个项目')
    router.push('/projects')
    return false
  }
  return true
}

/**
 * 显示标签输入框
 */
const showTagInput = () => {
  tagInputVisible.value = true
  nextTick(() => {
    tagInputRef.value?.focus()
  })
}

/**
 * 添加标签
 */
const addTag = () => {
  const tag = tagInputValue.value.trim()
  if (tag && !workflowForm.tags.includes(tag)) {
    workflowForm.tags.push(tag)
  }
  tagInputVisible.value = false
  tagInputValue.value = ''
}

/**
 * 移除标签
 */
const removeTag = (tag) => {
  const index = workflowForm.tags.indexOf(tag)
  if (index > -1) {
    workflowForm.tags.splice(index, 1)
  }
}



/**
 * 保存工作流
 */
const handleSave = async () => {
  if (!workflowFormRef.value) return
  
  // 检查当前项目
  if (!checkCurrentProject()) return
  
  try {
    const valid = await workflowFormRef.value.validate()
    if (!valid) return
    

    
    saving.value = true
    
    const workflowData = {
      ...workflowForm,
      project_id: projectStore.currentProject.id
    }
    
    await workflowStore.createWorkflow(workflowData)
    ElMessage.success('工作流创建成功')
    router.push('/workflows')
  } catch (error) {
    ElMessage.error(error.message || '创建工作流失败')
  } finally {
    saving.value = false
  }
}

/**
 * 组件挂载时检查当前项目
 */
onMounted(() => {
  checkCurrentProject()
})
</script>

<style scoped>
.workflow-create {
  padding: 24px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 24px;
}

.header-content h1 {
  margin: 0 0 8px;
  font-size: 24px;
  font-weight: 600;
  color: #1f2937;
}

.header-content p {
  margin: 0;
  color: #6b7280;
  font-size: 14px;
}

.header-actions {
  display: flex;
  gap: 12px;
}

.create-content {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.info-card {
  border: 1px solid #e5e7eb;
}

.info-card h3 {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
  color: #1f2937;
}

.workflow-form {
  margin-top: 16px;
}

.tag-item {
  margin-right: 8px;
  margin-bottom: 8px;
}



/* 响应式设计 */
@media (max-width: 768px) {
  .workflow-create {
    padding: 16px;
  }
  
  .page-header {
    flex-direction: column;
    gap: 16px;
    align-items: stretch;
  }
  
  .header-actions {
    justify-content: flex-end;
  }
  

}
</style>