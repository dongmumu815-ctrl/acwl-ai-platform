<template>
  <div class="error-page">
    <div class="error-container">
      <!-- 错误图标 -->
      <div class="error-icon">
        <svg viewBox="0 0 1024 1024" class="icon-403">
          <path d="M512 64C264.6 64 64 264.6 64 512s200.6 448 448 448 448-200.6 448-448S759.4 64 512 64zm0 820c-205.4 0-372-166.6-372-372s166.6-372 372-372 372 166.6 372 372-166.6 372-372 372z" fill="#ff4d4f"/>
          <path d="M685.4 354.8c0-4.4-3.6-8-8-8l-66 .3L512 465.6l-99.3-118.4-66-.3c-4.4 0-8 3.5-8 8 0 1.9.7 3.7 1.9 5.2l130.1 155L340.5 670a8.32 8.32 0 0 0 6.4 13.6l66-.3L512 564.4l99.3 118.9 66 .3c4.4 0 8-3.5 8-8 0-1.9-.7-3.7-1.9-5.2L553.5 515l130.1-155c1.2-1.4 1.8-3.3 1.8-5.2z" fill="white"/>
        </svg>
      </div>
      
      <!-- 错误信息 -->
      <div class="error-content">
        <h1 class="error-title">403</h1>
        <h2 class="error-subtitle">访问被拒绝</h2>
        <p class="error-description">
          抱歉，您没有权限访问此页面。
          <br>
          请联系管理员获取相应权限，或返回您有权限访问的页面。
        </p>
        
        <!-- 权限信息 -->
        <div class="permission-info">
          <el-alert
            title="权限不足"
            type="warning"
            :closable="false"
            show-icon
          >
            <template #default>
              <p>当前用户角色：<el-tag size="small">{{ userStore.userInfo?.role || '普通用户' }}</el-tag></p>
              <p>所需权限：<el-tag type="danger" size="small">管理员权限</el-tag></p>
            </template>
          </el-alert>
        </div>
        
        <!-- 操作按钮 -->
        <div class="error-actions">
          <el-button type="primary" @click="goHome">
            <el-icon><HomeFilled /></el-icon>
            返回首页
          </el-button>
          <el-button @click="goBack">
            <el-icon><ArrowLeft /></el-icon>
            返回上页
          </el-button>
          <el-button type="warning" @click="contactAdmin">
            <el-icon><Message /></el-icon>
            联系管理员
          </el-button>
        </div>
        
        <!-- 可访问的功能 -->
        <div class="accessible-features">
          <p class="features-title">您可以访问以下功能：</p>
          <div class="features-grid">
            <div class="feature-item" @click="$router.push('/dashboard')">
              <el-icon><Monitor /></el-icon>
              <span>仪表板</span>
            </div>
            <div class="feature-item" @click="$router.push('/models')">
              <el-icon><Box /></el-icon>
              <span>我的模型</span>
            </div>
            <div class="feature-item" @click="$router.push('/deployments')">
              <el-icon><VideoPlay /></el-icon>
              <span>我的部署</span>
            </div>
            <div class="feature-item" @click="$router.push('/profile')">
              <el-icon><User /></el-icon>
              <span>个人中心</span>
            </div>
          </div>
        </div>
        
        <!-- 权限申请 -->
        <div class="permission-request">
          <p class="request-title">需要更多权限？</p>
          <el-button type="info" plain @click="showRequestDialog">
            <el-icon><EditPen /></el-icon>
            申请权限
          </el-button>
        </div>
      </div>
    </div>
    
    <!-- 背景装饰 -->
    <div class="background-decoration">
      <div class="floating-shape shape-1"></div>
      <div class="floating-shape shape-2"></div>
      <div class="floating-shape shape-3"></div>
    </div>
    
    <!-- 权限申请对话框 -->
    <el-dialog
      v-model="requestDialogVisible"
      title="权限申请"
      width="500px"
      :before-close="handleCloseRequest"
    >
      <el-form
        ref="requestFormRef"
        :model="requestForm"
        :rules="requestRules"
        label-width="80px"
      >
        <el-form-item label="申请权限" prop="permission">
          <el-select
            v-model="requestForm.permission"
            placeholder="请选择需要申请的权限"
            style="width: 100%"
          >
            <el-option label="管理员权限" value="admin" />
            <el-option label="模型管理权限" value="model_manager" />
            <el-option label="部署管理权限" value="deployment_manager" />
            <el-option label="用户管理权限" value="user_manager" />
          </el-select>
        </el-form-item>
        
        <el-form-item label="申请理由" prop="reason">
          <el-input
            v-model="requestForm.reason"
            type="textarea"
            :rows="4"
            placeholder="请详细说明申请权限的理由..."
            maxlength="500"
            show-word-limit
          />
        </el-form-item>
      </el-form>
      
      <template #footer>
        <div class="dialog-footer">
          <el-button @click="requestDialogVisible = false">取消</el-button>
          <el-button type="primary" @click="submitRequest" :loading="submitting">
            提交申请
          </el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox, type FormInstance, type FormRules } from 'element-plus'
