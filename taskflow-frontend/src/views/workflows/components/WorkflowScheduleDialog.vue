<template>
  <el-dialog
    :model-value="visible"
    :title="isEdit ? '编辑调度' : '创建调度'"
    width="800px"
    @update:model-value="handleUpdateVisible"
    destroy-on-close
    append-to-body
  >
    <el-form :model="form" label-width="120px" ref="formRef" :rules="rules">
      <el-form-item label="调度名称" prop="schedule_name">
        <el-input v-model="form.schedule_name" placeholder="请输入调度名称" />
      </el-form-item>

      <el-form-item label="起止时间" prop="timeRange">
        <el-date-picker
          v-model="form.timeRange"
          type="datetimerange"
          range-separator="至"
          start-placeholder="开始时间"
          end-placeholder="结束时间"
          value-format="YYYY-MM-DD HH:mm:ss"
        />
      </el-form-item>

      <el-form-item label="调度类型" prop="schedule_type">
        <el-radio-group v-model="form.schedule_type">
          <el-radio label="cron">Cron表达式</el-radio>
          <el-radio label="interval">间隔执行</el-radio>
          <el-radio label="once">仅一次</el-radio>
        </el-radio-group>
      </el-form-item>

      <el-form-item v-if="form.schedule_type === 'cron'" label="Cron表达式" prop="cron_expression">
        <div class="cron-editor">
           <el-input v-model="form.cron_expression" placeholder="* * * * *" style="margin-bottom: 10px;">
             <template #append>
                <el-button @click="showCronHelper = !showCronHelper">
                  {{ showCronHelper ? '收起生成器' : '展开生成器' }}
                </el-button>
             </template>
           </el-input>
           
           <div v-if="showCronHelper" class="cron-helper">
             <el-tabs v-model="activeCronTab" type="border-card">
               <el-tab-pane label="秒" name="second">
                 <div class="cron-tab-content">
                   <el-radio-group v-model="cronState.second.type" class="cron-radio-group">
                     <el-radio label="every">每秒</el-radio>
                     <el-radio label="range">
                       周期从 <el-input-number v-model="cronState.second.rangeStart" :min="0" :max="59" size="small" /> 
                       - <el-input-number v-model="cronState.second.rangeEnd" :min="0" :max="59" size="small" /> 秒
                     </el-radio>
                     <el-radio label="interval">
                       从 <el-input-number v-model="cronState.second.intervalStart" :min="0" :max="59" size="small" /> 秒开始，
                       每 <el-input-number v-model="cronState.second.intervalStep" :min="1" :max="59" size="small" /> 秒执行一次
                     </el-radio>
                     <el-radio label="specific">
                       指定秒数
                       <el-select v-model="cronState.second.specific" multiple collapse-tags placeholder="请选择" size="small" style="width: 200px">
                         <el-option v-for="i in 60" :key="i-1" :label="i-1" :value="i-1" />
                       </el-select>
                     </el-radio>
                   </el-radio-group>
                 </div>
               </el-tab-pane>
               <el-tab-pane label="分" name="minute">
                 <div class="cron-tab-content">
                   <el-radio-group v-model="cronState.minute.type" class="cron-radio-group">
                     <el-radio label="every">每分</el-radio>
                     <el-radio label="range">
                       周期从 <el-input-number v-model="cronState.minute.rangeStart" :min="0" :max="59" size="small" /> 
                       - <el-input-number v-model="cronState.minute.rangeEnd" :min="0" :max="59" size="small" /> 分
                     </el-radio>
                     <el-radio label="interval">
                       从 <el-input-number v-model="cronState.minute.intervalStart" :min="0" :max="59" size="small" /> 分开始，
                       每 <el-input-number v-model="cronState.minute.intervalStep" :min="1" :max="59" size="small" /> 分执行一次
                     </el-radio>
                     <el-radio label="specific">
                       指定分数
                       <el-select v-model="cronState.minute.specific" multiple collapse-tags placeholder="请选择" size="small" style="width: 200px">
                         <el-option v-for="i in 60" :key="i-1" :label="i-1" :value="i-1" />
                       </el-select>
                     </el-radio>
                   </el-radio-group>
                 </div>
               </el-tab-pane>
               <el-tab-pane label="时" name="hour">
                 <div class="cron-tab-content">
                   <el-radio-group v-model="cronState.hour.type" class="cron-radio-group">
                     <el-radio label="every">每时</el-radio>
                     <el-radio label="range">
                       周期从 <el-input-number v-model="cronState.hour.rangeStart" :min="0" :max="23" size="small" /> 
                       - <el-input-number v-model="cronState.hour.rangeEnd" :min="0" :max="23" size="small" /> 时
                     </el-radio>
                     <el-radio label="interval">
                       从 <el-input-number v-model="cronState.hour.intervalStart" :min="0" :max="23" size="small" /> 时开始，
                       每 <el-input-number v-model="cronState.hour.intervalStep" :min="1" :max="23" size="small" /> 时执行一次
                     </el-radio>
                     <el-radio label="specific">
                       指定小时
                       <el-select v-model="cronState.hour.specific" multiple collapse-tags placeholder="请选择" size="small" style="width: 200px">
                         <el-option v-for="i in 24" :key="i-1" :label="i-1" :value="i-1" />
                       </el-select>
                     </el-radio>
                   </el-radio-group>
                 </div>
               </el-tab-pane>
               <!-- Days, Months, Weeks simplified for brevity but functional -->
             </el-tabs>
             <div class="cron-preview">
               <el-button type="primary" size="small" @click="generateCron">生成表达式</el-button>
             </div>
           </div>
        </div>
      </el-form-item>

      <el-form-item v-if="form.schedule_type === 'interval'" label="间隔(秒)" prop="interval_seconds">
        <el-input-number v-model="form.interval_seconds" :min="1" />
      </el-form-item>

      <el-form-item label="失败策略" prop="misfire_policy">
        <el-radio-group v-model="form.misfire_policy">
          <el-radio label="fire_once">执行一次</el-radio>
          <el-radio label="ignore">忽略</el-radio>
        </el-radio-group>
      </el-form-item>
      
      <el-form-item label="启用状态" prop="is_enabled">
        <el-switch v-model="form.is_enabled" />
      </el-form-item>
    </el-form>
    
    <template #footer>
      <el-button @click="handleCancel">取消</el-button>
      <el-button type="primary" :loading="loading" @click="handleSubmit">确定</el-button>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref, reactive, watch, computed } from 'vue'
