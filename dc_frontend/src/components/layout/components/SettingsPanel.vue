<template>
  <div class="settings-panel">
    <el-drawer
      v-model="visible"
      title="系统设置"
      direction="rtl"
      size="350px"
      :before-close="handleClose"
    >
      <div class="settings-content">
        <!-- 主题设置 -->
        <div class="setting-section">
          <h3 class="section-title">
            <el-icon><Sunny /></el-icon>
            主题设置
          </h3>
          
          <div class="setting-item">
            <label class="setting-label">主题模式</label>
            <el-radio-group v-model="settings.theme" @change="handleThemeChange">
              <el-radio label="light">浅色</el-radio>
              <el-radio label="dark">深色</el-radio>
              <el-radio label="auto">跟随系统</el-radio>
            </el-radio-group>
          </div>
          
          <div class="setting-item">
            <label class="setting-label">主题色</label>
            <div class="color-picker-group">
              <div
                v-for="color in themeColors"
                :key="color.name"
                class="color-item"
                :class="{ active: settings.primaryColor === color.value }"
                :style="{ backgroundColor: color.value }"
                @click="handleColorChange(color.value)"
              >
                <el-icon v-if="settings.primaryColor === color.value"><Check /></el-icon>
              </div>
            </div>
          </div>
        </div>

        <!-- 布局设置 -->
        <div class="setting-section">
          <h3 class="section-title">
            <el-icon><Grid /></el-icon>
            布局设置
          </h3>
          
          <div class="setting-item">
            <div class="setting-row">
              <label class="setting-label">侧边栏折叠</label>
              <el-switch
                v-model="settings.sidebarCollapsed"
                @change="handleSidebarChange"
              />
            </div>
          </div>
          
          <div class="setting-item">
            <div class="setting-row">
              <label class="setting-label">固定头部</label>
              <el-switch
                v-model="settings.fixedHeader"
                @change="handleHeaderChange"
              />
            </div>
          </div>
          
          <div class="setting-item">
            <div class="setting-row">
              <label class="setting-label">显示面包屑</label>
              <el-switch
                v-model="settings.showBreadcrumb"
                @change="handleBreadcrumbChange"
              />
            </div>
          </div>
        </div>

        <!-- 功能设置 -->
        <div class="setting-section">
          <h3 class="section-title">
            <el-icon><Setting /></el-icon>
            功能设置
          </h3>
          
          <div class="setting-item">
            <div class="setting-row">
              <label class="setting-label">页面缓存</label>
              <el-switch
                v-model="settings.pageCache"
                @change="handleCacheChange"
              />
            </div>
          </div>
          
          <div class="setting-item">
            <div class="setting-row">
              <label class="setting-label">页面动画</label>
              <el-switch
                v-model="settings.pageAnimation"
                @change="handleAnimationChange"
              />
            </div>
          </div>
          
          <div class="setting-item">
            <label class="setting-label">语言设置</label>
            <el-select v-model="settings.language" @change="handleLanguageChange">
              <el-option label="简体中文" value="zh-CN" />
              <el-option label="English" value="en-US" />
            </el-select>
          </div>
        </div>

        <!-- 操作按钮 -->
        <div class="setting-actions">
          <el-button @click="resetSettings">重置设置</el-button>
          <el-button type="primary" @click="saveSettings">保存设置</el-button>
        </div>
      </div>
    </el-drawer>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, watch } from 'vue'
import { ElMessage } from 'element-plus'

// Props
interface Props {
  modelValue: boolean
}

const props = withDefaults(defineProps<Props>(), {
  modelValue: false
})

// Emits
const emit = defineEmits<{
  'update:modelValue': [value: boolean]
  'settings-change': [settings: any]
}>()

// 响应式数据
const visible = ref(props.modelValue)

// 设置数据
const settings = reactive({
  theme: 'light',
  primaryColor: '#409EFF',
  sidebarCollapsed: false,
  fixedHeader: true,
  showBreadcrumb: true,
  pageCache: true,
  pageAnimation: true,
  language: 'zh-CN'
})

// 主题色选项
const themeColors = [
  { name: '默认蓝', value: '#409EFF' },
  { name: '成功绿', value: '#67C23A' },
  { name: '警告橙', value: '#E6A23C' },
  { name: '危险红', value: '#F56C6C' },
  { name: '信息灰', value: '#909399' },
  { name: '紫色', value: '#722ED1' },
  { name: '青色', value: '#13C2C2' },
  { name: '粉色', value: '#EB2F96' }
]

/**
 * 监听visible变化
 */
