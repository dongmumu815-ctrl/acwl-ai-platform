<template>
  <div id="app">
    <router-view />
  </div>
</template>

<script setup lang="ts">
// Vue 3 Composition API setup
</script>

<style lang="scss">
#app {
  font-family:
    "Helvetica Neue", Helvetica, "PingFang SC", "Hiragino Sans GB",
    "Microsoft YaHei", "微软雅黑", Arial, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  color: var(--el-text-color-primary);
  background-color: var(--el-bg-color);
  min-height: 100vh;
}

* {
  box-sizing: border-box;
  margin: 0;
  padding: 0;
}

html,
body {
  height: 100%;
  overflow-x: hidden;
}

::-webkit-scrollbar {
  width: 6px;
  height: 6px;
}

::-webkit-scrollbar-track {
  background: var(--el-fill-color-lighter);
}

::-webkit-scrollbar-thumb {
  background: var(--el-border-color-darker);
  border-radius: 3px;
}

::-webkit-scrollbar-thumb:hover {
  background: var(--el-border-color-dark);
}
</style>
