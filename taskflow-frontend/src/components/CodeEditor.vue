<template>
  <div class="code-editor-overlay" v-if="visible" @click.self="handleClose">
    <div class="code-editor-container">
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
        <div ref="editorContainer" class="monaco-editor-container"></div>
      </div>
      <div class="editor-footer">
        <div class="editor-info">
          <span>语言: {{ languageDisplay }}</span>
          <span>行数: {{ lineCount }}</span>
          <span>字符数: {{ charCount }}</span>
        </div>
        <div class="editor-tips">
          <el-text size="small" type="info">
            提示: Ctrl+S 保存, Ctrl+F 查找, Ctrl+H 替换, F11 全屏
          </el-text>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch, nextTick } from 'vue'
import * as monaco from 'monaco-editor'
import { Edit, MagicStick, FullScreen, Check, Close } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'

/**
 * 代码编辑器组件属性
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
  }
})

/**
 * 组件事件
 */
const emit = defineEmits(['update:modelValue', 'save', 'close'])

// 编辑器相关状态
const editorContainer = ref(null)
const editor = ref(null)
const monacoRef = ref(null)
const isFullscreen = ref(false)
const lineCount = ref(0)
const charCount = ref(0)
const isUpdatingFromProps = ref(false) // 标志：是否正在从props更新内容

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
 * 防抖函数
 * @param {Function} func - 要防抖的函数
 * @param {number} delay - 延迟时间（毫秒）
 * @returns {Function} 防抖后的函数
 */
const debounce = (func, delay) => {
  let timeoutId
  return (...args) => {
    clearTimeout(timeoutId)
    timeoutId = setTimeout(() => func.apply(null, args), delay)
  }
}

/**
 * 初始化 Monaco Editor - 极简版本
 */
