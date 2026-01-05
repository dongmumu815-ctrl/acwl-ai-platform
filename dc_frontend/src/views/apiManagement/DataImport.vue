<template>
  <div class="data-import">
    <el-card class="page-header">
      <h2>数据导入配置</h2>
      <p>创建和管理数据导入配置，支持Excel和CSV文件导入到MySQL和Doris数据库</p>
    </el-card>

    <!-- 步骤导航 -->
    <el-steps :active="currentStep" align-center class="steps-container">
      <el-step title="数据源配置" description="上传文件并配置数据源"></el-step>
      <el-step title="目标配置" description="配置目标数据库和表结构"></el-step>
      <el-step title="字段映射" description="配置源字段到目标字段的映射关系"></el-step>
      <el-step title="数据质量检查" description="配置数据质量检查规则"></el-step>
      <el-step title="执行导入" description="保存配置并执行数据导入"></el-step>
    </el-steps>

    <!-- 步骤内容 -->
    <div class="step-content">
      <!-- 步骤1: 数据源配置 -->
      <div v-if="currentStep === 0" class="step-panel">
        <DataSourceConfig 
          ref="dataSourceConfig"
          @next-step="handleDataSourceNext"
          @source-config-change="handleSourceConfigChange"
        />
      </div>

      <!-- 步骤2: 目标配置 -->
      <div v-if="currentStep === 1" class="step-panel">
        <TargetConfig 
          ref="targetConfig"
          @prev-step="prevStep"
          @next-step="handleTargetNext"
          @target-config-change="handleTargetConfigChange"
        />
      </div>

      <!-- 步骤3: 字段映射 -->
      <div v-if="currentStep === 2" class="step-panel">
        <FieldMapping 
          ref="fieldMapping"
          :source-fields="sourceFields"
          :target-fields="targetFields"
          :source-config="sourceConfig"
          :target-config="targetConfig"
          :template-id="getTemplateId()"
          :config-id="getConfigId()"
          @prev-step="prevStep"
          @next-step="handleMappingNext"
        />
      </div>

      <!-- 步骤4: 数据质量检查 -->
      <div v-if="currentStep === 3" class="step-panel">
        <QualityCheck 
          ref="qualityCheck"
          :source-config="sourceConfig"
          :source-fields="sourceFields"
          :target-fields="targetFields"
          :mappings="fieldMappings"
          @prev-step="prevStep"
          @next-step="handleQualityNext"
        />
      </div>

      <!-- 步骤5: 执行导入 -->
      <div v-if="currentStep === 4" class="step-panel">
        <JobExecution 
          ref="jobExecution"
          :source-config="sourceConfig"
          :target-config="targetConfig"
          :field-mappings="fieldMappings"
          :quality-rules="qualityRules"
          @prev-step="prevStep"
          @config-saved="handleConfigSaved"
          @execution-finished="handleExecutionFinished"
        />
      </div>
    </div>
  </div>
</template>

<script>
import DataSourceConfig from '../components/DataSourceConfig.vue'
import TargetConfig from '../components/TargetConfig.vue'
import FieldMapping from '../components/FieldMapping.vue'
import QualityCheck from '../components/QualityCheck.vue'
import JobExecution from '../components/JobExecution.vue'

