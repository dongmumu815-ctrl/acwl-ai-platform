<template>
  <div class="advanced-code-editor-demo">
    <div class="demo-header">
      <h2>高级代码编辑器演示</h2>
      <p>基于原生 textarea 的稳定代码编辑器，无 Web Worker 问题</p>
    </div>
    
    <div class="demo-features">
      <el-card class="feature-card">
        <h3>主要特性</h3>
        <ul>
          <li>✅ 基于原生 textarea，稳定可靠</li>
          <li>✅ 支持行号显示</li>
          <li>✅ 语法高亮（基础版）</li>
          <li>✅ 自动缩进和括号补全</li>
          <li>✅ 代码格式化功能</li>
          <li>✅ 全屏编辑模式</li>
          <li>✅ 快捷键支持</li>
          <li>✅ 选择信息显示</li>
        </ul>
      </el-card>
      
      <el-card class="feature-card">
        <h3>快捷键</h3>
        <ul>
          <li><kbd>Ctrl+S</kbd> - 保存代码</li>
          <li><kbd>F11</kbd> - 切换全屏</li>
          <li><kbd>Tab</kbd> - 增加缩进</li>
          <li><kbd>Shift+Tab</kbd> - 减少缩进</li>
          <li><kbd>Ctrl+A</kbd> - 全选</li>
          <li><kbd>Ctrl+Z</kbd> - 撤销</li>
          <li><kbd>ESC</kbd> - 关闭编辑器</li>
        </ul>
      </el-card>
    </div>
    
    <div class="demo-buttons">
      <el-button @click="testPythonEditor" type="primary" size="large">
        <el-icon><Edit /></el-icon>
        测试 Python 编辑器
      </el-button>
      <el-button @click="testJavaScriptEditor" type="success" size="large">
        <el-icon><Edit /></el-icon>
        测试 JavaScript 编辑器
      </el-button>
      <el-button @click="testSqlEditor" type="warning" size="large">
        <el-icon><Edit /></el-icon>
        测试 SQL 编辑器
      </el-button>
      <el-button @click="testShellEditor" type="info" size="large">
        <el-icon><Edit /></el-icon>
        测试 Shell 编辑器
      </el-button>
    </div>

    <div class="demo-info" v-if="editorVisible">
      <el-alert
        title="编辑器已打开"
        type="success"
        description="您可以在编辑器中输入代码，测试各种功能。编辑器支持自动缩进、括号补全、代码格式化等功能。"
        show-icon
        :closable="false"
      />
    </div>

    <!-- 高级代码编辑器组件 -->
    <AdvancedCodeEditor
      v-model="editorContent"
      :visible="editorVisible"
      :language="currentLanguage"
      :title="currentTitle"
      :show-line-numbers="true"
      @save="handleSave"
      @close="handleClose"
    />
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { ElMessage } from 'element-plus'
import { Edit } from '@element-plus/icons-vue'
import AdvancedCodeEditor from '@/components/AdvancedCodeEditor.vue'

// 编辑器状态
const editorVisible = ref(false)
const editorContent = ref('')
const currentLanguage = ref('python')
const currentTitle = ref('代码编辑器')

