<template>
  <div class="resource-list-container">
    <!-- 页面标题 -->
    <div class="page-header">
      <h1 class="page-title">
        <el-icon><FolderOpened /></el-icon>
        数据资源列表
      </h1>
      <p class="page-description">管理和浏览所有数据资源</p>
    </div>

    <!-- 筛选和操作栏 -->
    <div class="filter-bar">
      <div class="filter-left">
        <el-select v-model="filterDatasource" placeholder="数据源" style="width: 140px" clearable :loading="datasourceLoading">
          <el-option label="全部" value="" />
          <el-option 
            v-for="datasource in datasourceList" 
            :key="datasource.id" 
            :label="datasource.name" 
            :value="datasource.id.toString()" 
          />
        </el-select>
        
        <el-select v-model="filterCategory" placeholder="分类" style="width: 120px" clearable>
          <el-option label="全部" value="" />
          <el-option label="用户数据" value="用户数据" />
          <el-option label="搜索数据" value="搜索数据" />
          <el-option label="销售数据" value="销售数据" />
          <el-option label="监控数据" value="监控数据" />
          <el-option label="订单数据" value="订单数据" />
        </el-select>
        
        <el-select v-model="filterStatus" placeholder="状态" style="width: 100px" clearable>
          <el-option label="全部" value="" />
          <el-option label="正常" value="active" />
          <el-option label="维护" value="maintenance" />
          <el-option label="停用" value="inactive" />
        </el-select>
        
        <el-date-picker
          v-model="dateRange"
          type="daterange"
          range-separator="至"
          start-placeholder="开始日期"
          end-placeholder="结束日期"
          format="YYYY-MM-DD"
          value-format="YYYY-MM-DD"
          style="width: 240px"
        />
      </div>
      
      <div class="filter-right">
        <el-input
          v-model="searchKeyword"
          placeholder="搜索资源名称或描述..."
          style="width: 250px"
          clearable
        >
          <template #prefix>
            <el-icon><Search /></el-icon>
          </template>
        </el-input>
        
        <el-button type="primary" @click="addResource" :disabled="!hasCreatePermission">
          <el-icon><Plus /></el-icon>
          新增资源
        </el-button>
        
        <el-button @click="refreshResources">
          <el-icon><Refresh /></el-icon>
          刷新
        </el-button>
      </div>
    </div>

    <!-- 资源列表 -->
    <div class="resource-content">
      <el-table
        :data="filteredResources"
        v-loading="loading"
        stripe
        border
        style="width: 100%"
        @selection-change="handleSelectionChange"
      >
        <el-table-column type="selection" width="55" />
        
        <el-table-column prop="name" label="资源名称" min-width="200">
          <template #default="{ row }">
            <div class="resource-name">
              <el-icon class="resource-icon" :style="{ color: getTypeColor(row.type) }">
                <component :is="getTypeIcon(row.type)" />
              </el-icon>
              <div class="name-content">
                <div class="name-text">{{ row.name }}</div>
                <div class="name-desc">{{ row.description }}</div>
              </div>
            </div>
          </template>
        </el-table-column>
        
        <el-table-column prop="type" label="类型" width="80">
          <template #default="{ row }">
            <el-tag :type="getTypeTagType(row.type) as any">{{ getTypeLabel(row.type) }}</el-tag>
          </template>
        </el-table-column>
        
        <el-table-column prop="datasourceType" label="数据源" width="100">
          <template #default="{ row }">
            <el-tag :type="getDatasourceTagType(row.datasourceType)" size="small">
              {{ getDatasourceLabel(row.datasourceType) }}
            </el-tag>
          </template>
        </el-table-column>
        
        <el-table-column prop="category" label="分类" width="100">
          <template #default="{ row }">
            <el-tag type="info" size="small">{{ row.category }}</el-tag>
          </template>
        </el-table-column>
        
        <el-table-column prop="tags" label="标签" width="200">
          <template #default="{ row }">
            <div class="tags-container">
              <el-tag
                v-for="tag in row.tags.slice(0, 2)"
                :key="tag"
                size="small"
                class="tag-item"
              >
                {{ tag }}
              </el-tag>
              <el-tooltip v-if="row.tags.length > 2" :content="row.tags.slice(2).join(', ')">
                <el-tag size="small" type="info">+{{ row.tags.length - 2 }}</el-tag>
              </el-tooltip>
            </div>
          </template>
        </el-table-column>
