<template>
  <div class="servers-page-container">
    <!-- 左侧分组侧边栏 -->
    <div class="server-sidebar">
      <div class="sidebar-header">
        <span class="sidebar-title">服务器分组</span>
        <el-button link type="primary" @click="showGroupDialog('create')">
          <el-icon><Plus /></el-icon>
        </el-button>
      </div>
      <div class="group-list">
        <div 
          class="group-item" 
          :class="{ active: !currentGroupId }"
          @click="handleGroupSelect(null)"
        >
          <div class="group-info">
            <el-icon><Folder /></el-icon>
            <span class="group-name">全部服务器</span>
          </div>
          <span class="group-count">{{ stats.total || 0 }}</span>
        </div>
        <div 
          v-for="group in serverGroups" 
          :key="group.id"
          class="group-item"
          :class="{ active: currentGroupId === group.id }"
          @click="handleGroupSelect(group.id)"
        >
          <div class="group-info">
            <el-icon><Folder /></el-icon>
            <span class="group-name">{{ group.name }}</span>
          </div>
          <div class="group-actions">
            <span class="group-count">{{ group.server_count }}</span>
            <el-dropdown trigger="click" @command="(cmd) => handleGroupAction(cmd, group)" @click.stop>
              <el-icon class="more-btn"><MoreFilled /></el-icon>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item command="edit">编辑</el-dropdown-item>
                  <el-dropdown-item command="delete" divided type="danger">删除</el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
          </div>
        </div>
      </div>
    </div>

    <!-- 右侧主内容区 -->
    <div class="servers-page">
      <!-- 页面头部 -->
      <div class="page-header">
        <div class="header-content">
          <div class="header-left">
            <h1 class="page-title">
              <el-icon><Monitor /></el-icon>
              {{ currentGroupName }}
            </h1>
            <p class="page-description">管理和监控部署服务器资源</p>
          </div>
          <div class="header-right">
          <div class="auto-refresh">
            <span class="refresh-label">自动刷新</span>
            <el-switch
              v-model="autoRefresh"
              inline-prompt
              active-text="ON"
              inactive-text="OFF"
              @change="handleAutoRefreshChange"
            />
          </div>
          <el-button type="primary" @click="showCreateDialog">
            <el-icon><Plus /></el-icon>
            添加服务器
          </el-button>
          <el-dropdown 
            v-if="selectedServers.length > 0" 
            @command="handleBatchAction"
            style="margin-left: 12px"
          >
            <el-button type="warning" :loading="batchActionLoading">
              批量操作 ({{ selectedServers.length }})
              <el-icon class="el-icon--right"><arrow-down /></el-icon>
            </el-button>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="test">
                  <el-icon><Connection /></el-icon>
                  批量测试连接
                </el-dropdown-item>
                <el-dropdown-item command="password">
                  <el-icon><Key /></el-icon>
                  批量修改密码
                </el-dropdown-item>
                <el-dropdown-item command="script">
                  <el-icon><Cpu /></el-icon>
                  批量执行脚本
                </el-dropdown-item>
                <el-dropdown-item command="restart" divided>
                  <el-icon><VideoPlay /></el-icon>
                  批量重启
                </el-dropdown-item>
                <el-dropdown-item command="delete" type="danger">
                  <el-icon><Delete /></el-icon>
                  批量删除
                </el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
          <el-button @click="refreshServers">
            <el-icon><Refresh /></el-icon>
            刷新
          </el-button>
        </div>
      </div>
    </div>

    <!-- 统计卡片 -->
    <div class="stats-section">
      <el-row :gutter="20">
        <el-col :xs="12" :sm="6">
          <div class="stat-card">
            <div class="stat-icon total">
              <el-icon><Monitor /></el-icon>
            </div>
            <div class="stat-content">
              <div class="stat-value">{{ stats.total }}</div>
              <div class="stat-label">总服务器</div>
            </div>
          </div>
        </el-col>
        
        <el-col :xs="12" :sm="6">
          <div class="stat-card">
            <div class="stat-icon online">
              <el-icon><CircleCheckFilled /></el-icon>
            </div>
            <div class="stat-content">
              <div class="stat-value">{{ stats.online }}</div>
              <div class="stat-label">在线</div>
            </div>
          </div>
        </el-col>
        
        <el-col :xs="12" :sm="6">
          <div class="stat-card">
            <div class="stat-icon offline">
              <el-icon><CircleCloseFilled /></el-icon>
            </div>
            <div class="stat-content">
              <div class="stat-value">{{ stats.offline }}</div>
              <div class="stat-label">离线</div>
            </div>
          </div>
        </el-col>
        
        <el-col :xs="12" :sm="6">
          <div class="stat-card">
            <div class="stat-icon gpus">
              <el-icon><VideoCamera /></el-icon>
            </div>
            <div class="stat-content">
              <div class="stat-value">{{ stats.totalGpus }}</div>
              <div class="stat-label">GPU总数</div>
            </div>
          </div>
        </el-col>
      </el-row>
    </div>

    <!-- 搜索和筛选 -->
    <div class="search-section">
      <el-row :gutter="20">
        <el-col :xs="24" :sm="8">
          <el-input
            v-model="searchQuery"
            placeholder="搜索服务器名称、IP地址..."
            @input="handleSearch"
            clearable
          >
            <template #prefix>
              <el-icon><Search /></el-icon>
            </template>
          </el-input>
        </el-col>
        <el-col :xs="12" :sm="4">
          <el-select
            v-model="filterType"
            placeholder="服务器类型"
            @change="handleFilter"
            clearable
          >
            <el-option label="物理机" value="physical" />
            <el-option label="虚拟机" value="virtual" />
            <el-option label="云服务器" value="cloud" />
          </el-select>
        </el-col>
        <el-col :xs="12" :sm="4">
          <el-select
            v-model="filterStatus"
            placeholder="状态"
            @change="handleFilter"
            clearable
          >
            <el-option label="在线" value="online" />
            <el-option label="离线" value="offline" />
            <el-option label="维护中" value="maintenance" />
          </el-select>
        </el-col>
        <!-- 搜索与重置按钮区域（已移除搜索按钮，仅保留重置） -->
        <el-col :xs="24" :sm="8">
          <div class="search-actions">
            <el-button @click="resetSearch">
              <el-icon><Refresh /></el-icon>
              重置
            </el-button>
          </div>
        </el-col>
      </el-row>
    </div>

    <!-- 服务器列表 -->
    <div class="servers-section">
      <el-card shadow="never">
        <template #header>
          <div class="card-header">
            <span>服务器列表</span>
            <div class="header-actions">
              <el-dropdown v-if="viewMode === 'grid'" @command="handleGridSort" trigger="click" style="margin-right: 12px">
                <el-button size="small">
                  <el-icon style="margin-right: 4px"><Sort /></el-icon>
                  {{ getSortLabel() }}
                  <el-icon class="el-icon--right"><arrow-down /></el-icon>
                </el-button>
                <template #dropdown>
                  <el-dropdown-menu>
                    <el-dropdown-item command="created_at|desc">创建时间 (新->旧)</el-dropdown-item>
                    <el-dropdown-item command="created_at|asc">创建时间 (旧->新)</el-dropdown-item>
                    <el-dropdown-item command="name|asc">名称 (A->Z)</el-dropdown-item>
                    <el-dropdown-item command="name|desc">名称 (Z->A)</el-dropdown-item>
                    <el-dropdown-item command="status|desc">状态 (在线优先)</el-dropdown-item>
                    <el-dropdown-item command="cpu|desc">CPU核心 (多->少)</el-dropdown-item>
                  </el-dropdown-menu>
                </template>
              </el-dropdown>

              <el-radio-group v-model="viewMode" size="small">
                <el-radio-button value="grid">
                  <el-icon><Grid /></el-icon>
                </el-radio-button>
                <el-radio-button value="list">
                  <el-icon><List /></el-icon>
                </el-radio-button>
              </el-radio-group>
            </div>
          </div>
        </template>
        
        <!-- 网格视图 -->
        <div v-if="viewMode === 'grid'" class="grid-view">
          <div class="servers-grid">
            <div
              v-for="server in servers"
              :key="server.id"
              class="server-card"
              :class="{ 'is-selected': isSelected(server) }"
              @click="viewServerDetail(server)"
            >
            <!-- 多选 Checkbox -->
            <div class="server-select-checkbox" @click.stop>
              <el-checkbox 
                :model-value="isSelected(server)"
                @change="(val) => toggleSelection(server, val)"
              />
            </div>
            
            <div class="server-header">
              <div class="server-info">
                <div class="server-name">{{ server.name }}</div>
                <div class="server-ip">
                  {{ server.ip_address }}
                  <el-icon class="copy-icon" @click.stop="copyToClipboard(server.ip_address)"><CopyDocument /></el-icon>
                </div>
              </div>
              <div class="server-status" :class="server.status">
                <el-icon v-if="server.status === 'online'">
                  <CircleCheckFilled />
                </el-icon>
                <el-icon v-else-if="server.status === 'offline'">
                  <CircleCloseFilled />
                </el-icon>
                <el-icon v-else>
                  <WarningFilled />
                </el-icon>
                {{ getStatusText(server.status) }}
              </div>
            </div>
            
            <div class="server-details">
              <div class="detail-item">
                <span class="label">类型:</span>
                <span class="value">{{ getTypeText(server.server_type) }}</span>
              </div>
              <div class="detail-item">
                <span class="label">系统:</span>
                <span class="value">{{ server.os_info || '未知' }}</span>
              </div>
              <div class="detail-item">
                <span class="label">CPU:</span>
                <span class="value">{{ server.total_cpu_cores || 0 }} 核</span>
              </div>
              <div class="detail-item">
                <span class="label">内存:</span>
                <span class="value">{{ server.total_memory || '未知' }}</span>
              </div>
              <div class="detail-item">
                <span class="label">GPU:</span>
                <span class="value">{{ server.gpu_resources?.length || 0 }} 个</span>
              </div>
              <div class="detail-item">
                <span class="label">部署:</span>
                <span class="value">{{ server.deployment_count || 0 }} 个</span>
              </div>
            </div>

            <!-- 实时监控预览 -->
            <div class="server-monitor-preview" v-if="server.status === 'online'">
              <div class="monitor-status-indicator" :class="{ connected: server.monitor_connected }" :title="server.monitor_connected ? '监控已连接' : '监控未连接'">
                <div class="status-dot"></div>
              </div>
              <div class="monitor-item">
                <div class="monitor-label">
                  <span>CPU</span>
                  <span>{{ server.monitor?.cpu_usage || 0 }}%</span>
                </div>
                <el-progress 
                  :percentage="server.monitor?.cpu_usage || 0" 
                  :show-text="false" 
                  :stroke-width="4"
                  :color="getUsageColor(server.monitor?.cpu_usage)"
                />
              </div>
              <div class="monitor-item">
                <div class="monitor-label">
                  <span>内存</span>
                  <span>
                    {{ (server.monitor?.memory_used_kb !== undefined && server.monitor?.memory_used_kb !== null) ? formatSize(server.monitor.memory_used_kb) : '?' }} / {{ (server.monitor?.memory_total_kb !== undefined && server.monitor?.memory_total_kb !== null && server.monitor?.memory_total_kb > 0) ? formatSize(server.monitor.memory_total_kb) : (server.total_memory || '?') }}
                    ({{ server.monitor?.memory_usage || 0 }}%)
                  </span>
                </div>
                <el-progress 
                  :percentage="server.monitor?.memory_usage || 0" 
                  :show-text="false" 
                  :stroke-width="4"
                  :color="getUsageColor(server.monitor?.memory_usage)"
                />
              </div>
              
              <!-- 磁盘监控 (支持多磁盘) -->
              <template v-if="server.monitor?.disk_details && server.monitor.disk_details.length > 0">
                <div class="monitor-item" v-for="(disk, idx) in server.monitor.disk_details" :key="idx">
                  <div class="monitor-label">
                    <span>磁盘 ({{ disk.mount_point }})</span>
                    <span>
                      {{ formatSize(disk.used_kb) }} / {{ formatSize(disk.total_kb) }}
                      ({{ disk.usage }}%)
                    </span>
                  </div>
                  <el-progress 
                    :percentage="disk.usage || 0" 
                    :show-text="false" 
                    :stroke-width="4"
                    :color="getUsageColor(disk.usage)"
                  />
                </div>
              </template>
              <div class="monitor-item" v-else>
                <div class="monitor-label">
                  <span>磁盘</span>
                  <span>
                     <template v-if="server.total_storage">? / {{ server.total_storage }} ({{ server.monitor?.disk_usage || 0 }}%)</template>
                     <template v-else>{{ server.monitor?.disk_usage || 0 }}%</template>
                  </span>
                </div>
                <el-progress 
                  :percentage="server.monitor?.disk_usage || 0" 
                  :show-text="false" 
                  :stroke-width="4"
                  :color="getUsageColor(server.monitor?.disk_usage)"
                />
              </div>

              <div class="monitor-item" v-if="server.monitor?.gpu_count > 0">
                <div class="monitor-label">
                  <span>GPU</span>
                  <span>
                    {{ server.monitor?.gpu_memory_used ? formatSize(server.monitor.gpu_memory_used * 1024) : '?' }} / {{ server.monitor?.gpu_memory_total ? formatSize(server.monitor.gpu_memory_total * 1024) : '?' }}
                    ({{ server.monitor?.gpu_usage || 0 }}%)
                  </span>
                </div>
                <el-progress 
                  :percentage="server.monitor?.gpu_usage || 0" 
                  :show-text="false" 
                  :stroke-width="4"
                  :color="getUsageColor(server.monitor?.gpu_usage)"
                />
              </div>
            </div>
            
            <div class="server-actions" @click.stop>
              <el-button
                size="small"
                @click="testConnection(server)"
                :loading="server.testing"
              >
                <el-icon><Connection /></el-icon>
                测试连接
              </el-button>
              <el-button
                size="small"
                @click="viewGpus(server)"
              >
                <el-icon><VideoCamera /></el-icon>
                GPU资源
              </el-button>
              <el-dropdown @command="handleServerAction">
                <el-button size="small">
                  <el-icon><MoreFilled /></el-icon>
                </el-button>
                <template #dropdown>
                  <el-dropdown-menu>
                    <el-dropdown-item :command="{action: 'edit', server}">
                      <el-icon><Edit /></el-icon>
                      编辑
                    </el-dropdown-item>
                    <el-dropdown-item :command="{action: 'monitor', server}">
                      <el-icon><TrendCharts /></el-icon>
                      监控
                    </el-dropdown-item>
                    <el-dropdown-item :command="{action: 'terminal', server}">
                      <el-icon><Platform /></el-icon>
                      终端
                    </el-dropdown-item>
                    <el-dropdown-item :command="{action: 'scan', server}">
                      <el-icon><Search /></el-icon>
                      扫描GPU
                    </el-dropdown-item>
                    <el-dropdown-item
                      divided
                      :command="{action: 'delete', server}"
                    >
                      <el-icon><Delete /></el-icon>
                      删除
                    </el-dropdown-item>
                  </el-dropdown-menu>
                </template>
              </el-dropdown>
            </div>
          </div>
        </div>
        </div>
        
        <!-- 列表视图 -->
        <div v-else class="list-view">
          <el-table
            :data="servers"
            style="width: 100%"
            @selection-change="handleSelectionChange"
            @sort-change="handleSortChange"
          >
            <el-table-column type="selection" width="55" />
            <el-table-column prop="name" label="服务器名称" sortable="custom">
              <template #default="{ row }">
                <div class="server-name-cell">
                  <div class="server-info">
                    <div class="name">{{ row.name }}</div>
                    <div class="ip">
                      {{ row.ip_address }}
                      <el-icon class="copy-icon" @click.stop="copyToClipboard(row.ip_address)"><CopyDocument /></el-icon>
                    </div>
                  </div>
                </div>
              </template>
            </el-table-column>
            
            <el-table-column prop="server_type" label="类型" width="120">
              <template #default="{ row }">
                <el-tag size="small">{{ getTypeText(row.server_type) }}</el-tag>
              </template>
            </el-table-column>
            
            <el-table-column prop="status" label="状态" width="100" sortable="custom">
              <template #default="{ row }">
                <el-tag
                  :type="row.status === 'online' ? 'success' : row.status === 'offline' ? 'danger' : 'warning'"
                  size="small"
                >
                  {{ getStatusText(row.status) }}
                </el-tag>
              </template>
            </el-table-column>
            
            <el-table-column prop="os_info" label="操作系统" width="150">
              <template #default="{ row }">
                {{ row.os_info || '未知' }}
              </template>
            </el-table-column>
            
            <el-table-column prop="total_cpu_cores" label="CPU" width="80" sortable="custom">
              <template #default="{ row }">
                {{ row.total_cpu_cores || 0 }} 核
              </template>
            </el-table-column>
            
            <el-table-column prop="total_memory" label="内存" width="100">
              <template #default="{ row }">
                {{ row.total_memory || '未知' }}
              </template>
            </el-table-column>
            
            <el-table-column prop="gpu_count" label="GPU" width="80">
              <template #default="{ row }">
                {{ row.gpu_count || 0 }} 个
              </template>
            </el-table-column>
            
            <el-table-column prop="deployment_count" label="部署" width="80">
              <template #default="{ row }">
                {{ row.deployment_count || 0 }} 个
              </template>
            </el-table-column>
            
            <el-table-column label="操作" width="250" fixed="right">
              <template #default="{ row }">
                <el-button
                  size="small"
                  @click="testConnection(row)"
                  :loading="row.testing"
                >
                  <el-icon><Connection /></el-icon>
                  测试连接
                </el-button>
                <el-button
                  size="small"
                  @click="viewGpus(row)"
                >
                  <el-icon><VideoCamera /></el-icon>
                  GPU资源
                </el-button>
                <el-dropdown @command="handleServerAction">
                  <el-button size="small">
                    <el-icon><MoreFilled /></el-icon>
                  </el-button>
                  <template #dropdown>
                    <el-dropdown-menu>
                      <el-dropdown-item :command="{action: 'edit', server: row}">
                        <el-icon><Edit /></el-icon>
                        编辑
                      </el-dropdown-item>
                      <el-dropdown-item :command="{action: 'monitor', server: row}">
                      <el-icon><TrendCharts /></el-icon>
                      监控
                    </el-dropdown-item>
                    <el-dropdown-item :command="{action: 'terminal', server: row}">
                      <el-icon><Platform /></el-icon>
                      终端
                    </el-dropdown-item>
                    <el-dropdown-item :command="{action: 'scan', server: row}">
                      <el-icon><Search /></el-icon>
                      扫描GPU
                    </el-dropdown-item>
                    <el-dropdown-item :command="{action: 'restart', server: row}">
                      <el-icon><VideoPlay /></el-icon>
                      重启
                    </el-dropdown-item>
                    <el-dropdown-item
                      divided
                        :command="{action: 'delete', server: row}"
                      >
                        <el-icon><Delete /></el-icon>
                        删除
                      </el-dropdown-item>
                    </el-dropdown-menu>
                  </template>
                </el-dropdown>
              </template>
            </el-table-column>
          </el-table>
        </div>
        
        <!-- 分页 -->
        <div class="pagination-wrapper">
          <el-pagination
            v-model:current-page="pagination.currentPage"
            v-model:page-size="pagination.pageSize"
            :page-sizes="[12, 24, 48]"
            :total="pagination.total"
            layout="total, sizes, prev, pager, next, jumper"
            @size-change="handleSizeChange"
            @current-change="handleCurrentChange"
          />
        </div>
      </el-card>
    </div>

    <!-- 创建/编辑服务器对话框 -->
    <el-dialog
      v-model="dialogVisible"
      :title="dialogMode === 'create' ? '添加服务器' : '编辑服务器'"
      width="600px"
      @close="resetForm"
    >
      <el-form
        ref="formRef"
        :model="formData"
        :rules="formRules"
        label-width="100px"
      >
        <el-form-item label="服务器名称" prop="name">
          <el-input v-model="formData.name" placeholder="请输入服务器名称" />
        </el-form-item>
        
        <el-form-item label="所属分组" prop="group_id">
          <el-select v-model="formData.group_id" placeholder="请选择分组" style="width: 100%" clearable>
            <el-option
              v-for="group in serverGroups"
              :key="group.id"
              :label="group.name"
              :value="group.id"
            />
          </el-select>
        </el-form-item>
        
        <el-form-item label="IP地址" prop="ip_address">
          <el-input v-model="formData.ip_address" placeholder="请输入IP地址" />
        </el-form-item>
        
        <el-form-item label="SSH端口" prop="ssh_port">
          <el-input-number
            v-model="formData.ssh_port"
            :min="1"
            :max="65535"
            style="width: 100%"
          />
        </el-form-item>
        
        <el-form-item label="SSH用户名" prop="ssh_username">
          <el-input v-model="formData.ssh_username" placeholder="请输入SSH用户名" />
        </el-form-item>

        <el-form-item label="SSH密码" prop="ssh_password">
          <el-input 
            v-model="formData.ssh_password" 
            type="password" 
            placeholder="请输入SSH密码" 
            show-password 
          />
        </el-form-item>
        
        <el-form-item label="SSH密钥路径" prop="ssh_key_path">
          <el-input v-model="formData.ssh_key_path" placeholder="如: ~/.ssh/id_rsa" />
        </el-form-item>
        
        <el-form-item label="服务器类型" prop="server_type">
          <el-select v-model="formData.server_type" style="width: 100%">
            <el-option label="物理机" value="physical" />
            <el-option label="虚拟机" value="virtual" />
            <el-option label="云服务器" value="cloud" />
          </el-select>
        </el-form-item>
        
        <el-form-item label="操作系统" prop="os_info">
          <el-input v-model="formData.os_info" placeholder="如: Ubuntu 22.04 LTS" />
        </el-form-item>
        
        <el-form-item label="总内存" prop="total_memory">
          <el-input v-model="formData.total_memory" placeholder="如: 128GB" />
        </el-form-item>
        
        <el-form-item label="总存储" prop="total_storage">
          <el-input v-model="formData.total_storage" placeholder="如: 2TB" />
        </el-form-item>
        
        <el-form-item label="CPU核心数" prop="total_cpu_cores">
          <el-input-number
            v-model="formData.total_cpu_cores"
            :min="1"
            style="width: 100%"
          />
        </el-form-item>
        
        <el-form-item label="排序权重" prop="sort_order">
          <el-input-number
            v-model="formData.sort_order"
            :min="0"
            :step="1"
            style="width: 100%"
            placeholder="值越小越靠前"
          />
          <div class="form-tip">值越小排序越靠前，默认为0</div>
        </el-form-item>
      </el-form>
      
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="dialogVisible = false">取消</el-button>
          <el-button type="primary" @click="submitForm" :loading="submitting">
            {{ dialogMode === 'create' ? '创建' : '更新' }}
          </el-button>
        </span>
      </template>
    </el-dialog>

    <!-- GPU资源对话框 -->
    <el-dialog
      v-model="gpuDialogVisible"
      title="GPU资源管理"
      width="800px"
    >
      <div class="gpu-section">
        <div class="gpu-header">
          <h4>{{ currentServer?.name }} - GPU资源</h4>
          <el-button size="small" @click="scanGpus">
            <el-icon><Refresh /></el-icon>
            扫描GPU
          </el-button>
        </div>
        
        <div v-if="gpuResources.length === 0" class="no-gpus">
          <el-empty description="暂无GPU资源" />
        </div>
        
        <div v-else class="gpu-list">
          <div
            v-for="gpu in gpuResources"
            :key="gpu.id"
            class="gpu-item"
          >
            <div class="gpu-info">
              <div class="gpu-name">{{ gpu.gpu_name }}</div>
              <div class="gpu-details">
                <span>类型: {{ gpu.gpu_type || '未知' }}</span>
                <span>显存: {{ gpu.memory_size || '未知' }}</span>
                <span>CUDA: {{ gpu.cuda_version || '未知' }}</span>
                <span>设备ID: {{ gpu.device_id || '未知' }}</span>
              </div>
            </div>
            <div class="gpu-status">
              <el-tag :type="gpu.is_available ? 'success' : 'danger'">
                {{ gpu.is_available ? '可用' : '占用中' }}
              </el-tag>
            </div>
          </div>
        </div>
      </div>
    </el-dialog>

    <!-- 批量执行脚本对话框 -->
    <el-dialog
      v-model="scriptDialogVisible"
      title="批量执行脚本"
      width="800px"
      :close-on-click-modal="false"
    >
      <div class="script-dialog-content">
        <el-alert
          title="警告：此操作将在选定的服务器上以 root 权限(或 sudo)执行脚本，请谨慎操作。"
          type="warning"
          show-icon
          style="margin-bottom: 20px"
        />
        
        <el-form label-position="top">
          <el-form-item label="脚本模板">
            <el-select 
              v-model="selectedScriptTemplate" 
              placeholder="选择预设模板" 
              style="width: 100%"
              @change="handleTemplateChange"
            >
              <el-option label="自定义脚本" value="custom" />
              <el-option label="Docker 安装 (Ubuntu 22.04)" value="docker_ubuntu" />
              <el-option label="NVIDIA Driver 自动安装 (Ubuntu)" value="nvidia_driver" />
              <el-option label="系统更新 (apt update & upgrade)" value="apt_update" />
            </el-select>
          </el-form-item>
          
          <el-form-item label="脚本内容">
            <el-input
              v-model="scriptContent"
              type="textarea"
              :rows="10"
              font-family="monospace"
              placeholder="#!/bin/bash"
            />
          </el-form-item>

          <el-form-item label="执行模式">
             <el-radio-group v-model="executionMode">
                <el-radio value="batch">批量执行 ({{ selectedServers.length }} 台)</el-radio>
                <el-radio value="single">单台验证</el-radio>
             </el-radio-group>
          </el-form-item>

          <el-form-item v-if="executionMode === 'single'" label="选择验证服务器">
            <el-select v-model="verificationServerId" placeholder="请选择一台服务器进行验证" style="width: 100%">
               <el-option 
                 v-for="server in selectedServers" 
                 :key="server.id" 
                 :label="server.name + ' (' + server.ip_address + ')'" 
                 :value="server.id" 
               />
            </el-select>
          </el-form-item>
        </el-form>

        <!-- 执行结果展示 -->
        <div v-if="executionResults" class="execution-results">
           <el-divider content-position="left">执行结果</el-divider>
           <el-collapse>
              <el-collapse-item 
                v-for="(res, serverId) in executionResults" 
                :key="serverId" 
                :name="serverId"
              >
                <template #title>
                  <div class="result-header">
                    <span class="server-name">{{ res.server_name }} ({{ res.ip_address }})</span>
                    <el-tag :type="getStatusType(res.status)" size="small" style="margin-left: 10px">
                      {{ getStatusLabel(res.status) }}
                      <el-icon v-if="res.status === 'running'" class="is-loading"><Loading /></el-icon>
                    </el-tag>
                  </div>
                </template>
                <div class="result-content">
                   <div v-if="res.error_message" class="result-message error">{{ res.error_message }}</div>
                   <div v-if="res.stdout">
                     <strong>Output:</strong>
                     <pre class="log-output">{{ res.stdout }}</pre>
                   </div>
                   <div v-if="res.stderr" style="color: red">
                     <strong>Error:</strong>
                     <pre class="log-output">{{ res.stderr }}</pre>
                   </div>
                </div>
              </el-collapse-item>
           </el-collapse>
        </div>
      </div>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="scriptDialogVisible = false">关闭</el-button>
          <el-button type="primary" @click="handleExecuteScript" :loading="scriptExecuting">
            {{ executionMode === 'single' ? '开始验证' : '开始批量执行' }}
          </el-button>
        </span>
      </template>
    </el-dialog>

    <!-- 批量修改密码对话框 -->
    <el-dialog
      v-model="batchPasswordDialogVisible"
      title="批量修改密码"
      width="400px"
    >
      <div class="batch-password-form">
        <el-alert
          title="警告：这将修改所有选中服务器的SSH密码"
          type="warning"
          show-icon
          :closable="false"
          style="margin-bottom: 20px"
        />
        <el-input
          v-model="batchPassword"
          type="password"
          placeholder="请输入新密码"
          show-password
        />
      </div>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="batchPasswordDialogVisible = false">取消</el-button>
          <el-button 
            type="primary" 
            @click="submitBatchPassword" 
            :loading="batchSubmitting"
          >
            确认修改
          </el-button>
        </span>
      </template>
    </el-dialog>

    <!-- 终端抽屉 -->
    <el-drawer
      v-model="terminalDrawerVisible"
      :with-header="false"
      direction="rtl"
      :size="isTerminalFullscreen ? '100%' : '60%'"
      :destroy-on-close="false"
      @opened="handleTerminalDrawerOpened"
    >
      <div class="terminal-drawer-header">
        <span class="drawer-title">Web终端</span>
        <div class="drawer-actions">
          <el-select 
            v-model="globalTerminalTheme" 
            size="small" 
            placeholder="主题风格" 
            class="theme-selector"
            :teleported="false"
          >
            <template #prefix>
              <el-icon><Brush /></el-icon>
            </template>
            <el-option label="默认暗色" value="default">
              <span class="theme-option-label">默认暗色</span>
              <span class="theme-color-preview" style="background: #1e1e1e"></span>
            </el-option>
            <el-option label="GitHub" value="github">
              <span class="theme-option-label">GitHub</span>
              <span class="theme-color-preview" style="background: #ffffff; border: 1px solid #ddd"></span>
            </el-option>
            <el-option label="Solarized Dark" value="solarized-dark">
              <span class="theme-option-label">Solarized</span>
              <span class="theme-color-preview" style="background: #002b36"></span>
            </el-option>
            <el-option label="Monokai" value="monokai">
              <span class="theme-option-label">Monokai</span>
              <span class="theme-color-preview" style="background: #272822"></span>
            </el-option>
            <el-option label="Dracula" value="dracula">
              <span class="theme-option-label">Dracula</span>
              <span class="theme-color-preview" style="background: #282a36"></span>
            </el-option>
          </el-select>
          <el-button link @click="toggleTerminalFullscreen" :title="isTerminalFullscreen ? '退出全屏' : '全屏'">
            <el-icon>
              <ScaleToOriginal v-if="isTerminalFullscreen" />
              <FullScreen v-else />
            </el-icon>
          </el-button>
          <el-button link @click="terminalDrawerVisible = false">
            <el-icon><Close /></el-icon>
          </el-button>
        </div>
      </div>
      <div class="terminal-drawer-content">
        <el-tabs
          v-model="activeTerminalKey"
          type="card"
          editable
          class="terminal-tabs"
          @edit="handleTerminalTabEdit"
          @tab-change="handleTerminalTabChange"
        >
          <el-tab-pane
            v-for="item in terminalSessions"
            :key="item.key"
            :name="item.key"
          >
            <template #label>
              <span 
                class="custom-tabs-label" 
                @contextmenu="openContextMenu($event, item)"
              >
                {{ item.label }}
              </span>
            </template>
            <div class="terminal-pane-content">
              <WebTerminal
                :ref="(el) => setTerminalRef(el, item.key)"
                :server-id="item.serverId"
                :theme="globalTerminalTheme"
              />
            </div>
          </el-tab-pane>
        </el-tabs>

        <!-- Context Menu -->
        <div 
          v-if="contextMenuVisible" 
          class="context-menu" 
          :style="{ top: contextMenuPosition.top + 'px', left: contextMenuPosition.left + 'px' }"
          @click.stop
          @mouseleave="closeContextMenu"
        >
          <div class="menu-item" @click="handleDuplicateSession">
            <el-icon><CopyDocument /></el-icon>
            <span>复制终端</span>
          </div>
        </div>
      </div>
    </el-drawer>

    <!-- 分组表单对话框 -->
    <el-dialog
      v-model="groupDialogVisible"
      :title="groupDialogMode === 'create' ? '创建分组' : '编辑分组'"
      width="400px"
      @close="resetGroupForm"
    >
      <el-form
        ref="groupFormRef"
        :model="groupForm"
        :rules="groupRules"
        label-width="80px"
      >
        <el-form-item label="分组名称" prop="name">
          <el-input v-model="groupForm.name" placeholder="请输入分组名称" />
        </el-form-item>
        <el-form-item label="描述" prop="description">
          <el-input 
            v-model="groupForm.description" 
            type="textarea" 
            :rows="3" 
            placeholder="请输入分组描述" 
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="groupDialogVisible = false">取消</el-button>
          <el-button type="primary" :loading="groupSubmitting" @click="submitGroupForm">
            确定
          </el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, onUnmounted, computed, watch } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox, ElTable } from 'element-plus'
