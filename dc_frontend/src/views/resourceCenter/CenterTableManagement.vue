<template>
  <div class="center-table-management">
    <div class="page-header">
      <h2>中心表管理</h2>
      <p class="page-description">管理数据中心的核心表结构和配置</p>
    </div>

    <div class="content-wrapper">
      <el-card class="main-card">
        <template #header>
          <div class="card-header">
            <span>中心表列表</span>
            <div class="header-actions">
              <el-button type="primary" :icon="Plus" @click="handleCreate">
                创建中心表
              </el-button>
              <el-button :icon="Refresh" @click="handleRefresh">
                刷新
              </el-button>
            </div>
          </div>
        </template>

        <!-- 搜索和筛选区域 -->
        <div class="search-section">
          <el-form :model="searchForm" inline>
            <el-form-item label="表名称">
              <el-input
                v-model="searchForm.tableName"
                placeholder="请输入表名称"
                clearable
                style="width: 200px"
              />
            </el-form-item>
            <el-form-item label="状态">
              <el-select
                v-model="searchForm.status"
                placeholder="请选择状态"
                clearable
                style="width: 150px"
              >
                <el-option label="启用" value="active" />
                <el-option label="禁用" value="inactive" />
              </el-select>
            </el-form-item>
            <el-form-item>
              <el-button type="primary" @click="handleSearch">搜索</el-button>
              <el-button @click="handleReset">重置</el-button>
            </el-form-item>
          </el-form>
        </div>

        <!-- 表格区域 -->
        <div class="table-section">
          <el-table
            v-loading="loading"
            :data="tableData"
            stripe
            style="width: 100%"
          >
            <el-table-column prop="id" label="ID" width="80" />
            <el-table-column prop="tableName" label="表名称" min-width="150" />
            <el-table-column prop="description" label="描述" min-width="200" />
            <el-table-column prop="status" label="状态" width="100">
              <template #default="{ row }">
                <el-tag :type="row.status === 'active' ? 'success' : 'danger'">
                  {{ row.status === 'active' ? '启用' : '禁用' }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="createTime" label="创建时间" width="180" />
            <el-table-column prop="updateTime" label="更新时间" width="180" />
            <el-table-column label="操作" width="200" fixed="right">
              <template #default="{ row }">
                <el-button
                  type="primary"
                  size="small"
                  @click="handleEdit(row)"
                >
                  编辑
                </el-button>
                <el-button
                  type="info"
                  size="small"
                  @click="handleView(row)"
                >
                  查看
                </el-button>
                <el-button
                  type="danger"
                  size="small"
                  @click="handleDelete(row)"
                >
                  删除
                </el-button>
              </template>
            </el-table-column>
          </el-table>
        </div>

        <!-- 分页区域 -->
        <div class="pagination-section">
          <el-pagination
            v-model:current-page="pagination.currentPage"
            v-model:page-size="pagination.pageSize"
            :page-sizes="[10, 20, 50, 100]"
            :total="pagination.total"
            layout="total, sizes, prev, pager, next, jumper"
            @size-change="handleSizeChange"
            @current-change="handleCurrentChange"
          />
        </div>
      </el-card>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Refresh } from '@element-plus/icons-vue'

// 搜索表单
const searchForm = reactive({
  tableName: '',
  status: ''
})

// 表格数据
const tableData = ref([])
const loading = ref(false)

// 分页配置
const pagination = reactive({
  currentPage: 1,
  pageSize: 20,
  total: 0
})

// 获取表格数据
const fetchTableData = async () => {
  loading.value = true
  try {
    // TODO: 调用API获取数据
    // 模拟数据
    const mockData = [
      {
        id: 1,
        tableName: 'user_center_table',
        description: '用户中心表',
        status: 'active',
        createTime: '2024-01-15 10:30:00',
        updateTime: '2024-01-15 10:30:00'
      },
      {
        id: 2,
        tableName: 'product_center_table',
        description: '产品中心表',
        status: 'active',
        createTime: '2024-01-16 14:20:00',
        updateTime: '2024-01-16 14:20:00'
      }
    ]
    
    tableData.value = mockData
    pagination.total = mockData.length
  } catch (error) {
    ElMessage.error('获取数据失败')
  } finally {
    loading.value = false
  }
}

// 搜索
const handleSearch = () => {
  pagination.currentPage = 1
  fetchTableData()
}

// 重置
const handleReset = () => {
  Object.assign(searchForm, {
    tableName: '',
    status: ''
  })
  handleSearch()
}

// 刷新
const handleRefresh = () => {
  fetchTableData()
}

// 创建
const handleCreate = () => {
  ElMessage.info('创建功能待实现')
}

// 编辑
const handleEdit = (row: any) => {
  ElMessage.info(`编辑表: ${row.tableName}`)
}

// 查看
const handleView = (row: any) => {
  ElMessage.info(`查看表: ${row.tableName}`)
}

// 删除
const handleDelete = async (row: any) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除表 "${row.tableName}" 吗？`,
      '确认删除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    // TODO: 调用删除API
    ElMessage.success('删除成功')
    fetchTableData()
  } catch {
    // 用户取消删除
  }
}

// 分页大小改变
const handleSizeChange = (size: number) => {
  pagination.pageSize = size
  fetchTableData()
}

// 当前页改变
const handleCurrentChange = (page: number) => {
  pagination.currentPage = page
  fetchTableData()
}

onMounted(() => {
  fetchTableData()
})
</script>

<style scoped lang="scss">
.center-table-management {
  padding: 20px;

  .page-header {
    margin-bottom: 20px;

    h2 {
      margin: 0 0 8px 0;
      color: #303133;
      font-size: 24px;
      font-weight: 600;
    }

    .page-description {
      margin: 0;
      color: #606266;
      font-size: 14px;
    }
  }

  .content-wrapper {
    .main-card {
      .card-header {
        display: flex;
        justify-content: space-between;
        align-items: center;

        .header-actions {
          display: flex;
          gap: 12px;
        }
      }

      .search-section {
        margin-bottom: 20px;
        padding: 16px;
        background-color: #f8f9fa;
        border-radius: 6px;
      }

      .table-section {
        margin-bottom: 20px;
      }

      .pagination-section {
        display: flex;
        justify-content: flex-end;
      }
    }
  }
}
</style>