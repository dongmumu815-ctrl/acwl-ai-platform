<template>
  <div class="models-page">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="header-content">
        <div class="header-left">
          <h1 class="page-title">
            <el-icon><Box /></el-icon>
            模型管理
          </h1>
          <p class="page-description">管理和部署您的AI模型</p>
        </div>
        <div class="header-right">
          <PermissionButton 
            permission="model:create"
            type="primary" 
            @click="showUploadDialog"
          >
            <el-icon><Upload /></el-icon>
            上传模型
          </PermissionButton>
          <el-button @click="refreshModels">
            <el-icon><Refresh /></el-icon>
            刷新
          </el-button>
        </div>
      </div>
    </div>
    
    <!-- 统计卡片 -->
    <div class="stats-cards">
      <el-row :gutter="20">
        <el-col :xs="12" :sm="6">
          <div class="stat-card">
            <div class="stat-icon total">
              <el-icon><Box /></el-icon>
            </div>
            <div class="stat-content">
              <div class="stat-value">{{ stats.total }}</div>
              <div class="stat-label">总模型数</div>
            </div>
          </div>
        </el-col>
        
        <el-col :xs="12" :sm="6">
          <div class="stat-card">
            <div class="stat-icon active">
              <el-icon><VideoPlay /></el-icon>
            </div>
            <div class="stat-content">
              <div class="stat-value">{{ stats.active }}</div>
              <div class="stat-label">已激活</div>
            </div>
          </div>
        </el-col>
        
        <el-col :xs="12" :sm="6">
          <div class="stat-card">
            <div class="stat-icon training">
              <el-icon><Loading /></el-icon>
            </div>
            <div class="stat-content">
              <div class="stat-value">{{ stats.inactive }}</div>
              <div class="stat-label">未激活</div>
            </div>
          </div>
        </el-col>
        
        <el-col :xs="12" :sm="6">
          <div class="stat-card">
            <div class="stat-icon storage">
              <el-icon><FolderOpened /></el-icon>
            </div>
            <div class="stat-content">
              <div class="stat-value">{{ formatSize(stats.totalSize) }}</div>
              <div class="stat-label">存储占用</div>
            </div>
          </div>
        </el-col>
      </el-row>
    </div>
    
    <!-- 筛选和搜索 -->
    <div class="filter-section">
      <el-card shadow="never">
        <el-form :model="filters" inline>
          <el-form-item label="搜索">
            <el-input
              v-model="filters.search"
              placeholder="搜索模型名称或描述"
              clearable
              style="width: 250px"
              @input="handleSearch"
            >
              <template #prefix>
                <el-icon><Search /></el-icon>
              </template>
            </el-input>
          </el-form-item>
          
          <el-form-item label="类型">
            <el-select
              v-model="filters.type"
              placeholder="选择模型类型"
              clearable
              style="width: 150px"
              @change="handleFilter"
            >
              <el-option label="全部" value="" />
              <el-option label="大语言模型" :value="ModelType.LLM" />
              <el-option label="向量模型" :value="ModelType.EMBEDDING" />
              <el-option label="多模态模型" :value="ModelType.MULTIMODAL" />
              <el-option label="其他模型" :value="ModelType.OTHER" />
            </el-select>
          </el-form-item>
          
          <el-form-item label="状态">
            <el-select
              v-model="filters.status"
              placeholder="选择状态"
              clearable
              style="width: 120px"
              @change="handleFilter"
            >
              <el-option label="全部" value="" />
              <el-option label="已激活" value="active" />
              <el-option label="未激活" value="inactive" />
            </el-select>
          </el-form-item>
          
          <el-form-item>
            <el-button @click="resetFilters">
              <el-icon><RefreshLeft /></el-icon>
              重置
            </el-button>
          </el-form-item>
        </el-form>
      </el-card>
    </div>
    
    <!-- 模型列表 -->
    <div class="models-list">
      <el-card shadow="never">
        <template #header>
          <div class="card-header">
            <span>模型列表</span>
            <div class="header-actions">
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
          <el-row :gutter="20" style="row-gap: 20px;">
            <el-col
              v-for="model in paginatedModels"
              :key="model.id"
              :xs="24"
              :sm="12"
              :md="8"
              :lg="6"
            >
              <div class="model-card">
                <div class="model-header">
                  <div class="model-avatar">
                    <img
                      v-if="model.avatar"
                      :src="model.avatar"
                      :alt="model.name"
                    />
                    <el-icon v-else><Box /></el-icon>
                  </div>
                  <div class="model-status">
                    <el-tag
                      :type="model.is_active ? 'success' : 'info'"
                      size="small"
                    >
                      {{ model.is_active ? '已激活' : '未激活' }}
                    </el-tag>
                    <!-- 下载状态显示 -->
                    <el-tag
            v-if="model.download_status"
            :type="getDownloadStatusType(model.download_status)"
            size="small"
            class="download-status-tag"
            :style="model.download_status === 'FAILED' ? 'cursor: pointer;' : ''"
            @click="model.download_status === 'FAILED' ? showDownloadError(model) : null"
          >
            {{ getDownloadStatusText(model.download_status) }}
          </el-tag>
                  </div>
                </div>
                
                <div class="model-content">
                  <h3 class="model-name">{{ model.name }}</h3>
                  <p class="model-description">{{ model.description }}</p>
                  
                  <div class="model-meta">
                    <div class="meta-item">
                      <el-icon><Calendar /></el-icon>
                      <span>{{ formatDate(model.created_at) }}</span>
                    </div>
                    <div class="meta-item">
                    <el-icon><FolderOpened /></el-icon>
                    <span>{{ formatSize(model.model_size || 0) }}</span>
                  </div>
                  <div class="meta-item">
                    <el-icon><View /></el-icon>
                    <span>{{ getTypeText(model.model_type) }}</span>
                  </div>
                  </div>
                  
                  <div class="model-tags">
                    <el-tag
                      size="small"
                      class="tag-item"
                    >
                      {{ model.framework || 'Unknown' }}
                    </el-tag>
                    <el-tag
                      v-if="model.quantization"
                      size="small"
                      class="tag-item"
                      type="warning"
                    >
                      {{ model.quantization }}
                    </el-tag>
                  </div>
                  
                  <!-- 下载进度条 - 已注释，不显示虚假进度 -->
                  <!-- 
                  <div 
                    v-if="model.download_status === 'DOWNLOADING' && model.download_progress !== null"
                    class="download-progress"
                  >
                    <div class="progress-info">
                      <span class="progress-text">下载中...</span>
                      <span class="progress-percent">{{ Math.round(model.download_progress) }}%</span>
                    </div>
                    <el-progress 
                      :percentage="Math.round(model.download_progress)" 
                      :stroke-width="6"
                      :show-text="false"
                      status="success"
                    />
                  </div>
                  -->
                </div>
                
                <div class="model-actions">
                  <el-button
                    size="small"
                    @click="viewModel(model)"
                  >
                    查看
                  </el-button>
                  <el-button
                    v-if="model.is_active"
                    type="primary"
                    size="small"
                    @click="deployModel(model)"
                  >
                    部署
                  </el-button>
                  <el-dropdown trigger="click">
                    <el-button size="small" text>
                      <el-icon><MoreFilled /></el-icon>
                    </el-button>
                    <template #dropdown>
                      <el-dropdown-menu>
                        <el-dropdown-item @click="editModel(model)">
                          <el-icon><Edit /></el-icon>
                          编辑
                        </el-dropdown-item>
                        <!-- <el-dropdown-item @click="cloneModel(model)">
                          <el-icon><CopyDocument /></el-icon>
                          克隆
                        </el-dropdown-item> -->
                        <el-dropdown-item @click="downloadModel(model)">
                          <el-icon><Download /></el-icon>
                          下载
                        </el-dropdown-item>
                        <el-dropdown-item
                          divided
                          @click="deleteModel(model)"
                        >
                          <el-icon><Delete /></el-icon>
                          删除
                        </el-dropdown-item>
                      </el-dropdown-menu>
                    </template>
                  </el-dropdown>
                </div>
              </div>
            </el-col>
          </el-row>
        </div>
        
        <!-- 列表视图 -->
        <div v-else class="list-view">
          <el-table
            :data="paginatedModels"
            style="width: 100%"
            @sort-change="handleTableSort"
          >
            <el-table-column prop="name" label="模型名称" sortable>
              <template #default="{ row }">
                <div class="model-name-cell">
                  <div class="model-avatar-small">
                    <img
                      v-if="row.avatar"
                      :src="row.avatar"
                      :alt="row.name"
                    />
                    <el-icon v-else><Box /></el-icon>
                  </div>
                  <div class="model-info">
                    <div class="name">{{ row.name }}</div>
                    <div class="description">{{ row.description }}</div>
                  </div>
                </div>
              </template>
            </el-table-column>
            
            <el-table-column prop="model_type" label="类型" width="120">
              <template #default="{ row }">
                <el-tag size="small">{{ getTypeText(row.model_type) }}</el-tag>
              </template>
            </el-table-column>
            
            <el-table-column prop="is_active" label="状态" width="150">
              <template #default="{ row }">
                <!-- 下载状态显示 -->
                <div v-if="row.download_status">
                  <el-tag
                    :type="getDownloadStatusType(row.download_status)"
                    size="small"
                    :style="row.download_status === 'FAILED' ? 'cursor: pointer;' : ''"
                    @click="row.download_status === 'FAILED' ? showDownloadError(row) : null"
                  >
                    {{ getDownloadStatusText(row.download_status) }}
                  </el-tag>
                  <div v-if="row.download_status === 'DOWNLOADING' && row.download_progress !== null" class="progress-bar">
                    <!-- 注释掉进度条显示 - 不显示虚假进度 -->
                    <!--
                    <el-progress 
                      :percentage="row.download_progress" 
                      :stroke-width="4"
                      size="small"
                    />
                    -->
                  </div>
                  <div v-if="row.download_status === 'FAILED' && row.download_error" class="error-message">
                    <!-- 移除感叹号图标 -->
                  </div>
                </div>
                <!-- 正常激活状态显示 -->
                <el-tag
                  v-else
                  :type="row.is_active ? 'success' : 'info'"
                  size="small"
                >
                  {{ row.is_active ? '已激活' : '未激活' }}
                </el-tag>
              </template>
            </el-table-column>
            
            <el-table-column prop="model_size" label="大小" width="120" sortable>
              <template #default="{ row }">
                {{ formatSize(row.model_size || 0) }}
              </template>
            </el-table-column>
            
            <el-table-column prop="framework" label="框架" width="120">
              <template #default="{ row }">
                {{ row.framework || 'Unknown' }}
              </template>
            </el-table-column>
            
            <el-table-column prop="created_at" label="创建时间" width="180" sortable>
              <template #default="{ row }">
                {{ formatDate(row.created_at) }}
              </template>
            </el-table-column>
            
            <el-table-column label="操作" width="250" fixed="right">
              <template #default="{ row }">
                <div class="table-actions">
                  <PermissionButton 
                    permission="model:read"
                    size="small" 
                    @click="viewModel(row)"
                  >
                    查看
                  </PermissionButton>
                  <PermissionButton
                    v-if="row.is_active"
                    permission="model:deploy"
                    type="primary"
                    size="small"
                    @click="deployModel(row)"
                  >
                    部署
                  </PermissionButton>
                  <el-dropdown trigger="click">
                    <el-button size="small" text>
                      <el-icon><MoreFilled /></el-icon>
                    </el-button>
                    <template #dropdown>
                      <el-dropdown-menu>
                        <PermissionWrapper permission="model:update">
                          <el-dropdown-item @click="editModel(row)">
                            <el-icon><Edit /></el-icon>
                            编辑
                          </el-dropdown-item>
                        </PermissionWrapper>
                        <PermissionWrapper permission="model:create">
                          <el-dropdown-item @click="cloneModel(row)">
                            <el-icon><CopyDocument /></el-icon>
                            克隆
                          </el-dropdown-item>
                        </PermissionWrapper>
                        <PermissionWrapper permission="model:read">
                          <el-dropdown-item @click="downloadModel(row)">
                            <el-icon><Download /></el-icon>
                            下载
                          </el-dropdown-item>
                        </PermissionWrapper>
                        <PermissionWrapper permission="model:delete">
                          <el-dropdown-item
                            divided
                            @click="deleteModel(row)"
                          >
                            <el-icon><Delete /></el-icon>
                            删除
                          </el-dropdown-item>
                        </PermissionWrapper>
                      </el-dropdown-menu>
                    </template>
                  </el-dropdown>
                </div>
              </template>
            </el-table-column>
          </el-table>
        </div>
        
        <!-- 分页 -->
        <div class="pagination-wrapper">
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
    
    <!-- 上传模型对话框 -->
    <el-dialog
      v-model="uploadDialogVisible"
      title="上传模型"
      width="600px"
      :before-close="handleCloseUpload"
    >
      <el-form
        ref="uploadFormRef"
        :model="uploadForm"
        :rules="uploadRules"
        label-width="100px"
      >
        <el-form-item label="上传方式" prop="uploadType">
          <el-radio-group v-model="uploadForm.uploadType" @change="handleUploadTypeChange">
            <el-radio value="file">文件上传</el-radio>
            <el-radio value="download">源地址下载</el-radio>
          </el-radio-group>
          <div class="form-tip">
            文件上传：直接上传模型文件；源地址下载：通过ModelScope等平台下载模型
          </div>
        </el-form-item>
        
        <el-form-item label="模型名称" prop="name">
          <el-input
            v-model="uploadForm.name"
            placeholder="请输入模型名称"
          />
        </el-form-item>
        
        <el-form-item label="版本" prop="version">
          <el-input
            v-model="uploadForm.version"
            placeholder="请输入版本号"
          />
        </el-form-item>
        
        <el-form-item label="模型类型" prop="type">
          <el-select
            v-model="uploadForm.type"
            placeholder="请选择模型类型"
            style="width: 100%"
          >
            <el-option label="大语言模型" :value="ModelType.LLM" />
            <el-option label="向量模型" :value="ModelType.EMBEDDING" />
            <el-option label="多模态模型" :value="ModelType.MULTIMODAL" />
            <el-option label="其他模型" :value="ModelType.OTHER" />
          </el-select>
        </el-form-item>
        
        <el-form-item label="基础模型" prop="base_model">
          <el-input
            v-model="uploadForm.base_model"
            placeholder="请输入基础模型名称，如：llama2, gpt-3.5"
          />
        </el-form-item>
        
        <el-form-item label="框架" prop="framework">
          <el-select
            v-model="uploadForm.framework"
            placeholder="请选择框架"
            style="width: 100%"
            filterable
            allow-create
          >
            <el-option label="PyTorch" value="PyTorch" />
            <el-option label="TensorFlow" value="TensorFlow" />
            <el-option label="Transformers" value="Transformers" />
            <el-option label="ONNX" value="ONNX" />
            <el-option label="TensorRT" value="TensorRT" />
            <el-option label="OpenVINO" value="OpenVINO" />
            <el-option label="JAX" value="JAX" />
            <el-option label="MindSpore" value="MindSpore" />
            <el-option label="PaddlePaddle" value="PaddlePaddle" />
            <el-option label="其他" value="Other" />
          </el-select>
        </el-form-item>
        
        <el-form-item label="参数量" prop="parameters">
          <el-input-number
            v-model="uploadForm.parameters"
            :min="0"
            :step="1000000"
            placeholder="参数量（如：7000000000 表示70亿参数）"
            style="width: 100%"
          />
          <div class="form-tip">单位：个参数，如70亿参数请输入7000000000</div>
        </el-form-item>
        
        <el-form-item label="量化类型" prop="quantization">
          <el-select
            v-model="uploadForm.quantization"
            placeholder="请选择量化类型"
            style="width: 100%"
            clearable
          >
            <el-option label="FP32" value="FP32" />
            <el-option label="FP16" value="FP16" />
            <el-option label="BF16" value="BF16" />
            <el-option label="INT8" value="INT8" />
            <el-option label="INT4" value="INT4" />
            <el-option label="GPTQ" value="GPTQ" />
            <el-option label="AWQ" value="AWQ" />
            <el-option label="GGML" value="GGML" />
            <el-option label="GGUF" value="GGUF" />
            <el-option label="无量化" value="None" />
          </el-select>
        </el-form-item>
        
        <el-form-item label="源地址" prop="source_url" v-if="uploadForm.uploadType === 'download'">
          <el-input
            v-model="uploadForm.source_url"
            placeholder="请输入模型源地址，如：Qwen/Qwen3-VL-8B-Instruct"
          />
          <div class="form-tip">
            支持ModelScope格式，如：Qwen/Qwen3-VL-8B-Instruct，系统将通过 modelscope download 命令下载
          </div>
        </el-form-item>
        
        <el-form-item label="源地址" prop="source_url" v-else>
          <el-input
            v-model="uploadForm.source_url"
            placeholder="请输入模型源地址（可选），如：https://huggingface.co/model-name"
          />
        </el-form-item>
        
        <el-form-item label="描述" prop="description">
          <el-input
            v-model="uploadForm.description"
            type="textarea"
            :rows="3"
            placeholder="请输入模型描述"
          />
        </el-form-item>
        
        <el-form-item label="标签">
          <el-select
            v-model="uploadForm.tags"
            multiple
            filterable
            allow-create
            placeholder="请选择或输入标签"
            style="width: 100%"
          >
            <el-option
              v-for="tag in commonTags"
              :key="tag"
              :label="tag"
              :value="tag"
            />
          </el-select>
        </el-form-item>
        
        <el-form-item label="模型文件" prop="file" v-if="uploadForm.uploadType === 'file'">
          <el-upload
            ref="uploadRef"
            :auto-upload="false"
            :show-file-list="true"
            :limit="1"
            accept=".zip"
            :before-upload="beforeFileUpload"
            @change="handleFileChange"
            @remove="handleFileRemove"
          >
            <el-button>
              <el-icon><Upload /></el-icon>
              选择文件
            </el-button>
            <template #tip>
              <div class="el-upload__tip">
                仅支持 .zip 格式，文件大小不超过 10GB
              </div>
            </template>
          </el-upload>
        </el-form-item>
      </el-form>
      
      <template #footer>
        <div class="dialog-footer">
          <el-button @click="uploadDialogVisible = false">取消</el-button>
          <el-button
            type="primary"
            @click="submitUpload"
            :loading="uploading"
          >
            上传
          </el-button>
        </div>
      </template>
    </el-dialog>

    <!-- 查看模型对话框 -->
    <el-dialog
      v-model="viewDialogVisible"
      title="模型详情"
      width="800px"
      :before-close="handleCloseView"
    >
      <div v-loading="viewLoading" class="model-detail">
        <div v-if="currentModel" class="detail-content">
          <el-row :gutter="20">
            <el-col :span="12">
              <div class="detail-item">
                <label>模型名称：</label>
                <span>{{ currentModel.name }}</span>
              </div>
            </el-col>
            <el-col :span="12">
              <div class="detail-item">
                <label>版本：</label>
                <span>{{ currentModel.version }}</span>
              </div>
            </el-col>
          </el-row>
          
          <el-row :gutter="20">
            <el-col :span="12">
              <div class="detail-item">
                <label>模型类型：</label>
                <el-tag size="small">{{ getTypeText(currentModel.model_type) }}</el-tag>
              </div>
            </el-col>
            <el-col :span="12">
              <div class="detail-item">
                <label>状态：</label>
                <el-tag :type="currentModel.is_active ? 'success' : 'info'" size="small">
                  {{ currentModel.is_active ? '已激活' : '未激活' }}
                </el-tag>
              </div>
            </el-col>
          </el-row>
          
          <div class="detail-item">
            <label>描述：</label>
            <p>{{ currentModel.description || '暂无描述' }}</p>
          </div>
          
          <el-row :gutter="20">
            <el-col :span="12">
              <div class="detail-item">
                <label>基础模型：</label>
                <span>{{ currentModel.base_model || '无' }}</span>
              </div>
            </el-col>
            <el-col :span="12">
              <div class="detail-item">
                <label>框架：</label>
                <span>{{ currentModel.framework || '未知' }}</span>
              </div>
            </el-col>
          </el-row>
          
          <el-row :gutter="20">
            <el-col :span="12">
              <div class="detail-item">
                <label>模型大小：</label>
                <span>{{ formatSize(currentModel.model_size || 0) }}</span>
              </div>
            </el-col>
            <el-col :span="12">
              <div class="detail-item">
                <label>参数量：</label>
                <span>{{ currentModel.parameters ? formatNumber(currentModel.parameters) : '未知' }}</span>
              </div>
            </el-col>
          </el-row>
          
          <el-row :gutter="20">
            <el-col :span="12">
              <div class="detail-item">
                <label>量化类型：</label>
                <span>{{ currentModel.quantization || '无' }}</span>
              </div>
            </el-col>
            <el-col :span="12">
              <div class="detail-item">
                <label>创建时间：</label>
                <span>{{ formatDate(currentModel.created_at) }}</span>
              </div>
            </el-col>
          </el-row>
          
          <div class="detail-item">
            <label>源地址：</label>
            <span>{{ currentModel.source_url || '无' }}</span>
          </div>
          
          <div class="detail-item">
            <label>本地路径：</label>
            <span>{{ currentModel.local_path || '无' }}</span>
          </div>
        </div>
      </div>
      
      <template #footer>
        <div class="dialog-footer">
          <el-button @click="handleCloseView">关闭</el-button>
        </div>
      </template>
    </el-dialog>

    <!-- 编辑模型对话框 -->
    <el-dialog
      v-model="editDialogVisible"
      title="编辑模型"
      width="800px"
      :before-close="handleCloseEdit"
    >
      <el-form
        ref="editFormRef"
        :model="editForm"
        :rules="editRules"
        label-width="120px"
        v-loading="editLoading"
      >
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="模型名称" prop="name">
              <el-input v-model="editForm.name" placeholder="请输入模型名称" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="版本" prop="version">
              <el-input v-model="editForm.version" placeholder="请输入版本号" />
            </el-form-item>
          </el-col>
        </el-row>
        
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="模型类型" prop="model_type">
              <el-select v-model="editForm.model_type" placeholder="请选择模型类型" style="width: 100%">
                <el-option label="大语言模型" :value="ModelType.LLM" />
                <el-option label="向量模型" :value="ModelType.EMBEDDING" />
                <el-option label="多模态模型" :value="ModelType.MULTIMODAL" />
                <el-option label="其他模型" :value="ModelType.OTHER" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="状态">
              <el-switch
                v-model="editForm.is_active"
                active-text="已激活"
                inactive-text="未激活"
              />
            </el-form-item>
          </el-col>
        </el-row>
        
        <el-form-item label="描述">
          <el-input
            v-model="editForm.description"
            type="textarea"
            :rows="3"
            placeholder="请输入模型描述"
          />
        </el-form-item>
        
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="基础模型">
              <el-input v-model="editForm.base_model" placeholder="请输入基础模型名称" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="框架">
              <el-select v-model="editForm.framework" placeholder="请选择框架" style="width: 100%">
                <el-option label="PyTorch" value="PyTorch" />
                <el-option label="TensorFlow" value="TensorFlow" />
                <el-option label="Transformers" value="Transformers" />
                <el-option label="ONNX" value="ONNX" />
                <el-option label="TensorRT" value="TensorRT" />
                <el-option label="OpenVINO" value="OpenVINO" />
                <el-option label="JAX" value="JAX" />
                <el-option label="MindSpore" value="MindSpore" />
                <el-option label="PaddlePaddle" value="PaddlePaddle" />
                <el-option label="其他" value="Other" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>
        
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="模型大小(字节)">
              <el-input-number
                v-model="editForm.model_size"
                :min="0"
                style="width: 100%"
                placeholder="请输入模型大小"
              />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="参数量">
              <el-input-number
                v-model="editForm.parameters"
                :min="0"
                style="width: 100%"
                placeholder="请输入参数量"
              />
            </el-form-item>
          </el-col>
        </el-row>
        
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="量化类型">
              <el-select v-model="editForm.quantization" placeholder="请选择量化类型" style="width: 100%">
                <el-option label="FP32" value="FP32" />
                <el-option label="FP16" value="FP16" />
                <el-option label="BF16" value="BF16" />
                <el-option label="INT8" value="INT8" />
                <el-option label="INT4" value="INT4" />
                <el-option label="GPTQ" value="GPTQ" />
                <el-option label="AWQ" value="AWQ" />
                <el-option label="GGML" value="GGML" />
                <el-option label="GGUF" value="GGUF" />
                <el-option label="无量化" value="None" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>
        
        <el-form-item label="源地址">
          <el-input v-model="editForm.source_url" placeholder="请输入模型源地址" />
        </el-form-item>
        
        <el-form-item label="本地路径">
          <el-input v-model="editForm.local_path" placeholder="请输入本地存储路径" />
        </el-form-item>
      </el-form>
      
      <template #footer>
        <div class="dialog-footer">
          <el-button @click="handleCloseEdit">取消</el-button>
          <el-button type="primary" @click="handleEditSubmit" :loading="editLoading">
            保存
          </el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import type { UploadInstance, FormInstance, FormRules } from 'element-plus'
