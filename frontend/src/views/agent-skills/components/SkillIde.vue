<template>
  <div class="ide-container">
    <!-- Left Sidebar: File Tree -->
    <div class="ide-sidebar">
      <div class="sidebar-toolbar">
        <span class="sidebar-title">资源管理器</span>
        <div class="sidebar-actions">
          <el-tooltip content="新建文件">
            <el-button link :icon="DocumentAdd" @click="handleAddFile" size="small" />
          </el-tooltip>
          <el-tooltip content="新建文件夹">
            <el-button link :icon="FolderAdd" @click="handleAddFolder" size="small" />
          </el-tooltip>
          <el-tooltip content="折叠所有">
            <el-button link :icon="Operation" @click="handleCollapseAll" size="small" />
          </el-tooltip>
        </div>
      </div>
      
      <div class="file-tree-wrapper">
        <el-tree
          ref="treeRef"
          :data="fileTreeData"
          node-key="path"
          :expand-on-click-node="false"
          highlight-current
          @node-click="handleNodeClick"
          empty-text="暂无文件"
        >
          <template #default="{ node, data }">
            <div class="custom-tree-node" @contextmenu.prevent="handleContextMenu($event, data)">
              <el-icon v-if="data.isDir" class="node-icon"><Folder /></el-icon>
              <el-icon v-else class="node-icon"><Document /></el-icon>
              <span class="node-label">{{ node.label }}</span>
              
              <div class="node-actions" v-if="!readonly">
                 <el-icon @click.stop="handleRename(data)" title="重命名"><Edit /></el-icon>
                 <el-icon @click.stop="handleDelete(data)" title="删除" class="delete-icon"><Delete /></el-icon>
              </div>
            </div>
          </template>
        </el-tree>
      </div>
    </div>

    <!-- Right Main: Editor Area -->
    <div class="ide-main">
      <!-- Tabs -->
      <div class="editor-tabs" v-if="openFiles.length > 0">
        <div 
          v-for="file in openFiles" 
          :key="file"
          class="editor-tab"
          :class="{ active: currentFile === file }"
          @click="switchFile(file)"
        >
          <el-icon class="tab-icon"><Document /></el-icon>
          <span class="tab-name">{{ getFileName(file) }}</span>
          <el-icon class="close-icon" @click.stop="closeFile(file)"><Close /></el-icon>
        </div>
      </div>
      
      <!-- Editor -->
      <div class="monaco-wrapper" v-show="currentFile">
        <div ref="monacoContainer" class="monaco-container"></div>
      </div>
      
      <!-- Empty State -->
      <div v-if="!currentFile" class="empty-state">
        <el-empty description="选择或新建文件以开始编辑" />
      </div>
    </div>

    <!-- Dialogs -->
    <el-dialog v-model="dialogVisible" :title="dialogTitle" width="400px">
      <el-form @submit.prevent="confirmDialog">
        <el-form-item label="名称">
           <el-input 
             v-model="dialogInput" 
             placeholder="请输入名称" 
             ref="dialogInputRef" 
             @keyup.enter="confirmDialog"
           >
             <template #prepend v-if="dialogType === 'create' && selectedDir">{{ selectedDir }}/</template>
           </el-input>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="confirmDialog">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onBeforeUnmount, watch, nextTick, shallowRef } from 'vue'
import { DocumentAdd, FolderAdd, Delete, Folder, Document, Edit, Close, Operation } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import loader from '@monaco-editor/loader'

const props = defineProps<{
  modelValue: Record<string, string>
  readonly?: boolean
}>()

const emit = defineEmits<{
  (e: 'update:modelValue', value: Record<string, string>): void
  (e: 'save'): void
}>()

// --- State ---
const treeRef = ref()
const monacoContainer = ref()
const editor = shallowRef<any>(null)
const openFiles = ref<string[]>([])
const currentFile = ref<string>('')
const selectedDir = ref<string>('') // For creating new files

