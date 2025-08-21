<template>
  <div class="advanced-code-editor-overlay" v-if="visible" @click.self="handleClose">
    <div class="advanced-code-editor-container">
      <div class="editor-header">
        <div class="editor-title">
          <el-icon><Edit /></el-icon>
          <span>{{ title }}</span>
        </div>
        <div class="editor-actions">
          <el-button @click="handleFormat" size="small" type="primary" plain>
            <el-icon><MagicStick /></el-icon>
            格式化
          </el-button>
          <el-button @click="toggleHighlight" size="small" plain>
            <el-icon><View /></el-icon>
            {{ enableHighlight ? '关闭高亮' : '开启高亮' }}
          </el-button>
          <el-button @click="handleFullscreen" size="small" plain>
            <el-icon><FullScreen /></el-icon>
            {{ isFullscreen ? '退出全屏' : '全屏' }}
          </el-button>
          <el-button @click="handleSave" size="small" type="primary">
            <el-icon><Check /></el-icon>
            保存
          </el-button>
          <el-button @click="handleClose" size="small">
            <el-icon><Close /></el-icon>
            关闭
          </el-button>
        </div>
      </div>
      <div class="editor-content" :class="{ 'fullscreen': isFullscreen }">
        <div class="editor-wrapper">
          <div class="line-numbers" v-if="showLineNumbers">
            <div 
              v-for="lineNum in lineCount" 
              :key="lineNum" 
              class="line-number"
            >
              {{ lineNum }}
            </div>
          </div>
          <div class="code-editor-container">
            <!-- 语法高亮层 -->
            <div 
              v-if="enableHighlight"
              class="syntax-highlight-layer"
              v-html="highlightedCode"
              @scroll="handleScroll"
            ></div>
            <!-- 代码输入层 -->
            <textarea 
              ref="textareaRef"
              v-model="localValue"
              :placeholder="placeholder"
              :readonly="readonly"
              class="code-textarea"
              :class="[`language-${language}`, { 'transparent': enableHighlight }]"
              @input="handleInput"
              @keydown="handleKeydown"
              @scroll="handleScroll"
              @select="handleSelection"
              spellcheck="false"
            ></textarea>
          </div>
        </div>
      </div>
      <div class="editor-footer">
        <div class="editor-info">
          <span>语言: {{ languageDisplay }}</span>
          <span>行数: {{ lineCount }}</span>
          <span>字符数: {{ charCount }}</span>
          <span v-if="selectionInfo">选择: {{ selectionInfo }}</span>
        </div>
        <div class="editor-tips">
          <el-text size="small" type="info">
            提示: Ctrl+S 保存, Ctrl+A 全选, Ctrl+Z 撤销, F11 全屏
          </el-text>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, nextTick, onMounted, onUnmounted } from 'vue'
import { Edit, MagicStick, FullScreen, Check, Close, View } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'

/**
 * 高级代码编辑器组件属性
 */
const props = defineProps({
  visible: {
    type: Boolean,
    default: false
  },
  modelValue: {
    type: String,
    default: ''
  },
  language: {
    type: String,
    default: 'javascript',
    validator: (value) => ['javascript', 'python', 'sql', 'shell', 'bash'].includes(value)
  },
  title: {
    type: String,
    default: '代码编辑器'
  },
  readonly: {
    type: Boolean,
    default: false
  },
  placeholder: {
    type: String,
    default: '请输入代码...'
  },
  showLineNumbers: {
    type: Boolean,
    default: true
  }
})

/**
 * 组件事件
 */
const emit = defineEmits(['update:modelValue', 'save', 'close'])

// 编辑器相关状态
const textareaRef = ref(null)
const localValue = ref(props.modelValue || '')
const isFullscreen = ref(false)
const selectionInfo = ref('')
const enableHighlight = ref(true)

/**
 * 语言显示名称映射
 */
const languageMap = {
  python: 'Python',
  sql: 'SQL',
  shell: 'Shell',
  bash: 'Bash',
  javascript: 'JavaScript'
}

/**
 * 计算属性：语言显示名称
 */
const languageDisplay = computed(() => {
  return languageMap[props.language] || props.language
})

/**
 * 计算属性：行数
 */
const lineCount = computed(() => {
  if (!localValue.value) return 1
  return localValue.value.split('\n').length
})

