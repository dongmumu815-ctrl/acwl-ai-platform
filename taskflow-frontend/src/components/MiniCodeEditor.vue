<template>
  <div class="mini-code-editor">
    <textarea 
      ref="textareaRef"
      v-model="localValue"
      :placeholder="placeholder"
      :readonly="readonly"
      class="code-textarea"
      @input="handleInput"
      @keydown="handleKeydown"
    ></textarea>
  </div>
</template>

<script setup>
import { ref, watch, nextTick } from 'vue'

/**
 * 迷你代码编辑器组件属性
 */
const props = defineProps({
  modelValue: {
    type: String,
    default: ''
  },
  language: {
    type: String,
    default: 'sql',
    validator: (value) => ['javascript', 'python', 'sql', 'shell', 'bash'].includes(value)
  },
  height: {
    type: String,
    default: '120px'
  },
  readonly: {
    type: Boolean,
    default: false
  },
  placeholder: {
    type: String,
    default: ''
  }
})

/**
 * 组件事件
 */
const emit = defineEmits(['update:modelValue'])

// 组件状态
const textareaRef = ref(null)
const localValue = ref(props.modelValue || '')

/**
 * 处理输入事件
 */
const handleInput = () => {
  emit('update:modelValue', localValue.value)
}

/**
 * 处理键盘事件，添加基本的代码编辑功能
 */
const handleKeydown = (event) => {
  // Tab键缩进
  if (event.key === 'Tab') {
    event.preventDefault()
    const start = event.target.selectionStart
    const end = event.target.selectionEnd
    const value = event.target.value
    
    // 插入两个空格作为缩进
    const newValue = value.substring(0, start) + '  ' + value.substring(end)
    localValue.value = newValue
    
    nextTick(() => {
      event.target.selectionStart = event.target.selectionEnd = start + 2
    })
  }
  
  // Enter键自动缩进
  if (event.key === 'Enter') {
    const start = event.target.selectionStart
    const value = event.target.value
    const lines = value.substring(0, start).split('\n')
    const currentLine = lines[lines.length - 1]
    
    // 计算当前行的缩进
    const indent = currentLine.match(/^\s*/)[0]
    
    setTimeout(() => {
      const newStart = event.target.selectionStart
      const newValue = event.target.value
      const beforeCursor = newValue.substring(0, newStart)
      const afterCursor = newValue.substring(newStart)
      
      localValue.value = beforeCursor + indent + afterCursor
      
      nextTick(() => {
        event.target.selectionStart = event.target.selectionEnd = newStart + indent.length
      })
    }, 0)
  }
}

// 监听 modelValue 变化
watch(() => props.modelValue, (newValue) => {
  if (newValue !== localValue.value) {
    localValue.value = newValue || ''
  }
})
</script>

<style scoped>
.mini-code-editor {
  border: 1px solid #dcdfe6;
  border-radius: 4px;
  overflow: hidden;
}

.code-textarea {
  width: 100%;
  height: v-bind(height);
  border: none;
  outline: none;
  resize: none;
  padding: 8px 12px;
  font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
  font-size: 13px;
  line-height: 1.4;
  background: #fafafa;
  color: #333;
  tab-size: 2;
}

.code-textarea:focus {
  background: #fff;
}

.mini-code-editor:hover {
  border-color: #c0c4cc;
}

.mini-code-editor:focus-within {
  border-color: #409eff;
}

.code-textarea::placeholder {
  color: #c0c4cc;
  font-style: italic;
}

/* SQL语法高亮样式（简单版本） */
.mini-code-editor[data-language="sql"] .code-textarea {
  color: #0066cc;
}
</style>