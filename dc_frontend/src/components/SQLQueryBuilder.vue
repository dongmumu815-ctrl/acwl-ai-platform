<template>
  <div class="sql-query-builder">
    <el-card class="query-card">
      <template #header>
        <div class="card-header">
          <span>SQL查询构建器</span>
          <div class="header-actions">
            <el-button @click="clearQuery">
              <el-icon><Delete /></el-icon>
              清空
            </el-button>
            <el-button :disabled="!hasSavePermission" @click="saveQuery">
              <el-icon><Document /></el-icon>
              保存查询
            </el-button>
            <el-button
              type="primary"
              :loading="querying"
              :disabled="!hasQueryPermission"
              @click="executeQuery"
            >
              <el-icon><CaretRight /></el-icon>
              执行查询
            </el-button>
            <el-button
              v-if="!props.isInResourcePackage"
              type="success"
              :disabled="!queryResults.length || !hasQueryPermission"
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

      <div class="query-builder">
        <!-- 数据源选择 -->
        <div class="query-section">
          <h4 class="section-title">数据源</h4>
          <el-row :gutter="20">
            <el-col :span="6">
              <el-form-item label="数据源ID">
                <el-input
                  v-model="queryConfig.datasourceId"
                  placeholder="数据源ID"
                  style="width: 100%"
                  :disabled="true"
                  readonly
                />
              </el-form-item>
            </el-col>
            <el-col :span="6">
              <el-form-item v-if="queryConfig.datasourceId" label="SQL模板">
                <el-select
                  v-model="selectedTemplateId"
                  placeholder="选择SQL模板"
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
            <el-col :span="6">
              <el-form-item
                v-if="queryConfig.datasourceId && availableSchemas.length > 0"
                label="数据库/Schema"
              >
                <el-select
                  v-model="queryConfig.schema"
                  placeholder="请选择Schema"
                  style="width: 100%"
                  filterable
                  @change="onSchemaChange"
                >
                  <el-option
                    v-for="schema in availableSchemas"
                    :key="schema.name"
                    :label="schema.name"
                    :value="schema.name"
                  />
                </el-select>
              </el-form-item>
            </el-col>
            <el-col :span="6">
              <el-form-item v-if="queryConfig.datasourceId" label="数据表/集合">
                <el-select
                  v-model="queryConfig.table"
                  placeholder="请选择数据表"
                  style="width: 100%"
                  filterable
                  @change="onTableChange"
                >
                  <el-option
                    v-for="table in availableTables"
                    :key="table.name"
                    :label="table.name"
                    :value="table.name"
                  >
                    <div class="table-option">
                      <span class="table-name">{{ table.name }}</span>
                      <span class="table-count">({{ table.rowCount }} 行)</span>
                    </div>
                  </el-option>
                </el-select>
              </el-form-item>
            </el-col>
          </el-row>
        </div>

        <!-- 模板条件配置 -->
        <div
          v-if="
            templateConfig &&
            templateConfig.conditions &&
            templateConfig.conditions.length > 0
          "
          class="query-section"
        >
          <h4 class="section-title">模板条件配置</h4>
          <el-row :gutter="16">
            <el-col :span="24">
              <div class="template-conditions">
                <!-- 锁定条件 -->
                <div
                  v-if="
                    templateConfig?.value?.conditions?.filter((c) => c.locked)
                      .length > 0
                  "
                  class="condition-group"
                >
                  <h5 class="condition-group-title locked">
                    <el-icon><Lock /></el-icon>
                    锁定条件
                  </h5>
                  <el-row :gutter="16">
                    <el-col
                      v-for="condition in templateConfig.value.conditions.filter(
                        (c) => c.locked,
                      )"
                      :key="condition.name"
                      :span="8"
                    >
                      <el-form-item
                        :label="condition.label || condition.name"
                        class="locked-condition"
                      >
                        <div class="locked-condition-display">
                          <el-input
                            :value="condition.lockedValue"
                            readonly
                            disabled
                            class="locked-input"
                          >
                            <template #prefix>
                              <el-icon class="lock-icon"><Lock /></el-icon>
                            </template>
                          </el-input>
                          <div
                            v-if="condition.lockedReason"
                            class="locked-reason"
                          >
                            <el-tooltip
                              :content="condition.lockedReason"
                              placement="top"
                            >
                              <el-icon class="info-icon"
                                ><InfoFilled
                              /></el-icon>
                            </el-tooltip>
                          </div>
                        </div>
                      </el-form-item>
                    </el-col>
                  </el-row>
                </div>

                <!-- 必填条件 -->
                <div
                  v-if="
                    templateConfig?.value?.conditions?.filter(
                      (c) => c.required && !c.locked,
                    ).length > 0
                  "
                  class="condition-group"
                >
                  <h5 class="condition-group-title required">
                    <el-icon><Star /></el-icon>
                    必填条件
                  </h5>
                  <el-row :gutter="16">
                    <el-col
                      v-for="condition in templateConfig.value.conditions.filter(
                        (c) => c.required && !c.locked,
                      )"
                      :key="condition.name"
                      :span="8"
                    >
                      <el-form-item
                        :label="condition.label || condition.name"
                        :required="condition.required"
                      >
                        <!-- 文本输入 -->
                        <el-input
                          v-if="condition.type === 'text'"
                          v-model="templateConditionValues[condition.name]"
                          :placeholder="
                            condition.placeholder ||
                            `请输入${condition.label || condition.name}`
                          "
                        />
                        <!-- 数字输入 -->
                        <el-input-number
                          v-else-if="condition.type === 'number'"
                          v-model="templateConditionValues[condition.name]"
                          :placeholder="
                            condition.placeholder ||
                            `请输入${condition.label || condition.name}`
                          "
                          style="width: 100%"
                        />
                        <!-- 日期选择 -->
                        <el-date-picker
                          v-else-if="condition.type === 'date'"
                          v-model="templateConditionValues[condition.name]"
                          type="date"
                          :placeholder="
                            condition.placeholder ||
                            `请选择${condition.label || condition.name}`
                          "
                          style="width: 100%"
                        />
                        <!-- 下拉选择 -->
                        <el-select
                          v-else-if="condition.type === 'select'"
                          v-model="templateConditionValues[condition.name]"
                          :placeholder="
                            condition.placeholder ||
                            `请选择${condition.label || condition.name}`
                          "
                          style="width: 100%"
                          filterable
                        >
                          <el-option
                            v-for="option in condition.options"
                            :key="option.value"
                            :label="option.label"
                            :value="option.value"
                          />
                        </el-select>
                      </el-form-item>
                    </el-col>
                  </el-row>
                </div>

                <!-- 可选条件 -->
                <div
                  v-if="
                    templateConfig?.value?.conditions?.filter(
                      (c) => !c.required && !c.locked,
                    ).length > 0
                  "
                  class="condition-group"
                >
                  <h5 class="condition-group-title optional">
                    <el-icon><CircleCheck /></el-icon>
                    可选条件
                  </h5>
                  <el-row :gutter="16">
                    <el-col
                      v-for="condition in templateConfig.value.conditions.filter(
                        (c) => !c.required && !c.locked,
                      )"
                      :key="condition.name"
                      :span="8"
                    >
                      <el-form-item :label="condition.label || condition.name">
                        <!-- 文本输入 -->
                        <el-input
                          v-if="condition.type === 'text'"
                          v-model="templateConditionValues[condition.name]"
                          :placeholder="
                            condition.placeholder ||
                            `请输入${condition.label || condition.name}`
                          "
                        />
                        <!-- 数字输入 -->
                        <el-input-number
                          v-else-if="condition.type === 'number'"
                          v-model="templateConditionValues[condition.name]"
                          :placeholder="
                            condition.placeholder ||
                            `请输入${condition.label || condition.name}`
                          "
                          style="width: 100%"
                        />
                        <!-- 日期选择 -->
                        <el-date-picker
                          v-else-if="condition.type === 'date'"
                          v-model="templateConditionValues[condition.name]"
                          type="date"
                          :placeholder="
                            condition.placeholder ||
                            `请选择${condition.label || condition.name}`
                          "
                          style="width: 100%"
                        />
                        <!-- 下拉选择 -->
                        <el-select
                          v-else-if="condition.type === 'select'"
                          v-model="templateConditionValues[condition.name]"
                          :placeholder="
                            condition.placeholder ||
                            `请选择${condition.label || condition.name}`
                          "
                          style="width: 100%"
                          filterable
                        >
                          <el-option
                            v-for="option in condition.options"
                            :key="option.value"
                            :label="option.label"
                            :value="option.value"
                          />
                        </el-select>
                      </el-form-item>
                    </el-col>
                  </el-row>
                </div>
              </div>
            </el-col>
          </el-row>
        </div>

        <!-- 字段选择 -->
        <div v-if="queryConfig.table" class="query-section">
          <h4 class="section-title">字段选择</h4>
          <div class="fields-selection">
            <div class="field-groups">
              <div class="available-fields">
                <div class="field-header">
                  <h5>可用字段</h5>
                  <div class="field-search">
                    <el-input
                      v-model="fieldSearchText"
                      placeholder="搜索字段名或描述..."
                      size="small"
                      clearable
                      @keyup.enter="focusFirstField"
                      @clear="clearFieldSearch"
                    >
                      <template #prefix>
                        <el-icon><Search /></el-icon>
                      </template>
                    </el-input>
                  </div>
                </div>
                <div class="fields-list">
                  <div
                    v-for="field in filteredAvailableFields"
                    :key="field.name"
                    ref="fieldItems"
                    class="field-item"
                    :class="{ highlighted: isFieldHighlighted(field) }"
                    @click="addField(field)"
                  >
                    <el-icon><Plus /></el-icon>
                    <span
                      class="field-name"
                      v-html="highlightText(field.name, fieldSearchText)"
                    ></span>
                    <el-tag :type="getFieldTypeTag(field.type)" size="small">
                      <span
                        v-html="
                          highlightText(
                            field.description || field.type,
                            fieldSearchText,
                          )
                        "
                      ></span>
                    </el-tag>
                  </div>
                  <div
                    v-if="
                      filteredAvailableFields.length === 0 && fieldSearchText
                    "
                    class="no-fields"
                  >
                    <el-icon><InfoFilled /></el-icon>
                    <span>未找到匹配的字段</span>
                  </div>
                </div>
              </div>

              <div class="selected-fields">
                <h5>已选字段</h5>
                <div class="fields-list">
                  <div
                    v-for="(field, index) in queryConfig.fields"
                    :key="index"
                    class="field-item selected"
                  >
                    <el-icon @click="removeField(index)"><Close /></el-icon>
                    <span class="field-name">{{ field.name }}</span>
                    <el-input
                      v-model="field.alias"
                      placeholder="别名"
                      size="small"
                      style="width: 80px"
                      clearable
                    />
                  </div>
                  <div
                    v-if="queryConfig.fields.length === 0"
                    class="empty-fields"
                  >
                    <el-icon><InfoFilled /></el-icon>
                    <span>请从左侧选择字段</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- 条件设置 -->
        <div v-if="queryConfig.fields.length > 0" class="query-section">
          <h4 class="section-title">
            条件设置
            <el-button size="small" @click="addCondition">
              <el-icon><Plus /></el-icon>
              添加条件
            </el-button>
          </h4>
          <div class="conditions-list">
            <div
              v-for="(condition, index) in queryConfig.conditions"
              :key="index"
              class="condition-item"
              :class="{ 'locked-condition': condition.locked }"
            >
              <el-select
                v-if="index > 0"
                v-model="condition.logic"
                style="width: 80px"
                size="small"
                :disabled="condition.locked"
                filterable
              >
                <el-option label="AND" value="AND" />
                <el-option label="OR" value="OR" />
              </el-select>

              <el-select
                v-model="condition.field"
                placeholder="字段"
                style="width: 150px"
                size="small"
                :disabled="condition.locked"
                filterable
              >
                <el-option
                  v-for="field in availableFields"
                  :key="field.name"
                  :label="field.name"
                  :value="field.name"
                />
              </el-select>

              <el-select
                v-model="condition.operator"
                placeholder="操作符"
                style="width: 100px"
                size="small"
                :disabled="condition.locked"
                filterable
              >
                <el-option label="=" value="=" />
                <el-option label="!=" value="!=" />
                <el-option label=">" value=">" />
                <el-option label=">=" value=">=" />
                <el-option label="<" value="<" />
                <el-option label="<=" value="<=" />
                <el-option label="LIKE" value="LIKE" />
                <el-option label="IN" value="IN" />
                <el-option label="NOT IN" value="NOT IN" />
                <el-option label="IS NULL" value="IS NULL" />
                <el-option label="IS NOT NULL" value="IS NOT NULL" />
              </el-select>

              <el-input
                v-if="!['IS NULL', 'IS NOT NULL'].includes(condition.operator)"
                v-model="condition.value"
                placeholder="值"
                style="width: 150px"
                size="small"
                :disabled="condition.locked"
              />

              <!-- 锁定/解锁按钮 -->
              <el-button
                size="small"
                :type="condition.locked ? 'warning' : 'info'"
                :title="condition.locked ? '解锁条件' : '锁定条件'"
                @click="toggleConditionLock(index)"
              >
                <el-icon>
                  <Lock v-if="condition.locked" />
                  <Unlock v-else />
                </el-icon>
              </el-button>

              <el-button
                size="small"
                type="danger"
                :disabled="condition.locked"
                @click="removeCondition(index)"
              >
                <el-icon><Delete /></el-icon>
              </el-button>
            </div>
          </div>
        </div>

        <!-- 排序和限制 -->
        <div v-if="queryConfig.fields.length > 0" class="query-section">
          <h4 class="section-title">排序和限制</h4>
          <el-row :gutter="20">
            <el-col :span="8">
              <el-form-item label="排序字段">
                <el-select
                  v-model="queryConfig.orderBy.field"
                  placeholder="选择排序字段"
                  style="width: 100%"
                  clearable
                  filterable
                >
                  <el-option
                    v-for="field in availableFields"
                    :key="field.name"
                    :label="field.name"
                    :value="field.name"
                  />
                </el-select>
              </el-form-item>
            </el-col>
            <el-col :span="4">
              <el-form-item label="排序方式">
                <el-select
                  v-model="queryConfig.orderBy.direction"
                  style="width: 100%"
                  :disabled="!queryConfig.orderBy.field"
                  filterable
                >
                  <el-option label="升序" value="ASC" />
                  <el-option label="降序" value="DESC" />
                </el-select>
              </el-form-item>
            </el-col>
            <el-col :span="6">
              <el-form-item label="限制条数">
                <el-input-number
                  v-model="queryConfig.limit"
                  :min="1"
                  :max="10000"
                  style="width: 100%"
                  placeholder="最大1万条"
                />
              </el-form-item>
            </el-col>
            <el-col :span="6">
              <el-form-item label="偏移量">
                <el-input-number
                  v-model="queryConfig.offset"
                  :min="0"
                  style="width: 100%"
                  placeholder="起始位置"
                />
              </el-form-item>
            </el-col>
          </el-row>
        </div>

        <!-- SQL预览 -->
        <div v-if="queryConfig.fields.length > 0" class="query-section">
          <h4 class="section-title">
            SQL预览（包含所有条件）
            <el-button size="small" @click="copySQL">
              <el-icon><CopyDocument /></el-icon>
              复制
            </el-button>
          </h4>
          <div class="sql-preview">
            <pre><code>{{ generatedSQL }}</code></pre>
          </div>

          <!-- 执行SQL预览 -->
          <h4 class="section-title" style="margin-top: 16px">
            执行SQL（过滤空值条件）
            <el-button size="small" @click="copyExecutionSQL">
              <el-icon><CopyDocument /></el-icon>
              复制
            </el-button>
          </h4>
          <div class="sql-preview">
            <pre><code>{{ executionSQL }}</code></pre>
          </div>
        </div>
      </div>
    </el-card>

    <!-- 查询结果 -->
    <div
      v-if="queryResults.length > 0 || querying"
      class="query-results-section"
    >
      <el-card class="results-card">
        <template #header>
          <div class="card-header">
            <span>查询结果 ({{ queryResults.length }} 条记录)</span>
            <div class="header-actions">
              <el-button
                :disabled="queryResults.length === 0 || !hasExportPermission"
                @click="exportResults"
              >
                <el-icon><Download /></el-icon>
                导出
              </el-button>
              <el-button :loading="querying" @click="refreshQuery">
                <el-icon><Refresh /></el-icon>
                刷新
              </el-button>
            </div>
          </div>
        </template>

        <div v-loading="querying" class="results-content">
          <el-table
            v-if="queryResults.length > 0"
            :data="queryResults"
            stripe
            border
            style="width: 100%"
            max-height="500"
          >
            <el-table-column
              v-for="column in resultColumns"
              :key="column.prop"
              :prop="column.prop"
              :label="
                availableFields.find((field) => field.name === column.prop)
                  .description
              "
              :width="column.width"
              show-overflow-tooltip
            >
              <template #default="{ row }">
                <span v-if="column.type === 'date'">
                  {{ formatDateWithComment(row[column.prop], column.prop) }}
                </span>
                <span v-else-if="column.type === 'number'">
                  {{ formatNumberWithComment(row[column.prop], column.prop) }}
                </span>
                <el-tag
                  v-else-if="column.type === 'status'"
                  :type="getStatusTagType(row[column.prop])"
                >
                  {{ formatValueWithComment(row[column.prop], column.prop) }}
                </el-tag>
                <span v-else>
                  {{ formatValueWithComment(row[column.prop], column.prop) }}
                </span>
              </template>
            </el-table-column>
          </el-table>

          <div
            v-if="queryResults.length === 0 && !querying"
            class="empty-results"
          >
            <el-empty description="暂无查询结果" />
          </div>
        </div>
      </el-card>
    </div>

    <!-- 保存查询对话框 -->
    <el-dialog v-model="saveQueryVisible" title="保存查询" width="500px">
      <el-form :model="saveQueryForm" label-width="80px">
        <el-form-item label="查询名称" required>
          <el-input
            v-model="saveQueryForm.name"
            placeholder="请输入查询名称"
            maxlength="50"
            show-word-limit
          />
        </el-form-item>
        <el-form-item label="描述">
          <el-input
            v-model="saveQueryForm.description"
            type="textarea"
            :rows="3"
            placeholder="请输入查询描述"
            maxlength="200"
            show-word-limit
          />
        </el-form-item>
        <el-form-item label="标签">
          <el-select
            v-model="saveQueryForm.tags"
            multiple
            filterable
            allow-create
            placeholder="请选择或输入标签"
            style="width: 100%"
          >
            <el-option
              v-for="tag in queryTags"
              :key="tag"
              :label="tag"
              :value="tag"
            />
          </el-select>
        </el-form-item>
        <!-- 编辑时允许选择保存为新建 -->
        <el-form-item v-if="currentTemplateId" label="保存方式">
          <el-checkbox v-model="saveAsNew"
            >保存为新建（不更新当前模板）</el-checkbox
          >
        </el-form-item>
      </el-form>

      <template #footer>
        <div class="dialog-footer">
          <el-button @click="saveQueryVisible = false">取消</el-button>
          <el-button type="primary" @click="confirmSaveQuery"> 保存 </el-button>
        </div>
      </template>
    </el-dialog>

    <!-- 添加/更新资源包对话框 -->
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
            maxlength="50"
            show-word-limit
          />
        </el-form-item>
        <el-form-item label="描述">
          <el-input
            v-model="resourcePackageForm.description"
            type="textarea"
            :rows="3"
            placeholder="请输入资源包描述"
            maxlength="200"
            show-word-limit
          />
        </el-form-item>
        <el-form-item label="数据源">
          <el-input
            :value="`${queryConfig.datasourceId} (${queryConfig.schema || '默认'}.${queryConfig.table})`"
            readonly
            disabled
          />
        </el-form-item>
        <el-form-item label="查询字段">
          <el-tag
            v-for="field in queryConfig.fields"
            :key="field.name"
            style="margin-right: 8px; margin-bottom: 4px"
          >
            {{ field.alias || field.name }}
          </el-tag>
        </el-form-item>
        <el-form-item label="查询条件">
          <div v-if="queryConfig.conditions.length === 0" class="text-gray-500">
            无查询条件
          </div>
          <div v-else>
            <div
              v-for="(condition, index) in queryConfig.conditions"
              :key="index"
              class="condition-preview"
            >
              <span v-if="index > 0" class="logic-text">{{
                condition.logic
              }}</span>
              <span class="condition-text">
                {{ condition.field }} {{ condition.operator }}
                <span
                  v-if="
                    !['IS NULL', 'IS NOT NULL'].includes(condition.operator)
                  "
                >
                  "{{ condition.value }}"
                </span>
              </span>
            </div>
          </div>
        </el-form-item>
        <el-form-item label="限制条数">
          <el-input-number
            v-model="resourcePackageForm.limitConfig"
            :min="1"
            :max="10000"
            style="width: 200px"
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
            <el-option
              v-for="tag in queryTags"
              :key="tag"
              :label="tag"
              :value="tag"
            />
          </el-select>
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

