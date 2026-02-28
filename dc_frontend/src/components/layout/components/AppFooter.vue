<template>
  <div class="app-footer">
    <div class="footer-content">
      <div class="footer-left">
        <div class="copyright">
          <span>© 2025 ACWL AI 数据平台. All rights reserved.</span>
        </div>
        <div class="links">
          <a href="#" class="footer-link">隐私政策</a>
          <span class="separator">|</span>
          <a href="#" class="footer-link">服务条款</a>
          <span class="separator">|</span>
          <a href="#" class="footer-link">帮助中心</a>
        </div>
      </div>

      <div class="footer-right">
        <div class="system-info">
          <span class="info-item">
            <el-icon><Monitor /></el-icon>
            系统版本: v1.0.0
          </span>
          <span class="info-item">
            <el-icon><Connection /></el-icon>
            <span :class="connectionStatus.class">{{
              connectionStatus.text
            }}</span>
          </span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from "vue";

// 连接状态
const isOnline = ref(navigator.onLine);

/**
 * 计算连接状态显示
 */
const connectionStatus = computed(() => {
  return isOnline.value
    ? { text: "已连接", class: "status-online" }
    : { text: "离线", class: "status-offline" };
});

/**
 * 处理网络状态变化
 */
const handleOnline = () => {
  isOnline.value = true;
};

const handleOffline = () => {
  isOnline.value = false;
};

/**
 * 组件挂载时添加事件监听
 */
onMounted(() => {
  window.addEventListener("online", handleOnline);
  window.addEventListener("offline", handleOffline);
});

/**
 * 组件卸载时移除事件监听
 */
onUnmounted(() => {
  window.removeEventListener("online", handleOnline);
  window.removeEventListener("offline", handleOffline);
});
</script>

<style lang="scss" scoped>
.app-footer {
  background: var(--el-bg-color);
  border-top: 1px solid var(--el-border-color-light);
  padding: 12px 20px;

  .footer-content {
    display: flex;
    justify-content: space-between;
    align-items: center;
    max-width: 1200px;
    margin: 0 auto;

    .footer-left {
      display: flex;
      flex-direction: column;
      gap: 4px;

      .copyright {
        font-size: 12px;
        color: var(--el-text-color-secondary);
      }

      .links {
        display: flex;
        align-items: center;
        gap: 8px;

        .footer-link {
          font-size: 12px;
          color: var(--el-text-color-regular);
          text-decoration: none;
          transition: color 0.3s;

          &:hover {
            color: var(--el-color-primary);
          }
        }

        .separator {
          font-size: 12px;
          color: var(--el-text-color-placeholder);
        }
      }
    }

    .footer-right {
      .system-info {
        display: flex;
        align-items: center;
        gap: 16px;

        .info-item {
          display: flex;
          align-items: center;
          font-size: 12px;
          color: var(--el-text-color-regular);

          .el-icon {
            margin-right: 4px;
            font-size: 14px;
          }

          .status-online {
            color: var(--el-color-success);
          }

          .status-offline {
            color: var(--el-color-danger);
          }
        }
      }
    }
  }
}

// 响应式设计
@media (max-width: 768px) {
  .app-footer {
    padding: 12px 16px;

    .footer-content {
      flex-direction: column;
      gap: 8px;
      align-items: flex-start;

      .footer-left {
        width: 100%;

        .links {
          flex-wrap: wrap;
        }
      }

      .footer-right {
        width: 100%;

        .system-info {
          justify-content: flex-start;
          gap: 12px;
        }
      }
    }
  }
}

@media (max-width: 480px) {
  .app-footer {
    .footer-content {
      .footer-right {
        .system-info {
          flex-direction: column;
          align-items: flex-start;
          gap: 4px;
        }
      }
    }
  }
}
</style>
