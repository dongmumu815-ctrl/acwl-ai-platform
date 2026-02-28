<template>
  <div class="es-query-builder">
    <!-- ES查询构建器 -->
    <el-card class="query-card">
      <template #header>
        <div class="card-header">
          <span>Elasticsearch查询构建器</span>
          <div class="header-actions">
            <el-button @click="clearESQuery">
              <el-icon><Delete /></el-icon>
              清空
            </el-button>

            <el-button :disabled="!hasSavePermission" @click="saveESQuery">
              <el-icon><Document /></el-icon>
              保存查询
            </el-button>
            <el-button
              type="primary"
              :loading="querying"
              :disabled="!canExecuteQuery"
              @click="executeESQuery"
            >
              <el-icon><CaretRight /></el-icon>
              执行查询
            </el-button>
            <el-button
              v-if="!props.isInResourcePackage"
              type="success"
              :disabled="!hasValidQuery"
              @click="addToResourcePackage"
            >
              <el-icon>
                <FolderAdd />
              </el-icon>
              添加到资源包
            </el-button>
          </div>
        </div>
      </template>

      <div class="es-datasource-selector">
        <el-row :gutter="16">
          <el-col :span="8">
            <el-form-item label="数据源">
              <el-select
                v-model="esQueryConfig.datasourceId"
                placeholder="请选择ES数据源"
                style="width: 100%"
                filterable
                @change="onEsDatasourceChange"
              >
                <el-option
                  v-for="ds in esDatasources"
                  :key="ds.id"
                  :label="ds.name"
                  :value="ds.id"
                />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item v-if="props.dataResourceId" label="查询模板">
              <el-select
                v-model="selectedTemplateId"
                placeholder="选择查询模板"
                style="width: 100%"
                clearable
                :loading="loadingTemplates"
                filterable
                @change="onTemplateChange"
              >
                <el-option
                  v-for="template in availableTemplates"
                  :key="template.id"
                  :label="template.name"
                  :value="template.id"
                >
                  <div class="template-option">
                    <span class="template-name">{{ template.name }}</span>
                    <span class="template-desc">{{
                      template.description
                    }}</span>
                  </div>
                </el-option>
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>
      </div>

      <!-- 查询类型选择 -->
      <div class="query-type-selector">
        <el-radio-group v-model="queryType" @change="onQueryTypeChange">
          <el-radio-button label="visual">可视化查询</el-radio-button>
          <el-radio-button label="dsl">DSL查询</el-radio-button>
        </el-radio-group>
      </div>

      <!-- 可视化查询构建器 -->
      <div v-if="queryType === 'visual'" class="visual-query-builder">
        <!-- 索引选择 -->
        <div v-if="!shouldHideIndexSelector" class="query-section">
          <!-- <div  class="query-section"> -->
          <!-- <label class="section-label">索引选择:{{ visualQuery.indices }},{{ esQueryConfig.availableIndices }}</label>
          -->
          <el-select
            v-model="visualQuery.indices[0]"
            placeholder="请选择索引"
            style="width: 100%"
            filterable
            @change="onIndicesChange"
          >
            <el-option
              v-for="index in esQueryConfig.availableIndices"
              :key="index.name"
              :label="index.name"
              :value="index.name"
            />
          </el-select>
        </div>

        <!-- 当索引被预设时，显示当前使用的索引 -->
        <div v-if="shouldHideIndexSelector" class="query-section">
          <label class="section-label">当前索引:</label>
          <div class="current-indices">
            <el-tag
              v-for="index in visualQuery.indices"
              :key="index"
              type="primary"
              size="default"
            >
              {{ index }}
            </el-tag>
          </div>
        </div>

        <!-- 字段选择 -->
        <div class="query-section">
          <label class="section-label">返回字段:</label>
          <el-select
            v-model="visualQuery.fields"
            multiple
            placeholder="请选择字段（留空返回所有字段）"
            style="width: 100%"
            filterable
          >
            <el-option
              v-for="field in esQueryConfig.availableFields"
              :key="field.name"
              :label="`${field.name} (${field.comment || field.type})`"
              :value="field.name"
            />
          </el-select>
        </div>

        <!-- 查询条件 -->
        <div class="query-section">
          <div class="section-header">
            <label class="section-label">查询条件:</label>
            <el-button type="primary" size="small" @click="addCondition">
              <el-icon><Plus /></el-icon>
              添加条件
            </el-button>
          </div>

          <div
            v-if="visualQuery.conditions.length === 0"
            class="empty-conditions"
          >
            <el-text type="info">暂无查询条件，将返回所有文档</el-text>
          </div>

          <div v-else class="conditions-list">
            <div
              v-for="(condition, index) in visualQuery.conditions"
              :key="index"
              class="condition-item"
              :class="{ 'locked-condition': condition._locked }"
            >
              <!-- 锁定状态指示器 -->
              <div v-if="condition._locked" class="lock-indicator">
                <el-icon class="lock-icon"><Lock /></el-icon>
                <el-tag
                  :type="getLockTypeTagType(condition._lockType)"
                  size="small"
                  class="lock-type-tag"
                >
                  {{ getLockTypeLabel(condition._lockType) }}
                </el-tag>
              </div>

              <!-- 逻辑操作符 -->
              <div v-if="index > 0" class="logic-operator">
                <el-select
                  v-model="condition.logic"
                  size="small"
                  style="width: 80px"
                  :disabled="
                    condition._locked && condition._lockType === 'full'
                  "
                  filterable
                >
                  <el-option label="AND" value="must" />
                  <el-option label="OR" value="should" />
                  <el-option label="NOT" value="must_not" />
                </el-select>
              </div>

              <!-- 条件配置 -->
              <div class="condition-config">
                <!-- 字段选择 -->
                <el-select
                  v-model="condition.field"
                  placeholder="选择字段"
                  style="width: 150px"
                  :disabled="
                    condition._locked &&
                    (condition._lockType === 'full' ||
                      condition._lockType === 'field')
                  "
                  filterable
                  @change="onFieldChange(condition)"
                >
                  <el-option
                    v-for="field in esQueryConfig.availableFields"
                    :key="field.name"
                    :label="field.name"
                    :value="field.name"
                  />
                </el-select>

                <!-- 操作符选择 -->
                <el-select
                  v-model="condition.operator"
                  placeholder="操作符"
                  style="width: 120px"
                  :disabled="
                    condition._locked &&
                    (condition._lockType === 'full' ||
                      condition._lockType === 'operator')
                  "
                  filterable
                >
                  <el-option
                    v-for="op in getAvailableOperators(condition.field)"
                    :key="op.value"
                    :label="op.label"
                    :value="op.value"
                  />
                </el-select>

                <!-- 值输入 -->
                <div class="value-input">
                  <!-- 文本输入 -->
                  <el-input
                    v-if="
                      condition.operator !== 'range' &&
                      condition.operator !== 'exists'
                    "
                    v-model="condition.value"
                    placeholder="输入值"
                    style="width: 200px"
                    :disabled="
                      condition._locked &&
                      (condition._lockType === 'full' ||
                        condition._lockType === 'value')
                    "
                  />

                  <!-- 范围输入 -->
                  <div
                    v-else-if="condition.operator === 'range'"
                    class="range-input"
                  >
                    <el-input
                      v-model="condition.rangeFrom"
                      placeholder="从"
                      style="width: 90px"
                      :disabled="
                        condition._locked &&
                        (condition._lockType === 'full' ||
                          condition._lockType === 'value')
                      "
                    />
                    <span class="range-separator">-</span>
                    <el-input
                      v-model="condition.rangeTo"
                      placeholder="到"
                      style="width: 90px"
                      :disabled="
                        condition._locked &&
                        (condition._lockType === 'full' ||
                          condition._lockType === 'value')
                      "
                    />
                  </div>
                </div>

                <!-- 操作按钮 -->
                <div class="condition-actions">
                  <el-button
                    v-if="!condition._locked"
                    type="danger"
                    size="small"
                    @click="removeCondition(index)"
                  >
                    <el-icon><Delete /></el-icon>
                  </el-button>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- 排序设置 -->
        <div class="query-section">
          <div class="section-header">
            <label class="section-label">排序设置:</label>
            <el-button type="primary" size="small" @click="addSort">
              <el-icon><Plus /></el-icon>
              添加排序
            </el-button>
          </div>

          <div v-if="visualQuery.sorts.length === 0" class="empty-sorts">
            <el-text type="info">暂无排序设置</el-text>
          </div>

          <div v-else class="sorts-list">
            <div
              v-for="(sort, index) in visualQuery.sorts"
              :key="index"
              class="sort-item"
            >
              <el-select
                v-model="sort.field"
                placeholder="选择字段"
                style="width: 200px"
                filterable
              >
                <el-option
                  v-for="field in esQueryConfig.availableFields"
                  :key="field.name"
                  :label="`${field.name} (${field.comment || field.type})`"
                  :value="field.name"
                />
              </el-select>

              <el-select v-model="sort.order" style="width: 100px" filterable>
                <el-option label="升序" value="asc" />
                <el-option label="降序" value="desc" />
              </el-select>

              <el-button type="danger" size="small" @click="removeSort(index)">
                <el-icon><Delete /></el-icon>
              </el-button>
            </div>
          </div>
        </div>

        <!-- 聚合查询设置 -->
        <div class="query-section">
          <div class="section-header">
            <label class="section-label">聚合查询:</label>
            <el-button type="primary" size="small" @click="addAggregation">
              <el-icon><Plus /></el-icon>
              添加聚合
            </el-button>
          </div>

          <div
            v-if="visualQuery.aggregations.length === 0"
            class="empty-aggregations"
          >
            <el-text type="info">暂无聚合查询</el-text>
          </div>

          <div v-else class="aggregations-list">
            <div
              v-for="(agg, index) in visualQuery.aggregations"
              :key="index"
              class="aggregation-item"
            >
              <!-- 聚合名称 -->
              <el-input
                v-model="agg.name"
                placeholder="聚合名称"
                size="small"
                style="width: 120px"
              />

              <!-- 聚合类型 -->
              <el-select
                v-model="agg.type"
                placeholder="聚合类型"
                size="small"
                style="width: 120px"
                filterable
                @change="onAggregationTypeChange(agg)"
              >
                <el-option label="计数" value="value_count" />
                <el-option label="求和" value="sum" />
                <el-option label="平均值" value="avg" />
                <el-option label="最大值" value="max" />
                <el-option label="最小值" value="min" />
                <el-option label="分组" value="terms" />
                <el-option label="日期直方图" value="date_histogram" />
                <el-option label="数值直方图" value="histogram" />
                <el-option label="范围聚合" value="range" />
              </el-select>

              <!-- 字段选择 -->
              <el-select
                v-model="agg.field"
                placeholder="选择字段"
                size="small"
                style="width: 150px"
                filterable
              >
                <el-option
                  v-for="field in esQueryConfig.availableFields"
                  :key="field.name"
                  :label="`${field.name} (${field.comment || field.type})`"
                  :value="field.name"
                />
              </el-select>

              <!-- 聚合参数配置 -->
              <div class="aggregation-params">
                <!-- Terms聚合参数 -->
                <template v-if="agg.type === 'terms'">
                  <el-input-number
                    v-model="agg.params.size"
                    placeholder="返回数量"
                    :min="1"
                    :max="10000"
                    size="small"
                    style="width: 100px"
                  />
                  <span class="param-label">条数</span>
                </template>

                <!-- 日期直方图参数 -->
                <template v-if="agg.type === 'date_histogram'">
                  <el-select
                    v-model="agg.params.calendar_interval"
                    placeholder="时间间隔"
                    size="small"
                    style="width: 100px"
                    filterable
                  >
                    <el-option label="1分钟" value="1m" />
                    <el-option label="5分钟" value="5m" />
                    <el-option label="1小时" value="1h" />
                    <el-option label="1天" value="1d" />
                    <el-option label="1周" value="1w" />
                    <el-option label="1月" value="1M" />
                  </el-select>
                </template>

                <!-- 数值直方图参数 -->
                <template v-if="agg.type === 'histogram'">
                  <el-input-number
                    v-model="agg.params.interval"
                    placeholder="间隔"
                    :min="1"
                    size="small"
                    style="width: 100px"
                  />
                  <span class="param-label">间隔</span>
                </template>

                <!-- 范围聚合参数 -->
                <template v-if="agg.type === 'range'">
                  <el-button size="small" @click="addRange(agg)"
                    >添加范围</el-button
                  >
                  <div
                    v-for="(range, rangeIndex) in agg.params.ranges"
                    :key="rangeIndex"
                    class="range-config"
                  >
                    <el-input-number
                      v-model="range.from"
                      placeholder="起始值"
                      size="small"
                      style="width: 80px"
                    />
                    <span>-</span>
                    <el-input-number
                      v-model="range.to"
                      placeholder="结束值"
                      size="small"
                      style="width: 80px"
                    />
                    <el-button
                      type="danger"
                      size="small"
                      @click="removeRange(agg, rangeIndex)"
                    >
                      <el-icon><Delete /></el-icon>
                    </el-button>
                  </div>
                </template>
              </div>

              <!-- 删除聚合 -->
              <el-button
                type="danger"
                size="small"
                @click="removeAggregation(index)"
              >
                <el-icon><Delete /></el-icon>
              </el-button>
            </div>
          </div>
        </div>

        <!-- 分页设置 -->
        <div class="query-section">
          <label class="section-label">分页设置:</label>
          <el-row :gutter="16">
            <el-col :span="12">
              <el-input-number
                v-model="visualQuery.from"
                :min="0"
                placeholder="起始位置"
                style="width: 100%"
              />
            </el-col>
            <el-col :span="12">
              <el-input-number
                v-model="visualQuery.size"
                :min="1"
                :max="10000"
                placeholder="返回数量"
                style="width: 100%"
              />
            </el-col>
          </el-row>
        </div>
      </div>

      <!-- DSL查询编辑器 -->
      <div v-else-if="queryType === 'dsl'" class="dsl-query-editor">
        <div class="editor-header">
          <label class="section-label">DSL查询:</label>
          <div class="editor-actions">
            <el-button size="small" @click="formatDSL">
              <el-icon><Document /></el-icon>
              格式化
            </el-button>
            <el-button size="small" @click="validateDSL">
              <el-icon><Check /></el-icon>
              验证
            </el-button>
          </div>
        </div>

        <div class="dsl-editor">
          <textarea
            v-model="dslQuery"
            class="dsl-textarea"
            placeholder="请输入Elasticsearch DSL查询..."
            @input="onDSLChange"
          ></textarea>
        </div>

        <div v-if="dslValidationError" class="validation-error">
          <el-alert
            :title="dslValidationError"
            type="error"
            show-icon
            :closable="false"
          />
        </div>
      </div>

      <!-- 查询预览 -->
      <div class="query-preview">
        <div class="preview-header">
          <label class="section-label">查询预览:</label>
          <el-button size="small" @click="copyQuery">
            <el-icon><CopyDocument /></el-icon>
            复制查询
          </el-button>
        </div>

        <div class="preview-content">
          <pre class="query-json">{{ formattedQuery }}</pre>
        </div>
      </div>
    </el-card>

    <!-- 查询结果 -->
    <el-card v-if="queryResults" class="results-card">
      <template #header>
        <div class="results-header">
          <span>查询结果</span>
          <div class="results-info">
            <el-tag
              >总计:
              {{
                queryResults.hits?.total?.value || queryResults.hits?.total || 0
              }}</el-tag
            >
            <el-tag type="info">耗时: {{ queryResults.took }}ms</el-tag>
          </div>
        </div>
      </template>

      <div class="results-content">
        <!-- 聚合结果卡片 -->
        <el-card
          v-if="
            queryResults?.aggregations &&
            Object.keys(queryResults.aggregations).length > 0
          "
          class="aggregations-card"
          shadow="hover"
        >
          <template #header>
            <div class="aggregations-header">
              <el-icon><PieChart /></el-icon>
              <span>聚合结果</span>
              <el-button
                size="small"
                :type="aggregationsExpanded ? 'primary' : 'default'"
                @click="toggleAggregationsExpand"
              >
                {{ aggregationsExpanded ? "收起" : "展开" }}
              </el-button>
            </div>
          </template>

          <div class="aggregations-content">
            <!-- 聚合结果概览 -->
            <div class="aggregations-summary">
              <el-tag
                v-for="(agg, name) in queryResults.aggregations"
                :key="name"
                type="info"
                class="agg-tag"
              >
                {{ name }}: {{ getAggregationSummary(agg) }}
              </el-tag>
            </div>

            <!-- 详细聚合结果 -->
            <div v-if="aggregationsExpanded" class="aggregations-detail">
              <div
                v-for="(agg, name) in queryResults.aggregations"
                :key="name"
                class="aggregation-item"
              >
                <h4 class="aggregation-title">{{ name }}</h4>
                <div class="aggregation-data">
                  <!-- Terms 聚合 -->
                  <div v-if="agg.buckets" class="buckets-container">
                    <div class="bucket-cards">
                      <div
                        v-for="bucket in agg.buckets"
                        :key="bucket.key"
                        class="bucket-card"
                      >
                        <div class="bucket-name">{{ bucket.key }}</div>
                        <div class="bucket-count">{{ bucket.doc_count }}</div>
                      </div>
                    </div>
                    <div v-if="agg.sum_other_doc_count > 0" class="other-docs">
                      <el-text type="info" size="small">
                        其他分类: {{ agg.sum_other_doc_count }} 个文档
                      </el-text>
                    </div>
                  </div>

                  <!-- 数值聚合 -->
                  <div v-else-if="agg.value !== undefined" class="metric-value">
                    <el-statistic :value="agg.value" :precision="2" />
                  </div>

                  <!-- 其他类型聚合 -->
                  <div v-else class="raw-aggregation">
                    <pre>{{ JSON.stringify(agg, null, 2) }}</pre>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </el-card>

        <el-table
          :data="queryResults.hits?.hits || []"
          style="width: 100%"
          max-height="600"
          stripe
        >
          <!-- 文档ID列 -->
          <el-table-column
            prop="_id"
            label="文档ID"
            width="200"
            fixed="left"
            show-overflow-tooltip
          />
          <!-- 动态字段列 -->
          <el-table-column
            v-for="field in documentFields"
            :key="field"
            :prop="`_source.${field}`"
            :label="field"
            min-width="150"
            show-overflow-tooltip
          >
            <template #default="{ row }">
              <div class="field-value">
                {{ formatFieldValue(row._source[field]) }}
              </div>
            </template>
          </el-table-column>
          <!-- 完整文档列（可选显示） -->
          <el-table-column
            v-if="showFullDocument"
            label="完整文档"
            min-width="300"
          >
            <template #default="{ row }">
              <div class="document-source">
                <el-button
                  size="small"
                  :type="expandedDocs.has(row._id) ? 'primary' : 'default'"
                  @click="toggleDocumentExpand(row._id)"
                >
                  {{ expandedDocs.has(row._id) ? "收起" : "展开" }}
                </el-button>
                <div v-if="expandedDocs.has(row._id)" class="expanded-document">
                  <pre>{{ JSON.stringify(row._source, null, 2) }}</pre>
                </div>
              </div>
            </template>
          </el-table-column>
        </el-table>

        <!-- 结果控制选项 -->
        <div class="results-controls">
          <el-checkbox v-model="showFullDocument" label="显示完整文档列" />
          <el-button
            size="small"
            :disabled="!queryResults"
            @click="exportResults"
          >
            <el-icon><Download /></el-icon>
            导出结果
          </el-button>
        </div>

        <!-- 分页 -->
        <div class="pagination-wrapper">
          <el-pagination
            v-model:current-page="currentPage"
            v-model:page-size="pageSize"
            :page-sizes="[10, 20, 50, 100]"
            :total="
              queryResults.hits?.total?.value || queryResults.hits?.total || 0
            "
            layout="total, sizes, prev, pager, next, jumper"
            @size-change="handleSizeChange"
            @current-change="handleCurrentChange"
          />
        </div>
      </div>
    </el-card>

    <!-- 保存查询对话框 -->
    <el-dialog
      v-model="saveDialogVisible"
      :title="currentTemplateId ? '编辑ES查询模板' : '保存ES查询模板'"
      width="600px"
    >
      <el-form :model="saveForm" label-width="100px">
        <!-- 显示模板ID（仅在编辑模式下） -->
        <el-form-item v-if="currentTemplateId" label="模板ID">
          <el-input :value="currentTemplateId" disabled>
            <template #prepend>
              <el-icon><Document /></el-icon>
            </template>
          </el-input>
        </el-form-item>
        <el-form-item label="模板名称" required>
          <el-input v-model="saveForm.name" placeholder="请输入模板名称" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input
            v-model="saveForm.description"
            type="textarea"
            :rows="3"
            placeholder="请输入模板描述"
          />
        </el-form-item>
        <el-form-item label="查询内容">
          <div class="query-content">
            <pre>{{ formattedQuery }}</pre>
          </div>
        </el-form-item>
      </el-form>

      <template #footer>
        <div class="dialog-footer">
          <el-button @click="saveDialogVisible = false">取消</el-button>
          <el-button type="primary" :loading="saving" @click="confirmSaveQuery">
            {{ currentTemplateId ? "更新模板" : "保存模板" }}
          </el-button>
        </div>
      </template>
    </el-dialog>

    <!-- 添加到资源包对话框 -->
    <el-dialog
      v-model="resourcePackageVisible"
      :title="props.isInResourcePackage ? '更新资源包' : '添加到资源包'"
      width="600px"
    >
      <el-form :model="resourcePackageForm" label-width="100px">
        <el-form-item label="资源包名称" required>
          <el-input
            v-model="resourcePackageForm.name"
            placeholder="请输入资源包名称"
            maxlength="255"
            show-word-limit
          />
        </el-form-item>
        <el-form-item label="描述">
          <el-input
            v-model="resourcePackageForm.description"
            type="textarea"
            :rows="3"
            placeholder="请输入资源包描述"
            maxlength="500"
            show-word-limit
          />
        </el-form-item>
        <el-form-item label="标签">
          <el-select
            v-model="resourcePackageForm.tags"
            multiple
            filterable
            allow-create
            placeholder="请选择或输入标签"
            style="width: 100%"
          >
            <el-option label="数据分析" value="数据分析" />
            <el-option label="报表" value="报表" />
            <el-option label="监控" value="监控" />
            <el-option label="业务" value="业务" />
            <el-option label="测试" value="测试" />
          </el-select>
        </el-form-item>
        <el-form-item label="查询预览">
          <div class="query-content">
            <pre>{{ formattedQuery }}</pre>
          </div>
        </el-form-item>
      </el-form>

      <template #footer>
        <div class="dialog-footer">
          <el-button @click="resourcePackageVisible = false">取消</el-button>
          <el-button
            type="primary"
            :loading="creatingResourcePackage"
            @click="confirmAddToResourcePackage"
          >
            {{ props.isInResourcePackage ? "更新资源包" : "创建资源包" }}
          </el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, watch, onMounted, nextTick } from "vue";