import {
  Box,
  Upload,
  Refresh,
  VideoPlay,
  Loading,
  FolderOpened,
  Search,
  RefreshLeft,
  Grid,
  List,
  Calendar,
  View,
  MoreFilled,
  Edit,
  Download,
  Delete,
  CopyDocument,
  Warning
} from '@element-plus/icons-vue'
import { modelApi, type Model, ModelType } from '@/api/models'
import { PermissionButton, PermissionWrapper } from '@/components/Permission'

const router = useRouter()

// 响应式数据
const viewMode = ref('grid')
const uploadDialogVisible = ref(false)
const viewDialogVisible = ref(false)
const editDialogVisible = ref(false)
const uploadFormRef = ref()
const uploadRef = ref()
const editFormRef = ref()
const uploading = ref(false)
const loading = ref(false)
const viewLoading = ref(false)
const editLoading = ref(false)

// 统计数据
const stats = reactive({
  total: 0,
  active: 0,
  inactive: 0,
  totalSize: 0
})

// 筛选条件
const filters = reactive({
  search: '',
  type: '',
  status: '',
  sortBy: 'created_at'
})

// 分页
const pagination = reactive({
  currentPage: 1,
  pageSize: 20,
  total: 0
})

// 模型列表
const models = ref<Model[]>([])