import { getServers, createServer, updateServer, deleteServer, getServerStats, getServerGpuResources, scanServerGpus, testServerConnection, batchTestConnection, batchUpdatePassword, batchRestartServers, 
  batchDeleteServers, 
  restartServer,
  batchExecuteScript,
  getScriptExecutionStatus
} from '@/api/servers'
import { getServerGroups, createServerGroup, updateServerGroup, deleteServerGroup } from '@/api/server-groups'
import WebTerminal from '@/components/WebTerminal.vue'
import { getToken } from '@/utils/auth'

import {
  Monitor,
  Plus,
  Refresh,
  Search,
  CircleCheckFilled,
  CircleCloseFilled,
  WarningFilled,
  VideoCamera,
  Connection,
  MoreFilled,
  Edit,
  Delete,
  TrendCharts,
  Grid,
  List,
  CopyDocument,
  Key,
  VideoPlay,
  Platform,
  ArrowDown,
  Brush,
  Close,
  FullScreen,
  ScaleToOriginal,
  Folder,
  FolderAdd,
  Sort,
  Cpu,
  Loading
} from '@element-plus/icons-vue'

// 路由实例
const router = useRouter()

// 响应式数据
const selectedServers = ref<any[]>([])
const batchActionLoading = ref(false)
const batchPasswordDialogVisible = ref(false)
const batchPassword = ref('')
const batchSubmitting = ref(false)
// 终端相关数据
const terminalDrawerVisible = ref(false)
const isTerminalFullscreen = ref(false)
const terminalSessions = ref<Array<{ key: string; label: string; serverId: number }>>([])
const activeTerminalKey = ref('')
const terminalRefs = new Map<string, any>()
const globalTerminalTheme = ref('default')