// Dialog State
const dialogVisible = ref(false)
const dialogType = ref<'create' | 'rename'>('create')
const createType = ref<'file' | 'folder'>('file')
const dialogInput = ref('')
const dialogInputRef = ref()
const editingNode = ref<any>(null)

// --- Computed ---
const dialogTitle = computed(() => {
  if (dialogType.value === 'rename') return '重命名'
  return createType.value === 'file' ? '新建文件' : '新建文件夹'
})

interface TreeNode {
  label: string
  path: string
  isDir: boolean
  children?: TreeNode[]
}

const fileTreeData = computed(() => {
  const paths = Object.keys(props.modelValue).sort()
  const root: TreeNode[] = []

  paths.forEach(path => {
    const parts = path.split('/')
    let currentLevel = root
    let currentPath = ''

    parts.forEach((part, index) => {
      const isLast = index === parts.length - 1
      currentPath = currentPath ? `${currentPath}/${part}` : part
      
      let existingNode = currentLevel.find(node => node.label === part)
      
      if (!existingNode) {
        existingNode = {
          label: part,
          path: currentPath,
          isDir: !isLast, 
          children: []
        }
        // If it is in fileMap, it's a file, unless strictly used as dir structure
        // But here we treat keys in modelValue as files.
        if (isLast) {
             existingNode.isDir = false
             delete existingNode.children
        } else {
             existingNode.isDir = true
        }
        currentLevel.push(existingNode)
      }
      
      if (!isLast && existingNode.children) {
        currentLevel = existingNode.children
      }
    })
  })
  
  // Sort: Directories first, then files
  const sortNodes = (nodes: TreeNode[]) => {
      nodes.sort((a, b) => {
          if (a.isDir === b.isDir) return a.label.localeCompare(b.label)
          return a.isDir ? -1 : 1
      })
      nodes.forEach(node => {
          if (node.children) sortNodes(node.children)
      })
  }
  sortNodes(root)
  return root
})

// --- Methods ---

const getFileName = (path: string) => path.split('/').pop()

const handleNodeClick = (data: TreeNode) => {
  if (data.isDir) {
    selectedDir.value = data.path
  } else {
    // It's a file
    const parts = data.path.split('/')
    parts.pop()
    selectedDir.value = parts.join('/')
    
    openFile(data.path)
  }
}

const openFile = (path: string) => {
  if (!openFiles.value.includes(path)) {
    openFiles.value.push(path)
  }
  switchFile(path)
}

const switchFile = (path: string) => {
  currentFile.value = path
  updateEditorContent()
}

const closeFile = (path: string) => {
  const idx = openFiles.value.indexOf(path)
  if (idx > -1) {
    openFiles.value.splice(idx, 1)
  }
  if (currentFile.value === path) {
    // Switch to another file
    if (openFiles.value.length > 0) {
      switchFile(openFiles.value[openFiles.value.length - 1])
    } else {
      currentFile.value = ''
    }
  }
}

const handleCollapseAll = () => {
    // Element Plus Tree doesn't expose collapseAll easily without iterating nodes
    // But we can just set currentKey to null to collapse logic if we had v-if
    // Actually, simple hack:
    const nodes = treeRef.value?.store.nodesMap
    if (nodes) {
        Object.values(nodes).forEach((n: any) => n.expanded = false)
    }
}

// File Operations
const handleAddFile = () => {
  if (props.readonly) return
  dialogType.value = 'create'
  createType.value = 'file'
  dialogInput.value = ''
  dialogVisible.value = true
  nextTick(() => dialogInputRef.value?.focus())
}

const handleAddFolder = () => {
  if (props.readonly) return
  dialogType.value = 'create'
  createType.value = 'folder'
  dialogInput.value = ''
  dialogVisible.value = true
  nextTick(() => dialogInputRef.value?.focus())
}

const handleRename = (data: TreeNode) => {
  if (props.readonly) return
  dialogType.value = 'rename'
  editingNode.value = data
  dialogInput.value = data.label
  dialogVisible.value = true
  nextTick(() => dialogInputRef.value?.focus())
}