<script setup lang="ts">
import { ref, reactive, computed, watch, onMounted, onUnmounted } from "vue";
import {
  Search,
  Delete,
  Document,
  CaretRight,
  Plus,
  Close,
  InfoFilled,
  CopyDocument,
  Download,
  Refresh,
  FolderAdd,
  Lock,
  Unlock,
  Edit,
} from "@element-plus/icons-vue";
import { ElMessage, ElMessageBox } from "element-plus";
import { useUserStore } from "@/stores/user";
import { datasourceApi } from "@/api/datasource";
import { getResourceFields } from "@/api/resource";
import { getSQLTemplates } from "@/api/sqlQuery";
import { resourcePackageApi, PackageType } from "@/api/resourcePackage";
import type { SQLTemplateConfig } from "@/types/sql-template-config";

// 定义保存数据接口
interface SaveData {
  name: string;
  description?: string;
  queryConfig: QueryConfig;
  sql: string;
  datasourceId: number | null;
  config: SQLTemplateConfig | null;
  id?: number;
}

interface QueryField {
  name: string;
  type: string;
  alias?: string;
  comment?: string;
}

interface QueryCondition {
  field: string;
  operator: string;
  value: any;
  logic?: "AND" | "OR";
  locked?: boolean;
}

// 定义SQL资源类型
interface SQLResource {
  id: number;
  name: string;
  description?: string;
  type?: string;
}