export default {
  name: 'DataImport',
  components: {
    DataSourceConfig,
    TargetConfig,
    FieldMapping,
    QualityCheck,
    JobExecution
  },
  data() {
    return {
      // 响应式数据
      currentStep: 0,
      
      // 配置数据
      sourceConfig: {},
      targetConfig: {},
      sourceFields: [],
      targetFields: [],
      fieldMappings: [],
      qualityRules: []
    }
  },
  // 路由进入前的导航守卫
  beforeRouteEnter(to, from, next) {
    next(vm => {
      // 只有在templateId发生变化时才清空缓存，避免用户配置丢失
      const templateId = to.query.templateId
      const currentTemplateId = vm.$store.state.sourceConfig?.id
      
      // 只有在以下情况才清空配置：
      // 1. 有新的templateId且与当前不同
      // 2. 从模板管理页面(/template-management)进入且有templateId
      if (templateId && (templateId !== currentTemplateId || from.path === '/template-management')) {
        vm.clearAllData()
      }
    })
  },
  
  async mounted() {
    // 检查URL参数中是否有templateId
    const templateId = this.$route.query.templateId
    const currentTemplateId = this.$store.state.sourceConfig?.id
    
    if (templateId && templateId !== currentTemplateId) {
      // 只有在加载不同模板时才清空缓存数据，防止不同模板间数据混淆
      this.clearAllData()
      // 加载对应的模板配置
      await this.loadTemplateConfig(templateId)
    }
    // 如果没有templateId或templateId相同，保持现有配置不变，这样用户从其他页面返回时配置不会丢失
  },
  methods: {
    
    // 清空所有缓存数据的方法
    clearAllData() {
      // 清空本地组件数据
      this.currentStep = 0
      this.sourceConfig = {}
      this.targetConfig = {}
      this.sourceFields = []
      this.targetFields = []
      this.fieldMappings = []
      this.qualityRules = []
      
      // 清空store中的缓存数据
      this.$store.dispatch('clearAllCache')
    },
    
    // 加载模板配置
    async loadTemplateConfig(templateId) {
      try {
        console.log('DataImport组件正在加载模板配置，templateId:', templateId)
        
        // 导入templateApi
        const templateApi = await import('../services/templateApi')
        
        // 获取模板详情
        const response = await templateApi.default.getTemplateDetail(templateId)
        
        if (response.success && response.data) {
          const templateData = response.data
          console.log('DataImport组件成功获取模板数据:', templateData)
          
          // 构建源配置对象
          const sourceConfig = {
            id: templateId,
            name: templateData.name || '模板配置',
            description: templateData.description || '从模板加载的配置',
            created_at: templateData.created_at || new Date().toISOString(),
            type: 'file',
            excel_filename: templateData.excel_filename || '', // 从模板获取的Excel文件名
            columns: [],
            preview: []
          }
          
          // 检查是否有config字段中的MinIO配置
          if (templateData.config && templateData.config.minioConfig) {
            // MinIO配置存在，设置为MinIO模式
            sourceConfig.type = 'minio'
            sourceConfig.minioConfig = templateData.config.minioConfig
            sourceConfig.file_type = 'minio'
          } else if (templateData.config && templateData.config.fileConfig) {
            // 文件配置存在
            sourceConfig.fileConfig = templateData.config.fileConfig
            sourceConfig.file_type = templateData.config.fileConfig.fileType || templateData.file_type
          } else {
            // 兼容旧的配置结构
            sourceConfig.fileConfig = {
              filename: templateData.excel_filename || '', // 使用模板中的Excel文件名
              fileType: templateData.file_type,
              hasHeader: templateData.has_header === 1,
              headerRow: templateData.header_row || 1,
              dataStartRow: templateData.data_start_row || 2,
              sheet: templateData.sheet_name || ''
            }
            sourceConfig.file_type = templateData.file_type
          }
          
          this.$store.commit('SET_SOURCE_CONFIG', sourceConfig)
          this.sourceConfig = sourceConfig
          
          // 处理目标配置
          if (templateData.target_database && Object.keys(templateData.target_database).length > 0) {
            const targetConfig = {
              id: templateId,
              name: templateData.name || '模板配置',
              description: templateData.description || '从模板加载的配置',
              created_at: templateData.created_at || new Date().toISOString(),
              database: templateData.target_database,
              tableName: templateData.target_table || '',
              importMode: templateData.import_mode || 'insert',
              batchSize: templateData.batch_size || 1000
            }
            console.log('DataImport设置targetConfig到store:', targetConfig)
            this.$store.commit('SET_TARGET_CONFIG', targetConfig)
            this.targetConfig = targetConfig
            console.log('DataImport设置后的store.state.targetConfig:', this.$store.state.targetConfig)
          } else {
            // 即使没有目标数据库配置，也要设置基本的配置信息
            const targetConfig = {
              id: templateId,
              name: templateData.name || '模板配置',
              description: templateData.description || '从模板加载的配置',
              created_at: templateData.created_at || new Date().toISOString()
            }
            console.log('DataImport设置基本targetConfig到store:', targetConfig)
            this.$store.commit('SET_TARGET_CONFIG', targetConfig)
            this.targetConfig = targetConfig
            console.log('DataImport设置后的store.state.targetConfig:', this.$store.state.targetConfig)
          }
          
          // 处理字段映射
          if (templateData.field_mappings && templateData.field_mappings.length > 0) {
            // 保存原始字段映射数据
            this.fieldMappings = templateData.field_mappings
            // 同时保存到store中
            this.$store.commit('SET_FIELD_MAPPINGS', templateData.field_mappings)
            console.log('DataImport从模板加载字段映射到store:', templateData.field_mappings)
            
            // 从字段映射中提取源字段和目标字段
            console.log('原始字段映射数据:', JSON.stringify(templateData.field_mappings))
            console.log('字段映射详情字段:', JSON.stringify(templateData.field_mappings_detail))
            
            // 优先使用field_mappings_detail，如果存在的话
            const mappingsToUse = templateData.field_mappings_detail && templateData.field_mappings_detail.length > 0 
              ? templateData.field_mappings_detail 
              : templateData.field_mappings
            
            console.log('使用的映射数据:', JSON.stringify(mappingsToUse))
            
            const sourceFields = mappingsToUse.map((mapping, index) => {
              // 检查所有可能的源字段名称属性
              const name = mapping.sourceName || mapping.source_field || ''
              const type = mapping.sourceType || mapping.data_type || 'VARCHAR'
              const sourceIndex = mapping.sourceIndex !== undefined ? mapping.sourceIndex : index
              
              console.log(`处理源字段[${index}]: name=${name}, type=${type}, sourceIndex=${sourceIndex}`)
              
              return {
                name,
                type,
                sourceIndex,
                description: mapping.description || ''
              }
            }).filter(field => {
              const hasName = !!field.name
              if (!hasName) {
                console.warn(`发现没有名称的源字段[${field.sourceIndex}]，已过滤`)
              }
              return hasName
            }) // 过滤掉没有名称的字段
            
            const targetFields = mappingsToUse.map((mapping, index) => {
              // 检查所有可能的目标字段名称属性
              const name = mapping.targetName || mapping.target_field || ''
              const type = mapping.targetType || mapping.data_type || 'VARCHAR'
              const targetIndex = mapping.targetIndex !== undefined ? mapping.targetIndex : index
              
              console.log(`处理目标字段[${index}]: name=${name}, type=${type}, targetIndex=${targetIndex}`)
              
              return {
                name,
                type,
                targetIndex,
                is_required: mapping.is_required || false,
                default_value: mapping.default_value || '',
                description: mapping.description || ''
              }
            }).filter(field => {
              const hasName = !!field.name
              if (!hasName) {
                console.warn(`发现没有名称的目标字段[${field.targetIndex}]，已过滤`)
              }
              return hasName
            }) // 过滤掉没有名称的字段
            
            // 确保源字段和目标字段名称唯一
            const uniqueSourceFields = Array.from(new Map(sourceFields.map(field => 
              [field.name, field])).values())
            
            const uniqueTargetFields = Array.from(new Map(targetFields.map(field => 
              [field.name, field])).values())
            
            // 更新源字段列表
            this.sourceFields = uniqueSourceFields
            
            // 将源字段添加到源配置中，以便JobExecution组件能够获取
            if (this.sourceConfig && uniqueSourceFields.length > 0) {
              this.sourceConfig.sourceFields = uniqueSourceFields.map(field => field.name)
              // 同时更新store中的源配置
              this.$store.commit('SET_SOURCE_CONFIG', this.sourceConfig)
              console.log('DataImport更新源配置中的源字段:', this.sourceConfig.sourceFields)
            }
            
            // 注意：目标字段应该始终来自目标数据库配置，而不是从模板的字段映射中提取
            // 只有当没有从TargetConfig获取到目标字段时，才从模板中提取作为备用
            if (this.targetFields.length > 0) {
              // 如果已有完整的目标字段列表（来自TargetConfig），保持不变
              console.log('DataImport组件保持从TargetConfig获取的目标字段，数量:', this.targetFields.length)
              console.log('DataImport组件目标字段来源：目标数据库配置')
            } else {
              // 如果没有现有字段，使用模板字段作为备用（但这种情况应该很少发生）
              this.targetFields = uniqueTargetFields
              console.log('DataImport组件从模板加载的目标字段数量:', this.targetFields.length)
              console.log('DataImport组件目标字段来源：模板备用数据')
            }
            
            console.log('DataImport组件从模板加载的源字段数量:', this.sourceFields.length)
            
            // 确保字段映射组件能够接收到这些字段
            console.log('准备更新FieldMapping组件，源字段:', JSON.stringify(this.sourceFields))
            console.log('准备更新FieldMapping组件，目标字段:', JSON.stringify(this.targetFields))
            
            this.$nextTick(() => {
              if (this.$refs.fieldMapping) {
                console.log('DataImport组件正在更新FieldMapping组件的字段数据')
                if (typeof this.$refs.fieldMapping.updateFields === 'function') {
                  // 提取自定义字段数据
                  const customFields = templateData.custom_fields || []
                  console.log('DataImport组件传递自定义字段:', customFields)
                  this.$refs.fieldMapping.updateFields(this.sourceFields, this.targetFields, templateId, customFields)
                  console.log('FieldMapping组件的updateFields方法调用成功')
                } else {
                  console.error('FieldMapping组件没有updateFields方法')
                  console.log('FieldMapping组件的方法:', Object.keys(this.$refs.fieldMapping))
                }
              } else {
                console.error('找不到FieldMapping组件引用')
              }
            })
          } else {
            console.warn('DataImport组件未在模板中找到字段映射数据')
          }
          
          console.log('模板配置加载成功:', templateData)
          this.$message.success('模板配置加载成功')
        } else {
          throw new Error(response.error || '获取模板详情失败')
        }
      } catch (error) {
        console.error('加载模板配置失败:', error)
        this.$message.error('加载模板配置失败: ' + (error.message || '未知错误'))
      }
    },
    
    // 步骤导航方法
    nextStep() {
      if (this.currentStep < 4) {
        this.currentStep++
      }
    },
    
    prevStep() {
      if (this.currentStep > 0) {
        this.currentStep--
      }
    },
    
    // 步骤处理方法
    handleDataSourceNext(config) {
      this.sourceConfig = config.sourceConfig
      this.sourceFields = config.sourceFields || []
      
      // 确保MinIO配置的file_type正确传递到FieldMapping组件
      if (this.sourceConfig && this.sourceConfig.minioConfig) {
        this.sourceConfig.file_type = 'minio'
      } else if (this.sourceConfig && this.sourceConfig.fileConfig) {
        this.sourceConfig.file_type = this.sourceConfig.fileConfig.fileType || 'excel'
      }
      
      console.log('DataImport handleDataSourceNext - 更新后的sourceConfig:', this.sourceConfig)
      this.nextStep()
    },
    
    handleSourceConfigChange(config) {
      this.sourceConfig = config.sourceConfig
      this.sourceFields = config.sourceFields || []
      
      // 确保MinIO配置的file_type正确传递到FieldMapping组件
      if (this.sourceConfig && this.sourceConfig.minioConfig) {
        this.sourceConfig.file_type = 'minio'
      } else if (this.sourceConfig && this.sourceConfig.fileConfig) {
        this.sourceConfig.file_type = this.sourceConfig.fileConfig.fileType || 'excel'
      }
      
      console.log('DataImport handleSourceConfigChange - 更新后的sourceConfig:', this.sourceConfig)
    },
    
    handleTargetNext(config) {
      console.log('handleTargetNext 接收到的配置:', config)
      this.targetConfig = config.targetConfig || config
      this.targetFields = config.targetFields || []
      console.log('设置 targetConfig:', this.targetConfig)
      console.log('设置 targetFields:', this.targetFields)
      this.nextStep()
    },
    
    handleTargetConfigChange(config) {
      this.targetConfig = config.targetConfig
      this.targetFields = config.targetFields || []
    },
    
    handleMappingNext(mappings) {
      this.fieldMappings = mappings
      // 同时保存到store中，确保JobExecution组件能够获取到
      this.$store.commit('SET_FIELD_MAPPINGS', mappings)
      console.log('DataImport保存字段映射到store:', mappings)
      this.nextStep()
    },
    
    handleQualityNext(config) {
      // QualityCheck组件传递的是包含rules和checkResult的config对象
      this.qualityRules = config.rules || []
      this.nextStep()
    },
    
    handleConfigSaved(savedConfig) {
      console.log('配置保存成功:', savedConfig)
      this.$message.success('配置保存成功，可以开始执行数据导入')
      // 可以在这里添加跳转到配置管理页面的逻辑
    },
    
    // 获取模板ID
    getTemplateId() {
      // 优先从URL参数获取
      const urlTemplateId = this.$route.query.templateId
      if (urlTemplateId) {
        return urlTemplateId
      }
      
      // 从源配置或目标配置中获取
      if (this.sourceConfig && this.sourceConfig.id) {
        return this.sourceConfig.id
      }
      
      if (this.targetConfig && this.targetConfig.id) {
        return this.targetConfig.id
      }
      
      return null
    },
    
    // 获取配置ID
    getConfigId() {
      // 从store中获取配置ID
      const sourceConfig = this.$store.state.sourceConfig
      if (sourceConfig && (sourceConfig.config_id || sourceConfig.id)) {
        return sourceConfig.config_id || sourceConfig.id
      }
      
      // 从组件数据中获取
      if (this.sourceConfig && (this.sourceConfig.config_id || this.sourceConfig.id)) {
        return this.sourceConfig.config_id || this.sourceConfig.id
      }
      
      return null
    },
    
    // 处理执行完成事件
    handleExecutionFinished(result) {
      console.log('执行完成:', result)
      
      if (result.success) {
        this.$message.success('数据导入执行完成')
      } else {
        // 显示详细错误信息
        if (result.error_details && Array.isArray(result.error_details) && result.error_details.length > 0) {
          // 创建详细错误信息的弹窗
          const errorMessages = result.error_details.join('\n')
          this.$alert(errorMessages, '数据导入失败 - 详细错误信息', {
            confirmButtonText: '确定',
            type: 'error',
            customClass: 'error-details-dialog'
          })
        } else {
          // 显示基本错误信息
          const errorMsg = result.error || result.message || '数据导入失败'
          this.$message.error(errorMsg)
        }
      }
    }
  }
}
</script>