// 监控 WebSocket 连接池
const monitorSockets = new Map<number, WebSocket>()

const toggleTerminalFullscreen = () => {
  isTerminalFullscreen.value = !isTerminalFullscreen.value
  // 切换全屏后触发 fit，稍作延迟等待过渡动画
  setTimeout(() => {
    handleTerminalTabChange()
  }, 300)
}

const setTerminalRef = (el: any, key: string) => {
  if (el) {
    terminalRefs.set(key, el)
  } else {
    terminalRefs.delete(key)
  }
}

const handleTerminalTabEdit = (targetKey: string | undefined, action: 'remove' | 'add') => {
  if (action === 'remove' && targetKey) {
    const tabs = terminalSessions.value
    let activeName = activeTerminalKey.value
    if (activeName === targetKey) {
      tabs.forEach((tab, index) => {
        if (tab.key === targetKey) {
          const nextTab = tabs[index + 1] || tabs[index - 1]
          if (nextTab) {
            activeName = nextTab.key
          }
        }
      })
    }
    
    activeTerminalKey.value = activeName
    terminalSessions.value = tabs.filter((tab) => tab.key !== targetKey)
    
    if (terminalSessions.value.length === 0) {
      terminalDrawerVisible.value = false
    }
  }
}

const handleTerminalTabChange = () => {
  // 切换 tab 时，触发当前 tab 的 fit
  const term = terminalRefs.get(activeTerminalKey.value)
  if (term) {
    // 稍微延迟一下，确保 tab 内容可见
    setTimeout(() => {
      term.fit()
    }, 50)
  }
}