import {
  HomeFilled,
  ArrowLeft,
  Message,
  Monitor,
  Box,
  VideoPlay,
  User,
  EditPen
} from '@element-plus/icons-vue'
import { useUserStore } from '@/stores/user'

const router = useRouter()
const userStore = useUserStore()

const requestDialogVisible = ref(false)
const requestFormRef = ref<FormInstance>()
const submitting = ref(false)

// 权限申请表单
const requestForm = reactive({
  permission: '',
  reason: ''
})

// 表单验证规则
const requestRules: FormRules = {
  permission: [
    { required: true, message: '请选择需要申请的权限', trigger: 'change' }
  ],
  reason: [
    { required: true, message: '请填写申请理由', trigger: 'blur' },
    { min: 10, message: '申请理由至少10个字符', trigger: 'blur' }
  ]
}

// 返回首页
const goHome = () => {
  router.push('/dashboard')
}

// 返回上一页
const goBack = () => {
  if (window.history.length > 1) {
    router.go(-1)
  } else {
    router.push('/dashboard')
  }
}

// 联系管理员
const contactAdmin = () => {
  ElMessageBox.alert(
    '请通过以下方式联系管理员：\n\n' +
    '邮箱：admin@acwl-ai.com\n' +
    '电话：400-123-4567\n' +
    '工作时间：周一至周五 9:00-18:00',
    '联系管理员',
    {
      confirmButtonText: '知道了',
      type: 'info'
    }
  )
}

// 显示权限申请对话框
const showRequestDialog = () => {
  requestDialogVisible.value = true
}

// 关闭权限申请对话框
const handleCloseRequest = () => {
  requestForm.permission = ''
  requestForm.reason = ''
  requestDialogVisible.value = false
}

// 提交权限申请
const submitRequest = async () => {
  if (!requestFormRef.value) return
  
  try {
    await requestFormRef.value.validate()
    submitting.value = true
    
    // 这里应该调用实际的API
    // await permissionApi.requestPermission(requestForm)
    
    // 模拟提交
    await new Promise(resolve => setTimeout(resolve, 1000))
    
    ElMessage.success('权限申请已提交，请等待管理员审核')
    handleCloseRequest()
  } catch (error: any) {
    console.error('提交权限申请失败:', error)
    ElMessage.error('提交失败，请稍后重试')
  } finally {
    submitting.value = false
  }
}
</script>

<style lang="scss" scoped>
.error-page {
  position: relative;
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #ff9a9e 0%, #fecfef 50%, #fecfef 100%);
  overflow: hidden;
  
  .error-container {
    position: relative;
    z-index: 2;
    text-align: center;
    max-width: 700px;
    padding: 40px;
    background: rgba(255, 255, 255, 0.95);
    backdrop-filter: blur(10px);
    border-radius: 20px;
    box-shadow: 0 20px 40px rgba(0, 0, 0, 0.1);
    
    .error-icon {
      margin-bottom: 30px;
      
      .icon-403 {
        width: 120px;
        height: 120px;
        opacity: 0.9;
      }
    }
    
    .error-content {
      .error-title {
        font-size: 72px;
        font-weight: 700;
        color: #ff4d4f;
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
      
      .permission-info {
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
      
      .accessible-features {
        margin-bottom: 40px;
        
        .features-title {
          font-size: 16px;
          font-weight: 500;
          color: #606266;
          margin: 0 0 20px 0;
        }
        
        .features-grid {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
          gap: 16px;
          
          .feature-item {
            display: flex;
            flex-direction: column;
            align-items: center;
            gap: 8px;
            padding: 20px 16px;
            background: #f0f9ff;
            border: 2px solid #e1f5fe;
            border-radius: 12px;
            cursor: pointer;
            transition: all 0.3s ease;
            
            &:hover {
              background: #409eff;
              border-color: #409eff;
              color: white;
              transform: translateY(-2px);
              box-shadow: 0 8px 20px rgba(64, 158, 255, 0.3);
            }
            
            .el-icon {
              font-size: 24px;
              color: #409eff;
            }
            
            &:hover .el-icon {
              color: white;
            }
            
            span {
              font-size: 14px;
              font-weight: 500;
              color: #606266;
            }
            
            &:hover span {
              color: white;
            }
          }
        }
      }
      
      .permission-request {
        .request-title {
          font-size: 14px;
          color: #909399;
          margin: 0 0 16px 0;
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
      background: rgba(255, 77, 79, 0.1);
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
        
        .accessible-features {
          .features-grid {
            grid-template-columns: repeat(2, 1fr);
          }
        }
      }
    }
  }
}

@media (max-width: 480px) {
  .error-page {
    .error-container {
      .error-content {
        .accessible-features {
          .features-grid {
            grid-template-columns: 1fr;
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
        
        .accessible-features {
          .features-title {
            color: #e4e7ed;
          }
          
          .feature-item {
            background: #3a3a3a;
            border-color: #4a4a4a;
            
            .el-icon {
              color: #409eff;
            }
            
            span {
              color: #e4e7ed;
            }
            
            &:hover {
              background: #409eff;
              border-color: #409eff;
              
              .el-icon,
              span {
                color: white;
              }
            }
          }
        }
        
        .permission-request {
          .request-title {
            color: #c0c4cc;
          }
        }
      }
    }
  }
}
</style>