<!--         
        <el-table-column prop="size" label="大小" width="100">
          <template #default="{ row }">
            {{ formatSize(row.size) }}
          </template>
        </el-table-column>
        
        <el-table-column prop="records" label="记录数" width="100">
          <template #default="{ row }">
            <span v-if="row.records !== null">{{ formatNumber(row.records) }}</span>
            <span v-else class="text-placeholder">-</span>
          </template>
        </el-table-column> -->
        
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="getStatusTagType(row.status) as any">{{ getStatusLabel(row.status) }}</el-tag>
          </template>
        </el-table-column>
        
        <el-table-column  label="最后更新时间" width="180" >
            <template #default="{ row }">
              {{ row.updatedAt || '-' }}
            </template>
          </el-table-column>
        
        <el-table-column prop="owner" label="所有者" width="120" />
        
        <el-table-column label="操作" width="280" fixed="right">
          <template #default="{ row }">
            <el-button
              type="primary"
              size="small"
              @click="viewResource(row)"
              :disabled="!hasViewPermission"
            >
              查看
            </el-button>
            <el-button
              v-if="row.previewAvailable"
              type="info"
              size="small"
              @click="previewData(row)"
              :disabled="!hasViewPermission"
            >
              预览
            </el-button>
            <el-button
              type="success"
              size="small"
              @click="queryData(row)"
              :disabled="!hasViewPermission"
            >
              查询设定
            </el-button>
            <!-- <el-button
              type="warning"
              size="small"
              @click="showApiInfo(row)"
              :disabled="!hasViewPermission"
            >
              API
            </el-button> -->
            <el-dropdown trigger="click">
              <el-button size="small">
                更多<el-icon class="el-icon--right"><ArrowDown /></el-icon>
              </el-button>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item @click="editResource(row)" :disabled="!hasEditPermission">
                    <el-icon><Edit /></el-icon>编辑
                  </el-dropdown-item>
                  <el-dropdown-item @click="downloadResource(row)" :disabled="!hasDownloadPermission">
                    <el-icon><Download /></el-icon>导出
                  </el-dropdown-item>
                  <el-dropdown-item @click="shareResource(row)" :disabled="!hasSharePermission">
                    <el-icon><Share /></el-icon>分享
                  </el-dropdown-item>
                  <el-dropdown-item @click="copyResource(row)">
                    <el-icon><CopyDocument /></el-icon>复制链接
                  </el-dropdown-item>
                  <el-dropdown-item divided @click="deleteResource(row)" :disabled="!hasDeletePermission">
                    <el-icon><Delete /></el-icon>删除
                  </el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <!-- 批量操作栏 -->
    <div class="batch-actions" v-show="selectedResources.length > 0">
      <div class="batch-info">
        已选择 {{ selectedResources.length }} 个资源
      </div>
      <div class="batch-buttons">
        <el-button size="small" @click="batchDownload" :disabled="!hasDownloadPermission">
          <el-icon><Download /></el-icon>
          批量下载
        </el-button>
        <el-button size="small" @click="batchShare" :disabled="!hasSharePermission">
          <el-icon><Share /></el-icon>
          批量分享
        </el-button>
        <el-button type="danger" size="small" @click="batchDelete" :disabled="!hasDeletePermission">
          <el-icon><Delete /></el-icon>
          批量删除
        </el-button>
      </div>
    </div>

    <!-- 分页 -->
    <div class="pagination-container">
      <el-pagination
        v-model:current-page="currentPage"
        v-model:page-size="pageSize"
        :page-sizes="[10, 20, 50, 100]"
        :total="totalResources"
        layout="total, sizes, prev, pager, next, jumper"
        @size-change="handleSizeChange"
        @current-change="handleCurrentChange"
      />
    </div>

    <!-- 新增资源模态窗口 -->
    <el-dialog
      v-model="showAddResourceDialog"
      title="新增数据资源"
      width="600px"
      :before-close="cancelAddResource"
    >
      <el-form
        :model="newResourceForm"
        label-width="100px"
        label-position="left"
      >
        <el-form-item label="资源名称" required>
          <el-input
            v-model="newResourceForm.name"
            placeholder="请输入资源名称"
            clearable
          />
        </el-form-item>
        
        <el-form-item label="资源描述" required>
          <el-input
            v-model="newResourceForm.description"
            type="textarea"
            :rows="3"
            placeholder="请输入资源描述"
          />
        </el-form-item>
        
        <el-form-item label="资源类型">
          <el-select v-model="newResourceForm.type" style="width: 100%">
            <el-option label="数据表" value="table" />
            <el-option label="索引" value="index" />
            <el-option label="视图" value="view" />
          </el-select>
        </el-form-item>
        
        <el-form-item label="数据源">
          <el-select v-model="newResourceForm.datasourceId" style="width: 100%" :loading="datasourceLoading" placeholder="请选择数据源">
            <el-option 
              v-for="datasource in datasourceList" 
              :key="datasource.id" 
              :label="`${datasource.name} (${datasource.datasource_type})`" 
              :value="datasource.id" 
            />
          </el-select>
        </el-form-item>
        
        <!-- Schema选择 - 仅对关系型数据库显示 -->
        <el-form-item 
          v-if="selectedDatasourceType && ['mysql', 'postgresql', 'doris', 'clickhouse'].includes(selectedDatasourceType.toLowerCase())"
          label="Schema/数据库"
        >
          <el-select 
            v-model="newResourceForm.schema" 
            placeholder="请选择Schema/数据库" 
            style="width: 100%"
            :disabled="!newResourceForm.datasourceId"
            :loading="schemaLoading"
            clearable
          >
            <el-option 
              v-for="schema in availableSchemas" 
              :key="schema.name" 
              :label="schema.name" 
              :value="schema.name" 
            />
          </el-select>
        </el-form-item>
        
        <!-- 表/视图/索引选择 -->
        <el-form-item :label="getTableLabel()">
          <el-select 
            v-model="newResourceForm.tableName" 
            :placeholder="getTablePlaceholder()" 
            style="width: 100%"
            :disabled="!canSelectTable()"
            :loading="tableLoading"
            clearable
          >
            <el-option 
              v-for="table in availableTables" 
              :key="table.name" 
              :label="`${table.name} (${table.type})`" 
              :value="table.name" 
            />
          </el-select>
        </el-form-item>
        
        <el-form-item label="分类">
          <el-select v-model="newResourceForm.category" style="width: 100%">
            <el-option label="ODS层" :value="1" />
            <el-option label="DWD层" :value="2" />
            <el-option label="DWS层" :value="3" />
            <el-option label="ADS层" :value="4" />
            <el-option label="维度表" :value="5" />
            <el-option label="事实表" :value="6" />
            <el-option label="报表数据" :value="7" />
            <el-option label="实时数据" :value="8" />
            <el-option label="外部数据" :value="9" />
            <el-option label="临时数据" :value="10" />
          </el-select>
        </el-form-item>
        
        <el-form-item label="标签">
          <el-input
            v-model="newResourceForm.tagsInput"
            placeholder="请输入标签，多个标签用逗号分隔"
            clearable
          />
        </el-form-item>
        
        <el-form-item label="API端点">
          <el-input
            v-model="newResourceForm.apiEndpoint"
            placeholder="请输入API端点"
            clearable
          />
        </el-form-item>
        
        <el-form-item label="文件大小">
          <el-input
            v-model.number="newResourceForm.size"
            placeholder="文件大小（字节）"
            type="number"
            clearable
          >
            <template #append>字节</template>
          </el-input>
        </el-form-item>
        
        <el-form-item label="记录数量">
          <el-input
            v-model.number="newResourceForm.records"
            placeholder="记录数量"
            type="number"
            clearable
          >
            <template #append>条</template>
          </el-input>
        </el-form-item>
        
        <el-form-item label="状态">
          <el-select v-model="newResourceForm.status" style="width: 100%">
            <el-option label="正常" value="active" />
            <el-option label="维护" value="maintenance" />
            <el-option label="停用" value="inactive" />
          </el-select>
        </el-form-item>
        
        <el-form-item label="支持预览">
          <el-switch v-model="newResourceForm.previewAvailable" />
        </el-form-item>
        
        <el-form-item label="所有者">
          <el-input
            v-model="newResourceForm.owner"
            placeholder="资源所有者"
            clearable
          />
        </el-form-item>
      </el-form>
      
      <template #footer>
        <div class="dialog-footer">
          <el-button @click="cancelAddResource">取消</el-button>
          <el-button type="primary" @click="confirmAddResource">
            确认创建
          </el-button>
        </div>
      </template>
    </el-dialog>

    <!-- 编辑资源模态窗口 -->
    <el-dialog
      v-model="showEditResourceDialog"
      title="编辑数据资源"
      width="600px"
      :before-close="cancelEditResource"
    >
      <el-form
        :model="editResourceForm"
        label-width="100px"
        label-position="left"
      >
        <el-form-item label="资源名称" required>
          <el-input
            v-model="editResourceForm.name"
            placeholder="请输入资源名称"
            clearable
          />
        </el-form-item>
        
        <el-form-item label="资源描述" required>
          <el-input
            v-model="editResourceForm.description"
            type="textarea"
            :rows="3"
            placeholder="请输入资源描述"
          />
        </el-form-item>
        
        <el-form-item label="资源类型">
          <el-select v-model="editResourceForm.type" style="width: 100%" disabled>
            <el-option label="数据表" value="table" />
            <el-option label="索引" value="index" />
            <el-option label="视图" value="view" />
          </el-select>
        </el-form-item>
        
        <el-form-item label="数据源">
          <el-select v-model="editResourceForm.datasourceId" style="width: 100%" :loading="datasourceLoading" placeholder="请选择数据源" disabled>
            <el-option 
              v-for="datasource in datasourceList" 
              :key="datasource.id" 
              :label="`${datasource.name} (${datasource.datasource_type})`" 
              :value="datasource.id" 
            />
          </el-select>
        </el-form-item>
        
        <!-- Schema选择 - 仅对关系型数据库显示 -->
        <el-form-item 
          v-if="editingResource && editingResource.datasourceType && ['mysql', 'postgresql', 'doris', 'clickhouse'].includes(editingResource.datasourceType.toLowerCase())"
          label="Schema/数据库"
        >
          <el-select 
            v-model="editResourceForm.schema" 
            placeholder="请选择Schema/数据库" 
            style="width: 100%"
            :loading="schemaLoading"
            clearable
          >
            <el-option 
              v-for="schema in availableSchemas" 
              :key="schema.name" 
              :label="schema.name" 
              :value="schema.name" 
            />
          </el-select>
        </el-form-item>
        
        <!-- 表/视图/索引选择 -->
        <el-form-item :label="editingResource && editingResource.datasourceType === 'elasticsearch' ? '索引' : '表/视图'">
          <el-select 
            v-model="editResourceForm.tableName" 
            :placeholder="editingResource && editingResource.datasourceType === 'elasticsearch' ? '请选择索引' : '请选择表或视图'" 
            style="width: 100%"
            :loading="tableLoading"
            clearable
          >
            <el-option 
              v-for="table in availableTables" 
              :key="table.name" 
              :label="`${table.name} (${table.type})`" 
              :value="table.name" 
            />
          </el-select>
        </el-form-item>
        
        <el-form-item label="分类">
          <el-select v-model="editResourceForm.category" style="width: 100%">
            <el-option label="ODS层" :value="1" />
            <el-option label="DWD层" :value="2" />
            <el-option label="DWS层" :value="3" />
            <el-option label="ADS层" :value="4" />
            <el-option label="维度表" :value="5" />
            <el-option label="事实表" :value="6" />
            <el-option label="报表数据" :value="7" />
            <el-option label="实时数据" :value="8" />
            <el-option label="外部数据" :value="9" />
            <el-option label="临时数据" :value="10" />
          </el-select>
        </el-form-item>
        
        <el-form-item label="标签">
          <el-input
            v-model="editResourceForm.tagsInput"
            placeholder="请输入标签，多个标签用逗号分隔"
            clearable
          />
        </el-form-item>
        
        <el-form-item label="API端点">
          <el-input
            v-model="editResourceForm.apiEndpoint"
            placeholder="请输入API端点"
            clearable
          />
        </el-form-item>
        
        <el-form-item label="文件大小">
          <el-input
            v-model.number="editResourceForm.size"
            placeholder="文件大小（字节）"
            type="number"
            clearable
          >
            <template #append>字节</template>
          </el-input>
        </el-form-item>
        
        <el-form-item label="记录数量">
          <el-input
            v-model.number="editResourceForm.records"
            placeholder="记录数量"
            type="number"
            clearable
          >
            <template #append>条</template>
          </el-input>
        </el-form-item>
        
        <el-form-item label="状态">
          <el-select v-model="editResourceForm.status" style="width: 100%">
            <el-option label="正常" value="active" />
            <el-option label="维护" value="maintenance" />
            <el-option label="停用" value="inactive" />
          </el-select>
        </el-form-item>
        
        <el-form-item label="支持预览">
          <el-switch v-model="editResourceForm.previewAvailable" />
        </el-form-item>
        
        <el-form-item label="所有者">
          <el-input
            v-model="editResourceForm.owner"
            placeholder="资源所有者"
            clearable
          />
        </el-form-item>
      </el-form>
      
      <template #footer>
        <div class="dialog-footer">
          <el-button @click="cancelEditResource">取消</el-button>
          <el-button type="primary" @click="confirmEditResource">
            确认更新
          </el-button>
        </div>
      </template>
    </el-dialog>

    <!-- 数据预览模态窗口 -->
    <el-dialog
      v-model="showPreviewDialog"
      title="数据预览"
      width="80%"
      :before-close="() => { showPreviewDialog = false }"
    >
      <div v-if="currentPreviewData">
        <div class="preview-header">
          <h4>{{ currentPreviewData.resource.name }}</h4>
          <p>{{ currentPreviewData.resource.description }}</p>
          <div class="preview-info">
            <el-tag :type="getDatasourceTagType(currentPreviewData.resource.datasourceType)">
              {{ getDatasourceLabel(currentPreviewData.resource.datasourceType) }}
            </el-tag>
            <span class="info-item">数据库: {{ currentPreviewData.resource.database }}</span>
            <span class="info-item">表名: {{ currentPreviewData.resource.tableName }}</span>
          </div>
        </div>
        
        <el-table :data="currentPreviewData.data" border style="width: 100%">
          <el-table-column
            v-for="column in currentPreviewData.columns"
            :key="column"
            :prop="column"
            :label="column"
            show-overflow-tooltip
          />
        </el-table>
      </div>
      
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="showPreviewDialog = false">关闭</el-button>
        </span>
      </template>
    </el-dialog>

    <!-- API信息模态窗口 -->
    <el-dialog
      v-model="showApiDialog"
      title="API信息"
      width="70%"
      :before-close="() => { showApiDialog = false }"
    >
      <div v-if="currentApiInfo">
        <div class="api-header">
          <h4>{{ currentApiInfo.resource.name }}</h4>
          <p>{{ currentApiInfo.resource.description }}</p>
        </div>
        
        <el-tabs>
          <el-tab-pane label="基本信息" name="basic">
            <div class="api-basic-info">
              <div class="info-row">
                <label>API端点:</label>
                <el-input v-model="currentApiInfo.endpoint" readonly>
                  <template #append>
                    <el-button @click="copyToClipboard(currentApiInfo.endpoint)">复制</el-button>
                  </template>
                </el-input>
              </div>
              <div class="info-row">
                <label>支持方法:</label>
                <div>
                  <el-tag v-for="method in currentApiInfo.methods" :key="method" style="margin-right: 8px;">
                    {{ method }}
                  </el-tag>
                </div>
              </div>
            </div>
          </el-tab-pane>
          
          <el-tab-pane label="参数说明" name="params">
            <el-table :data="currentApiInfo.parameters" border>
              <el-table-column prop="name" label="参数名" width="120" />
              <el-table-column prop="type" label="类型" width="100" />
              <el-table-column prop="description" label="说明" />
              <el-table-column prop="default" label="默认值" width="100" />
            </el-table>
          </el-tab-pane>
          
          <el-tab-pane label="调用示例" name="examples">
            <div class="api-examples">
              <h5>cURL 示例:</h5>
              <el-input
                v-model="currentApiInfo.examples.curl"
                type="textarea"
                :rows="3"
                readonly
              >
                <template #append>
                  <el-button @click="copyToClipboard(currentApiInfo.examples.curl)">复制</el-button>
                </template>
              </el-input>
              
              <h5 style="margin-top: 20px;">JavaScript 示例:</h5>
              <el-input
                v-model="currentApiInfo.examples.javascript"
                type="textarea"
                :rows="6"
                readonly
              >
                <template #append>
                  <el-button @click="copyToClipboard(currentApiInfo.examples.javascript)">复制</el-button>
                </template>
              </el-input>
            </div>
          </el-tab-pane>
        </el-tabs>
      </div>
      
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="showApiDialog = false">关闭</el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useRoute, useRouter } from 'vue-router'
import { useUserStore } from '@/stores/user'
import { dataResourceApi } from '@/api/dataResource'
import { datasourceApi } from '@/api/datasource'

