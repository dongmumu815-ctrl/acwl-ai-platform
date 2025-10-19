<template>
  <div class="help-center">
    <div class="help-header">
      <h1>帮助中心</h1>
      <p class="subtitle">围绕产品的关键模块提供指引、概念与故障排查。</p>
    </div>

    <!-- 编辑提示：显示当前文档路径 -->
    <div class="edit-hint">
      <el-alert type="info" :closable="false" show-icon>
        <template #title>
          当前主题文档路径：<code>{{ editPath }}</code>
        </template>
        <template #default>
          在仓库中编辑该 Markdown 文件，保存后页面会自动刷新。
        </template>
      </el-alert>
    </div>

    <!-- 目录导航（切换 topic） -->
    <nav class="toc">
      <ul>
        <li><a href="#" @click.prevent="changeTopic('quick-start')">快速开始</a></li>
        <li><a href="#" @click.prevent="changeTopic('datasource-list')">数据源管理</a></li>
        <li><a href="#" @click.prevent="changeTopic('template-list')">模板与查询</a></li>
        <li><a href="#" @click.prevent="changeTopic('scheduler')">任务与调度</a></li>
        <li><a href="#" @click.prevent="changeTopic('security-and-permissions')">安全与权限</a></li>
        <li><a href="#" @click.prevent="changeTopic('troubleshooting')">故障排查</a></li>
        <li><a href="#" @click.prevent="changeTopic('faq')">常见问题</a></li>
        <li><a href="#" @click.prevent="changeTopic('glossary')">术语表</a></li>
        <li><a href="#" @click.prevent="changeTopic('changelog')">变更日志</a></li>
        <li><a href="#" @click.prevent="changeTopic('feedback')">反馈与支持</a></li>
      </ul>
    </nav>

    <!-- 文档渲染区域 -->
    <article class="doc-content" v-html="renderedHtml"></article>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref, watch, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import MarkdownIt from 'markdown-it'

const route = useRoute()
const router = useRouter()
const md = new MarkdownIt({ html: true, linkify: true, breaks: true })
const renderedHtml = ref('<p>加载中...</p>')
const currentFile = ref('/docs/user-guide/quick-start.md')
const editPath = computed(() => `frontend/public${currentFile.value}`)

const topicToFile: Record<string, string> = {
  'quick-start': '/docs/user-guide/quick-start.md',
  'datasource-list': '/docs/user-guide/datasource-list.md',
  'template-list': '/docs/user-guide/template-list.md',
  'scheduler': '/docs/user-guide/scheduler.md',
  'security-and-permissions': '/docs/user-guide/security-and-permissions.md',
  'troubleshooting': '/docs/user-guide/troubleshooting.md',
  'faq': '/docs/user-guide/faq.md',
  'glossary': '/docs/user-guide/glossary.md',
  'changelog': '/docs/user-guide/changelog.md',
  'feedback': '/docs/user-guide/feedback.md'
}

const loadMarkdown = async (topic: string) => {
  const file = topicToFile[topic] || topicToFile['quick-start']
  try {
    const res = await fetch(file)
    if (!res.ok) throw new Error(`无法加载文档: ${file}`)
    const text = await res.text()
    renderedHtml.value = md.render(text)
    currentFile.value = file
  } catch (err) {
    renderedHtml.value = `<p style="color:#f56c6c">${(err as Error).message}</p>`
  }
}

const changeTopic = (topic: string) => {
  router.replace({ path: '/help', query: { topic } })
}

onMounted(() => {
  const initialTopic = (route.query?.topic as string) || 'quick-start'
  loadMarkdown(initialTopic)
})

watch(() => route.query?.topic, (newTopic) => {
  loadMarkdown((newTopic as string) || 'quick-start')
})
</script>

<style scoped>
.help-center {
  max-width: 1080px;
  margin: 0 auto;
  padding: 24px 16px 48px;
}
.help-header {
  margin-bottom: 16px;
}
.edit-hint {
  margin: 8px 0 16px;
}
.subtitle {
  color: var(--el-text-color-secondary);
}
.toc {
  background: var(--el-color-info-light-9);
  border: 1px solid var(--el-border-color);
  border-radius: 8px;
  padding: 12px 16px;
  margin-bottom: 16px;
}
.toc ul {
  display: flex;
  flex-wrap: wrap;
  gap: 12px 24px;
  list-style: none;
  padding: 0;
  margin: 0;
}
.toc a {
  color: var(--el-color-primary);
  text-decoration: none;
}
.section {
  padding: 16px 0;
  border-top: 1px dashed var(--el-border-color-light);
}
.section:first-of-type {
  border-top: none;
}

.doc-content {
  padding: 16px 0;
}
</style>