const initEditor = async () => {
  // 防护检查：确保容器存在且编辑器未初始化
  if (!editorContainer.value || editor.value) {
    return
  }

  try {
    console.log('CodeEditor: 开始极简初始化')
    
    // 配置 Monaco Editor 的 Web Worker - 完全禁用避免MIME错误
    if (typeof window !== 'undefined') {
      window.MonacoEnvironment = {
        getWorker: function (workerId, label) {
          console.log('Monaco Worker 请求被禁用:', { workerId, label })
          // 完全禁用Web Worker，强制使用主线程
          return null
        }
      }
      console.log('CodeEditor: Web Worker 已完全禁用 - 主线程模式')
    }
    
    // 直接使用monaco，避免loader的复杂性
    const monacoInstance = monaco
    monacoRef.value = monacoInstance
    
    // 创建编辑器实例 - 性能优化配置
    editor.value = monacoInstance.editor.create(editorContainer.value, {
      value: props.modelValue || '',
      language: props.language || 'javascript',
      theme: 'vs-dark',
      fontSize: 14,
      readOnly: props.readonly,
      minimap: { enabled: false },
      automaticLayout: false, // 禁用自动布局
      // 性能优化配置
      wordWrap: 'off', // 禁用自动换行
      scrollBeyondLastLine: false, // 禁用滚动到最后一行之后
      renderLineHighlight: 'none', // 禁用行高亮
      renderWhitespace: 'none', // 禁用空白字符渲染
      renderControlCharacters: false, // 禁用控制字符渲染
      renderIndentGuides: false, // 禁用缩进指南
      codeLens: false, // 禁用代码镜头
      folding: false, // 禁用代码折叠
      links: false, // 禁用链接检测
      colorDecorators: false, // 禁用颜色装饰器
      lightbulb: { enabled: false }, // 禁用灯泡提示
      quickSuggestions: false, // 禁用快速建议
      suggestOnTriggerCharacters: false, // 禁用触发字符建议
      acceptSuggestionOnEnter: 'off', // 禁用回车接受建议
      tabCompletion: 'off', // 禁用Tab补全
      wordBasedSuggestions: false, // 禁用基于单词的建议
      parameterHints: { enabled: false }, // 禁用参数提示
      hover: { enabled: false }, // 禁用悬停提示
      contextmenu: false, // 禁用右键菜单
      mouseWheelZoom: false, // 禁用鼠标滚轮缩放
      smoothScrolling: false, // 禁用平滑滚动
      cursorBlinking: 'solid', // 使用实心光标
      cursorSmoothCaretAnimation: false, // 禁用光标动画
      fastScrollSensitivity: 1, // 快速滚动敏感度
      scrollbar: {
        vertical: 'auto',
        horizontal: 'auto',
        useShadows: false, // 禁用滚动条阴影
        verticalHasArrows: false,
        horizontalHasArrows: false
      }
    })
    
    // 初始化缓存内容
    if (props.modelValue) {
      lastKnownContent = props.modelValue
      console.log('CodeEditor: 初始化缓存内容，长度:', lastKnownContent.length)
    }
    
    // 使用防抖的内容变化监听，避免频繁触发
    console.log('CodeEditor: 设置防抖内容变化监听')
    
    let contentChangeTimeout = null
    
    editor.value.onDidChangeModelContent(() => {
       console.log('CodeEditor: 内容变化事件触发，isUpdatingFromProps:', isUpdatingFromProps.value)
       if (!isUpdatingFromProps.value) {
         // 清除之前的定时器，实现防抖
         if (contentChangeTimeout) {
           clearTimeout(contentChangeTimeout)
         }
         
         // 设置新的定时器，增加防抖延迟到500ms避免卡顿
          contentChangeTimeout = setTimeout(() => {
            try {
              // 更健壮的编辑器状态检查
              if (editor.value && typeof editor.value.getModel === 'function') {
                const model = editor.value.getModel()
                if (model && typeof model.getValue === 'function') {
                  const content = model.getValue() || ''
                  // 更新缓存内容
                  lastKnownContent = content
                  emit('update:modelValue', content)
                  console.log('CodeEditor: 发射update:modelValue事件，内容长度:', content.length)
                }
              }
            } catch (error) {
              console.warn('CodeEditor: 防抖内容获取失败:', error)
            }
            contentChangeTimeout = null
          }, 500)
       } else {
         console.log('CodeEditor: 跳过内容变化事件，正在从props更新')
       }
     })
     
     // 添加键盘事件监听，防止特定按键导致问题
     editor.value.onKeyDown((e) => {
       try {
         // 对回车键进行特殊处理
         if (e.keyCode === 13) { // Enter key
           console.log('CodeEditor: 检测到回车键')
           // 不阻止默认行为，但确保编辑器状态正常
            if (!editor.value || typeof editor.value.getModel !== 'function') {
              console.warn('CodeEditor: 编辑器状态异常，忽略回车键事件')
              e.preventDefault()
            }
         }
       } catch (error) {
         console.warn('CodeEditor: 键盘事件处理失败:', error)
       }
     })
    
    // 延迟初始化布局，避免死机
     console.log('CodeEditor: 延迟初始化布局')
     setTimeout(() => {
       try {
         if (editor.value && typeof editor.value.layout === 'function') {
           editor.value.layout()
           console.log('CodeEditor: 延迟布局完成')
         }
       } catch (error) {
         console.warn('CodeEditor: 延迟布局失败:', error)
       }
     }, 300) // 300ms 延迟  
    console.log('CodeEditor: 初始化完成')
  } catch (error) {
    console.error('CodeEditor: 初始化失败', error)
    if (editor.value) {
      try {
        editor.value.dispose()
      } catch (disposeError) {
        console.error('CodeEditor: 清理编辑器失败', disposeError)
      }
      editor.value = null
    }
  }
 }

/**
 * 更新统计信息 - 防死机版本
 */