import { useWorkflowStore } from '@/stores'
import { ElMessage } from 'element-plus'

const props = defineProps({
  visible: {
    type: Boolean,
    default: false
  },
  workflowId: {
    type: Number,
    required: true
  },
  scheduleData: {
    type: Object,
    default: null
  }
})

const emit = defineEmits(['update:visible', 'success'])

const workflowStore = useWorkflowStore()
const formRef = ref(null)
const loading = ref(false)
const showCronHelper = ref(false)
const activeCronTab = ref('second')

const isEdit = computed(() => !!props.scheduleData)

const form = reactive({
  schedule_name: '',
  timeRange: [],
  schedule_type: 'cron',
  cron_expression: '',
  interval_seconds: 60,
  misfire_policy: 'fire_once',
  is_enabled: true
})

const rules = {
  schedule_name: [{ required: true, message: '请输入调度名称', trigger: 'blur' }],
  schedule_type: [{ required: true, message: '请选择调度类型', trigger: 'change' }],
  cron_expression: [{ 
    required: true, 
    message: '请输入Cron表达式', 
    trigger: 'blur',
    validator: (rule, value, callback) => {
      if (form.schedule_type === 'cron' && !value) {
        callback(new Error('请输入Cron表达式'))
      } else {
        callback()
      }
    }
  }],
  interval_seconds: [{ 
    required: true, 
    message: '请输入间隔秒数', 
    trigger: 'blur',
    validator: (rule, value, callback) => {
      if (form.schedule_type === 'interval' && (!value || value < 1)) {
        callback(new Error('请输入有效的间隔秒数'))
      } else {
        callback()
      }
    }
  }]
}

// Cron Helper State
const cronState = reactive({
  second: { type: 'every', rangeStart: 0, rangeEnd: 59, intervalStart: 0, intervalStep: 5, specific: [] },
  minute: { type: 'every', rangeStart: 0, rangeEnd: 59, intervalStart: 0, intervalStep: 5, specific: [] },
  hour: { type: 'every', rangeStart: 0, rangeEnd: 23, intervalStart: 0, intervalStep: 1, specific: [] },
  // ... other fields can be added
})

const generateCron = () => {
  // Simple generator for demo purposes
  const getField = (fieldState, max) => {
    switch (fieldState.type) {
      case 'every': return '*'
      case 'range': return `${fieldState.rangeStart}-${fieldState.rangeEnd}`
      case 'interval': return `${fieldState.intervalStart}/${fieldState.intervalStep}`
      case 'specific': return fieldState.specific.length > 0 ? fieldState.specific.join(',') : '*'
      default: return '*'
    }
  }
  
  const second = getField(cronState.second)
  const minute = getField(cronState.minute)
  const hour = getField(cronState.hour)
  
  form.cron_expression = `${second} ${minute} ${hour} * * ?`
  showCronHelper.value = false
}

watch(
  () => props.visible,
  (val) => {
    if (val) {
      if (props.scheduleData) {
        // Edit mode
        Object.assign(form, {
          ...props.scheduleData,
          timeRange: props.scheduleData.start_time && props.scheduleData.end_time 
            ? [props.scheduleData.start_time, props.scheduleData.end_time] 
            : []
        })
      } else {
        // Create mode
        Object.assign(form, {
          schedule_name: '',
          timeRange: [],
          schedule_type: 'cron',
          cron_expression: '',
          interval_seconds: 60,
          misfire_policy: 'fire_once',
          is_enabled: true
        })
      }
    }
  }
)

const handleUpdateVisible = (val) => {
  emit('update:visible', val)
}

const handleCancel = () => {
  emit('update:visible', false)
}

const handleSubmit = async () => {
  if (!formRef.value) return
  
  await formRef.value.validate(async (valid) => {
    if (valid) {
      loading.value = true
      try {
        const payload = {
          ...form,
          start_time: form.timeRange?.[0] || null,
          end_time: form.timeRange?.[1] || null
        }
        delete payload.timeRange
        
        if (isEdit.value) {
          await workflowStore.updateWorkflowSchedule(props.workflowId, props.scheduleData.id, payload)
          ElMessage.success('调度更新成功')
        } else {
          await workflowStore.createWorkflowSchedule(props.workflowId, payload)
          ElMessage.success('调度创建成功')
        }
        emit('success')
        emit('update:visible', false)
      } catch (error) {
        ElMessage.error(error.message || '操作失败')
      } finally {
        loading.value = false
      }
    }
  })
}
</script>

<style scoped>
.cron-editor {
  width: 100%;
}
.cron-helper {
  margin-top: 10px;
  border: 1px solid #dcdfe6;
  border-radius: 4px;
}
.cron-tab-content {
  padding: 10px;
}
.cron-radio-group {
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.cron-preview {
  padding: 10px;
  text-align: right;
  border-top: 1px solid #dcdfe6;
  background-color: #f5f7fa;
}
</style>
