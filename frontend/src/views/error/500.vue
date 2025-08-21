<template>
  <div class="error-page">
    <div class="error-container">
      <!-- 错误图标 -->
      <div class="error-icon">
        <svg viewBox="0 0 1024 1024" class="icon-500">
          <path d="M512 64C264.6 64 64 264.6 64 512s200.6 448 448 448 448-200.6 448-448S759.4 64 512 64zm0 820c-205.4 0-372-166.6-372-372s166.6-372 372-372 372 166.6 372 372-166.6 372-372 372z" fill="#faad14"/>
          <path d="M464 688a48 48 0 1 0 96 0 48 48 0 1 0-96 0zm24-112h48c4.4 0 8-3.6 8-8V296c0-4.4-3.6-8-8-8h-48c-4.4 0-8 3.6-8 8v272c0 4.4 3.6 8 8 8z" fill="white"/>
        </svg>
      </div>
      
      <!-- 错误信息 -->
      <div class="error-content">
        <h1 class="error-title">500</h1>
        <h2 class="error-subtitle">服务器内部错误</h2>
        <p class="error-description">
          抱歉，服务器遇到了一个错误，无法完成您的请求。
          <br>
          我们的技术团队已经收到通知，正在紧急处理这个问题。
        </p>
        
        <!-- 错误详情 -->
        <div class="error-details" v-if="showDetails">
          <el-alert
            title="错误详情"
            type="error"
            :closable="false"
            show-icon
          >
            <template #default>
              <p><strong>错误ID：</strong>{{ errorId }}</p>
              <p><strong>发生时间：</strong>{{ errorTime }}</p>
              <p><strong>请求路径：</strong>{{ requestPath }}</p>
            </template>
          </el-alert>
        </div>
        
        <!-- 操作按钮 -->
        <div class="error-actions">
          <el-button type="primary" @click="refreshPage">
            <el-icon><Refresh /></el-icon>
            刷新页面
          </el-button>
          <el-button @click="goHome">
            <el-icon><HomeFilled /></el-icon>
            返回首页
          </el-button>
          <el-button type="warning" @click="reportError">
            <el-icon><Warning /></el-icon>
            报告问题
          </el-button>
        </div>
        
        <!-- 故障排除建议 -->
        <div class="troubleshooting">
          <h3 class="troubleshooting-title">您可以尝试以下解决方案：</h3>
          <div class="troubleshooting-list">
            <div class="troubleshooting-item">
              <el-icon class="item-icon"><Refresh /></el-icon>
              <div class="item-content">
                <h4>刷新页面</h4>
                <p>这可能是一个临时问题，刷新页面可能会解决</p>
              </div>
            </div>
            
            <div class="troubleshooting-item">
              <el-icon class="item-icon"><Clock /></el-icon>
              <div class="item-content">
                <h4>稍后重试</h4>
                <p>等待几分钟后再次尝试访问</p>
              </div>
            </div>
            
            <div class="troubleshooting-item">
              <el-icon class="item-icon"><Delete /></el-icon>
              <div class="item-content">
                <h4>清除缓存</h4>
                <p>清除浏览器缓存和Cookie后重新访问</p>
              </div>
            </div>
            
            <div class="troubleshooting-item">
              <el-icon class="item-icon"><Message /></el-icon>
              <div class="item-content">
                <h4>联系支持</h4>
                <p>如果问题持续存在，请联系技术支持</p>
              </div>
            </div>
          </div>
        </div>
        
        <!-- 系统状态 -->
        <div class="system-status">
          <h3 class="status-title">系统状态检查</h3>
          <div class="status-list">
            <div class="status-item">
              <span class="status-label">API 服务</span>
              <el-tag :type="systemStatus.api" size="small">
                {{ getStatusText(systemStatus.api) }}
              </el-tag>
            </div>
            
            <div class="status-item">
              <span class="status-label">数据库</span>
              <el-tag :type="systemStatus.database" size="small">
                {{ getStatusText(systemStatus.database) }}
              </el-tag>
            </div>
            
            <div class="status-item">
              <span class="status-label">文件存储</span>
              <el-tag :type="systemStatus.storage" size="small">
                {{ getStatusText(systemStatus.storage) }}
              </el-tag>
            </div>
            
            <div class="status-item">
              <span class="status-label">GPU 集群</span>
              <el-tag :type="systemStatus.gpu" size="small">
                {{ getStatusText(systemStatus.gpu) }}
              </el-tag>
            </div>
          </div>
          
          <div class="status-actions">
            <el-button text @click="checkSystemStatus">
              <el-icon><Refresh /></el-icon>
              重新检查
            </el-button>
            <el-button text @click="toggleDetails">
              <el-icon><View /></el-icon>
              {{ showDetails ? '隐藏' : '显示' }}详情
            </el-button>
          </div>
        </div>
      </div>
    </div>
    
    <!-- 背景装饰 -->
    <div class="background-decoration">
      <div class="floating-shape shape-1"></div>
      <div class="floating-shape shape-2"></div>
      <div class="floating-shape shape-3"></div>
    </div>
    
    <!-- 错误报告对话框 -->
    <el-dialog
      v-model="reportDialogVisible"
      title="报告问题"
      width="600px"
      :before-close="handleCloseReport"
    >
      <el-form
        ref="reportFormRef"
        :model="reportForm"
        :rules="reportRules"
        label-width="100px"
      >
        <el-form-item label="问题类型" prop="type">
          <el-select
            v-model="reportForm.type"
            placeholder="请选择问题类型"
            style="width: 100%"
          >
            <el-option label="页面无法加载" value="page_load" />
            <el-option label="功能异常" value="function_error" />
            <el-option label="数据丢失" value="data_loss" />
            <el-option label="性能问题" value="performance" />
            <el-option label="其他问题" value="other" />
          </el-select>
        </el-form-item>
        
        <el-form-item label="问题描述" prop="description">
          <el-input
            v-model="reportForm.description"
            type="textarea"
            :rows="4"
            placeholder="请详细描述遇到的问题，包括操作步骤和预期结果..."
            maxlength="1000"
            show-word-limit
          />
        </el-form-item>
        
        <el-form-item label="联系方式" prop="contact">
          <el-input
            v-model="reportForm.contact"
            placeholder="请提供您的邮箱或电话，以便我们联系您"
          />
        </el-form-item>
        
        <el-form-item label="紧急程度">
          <el-radio-group v-model="reportForm.priority">
            <el-radio label="low">低</el-radio>
            <el-radio label="medium">中</el-radio>
            <el-radio label="high">高</el-radio>
            <el-radio label="urgent">紧急</el-radio>
          </el-radio-group>
        </el-form-item>
      </el-form>
      
      <template #footer>
        <div class="dialog-footer">
          <el-button @click="reportDialogVisible = false">取消</el-button>
          <el-button type="primary" @click="submitReport" :loading="submitting">
            提交报告
          </el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage, type FormInstance, type FormRules } from 'element-plus'