// 定义SQL模板类型
interface SQLTemplate {
  id: number;
  name: string;
  query: string;
  config?: SQLTemplateConfig;
  // 支持两种字段名格式
  datasource_id?: number;
  data_resource_id?: number;
  datasourceId?: number;
  dataResourceId?: number;
  description?: string;
  tags?: string[];
}

// 定义查询结果行类型
interface QueryResultRow {
  [key: string]: string | number | boolean | null | undefined;
}

// 定义组件属性
interface Props {
  sqlResources?: SQLResource[];
  hasQueryPermission?: boolean;
  hasExportPermission?: boolean;
  hasSavePermission?: boolean;
  initialDatasourceId?: number | null;
  initialResourceId?: number | null;
  initialSchema?: string;
  initialTableName?: string;
  // 资源包相关属性
  isInResourcePackage?: boolean;
  resourcePackageId?: number | null;
  resourcePackageName?: string;
}

// 定义查询配置类型
interface QueryConfig {
  datasourceId: number | null;
  resourceId?: number;
  schema: string;
  table: string;
  fields: QueryField[];
  conditions: QueryCondition[];
  orderBy: { field: string; direction: "ASC" | "DESC" };
  limit: number;
  offset: number;
  sql: string;
}

// 定义保存表单类型
interface SaveForm {
  name: string;
  description: string;
  tags: string[];
}

// 定义组件事件
interface Emits {
  (e: "execute-query", config: QueryConfig): void;
  (e: "save-query", form: SaveForm): void;
  (e: "update-query", form: SaveForm): void;
  (e: "export-results", results: Record<string, any>[]): void;
  (
    e: "add-to-resource-package",
    data: {
      name: string;
      description: string;
      type: string;
      [key: string]: any;
    },
  ): void;
  (
    e: "update-resource-package",
    data: {
      id: number;
      name: string;
      description: string;
      type: string;
      [key: string]: any;
    },
  ): void;
}

const props = withDefaults(defineProps<Props>(), {
  sqlResources: () => [],
  hasQueryPermission: false,
  hasExportPermission: false,
  hasSavePermission: false,
  initialDatasourceId: null,
  initialResourceId: null,
  initialSchema: "",
  initialTableName: "",
  // 资源包相关属性默认值
  isInResourcePackage: false,
  resourcePackageId: null,
  resourcePackageName: "",
});

const emit = defineEmits<Emits>();

// 用户状态管理
const userStore = useUserStore();

// 响应式数据
const querying = ref(false);
const saveQueryVisible = ref(false);
const saveAsNew = ref(false);
const resourcePackageVisible = ref(false);
const creatingResourcePackage = ref(false);
const currentTemplateId = ref<number | null>(null); // 当前加载的模板ID

// 缓存机制（提升性能）
const tablesCache = new Map<string, any[]>(); // 表列表缓存，key: datasourceId_schema
const fieldsCache = new Map<string, QueryField[]>(); // 字段列表缓存，key: datasourceId_schema_table

// 模板选择相关（优化类型定义）
const selectedTemplateId = ref<number | null>(null); // 用户选择的模板ID
const availableTemplates = ref<SQLTemplate[]>([]); // 可用的模板列表
const loadingTemplates = ref(false); // 模板加载状态
const lastLoadedResourceId = ref<number | null>(null); // 上次加载模板的resourceId，用于防重复调用
const templateConfig = ref<SQLTemplateConfig | null>(null); // 当前模板的配置信息
const templateConditionValues = ref<
  Record<string, string | number | boolean | null>
>({}); // 模板条件的用户输入值

// SQL查询配置
const queryConfig = reactive({
  datasourceId: null as number | null, // 直接使用数据源ID
  resourceId: null as number | null, // 数据资源ID
  schema: "",
  table: "",
  fields: [] as QueryField[],
  conditions: [] as QueryCondition[],
  orderBy: {
    field: "",
    direction: "ASC",
  },
  limit: 100,
  offset: 0,
});

// 保存查询表单
const saveQueryForm = reactive({
  name: "",
  description: "",
  tags: [] as string[],
});

// 资源包表单
const resourcePackageForm = reactive({
  name: "",
  description: "",
  limitConfig: 1000,
  tags: [] as string[],
});

// 查询结果
const queryResults = ref<QueryResultRow[]>([]);
const resultColumns = ref<{ name: string; type: string; prop: string }[]>([]);
const availableSchemas = ref<{ name: string; description?: string }[]>([]);
const availableTables = ref<
  { name: string; type?: string; schema?: string; rowCount?: number }[]
>([]);
const availableFields = ref<
  { name: string; type: string; description?: string }[]
>([]);
const queryTags = ref<string[]>([
  "常用查询",
  "报表查询",
  "数据分析",
  "业务查询",
]);

// 字段搜索相关
const fieldSearchText = ref("");
const fieldItems = ref<HTMLElement[]>([]);

/**
 * 过滤后的可用字段
 */
const filteredAvailableFields = computed(() => {
  if (!fieldSearchText.value.trim()) {
    return availableFields.value;
  }

  const searchText = fieldSearchText.value.toLowerCase().trim();
  return availableFields.value.filter((field) => {
    const nameMatch = field.name.toLowerCase().includes(searchText);
    const descMatch =
      field.description?.toLowerCase().includes(searchText) || false;
    const typeMatch = field.type.toLowerCase().includes(searchText);
    return nameMatch || descMatch || typeMatch;
  });
});

/**
 * 判断是否禁用数据源选择
 */
const isResourceSelectionDisabled = computed(() => {
  return (
    props.initialDatasourceId !== null &&
    props.initialDatasourceId !== undefined
  );
});

/**
 * 生成SQL语句（优化版本，使用缓存）
 */
