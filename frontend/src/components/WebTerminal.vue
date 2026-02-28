<template>
  <div class="terminal-wrapper">
    <div class="terminal-container" ref="terminalRef"></div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, nextTick, watch } from 'vue'
import { Terminal } from 'xterm'
import { FitAddon } from 'xterm-addon-fit'
import { WebLinksAddon } from 'xterm-addon-web-links'
import { getToken } from '@/utils/auth'
import 'xterm/css/xterm.css'

const props = defineProps<{
  serverId: number | null
  theme?: string
}>()

const terminalRef = ref<HTMLElement | null>(null)
let term: Terminal | null = null
let fitAddon: FitAddon | null = null
let socket: WebSocket | null = null
let resizeObserver: ResizeObserver | null = null

// 主题配置
const themeConfigs: Record<string, any> = {
  'default': {
    background: '#1e1e1e',
    foreground: '#ffffff',
    cursor: '#ffffff',
    selectionBackground: 'rgba(255, 255, 255, 0.3)',
    black: '#000000',
    red: '#cd3131',
    green: '#0dbc79',
    yellow: '#e5e510',
    blue: '#2472c8',
    magenta: '#bc3fbc',
    cyan: '#11a8cd',
    white: '#e5e5e5',
    brightBlack: '#666666',
    brightRed: '#f14c4c',
    brightGreen: '#23d18b',
    brightYellow: '#f5f543',
    brightBlue: '#3b8eea',
    brightMagenta: '#d670d6',
    brightCyan: '#29b8db',
    brightWhite: '#e5e5e5'
  },
  'github': {
    background: '#ffffff',
    foreground: '#24292e',
    cursor: '#24292e',
    selectionBackground: '#c8c8fa',
    black: '#24292e',
    red: '#d73a49',
    green: '#28a745',
    yellow: '#dbab09',
    blue: '#0366d6',
    magenta: '#5a32a3',
    cyan: '#0598bc',
    white: '#6a737d',
    brightBlack: '#959da5',
    brightRed: '#cb2431',
    brightGreen: '#22863a',
    brightYellow: '#b08800',
    brightBlue: '#005cc5',
    brightMagenta: '#5a32a3',
    brightCyan: '#3192aa',
    brightWhite: '#d1d5da'
  },
  'solarized-dark': {
    background: '#002b36',
    foreground: '#839496',
    cursor: '#93a1a1',
    selectionBackground: '#073642',
    black: '#073642',
    red: '#dc322f',
    green: '#859900',
    yellow: '#b58900',
    blue: '#268bd2',
    magenta: '#d33682',
    cyan: '#2aa198',
    white: '#eee8d5',
    brightBlack: '#002b36',
    brightRed: '#cb4b16',
    brightGreen: '#586e75',
    brightYellow: '#657b83',
    brightBlue: '#839496',
    brightMagenta: '#6c71c4',
    brightCyan: '#93a1a1',
    brightWhite: '#fdf6e3'
  },
  'monokai': {
    background: '#272822',
    foreground: '#f8f8f2',
    cursor: '#f8f8f0',
    selectionBackground: '#49483e',
    black: '#272822',
    red: '#f92672',
    green: '#a6e22e',
    yellow: '#f4bf75',
    blue: '#66d9ef',
    magenta: '#ae81ff',
    cyan: '#a1efe4',
    white: '#f8f8f2',
    brightBlack: '#75715e',
    brightRed: '#f92672',
    brightGreen: '#a6e22e',
    brightYellow: '#f4bf75',
    brightBlue: '#66d9ef',
    brightMagenta: '#ae81ff',
    brightCyan: '#a1efe4',
    brightWhite: '#f9f8f5'
  },
  'dracula': {
    background: '#282a36',
    foreground: '#f8f8f2',
    cursor: '#f8f8f2',
    selectionBackground: '#44475a',
    black: '#21222c',
    red: '#ff5555',
    green: '#50fa7b',
    yellow: '#f1fa8c',
    blue: '#bd93f9',
    magenta: '#ff79c6',
    cyan: '#8be9fd',
    white: '#f8f8f2',
    brightBlack: '#6272a4',
    brightRed: '#ff6e6e',
    brightGreen: '#69ff94',
    brightYellow: '#ffffa5',
    brightBlue: '#d6acff',
    brightMagenta: '#ff92df',
    brightCyan: '#a4ffff',
    brightWhite: '#ffffff'
  }
}

const applyTheme = (themeName: string) => {
  if (term && themeConfigs[themeName]) {
    const theme = themeConfigs[themeName]
    term.options.theme = theme
    if (terminalRef.value) {
      terminalRef.value.style.backgroundColor = theme.background
    }
    const wrapper = terminalRef.value?.parentElement
    if (wrapper) {
      wrapper.style.backgroundColor = theme.background
    }
  }
}

