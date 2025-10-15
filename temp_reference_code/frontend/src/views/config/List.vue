<template>
  <div>
    <div class="page-card">
      <div class="page-header">
        <h2>系统配置</h2>
        <el-button type="primary" @click="showAddDialog">
          <el-icon><Plus /></el-icon>
          添加配置
        </el-button>
      </div>
      
      <div class="page-content">
        <!-- 搜索栏 -->
        <div class="table-toolbar">
          <el-input
            v-model="searchQuery"
            placeholder="搜索配置键或描述"
            style="width: 300px;"
            clearable
          >
            <template #prefix>
              <el-icon><Search /></el-icon>
            </template>
          </el-input>
          <div>
            <el-select v-model="categoryFilter" placeholder="选择分类" style="width: 150px; margin-right: 10px;" clearable>
              <el-option label="全部分类" value="" />
              <el-option label="系统设置" value="system" />
              <el-option label="API设置" value="api" />
              <el-option label="邮件设置" value="email" />
              <el-option label="存储设置" value="storage" />
              <el-option label="安全设置" value="security" />
              <el-option label="其他" value="other" />
            </el-select>
            <el-button @click="loadConfigs">刷新</el-button>
          </div>
        </div>
        
        <!-- 配置表格 -->
        <el-table
          :data="filteredConfigs"
          style="width: 100%"
          v-loading="loading"
        >
          <el-table-column prop="id" label="ID" width="80" />
          <el-table-column prop="key" label="配置键" width="200">
            <template #default="{ row }">
              <el-tag type="info">{{ row.key }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="value" label="配置值" width="250">
            <template #default="{ row }">
              <div class="config-value">
                <span v-if="row.value_type === 'password'" class="password-mask">••••••••</span>
                <span v-else-if="row.value && row.value.length > 50" :title="row.value">
                  {{ row.value.substring(0, 50) }}...
                </span>
                <span v-else>{{ row.value || '(空)' }}</span>
              </div>
            </template>
          </el-table-column>
          <el-table-column prop="value_type" label="类型" width="100">
            <template #default="{ row }">
              <el-tag :type="getTypeTagType(row.value_type)">{{ getTypeText(row.value_type) }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="category" label="分类" width="120">
            <template #default="{ row }">
              <el-tag :type="getCategoryTagType(row.category)">{{ getCategoryText(row.category) }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="description" label="描述" min-width="200" />
          <el-table-column prop="is_active" label="状态" width="100">
            <template #default="{ row }">
              <el-tag :type="row.is_active ? 'success' : 'danger'">
                {{ row.is_active ? '启用' : '禁用' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="updated_at" label="更新时间" width="180">
            <template #default="{ row }">
              {{ formatDate(row.updated_at) }}
            </template>
          </el-table-column>
          <el-table-column label="操作" width="180" fixed="right">
            <template #default="{ row }">
              <el-button size="small" @click="showEditDialog(row)">编辑</el-button>
              <el-button
                size="small"
                :type="row.is_active ? 'warning' : 'success'"
                @click="toggleConfigStatus(row)"
              >
                {{ row.is_active ? '禁用' : '启用' }}
              </el-button>
              <el-button
                size="small"
                type="danger"
                @click="deleteConfig(row)"
              >
                删除
              </el-button>
            </template>
          </el-table-column>
        </el-table>
        
        <!-- 分页 -->
        <div style="margin-top: 20px; text-align: right;">
          <el-pagination
            v-model:current-page="currentPage"
            v-model:page-size="pageSize"
            :page-sizes="[10, 20, 50, 100]"
            :total="total"
            layout="total, sizes, prev, pager, next, jumper"
            @size-change="handleSizeChange"
            @current-change="handleCurrentChange"
          />
        </div>
      </div>
    </div>
    
    <!-- 添加/编辑配置对话框 -->
    <el-dialog
      v-model="dialogVisible"
      :title="dialogTitle"
      width="600px"
      @close="resetForm"
    >
      <el-form
        ref="configFormRef"
        :model="configForm"
        :rules="configRules"
        label-width="100px"
      >
        <el-form-item label="配置键" prop="key">
          <el-input
            v-model="configForm.key"
            :disabled="isEdit"
            placeholder="请输入配置键，如：system.title"
          />
        </el-form-item>
        
        <el-form-item label="配置值" prop="value">
          <el-input
            v-if="configForm.value_type === 'text' || configForm.value_type === 'url'"
            v-model="configForm.value"
            placeholder="请输入配置值"
          />
          <el-input
            v-else-if="configForm.value_type === 'textarea'"
            v-model="configForm.value"
            type="textarea"
            :rows="4"
            placeholder="请输入配置值"
          />
          <el-input
            v-else-if="configForm.value_type === 'password'"
            v-model="configForm.value"
            type="password"
            placeholder="请输入配置值"
            show-password
          />
          <el-input-number
            v-else-if="configForm.value_type === 'number'"
            v-model="configForm.value"
            style="width: 100%;"
            placeholder="请输入数字"
          />
          <el-switch
            v-else-if="configForm.value_type === 'boolean'"
            v-model="configForm.value"
            active-text="是"
            inactive-text="否"
          />
          <el-input
            v-else
            v-model="configForm.value"
            placeholder="请输入配置值"
          />
        </el-form-item>
        
        <el-form-item label="值类型" prop="value_type">
          <el-select v-model="configForm.value_type" placeholder="请选择值类型" style="width: 100%;">
            <el-option label="文本" value="text" />
            <el-option label="多行文本" value="textarea" />
            <el-option label="数字" value="number" />
            <el-option label="布尔值" value="boolean" />
            <el-option label="密码" value="password" />
            <el-option label="URL" value="url" />
            <el-option label="JSON" value="json" />
          </el-select>
        </el-form-item>
        
        <el-form-item label="分类" prop="category">
          <el-select v-model="configForm.category" placeholder="请选择分类" style="width: 100%;">
            <el-option label="系统设置" value="system" />
            <el-option label="API设置" value="api" />
            <el-option label="邮件设置" value="email" />
            <el-option label="存储设置" value="storage" />
            <el-option label="安全设置" value="security" />
            <el-option label="其他" value="other" />
          </el-select>
        </el-form-item>
        
        <el-form-item label="描述" prop="description">
          <el-input
            v-model="configForm.description"
            type="textarea"
            :rows="2"
            placeholder="请输入配置描述"
          />
        </el-form-item>
        
        <el-form-item label="状态" prop="is_active">
          <el-switch
            v-model="configForm.is_active"
            active-text="启用"
            inactive-text="禁用"
          />
        </el-form-item>
        
        <el-form-item label="是否敏感" prop="is_sensitive">
          <el-switch
            v-model="configForm.is_sensitive"
            active-text="是"
            inactive-text="否"
          />
          <div class="form-tip">敏感配置将在日志中隐藏</div>
        </el-form-item>
      </el-form>
      
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="dialogVisible = false">取消</el-button>
          <el-button type="primary" @click="saveConfig" :loading="saving">
            {{ saving ? '保存中...' : '保存' }}
          </el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import api from '@/utils/api'
import dayjs from 'dayjs'

// 响应式数据
const loading = ref(false)
const saving = ref(false)
const configs = ref([])
const searchQuery = ref('')
const categoryFilter = ref('')
const currentPage = ref(1)
const pageSize = ref(20)
const total = ref(0)

// 对话框相关
const dialogVisible = ref(false)
const isEdit = ref(false)
const configFormRef = ref()

// 配置表单
const configForm = reactive({
  id: null,
  key: '',
  value: '',
  value_type: 'text',
  category: 'system',
  description: '',
  is_active: true,
  is_sensitive: false
})

// 表单验证规则
const configRules = {
  key: [
    { required: true, message: '请输入配置键', trigger: 'blur' },
    { min: 2, max: 100, message: '配置键长度在 2 到 100 个字符', trigger: 'blur' },
    { pattern: /^[a-zA-Z][a-zA-Z0-9._-]*$/, message: '配置键只能包含字母、数字、点、下划线和连字符，且必须以字母开头', trigger: 'blur' }
  ],
  value: [
    { required: true, message: '请输入配置值', trigger: 'blur' }
  ],
  value_type: [
    { required: true, message: '请选择值类型', trigger: 'change' }
  ],
  category: [
    { required: true, message: '请选择分类', trigger: 'change' }
  ],
  description: [
    { required: true, message: '请输入配置描述', trigger: 'blur' }
  ]
}

// 计算属性
const dialogTitle = computed(() => isEdit.value ? '编辑配置' : '添加配置')

const filteredConfigs = computed(() => {
  let result = configs.value
  
  // 按分类筛选
  if (categoryFilter.value) {
    result = result.filter(config => config.category === categoryFilter.value)
  }
  
  // 按搜索关键词筛选
  if (searchQuery.value) {
    const query = searchQuery.value.toLowerCase()
    result = result.filter(config => 
      config.key.toLowerCase().includes(query) ||
      (config.description && config.description.toLowerCase().includes(query))
    )
  }
  
  return result
})

// 获取类型标签类型
const getTypeTagType = (type) => {
  const typeMap = {
    'text': 'primary',
    'textarea': 'primary',
    'number': 'success',
    'boolean': 'warning',
    'password': 'danger',
    'url': 'info',
    'json': 'primary'
  }
  return typeMap[type] || 'default'
}

// 获取类型文本
const getTypeText = (type) => {
  const textMap = {
    'text': '文本',
    'textarea': '多行',
    'number': '数字',
    'boolean': '布尔',
    'password': '密码',
    'url': 'URL',
    'json': 'JSON'
  }
  return textMap[type] || type
}

// 获取分类标签类型
const getCategoryTagType = (category) => {
  const typeMap = {
    'system': 'primary',
    'api': 'success',
    'email': 'warning',
    'storage': 'info',
    'security': 'danger',
    'other': 'default'
  }
  return typeMap[category] || 'default'
}

// 获取分类文本
const getCategoryText = (category) => {
  const textMap = {
    'system': '系统设置',
    'api': 'API设置',
    'email': '邮件设置',
    'storage': '存储设置',
    'security': '安全设置',
    'other': '其他'
  }
  return textMap[category] || category
}

// 格式化日期
const formatDate = (dateString) => {
  return dayjs(dateString).format('YYYY-MM-DD HH:mm:ss')
}

// 加载配置列表
const loadConfigs = async () => {
  loading.value = true
  try {
    const response = await api.get('/admin/configs', {
      params: {
        page: currentPage.value,
        size: pageSize.value
      }
    })
    
    configs.value = response.data.items || []
    total.value = response.data.total || 0
  } catch (error) {
    console.error('加载配置列表失败:', error)
    ElMessage.error('加载配置列表失败')
  } finally {
    loading.value = false
  }
}

// 分页处理
const handleSizeChange = (val) => {
  pageSize.value = val
  currentPage.value = 1
  loadConfigs()
}

const handleCurrentChange = (val) => {
  currentPage.value = val
  loadConfigs()
}

// 显示添加对话框
const showAddDialog = () => {
  isEdit.value = false
  dialogVisible.value = true
}

// 显示编辑对话框
const showEditDialog = (config) => {
  isEdit.value = true
  Object.assign(configForm, config)
  dialogVisible.value = true
}

// 重置表单
const resetForm = () => {
  if (configFormRef.value) {
    configFormRef.value.resetFields()
  }
  Object.assign(configForm, {
    id: null,
    key: '',
    value: '',
    value_type: 'text',
    category: 'system',
    description: '',
    is_active: true,
    is_sensitive: false
  })
}

// 保存配置
const saveConfig = async () => {
  if (!configFormRef.value) return
  
  try {
    const valid = await configFormRef.value.validate()
    if (!valid) return
    
    saving.value = true
    
    const data = { ...configForm }
    
    // 处理不同类型的值
    if (data.value_type === 'number') {
      data.value = Number(data.value)
    } else if (data.value_type === 'boolean') {
      data.value = Boolean(data.value)
    } else {
      data.value = String(data.value)
    }
    
    if (isEdit.value) {
      await api.put(`/admin/configs/${configForm.id}`, data)
      ElMessage.success('配置更新成功')
    } else {
      await api.post('/admin/configs', data)
      ElMessage.success('配置添加成功')
    }
    
    dialogVisible.value = false
    loadConfigs()
  } catch (error) {
    console.error('保存配置失败:', error)
    ElMessage.error('保存配置失败')
  } finally {
    saving.value = false
  }
}

// 切换配置状态
const toggleConfigStatus = async (config) => {
  try {
    const action = config.is_active ? '禁用' : '启用'
    await ElMessageBox.confirm(`确定要${action}配置 "${config.key}" 吗？`, '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    
    await api.put(`/admin/configs/${config.id}`, {
      ...config,
      is_active: !config.is_active
    })
    
    ElMessage.success(`配置${action}成功`)
    loadConfigs()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('切换配置状态失败:', error)
      ElMessage.error('操作失败')
    }
  }
}

// 删除配置
const deleteConfig = async (config) => {
  try {
    await ElMessageBox.confirm(`确定要删除配置 "${config.key}" 吗？此操作不可恢复！`, '警告', {
      confirmButtonText: '确定删除',
      cancelButtonText: '取消',
      type: 'error'
    })
    
    await api.delete(`/admin/configs/${config.id}`)
    ElMessage.success('配置删除成功')
    loadConfigs()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除配置失败:', error)
      ElMessage.error('删除配置失败')
    }
  }
}

// 组件挂载时加载数据
onMounted(() => {
  loadConfigs()
})
</script>

<style scoped>
.page-card {
  background: #fff;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.page-header {
  padding: 20px;
  border-bottom: 1px solid #f0f0f0;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.page-header h2 {
  margin: 0;
  color: #333;
}

.page-content {
  padding: 20px;
}

.table-toolbar {
  margin-bottom: 16px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.config-value {
  max-width: 250px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.password-mask {
  color: #999;
  font-family: monospace;
}

.form-tip {
  font-size: 12px;
  color: #999;
  margin-top: 4px;
}
</style>