const handleTerminalDrawerOpened = () => {
  // 抽屉打开动画结束后，触发当前 tab 的 fit
  handleTerminalTabChange()
}

const searchQuery = ref('')
const filterType = ref('')
const filterStatus = ref('')
const sortBy = ref('created_at')
const sortOrder = ref('desc')
const dialogVisible = ref(false)
const gpuDialogVisible = ref(false)
const dialogMode = ref<'create' | 'edit'>('create')
const submitting = ref(false)
const currentServer = ref<any>(null)
const serverId = ref<number>(0)
const viewMode = ref('grid')
const autoRefresh = ref(false)
let refreshTimer: any = null

// 分页
const pagination = reactive({
  currentPage: 1,
  pageSize: 12,
  total: 0
})

// 分组相关状态
const serverGroups = ref<any[]>([])
const currentGroupId = ref<number | null>(null)
const currentGroupName = computed(() => {
  if (!currentGroupId.value) return '全部服务器'
  const group = serverGroups.value.find(g => g.id === currentGroupId.value)
  return group ? group.name : '未知分组'
})
const groupDialogVisible = ref(false)
const groupDialogMode = ref<'create' | 'edit'>('create')
const groupSubmitting = ref(false)
const groupForm = reactive({
  id: undefined as number | undefined,
  name: '',
  description: ''
})
const groupFormRef = ref<any>(null)
const groupRules = {
  name: [{ required: true, message: '请输入分组名称', trigger: 'blur' }]
}

// 加载分组列表
const loadServerGroups = async () => {
  try {
    const res = await getServerGroups()
    serverGroups.value = res.items || []
  } catch (error) {
    console.error('加载分组列表失败:', error)
  }
}

// 分组选择处理
const handleGroupSelect = (groupId: number | null) => {
  currentGroupId.value = groupId
  pagination.currentPage = 1
  loadServers({ fetchStats: true, fetchGroups: false })
}

// 显示分组对话框
const showGroupDialog = (mode: 'create' | 'edit', group?: any) => {
  groupDialogMode.value = mode
  groupDialogVisible.value = true
  
  if (mode === 'edit' && group) {
    groupForm.id = group.id
    groupForm.name = group.name
    groupForm.description = group.description
  } else {
    resetGroupForm()
  }
}

// 重置分组表单
const resetGroupForm = () => {
  if (groupFormRef.value) {
    groupFormRef.value.resetFields()
  }
  groupForm.id = undefined
  groupForm.name = ''
  groupForm.description = ''
}

// 提交分组表单
const submitGroupForm = async () => {
  if (!groupFormRef.value) return
  
  await groupFormRef.value.validate(async (valid: boolean) => {
    if (valid) {
      groupSubmitting.value = true
      try {
        if (groupDialogMode.value === 'create') {
          await createServerGroup({
            name: groupForm.name,
            description: groupForm.description
          })
          ElMessage.success('创建分组成功')
        } else {
          await updateServerGroup(groupForm.id!, {
            name: groupForm.name,
            description: groupForm.description
          })
          ElMessage.success('更新分组成功')
        }
        groupDialogVisible.value = false
        loadServerGroups()
      } catch (error) {
        ElMessage.error(groupDialogMode.value === 'create' ? '创建分组失败' : '更新分组失败')
        console.error(error)
      } finally {
        groupSubmitting.value = false
      }
    }
  })
}

// 分组操作
const handleGroupAction = async (command: string, group: any) => {
  if (command === 'edit') {
    showGroupDialog('edit', group)
  } else if (command === 'delete') {
    if (group.server_count > 0) {
      ElMessage.warning('该分组下仍有服务器，无法删除')
      return
    }
    
    try {
      await ElMessageBox.confirm(
        `确定要删除分组 "${group.name}" 吗？`,
        '提示',
        {
          confirmButtonText: '确定',
          cancelButtonText: '取消',
          type: 'warning'
        }
      )
      
      await deleteServerGroup(group.id)
      ElMessage.success('删除分组成功')
      
      if (currentGroupId.value === group.id) {
        currentGroupId.value = null
        loadServers()
      }
      loadServerGroups()
    } catch (error: any) {
      if (error !== 'cancel') {
        ElMessage.error('删除分组失败')
      }
    }
  }
}

// 统计数据
const stats = reactive({
  total: 0,
  online: 0,
  offline: 0,
  totalGpus: 0
})

// 服务器列表
const servers = ref<any[]>([])
const gpuResources = ref<any[]>([])

// 表单数据
const formData = reactive({
  name: '',
  ip_address: '',
  ssh_port: 22,
  ssh_username: '',
  ssh_password: '',
  ssh_key_path: '',
  server_type: 'physical',
  os_info: '',
  total_memory: '',
  total_storage: '',
  total_cpu_cores: null,
  group_id: undefined as number | undefined,
  sort_order: 0
})

// 表单验证规则
const validateIpOrDomain = (rule: any, value: string, callback: (error?: Error) => void) => {
  const v = (value || '').trim()
  const hasProtocol = v.includes('://')
  const hasSlash = v.includes('/')
  const hasPort = v.includes(':')
  const ipv4 = /^(25[0-5]|2[0-4]\d|1\d{2}|[1-9]?\d)(\.(25[0-5]|2[0-4]\d|1\d{2}|[1-9]?\d)){3}$/
  const hostname = /^(localhost|(?:[a-zA-Z0-9-]{1,63}\.)+[a-zA-Z]{2,63})$/
  if (!v) return callback(new Error('请输入IP或域名'))
  if (hasProtocol || hasSlash || hasPort) return callback(new Error('请不要包含协议、路径或端口'))
  if (ipv4.test(v) || hostname.test(v)) return callback()
  return callback(new Error('请输入有效的IP或域名'))
}