/**
 * 计算属性：字符数
 */
const charCount = computed(() => {
  return localValue.value.length
})

/**
 * 计算属性：语法高亮后的代码
 */
const highlightedCode = computed(() => {
  if (!enableHighlight.value || !localValue.value) {
    return ''
  }
  return highlightSyntax(localValue.value, props.language)
})

/**
 * 切换语法高亮
 */
const toggleHighlight = () => {
  enableHighlight.value = !enableHighlight.value
  ElMessage.success(enableHighlight.value ? '语法高亮已开启' : '语法高亮已关闭')
}

/**
 * 处理输入事件
 */
const handleInput = () => {
  emit('update:modelValue', localValue.value)
}

/**
 * 处理键盘事件，添加高级代码编辑功能
 */
const handleKeydown = (event) => {
  // Ctrl+S 保存
  if (event.ctrlKey && event.key === 's') {
    event.preventDefault()
    handleSave()
    return
  }
  
  // F11 全屏
  if (event.key === 'F11') {
    event.preventDefault()
    handleFullscreen()
    return
  }
  
  // Tab键缩进
  if (event.key === 'Tab') {
    event.preventDefault()
    const start = event.target.selectionStart
    const end = event.target.selectionEnd
    const value = event.target.value
    
    if (event.shiftKey) {
      // Shift+Tab 减少缩进
      const lines = value.substring(0, start).split('\n')
      const currentLineStart = value.lastIndexOf('\n', start - 1) + 1
      const currentLine = value.substring(currentLineStart, value.indexOf('\n', start) === -1 ? value.length : value.indexOf('\n', start))
      
      if (currentLine.startsWith('  ')) {
        const newValue = value.substring(0, currentLineStart) + currentLine.substring(2) + value.substring(currentLineStart + currentLine.length)
        localValue.value = newValue
        
        nextTick(() => {
          event.target.selectionStart = event.target.selectionEnd = start - 2
        })
      }
    } else {
      // Tab 增加缩进
      const newValue = value.substring(0, start) + '  ' + value.substring(end)
      localValue.value = newValue
      
      nextTick(() => {
        event.target.selectionStart = event.target.selectionEnd = start + 2
      })
    }
  }
  
  // Enter键自动缩进
  if (event.key === 'Enter') {
    const start = event.target.selectionStart
    const value = event.target.value
    const lines = value.substring(0, start).split('\n')
    const currentLine = lines[lines.length - 1]
    
    // 计算当前行的缩进
    const indent = currentLine.match(/^\s*/)[0]
    
    // 检查是否需要额外缩进（如函数定义、if语句等）
    let extraIndent = ''
    if (props.language === 'python') {
      if (currentLine.trim().endsWith(':')) {
        extraIndent = '  '
      }
    } else if (props.language === 'javascript') {
      if (currentLine.trim().endsWith('{')) {
        extraIndent = '  '
      }
    }
    
    setTimeout(() => {
      const newStart = event.target.selectionStart
      const newValue = event.target.value
      const beforeCursor = newValue.substring(0, newStart)
      const afterCursor = newValue.substring(newStart)
      
      localValue.value = beforeCursor + indent + extraIndent + afterCursor
      
      nextTick(() => {
        event.target.selectionStart = event.target.selectionEnd = newStart + indent.length + extraIndent.length
      })
    }, 0)
  }
  
  // 括号自动补全
  if (['(', '[', '{', '"', "'"].includes(event.key)) {
    const start = event.target.selectionStart
    const end = event.target.selectionEnd
    const value = event.target.value
    
    const pairs = {
      '(': ')',
      '[': ']',
      '{': '}',
      '"': '"',
      "'": "'"
    }
    
    if (start === end) { // 没有选中文本
      event.preventDefault()
      const newValue = value.substring(0, start) + event.key + pairs[event.key] + value.substring(end)
      localValue.value = newValue
      
      nextTick(() => {
        event.target.selectionStart = event.target.selectionEnd = start + 1
      })
    }
  }
}

/**
 * 处理滚动事件，同步行号和高亮层
 */
