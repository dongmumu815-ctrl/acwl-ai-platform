<template>
  <!-- Robot图标SVG组件 -->
  <svg
    viewBox="0 0 1024 1024"
    xmlns="http://www.w3.org/2000/svg"
    :width="size"
    :height="size"
    :style="{ color: color }"
  >
    <!-- 机器人头部 -->
    <path
      d="M512 128c106.039 0 192 85.961 192 192v64h64c35.346 0 64 28.654 64 64v320c0 35.346-28.654 64-64 64H256c-35.346 0-64-28.654-64-64V448c0-35.346 28.654-64 64-64h64v-64c0-106.039 85.961-192 192-192z"
      fill="currentColor"
    />
    <!-- 机器人眼睛 -->
    <circle cx="448" cy="288" r="24" fill="#fff" />
    <circle cx="576" cy="288" r="24" fill="#fff" />
    <!-- 机器人嘴巴 -->
    <rect x="480" y="336" width="64" height="16" rx="8" fill="#fff" />
    <!-- 机器人天线 -->
    <line x1="512" y1="128" x2="512" y2="80" stroke="currentColor" stroke-width="8" stroke-linecap="round" />
    <circle cx="512" cy="72" r="8" fill="currentColor" />
    <!-- 机器人身体装饰线条 -->
    <rect x="320" y="480" width="384" height="8" rx="4" fill="#fff" opacity="0.6" />
    <rect x="320" y="520" width="384" height="8" rx="4" fill="#fff" opacity="0.6" />
    <rect x="320" y="560" width="384" height="8" rx="4" fill="#fff" opacity="0.6" />
    <!-- 机器人手臂 -->
    <rect x="192" y="480" width="48" height="128" rx="24" fill="currentColor" />
    <rect x="784" y="480" width="48" height="128" rx="24" fill="currentColor" />
    <!-- 机器人腿部 -->
    <rect x="400" y="832" width="48" height="128" rx="24" fill="currentColor" />
    <rect x="576" y="832" width="48" height="128" rx="24" fill="currentColor" />
  </svg>
</template>

<script setup lang="ts">
/**
 * Robot图标组件
 * 用于智能体管理菜单的图标显示
 */
interface Props {
  size?: string | number
  color?: string
}

// 定义组件属性，设置默认值
withDefaults(defineProps<Props>(), {
  size: '1em',
  color: 'currentColor'
})
</script>

<style scoped>
/* 确保SVG图标能够正确继承父元素的颜色和大小 */
svg {
  display: inline-block;
  vertical-align: middle;
}
</style>