const formRules = {
  name: [{ required: true, message: '请输入服务器名称', trigger: 'blur' }],
  ip_address: [
    { required: true, message: '请输入IP或域名', trigger: 'blur' },
    { validator: validateIpOrDomain, trigger: 'blur' }
  ],
  ssh_port: [{ required: true, message: '请输入SSH端口', trigger: 'blur' }],
  server_type: [{ required: true, message: '请选择服务器类型', trigger: 'change' }]
}

const formRef = ref()

// 辅助函数
const getTypeText = (type: string) => {
  const map: Record<string, string> = {
    physical: '物理机',
    virtual: '虚拟机',
    cloud: '云服务器'
  }
  return map[type] || type
}

const getStatusText = (status: string) => {
  const map: Record<string, string> = {
    online: '在线',
    offline: '离线',
    maintenance: '维护中'
  }
  return map[status] || status
}

const getUsageColor = (usage: number = 0) => {
  if (usage >= 90) return '#f56c6c'
  if (usage >= 70) return '#e6a23c'
  return '#67c23a'
}

const formatSize = (kb: number) => {
  if (!kb) return '0 B'
  if (kb < 1024) return kb + ' KB'
  if (kb < 1024 * 1024) return (kb / 1024).toFixed(1) + ' MB'
  if (kb < 1024 * 1024 * 1024) return (kb / (1024 * 1024)).toFixed(1) + ' GB'
  return (kb / (1024 * 1024 * 1024)).toFixed(1) + ' TB'
}

// 建立监控 WebSocket 连接
const connectMonitor = (server: any) => {
  if (monitorSockets.has(server.id)) return

  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
  const host = window.location.host
  const token = getToken()
  const wsUrl = `${protocol}//${host}/api/v1/ws/monitor/${server.id}?token=${token}`
  
  try {
    const socket = new WebSocket(wsUrl)
    
    socket.onopen = () => {
      // Find current server to update status
      const currentServer = servers.value.find(s => s.id === server.id)
      if (currentServer) {
        currentServer.monitor_connected = true
      }
    }

    socket.onmessage = (event) => {
      try {
        const msg = JSON.parse(event.data)
        
        if (msg.type === 'error') {
          console.error(`Server ${server.id} monitoring error:`, msg.message)
          // If server reports error (e.g. SSH failed), stop retrying
          monitorSockets.delete(server.id)
          const currentServer = servers.value.find(s => s.id === server.id)
          if (currentServer) {
            currentServer.monitor_connected = false
            // Optional: You could add a field to show error state in UI
            // currentServer.monitor_error = msg.message 
          }
          return
        }

        if (msg.type === 'monitor_data' && msg.data) {
          // Find the current server object in the reactive array
          // This ensures that even if servers.value is replaced (e.g. by auto-refresh),
          // we update the currently displayed object.
          const currentServer = servers.value.find(s => s.id === server.id)
          
          if (currentServer) {
             if (!currentServer.monitor) {
                currentServer.monitor = {
                  cpu_usage: 0,
                  memory_usage: 0,
                  disk_usage: 0,
                  gpu_usage: 0,
                  gpu_count: 0,
                  gpu_memory_used: 0,
                  gpu_memory_total: 0,
                  disk_details: []
                }
             }
             currentServer.monitor.cpu_usage = msg.data.cpu_usage
             currentServer.monitor.memory_usage = msg.data.memory_usage
             currentServer.monitor.memory_total_kb = msg.data.memory_total_kb
             currentServer.monitor.memory_used_kb = msg.data.memory_used_kb
             currentServer.monitor.disk_usage = msg.data.disk_usage
             currentServer.monitor.gpu_usage = msg.data.gpu_usage
             currentServer.monitor.gpu_count = msg.data.gpu_count
             currentServer.monitor.gpu_memory_used = msg.data.gpu_memory_used
             currentServer.monitor.gpu_memory_total = msg.data.gpu_memory_total
             currentServer.monitor.disk_details = msg.data.disk_details
             
             // Update static info if provided (auto-synced from backend)
             if (msg.data.total_memory) {
               currentServer.total_memory = msg.data.total_memory
             }
             if (msg.data.total_storage) {
               currentServer.total_storage = msg.data.total_storage
             }
             
             // Ensure connected status is true (in case onopen didn't catch the right object ref)
             currentServer.monitor_connected = true
          }
        }
      } catch (e) {
        console.warn('解析监控数据失败:', e)
      }
    }
    
    socket.onerror = (error) => {
      console.warn(`监控连接错误 (Server ${server.id}):`, error)
      const currentServer = servers.value.find(s => s.id === server.id)
      if (currentServer) {
        currentServer.monitor_connected = false
      }
    }
    
    socket.onclose = () => {
      // Check if this was an intentional close (stopped by user/component unmount)
      // If stopMonitoring() was called, the socket is already removed from the map.
      const wasMonitoring = monitorSockets.has(server.id)
      monitorSockets.delete(server.id)
      
      const currentServer = servers.value.find(s => s.id === server.id)
      if (currentServer) {
        currentServer.monitor_connected = false
      }

      // Only reconnect if it was in the map (meaning accidental close)
      if (wasMonitoring) {
        console.log(`监控连接意外断开 (Server ${server.id})，5秒后尝试重连...`)
        setTimeout(() => {
          // Check if server is still in the list and online before reconnecting
          const s = servers.value.find(item => item.id === server.id)
          if (s && s.status === 'online') {
            connectMonitor(s)
          }
        }, 5000)
      }
    }
    
    monitorSockets.set(server.id, socket)
  } catch (e) {
    console.error(`创建监控连接失败 (Server ${server.id}):`, e)
    const currentServer = servers.value.find(s => s.id === server.id)
    if (currentServer) {
      currentServer.monitor_connected = false
    }
  }
}

// 启动监控数据更新
const startMonitoring = () => {
  servers.value.forEach(server => {
    if (server.status === 'online') {
      connectMonitor(server)
    }
  })
}

// 停止所有监控连接
const stopMonitoring = () => {
  const sockets = new Map(monitorSockets)
  monitorSockets.clear() // Clear first to prevent reconnect logic in onclose
  sockets.forEach(socket => {
    socket.close()
  })
}

// 方法
const isSelected = (server: any) => {
  return selectedServers.value.some(s => s.id === server.id)
}

const toggleSelection = (server: any, checked: boolean) => {
  if (checked) {
    if (!isSelected(server)) {
      selectedServers.value.push(server)
    }
  } else {
    selectedServers.value = selectedServers.value.filter(s => s.id !== server.id)
  }
}

const handleSelectionChange = (val: any[]) => {
  selectedServers.value = val
}

// 批量脚本执行相关
const scriptDialogVisible = ref(false)
const selectedScriptTemplate = ref('custom')
const scriptContent = ref('')
const executionMode = ref('batch')
const verificationServerId = ref<number | null>(null)
const scriptExecuting = ref(false)
const executionResults = ref<any>(null)

const TEMPLATES = {
  docker_ubuntu: `#!/bin/bash

# install-docker-cn.sh
# 在 Ubuntu 上安装 Docker 并配置国内镜像加速（适用于 20.04 / 22.04 / 24.04）
# Updated by Trae

# 设置日志文件
LOG_FILE="/var/log/acwl_docker_install.log"
# 确保日志文件可写（如果脚本以 sudo 运行）
touch "$LOG_FILE" || LOG_FILE="/tmp/acwl_docker_install.log"
echo "🔍 日志将记录到: $LOG_FILE"

# 将 stdout 和 stderr 同时输出到控制台和日志文件
exec > >(tee -a "$LOG_FILE") 2>&1

set -e  # 遇错即停

echo "🚀 开始执行 Docker 安装/配置脚本..."
date "+%Y-%m-%d %H:%M:%S"

SKIP_INSTALL=false

# 0. 检查 Docker 是否已安装
if command -v docker &> /dev/null; then
    echo "✅ 检测到 Docker 已安装，版本: $(docker --version)"
    
    # 检查服务状态
    if systemctl is-active --quiet docker; then
        echo "✅ Docker 服务运行正常。"
        echo "⏩ 将跳过基础安装步骤，仅更新镜像源配置以确保加速生效。"
        SKIP_INSTALL=true
    else
        echo "⚠️  Docker 服务未运行，将执行完整安装流程以尝试修复..."
    fi
else
    echo "⚪ Docker 未安装，准备开始安装..."
fi

if [ "$SKIP_INSTALL" = "false" ]; then
    # 1. 更新系统并安装依赖
    echo "🔧 正在更新系统并安装必要依赖..."
    sudo apt-get update
    sudo apt-get install -y ca-certificates curl gnupg lsb-release

    # 2. 添加 Docker 清华镜像 GPG 密钥
    echo "🔑 正在添加 Docker GPG 密钥（清华源）..."
    sudo install -m 0755 -d /etc/apt/keyrings
    # 如果文件存在先删除，避免交互式确认
    if [ -f /etc/apt/keyrings/docker.gpg ]; then
        sudo rm /etc/apt/keyrings/docker.gpg
    fi
    curl -fsSL https://mirrors.tuna.tsinghua.edu.cn/docker-ce/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
    sudo chmod a+r /etc/apt/keyrings/docker.gpg

    # 3. 添加清华 Docker APT 源
    echo "📥 正在添加 Docker 清华软件源..."
    UBUNTU_CODENAME=$(lsb_release -cs)
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://mirrors.tuna.tsinghua.edu.cn/docker-ce/linux/ubuntu $UBUNTU_CODENAME stable" \\
      | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

    # 4. 安装 Docker 引擎及相关组件
    echo "📦 正在安装 Docker Engine 和插件..."
    sudo apt-get update
    # 使用非交互模式安装，避免因配置文件冲突或服务重启确认导致卡死
    export DEBIAN_FRONTEND=noninteractive
    sudo -E apt-get install -y -o Dpkg::Options::="--force-confdef" -o Dpkg::Options::="--force-confold" docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
fi

# 5. 配置国内镜像加速器 (始终执行，确保配置最新)
echo "🌐 正在配置 Docker 国内镜像加速器..."
sudo mkdir -p /etc/docker

# 备份原有配置
if [ -f /etc/docker/daemon.json ]; then
    BACKUP_FILE="/etc/docker/daemon.json.bak.$(date +%s)"
    echo "📄 备份现有配置到 $BACKUP_FILE"
    sudo cp /etc/docker/daemon.json "$BACKUP_FILE"
fi

cat <<EOF | sudo tee /etc/docker/daemon.json
{
  "registry-mirrors": [
    "https://docker.xuanyuan.me",
    "https://docker.1ms.run",
    "https://docker.m.daocloud.io"
  ],
  "runtimes": {
    "nvidia": {
      "args": [],
      "path": "nvidia-container-runtime"
    }
  }
}
EOF

# 6. 重启 Docker 服务
echo "🔄 正在重启 Docker 服务..."
sudo systemctl daemon-reload
sudo systemctl restart docker
sudo systemctl enable docker

# 7. 将当前用户加入 docker 组（避免每次用 sudo）
REAL_USER=\${SUDO_USER:-$(whoami)}
if [ "$REAL_USER" = "root" ]; then
    echo "⚠️  当前似乎是直接以 root 运行，跳过用户组配置。"
else
    # 检查用户是否已在 docker 组
    if groups "$REAL_USER" | grep &>/dev/null '\\bdocker\\b'; then
        echo "✅ 用户 $REAL_USER 已在 docker 组中。"
    else
        echo "👥 正在将用户 $REAL_USER 加入 docker 用户组..."
        sudo usermod -aG docker "$REAL_USER"
    fi
fi

# 8. 提示用户重新登录或刷新组权限
echo ""
echo "✅ Docker 部署/配置完成！"
echo ""
if [ "$SKIP_INSTALL" = "false" ]; then
    echo "💡 提示：如果是首次安装，请执行 'newgrp docker' 或重新登录以生效组权限。"
fi
echo "🧪 验证安装："
echo "   docker run --rm hello-world"
echo ""

echo "✅ 脚本执行完毕"
date "+%Y-%m-%d %H:%M:%S"
`,
  nvidia_driver: `#!/bin/bash
# Auto install NVIDIA drivers on Ubuntu
# 注意：安装后可能需要重启
set -e

echo "Updating apt..."
sudo apt-get update
sudo apt-get install -y ubuntu-drivers-common

echo "Auto installing drivers..."
sudo ubuntu-drivers autoinstall

echo "Done. Please restart the server."
`,
  apt_update: `#!/bin/bash
set -e
sudo apt-get update
sudo apt-get upgrade -y
echo "System updated."
`
}

