<template>
  <div class="api-fields">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="header-content">
        <div class="header-left">
          <el-button size="small" @click="goBack">
            <el-icon><ArrowLeft /></el-icon>
            返回
          </el-button>
          <div class="title-section">
            <h1 class="page-title">
              <el-icon><Setting /></el-icon>
              API字段映射
            </h1>
            <p v-if="apiInfo" class="page-description">
              {{ apiInfo.api_name }} ({{ apiInfo.api_code }})
            </p>
          </div>
        </div>
        <div class="header-right">
          <template v-if="!isMappingMode">
            <el-button type="primary" @click="showCreateDialog">
              <el-icon><Plus /></el-icon>
              添加字段
            </el-button>
            <el-button @click="openCenterDrawer"> 从资源类型添加 </el-button>
          </template>
          <el-button @click="loadFields()">
            <el-icon><Refresh /></el-icon>
            刷新
          </el-button>
        </div>
      </div>
    </div>

    <!-- 1. 数据详情 (API信息卡片) -->
    <div v-if="apiInfo" class="page-card">
      <div class="card-header">
        <h3>数据详情</h3>
      </div>
      <div class="api-info">
        <el-row :gutter="20">
          <el-col :span="6">
            <div class="info-item">
              <span class="label">API名称:</span>
              <span class="value">{{ apiInfo.api_name }}</span>
            </div>
          </el-col>
          <el-col :span="6">
            <div class="info-item">
              <span class="label">API代码:</span>
              <span class="value">{{ apiInfo.api_code }}</span>
            </div>
          </el-col>
          <el-col :span="6">
            <div class="info-item">
              <span class="label">请求方法:</span>
              <el-tag :type="getMethodTagType(apiInfo.http_method)">
                {{ apiInfo.http_method }}
              </el-tag>
            </div>
          </el-col>
          <el-col :span="6">
            <div class="info-item">
              <span class="label">状态:</span>
              <el-tag :type="apiInfo.is_active ? 'success' : 'danger'">
                {{ apiInfo.is_active ? "激活" : "禁用" }}
              </el-tag>
            </div>
          </el-col>
        </el-row>
        <el-row :gutter="20" style="margin-top: 8px">
          <el-col :span="6">
            <div class="info-item">
              <span class="label">资源类型:</span>
              <span class="value">
                <template v-if="resourceTypeName">
                  {{ resourceTypeName }}
                </template>
                <template v-else> 未配置 </template>
              </span>
            </div>
          </el-col>
        </el-row>
      </div>
    </div>

    <!-- 映射模式 -->
    <template v-if="isMappingMode">
      <!-- 2. 数据源选择 -->
      <div class="page-card">
        <div class="card-header">
          <h3>数据源配置</h3>
          <div class="header-actions">
            <el-select
              v-model="selectedDatasourceId"
              placeholder="选择数据源"
              style="width: 220px"
              filterable
              @change="handleDatasourceChange"
            >
              <el-option
                v-for="ds in datasources"
                :key="ds.id"
                :label="ds.name"
                :value="ds.id"
              />
            </el-select>
            <el-select
              v-model="selectedSchema"
              placeholder="选择Schema"
              style="width: 180px"
              filterable
              clearable
              :disabled="!selectedDatasourceId"
              @change="handleSchemaChange"
            >
              <el-option
                v-for="sch in schemas"
                :key="sch.name"
                :label="sch.name"
                :value="sch.name"
              />
            </el-select>
            <el-select
              v-model="selectedTable"
              placeholder="选择数据表"
              style="width: 220px"
              filterable
              :disabled="!selectedDatasourceId"
              @change="handleTableChange"
            >
              <el-option
                v-for="tb in tables"
                :key="tb.name"
                :label="tb.name"
                :value="tb.name"
              />
            </el-select>

            <el-divider direction="vertical" />

            <el-button
              :disabled="sourceFields.length === 0 || targetFields.length === 0"
              @click="clearMapping"
              >清空映射</el-button
            >
            <el-button
              type="primary"
              :disabled="sourceFields.length === 0 || targetFields.length === 0"
              @click="autoMapping"
              >自动映射</el-button
            >
            <el-button
              :disabled="mappingPairs.length === 0"
              @click="previewVisible = true"
              >预览配置</el-button
            >
            <el-button
              type="success"
              :disabled="mappingPairs.length === 0 || !canSave"
              @click="saveMapping"
              >保存映射</el-button
            >
          </div>
        </div>
      </div>

      <!-- 3. 字段映射 (模仿 FieldMapping.vue) -->
      <div v-if="selectedTable" class="page-card mapping-container">
        <div ref="scrollArea" class="mapping-board">
          <div class="mapping-columns">
            <!-- 左侧：API字段 (源) -->
            <div ref="sourceListRef" class="source-list">
              <div class="list-header">
                <h3>API 字段 (源)</h3>
                <div style="display: flex; align-items: center; gap: 8px">
                  <span class="count">{{ sourceFields.length }}</span>
                  <el-button
                    type="primary"
                    link
                    size="small"
                    @click="addSourceField"
                  >
                    <el-icon><Plus /></el-icon>
                    自定义
                  </el-button>
                </div>
              </div>
              <div class="fields-scroll-container">
                <div
                  v-for="sf in sourceFields"
                  :id="'source-field-' + sf.field_name"
                  :key="sf.field_name"
                  :ref="(el) => setSourceRef(sf.field_name, el as HTMLElement)"
                  :class="[
                    'field-item',
                    selectedSource === sf.field_name ? 'active' : '',
                    hasSourceMapping(sf.field_name) ? 'mapped' : '',
                    highlightedField === sf.field_name ? 'highlighted' : '',
                  ]"
                  @click="handleSourceClick(sf.field_name)"
                >
                  <div class="field-content">
                    <div class="field-info">
                      <span class="field-name" :title="sf.field_name">
                        {{ sf.field_name }}
                      </span>
                      <span class="field-type">{{ sf.field_type }}</span>
                    </div>
                    <div v-if="sf.description" class="field-desc">
                      {{ sf.description }}
                    </div>
                  </div>
                  <div class="field-status">
                    <el-tag v-if="hasSourceMapping(sf.field_name)" size="small"
                      >已映射</el-tag
                    >
                  </div>
                </div>
              </div>
            </div>

            <!-- 中间：连线区域 -->
            <div ref="connectorRef" class="connector">
              <svg
                :width="connectorWidth"
                :height="connectorHeight"
                class="connection-svg"
              >
                <g v-for="ln in lines" :key="`${ln.source}-${ln.target}`">
                  <path
                    :d="ln.path"
                    stroke="#409EFF"
                    stroke-width="2"
                    fill="none"
                    class="connection-line"
                  />
                  <!-- 删除按钮 -->
                  <g
                    class="delete-btn-group"
                    style="cursor: pointer"
                    @click="removeMapping(ln.source)"
                  >
                    <circle
                      :cx="ln.mx"
                      :cy="ln.my"
                      r="8"
                      fill="#F56C6C"
                      stroke="#ffffff"
                      stroke-width="1"
                    />
                    <text
                      :x="ln.mx"
                      :y="ln.my + 1"
                      text-anchor="middle"
                      dominant-baseline="middle"
                      font-size="10"
                      fill="#ffffff"
                      font-weight="bold"
                      style="pointer-events: none"
                    >
                      ×
                    </text>
                  </g>
                </g>
              </svg>
            </div>

            <!-- 右侧：表字段 (目标) -->
            <div ref="targetListRef" class="target-list">
              <div class="list-header">
                <h3>表字段 (目标)</h3>
                <span class="count">{{ targetFields.length }}</span>
              </div>
              <div class="fields-scroll-container">
                <div
                  v-for="tf in targetFields"
                  :id="'target-field-' + tf.name"
                  :key="tf.name"
                  :ref="(el) => setTargetRef(tf.name, el as HTMLElement)"
                  :class="[
                    'field-item',
                    mappingLookup[tf.name]
                      ? 'mapped'
                      : selectedTarget === tf.name
                        ? 'active'
                        : '',
                  ]"
                  @click="handleTargetClick(tf.name)"
                >
                  <div class="field-content">
                    <div class="field-info">
                      <span class="field-name" :title="tf.name">
                        <span
                          v-html="highlightText(tf.name, targetSearch)"
                        ></span>
                      </span>
                      <span class="field-type">{{ tf.type || "-" }}</span>
                      <span v-if="!tf.nullable" class="required-badge"
                        >必填</span
                      >
                    </div>
                    <div v-if="tf.comment" class="field-desc">
                      {{ tf.comment }}
                    </div>
                  </div>
                  <div v-if="mappingLookup[tf.name]" class="field-map-info">
                    <el-icon><Link /></el-icon> {{ mappingLookup[tf.name] }}
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </template>

    <!-- 字段列表模式 -->
    <div v-else class="page-card">
      <div class="card-header">
        <h3>字段列表</h3>
        <div class="header-actions">
          <el-button size="small" :loading="saving" @click="saveFieldsOrder">
            <el-icon><Check /></el-icon>
            保存排序
          </el-button>
        </div>
      </div>

      <el-table
        v-loading="loading"
        :data="fields"
        style="width: 100%"
        row-key="id"
        @sort-change="handleSortChange"
      >
        <el-table-column label="排序" width="60">
          <template #default="{ $index }">
            <span class="drag-handle">{{ $index + 1 }}</span>
          </template>
        </el-table-column>
        <el-table-column
          prop="field_name"
          label="字段名称"
          width="150"
          sortable
        />
        <el-table-column prop="field_type" label="字段类型" width="120">
          <template #default="{ row }">
            <el-tag :type="getFieldTypeTagType(row.field_type)">
              {{ getFieldTypeLabel(row.field_type) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="is_required" label="是否必填" width="180">
          <template #default="{ row }">
            <el-switch
              v-model="row.is_required"
              active-text="必填"
              inactive-text="可选"
              @change="onRequiredChange(row, $event)"
            />
          </template>
        </el-table-column>
        <el-table-column
          prop="default_value"
          label="默认值"
          width="100"
          show-overflow-tooltip
        />
        <el-table-column
          prop="description"
          label="描述"
          min-width="200"
          show-overflow-tooltip
        />
        <el-table-column
          prop="validation_rules"
          label="验证规则"
          width="120"
          show-overflow-tooltip
        />
        <el-table-column prop="sort_order" label="排序" width="80" sortable />
        <el-table-column prop="created_at" label="创建时间" width="150">
          <template #default="{ row }">
            {{ formatDate(row.created_at) }}
          </template>
        </el-table-column>
        <!-- 是否上传勾选 -->
        <el-table-column
          prop="is_upload"
          label="是否上传"
          width="120"
          fixed="right"
        >
          <template #default="{ row }">
            <el-checkbox
              v-model="row.is_upload"
              :true-value="1"
              :false-value="0"
              @change="onUploadChange(row, $event)"
            ></el-checkbox>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <!-- 创建/编辑字段对话框 -->
    <el-dialog
      v-model="dialogVisible"
      :title="isEdit ? '编辑字段' : '添加字段'"
      width="600px"
      @close="resetForm"
    >
      <el-form
        ref="formRef"
        :model="form"
        :rules="formRules"
        label-width="120px"
      >
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="字段名称" prop="field_name">
              <el-input
                v-model="form.field_name"
                placeholder="请输入字段名称"
              />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="字段类型" prop="field_type">
              <el-select v-model="form.field_type" style="width: 100%">
                <el-option label="字符串" value="string" />
                <el-option label="整数" value="int" />
                <el-option label="浮点数" value="float" />
                <el-option label="布尔值" value="boolean" />
                <el-option label="日期" value="date" />
                <el-option label="日期时间" value="datetime" />
                <el-option label="文本" value="text" />
                <el-option label="邮箱" value="email" />
                <el-option label="URL" value="url" />
                <el-option label="JSON" value="json" />
                <el-option label="文件" value="file" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>

        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="是否必填" prop="is_required">
              <el-switch
                v-model="form.is_required"
                active-text="必填"
                inactive-text="可选"
              />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="排序" prop="sort_order">
              <el-input-number
                v-model="form.sort_order"
                :min="1"
                :max="999"
                style="width: 100%"
              />
            </el-form-item>
          </el-col>
        </el-row>

        <el-form-item label="默认值" prop="default_value">
          <el-input v-model="form.default_value" placeholder="请输入默认值" />
        </el-form-item>

        <el-form-item label="描述" prop="description">
          <el-input
            v-model="form.description"
            type="textarea"
            :rows="3"
            placeholder="请输入字段描述"
          />
        </el-form-item>

        <el-form-item label="验证规则" prop="validation_rules">
          <el-input
            v-model="form.validation_rules"
            type="textarea"
            :rows="2"
            placeholder="请输入验证规则（JSON格式）"
          />
        </el-form-item>
      </el-form>

      <template #footer>
        <div class="dialog-footer">
          <el-button @click="dialogVisible = false">取消</el-button>
          <el-button type="primary" :loading="submitting" @click="submitForm">
            {{ isEdit ? "更新" : "创建" }}
          </el-button>
        </div>
      </template>
    </el-dialog>

    <!-- 资源类型字段选择抽屉 -->
    <el-drawer
      v-model="centerDrawerVisible"
      title="从资源类型选择字段"
      direction="rtl"
      size="800px"
    >
      <div class="panel-header">
        <h4>资源类型字段</h4>
        <el-button
          :loading="centerFieldsLoading"
          size="small"
          @click="loadResourceTypeFields"
        >
          <el-icon><Refresh /></el-icon>
          刷新字段
        </el-button>
      </div>
      <div class="center-fields-list">
        <el-table
          v-loading="centerFieldsLoading"
          :data="centerTableFields"
          size="small"
          @selection-change="handleCenterFieldSelection"
        >
          <el-table-column
            type="selection"
            width="55"
            :selectable="selectableCenterField"
          />
          <el-table-column prop="column_name" label="字段名" width="150" />
          <el-table-column prop="data_type" label="数据类型" width="120" />
          <el-table-column
            prop="column_comment"
            label="字段说明"
            show-overflow-tooltip
          >
            <template #default="{ row }">
              {{ row.column_comment || "-" }}
            </template>
          </el-table-column>
          <el-table-column label="状态" width="100">
            <template #default="{ row }">
              <el-tag
                :type="isExistingCenterField(row) ? 'info' : 'success'"
                size="small"
              >
                {{ isExistingCenterField(row) ? "已存在" : "可添加" }}
              </el-tag>
            </template>
          </el-table-column>
        </el-table>
      </div>
      <template #footer>
        <el-button @click="centerDrawerVisible = false">取消</el-button>
        <el-button
          type="primary"
          :disabled="selectedCenterFields.length === 0"
          :loading="addingFromCenter"
          @click="addSelectedFields"
        >
          添加选中字段 ({{ selectedCenterFields.length }})
        </el-button>
      </template>
    </el-drawer>

    <!-- 预览映射对话框 -->
    <el-dialog v-model="previewVisible" title="映射预览" width="600px">
      <el-table :data="mappingPairs" style="width: 100%">
        <el-table-column prop="source" label="源字段 (API)" />
        <el-table-column prop="target" label="目标字段 (Table)" />
        <el-table-column label="操作" width="120">
          <template #default="{ row }">
            <el-button
              type="danger"
              size="small"
              @click="removeMapping(row.source)"
              >删除</el-button
            >
          </template>
        </el-table-column>
      </el-table>
      <template #footer>
        <el-button @click="previewVisible = false">关闭</el-button>
        <el-button type="success" @click="saveMapping">保存映射</el-button>
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
          <el-input
            v-model="sourceFieldForm.name"
            placeholder="请输入字段名称"
          />
        </el-form-item>

        <el-form-item label="字段类型" required>
          <el-select
            v-model="sourceFieldForm.type"
            placeholder="请选择字段类型"
          >
            <el-option
              v-for="typeOption in fieldTypeOptions"
              :key="typeOption"
              :label="typeOption"
              :value="typeOption"
            />
          </el-select>
        </el-form-item>

        <el-form-item label="生成类型" required>
          <el-select
            v-model="sourceFieldForm.generateType"
            placeholder="请选择生成类型"
          >
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
        <el-form-item
          v-if="sourceFieldForm.generateType === 'external_param'"
          label="参数名"
          required
        >
          <el-input
            v-model="sourceFieldForm.parameterName"
            placeholder="请输入参数名"
          />
        </el-form-item>

        <!-- 常量值配置 -->
        <el-form-item
          v-if="sourceFieldForm.generateType === 'constant'"
          label="常量值"
          required
        >
          <el-input
            v-model="sourceFieldForm.constantValue"
            placeholder="请输入常量值"
          />
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
            <el-input
              v-model="sourceFieldForm.separator"
              placeholder="请输入分隔符（可选）"
            />
          </el-form-item>
        </template>

        <!-- 条件判断配置 -->
        <template v-if="sourceFieldForm.generateType === 'condition'">
          <el-form-item label="判断字段" required>
            <el-select
              v-model="sourceFieldForm.conditionField"
              placeholder="请选择判断字段"
            >
              <el-option
                v-for="field in availableOriginalFields"
                :key="getFieldName(field)"
                :label="getFieldName(field)"
                :value="getFieldName(field)"
              />
            </el-select>
          </el-form-item>
          <el-form-item label="操作符" required>
            <el-select
              v-model="sourceFieldForm.conditionOperator"
              placeholder="请选择操作符"
            >
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
            <el-input
              v-model="sourceFieldForm.conditionValue"
              placeholder="请输入比较值"
            />
          </el-form-item>
          <el-form-item label="真值" required>
            <el-input
              v-model="sourceFieldForm.trueValue"
              placeholder="条件为真时的值"
            />
          </el-form-item>
          <el-form-item label="假值" required>
            <el-input
              v-model="sourceFieldForm.falseValue"
              placeholder="条件为假时的值"
            />
          </el-form-item>
        </template>

        <!-- 多条件判断配置 -->
        <template v-if="sourceFieldForm.generateType === 'case_when'">
          <el-form-item label="判断字段" required>
            <el-select
              v-model="sourceFieldForm.caseWhenField"
              placeholder="请选择判断字段"
            >
              <el-option
                v-for="field in availableOriginalFields"
                :key="getFieldName(field)"
                :label="getFieldName(field)"
                :value="getFieldName(field)"
              />
            </el-select>
          </el-form-item>
          <el-form-item label="条件分支">
            <div
              v-for="(branch, index) in sourceFieldForm.caseBranches"
              :key="index"
              class="case-branch"
              style="margin-bottom: 10px"
            >
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
                  <el-button
                    type="danger"
                    size="small"
                    @click="removeCaseBranch(index)"
                  >
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
            <el-input
              v-model="sourceFieldForm.defaultValue"
              placeholder="所有条件都不满足时的默认值"
            />
          </el-form-item>
        </template>

        <!-- 数学运算配置 -->
        <el-form-item
          v-if="sourceFieldForm.generateType === 'math'"
          label="数学表达式"
          required
        >
          <el-input
            v-model="sourceFieldForm.mathExpression"
            type="textarea"
            placeholder="请输入数学表达式，如：field1 + field2 * 100"
          />
        </el-form-item>

        <!-- 日期函数配置 -->
        <template v-if="sourceFieldForm.generateType === 'date'">
          <el-form-item label="日期函数" required>
            <el-select
              v-model="sourceFieldForm.dateFunction"
              placeholder="请选择日期函数"
            >
              <el-option label="当前时间" value="NOW()" />
              <el-option label="当前日期" value="CURDATE()" />
              <el-option label="当前时间戳" value="UNIX_TIMESTAMP()" />
            </el-select>
          </el-form-item>
          <el-form-item label="日期格式">
            <el-input
              v-model="sourceFieldForm.dateFormat"
              placeholder="日期格式，如：%Y-%m-%d %H:%i:%s"
            />
          </el-form-item>
          <el-form-item label="时间间隔">
            <el-input
              v-model="sourceFieldForm.dateInterval"
              placeholder="时间间隔，如：1 DAY, -1 MONTH"
            />
          </el-form-item>
        </template>

        <!-- 预览 -->
        <el-form-item label="表达式预览">
          <el-input
            :value="generateExpression()"
            readonly
            type="textarea"
            rows="2"
          />
        </el-form-item>

        <el-form-item label="样本结果">
          <el-input :value="generateSampleResult()" readonly />
        </el-form-item>
      </el-form>

      <template #footer>
        <span class="dialog-footer">
          <el-button @click="showSourceFieldDialog = false">取消</el-button>
          <el-button
            type="primary"
            :disabled="!isSourceFieldFormValid"
            @click="saveSourceField"
          >
            {{ editingSourceField !== null ? "更新" : "添加" }}
          </el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, computed, nextTick } from "vue";
import { useRoute, useRouter } from "vue-router";
import { ElMessage, ElMessageBox } from "element-plus";
import type { FormInstance, FormRules } from "element-plus";
import { formatDate } from "@/utils/date";
import {
  getApi,
  getApiFields,
  createApiField,
  updateApiField,
  deleteApiField,
  updateApi,
} from "@/api/apiManagement";
import type {
  CustomApi,
  ApiField,
  ApiFieldCreate,
  ApiFieldUpdate,
} from "@/types/apiManagement";
import { getResourceType } from "@/api/resourceType";
import { datasourceApi } from "@/api/datasource";
import { templateApi } from "@/api/template";

/**
 * 路由
 */
const route = useRoute();
const router = useRouter();

/**
 * 响应式数据
 */
const loading = ref(false);
const saving = ref(false);
const apiInfo = ref<CustomApi | null>(null);
const resourceTypeName = ref("");
const fields = ref<ApiField[]>([]);
const dialogVisible = ref(false);
const isEdit = ref(false);
const submitting = ref(false);
const formRef = ref<FormInstance>();

// 表单数据
const form = reactive<ApiFieldCreate & { id?: number }>({
  field_name: "",
  field_type: "string",
  is_required: false,
  default_value: "",
  description: "",
  validation_rules: "",
  sort_order: 1,
});

// 表单验证规则
const formRules: FormRules = {
  field_name: [
    { required: true, message: "请输入字段名称", trigger: "blur" },
    { min: 1, max: 50, message: "长度在 1 到 50 个字符", trigger: "blur" },
    {
      pattern: /^[a-zA-Z][a-zA-Z0-9_]*$/,
      message: "必须以字母开头，只能包含字母、数字和下划线",
      trigger: "blur",
    },
  ],
  field_type: [
    { required: true, message: "请选择字段类型", trigger: "change" },
  ],
  sort_order: [{ required: true, message: "请输入排序", trigger: "blur" }],
};

// 新增：中心表字段选择相关
interface CenterTableField {
  column_name: string;
  data_type: string;
  column_comment: string;
  is_nullable: boolean;
}

const centerDrawerVisible = ref(false);
const centerTableFields = ref<CenterTableField[]>([]);
const selectedCenterFields = ref<CenterTableField[]>([]);
const centerFieldsLoading = ref(false);
const addingFromCenter = ref(false);
const isMappingMode = ref(false);
// const currentStep = ref(0) // Removed steps
const datasources = ref<any[]>([]);
const selectedDatasourceId = ref<number | null>(null);
const schemas = ref<Array<{ name: string }>>([]);
const selectedSchema = ref<string | null>(null);
const tables = ref<Array<{ name: string; type: string }>>([]);
const selectedTable = ref<string | null>(null);
const tableFields = ref<
  Array<{ name: string; type?: string; nullable?: boolean; comment?: string }>
>([]);
const previewVisible = ref(false);
const selectedSource = ref<string | null>(null);
const selectedTarget = ref<string | null>(null);
const mappings = ref<Record<string, string>>({});

// 自定义字段状态
const showSourceFieldDialog = ref(false);
const editingSourceField = ref<number | null>(null);
const fieldTypeOptions = [
  "VARCHAR",
  "INT",
  "BIGINT",
  "DECIMAL",
  "DATE",
  "DATETIME",
  "TEXT",
  "BOOLEAN",
];

const sourceFieldForm = reactive({
  name: "",
  type: "VARCHAR",
  generateType: "external_param",
  parameterName: "",
  constantValue: "",
  concatFields: [] as string[],
  separator: "",
  conditionField: "",
  conditionOperator: "=",
  conditionValue: "",
  trueValue: "",
  falseValue: "",
  caseWhenField: "",
  caseBranches: [] as any[],
  defaultValue: "",
  mathExpression: "",
  dateFunction: "NOW()",
  dateFormat: "%Y-%m-%d %H:%i:%s",
  dateInterval: "",
});

const needsConditionValue = computed(() => {
  return (
    sourceFieldForm.conditionOperator &&
    !["IS NULL", "IS NOT NULL"].includes(sourceFieldForm.conditionOperator)
  );
});

const isSourceFieldFormValid = computed(() => {
  if (
    !sourceFieldForm.name ||
    !sourceFieldForm.type ||
    !sourceFieldForm.generateType
  ) {
    return false;
  }

  switch (sourceFieldForm.generateType) {
    case "constant":
      return !!sourceFieldForm.constantValue;
    case "snowflake":
    case "uuid":
      return true;
    case "concat":
      return sourceFieldForm.concatFields.length > 0;
    case "condition":
      return (
        sourceFieldForm.conditionField &&
        sourceFieldForm.conditionOperator &&
        (!needsConditionValue.value || sourceFieldForm.conditionValue) &&
        sourceFieldForm.trueValue !== "" &&
        sourceFieldForm.falseValue !== ""
      );
    case "case_when":
      return (
        sourceFieldForm.caseWhenField &&
        sourceFieldForm.caseBranches.length > 0 &&
        sourceFieldForm.defaultValue !== ""
      );
    case "math":
      return !!sourceFieldForm.mathExpression;
    case "date":
      return !!sourceFieldForm.dateFunction;
    case "external_param":
      return !!sourceFieldForm.parameterName;
    default:
      return true;
  }
});

const availableOriginalFields = computed(() => {
  // Use all source fields (excluding current one if editing could be nice, but not strictly necessary for MVP)
  // Filtering out the field itself to prevent self-reference in complex logic
  return sourceFields.value.filter(
    (f) => f.field_name !== sourceFieldForm.name,
  );
});

const sourceFieldRefs = ref<Record<string, HTMLElement | null>>({});
const targetFieldRefs = ref<Record<string, HTMLElement | null>>({});
const connectorRef = ref<HTMLElement | null>(null);
const sourceListRef = ref<HTMLElement | null>(null);
const targetListRef = ref<HTMLElement | null>(null);
const connectorWidth = ref(150); // Increased width for better curve
const connectorHeight = ref(600);
const lines = ref<
  Array<{
    source: string;
    target: string;
    path: string;
    mx: number;
    my: number;
  }>
>([]);
const originalFieldMappings = ref<any[]>([]);
const customFields = ref<any[]>([]);
const sortedMappedSourceNames = ref<string[]>([]);

const sourceFields = computed(() => {
  // 分离映射过的和未映射的字段
  const mapped = [] as any[];
  const unmapped = [] as any[];

  // 基础字段 + 自定义字段
  const allFields = [
    ...fields.value.filter((f) => Number(f.is_upload) === 1),
    ...customFields.value,
  ];

  // 按照映射关系的顺序进行排序
  // 1. 已经建立映射的字段，按照在mappings中出现的顺序（或者一个固定的逻辑顺序）
  // 2. 未建立映射的字段

  // 我们需要一个稳定的排序，这里我们可以根据 mappingPairs 的顺序来排
  // 但 mappingPairs 是基于 mappings 对象的，顺序不一定保证
  // 更好的方式是：
  // 遍历所有已存在的映射关系（mappings），找到对应的源字段，按顺序加入 mapped 数组
  // 然后遍历所有字段，如果没在 mapped 中，加入 unmapped 数组

  // 找出所有已映射的源字段名 (使用 sortedMappedSourceNames 而不是实时 mappings)
  const mappedSourceNames = sortedMappedSourceNames.value;

  // 按映射顺序添加源字段
  mappedSourceNames.forEach((name) => {
    const field = allFields.find((f) => f.field_name === name);
    if (field) {
      mapped.push(field);
    }
  });

  // 添加剩余未映射的字段
  allFields.forEach((f) => {
    if (!mappedSourceNames.includes(f.field_name)) {
      unmapped.push(f);
    }
  });

  return [...mapped, ...unmapped];
});

const targetFields = computed(() => {
  const mapped = [] as any[];
  const unmapped = [] as any[];

  // 这里的关键是：目标字段的排序必须与源字段的排序一致
  // 即：如果 sourceFields[0] 映射到了 targetA，那么 targetFields[0] 必须是 targetA

  // 1. 根据 sourceFields 的顺序，找到对应的目标字段
  sourceFields.value.forEach((sf) => {
    // 只有当源字段在"已排序映射列表"中时，才将其目标字段放入 mapped 组
    if (sortedMappedSourceNames.value.includes(sf.field_name)) {
      const targetName = mappings.value[sf.field_name];
      if (targetName) {
        const targetField = tableFields.value.find(
          (tf) => tf.name === targetName,
        );
        if (targetField) {
          mapped.push(targetField);
        }
      }
    }
  });

  // 2. 找出未被映射的目标字段
  const mappedTargetNames = mapped.map((f) => f.name);
  tableFields.value.forEach((f) => {
    if (!mappedTargetNames.includes(f.name)) {
      unmapped.push(f);
    }
  });

  return [...mapped, ...unmapped];
});

const mappingPairs = computed(() =>
  Object.entries(mappings.value)
    .filter(([s, t]) => !!t)
    .map(([source, target]) => ({ source, target })),
);
const mappingLookup = computed<Record<string, string>>(() => {
  const rev: Record<string, string> = {};
  for (const [s, t] of Object.entries(mappings.value)) {
    if (t) rev[t] = s;
  }
  return rev;
});

const canSave = computed(
  () =>
    mappingPairs.value.length > 0 &&
    !!selectedDatasourceId.value &&
    !!selectedTable.value,
);

// 资源类型字段选择依赖于当前 API 的 resource_type_id

/**
 * 生命周期钩子
 */
onMounted(async () => {
  const apiId = route.params.id as string;
  let apiInfoPromise = Promise.resolve();

  if (apiId) {
    apiInfoPromise = loadApiInfo(parseInt(apiId));
    loadFields(parseInt(apiId));
  }
  isMappingMode.value = String(route.query.mode || "") === "mapping";
  if (isMappingMode.value) {
    await loadDatasources();

    // 等待 API 信息加载完成
    await apiInfoPromise;

    // 如果有 templateId，加载模板配置
    let tid = route.query.templateId as string;

    // 如果 URL 中没有 templateId，但 API 信息中有 mapping_config_id，则使用它
    if (!tid && apiInfo.value?.mapping_config_id) {
      tid = String(apiInfo.value.mapping_config_id);
      console.log("Using mapping_config_id from API info:", tid);
      router.replace({
        query: { ...route.query, templateId: tid },
      });
    }

    if (tid) {
      await loadTemplateConfig(tid);
    } else {
      restoreMapping();
    }

    await nextTick();
    refreshLines();
    window.addEventListener("resize", refreshLines);
  }
});

const loadTemplateConfig = async (tid: string) => {
  try {
    const res = await templateApi.get(Number(tid) || (tid as any));
    if (res.success && res.data) {
      const t = res.data;
      const config = t.execution_config || {};

      // 恢复数据源
      if (config.datasource_id) {
        selectedDatasourceId.value = config.datasource_id;
        await loadSchemas();
      }
      // 恢复Schema
      if (config.schema) {
        selectedSchema.value = config.schema;
        await loadTables();
      }
      // 恢复表
      if (t.target_table) {
        selectedTable.value = t.target_table;
        await loadTableFields();
      }
      // 恢复映射
      if (t.field_mappings) {
        if (Array.isArray(t.field_mappings)) {
          originalFieldMappings.value = t.field_mappings;
          // 转换为简单的 KV 映射供 UI 显示
          const simpleMappings: Record<string, string> = {};
          const restoredCustomFields: any[] = [];

          t.field_mappings.forEach((m: any) => {
            if (m.sourceName && m.targetName) {
              simpleMappings[m.sourceName] = m.targetName;
            }
            // 恢复自定义字段
            // 兼容逻辑：如果有 isCustom 标记，或者 generateType 不是 normal，或者有 expression 且不为空
            const isCustomField =
              m.isCustom ||
              (m.generateType && m.generateType !== "normal") ||
              (m.expression && m.expression.trim() !== "");

            if (isCustomField) {
              restoredCustomFields.push({
                field_name: m.sourceName,
                field_type: m.sourceType,
                description: `自定义字段: ${m.expression || ""}`,
                is_custom: true,
                is_upload: 1,

                // Restore all complex properties
                expression: m.expression,
                generateType: m.generateType || "constant", // fallback
                parameterName: m.parameterName,
                constantValue: m.constantValue,
                concatFields: m.concatFields || [],
                separator: m.separator,
                conditionField: m.conditionField,
                conditionOperator: m.conditionOperator,
                conditionValue: m.conditionValue,
                trueValue: m.trueValue,
                falseValue: m.falseValue,
                caseBranches: m.caseBranches || [],
                defaultValue: m.defaultValue,
                mathExpression: m.mathExpression,
                dateFunction: m.dateFunction,
                dateFormat: m.dateFormat,
                dateInterval: m.dateInterval,
              });
            }
          });

          mappings.value = simpleMappings;
          customFields.value = restoredCustomFields;
          sortedMappedSourceNames.value = Object.keys(simpleMappings);
        } else {
          mappings.value = t.field_mappings;
          sortedMappedSourceNames.value = Object.keys(t.field_mappings || {});
          originalFieldMappings.value = [];
        }
      }
    }
  } catch (e) {
    console.error("加载模板配置失败", e);
  }
};

/**
 * 方法定义
 */

/**
 * 加载API信息
 */
const loadApiInfo = async (apiId: number) => {
  try {
    const response = await getApi(apiId);
    if (response.success) {
      apiInfo.value = response.data;
      // 加载资源类型名称
      try {
        const rid = apiInfo.value?.resource_type_id;
        if (rid) {
          const rtResp = await getResourceType(String(rid));
          if (rtResp?.success && rtResp.data) {
            resourceTypeName.value = rtResp.data.name || "";
          } else {
            resourceTypeName.value = "";
          }
        } else {
          resourceTypeName.value = "";
        }
      } catch (e) {
        resourceTypeName.value = "";
      }
    } else {
      ElMessage.error(response.message || "加载API信息失败");
    }
  } catch (error) {
    console.error("加载API信息失败:", error);
    ElMessage.error("加载API信息失败");
  }
};

/**
 * 加载字段列表
 */
const loadFields = async (apiId?: number) => {
  const id =
    typeof apiId === "number" ? apiId : parseInt(route.params.id as string);

  try {
    loading.value = true;
    const response = await getApiFields(id);

    if (response.success) {
      // 处理分页响应结构，获取items数组
      const items = response.data.items || response.data || [];
      // 归一化 is_upload 类型，确保为数字 0/1，避免 '1'/'0' 导致复选框不勾选
      const normalized = items.map((item: any) => ({
        ...item,
        field_type:
          typeof item.field_type === "string" &&
          item.field_type.toLowerCase() === "integer"
            ? "int"
            : item.field_type,
        is_upload:
          item?.is_upload === undefined || item?.is_upload === null
            ? 0
            : typeof item.is_upload === "string"
              ? Number(item.is_upload)
              : item.is_upload,
      }));
      // 根据后端返回的 sort_order 排序
      const sortedFields = normalized.sort((a, b) => {
        const orderA = a.sort_order || 0;
        const orderB = b.sort_order || 0;
        return orderA - orderB;
      });
      fields.value = sortedFields;

      if (isMappingMode.value) {
        nextTick(() => refreshLines());
      }
    } else {
      ElMessage.error(response.message || "加载字段列表失败");
    }
  } catch (error) {
    console.error("加载字段列表失败:", error);
    ElMessage.error("加载字段列表失败");
  } finally {
    loading.value = false;
  }
};

/**
 * 获取请求方法标签类型
 */
const getMethodTagType = (method: string) => {
  const types: Record<string, string> = {
    GET: "success",
    POST: "primary",
    PUT: "warning",
    DELETE: "danger",
  };
  return types[method] || "info";
};

/**
 * 获取字段类型标签类型
 */
const getFieldTypeTagType = (type: string) => {
  const types: Record<string, string> = {
    string: "primary",
    number: "success",
    boolean: "warning",
    date: "info",
    array: "danger",
    object: "",
  };
  return types[type] || "info";
};

const handleDatasourceChange = async (val: number) => {
  selectedDatasourceId.value = val;
  schemas.value = [];
  selectedSchema.value = null;
  tables.value = [];
  selectedTable.value = null;
  tableFields.value = [];
  await loadSchemas();
};

const handleSchemaChange = async (val: string) => {
  selectedSchema.value = val;
  tables.value = [];
  selectedTable.value = null;
  tableFields.value = [];
  await loadTables();
};

const handleTableChange = async (val: string) => {
  selectedTable.value = val;
  if (!val) return;
  await loadTableFields();
};

const loadDatasources = async () => {
  try {
    const resp = await datasourceApi.getDataSourceList({ page_size: 1000 });
    datasources.value = resp.data?.items || [];
  } catch (e) {
    datasources.value = [];
  }
};

const loadSchemas = async () => {
  if (!selectedDatasourceId.value) return;
  try {
    const resp = await datasourceApi.getDataSourceSchemas(
      selectedDatasourceId.value,
    );
    schemas.value = resp.data || [];
  } catch (e) {
    schemas.value = [];
  }
};

const loadTables = async () => {
  if (!selectedDatasourceId.value) return;
  try {
    if (selectedSchema.value) {
      const resp = await datasourceApi.getDataSourceTablesWithSchema(
        selectedDatasourceId.value,
        selectedSchema.value,
      );
      tables.value = resp.data || [];
    } else {
      const resp = await datasourceApi.getDataSourceTables(
        selectedDatasourceId.value,
      );
      tables.value = resp.data || [];
    }
  } catch (e) {
    tables.value = [];
  }
};

const loadTableFields = async () => {
  if (!selectedDatasourceId.value || !selectedTable.value) return;
  try {
    const resp = await datasourceApi.getDataSourceTableFields(
      selectedDatasourceId.value,
      selectedSchema.value || "",
      selectedTable.value,
    );
    tableFields.value = resp.data || [];
    await nextTick();
    refreshLines();
  } catch (e) {
    tableFields.value = [];
  }
};

const clearMapping = () => {
  mappings.value = {};
  refreshLines();
};

const autoMapping = () => {
  if (sourceFields.value.length === 0 || targetFields.value.length === 0)
    return;
  const norm = (s: string) => s.toLowerCase().replace(/[^a-z0-9]/g, "");
  const targetIndex = new Map<string, string>();
  targetFields.value.forEach((tf) => targetIndex.set(norm(tf.name), tf.name));
  const tmp: Record<string, string> = {};
  sourceFields.value.forEach((sf) => {
    const k = norm(sf.field_name);
    const hit = targetIndex.get(k);
    if (hit) tmp[sf.field_name] = hit;
  });
  mappings.value = tmp;
  refreshLines();
};

const saveMapping = async () => {
  const apiId = parseInt(route.params.id as string);
  // 优先从 URL 参数获取 templateId
  let templateId = route.query.templateId as string;

  // 构造模板数据
  const executionConfig = {
    datasource_id: selectedDatasourceId.value,
    schema: selectedSchema.value || "",
    batchSize: 1000, // 默认批量大小
  };

  // 构建复杂的 field_mappings 数组
  const complexMappings: any[] = [];
  // 查找选中的数据源信息
  const selectedDs = datasources.value.find(
    (d) => d.id === selectedDatasourceId.value,
  );

  for (const [source, target] of Object.entries(mappings.value)) {
    if (!target) continue;

    // 尝试从原始配置中查找现有配置
    const existing = originalFieldMappings.value.find(
      (m: any) => m.sourceName === source && m.targetName === target,
    );

    // 获取最新的源字段和目标字段信息
    const sField = sourceFields.value.find((f) => f.field_name === source);
    const tField = targetFields.value.find((f) => f.name === target);

    // 构建最新的映射对象
    let currentMapping: any = {
      sourceName: source,
      targetName: target,
      sourceType: sField?.field_type || "string",
      targetType: tField?.type || "VARCHAR",
      sourceIndex: sourceFields.value.findIndex((f) => f.field_name === source),
      targetIndex: targetFields.value.findIndex((f) => f.name === target),
    };

    // 只有自定义字段才包含额外属性
    if (sField?.is_custom) {
      currentMapping = {
        ...currentMapping,
        isCustom: true,
        generateType: sField?.generateType || "normal",
        expression: sField?.expression || "",
        sample: sField?.sample || "",

        // Complex properties for custom fields
        parameterName: sField?.parameterName,
        constantValue: sField?.constantValue,
        concatFields: sField?.concatFields,
        separator: sField?.separator,
        conditionField: sField?.conditionField,
        conditionOperator: sField?.conditionOperator,
        conditionValue: sField?.conditionValue,
        trueValue: sField?.trueValue,
        falseValue: sField?.falseValue,
        caseBranches: sField?.caseBranches,
        defaultValue: sField?.defaultValue,
        mathExpression: sField?.mathExpression,
        dateFunction: sField?.dateFunction,
        dateFormat: sField?.dateFormat,
        dateInterval: sField?.dateInterval,
      };
    }

    if (existing) {
      // 合并现有配置和最新配置，确保自定义字段属性被更新
      // 关键修正：如果是普通字段，我们必须强制覆盖 existing 中的旧属性，
      // 因为 existing 可能包含以前保存的冗余字段（如 isCustom: false, generateType: normal 等）
      // 如果我们只是 ...existing, ...currentMapping，而 currentMapping 中没有这些 key（为了精简），
      // 那么 existing 中的旧 key 依然会保留下来。

      if (!sField?.is_custom) {
        // 对于普通字段，我们只保留核心字段，完全丢弃 existing 中的其他垃圾属性
        // 但我们需要保留 existing 中的一些可能不在 currentMapping 中的有用属性吗？
        // 根据需求，普通字段只需要那 6 个属性。
        // 所以直接使用 currentMapping 即可，不需要合并 existing 的垃圾。
        complexMappings.push(currentMapping);
      } else {
        // 对于自定义字段，可能需要保留一些状态，或者直接覆盖
        // 为了安全起见，自定义字段还是合并一下，但 currentMapping 已经包含了所有必要信息
        complexMappings.push({
          ...existing,
          ...currentMapping,
        });
      }
    } else {
      complexMappings.push(currentMapping);
    }
  }

  // 提取自定义字段到单独的 custom_fields 数组
  const customFieldsToSave = complexMappings
    .filter((m) => m.isCustom)
    .map((m) => ({
      field_name: m.sourceName,
      field_type: m.sourceType,
      description: m.expression || "自定义字段",
      expression: m.expression,
      generateType: m.generateType,
      // Copy other custom properties if needed
      ...m,
    }));

  const targetDbConfig = { datasource_id: selectedDatasourceId.value };

  const templateData: any = {
    name: apiInfo.value
      ? `API映射-${apiInfo.value.api_name}`
      : `API映射-${apiId}`,
    description: "自动生成的API字段映射配置",
    batch_id:
      (apiInfo.value as any)?.link_read_id ||
      (apiInfo.value as any)?.resource_type_id ||
      `API-${apiId}`,
    api_code: (apiInfo.value as any)?.api_code,
    api_id: apiId,
    request_id: null,
    customer_id: (apiInfo.value as any)?.customer_id,
    target_table: selectedTable.value,
    field_mappings: complexMappings, // 发送复杂数组结构
    custom_fields: customFieldsToSave, // 保存一份到 custom_fields
    target_database: targetDbConfig,
    executionConfig: executionConfig,

    // 设置 file_type 为 minio
    file_type: "minio",
    // 设置 sheet_name 为 data.data_list
    sheet_name: "data.data_list",

    import_mode: "insert", // 默认模式
    is_active: true,
  };

  try {
    saving.value = true;
    let resp;

    if (templateId) {
      // 更新现有模板
      resp = await templateApi.update(
        Number(templateId) || (templateId as any),
        templateData,
      );
    } else {
      // 创建新模板
      resp = await templateApi.create(templateData);
    }

    if (resp.success) {
      const data = resp.data;
      const newTemplateId = data.id;

      // 更新 mapping_config_id 到 CustomApi
      if (newTemplateId) {
        try {
          console.log("Updating API with mapping_config_id:", newTemplateId);
          // 移除 Number() 转换，因为 newTemplateId 可能是 UUID 字符串
          const updateResult = await updateApi(apiId, {
            mapping_config_id: newTemplateId,
          });
          console.log("API update result:", updateResult);
        } catch (err) {
          console.error("更新API mapping_config_id失败:", err);
        }
      }

      // 更新 URL，加上 templateId
      if (!templateId && newTemplateId) {
        router.replace({
          query: { ...route.query, templateId: newTemplateId },
        });
        templateId = newTemplateId;
      }

      // 保存到本地存储作为备份（可选）
      const key = `api_field_mapping:${apiId}:${selectedDatasourceId.value || ""}:${selectedSchema.value || ""}:${selectedTable.value || ""}`;
      localStorage.setItem(
        key,
        JSON.stringify({
          template_id: newTemplateId,
          ...executionConfig,
          mappings: mappings.value,
        }),
      );

      // 保存成功后，更新已排序的映射列表，使映射字段移动到前面
      sortedMappedSourceNames.value = Object.keys(mappings.value).filter(
        (k) => !!mappings.value[k],
      );
      await nextTick();
      refreshLines();

      ElMessage.success(templateId ? "映射配置更新成功" : "映射配置创建成功");
    } else {
      ElMessage.error(resp.message || "保存失败");
    }
  } catch (e: any) {
    console.error("保存映射失败:", e);
    ElMessage.error(e?.message || "保存映射失败");
  } finally {
    saving.value = false;
  }
};

const restoreMapping = () => {
  const prefix = `api_field_mapping:${route.params.id}:`;
  for (let i = 0; i < localStorage.length; i++) {
    const k = localStorage.key(i) || "";
    if (k.startsWith(prefix)) {
      try {
        const parsed = JSON.parse(localStorage.getItem(k) || "{}");
        if (parsed && parsed.mappings) {
          mappings.value = parsed.mappings;
          sortedMappedSourceNames.value = Object.keys(parsed.mappings);
          break;
        }
      } catch {}
    }
  }
};

const setSourceRef = (name: string, el: HTMLElement | null) => {
  sourceFieldRefs.value[name] = el;
};
const setTargetRef = (name: string, el: HTMLElement | null) => {
  targetFieldRefs.value[name] = el;
};

const addSourceField = () => {
  editingSourceField.value = null;
  sourceFieldForm.name = "";
  sourceFieldForm.type = "VARCHAR";
  sourceFieldForm.generateType = "external_param";
  sourceFieldForm.parameterName = "";
  sourceFieldForm.constantValue = "";
  sourceFieldForm.concatFields = [];
  sourceFieldForm.separator = "";
  sourceFieldForm.conditionField = "";
  sourceFieldForm.conditionOperator = "=";
  sourceFieldForm.conditionValue = "";
  sourceFieldForm.trueValue = "";
  sourceFieldForm.falseValue = "";
  sourceFieldForm.caseWhenField = "";
  sourceFieldForm.caseBranches = [];
  sourceFieldForm.defaultValue = "";
  sourceFieldForm.mathExpression = "";
  sourceFieldForm.dateFunction = "NOW()";
  sourceFieldForm.dateFormat = "%Y-%m-%d %H:%i:%s";
  sourceFieldForm.dateInterval = "";

  showSourceFieldDialog.value = true;
};

const addCaseBranch = () => {
  sourceFieldForm.caseBranches.push({
    operator: "=",
    condition: "",
    value: "",
  });
};

const removeCaseBranch = (index: number) => {
  sourceFieldForm.caseBranches.splice(index, 1);
};

const getFieldName = (field: any) => field.field_name || field.name || "";

const generateExpression = () => {
  switch (sourceFieldForm.generateType) {
    case "constant":
      return `'${sourceFieldForm.constantValue}'`;
    case "uuid":
      return "UUID()";
    case "snowflake":
      return "snowid()";
    case "concat": {
      const fields = sourceFieldForm.concatFields
        .map((field) => `COALESCE(${field}, '')`)
        .join(", ");
      const separator = sourceFieldForm.separator
        ? `'${sourceFieldForm.separator}'`
        : "''";
      return `CONCAT(${fields.split(", ").join(`, ${separator}, `)})`;
    }
    case "condition": {
      const condition =
        sourceFieldForm.conditionOperator === "IS NULL" ||
        sourceFieldForm.conditionOperator === "IS NOT NULL"
          ? `${sourceFieldForm.conditionField} ${sourceFieldForm.conditionOperator}`
          : `${sourceFieldForm.conditionField} ${sourceFieldForm.conditionOperator} '${sourceFieldForm.conditionValue}'`;
      return `IF(${condition}, '${sourceFieldForm.trueValue}', '${sourceFieldForm.falseValue}')`;
    }
    case "case_when": {
      let expression = "CASE";
      sourceFieldForm.caseBranches.forEach((branch) => {
        const condition = ["IS NULL", "IS NOT NULL"].includes(branch.operator)
          ? `${sourceFieldForm.caseWhenField} ${branch.operator}`
          : `${sourceFieldForm.caseWhenField} ${branch.operator} '${branch.condition}'`;
        expression += ` WHEN ${condition} THEN '${branch.value}'`;
      });
      expression += ` ELSE '${sourceFieldForm.defaultValue}' END`;
      return expression;
    }
    case "math":
      return sourceFieldForm.mathExpression;
    case "date": {
      let expr = sourceFieldForm.dateFunction;
      if (sourceFieldForm.dateInterval) {
        expr = `DATE_ADD(${expr}, INTERVAL ${sourceFieldForm.dateInterval})`;
      }
      if (sourceFieldForm.dateFormat) {
        expr = `DATE_FORMAT(${expr}, '${sourceFieldForm.dateFormat}')`;
      }
      return expr;
    }
    case "external_param":
      // 只有当parameterName不为空时才生成表达式
      return sourceFieldForm.parameterName
        ? `\${${sourceFieldForm.parameterName}}`
        : "";
    default:
      return "";
  }
};

const generateSampleResult = () => {
  // Simple mock implementation
  return "预览结果";
};

const saveSourceField = () => {
  if (!isSourceFieldFormValid.value) {
    ElMessage.warning("请填写完整信息");
    return;
  }

  // Check duplicates
  const exists = sourceFields.value.find(
    (f) => f.field_name === sourceFieldForm.name,
  );
  if (exists && editingSourceField.value === null) {
    ElMessage.warning("字段名称已存在");
    return;
  }

  const expression = generateExpression();
  const sample = generateSampleResult();

  const fieldData = {
    field_name: sourceFieldForm.name,
    field_type: sourceFieldForm.type,
    description: `自定义字段: ${expression}`,
    is_custom: true,
    is_upload: 1,

    // Complex properties
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
    caseBranches: JSON.parse(JSON.stringify(sourceFieldForm.caseBranches)),
    defaultValue: sourceFieldForm.defaultValue,
    mathExpression: sourceFieldForm.mathExpression,
    dateFunction: sourceFieldForm.dateFunction,
    dateFormat: sourceFieldForm.dateFormat,
    dateInterval: sourceFieldForm.dateInterval,
  };

  // 更新或添加
  if (editingSourceField.value !== null) {
    // 暂时不支持编辑，如果需要支持，可以根据索引更新
    // 这里我们只做添加
  }

  customFields.value.push(fieldData);

  // 自动映射：如果是外部参数，且参数名与源字段名相同，或者其他逻辑
  // 这里不强制自动映射，由用户手动连线

  showSourceFieldDialog.value = false;

  // 强制刷新视图和连接线
  nextTick(() => {
    // 触发重新计算 sourceFields
    // 并且刷新连接线
    refreshLines();
  });
};

const hasSourceMapping = (name: string) => {
  return !!mappings.value[name];
};

const refreshLines = () => {
  const cont = connectorRef.value;
  const srcCont = sourceListRef.value;
  const tgtCont = targetListRef.value;
  if (!cont || !srcCont || !tgtCont) return;

  // Update height to match content
  connectorHeight.value = Math.max(
    srcCont.scrollHeight,
    tgtCont.scrollHeight,
    600,
  );

  const rectCont = cont.getBoundingClientRect();
  const res: Array<{
    source: string;
    target: string;
    path: string;
    mx: number;
    my: number;
  }> = [];

  const width = rectCont.width;

  for (const [s, t] of Object.entries(mappings.value)) {
    if (!t) continue;
    const sEl = sourceFieldRefs.value[s];
    const tEl = targetFieldRefs.value[t];
    if (!sEl || !tEl) continue;

    // Check if elements are visible
    if (sEl.offsetParent === null || tEl.offsetParent === null) continue;

    const sRect = sEl.getBoundingClientRect();
    const tRect = tEl.getBoundingClientRect();

    // Relative coordinates in SVG
    const y1 = sRect.top - rectCont.top + sRect.height / 2;
    const y2 = tRect.top - rectCont.top + tRect.height / 2;

    // Bezier Curve: M 0 y1 Q width/2 y1, width/2 y2, width y2 (Simplified Cubic or Quadratic)
    // Using Cubic Bezier for smoother curve: C cp1x cp1y, cp2x cp2y, x y
    // M 0 y1 C width/2 y1, width/2 y2, width y2

    const path = `M 0 ${y1} C ${width / 2} ${y1}, ${width / 2} ${y2}, ${width} ${y2}`;

    const mx = width / 2;
    const my = (y1 + y2) / 2;

    res.push({ source: s, target: t, path, mx, my });
  }
  lines.value = res;
};

const handleSourceClick = (sourceName: string) => {
  selectedSource.value = sourceName;
  if (selectedTarget.value) {
    mappings.value[sourceName] = selectedTarget.value;
    selectedSource.value = null;
    selectedTarget.value = null;
    refreshLines();
  }
};

const handleTargetClick = (targetName: string) => {
  selectedTarget.value = targetName;
  if (selectedSource.value) {
    mappings.value[selectedSource.value] = targetName;
    selectedSource.value = null;
    selectedTarget.value = null;
    refreshLines();
  }
};

const removeMapping = (sourceName: string) => {
  delete mappings.value[sourceName];
  refreshLines();
};

/**
 * 获取字段类型标签
 */
const getFieldTypeLabel = (type: string) => {
  const labels: Record<string, string> = {
    string: "字符串",
    number: "数字",
    boolean: "布尔值",
    date: "日期",
    array: "数组",
    object: "对象",
  };
  return labels[type] || type;
};

/**
 * 返回上一页
 */
const goBack = () => {
  router.back();
};

/**
 * 显示创建对话框
 */
const showCreateDialog = () => {
  isEdit.value = false;
  dialogVisible.value = true;
  resetForm();

  // 设置默认排序为最大值+1
  const maxOrder = Math.max(...fields.value.map((f) => f.sort_order || 0), 0);
  form.sort_order = maxOrder + 1;
};

const resetForm = () => {
  formRef.value?.resetFields();
  form.field_name = "";
  form.field_type = "string";
  form.is_required = false;
  form.default_value = "";
  form.description = "";
  form.validation_rules = "";
  form.sort_order = 1;
};

const submitForm = async () => {
  if (!formRef.value) return;
  await formRef.value.validate(async (valid) => {
    if (valid) {
      submitting.value = true;
      try {
        const apiId = parseInt(route.params.id as string);
        if (isEdit.value) {
          // Update logic if needed
        } else {
          const resp = await createApiField(apiId, form);
          if (resp.success) {
            ElMessage.success("创建字段成功");
            dialogVisible.value = false;
            loadFields(apiId);
          } else {
            ElMessage.error(resp.message || "创建字段失败");
          }
        }
      } catch (e) {
        ElMessage.error("操作失败");
      } finally {
        submitting.value = false;
      }
    }
  });
};

const onRequiredChange = async (row: ApiField, val: any) => {
  // Implementation for quick update
  // Currently placeholder, assume backend update or separate implementation
};

const onUploadChange = async (row: ApiField, val: any) => {
  // Implementation for quick update
};

const saveFieldsOrder = async () => {
  saving.value = true;
  // Implementation
  saving.value = false;
};

const handleSortChange = () => {};

// 打开资源类型字段选择抽屉
const openCenterDrawer = () => {
  if (!apiInfo.value?.resource_type_id) {
    ElMessage.warning("请先在 API 基础信息中选择资源类型");
    return;
  }
  centerDrawerVisible.value = true;
  if (centerTableFields.value.length === 0) {
    loadResourceTypeFields();
  }
};

// 加载资源类型字段（基于当前API的 resource_type_id）
const loadResourceTypeFields = async () => {
  try {
    centerFieldsLoading.value = true;
    const rtid = apiInfo.value?.resource_type_id;
    if (!rtid) {
      ElMessage.warning("当前 API 未配置资源类型，无法加载字段");
      return;
    }
    const response = await getResourceType(String(rtid));
    if (response?.success && response.data) {
      const meta = (response.data.metadata || []) as any[];
      centerTableFields.value = meta.map((m: any) => ({
        column_name: m.key,
        data_type:
          ((m.type || "string") as string).toLowerCase() === "integer"
            ? "int"
            : m.type || "string",
        column_comment: m.description || "",
        is_nullable: !(m.required === true),
      }));
    } else {
      centerTableFields.value = [];
      ElMessage.warning(response?.message || "资源类型未包含字段元数据");
    }
  } catch (e: any) {
    console.error("加载资源类型字段失败:", e);
    ElMessage.error(e?.message || "加载资源类型字段失败");
  } finally {
    centerFieldsLoading.value = false;
  }
};

// 新增：处理中心表字段选择
const handleCenterFieldSelection = (selection: CenterTableField[]) => {
  selectedCenterFields.value = selection;
};

// 新增：中心表字段是否可选择（已存在则禁选）
const selectableCenterField = (row: CenterTableField) => {
  return !fields.value.some((f) => f.field_name === row.column_name);
};

// 新增：判断中心表字段在当前API中是否已存在
const isExistingCenterField = (row: CenterTableField) => {
  return fields.value.some((f) => f.field_name === row.column_name);
};
// 将资源类型字段的类型映射为 API 字段类型
const mapDataTypeToApiFieldType = (
  dataType: string,
): ApiFieldCreate["field_type"] => {
  const t = (dataType || "").toLowerCase();
  if (
    t === "int" ||
    t.includes("bigint") ||
    t.includes("smallint") ||
    t.includes("int")
  ) {
    return "int";
  }
  if (
    t.includes("decimal") ||
    t.includes("float") ||
    t.includes("double") ||
    t.includes("numeric")
  ) {
    return "float";
  }
  if (t === "boolean" || t.includes("bool")) {
    return "boolean";
  }
  if (t === "date") {
    return "date";
  }
  if (t.includes("timestamp") || t.includes("datetime") || t.includes("time")) {
    return "datetime";
  }
  if (t.includes("json")) {
    return "json";
  }
  if (t.includes("text") || t.includes("char")) {
    return "text";
  }
  return "string";
};

// 新增：批量添加选中中心表字段到当前API
const addSelectedFields = async () => {
  if (selectedCenterFields.value.length === 0) {
    ElMessage.warning("请先选择要添加的字段");
    return;
  }
  const existingNames = new Set(fields.value.map((f) => f.field_name));
  const unique = selectedCenterFields.value.filter(
    (f) => !existingNames.has(f.column_name),
  );
  if (unique.length === 0) {
    ElMessage.warning("所选字段已存在，无需重复添加");
    return;
  }

  const apiId = parseInt(route.params.id as string);
  let order = Math.max(...fields.value.map((f) => f.sort_order || 0), 0);

  try {
    addingFromCenter.value = true;
    for (const f of unique) {
      const createData: ApiFieldCreate = {
        field_name: f.column_name,
        field_type: mapDataTypeToApiFieldType(f.data_type),
        is_required: !f.is_nullable,
        is_upload: 1,
        description: f.column_comment || "",
        sort_order: ++order,
      };
      const resp = await createApiField(apiId, createData);
      if (!resp.success) {
        ElMessage.error(resp.message || `添加字段失败：${f.column_name}`);
      }
    }
    ElMessage.success(`成功添加 ${unique.length} 个字段`);
    centerDrawerVisible.value = false;
    loadFields(apiId);
  } catch (e: any) {
    ElMessage.error(e?.message || "添加字段失败");
  } finally {
    addingFromCenter.value = false;
  }
};

// 搜索和高亮逻辑
const handleSourceSearch = (val: string) => {
  if (!val) return;
  const match = sourceFields.value.find((f) =>
    f.field_name.toLowerCase().includes(val.toLowerCase()),
  );
  if (match) {
    scrollToField(match.field_name, "source");
  }
};

const handleTargetSearch = (val: string) => {
  if (!val) return;
  const match = targetFields.value.find((f) =>
    f.name.toLowerCase().includes(val.toLowerCase()),
  );
  if (match) {
    scrollToField(match.name, "target");
  }
};

const scrollToField = (fieldName: string, type: "source" | "target") => {
  const id =
    type === "source"
      ? `source-field-${fieldName}`
      : `target-field-${fieldName}`;
  // 此时需要通过id获取DOM，因为ref是基于v-for的函数引用，查找起来稍微麻烦点，虽然也可以用 sourceFieldRefs
  // 这里尝试用 sourceFieldRefs / targetFieldRefs
  const refs =
    type === "source" ? sourceFieldRefs.value : targetFieldRefs.value;
  const el = refs[fieldName];

  if (el) {
    el.scrollIntoView({ behavior: "smooth", block: "center" });
    highlightedField.value = fieldName;
    setTimeout(() => {
      highlightedField.value = null;
    }, 2000);
  }
};

const highlightText = (text: string, query: string) => {
  if (!query) return text;
  const regex = new RegExp(`(${query})`, "gi");
  return text.replace(
    regex,
    '<span style="color: #e6a23c; font-weight: bold;">$1</span>',
  );
};
</script>

<style scoped>
.api-fields {
  padding: 20px;
}

.page-header {
  margin-bottom: 20px;
  background: #fff;
  padding: 16px 24px;
  border-radius: 4px;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.1);
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 16px;
}