const generatedSQL = computed(() => {
  // 早期返回，避免不必要的计算
  if (!queryConfig.table || queryConfig.fields.length === 0) {
    return "";
  }

  const parts: string[] = ["SELECT"];

  // 字段列表 - 优化：减少字符串拼接
  const fieldList = queryConfig.fields.map((field: QueryField) => {
    return field.alias && field.alias !== field.name
      ? `${field.name} AS ${field.alias}`
      : field.name;
  });
  parts.push(fieldList.join(", "));
  parts.push("FROM", queryConfig.table);

  // WHERE条件 - 优化：只在有条件时处理
  if (queryConfig.conditions.length > 0) {
    const conditionParts: string[] = ["WHERE"];
    const conditionList = queryConfig.conditions.map(
      (condition: QueryCondition, index: number) => {
        const prefix = index > 0 ? `${condition.logic} ` : "";

        if (["IS NULL", "IS NOT NULL"].includes(condition.operator)) {
          return `${prefix}${condition.field} ${condition.operator}`;
        } else {
          return `${prefix}${condition.field} ${condition.operator} '${condition.value}'`;
        }
      },
    );
    conditionParts.push(conditionList.join(" "));
    parts.push(conditionParts.join(" "));
  }

  // ORDER BY - 优化：只在有排序字段时添加
  if (queryConfig.orderBy.field) {
    parts.push(
      `ORDER BY ${queryConfig.orderBy.field} ${queryConfig.orderBy.direction}`,
    );
  }

  // LIMIT - 优化：只在有限制时添加
  if (queryConfig.limit) {
    parts.push(`LIMIT ${queryConfig.limit}`);
  }

  // OFFSET - 优化：只在有偏移时添加
  if (queryConfig.offset) {
    parts.push(`OFFSET ${queryConfig.offset}`);
  }

  return parts.join(" ");
});

/**
 * 生成执行查询时的SQL语句（过滤空值条件）
 */
const executionSQL = computed(() => {
  // 早期返回，避免不必要的计算
  if (!queryConfig.table || queryConfig.fields.length === 0) {
    return "";
  }

  const parts: string[] = ["SELECT"];

  // 字段列表 - 优化：减少字符串拼接
  const fieldList = queryConfig.fields.map((field: QueryField) => {
    return field.alias && field.alias !== field.name
      ? `${field.name} AS ${field.alias}`
      : field.name;
  });
  parts.push(fieldList.join(", "));
  parts.push("FROM", queryConfig.table);

  // WHERE条件 - 过滤掉值为空的条件
  const validConditions = queryConfig.conditions.filter(
    (condition: QueryCondition) => {
      // 对于IS NULL和IS NOT NULL操作符，不需要值
      if (["IS NULL", "IS NOT NULL"].includes(condition.operator)) {
        return true;
      }
      // 对于其他操作符，检查值是否为空
      return (
        condition.value !== null &&
        condition.value !== undefined &&
        condition.value !== ""
      );
    },
  );

  if (validConditions.length > 0) {
    const conditionParts: string[] = ["WHERE"];
    const conditionList = validConditions.map(
      (condition: QueryCondition, index: number) => {
        const prefix = index > 0 ? `${condition.logic} ` : "";

        if (["IS NULL", "IS NOT NULL"].includes(condition.operator)) {
          return `${prefix}${condition.field} ${condition.operator}`;
        } else {
          return `${prefix}${condition.field} ${condition.operator} '${condition.value}'`;
        }
      },
    );
    conditionParts.push(conditionList.join(" "));
    parts.push(conditionParts.join(" "));
  }

  // ORDER BY - 优化：只在有排序字段时添加
  if (queryConfig.orderBy.field) {
    parts.push(
      `ORDER BY ${queryConfig.orderBy.field} ${queryConfig.orderBy.direction}`,
    );
  }

  // LIMIT - 优化：只在有限制时添加
  if (queryConfig.limit) {
    parts.push(`LIMIT ${queryConfig.limit}`);
  }

  // OFFSET - 优化：只在有偏移时添加
  if (queryConfig.offset) {
    parts.push(`OFFSET ${queryConfig.offset}`);
  }

  return parts.join(" ");
});

/**
 * 获取有效的查询条件（过滤空值条件）
 */
const getValidConditions = () => {
  return queryConfig.conditions.filter((condition: QueryCondition) => {
    // 对于IS NULL和IS NOT NULL操作符，不需要值
    if (["IS NULL", "IS NOT NULL"].includes(condition.operator)) {
      return true;
    }
    // 对于其他操作符，检查值是否为空
    return (
      condition.value !== null &&
      condition.value !== undefined &&
      condition.value !== ""
    );
  });
};

/**
 * 数据源变更处理（带缓存清理）
 */
const onDatasourceChange = async () => {
  console.log(
    "[onDatasourceChange] 开始处理数据源变更，当前数据源ID:",
    queryConfig.datasourceId,
  );

  queryConfig.schema = "";
  queryConfig.table = "";
  queryConfig.fields = [];
  queryConfig.conditions = [];
  availableSchemas.value = [];
  availableTables.value = [];
  availableFields.value = [];

  // 清理相关缓存
  const oldDatasourceId = queryConfig.datasourceId;
  if (oldDatasourceId) {
    // 清理该数据源相关的所有缓存
    for (const [key] of tablesCache) {
      if (key.startsWith(`${oldDatasourceId}_`)) {
        tablesCache.delete(key);
      }
    }
    for (const [key] of fieldsCache) {
      if (key.startsWith(`${oldDatasourceId}_`)) {
        fieldsCache.delete(key);
      }
    }
    console.log("[onDatasourceChange] 已清理数据源相关缓存");
  }

  console.log("[onDatasourceChange] 已清空所有配置和可用选项");

  if (!queryConfig.datasourceId) {
    console.log("[onDatasourceChange] 数据源ID为空，结束处理");
    return;
  }

  try {
    const datasourceId = queryConfig.datasourceId;
    console.log(
      "[onDatasourceChange] 开始获取Schema列表，数据源ID:",
      datasourceId,
    );

    // 先获取Schema列表
    const schemasResponse =
      await datasourceApi.getDataSourceSchemas(datasourceId);
    console.log("[onDatasourceChange] Schema API响应:", schemasResponse);

    if (schemasResponse.data && schemasResponse.data.length > 0) {
      availableSchemas.value = schemasResponse.data;
      console.log(
        "[onDatasourceChange] 成功加载Schema列表:",
        availableSchemas.value,
      );

      // 如果有初始Schema或者只有一个Schema，自动选择
      if (
        props.initialSchema &&
        schemasResponse.data.find((s) => s.name === props.initialSchema)
      ) {
        queryConfig.schema = props.initialSchema;
        console.log(
          "[onDatasourceChange] 自动选择初始Schema:",
          props.initialSchema,
        );
      } else if (schemasResponse.data.length === 1) {
        queryConfig.schema = schemasResponse.data[0].name;
        console.log(
          "[onDatasourceChange] 自动选择唯一Schema:",
          queryConfig.schema,
        );
      }

      // 如果已选择Schema，加载表列表
      if (queryConfig.schema) {
        console.log(
          "[onDatasourceChange] 开始加载表列表，Schema:",
          queryConfig.schema,
        );
        await loadTablesForSchema(datasourceId, queryConfig.schema);
      }
    } else {
      console.log("[onDatasourceChange] 无Schema数据，尝试直接获取表列表");
      // 如果没有Schema，尝试直接获取表列表（兼容非关系型数据库）
      const response = await datasourceApi.getDataSourceTables(datasourceId);
      console.log("[onDatasourceChange] 表列表API响应:", response);

      if (response.data) {
        availableTables.value = response.data.map((table) => ({
          name: table.name,
          type: table.type || "table",
          schema: table.schema,
          rowCount: 0, // 暂时设为0，后续可以通过其他API获取
        }));
      }
    }

    // 注释掉这里的调用，避免重复加载
    // await loadLatestSQLTemplate()
  } catch (error) {
    console.error("获取数据源信息失败:", error);
    ElMessage.error("获取数据源信息失败");
    availableSchemas.value = [];
    availableTables.value = [];
  }
};

/**
 * 加载当前数据资源的最新SQL模板
 */
const loadLatestSQLTemplate = async () => {
  if (!queryConfig.resourceId) {
    return;
  }

  try {
    // 获取当前数据资源的SQL模板列表，按ID降序排列获取最新的
    const response = await getSQLTemplates({
      dataResourceId: queryConfig.resourceId,
      isTemplate: true,
    });

    if (response.data && response.data.length > 0) {
      // 按ID降序排序，获取最新的模板
      const latestTemplate = response.data.sort((a, b) => b.id - a.id)[0];

      console.log("[loadLatestSQLTemplate] 最新模板:", latestTemplate);

      // 保存当前模板ID和信息
      currentTemplateId.value = latestTemplate.id;
      saveQueryForm.name = latestTemplate.name;
      saveQueryForm.description = latestTemplate.description || "";
      saveQueryForm.tags = latestTemplate.tags || [];

      // 解析SQL模板并填充到查询构建器
      await parseSQLTemplate(latestTemplate.query);

      ElMessage.success(`已加载最新的SQL模板: ${latestTemplate.name}`);
      selectedTemplateId.value = latestTemplate.id;
    }
  } catch (error) {
    console.error("加载SQL模板失败:", error);
    // 不显示错误消息，因为没有模板是正常情况
  }
};

/**
 * 加载指定Schema下的表列表（带缓存优化）
 */