const updateStats = () => {
  // 暂时禁用统计更新以避免死机
  console.log('CodeEditor: updateStats 被跳过 - 防死机模式')
  // 如果需要统计信息，可以考虑使用更简单的方式
  
  // try {
  //   if (editor.value) {
  //     const model = editor.value.getModel()
  //     if (model && !model.isDisposed) {
  //       lineCount.value = model.getLineCount()
  //       charCount.value = model.getValueLength()
  //     }
  //   }
  // } catch (error) {
  //   console.error('CodeEditor: updateStats 失败:', error)
  // }
}


/**
 * 格式化代码
 */
const handleFormat = async () => {
  if (!editor.value) return
  
  try {
    // 获取当前语言
    const model = editor.value.getModel()
    const language = model ? model.getLanguageId() : props.language
    
    console.log('开始格式化代码，语言:', language)
    
    // 对于SQL，暂时禁用格式化功能以避免卡死
    if (language === 'sql') {
      ElMessage.warning('SQL格式化功能暂时禁用，避免页面卡死')
      return
    }
    
    // 对于其他语言，使用Monaco内置格式化
    await editor.value.getAction('editor.action.formatDocument').run()
    ElMessage.success('代码格式化完成')
  } catch (error) {
    console.warn('格式化失败:', error)
    ElMessage.warning('当前语言不支持自动格式化')
  }
}

/**
 * 格式化SQL代码
 * @param {string} sql - 原始SQL代码
 * @returns {string} 格式化后的SQL代码
 */
const formatSqlCode = (sql) => {
  if (!sql || typeof sql !== 'string') return sql
  
  try {
    // 简单的格式化：只处理基本的大小写和换行
    let formatted = sql.trim()
    
    // 将常见的SQL关键字转换为大写（使用简单的字符串替换）
    const keywords = ['select', 'from', 'where', 'insert', 'update', 'delete', 'create', 'alter', 'drop']
    
    keywords.forEach(keyword => {
      // 使用简单的字符串替换，避免复杂正则表达式
      const upperKeyword = keyword.toUpperCase()
      // 替换小写版本
      formatted = formatted.split(' ' + keyword + ' ').join(' ' + upperKeyword + ' ')
      formatted = formatted.split('\n' + keyword + ' ').join('\n' + upperKeyword + ' ')
      // 处理开头的情况
      if (formatted.toLowerCase().startsWith(keyword + ' ')) {
        formatted = upperKeyword + formatted.substring(keyword.length)
      }
    })
    
    return formatted
  } catch (error) {
    console.error('SQL格式化出错:', error)
    return sql // 出错时返回原始SQL
  }
}

/**
 * 切换全屏模式 - 极简版本，避免 layout() 调用
 */
const handleFullscreen = () => {
  console.log('CodeEditor: handleFullscreen 开始执行 - 极简模式')
  try {
    console.log('CodeEditor: 切换全屏状态，当前状态:', isFullscreen.value)
    isFullscreen.value = !isFullscreen.value
    console.log('CodeEditor: 全屏状态已切换为:', isFullscreen.value)
    
    // 暂时跳过 layout 调用以避免死机
    console.log('CodeEditor: 跳过 layout 调用 - 防死机模式')
    // nextTick(() => {
    //   try {
    //     if (editor.value) {
    //       editor.value.layout()
    //     }
    //   } catch (layoutError) {
    //     console.error('CodeEditor: layout 执行失败:', layoutError)
    //   }
    // })
    
    console.log('CodeEditor: handleFullscreen 执行完成')
  } catch (error) {
    console.error('CodeEditor: handleFullscreen 执行失败:', error)
  }
}

/**
 * 保存代码 - 完全避免编辑器API调用，使用缓存内容
 */
let lastKnownContent = ''

const handleSave = () => {
  console.log('CodeEditor: handleSave 开始执行 - 安全模式')
  try {
    // 优先使用最后已知的内容，避免任何编辑器API调用
    const valueToSave = lastKnownContent || props.modelValue || ''
    console.log('CodeEditor: 使用缓存内容保存，长度:', valueToSave.length)
    
    // 同时触发保存事件和更新父组件的v-model
    emit('update:modelValue', valueToSave)
    emit('save', valueToSave)
    ElMessage.success('代码已保存')
    
    console.log('CodeEditor: handleSave 执行完成，内容已同步到父组件')
  } catch (error) {
    console.error('CodeEditor: handleSave 执行失败:', error)
    ElMessage.error('保存失败: ' + error.message)
  }
}