// 路由和状态管理
const route = useRoute();
const router = useRouter();
const userStore = useUserStore();

// 响应式数据
const loading = ref(false);
const searchKeyword = ref('');
const filterStatus = ref('');
const filterDatasource = ref('');
const filterCategory = ref('');
const dateRange = ref<[string, string] | null>(null);

// 权限控制
const hasCreatePermission = computed(() => {
  return userStore.hasPermission('data:resource:create') || userStore.hasRole('admin');
});

const hasEditPermission = computed(() => {
  return userStore.hasPermission('data:resource:edit') || userStore.hasRole('admin');
});

const hasDeletePermission = computed(() => {
  return userStore.hasPermission('data:resource:delete') || userStore.hasRole('admin');
});

const hasViewPermission = computed(() => {
  return userStore.hasPermission('data:resource:view') || userStore.hasRole('admin');
});

const hasDownloadPermission = computed(() => {
  return userStore.hasPermission('data:resource:download') || userStore.hasRole('admin');
});

const hasSharePermission = computed(() => {
  return userStore.hasPermission('data:resource:share') || userStore.hasRole('admin');
});

// 数据安全配置
const securityConfig = reactive({
  enableDataMasking: true, // 启用数据脱敏
  sensitiveFields: ['password', 'phone', 'email', 'id_card'], // 敏感字段
  auditLog: true // 启用审计日志
});

/**
 * 记录资源活动日志
 * @param action 活动类型
 * @param details 活动详情
 */
const logResourceActivity = (action: string, details: any) => {
  console.log('记录审计日志:', action, details);
  
  // 调用API记录审计日志
  try {
    // 这里可以调用后端API记录审计日志
    // 例如：recordResourceAccess(resource.id, { operation: action, details })
    // 目前仅打印日志，后续可以集成实际的API调用
  } catch (error) {
    console.error('记录审计日志失败:', error);
  }
};

// 数据源列表
const datasourceList = ref<any[]>([]);
const datasourceLoading = ref(false);

// Schema列表
const availableSchemas = ref<any[]>([]);
const schemaLoading = ref(false);

// 表/视图/索引列表
const availableTables = ref<any[]>([]);
const tableLoading = ref(false);

// 分页数据
const currentPage = ref(1);
const pageSize = ref(20);
const totalResources = ref(0);
const selectedResources = ref<any[]>([]);

// 新增资源模态窗口
const showAddResourceDialog = ref(false);
const newResourceForm = ref({
  name: '',
  description: '',
  type: 'table',
  datasourceId: null as number | null,
  schema: '',
  tableName: '',
  size: null,
  records: null,
  status: 'active',
  owner: '',
  tags: [] as string[],
  tagsInput: '',
  category: '',
  apiEndpoint: '',
  previewAvailable: true
});

// 编辑资源模态窗口
const showEditResourceDialog = ref(false);
const editResourceForm = ref({
  id: null as number | null,
  name: '',
  description: '',
  type: 'table',
  datasourceId: null as number | null,
  schema: '',
  tableName: '',
  size: null,
  records: null,
  status: 'active',
  owner: '',
  tags: [] as string[],
  tagsInput: '',
  category: '',
  apiEndpoint: '',
  previewAvailable: true
});
const editingResource = ref<any>(null);

// 数据预览和API信息模态窗口
const showPreviewDialog = ref(false);
const showApiDialog = ref(false);
const currentPreviewData = ref<any>(null);
const currentApiInfo = ref<any>(null);