import { ElMessage, ElMessageBox } from "element-plus";
import {
  Delete,
  Document,
  CaretRight,
  FolderAdd,
  Plus,
  Lock,
  Check,
  CopyDocument,
  Edit,
  Download,
  PieChart,
} from "@element-plus/icons-vue";
import { useUserStore } from "@/stores/user";
import { datasourceApi } from "@/api/datasource";
import { templateApi } from "@/api/template";
import {
  getESIndices,
  getESFieldMapping,
  executeESQuery as executeESQueryAPI,
  saveESQueryTemplate,
  updateESQueryTemplate,
} from "@/api/esQuery";
import { resourcePackageApi, PackageType } from "@/api/resourcePackage";

// Props
const props = defineProps({
  initialDatasourceId: {
    type: String,
    default: "",
  },
  initialIndices: {
    type: Array,
    default: () => [],
  },
  initialQuery: {
    type: Object,
    default: () => ({}),
  },
  dataResourceId: {
    type: [String, Number],
    default: null,
  },
  // 资源包相关属性
  isInResourcePackage: {
    type: Boolean,
    default: false,
  },
  resourcePackageId: {
    type: [String, Number],
    default: null,
  },
  resourcePackageName: {
    type: String,
    default: "",
  },
});

// Emits
const emit = defineEmits([
  "query-executed",
  "query-saved",
  "add-to-resource-package",
  "update-resource-package",
]);