import {
  Refresh,
  HomeFilled,
  Warning,
  Clock,
  Delete,
  Message,
  View
} from '@element-plus/icons-vue'

const router = useRouter()
const route = useRoute()

const showDetails = ref(false)
const reportDialogVisible = ref(false)
const reportFormRef = ref<FormInstance>()
const submitting = ref(false)

// 错误信息
const errorId = ref('')
const errorTime = ref('')
const requestPath = ref('')

// 系统状态
const systemStatus = reactive({
  api: 'danger' as 'success' | 'warning' | 'danger',
  database: 'warning' as 'success' | 'warning' | 'danger',
  storage: 'success' as 'success' | 'warning' | 'danger',
  gpu: 'success' as 'success' | 'warning' | 'danger'
})

// 错误报告表单
const reportForm = reactive({
  type: '',
  description: '',
  contact: '',
  priority: 'medium'
})

// 表单验证规则
const reportRules: FormRules = {
  type: [
    { required: true, message: '请选择问题类型', trigger: 'change' }
  ],
  description: [
    { required: true, message: '请描述遇到的问题', trigger: 'blur' },
    { min: 10, message: '问题描述至少10个字符', trigger: 'blur' }
  ],
  contact: [
    { required: true, message: '请提供联系方式', trigger: 'blur' }
  ]
}

// 获取状态文本
const getStatusText = (status: string) => {
  const statusMap: Record<string, string> = {
    success: '正常',
    warning: '异常',
    danger: '故障'
  }
  return statusMap[status] || '未知'
}

