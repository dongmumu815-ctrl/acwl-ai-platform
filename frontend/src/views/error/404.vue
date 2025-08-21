<template>
  <div class="error-page">
    <div class="error-container">
      <!-- 错误图标 -->
      <div class="error-icon">
        <svg viewBox="0 0 1024 1024" class="icon-404">
          <path d="M512 64C264.6 64 64 264.6 64 512s200.6 448 448 448 448-200.6 448-448S759.4 64 512 64zm0 820c-205.4 0-372-166.6-372-372s166.6-372 372-372 372 166.6 372 372-166.6 372-372 372z" fill="#f5f5f5"/>
          <path d="M623.6 316.7C593.6 290.4 554 276 512 276s-81.6 14.4-111.6 40.7C369.2 344 352 380.7 352 420v7.6c0 4.4 3.6 8 8 8h48c4.4 0 8-3.6 8-8V420c0-44.1 43.1-80 96-80s96 35.9 96 80c0 31.1-22 59.6-56.1 72.7-21.2 8.1-39.2 22.3-52.1 40.9-13.1 19-19.8 41.3-19.8 64.9V620c0 4.4 3.6 8 8 8h48c4.4 0 8-3.6 8-8v-22.7a48.3 48.3 0 0 1 30.9-44.8c59-22.7 97.1-74.7 97.1-132.5 0-39.3-17.2-76-48.4-103.3z" fill="#bfbfbf"/>
          <path d="M512 732a40 40 0 1 0 0 80 40 40 0 0 0 0-80z" fill="#bfbfbf"/>
        </svg>
      </div>
      
      <!-- 错误信息 -->
      <div class="error-content">
        <h1 class="error-title">404</h1>
        <h2 class="error-subtitle">页面未找到</h2>
        <p class="error-description">
          抱歉，您访问的页面不存在或已被移除。
          <br>
          请检查URL是否正确，或返回首页继续浏览。
        </p>
        
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
        </div>
        
        <!-- 搜索框 -->
        <div class="search-section">
          <p class="search-tip">或者尝试搜索您需要的内容：</p>
          <el-input
            v-model="searchKeyword"
            placeholder="搜索模型、部署、数据集..."
            class="search-input"
            @keyup.enter="handleSearch"
          >
            <template #append>
              <el-button @click="handleSearch">
                <el-icon><Search /></el-icon>
              </el-button>
            </template>
          </el-input>
        </div>
        
        <!-- 快速链接 -->
        <div class="quick-links">
          <p class="links-title">您可能想要访问：</p>
          <div class="links-grid">
            <router-link to="/dashboard" class="quick-link">
              <el-icon><Monitor /></el-icon>
              <span>仪表板</span>
            </router-link>
            <router-link to="/models" class="quick-link">
              <el-icon><Box /></el-icon>
              <span>模型管理</span>
            </router-link>
            <router-link to="/deployments" class="quick-link">
              <el-icon><VideoPlay /></el-icon>
              <span>部署管理</span>
            </router-link>
            <router-link to="/datasets" class="quick-link">
              <el-icon><FolderOpened /></el-icon>
              <span>数据集</span>
            </router-link>
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
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import {
  HomeFilled,
  ArrowLeft,
  Search,
  Monitor,
  Box,
  VideoPlay,
  FolderOpened
} from '@element-plus/icons-vue'

const router = useRouter()
const searchKeyword = ref('')

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

// 处理搜索
const handleSearch = () => {
  if (!searchKeyword.value.trim()) {
    ElMessage.warning('请输入搜索关键词')
    return
  }
  
  // 这里应该跳转到搜索页面或执行搜索逻辑
  ElMessage.info(`搜索功能开发中: ${searchKeyword.value}`)
  searchKeyword.value = ''
}
</script>

<style lang="scss" scoped>
.error-page {
  position: relative;
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
  overflow: hidden;
  
  .error-container {
    position: relative;
    z-index: 2;
    text-align: center;
    max-width: 600px;
    padding: 40px;
    background: rgba(255, 255, 255, 0.95);
    backdrop-filter: blur(10px);
    border-radius: 20px;
    box-shadow: 0 20px 40px rgba(0, 0, 0, 0.1);
    
    .error-icon {
      margin-bottom: 30px;
      
      .icon-404 {
        width: 120px;
        height: 120px;
        opacity: 0.8;
      }
    }
    
    .error-content {
      .error-title {
        font-size: 72px;
        font-weight: 700;
        color: #409eff;
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
      
      .error-actions {
        display: flex;
        justify-content: center;
        gap: 16px;
        margin-bottom: 40px;
        
        .el-button {
          padding: 12px 24px;
          font-size: 14px;
        }
      }
      
      .search-section {
        margin-bottom: 40px;
        
        .search-tip {
          font-size: 14px;
          color: #909399;
          margin: 0 0 16px 0;
        }
        
        .search-input {
          max-width: 400px;
          
          :deep(.el-input-group__append) {
            padding: 0;
            
            .el-button {
              border: none;
              padding: 0 15px;
            }
          }
        }
      }
      
      .quick-links {
        .links-title {
          font-size: 14px;
          color: #909399;
          margin: 0 0 20px 0;
        }
        
        .links-grid {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
          gap: 16px;
          
          .quick-link {
            display: flex;
            flex-direction: column;
            align-items: center;
            gap: 8px;
            padding: 20px 16px;
            background: #f8f9fa;
            border-radius: 12px;
            text-decoration: none;
            color: #606266;
            transition: all 0.3s ease;
            
            &:hover {
              background: #409eff;
              color: white;
              transform: translateY(-2px);
              box-shadow: 0 8px 20px rgba(64, 158, 255, 0.3);
            }
            
            .el-icon {
              font-size: 24px;
            }
            
            span {
              font-size: 14px;
              font-weight: 500;
            }
          }
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
      background: rgba(64, 158, 255, 0.1);
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
        
        .quick-links {
          .links-grid {
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
        .quick-links {
          .links-grid {
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
        
        .search-section {
          .search-tip {
            color: #c0c4cc;
          }
        }
        
        .quick-links {
          .links-title {
            color: #c0c4cc;
          }
          
          .quick-link {
            background: #3a3a3a;
            color: #e4e7ed;
            
            &:hover {
              background: #409eff;
              color: white;
            }
          }
        }
      }
    }
  }
}
</style>