// 当前查看/编辑的模型
const currentModel = ref<Model | null>(null)

// 编辑表单
const editForm = reactive({
  name: '',
  version: '',
  description: '',
  base_model: '',
  model_type: ModelType.LLM,
  model_size: 0,
  parameters: 0,
  framework: '',
  quantization: '',
  source_url: '',
  local_path: '',
  is_active: false
})

// 上传表单
const uploadForm = reactive({
  uploadType: 'file' as 'file' | 'download',
  name: '',
  version: '1.0',
  type: ModelType.LLM,
  base_model: '',
  description: '',
  framework: '',
  parameters: null as number | null,
  quantization: '',
  source_url: '',
  tags: [] as string[],
  file: null as File | null
})

// 常用标签
const commonTags = [
  'GPT', 'BERT', 'Transformer', 'CNN', 'RNN',
  '自然语言处理', '计算机视觉', '语音识别', '推荐系统'
]

// 表单验证规则
const uploadRules: FormRules = {
  name: [
    { required: true, message: '请输入模型名称', trigger: 'blur' }
  ],
  version: [
    { required: true, message: '请输入版本号', trigger: 'blur' }
  ],
  type: [
    { required: true, message: '请选择模型类型', trigger: 'change' }
  ],
  description: [
    { required: true, message: '请输入模型描述', trigger: 'blur' }
  ],
  source_url: [
    {
      validator: (rule: any, value: string, callback: any) => {
        if (uploadForm.uploadType === 'download' && !value) {
          callback(new Error('源地址下载模式必须填写源地址'))
        } else {
          callback()
        }
      },
      trigger: 'blur'
    }
  ],
  file: [
    {
      validator: (rule: any, value: any, callback: any) => {
        if (uploadForm.uploadType === 'file' && !uploadForm.file) {
          callback(new Error('文件上传模式必须选择文件'))
        } else {
          callback()
        }
      },
      trigger: 'change'
    }
  ]
}

