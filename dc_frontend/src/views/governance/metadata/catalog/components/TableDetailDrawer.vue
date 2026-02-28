<template>
  <el-drawer
    v-model="visible"
    title="表元数据详情"
    size="60%"
    :destroy-on-close="true"
    @close="handleClose"
  >
    <div v-loading="loading" class="drawer-content">
      <!-- 表基本信息 -->
      <el-descriptions title="基本信息" :column="2" border>
        <template #extra>
          <el-button type="primary" link @click="isEditingTable = !isEditingTable">
            {{ isEditingTable ? '取消编辑' : '编辑信息' }}
          </el-button>
          <el-button v-if="isEditingTable" type="primary" @click="handleSaveTable">保存</el-button>
        </template>
        <el-descriptions-item label="表名">{{ tableData?.table_name }}</el-descriptions-item>
        <el-descriptions-item label="Schema">{{ tableData?.schema_name }}</el-descriptions-item>
        <el-descriptions-item label="描述" :span="2">
          <el-input
            v-if="isEditingTable"
            v-model="tableForm.description"
            type="textarea"
            :rows="2"
          />
          <span v-else>{{ tableData?.description || '-' }}</span>
        </el-descriptions-item>
        <el-descriptions-item label="负责人">
          <el-input v-if="isEditingTable" v-model="tableForm.owner" />
          <span v-else>{{ tableData?.owner || '-' }}</span>
        </el-descriptions-item>
        <el-descriptions-item label="分级分类">
          <el-select v-if="isEditingTable" v-model="tableForm.classification_level">
            <el-option label="L1 - 公开" value="L1" />
            <el-option label="L2 - 内部" value="L2" />
            <el-option label="L3 - 敏感" value="L3" />
            <el-option label="L4 - 绝密" value="L4" />
          </el-select>
          <el-tag v-else>{{ tableData?.classification_level || '未分级' }}</el-tag>
        </el-descriptions-item>
      </el-descriptions>

      <el-divider />

      <!-- 字段列表 -->
      <div class="column-list">
        <h3>字段信息</h3>
        <el-table :data="tableData?.columns || []" stripe style="width: 100%">
          <el-table-column prop="column_name" label="字段名" width="180">
            <template #default="{ row }">
              <span>{{ row.column_name }}</span>
              <el-tag v-if="row.is_primary_key" size="small" type="warning" style="margin-left: 5px">PK</el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="data_type" label="类型" width="120" />
          <el-table-column prop="description" label="描述">
            <template #default="{ row }">
              <div v-if="editingColumnId === row.id" class="edit-cell">
                <el-input v-model="row.tempDescription" size="small" />
              </div>
              <span v-else>{{ row.description || '-' }}</span>
            </template>
          </el-table-column>
          <el-table-column prop="security_level" label="安全等级" width="120">
             <template #default="{ row }">
              <div v-if="editingColumnId === row.id" class="edit-cell">
                <el-select v-model="row.tempSecurityLevel" size="small">
                  <el-option label="公开" value="Public" />
                  <el-option label="内部" value="Internal" />
                  <el-option label="敏感" value="Sensitive" />
                </el-select>
              </div>
              <span v-else>{{ row.security_level || '-' }}</span>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="120" fixed="right">
            <template #default="{ row }">
              <div v-if="editingColumnId === row.id">
                <el-button link type="primary" size="small" @click="handleSaveColumn(row)">保存</el-button>
                <el-button link size="small" @click="cancelEditColumn(row)">取消</el-button>
              </div>
              <el-button v-else link type="primary" size="small" @click="startEditColumn(row)">编辑</el-button>
            </template>
          </el-table-column>
        </el-table>
      </div>
    </div>
  </el-drawer>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import { governanceApi } from '@/api/governance'
import type { GovernanceTable } from '@/types/governance'
import { ElMessage } from 'element-plus'

const props = defineProps<{
  modelValue: boolean
  tableId?: number
}>()

const emit = defineEmits(['update:modelValue', 'refresh'])

const visible = ref(false)
const loading = ref(false)
const tableData = ref<GovernanceTable | null>(null)

// 表单编辑状态
const isEditingTable = ref(false)
const tableForm = ref({
  description: '',
  owner: '',
  classification_level: ''
})

// 字段编辑状态
const editingColumnId = ref<number | null>(null)

watch(() => props.modelValue, (val) => {
  visible.value = val
  if (val && props.tableId) {
    fetchDetail(props.tableId)
  }
})

watch(() => visible.value, (val) => {
  emit('update:modelValue', val)
})

const fetchDetail = async (id: number) => {
  loading.value = true
  try {
    const res = await governanceApi.getTable(id)
    if (res.code === 200) {
      tableData.value = res.data
      // 初始化表单数据
      tableForm.value = {
        description: res.data.description || '',
        owner: res.data.owner || '',
        classification_level: res.data.classification_level || ''
      }
    }
  } catch (error) {
    console.error(error)
  } finally {
    loading.value = false
  }
}

const handleClose = () => {
  isEditingTable.value = false
  editingColumnId.value = null
  tableData.value = null
}

const handleSaveTable = async () => {
  if (!tableData.value) return
  
  try {
    await governanceApi.updateTable(tableData.value.id, tableForm.value)
    ElMessage.success('更新成功')
    isEditingTable.value = false
    fetchDetail(tableData.value.id) // 刷新数据
    emit('refresh')
  } catch (error) {
    console.error(error)
  }
}

const startEditColumn = (row: any) => {
  editingColumnId.value = row.id
  row.tempDescription = row.description
  row.tempSecurityLevel = row.security_level
}

const cancelEditColumn = (row: any) => {
  editingColumnId.value = null
  delete row.tempDescription
  delete row.tempSecurityLevel
}

const handleSaveColumn = async (row: any) => {
  try {
    await governanceApi.updateColumn(row.id, {
      description: row.tempDescription,
      security_level: row.tempSecurityLevel
    })
    ElMessage.success('字段更新成功')
    editingColumnId.value = null
    // 更新本地数据，避免刷新
    row.description = row.tempDescription
    row.security_level = row.tempSecurityLevel
  } catch (error) {
    console.error(error)
  }
}
</script>

<style scoped>
.drawer-content {
  padding: 0 20px;
}
.column-list {
  margin-top: 20px;
}
</style>