<style scoped>
.data-import {
  padding: 20px;
  max-width: 1200px;
  margin: 0 auto;
}

.page-header {
  margin-bottom: 30px;
  text-align: center;
}

.page-header h2 {
  color: #303133;
  margin-bottom: 10px;
}

.page-header p {
  color: #606266;
  font-size: 14px;
}

.steps-container {
  margin: 30px 0;
}

.step-content {
  margin-top: 30px;
}

.step-panel {
  min-height: 400px;
}

.file-info {
  margin-top: 20px;
  padding: 15px;
  background-color: #f5f7fa;
  border-radius: 4px;
}

.mapping-section,
.import-section,
.progress-section {
  margin-top: 20px;
}

.mapping-actions {
  margin-top: 15px;
  text-align: center;
}

.progress-info {
  margin-top: 15px;
  text-align: center;
}

.el-upload {
  width: 100%;
}

.el-upload-dragger {
  width: 100%;
}

/* 步骤样式 */
.el-steps {
  margin: 20px 0;
}

/* 错误详情对话框样式 */
.error-details-dialog .el-message-box__message {
  white-space: pre-line;
  text-align: left;
  max-height: 300px;
  overflow-y: auto;
  font-family: 'Courier New', monospace;
  font-size: 13px;
  line-height: 1.5;
  background-color: #f5f5f5;
  padding: 10px;
  border-radius: 4px;
  border: 1px solid #dcdfe6;
}

.error-details-dialog .el-message-box {
  width: 600px;
  max-width: 90vw;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .data-import {
    padding: 10px;
  }
  
  .steps-container {
    margin: 20px 0;
  }
  
  .step-content {
    margin-top: 20px;
  }
  
  .error-details-dialog .el-message-box {
    width: 95vw;
  }
}
</style>