// 编辑表单验证规则
const editRules: FormRules = {
  name: [
    { required: true, message: '请输入模型名称', trigger: 'blur' }
  ],
  version: [
    { required: true, message: '请输入模型版本', trigger: 'blur' }
  ],
  model_type: [
    { required: true, message: '请选择模型类型', trigger: 'change' }
  ]
}

// 计算属性
const filteredModels = computed(() => {
  let result = [...models.value]
  
  // 搜索过滤
  if (filters.search) {
    const searchTerm = filters.search.toLowerCase()
    result = result.filter(
      model => 
        model.name.toLowerCase().includes(searchTerm) ||
        model.description?.toLowerCase().includes(searchTerm)
    )
  }
  
  // 类型过滤
  if (filters.type) {
    result = result.filter(model => model.model_type === filters.type)
  }
  
  // 状态过滤
  if (filters.status) {
    if (filters.status === 'active') {
      result = result.filter(model => model.is_active)
    } else if (filters.status === 'inactive') {
      result = result.filter(model => !model.is_active)
    }
  }
  
  // 排序
  result.sort((a, b) => {
    const field = filters.sortBy
    if (field === 'created_at' || field === 'updated_at') {
      return new Date(b[field]).getTime() - new Date(a[field]).getTime()
    }
    if (field === 'size') {
      return (b.model_size || 0) - (a.model_size || 0)
    }
    return 0
  })
  
  return result
})