const handleTemplateChange = (val: string) => {
  if (val === 'custom') {
    scriptContent.value = ''
  } else {
    scriptContent.value = TEMPLATES[val as keyof typeof TEMPLATES] || ''
  }
}

const scriptTaskId = ref<number | null>(null)
let pollTimer: any = null

const getStatusType = (status: string) => {
  const map: Record<string, string> = {
    'pending': 'info',
    'running': 'primary',
    'completed': 'success',
    'success': 'success',
    'failed': 'danger',
    'timeout': 'warning',
    'partial_failed': 'warning'
  }
  return map[status] || 'info'
}

const getStatusLabel = (status: string) => {
  const map: Record<string, string> = {
    'pending': '等待中',
    'running': '执行中',
    'completed': '已完成',
    'success': '成功',
    'failed': '失败',
    'timeout': '超时',
    'partial_failed': '部分失败'
  }
  return map[status] || status
}

const pollExecutionStatus = async (taskId: number) => {
  try {
    const res = await getScriptExecutionStatus(taskId)
    const record = res.data || res
    
    // 转换后端详情列表为前端 map 结构
    const results: Record<number, any> = {}
    if (record.details) {
      record.details.forEach((detail: any) => {
        results[detail.server_id] = {
          server_name: detail.server_name,
          ip_address: detail.server_ip, // 注意后端字段可能不同，这里假设后端返回 server_ip
          status: detail.status,
          stdout: detail.stdout,
          stderr: detail.stderr,
          error_message: detail.error_message
        }
      })
    }
    executionResults.value = results

    // 检查是否所有任务都已结束
    const isFinished = ['completed', 'failed', 'partial_failed'].includes(record.status)
    
    if (isFinished) {
      if (pollTimer) {
        clearInterval(pollTimer)
        pollTimer = null
      }
      scriptExecuting.value = false
      if (record.status === 'completed') {
        ElMessage.success('脚本批量执行完成')
      } else if (record.status === 'partial_failed') {
        ElMessage.warning('脚本执行完成，但有部分服务器失败')
      } else {
        ElMessage.error('脚本执行失败')
      }
    }
  } catch (error) {
    console.error('获取执行状态失败:', error)
    // 不中断轮询，可能是网络波动
  }
}

const handleExecuteScript = async () => {
  if (!scriptContent.value.trim()) {
    ElMessage.warning('请输入脚本内容')
    return
  }

  let targetIds: number[] = []
  if (executionMode.value === 'single') {
    if (!verificationServerId.value) {
      ElMessage.warning('请选择验证服务器')
      return
    }
    targetIds = [verificationServerId.value]
  } else {
    targetIds = selectedServers.value.map(s => s.id)
  }

  if (targetIds.length === 0) return

  scriptExecuting.value = true
  executionResults.value = null
  
  try {
    const res = await batchExecuteScript(targetIds, scriptContent.value)
    const taskId = res.task_id || (res.data as any)?.task_id
    
    if (taskId) {
      scriptTaskId.value = taskId
      ElMessage.success('脚本任务已提交，正在执行...')
      
      // 立即轮询一次
      await pollExecutionStatus(taskId)
      
      // 启动轮询
      if (pollTimer) clearInterval(pollTimer)
      pollTimer = setInterval(() => {
        pollExecutionStatus(taskId)
      }, 2000) // 每2秒轮询一次
    } else {
      throw new Error('未获取到任务ID')
    }
  } catch (error: any) {
    console.error(error)
    ElMessage.error(error.message || '脚本执行出错')
    scriptExecuting.value = false
  }
}

// 监听对话框关闭，清除轮询
watch(() => scriptDialogVisible.value, (val) => {
  if (!val && pollTimer) {
    clearInterval(pollTimer)
    pollTimer = null
  }
})

// 批量操作处理
const handleBatchAction = async (command: string) => {
  if (selectedServers.value.length === 0) return
  if (batchActionLoading.value) return
  
  const ids = selectedServers.value.map(s => s.id)
  const serverNames = selectedServers.value.map(s => s.name).join(', ')
  
  if (command === 'test') {
    try {
      batchActionLoading.value = true
      ElMessage.info('开始批量测试连接...')
      // 幂等性设计：前端防止重复提交，API层面假设支持幂等
      await batchTestConnection(ids)
      ElMessage.success('批量测试请求已发送，请稍后刷新查看状态')
      loadServers()
    } catch (error: any) {
      ElMessage.error(error.message || '批量测试失败')
    } finally {
      batchActionLoading.value = false
    }
  } else if (command === 'password') {
    batchPassword.value = ''
    batchPasswordDialogVisible.value = true
  } else if (command === 'script') {
    scriptDialogVisible.value = true
    scriptContent.value = ''
    selectedScriptTemplate.value = 'custom'
    executionMode.value = 'batch'
    executionResults.value = null
  } else if (command === 'restart') {
    try {
      await ElMessageBox.confirm(
        `确定要重启以下 ${ids.length} 台服务器吗？\n${serverNames}`,
        '批量重启确认',
        {
          confirmButtonText: '确定重启',
          cancelButtonText: '取消',
          type: 'warning'
        }
      )
      
      batchActionLoading.value = true
      ElMessage.info('正在发起批量重启请求...')
      
      const res = await batchRestartServers(ids)
      const results = res.results || []
      const failed = results.filter((r: any) => !r.success)
      
      if (failed.length === 0) {
        ElMessage.success('所有服务器重启指令已发送')
      } else if (failed.length === ids.length) {
        ElMessage.error('所有服务器重启失败')
      } else {
        ElMessage.warning(`操作完成，但在 ${failed.length} 台服务器上失败`)
      }
      
      loadServers()
    } catch (error: any) {
      if (error !== 'cancel') {
        ElMessage.error(error.message || '批量重启失败')
      }
    } finally {
      batchActionLoading.value = false
    }
  } else if (command === 'delete') {
    try {
      await ElMessageBox.confirm(
        `确定要删除以下 ${ids.length} 台服务器吗？此操作不可恢复！\n${serverNames}`,
        '批量删除确认',
        {
          confirmButtonText: '确定删除',
          cancelButtonText: '取消',
          type: 'error'
        }
      )
      
      batchActionLoading.value = true
      
      const res = await batchDeleteServers(ids)
      const results = res.results || []
      const failed = results.filter((r: any) => !r.success)
      
      if (failed.length === 0) {
        ElMessage.success('批量删除操作完成')
      } else if (failed.length === ids.length) {
        ElMessage.error('所有服务器删除失败')
      } else {
        ElMessage.warning(`操作完成，但在 ${failed.length} 台服务器上失败`)
      }
      
      selectedServers.value = [] // 清空选中
      loadServers()
    } catch (error: any) {
      if (error !== 'cancel') {
        ElMessage.error(error.message || '批量删除失败')
      }
    } finally {
      batchActionLoading.value = false
    }
  }
}

const submitBatchPassword = async () => {
  if (!batchPassword.value) {
    ElMessage.warning('请输入新密码')
    return
  }
  
  try {
    batchSubmitting.value = true
    const ids = selectedServers.value.map(s => s.id)
    await batchUpdatePassword(ids, batchPassword.value)
    ElMessage.success('批量修改密码成功')
    batchPasswordDialogVisible.value = false
    batchPassword.value = ''
  } catch (error: any) {
    ElMessage.error(error.message || '批量修改密码失败')
  } finally {
    batchSubmitting.value = false
  }
}

const copyToClipboard = async (text: string) => {
  try {
    await navigator.clipboard.writeText(text)
    ElMessage.success('IP地址已复制')
  } catch (err) {
    console.error('复制失败:', err)
    ElMessage.error('复制失败')
  }
}

const handleAutoRefreshChange = (val: boolean) => {
  if (val) {
    // 立即刷新一次
    loadServers({ fetchStats: true })
    // 设置定时器
    refreshTimer = setInterval(() => {
      loadServers({ fetchStats: true })
    }, 30000) // 每30秒刷新一次
  } else {
    if (refreshTimer) {
      clearInterval(refreshTimer)
      refreshTimer = null
    }
  }
}


// 新增：独立统计数据获取方法，保证与列表查询解耦
const fetchStats = async () => {
  try {
    const statsResponse = await getServerStats()
    console.log('服务器统计数据:', statsResponse)
    const s = (statsResponse && (statsResponse as any).data) ? (statsResponse as any).data : statsResponse
    stats.total = (s as any)?.total ?? 0
    stats.online = (s as any)?.online ?? 0
    stats.offline = (s as any)?.offline ?? 0
    stats.totalGpus = (s as any)?.total_gpus ?? 0
  } catch (error) {
    console.error('获取服务器统计数据失败:', error)
  }
}