// 用户状态管理
const userStore = useUserStore();

// Reactive data
const queryType = ref("visual");
const querying = ref(false);
const saving = ref(false);
const loadingTemplates = ref(false);
const saveDialogVisible = ref(false);
const dslValidationError = ref("");
const selectedTemplateId = ref("");
const currentTemplateId = ref(null); // 当前编辑的模板ID，用于区分新增和更新操作
const currentPage = ref(1);
const pageSize = ref(20);

// 查询结果显示控制
const showFullDocument = ref(false);
const expandedDocs = ref(new Set());
const aggregationsExpanded = ref(false);

// ES数据源配置
const esQueryConfig = reactive({
  datasourceId: props.initialDatasourceId || "",
  availableIndices: [...props.initialIndices],
  availableFields: [],
  builderQuery: { ...props.initialQuery },
});

// ES数据源列表
const esDatasources = ref([]);

// 可用模板
const availableTemplates = ref([]);

// 可视化查询配置
const visualQuery = reactive({
  indices: [...(props.initialIndices || [])],
  fields: [],
  conditions: [],
  sorts: [],
  aggregations: [],
  from: 0,
  size: 20,
});

// DSL查询
const dslQuery = ref("");

// 查询结果
const queryResults = ref(null);

// 保存表单
const saveForm = reactive({
  name: "",
  description: "",
});

// 资源包表单
const resourcePackageForm = reactive({
  name: "",
  description: "",
  tags: [],
});

// 资源包对话框状态
const resourcePackageVisible = ref(false);
const creatingResourcePackage = ref(false);

// Computed
const hasSavePermission = computed(() => {
  return (
    userStore.hasPermission("data:resource:save") || userStore.hasRole("admin")
  );
});

const canExecuteQuery = computed(() => {
  return (
    esQueryConfig.datasourceId &&
    ((queryType.value === "visual" && visualQuery.indices.length > 0) ||
      (queryType.value === "dsl" && dslQuery.value.trim()))
  );
});

const hasValidQuery = computed(() => {
  return (
    queryResults.value &&
    queryResults.value.hits?.hits &&
    queryResults.value.hits.hits.length > 0
  );
});

const formattedQuery = computed(() => {
  try {
    const query = buildQuery();
    return JSON.stringify(query, null, 2);
  } catch (error) {
    return "查询构建错误: " + error.message;
  }
});

/**
 * 判断是否应该隐藏索引选择器
 * 当有初始索引时（从URL参数传入），隐藏索引选择器
 */
const shouldHideIndexSelector = computed(() => {
  return props.initialIndices && props.initialIndices.length > 0;
});

/**
 * 动态生成文档字段列表
 * 从查询结果中提取所有文档的字段作为表头
 */
const documentFields = computed(() => {
  if (
    !queryResults.value?.hits?.hits ||
    queryResults.value.hits.hits.length === 0
  ) {
    return [];
  }

  const fieldsSet = new Set();

  // 遍历所有文档，收集所有字段
  queryResults.value.hits.hits.forEach((hit) => {
    if (hit._source && typeof hit._source === "object") {
      Object.keys(hit._source).forEach((field) => {
        fieldsSet.add(field);
      });
    }
  });

  // 转换为数组并排序
  return Array.from(fieldsSet).sort();
});

// Methods
/**
 * 加载ES数据源列表
 */
