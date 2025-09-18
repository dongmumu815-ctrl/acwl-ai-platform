<template>
  <div class="error-container">
    <div class="error-content">
      <!-- 404图标 -->
      <div class="error-icon">
        <svg viewBox="0 0 200 200" class="error-svg">
          <circle cx="100" cy="100" r="80" fill="none" stroke="#e6f7ff" stroke-width="2"/>
          <text x="100" y="110" text-anchor="middle" class="error-number">404</text>
        </svg>
      </div>
      
      <!-- 错误信息 -->
      <div class="error-info">
        <h1 class="error-title">页面不存在</h1>
        <p class="error-description">
          抱歉，您访问的页面不存在或已被移除。
        </p>
        <p class="error-suggestion">
          请检查URL是否正确，或返回首页继续浏览。
        </p>
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
        <el-button @click="refresh">
          <el-icon><Refresh /></el-icon>
          刷新页面
        </el-button>
      </div>
      
      <!-- 建议链接 -->
      <div class="error-links">
        <h3>您可能想要访问：</h3>
        <div class="link-grid">
          <router-link to="/dashboard" class="suggestion-link">
            <el-icon><Monitor /></el-icon>
            <span>仪表盘</span>
          </router-link>
          <router-link to="/data-resources/list" class="suggestion-link">
            <el-icon><FolderOpened /></el-icon>
            <span>数据资源</span>
          </router-link>
          <router-link to="/users/list" class="suggestion-link">
            <el-icon><User /></el-icon>
            <span>用户管理</span>
          </router-link>
          <router-link to="/system/settings" class="suggestion-link">
            <el-icon><Setting /></el-icon>
            <span>系统设置</span>
          </router-link>
        </div>
      </div>
    </div>
    
    <!-- 背景装饰 -->
    <div class="error-background">
      <div class="floating-shape shape-1"></div>
      <div class="floating-shape shape-2"></div>
      <div class="floating-shape shape-3"></div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { HomeFilled, ArrowLeft, Refresh, Monitor, FolderOpened, User, Setting } from '@element-plus/icons-vue'

const router = useRouter()

/**
 * 返回首页
 */
const goHome = () => {
  router.push('/')
  ElMessage.success('已返回首页')
}

/**
 * 返回上一页
 */
const goBack = () => {
  if (window.history.length > 1) {
    router.go(-1)
  } else {
    router.push('/')
    ElMessage.info('没有上一页，已返回首页')
  }
}

/**
 * 刷新当前页面
 */
const refresh = () => {
  window.location.reload()
}
</script>

<style lang="scss" scoped>
.error-container {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  position: relative;
  overflow: hidden;
  padding: 20px;
}

.error-content {
  text-align: center;
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(10px);
  border-radius: 20px;
  padding: 60px 40px;
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.1);
  max-width: 600px;
  width: 100%;
  position: relative;
  z-index: 2;
}

.error-icon {
  margin-bottom: 30px;
  
  .error-svg {
    width: 150px;
    height: 150px;
    
    .error-number {
      font-size: 36px;
      font-weight: bold;
      fill: #667eea;
    }
  }
}

.error-info {
  margin-bottom: 40px;
  
  .error-title {
    font-size: 32px;
    font-weight: 600;
    color: #2c3e50;
    margin: 0 0 16px 0;
  }
  
  .error-description {
    font-size: 16px;
    color: #5a6c7d;
    margin: 0 0 12px 0;
    line-height: 1.6;
  }
  
  .error-suggestion {
    font-size: 14px;
    color: #8492a6;
    margin: 0;
    line-height: 1.5;
  }
}

.error-actions {
  display: flex;
  gap: 16px;
  justify-content: center;
  margin-bottom: 40px;
  flex-wrap: wrap;
  
  .el-button {
    border-radius: 8px;
    padding: 12px 24px;
    font-weight: 500;
    
    .el-icon {
      margin-right: 6px;
    }
  }
}

.error-links {
  h3 {
    font-size: 18px;
    color: #2c3e50;
    margin: 0 0 20px 0;
    font-weight: 600;
  }
  
  .link-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
    gap: 16px;
    
    .suggestion-link {
      display: flex;
      flex-direction: column;
      align-items: center;
      padding: 20px 16px;
      background: #f8fafc;
      border-radius: 12px;
      text-decoration: none;
      color: #5a6c7d;
      transition: all 0.3s ease;
      border: 2px solid transparent;
      
      &:hover {
        background: #e6f7ff;
        border-color: #667eea;
        color: #667eea;
        transform: translateY(-2px);
      }
      
      .el-icon {
        font-size: 24px;
        margin-bottom: 8px;
      }
      
      span {
        font-size: 14px;
        font-weight: 500;
      }
    }
  }
}

.error-background {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  z-index: 1;
  
  .floating-shape {
    position: absolute;
    border-radius: 50%;
    background: rgba(255, 255, 255, 0.1);
    animation: float 6s ease-in-out infinite;
    
    &.shape-1 {
      width: 80px;
      height: 80px;
      top: 20%;
      left: 10%;
      animation-delay: 0s;
    }
    
    &.shape-2 {
      width: 120px;
      height: 120px;
      top: 60%;
      right: 15%;
      animation-delay: 2s;
    }
    
    &.shape-3 {
      width: 60px;
      height: 60px;
      bottom: 20%;
      left: 20%;
      animation-delay: 4s;
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
  .error-container {
    padding: 16px;
  }
  
  .error-content {
    padding: 40px 24px;
  }
  
  .error-icon .error-svg {
    width: 120px;
    height: 120px;
    
    .error-number {
      font-size: 28px;
    }
  }
  
  .error-info .error-title {
    font-size: 24px;
  }
  
  .error-actions {
    flex-direction: column;
    align-items: center;
    
    .el-button {
      width: 100%;
      max-width: 200px;
    }
  }
  
  .error-links .link-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 480px) {
  .error-links .link-grid {
    grid-template-columns: 1fr;
  }
}
</style>