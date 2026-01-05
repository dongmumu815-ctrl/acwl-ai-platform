<template>
  <div class="field-mapping">
    <h2>字段映射配置</h2>
    
    <!-- 配置详情显示 -->
    <div class="config-info" v-if="currentConfig && Object.keys(currentConfig).length > 0">
      <h3>当前配置信息</h3>
      <div class="config-details">
        <p><strong>配置ID：</strong>{{ currentConfig.id || '未保存' }}</p>
        <p><strong>配置名称：</strong>{{ currentConfig.name || '未命名' }}</p>
        <p><strong>配置描述：</strong>{{ currentConfig.description || '无描述' }}</p>
        <p><strong>文件类型：</strong>{{ getFileTypeDisplay() }}</p>
        <p><strong>创建时间：</strong>{{ currentConfig.created_at ? formatDate(currentConfig.created_at) : '未知' }}</p>
      </div>
    </div>
    
    <!-- 全局设定 -->
    <div class="global-settings">
      <h3>全局设定</h3>
      <div class="settings-content">
        <div class="setting-item">
          <label class="setting-label">数据处理模式：</label>
          <el-radio-group v-model="globalSettings.mode" @change="onModeChange">
            <el-radio value="insert">新增模式</el-radio>
            <el-radio value="update">覆盖模式</el-radio>
          </el-radio-group>
        </div>
        
        <div class="setting-item" v-if="globalSettings.mode === 'update'">
          <label class="setting-label">更新条件字段：</label>
          <div class="update-conditions">
            <el-checkbox-group v-model="globalSettings.updateConditions">
              <el-checkbox 
                v-for="(field, index) in mappedTargetFields" 
                :key="index"
                :value="field.name"
                :disabled="!field.isMapped">
                {{ field.name }} ({{ field.type }})
              </el-checkbox>
            </el-checkbox-group>
            <div class="condition-hint" v-if="mappedTargetFields.length === 0">
              <el-text type="info">请先配置字段映射后再选择更新条件</el-text>
            </div>
          </div>
        </div>
      </div>
    </div>
    
    
    <div class="mapping-container">
      <!-- 统一滚动区域 -->
      <div class="unified-scroll-area" ref="scrollArea" @scroll="updateConnections">
        <div class="fields-wrapper">
          <!-- 左侧：源字段列表 -->
          <div class="source-column">
            <div class="column-header">
              <h3>源字段 ({{ orderedSourceFields.length }})</h3>
              <el-button 
                type="primary" 
                size="small" 
                @click="addSourceField" 
                icon="el-icon-plus">
                <el-icon><Plus /></el-icon>
                添加字段
              </el-button>
            </div>
            <div class="field-list">
              <draggable 
                v-model="orderedSourceFields" 
                group="{ name: 'fields', pull: 'clone', put: false }"
                @change="onSourceOrderChange"
                @end="onDragEnd"
                item-key="name"
                class="draggable-list">
                <template #item="{element, index}">
                  <div 
                    :key="element.name"
                    :data-index="index"
                    :data-field-id="getFieldName(element)"
                    class="field-item source-field"
                    :class="{mapped: hasSourceMapping(index), custom: element.isCustom, selected: selectedSourceIndex === index}"
                    @click="selectSourceField(index)"
                    ref="sourceField">
                    <div class="field-content">
                      <div class="field-info">
                        <span class="field-name">{{ getFieldName(element) }}</span>
                        <span class="field-type">{{ getFieldType(element) }}</span>
                        <span v-if="element.isCustom" class="custom-badge">自定义</span>
                      </div>
                      <div class="field-sample">
                        <!-- {{ element }} -->
                        示例: {{ element.sample || '暂无示例' }}
                      </div>
                      <div class="field-expression" v-if="element.expression">
                        表达式: {{ element.expression }}
                      </div>
                    </div>
                    <div class="field-actions">
                      <!-- 调试信息 -->
                      <span v-if="isDevelopment" style="font-size: 10px; color: #999;">isCustom: {{ element.isCustom }}</span>
                      <el-button 
                        v-if="element.isCustom" 
                        text 
                        size="small" 
                        @click="editSourceField(index)">
                        <el-icon><Edit /></el-icon>
                      </el-button>
                      <el-button 
                        v-if="element.isCustom" 
                        text 
                        size="small" 
                        @click="removeSourceField(index)">
                        <el-icon><Delete /></el-icon>
                      </el-button>
                    </div>
                  </div>
                </template>
              </draggable>
            </div>
          </div>
          
          <!-- 中间：连接线区域 -->
          <div class="connection-area">
            <svg ref="connectionSvg" class="connection-svg">
              <g v-for="(connection, index) in connections" :key="index">
                <path 
                  :d="connection.path" 
                  :stroke="connection.color" 
                  stroke-width="2" 
                  fill="none"
                  :class="{ active: activeConnections.includes(index) }"
                />
                <!-- 删除映射按钮 -->
                <circle 
                  :cx="connection.midX" 
                  :cy="connection.midY" 
                  r="8" 
                  fill="#f56c6c" 
                  stroke="#fff" 
                  stroke-width="1" 
                  class="delete-mapping-btn"
                  @click="removeMappingByIndex(index)"
                  style="cursor: pointer;"
                />
                <text 
                  :x="connection.midX" 
                  :y="connection.midY + 1" 
                  text-anchor="middle" 
                  dominant-baseline="middle" 
                  fill="white" 
                  font-size="10" 
                  font-weight="bold" 
                  class="delete-mapping-text"
                  @click="removeMappingByIndex(index)"
                  style="cursor: pointer; pointer-events: none;"
                >×</text>
              </g>
            </svg>
          </div>
          
          <!-- 右侧：目标字段列表 -->
          <div class="target-column">
            <div class="column-header">
              <h3>目标字段 ({{ orderedTargetFields.length }})</h3>
            </div>
            <div class="field-list">
              <draggable 
                v-model="orderedTargetFields" 
                group="{ name: 'fields', pull: false, put: true }"
                @change="onTargetOrderChange"
                @add="onTargetAdd"
                @end="onDragEnd"
                item-key="name"
                class="draggable-list">
                <template #item="{element, index}">
                  <div 
                    :key="element.name"
                    :data-index="index"
                    :data-field-id="getFieldName(element)"
                    class="field-item target-field"
                    :class="{mapped: hasTargetMapping(index), selected: selectedTargetIndex === index}"
                    @click="selectTargetField(index)"
                    ref="targetField">
                    <div class="field-content">
                      <div class="field-info">
                        <span class="field-name">{{ getFieldName(element) }}</span>
                        <span class="field-type">{{ getFieldType(element) }}</span>
                        <span v-if="!element.nullable" class="required-badge">必填</span>
                      </div>
                      <div class="field-sample" v-if="element.sample">
                        示例: {{ element.sample }}
                      </div>
                      <div class="field-sample" v-if="hasTargetMapping(index)">
                        映射: {{ getFieldName(getSourceFieldByTargetIndex(index)) }}
                      </div>
                    </div>
                    <div class="field-actions">
                      <el-button 
                        text 
                        size="small" 
                        @click="removeTargetField(index)">
                        <el-icon><Delete /></el-icon>
                      </el-button>
                    </div>
                  </div>
                </template>
              </draggable>
            </div>
          </div>
        </div>
      </div>
      
      <!-- 操作按钮区域 -->
      <div class="action-buttons">
        <div class="left-buttons">
          <el-button @click="clearMappings">清空映射</el-button>
          <el-button @click="autoMapping" type="primary">自动映射</el-button>
          <el-button @click="previewSeaTunnelConfig" type="info">预览配置</el-button>
        </div>
        <div class="right-buttons">
          <el-button @click="$emit('prev-step')">上一步</el-button>
          <el-button @click="saveMappingsOnly" type="success">保存映射</el-button>
          <el-button @click="nextStep" type="primary" :disabled="!canProceed">下一步</el-button>
        </div>
      </div>
    </div>
    
    <!-- 配置预览对话框 -->
    <el-dialog 
      v-model="showConfigPreview" 
      title="SeaTunnel配置预览" 
      width="80%" 
      :before-close="() => showConfigPreview = false">
      <el-input 
        v-model="configPreviewContent"
        type="textarea" 
        :rows="20" 
        readonly 
        placeholder="配置内容将在这里显示..."
      />
      <template #footer>
        <div class="dialog-footer">
          <el-button @click="copyConfigContent">复制配置</el-button>
          <el-button @click="downloadConfig" type="primary">下载配置</el-button>
          <el-button @click="showConfigPreview = false">关闭</el-button>
        </div>
      </template>
    </el-dialog>
    
    <!-- 添加/编辑源字段对话框 -->
    <el-dialog
      v-model="showSourceFieldDialog"
      :title="editingSourceField !== null ? '编辑源字段' : '添加源字段'"
      width="600px"
      :close-on-click-modal="false"
    >
      <el-form :model="sourceFieldForm" label-width="120px">
        <el-form-item label="字段名称" required>
          <el-input v-model="sourceFieldForm.name" placeholder="请输入字段名称" />
        </el-form-item>
        
        <el-form-item label="字段类型" required>
          <el-select v-model="sourceFieldForm.type" placeholder="请选择字段类型">
            <el-option 
              v-for="typeOption in fieldTypeOptions" 
              :key="typeOption" 
              :label="typeOption" 
              :value="typeOption" 
            />
          </el-select>
        </el-form-item>
        
        <el-form-item label="生成类型" required>
          <el-select v-model="sourceFieldForm.generateType" placeholder="请选择生成类型">
            <el-option label="常量值" value="constant" />
            <el-option label="UUID" value="uuid" />
            <el-option label="雪花ID" value="snowflake" />
            <el-option label="字段拼接" value="concat" />
            <el-option label="条件判断" value="condition" />
            <el-option label="多条件判断" value="case_when" />
            <el-option label="数学运算" value="math" />
            <el-option label="日期函数" value="date" />
            <el-option label="外部参数" value="external_param" />
          </el-select>
        </el-form-item>
        
        <!-- 参数名配置 -->
        <el-form-item label="参数名" v-if="sourceFieldForm.generateType === 'external_param'" required>
          <el-input v-model="sourceFieldForm.parameterName" placeholder="请输入参数名" />
        </el-form-item>
        
        <!-- 常量值配置 -->
        <el-form-item v-if="sourceFieldForm.generateType === 'constant'" label="常量值" required>
          <el-input v-model="sourceFieldForm.constantValue" placeholder="请输入常量值" />
        </el-form-item>
        
        <!-- 字段拼接配置 -->
        <template v-if="sourceFieldForm.generateType === 'concat'">
          <el-form-item label="拼接字段" required>
            <el-select
              v-model="sourceFieldForm.concatFields"
              multiple
              placeholder="请选择要拼接的字段"
              style="width: 100%"
            >
              <el-option
                v-for="field in availableOriginalFields"
                :key="getFieldName(field)"
                :label="getFieldName(field)"
                :value="getFieldName(field)"
              />
            </el-select>
          </el-form-item>
          <el-form-item label="分隔符">
            <el-input v-model="sourceFieldForm.separator" placeholder="请输入分隔符（可选）" />
          </el-form-item>
        </template>
        
        <!-- 条件判断配置 -->
        <template v-if="sourceFieldForm.generateType === 'condition'">
          <el-form-item label="判断字段" required>
            <el-select v-model="sourceFieldForm.conditionField" placeholder="请选择判断字段">
              <el-option
                v-for="field in availableOriginalFields"
                :key="getFieldName(field)"
                :label="getFieldName(field)"
                :value="getFieldName(field)"
              />
            </el-select>
          </el-form-item>
          <el-form-item label="操作符" required>
            <el-select v-model="sourceFieldForm.conditionOperator" placeholder="请选择操作符">
              <el-option label="等于" value="=" />
              <el-option label="不等于" value="!=" />
              <el-option label="大于" value=">" />
              <el-option label="小于" value="<" />
              <el-option label="大于等于" value=">=" />
              <el-option label="小于等于" value="<=" />
              <el-option label="包含" value="LIKE" />
              <el-option label="为空" value="IS NULL" />
              <el-option label="不为空" value="IS NOT NULL" />
            </el-select>
          </el-form-item>
          <el-form-item v-if="needsConditionValue" label="比较值" required>
            <el-input v-model="sourceFieldForm.conditionValue" placeholder="请输入比较值" />
          </el-form-item>
          <el-form-item label="真值" required>
            <el-input v-model="sourceFieldForm.trueValue" placeholder="条件为真时的值" />
          </el-form-item>
          <el-form-item label="假值" required>
            <el-input v-model="sourceFieldForm.falseValue" placeholder="条件为假时的值" />
          </el-form-item>
        </template>
        
        <!-- 多条件判断配置 -->
        <template v-if="sourceFieldForm.generateType === 'case_when'">
          <el-form-item label="判断字段" required>
            <el-select v-model="sourceFieldForm.caseWhenField" placeholder="请选择判断字段">
              <el-option
                v-for="field in availableOriginalFields"
                :key="getFieldName(field)"
                :label="getFieldName(field)"
                :value="getFieldName(field)"
              />
            </el-select>
          </el-form-item>
          <el-form-item label="条件分支">
            <div v-for="(branch, index) in sourceFieldForm.caseBranches" :key="index" class="case-branch">
              <el-row :gutter="10">
                <el-col :span="6">
                  <el-select v-model="branch.operator" placeholder="操作符">
                    <el-option label="=" value="=" />
                    <el-option label="!=" value="!=" />
                    <el-option label=">" value=">" />
                    <el-option label="<" value="<" />
                    <el-option label=">=" value=">=" />
                    <el-option label="<=" value="<=" />
                    <el-option label="LIKE" value="LIKE" />
                    <el-option label="IS NULL" value="IS NULL" />
                    <el-option label="IS NOT NULL" value="IS NOT NULL" />
                  </el-select>
                </el-col>
                <el-col :span="7">
                  <el-input
                    v-if="!['IS NULL', 'IS NOT NULL'].includes(branch.operator)"
                    v-model="branch.condition"
                    placeholder="条件值"
                  />
                </el-col>
                <el-col :span="7">
                  <el-input v-model="branch.value" placeholder="结果值" />
                </el-col>
                <el-col :span="4">
                  <el-button type="danger" size="small" @click="removeCaseBranch(index)">
                    <el-icon><Delete /></el-icon>
                  </el-button>
                </el-col>
              </el-row>
            </div>
            <el-button type="primary" size="small" @click="addCaseBranch">
              <el-icon><Plus /></el-icon>
              添加分支
            </el-button>
          </el-form-item>
          <el-form-item label="默认值" required>
            <el-input v-model="sourceFieldForm.defaultValue" placeholder="所有条件都不满足时的默认值" />
          </el-form-item>
        </template>
        
        <!-- 数学运算配置 -->
        <el-form-item v-if="sourceFieldForm.generateType === 'math'" label="数学表达式" required>
          <el-input
            v-model="sourceFieldForm.mathExpression"
            type="textarea"
            placeholder="请输入数学表达式，如：field1 + field2 * 100"
          />
        </el-form-item>
        
        <!-- 日期函数配置 -->
        <template v-if="sourceFieldForm.generateType === 'date'">
          <el-form-item label="日期函数" required>
            <el-select v-model="sourceFieldForm.dateFunction" placeholder="请选择日期函数">
              <el-option label="当前时间" value="NOW()" />
              <el-option label="当前日期" value="CURDATE()" />
              <el-option label="当前时间戳" value="UNIX_TIMESTAMP()" />
            </el-select>
          </el-form-item>
          <el-form-item label="日期格式">
            <el-input v-model="sourceFieldForm.dateFormat" placeholder="日期格式，如：%Y-%m-%d %H:%i:%s" />
          </el-form-item>
          <el-form-item label="时间间隔">
            <el-input v-model="sourceFieldForm.dateInterval" placeholder="时间间隔，如：1 DAY, -1 MONTH" />
          </el-form-item>
        </template>
        
        <!-- 预览 -->
        <el-form-item label="表达式预览">
          <el-input :value="generateExpression()" readonly type="textarea" rows="2" />
        </el-form-item>
        
        <el-form-item label="样本结果">
          <el-input :value="generateSampleResult()" readonly />
        </el-form-item>
      </el-form>
      
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="showSourceFieldDialog = false">取消</el-button>
          <el-button type="primary" :disabled="!isSourceFieldFormValid" @click="saveSourceField">
            {{ editingSourceField !== null ? '更新' : '添加' }}
          </el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script>