const loadESDatasources = async () => {
  try {
    const response = await datasourceApi.getDataSourceList({
      datasource_type: "elasticsearch",
    });
    if (response.success) {
      esDatasources.value = response.data.items || response.data;
    }
  } catch (error) {
    console.error("加载ES数据源失败:", error);
    ElMessage.error("加载ES数据源失败");
  }
};

/**
 * 加载查询模板列表
 */
const loadTemplates = async () => {
  console.log("🔄 loadTemplates 被调用，当前状态:", {
    dataResourceId: props.dataResourceId,
    hasDataResourceId: !!props.dataResourceId,
  });

  if (!props.dataResourceId) {
    console.log("❌ 没有dataResourceId，跳过模板加载");
    return;
  }

  loadingTemplates.value = true;
  try {
    console.log("📡 开始请求模板数据...");
    const templates = await templateApi.list(
      undefined, // datasource_id
      "es", // type
      props.dataResourceId, // data_resource_id
      undefined, // indices
    );
    console.log("✅ 模板数据请求成功:", templates);
    console.log("📋 API返回的模板数量:", templates?.data?.length || 0);

    // 从响应中提取模板数据数组
    availableTemplates.value = templates?.data || [];
    console.log(
      "💾 availableTemplates 已更新，数量:",
      availableTemplates.value.length,
    );
    console.log("💾 availableTemplates 内容:", availableTemplates.value);

    // 自动选择最新的模板（按创建时间或更新时间排序）
    if (availableTemplates.value.length > 0) {
      // 找到最新的模板（假设有 created_at 或 updated_at 字段，或者使用 id 最大值）
      const latestTemplate = availableTemplates.value.reduce(
        (latest, current) => {
          // 优先使用 updated_at，其次 created_at，最后使用 id
          const latestTime =
            latest.updated_at || latest.created_at || latest.id;
          const currentTime =
            current.updated_at || current.created_at || current.id;
          return currentTime > latestTime ? current : latest;
        },
      );

      console.log(
        "🎯 自动选择最新模板:",
        latestTemplate.name,
        "ID:",
        latestTemplate.id,
      );
      selectedTemplateId.value = latestTemplate.id;
      visualQuery.indices = [latestTemplate.indices[0]];
      saveForm.name = latestTemplate.name;
      saveForm.description = latestTemplate.description;
      // 触发模板变更事件，自动加载模板内容
      await onTemplateChange();
    }
  } catch (error) {
    console.error("❌ 加载查询模板失败:", error);
    ElMessage.error("加载查询模板失败");
  } finally {
    loadingTemplates.value = false;
    console.log("🏁 loadTemplates 完成");
  }
};

/**
 * ES数据源变更处理
 */
const onEsDatasourceChange = async () => {
  // 重置相关状态
  esQueryConfig.availableFields = [];
  selectedTemplateId.value = "";

  if (!esQueryConfig.datasourceId) return;

  try {
    // 如果有初始索引（从URL参数传入），优先使用初始索引，不需要从服务器获取
    if (props.initialIndices && props.initialIndices.length > 0) {
      esQueryConfig.availableIndices = [...props.initialIndices];
      // 对于单选模式，只选择第一个索引
      visualQuery.indices = props.initialIndices[0];
    } else {
      // 只有在没有初始索引时，才从服务器加载索引列表
      const indicesResponse = await getESIndices(
        parseInt(esQueryConfig.datasourceId),
      );
      if (indicesResponse.data) {
        esQueryConfig.availableIndices = indicesResponse.data;
        visualQuery.indices = [];
      } else {
        esQueryConfig.availableIndices = [];
        visualQuery.indices = [];
      }
    }

    // 加载模板
    await loadTemplates();

    // 如果索引已经确定，自动加载字段信息
    if (visualQuery.indices.length > 0) {
      await loadFieldsForIndices();
    }
  } catch (error) {
    console.error("加载数据源信息失败:", error);
    ElMessage.error("加载数据源信息失败");
  }
};

/**
 * 加载选中索引的字段信息
 */
const loadFieldsForIndices = async () => {
  // 确保visualQuery.indices是数组，如果不是则转换为数组
  const selectedIndices = Array.isArray(visualQuery.indices)
    ? visualQuery.indices
    : visualQuery.indices
      ? [visualQuery.indices]
      : [];

  console.log("🔍 loadFieldsForIndices 调用，当前状态:", {
    datasourceId: esQueryConfig.datasourceId,
    indices: selectedIndices,
    indicesLength: selectedIndices.length,
  });

  if (!selectedIndices.length) {
    console.log("⚠️ 没有选中的索引");
    esQueryConfig.availableFields = [];
    return;
  }

  // 确保数据源ID存在
  if (!esQueryConfig.datasourceId) {
    console.warn("❌ 数据源ID为空");
    esQueryConfig.availableFields = [];
    return;
  }

  try {
    console.log("📡 请求字段映射信息:", {
      datasourceId: esQueryConfig.datasourceId,
      indices: selectedIndices,
    });

    // 加载选中索引的字段映射信息
    const fieldsResponse = await getESFieldMapping(
      parseInt(esQueryConfig.datasourceId),
      selectedIndices,
    );
    console.log("字段API响应:", fieldsResponse);

    if (fieldsResponse.data && fieldsResponse.data.fields) {
      esQueryConfig.availableFields = fieldsResponse.data.fields;
      console.log("成功加载字段:", esQueryConfig.availableFields);
    } else {
      console.warn("API响应中没有字段数据:", fieldsResponse);
      esQueryConfig.availableFields = [];
    }
  } catch (error) {
    console.error("加载字段信息失败:", error);
    ElMessage.error("加载字段信息失败");
    esQueryConfig.availableFields = [];
  }
};

const onTemplateChange = async () => {
  if (!selectedTemplateId.value) {
    // 清空选择时，重置当前模板ID和保存表单
    currentTemplateId.value = null;
    saveForm.name = "";
    saveForm.description = "";
    return;
  }
  const template = availableTemplates.value.find(
    (t) => t.id === selectedTemplateId.value,
  );
  if (!template) return;
  try {
    // 处理 query 字段可能是对象或字符串的情况
    let query;
    if (typeof template.query === "string") {
      query = JSON.parse(template.query);
    } else {
      query = template.query;
    }

    console.log("📋 模板查询数据:", query);
    loadQuery(query);

    // 设置当前模板ID为编辑状态
    currentTemplateId.value = template.id;

    // 填充保存表单的名称和描述
    saveForm.name = template.name || "";
    saveForm.description = template.description || "";

    // alert(3)

    console.log(
      "加载模板成功，设置当前模板ID为编辑状态:",
      currentTemplateId.value,
    );

    ElMessage.success("模板加载成功");
  } catch (error) {
    console.error("加载模板失败:", error);
    ElMessage.error("模板格式错误");
  }
};

const onQueryTypeChange = () => {
  if (queryType.value === "dsl") {
    // 切换到DSL时，将可视化查询转换为DSL
    try {
      const query = buildVisualQuery();
      dslQuery.value = JSON.stringify(query, null, 2);
    } catch (error) {
      console.error("转换查询失败:", error);
    }
  }
};

const onIndicesChange = () => {
  // 加载选中索引的字段信息
  loadFieldsForIndices();
};

const onFieldChange = (condition) => {
  // 重置操作符和值
  condition.operator = "";
  condition.value = "";
  condition.rangeFrom = "";
  condition.rangeTo = "";
};

const addCondition = () => {
  visualQuery.conditions.push({
    logic: "must",
    field: "",
    operator: "",
    value: "",
    rangeFrom: "",
    rangeTo: "",
    _locked: false,
    _lockType: null,
  });
};

const removeCondition = (index) => {
  visualQuery.conditions.splice(index, 1);
};

const addSort = () => {
  visualQuery.sorts.push({
    field: "",
    order: "asc",
  });
};

const removeSort = (index) => {
  visualQuery.sorts.splice(index, 1);
};

const addAggregation = () => {
  visualQuery.aggregations.push({
    name: "",
    type: "terms",
    field: "",
    params: {
      size: 10,
      calendar_interval: "1d",
      interval: 1,
      ranges: [],
    },
  });
};

const removeAggregation = (index) => {
  visualQuery.aggregations.splice(index, 1);
};

const onAggregationTypeChange = (agg) => {
  // 重置参数
  agg.params = {
    size: 10,
    calendar_interval: "1d",
    interval: 1,
    ranges: [],
  };
};

const addRange = (agg) => {
  if (!agg.params.ranges) {
    agg.params.ranges = [];
  }
  agg.params.ranges.push({
    from: 0,
    to: 100,
  });
};

const removeRange = (agg, rangeIndex) => {
  agg.params.ranges.splice(rangeIndex, 1);
};

const getAvailableOperators = (fieldName) => {
  const field = esQueryConfig.availableFields.find((f) => f.name === fieldName);
  if (!field) return [];

  const operators = [
    { label: "等于", value: "term" },
    { label: "包含", value: "match" },
    { label: "前缀", value: "prefix" },
    { label: "通配符", value: "wildcard" },
    { label: "存在", value: "exists" },
  ];

  if (["integer", "long", "float", "double", "date"].includes(field.type)) {
    operators.push(
      { label: "范围", value: "range" },
      { label: "大于", value: "gt" },
      { label: "小于", value: "lt" },
      { label: "大于等于", value: "gte" },
      { label: "小于等于", value: "lte" },
    );
  }

  return operators;
};

