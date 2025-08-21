<template>
  <div class="app-footer">
    <div class="footer-content">
      <!-- 左侧信息 -->
      <div class="footer-left">
        <span class="copyright">
          © {{ currentYear }} ACWL AI Platform. All rights reserved.
        </span>
      </div>
      
      <!-- 右侧信息 -->
      <div class="footer-right">
        <span class="version">Version {{ version }}</span>
        <el-divider direction="vertical" />
        <span class="build-info">Build {{ buildTime }}</span>
        <el-divider direction="vertical" />
        <el-link
          href="https://github.com/acwl-ai/platform"
          target="_blank"
          type="primary"
          :underline="false"
          class="github-link"
        >
          <el-icon><Link /></el-icon>
          GitHub
        </el-link>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { Link } from '@element-plus/icons-vue'

// 当前年份
const currentYear = computed(() => new Date().getFullYear())

// 版本信息（从环境变量或package.json获取）
const version = computed(() => {
  return import.meta.env.VITE_APP_VERSION || '1.0.0'
})

// 构建时间
const buildTime = computed(() => {
  return import.meta.env.VITE_APP_BUILD_TIME || new Date().toISOString().slice(0, 10)
})
</script>

<style lang="scss" scoped>
.app-footer {
  background: var(--el-bg-color);
  border-top: 1px solid var(--el-border-color-light);
  padding: 0;
  
  .footer-content {
    display: flex;
    align-items: center;
    justify-content: space-between;
    height: 50px;
    padding: 0 20px;
    max-width: 1200px;
    margin: 0 auto;
    
    .footer-left {
      .copyright {
        font-size: 13px;
        color: var(--el-text-color-regular);
      }
    }
    
    .footer-right {
      display: flex;
      align-items: center;
      gap: 8px;
      
      .version,
      .build-info {
        font-size: 12px;
        color: var(--el-text-color-placeholder);
      }
      
      .github-link {
        font-size: 12px;
        display: flex;
        align-items: center;
        gap: 4px;
        
        .el-icon {
          font-size: 14px;
        }
      }
      
      :deep(.el-divider--vertical) {
        height: 12px;
        margin: 0 8px;
        border-color: var(--el-border-color-lighter);
      }
    }
  }
}

// 响应式设计
@media (max-width: 768px) {
  .app-footer {
    .footer-content {
      padding: 0 12px;
      flex-direction: column;
      height: auto;
      padding-top: 12px;
      padding-bottom: 12px;
      gap: 8px;
      
      .footer-right {
        .build-info {
          display: none;
        }
      }
    }
  }
}

@media (max-width: 480px) {
  .app-footer {
    .footer-content {
      .footer-right {
        .version {
          display: none;
        }
        
        :deep(.el-divider--vertical) {
          display: none;
        }
      }
    }
  }
}

// 暗色主题
.dark {
  .app-footer {
    background: var(--el-bg-color);
    border-top-color: var(--el-border-color);
  }
}
</style>