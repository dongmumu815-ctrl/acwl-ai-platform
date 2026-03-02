
<template>
  <el-dialog
    v-model="visible"
    title="部署日志"
    width="900px"
    :close-on-click-modal="false"
    :close-on-press-escape="false"
    class="deployment-logs-dialog"
    append-to-body
  >
    <div class="logs-header">
      <div class="status-indicator">
        <span class="status-dot" :class="statusClass"></span>
        <span class="status-text">{{ statusText }}</span>
      </div>
      <el-button size="small" @click="clearLogs" link>清空</el-button>
    </div>
    
    <div class="logs-container" ref="logsContainer">
      <div v-if="logs.length === 0" class="empty-logs">等待日志输出...</div>
      <div v-for="(log, index) in logs" :key="index" class="log-line">{{ log }}</div>
    </div>
    
    <template #footer>
      <div class="dialog-footer">
        <el-button @click="closeDialog">关闭</el-button>
      </div>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, watch, nextTick, onBeforeUnmount, computed } from 'vue'

const props = defineProps<{
  modelValue: boolean
  instanceId: number | null
}>()

const emit = defineEmits(['update:modelValue'])

const visible = ref(false)
const logs = ref<string[]>([])
const connectionStatus = ref<'disconnected' | 'connecting' | 'connected' | 'error'>('disconnected')
let ws: WebSocket | null = null

const statusText = computed(() => {
  switch (connectionStatus.value) {
    case 'connected': return '实时日志已连接'
    case 'connecting': return '正在连接...'
    case 'disconnected': return '已断开'
    case 'error': return '连接错误'
    default: return '未知状态'
  }
})

const statusClass = computed(() => {
  return connectionStatus.value
})

watch(() => props.modelValue, (val) => {
  visible.value = val
  if (val && props.instanceId) {
    connectWs(props.instanceId)
  } else {
    disconnectWs()
  }
})

watch(visible, (val) => {
  emit('update:modelValue', val)
})

const logsContainer = ref<HTMLElement | null>(null)

const scrollToBottom = () => {
  nextTick(() => {
    if (logsContainer.value) {
      logsContainer.value.scrollTop = logsContainer.value.scrollHeight
    }
  })
}

const clearLogs = () => {
  logs.value = []
}

const connectWs = (id: number) => {
  logs.value = []
  connectionStatus.value = 'connecting'
  
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
  const host = window.location.host
  
  // Try to determine API base URL
  // If VITE_API_URL is relative (starts with /), append to host
  // If absolute, parse it
  const apiBase = import.meta.env.VITE_API_URL || '/api/v1'
  
  let wsUrl = ''
  if (apiBase.startsWith('http')) {
      wsUrl = apiBase.replace(/^http/, 'ws')
  } else {
      wsUrl = `${protocol}//${host}${apiBase}`
  }
  
  // Remove trailing slash if exists
  wsUrl = wsUrl.replace(/\/$/, '')
  
  const url = `${wsUrl}/ws/deploy/${id}`
  console.log('Connecting to WS:', url)
  
  try {
    ws = new WebSocket(url)
    
    ws.onopen = () => {
      connectionStatus.value = 'connected'
      logs.value.push('[System] Log connection established.')
    }
    
    ws.onmessage = (event) => {
      logs.value.push(event.data)
      scrollToBottom()
    }
    
    ws.onclose = () => {
      connectionStatus.value = 'disconnected'
      logs.value.push('[System] Connection closed.')
      scrollToBottom()
    }
    
    ws.onerror = (error) => {
      console.error('WS Error:', error)
      connectionStatus.value = 'error'
      logs.value.push('[System] Connection error occurred.')
    }
  } catch (e) {
    console.error('WS Creation Error:', e)
    connectionStatus.value = 'error'
  }
}

const disconnectWs = () => {
  if (ws) {
    ws.close()
    ws = null
  }
  connectionStatus.value = 'disconnected'
}

const closeDialog = () => {
  visible.value = false
}

onBeforeUnmount(() => {
  disconnectWs()
})
</script>

<style scoped>
.deployment-logs-dialog :deep(.el-dialog__body) {
  padding-top: 10px;
  padding-bottom: 10px;
}

.logs-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}

.status-indicator {
  display: flex;
  align-items: center;
  font-size: 13px;
}

.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  margin-right: 6px;
  background-color: #ccc;
}

.status-dot.connected { background-color: #67c23a; box-shadow: 0 0 4px #67c23a; }
.status-dot.connecting { background-color: #e6a23c; animation: pulse 1s infinite; }
.status-dot.disconnected { background-color: #909399; }
.status-dot.error { background-color: #f56c6c; }

@keyframes pulse {
  0% { opacity: 1; }
  50% { opacity: 0.5; }
  100% { opacity: 1; }
}

.logs-container {
  background-color: #1e1e1e;
  color: #d4d4d4;
  font-family: 'Consolas', 'Monaco', monospace;
  padding: 12px;
  height: 500px;
  overflow-y: auto;
  border-radius: 4px;
  font-size: 13px;
  line-height: 1.5;
  white-space: pre-wrap;
  word-break: break-all;
  border: 1px solid #333;
}
.log-line {
  margin-bottom: 2px;
}
.empty-logs {
  color: #666;
  text-align: center;
  margin-top: 220px;
}
</style>