const getLockTypeTagType = (lockType) => {
  switch (lockType) {
    case "full":
      return "danger";
    case "field":
      return "warning";
    case "operator":
      return "info";
    case "value":
      return "success";
    default:
      return "info";
  }
};

const getLockTypeLabel = (lockType) => {
  switch (lockType) {
    case "full":
      return "完全锁定";
    case "field":
      return "字段锁定";
    case "operator":
      return "操作符锁定";
    case "value":
      return "值锁定";
    default:
      return "锁定";
  }
};

const buildVisualQuery = () => {
  const query = {
    query: {
      bool: {
        must: [],
        should: [],
        must_not: [],
      },
    },
  };

  // 构建查询条件
  visualQuery.conditions.forEach((condition) => {
    if (!condition.field || !condition.operator) return;

    let clause = {};

    // 获取字段信息，判断是否需要添加 .keyword 后缀
    const fieldInfo = esQueryConfig.availableFields.find(
      (f) => f.name === condition.field,
    );
    let fieldName = condition.field;

    // 对于 text 类型字段，在 term 查询时自动添加 .keyword 后缀
    if (
      fieldInfo &&
      fieldInfo.type === "text" &&
      condition.operator === "term"
    ) {
      fieldName = `${condition.field}.keyword`;
      console.log(
        `🔧 为 text 字段 ${condition.field} 的 term 查询添加 .keyword 后缀: ${fieldName}`,
      );
    }

    switch (condition.operator) {
      case "term":
        clause = { term: { [fieldName]: condition.value } };
        break;
      case "match":
        clause = { match: { [condition.field]: condition.value } };
        break;
      case "prefix":
        // prefix 查询对 text 字段也需要使用 .keyword 后缀
        if (fieldInfo && fieldInfo.type === "text") {
          fieldName = `${condition.field}.keyword`;
          console.log(
            `🔧 为 text 字段 ${condition.field} 的 prefix 查询添加 .keyword 后缀: ${fieldName}`,
          );
        }
        clause = { prefix: { [fieldName]: condition.value } };
        break;
      case "wildcard":
        // wildcard 查询对 text 字段也需要使用 .keyword 后缀
        if (fieldInfo && fieldInfo.type === "text") {
          fieldName = `${condition.field}.keyword`;
          console.log(
            `🔧 为 text 字段 ${condition.field} 的 wildcard 查询添加 .keyword 后缀: ${fieldName}`,
          );
        }
        clause = { wildcard: { [fieldName]: condition.value } };
        break;
      case "exists":
        clause = { exists: { field: condition.field } };
        break;
      case "range":
        const rangeClause = {};
        if (condition.rangeFrom) rangeClause.gte = condition.rangeFrom;
        if (condition.rangeTo) rangeClause.lte = condition.rangeTo;
        clause = { range: { [condition.field]: rangeClause } };
        break;
      case "gt":
        clause = { range: { [condition.field]: { gt: condition.value } } };
        break;
      case "lt":
        clause = { range: { [condition.field]: { lt: condition.value } } };
        break;
      case "gte":
        clause = { range: { [condition.field]: { gte: condition.value } } };
        break;
      case "lte":
        clause = { range: { [condition.field]: { lte: condition.value } } };
        break;
    }

    if (Object.keys(clause).length > 0) {
      const logic = condition.logic || "must";
      query.query.bool[logic].push(clause);
    }
  });

  // 如果没有查询条件，使用match_all
  if (
    query.query.bool.must.length === 0 &&
    query.query.bool.should.length === 0 &&
    query.query.bool.must_not.length === 0
  ) {
    query.query = { match_all: {} };
  }

  // 添加字段选择
  if (visualQuery.fields.length > 0) {
    query._source = visualQuery.fields;
  }

  // 添加排序
  if (visualQuery.sorts.length > 0) {
    query.sort = visualQuery.sorts.map((sort) => {
      // 获取字段信息，判断是否需要添加 .keyword 后缀
      const fieldInfo = esQueryConfig.availableFields.find(
        (f) => f.name === sort.field,
      );
      let fieldName = sort.field;

      // 对于 text 类型字段，在排序时自动添加 .keyword 后缀
      if (fieldInfo && fieldInfo.type === "text") {
        fieldName = `${sort.field}.keyword`;
        console.log(
          `🔧 为 text 字段 ${sort.field} 添加 .keyword 后缀: ${fieldName}`,
        );
      }

      return {
        [fieldName]: { order: sort.order },
      };
    });
  }

  // 添加分页
  query.from = visualQuery.from;
  query.size = visualQuery.size;

  // 添加聚合查询
  if (visualQuery.aggregations.length > 0) {
    query.aggs = {};

    visualQuery.aggregations.forEach((agg) => {
      if (!agg.name || !agg.type || !agg.field) return;

      let aggConfig = {};

      // 获取字段信息，判断是否需要添加 .keyword 后缀
      const fieldInfo = esQueryConfig.availableFields.find(
        (f) => f.name === agg.field,
      );
      let fieldName = agg.field;

      // 对于 text 类型字段，在聚合时自动添加 .keyword 后缀
      if (fieldInfo && fieldInfo.type === "text") {
        fieldName = `${agg.field}.keyword`;
        console.log(
          `🔧 为 text 字段 ${agg.field} 添加 .keyword 后缀: ${fieldName}`,
        );
      }

      switch (agg.type) {
        case "value_count":
        case "sum":
        case "avg":
        case "max":
        case "min":
          aggConfig = {
            [agg.type]: {
              field: fieldName,
            },
          };
          break;
        case "terms":
          aggConfig = {
            terms: {
              field: fieldName,
              size: agg.params.size || 10,
            },
          };
          break;
        case "date_histogram":
          aggConfig = {
            date_histogram: {
              field: fieldName,
              calendar_interval: agg.params.calendar_interval || "1d",
            },
          };
          break;
        case "histogram":
          aggConfig = {
            histogram: {
              field: fieldName,
              interval: agg.params.interval || 1,
            },
          };
          break;
        case "range":
          if (agg.params.ranges && agg.params.ranges.length > 0) {
            aggConfig = {
              range: {
                field: fieldName,
                ranges: agg.params.ranges.map((range) => ({
                  from: range.from,
                  to: range.to,
                })),
              },
            };
          }
          break;
      }

      if (Object.keys(aggConfig).length > 0) {
        query.aggs[agg.name] = aggConfig;
      }
    });
  }

  return query;
};

const buildQuery = () => {
  if (queryType.value === "visual") {
    return buildVisualQuery();
  } else {
    return JSON.parse(dslQuery.value);
  }
};

const formatDSL = () => {
  try {
    const parsed = JSON.parse(dslQuery.value);
    dslQuery.value = JSON.stringify(parsed, null, 2);
    dslValidationError.value = "";
  } catch (error) {
    dslValidationError.value = "JSON格式错误: " + error.message;
  }
};

const validateDSL = () => {
  try {
    JSON.parse(dslQuery.value);
    dslValidationError.value = "";
    ElMessage.success("DSL格式正确");
  } catch (error) {
    dslValidationError.value = "JSON格式错误: " + error.message;
    ElMessage.error("DSL格式错误");
  }
};

const onDSLChange = () => {
  dslValidationError.value = "";
};

const copyQuery = async () => {
  try {
    await navigator.clipboard.writeText(formattedQuery.value);
    ElMessage.success("查询已复制到剪贴板");
  } catch (error) {
    ElMessage.error("复制失败");
  }
};

const executeESQuery = async () => {
  if (!canExecuteQuery.value) {
    ElMessage.warning("请先选择数据源和索引");
    return;
  }

  querying.value = true;
  try {
    const fullQuery = buildQuery();

    // 分离查询的各个部分
    let queryPart, sortPart, sourcePart, sizePart, fromPart, aggsPart;

    if (queryType.value === "visual") {
      // 可视化查询：从buildVisualQuery返回的完整对象中提取各部分
      queryPart = fullQuery.query;
      sortPart = fullQuery.sort;
      sourcePart = fullQuery._source;
      sizePart = fullQuery.size || 100;
      fromPart = fullQuery.from || 0;
      aggsPart = fullQuery.aggs;
    } else {
      // DSL查询：解析JSON字符串
      const parsedQuery =
        typeof fullQuery === "string" ? JSON.parse(fullQuery) : fullQuery;
      queryPart = parsedQuery.query || parsedQuery;
      sortPart = parsedQuery.sort;
      sourcePart = parsedQuery._source;
      sizePart = parsedQuery.size || 100;
      fromPart = parsedQuery.from || 0;
      aggsPart = parsedQuery.aggs;
    }

    // 构建标准的ES查询请求
    const queryRequest = {
      datasourceId: parseInt(esQueryConfig.datasourceId),
      index:
        queryType.value === "visual"
          ? Array.isArray(visualQuery.indices)
            ? visualQuery.indices
            : [visualQuery.indices]
          : [esQueryConfig.selectedIndex],
      query: queryPart, // 只传递query部分
      size: sizePart,
      from: fromPart,
    };

    // 添加可选参数
    if (sortPart) {
      queryRequest.sort = sortPart;
    }

    if (sourcePart) {
      queryRequest._source = sourcePart;
    }

    if (aggsPart) {
      queryRequest.aggs = aggsPart;
    }

    console.log("执行ES查询:", queryRequest);

    const response = await executeESQueryAPI(queryRequest);

    console.log("ES查询响应:", response);

    if (response.data) {
      queryResults.value = response.data;
      emit("query-executed", response.data);
      ElMessage.success("查询执行成功");
    } else {
      ElMessage.error("查询执行失败：未返回数据");
    }
  } catch (error) {
    console.error("查询执行失败:", error);
    ElMessage.error(
      "查询执行失败: " + (error.response?.data?.detail || error.message),
    );
  } finally {
    querying.value = false;
  }
};