const loadTablesForSchema = async (datasourceId: number, schema: string) => {
  console.log("[loadTablesForSchema] 开始加载表列表:", {
    datasourceId,
    schema,
  });

  // 检查缓存
  const cacheKey = `${datasourceId}_${schema}`;
  if (tablesCache.has(cacheKey)) {
    console.log("[loadTablesForSchema] 使用缓存数据");
    availableTables.value = tablesCache.get(cacheKey)!;
    return;
  }

  try {
    const tablesResponse = await datasourceApi.getDataSourceTablesWithSchema(
      datasourceId,
      schema,
    );
    console.log("[loadTablesForSchema] 表列表API响应:", tablesResponse);

    if (tablesResponse.data) {
      const tables = tablesResponse.data.map((table) => ({
        name: table.name,
        type: table.type || "table",
        schema: schema,
        rowCount: 0, // 暂时设为0，后续可以通过其他API获取
      }));

      // 更新缓存和响应式数据
      tablesCache.set(cacheKey, tables);
      availableTables.value = tables;
      console.log(
        "[loadTablesForSchema] 成功加载表列表并缓存:",
        availableTables.value,
      );
    } else {
      console.log("[loadTablesForSchema] API响应无数据");
      availableTables.value = [];
    }
  } catch (error) {
    console.error("[loadTablesForSchema] 获取数据表列表失败:", error);
    ElMessage.error("获取数据表列表失败");
    availableTables.value = [];
  }
};

/**
 * Schema变更处理
 */
const onSchemaChange = async () => {
  queryConfig.table = "";
  queryConfig.fields = [];
  queryConfig.conditions = [];
  availableTables.value = [];
  availableFields.value = [];

  if (!queryConfig.schema || !queryConfig.datasourceId) {
    return;
  }

  try {
    const datasourceId = queryConfig.datasourceId;
    await loadTablesForSchema(datasourceId, queryConfig.schema);
  } catch (error) {
    console.error("Schema变更失败:", error);
    ElMessage.error("Schema变更失败");
  }
};

/**
 * 数据表变更处理（带缓存优化）
 */
const onTableChange = async () => {
  console.log("🔄 开始表变更处理:", {
    table: queryConfig.table,
    schema: queryConfig.schema,
    datasourceId: queryConfig.datasourceId,
  });

  queryConfig.fields = [];
  queryConfig.conditions = [];
  availableFields.value = [];

  if (!queryConfig.table || !queryConfig.schema) {
    console.log("⚠️ 表名或Schema为空，跳过字段加载");
    return;
  }

  try {
    // 获取数据源ID
    if (!queryConfig.datasourceId) {
      console.log("❌ 数据源ID为空");
      ElMessage.error("请先设置有效的数据源ID");
      return;
    }
    const datasourceId = queryConfig.datasourceId;

    // 检查字段缓存
    const fieldsCacheKey = `${datasourceId}_${queryConfig.schema}_${queryConfig.table}`;
    if (fieldsCache.has(fieldsCacheKey)) {
      console.log("🔄 使用字段缓存数据");
      availableFields.value = fieldsCache.get(fieldsCacheKey)!;
      return;
    }

    console.log("🔄 开始获取表字段信息:", {
      datasourceId,
      schema: queryConfig.schema,
      table: queryConfig.table,
    });

    // 调用数据源API获取表字段信息
    const response = await datasourceApi.getDataSourceTableFields(
      datasourceId,
      queryConfig.schema,
      queryConfig.table,
    );
    console.log("📊 API响应:", response);

    if (response.data) {
      const fields = response.data.map((field) => ({
        name: field.name,
        type: field.type || "varchar",
        description: field.comment || "",
      }));

      // 更新缓存和响应式数据
      fieldsCache.set(fieldsCacheKey, fields);
      availableFields.value = fields;
      console.log("✅ 字段信息加载成功并缓存:", availableFields.value);
    } else {
      console.log("⚠️ API响应中没有数据");
    }
  } catch (error) {
    console.error("❌ 获取字段信息失败:", error);
    ElMessage.error("获取字段信息失败");
    availableFields.value = [];
  }
};

/**
 * 添加字段
 */
const addField = (field: QueryField) => {
  const exists = queryConfig.fields.some(
    (f: QueryField) => f.name === field.name,
  );
  if (!exists) {
    queryConfig.fields.push({ ...field, alias: "" });
  }
};

/**
 * 移除字段
 */
const removeField = (index: number) => {
  queryConfig.fields.splice(index, 1);
};

/**
 * 清空字段搜索
 */
const clearFieldSearch = () => {
  fieldSearchText.value = "";
};

/**
 * 聚焦到第一个搜索结果字段
 */
const focusFirstField = () => {
  if (filteredAvailableFields.value.length > 0) {
    const firstField = filteredAvailableFields.value[0];
    addField(firstField);
    fieldSearchText.value = "";
  }
};

/**
 * 判断字段是否高亮显示
 */
const isFieldHighlighted = (field: {
  name: string;
  type: string;
  description?: string;
}) => {
  return fieldSearchText.value.trim() !== "";
};

/**
 * 高亮搜索文本
 */
const highlightText = (text: string, searchText: string) => {
  if (!searchText.trim() || !text) {
    return text;
  }

  const regex = new RegExp(
    `(${searchText.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")})`,
    "gi",
  );
  return text.replace(regex, '<mark class="search-highlight">$1</mark>');
};

/**
 * 添加条件
 */
const addCondition = () => {
  queryConfig.conditions.push({
    logic: "AND" as const,
    field: "",
    operator: "=",
    value: "",
    locked: false,
  });
};

/**
 * 移除条件
 */
const removeCondition = (index: number) => {
  queryConfig.conditions.splice(index, 1);
};

/**
 * 切换条件锁定状态
 */
const toggleConditionLock = (index: number) => {
  const condition = queryConfig.conditions[index];
  if (condition) {
    condition.locked = !condition.locked;
  }
};

/**
 * 清空查询
 */
const clearQuery = () => {
  queryConfig.datasourceId = null;
  queryConfig.schema = "";
  queryConfig.table = "";
  queryConfig.fields = [];
  queryConfig.conditions = [];
  queryConfig.orderBy.field = "";
  queryConfig.orderBy.direction = "ASC";
  queryConfig.limit = 100;
  queryConfig.offset = 0;
  availableSchemas.value = [];
  availableTables.value = [];
  availableFields.value = [];
  queryResults.value = [];
  resultColumns.value = [];

  // 清除当前模板ID和保存表单
  currentTemplateId.value = null;
  saveQueryForm.name = "";
  saveQueryForm.description = "";
  saveQueryForm.tags = [];
};

/**
 * 执行查询
 */
const executeQuery = () => {
  if (queryConfig.fields.length === 0) {
    ElMessage.warning("请至少选择一个字段");
    return;
  }

  if (!queryConfig.datasourceId) {
    ElMessage.warning("请选择数据源");
    return;
  }

  if (!queryConfig.table) {
    ElMessage.warning("请选择数据表");
    return;
  }

  querying.value = true;

  // 构建查询参数，使用过滤后的条件
  const validConditions = getValidConditions();
  const queryParams = {
    datasourceId: queryConfig.datasourceId,
    resourceId: queryConfig.resourceId,
    schema: queryConfig.schema,
    table: queryConfig.table,
    fields: queryConfig.fields.map((field) => ({
      name: field.name,
      alias: field.alias || "",
      type: field.type,
    })),
    conditions: validConditions, // 使用过滤后的条件
    orderBy: queryConfig.orderBy,
    limit: queryConfig.limit,
    offset: queryConfig.offset,
    sql: executionSQL.value, // 使用执行时的SQL语句（过滤空值条件）
  };

  console.log("🚀 执行查询，参数:", queryParams);

  // 发送查询请求到父组件
  emit("execute-query", queryParams);
};

/**
 * 刷新查询
 */
const refreshQuery = () => {
  executeQuery();
};

/**
 * 保存查询
 */
const saveQuery = () => {
  if (queryConfig.fields.length === 0) {
    ElMessage.warning("请先构建查询条件");
    return;
  }
  // 每次打开保存对话框时重置“保存为新建”选项
  saveAsNew.value = false;
  saveQueryVisible.value = true;
};

/**
 * 确认保存查询
 */
const confirmSaveQuery = () => {
  if (!saveQueryForm.name.trim()) {
    ElMessage.warning("请输入查询名称");
    return;
  }

  // 若选择“保存为新建”，清空当前模板ID以触发新增逻辑
  if (saveAsNew.value) {
    currentTemplateId.value = null;
  }

  // 构建配置对象，包含当前的条件设置
  const configToSave = {
    ...templateConfig.value,
    conditions: queryConfig.conditions.map((condition) => ({
      name: condition.field,
      label: condition.field,
      type: "string",
      required: false,
      locked: condition.locked || false,
      lockedValue: condition.locked ? condition.value : undefined,
      defaultValue: !condition.locked ? condition.value : undefined,
      operator: condition.operator || "=",
    })),
  };

  const saveData: SaveData = {
    ...saveQueryForm,
    queryConfig: { ...queryConfig },
    sql: generatedSQL.value,
    datasourceId: queryConfig.datasourceId,
    config: configToSave, // 包含完整的条件配置信息
  };

  // 如果有当前模板ID，则是更新操作
  if (currentTemplateId.value) {
    saveData.id = currentTemplateId.value;
    emit("update-query", saveData);
    ElMessage.success("查询模板已更新");
  } else {
    // 否则是新增操作
    emit("save-query", saveData);
    ElMessage.success("查询已保存");
  }

  saveQueryVisible.value = false;
};

/**
 * 导出结果
 */
const exportResults = () => {
  emit("export-results", queryResults.value);
};

/**
 * 复制SQL
 */
const copySQL = async () => {
  try {
    await navigator.clipboard.writeText(generatedSQL.value);
    ElMessage.success("SQL已复制到剪贴板");
  } catch (err) {
    ElMessage.error("复制失败");
  }
};

/**
 * 复制执行SQL
 */
const copyExecutionSQL = async () => {
  try {
    await navigator.clipboard.writeText(executionSQL.value);
    ElMessage.success("执行SQL已复制到剪贴板");
  } catch (err) {
    ElMessage.error("复制失败");
  }
};

/**
 * 解析SQL模板并填充到查询构建器
 * @param sqlQuery SQL查询语句
 */