// 资源数据
const resources = ref([
  {
    id: 1,
    name: '用户行为分析表',
    description: 'Doris数据库中的用户行为分析数据表',
    type: 'table',
    datasourceType: 'doris',
    datasourceName: 'Doris生产环境',
    database: 'analytics_db',
    tableName: 'user_behavior',
    size: 2147483648, // 2GB
    records: 1250000,
    status: 'active',
    lastAccessed: '2024-01-15 14:30:00',
    owner: '张三',
    createdAt: '2024-01-10 09:00:00',
    tags: ['用户分析', '实时数据', '核心业务'],
    category: '用户数据',
    apiEndpoint: '/api/v1/data/user-behavior',
    previewAvailable: true
  },
  {
    id: 2,
    name: '商品搜索日志',
    description: 'Elasticsearch中的商品搜索行为日志',
    type: 'index',
    datasourceType: 'elasticsearch',
    datasourceName: 'ES集群',
    database: 'search_logs',
    tableName: 'product_search_2024',
    size: 52428800, // 50MB
    records: 850000,
    status: 'active',
    lastAccessed: '2024-01-14 16:45:00',
    owner: '李四',
    createdAt: '2024-01-12 11:20:00',
    tags: ['搜索分析', '商品推荐', '用户行为'],
    category: '搜索数据',
    apiEndpoint: '/api/v1/data/search-logs',
    previewAvailable: true
  },
  {
    id: 3,
    name: '销售数据汇总',
    description: 'Doris中的销售数据汇总表，包含多个源表聚合',
    type: 'view',
    datasourceType: 'doris',
    datasourceName: 'Doris生产环境',
    database: 'sales_db',
    tableName: 'sales_summary_view',
    size: 1073741824, // 1GB
    records: 500000,
    status: 'active',
    lastAccessed: '2024-01-13 10:15:00',
    owner: '王五',
    createdAt: '2024-01-08 15:30:00',
    tags: ['销售分析', '业务报表', '汇总数据'],
    category: '销售数据',
    apiEndpoint: '/api/v1/data/sales-summary',
    previewAvailable: true
  },
  {
    id: 4,
    name: '实时监控指标',
    description: 'ES中的系统监控指标数据',
    type: 'index',
    datasourceType: 'elasticsearch',
    datasourceName: 'ES集群',
    database: 'monitoring',
    tableName: 'system_metrics',
    size: 10485760, // 10MB
    records: 2000000,
    status: 'maintenance',
    lastAccessed: '2024-01-15 09:20:00',
    owner: '赵六',
    createdAt: '2024-01-01 08:00:00',
    tags: ['系统监控', '实时指标', '运维数据'],
    category: '监控数据',
    apiEndpoint: '/api/v1/data/system-metrics',
    previewAvailable: false
  },
  {
    id: 5,
    name: '历史订单数据',
    description: 'Doris中的历史订单归档数据',
    type: 'table',
    datasourceType: 'doris',
    datasourceName: 'Doris生产环境',
    database: 'archive_db',
    tableName: 'orders_history',
    size: 5368709120, // 5GB
    records: 5000000,
    status: 'active',
    lastAccessed: '2024-01-05 12:00:00',
    owner: '孙七',
    createdAt: '2023-12-31 23:59:59',
    tags: ['历史数据', '订单分析', '归档数据'],
    category: '订单数据',
    apiEndpoint: '/api/v1/data/orders-history',
    previewAvailable: true
  }
])

/**
 * 过滤后的资源列表
 */
const filteredResources = computed(() => {
  let filtered = resources.value
  
  // 按数据源筛选
  if (filterDatasource.value) {
    filtered = filtered.filter(resource => resource.datasourceType === filterDatasource.value)
  }
  
  // 按分类筛选
  if (filterCategory.value) {
    filtered = filtered.filter(resource => resource.category === filterCategory.value)
  }
  
  // 按状态筛选
  if (filterStatus.value) {
    filtered = filtered.filter(resource => resource.status === filterStatus.value)
  }
  
  // 按关键词搜索
  if (searchKeyword.value) {
    const keyword = searchKeyword.value.toLowerCase()
    filtered = filtered.filter(resource => 
      resource.name.toLowerCase().includes(keyword) ||
      resource.description.toLowerCase().includes(keyword) ||
      resource.tags.some(tag => tag.toLowerCase().includes(keyword))
    )
  }
  
  // 按日期范围筛选
  if (dateRange.value && dateRange.value.length === 2) {
    const [startDate, endDate] = dateRange.value
    filtered = filtered.filter(resource => {
      const accessDate = resource.lastAccessed.split(' ')[0]
      return accessDate >= startDate && accessDate <= endDate
    })
  }
  
  return filtered;
});

/**
 * 选中数据源的类型
 */
const selectedDatasourceType = computed(() => {
  if (!newResourceForm.value.datasourceId) return null
  const datasource = datasourceList.value.find(ds => ds.id === newResourceForm.value.datasourceId)
  return datasource?.datasource_type || null;
});

/**
 * 获取表标签文本
 */
const getTableLabel = () => {
  const dsType = selectedDatasourceType.value;
  if (!dsType) return '表/视图/索引';
  
  switch (dsType.toLowerCase()) {
    case 'elasticsearch':
      return '索引';
    case 'mysql':
    case 'postgresql':
    case 'doris':
    case 'clickhouse':
      return '表/视图';
    default:
      return '表/视图/索引';
  }
};

/**
 * 获取表选择占位符文本
 */
const getTablePlaceholder = () => {
  const dsType = selectedDatasourceType.value;
  if (!dsType) return '请先选择数据源';
  
  switch (dsType.toLowerCase()) {
    case 'elasticsearch':
      return '请选择索引';
    case 'mysql':
    case 'postgresql':
    case 'doris':
    case 'clickhouse':
      return newResourceForm.value.schema ? '请选择表或视图' : '请先选择Schema/数据库';
    default:
      return '请选择表/视图/索引';
  }
};

/**
 * 判断是否可以选择表
 */
const canSelectTable = () => {
  if (!newResourceForm.value.datasourceId) return false;
  
  const dsType = selectedDatasourceType.value;
  if (!dsType) return false;
  
  // ES类型只需要选择数据源即可
  if (dsType.toLowerCase() === 'elasticsearch') {
    return true;
  }
  
  // 关系型数据库需要先选择Schema
  if (['mysql', 'postgresql', 'doris', 'clickhouse'].includes(dsType.toLowerCase())) {
    return !!newResourceForm.value.schema;
  }
  
  return true;
};

/**
 * 获取类型图标
 */
const getTypeIcon = (type: string) => {
  const iconMap: Record<string, string> = {
    database: 'Coin',
    file: 'Document',
    api: 'Connection',
    report: 'DataAnalysis'
  };
  return iconMap[type] || 'Document';
};

/**
 * 获取类型颜色
 */
const getTypeColor = (type: string) => {
  const colorMap: Record<string, string> = {
    database: '#409EFF',
    file: '#67C23A',
    api: '#E6A23C',
    report: '#F56C6C'
  };
  return colorMap[type] || '#909399';
};

/**
 * 获取类型标签类型
 */
const getTypeTagType = (type: string) => {
  const tagMap: Record<string, string> = {
    table: 'primary',
    index: 'success',
    view: 'warning'
  };
  return tagMap[type] || 'info';
};

/**
 * 获取类型标签文本
 */
const getTypeLabel = (type: string) => {
  const labelMap: Record<string, string> = {
    table: '数据表',
    index: '索引',
    view: '视图'
  };
  return labelMap[type] || type;
};

/**
 * 获取数据源标签类型
 */
const getDatasourceTagType = (datasourceType: string) => {
  const tagMap: Record<string, string> = {
    doris: 'primary',
    elasticsearch: 'success'
  };
  return tagMap[datasourceType] || 'info';
};

/**
 * 获取数据源标签文本
 */
const getDatasourceLabel = (datasourceType: string) => {
  const labelMap: Record<string, string> = {
    doris: 'Doris',
    elasticsearch: 'ES'
  };
  return labelMap[datasourceType] || datasourceType;
};

/**
 * 获取状态标签类型
 */
const getStatusTagType = (status: string) => {
  const tagMap: Record<string, string> = {
    active: 'success',
    maintenance: 'warning',
    inactive: 'info'
  };
  return tagMap[status] || 'info';
};

/**
 * 获取状态标签文本
 */
const getStatusLabel = (status: string) => {
  const labelMap: Record<string, string> = {
    active: '正常',
    maintenance: '维护',
    inactive: '停用'
  };
  return labelMap[status] || status;
};

/**
 * 格式化文件大小
 */
const formatSize = (bytes: number | null) => {
  if (bytes === null) return '-';
  if (bytes === 0) return '0 B';
  
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
};

/**
 * 格式化数字
 */
const formatNumber = (num: number) => {
  return num.toLocaleString();
};

/**
 * 格式化日期
 */
const formatDate = (dateStr: string | null | undefined) => {
  if (!dateStr) return '-';
  
  try {
    const date = new Date(dateStr);
    if (isNaN(date.getTime())) {
      return '-';
    }
    return date.toLocaleString('zh-CN');
  } catch (error) {
    console.error('日期格式化错误:', error, '原始值:', dateStr);
    return '-';
  }
};

/**
 * 处理选择变化
 */
const handleSelectionChange = (selection: any[]) => {
  selectedResources.value = selection;
};

/**
 * 数据预览
 */
