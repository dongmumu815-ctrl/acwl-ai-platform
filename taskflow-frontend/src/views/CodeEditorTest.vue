<template>
  <div class="code-editor-test">
    <div class="test-header">
      <h2>代码编辑器测试页面</h2>
      <p>测试 Monaco Editor 功能</p>
    </div>
    
    <div class="test-buttons">
      <el-button @click="testPythonEditor" type="primary">
        测试 Python 编辑器
      </el-button>
      <el-button @click="testShellEditor" type="success">
        测试 Shell 编辑器
      </el-button>
      <el-button @click="testSqlEditor" type="warning">
        测试 SQL 编辑器
      </el-button>
      <el-button @click="closeEditor" type="danger" v-if="editorVisible">
        关闭编辑器
      </el-button>
      <el-button @click="checkMonaco" type="info">
        检查 Monaco 状态
      </el-button>
    </div>

    <div class="test-info">
      <p>当前编辑器状态: {{ editorVisible ? '显示' : '隐藏' }}</p>
      <p>当前语言: {{ currentLanguage }}</p>
      <p>当前标题: {{ currentTitle }}</p>
      <p>Monaco Editor 加载状态: {{ monacoStatus }}</p>
    </div>

    <!-- 代码编辑器组件 -->
    <AdvancedCodeEditor
      v-model="editorContent"
      :visible="editorVisible"
      :language="currentLanguage"
      :title="currentTitle"
      @save="handleSave"
      @close="handleClose"
    />
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import AdvancedCodeEditor from '@/components/AdvancedCodeEditor.vue'

// 代码编辑器状态
const editorVisible = ref(false)
const editorContent = ref('')
const currentLanguage = ref('python')
const currentTitle = ref('代码编辑器')
const currentContent = ref('')
const monacoStatus = ref('检查中...')

/**
 * 检查 Monaco Editor 状态
 */
const checkMonaco = () => {
  try {
    // 检查 Monaco 是否已加载
    if (typeof window.monaco !== 'undefined') {
      monacoStatus.value = '✅ Monaco Editor 已加载'
      console.log('Monaco Editor 版本:', window.monaco.editor.VERSION || 'unknown')
      console.log('Monaco Editor 对象:', window.monaco)
    } else {
      monacoStatus.value = '❌ Monaco Editor 未加载'
    }
  } catch (error) {
    monacoStatus.value = '❌ 检查失败: ' + error.message
    console.error('Monaco 检查错误:', error)
  }
}

/**
 * 测试 Python 编辑器
 */
const testPythonEditor = () => {
  console.log('测试 Python 编辑器')
  currentLanguage.value = 'python'
  currentTitle.value = 'Python 代码编辑器'
  editorContent.value = `# Python 示例代码
import pandas as pd
import numpy as np

def process_data(data):
    """处理数据的函数"""
    df = pd.DataFrame(data)
    result = df.groupby('category').sum()
    return result.to_dict()

# 主程序
if __name__ == "__main__":
    sample_data = [
        {'category': 'A', 'value': 10},
        {'category': 'B', 'value': 20},
        {'category': 'A', 'value': 15}
    ]
    
    result = process_data(sample_data)
    print(f"处理结果: {result}")`
  editorVisible.value = true
  console.log('编辑器应该显示了:', editorVisible.value)
}

/**
 * 测试 Shell 编辑器
 */
const testShellEditor = () => {
  console.log('测试 Shell 编辑器')
  currentLanguage.value = 'shell'
  currentTitle.value = 'Shell 脚本编辑器'
  editorContent.value = `#!/bin/bash

# Shell 脚本示例
echo "开始执行脚本..."

# 设置变量
LOG_FILE="/var/log/app.log"
BACKUP_DIR="/backup"

# 创建备份目录
if [ ! -d "$BACKUP_DIR" ]; then
    mkdir -p "$BACKUP_DIR"
    echo "创建备份目录: $BACKUP_DIR"
fi

# 备份日志文件
if [ -f "$LOG_FILE" ]; then
    cp "$LOG_FILE" "$BACKUP_DIR/app_$(date +%Y%m%d_%H%M%S).log"
    echo "日志文件已备份"
else
    echo "警告: 日志文件不存在"
fi

echo "脚本执行完成"`
  editorVisible.value = true
}

/**
 * 测试 SQL 编辑器
 */
const testSqlEditor = () => {
  console.log('测试 SQL 编辑器')
  currentLanguage.value = 'sql'
  currentTitle.value = 'SQL 查询编辑器'
  editorContent.value = `-- SQL 查询示例
-- 查询用户订单统计信息

SELECT 
    u.user_id,
    u.username,
    u.email,
    COUNT(o.order_id) as total_orders,
    SUM(o.total_amount) as total_spent,
    AVG(o.total_amount) as avg_order_value,
    MAX(o.created_at) as last_order_date
FROM 
    users u
LEFT JOIN 
    orders o ON u.user_id = o.user_id
WHERE 
    u.status = 'active'
    AND u.created_at >= '2024-01-01'
GROUP BY 
    u.user_id, u.username, u.email
HAVING 
    COUNT(o.order_id) > 0
ORDER BY 
    total_spent DESC, total_orders DESC
LIMIT 100;`
  editorVisible.value = true
}

/**
 * 关闭编辑器
 */
const closeEditor = () => {
  editorVisible.value = false
  ElMessage.info('编辑器已关闭')
}

/**
 * 保存代码编辑器内容
 * @param {string} content - 编辑器内容
 */
const handleSave = (content) => {
  currentContent.value = content
  ElMessage.success('代码已保存')
  console.log('保存的代码:', content)
}

/**
 * 关闭代码编辑器
 */
const handleClose = () => {
  editorVisible.value = false
}

// 组件挂载时检查 Monaco 状态
onMounted(() => {
  checkMonaco()
})
</script>

<style scoped>
.code-editor-test {
  padding: 20px;
  max-width: 1200px;
  margin: 0 auto;
}

.test-controls {
  margin: 20px 0;
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}

.current-content {
  margin-top: 20px;
  padding: 16px;
  background: #f5f5f5;
  border-radius: 8px;
  border: 1px solid #e0e0e0;
}

.current-content h3 {
  margin: 0 0 12px 0;
  color: #333;
  font-size: 16px;
}

.current-content pre {
  margin: 0;
  padding: 12px;
  background: #fff;
  border-radius: 4px;
  border: 1px solid #ddd;
  overflow-x: auto;
  font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
  font-size: 14px;
  line-height: 1.5;
  color: #333;
}

@media (max-width: 768px) {
  .code-editor-test {
    padding: 12px;
  }
  
  .test-controls {
    flex-direction: column;
  }
  
  .test-controls .el-button {
    width: 100%;
  }
}
</style>