// 刷新页面
const refreshPage = () => {
  window.location.reload()
}

// 返回首页
const goHome = () => {
  router.push('/dashboard')
}

// 报告错误
const reportError = () => {
  reportDialogVisible.value = true
}

// 检查系统状态
const checkSystemStatus = async () => {
  try {
    // 这里应该调用实际的API检查系统状态
    // const response = await systemApi.checkStatus()
    
    // 模拟状态检查
    ElMessage.info('正在检查系统状态...')
    
    setTimeout(() => {
      // 随机更新状态
      const statuses = ['success', 'warning', 'danger'] as const
      systemStatus.api = statuses[Math.floor(Math.random() * statuses.length)]
      systemStatus.database = statuses[Math.floor(Math.random() * statuses.length)]
      systemStatus.storage = statuses[Math.floor(Math.random() * statuses.length)]
      systemStatus.gpu = statuses[Math.floor(Math.random() * statuses.length)]
      
      ElMessage.success('系统状态已更新')
    }, 1000)
  } catch (error) {
    ElMessage.error('检查系统状态失败')
  }
}

// 切换详情显示
const toggleDetails = () => {
  showDetails.value = !showDetails.value
}

// 关闭报告对话框
const handleCloseReport = () => {
  reportForm.type = ''
  reportForm.description = ''
  reportForm.contact = ''
  reportForm.priority = 'medium'
  reportDialogVisible.value = false
}

// 提交错误报告
const submitReport = async () => {
  if (!reportFormRef.value) return
  
  try {
    await reportFormRef.value.validate()
    submitting.value = true
    
    // 这里应该调用实际的API
    // await errorApi.reportError({
    //   ...reportForm,
    //   errorId: errorId.value,
    //   requestPath: requestPath.value,
    //   userAgent: navigator.userAgent,
    //   timestamp: new Date().toISOString()
    // })
    
    // 模拟提交
    await new Promise(resolve => setTimeout(resolve, 1000))
    
    ElMessage.success('问题报告已提交，我们会尽快处理')
    handleCloseReport()
  } catch (error: any) {
    console.error('提交错误报告失败:', error)
    ElMessage.error('提交失败，请稍后重试')
  } finally {
    submitting.value = false
  }
}

// 生成错误ID
const generateErrorId = () => {
  return 'ERR-' + Date.now().toString(36).toUpperCase() + '-' + Math.random().toString(36).substr(2, 5).toUpperCase()
}

onMounted(() => {
  // 初始化错误信息
  errorId.value = generateErrorId()
  errorTime.value = new Date().toLocaleString('zh-CN')
  requestPath.value = route.fullPath
  
  // 检查系统状态
  checkSystemStatus()
})
</script>