.title-section {
  display: flex;
  flex-direction: column;
}

.page-title {
  margin: 0;
  font-size: 20px;
  display: flex;
  align-items: center;
  gap: 8px;
}

.page-description {
  margin: 4px 0 0;
  color: #909399;
  font-size: 13px;
}

.page-card {
  background: #fff;
  border-radius: 4px;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.1);
  margin-bottom: 20px;
  padding: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  border-bottom: 1px solid #ebeef5;
  padding-bottom: 12px;
}

.card-header h3 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: #303133;
}

.info-item {
  margin-bottom: 12px;
}

.info-item .label {
  color: #909399;
  margin-right: 8px;
}

.info-item .value {
  color: #303133;
  font-weight: 500;
}

/* Mapping Board Styles */
.mapping-board {
  position: relative;
  min-height: 500px;
  background: #f5f7fa;
  padding: 20px;
  border-radius: 4px;
}

.mapping-columns {
  display: flex;
  justify-content: space-between;
  gap: 0; /* Gap handled by connector width */
}

.source-list,
.target-list {
  flex: 1;
  background: #fff;
  border-radius: 8px;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.05);
  padding: 16px;
  min-height: 500px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.list-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-bottom: 12px;
  border-bottom: 1px solid #ebeef5;
  margin-bottom: 8px;
  font-weight: bold;
  color: #606266;
}