const clearESQuery = () => {
  // 重置可视化查询
  visualQuery.indices = [];
  visualQuery.fields = [];
  visualQuery.conditions = [];
  visualQuery.sorts = [];
  visualQuery.aggregations = [];
  visualQuery.from = 0;
  visualQuery.size = 20;

  // 重置DSL查询
  dslQuery.value = "";
  dslValidationError.value = "";

  // 清除结果
  queryResults.value = null;
  selectedTemplateId.value = "";

  // 重置当前模板ID，回到新建状态
  currentTemplateId.value = null;

  ElMessage.success("查询已清空");
};

const saveESQuery = () => {
  if (!hasValidQuery.value && !formattedQuery.value) {
    ElMessage.warning("请先构建查询");
    return;
  }

  // saveForm.name = ''
  // saveForm.description = ''
  saveDialogVisible.value = true;
};

/**
 * 确认保存查询模板
 */
const confirmSaveQuery = async () => {
  if (!saveForm.name.trim()) {
    ElMessage.warning("请输入模板名称");
    return;
  }

  saving.value = true;
  try {
    // 构建保存数据，匹配后端ESTemplateRequest结构
    let queryObject = {};
    try {
      // 将JSON字符串解析为对象，后端期望字典类型
      queryObject = formattedQuery.value
        ? JSON.parse(formattedQuery.value)
        : {};
    } catch (error) {
      console.error("解析查询JSON失败:", error);
      ElMessage.error("查询格式错误，请检查查询条件");
      saving.value = false;
      return;
    }

    const templateData = {
      name: saveForm.name,
      description: saveForm.description,
      datasourceId: esQueryConfig.datasourceId, // 后端要求的字段名
      indices:
        queryType.value === "visual"
          ? Array.isArray(visualQuery.indices)
            ? visualQuery.indices
            : [visualQuery.indices]
          : esQueryConfig.selectedIndex
            ? [esQueryConfig.selectedIndex]
            : [], // 后端要求的字段名和格式
      query: queryObject, // 解析后的查询对象，而不是字符串
      tags: [],
      dataResourceId: props.dataResourceId, // 添加数据资源ID字段，使用驼峰命名
      // 条件锁定相关配置（可选）
      conditionLockTypes: esQueryConfig.lockedConditions
        ? esQueryConfig.lockedConditions.reduce((acc, condition) => {
            acc[condition.field] = "locked";
            return acc;
          }, {})
        : undefined,
      conditionRanges: undefined,
      allowedOperators: undefined,
    };

    let result;
    // 根据currentTemplateId判断是创建还是更新
    if (currentTemplateId.value) {
      // 更新现有模板
      console.log("更新ES查询模板，ID:", currentTemplateId.value);
      result = await updateESQueryTemplate(
        currentTemplateId.value,
        templateData,
      );
      ElMessage.success("查询模板更新成功");
    } else {
      // 创建新模板
      console.log("创建新的ES查询模板");
      result = await saveESQueryTemplate(templateData);

      // 保存成功后，设置当前模板ID为编辑状态
      if (result && result.data && result.data.id) {
        currentTemplateId.value = result.data.id;
        saveForm.name = result.data.name;
        saveForm.description = result.data.description;
        console.log(
          "保存成功，设置当前模板ID为编辑状态:",
          currentTemplateId.value,
        );
      }
      ElMessage.success("查询模板保存成功");
    }

    // 保存成功后，更新saveForm中的模板信息，确保下次打开对话框时显示正确的信息
    if (result && result.data) {
      // 如果后端返回了更新后的模板信息，使用返回的信息
      if (result.data.name) {
        saveForm.name = result.data.name;
      }
      if (result.data.description !== undefined) {
        saveForm.description = result.data.description || "";
      }
    }

    saveDialogVisible.value = false;
    emit("query-saved", result);
    await loadTemplates(); // 重新加载模板列表
  } catch (error) {
    console.error("保存查询模板失败:", error);
    ElMessage.error("保存失败");
  } finally {
    saving.value = false;
  }
};

/**
 * 添加到资源包
 */
const addToResourcePackage = () => {
  if (!hasValidQuery.value) {
    ElMessage.warning("请先执行查询");
    return;
  }

  if (!esQueryConfig.datasourceId) {
    ElMessage.warning("请先选择数据源");
    return;
  }

  if (props.isInResourcePackage) {
    // 更新模式：初始化表单为当前资源包的数据
    resourcePackageForm.name = props.resourcePackageName || "";
    resourcePackageForm.description = ""; // 可以从props中获取，如果有的话
    resourcePackageForm.tags = []; // 可以从props中获取，如果有的话
  } else {
    // 创建模式：重置表单
    resourcePackageForm.name = "";
    resourcePackageForm.description = "";
    resourcePackageForm.tags = [];
  }

  // 显示资源包创建对话框
  resourcePackageVisible.value = true;
};

/**
 * 确认添加到资源包
 */
const confirmAddToResourcePackage = async () => {
  if (!resourcePackageForm.name.trim()) {
    ElMessage.warning("请输入资源包名称");
    return;
  }

  try {
    creatingResourcePackage.value = true;

    // 构建资源包数据
    const packageData = {
      name: resourcePackageForm.name,
      description: resourcePackageForm.description,
      type: PackageType.ELASTICSEARCH,
      datasource_id: parseInt(esQueryConfig.datasourceId),
      template_type: "elasticsearch",
      template_id: currentTemplateId.value, // 使用当前模板ID而不是选中的模板ID
      dynamic_params: {},
      resource_id: props.dataResourceId ? parseInt(props.dataResourceId) : null,
      tags: resourcePackageForm.tags,
      is_active: true,
    };

    console.log("📦 构建ES资源包数据:", packageData);
    console.log("🔍 当前模板ID:", currentTemplateId.value);
    console.log("🔍 选中模板ID:", selectedTemplateId.value);

    if (props.isInResourcePackage && props.resourcePackageId) {
      // 更新模式
      await resourcePackageApi.update(props.resourcePackageId, packageData);
      ElMessage.success("资源包更新成功");

      // 触发更新事件通知父组件
      emit("update-resource-package", {
        id: props.resourcePackageId,
        ...packageData,
      });
    } else {
      // 创建模式
      await resourcePackageApi.create(packageData);
      ElMessage.success("资源包创建成功");

      // 触发创建事件通知父组件
      emit("add-to-resource-package", packageData);
    }

    resourcePackageVisible.value = false;
  } catch (error) {
    console.error(
      props.isInResourcePackage ? "更新资源包失败:" : "创建资源包失败:",
      error,
    );
    ElMessage.error(
      props.isInResourcePackage ? "更新资源包失败" : "创建资源包失败",
    );
  } finally {
    creatingResourcePackage.value = false;
  }
};

const handleSizeChange = (newSize) => {
  pageSize.value = newSize;
  visualQuery.size = newSize;
  if (queryType.value === "visual") {
    executeESQuery();
  }
};

const handleCurrentChange = (newPage) => {
  currentPage.value = newPage;
  visualQuery.from = (newPage - 1) * pageSize.value;
  if (queryType.value === "visual") {
    executeESQuery();
  }
};

// 公开方法
const loadQuery = (query) => {
  try {
    console.log("🔄 loadQuery 开始处理查询:", query);

    // 重置可视化查询状态
    visualQuery.conditions = [];
    visualQuery.sorts = [];
    visualQuery.aggregations = [];
    visualQuery.fields = [];

    if (query.query) {
      // 这是一个完整的ES查询
      if (query.query.bool) {
        // 解析bool查询到可视化界面
        queryType.value = "visual";

        // 解析must条件
        if (query.query.bool.must) {
          query.query.bool.must.forEach((clause) => {
            const condition = parseClauseToCondition(clause, "must");
            if (condition) visualQuery.conditions.push(condition);
          });
        }

        // 解析should条件
        if (query.query.bool.should) {
          query.query.bool.should.forEach((clause) => {
            const condition = parseClauseToCondition(clause, "should");
            if (condition) visualQuery.conditions.push(condition);
          });
        }

        // 解析must_not条件
        if (query.query.bool.must_not) {
          query.query.bool.must_not.forEach((clause) => {
            const condition = parseClauseToCondition(clause, "must_not");
            if (condition) visualQuery.conditions.push(condition);
          });
        }
      } else if (query.query.match_all) {
        // match_all查询，使用可视化模式但不添加任何条件
        queryType.value = "visual";
        console.log("📋 检测到 match_all 查询，使用可视化模式，无查询条件");
      } else {
        // 其他查询类型，使用DSL模式
        queryType.value = "dsl";
        dslQuery.value = JSON.stringify(query, null, 2);
        console.log("📋 使用DSL模式处理复杂查询");
        return; // DSL模式下不需要继续解析其他属性
      }

      // 解析其他属性
      if (query._source) {
        visualQuery.fields = Array.isArray(query._source) ? query._source : [];
        console.log("📋 还原字段选择:", visualQuery.fields);
      }

      if (query.sort) {
        visualQuery.sorts = query.sort.map((sortItem) => {
          const field = Object.keys(sortItem)[0];
          const order = sortItem[field].order || "asc";
          return { field, order };
        });
        console.log("📋 还原排序设置:", visualQuery.sorts);
      }

      // 解析聚合查询
      if (query.aggs) {
        visualQuery.aggregations = parseAggregations(query.aggs);
        console.log("📋 还原聚合查询:", visualQuery.aggregations);
      }

      if (query.from !== undefined) {
        visualQuery.from = query.from;
        console.log("📋 还原分页起始位置:", visualQuery.from);
      }

      if (query.size !== undefined) {
        visualQuery.size = query.size;
        console.log("📋 还原分页大小:", visualQuery.size);
      }
    }

    console.log("✅ loadQuery 完成，最终状态:", {
      queryType: queryType.value,
      conditions: visualQuery.conditions.length,
      aggregations: visualQuery.aggregations.length,
      sorts: visualQuery.sorts.length,
      fields: visualQuery.fields.length,
    });
  } catch (error) {
    console.error("加载查询失败:", error);
    ElMessage.error("查询格式错误");
  }
};