const handleScroll = () => {
  if (textareaRef.value) {
    // 同步行号滚动
    if (props.showLineNumbers) {
      const lineNumbers = document.querySelector('.line-numbers')
      if (lineNumbers) {
        lineNumbers.scrollTop = textareaRef.value.scrollTop
      }
    }
    
    // 同步语法高亮层滚动
    if (enableHighlight.value) {
      const highlightLayer = document.querySelector('.syntax-highlight-layer')
      if (highlightLayer) {
        highlightLayer.scrollTop = textareaRef.value.scrollTop
        highlightLayer.scrollLeft = textareaRef.value.scrollLeft
      }
    }
  }
}

/**
 * 处理选择事件，更新选择信息
 */
const handleSelection = () => {
  if (textareaRef.value) {
    const start = textareaRef.value.selectionStart
    const end = textareaRef.value.selectionEnd
    
    if (start !== end) {
      const selectedText = localValue.value.substring(start, end)
      const lines = selectedText.split('\n').length
      const chars = selectedText.length
      selectionInfo.value = `${lines}行 ${chars}字符`
    } else {
      selectionInfo.value = ''
    }
  }
}

/**
 * 格式化代码
 */
const handleFormat = () => {
  try {
    let formatted = localValue.value
    
    if (props.language === 'sql') {
      formatted = formatSQL(formatted)
    } else if (props.language === 'javascript') {
      formatted = formatJavaScript(formatted)
    } else if (props.language === 'python') {
      formatted = formatPython(formatted)
    }
    
    localValue.value = formatted
    emit('update:modelValue', formatted)
    ElMessage.success('代码格式化完成')
  } catch (error) {
    console.error('格式化失败:', error)
    ElMessage.error('格式化失败: ' + error.message)
  }
}

/**
 * 格式化SQL代码
 */
const formatSQL = (sql) => {
  if (!sql.trim()) return sql
  
  try {
    // 基本的SQL格式化
    let formatted = sql
      .replace(/\s+/g, ' ') /* 合并多个空格 */
      .replace(/;\s*/g, ';\n') /* 分号后换行 */
      .replace(/\b(SELECT|FROM|WHERE|JOIN|INNER JOIN|LEFT JOIN|RIGHT JOIN|GROUP BY|ORDER BY|HAVING|UNION)\b/gi, '\n$1')
      .replace(/\b(INSERT INTO|UPDATE|DELETE FROM|CREATE TABLE|ALTER TABLE|DROP TABLE)\b/gi, '\n$1')
      .replace(/\n\s*\n/g, '\n') // 移除多余空行
      .trim()
    
    // 关键字大写
    const keywords = ['SELECT', 'FROM', 'WHERE', 'JOIN', 'INNER', 'LEFT', 'RIGHT', 'GROUP', 'ORDER', 'BY', 'HAVING', 'UNION', 'INSERT', 'INTO', 'UPDATE', 'DELETE', 'CREATE', 'TABLE', 'ALTER', 'DROP', 'AND', 'OR', 'NOT', 'NULL', 'IS', 'AS', 'ON']
    keywords.forEach(keyword => {
      const regex = new RegExp(`\\b${keyword}\\b`, 'gi')
      formatted = formatted.replace(regex, keyword)
    })
    
    return formatted
  } catch (error) {
    console.error('SQL格式化出错:', error)
    return sql
  }
}

/**
 * 格式化JavaScript代码（简单版）
 */
const formatJavaScript = (js) => {
  if (!js.trim()) return js
  
  try {
    // 基本的JavaScript格式化
    let formatted = js
      .replace(/;\s*(?=\S)/g, ';\n') // 分号后换行（如果后面不是空白）
      .replace(/{\s*/g, ' {\n') // 左大括号后换行
      .replace(/}\s*/g, '\n}\n') // 右大括号前后换行
      .replace(/\n\s*\n/g, '\n') // 移除多余空行
      .trim()
    
    return formatted
  } catch (error) {
    console.error('JavaScript格式化出错:', error)
    return js
  }
}

/**
 * 格式化Python代码（简单版）
 */
const formatPython = (python) => {
  if (!python.trim()) return python
  
  try {
    // 基本的Python格式化
    let formatted = python
      .replace(/:\s*(?=\S)/g, ':\n') // 冒号后换行（如果后面不是空白）
      .replace(/\n\s*\n\s*\n/g, '\n\n') // 最多保留一个空行
      .trim()
    
    return formatted
  } catch (error) {
    console.error('Python格式化出错:', error)
    return python
  }
}