.list-header .count {
  background: #f0f2f5;
  padding: 2px 8px;
  border-radius: 10px;
  font-size: 12px;
  color: #909399;
}

.field-item {
  padding: 10px 12px;
  border: 1px solid #ebeef5;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.3s;
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: #fff;
  height: 64px;
  box-sizing: border-box;
  margin-bottom: 12px;
}

.field-item:hover {
  border-color: #409eff;
  background-color: #ecf5ff;
}

.field-item.active {
  border-color: #409eff;
  background-color: #ecf5ff;
  box-shadow: 0 0 0 2px rgba(64, 158, 255, 0.2);
}

.field-item.mapped {
  background-color: #f0f9eb;
  border-color: #67c23a;
}

.field-content {
  flex: 1;
  overflow: hidden;
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
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.field-type {
  font-size: 12px;
  color: #909399;
  background: #f4f4f5;
  padding: 1px 5px;
  border-radius: 4px;
}

.field-desc {
  font-size: 12px;
  color: #909399;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.required-badge {
  font-size: 12px;
  color: #f56c6c;
  background: #fef0f0;
  padding: 1px 5px;
  border-radius: 4px;
}

.field-status {
  margin-left: 8px;
}

.field-map-info {
  font-size: 12px;
  color: #67c23a;
  display: flex;
  align-items: center;
  gap: 4px;
}

/* Connector Styles */
.connector {
  width: 150px;
  position: relative;
  pointer-events: none; /* Let clicks pass through to SVG elements */
}

.connection-svg {
  position: absolute;
  top: 0;
  left: 0;
  pointer-events: auto; /* Re-enable pointer events for SVG */
  overflow: visible;
}

.connection-line {
  transition: all 0.3s;
}

.connection-line:hover {
  stroke-width: 3;
  stroke: #66b1ff;
}

.delete-btn-group {
  /* opacity: 0; removed to make it always visible or visible on hover of line */
  transition: opacity 0.3s;
}

.delete-btn-group:hover circle {
  fill: #e53e3e;
  r: 10;
  transition: all 0.2s;
}

/* g:hover > .delete-btn-group {
  opacity: 1;
} */

.connection-line:hover + .delete-btn-group,
.delete-btn-group:hover {
  opacity: 1;
}

.list-search {
  padding-bottom: 8px;
  border-bottom: 1px solid #ebeef5;
  margin-bottom: 8px;
}

.fields-scroll-container {
  flex: 1;
  overflow-y: auto;
  padding-right: 4px; /* for scrollbar */
}

.field-item.highlighted {
  animation: highlight-pulse 2s ease-in-out;
  border-color: #e6a23c;
  background-color: #fdf6ec;
}

@keyframes highlight-pulse {
  0% {
    box-shadow: 0 0 0 0 rgba(230, 162, 60, 0.7);
  }
  70% {
    box-shadow: 0 0 0 6px rgba(230, 162, 60, 0);
  }
  100% {
    box-shadow: 0 0 0 0 rgba(230, 162, 60, 0);
  }
}

.header-actions {
  display: flex;
  gap: 10px;
  align-items: center;
}
</style>