/**
 * 关闭编辑器
 */
const handleClose = () => {
  console.log('CodeEditor: handleClose 开始执行')
  try {
    console.log('CodeEditor: 触发 close 事件')
    emit('close')
    console.log('CodeEditor: close 事件已触发')
    console.log('CodeEditor: handleClose 执行完成')
  } catch (error) {
    console.error('CodeEditor: handleClose 执行失败:', error)
  }
}

/**
 * 极简清理编辑器实例 - 避免复杂的 dispose 调用
 */
const cleanupEditor = () => {
  console.log('CodeEditor: 开始极简清理编辑器')
  try {
    // 直接清理引用，避免调用可能有问题的 dispose 方法
    editor.value = null
    monacoRef.value = null
    console.log('CodeEditor: 编辑器引用已清理')
  } catch (error) {
    console.error('CodeEditor: 清理编辑器时出错', error)
  }
}

/**
 * 监听 visible 变化
 */
watch(() => props.visible, (newVal) => {
  console.log('CodeEditor: visible 变化监听器触发，新值:', newVal)
  if (newVal) {
    // 确保编辑器容器存在且编辑器未初始化
    nextTick(() => {
      if (!editor.value && editorContainer.value) {
        console.log('CodeEditor: visible 变化触发初始化')
        initEditor()
      } else if (editor.value) {
        console.log('CodeEditor: 编辑器已存在，执行布局调整')
        try {
          editor.value.layout()
          updateStats()
        } catch (error) {
          console.error('CodeEditor: 布局调整失败', error)
        }
      }
    })
  } else {
    // 清理编辑器实例
    console.log('CodeEditor: visible 为 false，开始清理编辑器')
    cleanupEditor()
    console.log('CodeEditor: visible 变化处理完成')
  }
})

/**
 * 监听 modelValue 变化 - 防死机版本
 */
watch(() => props.modelValue, (newVal) => {
  if (editor.value && newVal !== undefined) {
    console.log('CodeEditor: modelValue 变化，准备更新编辑器内容 - 防死机模式')
    
    // 使用异步更新避免阻塞
    setTimeout(() => {
      try {
        if (editor.value && typeof editor.value.getModel === 'function') {
          const model = editor.value.getModel()
          if (model && typeof model.getValue === 'function') {
            isUpdatingFromProps.value = true
            if (typeof editor.value.setValue === 'function') {
              editor.value.setValue(newVal || '')
              // 同步更新缓存内容
              lastKnownContent = newVal || ''
              console.log('CodeEditor: 编辑器内容异步更新完成')
            }
            
            // 重置标志位 - 缩短延迟时间，避免阻塞用户输入
            setTimeout(() => {
              isUpdatingFromProps.value = false
            }, 50)
          } else {
            console.warn('CodeEditor: 编辑器模型无效，跳过更新')
          }
        }
      } catch (error) {
        console.error('CodeEditor: 异步更新编辑器内容失败:', error)
        isUpdatingFromProps.value = false
      }
    }, 20) // 20ms 延迟
  }
})

/**
 * 监听语言变化
 */
watch(() => props.language, (newVal) => {
  if (editor.value && monacoRef.value) {
    const model = editor.value.getModel()
    if (model) {
      monacoRef.value.editor.setModelLanguage(model, newVal)
    }
  }
})

/**
 * 组件卸载时清理
 */
onUnmounted(() => {
  console.log('CodeEditor: 组件卸载，开始清理')
  cleanupEditor()
  console.log('CodeEditor: 组件卸载清理完成')
})
</script>

<style scoped>
.code-editor-overlay {
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

.code-editor-container {
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

.monaco-editor-container {
  width: 100%;
  height: 100%;
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
  .code-editor-container {
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
}
</style>