const loadServers = async (opts?: { fetchStats?: boolean, fetchGroups?: boolean }) => {
  try {
    // 根据选项决定是否刷新统计
    if ((opts?.fetchStats ?? true) === true) {
      await fetchStats()
    }

    // 获取分页列表数据（携带查询参数）
    const params: any = {
      page: pagination.currentPage,
      size: pagination.pageSize,
      search: (searchQuery.value?.trim() || undefined),
      server_type: (filterType.value || undefined),
      status: (filterStatus.value || undefined),
      sort_by: sortBy.value,
      sort_order: sortOrder.value
    }
    
    // 如果选择了分组，添加分组筛选
    if (currentGroupId.value) {
      params.group_id = currentGroupId.value
    }
    
    console.log('列表查询参数:', params)

    const response: any = await getServers(params)
    console.log('服务器列表数据:', response)

    // 适配多种可能的API响应结构
    let serverList = []
    if (response.data?.items) {
      serverList = response.data.items
    } else if (Array.isArray(response.data)) {
      serverList = response.data
    } else if (response.items) {
      serverList = response.items
    } else if (response.data?.data) {
      serverList = response.data.data
    }

    console.log('解析后的服务器列表:', serverList)
    servers.value = serverList || []

    // 启动监控 (暂时禁用以减少资源消耗，列表页不需要建立大量SSH连接)
    startMonitoring()

    // 如果有分页信息，使用分页总数
    pagination.total = response.data?.total || response.total || serverList?.length || 0
    
    // 刷新分组列表以更新计数
    if (opts?.fetchGroups !== false) {
      loadServerGroups()
    }
  } catch (error) {
    ElMessage.error('加载服务器列表失败')
    console.error('加载服务器列表错误:', error)
  }
}

const handleSearch = () => {
  pagination.currentPage = 1
  // 只刷新列表，不刷新统计
  loadServers({ fetchStats: false })
}

const handleFilter = () => {
  pagination.currentPage = 1
  // 只刷新列表，不刷新统计
  loadServers({ fetchStats: false })
}

const handleSortChange = ({ prop, order }: any) => {
  if (!order) {
    sortBy.value = 'created_at'
    sortOrder.value = 'desc'
  } else {
    // 映射前端 prop 到后端字段
    const map: Record<string, string> = {
      'name': 'name',
      'status': 'status',
      'total_cpu_cores': 'cpu'
    }
    sortBy.value = map[prop] || 'created_at'
    sortOrder.value = order === 'ascending' ? 'asc' : 'desc'
  }
  loadServers({ fetchStats: false })
}

const handleGridSort = (command: string) => {
  const [field, order] = command.split('|')
  sortBy.value = field
  sortOrder.value = order
  loadServers({ fetchStats: false })
}

const getSortLabel = () => {
  const map: Record<string, string> = {
    'created_at|desc': '创建时间',
    'created_at|asc': '创建时间',
    'name|asc': '名称 (A-Z)',
    'name|desc': '名称 (Z-A)',
    'status|desc': '状态',
    'cpu|desc': 'CPU核心'
  }
  const key = `${sortBy.value}|${sortOrder.value}`
  return map[key] || '排序'
}

const refreshServers = () => {
  // 刷新按钮完整刷新统计与列表
  loadServers({ fetchStats: true })
}

// 生命周期
onMounted(() => {
  // 首次进入页面，获取统计与列表
  loadServers({ fetchStats: true })
  
  // 加载分组列表
  loadServerGroups()
})

onUnmounted(() => {
  if (refreshTimer) clearInterval(refreshTimer)
  stopMonitoring()
})

const showCreateDialog = () => {
  dialogMode.value = 'create'
  resetForm()
  dialogVisible.value = true
}

const handleEdit = (server: any) => {
  dialogMode.value = 'edit'
  serverId.value = server.id
  Object.assign(formData, {
    name: server.name,
    ip_address: server.ip_address,
    ssh_port: server.ssh_port,
    ssh_username: server.ssh_username,
    ssh_password: server.ssh_password,
    ssh_key_path: server.ssh_key_path,
    server_type: server.server_type,
    os_info: server.os_info,
    total_memory: server.total_memory,
    total_storage: server.total_storage,
    total_cpu_cores: server.total_cpu_cores,
    group_id: server.group_id,
    sort_order: server.sort_order || 0
  })
  dialogVisible.value = true
}

const resetForm = () => {
  Object.assign(formData, {
    name: '',
    ip_address: '',
    ssh_port: 22,
    ssh_username: '',
    ssh_password: '',
    ssh_key_path: '',
    server_type: 'physical',
    os_info: '',
    total_memory: '',
    total_storage: '',
    total_cpu_cores: null,
    group_id: undefined as number | undefined,
    sort_order: 0
  })
  formRef.value?.clearValidate()
}

const submitForm = async () => {
  try {
    await formRef.value?.validate()
    submitting.value = true
    
    if (dialogMode.value === 'create') {
      await createServer(formData) // 传递 reactive 对象本身
    } else {
      await updateServer(serverId.value, formData)
    }
    
    ElMessage.success(dialogMode.value === 'create' 
      ? '服务器创建成功' 
      : '服务器更新成功'
    )
    dialogVisible.value = false
    loadServers() // 刷新列表
  } catch (error) {
    ElMessage.error('操作失败：' + (error.response?.data?.message || error.message))
  } finally {
    submitting.value = false
  }
}


const testConnection = async (server: any) => {
  server.testing = true
  try {
    // 调用API测试连接
    const response = await testServerConnection(server.id)
    
    // 直接使用响应中的数据，不需要通过response.data访问
    if (response.status === 'success') {
      ElMessage.success(response.message || '连接测试成功')
      server.status = 'online'
      
      // 更新服务器详细信息
      if (response.data) {
        if (response.data.os_info) server.os_info = response.data.os_info
        if (response.data.total_cpu_cores) server.total_cpu_cores = response.data.total_cpu_cores
        if (response.data.total_memory) server.total_memory = response.data.total_memory
        if (response.data.gpu_count !== undefined) server.gpu_count = response.data.gpu_count
        if (response.data.status) server.status = response.data.status
      }
    } else {
      ElMessage.error(`连接测试失败: ${response.message || '未知错误'}`)
      server.status = 'offline'
    }
  } catch (error: any) {
    ElMessage.error(`连接测试失败: ${error.response?.data?.message || error.message || '未知错误'}`)
    server.status = 'offline'
  } finally {
    server.testing = false
  }
}

const viewGpus = (server: any) => {
  currentServer.value = server
  loadGpuResources(server.id)
  gpuDialogVisible.value = true
}

const loadGpuResources = async (serverId: number) => {
  try {
    const res: any = await getServerGpuResources(serverId)
    const list = Array.isArray(res?.data) ? res.data : (Array.isArray(res) ? res : [])
    gpuResources.value = list || []
  } catch (error: any) {
    console.error('加载GPU资源失败:', error)
    ElMessage.error(error?.response?.data?.message || '加载GPU资源失败')
  }
}

const scanGpus = async () => {
  try {
    const serverId = currentServer.value?.id
    if (!serverId) {
      ElMessage.warning('请先选择服务器')
      return
    }
    const res: any = await scanServerGpus(serverId)
    const list = Array.isArray(res?.data) ? res.data : (Array.isArray(res) ? res : [])
    gpuResources.value = list || []
    ElMessage.success('GPU扫描完成')
  } catch (error: any) {
    console.error('GPU扫描失败:', error)
    ElMessage.error(error?.response?.data?.message || 'GPU扫描失败')
  }
}

// Context Menu Logic
const contextMenuVisible = ref(false)
const contextMenuPosition = reactive({ top: 0, left: 0 })
const currentContextSession = ref<any>(null)

const openContextMenu = (e: MouseEvent, session: any) => {
  e.preventDefault()
  contextMenuVisible.value = true
  contextMenuPosition.top = e.clientY
  contextMenuPosition.left = e.clientX
  currentContextSession.value = session
}

const closeContextMenu = () => {
  contextMenuVisible.value = false
  currentContextSession.value = null
}

const handleDuplicateSession = () => {
  if (currentContextSession.value) {
    const session = currentContextSession.value
    // Use a unique key for the new session
    const newKey = `server-${session.serverId}-${Date.now()}`
    
    const newSession = {
      key: newKey,
      label: session.label, // Use same label
      serverId: session.serverId
    }
    
    // Find index to insert after
    const index = terminalSessions.value.findIndex(s => s.key === session.key)
    if (index !== -1) {
      terminalSessions.value.splice(index + 1, 0, newSession)
    } else {
      terminalSessions.value.push(newSession)
    }
    
    activeTerminalKey.value = newKey
    closeContextMenu()
  }
}

// Close context menu on global click
const handleGlobalClick = () => {
  if (contextMenuVisible.value) {
    closeContextMenu()
  }
}

onMounted(() => {
  window.addEventListener('click', handleGlobalClick)
})

onUnmounted(() => {
  window.removeEventListener('click', handleGlobalClick)
})

const handleServerAction = async ({ action, server }: any) => {
  switch (action) {
    case 'edit':
      dialogMode.value = 'edit'
      serverId.value = server.id
      Object.assign(formData, server)
      dialogVisible.value = true
      break
    case 'monitor':
      // 跳转到监控页面
      router.push('/monitoring')
      break
    case 'scan':
      currentServer.value = server
      await scanGpus()
      break
    case 'restart':
      try {
        await ElMessageBox.confirm('确定要重启这个服务器吗？重启期间服务将不可用。', '确认重启', {
          confirmButtonText: '确定重启',
          cancelButtonText: '取消',
          type: 'warning'
        })
        await restartServer(server.id)
        ElMessage.success('重启命令已发送')
      } catch (error: any) {
        if (error !== 'cancel') {
           ElMessage.error(error.message || '重启失败')
        }
      }
      break
    case 'terminal':
      {
        const existingSession = terminalSessions.value.find(s => s.serverId === server.id)
        if (existingSession) {
          activeTerminalKey.value = existingSession.key
        } else {
          const key = `server-${server.id}-${Date.now()}`
          terminalSessions.value.push({
            key,
            label: server.name,
            serverId: server.id
          })
          activeTerminalKey.value = key
        }
        terminalDrawerVisible.value = true
      }
      break
    case 'delete':
      try {
        await ElMessageBox.confirm('确定要删除这个服务器吗？', '确认删除', {
          type: 'warning'
        })
        await deleteServer(server.id)
        ElMessage.success('服务器删除成功')
        loadServers()
      } catch (error) {
        if (error !== 'cancel') {
          ElMessage.error('删除服务器失败')
        }
      }
      break
  }
}