const handleDelete = (data: TreeNode) => {
  if (props.readonly) return
  ElMessageBox.confirm(`确定删除 ${data.label} 吗？`, '提示', {
    type: 'warning'
  }).then(() => {
    const newMap = { ...props.modelValue }
    
    if (data.isDir) {
       // Delete dir prefix
       const prefix = data.path + '/'
       Object.keys(newMap).forEach(key => {
           if (key === data.path || key.startsWith(prefix)) {
               delete newMap[key]
           }
       })
    } else {
       delete newMap[data.path]
    }
    
    emit('update:modelValue', newMap)
    
    // Close tabs if deleted
    if (!data.isDir) {
        closeFile(data.path)
    } else {
        openFiles.value.forEach(f => {
            if (f.startsWith(data.path + '/')) closeFile(f)
        })
    }
  })
}

const confirmDialog = () => {
  if (!dialogInput.value.trim()) return
  
  const newMap = { ...props.modelValue }
  
  if (dialogType.value === 'create') {
      let fullPath = selectedDir.value 
        ? `${selectedDir.value}/${dialogInput.value}` 
        : dialogInput.value
      
      if (createType.value === 'folder') {
          // Folder placeholder
          fullPath += '/.keep'
      }
      
      if (newMap[fullPath]) {
          ElMessage.warning('文件已存在')
          return
      }
      
      newMap[fullPath] = ''
      emit('update:modelValue', newMap)
      
      if (createType.value === 'file') {
          openFile(fullPath)
      }
  } else {
      // Rename
      const oldPath = editingNode.value.path
      const pathParts = oldPath.split('/')
      pathParts.pop() // remove old name
      const basePath = pathParts.join('/')
      const newPath = basePath ? `${basePath}/${dialogInput.value}` : dialogInput.value
      
      // We need to rename all keys starting with oldPath
      const keys = Object.keys(newMap)
      const updates: Record<string, string> = {}
      let hasUpdate = false
      
      keys.forEach(key => {
          if (key === oldPath || key.startsWith(oldPath + '/')) {
              const suffix = key.slice(oldPath.length)
              const dest = newPath + suffix
              updates[dest] = newMap[key]
              delete newMap[key]
              hasUpdate = true
              
              // Update open files
              const idx = openFiles.value.indexOf(key)
              if (idx > -1) {
                  openFiles.value[idx] = dest
              }
              if (currentFile.value === key) {
                  currentFile.value = dest
              }
          }
      })
      
      if (hasUpdate) {
          Object.assign(newMap, updates)
          emit('update:modelValue', newMap)
      }
  }
  
  dialogVisible.value = false
}

// Monaco Editor Logic
const initMonaco = async () => {
  if (!monacoContainer.value) return
  
  const monaco = await loader.init()
  
  editor.value = monaco.editor.create(monacoContainer.value, {
    value: '',
    language: 'plaintext',
    theme: 'vs-dark',
    automaticLayout: true,
    minimap: { enabled: true },
    scrollBeyondLastLine: false,
    fontSize: 14,
    fontFamily: "'Fira Code', 'Consolas', monospace",
  })
  
  editor.value.onDidChangeModelContent(() => {
    if (currentFile.value) {
        const val = editor.value.getValue()
        // Only update if changed
        if (props.modelValue[currentFile.value] !== val) {
            const newMap = { ...props.modelValue }
            newMap[currentFile.value] = val
            emit('update:modelValue', newMap)
        }
    }
  })
  
  // Bind Ctrl+S
  editor.value.addCommand(monaco.KeyMod.CtrlCmd | monaco.KeyCode.KeyS, () => {
      emit('save')
  })
}