const parseClauseToCondition = (clause, logic) => {
  const condition = {
    logic,
    field: "",
    operator: "",
    value: "",
    rangeFrom: "",
    rangeTo: "",
    _locked: false,
    _lockType: null,
  };

  if (clause.term) {
    const field = Object.keys(clause.term)[0];
    condition.field = field;
    condition.operator = "term";
    condition.value = clause.term[field];
  } else if (clause.match) {
    const field = Object.keys(clause.match)[0];
    condition.field = field;
    condition.operator = "match";
    condition.value = clause.match[field];
  } else if (clause.prefix) {
    const field = Object.keys(clause.prefix)[0];
    condition.field = field;
    condition.operator = "prefix";
    condition.value = clause.prefix[field];
  } else if (clause.wildcard) {
    const field = Object.keys(clause.wildcard)[0];
    condition.field = field;
    condition.operator = "wildcard";
    condition.value = clause.wildcard[field];
  } else if (clause.exists) {
    condition.field = clause.exists.field;
    condition.operator = "exists";
  } else if (clause.range) {
    const field = Object.keys(clause.range)[0];
    const rangeValue = clause.range[field];
    condition.field = field;

    if (rangeValue.gte !== undefined && rangeValue.lte !== undefined) {
      condition.operator = "range";
      condition.rangeFrom = rangeValue.gte;
      condition.rangeTo = rangeValue.lte;
    } else if (rangeValue.gt !== undefined) {
      condition.operator = "gt";
      condition.value = rangeValue.gt;
    } else if (rangeValue.lt !== undefined) {
      condition.operator = "lt";
      condition.value = rangeValue.lt;
    } else if (rangeValue.gte !== undefined) {
      condition.operator = "gte";
      condition.value = rangeValue.gte;
    } else if (rangeValue.lte !== undefined) {
      condition.operator = "lte";
      condition.value = rangeValue.lte;
    }
  }

  return condition.field ? condition : null;
};

/**
 * 解析ES聚合查询到可视化聚合配置
 * @param {Object} aggs - ES聚合查询对象
 * @returns {Array} 可视化聚合配置数组
 */
const parseAggregations = (aggs) => {
  const aggregations = [];

  for (const [aggName, aggConfig] of Object.entries(aggs)) {
    const aggregation = {
      name: aggName,
      type: "",
      field: "",
      params: {},
    };

    // 确定聚合类型
    if (aggConfig.terms) {
      aggregation.type = "terms";
      aggregation.field = aggConfig.terms.field;
      aggregation.params = {
        size: aggConfig.terms.size || 10,
      };
    } else if (aggConfig.date_histogram) {
      aggregation.type = "date_histogram";
      aggregation.field = aggConfig.date_histogram.field;
      aggregation.params = {
        calendar_interval:
          aggConfig.date_histogram.calendar_interval ||
          aggConfig.date_histogram.interval ||
          "1d",
      };
    } else if (aggConfig.histogram) {
      aggregation.type = "histogram";
      aggregation.field = aggConfig.histogram.field;
      aggregation.params = {
        interval: aggConfig.histogram.interval || 1,
      };
    } else if (aggConfig.range) {
      aggregation.type = "range";
      aggregation.field = aggConfig.range.field;
      aggregation.params = {
        ranges: aggConfig.range.ranges || [],
      };
    } else if (aggConfig.sum) {
      aggregation.type = "sum";
      aggregation.field = aggConfig.sum.field;
      aggregation.params = {};
    } else if (aggConfig.avg) {
      aggregation.type = "avg";
      aggregation.field = aggConfig.avg.field;
      aggregation.params = {};
    } else if (aggConfig.max) {
      aggregation.type = "max";
      aggregation.field = aggConfig.max.field;
      aggregation.params = {};
    } else if (aggConfig.min) {
      aggregation.type = "min";
      aggregation.field = aggConfig.min.field;
      aggregation.params = {};
    } else if (aggConfig.value_count) {
      aggregation.type = "value_count";
      aggregation.field = aggConfig.value_count.field;
      aggregation.params = {};
    }

    if (aggregation.type) {
      aggregations.push(aggregation);
      console.log(
        `📊 解析聚合: ${aggName} (${aggregation.type}) -> ${aggregation.field}`,
      );
    } else {
      console.warn(`⚠️ 未识别的聚合类型:`, aggConfig);
    }
  }

  return aggregations;
};

const clearQuery = () => {
  clearESQuery();
};

/**
 * 格式化字段值显示
 * 处理不同类型的字段值，使其在表格中更好地显示
 */
const formatFieldValue = (value) => {
  if (value === null || value === undefined) {
    return "-";
  }

  if (typeof value === "object") {
    if (Array.isArray(value)) {
      // 数组类型，显示前几个元素
      if (value.length === 0) return "[]";
      if (value.length <= 3) {
        return value
          .map((v) => (typeof v === "object" ? JSON.stringify(v) : String(v)))
          .join(", ");
      }
      return `[${value
        .slice(0, 3)
        .map((v) => (typeof v === "object" ? JSON.stringify(v) : String(v)))
        .join(", ")}...] (${value.length}项)`;
    } else {
      // 对象类型，显示JSON字符串（截断）
      const jsonStr = JSON.stringify(value);
      return jsonStr.length > 100 ? jsonStr.substring(0, 100) + "..." : jsonStr;
    }
  }

  if (typeof value === "string") {
    // 字符串类型，如果太长则截断
    return value.length > 100 ? value.substring(0, 100) + "..." : value;
  }

  if (typeof value === "number") {
    // 数字类型，保留合理的小数位数
    return Number.isInteger(value) ? value : value.toFixed(3);
  }

  if (typeof value === "boolean") {
    return value ? "是" : "否";
  }

  return String(value);
};

/**
 * 格式化字段值并添加注释
 * 在字段值后面添加字段映射中的注释信息
 */
const formatFieldValueWithComment = (value, fieldName) => {
  const formattedValue = formatFieldValue(value);

  // 查找字段映射中的注释
  const fieldMapping = esQueryConfig.availableFields.find(
    (field) => field.name === fieldName,
  );
  if (
    fieldMapping &&
    fieldMapping.comment &&
    fieldMapping.comment !== fieldName
  ) {
    return `${formattedValue} (${fieldMapping.comment})`;
  }

  return formattedValue;
};

/**
 * 切换文档展开状态
 */
const toggleDocumentExpand = (docId) => {
  if (expandedDocs.value.has(docId)) {
    expandedDocs.value.delete(docId);
  } else {
    expandedDocs.value.add(docId);
  }
};

/**
 * 切换聚合结果展开状态
 */
const toggleAggregationsExpand = () => {
  aggregationsExpanded.value = !aggregationsExpanded.value;
};

/**
 * 获取聚合结果摘要信息
 * @param {Object} agg - 聚合结果对象
 * @returns {String} 聚合摘要文本
 */
const getAggregationSummary = (agg) => {
  if (agg.buckets && Array.isArray(agg.buckets)) {
    // Terms 聚合
    const totalBuckets = agg.buckets.length;
    const totalDocs = agg.buckets.reduce(
      (sum, bucket) => sum + bucket.doc_count,
      0,
    );
    return `${totalBuckets}个分类, ${totalDocs}个文档`;
  } else if (agg.value !== undefined) {
    // 数值聚合 (sum, avg, max, min, etc.)
    return `值: ${agg.value}`;
  } else if (agg.doc_count !== undefined) {
    // 简单计数聚合
    return `${agg.doc_count}个文档`;
  } else {
    // 其他类型聚合
    return "复合聚合";
  }
};

/**
 * 导出查询结果
 */
