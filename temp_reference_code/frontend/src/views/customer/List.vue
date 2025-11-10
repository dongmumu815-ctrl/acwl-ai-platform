<template>
  <div>
    <div class="page-card">
      <div class="page-header">
        <h2>平台管理</h2>
        <el-button type="primary" @click="showAddDialog">
          <el-icon><Plus /></el-icon>
          添加平台
        </el-button>
      </div>
      
      <div class="page-content">
        <!-- 搜索栏 -->
        <div class="table-toolbar">
          <el-input
            v-model="searchQuery"
            placeholder="搜索平台名称或邮箱"
            style="width: 300px;"
            clearable
            @input="handleSearch"
          >
            <template #prefix>
              <el-icon><Search /></el-icon>
            </template>
          </el-input>
          <el-button @click="loadCustomers">刷新</el-button>
        </div>
        
        <!-- 客户表格 -->
        <el-table
          :data="filteredCustomers"
          style="width: 100%"
          v-loading="loading"
        >
          <el-table-column prop="id" label="ID" width="80" />
          <el-table-column prop="name" label="客户名称" width="200" />
          <el-table-column prop="email" label="邮箱" width="200" />
          <el-table-column prop="phone" label="电话" width="150" />
          <el-table-column prop="company" label="公司" width="150" />
          <el-table-column prop="app_id" label="App ID" width="120" />
          <el-table-column prop="rate_limit" label="调用限制/分钟" width="120" />
          <el-table-column prop="max_apis" label="最大API数" width="100" />
          <el-table-column prop="total_api_calls" label="总调用次数" width="120" />
          <el-table-column prop="last_api_call_at" label="最后调用时间" width="150">
            <template #default="{ row }">
              {{ row.last_api_call_at ? formatDate(row.last_api_call_at) : '从未调用' }}
            </template>
          </el-table-column>
          <el-table-column prop="created_at" label="创建时间" width="150">
            <template #default="{ row }">
              {{ formatDate(row.created_at) }}
            </template>
          </el-table-column>
          <el-table-column prop="status" label="状态" width="100">
            <template #default="{ row }">
              <el-tag :type="row.status === 'active' ? 'success' : 'danger'">
                {{ row.status === 'active' ? '启用' : '禁用' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="200" fixed="right">
            <template #default="{ row }">
              <el-button size="small" @click="showEditDialog(row)">编辑</el-button>
              <el-button
                size="small"
                :type="row.status === 'active' ? 'warning' : 'success'"
                @click="toggleCustomerStatus(row)"
              >
                {{ row.status === 'active' ? '禁用' : '启用' }}
              </el-button>
              <el-button
                size="small"
                type="info"
                @click="resetAppSecret(row)"
              >
                重置密钥
              </el-button>
              <el-button
                size="small"
                type="danger"
                @click="deleteCustomer(row)"
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
    
    <!-- 添加/编辑客户对话框 -->
    <el-dialog
      v-model="dialogVisible"
      :title="dialogTitle"
      width="600px"
      @close="resetForm"
    >
      <el-form
        ref="customerFormRef"
        :model="customerForm"
        :rules="customerRules"
        label-width="100px"
      >
        <el-form-item label="客户名称" prop="name">
          <el-input
            v-model="customerForm.name"
            placeholder="请输入客户名称"
          />
        </el-form-item>
        
        <el-form-item label="邮箱" prop="email">
          <el-input
            v-model="customerForm.email"
            placeholder="请输入邮箱地址"
          />
        </el-form-item>
        
        <el-form-item label="电话" prop="phone">
          <el-input
            v-model="customerForm.phone"
            placeholder="请输入电话号码"
          />
        </el-form-item>
        
        <el-form-item label="公司" prop="company">
          <el-input
            v-model="customerForm.company"
            placeholder="请输入公司名称"
          />
        </el-form-item>
        
        <el-form-item label="App ID" prop="app_id" v-if="isEdit">
          <el-input
            v-model="customerForm.app_id"
            readonly
            placeholder="系统自动生成"
          />
        </el-form-item>
        
        <el-form-item label="App Secret" prop="app_secret" v-if="isEdit">
          <el-input
            v-model="customerForm.app_secret"
            readonly
            placeholder="系统自动生成"
            type="password"
            show-password
          />
        </el-form-item>
        
        <el-form-item label="API调用限制" prop="rate_limit">
          <el-input-number
            v-model="customerForm.rate_limit"
            :min="0"
            placeholder="每分钟调用次数限制"
          />
        </el-form-item>
        
        <el-form-item label="最大API数量" prop="max_apis">
          <el-input-number
            v-model="customerForm.max_apis"
            :min="0"
            placeholder="最大可创建API数量"
          />
        </el-form-item>
        
        <el-form-item label="状态" prop="status">
          <el-select
            v-model="customerForm.status"
            placeholder="请选择状态"
          >
            <el-option label="启用" value="active" />
            <el-option label="禁用" value="inactive" />
          </el-select>
        </el-form-item>
        
        <el-form-item label="备注" prop="notes">
          <el-input
            v-model="customerForm.notes"
            type="textarea"
            :rows="3"
            placeholder="请输入备注信息"
          />
        </el-form-item>
      </el-form>
      
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="dialogVisible = false">取消</el-button>
          <el-button type="primary" @click="saveCustomer" :loading="saving">
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
import { Plus, Search } from '@element-plus/icons-vue'
import api from '@/utils/api'
import dayjs from 'dayjs'

// 响应式数据
const loading = ref(false)
const saving = ref(false)
const customers = ref([])
const searchQuery = ref('')
const currentPage = ref(1)
const pageSize = ref(20)
const total = ref(0)

// 对话框相关
const dialogVisible = ref(false)
const isEdit = ref(false)
const customerFormRef = ref()

// 客户表单
const customerForm = reactive({
  id: null,
  name: '',
  email: '',
  phone: '',
  company: '',
  app_id: '',
  app_secret: '',
  rate_limit: 60,
  max_apis: 10,
  status: 'active',
  notes: ''
})

// 表单验证规则
const customerRules = {
  name: [
    { required: true, message: '请输入客户名称', trigger: 'blur' },
    { min: 2, max: 50, message: '客户名称长度在 2 到 50 个字符', trigger: 'blur' }
  ],
  email: [
    { required: true, message: '请输入邮箱', trigger: 'blur' },
    { type: 'email', message: '请输入正确的邮箱格式', trigger: 'blur' }
  ],
  phone: [
    { required: true, message: '请输入电话', trigger: 'blur' },
    { pattern: /^1[3-9]\d{9}$/, message: '请输入正确的手机号码', trigger: 'blur' }
  ],
  company: [
    { required: true, message: '请输入公司名称', trigger: 'blur' }
  ],
  rate_limit: [
    { required: true, message: '请设置API调用限制', trigger: 'blur' },
    { type: 'number', min: 0, message: '调用限制不能小于0', trigger: 'blur' }
  ],
  max_apis: [
    { required: true, message: '请设置最大API数量', trigger: 'blur' },
    { type: 'number', min: 0, message: 'API数量不能小于0', trigger: 'blur' }
  ],
  status: [
    { required: true, message: '请选择状态', trigger: 'change' }
  ]
}

// 计算属性
const dialogTitle = computed(() => isEdit.value ? '编辑客户' : '添加平台')

const filteredCustomers = computed(() => {
  console.log('计算filteredCustomers, customers.value:', customers.value)
  console.log('searchQuery.value:', searchQuery.value)
  
  if (!searchQuery.value) {
    console.log('无搜索条件，返回所有客户:', customers.value)
    return customers.value
  }
  
  const query = searchQuery.value.toLowerCase()
  const filtered = customers.value.filter(customer => 
    customer.name?.toLowerCase().includes(query) ||
    customer.email?.toLowerCase().includes(query)
  )
  console.log('过滤后的客户:', filtered)
  return filtered
})

// 格式化日期
const formatDate = (dateString) => {
  return dayjs(dateString).format('YYYY-MM-DD HH:mm:ss')
}

// 加载客户列表
const loadCustomers = async () => {
  loading.value = true
  try {
    const response = await api.get('/admin/customers', {
      params: {
        page: currentPage.value,
        size: pageSize.value
      }
    })
    
    // 调试：打印完整的响应数据
    console.log('API响应数据:', response.data)
    console.log('客户数据:', response.data.data)
    console.log('分页信息:', response.data.pagination)
    
    // 根据实际API响应格式调整数据获取
    customers.value = response.data.data || []
    total.value = response.data.pagination?.total || 0
    
    console.log('设置后的customers:', customers.value)
    console.log('设置后的total:', total.value)
  } catch (error) {
    console.error('加载客户列表失败:', error)
    ElMessage.error('加载客户列表失败')
  } finally {
    loading.value = false
  }
}

// 搜索处理
const handleSearch = () => {
  // 搜索是通过计算属性实现的，这里可以添加防抖逻辑
}

// 分页处理
const handleSizeChange = (val) => {
  pageSize.value = val
  currentPage.value = 1
  loadCustomers()
}

const handleCurrentChange = (val) => {
  currentPage.value = val
  loadCustomers()
}

// 显示添加对话框
const showAddDialog = () => {
  isEdit.value = false
  dialogVisible.value = true
}

// 显示编辑对话框
const showEditDialog = (customer) => {
  isEdit.value = true
  Object.assign(customerForm, customer)
  dialogVisible.value = true
}

// 重置表单
const resetForm = () => {
  if (customerFormRef.value) {
    customerFormRef.value.resetFields()
  }
  Object.assign(customerForm, {
    id: null,
    name: '',
    email: '',
    phone: '',
    company: '',
    app_id: '',
    app_secret: '',
    rate_limit: 60,
    max_apis: 10,
    status: 'active',
    notes: ''
  })
}

// 保存客户
const saveCustomer = async () => {
  if (!customerFormRef.value) return
  
  try {
    const valid = await customerFormRef.value.validate()
    if (!valid) return
    
    saving.value = true
    
    if (isEdit.value) {
      // 编辑客户
      await api.put(`/admin/customers/${customerForm.id}`, customerForm)
      ElMessage.success('客户更新成功')
    } else {
      // 添加平台
      await api.post('/admin/customers', customerForm)
      ElMessage.success('客户添加成功')
    }
    
    dialogVisible.value = false
    loadCustomers()
  } catch (error) {
    console.error('保存客户失败:', error)
    ElMessage.error('保存客户失败')
  } finally {
    saving.value = false
  }
}

// 切换客户状态
const toggleCustomerStatus = async (customer) => {
  try {
    const action = customer.status === 'active' ? '禁用' : '启用'
    await ElMessageBox.confirm(`确定要${action}客户 "${customer.name}" 吗？`, '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    
    await api.put(`/admin/customers/${customer.id}`, {
      ...customer,
      status: customer.status === 'active' ? 'inactive' : 'active'
    })
    
    ElMessage.success(`客户${action}成功`)
    loadCustomers()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('切换客户状态失败:', error)
      ElMessage.error('操作失败')
    }
  }
}

// 重置App Secret
const resetAppSecret = async (customer) => {
  try {
    await ElMessageBox.confirm(
      '确定要重置该客户的App Secret吗？重置后原密钥将失效。',
      '确认重置',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    const response = await api.post(`/admin/customers/${customer.id}/reset-secret`)
    ElMessage.success('App Secret重置成功')
    
    // 显示新的App Secret
    ElMessageBox.alert(
      `新的App Secret: ${response.data.data.app_secret}`,
      '新密钥',
      {
        confirmButtonText: '我已保存',
        type: 'success'
      }
    )
    
    loadCustomers()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('重置密钥失败:', error)
      ElMessage.error('重置失败')
    }
  }
}

// 删除客户
const deleteCustomer = async (customer) => {
  try {
    await ElMessageBox.confirm(`确定要删除客户 "${customer.name}" 吗？此操作不可恢复！`, '警告', {
      confirmButtonText: '确定删除',
      cancelButtonText: '取消',
      type: 'error'
    })
    
    await api.delete(`/admin/customers/${customer.id}`)
    ElMessage.success('客户删除成功')
    loadCustomers()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除客户失败:', error)
      ElMessage.error('删除客户失败')
    }
  }
}

// 组件挂载时加载数据
onMounted(() => {
  loadCustomers()
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
</style>