const previewData = (resource: any) => {
  // 权限检查
  if (!hasViewPermission.value) {
    ElMessage.error('您没有查看资源的权限');
    return;
  }
  
  console.log('=== 数据预览调试信息 ===');
  console.log('预览资源:', resource);
  console.log('数据源类型:', resource.datasourceType);
  console.log('表名:', resource.tableName);
  console.log('========================');
  
  // 模拟数据预览
  currentPreviewData.value = {
    resource: resource,
    columns: ['id', 'name', 'created_at', 'updated_at'],
    data: [
      { id: 1, name: '示例数据1', created_at: '2024-01-15 10:00:00', updated_at: '2024-01-15 10:00:00' },
      { id: 2, name: '示例数据2', created_at: '2024-01-15 11:00:00', updated_at: '2024-01-15 11:00:00' },
      { id: 3, name: '示例数据3', created_at: '2024-01-15 12:00:00', updated_at: '2024-01-15 12:00:00' }
    ]
  }
  
  // 记录审计日志
  if (securityConfig.auditLog) {
    logResourceActivity('PREVIEW_RESOURCE', {
      resourceId: resource.id,
      resourceName: resource.name
    });
  }
  
  showPreviewDialog.value = true;
  ElMessage.success(`正在预览: ${resource.name}`);
};

/**
 * 显示API信息
 */
const showApiInfo = (resource: any) => {
  // 权限检查
  if (!hasViewPermission.value) {
    ElMessage.error('您没有查看资源的权限');
    return;
  }
  
  console.log('=== API信息调试信息 ===');
  console.log('API资源:', resource);
  console.log('API端点:', resource.apiEndpoint);
  console.log('========================');
  
  // 记录审计日志
  if (securityConfig.auditLog) {
    logResourceActivity('VIEW_API_INFO', {
      resourceId: resource.id,
      resourceName: resource.name
    });
  }
  
  currentApiInfo.value = {
    resource: resource,
    endpoint: resource.apiEndpoint,
    methods: ['GET', 'POST'],
    parameters: [
      { name: 'limit', type: 'integer', description: '返回记录数限制', default: '100' },
      { name: 'offset', type: 'integer', description: '偏移量', default: '0' },
      { name: 'filter', type: 'string', description: '过滤条件', default: '' }
    ],
    examples: {
      curl: `curl -X GET "${resource.apiEndpoint}?limit=10&offset=0" -H "Authorization: Bearer YOUR_TOKEN"`,
      javascript: `fetch('${resource.apiEndpoint}?limit=10&offset=0', {
  headers: {
    'Authorization': 'Bearer YOUR_TOKEN'
  }
}).then(response => response.json())`
    }
  }
  
  showApiDialog.value = true;
  ElMessage.info(`查看API信息: ${resource.name}`);
};

/**
 * 新增资源
 */
const addResource = () => {
  console.log('=== 新增资源调试信息 ===');
  console.log('当前路由:', route.path);
  console.log('用户权限:', userStore.userPermissions);
  console.log('打开新增资源模态窗口');
  console.log('========================');
  
  // 权限检查
  if (!hasCreatePermission.value) {
    ElMessage.error('您没有创建资源的权限');
    return;
  }
  
  // 记录审计日志
  if (securityConfig.auditLog) {
    logResourceActivity('OPEN_CREATE_FORM', {});
  }
  
  // 重置表单
  newResourceForm.value = {
    name: '',
    description: '',
    type: 'table',
    datasourceId: null,
    schema: '',
    tableName: '',
    size: null,
    records: null,
    status: 'active',
    owner: userStore.userInfo?.username || '',
    tags: [],
    tagsInput: '',
    category: '',
    apiEndpoint: '',
    previewAvailable: true
  }
  
  showAddResourceDialog.value = true;
};

/**
 * 确认新增资源
 */
const confirmAddResource = async () => {
  if (!newResourceForm.value.name.trim()) {
    ElMessage.warning('请输入资源名称')
    return
  }
  
  if (!newResourceForm.value.description.trim()) {
    ElMessage.warning('请输入资源描述')
    return
  }
  
  if (!newResourceForm.value.datasourceId) {
    ElMessage.warning('请选择数据源')
    return
  }
  
  if (!newResourceForm.value.tableName.trim()) {
    ElMessage.warning('请选择数据库表/视图/索引')
    return
  }
  
  // 获取选中的数据源信息
  const selectedDatasource = datasourceList.value.find(ds => ds.id === newResourceForm.value.datasourceId)
  if (!selectedDatasource) {
    ElMessage.error('选择的数据源不存在')
    return
  }
  
  // 获取选中的表信息
  const selectedTable = availableTables.value.find(table => table.name === newResourceForm.value.tableName)
  if (!selectedTable) {
    ElMessage.error('选择的表/视图/索引不存在')
    return
  }
  
  // 处理标签输入
  const tags = newResourceForm.value.tagsInput
    ? newResourceForm.value.tagsInput.split(',').map(tag => tag.trim()).filter(tag => tag)
    : []
  
  try {
    // 根据数据源类型确定资源类型
    let resourceType = 'doris_table' // 默认为Doris表
    if (selectedDatasource.datasource_type === 'elasticsearch') {
      resourceType = 'elasticsearch_index'
    }
    
    // 构建创建数据资源的请求数据
    const createData = {
      name: newResourceForm.value.name,
      display_name: newResourceForm.value.name, // 显示名称与名称相同
      description: newResourceForm.value.description,
      resource_type: resourceType,
      datasource_id: newResourceForm.value.datasourceId,
      database_name: resourceType === 'doris_table' ? newResourceForm.value.schema : null,
      table_name: resourceType === 'doris_table' ? newResourceForm.value.tableName : null,
      index_name: resourceType === 'elasticsearch_index' ? newResourceForm.value.tableName : null,
      tags: tags.length > 0 ? { tags: tags } : null, // 标签格式调整
      category_id: newResourceForm.value.category || null,
      is_public: true,
      status: 'active' // 设置状态为活跃，使用小写
    }
    
    console.log('=== 创建数据资源请求 ===');
    console.log('请求数据:', createData);
    console.log('========================');
    
    // 调用API创建数据资源
    const response = await dataResourceApi.createResource(createData)
    
    if (response.success) {
      ElMessage.success('资源创建成功')
      
      // 关闭模态窗口
      showAddResourceDialog.value = false
      
      // 重新加载资源列表
      await loadResources()
      
      console.log('=== 新增资源成功 ===');
      console.log('新资源:', response.data);
      console.log('=====================');
    } else {
      ElMessage.error(response.message || '创建资源失败')
    }
  } catch (error) {
    console.error('创建资源失败:', error)
    ElMessage.error('创建资源失败，请稍后重试')
  }
};

/**
 * 取消新增资源
 */
const cancelAddResource = () => {
  showAddResourceDialog.value = false;
};

/**
 * 确认编辑资源
 */
const confirmEditResource = async () => {
  if (!editResourceForm.value.name.trim()) {
    ElMessage.warning('请输入资源名称');
    return;
  }
  
  if (!editResourceForm.value.description.trim()) {
    ElMessage.warning('请输入资源描述');
    return;
  }
  
  if (!editResourceForm.value.datasourceId) {
    ElMessage.warning('请选择数据源');
    return;
  }
  
  if (!editResourceForm.value.tableName.trim()) {
    ElMessage.warning('请选择数据库表/视图/索引');
    return;
  }
  
  // 获取选中的数据源信息
  const selectedDatasource = datasourceList.value.find(ds => ds.id === editResourceForm.value.datasourceId);
  if (!selectedDatasource) {
    ElMessage.error('选择的数据源不存在');
    return;
  }
  
  // 处理标签输入
  const tags = editResourceForm.value.tagsInput
    ? editResourceForm.value.tagsInput.split(',').map(tag => tag.trim()).filter(tag => tag)
    : [];
  
  try {
    // 根据数据源类型确定资源类型
    let resourceType = 'doris_table'; // 默认为Doris表
    if (selectedDatasource.datasource_type === 'elasticsearch') {
      resourceType = 'elasticsearch_index';
    }
    
    // 构建更新数据资源的请求数据
    const updateData = {
      name: editResourceForm.value.name,
      display_name: editResourceForm.value.name, // 显示名称与名称相同
      description: editResourceForm.value.description,
      resource_type: resourceType,
      datasource_id: editResourceForm.value.datasourceId,
      database_name: resourceType === 'doris_table' ? editResourceForm.value.schema : null,
      table_name: resourceType === 'doris_table' ? editResourceForm.value.tableName : null,
      index_name: resourceType === 'elasticsearch_index' ? editResourceForm.value.tableName : null,
      tags: tags.length > 0 ? { tags: tags } : null, // 标签格式调整
      category_id: editResourceForm.value.category || null,
      is_public: true,
      status: editResourceForm.value.status
    };
    
    console.log('=== 更新数据资源请求 ===');
    console.log('资源ID:', editResourceForm.value.id);
    console.log('请求数据:', updateData);
    console.log('========================');
    
    // 调用API更新数据资源
    const response = await dataResourceApi.updateResource(editResourceForm.value.id!, updateData);
    
    if (response.success) {
      ElMessage.success('资源更新成功');
      
      // 关闭模态窗口
      showEditResourceDialog.value = false;
      
      // 重新加载资源列表
      await loadResources();
      
      // 记录审计日志
      if (securityConfig.auditLog) {
        logResourceActivity('UPDATE_RESOURCE', {
          resourceId: editResourceForm.value.id,
          resourceName: editResourceForm.value.name,
          changes: updateData
        });
      }
      
      console.log('=== 编辑资源成功 ===');
      console.log('更新后的资源:', response.data);
      console.log('=====================');
    } else {
      ElMessage.error(response.message || '更新资源失败');
    }
  } catch (error) {
    console.error('更新资源失败:', error);
    ElMessage.error('更新资源失败，请稍后重试');
  }
};