const parseSQLTemplate = async (sqlQuery: string) => {
  try {
    console.log("🔍 开始解析SQL:", sqlQuery);

    // 检查SQL查询是否为空或undefined
    if (!sqlQuery || typeof sqlQuery !== "string") {
      console.warn("⚠️ SQL查询为空或无效，跳过解析");
      return;
    }

    // 解析SQL语句并尝试提取表名和字段
    const sql = sqlQuery.toLowerCase().trim();
    console.log("🔍 转换为小写SQL:", sql);

    // 简单的SQL解析，提取表名
    const fromMatch = sql.match(/from\s+([\w_]+)/);
    console.log("🔍 表名匹配结果:", fromMatch);

    if (fromMatch) {
      queryConfig.table = fromMatch[1];
      console.log("📝 设置表名:", queryConfig.table);

      // 如果找到表名，尝试加载该表的字段信息
      console.log("🔄 开始加载表字段信息...");
      try {
        await onTableChange();
        console.log("✅ 表字段信息加载完成");
      } catch (error) {
        console.error("❌ 表字段信息加载失败:", error);
        // 继续执行，不中断解析过程
      }

      // 等待字段信息加载完成后再解析字段
      await new Promise((resolve) => setTimeout(resolve, 500));
      console.log("📊 当前可用字段数量:", availableFields.value.length);
      console.log("📊 当前可用字段:", availableFields.value);
    }

    // 提取字段（简单处理SELECT后的字段）
    console.log("🔍 开始提取字段...");
    const selectMatch = sql.match(/select\s+(.+?)\s+from/);
    console.log("🔍 字段匹配结果:", selectMatch);

    if (selectMatch) {
      const fieldsStr = selectMatch[1].trim();
      console.log("📝 提取的字段字符串:", fieldsStr);

      if (fieldsStr !== "*") {
        console.log("🔍 开始解析字段名称...");
        const fieldNames = fieldsStr.split(",").map((field: string) => {
          const trimmed = field.trim();
          const parts = trimmed.split(/\s+as\s+/i);
          return {
            name: parts[0],
            alias: parts[1] || "",
            type: "varchar", // 默认类型，会在字段匹配时更新
          };
        });

        console.log("📝 解析的字段名称:", fieldNames);
        console.log(
          "📊 可用字段列表:",
          availableFields.value.map((f) => f.name),
        );

        // 匹配已加载的字段信息（使用不区分大小写的匹配）
        console.log("🔍 开始匹配字段...");
        queryConfig.fields = fieldNames.map((field) => {
          const availableField = availableFields.value.find(
            (af) => af.name.toLowerCase() === field.name.toLowerCase(),
          );
          console.log(`🔍 匹配字段 ${field.name}:`, availableField);

          const matchedField = {
            name: availableField?.name || field.name, // 使用原始字段名
            alias: field.alias,
            type: availableField?.type || field.type,
            description: availableField?.description || "",
          };
          console.log(`✅ 字段匹配结果:`, matchedField);
          return matchedField;
        });

        console.log("✅ 最终设置的字段:", queryConfig.fields);
        console.log("✅ 字段数量:", queryConfig.fields.length);
      } else {
        console.log("🔍 检测到SELECT *，不设置具体字段");
      }
    }

    // 解析WHERE条件（简单处理）
    const whereMatch = sql.match(/where\s+(.+?)(?:\s+order\s+by|\s+limit|$)/);
    if (whereMatch) {
      const whereClause = whereMatch[1].trim();
      console.log("🔍 WHERE条件:", whereClause);
      // 这里可以进一步解析WHERE条件，暂时简化处理
      queryConfig.conditions = [];
    }

    // 解析ORDER BY
    const orderMatch = sql.match(/order\s+by\s+([\w_]+)\s+(asc|desc)?/);
    if (orderMatch) {
      queryConfig.orderBy.field = orderMatch[1];
      queryConfig.orderBy.direction = orderMatch[2]?.toUpperCase() || "ASC";
      console.log("📝 设置排序:", queryConfig.orderBy);
    }

    // 解析LIMIT
    const limitMatch = sql.match(/limit\s+(\d+)/);
    if (limitMatch) {
      queryConfig.limit = parseInt(limitMatch[1]);
      console.log("📝 设置限制:", queryConfig.limit);
    }

    // 解析OFFSET
    const offsetMatch = sql.match(/offset\s+(\d+)/);
    if (offsetMatch) {
      queryConfig.offset = parseInt(offsetMatch[1]);
      console.log("📝 设置偏移:", queryConfig.offset);
    }

    console.log("✅ SQL解析完成，最终配置:", {
      table: queryConfig.table,
      fields: queryConfig.fields,
      conditions: queryConfig.conditions,
      orderBy: queryConfig.orderBy,
      limit: queryConfig.limit,
      offset: queryConfig.offset,
    });
  } catch (error) {
    console.error("❌ 解析SQL模板失败:", error);
  }
};

/**
 * 加载模板
 * @param template 模板数据
 */
const loadTemplate = async (template: SQLTemplate) => {
  try {
    console.log("🔄 开始加载模板:", template);

    // 设置数据源和资源ID（支持两种字段名格式）
    queryConfig.datasourceId =
      template.datasource_id || template.datasourceId || null;
    queryConfig.resourceId =
      template.data_resource_id || template.dataResourceId || null;

    // 处理模板配置
    if (template.config) {
      console.log("🔄 加载模板配置:", template.config);
      templateConfig.value = template.config as SQLTemplateConfig;

      // 初始化条件值
      templateConditionValues.value = {};

      // 处理必填条件
      if (templateConfig.value.requiredConditions) {
        templateConfig.value.requiredConditions.forEach((condition) => {
          templateConditionValues.value[condition.field] =
            condition.defaultValue || null;
        });
      }

      // 处理可选条件
      if (templateConfig.value.optionalConditions) {
        templateConfig.value.optionalConditions.forEach((condition) => {
          templateConditionValues.value[condition.field] =
            condition.defaultValue || null;
        });
      }

      // 处理锁定条件
      if (templateConfig.value.lockedConditions) {
        templateConfig.value.lockedConditions.forEach((condition) => {
          templateConditionValues.value[condition.field] =
            condition.lockedValue;
        });
      }

      console.log("✅ 模板配置加载完成:", templateConfig.value);
      console.log("📝 条件值初始化:", templateConditionValues.value);
    } else {
      templateConfig.value = null;
      templateConditionValues.value = {};
    }

    console.log("📝 设置配置:", {
      datasourceId: queryConfig.datasourceId,
      resourceId: queryConfig.resourceId,
    });

    // 先加载数据源信息
    if (queryConfig.datasourceId) {
      console.log("🔄 开始加载数据源信息...");
      await onDatasourceChange();
      console.log("✅ 数据源信息加载完成");
    }

    // 调用SQL解析函数（等待解析完成）
    console.log("🔄 开始解析SQL:", template.query);
    await parseSQLTemplate(template.query);
    console.log("✅ SQL解析完成");

    // 添加模板中的条件配置到查询配置
    if (
      templateConfig.value?.conditions &&
      Array.isArray(templateConfig.value.conditions)
    ) {
      console.log("🔄 处理模板条件配置:", templateConfig.value.conditions);
      templateConfig.value.conditions.forEach((condition) => {
        console.log("🔍 处理条件:", condition);

        // 处理所有条件配置，不仅仅是锁定的条件
        const fieldName = condition.name || condition.field; // 兼容两种字段名
        const conditionValue =
          condition.lockedValue ||
          condition.value ||
          condition.defaultValue ||
          ""; // 优先使用lockedValue，然后是value，最后是defaultValue
        const isLocked = condition.locked === true; // 明确检查是否锁定

        const existingCondition = queryConfig.conditions.find(
          (c) => c.field === fieldName,
        );
        if (!existingCondition) {
          const newCondition: QueryCondition = {
            logic: "AND" as const,
            field: fieldName,
            operator: condition.operator || "=",
            value: conditionValue,
            locked: isLocked,
          };
          console.log(
            `➕ 添加新的${isLocked ? "锁定" : "普通"}条件:`,
            newCondition,
          );
          queryConfig.conditions.push(newCondition);
        } else {
          // 如果条件已存在，更新其属性
          existingCondition.locked = isLocked;
          existingCondition.operator =
            condition.operator || existingCondition.operator;
          existingCondition.value = conditionValue;
          console.log(
            `🔄 更新现有条件为${isLocked ? "锁定" : "普通"}:`,
            existingCondition,
          );
        }
      });
      console.log("✅ 条件处理完成，当前查询条件:", queryConfig.conditions);
    }

    // 额外等待确保所有异步操作完成
    await new Promise((resolve) => setTimeout(resolve, 200));

    console.log("📊 当前查询配置:", {
      table: queryConfig.table,
      fields: queryConfig.fields,
      conditions: queryConfig.conditions,
      orderBy: queryConfig.orderBy,
      limit: queryConfig.limit,
    });

    console.log(
      "📊 字段详细信息:",
      queryConfig.fields.map((f) => ({
        name: f.name,
        type: f.type,
        description: f.comment,
      })),
    );

    ElMessage.success(`已加载模板: ${template.name}`);
  } catch (error) {
    console.error("❌ 加载模板失败:", error);
    ElMessage.error("加载模板失败");
  }
};

/**
 * 获取资源类型标签
 */
const getResourceTypeTag = (type: string) => {
  const typeMap: Record<string, string> = {
    mysql: "success",
    postgresql: "info",
    oracle: "warning",
    sqlserver: "danger",
  };
  return typeMap[type] || "info";
};

/**
 * 获取资源类型标签文本
 */