const paginatedModels = computed(() => {
  // 由于使用服务器端分页，直接返回从API获取的模型列表
  return models.value
})

// 方法
const formatSize = (bytes: number) => {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB', 'TB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

const formatNumber = (num: number) => {
  if (num >= 1e9) {
    return (num / 1e9).toFixed(1) + 'B'
  } else if (num >= 1e6) {
    return (num / 1e6).toFixed(1) + 'M'
  } else if (num >= 1e3) {
    return (num / 1e3).toFixed(1) + 'K'
  }
  return num.toString()
}

const formatDate = (date: string) => {
  return new Date(date).toLocaleString('zh-CN')
}

const getDownloadStatusType = (status: string) => {
  const statusMap: Record<string, string> = {
    PENDING: 'info',
    DOWNLOADING: 'warning',
    COMPLETED: 'success',
    FAILED: 'danger',
    UPLOADED: 'success'
  }
  return statusMap[status] || 'info'
}

const getDownloadStatusText = (status: string) => {
  const statusMap: Record<string, string> = {
    PENDING: '等待下载',
    DOWNLOADING: '下载中',
    COMPLETED: '下载完成',
    FAILED: '下载失败',
    UPLOADED: '已上传'
  }
  return statusMap[status] || '未知状态'
}

const getStatusType = (status: string) => {
  const statusMap: Record<string, string> = {
    ready: 'success',
    running: 'primary',
    training: 'warning',
    error: 'danger'
  }
  return statusMap[status] || 'info'
}

const getStatusText = (status: string) => {
  const statusMap: Record<string, string> = {
    ready: '就绪',
    running: '运行中',
    training: '训练中',
    error: '错误'
  }
  return statusMap[status] || '未知'
}

const getTypeText = (type: ModelType) => {
  const typeMap: Record<ModelType, string> = {
    [ModelType.LLM]: '大语言模型',
    [ModelType.EMBEDDING]: '向量模型',
    [ModelType.MULTIMODAL]: '多模态模型',
    [ModelType.OTHER]: '其他模型'
  }
  return typeMap[type] || type
}

const handleSearch = () => {
  pagination.currentPage = 1
  refreshModels(false) // 不调用统计API
}

const handleFilter = () => {
  pagination.currentPage = 1
  refreshModels(false) // 不调用统计API
}

const handleSort = () => {
  pagination.currentPage = 1
  refreshModels(false) // 不调用统计API
}

const resetFilters = () => {
  filters.search = ''
  filters.type = ''
  filters.status = ''
  filters.sortBy = 'created_at'
  pagination.currentPage = 1
  refreshModels(true) // 重置时获取统计数据
}

const handleTableSort = ({ prop, order }: any) => {
  if (order) {
    filters.sortBy = prop
    pagination.currentPage = 1
    refreshModels(false) // 不调用统计API
  }
}

const handleSizeChange = (size: number) => {
  pagination.pageSize = size
  pagination.currentPage = 1
  refreshModels(false) // 不调用统计API
}

const handleCurrentChange = (page: number) => {
  pagination.currentPage = page
  refreshModels(false) // 不调用统计API
}

const refreshModels = async (fetchStatsData = true) => {
  try {
    loading.value = true
    
    // 调用实际的API
    const response = await modelApi.getModels({
      page: pagination.currentPage,
      size: pagination.pageSize,
      search: filters.search ? filters.search.trim() : undefined,
      model_type: filters.type as ModelType || undefined,
      is_active: filters.status === 'active' ? true : filters.status === 'inactive' ? false : undefined
    })
    
    console.log('搜索参数:', {
      search: filters.search ? filters.search.trim() : undefined,
      model_type: filters.type as ModelType || undefined,
      is_active: filters.status === 'active' ? true : filters.status === 'inactive' ? false : undefined
    })
    console.log('API响应:', response)
    
    // 检查响应数据结构
    if (!response || typeof response !== 'object') {
      throw new Error('API响应格式错误：响应为空或不是对象')
    }
    
    if (!response.items || !Array.isArray(response.items)) {
      throw new Error('API响应格式错误：缺少items字段或items不是数组')
    }
    
    models.value = response.items
    pagination.total = response.total || 0
    
    // 仅在需要时获取统计数据
    if (fetchStatsData) {
      await fetchStats()
    }
  } catch (error: any) {
    console.error('刷新模型列表失败:', error)
    ElMessage.error(error.response?.data?.message || error.message || '刷新失败，请稍后重试')
  } finally {
    loading.value = false
  }
}

const fetchStats = async () => {
  try {
    // 调用统计API
    const statsResponse = await modelApi.getStats()
    
    // 更新统计数据
    if (statsResponse) {
      stats.total = statsResponse.total_count
      stats.active = statsResponse.active_count
      stats.inactive = statsResponse.inactive_count
      stats.totalSize = statsResponse.total_size
    } else {
      // 如果API不可用，回退到本地计算
      updateStatsFromLocalData()
    }
  } catch (error) {
    console.error('获取统计数据失败:', error)
    // 如果API调用失败，回退到本地计算
    updateStatsFromLocalData()
  }
}

const updateStatsFromLocalData = () => {
  stats.total = models.value.length
  stats.active = models.value.filter(m => m.is_active).length
  stats.inactive = models.value.filter(m => !m.is_active).length
  stats.totalSize = models.value.reduce((sum, m) => sum + (m.model_size || 0), 0)
}

const showUploadDialog = () => {
  uploadDialogVisible.value = true
}

const handleCloseUpload = () => {
  uploadForm.uploadType = 'file'
  uploadForm.name = ''
  uploadForm.version = '1.0'
  uploadForm.type = ModelType.LLM
  uploadForm.base_model = ''
  uploadForm.description = ''
  uploadForm.framework = ''
  uploadForm.parameters = null
  uploadForm.quantization = ''
  uploadForm.source_url = ''
  uploadForm.tags = []
  uploadForm.file = null
  uploadDialogVisible.value = false
}

const beforeFileUpload = (file: any) => {
  console.log('beforeFileUpload called with file:', file)
  console.log('File type:', file.type)
  console.log('File name:', file.name)
  
  // 检查文件类型
  const isZip = file.type === 'application/zip' || file.type === 'application/x-zip-compressed' || file.name.toLowerCase().endsWith('.zip')
  console.log('Is zip file:', isZip)
  
  if (!isZip) {
    ElMessage.error('只能上传 .zip 格式的文件!')
    console.log('File type validation failed')
    return false
  }
  
  // 检查文件大小 (10GB = 10 * 1024 * 1024 * 1024 bytes)
  const isLt10GB = file.size / 1024 / 1024 / 1024 < 10
  if (!isLt10GB) {
    ElMessage.error('文件大小不能超过 10GB!')
    console.log('File size validation failed')
    return false
  }
  
  console.log('File validation passed')
  return true
}

const handleFileChange = (file: any) => {
  console.log('handleFileChange called with file:', file)
  
  // 双重验证文件类型
  if (file.raw) {
    const isZip = file.raw.type === 'application/zip' || file.raw.type === 'application/x-zip-compressed' || file.raw.name.toLowerCase().endsWith('.zip')
    if (!isZip) {
      ElMessage.error('只能上传 .zip 格式的文件!')
      // 清除无效文件
      uploadForm.file = null
      // 清除上传组件中的文件列表
      if (uploadRef.value) {
        uploadRef.value.clearFiles()
      }
      return
    }
  }
  
  uploadForm.file = file.raw
}

const handleFileRemove = () => {
  uploadForm.file = null
}

const submitUpload = async () => {
  if (!uploadFormRef.value) return
  
  try {
    await uploadFormRef.value.validate()
    uploading.value = true
    
    // 调用实际的API上传文件
    const formData = new FormData()
    
    // 添加上传类型
    formData.append('upload_type', uploadForm.uploadType)
    
    // 根据上传类型添加不同的字段
    if (uploadForm.uploadType === 'file') {
      // 文件上传模式
      formData.append('file', uploadForm.file!)
    } else {
      // 源地址下载模式
      formData.append('source_url', uploadForm.source_url)
    }
    
    // 添加通用字段
    formData.append('name', uploadForm.name)
    formData.append('version', uploadForm.version)
    formData.append('model_type', uploadForm.type)
    if (uploadForm.base_model) {
      formData.append('base_model', uploadForm.base_model)
    }
    formData.append('description', uploadForm.description)
    if (uploadForm.framework) {
      formData.append('framework', uploadForm.framework)
    }
    if (uploadForm.parameters !== null) {
      formData.append('parameters', uploadForm.parameters.toString())
    }
    if (uploadForm.quantization) {
      formData.append('quantization', uploadForm.quantization)
    }
    if (uploadForm.tags.length > 0) {
      formData.append('tags', JSON.stringify(uploadForm.tags))
    }
    
    await modelApi.uploadModel(formData)
    
    if (uploadForm.uploadType === 'file') {
      ElMessage.success('模型上传成功')
    } else {
      ElMessage.success('模型下载任务已启动，请稍后查看下载进度')
    }
    handleCloseUpload()
    refreshModels()
  } catch (error: any) {
    console.error('上传模型失败:', error)
    ElMessage.error(error.response?.data?.message || '上传失败，请稍后重试')
  } finally {
    uploading.value = false
  }
}

const viewModel = async (model: Model) => {
  try {
    viewLoading.value = true
    const response = await modelApi.getModel(model.id)
    currentModel.value = response
    viewDialogVisible.value = true
  } catch (error: any) {
    console.error('获取模型详情失败:', error)
    ElMessage.error(error.response?.data?.message || '获取模型详情失败，请稍后重试')
  } finally {
    viewLoading.value = false
  }
}

const editModel = async (model: Model) => {
  try {
    viewLoading.value = true
    const response = await modelApi.getModel(model.id)
    currentModel.value = response
    
    // 填充编辑表单
    Object.assign(editForm, {
      name: response.name,
      version: response.version,
      description: response.description || '',
      base_model: response.base_model || '',
      model_type: response.model_type,
      model_size: response.model_size || 0,
      parameters: response.parameters || 0,
      framework: response.framework || '',
      quantization: response.quantization || '',
      source_url: response.source_url || '',
      local_path: response.local_path || '',
      is_active: response.is_active
    })
    
    editDialogVisible.value = true
  } catch (error: any) {
    console.error('获取模型详情失败:', error)
    ElMessage.error(error.response?.data?.message || '获取模型详情失败，请稍后重试')
  } finally {
    viewLoading.value = false
  }
}

const handleCloseView = () => {
  viewDialogVisible.value = false
  currentModel.value = null
}

const handleCloseEdit = () => {
  editDialogVisible.value = false
  currentModel.value = null
  // 重置表单
  Object.assign(editForm, {
    name: '',
    version: '',
    description: '',
    base_model: '',
    model_type: ModelType.LLM,
    model_size: 0,
    parameters: 0,
    framework: '',
    quantization: '',
    source_url: '',
    local_path: '',
    is_active: false
  })
}

const handleEditSubmit = async () => {
  if (!editFormRef.value || !currentModel.value) return
  
  try {
    await editFormRef.value.validate()
    editLoading.value = true
    
    await modelApi.updateModel(currentModel.value.id, editForm)
    
    ElMessage.success('模型更新成功')
    handleCloseEdit()
    refreshModels()
  } catch (error: any) {
    if (error.response) {
      console.error('更新模型失败:', error)
      ElMessage.error(error.response?.data?.message || '更新失败，请稍后重试')
    }
  } finally {
    editLoading.value = false
  }
}

const deployModel = (model: Model) => {
  router.push(`/deployments/create?modelId=${model.id}`)
}

const cloneModel = async (model: Model) => {
  try {
    const { value: newName } = await ElMessageBox.prompt(
      `请输入克隆模型的新名称：`,
      '克隆模型',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        inputValue: `${model.name}-copy`,
        inputPattern: /^.{1,100}$/,
        inputErrorMessage: '模型名称长度应在1-100个字符之间'
      }
    )
    
    await modelApi.cloneModel(model.id, newName)
    
    ElMessage.success('模型克隆成功')
    refreshModels()
  } catch (error: any) {
    if (error !== 'cancel') {
      console.error('克隆模型失败:', error)
      ElMessage.error(error.response?.data?.message || '克隆失败，请稍后重试')
    }
  }
}