/**
 * 取消编辑资源
 */
const cancelEditResource = () => {
  showEditResourceDialog.value = false;
  editingResource.value = null;
};

/**
 * 复制到剪贴板
 */
const copyToClipboard = async (text: string) => {
  try {
    await navigator.clipboard.writeText(text);
    ElMessage.success('已复制到剪贴板');
  } catch (err) {
    console.error('复制失败:', err);
    ElMessage.error('复制失败');
  }
};

/**
 * 查看资源
 */
const viewResource = (resource: any) => {
  // 权限检查
  if (!hasViewPermission.value) {
    ElMessage.error('您没有查看资源的权限');
    return;
  }
  
  console.log('=== 查看资源调试信息 ===');
  console.log('点击的资源:', resource);
  console.log('资源ID:', resource.id);
  console.log('资源名称:', resource.name);
  console.log('资源类型:', resource.type);
  console.log('当前路由:', route.path);
  console.log('准备跳转到资源详情页面');
  console.log('========================');
  
  // 记录审计日志
  if (securityConfig.auditLog) {
    logResourceActivity('VIEW_RESOURCE', {
      resourceId: resource.id,
      resourceName: resource.name
    });
  }
  
  // 跳转到资源详情页面
  router.push(`/data-resources/detail/${resource.id}`);
  
  ElMessage.info(`查看资源: ${resource.name}`);
};

/**
 * 查询数据
 */
const queryData = (resource: any) => {
  // 权限检查
  if (!hasViewPermission.value) {
    ElMessage.error('您没有查询资源的权限');
    return;
  }
  
  console.log('=== 查询数据调试信息 ===');
  console.log('点击的资源:', resource);
  console.log('资源ID:', resource.id);
  console.log('资源名称:', resource.name);
  console.log('当前路由:', route.path);
  console.log('准备跳转到数据查询页面');
  console.log('========================');
  
  // 记录审计日志
  if (securityConfig.auditLog) {
    logResourceActivity('QUERY_RESOURCE', {
      resourceId: resource.id,
      resourceName: resource.name
    });
  }
  
  // 跳转到数据查询页面，传递完整的数据源信息
  const queryParams: any = {
    datasourceType: resource.datasourceType
  };
  
  // 根据数据源类型传递不同的参数
  if (resource.datasourceType === 'elasticsearch') {
    // ES数据源传递索引信息
    if (resource.tableName) {
      queryParams.indices = resource.tableName;
    }
  } else {
    // SQL数据源传递schema和表名信息
    if (resource.database) {
      queryParams.schema = resource.database;
    }
    if (resource.tableName) {
      queryParams.tableName = resource.tableName;
    }
  }
  
  router.push({
    path: `/data-resources/query/${resource.datasourceId}`,
    query: queryParams
  });
  
  ElMessage.info(`查询数据: ${resource.name}`);
};

/**
 * 编辑资源
 */
const editResource = (resource: any) => {
  // 权限检查
  if (!hasEditPermission.value) {
    ElMessage.error('您没有编辑资源的权限');
    return;
  }
  
  console.log('=== 编辑资源调试信息 ===');
  console.log('点击编辑的资源:', resource);
  console.log('资源ID:', resource.id);
  console.log('资源名称:', resource.name);
  console.log('当前用户权限:', userStore.userPermissions);
  console.log('准备打开编辑对话框');
  console.log('========================');
  
  // 记录审计日志
  if (securityConfig.auditLog) {
    logResourceActivity('EDIT_RESOURCE', {
      resourceId: resource.id,
      resourceName: resource.name
    });
  }
  
  // 保存当前编辑的资源
  editingResource.value = resource;
  
  // 填充编辑表单
  editResourceForm.value = {
    id: resource.id,
    name: resource.name,
    description: resource.description,
    type: resource.type,
    datasourceId: resource.datasourceId,
    schema: resource.database || '',
    tableName: resource.tableName,
    size: resource.size,
    records: resource.records,
    status: resource.status,
    owner: resource.owner,
    tags: [...resource.tags],
    tagsInput: resource.tags.join(', '),
    category: resource.category,
    apiEndpoint: resource.apiEndpoint,
    previewAvailable: resource.previewAvailable
  };
  
  // 如果有数据源ID，加载相关的Schema和表信息
  if (resource.datasourceId) {
    const dsType = resource.datasourceType;
    if (dsType && ['mysql', 'postgresql', 'doris', 'clickhouse'].includes(dsType.toLowerCase())) {
      // 关系型数据库：先获取Schema列表
      loadDataSourceSchemas(resource.datasourceId);
      if (resource.database) {
        // 如果有Schema，获取表列表
        loadDataSourceTablesWithSchema(resource.datasourceId, resource.database);
      }
    } else {
      // ES等：直接获取索引列表
      loadDataSourceTables(resource.datasourceId);
    }
  }
  
  // 打开编辑对话框
  showEditResourceDialog.value = true;
  
  ElMessage.info(`编辑资源: ${resource.name}`);
};

/**
 * 下载资源
 */
const downloadResource = (resource: any) => {
  // 权限检查
  if (!hasDownloadPermission.value) {
    ElMessage.error('您没有下载资源的权限');
    return;
  }
  
  // 记录审计日志
  if (securityConfig.auditLog) {
    logResourceActivity('DOWNLOAD_RESOURCE', {
      resourceId: resource.id,
      resourceName: resource.name
    });
  }
  
  ElMessage.success(`开始下载: ${resource.name}`);
};

/**
 * 分享资源
 */
const shareResource = (resource: any) => {
  // 权限检查
  if (!hasSharePermission.value) {
    ElMessage.error('您没有分享资源的权限');
    return;
  }
  
  // 记录审计日志
  if (securityConfig.auditLog) {
    logResourceActivity('SHARE_RESOURCE', {
      resourceId: resource.id,
      resourceName: resource.name
    });
  }
  
  ElMessage.info(`分享资源: ${resource.name}`);
};

/**
 * 复制资源
 */
const copyResource = (resource: any) => {
  // 记录审计日志
  if (securityConfig.auditLog) {
    logResourceActivity('COPY_RESOURCE_LINK', {
      resourceId: resource.id,
      resourceName: resource.name
    });
  }
  
  ElMessage.success(`已复制资源链接: ${resource.name}`);
};

/**
 * 删除资源
 */
const deleteResource = async (resource: any) => {
  // 权限检查
  if (!hasDeletePermission.value) {
    ElMessage.error('您没有删除资源的权限');
    return;
  }
  
  try {
    await ElMessageBox.confirm(
      `确定要删除资源 "${resource.name}" 吗？此操作不可撤销！`,
      '确认删除',
      {
        confirmButtonText: '确定删除',
        cancelButtonText: '取消',
        type: 'warning',
        dangerouslyUseHTMLString: false
      }
    );
    
    // 显示删除中的加载状态
    const loadingMessage = ElMessage({
      message: '正在删除资源...',
      type: 'info',
      duration: 0,
      showClose: false
    });
    
    try {
      // 调用API删除资源
      await dataResourceApi.deleteResource(resource.id);
      
      // 从本地列表中移除
      const index = resources.value.findIndex(r => r.id === resource.id);
      if (index > -1) {
        resources.value.splice(index, 1);
      }
      
      // 更新总数
      if (totalResources.value > 0) {
        totalResources.value--;
      }
      
      // 关闭加载消息
      loadingMessage.close();
      
      ElMessage.success('资源删除成功');
      
      // 记录审计日志
      if (securityConfig.auditLog) {
        logResourceActivity('DELETE_RESOURCE', {
          resourceId: resource.id,
          resourceName: resource.name
        });
      }
      
      // 如果当前页没有数据了，且不是第一页，则跳转到上一页
      if (resources.value.length === 0 && currentPage.value > 1) {
        currentPage.value--;
        await loadResources();
      }
      
    } catch (error: any) {
      // 关闭加载消息
      loadingMessage.close();
      
      console.error('删除资源失败:', error);
      
      // 根据错误类型显示不同的错误信息
      if (error.response?.status === 403) {
        ElMessage.error('权限不足，无法删除该资源');
      } else if (error.response?.status === 404) {
        ElMessage.error('资源不存在或已被删除');
        // 刷新列表以同步状态
        await loadResources();
      } else if (error.response?.status === 409) {
        ElMessage.error('资源正在使用中，无法删除');
      } else {
        const errorMessage = error.response?.data?.message || error.message || '删除资源失败';
        ElMessage.error(`删除失败: ${errorMessage}`);
      }
    }
    
  } catch {
    // 用户取消删除，不需要处理
  }
};