const exportResults = () => {
  if (!queryResults.value?.hits?.hits) {
    ElMessage.warning("没有可导出的查询结果");
    return;
  }

  try {
    // 准备导出数据
    const exportData = queryResults.value.hits.hits.map((hit) => {
      const row = {
        _id: hit._id,
        ...hit._source,
      };
      return row;
    });

    // 转换为CSV格式
    const headers = ["_id", ...documentFields.value];
    const csvContent = [
      headers.join(","),
      ...exportData.map((row) =>
        headers
          .map((header) => {
            const value = row[header];
            if (value === null || value === undefined) return "";
            if (typeof value === "object")
              return `"${JSON.stringify(value).replace(/"/g, '""')}"`;
            if (typeof value === "string" && value.includes(","))
              return `"${value.replace(/"/g, '""')}"`;
            return value;
          })
          .join(","),
      ),
    ].join("\n");

    // 下载文件
    const blob = new Blob([csvContent], { type: "text/csv;charset=utf-8;" });
    const link = document.createElement("a");
    const url = URL.createObjectURL(blob);
    link.setAttribute("href", url);
    link.setAttribute(
      "download",
      `es_query_results_${new Date().getTime()}.csv`,
    );
    link.style.visibility = "hidden";
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);

    ElMessage.success("查询结果已导出");
  } catch (error) {
    console.error("导出失败:", error);
    ElMessage.error("导出失败: " + error.message);
  }
};

// 生命周期
onMounted(async () => {
  console.log("🚀 ESQueryBuilder onMounted 开始，props:", {
    initialDatasourceId: props.initialDatasourceId,
    dataResourceId: props.dataResourceId,
    initialIndices: props.initialIndices,
    initialQuery: props.initialQuery,
  });

  await loadESDatasources();

  if (props.initialDatasourceId) {
    console.log("📡 有初始数据源ID，调用 onEsDatasourceChange");
    await onEsDatasourceChange();
  } else if (props.dataResourceId) {
    console.log("📡 没有初始数据源但有dataResourceId，直接加载模板");
    // 即使没有初始数据源，如果有dataResourceId也要加载模板
    await loadTemplates();
  } else {
    console.log("⚠️ 既没有初始数据源也没有dataResourceId");
  }

  if (Object.keys(props.initialQuery).length > 0) {
    loadQuery(props.initialQuery);
  }
});

// 监听数据源变化
watch(
  () => esQueryConfig.datasourceId,
  () => {
    if (esQueryConfig.datasourceId) {
      onEsDatasourceChange();
    }
  },
);

// 监听数据资源ID变化，自动加载模板
watch(
  () => props.dataResourceId,
  (newDataResourceId) => {
    if (newDataResourceId) {
      loadTemplates();
    }
  },
);

// 暴露方法给父组件
defineExpose({
  loadQuery,
  clearQuery,
  executeQuery: executeESQuery,
  getQuery: () => buildQuery(),
  getSelectedIndices: () =>
    queryType.value === "visual"
      ? Array.isArray(visualQuery.indices)
        ? visualQuery.indices
        : [visualQuery.indices]
      : esQueryConfig.selectedIndex
        ? [esQueryConfig.selectedIndex]
        : [],
});
</script>

<style scoped>
.es-query-builder {
  width: 100%;
}

.query-card {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-actions {
  display: flex;
  gap: 8px;
}

.es-datasource-selector {
  margin-bottom: 20px;
}

.query-type-selector {
  margin-bottom: 20px;
  text-align: center;
}

.visual-query-builder {
  space-y: 20px;
}

.query-section {
  margin-bottom: 20px;
  padding: 16px;
  border: 1px solid #e4e7ed;
  border-radius: 6px;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.section-label {
  font-weight: 600;
  color: #303133;
}

.empty-conditions,
.empty-sorts {
  text-align: center;
  padding: 20px;
  color: #909399;
}

.conditions-list,
.sorts-list {
  space-y: 12px;
}

.condition-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  border: 1px solid #e4e7ed;
  border-radius: 6px;
  position: relative;
}

.condition-item.locked-condition {
  background-color: #fdf6ec;
  border-color: #f5dab1;
}

.lock-indicator {
  position: absolute;
  top: -8px;
  right: 8px;
  display: flex;
  align-items: center;
  gap: 4px;
}

.lock-icon {
  color: #e6a23c;
}

.lock-type-tag {
  font-size: 10px;
}

.logic-operator {
  min-width: 80px;
}

.condition-config {
  display: flex;
  align-items: center;
  gap: 8px;
  flex: 1;
}

.value-input {
  min-width: 200px;
}

.range-input {
  display: flex;
  align-items: center;
  gap: 8px;
}

.range-separator {
  color: #909399;
}

.condition-actions {
  display: flex;
  gap: 4px;
}

.sort-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 8px;
  border: 1px solid #e4e7ed;
  border-radius: 4px;
}

.dsl-query-editor {
  margin-bottom: 20px;
}

.editor-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.editor-actions {
  display: flex;
  gap: 8px;
}

.dsl-editor {
  border: 1px solid #dcdfe6;
  border-radius: 6px;
  overflow: hidden;
}

.dsl-textarea {
  width: 100%;
  min-height: 300px;
  padding: 12px;
  border: none;
  outline: none;
  font-family: "Monaco", "Menlo", "Ubuntu Mono", monospace;
  font-size: 14px;
  line-height: 1.5;
  resize: vertical;
}

.validation-error {
  margin-top: 12px;
}

.query-preview {
  margin-bottom: 20px;
}

.preview-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.preview-content {
  border: 1px solid #dcdfe6;
  border-radius: 6px;
  overflow: hidden;
}

.query-json {
  margin: 0;
  padding: 12px;
  background-color: #f5f7fa;
  font-family: "Monaco", "Menlo", "Ubuntu Mono", monospace;
  font-size: 12px;
  line-height: 1.5;
  overflow-x: auto;
}

.results-card {
  margin-top: 20px;
}

.results-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.results-info {
  display: flex;
  gap: 8px;
}

.results-content {
  max-height: 600px;
  overflow: auto;
}

.document-source {
  max-height: 200px;
  overflow: auto;
}

.document-source pre {
  margin: 0;
  font-size: 12px;
  line-height: 1.4;
}

.pagination-wrapper {
  margin-top: 20px;
  text-align: center;
}

.template-option {
  display: flex;
  flex-direction: column;
}

.template-name {
  font-weight: 600;
}

.template-desc {
  font-size: 12px;
  color: #909399;
}

.query-content {
  max-height: 300px;
  overflow: auto;
  border: 1px solid #dcdfe6;
  border-radius: 4px;
  padding: 12px;
  background-color: #f5f7fa;
}

.current-indices {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
  align-items: center;
}

.query-content pre {
  margin: 0;
  font-family: "Monaco", "Menlo", "Ubuntu Mono", monospace;
  font-size: 12px;
  line-height: 1.5;
}

.dialog-footer {
  text-align: right;
}

/* 查询结果显示样式 */
.results-content {
  margin-top: 16px;
}

.field-value {
  max-width: 200px;
  word-break: break-word;
  line-height: 1.4;
}

.document-source {
  position: relative;
}

.expanded-document {
  margin-top: 8px;
  max-height: 300px;
  overflow: auto;
  border: 1px solid #e4e7ed;
  border-radius: 4px;
  background-color: #f8f9fa;
}

.expanded-document pre {
  margin: 0;
  padding: 12px;
  font-family: "Monaco", "Menlo", "Ubuntu Mono", monospace;
  font-size: 12px;
  line-height: 1.4;
  color: #2c3e50;
}

.results-controls {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin: 16px 0;
  padding: 12px;
  background-color: #f8f9fa;
  border-radius: 4px;
  border: 1px solid #e4e7ed;
}

.results-controls .el-checkbox {
  margin-right: auto;
}

/* 表格样式优化 */
.el-table .el-table__cell {
  padding: 8px 12px;
}

.el-table .field-value {
  font-size: 13px;
  color: #606266;
}

.el-table .el-tag {
  font-weight: 500;
}

/* 聚合结果卡片样式 */
.aggregations-card {
  margin-bottom: 16px;
}

.aggregations-header {
  display: flex;
  align-items: center;
  gap: 8px;
}

.aggregations-header .el-icon {
  color: #409eff;
}

.aggregations-content {
  margin-top: 16px;
}

.aggregations-summary {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 16px;
}

.agg-tag {
  font-size: 12px;
}

.aggregations-detail {
  border-top: 1px solid #ebeef5;
  padding-top: 16px;
}

.aggregation-item {
  margin-bottom: 24px;
}

.aggregation-item:last-child {
  margin-bottom: 0;
}

.aggregation-title {
  margin: 0 0 12px 0;
  font-size: 14px;
  font-weight: 600;
  color: #303133;
}

.aggregation-data {
  background: #fafafa;
  border-radius: 4px;
  padding: 12px;
}

.bucket-cards {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  margin-top: 8px;
}

.bucket-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 12px 16px;
  background: #ffffff;
  border: 1px solid #e4e7ed;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  transition: all 0.3s ease;
  min-width: 120px;
  cursor: default;
}

.bucket-card:hover {
  border-color: #409eff;
  box-shadow: 0 4px 8px rgba(64, 158, 255, 0.2);
  transform: translateY(-2px);
}

.bucket-name {
  font-size: 13px;
  font-weight: 500;
  color: #303133;
  text-align: center;
  margin-bottom: 6px;
  word-break: break-word;
  line-height: 1.4;
}

.bucket-count {
  font-size: 18px;
  font-weight: 600;
  color: #409eff;
  text-align: center;
}

.other-docs {
  margin-top: 8px;
  text-align: center;
}

.metric-value {
  text-align: center;
}

.raw-aggregation pre {
  margin: 0;
  font-size: 12px;
  color: #606266;
  background: #f5f7fa;
  padding: 8px;
  border-radius: 4px;
  max-height: 200px;
  overflow-y: auto;
}
</style>