/**
 * 切换全屏模式
 */
const handleFullscreen = () => {
  isFullscreen.value = !isFullscreen.value
  
  nextTick(() => {
    if (textareaRef.value) {
      textareaRef.value.focus()
    }
  })
}

/**
 * 保存代码
 */
const handleSave = () => {
  try {
    emit('update:modelValue', localValue.value)
    emit('save', localValue.value)
    ElMessage.success('代码已保存')
  } catch (error) {
    console.error('保存失败:', error)
    ElMessage.error('保存失败: ' + error.message)
  }
}

/**
 * 关闭编辑器
 */
const handleClose = () => {
  emit('close')
}

/**
 * 监听 modelValue 变化
 */
watch(() => props.modelValue, (newValue) => {
  if (newValue !== localValue.value) {
    localValue.value = newValue || ''
  }
})

/**
 * 监听 visible 变化，自动聚焦
 */
watch(() => props.visible, (newVal) => {
  if (newVal) {
    nextTick(() => {
      if (textareaRef.value) {
        textareaRef.value.focus()
      }
    })
  }
})

/**
 * 键盘快捷键监听
 */
const handleGlobalKeydown = (event) => {
  if (props.visible) {
    // ESC 关闭编辑器
    if (event.key === 'Escape') {
      handleClose()
    }
  }
}

/**
 * 组件挂载时添加全局键盘监听
 */
onMounted(() => {
  document.addEventListener('keydown', handleGlobalKeydown)
})

/**
 * 组件卸载时移除全局键盘监听
 */
onUnmounted(() => {
  document.removeEventListener('keydown', handleGlobalKeydown)
})

/**
 * 语法高亮核心函数
 */
const highlightSyntax = (code, language) => {
  if (!code) return ''
  
  let highlighted = escapeHtml(code)
  
  switch (language) {
    case 'python':
      highlighted = highlightPython(highlighted)
      break
    case 'javascript':
      highlighted = highlightJavaScript(highlighted)
      break
    case 'sql':
      highlighted = highlightSQL(highlighted)
      break
    case 'shell':
    case 'bash':
      highlighted = highlightShell(highlighted)
      break
    default:
      highlighted = highlightGeneric(highlighted)
  }
  
  return highlighted
}

/**
 * HTML转义函数
 */
const escapeHtml = (text) => {
  const div = document.createElement('div')
  div.textContent = text
  return div.innerHTML
}

/**
 * Python语法高亮
 */