const getResourceTypeLabel = (type: string) => {
  const labelMap: Record<string, string> = {
    mysql: "MySQL",
    postgresql: "PostgreSQL",
    oracle: "Oracle",
    sqlserver: "SQL Server",
  };
  return labelMap[type] || type;
};

/**
 * 获取字段类型标签
 */
const getFieldTypeTag = (
  type: string,
): "success" | "primary" | "warning" | "info" | "danger" => {
  const typeMap: Record<
    string,
    "success" | "primary" | "warning" | "info" | "danger"
  > = {
    int: "success",
    varchar: "info",
    datetime: "warning",
    decimal: "danger",
    enum: "primary",
  };
  return typeMap[type] || "info";
};

/**
 * 格式化日期
 */
const formatDate = (date: string) => {
  if (!date) return "";
  return new Date(date).toLocaleString();
};

/**
 * 格式化数字
 */
const formatNumber = (num: number) => {
  if (num === null || num === undefined) return "";
  return num.toLocaleString();
};

/**
 * 格式化日期并添加注释
 */
const formatDateWithComment = (date: string, fieldName: string) => {
  const formattedDate = formatDate(date);
  return formatValueWithComment(formattedDate, fieldName);
};

/**
 * 格式化数字并添加注释
 */
const formatNumberWithComment = (num: number, fieldName: string) => {
  const formattedNumber = formatNumber(num);
  return formatValueWithComment(formattedNumber, fieldName);
};

/**
 * 格式化值并添加注释
 * 在字段值后面添加字段映射中的注释信息
 */
const formatValueWithComment = (value: any, fieldName: string) => {
  if (value === null || value === undefined) {
    value = "";
  }

  // (${fieldMapping.description})
  // 查找字段映射中的注释
  const fieldMapping = availableFields.value.find(
    (field) => field.name === fieldName,
  );
  if (
    fieldMapping &&
    fieldMapping.description &&
    fieldMapping.description !== fieldName
  ) {
    return `${value} `;
  }

  return value;
};

/**
 * 获取状态标签类型
 */
const getStatusTagType = (
  status: string,
): "success" | "primary" | "warning" | "info" | "danger" => {
  const statusMap: Record<
    string,
    "success" | "primary" | "warning" | "info" | "danger"
  > = {
    active: "success",
    inactive: "info",
    pending: "warning",
    deleted: "danger",
  };
  return statusMap[status] || "info";
};

/**
 * 组件挂载时初始化
 */
onMounted(async () => {
  console.log("🚀 组件挂载，初始化参数:", {
    initialDatasourceId: props.initialDatasourceId,
    initialResourceId: props.initialResourceId,
    initialSchema: props.initialSchema,
    initialTableName: props.initialTableName,
  });

  // 如果有初始数据源ID，设置并加载相关数据
  if (props.initialDatasourceId) {
    queryConfig.datasourceId = props.initialDatasourceId;
    console.log("📝 设置datasourceId:", props.initialDatasourceId);
  }

  // 如果有初始资源ID，设置资源ID
  if (props.initialResourceId) {
    queryConfig.resourceId = props.initialResourceId;
    console.log("📝 onMounted设置resourceId:", props.initialResourceId);
  }

  // 加载数据源相关信息
  if (queryConfig.datasourceId) {
    console.log("🔄 开始加载数据源信息...");
    await onDatasourceChange();
  }

  // 设置初始Schema
  if (props.initialSchema) {
    queryConfig.schema = props.initialSchema;
    console.log("📝 设置初始Schema:", props.initialSchema);
    await onSchemaChange();
  }

  // 设置初始表名
  if (props.initialTableName) {
    queryConfig.table = props.initialTableName;
    console.log("📝 设置初始表名:", props.initialTableName);
    await onTableChange();
  }

  // 模板加载由watch监听器统一处理，这里不重复调用
  console.log("📝 组件挂载完成，resourceId:", queryConfig.resourceId);

  console.log("✅ 组件初始化完成");
});

/**
 * 组件卸载时清理资源
 */
onUnmounted(() => {
  console.log("🧹 组件卸载，清理缓存和定时器");

  // 清理防抖定时器
  if (resourceIdDebounceTimer) {
    clearTimeout(resourceIdDebounceTimer);
    resourceIdDebounceTimer = null;
  }

  // 清理所有缓存
  tablesCache.clear();
  fieldsCache.clear();

  console.log("✅ 资源清理完成");
});

// 监听props变化
watch(
  () => props.initialResourceId,
  (newVal, oldVal) => {
    if (newVal && newVal !== oldVal && oldVal !== undefined) {
      queryConfig.resourceId = newVal;
      console.log("🔄 监听到resourceId变化:", newVal);
      // 当resourceId变化时，不在这里调用loadLatestSQLTemplate，由queryConfig.resourceId的监听器统一处理
    }
  },
  { immediate: false },
);

// 防抖定时器
let resourceIdDebounceTimer: NodeJS.Timeout | null = null;

// 监听queryConfig.resourceId变化，处理模板加载（添加防抖优化）
watch(
  () => queryConfig.resourceId,
  async (newVal, oldVal) => {
    console.log("👀 watch resourceId变化:", { newVal, oldVal });

    // 清除之前的防抖定时器
    if (resourceIdDebounceTimer) {
      clearTimeout(resourceIdDebounceTimer);
    }

    if (newVal && newVal !== oldVal) {
      console.log("🔄 queryConfig.resourceId变化，加载SQL模板:", newVal);
      // 重置防重复调用状态，允许新的resourceId加载
      lastLoadedResourceId.value = null;

      // 使用防抖机制，避免频繁调用
      resourceIdDebounceTimer = setTimeout(async () => {
        try {
          // 只加载模板列表，最新模板会在列表加载完成后自动选择
          await loadAvailableTemplates();
          console.log("✅ 模板加载完成");
        } catch (error) {
          console.error("❌ 模板加载失败:", error);
        }
      }, 300); // 300ms防抖延迟
    } else if (!newVal) {
      console.log("🧹 resourceId为空，清空模板列表");
      availableTemplates.value = [];
      selectedTemplateId.value = null;
    }
  },
  { immediate: true },
);

/**
 * 设置查询结果
 * @param results 查询结果数据
 * @param columns 结果列信息
 */
const setQueryResults = (
  results: Record<string, any>[],
  columns: { name: string; type: string; prop: string }[],
) => {
  queryResults.value = results;
  resultColumns.value = columns;
  querying.value = false;

  if (results && results.length > 0) {
    ElMessage.success(`查询成功，共返回 ${results.length} 条记录`);
  } else {
    ElMessage.info("查询完成，未找到匹配的记录");
  }
};

/**
 * 处理查询错误
 * @param error 错误信息
 */
const handleQueryError = (error: string | Error) => {
  querying.value = false;
  const errorMessage = typeof error === "string" ? error : error.message;
  ElMessage.error(`查询失败: ${errorMessage}`);
  console.error("❌ 查询执行失败:", error);
};

/**
 * 重置查询状态
 */
const resetQueryState = () => {
  querying.value = false;
};

/**
 * 添加到资源包
 */
const addToResourcePackage = () => {
  openAddToResourcePackage();
};

/**
 * 打开添加/更新资源包对话框
 */
const openAddToResourcePackage = () => {
  if (!queryConfig.table || queryConfig.fields.length === 0) {
    ElMessage.warning("请先配置查询条件");
    return;
  }

  // 根据是否在资源包中设置表单初始值
  if (props.isInResourcePackage) {
    // 更新模式：使用现有资源包信息
    resourcePackageForm.name = props.resourcePackageName || "";
    resourcePackageForm.description = "";
    resourcePackageForm.limitConfig = 1000;
    resourcePackageForm.tags = [];
  } else {
    // 创建模式：重置表单
    resourcePackageForm.name = "";
    resourcePackageForm.description = "";
    resourcePackageForm.limitConfig = 1000;
    resourcePackageForm.tags = [];
  }

  resourcePackageVisible.value = true;
};

/**
 * 确认添加/更新资源包
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
      type: PackageType.SQL,
      datasource_id: queryConfig.datasourceId,
      template_type: "sql",
      template_id: currentTemplateId.value, // 使用当前模板ID而不是选中的模板ID
      dynamic_params: queryConfig.conditions.reduce(
        (params: any, condition: any) => {
          params[condition.param_name] = condition.default_value || "";
          return params;
        },
        {},
      ),
      // 关联数据资源ID（若存在）以便后续查询设定能加载资源详情
      resource_id: queryConfig.resourceId || null,
      tags: resourcePackageForm.tags,
      is_active: true,
    };

    console.log("📦 构建资源包数据:", packageData);
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

/**
 * 加载可用的SQL模板列表
 */