// 示例代码
const sampleCodes = {
  python: `# Python 示例代码
def fibonacci(n):
    """计算斐波那契数列的第n项"""
    if n <= 1:
        return n
    else:
        return fibonacci(n-1) + fibonacci(n-2)

# 测试函数
for i in range(10):
    print(f"fibonacci({i}) = {fibonacci(i)}")

# 列表推导式示例
squares = [x**2 for x in range(10)]
print("前10个数的平方:", squares)

# 字典示例
student_grades = {
    "张三": 85,
    "李四": 92,
    "王五": 78
}

for name, grade in student_grades.items():
    print(f"{name}: {grade}分")
`,
  
  javascript: `// JavaScript 示例代码
class Calculator {
    constructor() {
        this.result = 0;
    }
    
    add(value) {
        this.result += value;
        return this;
    }
    
    subtract(value) {
        this.result -= value;
        return this;
    }
    
    multiply(value) {
        this.result *= value;
        return this;
    }
    
    divide(value) {
        if (value !== 0) {
            this.result /= value;
        } else {
            console.error("除数不能为零");
        }
        return this;
    }
    
    getResult() {
        return this.result;
    }
    
    reset() {
        this.result = 0;
        return this;
    }
}

// 使用示例
const calc = new Calculator();
const result = calc
    .add(10)
    .multiply(2)
    .subtract(5)
    .divide(3)
    .getResult();

console.log("计算结果:", result);

// 异步函数示例
async function fetchUserData(userId) {
    try {
        const response = await fetch(\`/api/users/\${userId}\`);
        const userData = await response.json();
        return userData;
    } catch (error) {
        console.error("获取用户数据失败:", error);
        throw error;
    }
}

// 数组操作示例
const numbers = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10];
const evenNumbers = numbers.filter(num => num % 2 === 0);
const doubledNumbers = numbers.map(num => num * 2);
const sum = numbers.reduce((acc, num) => acc + num, 0);

console.log("偶数:", evenNumbers);
console.log("翻倍:", doubledNumbers);
console.log("总和:", sum);
`,
  
  sql: `-- SQL 示例代码
-- 创建用户表
CREATE TABLE users (
    id INT PRIMARY KEY AUTO_INCREMENT,
    username VARCHAR(50) NOT NULL UNIQUE,
    email VARCHAR(100) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- 创建订单表
CREATE TABLE orders (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL,
    total_amount DECIMAL(10, 2) NOT NULL,
    status ENUM('pending', 'paid', 'shipped', 'delivered', 'cancelled') DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- 插入示例数据
INSERT INTO users (username, email, password_hash) VALUES
('john_doe', 'john@example.com', 'hashed_password_1'),
('jane_smith', 'jane@example.com', 'hashed_password_2'),
('bob_wilson', 'bob@example.com', 'hashed_password_3');

INSERT INTO orders (user_id, total_amount, status) VALUES
(1, 99.99, 'paid'),
(2, 149.50, 'shipped'),
(1, 75.25, 'pending'),
(3, 200.00, 'delivered');

-- 查询示例
-- 查询所有用户及其订单总数
SELECT 
    u.username,
    u.email,
    COUNT(o.id) as order_count,
    COALESCE(SUM(o.total_amount), 0) as total_spent
FROM users u
LEFT JOIN orders o ON u.id = o.user_id
GROUP BY u.id, u.username, u.email
ORDER BY total_spent DESC;

-- 查询最近30天的订单统计
SELECT 
    DATE(created_at) as order_date,
    COUNT(*) as order_count,
    SUM(total_amount) as daily_revenue
FROM orders
WHERE created_at >= DATE_SUB(CURRENT_DATE, INTERVAL 30 DAY)
GROUP BY DATE(created_at)
ORDER BY order_date DESC;

-- 更新订单状态
UPDATE orders 
SET status = 'shipped' 
WHERE status = 'paid' AND created_at < DATE_SUB(NOW(), INTERVAL 1 DAY);

-- 删除超过1年的已取消订单
DELETE FROM orders 
WHERE status = 'cancelled' 
AND created_at < DATE_SUB(CURRENT_DATE, INTERVAL 1 YEAR);
`,
  
  shell: `#!/bin/bash
# Shell 脚本示例

# 设置脚本选项
set -euo pipefail  # 遇到错误时退出，未定义变量时退出，管道失败时退出

# 定义变量
SCRIPT_DIR="$(cd "$(dirname "\${BASH_SOURCE[0]}")" && pwd)"
LOG_FILE="\${SCRIPT_DIR}/deployment.log"
APP_NAME="my-application"
BACKUP_DIR="/backup"

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 日志函数
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "\${LOG_FILE}"
}

log_info() {
    echo -e "\${BLUE}[INFO]\${NC} $1" | tee -a "\${LOG_FILE}"
}

log_success() {
    echo -e "\${GREEN}[SUCCESS]\${NC} $1" | tee -a "\${LOG_FILE}"
}

log_warning() {
    echo -e "\${YELLOW}[WARNING]\${NC} $1" | tee -a "\${LOG_FILE}"
}

log_error() {
    echo -e "\${RED}[ERROR]\${NC} $1" | tee -a "\${LOG_FILE}"
}

# 检查依赖
check_dependencies() {
    log_info "检查系统依赖..."
    
    local deps=("git" "docker" "docker-compose" "curl")
    local missing_deps=()
    
    for dep in "\${deps[@]}"; do
        if ! command -v "\${dep}" &> /dev/null; then
            missing_deps+=("\${dep}")
        fi
    done
    
    if [ \${#missing_deps[@]} -ne 0 ]; then
        log_error "缺少以下依赖: \${missing_deps[*]}"
        exit 1
    fi
    
    log_success "所有依赖检查通过"
}

# 创建备份
create_backup() {
    log_info "创建应用备份..."
    
    local backup_name="\${APP_NAME}_backup_$(date +%Y%m%d_%H%M%S)"
    local backup_path="\${BACKUP_DIR}/\${backup_name}.tar.gz"
    
    # 确保备份目录存在
    mkdir -p "\${BACKUP_DIR}"
    
    # 创建备份
    if tar -czf "\${backup_path}" -C "/opt" "\${APP_NAME}"; then
        log_success "备份创建成功: \${backup_path}"
    else
        log_error "备份创建失败"
        exit 1
    fi
}

# 部署应用
deploy_application() {
    log_info "开始部署应用..."
    
    # 拉取最新代码
    log_info "拉取最新代码..."
    git pull origin main
    
    # 构建Docker镜像
    log_info "构建Docker镜像..."
    docker-compose build
    
    # 停止旧容器
    log_info "停止旧容器..."
    docker-compose down
    
    # 启动新容器
    log_info "启动新容器..."
    docker-compose up -d
    
    # 等待服务启动
    log_info "等待服务启动..."
    sleep 30
    
    # 健康检查
    if curl -f http://localhost:8080/health &> /dev/null; then
        log_success "应用部署成功，健康检查通过"
    else
        log_error "应用部署失败，健康检查未通过"
        exit 1
    fi
}

# 清理旧备份
cleanup_old_backups() {
    log_info "清理旧备份文件..."
    
    # 保留最近7天的备份
    find "\${BACKUP_DIR}" -name "\${APP_NAME}_backup_*.tar.gz" -mtime +7 -delete
    
    log_success "旧备份清理完成"
}

# 主函数
main() {
    log_info "开始部署流程..."
    
    check_dependencies
    create_backup
    deploy_application
    cleanup_old_backups
    
    log_success "部署流程完成！"
}

# 错误处理
trap 'log_error "脚本执行失败，退出码: $?"' ERR

# 执行主函数
main "$@"
`
}