const downloadModel = async (model: Model) => {
  try {
    ElMessage.info('正在开始下载...')
    
    // 直接下载文件流
    const response = await modelApi.downloadModelFile(model.id)
    
    // 创建下载链接
    const blob = new Blob([response.data], { type: 'application/zip' })
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `${model.name}-${model.version}.zip`
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    window.URL.revokeObjectURL(url)
    
    ElMessage.success('下载完成')
  } catch (error: any) {
    console.error('下载失败:', error)
    ElMessage.error(error.response?.data?.message || '下载失败，请稍后重试')
  }
}

const deleteModel = async (model: Model) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除模型 "${model.name}" 吗？此操作不可恢复。`,
      '确认删除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    await modelApi.deleteModel(model.id)
    
    ElMessage.success('模型删除成功')
    refreshModels()
  } catch (error: any) {
    if (error !== 'cancel') {
      console.error('删除模型失败:', error)
      ElMessage.error(error.response?.data?.message || '删除失败，请稍后重试')
    }
  }
}

// 下载状态检查定时器
const downloadStatusTimer = ref<NodeJS.Timeout | null>(null)

// 检查下载状态
const checkDownloadStatus = async () => {
  try {
    // 获取所有正在下载的模型
    const downloadingModels = models.value.filter(model => 
      model.download_status && 
      ['PENDING', 'DOWNLOADING'].includes(model.download_status)
    )
    
    if (downloadingModels.length === 0) {
      // 没有正在下载的模型，停止定时器
      if (downloadStatusTimer.value) {
        clearInterval(downloadStatusTimer.value)
        downloadStatusTimer.value = null
      }
      return
    }
    
    // 检查每个正在下载的模型状态
    for (const model of downloadingModels) {
      try {
        const response = await modelApi.getDownloadStatus(model.id)
        // 更新模型的下载状态
        const index = models.value.findIndex(m => m.id === model.id)
        if (index !== -1) {
          models.value[index] = {
            ...models.value[index],
            download_status: response.download_status,
            download_progress: response.download_progress,
            download_error: response.download_error
          }
        }
      } catch (error) {
        console.error(`检查模型 ${model.id} 下载状态失败:`, error)
      }
    }
  } catch (error) {
    console.error('检查下载状态失败:', error)
  }
}

// 启动下载状态检查 -- 不检查
// const startDownloadStatusCheck = () => {
//   if (!downloadStatusTimer.value) {
//     downloadStatusTimer.value = setInterval(checkDownloadStatus, 3000) // 每3秒检查一次
//   }
// }

// 停止下载状态检查
// const stopDownloadStatusCheck = () => {
//   if (downloadStatusTimer.value) {
//     clearInterval(downloadStatusTimer.value)
//     downloadStatusTimer.value = null
//   }
// }

onMounted(() => {
  refreshModels()
  // 启动下载状态检查
  // startDownloadStatusCheck()
})

onUnmounted(() => {
  // 组件卸载时清理定时器
  // stopDownloadStatusCheck()
})

// 显示下载错误详情
const showDownloadError = (model: any) => {
  ElMessageBox.confirm(
    model.download_error || '未知错误',
    '下载失败原因',
    {
      confirmButtonText: '重新下载',
      cancelButtonText: '关闭',
      type: 'error',
      dangerouslyUseHTMLString: false,
      distinguishCancelAndClose: true
    }
  ).then(() => {
    // 点击重新下载按钮
    retryDownload(model)
  }).catch((action) => {
    // 点击关闭或取消按钮，不做任何操作
    if (action === 'cancel' || action === 'close') {
      // 用户取消，不做任何操作
    }
  })
}

// 重新下载模型
const retryDownload = async (model: any) => {
  try {
    // 设置重试状态
    model.retrying = true
    
    // 调用重新下载API
    await modelApi.retryDownload(model.id)
    
    // 更新模型状态
    model.download_status = 'PENDING'
    model.download_error = null
    model.download_progress = 0
    
    ElMessage.success('已重新开始下载')
    
    // 刷新模型列表
    await refreshModels()
  } catch (error: any) {
    console.error('重新下载失败:', error)
    ElMessage.error(error.response?.data?.detail || '重新下载失败')
  } finally {
    model.retrying = false
  }
}
</script>

<style lang="scss" scoped>
.models-page {
  padding: 20px;
  
  .page-header {
    margin-bottom: 20px;
    
    .header-content {
      display: flex;
      justify-content: space-between;
      align-items: flex-start;
      
      .header-left {
        .page-title {
          display: flex;
          align-items: center;
          gap: 8px;
          font-size: 24px;
          font-weight: 600;
          color: var(--el-text-color-primary);
          margin: 0 0 8px 0;
        }
        
        .page-description {
          color: var(--el-text-color-regular);
          margin: 0;
        }
      }
      
      .header-right {
        display: flex;
        gap: 12px;
      }
    }
  }
  
  .stats-cards {
    margin-bottom: 20px;
    
    .stat-card {
      display: flex;
      align-items: center;
      padding: 20px;
      background: white;
      border-radius: 8px;
      box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
      
      .stat-icon {
        width: 48px;
        height: 48px;
        border-radius: 8px;
        display: flex;
        align-items: center;
        justify-content: center;
        margin-right: 16px;
        
        .el-icon {
          font-size: 24px;
          color: white;
        }
        
        &.total {
          background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        }
        
        &.active {
          background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        }
        
        &.training {
          background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
        }
        
        &.storage {
          background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%);
        }
      }
      
      .stat-content {
        .stat-value {
          font-size: 24px;
          font-weight: 600;
          color: var(--el-text-color-primary);
          margin-bottom: 4px;
        }
        
        .stat-label {
          font-size: 14px;
          color: var(--el-text-color-regular);
        }
      }
    }
  }
  
  .filter-section {
    margin-bottom: 20px;
    
    :deep(.el-card__body) {
      padding: 16px 20px;
    }
  }
  
  .models-list {
    .card-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      
      .header-actions {
        display: flex;
        align-items: center;
        gap: 12px;
      }
    }
    
    .grid-view {
      .model-card {
        background: white;
        border: 1px solid var(--el-border-color-light);
        border-radius: 8px;
        padding: 16px;
        transition: all 0.3s ease;
        height: 100%;
        display: flex;
        flex-direction: column;
        
        &:hover {
          box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
          transform: translateY(-2px);
        }
        
        .model-header {
          display: flex;
          justify-content: space-between;
          align-items: flex-start;
          margin-bottom: 12px;
          
          .model-avatar {
            width: 48px;
            height: 48px;
            border-radius: 8px;
            background: var(--el-fill-color-light);
            display: flex;
            align-items: center;
            justify-content: center;
            
            img {
              width: 100%;
              height: 100%;
              border-radius: 8px;
              object-fit: cover;
            }
            
            .el-icon {
              font-size: 24px;
              color: var(--el-text-color-placeholder);
            }
          }
          
          .model-status {
            display: flex;
            flex-direction: column;
            gap: 4px;
            align-items: flex-end;
            
            .download-status-tag {
              margin-top: 4px;
            }
          }
        }
        
        .model-content {
          flex: 1;
          
          .model-name {
            font-size: 16px;
            font-weight: 600;
            color: var(--el-text-color-primary);
            margin: 0 0 8px 0;
            line-height: 1.4;
          }
          
          .model-description {
            font-size: 14px;
            color: var(--el-text-color-regular);
            line-height: 1.5;
            margin: 0 0 12px 0;
            display: -webkit-box;
            -webkit-line-clamp: 2;
            -webkit-box-orient: vertical;
            overflow: hidden;
          }
          
          .model-meta {
            margin-bottom: 12px;
            
            .meta-item {
              display: flex;
              align-items: center;
              gap: 4px;
              font-size: 12px;
              color: var(--el-text-color-secondary);
              margin-bottom: 4px;
              
              &:last-child {
                margin-bottom: 0;
              }
              
              .el-icon {
                font-size: 14px;
              }
            }
          }
          
          .model-tags {
            margin-bottom: 16px;
            
            .tag-item {
              margin-right: 6px;
              margin-bottom: 6px;
            }
          }
          
          .download-progress {
            margin-top: 12px;
            margin-bottom: 16px;
            
            .progress-info {
              display: flex;
              justify-content: space-between;
              align-items: center;
              margin-bottom: 6px;
              
              .progress-text {
                font-size: 12px;
                color: var(--el-text-color-regular);
              }
              
              .progress-percent {
                font-size: 12px;
                font-weight: 600;
                color: var(--el-color-success);
              }
            }
          }
          
          .download-error {
            margin-top: 12px;
            
            :deep(.el-alert) {
              padding: 8px 12px;
              
              .el-alert__title {
                font-size: 12px;
                line-height: 1.4;
              }
            }
          }
        }
        
        .model-actions {
          display: flex;
          justify-content: space-between;
          align-items: center;
          gap: 8px;
          
          .el-button {
            flex: 1;
            
            &:last-child {
              flex: none;
              width: auto;
            }
          }
        }
      }
    }
    
    .list-view {
      .model-name-cell {
        display: flex;
        align-items: center;
        gap: 12px;
        
        .model-avatar-small {
          width: 32px;
          height: 32px;
          border-radius: 6px;
          background: var(--el-fill-color-light);
          display: flex;
          align-items: center;
          justify-content: center;
          flex-shrink: 0;
          
          img {
            width: 100%;
            height: 100%;
            border-radius: 6px;
            object-fit: cover;
          }
          
          .el-icon {
            font-size: 16px;
            color: var(--el-text-color-placeholder);
          }
        }
        
        .model-info {
          .name {
            font-weight: 600;
            color: var(--el-text-color-primary);
            margin-bottom: 2px;
          }
          
          .description {
            font-size: 12px;
            color: var(--el-text-color-secondary);
            display: -webkit-box;
            -webkit-line-clamp: 1;
            -webkit-box-orient: vertical;
            overflow: hidden;
          }
        }
      }
    }
    
    .pagination-wrapper {
      display: flex;
      justify-content: center;
      margin-top: 20px;
    }
    
    .table-actions {
      display: flex;
      gap: 8px;
      align-items: center;
      
      .el-button {
        margin: 0;
      }
    }
    
    .progress-bar {
      margin-top: 4px;
      width: 100%;
    }
    
    .error-message {
      margin-top: 4px;
      display: flex;
      align-items: center;
    }
  }

  .model-detail {
    .detail-content {
      .detail-item {
        margin-bottom: 16px;
        
        label {
          font-weight: 600;
          color: var(--el-text-color-primary);
          margin-right: 8px;
        }
        
        span, p {
          color: var(--el-text-color-regular);
        }
        
        p {
          margin: 4px 0 0 0;
          line-height: 1.5;
        }
      }
    }
  }
}

// 响应式设计
@media (max-width: 768px) {
  .models-page {
    padding: 16px;
    
    .page-header {
      .header-content {
        flex-direction: column;
        gap: 16px;
        
        .header-right {
          width: 100%;
          justify-content: flex-end;
        }
      }
    }
    
    .filter-section {
      :deep(.el-form) {
        .el-form-item {
          margin-bottom: 16px;
          
          .el-input,
          .el-select {
            width: 100% !important;
          }
        }
      }
    }
    
    .models-list {
      .grid-view {
        .model-card {
          .model-actions {
            flex-direction: column;
            
            .el-button {
              width: 100%;
            }
          }
        }
      }
    }
  }
}

// 暗色主题
.dark {
  .models-page {
    .stats-cards {
      .stat-card {
        background: var(--el-bg-color-page);
        border: 1px solid var(--el-border-color);
      }
    }
    
    .models-list {
      .grid-view {
        .model-card {
          background: var(--el-bg-color-page);
          border-color: var(--el-border-color);
        }
      }
    }
  }
}
</style>