import { ref, reactive, computed, onMounted, nextTick, watch, getCurrentInstance } from 'vue'
import { useStore } from 'vuex'
import { ElMessageBox, ElMessage } from 'element-plus'
import { Edit, Delete, Plus } from '@element-plus/icons-vue'
import draggable from 'vuedraggable'
import { generateApi, configApi } from '../services/api'
import templateApi from '../services/templateApi'

export default {
  name: 'FieldMapping',
  components: {
    draggable,
    Edit,
    Delete,
    Plus
  },
  emits: ['prev-step', 'next-step'],
  props: {
    sourceFields: {
      type: Array,
      default: () => []
    },
    targetFields: {
      type: Array,
      default: () => []
    },
    sourceConfig: {
      type: Object,
      default: () => ({})
    },
    targetConfig: {
      type: Object,
      default: () => ({})
    },
    templateId: {
      type: String,
      default: ''
    },
    configId: {
      type: String,
      default: ''
    },
    fieldTypeOptions: {
      type: Array,
      default: () => ['VARCHAR', 'INT', 'BIGINT', 'DECIMAL', 'DATE', 'DATETIME', 'TEXT', 'BOOLEAN']
    }
  },
  setup(props, { emit }) {
    const store = useStore()
    
    // 响应式数据
    const scrollArea = ref(null)
    const connectionSvg = ref(null)
    const sourceField = ref([])
    const targetField = ref([])
    
    const orderedSourceFields = ref([])
    const orderedTargetFields = ref([])
    const positionMappings = ref([])
    const connections = ref([])
    const activeConnections = ref([])
    const selectedSourceIndex = ref(null)
    const selectedTargetIndex = ref(null)
    const deletedTargetFields = ref([]) // 存储已删除的目标字段
    
    const showConfigPreview = ref(false)
    const configPreviewContent = ref('')
    const configPreviewLoading = ref(false)
    
    const showSourceFieldDialog = ref(false)
    const editingSourceField = ref(null)
    const sourceFieldForm = reactive({
      name: '',
      type: 'VARCHAR',
      generateType: 'external_param',
      parameterName: '',
      constantValue: '',
      concatFields: [],
      separator: '',
      conditionField: '',
      conditionOperator: '=',
      conditionValue: '',
      trueValue: '',
      falseValue: '',
      caseWhenField: '',
      caseBranches: [],
      defaultValue: '',
      mathExpression: '',
      dateFunction: 'NOW()',
      dateFormat: '%Y-%m-%d %H:%i:%s',
      dateInterval: ''
    })
    
    // 全局设定
    const globalSettings = reactive({
      mode: 'insert', // 'insert' 或 'update'
      updateConditions: [] // 更新条件字段列表
    })
    
    // 计算属性
    const isDevelopment = computed(() => {
      return process.env.NODE_ENV === 'development'
    })
    
    const canProceed = computed(() => {
      return positionMappings.value.length > 0 && 
             orderedSourceFields.value.length > 0 && 
             orderedTargetFields.value.length > 0
    })
    
    const currentConfig = computed(() => {
      return store.state.targetConfig || {}
    })
    
    const originalSourceFields = computed(() => {
      return orderedSourceFields.value.filter(field => !field.isCustom)
    })
    
    const availableOriginalFields = computed(() => {
      return originalSourceFields.value
    })
    
    const needsConditionValue = computed(() => {
      return sourceFieldForm.conditionOperator && 
             !['IS NULL', 'IS NOT NULL'].includes(sourceFieldForm.conditionOperator)
    })
    
    const isSourceFieldFormValid = computed(() => {
      if (!sourceFieldForm.name || !sourceFieldForm.type || !sourceFieldForm.generateType) {
        return false
      }
      
      switch (sourceFieldForm.generateType) {
        case 'constant':
          return !!sourceFieldForm.constantValue
        case 'snowflake':
          return true
        case 'concat':
          return sourceFieldForm.concatFields.length > 0
        case 'condition':
          return sourceFieldForm.conditionField && 
                 sourceFieldForm.conditionOperator && 
                 sourceFieldForm.trueValue && 
                 sourceFieldForm.falseValue &&
                 (!needsConditionValue.value || sourceFieldForm.conditionValue)
        case 'case_when':
          return sourceFieldForm.caseWhenField && 
                 sourceFieldForm.caseBranches.length > 0 &&
                 sourceFieldForm.caseBranches.every(branch => 
                   branch.operator && branch.condition && branch.value
                 )
        case 'math':
          return !!sourceFieldForm.mathExpression
        case 'date':
          return !!sourceFieldForm.dateFunction
        case 'external_param':
          return !!sourceFieldForm.parameterName
        default:
          return true
      }
    })
    
    // 已映射的目标字段列表
    const mappedTargetFields = computed(() => {
      return orderedTargetFields.value.map((field, index) => {
        const isMapped = hasTargetMapping(index)
        return {
          name: getFieldName(field),
          type: getFieldType(field),
          index: index,
          isMapped: isMapped
        }
      }).filter(field => field.isMapped)
    })
    
    // 辅助函数
    const getFieldName = (field) => {
      return field.name || field.column_name || field.field_name || field
    }
    
    const getFieldType = (field) => {
      return field.type || field.column_type || field.data_type || 'string'
    }
    
    // 方法
    const hasSourceMapping = (sourceIndex) => {
      return positionMappings.value.some(m => m.sourceIndex === sourceIndex)
    }
    
    const hasTargetMapping = (targetIndex) => {
      return positionMappings.value.some(m => m.targetIndex === targetIndex)
    }
    
    const getSourceFieldByTargetIndex = (targetIndex) => {
      const mapping = positionMappings.value.find(m => m.targetIndex === targetIndex)
      return mapping ? orderedSourceFields.value[mapping.sourceIndex] : null
    }
    
    const onSourceOrderChange = () => {
      updateConnections()
    }
    
    const onTargetOrderChange = () => {
      updateConnections()
    }
    
    const onTargetAdd = (evt) => {
      const { newIndex, element } = evt.added
      if (element && getFieldName(element)) {
        // 找到源字段的索引
        const sourceIndex = orderedSourceFields.value.findIndex(f => getFieldName(f) === getFieldName(element))
        if (sourceIndex !== -1) {
          // 创建映射
          positionMappings.value.push({
            sourceIndex,
            targetIndex: newIndex
          })
          
          // 移除拖拽添加的重复项
          orderedTargetFields.value.splice(newIndex, 1)
          
          nextTick(() => {
            updateConnections()
          })
        }
      }
    }
    
    const onDragEnd = () => {
      updateConnections()
    }
    
    const selectSourceField = (index) => {
      if (selectedSourceIndex.value === index) {
        selectedSourceIndex.value = null
      } else {
        selectedSourceIndex.value = index
        // 如果已选择目标字段，建立映射
        if (selectedTargetIndex.value !== null) {
          createMapping(index, selectedTargetIndex.value)
        }
      }
    }
    
    const selectTargetField = (index) => {
      if (selectedTargetIndex.value === index) {
        selectedTargetIndex.value = null
      } else {
        selectedTargetIndex.value = index
        // 如果已选择源字段，建立映射
        if (selectedSourceIndex.value !== null) {
          createMapping(selectedSourceIndex.value, index)
        }
      }
    }
    
    const createMapping = (sourceIndex, targetIndex) => {
      // 检查是否已存在映射
      const existingMapping = positionMappings.value.find(
        m => m.sourceIndex === sourceIndex || m.targetIndex === targetIndex
      )
      
      if (existingMapping) {
        // 移除现有映射
        const index = positionMappings.value.indexOf(existingMapping)
        positionMappings.value.splice(index, 1)
      }
      
      // 创建新映射
      positionMappings.value.push({
        sourceIndex,
        targetIndex
      })
      
      // 清除选择状态
      selectedSourceIndex.value = null
      selectedTargetIndex.value = null
      
      nextTick(() => {
        updateConnections()
      })
    }
    
    const removeMapping = (sourceIndex, targetIndex) => {
      const mappingIndex = positionMappings.value.findIndex(
        mapping => mapping.sourceIndex === sourceIndex && mapping.targetIndex === targetIndex
      )
      if (mappingIndex !== -1) {
        positionMappings.value.splice(mappingIndex, 1)
        updateConnections()
      }
    }
    
    const removeMappingByIndex = (connectionIndex) => {
      if (connectionIndex >= 0 && connectionIndex < positionMappings.value.length) {
        positionMappings.value.splice(connectionIndex, 1)
        updateConnections()
        ElMessage.success('映射关系已删除')
      }
    }
    
    const updateConnections = () => {
      console.log('FieldMapping.updateConnections: 开始更新连接线')
      console.log('- 当前映射关系数量:', positionMappings.value.length)
      console.log('- 当前映射关系详情:', JSON.stringify(positionMappings.value))
      
      nextTick(() => {
        if (!connectionSvg.value || !scrollArea.value) {
          console.warn('FieldMapping.updateConnections: SVG容器或滚动区域不存在，无法绘制连接线')
          return
        }
        
        const svgRect = connectionSvg.value.getBoundingClientRect()
        
        connections.value = []
        
        // 获取所有源字段和目标字段的DOM元素
        const sourceElements = scrollArea.value.querySelectorAll('.source-field')
        const targetElements = scrollArea.value.querySelectorAll('.target-field')
        
        positionMappings.value.forEach(mapping => {
          const sourceEl = sourceElements[mapping.sourceIndex]
          const targetEl = targetElements[mapping.targetIndex]
          
          if (sourceEl && targetEl) {
            const sourceRect = sourceEl.getBoundingClientRect()
            const targetRect = targetEl.getBoundingClientRect()
            
            // 计算相对于SVG容器的坐标
            const sourceY = sourceRect.top + sourceRect.height / 2 - svgRect.top
            const targetY = targetRect.top + targetRect.height / 2 - svgRect.top
            
            // 生成SVG路径
            const path = `M 0 ${sourceY} Q ${svgRect.width / 2} ${sourceY} ${svgRect.width} ${targetY}`
            
            // 计算连接线中点坐标（贝塞尔曲线的中点）
            const midX = svgRect.width / 2
            const midY = (sourceY + targetY) / 2
            
            connections.value.push({
              x1: 0,
              y1: sourceY,
              x2: svgRect.width,
              y2: targetY,
              path: path,
              color: '#409eff',
              midX: midX,
              midY: midY,
              sourceIndex: mapping.sourceIndex,
              targetIndex: mapping.targetIndex
            })
          }
        })
        
        activeConnections.value = connections.value
      })
    }
    
    const addSourceField = () => {
      editingSourceField.value = null
      sourceFieldForm.name = ''
      sourceFieldForm.type = 'VARCHAR'
      sourceFieldForm.generateType = 'external_param'
      // 重置其他字段...
      sourceFieldForm.parameterName = ''
      sourceFieldForm.constantValue = ''
      sourceFieldForm.expression = ''
      
      showSourceFieldDialog.value = true
    }

    const addSourceFieldImpl = (externalParams = {}) => {
      // 使用外部参数或默认值
      const defaultType = externalParams.defaultType || (props.fieldTypeOptions && props.fieldTypeOptions[0]) || 'VARCHAR'
      
      Object.assign(sourceFieldForm, {
        name: externalParams.name || '',
        type: externalParams.type || defaultType,
        generateType: externalParams.generateType || 'external_param',
        parameterName: externalParams.parameterName || '',
        constantValue: externalParams.constantValue || '',
        concatFields: externalParams.concatFields || [],
        separator: externalParams.separator || '',
        conditionField: externalParams.conditionField || '',
        conditionOperator: externalParams.conditionOperator || '=',
        conditionValue: externalParams.conditionValue || '',
        trueValue: externalParams.trueValue || '',
        falseValue: externalParams.falseValue || '',
        caseBranches: externalParams.caseBranches || [],
        defaultValue: externalParams.defaultValue || '',
        mathExpression: externalParams.mathExpression || '',
        dateFunction: externalParams.dateFunction || 'NOW()',
        dateFormat: externalParams.dateFormat || '%Y-%m-%d %H:%i:%s',
        dateInterval: externalParams.dateInterval || ''
      })
      editingSourceField.value = null
      showSourceFieldDialog.value = true
    }
    
    const editSourceField = (index) => {
      const field = orderedSourceFields.value[index]
      Object.assign(sourceFieldForm, {
        name: field.name,
        type: field.type,
        generateType: field.generateType || 'external_param',
        parameterName: field.parameterName || '',
        constantValue: field.constantValue || '',
        concatFields: field.concatFields || [],
        separator: field.separator || '',
        conditionField: field.conditionField || '',
        conditionOperator: field.conditionOperator || '=',
        conditionValue: field.conditionValue || '',
        trueValue: field.trueValue || '',
        falseValue: field.falseValue || '',
        caseBranches: field.caseBranches || [],
        defaultValue: field.defaultValue || '',
        mathExpression: field.mathExpression || '',
        dateFunction: field.dateFunction || 'NOW()',
        dateFormat: field.dateFormat || '%Y-%m-%d %H:%i:%s',
        dateInterval: field.dateInterval || ''
      })
      editingSourceField.value = index
      showSourceFieldDialog.value = true
    }
    
    const saveSourceField = () => {
      const expression = generateExpression()
      const sample = generateSampleResult()
      
      const fieldData = {
        name: sourceFieldForm.name,
        type: sourceFieldForm.type,
        isCustom: true,
        expression,
        sample,
        generateType: sourceFieldForm.generateType,
        parameterName: sourceFieldForm.parameterName,
        constantValue: sourceFieldForm.constantValue,
        concatFields: [...sourceFieldForm.concatFields],
        separator: sourceFieldForm.separator,
        conditionField: sourceFieldForm.conditionField,
        conditionOperator: sourceFieldForm.conditionOperator,
        conditionValue: sourceFieldForm.conditionValue,
        trueValue: sourceFieldForm.trueValue,
        falseValue: sourceFieldForm.falseValue,
        caseBranches: [...sourceFieldForm.caseBranches],
        defaultValue: sourceFieldForm.defaultValue,
        mathExpression: sourceFieldForm.mathExpression,
        dateFunction: sourceFieldForm.dateFunction,
        dateFormat: sourceFieldForm.dateFormat,
        dateInterval: sourceFieldForm.dateInterval
      }
      
      if (editingSourceField.value !== null) {
        console.log('更新自定义字段:', fieldData)
        orderedSourceFields.value[editingSourceField.value] = fieldData
      } else {
        console.log('添加新的自定义字段:', fieldData)
        orderedSourceFields.value.push(fieldData)
      }
      
      showSourceFieldDialog.value = false
      
      nextTick(() => {
        updateConnections()
      })
    }
    
    const removeSourceField = async (index) => {
      try {
        await ElMessageBox.confirm('确定要删除这个源字段吗？', '确认删除', {
          type: 'warning'
        })
        
        orderedSourceFields.value.splice(index, 1)
        
        positionMappings.value = positionMappings.value.filter(mapping => {
          if (mapping.sourceIndex === index) {
            return false
          }
          if (mapping.sourceIndex > index) {
            mapping.sourceIndex--
          }
          return true
        })
        
        nextTick(() => {
          updateConnections()
        })
        
        ElMessage.success('源字段删除成功')
      } catch {
        // 用户取消删除
      }
    }
    
    const removeTargetField = async (index) => {
      try {
        await ElMessageBox.confirm('确定要删除这个目标字段吗？', '确认删除', {
          type: 'warning'
        })
        
        // 保存被删除的字段到deletedTargetFields
        const fieldToDelete = orderedTargetFields.value[index]
        deletedTargetFields.value.push({
          ...fieldToDelete,
          originalIndex: index // 保存原始索引位置，用于恢复时的排序
        })
        
        // 从目标字段列表中移除
        orderedTargetFields.value.splice(index, 1)
        
        // 更新映射关系
        positionMappings.value = positionMappings.value.filter(mapping => {
          if (mapping.targetIndex === index) {
            return false
          }
          if (mapping.targetIndex > index) {
            mapping.targetIndex--
          }
          return true
        })
        
        nextTick(() => {
          updateConnections()
        })
        
        ElMessage.success('目标字段删除成功')
      } catch {
        // 用户取消删除
      }
    }
    
    const clearMappings = () => {
      // 清空映射关系
      positionMappings.value = []
      connections.value = []
      activeConnections.value = []
      
      // 恢复已删除的目标字段
      if (deletedTargetFields.value.length > 0) {
        // 按原始索引排序，确保字段恢复到正确的位置
        const sortedDeletedFields = [...deletedTargetFields.value].sort((a, b) => a.originalIndex - b.originalIndex)
        
        // 将已删除的字段恢复到目标字段列表
        sortedDeletedFields.forEach(field => {
          // 移除originalIndex属性，避免污染数据
          // eslint-disable-next-line no-unused-vars
          const { originalIndex: _, ...cleanField } = field
          orderedTargetFields.value.push(cleanField)
        })
        
        // 清空已删除字段列表
        deletedTargetFields.value = []
        
        ElMessage.success('已恢复所有删除的目标字段')
      }
      
      // 更新连接线
      nextTick(() => {
        updateConnections()
      })
    }
    
    const autoMapping = () => {
      // 清空现有映射
      positionMappings.value = []
      
      // 获取未删除的源字段和目标字段
      const availableSourceFields = orderedSourceFields.value.filter(field => !field.isDeleted)
      const availableTargetFields = orderedTargetFields.value.filter(field => !field.isDeleted)
      
      // 建立1:1映射关系
      const maxMappings = Math.min(availableSourceFields.length, availableTargetFields.length)
      
      for (let i = 0; i < maxMappings; i++) {
        // 找到源字段在完整列表中的索引
        const sourceIndex = orderedSourceFields.value.findIndex(field => 
          getFieldName(field) === getFieldName(availableSourceFields[i]) && !field.isDeleted
        )
        
        // 找到目标字段在完整列表中的索引
        const targetIndex = orderedTargetFields.value.findIndex(field => 
          getFieldName(field) === getFieldName(availableTargetFields[i]) && !field.isDeleted
        )
        
        if (sourceIndex !== -1 && targetIndex !== -1) {
          positionMappings.value.push({
            sourceIndex,
            targetIndex
          })
        }
      }
      
      // 更新连接线
      nextTick(() => {
        updateConnections()
      })
      
      ElMessage.success(`已自动建立 ${positionMappings.value.length} 个字段映射`)
    }
    
    // 全局设定相关方法
    const onModeChange = (newMode) => {
      if (newMode === 'insert') {
        // 切换到新增模式时清空更新条件
        globalSettings.updateConditions = []
      }
    }
    
    // 验证覆盖模式的更新条件
    const validateUpdateConditions = () => {
      if (globalSettings.mode === 'update') {
        if (globalSettings.updateConditions.length === 0) {
          ElMessage.error('覆盖模式下至少需要选择一个更新条件字段')
          return false
        }
        
        // 检查选择的更新条件字段是否都已配置映射
        const unmappedConditions = globalSettings.updateConditions.filter(conditionField => {
          return !mappedTargetFields.value.some(field => field.name === conditionField)
        })
        
        if (unmappedConditions.length > 0) {
          ElMessage.error(`以下作为更新条件的字段没有配置映射：${unmappedConditions.join(', ')}`)
          return false
        }
      }
      return true
    }
    
    // 生成表达式
    const generateExpression = () => {
      switch (sourceFieldForm.generateType) {
        case 'constant':
          return `'${sourceFieldForm.constantValue}'`
        case 'uuid':
          return 'UUID()'
        case 'snowflake':
          return 'snowid()'
        case 'concat': {
          const fields = sourceFieldForm.concatFields.map(field => `COALESCE(${field}, '')`).join(', ')
          const separator = sourceFieldForm.separator ? `'${sourceFieldForm.separator}'` : "''"
          return `CONCAT(${fields.split(', ').join(`, ${separator}, `)})`
        }
        case 'condition': {
          const condition = sourceFieldForm.conditionOperator === 'IS NULL' || sourceFieldForm.conditionOperator === 'IS NOT NULL'
            ? `${sourceFieldForm.conditionField} ${sourceFieldForm.conditionOperator}`
            : `${sourceFieldForm.conditionField} ${sourceFieldForm.conditionOperator} '${sourceFieldForm.conditionValue}'`
          return `CASE WHEN ${condition} THEN '${sourceFieldForm.trueValue}' ELSE '${sourceFieldForm.falseValue}' END`
        }
        case 'case_when': {
          const branches = sourceFieldForm.caseBranches.map(branch => {
            const branchCondition = branch.operator === 'IS NULL' || branch.operator === 'IS NOT NULL'
              ? `${sourceFieldForm.caseWhenField} ${branch.operator}`
              : `${sourceFieldForm.caseWhenField} ${branch.operator} '${branch.condition}'`
            return `WHEN ${branchCondition} THEN '${branch.value}'`
          }).join(' ')
          return `CASE ${branches} ELSE '${sourceFieldForm.defaultValue}' END`
        }
        case 'math':
          return sourceFieldForm.mathExpression
        case 'date': {
          if (sourceFieldForm.dateInterval) {
            return `DATE_FORMAT(DATE_ADD(${sourceFieldForm.dateFunction}, INTERVAL ${sourceFieldForm.dateInterval}), '${sourceFieldForm.dateFormat}')`
          }
          return `DATE_FORMAT(${sourceFieldForm.dateFunction}, '${sourceFieldForm.dateFormat}')`
        }
        default:
          return ''
      }
    }
    
    // 生成样本结果
    const generateSampleResult = () => {
      switch (sourceFieldForm.generateType) {
        case 'constant':
          return sourceFieldForm.constantValue
        case 'uuid':
          return '550e8400-e29b-41d4-a716-446655440000'
        case 'snowflake':
          return '1234567890123456789'
        case 'concat':
          return sourceFieldForm.concatFields.map(field => `[${field}]`).join(sourceFieldForm.separator || '')
        case 'condition':
          return `[${sourceFieldForm.trueValue}/${sourceFieldForm.falseValue}]`
        case 'case_when':
          return sourceFieldForm.caseBranches.length > 0 ? sourceFieldForm.caseBranches[0].value : sourceFieldForm.defaultValue
        case 'math':
          return '[计算结果]'
        case 'date':
          return new Date().toISOString().slice(0, 19).replace('T', ' ')
        default:
          return ''
      }
    }
    
    // 添加case分支
    const addCaseBranch = () => {
      sourceFieldForm.caseBranches.push({
        operator: '=',
        condition: '',
        value: ''
      })
    }
    
    // 删除case分支
    const removeCaseBranch = (index) => {
      sourceFieldForm.caseBranches.splice(index, 1)
    }
    
    // 生成默认映射
    const generateDefaultMapping = () => {
      console.log('FieldMapping.generateDefaultMapping: 开始生成默认映射')
      console.log('- 当前源字段数量:', orderedSourceFields.value.length)
      console.log('- 当前目标字段数量:', orderedTargetFields.value.length)
      console.log('- 当前源字段详情:', JSON.stringify(orderedSourceFields.value))
      console.log('- 当前目标字段详情:', JSON.stringify(orderedTargetFields.value))
      
      if (props.configId) {
        // 如果有配置ID，不生成默认映射
        console.log('FieldMapping.generateDefaultMapping: 检测到configId，跳过默认映射生成')
        return
      }
      
      // 清空现有映射
      positionMappings.value = []
      
      // 获取可用的源字段和目标字段
      const availableSourceFields = orderedSourceFields.value.filter(field => !field.isDeleted)
      const availableTargetFields = orderedTargetFields.value.filter(field => !field.isDeleted)
      
      console.log('- 可用源字段数量:', availableSourceFields.length)
      console.log('- 可用目标字段数量:', availableTargetFields.length)
      
      // 按顺序建立1:1映射关系
      const maxMappings = Math.min(availableSourceFields.length, availableTargetFields.length)
      console.log('- 最大可映射数量:', maxMappings)
      
      // 检查字段是否包含索引信息
      const hasSourceIndexInfo = availableSourceFields.some(field => field.sourceIndex !== undefined)
      const hasTargetIndexInfo = availableTargetFields.some(field => field.targetIndex !== undefined)
      console.log('- 源字段包含索引信息:', hasSourceIndexInfo)
      console.log('- 目标字段包含索引信息:', hasTargetIndexInfo)
      
      if (hasSourceIndexInfo && hasTargetIndexInfo) {
        console.log('- 使用字段索引信息生成映射')
        // 如果源字段和目标字段都包含索引信息，则按索引匹配
        for (let i = 0; i < maxMappings; i++) {
          const sourceField = availableSourceFields[i]
          const targetField = availableTargetFields[i]
          
          // 获取字段在原始数组中的索引
          const sourceIndex = orderedSourceFields.value.findIndex(field => 
            getFieldName(field) === getFieldName(sourceField) && !field.isDeleted
          )
          
          const targetIndex = orderedTargetFields.value.findIndex(field => 
            getFieldName(field) === getFieldName(targetField) && !field.isDeleted
          )
          
          console.log(`- 映射[${i}]: 源字段=${getFieldName(sourceField)}(索引=${sourceIndex}), 目标字段=${getFieldName(targetField)}(索引=${targetIndex})`)
          
          if (sourceIndex !== -1 && targetIndex !== -1) {
            positionMappings.value.push({
              sourceIndex,
              targetIndex
            })
          }
        }
      } else {
        console.log('- 使用字段顺序生成映射')
        // 如果字段不包含索引信息，则按顺序匹配
        for (let i = 0; i < maxMappings; i++) {
          const sourceIndex = orderedSourceFields.value.findIndex(field => 
            getFieldName(field) === getFieldName(availableSourceFields[i]) && !field.isDeleted
          )
          
          const targetIndex = orderedTargetFields.value.findIndex(field => 
            getFieldName(field) === getFieldName(availableTargetFields[i]) && !field.isDeleted
          )
          
          console.log(`- 映射[${i}]: 源字段索引=${sourceIndex}, 目标字段索引=${targetIndex}`)
          
          if (sourceIndex !== -1 && targetIndex !== -1) {
            positionMappings.value.push({
              sourceIndex,
              targetIndex
            })
          }
        }
      }
      
      console.log('- 生成的映射关系:', JSON.stringify(positionMappings.value))
      
      // 更新连接线
      nextTick(() => {
        updateConnections()
      })
    }
    
    // 从API加载配置
    const loadConfigFromApi = async () => {
      if (!props.configId) {
        return
      }
      
      try {
        const response = await configApi.getConfigDetail(props.configId)
        if (response.data && response.data.fieldMappings) {
          // 恢复字段映射配置
          const mappings = response.data.fieldMappings
          positionMappings.value = mappings.map(mapping => ({
            sourceIndex: mapping.sourceIndex,
            targetIndex: mapping.targetIndex
          }))
          
          // 从field_mappings中识别和恢复自定义字段
          const customFieldsFromMappings = mappings
            .filter(mapping => mapping.isCustom || mapping.generateType) // 通过isCustom或generateType标识自定义字段
            .map(mapping => ({
              name: mapping.sourceName,
              type: mapping.sourceType || 'VARCHAR',
              isCustom: true,
              // 生成/自定义字段参数完整恢复
              generateType: mapping.generateType || 'constant',
              expression: mapping.expression || '',
              dateFormat: mapping.dateFormat || '',
              dateFunction: mapping.dateFunction || '',
              dateInterval: mapping.dateInterval || '',
              defaultValue: mapping.defaultValue || '',
              constantValue: mapping.constantValue || '',
              parameterName: mapping.parameterName || '',
              separator: mapping.separator || '',
              trueValue: mapping.trueValue || '',
              falseValue: mapping.falseValue || '',
              caseBranches: mapping.caseBranches || [],
              concatFields: mapping.concatFields || [],
              sample: mapping.sample || '',
              conditionField: mapping.conditionField || '',
              conditionValue: mapping.conditionValue || '',
              conditionOperator: mapping.conditionOperator || '=',
              mathExpression: mapping.mathExpression || '',
              isDeleted: mapping.isDeleted || false
            }))
          
          // 将自定义字段添加到源字段列表
          customFieldsFromMappings.forEach(customField => {
            orderedSourceFields.value.push(customField)
          })
          
          // 兼容性处理：如果还有单独的custom_fields，也要处理（向后兼容）
          if (response.data.custom_fields) {
            response.data.custom_fields.forEach(field => {
              // 确保自定义字段有isCustom标记且不重复
              const customField = {
                ...field,
                isCustom: true
              }
              // 检查是否已存在同名字段
              if (!orderedSourceFields.value.some(existingField => existingField.name === customField.name)) {
                orderedSourceFields.value.push(customField)
              }
            })
          }
          
          nextTick(() => {
            updateConnections()
          })
        }
      } catch (error) {
        console.error('加载配置失败:', error)
      }
    }
    
    // 从模板加载配置
    const loadTemplateConfig = async (templateId) => {
      try {
        console.log('FieldMapping组件正在加载模板配置，templateId:', templateId)
        
        // 注释：移除props字段数据检查，确保总是尝试从数据库加载字段映射配置

        // 直接加载模板详情（包含完整的 field_mappings 与 custom_fields）
        const response = await templateApi.getTemplateDetail(templateId)
        
        if (response && response.success && response.data) {
          const templateData = response.data
          console.log('FieldMapping组件成功获取模板数据:', templateData)
          
          // 构建目标配置对象并保存到store（与TargetConfig.vue保持一致）
          const targetConfig = {
            id: templateId,
            name: templateData.name || '模板配置',
            description: templateData.description || '从模板加载的配置',
            created_at: templateData.created_at || new Date().toISOString(),
            // 如果有目标数据库配置，也保存进来
            database: templateData.target_database || {},
            table: templateData.target_table || '',
            // 保留原始模板数据用于字段映射恢复
            templateData: templateData
          }
          
          // 保存模板配置到store
          store.commit('SET_TARGET_CONFIG', targetConfig)
          
          // 始终优先使用模板中的字段映射；仅当模板中没有映射时再尝试数据库映射
          let fieldMappingsToUse = Array.isArray(templateData.field_mappings) && templateData.field_mappings.length > 0
            ? templateData.field_mappings
            : []
          // 保留一次数据库回退响应以提取可能的全局设置
          let mappingDataForFallback = null

          // 如果模板中没有字段映射，作为回退再尝试获取数据库中的简单映射（不含自定义参数）
          if (fieldMappingsToUse.length === 0) {
            try {
              const mappingResponse = await fetch(`/api/get-mapping/${templateId}`)
              if (mappingResponse.ok) {
                const mappingData = await mappingResponse.json()
                if (mappingData.success && Array.isArray(mappingData.mappings) && mappingData.mappings.length > 0) {
                  fieldMappingsToUse = mappingData.mappings
                  mappingDataForFallback = mappingData
                  console.log('FieldMapping组件使用数据库回退映射（模板无映射时）:', fieldMappingsToUse)
                }
              }
            } catch (error) {
              console.warn('数据库回退映射获取失败，继续使用模板数据:', error)
            }
          }
          
          // 确保目标字段不为空 - 如果当前目标字段为空，尝试从props获取
          if (orderedTargetFields.value.length === 0 && props.targetFields && props.targetFields.length > 0) {
            console.log('FieldMapping组件目标字段为空，从props重新获取:', props.targetFields.length)
            orderedTargetFields.value = [...props.targetFields]
          }
          
          // 注意：不再从字段映射中提取源字段，源字段应该来自预览数据
          // 源字段保持从DataSourceConfig传入的预览字段，目标字段保持完整的目标表字段
          console.log('FieldMapping组件保留预览的源字段列表，字段数量:', orderedSourceFields.value.length)
          console.log('FieldMapping组件保留完整的目标字段列表，字段数量:', orderedTargetFields.value.length)
          console.log('FieldMapping组件当前源字段:', orderedSourceFields.value)
          console.log('FieldMapping组件当前目标字段:', orderedTargetFields.value)
          
          // 从field_mappings中识别和恢复自定义字段
          if (fieldMappingsToUse && Array.isArray(fieldMappingsToUse)) {
            console.log('🔥 loadConfigFromApi: 从field_mappings识别自定义字段')
            
            // 从field_mappings中提取自定义字段
            const customFieldsFromMappings = fieldMappingsToUse
              .filter(mapping => mapping.isCustom || mapping.generateType) // 通过isCustom或generateType标识自定义字段
              .map(mapping => ({
                name: mapping.sourceName,
                type: mapping.sourceType || 'VARCHAR',
                isCustom: true,
                // 生成/自定义字段参数完整恢复
                generateType: mapping.generateType || 'constant',
                expression: mapping.expression || '',
                dateFormat: mapping.dateFormat || '',
                dateFunction: mapping.dateFunction || '',
                dateInterval: mapping.dateInterval || '',
                defaultValue: mapping.defaultValue || '',
                constantValue: mapping.constantValue || '',
                parameterName: mapping.parameterName || '',
                separator: mapping.separator || '',
                trueValue: mapping.trueValue || '',
                falseValue: mapping.falseValue || '',
                caseBranches: mapping.caseBranches || [],
                concatFields: mapping.concatFields || [],
                sample: mapping.sample || '',
                conditionField: mapping.conditionField || '',
                conditionValue: mapping.conditionValue || '',
                conditionOperator: mapping.conditionOperator || '=',
                mathExpression: mapping.mathExpression || '',
                isDeleted: mapping.isDeleted || false
              }))
            
            console.log('🔥 loadConfigFromApi: 从field_mappings提取的自定义字段:', JSON.stringify(customFieldsFromMappings))
            
            // 过滤掉已存在的同名字段，避免重复添加
            const newCustomFields = customFieldsFromMappings.filter(customField => 
              !orderedSourceFields.value.some(existingField => existingField.name === customField.name)
            )
            
            // 将不重复的自定义字段添加到源字段列表
            orderedSourceFields.value = [...orderedSourceFields.value, ...newCustomFields]
            console.log('🔥 loadConfigFromApi: 添加自定义字段后的源字段列表:', JSON.stringify(orderedSourceFields.value))
          }
          
          // 兼容性处理：如果还有单独的custom_fields，也要处理（向后兼容）
          if (templateData.custom_fields && Array.isArray(templateData.custom_fields)) {
            console.log('🔥 loadConfigFromApi: 兼容处理单独的custom_fields')
            
            const customFields = templateData.custom_fields.map(field => ({
              ...field,
              isCustom: true
            }))
            
            // 过滤掉已存在的同名字段，避免重复添加
            const newCustomFields = customFields.filter(customField => 
              !orderedSourceFields.value.some(existingField => existingField.name === customField.name)
            )
            
            // 将不重复的自定义字段添加到源字段列表
            orderedSourceFields.value = [...orderedSourceFields.value, ...newCustomFields]
          }
          
          // 延迟恢复映射，确保所有字段都已经加载完成
          nextTick(() => {
            // 如果有字段映射配置，按映射关系重新排序字段
            if (fieldMappingsToUse && Array.isArray(fieldMappingsToUse)) {

              
              const mappings = fieldMappingsToUse
              const allSourceFields = [...orderedSourceFields.value]
              const allTargetFields = [...orderedTargetFields.value]
              
              // 按映射关系重新排序字段
              const orderedSourceFieldsFromMapping = []
              const orderedTargetFieldsFromMapping = []
              const newMappings = []
              
              mappings.forEach((mappingItem) => {
                // 处理源字段 - 通过名称查找
                let sourceField = allSourceFields.find(f => getFieldName(f) === mappingItem.sourceName)
                
                // 如果源字段不存在且是自定义字段，从映射中恢复
                if (!sourceField && (mappingItem.isCustom || mappingItem.generateType)) {
                  sourceField = {
                    name: mappingItem.sourceName,
                    type: mappingItem.sourceType || 'VARCHAR',
                    isCustom: true,
                    // 完整恢复映射里的所有自定义参数
                    generateType: mappingItem.generateType || 'constant',
                    expression: mappingItem.expression || '',
                    dateFormat: mappingItem.dateFormat || '',
                    dateFunction: mappingItem.dateFunction || '',
                    dateInterval: mappingItem.dateInterval || '',
                    defaultValue: mappingItem.defaultValue || '',
                    constantValue: mappingItem.constantValue || '',
                    parameterName: mappingItem.parameterName || '',
                    separator: mappingItem.separator || '',
                    trueValue: mappingItem.trueValue || '',
                    falseValue: mappingItem.falseValue || '',
                    caseBranches: mappingItem.caseBranches || [],
                    concatFields: mappingItem.concatFields || [],
                    sample: mappingItem.sample || '',
                    conditionField: mappingItem.conditionField || '',
                    conditionValue: mappingItem.conditionValue || '',
                    conditionOperator: mappingItem.conditionOperator || '=',
                    mathExpression: mappingItem.mathExpression || '',
                    isDeleted: mappingItem.isDeleted || false
                  }
                }
                
                // 处理目标字段 - 通过名称查找
                const targetField = allTargetFields.find(f => getFieldName(f) === mappingItem.targetName)
                
                // 如果目标字段不存在，记录警告但不影响其他字段的处理
                if (!targetField) {
                  console.warn(`目标字段 '${mappingItem.targetName}' 在当前目标字段列表中不存在，跳过此映射`)
                }
                
                // 只有当源字段和目标字段都存在时才建立映射
                if (sourceField && targetField) {
                  // 检查是否为自定义字段（通过isCustom或generateType判断）
                  if (mappingItem.isCustom || mappingItem.generateType) {
                    // 更新字段属性而不是替换整个对象，确保保留原有的isCustom等属性
                    sourceField.isCustom = true
                    sourceField.generateType = mappingItem.generateType || 'constant'
                    sourceField.expression = mappingItem.expression || ''
                    sourceField.dateFormat = mappingItem.dateFormat || ''
                    sourceField.dateFunction = mappingItem.dateFunction || ''
                    sourceField.dateInterval = mappingItem.dateInterval || ''
                    sourceField.defaultValue = mappingItem.defaultValue || ''
                    sourceField.constantValue = mappingItem.constantValue || ''
                    sourceField.parameterName = mappingItem.parameterName || ''
                    sourceField.separator = mappingItem.separator || ''
                    sourceField.trueValue = mappingItem.trueValue || ''
                    sourceField.falseValue = mappingItem.falseValue || ''
                    sourceField.caseBranches = mappingItem.caseBranches || []
                    sourceField.concatFields = mappingItem.concatFields || []
                    sourceField.sample = mappingItem.sample || ''
                    sourceField.conditionField = mappingItem.conditionField || ''
                    sourceField.conditionValue = mappingItem.conditionValue || ''
                    sourceField.conditionOperator = mappingItem.conditionOperator || '='
                    sourceField.mathExpression = mappingItem.mathExpression || ''
                    sourceField.isDeleted = mappingItem.isDeleted || false
                  }
                  
                  // 确保自定义字段保留完整属性
                  if (sourceField.isCustom) {
                    // 查找原始自定义字段以保留完整属性
                    const originalCustomField = allSourceFields.find(f => f.isCustom && f.name === sourceField.name)
                    if (originalCustomField) {
                      // 保留原始自定义字段的所有属性，只更新必要的映射相关属性
                      orderedSourceFieldsFromMapping.push({
                        ...originalCustomField,
                        // 覆盖映射中提供的所有自定义属性
                        generateType: mappingItem.generateType || originalCustomField.generateType,
                        expression: mappingItem.expression || originalCustomField.expression,
                        dateFormat: mappingItem.dateFormat || originalCustomField.dateFormat,
                        dateFunction: mappingItem.dateFunction || originalCustomField.dateFunction,
                        dateInterval: mappingItem.dateInterval || originalCustomField.dateInterval,
                        defaultValue: mappingItem.defaultValue || originalCustomField.defaultValue,
                        constantValue: mappingItem.constantValue || originalCustomField.constantValue,
                        parameterName: mappingItem.parameterName || originalCustomField.parameterName,
                        separator: mappingItem.separator || originalCustomField.separator,
                        trueValue: mappingItem.trueValue || originalCustomField.trueValue,
                        falseValue: mappingItem.falseValue || originalCustomField.falseValue,
                        caseBranches: mappingItem.caseBranches || originalCustomField.caseBranches,
                        concatFields: mappingItem.concatFields || originalCustomField.concatFields,
                        sample: mappingItem.sample || originalCustomField.sample,
                        conditionField: mappingItem.conditionField || originalCustomField.conditionField,
                        conditionValue: mappingItem.conditionValue || originalCustomField.conditionValue,
                        conditionOperator: mappingItem.conditionOperator || originalCustomField.conditionOperator,
                        mathExpression: mappingItem.mathExpression || originalCustomField.mathExpression,
                        // 兼容旧版Babel，不使用 nullish 合并运算符
                        isDeleted: (mappingItem.isDeleted !== undefined ? mappingItem.isDeleted : originalCustomField.isDeleted)
                      })
                    } else {
                      orderedSourceFieldsFromMapping.push({
                        ...sourceField,
                        isCustom: true
                      })
                    }
                  } else {
                    orderedSourceFieldsFromMapping.push(sourceField)
                  }
                  
                  orderedTargetFieldsFromMapping.push(targetField)
                  
                  // 创建映射关系（使用当前在排序后数组中的索引）
                  newMappings.push({
                    sourceIndex: orderedSourceFieldsFromMapping.length - 1,
                    targetIndex: orderedTargetFieldsFromMapping.length - 1
                  })
                } else {
                  // 如果源字段或目标字段不存在，跳过此映射并记录日志
                  console.warn(`跳过映射：源字段 '${mappingItem.sourceName}' 或目标字段 '${mappingItem.targetName}' 不存在`)
                }
              })
              
              // 添加未映射的源字段到末尾，确保保留自定义字段的isCustom属性
              const mappedSourceNames = new Set(mappings.map(m => m.sourceName))
              allSourceFields.forEach(field => {
                if (!mappedSourceNames.has(getFieldName(field))) {
                  // 确保自定义字段保留isCustom属性
                  if (field.isCustom) {
                    orderedSourceFieldsFromMapping.push({
                      ...field,
                      isCustom: true
                    })
                  } else {
                    orderedSourceFieldsFromMapping.push(field)
                  }
                }
              })
              
              // 确保所有目标字段都保留，不管是否有映射关系
              // 首先添加所有现有的目标字段
              const addedTargetNames = new Set(orderedTargetFieldsFromMapping.map(f => getFieldName(f)))
              allTargetFields.forEach(field => {
                if (!addedTargetNames.has(getFieldName(field))) {
                  orderedTargetFieldsFromMapping.push(field)
                }
              })
              
              // 确保orderedSourceFieldsFromMapping中的自定义字段保留完整属性
              const enhancedSourceFields = orderedSourceFieldsFromMapping.map(field => {
                if (field.isCustom) {
                  // 查找原始自定义字段以保留完整属性（使用allSourceFields而不是orderedSourceFields.value）
                  const originalCustomField = allSourceFields.find(f => f.isCustom && f.name === field.name)
                  if (originalCustomField) {
                    return { ...originalCustomField, ...field }
                  }
                }
                return field
              })
              
              // 保留当前已存在但不在映射恢复列表中的自定义字段，避免重复
              // 同时检查是否与目标字段重名，避免与目标表字段冲突
              const existingCustomFields = orderedSourceFields.value.filter(f => {
                const isCustomAndNotInMapping = f.isCustom && !enhancedSourceFields.some(enhanced => enhanced.name === f.name)
                const notConflictWithTarget = !orderedTargetFieldsFromMapping.some(target => target.name === f.name)
                return isCustomAndNotInMapping && notConflictWithTarget
              })
              console.log('🔥 loadConfigFromApi: 保留的现有自定义字段:', JSON.stringify(existingCustomFields))
              
              // 更新字段列表和映射关系，合并现有自定义字段
              orderedSourceFields.value = [...enhancedSourceFields, ...existingCustomFields]
              console.log('🔥 loadTemplateConfig: 准备设置目标字段，orderedTargetFieldsFromMapping长度:', orderedTargetFieldsFromMapping.length)
              console.log('🔥 loadTemplateConfig: orderedTargetFieldsFromMapping内容:', orderedTargetFieldsFromMapping)
              
              // 保护机制：如果处理后的目标字段为空，保留原有的目标字段
              if (orderedTargetFieldsFromMapping.length > 0) {
                orderedTargetFields.value = orderedTargetFieldsFromMapping
                console.log('🔥 loadTemplateConfig: 使用处理后的目标字段，长度:', orderedTargetFields.value.length)
              } else {
                console.log('🔥 loadTemplateConfig: 处理后的目标字段为空，保留原有目标字段，长度:', orderedTargetFields.value.length)
              }
              
              positionMappings.value = newMappings
              
              console.log('🔥 loadConfigFromApi: 字段映射恢复后的最终源字段列表:', JSON.stringify(orderedSourceFields.value))
              console.log('🔥 loadConfigFromApi: 自定义字段数量:', orderedSourceFields.value.filter(f => f.isCustom).length)
              
              // 加载全局设定 - 优先使用模板的global_settings；如无则尝试数据库回退响应中的global_settings
              const globalSettingsToUse = (templateData.global_settings && Object.keys(templateData.global_settings).length > 0)
                ? templateData.global_settings
                : ((mappingDataForFallback && mappingDataForFallback.global_settings) ? mappingDataForFallback.global_settings : null)
              if (globalSettingsToUse) {
                globalSettings.mode = globalSettingsToUse.mode || 'insert'
                globalSettings.updateConditions = globalSettingsToUse.update_conditions || []
                console.log('FieldMapping组件加载全局设定:', globalSettingsToUse)
              }
              
              // 同时保存到store
              store.commit('SET_FIELD_MAPPINGS', newMappings)
              

            } else {
              // 没有字段映射配置时，确保目标字段不会丢失
              console.log('🔥 loadTemplateConfig: 没有字段映射配置，保持现有字段不变')
              console.log('🔥 loadTemplateConfig: 当前目标字段数量:', orderedTargetFields.value.length)
            }
            
            // 更新连接线
            nextTick(() => {
              updateConnections()
            })
          })
          

          
          ElMessage.success('模板配置加载成功')
        } else {
          console.error('模板数据格式错误:', response)
          ElMessage.error('模板数据格式错误')
        }
      } catch (error) {
        console.error('加载模板配置失败:', error)
        ElMessage.error('加载模板配置失败: ' + error.message)
      }
    }
    
    const saveMappings = async () => {
      if (!canProceed.value) {
        ElMessage.warning('请先配置字段映射')
        return
      }
      
      // 验证全局设定
      if (!validateUpdateConditions()) {
        return
      }
      
      try {
        // 构建映射数据，将自定义字段信息直接集成到field_mappings中
        const mappingData = positionMappings.value.map(mapping => {
          const sourceField = orderedSourceFields.value[mapping.sourceIndex]
          const targetField = orderedTargetFields.value[mapping.targetIndex]
          
          if (!sourceField || !targetField) return null
          
          const mappingItem = {
            sourceName: getFieldName(sourceField),
            targetName: getFieldName(targetField),
            sourceIndex: mapping.sourceIndex,
            targetIndex: mapping.targetIndex,
            sourceType: getFieldType(sourceField),
            targetType: getFieldType(targetField)
          }
          
          // 如果是自定义字段，添加自定义字段的所有属性
          if (sourceField.isCustom) {
            mappingItem.isCustom = true
            mappingItem.generateType = sourceField.generateType
            mappingItem.expression = sourceField.expression || ''
            mappingItem.dateFormat = sourceField.dateFormat || ''
            mappingItem.dateFunction = sourceField.dateFunction || ''
            mappingItem.dateInterval = sourceField.dateInterval || ''
            mappingItem.defaultValue = sourceField.defaultValue || ''
            mappingItem.constantValue = sourceField.constantValue || ''
            
            // 自动设置parameterName：如果generateType为external_param且parameterName为空，则使用字段名
            if (sourceField.generateType === 'external_param' && !sourceField.parameterName) {
              mappingItem.parameterName = sourceField.name
              console.log(`自动设置external_param字段 '${sourceField.name}' 的parameterName为: ${sourceField.name}`)
            } else {
              mappingItem.parameterName = sourceField.parameterName || ''
            }
            
            mappingItem.conditionField = sourceField.conditionField || ''
            mappingItem.conditionValue = sourceField.conditionValue || ''
            mappingItem.conditionOperator = sourceField.conditionOperator || '='
            mappingItem.mathExpression = sourceField.mathExpression || ''
            mappingItem.separator = sourceField.separator || ''
            mappingItem.trueValue = sourceField.trueValue || ''
            mappingItem.falseValue = sourceField.falseValue || ''
            mappingItem.caseBranches = sourceField.caseBranches || []
            mappingItem.concatFields = sourceField.concatFields || []
            mappingItem.sample = sourceField.sample || ''
          }
          
          return mappingItem
        }).filter(mapping => mapping !== null)
        
        // 保存到 store - 映射数据已包含自定义字段信息
        store.commit('SET_FIELD_MAPPINGS', mappingData)
        store.commit('SET_GLOBAL_SETTINGS', {
          mode: globalSettings.mode,
          updateConditions: globalSettings.updateConditions
        })
        
        // 使用动态获取的模板ID保存到服务端
        const route = getCurrentInstance()?.proxy?.$route
        const templateId = route?.query?.templateId || props.templateId || props.configId || store.state.targetConfig?.id
        
        // 验证templateId是否存在
        if (!templateId) {
          ElMessage.error('无法获取模板ID，请确保在正确的模板配置页面中操作')
          return
        }
        
        // 提取自定义字段信息
        const customFields = orderedSourceFields.value
          .filter(field => field.isCustom)
          .map(field => {
            // 自动设置parameterName：如果generateType为external_param且parameterName为空，则使用字段名
            let parameterName = field.parameterName || ''
            if (field.generateType === 'external_param' && !parameterName) {
              parameterName = field.name
              console.log(`自动设置custom_fields中external_param字段 '${field.name}' 的parameterName为: ${field.name}`)
            }
            
            return {
              name: field.name,
              type: field.type || 'VARCHAR',
              sample: field.sample || '',
              isCustom: true,
              separator: field.separator || '',
              trueValue: field.trueValue || '',
              dateFormat: field.dateFormat || '%Y-%m-%d %H:%i:%s',
              expression: field.expression || '',
              falseValue: field.falseValue || '',
              caseBranches: field.caseBranches || [],
              concatFields: field.concatFields || [],
              dateFunction: field.dateFunction || 'NOW()',
              dateInterval: field.dateInterval || '',
              defaultValue: field.defaultValue || '',
              generateType: field.generateType || 'constant',
              constantValue: field.constantValue || '',
              parameterName: parameterName,
              conditionField: field.conditionField || '',
              conditionValue: field.conditionValue || '',
              mathExpression: field.mathExpression || '',
              conditionOperator: field.conditionOperator || '=',
              isDeleted: field.isDeleted || false
            }
          })
        
        // 构建保存到模板的数据 - 自定义字段信息已集成到field_mappings中
        console.log('🔥 saveMappings: 保存前的源字段列表:', JSON.stringify(orderedSourceFields.value))
        console.log('🔥 saveMappings: 构建的映射数据(包含自定义字段):', JSON.stringify(mappingData))
        console.log('🔥 saveMappings: 提取的自定义字段:', JSON.stringify(customFields))
        
        const templateUpdateData = {
          field_mappings: mappingData,
          custom_fields: customFields,
          global_settings: {
            mode: globalSettings.mode,
            update_conditions: globalSettings.updateConditions,
            file_type: store.state.sourceConfig?.file_type || props.sourceConfig?.file_type || 'excel'
          }
        }
        
        console.log('🔥 saveMappings: 发送到后端的数据:', JSON.stringify(templateUpdateData))
        
        try {
          // 使用PUT方法更新模板的field_mappings字段
          await templateApi.updateTemplate(templateId, templateUpdateData)
          ElMessage.success('字段映射已保存到模板')

        } catch (error) {
          console.error('保存到模板失败:', error)
          ElMessage.error('保存到模板失败: ' + (error.message || '未知错误'))
        }
        
      } catch (error) {
        console.error('保存字段映射失败:', error)
        ElMessage.error('保存失败: ' + error.message)
      }
    }
    
    const saveMappingsOnly = async () => {
      await saveMappings()
    }
    
    const nextStep = async () => {
      await saveMappings()
      
      // 构建映射数据并触发下一步事件
      const mappingData = {
        fieldMappings: positionMappings.value.map(mapping => {
          const sourceField = orderedSourceFields.value[mapping.sourceIndex]
          const targetField = orderedTargetFields.value[mapping.targetIndex]
          
          if (!sourceField || !targetField) return null
          
          return {
            sourceField: getFieldName(sourceField),
            targetField: getFieldName(targetField),
            sourceIndex: mapping.sourceIndex,
            targetIndex: mapping.targetIndex,
            sourceFieldType: getFieldType(sourceField),
            targetFieldType: getFieldType(targetField),
            isCustomSource: sourceField.isCustom || false,
            expression: sourceField.expression || null
          }
        }).filter(mapping => mapping !== null),
        customFields: orderedSourceFields.value.filter(field => field.isCustom).map(field => ({
          name: field.name,
          type: field.type,
          sample: field.sample || '',
          isCustom: true,
          separator: field.separator || '',
          trueValue: field.trueValue || '',
          dateFormat: field.dateFormat || '%Y-%m-%d %H:%i:%s',
          expression: field.expression || '',
          falseValue: field.falseValue || '',
          caseBranches: field.caseBranches || [],
          concatFields: field.concatFields || [],
          dateFunction: field.dateFunction || 'NOW()',
          dateInterval: field.dateInterval || '',
          defaultValue: field.defaultValue || '',
          generateType: field.generateType || 'constant',
          constantValue: field.constantValue || '',
          parameterName: field.parameterName || '',
          conditionField: field.conditionField || '',
          conditionValue: field.conditionValue || '',
          mathExpression: field.mathExpression || '',
          conditionOperator: field.conditionOperator || '='
        })),
        globalSettings: {
          mode: globalSettings.mode,
          updateConditions: globalSettings.updateConditions
        }
      }
      
      // 保存到store - 使用新的数据结构
      store.commit('SET_FIELD_MAPPINGS', {
        mappings: mappingData.fieldMappings,
        customFields: mappingData.customFields
      })
      
      emit('next-step', mappingData)
    }
    
    const previewSeaTunnelConfig = async () => {
      configPreviewLoading.value = true
      try {
        const requestData = {
          source: props.sourceConfig,
          target: props.targetConfig,
          mappings: positionMappings.value
        }
        
        const response = await generateApi.generateConfigPreview(requestData)
        
        if (response && response.success && response.config) {
          configPreviewContent.value = response.config
          showConfigPreview.value = true
        } else {
          ElMessage.error(response?.message || '生成配置失败')
        }
      } catch (error) {
        ElMessage.error('预览配置失败: ' + error.message)
      } finally {
        configPreviewLoading.value = false
      }
    }
    
    const copyConfigContent = async () => {
      try {
        await navigator.clipboard.writeText(configPreviewContent.value || '')
        ElMessage.success('配置内容已复制到剪贴板')
      } catch (error) {
        ElMessage.error('复制失败: ' + error.message)
      }
    }
    
    const downloadConfig = () => {
      const content = configPreviewContent.value || ''
      const blob = new Blob([content], { type: 'text/plain' })
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = 'seatunnel-config.conf'
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
      URL.revokeObjectURL(url)
    }
    
    // 格式化日期显示
    const formatDate = (dateString) => {
      if (!dateString) return '未知'
      const date = new Date(dateString)
      return date.toLocaleString('zh-CN', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit'
      })
    }
    
    // 获取文件类型显示文本
    const getFileTypeDisplay = () => {
      // 优先从props.sourceConfig获取file_type
      if (props.sourceConfig?.file_type) {
        return props.sourceConfig.file_type === 'minio' ? 'MinIO存储' : 
               props.sourceConfig.file_type === 'excel' ? 'Excel文件' : 
               props.sourceConfig.file_type
      }
      
      // 从store中获取
      const storeConfig = store.state.sourceConfig
      if (storeConfig?.file_type) {
        return storeConfig.file_type === 'minio' ? 'MinIO存储' : 
               storeConfig.file_type === 'excel' ? 'Excel文件' : 
               storeConfig.file_type
      }
      
      // 兼容旧的配置结构
      if (storeConfig?.fileConfig?.fileType) {
        return storeConfig.fileConfig.fileType === 'excel' ? 'Excel文件' : storeConfig.fileConfig.fileType
      }
      
      return '未知'
    }
    
    // 监听映射变化，自动清理无效的更新条件
    watch(positionMappings, () => {
      if (globalSettings.mode === 'update') {
        // 过滤掉已经不存在映射的更新条件字段
        const validConditions = globalSettings.updateConditions.filter(conditionField => {
          return mappedTargetFields.value.some(field => field.name === conditionField)
        })
        globalSettings.updateConditions = validConditions
      }
    }, { deep: true })
    
    // 监听字段变化
    watch([() => props.sourceFields, () => props.targetFields], ([newSourceFields, newTargetFields]) => {
      console.log('FieldMapping接收到新的源字段:', newSourceFields)
      console.log('FieldMapping接收到新的目标字段:', newTargetFields)
      
      let fieldsUpdated = false
      
      // 只有当新字段不为空时才更新
      if (newSourceFields && newSourceFields.length > 0) {
        console.log('FieldMapping组件更新源字段列表，字段数量:', newSourceFields.length)
        orderedSourceFields.value = [...newSourceFields]
        fieldsUpdated = true
      }
      
      if (newTargetFields && newTargetFields.length > 0) {
        console.log('FieldMapping组件更新目标字段列表，字段数量:', newTargetFields.length)
        console.log('FieldMapping组件目标字段详情:', newTargetFields)
        orderedTargetFields.value = [...newTargetFields]
        console.log('FieldMapping组件更新后orderedTargetFields长度:', orderedTargetFields.value.length)
        fieldsUpdated = true
      } else {
        console.log('FieldMapping组件未收到有效的目标字段数据:', newTargetFields)
      }
      
      // 如果字段已加载且没有现有映射，尝试从store恢复或生成默认映射
      if (fieldsUpdated && orderedSourceFields.value.length > 0 && orderedTargetFields.value.length > 0 && positionMappings.value.length === 0) {
        // 首先尝试从store中恢复字段映射
        if (store.state.fieldMappings && Array.isArray(store.state.fieldMappings) && store.state.fieldMappings.length > 0) {
          console.log('FieldMapping组件从store恢复字段映射（字段变化触发）:', store.state.fieldMappings)
          positionMappings.value = store.state.fieldMappings.map(mapping => ({
            sourceIndex: mapping.sourceIndex,
            targetIndex: mapping.targetIndex
          }))
          
          // 同时恢复全局设置
          if (store.state.globalSettings) {
            console.log('FieldMapping组件从store恢复全局设置（字段变化触发）:', store.state.globalSettings)
            globalSettings.mode = store.state.globalSettings.mode || 'insert'
            globalSettings.updateConditions = store.state.globalSettings.updateConditions || []
          }
        } else {
          // 检查是否有来自模板的字段映射
          const route = getCurrentInstance()?.proxy?.$route
          const templateId = route?.query?.templateId || props.templateId || props.configId
          
          // 如果不是从模板加载的，才生成默认映射
          if (!templateId) {
            console.log('FieldMapping组件生成默认映射')
            generateDefaultMapping()
          } else {
            console.log('FieldMapping组件检测到模板ID或配置ID，跳过默认映射生成')
          }
        }
      }
      
      // 无论是否生成默认映射，都更新连接线
      if (fieldsUpdated) {
        nextTick(() => {
          console.log('FieldMapping组件更新连接线')
          updateConnections()
        })
      }
    }, { immediate: true })
    
    // 监听store中targetConfig的变化
    watch(() => store.state.targetConfig, () => {
      // 监听配置变化
    }, { deep: true, immediate: true })
    
    onMounted(async () => {
      console.log('FieldMapping组件已挂载')
      
      // 尝试从URL获取templateId
      const route = getCurrentInstance()?.proxy?.$route
      const templateId = route?.query?.templateId || props.templateId || props.configId
      
      console.log('FieldMapping组件初始化参数:', {
        'URL templateId': route?.query?.templateId,
        'props templateId': props.templateId,
        'props configId': props.configId,
        '使用的templateId': templateId,
        '源字段数量': props.sourceFields?.length || 0,
        '目标字段数量': props.targetFields?.length || 0,
        'store中的fieldMappings': store.state.fieldMappings
      })
      
      // 检查是否已经从props接收到了字段数据
      const hasSourceFields = props.sourceFields && props.sourceFields.length > 0
      const hasTargetFields = props.targetFields && props.targetFields.length > 0
      
      if (templateId) {
        // 无论是否有props字段数据，都要尝试从数据库加载字段映射配置
        console.log('FieldMapping组件从模板加载配置（包括数据库字段映射）')
        await loadTemplateConfig(templateId)
        
        // 如果props中有字段数据且模板加载后没有字段，则使用props数据作为补充
        if (hasSourceFields && hasTargetFields && orderedSourceFields.value.length === 0 && orderedTargetFields.value.length === 0) {
          console.log('FieldMapping组件使用props字段数据作为补充')
          orderedSourceFields.value = [...props.sourceFields]
          orderedTargetFields.value = [...props.targetFields]
        }
      } else {
        // 先尝试从API加载配置
        await loadConfigFromApi()
      }
      
      // 尝试从store中恢复字段映射和自定义字段
      const storeFieldMappings = store.state.fieldMappings
      if (storeFieldMappings) {
        // 恢复映射关系
        const mappings = storeFieldMappings.mappings || (Array.isArray(storeFieldMappings) ? storeFieldMappings : [])
        if (mappings.length > 0) {
          console.log('FieldMapping组件从store恢复字段映射:', mappings)
          positionMappings.value = mappings.map(mapping => ({
            sourceIndex: mapping.sourceIndex,
            targetIndex: mapping.targetIndex
          }))
        }
        
        // 恢复自定义字段
        const customFields = storeFieldMappings.customFields || []
        if (customFields.length > 0) {
          console.log('FieldMapping组件从store恢复自定义字段:', customFields)
          // 确保自定义字段有isCustom标记
          const restoredCustomFields = customFields.map(field => ({
            ...field,
            isCustom: true
          }))
          // 将自定义字段添加到源字段列表（如果不存在）
          const existingCustomFieldNames = new Set(orderedSourceFields.value.filter(f => f.isCustom).map(f => f.name))
          const newCustomFields = restoredCustomFields.filter(field => !existingCustomFieldNames.has(field.name))
          if (newCustomFields.length > 0) {
            orderedSourceFields.value = [...orderedSourceFields.value, ...newCustomFields]
          }
        }
        
        if (mappings.length > 0) {
          nextTick(() => {
            updateConnections()
          })
        }
      }
      
      if (!templateId && !props.configId && orderedSourceFields.value.length > 0 && 
          orderedTargetFields.value.length > 0 && positionMappings.value.length === 0) {
        // 如果store中没有映射且没有配置，生成默认映射
        console.log('FieldMapping组件生成默认映射（onMounted触发）')
        generateDefaultMapping()
      }
      
      // 尝试从store中恢复全局设置
      if (store.state.globalSettings) {
        console.log('FieldMapping组件从store恢复全局设置:', store.state.globalSettings)
        globalSettings.mode = store.state.globalSettings.mode || 'insert'
        globalSettings.updateConditions = store.state.globalSettings.updateConditions || []
      }
      
      nextTick(() => {
        console.log('FieldMapping组件更新连接线（onMounted触发）')
        updateConnections()
      })
    })
    
    // 添加一个方法，允许父组件直接更新字段数据
    const updateFields = (newSourceFields, newTargetFields, templateId, customFields) => {
      console.log('FieldMapping.updateFields被调用，接收到新的字段数据')
      console.log('- 源字段数量:', newSourceFields?.length || 0)
      console.log('- 目标字段数量:', newTargetFields?.length || 0)
      console.log('- 模板ID:', templateId)
      console.log('- 自定义字段数量:', customFields?.length || 0)
      console.log('- 源字段详情:', JSON.stringify(newSourceFields))
      console.log('- 目标字段详情:', JSON.stringify(newTargetFields))
      console.log('- 自定义字段详情:', JSON.stringify(customFields))
      
      if (newSourceFields && newSourceFields.length > 0) {
        console.log('FieldMapping.updateFields: 更新源字段列表')
        
        // 检查字段是否包含索引信息
        const hasSourceIndexInfo = newSourceFields.some(field => field.sourceIndex !== undefined)
        console.log('- 源字段包含索引信息:', hasSourceIndexInfo)
        
        if (hasSourceIndexInfo) {
          // 如果包含索引信息，按索引排序
          const sortedSourceFields = [...newSourceFields].sort((a, b) => {
            // 确保sourceIndex存在，如果不存在则使用默认值0
            const indexA = a.sourceIndex !== undefined ? a.sourceIndex : 0
            const indexB = b.sourceIndex !== undefined ? b.sourceIndex : 0
            return indexA - indexB
          })
          console.log('- 按索引排序后的源字段:', JSON.stringify(sortedSourceFields))
          orderedSourceFields.value = sortedSourceFields
        } else {
          // 如果不包含索引信息，直接使用原始顺序
          orderedSourceFields.value = [...newSourceFields]
        }
        
        // 添加自定义字段到源字段列表
        if (customFields && Array.isArray(customFields) && customFields.length > 0) {
          console.log('FieldMapping.updateFields: 添加自定义字段到源字段列表')
          console.log('🔥 自定义字段处理前:', JSON.stringify(customFields))
          const customFieldsWithFlag = customFields.map(field => ({
            ...field,
            isCustom: true
          }))
          console.log('🔥 自定义字段处理后:', JSON.stringify(customFieldsWithFlag))
          orderedSourceFields.value = [...orderedSourceFields.value, ...customFieldsWithFlag]
          console.log('🔥 最终源字段列表:', JSON.stringify(orderedSourceFields.value))
        }
      } else {
        console.warn('FieldMapping.updateFields: 接收到空的源字段列表')
        
        // 即使源字段为空，也要处理自定义字段
        if (customFields && Array.isArray(customFields) && customFields.length > 0) {
          console.log('FieldMapping.updateFields: 仅添加自定义字段')
          console.log('🔥 空源字段时自定义字段处理前:', JSON.stringify(customFields))
          const customFieldsWithFlag = customFields.map(field => ({
            ...field,
            isCustom: true
          }))
          console.log('🔥 空源字段时自定义字段处理后:', JSON.stringify(customFieldsWithFlag))
          orderedSourceFields.value = customFieldsWithFlag
          console.log('🔥 空源字段时最终源字段列表:', JSON.stringify(orderedSourceFields.value))
        }
      }
      
      if (newTargetFields && newTargetFields.length > 0) {
        console.log('FieldMapping.updateFields: 更新目标字段列表')
        
        // 检查字段是否包含索引信息
        const hasTargetIndexInfo = newTargetFields.some(field => field.targetIndex !== undefined)
        console.log('- 目标字段包含索引信息:', hasTargetIndexInfo)
        
        if (hasTargetIndexInfo) {
          // 如果包含索引信息，按索引排序
          const sortedTargetFields = [...newTargetFields].sort((a, b) => {
            // 确保targetIndex存在，如果不存在则使用默认值0
            const indexA = a.targetIndex !== undefined ? a.targetIndex : 0
            const indexB = b.targetIndex !== undefined ? b.targetIndex : 0
            return indexA - indexB
          })
          console.log('- 按索引排序后的目标字段:', JSON.stringify(sortedTargetFields))
          orderedTargetFields.value = sortedTargetFields
        } else {
          // 如果不包含索引信息，直接使用原始顺序
          orderedTargetFields.value = [...newTargetFields]
        }
      } else {
        console.warn('FieldMapping.updateFields: 接收到空的目标字段列表')
      }
      
      // 如果有模板ID，则尝试加载模板配置
      if (templateId) {
        // 设置props.templateId，这样watch和onMounted中可以检测到
        props.templateId = templateId
        
        // 检查是否有字段映射信息
        const hasSourceIndexInfo = newSourceFields.some(field => field.sourceIndex !== undefined)
        const hasTargetIndexInfo = newTargetFields.some(field => field.targetIndex !== undefined)
        
        // 如果已经有字段数据，则跳过模板加载，直接更新连接
        if (orderedSourceFields.value.length > 0 && orderedTargetFields.value.length > 0) {
          console.log('FieldMapping.updateFields: 已有字段数据，直接更新连接')
          
          // 如果源字段和目标字段都包含索引信息，则尝试根据索引创建映射
          if (hasSourceIndexInfo && hasTargetIndexInfo && positionMappings.value.length === 0) {
            console.log('FieldMapping.updateFields: 字段包含索引信息，尝试创建映射')
            
            // 清空现有映射
            positionMappings.value = []
            
            // 创建映射关系
            const maxMappings = Math.min(orderedSourceFields.value.length, orderedTargetFields.value.length)
            for (let i = 0; i < maxMappings; i++) {
              const sourceField = orderedSourceFields.value[i]
              const targetField = orderedTargetFields.value[i]
              
              if (sourceField && targetField) {
                console.log(`- 创建映射: 源字段=${getFieldName(sourceField)}(索引=${i}), 目标字段=${getFieldName(targetField)}(索引=${i})`)
                positionMappings.value.push({
                  sourceIndex: i,
                  targetIndex: i
                })
              }
            }
          }
          
          nextTick(() => {
            updateConnections()
          })
        }
      } else if (orderedSourceFields.value.length > 0 && orderedTargetFields.value.length > 0 && positionMappings.value.length === 0) {
        // 如果没有模板ID但有字段数据，且没有现有映射，则生成默认映射
        console.log('FieldMapping.updateFields: 生成默认映射')
        generateDefaultMapping()
      }
    }
    
    return {
      // 响应式数据
      scrollArea,
      connectionSvg,
      sourceField,
      targetField,
      orderedSourceFields,
      orderedTargetFields,
      positionMappings,
      connections,
      activeConnections,
      selectedSourceIndex,
      selectedTargetIndex,
      deletedTargetFields,
      showConfigPreview,
      configPreviewContent,
      configPreviewLoading,
      showSourceFieldDialog,
      editingSourceField,
      sourceFieldForm,
      
      // 添加updateFields方法到组件实例
      updateFields,
      
      // 计算属性
      isDevelopment,
      canProceed,
      currentConfig,
      originalSourceFields,
      availableOriginalFields,
      needsConditionValue,
      isSourceFieldFormValid,
      
      // 方法
      hasSourceMapping,
      hasTargetMapping,
      getSourceFieldByTargetIndex,
      selectSourceField,
      selectTargetField,
      createMapping,
      onSourceOrderChange,
      onTargetOrderChange,
      onTargetAdd,
      onDragEnd,
      removeMapping,
      removeMappingByIndex,
      updateConnections,
      addSourceField,
      editSourceField,
      saveSourceField,
      removeSourceField,
      removeTargetField,
      clearMappings,
      autoMapping,
      generateExpression,
      generateSampleResult,
      addCaseBranch,
      removeCaseBranch,
      generateDefaultMapping,
      loadConfigFromApi,
      saveMappings,
      saveMappingsOnly,
      nextStep,
      previewSeaTunnelConfig,
      copyConfigContent,
      downloadConfig,
      formatDate,
      getFileTypeDisplay,
      
      // 辅助函数
      getFieldName,
      getFieldType,
      
      // 全局设定
      globalSettings,
      mappedTargetFields,
      onModeChange,
      validateUpdateConditions,
      
      // Props
      fieldTypeOptions: props.fieldTypeOptions
    }
  }
}
</script>