watch(() => props.theme, (newTheme) => {
  if (newTheme) {
    applyTheme(newTheme)
  }
})

// 防抖函数
const debounce = (fn: Function, delay: number) => {
  let timeoutId: any
  return (...args: any[]) => {
    clearTimeout(timeoutId)
    timeoutId = setTimeout(() => fn(...args), delay)
  }
}

// 复制到剪贴板
const copyToClipboard = async (text: string) => {
  try {
    if (navigator.clipboard && navigator.clipboard.writeText) {
      await navigator.clipboard.writeText(text)
    } else {
      console.warn('Clipboard API not supported')
    }
  } catch (err) {
    console.error('复制失败:', err)
  }
}

const initTerminal = () => {
  if (!terminalRef.value) return

  term = new Terminal({
    cursorBlink: true,
    fontSize: 14,
    fontFamily: 'Menlo, Monaco, "Courier New", monospace',
    theme: themeConfigs[props.theme || 'default'],
    convertEol: true, // Handle \n as \r\n
  })

  // 初始应用主题
  applyTheme(props.theme || 'default')

  fitAddon = new FitAddon()
  term.loadAddon(fitAddon)
  term.loadAddon(new WebLinksAddon())

  term.open(terminalRef.value)
  
  // 监听容器大小变化
  resizeObserver = new ResizeObserver(() => {
    fit()
  })
  resizeObserver.observe(terminalRef.value)

  term.onData(data => {
    if (socket && socket.readyState === WebSocket.OPEN) {
      socket.send(JSON.stringify({ type: 'input', data }))
    }
  })
  
  term.onResize((size) => {
    if (socket && socket.readyState === WebSocket.OPEN) {
      socket.send(JSON.stringify({ 
        type: 'resize', 
        rows: size.rows, 
        cols: size.cols 
      }))
    }
  })

  // 监听选区变化，实现选中即复制
  term.onSelectionChange(debounce(() => {
    if (!term) return
    const selection = term.getSelection()
    if (selection) {
      copyToClipboard(selection)
    }
  }, 300))
}

const fit = () => {
  if (fitAddon && term && terminalRef.value && terminalRef.value.offsetParent) {
    try {
      fitAddon.fit()
      // 发送新的尺寸给后端
      if (socket && socket.readyState === WebSocket.OPEN) {
        socket.send(JSON.stringify({ 
          type: 'resize', 
          rows: term.rows, 
          cols: term.cols 
        }))
      }
    } catch (e) {
      console.warn('Terminal fit failed', e)
    }
  }
}

const connect = () => {
  if (!props.serverId) return

  if (socket) {
    socket.close()
  }

  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
  const host = window.location.host
  const token = getToken()
  // 加上 /v1 路径前缀，并附带 token
  const wsUrl = `${protocol}//${host}/api/v1/ws/ssh/${props.serverId}?token=${token}`
  
  term?.write(`\r\n\x1b[33m正在连接到服务器 (ID: ${props.serverId})...\x1b[0m\r\n`)
  
  try {
    socket = new WebSocket(wsUrl)
  } catch (e) {
    term?.write(`\r\n\x1b[31mWebSocket创建失败: ${e}\x1b[0m\r\n`)
    return
  }

  socket.onopen = () => {
    term?.write('\r\n\x1b[32m连接成功！\x1b[0m\r\n')
    // Send initial resize
    nextTick(() => {
      fit()
    })
  }

  socket.onmessage = (event) => {
    try {
      // Try to parse as JSON first
      const msg = JSON.parse(event.data)
      if (msg.type === 'output') {
           term?.write(msg.data)
      } else if (typeof msg === 'string') {
          term?.write(msg)
      }
    } catch (e) {
      // If not JSON, treat as raw string
      term?.write(event.data)
    }
  }

  socket.onclose = (event) => {
    console.log('WS Closed:', event)
    term?.write('\r\n\x1b[31m连接已关闭。\x1b[0m\r\n')
  }

  socket.onerror = (error) => {
    console.error('WebSocket error:', error)
    term?.write('\r\n\x1b[31m连接发生错误。\x1b[0m\r\n')
  }
}

const dispose = () => {
  if (resizeObserver) {
    resizeObserver.disconnect()
    resizeObserver = null
  }
  if (socket) {
    socket.close()
    socket = null
  }
  if (term) {
    term.dispose()
    term = null
  }
}

onMounted(() => {
  initTerminal()
  connect()
})

onUnmounted(() => {
  dispose()
})

// 暴露 fit 方法给父组件
defineExpose({
  fit
})
</script>

<style scoped>
.terminal-wrapper {
  width: 100%;
  height: 100%;
  background-color: #1e1e1e;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.terminal-container {
  width: 100%;
  flex: 1;
  overflow: hidden;
}

/* 覆盖 xterm 的滚动条样式 */
:deep(.xterm-viewport) {
  overflow-y: auto;
}
</style>
