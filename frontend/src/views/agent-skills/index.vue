<template>
  <div class="app-container">
    <div class="filter-container">
      <el-input
        v-model="queryParams.search"
        placeholder="搜索技能名称/描述"
        style="width: 200px;"
        class="filter-item"
        @keyup.enter="handleQuery"
      />
      <el-select
        v-model="queryParams.tool_type"
        placeholder="技能类型"
        clearable
        class="filter-item"
        style="width: 130px; margin-left: 10px;"
      >
        <el-option label="内置" value="builtin" />
        <el-option label="自定义" value="custom" />
        <el-option label="API" value="api" />
      </el-select>
      <el-button
        class="filter-item"
        type="primary"
        icon="Search"
        style="margin-left: 10px;"
        @click="handleQuery"
      >
        搜索
      </el-button>
      <el-button
        class="filter-item"
        style="margin-left: 10px;"
        type="success"
        icon="VideoPlay"
        @click="handleTestRunner"
      >
        技能测试
      </el-button>
      <el-button
        class="filter-item"
        style="margin-left: 10px;"
        type="primary"
        icon="Plus"
        @click="handleCreate"
      >
        新增技能
      </el-button>
    </div>

    <el-table
      v-loading="loading"
      :data="list"
      border
      fit
      highlight-current-row
      style="width: 100%;"
    >
      <el-table-column label="ID" prop="id" align="center" width="80" />
      <el-table-column label="名称" prop="name" align="center" width="150" />
      <el-table-column label="显示名称" prop="display_name" align="center" width="150" />
      <el-table-column label="描述" prop="description" align="center" />
      <el-table-column label="类型" prop="tool_type" align="center" width="100">
        <template #default="{ row }">
          <el-tag :type="row.tool_type === 'custom' ? 'success' : 'info'">
            {{ row.tool_type }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="状态" align="center" width="100">
        <template #default="{ row }">
          <el-switch
            v-model="row.is_enabled"
            active-color="#13ce66"
            inactive-color="#ff4949"
            @change="handleStatusChange(row)"
          />
        </template>
      </el-table-column>
      <el-table-column label="创建时间" prop="created_at" align="center" width="180">
        <template #default="{ row }">
          <span>{{ formatDateTime(row.created_at) }}</span>
        </template>
      </el-table-column>
      <el-table-column label="操作" align="center" width="240" class-name="small-padding fixed-width">
        <template #default="{ row }">
          <el-button
            v-if="row.name === 'book-review'"
            type="success"
            size="small"
            :loading="startingSkill[row.name]"
            @click="handleStartSkill(row)"
          >
            启动API
          </el-button>
          <el-button type="primary" size="small" @click="handleUpdate(row)">
            编辑
          </el-button>
          <el-button
            v-if="!row.is_builtin"
            size="small"
            type="danger"
            @click="handleDelete(row)"
          >
            删除
          </el-button>
        </template>
      </el-table-column>
    </el-table>

    <pagination
      v-show="total > 0"
      :total="total"
      v-model:page="queryParams.page"
      v-model:limit="queryParams.size"
      @pagination="getList"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { getAgentTools, updateAgentTool, deleteAgentTool, executeAgentToolTask } from '@/api/agents'
import type { AgentTool } from '@/types/agent'
import { formatDateTime } from '@/utils/date'
import Pagination from '@/components/Pagination/index.vue'

const router = useRouter()
const loading = ref(false)
const list = ref<AgentTool[]>([])
const total = ref(0)
const startingSkill = reactive<Record<string, boolean>>({})

const queryParams = reactive({
  page: 1,
  size: 20,
  search: '',
  tool_type: '',
  is_enabled: undefined as boolean | undefined
})

const getList = async () => {
  loading.value = true
  try {
    const response = await getAgentTools(queryParams)
    list.value = response.items
    total.value = response.total
  } catch (error) {
    console.error(error)
  } finally {
    loading.value = false
  }
}

const handleQuery = () => {
  queryParams.page = 1
  getList()
}

const handleCreate = () => {
  router.push('/agents/skills/edit')
}

const handleTestRunner = () => {
  router.push('/agents/skills/test-runner')
}

const handleUpdate = (row: AgentTool) => {
  router.push(`/agents/skills/edit/${row.id}`)
}

const handleStatusChange = async (row: AgentTool) => {
  try {
    await updateAgentTool(row.id, { is_enabled: row.is_enabled })
    ElMessage.success('状态更新成功')
  } catch (error) {
    row.is_enabled = !row.is_enabled
    ElMessage.error('状态更新失败')
  }
}

const handleDelete = (row: AgentTool) => {
  ElMessageBox.confirm('确认删除该技能吗？', '提示', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning'
  }).then(async () => {
    try {
      await deleteAgentTool(row.id)
      ElMessage.success('删除成功')
      getList()
    } catch (error) {
      ElMessage.error('删除失败')
    }
  })
}

const handleStartSkill = async (row: AgentTool) => {
  startingSkill[row.name] = true
  try {
    const response = await executeAgentToolTask({
      prompt: 'Action: book-review\\nAction Input: {"run_script":"api.py","background":true}',
      skill_names: [row.name]
    })
    ElMessage.success(response.result || '启动指令已发送')
  } catch (error) {
    ElMessage.error('启动失败')
  } finally {
    startingSkill[row.name] = false
  }
}

onMounted(() => {
  getList()
})
</script>