const loadAvailableTemplates = async () => {
  console.log("🔄 loadAvailableTemplates 被调用，当前状态:", {
    resourceId: queryConfig.resourceId,
    datasourceId: queryConfig.datasourceId,
    initialResourceId: props.initialResourceId,
    lastLoadedResourceId: lastLoadedResourceId.value,
    isLoading: loadingTemplates.value,
  });

  // 如果没有resourceId，尝试使用props中的初始值
  if (!queryConfig.resourceId && props.initialResourceId) {
    queryConfig.resourceId = props.initialResourceId;
    console.log("📝 从props设置resourceId:", queryConfig.resourceId);
  }

  if (!queryConfig.resourceId) {
    console.log("⚠️ resourceId为空，清空模板列表");
    availableTemplates.value = [];
    lastLoadedResourceId.value = null;
    return;
  }

  // 防重复调用：如果正在加载或已经为相同resourceId加载过，则跳过
  if (loadingTemplates.value) {
    console.log("⏳ 模板正在加载中，跳过重复调用");
    return;
  }

  if (lastLoadedResourceId.value === queryConfig.resourceId) {
    console.log("✅ 相同resourceId已加载过模板，跳过重复调用");
    return;
  }

  try {
    loadingTemplates.value = true;
    console.log("🔄 开始加载模板列表，resourceId:", queryConfig.resourceId);

    // 调用API获取模板列表
    const response = await getSQLTemplates({
      dataResourceId: queryConfig.resourceId,
      isTemplate: true,
    });

    console.log("📊 API响应:", response);

    if (response.data && response.data.length > 0) {
      // 按ID降序排序，最新的在前面
      availableTemplates.value = response.data.sort((a, b) => b.id - a.id);
      console.log(
        "✅ 模板列表加载成功，数量:",
        availableTemplates.value.length,
      );
      console.log(
        "📋 模板列表详情:",
        availableTemplates.value.map((t) => ({ id: t.id, name: t.name })),
      );

      // 自动选择最新的模板（第一个）
      const latestTemplate = availableTemplates.value[0];
      if (latestTemplate) {
        console.log("🎯 自动选择最新模板:", latestTemplate.name);
        selectedTemplateId.value = latestTemplate.id;
        currentTemplateId.value = latestTemplate.id;
        saveQueryForm.name = latestTemplate.name;
        saveQueryForm.description = latestTemplate.description || "";
        saveQueryForm.tags = latestTemplate.tags || [];

        // 加载模板配置
        await loadTemplate(latestTemplate);
      }
    } else {
      availableTemplates.value = [];
      console.log("⚠️ API响应为空或没有找到可用的模板");
    }
  } catch (error) {
    console.error("❌ 加载模板列表失败:", error);
    availableTemplates.value = [];
    ElMessage.error("加载模板列表失败");
  } finally {
    loadingTemplates.value = false;
    // 记录成功加载的resourceId，防止重复调用
    lastLoadedResourceId.value = queryConfig.resourceId;
    console.log("🏁 模板加载完成，最终状态:", {
      templatesCount: availableTemplates.value.length,
      loading: loadingTemplates.value,
      lastLoadedResourceId: lastLoadedResourceId.value,
    });
  }
};

/**
 * 模板选择变更处理
 * @param templateId 选择的模板ID
 */
const onTemplateChange = async (templateId: number | null) => {
  console.log("🔄 模板选择变更:", templateId);

  if (!templateId) {
    // 清空选择，不做任何操作
    selectedTemplateId.value = null;
    return;
  }

  // 查找选中的模板
  const selectedTemplate = availableTemplates.value.find(
    (template) => template.id === templateId,
  );
  if (!selectedTemplate) {
    ElMessage.error("未找到选中的模板");
    return;
  }

  try {
    console.log("🔄 开始加载选中的模板:", selectedTemplate);

    // 使用现有的loadTemplate方法加载模板
    await loadTemplate(selectedTemplate);

    // 更新当前模板ID和保存表单信息
    currentTemplateId.value = selectedTemplate.id;
    saveQueryForm.name = selectedTemplate.name;
    saveQueryForm.description = selectedTemplate.description || "";
    saveQueryForm.tags = selectedTemplate.tags || [];

    console.log("✅ 模板加载完成");
  } catch (error) {
    console.error("❌ 加载选中模板失败:", error);
    ElMessage.error("加载选中模板失败");
  }
};

/**
 * 设置当前模板ID
 * @param templateId 模板ID
 */
const setCurrentTemplateId = (templateId: number) => {
  currentTemplateId.value = templateId;
  console.log("✅ 设置当前模板ID:", templateId);
};

// 暴露方法给父组件
defineExpose({
  clearQuery,
  executeQuery,
  loadTemplate,
  setQueryResults,
  handleQueryError,
  resetQueryState,
  setCurrentTemplateId,
});
</script>

<style scoped>
.sql-query-builder {
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

.query-section {
  margin-bottom: 24px;
}

.section-title {
  margin: 0 0 16px 0;
  font-size: 16px;
  font-weight: 600;
  color: #303133;
  display: flex;
  align-items: center;
  gap: 8px;
}

.fields-selection {
  border: 1px solid #dcdfe6;
  border-radius: 4px;
  padding: 16px;
}

.field-groups {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
}

.available-fields,
.selected-fields {
  min-width: 0; /* 防止在网格中子项固定宽度导致溢出 */
}

/* 小屏幕下字段选择区域改为单列，避免溢出 */
@media (max-width: 768px) {
  .field-groups {
    grid-template-columns: 1fr;
  }
}

.available-fields h5,
.selected-fields h5 {
  margin: 0 0 12px 0;
  font-size: 14px;
  font-weight: 600;
  color: #606266;
}

.fields-list {
  min-height: 200px;
  max-height: 300px;
  overflow-y: auto;
  overflow-x: hidden;
  border: 1px solid #ebeef5;
  border-radius: 4px;
  padding: 8px;
}

.field-item {
  display: flex;
  align-items: center;
  flex-wrap: wrap; /* 允许在小屏幕下换行，避免横向溢出 */
  gap: 8px;
  padding: 8px;
  margin-bottom: 4px;
  border-radius: 4px;
  cursor: pointer;
  transition: background-color 0.2s;
}

.field-item:hover {
  background-color: #f5f7fa;
}

.field-item.selected {
  background-color: #e1f3d8;
}

/* 字段搜索样式 */
.field-search {
  margin-bottom: 12px;
}

.field-search .el-input {
  width: 100%;
}

.field-search .el-input__wrapper {
  border-radius: 6px;
}

.search-highlight {
  background-color: #ffd04b;
  color: #606266;
  padding: 1px 2px;
  border-radius: 2px;
  font-weight: 500;
}

.field-item.highlighted {
  border: 1px solid #409eff;
  background-color: #ecf5ff;
}

.field-item.highlighted:hover {
  background-color: #d9ecff;
}

.no-fields-found {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40px 20px;
  color: #909399;
  font-size: 14px;
  text-align: center;
}

.no-fields-found .el-icon {
  font-size: 48px;
  margin-bottom: 12px;
  opacity: 0.5;
}

.field-name {
  flex: 1;
  font-size: 14px;
  word-break: break-word; /* 长字段名在小屏幕下换行，避免溢出 */
}

.field-info {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.field-description {
  font-size: 12px;
  color: #909399;
  line-height: 1.2;
}

.empty-fields {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 40px;
  color: #909399;
  font-size: 14px;
}

.conditions-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.condition-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  background-color: #f8f9fa;
  border-radius: 4px;
}

.sql-preview {
  background-color: #f8f9fa;
  border: 1px solid #ebeef5;
  border-radius: 4px;
  padding: 16px;
}

.sql-preview pre {
  margin: 0;
  font-family: "Courier New", monospace;
  font-size: 14px;
  line-height: 1.5;
  color: #303133;
  white-space: pre-wrap;
  word-break: break-all;
}

.results-card {
  margin-top: 20px;
}

.results-content {
  min-height: 200px;
}

.empty-results {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 200px;
}

.resource-option,
.table-option {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
}

.table-count {
  color: #909399;
  font-size: 12px;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
}

.template-option {
  display: flex;
  flex-direction: column;
  gap: 4px;
  width: 100%;
}

.template-name {
  font-weight: 600;
  color: #303133;
}

.template-desc {
  font-size: 12px;
  color: #909399;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

/* 已选字段别名输入框在小屏幕下占满行，提升可读性 */
@media (max-width: 768px) {
  .selected-fields .alias-input {
    width: 100%;
  }
}

/* 模板条件配置样式 */
.template-conditions {
  background: #f8f9fa;
  border-radius: 8px;
  padding: 16px;
  border: 1px solid #e4e7ed;
}

.condition-group {
  margin-bottom: 20px;
}

.condition-group:last-child {
  margin-bottom: 0;
}

.condition-group-title {
  margin: 0 0 12px 0;
  font-size: 14px;
  font-weight: 600;
  display: flex;
  align-items: center;
  gap: 8px;
}

.condition-group-title.required {
  color: #e6a23c;
}

.condition-group-title.required::before {
  content: "●";
  color: #f56c6c;
  font-size: 12px;
}

.condition-group-title.optional {
  color: #909399;
}

.condition-group-title.optional::before {
  content: "○";
  color: #909399;
  font-size: 12px;
}

.condition-group-title.locked {
  color: #f56c6c;
  background: #fef0f0;
  padding: 8px 12px;
  border-radius: 4px;
  border: 1px solid #fbc4c4;
}

.condition-group-title.locked::before {
  content: "";
}

/* 锁定条件样式 */
.locked-condition {
  position: relative;
  background-color: #fef0f0;
  border: 1px solid #fbc4c4;
  border-radius: 4px;
  padding: 8px;
}

.condition-item.locked-condition {
  background-color: #fef0f0;
  border: 1px solid #fbc4c4;
  border-radius: 4px;
  padding: 8px;
}

.locked-condition-display {
  display: flex;
  align-items: center;
  gap: 8px;
}

.locked-input {
  flex: 1;
}

.locked-input :deep(.el-input__inner) {
  background-color: #f5f7fa !important;
  border-color: #e4e7ed !important;
  color: #909399 !important;
  cursor: not-allowed;
}

.locked-input :deep(.el-input__prefix) {
  color: #f56c6c;
}

.lock-icon {
  color: #f56c6c;
  font-size: 14px;
}

.locked-reason {
  display: flex;
  align-items: center;
}

.info-icon {
  color: #909399;
  font-size: 16px;
  cursor: help;
}

.info-icon:hover {
  color: #409eff;
}
</style>