/**
 * 批量下载
 */
const batchDownload = () => {
  // 权限检查
  if (!hasDownloadPermission.value) {
    ElMessage.error('您没有下载资源的权限');
    return;
  }
  
  // 记录审计日志
  if (securityConfig.auditLog) {
    logResourceActivity('BATCH_DOWNLOAD_RESOURCES', {
      resourceIds: selectedResources.value.map(r => r.id),
      count: selectedResources.value.length
    });
  }
  
  ElMessage.success(`开始批量下载 ${selectedResources.value.length} 个资源`);
};

/**
 * 批量分享
 */
const batchShare = () => {
  // 权限检查
  if (!hasSharePermission.value) {
    ElMessage.error('您没有分享资源的权限');
    return;
  }
  
  // 记录审计日志
  if (securityConfig.auditLog) {
    logResourceActivity('BATCH_SHARE_RESOURCES', {
      resourceIds: selectedResources.value.map(r => r.id),
      count: selectedResources.value.length
    });
  }
  
  ElMessage.info(`批量分享 ${selectedResources.value.length} 个资源`);
};

/**
 * 批量删除
 */
const batchDelete = async () => {
  // 权限检查
  if (!hasDeletePermission.value) {
    ElMessage.error('您没有删除资源的权限');
    return;
  }
  
  if (selectedResources.value.length === 0) {
    ElMessage.warning('请先选择要删除的资源');
    return;
  }
  
  try {
    await ElMessageBox.confirm(
      `确定要删除选中的 ${selectedResources.value.length} 个资源吗？此操作不可撤销！`,
      '确认批量删除',
      {
        confirmButtonText: '确定删除',
        cancelButtonText: '取消',
        type: 'warning',
        dangerouslyUseHTMLString: false
      }
    );
    
    // 显示批量删除中的加载状态
    const loadingMessage = ElMessage({
      message: `正在删除 ${selectedResources.value.length} 个资源...`,
      type: 'info',
      duration: 0,
      showClose: false
    });
    
    try {
      const selectedIds = selectedResources.value.map(r => r.id);
      const selectedNames = selectedResources.value.map(r => r.name);
      
      // 使用批量操作API
      const response = await dataResourceApi.batchOperation({
        operation: 'delete',
        resource_ids: selectedIds
      });
      
      // 关闭加载消息
      loadingMessage.close();
      
      // 处理批量操作结果
      if (response.data) {
        const { success_count, failed_count, errors } = response.data;
        
        if (success_count > 0) {
          // 从本地列表中移除成功删除的资源
          resources.value = resources.value.filter(r => !selectedIds.includes(r.id));
          
          // 更新总数
          totalResources.value = Math.max(0, totalResources.value - success_count);
          
          // 清空选择
          selectedResources.value = [];
          
          // 记录审计日志
          if (securityConfig.auditLog) {
            logResourceActivity('BATCH_DELETE_RESOURCES', {
              resourceIds: selectedIds,
              count: success_count,
              failedCount: failed_count
            });
          }
        }
        
        // 显示结果消息
        if (failed_count === 0) {
          ElMessage.success(`成功删除 ${success_count} 个资源`);
        } else if (success_count === 0) {
          ElMessage.error(`删除失败，所有 ${failed_count} 个资源都无法删除`);
          if (errors && errors.length > 0) {
            console.error('批量删除错误:', errors);
          }
        } else {
          ElMessage.warning(`部分删除成功：成功 ${success_count} 个，失败 ${failed_count} 个`);
          if (errors && errors.length > 0) {
            console.error('批量删除错误:', errors);
          }
        }
        
        // 如果当前页没有数据了，且不是第一页，则跳转到上一页
        if (resources.value.length === 0 && currentPage.value > 1) {
          currentPage.value--;
          await loadResources();
        }
      }
      
    } catch (error: any) {
      // 关闭加载消息
      loadingMessage.close();
      
      console.error('批量删除资源失败:', error);
      
      // 根据错误类型显示不同的错误信息
      if (error.response?.status === 403) {
        ElMessage.error('权限不足，无法删除选中的资源');
      } else if (error.response?.status === 404) {
        ElMessage.error('部分资源不存在或已被删除');
        // 刷新列表以同步状态
        await loadResources();
        selectedResources.value = [];
      } else {
        const errorMessage = error.response?.data?.message || error.message || '批量删除失败';
        ElMessage.error(`批量删除失败: ${errorMessage}`);
      }
    }
    
  } catch {
    // 用户取消删除，不需要处理
  }
};

/**
 * 刷新资源列表
 */
const refreshResources = () => {
  loadResources();
  ElMessage.success('资源列表已刷新');
};

/**
 * 处理页面大小变化
 */
const handleSizeChange = (size: number) => {
  pageSize.value = size;
  currentPage.value = 1;
  loadResources();
};

/**
 * 处理当前页变化
 */
const handleCurrentChange = (page: number) => {
  currentPage.value = page;
  loadResources();
};

/**
 * 加载数据源列表
 */
const loadDatasources = async () => {
  try {
    datasourceLoading.value = true;
    const response = await datasourceApi.getDataSourceList({
      page: 1,
      size: 100 // 获取所有数据源用于选择
    });
    
    if (response.data && response.data.items) {
      datasourceList.value = response.data.items;
    }
  } catch (error) {
    console.error('加载数据源列表失败:', error);
    ElMessage.error('加载数据源列表失败');
  } finally {
    datasourceLoading.value = false;
  }
};

/**
 * 获取数据源的表/视图/索引列表
 * @param datasourceId 数据源ID
 */
const loadDataSourceTables = async (datasourceId: number) => {
  if (!datasourceId) {
    availableTables.value = [];
    return;
  }
  
  try {
    tableLoading.value = true;
    const response = await datasourceApi.getDataSourceTables(datasourceId);
    
    if (response.data) {
      availableTables.value = response.data;
    }
  } catch (error) {
    console.error('获取数据源表列表失败:', error);
    ElMessage.error('获取数据源表列表失败');
    availableTables.value = [];
  } finally {
    tableLoading.value = false;
  }
};

/**
 * 获取指定Schema下的表/视图列表
 * @param datasourceId 数据源ID
 * @param schema Schema名称
 */
const loadDataSourceTablesWithSchema = async (datasourceId: number, schema: string) => {
  if (!datasourceId || !schema) {
    availableTables.value = [];
    return;
  }
  
  try {
    tableLoading.value = true;
    const response = await datasourceApi.getDataSourceTablesWithSchema(datasourceId, schema);
    
    if (response.data) {
      availableTables.value = response.data;
    }
  } catch (error) {
    console.error('获取Schema下表列表失败:', error);
    ElMessage.error('获取Schema下表列表失败');
    availableTables.value = [];
  } finally {
    tableLoading.value = false;
  }
};

/**
 * 获取数据源的Schema列表
 * @param datasourceId 数据源ID
 */
const loadDataSourceSchemas = async (datasourceId: number) => {
  if (!datasourceId) {
    availableSchemas.value = [];
    return;
  }
  
  try {
    schemaLoading.value = true;
    const response = await datasourceApi.getDataSourceSchemas(datasourceId);
    
    if (response.data) {
      availableSchemas.value = response.data;
    }
  } catch (error) {
    console.error('获取数据源Schema列表失败:', error);
    ElMessage.error('获取数据源Schema列表失败');
    availableSchemas.value = [];
  } finally {
    schemaLoading.value = false;
  }
};

/**
 * 将API返回的数据转换为前端表格所需的格式
 */