<style scoped>
.field-mapping {
  padding: 20px;
  background: #f5f5f5;
  min-height: auto;
}

.field-mapping h2 {
  text-align: center;
  color: #303133;
  margin-bottom: 30px;
}

.config-info {
  margin-bottom: 20px;
  padding: 15px;
  background-color: #f5f7fa;
  border-radius: 4px;
  border: 1px solid #e4e7ed;
}

.config-info h3 {
  margin: 0 0 10px 0;
  color: #303133;
  font-size: 16px;
}

.config-details {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 8px;
}

.config-details p {
  margin: 0;
  font-size: 14px;
  color: #606266;
}

.global-settings {
  margin-bottom: 20px;
  padding: 15px;
  background-color: #f9f9f9;
  border-radius: 4px;
  border: 1px solid #e4e7ed;
}

.global-settings h3 {
  margin: 0 0 15px 0;
  color: #303133;
  font-size: 16px;
}

.settings-content {
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.setting-item {
  display: flex;
  align-items: flex-start;
  gap: 15px;
}

.setting-label {
  min-width: 120px;
  font-weight: 500;
  color: #303133;
  line-height: 32px;
}

.update-conditions {
  flex: 1;
}

.condition-hint {
  margin-top: 8px;
  padding: 8px;
  background-color: #f0f9ff;
  border-radius: 4px;
  border: 1px solid #b3d8ff;
}

.mapping-container {
  background: white;
  border-radius: 8px;
  padding: 20px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
}

.unified-scroll-area {
  height: 600px;
  overflow-y: auto;
  border: 1px solid #e4e7ed;
  border-radius: 4px;
}

.fields-wrapper {
  display: flex;
  min-height: 100%;
}

.source-column,
.target-column {
  flex: 1;
  padding: 15px;
  border-right: 1px solid #e4e7ed;
}

.target-column {
  border-right: none;
}

.connection-area {
  width: 100px;
  position: relative;
  background: #fafafa;
}

.connection-svg {
  width: 100%;
  height: 100%;
  position: absolute;
  top: 0;
  left: 0;
}

.delete-mapping-btn {
  transition: all 0.2s ease;
}

.delete-mapping-btn:hover {
  r: 10;
  fill: #e53e3e;
}

.delete-mapping-text {
  user-select: none;
}

.column-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 15px;
  padding-bottom: 10px;
  border-bottom: 2px solid #409eff;
}