const highlightPython = (code) => {
  // Python关键字
  const keywords = ['def', 'class', 'if', 'elif', 'else', 'for', 'while', 'try', 'except', 'finally', 'with', 'as', 'import', 'from', 'return', 'yield', 'break', 'continue', 'pass', 'lambda', 'and', 'or', 'not', 'in', 'is', 'True', 'False', 'None']
  
  // 高亮关键字
  keywords.forEach(keyword => {
    const regex = new RegExp(`\\b${keyword.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')}\\b`, 'g')
    code = code.replace(regex, `<span class="keyword">${keyword}</span>`)
  })
  
  // 高亮字符串
  code = code.replace(/(['"`])([^\1]*?)\1/g, '<span class="string">$1$2$1</span>')
  
  // 高亮注释
  code = code.replace(/(#.*$)/gm, '<span class="comment">$1</span>')
  
  // 高亮数字
  code = code.replace(/\b\d+(\.\d+)?\b/g, '<span class="number">$&</span>')
  
  // 高亮函数定义
  code = code.replace(/\bdef\s+(\w+)/g, 'def <span class="function">$1</span>')
  
  return code
}

/**
 * JavaScript语法高亮
 */
const highlightJavaScript = (code) => {
  // JavaScript关键字
  const keywords = ['function', 'var', 'let', 'const', 'if', 'else', 'for', 'while', 'do', 'switch', 'case', 'default', 'break', 'continue', 'return', 'try', 'catch', 'finally', 'throw', 'new', 'this', 'typeof', 'instanceof', 'true', 'false', 'null', 'undefined']
  
  // 高亮关键字
  keywords.forEach(keyword => {
    const regex = new RegExp(`\\b${keyword.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')}\\b`, 'g')
    code = code.replace(regex, `<span class="keyword">${keyword}</span>`)
  })
  
  // 高亮字符串
  code = code.replace(/(['"`])([^\1]*?)\1/g, '<span class="string">$1$2$1</span>')
  
  // 高亮注释
  code = code.replace(/(\/\/.*$)/gm, '<span class="comment">$1</span>')
  code = code.replace(/(\/\*[\s\S]*?\*\/)/g, '<span class="comment">$1</span>')
  
  // 高亮数字
  code = code.replace(/\b\d+(\.\d+)?\b/g, '<span class="number">$&</span>')
  
  // 高亮函数定义
  code = code.replace(/\bfunction\s+(\w+)/g, 'function <span class="function">$1</span>')
  
  return code
}

/**
 * SQL语法高亮
 */
const highlightSQL = (code) => {
  // SQL关键字
  const keywords = ['SELECT', 'FROM', 'WHERE', 'JOIN', 'INNER', 'LEFT', 'RIGHT', 'OUTER', 'ON', 'GROUP', 'BY', 'ORDER', 'HAVING', 'INSERT', 'INTO', 'VALUES', 'UPDATE', 'SET', 'DELETE', 'CREATE', 'TABLE', 'ALTER', 'DROP', 'INDEX', 'DATABASE', 'SCHEMA', 'AND', 'OR', 'NOT', 'NULL', 'IS', 'AS', 'DISTINCT', 'COUNT', 'SUM', 'AVG', 'MAX', 'MIN']
  
  // 高亮关键字（不区分大小写）
  keywords.forEach(keyword => {
    const regex = new RegExp(`\\b${keyword.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')}\\b`, 'gi')
    code = code.replace(regex, `<span class="keyword">${keyword}</span>`)
  })
  
  // 高亮字符串
  code = code.replace(/('[^']*')/g, '<span class="string">$1</span>')
  code = code.replace(/("[^"]*")/g, '<span class="string">$1</span>')
  
  // 高亮注释
  code = code.replace(/(--.*$)/gm, '<span class="comment">$1</span>')
  code = code.replace(/(\/\*[\s\S]*?\*\/)/g, '<span class="comment">$1</span>')
  
  // 高亮数字
  code = code.replace(/\b\d+(\.\d+)?\b/g, '<span class="number">$&</span>')
  
  return code
}

/**
 * Shell/Bash语法高亮
 */
const highlightShell = (code) => {
  // Shell关键字
  const keywords = ['if', 'then', 'else', 'elif', 'fi', 'for', 'while', 'do', 'done', 'case', 'esac', 'function', 'return', 'exit', 'break', 'continue', 'echo', 'printf', 'read', 'export', 'source', 'cd', 'ls', 'cp', 'mv', 'rm', 'mkdir', 'chmod', 'chown', 'grep', 'sed', 'awk', 'sort', 'uniq', 'head', 'tail', 'cat', 'less', 'more']
  
  // 高亮关键字
  keywords.forEach(keyword => {
    const regex = new RegExp(`\\b${keyword.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')}\\b`, 'g')
    code = code.replace(regex, `<span class="keyword">${keyword}</span>`)
  })
  
  // 高亮字符串
  code = code.replace(/(['"`])([^\1]*?)\1/g, '<span class="string">$1$2$1</span>')
  
  // 高亮注释
  code = code.replace(/(#.*$)/gm, '<span class="comment">$1</span>')
  
  // 高亮变量
  code = code.replace(/(\$\w+|\$\{[^}]+\})/g, '<span class="variable">$1</span>')
  
  // 高亮数字
  code = code.replace(/\b\d+(\.\d+)?\b/g, '<span class="number">$&</span>')
  
  return code
}

/**
 * 通用语法高亮
 */
const highlightGeneric = (code) => {
  // 高亮字符串
  code = code.replace(/(['"`])([^\1]*?)\1/g, '<span class="string">$1$2$1</span>')
  
  // 高亮注释
  code = code.replace(/(#.*$)/gm, '<span class="comment">$1</span>')
  code = code.replace(/(\/\/.*$)/gm, '<span class="comment">$1</span>')
  code = code.replace(/(\/\*[\s\S]*?\*\/)/g, '<span class="comment">$1</span>')
  
  // 高亮数字
  code = code.replace(/\b\d+(\.\d+)?\b/g, '<span class="number">$&</span>')
  
  return code
}
</script>

<style scoped>
.advanced-code-editor-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  z-index: 2000;
  display: flex;
  align-items: center;
  justify-content: center;
  backdrop-filter: blur(4px);
}

.advanced-code-editor-container {
  width: 90vw;
  height: 80vh;
  max-width: 1200px;
  background: #1e1e1e;
  border-radius: 8px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.editor-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  background: #2d2d30;
  border-bottom: 1px solid #3e3e42;
}

.editor-title {
  display: flex;
  align-items: center;
  gap: 8px;
  color: #cccccc;
  font-size: 14px;
  font-weight: 500;
}

.editor-actions {
  display: flex;
  gap: 8px;
}

.editor-content {
  flex: 1;
  position: relative;
  overflow: hidden;
}

.editor-content.fullscreen {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  z-index: 2001;
  background: #1e1e1e;
}

.editor-wrapper {
  display: flex;
  height: 100%;
  background: #1e1e1e;
}

.code-editor-container {
  flex: 1;
  position: relative;
  overflow: hidden;
}

.syntax-highlight-layer {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  padding: 8px 12px;
  font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
  font-size: 13px;
  line-height: 1.4;
  background: transparent;
  color: transparent;
  white-space: pre;
  overflow: auto;
  pointer-events: none;
  z-index: 1;
  tab-size: 2;
}

.line-numbers {
  background: #252526;
  color: #858585;
  padding: 8px 8px 8px 16px;
  font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
  font-size: 13px;
  line-height: 1.4;
  text-align: right;
  user-select: none;
  border-right: 1px solid #3e3e42;
  overflow: hidden;
  min-width: 50px;
}

.line-number {
  height: 18.2px; /* 匹配textarea行高 */
  display: flex;
  align-items: center;
  justify-content: flex-end;
}

.code-textarea {
  flex: 1;
  border: none;
  outline: none;
  resize: none;
  padding: 8px 12px;
  font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
  font-size: 13px;
  line-height: 1.4;
  background: #1e1e1e;
  color: #d4d4d4;
  tab-size: 2;
  white-space: pre;
  overflow-wrap: normal;
  overflow-x: auto;
  position: relative;
  z-index: 2;
}

.code-textarea.transparent {
  color: transparent;
  caret-color: #d4d4d4;
}

.code-textarea:focus {
  background: #1e1e1e;
}

.code-textarea::placeholder {
  color: #6a6a6a;
  font-style: italic;
}

/* 语言特定样式 */
.code-textarea.language-sql {
  color: #569cd6;
}

.code-textarea.language-python {
  color: #dcdcaa;
}

.code-textarea.language-javascript {
  color: #ce9178;
}

.code-textarea.language-shell,
.code-textarea.language-bash {
  color: #b5cea8;
}

/* 语法高亮样式 */
.syntax-highlight-layer :deep(.keyword) {
  color: #569cd6;
  font-weight: bold;
}

.syntax-highlight-layer :deep(.string) {
  color: #ce9178;
}

.syntax-highlight-layer :deep(.comment) {
  color: #6a9955;
  font-style: italic;
}

.syntax-highlight-layer :deep(.number) {
  color: #b5cea8;
}

.syntax-highlight-layer :deep(.function) {
  color: #dcdcaa;
  font-weight: bold;
}

.syntax-highlight-layer :deep(.variable) {
  color: #9cdcfe;
}

.syntax-highlight-layer :deep(.operator) {
  color: #d4d4d4;
}

.syntax-highlight-layer :deep(.punctuation) {
  color: #d4d4d4;
}

.editor-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 16px;
  background: #2d2d30;
  border-top: 1px solid #3e3e42;
  font-size: 12px;
}

.editor-info {
  display: flex;
  gap: 16px;
  color: #cccccc;
}

.editor-tips {
  color: #888888;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .advanced-code-editor-container {
    width: 95vw;
    height: 90vh;
  }
  
  .editor-header {
    flex-direction: column;
    gap: 8px;
    align-items: stretch;
  }
  
  .editor-actions {
    justify-content: center;
  }
  
  .editor-footer {
    flex-direction: column;
    gap: 4px;
    align-items: center;
  }
  
  .line-numbers {
    display: none;
  }
}
</style>