watch(
  () => props.modelValue,
  (newVal) => {
    visible.value = newVal
  }
)

watch(
  visible,
  (newVal) => {
    emit('update:modelValue', newVal)
  }
)

/**
 * 处理关闭事件
 */
const handleClose = () => {
  visible.value = false
}

/**
 * 处理主题变化
 */
const handleThemeChange = (theme: string) => {
  // 应用主题
  document.documentElement.setAttribute('data-theme', theme)
  emitSettingsChange()
}

/**
 * 处理颜色变化
 */
const handleColorChange = (color: string) => {
  settings.primaryColor = color
  // 应用主题色
  document.documentElement.style.setProperty('--el-color-primary', color)
  emitSettingsChange()
}

/**
 * 处理侧边栏变化
 */
const handleSidebarChange = () => {
  emitSettingsChange()
}

/**
 * 处理头部固定变化
 */
const handleHeaderChange = () => {
  emitSettingsChange()
}

/**
 * 处理面包屑显示变化
 */
const handleBreadcrumbChange = () => {
  emitSettingsChange()
}

/**
 * 处理缓存变化
 */
const handleCacheChange = () => {
  emitSettingsChange()
}

/**
 * 处理动画变化
 */
const handleAnimationChange = () => {
  emitSettingsChange()
}

/**
 * 处理语言变化
 */
const handleLanguageChange = () => {
  emitSettingsChange()
}

/**
 * 发送设置变化事件
 */
const emitSettingsChange = () => {
  emit('settings-change', { ...settings })
}

/**
 * 重置设置
 */
const resetSettings = () => {
  Object.assign(settings, {
    theme: 'light',
    primaryColor: '#409EFF',
    sidebarCollapsed: false,
    fixedHeader: true,
    showBreadcrumb: true,
    pageCache: true,
    pageAnimation: true,
    language: 'zh-CN'
  })
  
  // 应用重置后的设置
  document.documentElement.setAttribute('data-theme', settings.theme)
  document.documentElement.style.setProperty('--el-color-primary', settings.primaryColor)
  
  emitSettingsChange()
  ElMessage.success('设置已重置')
}

/**
 * 保存设置
 */
const saveSettings = () => {
  // 保存到本地存储
  localStorage.setItem('app-settings', JSON.stringify(settings))
  ElMessage.success('设置已保存')
}

/**
 * 加载设置
 */
const loadSettings = () => {
  try {
    const savedSettings = localStorage.getItem('app-settings')
    if (savedSettings) {
      const parsed = JSON.parse(savedSettings)
      Object.assign(settings, parsed)
      
      // 应用加载的设置
      document.documentElement.setAttribute('data-theme', settings.theme)
      document.documentElement.style.setProperty('--el-color-primary', settings.primaryColor)
    }
  } catch (error) {
    console.error('加载设置失败:', error)
  }
}

// 组件挂载时加载设置
loadSettings()
</script>

<style lang="scss" scoped>
.settings-content {
  padding: 0 4px;
}

.setting-section {
  margin-bottom: 32px;
  
  .section-title {
    display: flex;
    align-items: center;
    font-size: 16px;
    font-weight: 600;
    color: var(--el-text-color-primary);
    margin: 0 0 16px 0;
    
    .el-icon {
      margin-right: 8px;
      color: var(--el-color-primary);
    }
  }
}

.setting-item {
  margin-bottom: 16px;
  
  .setting-label {
    display: block;
    font-size: 14px;
    color: var(--el-text-color-regular);
    margin-bottom: 8px;
  }
  
  .setting-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    
    .setting-label {
      margin-bottom: 0;
    }
  }
}

.color-picker-group {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 8px;
  
  .color-item {
    width: 32px;
    height: 32px;
    border-radius: 6px;
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: center;
    transition: all 0.3s;
    border: 2px solid transparent;
    
    &:hover {
      transform: scale(1.1);
    }
    
    &.active {
      border-color: var(--el-color-primary);
      box-shadow: 0 0 0 2px rgba(64, 158, 255, 0.2);
      
      .el-icon {
        color: white;
        font-size: 16px;
      }
    }
  }
}

.setting-actions {
  display: flex;
  gap: 12px;
  padding-top: 20px;
  border-top: 1px solid var(--el-border-color-light);
  
  .el-button {
    flex: 1;
  }
}

// 深色主题适配
:deep(.el-drawer__header) {
  border-bottom: 1px solid var(--el-border-color-light);
  padding: 20px 20px 16px;
  margin-bottom: 0;
}

:deep(.el-drawer__body) {
  padding: 20px;
}
</style>