.column-header h3 {
  margin: 0;
  color: #303133;
}

.field-list {
  min-height: 400px;
}

.field-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px;
  margin-bottom: 8px;
  background: #f8f9fa;
  border: 1px solid #e4e7ed;
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.3s;
  min-height: 80px;
  box-sizing: border-box;
}

.field-item:hover {
  background: #ecf5ff;
  border-color: #409eff;
}

.field-item.mapped {
  background: #e8f5e8;
  border-color: #67c23a;
}

.field-item.custom {
  background: #fff7e6;
  border-color: #ffd591;
}

.field-item.custom.mapped {
  background: #f6ffed;
  border-color: #b7eb8f;
}

.field-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  justify-content: center;
}

.field-info {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 4px;
}

.field-name {
  font-weight: 500;
  color: #303133;
}

.field-type {
  font-size: 12px;
  color: #909399;
  background: #f0f0f0;
  padding: 2px 6px;
  border-radius: 3px;
}

.custom-badge {
  font-size: 10px;
  color: #409eff;
  background: #ecf5ff;
  padding: 2px 4px;
  border-radius: 2px;
}

.required-badge {
  font-size: 10px;
  color: #f56c6c;
  background: #fef0f0;
  padding: 2px 4px;
  border-radius: 2px;
}

.field-sample,
.field-expression {
  font-size: 11px;
  color: #606266;
  margin-top: 1px;
  line-height: 1.2;
}

.field-actions {
  display: flex;
  gap: 4px;
  opacity: 0;
  transition: opacity 0.3s;
}

.field-item:hover .field-actions {
  opacity: 1;
}

.field-item.selected {
  border: 2px solid #409eff;
  background-color: #ecf5ff;
}

.field-mapping {
  font-size: 11px;
  color: #606266;
  margin-top: 1px;
  line-height: 1.2;
}

.case-branch {
  margin-bottom: 8px;
  padding: 8px;
  background: #f8f9fa;
  border-radius: 4px;
}

.action-buttons {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 20px;
  padding-top: 20px;
  border-top: 1px solid #e4e7ed;
}

.left-buttons,
.right-buttons {
  display: flex;
  gap: 10px;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}
</style>