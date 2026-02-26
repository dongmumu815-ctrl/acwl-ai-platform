<template>
  <div class="metadata-catalog">
    <el-card class="filter-container">
      <el-form :inline="true" :model="queryParams" class="demo-form-inline">
        <el-form-item label="数据源">
          <el-select v-model="queryParams.datasource_id" placeholder="选择数据源" clearable @change="handleSearch">
            <el-option
              v-for="item in datasourceList"
              :key="item.id"
              :label="item.name"
              :value="item.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="关键词">
          <el-input v-model="queryParams.search" placeholder="表名/Schema/描述" clearable @keyup.enter="handleSearch" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleSearch">查询</el-button>
          <el-button @click="resetQuery">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <el-card class="table-container">
      <el-table
        v-loading="loading"
        :data="tableList"
        style="width: 100%"
        border
      >
        <el-table-column prop="table_name" label="表名" min-width="180">
          <template #default="{ row }">
            <el-link type="primary" @click="handleDetail(row)">{{ row.table_name }}</el-link>
          </template>
        </el-table-column>
        <el-table-column prop="schema_name" label="Schema" width="120" />
        <el-table-column prop="description" label="描述" min-width="200" show-overflow-tooltip />
        <el-table-column prop="classification_level" label="分级分类" width="120">
          <template #default="{ row }">
            <el-tag v-if="row.classification_level">{{ row.classification_level }}</el-tag>
            <span v-else>-</span>
          </template>
        </el-table-column>
        <el-table-column prop="owner" label="负责人" width="120" />
        <el-table-column prop="updated_at" label="更新时间" width="180">
          <template #default="{ row }">
            {{ formatTime(row.updated_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="100" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" size="small" @click="handleDetail(row)">详情</el-button>
          </template>
        </el-table-column>
      </el-table>

      <div class="pagination-container">
        <el-pagination
          v-model:current-page="queryParams.page"
          v-model:page-size="queryParams.size"
          :page-sizes="[10, 20, 50, 100]"
          :total="total"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="handleSizeChange"
          @current-change="handleCurrentChange"
        />
      </div>
    </el-card>

    <!-- 详情抽屉 -->
    <TableDetailDrawer
      v-model="drawerVisible"
      :table-id="currentTableId"
      @refresh="fetchData"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { governanceApi } from '@/api/governance'
import { datasourceApi } from '@/api/datasource'
import TableDetailDrawer from './components/TableDetailDrawer.vue'
import type { GovernanceTable } from '@/types/governance'
import dayjs from 'dayjs'

const loading = ref(false)
const tableList = ref<GovernanceTable[]>([])
const total = ref(0)
const datasourceList = ref<any[]>([])

const queryParams = reactive({
  page: 1,
  size: 20,
  search: '',
  datasource_id: undefined as number | undefined
})

// 详情抽屉控制
const drawerVisible = ref(false)
const currentTableId = ref<number | undefined>(undefined)

onMounted(() => {
  fetchDatasources()
  fetchData()
})

const fetchDatasources = async () => {
  try {
    const res = await datasourceApi.getDataSourceList({ page: 1, size: 100 })
    if (res.code === 200) {
      datasourceList.value = res.data.items
    }
  } catch (error) {
    console.error(error)
  }
}

const fetchData = async () => {
  loading.value = true
  try {
    const res = await governanceApi.getTables(queryParams)
    if (res.code === 200) {
      tableList.value = res.data.items
      total.value = res.data.total
    }
  } catch (error) {
    console.error(error)
  } finally {
    loading.value = false
  }
}

const handleSearch = () => {
  queryParams.page = 1
  fetchData()
}

const resetQuery = () => {
  queryParams.search = ''
  queryParams.datasource_id = undefined
  handleSearch()
}

const handleSizeChange = (val: number) => {
  queryParams.size = val
  fetchData()
}

const handleCurrentChange = (val: number) => {
  queryParams.page = val
  fetchData()
}

const handleDetail = (row: GovernanceTable) => {
  currentTableId.value = row.id
  drawerVisible.value = true
}

const formatTime = (time: string) => {
  if (!time) return '-'
  return dayjs(time).format('YYYY-MM-DD HH:mm:ss')
}
</script>

<style scoped>
.metadata-catalog {
  padding: 20px;
}
.filter-container {
  margin-bottom: 20px;
}
.pagination-container {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
}
</style>
