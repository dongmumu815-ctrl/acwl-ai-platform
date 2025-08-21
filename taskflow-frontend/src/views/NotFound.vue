<template>
  <div class="not-found-container">
    <div class="not-found-content">
      <div class="error-illustration">
        <div class="error-code">404</div>
        <div class="error-icon">
          <el-icon :size="120" color="#E6A23C">
            <WarningFilled />
          </el-icon>
        </div>
      </div>
      
      <div class="error-info">
        <h1 class="error-title">页面不存在</h1>
        <p class="error-description">
          抱歉，您访问的页面不存在或已被移除。
        </p>
        <p class="error-suggestion">
          请检查URL是否正确，或者返回首页继续浏览。
        </p>
      </div>
      
      <div class="error-actions">
        <el-button type="primary" size="large" @click="goHome">
          <el-icon><HomeFilled /></el-icon>
          返回首页
        </el-button>
        <el-button size="large" @click="goBack">
          <el-icon><ArrowLeft /></el-icon>
          返回上页
        </el-button>
      </div>
      
      <div class="quick-links">
        <h3>快速导航</h3>
        <div class="links-grid">
          <el-card 
            v-for="link in quickLinks" 
            :key="link.path"
            class="link-card"
            shadow="hover"
            @click="navigateTo(link.path)"
          >
            <div class="link-content">
              <el-icon :size="24" :color="link.color">
                <component :is="link.icon" />
              </el-icon>
              <span class="link-title">{{ link.title }}</span>
            </div>
          </el-card>
        </div>
      </div>
    </div>
    
    <!-- 背景装饰 -->
    <div class="background-decoration">
      <div class="floating-shape shape-1"></div>
      <div class="floating-shape shape-2"></div>
      <div class="floating-shape shape-3"></div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import {
  WarningFilled,
  HomeFilled,
  ArrowLeft,
  Operation,
  Document,
  FolderOpened,
  Monitor,
  Setting
} from '@element-plus/icons-vue'

const router = useRouter()

// 快速导航链接
const quickLinks = ref([
  {
    title: '工作流管理',
    path: '/workflows',
    icon: 'Operation',
    color: '#409EFF'
  },
  {
    title: '任务管理',
    path: '/tasks',
    icon: 'Document',
    color: '#67C23A'
  },
  {
    title: '项目管理',
    path: '/projects',
    icon: 'FolderOpened',
    color: '#E6A23C'
  },
  {
    title: '实时监控',
    path: '/monitoring',
    icon: 'Monitor',
    color: '#F56C6C'
  },
  {
    title: '系统设置',
    path: '/settings',
    icon: 'Setting',
    color: '#909399'
  }
])

/**
 * 返回首页
 */
const goHome = () => {
  router.push('/')
}

/**
 * 返回上一页
 */
const goBack = () => {
  if (window.history.length > 1) {
    router.go(-1)
  } else {
    router.push('/')
  }
}

/**
 * 导航到指定路径
 * @param {string} path - 目标路径
 */
const navigateTo = (path) => {
  router.push(path)
}
</script>

<style scoped>
.not-found-container {
  position: relative;
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
  overflow: hidden;
}

.not-found-content {
  position: relative;
  text-align: center;
  max-width: 800px;
  padding: 40px;
  z-index: 1;
}

.error-illustration {
  position: relative;
  margin-bottom: 40px;
}

.error-code {
  font-size: 120px;
  font-weight: bold;
  color: #E6A23C;
  text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.1);
  margin-bottom: 20px;
  animation: bounce 2s infinite;
}

@keyframes bounce {
  0%, 20%, 50%, 80%, 100% {
    transform: translateY(0);
  }
  40% {
    transform: translateY(-10px);
  }
  60% {
    transform: translateY(-5px);
  }
}

.error-icon {
  margin-bottom: 20px;
}

.error-info {
  margin-bottom: 40px;
}

.error-title {
  font-size: 32px;
  font-weight: bold;
  color: #2c3e50;
  margin: 0 0 16px 0;
}

.error-description {
  font-size: 18px;
  color: #7f8c8d;
  margin: 0 0 12px 0;
  line-height: 1.6;
}

.error-suggestion {
  font-size: 16px;
  color: #95a5a6;
  margin: 0;
  line-height: 1.6;
}

.error-actions {
  display: flex;
  gap: 16px;
  justify-content: center;
  margin-bottom: 60px;
  flex-wrap: wrap;
}

.quick-links {
  margin-top: 40px;
}

.quick-links h3 {
  font-size: 20px;
  color: #2c3e50;
  margin: 0 0 24px 0;
}

.links-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: 16px;
  max-width: 600px;
  margin: 0 auto;
}

.link-card {
  cursor: pointer;
  transition: all 0.3s ease;
  border-radius: 12px;
}

.link-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 25px rgba(0, 0, 0, 0.15);
}

.link-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  padding: 16px;
}

.link-title {
  font-size: 14px;
  font-weight: 500;
  color: #2c3e50;
}

.background-decoration {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  pointer-events: none;
  overflow: hidden;
}

.floating-shape {
  position: absolute;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.1);
  animation: float 6s ease-in-out infinite;
}

.shape-1 {
  width: 80px;
  height: 80px;
  top: 20%;
  left: 10%;
  animation-delay: 0s;
}

.shape-2 {
  width: 120px;
  height: 120px;
  top: 60%;
  right: 15%;
  animation-delay: 2s;
}

.shape-3 {
  width: 60px;
  height: 60px;
  bottom: 20%;
  left: 20%;
  animation-delay: 4s;
}

@keyframes float {
  0%, 100% {
    transform: translateY(0px) rotate(0deg);
  }
  50% {
    transform: translateY(-20px) rotate(180deg);
  }
}

/* 响应式设计 */
@media (max-width: 768px) {
  .not-found-content {
    padding: 20px;
  }
  
  .error-code {
    font-size: 80px;
  }
  
  .error-title {
    font-size: 24px;
  }
  
  .error-description {
    font-size: 16px;
  }
  
  .error-actions {
    flex-direction: column;
    align-items: center;
  }
  
  .links-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 480px) {
  .error-code {
    font-size: 60px;
  }
  
  .error-title {
    font-size: 20px;
  }
  
  .links-grid {
    grid-template-columns: 1fr;
  }
}
</style>