<style lang="scss" scoped>
.error-page {
  position: relative;
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #ffecd2 0%, #fcb69f 100%);
  overflow: hidden;
  
  .error-container {
    position: relative;
    z-index: 2;
    text-align: center;
    max-width: 800px;
    padding: 40px;
    background: rgba(255, 255, 255, 0.95);
    backdrop-filter: blur(10px);
    border-radius: 20px;
    box-shadow: 0 20px 40px rgba(0, 0, 0, 0.1);
    
    .error-icon {
      margin-bottom: 30px;
      
      .icon-500 {
        width: 120px;
        height: 120px;
        opacity: 0.9;
      }
    }
    
    .error-content {
      .error-title {
        font-size: 72px;
        font-weight: 700;
        color: #faad14;
        margin: 0 0 10px 0;
        text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.1);
      }
      
      .error-subtitle {
        font-size: 24px;
        font-weight: 600;
        color: #606266;
        margin: 0 0 15px 0;
      }
      
      .error-description {
        font-size: 16px;
        color: #909399;
        line-height: 1.6;
        margin: 0 0 30px 0;
      }
      
      .error-details {
        margin-bottom: 30px;
        text-align: left;
        
        :deep(.el-alert) {
          .el-alert__content {
            p {
              margin: 5px 0;
              
              &:last-child {
                margin-bottom: 0;
              }
            }
          }
        }
      }
      
      .error-actions {
        display: flex;
        justify-content: center;
        gap: 16px;
        margin-bottom: 40px;
        flex-wrap: wrap;
        
        .el-button {
          padding: 12px 24px;
          font-size: 14px;
        }
      }
      
      .troubleshooting {
        text-align: left;
        margin-bottom: 40px;
        
        .troubleshooting-title {
          font-size: 18px;
          font-weight: 600;
          color: #606266;
          margin: 0 0 20px 0;
          text-align: center;
        }
        
        .troubleshooting-list {
          .troubleshooting-item {
            display: flex;
            align-items: flex-start;
            gap: 16px;
            padding: 16px;
            background: #f8f9fa;
            border-radius: 12px;
            margin-bottom: 12px;
            
            &:last-child {
              margin-bottom: 0;
            }
            
            .item-icon {
              font-size: 24px;
              color: #409eff;
              margin-top: 4px;
              flex-shrink: 0;
            }
            
            .item-content {
              h4 {
                font-size: 16px;
                font-weight: 600;
                color: #606266;
                margin: 0 0 4px 0;
              }
              
              p {
                font-size: 14px;
                color: #909399;
                margin: 0;
                line-height: 1.4;
              }
            }
          }
        }
      }
      
      .system-status {
        text-align: left;
        
        .status-title {
          font-size: 18px;
          font-weight: 600;
          color: #606266;
          margin: 0 0 20px 0;
          text-align: center;
        }
        
        .status-list {
          background: #f8f9fa;
          border-radius: 12px;
          padding: 20px;
          margin-bottom: 16px;
          
          .status-item {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 8px 0;
            border-bottom: 1px solid #e4e7ed;
            
            &:last-child {
              border-bottom: none;
            }
            
            .status-label {
              font-size: 14px;
              color: #606266;
            }
          }
        }
        
        .status-actions {
          display: flex;
          justify-content: center;
          gap: 16px;
        }
      }
    }
  }
  
  .background-decoration {
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    z-index: 1;
    
    .floating-shape {
      position: absolute;
      border-radius: 50%;
      background: rgba(250, 173, 20, 0.1);
      animation: float 6s ease-in-out infinite;
      
      &.shape-1 {
        width: 200px;
        height: 200px;
        top: 10%;
        left: 10%;
        animation-delay: 0s;
      }
      
      &.shape-2 {
        width: 150px;
        height: 150px;
        top: 60%;
        right: 15%;
        animation-delay: 2s;
      }
      
      &.shape-3 {
        width: 100px;
        height: 100px;
        bottom: 20%;
        left: 20%;
        animation-delay: 4s;
      }
    }
  }
}

@keyframes float {
  0%, 100% {
    transform: translateY(0px) rotate(0deg);
  }
  50% {
    transform: translateY(-20px) rotate(180deg);
  }
}

// 响应式设计
@media (max-width: 768px) {
  .error-page {
    padding: 20px;
    
    .error-container {
      padding: 30px 20px;
      
      .error-content {
        .error-title {
          font-size: 48px;
        }
        
        .error-subtitle {
          font-size: 20px;
        }
        
        .error-actions {
          flex-direction: column;
          align-items: center;
          
          .el-button {
            width: 200px;
          }
        }
        
        .troubleshooting {
          .troubleshooting-list {
            .troubleshooting-item {
              flex-direction: column;
              text-align: center;
              
              .item-icon {
                margin-top: 0;
              }
            }
          }
        }
      }
    }
  }
}

// 暗色主题
.dark {
  .error-page {
    background: linear-gradient(135deg, #2c3e50 0%, #34495e 100%);
    
    .error-container {
      background: rgba(44, 62, 80, 0.95);
      
      .error-content {
        .error-subtitle {
          color: #e4e7ed;
        }
        
        .error-description {
          color: #c0c4cc;
        }
        
        .troubleshooting {
          .troubleshooting-title {
            color: #e4e7ed;
          }
          
          .troubleshooting-list {
            .troubleshooting-item {
              background: #3a3a3a;
              
              .item-content {
                h4 {
                  color: #e4e7ed;
                }
                
                p {
                  color: #c0c4cc;
                }
              }
            }
          }
        }
        
        .system-status {
          .status-title {
            color: #e4e7ed;
          }
          
          .status-list {
            background: #3a3a3a;
            
            .status-item {
              border-bottom-color: #4a4a4a;
              
              .status-label {
                color: #e4e7ed;
              }
            }
          }
        }
      }
    }
  }
}
</style>