const transformApiDataToTableFormat = (apiData: any) => {
  return {
    id: apiData.id,
    name: apiData.name || apiData.display_name,
    description: apiData.description,
    type: getResourceTypeFromApiType(apiData.resource_type),
    datasourceType: apiData.datasource?.datasource_type || 'unknown',
    datasourceName: apiData.datasource?.name || '未知数据源',
    datasourceId: apiData.datasource_id, // 保留数据源ID
    database: apiData.database_name,
    tableName: apiData.table_name || apiData.index_name,
    size: null, // API暂未返回大小信息
    records: null, // API暂未返回记录数信息
    updatedAt: apiData.updated_at,
    status: apiData.status,
    lastAccessed: apiData.last_accessed_at,
    owner: 'admin', // API暂未返回所有者信息
    createdAt: apiData.created_at,
    tags: apiData.tag_list || [],
    category: apiData.category?.name || '未分类',
    apiEndpoint: `/api/v1/data-resources/${apiData.id}`,
    previewAvailable: true
  };
};

/**
 * 将API资源类型转换为前端显示类型
 */
const getResourceTypeFromApiType = (apiType: string) => {
  const typeMap: Record<string, string> = {
    'elasticsearch_index': 'index',
    'doris_table': 'table',
    'mysql_table': 'table',
    'postgresql_table': 'table'
  };
  return typeMap[apiType] || 'table';
};

/**
 * 加载资源列表
 */
const loadResources = async () => {
  try {
    loading.value = true;
    const response = await dataResourceApi.getResourceList({
      page: currentPage.value,
      pageSize: pageSize.value,
      datasource: filterDatasource.value,
      category: filterCategory.value,
      status: filterStatus.value,
      keyword: searchKeyword.value,
      dateRange: dateRange.value
    });
    
    console.log('API返回的原始数据:', response.data);
    
    // 转换API数据格式
    if (response.data && response.data.items) {
      resources.value = response.data.items.map(transformApiDataToTableFormat);
      totalResources.value = response.data.total;
    } else {
      resources.value = [];
      totalResources.value = 0;
    }
    
    console.log('转换后的表格数据:', resources.value);
  } catch (error) {
    console.error('加载资源列表失败:', error);
    ElMessage.error('加载资源列表失败');
  } finally {
    loading.value = false;
  }
};

/**
 * 监听数据源选择变化
 */
watch(
  () => newResourceForm.value.datasourceId,
  (newDatasourceId) => {
    if (newDatasourceId) {
      // 清空之前的选择
      newResourceForm.value.schema = '';
      newResourceForm.value.tableName = '';
      availableTables.value = [];
      
      const dsType = selectedDatasourceType.value;
      if (dsType && ['mysql', 'postgresql', 'doris', 'clickhouse'].includes(dsType.toLowerCase())) {
        // 关系型数据库：先获取Schema列表
        loadDataSourceSchemas(newDatasourceId);
      } else {
        // ES等：直接获取索引列表
        loadDataSourceTables(newDatasourceId);
      }
    } else {
      availableSchemas.value = [];
      availableTables.value = [];
      newResourceForm.value.schema = '';
      newResourceForm.value.tableName = '';
    }
  }
);

/**
 * 监听Schema选择变化，自动获取表列表
 */
watch(
  () => newResourceForm.value.schema,
  (newSchema) => {
    if (newSchema && newResourceForm.value.datasourceId) {
      // 清空之前选择的表名
      newResourceForm.value.tableName = '';
      // 获取指定Schema下的表列表
      loadDataSourceTablesWithSchema(newResourceForm.value.datasourceId, newSchema);
    } else {
      availableTables.value = [];
      newResourceForm.value.tableName = '';
    }
  }
);

/**
 * 组件挂载时加载数据
 */
onMounted(() => {
  loadResources();
  loadDatasources();
});
</script>

<style lang="scss" scoped>
.resource-list-container {
  padding: 20px;
  background: var(--el-bg-color-page);
  min-height: 100vh;
}

.page-header {
  margin-bottom: 24px;
  
  .page-title {
    display: flex;
    align-items: center;
    font-size: 24px;
    font-weight: 600;
    color: var(--el-text-color-primary);
    margin: 0 0 8px 0;
    
    .el-icon {
      margin-right: 8px;
      color: var(--el-color-primary);
    }
  }
  
  .page-description {
    color: var(--el-text-color-secondary);
    margin: 0;
  }
}

.filter-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  padding: 16px;
  background: var(--el-bg-color);
  border-radius: 8px;
  border: 1px solid var(--el-border-color-light);
  
  .filter-left {
    display: flex;
    gap: 12px;
    align-items: center;
  }
  
  .filter-right {
    display: flex;
    gap: 12px;
    align-items: center;
  }
}

.resource-content {
  background: var(--el-bg-color);
  border-radius: 8px;
  border: 1px solid var(--el-border-color-light);
  overflow: hidden;
  
  .resource-name {
    display: flex;
    align-items: center;
    
    .resource-icon {
      margin-right: 12px;
      font-size: 18px;
    }
    
    .name-content {
      .name-text {
        font-weight: 500;
        color: var(--el-text-color-primary);
        margin-bottom: 2px;
      }
      
      .name-desc {
        font-size: 12px;
        color: var(--el-text-color-secondary);
      }
    }
  }
  
  .text-placeholder {
    color: var(--el-text-color-placeholder);
  }
}

.batch-actions {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 16px;
  padding: 12px 16px;
  background: var(--el-color-primary-light-9);
  border: 1px solid var(--el-color-primary-light-7);
  border-radius: 6px;
  
  .batch-info {
    color: var(--el-color-primary);
    font-weight: 500;
  }
  
  .batch-buttons {
    display: flex;
    gap: 8px;
  }
}

.pagination-container {
  display: flex;
  justify-content: center;
  margin-top: 20px;
  padding: 16px;
  background: var(--el-bg-color);
  border-radius: 8px;
  border: 1px solid var(--el-border-color-light);
}

// 新增资源模态窗口样式
.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}

:deep(.el-dialog) {
  .el-dialog__header {
    padding: 20px 20px 10px 20px;
    border-bottom: 1px solid var(--el-border-color-light);
    
    .el-dialog__title {
      font-size: 18px;
      font-weight: 600;
      color: var(--el-text-color-primary);
    }
  }
  
  .el-dialog__body {
    padding: 20px;
  }
  
  .el-dialog__footer {
    padding: 10px 20px 20px 20px;
    border-top: 1px solid var(--el-border-color-light);
  }
}

:deep(.el-form) {
  .el-form-item {
    margin-bottom: 20px;
    
    .el-form-item__label {
      font-weight: 500;
      color: var(--el-text-color-regular);
    }
    
    .el-input__wrapper {
      border-radius: 6px;
    }
    
    .el-textarea__inner {
      border-radius: 6px;
    }
    
    .el-select {
      .el-input__wrapper {
        border-radius: 6px;
      }
    }
  }
}

// 响应式设计
@media (max-width: 1200px) {
  .filter-bar {
    flex-direction: column;
    gap: 16px;
    align-items: stretch;
    
    .filter-left,
    .filter-right {
      justify-content: center;
      flex-wrap: wrap;
    }
  }
}

@media (max-width: 768px) {
  .resource-list-container {
    padding: 16px;
  }
  
  .filter-bar {
    .filter-left,
    .filter-right {
      flex-direction: column;
      width: 100%;
    }
  }
  
  .batch-actions {
    flex-direction: column;
    gap: 12px;
    text-align: center;
  }
  
  :deep(.el-dialog) {
    width: 90% !important;
    margin: 5vh auto;
  }
}

// 预览和API模态窗口样式
.preview-header {
  margin-bottom: 20px;
  
  h4 {
    margin: 0 0 8px 0;
    color: var(--el-text-color-primary);
    font-size: 18px;
    font-weight: 600;
  }
  
  p {
    margin: 0 0 12px 0;
    color: var(--el-text-color-secondary);
    font-size: 14px;
  }
  
  .preview-info {
    display: flex;
    align-items: center;
    gap: 16px;
    
    .info-item {
      font-size: 13px;
      color: var(--el-text-color-regular);
    }
  }
}

.api-header {
  margin-bottom: 20px;
  
  h4 {
    margin: 0 0 8px 0;
    color: var(--el-text-color-primary);
    font-size: 18px;
    font-weight: 600;
  }
  
  p {
    margin: 0;
    color: var(--el-text-color-secondary);
    font-size: 14px;
  }
}

.api-basic-info {
  .info-row {
    margin-bottom: 16px;
    
    label {
      display: block;
      margin-bottom: 8px;
      font-weight: 500;
      color: var(--el-text-color-regular);
    }
  }
}

.api-examples {
  h5 {
    margin: 0 0 8px 0;
    color: var(--el-text-color-primary);
    font-size: 14px;
    font-weight: 600;
  }
}

.tags-container {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
  
  .tag-item {
    margin: 0;
  }
}
</style>