const viewServerDetail = (server: any) => {
  // TODO: 跳转到服务器详情页面
  console.log('查看服务器详情:', server)
}

// 新增：重置搜索与筛选
const resetSearch = () => {
  searchQuery.value = ''
  filterType.value = ''
  filterStatus.value = ''
  pagination.currentPage = 1
  loadServers()
}

const handleSizeChange = (size: number) => {
  pagination.pageSize = size
  loadServers({ fetchStats: false })
}

const handleCurrentChange = (page: number) => {
  pagination.currentPage = page
  loadServers({ fetchStats: false })
}



// 生命周期（已上移并统一为加载统计+列表）
</script>

<style scoped>
.log-output {
  background-color: #1e1e1e;
  color: #d4d4d4;
  padding: 10px;
  border-radius: 4px;
  max-height: 200px;
  overflow-y: auto;
  font-family: 'Consolas', 'Monaco', monospace;
  font-size: 12px;
  white-space: pre-wrap;
  margin: 5px 0;
}

.result-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: 100%;
  padding-right: 10px;
}

.script-dialog-content {
  max-height: 60vh;
  overflow-y: auto;
  padding-right: 10px;
}

.servers-page {
  padding: 20px;
}

/* 终端相关样式 */
.terminal-drawer-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  border-bottom: 1px solid #dcdfe6;
}

.terminal-drawer-header .drawer-title {
  font-size: 16px;
  font-weight: 600;
  color: #303133;
}

.terminal-drawer-header .drawer-actions {
  display: flex;
  align-items: center;
  gap: 12px;
}

.theme-selector {
  width: 140px;
}

.theme-option-label {
  float: left;
}

.theme-color-preview {
  float: right;
  width: 16px;
  height: 16px;
  border-radius: 4px;
  margin-top: 8px;
  margin-left: 8px;
}

.terminal-drawer-content {
  height: calc(100% - 65px); /* 减去header高度 */
  display: flex;
  flex-direction: column;
}

.terminal-tabs {
  height: 100%;
  display: flex;
  flex-direction: column;
}

:deep(.terminal-tabs .el-tabs__content) {
  flex: 1;
  padding: 0;
}

:deep(.terminal-tabs .el-tab-pane) {
  height: 100%;
}

.terminal-pane-content {
  height: 100%;
  background-color: #1e1e1e;
  padding: 10px;
}

.custom-tabs-label {
  display: inline-block;
  user-select: none;
}

.context-menu {
  position: fixed;
  z-index: 9999;
  background-color: #fff;
  border: 1px solid #dcdfe6;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
  border-radius: 4px;
  padding: 5px 0;
  min-width: 120px;
}

.context-menu .menu-item {
  padding: 8px 16px;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  color: #606266;
  transition: background-color 0.3s;
}

.context-menu .menu-item:hover {
  background-color: #f5f7fa;
  color: #409eff;
}

/* 布局容器 */
.servers-page-container {
  display: flex;
  height: 100%;
  width: 100%;
  overflow: hidden;
  background-color: #f0f2f5;
}

/* 侧边栏样式 */
.server-sidebar {
  width: 240px;
  background-color: #fff;
  border-right: 1px solid #dcdfe6;
  display: flex;
  flex-direction: column;
  flex-shrink: 0;
}

.sidebar-header {
  padding: 16px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-bottom: 1px solid #ebeef5;
}

.sidebar-title {
  font-size: 16px;
  font-weight: 600;
  color: #303133;
}

.group-list {
  flex: 1;
  overflow-y: auto;
  padding: 8px;
}

.group-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 12px;
  margin-bottom: 4px;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.3s;
}

.group-item:hover {
  background-color: #f5f7fa;
}

.group-item.active {
  background-color: #e6f7ff;
  color: #1890ff;
}

.group-info {
  display: flex;
  align-items: center;
  gap: 8px;
  overflow: hidden;
}

.group-name {
  font-size: 14px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.group-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}

.group-count {
  font-size: 12px;
  color: #909399;
  background-color: #f0f2f5;
  padding: 2px 6px;
  border-radius: 10px;
}

.more-btn {
  transform: rotate(90deg);
  cursor: pointer;
  color: #909399;
  display: none;
}

.group-item:hover .more-btn {
  display: block;
}

/* 主内容区样式调整 */
.servers-page {
  flex: 1;
  display: flex;
  flex-direction: column;
  height: 100%;
  overflow-y: auto;
  padding: 20px;
}

.page-header {
  margin-bottom: 24px;
  background-color: #fff;
  padding: 20px;
  border-radius: 12px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.page-title {
  margin: 0;
  font-size: 24px;
  font-weight: 600;
  color: #1f2937;
  display: flex;
  align-items: center;
  gap: 8px;
}

.page-description {
  margin: 4px 0 0 0;
  color: #6b7280;
  font-size: 14px;
}

.header-right {
  display: flex;
  gap: 12px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-weight: 600;
}

.header-actions {
  display: flex;
  gap: 12px;
}

.stats-section {
  margin-bottom: 24px;
}

.stat-card {
  background: white;
  border-radius: 12px;
  padding: 20px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  display: flex;
  align-items: center;
  gap: 16px;
  transition: all 0.3s ease;
}

.server-card {
  position: relative; /* 为 checkbox 定位 */
  cursor: pointer;
  background: white;
  border-radius: 12px;
  transition: all 0.3s ease;
}

.server-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.server-card.is-selected {
  border-color: #3b82f6;
  background-color: #eff6ff;
  box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.2);
}

.server-select-checkbox {
  position: absolute;
  top: 12px;
  left: 12px;
  right: auto;
  z-index: 10;
  width: 32px;
  height: 32px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
  color: white;
}

.stat-icon.total {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.stat-icon.online {
  background: linear-gradient(135deg, #4ade80 0%, #22c55e 100%);
}

.stat-icon.offline {
  background: linear-gradient(135deg, #f87171 0%, #ef4444 100%);
}

.stat-icon.gpus {
  background: linear-gradient(135deg, #fbbf24 0%, #f59e0b 100%);
}

.stat-content {
  flex: 1;
}

.stat-value {
  font-size: 28px;
  font-weight: 700;
  color: #1f2937;
  line-height: 1;
}

.stat-label {
  font-size: 14px;
  color: #6b7280;
  margin-top: 4px;
}

.search-section {
  margin-bottom: 24px;
}

.servers-section {
  margin-bottom: 24px;
}

.grid-view .servers-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(400px, 1fr));
  gap: 20px;
  margin-bottom: 24px;
}

.list-view {
  margin-bottom: 24px;
}

.server-name-cell {
  display: flex;
  align-items: center;
}

.server-name-cell .server-info .name {
  font-weight: 600;
  color: #1f2937;
  margin-bottom: 2px;
}

.server-name-cell .server-info .ip {
  font-size: 12px;
  color: #6b7280;
}

.server-card {
  background: white;
  border-radius: 12px;
  padding: 20px;
  border: 1px solid #e5e7eb;
  transition: all 0.3s ease;
  cursor: pointer;
}

.server-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  border-color: #3b82f6;
}

.server-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 16px;
  padding-left: 48px;
}

.server-name {
  font-size: 18px;
  font-weight: 600;
  color: #1f2937;
  margin-bottom: 4px;
}

.server-ip {
  font-size: 14px;
  color: #6b7280;
  font-family: 'Monaco', 'Menlo', monospace;
  display: flex;
  align-items: center;
  gap: 4px;
}

.copy-icon {
  cursor: pointer;
  font-size: 14px;
  color: #9ca3af;
  transition: color 0.2s;
}

.copy-icon:hover {
  color: #3b82f6;
}

.server-status {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  font-weight: 500;
  padding: 4px 8px;
  border-radius: 6px;
}

.server-status.online {
  color: #059669;
  background: #d1fae5;
}

.server-status.offline {
  color: #dc2626;
  background: #fee2e2;
}

.server-status.maintenance {
  color: #d97706;
  background: #fef3c7;
}

.server-details {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 8px;
  margin-bottom: 16px;
}

.detail-item {
  display: flex;
  justify-content: space-between;
  font-size: 14px;
}

.detail-item .label {
  color: #6b7280;
}

.detail-item .value {
  color: #1f2937;
  font-weight: 500;
}

/* 监控预览样式 */
.server-monitor-preview {
  position: relative;
  margin-bottom: 16px;
  padding: 12px;
  background-color: #f9fafb;
  border-radius: 8px;
  border: 1px solid #f3f4f6;
}

.monitor-status-indicator {
  position: absolute;
  top: 8px;
  right: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 12px;
  height: 12px;
  cursor: help;
}

.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background-color: #d1d5db;
  transition: all 0.3s ease;
}

.monitor-status-indicator.connected .status-dot {
  background-color: #10b981;
  box-shadow: 0 0 8px rgba(16, 185, 129, 0.6);
}

.monitor-item {
  margin-bottom: 8px;
}

.monitor-item:last-child {
  margin-bottom: 0;
}

.monitor-label {
  display: flex;
  justify-content: space-between;
  font-size: 12px;
  color: #6b7280;
  margin-bottom: 4px;
}

.server-actions {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.pagination-wrapper {
  display: flex;
  justify-content: center;
  margin-top: 24px;
}

.gpu-section {
  max-height: 400px;
  overflow-y: auto;
}

.gpu-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  padding-bottom: 12px;
  border-bottom: 1px solid #e5e7eb;
}

.gpu-header h4 {
  margin: 0;
  color: #1f2937;
}

.no-gpus {
  text-align: center;
  padding: 40px 0;
}

.gpu-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.gpu-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px;
  background: #f9fafb;
  border-radius: 8px;
  border: 1px solid #e5e7eb;
}

.gpu-info {
  flex: 1;
}

.gpu-name {
  font-weight: 600;
  color: #1f2937;
  margin-bottom: 4px;
}

.gpu-details {
  display: flex;
  gap: 16px;
  font-size: 12px;
  color: #6b7280;
}

.gpu-status {
  margin-left: 16px;
}

@media (max-width: 768px) {
  .servers-grid {
    grid-template-columns: 1fr;
  }
  
  .server-details {
    grid-template-columns: 1fr;
  }
  
  .gpu-details {
    flex-direction: column;
    gap: 4px;
  }
}
.form-tip {
  font-size: 12px;
  color: #909399;
  margin-top: 4px;
}
</style>