/**
 * 测试Python编辑器
 */
const testPythonEditor = () => {
  currentLanguage.value = 'python'
  currentTitle.value = 'Python 代码编辑器'
  editorContent.value = sampleCodes.python
  editorVisible.value = true
  ElMessage.success('Python 编辑器已打开')
}

/**
 * 测试JavaScript编辑器
 */
const testJavaScriptEditor = () => {
  currentLanguage.value = 'javascript'
  currentTitle.value = 'JavaScript 代码编辑器'
  editorContent.value = sampleCodes.javascript
  editorVisible.value = true
  ElMessage.success('JavaScript 编辑器已打开')
}

/**
 * 测试SQL编辑器
 */
const testSqlEditor = () => {
  currentLanguage.value = 'sql'
  currentTitle.value = 'SQL 代码编辑器'
  editorContent.value = sampleCodes.sql
  editorVisible.value = true
  ElMessage.success('SQL 编辑器已打开')
}

/**
 * 测试Shell编辑器
 */
const testShellEditor = () => {
  currentLanguage.value = 'shell'
  currentTitle.value = 'Shell 脚本编辑器'
  editorContent.value = sampleCodes.shell
  editorVisible.value = true
  ElMessage.success('Shell 编辑器已打开')
}

/**
 * 处理保存事件
 */
const handleSave = (content) => {
  console.log('保存的代码内容:', content)
  ElMessage.success(`代码已保存！内容长度: ${content.length} 字符`)
}

/**
 * 处理关闭事件
 */
const handleClose = () => {
  editorVisible.value = false
  ElMessage.info('编辑器已关闭')
}
</script>

<style scoped>
.advanced-code-editor-demo {
  padding: 20px;
  max-width: 1200px;
  margin: 0 auto;
}

.demo-header {
  text-align: center;
  margin-bottom: 30px;
}

.demo-header h2 {
  color: #2c3e50;
  margin-bottom: 10px;
}

.demo-header p {
  color: #7f8c8d;
  font-size: 16px;
}

.demo-features {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
  margin-bottom: 30px;
}

.feature-card {
  height: 100%;
}

.feature-card h3 {
  color: #2c3e50;
  margin-bottom: 15px;
  font-size: 18px;
}

.feature-card ul {
  list-style: none;
  padding: 0;
  margin: 0;
}

.feature-card li {
  padding: 8px 0;
  color: #34495e;
  font-size: 14px;
}

.feature-card kbd {
  background: #f8f9fa;
  border: 1px solid #dee2e6;
  border-radius: 3px;
  padding: 2px 6px;
  font-size: 12px;
  color: #495057;
  margin-right: 8px;
}

.demo-buttons {
  display: flex;
  justify-content: center;
  gap: 15px;
  margin-bottom: 20px;
  flex-wrap: wrap;
}

.demo-info {
  margin-bottom: 20px;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .demo-features {
    grid-template-columns: 1fr;
  }
  
  .demo-buttons {
    flex-direction: column;
    align-items: center;
  }
  
  .demo-buttons .el-button {
    width: 100%;
    max-width: 300px;
  }
}
</style>