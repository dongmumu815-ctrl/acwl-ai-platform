<template>
  <div class="pdf-viewer">
    <div class="toolbar">
      <el-button size="small" @click="openInNewTab" :disabled="!src">在新标签打开</el-button>
    </div>
    <div class="viewer">
      <iframe v-if="src" :src="src" frameborder="0" class="iframe"></iframe>
      <el-empty v-else description="无有效 PDF 链接" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { defineProps } from 'vue'
const props = defineProps<{ src: string }>()
const openInNewTab = () => {
  if (props.src) window.open(props.src, '_blank')
}
</script>

<style scoped>
.pdf-viewer {
  width: 100%;
}
.viewer {
  width: 100%;
  height: 80vh;
  background: #f5f7fa;
  border: 1px solid #e4e7ed;
}
.iframe {
  width: 100%;
  height: 100%;
}
.toolbar {
  margin-bottom: 8px;
  display: flex;
  justify-content: flex-end;
}
</style>