const updateEditorContent = () => {
  if (!editor.value) return
  if (!currentFile.value) return
  
  const content = props.modelValue[currentFile.value] || ''
  const model = editor.value.getModel()
  
  if (model) {
      if (model.getValue() !== content) {
          // Preserve cursor position if possible? No, full replace for simplicity for now.
          // Or use pushEditOperations to be smoother?
          // Since we are the source of truth, setValue is fine.
          editor.value.setValue(content)
      }
      
      // Set language
      const ext = currentFile.value.split('.').pop()?.toLowerCase()
      let lang = 'plaintext'
      const langMap: Record<string, string> = {
          'md': 'markdown',
          'py': 'python',
          'js': 'javascript',
          'ts': 'typescript',
          'json': 'json',
          'yaml': 'yaml',
          'yml': 'yaml',
          'html': 'html',
          'css': 'css',
          'sql': 'sql',
          'sh': 'shell'
      }
      if (ext && langMap[ext]) lang = langMap[ext]
      
      const monaco = (window as any).monaco
      if (monaco) {
          monaco.editor.setModelLanguage(model, lang)
      }
  }
}

watch(() => props.modelValue, (newVal) => {
    // If external update (e.g. AI generation), refresh editor
    if (currentFile.value && editor.value) {
        const content = newVal[currentFile.value]
        if (content !== undefined && content !== editor.value.getValue()) {
             editor.value.setValue(content)
        }
    }
}, { deep: true })

onMounted(() => {
  initMonaco()
})

onBeforeUnmount(() => {
  if (editor.value) {
    editor.value.dispose()
  }
})

// Expose openFile to parent if needed (via template ref)
defineExpose({
    openFile
})

</script>

<style scoped>
.ide-container {
  display: flex;
  width: 100%;
  height: 100%;
  border: 1px solid #dcdfe6;
  background-color: #fff;
  overflow: hidden;
}

.ide-sidebar {
  width: 250px;
  border-right: 1px solid #dcdfe6;
  display: flex;
  flex-direction: column;
  background-color: #f5f7fa;
  flex-shrink: 0;
}

.sidebar-toolbar {
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 10px;
  border-bottom: 1px solid #e4e7ed;
  background-color: #f5f7fa;
}

.sidebar-title {
  font-size: 12px;
  font-weight: bold;
  color: #606266;
  text-transform: uppercase;
}

.file-tree-wrapper {
  flex: 1;
  overflow-y: auto;
}

.custom-tree-node {
  display: flex;
  align-items: center;
  width: 100%;
  padding-right: 8px;
  font-size: 13px;
}

.node-icon {
  margin-right: 6px;
  color: #909399;
}

.node-label {
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.node-actions {
  display: none;
}

.custom-tree-node:hover .node-actions {
  display: flex;
  gap: 4px;
}

.node-actions .el-icon {
  cursor: pointer;
  color: #909399;
  font-size: 14px;
}

.node-actions .el-icon:hover {
  color: #409eff;
}

.node-actions .delete-icon:hover {
  color: #f56c6c;
}

.ide-main {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  background-color: #1e1e1e; /* VS Code dark bg */
}

.editor-tabs {
  display: flex;
  background-color: #252526;
  overflow-x: auto;
  height: 35px;
  flex-shrink: 0;
}

.editor-tabs::-webkit-scrollbar {
  height: 4px;
}
.editor-tabs::-webkit-scrollbar-thumb {
  background: #424242;
}

.editor-tab {
  display: flex;
  align-items: center;
  padding: 0 10px;
  color: #969696;
  background-color: #2d2d2d;
  cursor: pointer;
  border-right: 1px solid #252526;
  font-size: 13px;
  user-select: none;
  min-width: 100px;
  max-width: 200px;
}

.editor-tab:hover {
  background-color: #2a2d2e;
  color: #cfcfcf;
}

.editor-tab.active {
  background-color: #1e1e1e;
  color: #ffffff;
  border-top: 1px solid #007fd4;
}

.tab-icon {
  margin-right: 6px;
  font-size: 14px;
}

.tab-name {
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  margin-right: 6px;
}

.close-icon {
  font-size: 12px;
  border-radius: 3px;
  padding: 2px;
}

.close-icon:hover {
  background-color: #4d4d4d;
  color: #fff;
}

.monaco-wrapper {
  flex: 1;
  overflow: hidden;
  position: relative;
}

.monaco-container {
  width: 100%;
  height: 100%;
}

.empty-state {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: #1e1e1e;
}
</style>
