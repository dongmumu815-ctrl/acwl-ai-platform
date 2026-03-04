<template>
  <div class="es-package-query-panel">
    <!-- 标题与操作 -->
    <el-card class="header-card package-info-card" shadow="never">
      <template #header>
        <div class="card-header">
          <span class="card-title">资源中心查询</span>
          <div class="header-actions">
            <el-button
              type="primary"
              size="small"
              :disabled="!results?.hits?.hits?.length"
              @click="openExportDialog('current')"
            >
              <el-icon style="margin-right: 4px"><Download /></el-icon>
              导出当前页结果
            </el-button>
            <el-button
              type="primary"
              size="small"
              :disabled="!results?.hits?.hits?.length"
              @click="openExportDialog('all')"
            >
              <el-icon style="margin-right: 4px"><Download /></el-icon>
              导出全部结果
            </el-button>

            <!-- 导出进度显示 -->
            <div
              v-if="
                exportStatus === 'processing' ||
                exportStatus === 'completed' ||
                latestFileAvailable
              "
              class="export-progress"
            >
              <el-progress
                v-if="exportPercentage !== undefined"
                :percentage="exportPercentage"
                :stroke-width="8"
                :status="
                  exportStatus === 'failed'
                    ? 'exception'
                    : exportStatus === 'completed'
                      ? 'success'
                      : undefined
                "
                style="width: 180px; margin-left: 8px"
              />
              <div v-if="exportProgress" class="export-progress-text">
                <span v-if="exportProgress?.total != null"
                  >已处理 {{ formatNumber(exportProgress?.processed) }} /
                  {{ formatNumber(exportProgress?.total) }}</span
                >
                <span v-else
                  >已处理
                  {{ formatNumber(exportProgress?.processed || 0) }}</span
                >
                <span class="divider">|</span>
                <span>页 {{ exportProgress?.pages_fetched || 0 }}</span>
                <span class="divider">|</span>
                <span>分片 {{ exportProgress?.files_generated || 0 }}</span>
              </div>
              <div v-else class="export-progress-text">已有可下载文件</div>
              <el-link
                v-if="canDownloadNow || latestFileAvailable"
                type="primary"
                :underline="true"
                style="margin-left: 8px"
                @click="downloadExportFile"
              >
                <el-icon><Download /></el-icon>
                下载文件
              </el-link>
            </div>
          </div>
        </div>
      </template>
      <div class="section filters-detail-section">
        <div class="section-body">
          <div class="section-body">
            <div class="header-search">
              <el-input
                v-model="defaultSearchValue"
                placeholder="输入搜索关键词"
                clearable
                class="search-input"
                style="width: 75%"
                @keyup.enter="executeQuery"
              >
                <!-- 前缀下拉选项 -->
                <template #prepend>
                  <el-select
                    v-model="defaultSearchField"
                    placeholder="全部字段"
                    style="width: 150px; height: 100%"
                    filterable
                    :disabled="availableFieldNames.length === 0"
                  >
                    <el-option label="全部字段" value="" />
                    <el-option
                      v-for="f in availableFieldNames"
                      :key="f"
                      :label="getFieldDisplayName(f)"
                      :value="f"
                    />
                  </el-select>
                </template>
                <template #append>
                  <el-button
                    type="primary"
                    :icon="Search"
                    @click="executeQuery"
                  />
                </template>
              </el-input>
              <el-button
                class="advanced-toggle-btn"
                size="default"
                plain
                type="info"
                text
                @click="toggleAdvanced"
              >
                >>高级搜索
              </el-button>
            </div>
          </div>
          <div v-if="fixedConditions.length" class="locked-conditions">
            <span class="section-title">限定条件</span>
            <div class="condition-list">
              <el-tag
                v-for="(cond, idx) in fixedConditions"
                :key="idx"
                type="warning"
                class="condition-tag"
              >
                <el-icon style="margin-right: 4px"><Lock /></el-icon>
                {{ formatFixedCondition(cond) }}
              </el-tag>
            </div>
          </div>

          <!-- 高级检索：点击按钮后展示，查询/重置/添加条件都在此处 -->
          <div v-if="showAdvanced" class="query-builder">
            <div class="qb-header">
              <span class="section-title">高级检索</span>
              <div class="qb-actions">
                <el-button
                  plain
                  type="primary"
                  size="small"
                  :loading="loading"
                  @click="executeQuery"
                  >查询</el-button
                >
                <el-button size="small" @click="resetConditions"
                  >重置</el-button
                >
                <el-button
                  plain
                  type="primary"
                  size="small"
                  :disabled="availableFieldNames.length === 0"
                  @click="addCondition"
                >
                  <el-icon><Plus /></el-icon>
                  添加条件
                </el-button>
                <el-button size="small" @click="toggleAdvanced">收起</el-button>
              </div>
            </div>
            <div v-show="!conditionsCollapsed" class="conditions">
              <div v-for="(c, i) in conditions" :key="i" class="condition-item">
                <el-select
                  v-if="i > 0"
                  v-model="c.logic"
                  size="small"
                  style="width: 90px"
                >
                  <el-option label="AND" value="must" />
                  <el-option label="OR" value="should" />
                  <el-option label="NOT" value="must_not" />
                </el-select>
                <div
                  v-else
                  :style="{ width: '90px', display: 'inline-block' }"
                ></div>

                <el-select
                  v-model="c.field"
                  size="small"
                  style="width: 180px"
                  filterable
                  :disabled="availableFieldNames.length === 0"
                >
                  <el-option label="全部字段" value="_all_fields" />
                  <el-option
                    v-for="f in availableFieldNames"
                    :key="f"
                    :label="getFieldDisplayName(f)"
                    :value="f"
                  />
                </el-select>

                <el-select v-model="c.type" size="small" style="width: 140px">
                  <el-option label="匹配 (match)" value="match" />
                  <el-option label="精确 (term)" value="term" />
                  <el-option label="范围 (range)" value="range" />
                  <el-option label="存在 (exists)" value="exists" />
                  <el-option label="通配符 (wildcard)" value="wildcard" />
                  <el-option label="前缀 (prefix)" value="prefix" />
                </el-select>

                <template v-if="c.type === 'range'">
                  <el-input
                    v-model="c.value.gte"
                    size="small"
                    placeholder="最小值"
                    style="width: 120px"
                  />
                  <span class="dash">-</span>
                  <el-input
                    v-model="c.value.lte"
                    size="small"
                    placeholder="最大值"
                    style="width: 120px"
                  />
                </template>
                <template v-else-if="c.type === 'exists'">
                  <el-tag size="small" type="info">字段存在</el-tag>
                </template>
                <template v-else>
                  <el-input
                    v-model="c.value"
                    size="small"
                    placeholder="查询值"
                    style="width: 260px"
                  />
                </template>

                <el-button
                  size="small"
                  type="danger"
                  plain
                  @click="removeCondition(i)"
                >
                  <el-icon><Delete /></el-icon>
                </el-button>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div
        class="section filters-detail-section results-card"
        :class="{ 'fullscreen-mode': isFullscreen }"
      >
        <div class="section-header">
          <span class="section-title">聚合结果</span>
          <div class="header-actions">
            <div class="view-switch">
              <!-- <el-radio-group v-model="viewMode" size="small">
                <el-radio-button label="card">卡片</el-radio-button>
                <el-radio-button label="list">列表</el-radio-button>
              </el-radio-group> -->
              <div class="display-toggles">
                <el-switch
                  v-model="compactMode"
                  size="small"
                  active-text="紧凑"
                  inactive-text="常规"
                />
                <el-switch
                  v-model="wrapLongText"
                  size="small"
                  active-text="自动换行"
                  inactive-text="省略"
                />
                <el-button
                  size="small"
                  :type="isFullscreen ? 'default' : 'primary'"
                  :icon="FullScreen"
                  @click="toggleFullscreen"
                >
                  {{ isFullscreen ? "退出全屏" : "全屏显示" }}
                </el-button>
                <el-button
                  size="small"
                  :type="isAllSelected ? 'success' : 'default'"
                  :icon="Check"
                  style="margin-left: 8px"
                  @click="toggleSelectAll"
                >
                  {{ isAllSelected ? "取消全选" : "全选当前页" }}
                </el-button>
                <span
                  class="selected-count"
                  style="
                    margin-left: 8px;
                    color: var(--el-text-color-secondary);
                  "
                >
                  已选 {{ selectedCount }} 条
                </span>
              </div>
            </div>
          </div>
        </div>
        <div class="section-body">
          <!-- 结果展示：左右两栏 -->
          <div v-loading="loading" class="section results-section">
            <!-- <div class="section-header">
          <div class="results-header">
            <span class="section-title">查询结果</span>
          </div>
        </div> -->
            <div class="section-body">
              <div v-if="!results" class="no-data">
                <el-empty description="暂无结果，配置条件后点击查询" />
              </div>

              <div v-else class="results-grid">
                <!-- 左侧聚合结果 20% -->
                <div class="agg-pane" ref="aggPaneRef">
                  <!-- <div class="agg-header">聚合结果</div> -->
                  <div v-if="!results.aggregations" class="agg-empty">
                    <el-empty description="无聚合数据" :image-size="60" />
                  </div>
                  <div v-else class="aggregations">
                    <el-collapse v-model="activeAggs">
                      <el-collapse-item
                        v-for="(agg, aggName) in normalizedAggs"
                        :key="aggName"
                        :name="aggName"
                        class="agg-card"
                      >
                        <template #title>
                          <div class="agg-title">
                            <span>{{ aggName }}</span>
                          </div>
                        </template>
                        <div class="agg-body agg-scroll">
                          <template v-if="agg.type === 'terms'">
                            <div
                              v-for="bucket in agg.buckets.slice(0, 4000)"
                              :key="bucket.key"
                              class="agg-row clickable"
                              @click="onAggBucketClick(String(aggName), bucket)"
                            >
                              <span class="agg-key">{{
                                formatAggKey(bucket.key)
                              }}</span>
                              <span class="agg-count">{{
                                bucket.doc_count
                              }}</span>
                            </div>
                          </template>
                          <template
                            v-else-if="
                              [
                                'sum',
                                'avg',
                                'max',
                                'min',
                                'value_count',
                              ].includes(agg.type)
                            "
                          >
                            <div class="agg-row">
                              <span class="agg-key">值</span>
                              <span class="agg-count">{{ agg.value }}</span>
                            </div>
                          </template>
                          <template v-else>
                            <pre class="agg-json">{{
                              JSON.stringify(agg.raw, null, 2)
                            }}</pre>
                          </template>
                        </div>
                      </el-collapse-item>
                    </el-collapse>
                  </div>
                </div>

                <!-- 右侧查询结果 80% -->
                <div class="result-pane">
                  <template v-if="viewMode === 'list'">
                    <div class="table-container" ref="tableContainerRef" @scroll="onResultScroll">
                      <el-table
                        ref="tableRef"
                        :data="processedRecords"
                        border
                        stripe
                        :size="compactMode ? 'small' : 'default'"
                        style="width: 100%"
                        @sort-change="onSortChange"
                        @row-click="openRowDetail"
                        @selection-change="onTableSelectionChange"
                      >
                        <el-table-column type="selection" width="48" />
                        <el-table-column type="index" label="#" width="60" />
                        <el-table-column
                          v-for="col in displayFields"
                          :key="col"
                          :prop="col"
                          :label="getFieldDisplayName(col)"
                          min-width="100"
                          sortable="custom"
                        >
                          <template #default="{ row }">
                            <template v-if="col === 'snippet' && row?.pdf_url && row?.pdf_url !== 'null' && row?.pageNumber">
                              <span
                                :class="wrapLongText ? 'cell wrap' : 'cell ellipsis'"
                                style="cursor: pointer"
                                @click.stop="openPdfAtHit(row)"
                                v-html="
                                  formatTextWithHighlight(
                                    formatCell(row[col]),
                                    DEFAULT_MAX_CHARS,
                                    executedSearchValue,
                                  )
                                "
                              ></span>
                            </template>
                            <template v-else>
                              <span
                                :class="wrapLongText ? 'cell wrap' : 'cell ellipsis'"
                                v-html="
                                  formatTextWithHighlight(
                                    formatCell(row[col]),
                                    DEFAULT_MAX_CHARS,
                                    executedSearchValue,
                                  )
                                "
                              ></span>
                            </template>
                          </template>
                        </el-table-column>
                      </el-table>

                      <!-- PDF 预览弹窗 -->
                      <el-dialog
                        v-model="pdfDialogVisible"
                        title="全文预览"
                        width="80%"
                      >
                        <PdfViewer :src="pdfUrl || ''" />
                      </el-dialog>
                    </div>
                  </template>

                  <template v-else>
                    <!-- <div class="result-summary">
                      检索结果：为您检索到 {{ totalHits }} 条结果
                    </div> -->
                    <div class="cards-container" ref="cardsContainerRef" @scroll="onCardsScroll">
                      <div class="cards" :class="{ compact: compactMode }">
                        <el-card
                          v-for="(row, idx) in visibleRecords"
                          :key="idx"
                          class="result-card"
                          shadow="never"
                        >
                          <div class="card-content">
                            <!-- 
                            <el-tooltip content="复制" placement="top">
                              <el-button
                                size="small"
                                circle
                                class="card-copy-btn"
                                @click="copyRow(row)"
                              >
                                <el-icon><CopyDocument /></el-icon>
                              </el-button>
                            </el-tooltip>
                            -->
                            <div class="card-title-row">
                              <el-checkbox
                                :model-value="isCardSelected(idx)"
                                style="margin-right: 8px"
                                @change="
                                  (val: boolean) =>
                                    toggleCardSelection(idx, val)
                                "
                              />
                              <el-link
                                type="primary"
                                :underline="false"
                                class="card-title-link"
                                @click="openRowDetail(row)"
                              >
                                <span
                                  v-html="
                                    formatTextWithHighlight(
                                      formatCell(row[getTitleField(row)]),
                                      null,
                                      executedSearchValue,
                                    )
                                  "
                                ></span>
                              </el-link>
                            </div>
                            <div class="card-row wide">
                              <div
                                v-for="f in getKeyFields(row)"
                                :key="f"
                                class="kv"
                              >
                                <span class="k"
                                  >{{ getFieldDisplayName(f) }}：</span
                                >
                                <span
                                  class="v"
                                  :class="{ wrap: wrapLongText }"
                                  v-if="!(f === 'snippet' && row?.pdf_url && row?.pdf_url !== 'null' && row?.pageNumber)"
                                  v-html="
                                    formatTextWithHighlight(
                                      formatCell(row[f]),
                                      DEFAULT_MAX_CHARS,
                                      executedSearchValue,
                                    )
                                  "
                                ></span>
                                <template v-else>
                                  <span
                                    class="v"
                                    :class="{ wrap: wrapLongText }"
                                    style="cursor: pointer"
                                    @click.stop="openPdfAtHit(row)"
                                    v-html="
                                      formatTextWithHighlight(
                                        formatCell(row[f]),
                                        DEFAULT_MAX_CHARS,
                                        executedSearchValue,
                                      )
                                    "
                                  ></span>
                                </template>
                                <template v-if="f === 'publication_category'">
                                  <el-icon
                                    v-if="
                                      String(row[f]).toUpperCase() === 'BOOK'
                                    "
                                    style="margin-left: 6px; color: #6b7fd7"
                                  >
                                    <Reading />
                                  </el-icon>
                                  <el-icon
                                    v-else-if="
                                      String(row[f]).toUpperCase() ===
                                      'JOURNAL_ARTICLE'
                                    "
                                    style="margin-left: 6px; color: #e37b40"
                                  >
                                    <Document />
                                  </el-icon>
                                </template>
                              </div>
                            </div>
                            <!-- 描述字段单独展示（如果存在），使用宽行显示更易读 -->
                            <div
                              v-if="
                                row &&
                                'description' in row &&
                                row['description'] !== undefined &&
                                row['description'] !== null
                              "
                              class="card-row wide"
                            >
                              <div class="kv">
                                <span class="k">{{
                                  getFieldDisplayName("description")
                                }}</span>
                                <span
                                  class="v"
                                  :class="{ wrap: wrapLongText }"
                                  v-html="
                                    formatTextWithHighlight(
                                      formatCell(row['description']),
                                      DEFAULT_MAX_CHARS,
                                      executedSearchValue,
                                    )
                                  "
                                ></span>
                              </div>
                            </div>
                          </div>
                        </el-card>
                      </div>
                    </div>
                  </template>
                  <div v-if="results" class="pager">
                    <el-pagination
                      v-model:current-page="currentPage"
                      v-model:page-size="pageSize"
                      :page-sizes="[10, 20, 50, 100, 1000, 2000, 3000, 4000]"
                      layout="total, sizes, prev, pager, next, jumper"
                      :total="totalHits"
                      @current-change="onPageChange"
                      @size-change="onPageSizeChange"
                    />
                  </div>
                  <!-- 通用：行详情弹窗（列表与卡片视图均可用） -->
                  <el-drawer
                    v-model="detailVisible"
                    :with-header="false"
                    size="60%"
                    class="detail-drawer"
                  >
                    <div class="detail-header">
                      <el-page-header @back="detailVisible = false">
                        <template #icon>
                          <el-icon style="font-size: 22px"
                            ><ArrowLeft
                          /></el-icon>
                        </template>
                        <template #title>
                          <span style="font-size: 22px">数据详情</span>
                        </template>
                      </el-page-header>
                    </div>
                    <div class="detail-body narrow-content">
                      <el-collapse
                        v-model="activeInfos"
                        class="detail-collapse"
                      >
                        <el-collapse-item name="basic">
                          <template #title>
                            <div class="collapse-title">
                              <span class="left-bar"></span>
                              <span class="title-text">基本信息</span>
                            </div>
                          </template>
                          <div class="collapse-content">
                            <el-form
                              label-position="left"
                              label-width="180px"
                              class="detail-form"
                            >
                              <el-form-item
                                v-for="f in basicDisplayFields"
                                :key="f"
                                :label="getFieldDisplayName(f) + '：'"
                              >
                                <!-- 如果是PDF字段且有值，显示为可点击链接 -->
                                <template
                                  v-if="
                                    f === 'pdf_url' &&
                                    selectedRow?.[f] &&
                                    selectedRow?.[f] !== 'null'
                                  "
                                >
                                  <a
                                    :href="selectedRow[f]"
                                    target="_blank"
                                    class="pdf-link"
                                    style="
                                      color: #409eff;
                                      text-decoration: none;
                                      cursor: pointer;
                                    "
                                  >
                                    查看PDF文档
                                  </a>
                                </template>
                                <!-- 其他字段正常显示 -->
                                <span
                                  v-else
                                  :class="
                                    wrapLongText ? 'cell wrap' : 'cell ellipsis'
                                  "
                                  style="
                                    white-space: pre-wrap;
                                    word-break: break-word;
                                  "
                                  v-html="
                                    formatTextWithHighlight(
                                      typeof selectedRow?.[f] === 'object'
                                        ? JSON.stringify(
                                            selectedRow?.[f],
                                            null,
                                            2,
                                          )
                                        : selectedRow?.[f],
                                      null,
                                      executedSearchValue,
                                    )
                                  "
                                ></span>
                              </el-form-item>
                            </el-form>
                          </div>
                        </el-collapse-item>
                        <!-- 注释掉全文PDF预览功能
                        <template v-if="selectedRow && selectedRow['pdf_url'] && selectedRow['pdf_url'] !== 'null'">
                          <el-collapse-item name="pdfInfo">
                            <template #title>
                              <div class="collapse-title">
                                <span class="left-bar"></span>
                                <span class="title-text">全文信息</span>
                              </div>
                            </template>
                            <div class="collapse-content">
                              <div class="pdf-inline-preview" style="margin-top: 8px;">
                                <PdfViewer :src="String(selectedRow['pdf_url'])" />
                              </div>
                            </div>
                          </el-collapse-item>
                        </template>
                        -->
                      </el-collapse>
                    </div>
                  </el-drawer>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </el-card>

    <!-- 导出字段选择弹窗 -->
    <el-dialog v-model="exportDialogVisible" title="导出选项" width="500px">
      <div style="margin-bottom: 16px">
        <span style="font-weight: bold; margin-right: 8px">导出范围:</span>
        <el-tag>{{
          exportType === "current" ? "当前页结果" : "全部查询结果"
        }}</el-tag>
      </div>
      <div style="margin-bottom: 8px; font-weight: bold">选择导出字段:</div>
      <el-checkbox
        v-model="checkAllExportFields"
        :indeterminate="isIndeterminateExportFields"
        @change="handleCheckAllExportFieldsChange"
      >
        全选
      </el-checkbox>
      <div style="margin: 10px 0"></div>
      <el-checkbox-group
        v-model="selectedExportFields"
        class="export-fields-group"
        @change="handleCheckedExportFieldsChange"
      >
        <el-checkbox
          v-for="field in availableFieldNames"
          :key="field"
          :label="field"
        >
          {{ getFieldDisplayName(field) }}
        </el-checkbox>
      </el-checkbox-group>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="exportDialogVisible = false">取消</el-button>
          <el-button
            type="primary"
            :loading="exportLoading"
            @click="executeExport"
          >
            确认导出
          </el-button>
        </span>
      </template>
    </el-dialog>
    <!-- 下载资源包功能已禁用 -->
  </div>
</template>

<script setup lang="ts">
import {
  ref,
  reactive,
  computed,
  onMounted,
  watch,
  nextTick,
  onUnmounted,
} from "vue";

import { ElMessage, ElMessageBox } from "element-plus";
import {
  Lock,
  Plus,
  Delete,
  CopyDocument,
  Search,
  Download,
  FullScreen,
  CaretRight,
  CaretBottom,
  Reading,
  Collection,
  Document,
  Check,
} from "@element-plus/icons-vue";
import { ArrowLeft, Close } from "@element-plus/icons-vue";
import { templateApi } from "@/api/template";
import { executeESQuery, getESFieldMapping } from "@/api/esQuery";
import { dataResourceApi } from "@/api/dataResource";
import { resourcePackageApi } from "@/api/resourcePackage";
import type { ResourcePackageFile } from "@/api/resourcePackage";
import PdfViewer from "@/components/PdfViewer.vue";
import * as XLSX from "xlsx";

const props = defineProps<{ packageData: any }>();

const aggPaneRef = ref<HTMLElement | null>(null);
const cardsContainerRef = ref<HTMLElement | null>(null);
const tableContainerRef = ref<HTMLElement | null>(null);
const AGG_SCROLL_RATIO = 0.6;

const loading = ref(false);
const downloadLoading = ref(false);
const generateLoading = ref(false);
const latestDownloadLoading = ref(false);
const downloadDialogVisible = ref(false);
const dialogData = reactive<{
  excel_time?: string;
  download_time?: string;
  download_url?: string;
}>({
  excel_time: undefined,
  download_time: undefined,
  download_url: undefined,
});

// 历史文件相关状态
const historyFiles = ref<ResourcePackageFile[]>([]);
const selectedFileId = ref<number | null>(null);
const historyLoading = ref(false);
const historyDownloadLoading = ref(false);
const templateDetail = ref<any | null>(null);
const fixedConditions = ref<any[]>([]);
const sourceFields = ref<string[]>([]);
const availableFields = ref<Array<{ name: string; type?: string }>>([]);
const availableFieldNames = computed(() =>
  sourceFields.value.length > 0
    ? sourceFields.value
    : availableFields.value.map((f) => f.name),
);
const selectedIndices = ref<string[]>([]);

// 字段映射信息，用于显示字段注释
const fieldMappings = ref<
  Record<
    string,
    { name: string; type: string; comment?: string; display_name: string }
  >
>({});

type Logic = "must" | "should" | "must_not";
type Cond = { field: string; type: string; value: any; logic: Logic };
const conditions = reactive<Cond[]>([]);
const conditionsCollapsed = ref(false);
// 高级检索显示与折叠
const showAdvanced = ref(false);
const toggleAdvanced = () => {
  showAdvanced.value = !showAdvanced.value;
};

// 默认搜索相关状态
const defaultSearchField = ref<string>("");
const defaultSearchValue = ref<string>("");
// 已执行查询的搜索词，用于高亮显示
const executedSearchValue = ref<string | string[]>("");

const viewMode = ref<"list" | "card">("card");
const compactMode = ref(true);
const wrapLongText = ref(false);
const isFullscreen = ref(false);
// 左侧聚合展开项（使用 Collapse 组件）
const activeAggs = ref<string[]>([]);
// 抽屉内展开项
const activeInfos = ref<string[]>(["basic", "pdfInfo"]);
const results = ref<any | null>(null);

function stripTags(html: string): string {
  if (!html) return "";
  return html.replace(/<[^>]*>/g, "");
}
function extractSentence(
  text: string,
  keyword: string | string[],
  maxLen = 200,
): string {
  if (!text) return "";
  if (!keyword)
    return text.length > maxLen ? text.slice(0, maxLen) + "…" : text;
  if (Array.isArray(keyword) && keyword.length === 0)
    return text.length > maxLen ? text.slice(0, maxLen) + "…" : text;

  const lower = text.toLowerCase();
  let idx = -1;
  let kLen = 0;

  if (Array.isArray(keyword)) {
    // 找到第一个匹配的关键词
    for (const k of keyword) {
      if (!k || typeof k !== "string") continue;
      const i = lower.indexOf(k.toLowerCase());
      if (i >= 0) {
        idx = i;
        kLen = k.length;
        break; // 找到一个即可
      }
    }
  } else {
    idx = lower.indexOf(keyword.toLowerCase());
    kLen = keyword.length;
  }

  if (idx < 0) {
    return text.length > maxLen ? text.slice(0, maxLen) + "…" : text;
  }
  // 寻找句子边界（中英文常见标点）
  const left = Math.max(
    text.lastIndexOf("。", idx),
    text.lastIndexOf("！", idx),
    text.lastIndexOf("？", idx),
    text.lastIndexOf(";", idx),
    text.lastIndexOf(".", idx),
    text.lastIndexOf("!", idx),
    text.lastIndexOf("?", idx),
  );
  const rightCandidates = [
    text.indexOf("。", idx),
    text.indexOf("！", idx),
    text.indexOf("？", idx),
    text.indexOf(";", idx),
    text.indexOf(".", idx),
    text.indexOf("!", idx),
    text.indexOf("?", idx),
  ].filter((v) => v >= 0);
  const right = rightCandidates.length ? Math.min(...rightCandidates) : -1;
  const start = left >= 0 ? left + 1 : 0;
  const end = right >= 0 ? right + 1 : text.length;
  const sentence = text.slice(start, end).trim();
  if (sentence.length > maxLen) {
    // 过长时，以关键词为中心截取
    const half = Math.floor(maxLen / 2);
    const s = Math.max(0, idx - half);
    const e = Math.min(text.length, idx + kLen + half);
    return (s > 0 ? "…" : "") + text.slice(s, e) + (e < text.length ? "…" : "");
  }
  return sentence;
}

const records = computed<any[]>(() => {
  const hits = results.value?.hits?.hits || [];
  let keyword: string | string[] = "";
  if (Array.isArray(executedSearchValue.value)) {
    keyword = executedSearchValue.value;
  } else {
    keyword = executedSearchValue.value?.trim() || "";
  }

  const isPagesSearch = Boolean(
    defaultSearchField.value &&
    (defaultSearchField.value === "pages" ||
      defaultSearchField.value.startsWith("pages")),
  );
  const expanded: any[] = [];

  hits.forEach((h: any) => {
    const src = h?._source || {};
    const common = { ...src };

    if (isPagesSearch) {
      const inner = h?.inner_hits?.pages?.hits?.hits || [];
      if (inner.length) {
        inner.forEach((ih: any) => {
          const fragments: string[] = ih?.highlight?.["pages.content"] || [];
          const fragHtml = fragments[0] || "";
          const fragPlain = stripTags(fragHtml);
          let pageNum: any = ih?._source?.pages?.pageNumber;
          if (pageNum === undefined || pageNum === null) {
            const pagesArr = Array.isArray(src?.pages) ? src.pages : [];
            const found = pagesArr.find(
              (p: any) =>
                typeof p?.content === "string" && p.content.includes(fragPlain),
            );
            pageNum = found?.pageNumber ?? null;
          }
          expanded.push({
            ...common,
            pageNumber: pageNum ?? null,
            snippet: fragPlain,
          });
        });
        return;
      }
      // fallback：未返回 inner_hits 时，遍历 pages 数组
      const pagesArr = Array.isArray(src?.pages) ? src.pages : [];
      pagesArr.forEach((p: any) => {
        const content: string = String(p?.content ?? "");
        if (!content) return;

        let matched = false;
        if (!keyword) matched = true;
        else if (Array.isArray(keyword)) {
          matched =
            keyword.length === 0 ||
            keyword.some((k) =>
              content.toLowerCase().includes(k.toLowerCase()),
            );
        } else {
          matched = content.toLowerCase().includes(keyword.toLowerCase());
        }

        if (matched) {
          const sent = extractSentence(content, keyword);
          expanded.push({
            ...common,
            pageNumber: p?.pageNumber ?? null,
            snippet: sent,
          });
        }
      });
      return;
    }

    // 非 pages 检索，直接使用原始 _source
    expanded.push(src);
  });

  return expanded;
});
// 卡片视图：增量渲染（滚动加载）
const CARD_INITIAL_BATCH = 50;
const CARD_BATCH_SIZE = 50;
const visibleCount = ref<number>(CARD_INITIAL_BATCH);
const visibleRecords = computed<any[]>(() =>
  records.value.slice(0, Math.max(0, visibleCount.value)),
);
function loadMoreCards() {
  if (visibleCount.value >= records.value.length) return;
  visibleCount.value = Math.min(
    visibleCount.value + CARD_BATCH_SIZE,
    records.value.length,
  );
}
function onCardsScroll(e: Event) {
  const el = e.target as HTMLElement;
  if (!el) return;
  syncAggScroll(el.scrollTop);
  const threshold = 200; // 距底部 200px 触发加载
  if (el.scrollTop + el.clientHeight >= el.scrollHeight - threshold) {
    loadMoreCards();
  }
}

function onResultScroll(e: Event) {
  const el = e.target as HTMLElement;
  if (!el) return;
  syncAggScroll(el.scrollTop);
}

function syncAggScroll(scrollTop: number) {
  const aggEl = aggPaneRef.value;
  if (!aggEl) return;
  const scaledTop = scrollTop * AGG_SCROLL_RATIO;
  const maxTop = Math.max(0, aggEl.scrollHeight - aggEl.clientHeight);
  aggEl.scrollTop = Math.min(Math.max(scaledTop, 0), maxTop);
}
// 全字段搜索与列排序
const sortState = ref<{
  field: string | null;
  order: "ascending" | "descending" | null;
}>({ field: null, order: null });
const processedRecords = computed<any[]>(() => {
  let data = records.value || [];
  const { field, order } = sortState.value;
  if (field && order) {
    data = [...data].sort((a: Record<string, any>, b: Record<string, any>) => {
      const va = a?.[field];
      const vb = b?.[field];
      const na =
        typeof va === "number"
          ? va
          : Number.isFinite(Number(va))
            ? Number(va)
            : null;
      const nb =
        typeof vb === "number"
          ? vb
          : Number.isFinite(Number(vb))
            ? Number(vb)
            : null;
      let cmp = 0;
      if (na !== null && nb !== null) cmp = na - nb;
      else
        cmp = String(formatCell(va)).localeCompare(
          String(formatCell(vb)),
          "zh-CN",
          { numeric: true, sensitivity: "base" },
        );
      return order === "ascending" ? cmp : -cmp;
    });
  }
  return data;
});
// 表格排序事件
const onSortChange = (payload: {
  prop: string;
  order: "ascending" | "descending" | null;
}) => {
  sortState.value = {
    field: payload?.prop || null,
    order: payload?.order || null,
  };
};

// 勾选导出：列表与卡片视图的选中项
const tableRef = ref<any>();
const selectedTableRows = ref<Record<string, any>[]>([]);
const selectedCardIndices = ref<Set<number>>(new Set());
const selectedCount = computed(() =>
  viewMode.value === "list"
    ? selectedTableRows.value.length
    : selectedCardIndices.value.size,
);

const onTableSelectionChange = (rows: Record<string, any>[]) => {
  selectedTableRows.value = rows || [];
};

const isCardSelected = (idx: number) => selectedCardIndices.value.has(idx);
const toggleCardSelection = (idx: number, val: boolean) => {
  if (val) selectedCardIndices.value.add(idx);
  else selectedCardIndices.value.delete(idx);
};

// 数据变化时默认全选当前页的列表与卡片数据
watch(
  processedRecords,
  (rows) => {
    nextTick(() => {
      // 表格选择默认全选
      selectedTableRows.value = [...(rows || [])];
      try {
        tableRef.value?.clearSelection?.();
        (rows || []).forEach((r: Record<string, any>) =>
          tableRef.value?.toggleRowSelection?.(r, true),
        );
      } catch {}
    });
  },
  { immediate: true },
);

watch(
  records,
  (rows) => {
    // 记录变化时重置可见数量（卡片视图）
    visibleCount.value = Math.min(CARD_INITIAL_BATCH, rows.length);
    // 卡片选择默认全选
    selectedCardIndices.value = new Set((rows || []).map((_, i) => i));
  },
  { immediate: true },
);

// 导出弹窗相关状态
const exportDialogVisible = ref(false);
const exportType = ref<"current" | "all">("current");
const checkAllExportFields = ref(false);
const isIndeterminateExportFields = ref(false);
const selectedExportFields = ref<string[]>([]);
const exportLoading = ref(false);

const openExportDialog = (type: "current" | "all") => {
  exportType.value = type;
  exportDialogVisible.value = true;
  // 默认全选所有字段
  selectedExportFields.value = [...availableFieldNames.value];
  checkAllExportFields.value = true;
  isIndeterminateExportFields.value = false;
};

const handleCheckAllExportFieldsChange = (val: boolean) => {
  selectedExportFields.value = val ? [...availableFieldNames.value] : [];
  isIndeterminateExportFields.value = false;
};

const handleCheckedExportFieldsChange = (value: string[]) => {
  const checkedCount = value.length;
  checkAllExportFields.value =
    checkedCount === availableFieldNames.value.length;
  isIndeterminateExportFields.value =
    checkedCount > 0 && checkedCount < availableFieldNames.value.length;
};

const executeExport = async () => {
  if (selectedExportFields.value.length === 0) {
    ElMessage.warning("请至少选择一个导出字段");
    return;
  }

  exportLoading.value = true;
  try {
    await handleExport();
    exportDialogVisible.value = false;
  } catch (error) {
    console.error("导出异常:", error);
    ElMessage.error("导出失败");
  } finally {
    exportLoading.value = false;
  }
};

const handleExport = async () => {
  const columns = selectedExportFields.value;
  let dataToExport: any[] = [];

  if (exportType.value === "current") {
    // 导出当前页：基于当前勾选或当前页所有数据
    // 优先使用勾选的数据
    let candidates =
      viewMode.value === "list"
        ? selectedTableRows.value
        : Array.from(selectedCardIndices.value)
            .map((i) => records.value?.[i])
            .filter(Boolean);

    // 如果没有勾选，则导出当前页所有数据
    if (!candidates || candidates.length === 0) {
      candidates = records.value || [];
    }

    if (candidates.length === 0) {
      ElMessage.warning("当前页无数据可导出");
      return;
    }
    dataToExport = candidates;
  } else {
    // 导出全部：使用后端异步导出（打包功能）
    try {
      await exportAllResults(columns, true);
    } catch (e) {
      console.error(e);
      ElMessage.error("发起导出任务失败");
    }
    // 不需要在此处调用 exportToCSV，因为后端会处理文件生成
    return;
  }

  if (dataToExport.length === 0) {
    ElMessage.warning("无数据可导出");
    return;
  }

  exportToCSV(dataToExport, columns);
};

const fetchAllData = async (columns: string[]) => {
  const allRows: any[] = [];
  const batchSize = 1000;
  let searchAfter = null;

  // 构建基础查询
  const dsl = buildDSL();
  const query = dsl.query;

  // 循环拉取
  while (true) {
    const req: any = {
      datasourceId: props.packageData.datasource_id,
      index: selectedIndices.value,
      query: query,
      size: batchSize,
      // 仅获取需要的字段，减少传输量
      _source: columns,
    };

    // 使用 search_after 进行深度分页
    if (searchAfter) {
      req.search_after = searchAfter;
    } else {
      // 第一页
      req.from = 0;
    }

    // 强制使用 _shard_doc 排序以确保游标稳定
    // 如果原查询有排序，附加 _shard_doc；否则直接使用 _shard_doc
    if (dsl.sort) {
      req.sort = [...dsl.sort];
      // 检查是否已有 _shard_doc，没有则追加
      const hasShardDoc = req.sort.some((s: any) => s._shard_doc);
      if (!hasShardDoc) {
        req.sort.push({ _shard_doc: { order: "asc" } });
      }
    } else {
      req.sort = [{ _shard_doc: { order: "asc" } }];
    }

    const resp = await executeESQuery(req);
    const data = resp?.data || resp;
    const hits = data?.hits?.hits || [];

    if (hits.length === 0) break;

    allRows.push(...hits.map((h: any) => h._source));

    // 更新游标
    const lastHit = hits[hits.length - 1];
    if (lastHit && lastHit.sort) {
      searchAfter = lastHit.sort;
    } else {
      // 如果没有 sort 字段，无法继续
      break;
    }

    if (hits.length < batchSize) break;

    // 安全限制：防止浏览器崩溃，限制最大导出 10万条
    if (allRows.length >= 100000) {
      ElMessage.warning("导出数据量过大，已截断为前100,000条");
      break;
    }
  }

  return allRows;
};

const exportToCSV = (rows: any[], columns: string[]) => {
  // 构建CSV内容
  let csvContent = "";

  // 添加表头
  const headers = columns.map(
    (field) => `"${getFieldDisplayName(field).replace(/"/g, '""')}"`,
  );
  csvContent += headers.join(",") + "\n";

  // 添加数据行
  rows.forEach((row: Record<string, any>) => {
    const values: string[] = [];
    columns.forEach((field: string) => {
      const v = row?.[field];
      // 使用 formatCell 保持格式一致性，但要注意 formatCell 可能返回 HTML (如 snippet)，这里需要纯文本
      // 简单起见，直接转字符串，或者剥离 HTML
      let cellValue = v;
      if (cellValue === null || cellValue === undefined) {
        cellValue = "";
      } else if (typeof cellValue === "object") {
        cellValue = JSON.stringify(cellValue);
      } else {
        cellValue = String(cellValue);
      }

      // 处理CSV特殊字符
      cellValue = cellValue.replace(/"/g, '""');
      values.push(`"${cellValue}"`);
    });
    csvContent += values.join(",") + "\n";
  });

  // 创建并下载CSV文件
  const blob = new Blob(["\uFEFF" + csvContent], {
    type: "text/csv;charset=utf-8;",
  });
  const link = document.createElement("a");
  const fileName = `${props.packageData?.name || "资源包查询"}_${exportType.value === "all" ? "全部" : "当前页"}_${new Date()
    .toISOString()
    .slice(0, 10)}.csv`;
  link.href = URL.createObjectURL(blob);
  link.download = fileName;
  link.click();
  URL.revokeObjectURL(link.href);

  ElMessage.success("导出成功");
};

// 全选/取消全选逻辑与状态
const isAllSelected = computed(() => {
  if (viewMode.value === "list") {
    return (
      processedRecords.value.length > 0 &&
      selectedTableRows.value.length === processedRecords.value.length
    );
  }
  return (
    records.value.length > 0 &&
    selectedCardIndices.value.size === records.value.length
  );
});

const selectAllCurrentView = () => {
  if (viewMode.value === "list") {
    const rows = processedRecords.value || [];
    selectedTableRows.value = [...rows];
    nextTick(() => {
      try {
        tableRef.value?.clearSelection?.();
        rows.forEach((r: Record<string, any>) =>
          tableRef.value?.toggleRowSelection?.(r, true),
        );
      } catch {}
    });
  } else {
    const rows = records.value || [];
    selectedCardIndices.value = new Set(rows.map((_, i) => i));
  }
};

const clearAllSelection = () => {
  if (viewMode.value === "list") {
    selectedTableRows.value = [];
    try {
      tableRef.value?.clearSelection?.();
    } catch {}
  } else {
    selectedCardIndices.value = new Set();
  }
};

const toggleSelectAll = () => {
  if (isAllSelected.value) {
    clearAllSelection();
  } else {
    selectAllCurrentView();
  }
};

// 导出当前查询结果到 CSV
const exportResults = async () => {
  const exportRows =
    viewMode.value === "list"
      ? selectedTableRows.value
      : Array.from(selectedCardIndices.value)
          .map((i) => records.value?.[i])
          .filter(Boolean);

  if (!exportRows?.length) {
    ElMessage.warning("没有数据可导出（请勾选需要导出的记录）");
    return;
  }
  try {
    await ElMessageBox.confirm("确定要导出查询结果吗？", "确认导出", {
      confirmButtonText: "确定",
      cancelButtonText: "取消",
      type: "info",
    });

    // 构建CSV内容
    let csvContent = "";

    // 添加表头
    const headers = displayFields.value.map(
      (field) => `"${getFieldDisplayName(field).replace(/"/g, '""')}"`,
    );
    csvContent += headers.join(",") + "\n";

    // 添加数据行
    exportRows.forEach((row: Record<string, any>) => {
      const values: string[] = [];
      displayFields.value.forEach((field: string) => {
        const v = row?.[field];
        let cellValue = typeof v === "object" ? JSON.stringify(v) : (v ?? "");
        // 处理CSV特殊字符
        cellValue = String(cellValue).replace(/"/g, '""');
        values.push(`"${cellValue}"`);
      });
      csvContent += values.join(",") + "\n";
    });

    // 创建并下载CSV文件
    const blob = new Blob(["\uFEFF" + csvContent], {
      type: "text/csv;charset=utf-8;",
    });
    const link = document.createElement("a");
    const fileName = `${props.packageData?.name || "资源包查询"}_${new Date()
      .toISOString()
      .slice(0, 10)}.csv`;
    link.href = URL.createObjectURL(blob);
    link.download = fileName;
    link.click();
    URL.revokeObjectURL(link.href);

    ElMessage.success("导出成功");
  } catch (error: any) {
    if (error !== "cancel") {
      console.error("导出失败:", error);
      ElMessage.error("导出失败");
    }
  }
};
// 行详情
const detailVisible = ref(false);
const selectedRow = ref<Record<string, any> | null>(null);
const pdfDialogVisible = ref(false);
const pdfUrl = ref<string | null>(null);
const openRowDetail = (row: Record<string, any>) => {
  selectedRow.value = row;
  detailVisible.value = true;
};
const openPdf = () => {
  const url = selectedRow.value?.["pdf_url"];
  if (url && url !== "null") {
    pdfUrl.value = String(url);
    pdfDialogVisible.value = true;
  } else {
    ElMessage.warning("未找到有效的 pdf_url 字段");
  }
};

function buildPdfOpenUrl(url: string, page?: number | null, keyword?: string | null): string {
  const origin = window.location.origin;
  const viewer = `${origin}/api/v1/utils/pdf-viewer`;
  const proxied = `${origin}/api/v1/utils/pdf-proxy?url=${encodeURIComponent(String(url))}`;
  const file = encodeURIComponent(proxied);
  const params = new URLSearchParams();
  if (page && Number.isFinite(Number(page))) {
    params.set('page', String(page));
  }
  if (keyword && String(keyword).trim()) {
    params.set('search', String(keyword).trim());
  }
  const hash = params.toString();
  // 将 page/search 放到查询字符串，viewer 也支持从 query 读取
  return `${viewer}?file=${file}${hash ? '&' + hash : ''}`;
}

const openPdfAtHit = (row: Record<string, any>) => {
  try {
    const url = row?.['pdf_url'];
    const page = row?.['pageNumber'];
    let keyword: string | null = null;
    if (Array.isArray(executedSearchValue.value)) {
      keyword = executedSearchValue.value.find((k) => typeof k === 'string' && k.trim()) || null;
    } else {
      const k = executedSearchValue.value?.trim();
      keyword = k ? k : null;
    }
    if (!url || url === 'null') {
      ElMessage.warning('未找到有效的 PDF 链接');
      return;
    }
    const finalUrl = buildPdfOpenUrl(String(url), page ?? null, keyword);
    window.open(finalUrl, '_blank');
  } catch (e) {
    console.error(e);
    ElMessage.error('打开PDF失败');
  }
};
// 分页
const currentPage = ref(1);
const pageSize = ref(100);
// 滑动查询相关状态
const MAX_RESULT_WINDOW = 10000;
const pagingMode = ref<"offset" | "search_after">("offset");
const lastSearchAfter = ref<any[] | null>(null);
const lastPageLoaded = ref<number>(1);

function onPageChange(page: number) {
  const maxOffsetPages = Math.floor(MAX_RESULT_WINDOW / pageSize.value);
  // 1) 在 offset 窗口内允许任意跳页
  if (page <= maxOffsetPages) {
    pagingMode.value = "offset";
    currentPage.value = page;
    lastPageLoaded.value = page;
    lastSearchAfter.value = null;
    executeQuery();
    return;
  }

  // 2) 第一次跨窗口跳转：先收敛到上限页，并提示继续点击“下一页”进入滑动模式
  if (lastPageLoaded.value < maxOffsetPages) {
    pagingMode.value = "offset";
    currentPage.value = maxOffsetPages;
    lastPageLoaded.value = maxOffsetPages;
    lastSearchAfter.value = null;
    ElMessage.warning(
      `超过 10,000 结果窗口限制，已跳转至上限页（第 ${maxOffsetPages} 页），继续点击“下一页”将进入滑动查询模式`,
    );
    executeQuery();
    return;
  }

  // 3) 从上限页开始的连续下一页：切换为 search_after 模式并仅允许逐页前进
  if (pagingMode.value !== "search_after") {
    pagingMode.value = "search_after";
  }
  if (page === lastPageLoaded.value + 1) {
    currentPage.value = page;
    lastPageLoaded.value = page;
    executeQuery();
  } else {
    const target = lastPageLoaded.value + 1;
    ElMessage.warning(`滑动查询模式下仅支持逐页前进，已跳至第 ${target} 页`);
    currentPage.value = target;
    executeQuery();
    lastPageLoaded.value = currentPage.value;
  }
}
const totalHits = computed<number>(() => {
  const total = results.value?.hits?.total;
  if (typeof total === "number") return total;
  if (typeof total?.value === "number") return total.value;
  return records.value.length;
});

// 重复的深分页状态与方法已移除，统一使用上方 onPageChange 实现

// 按字段值长度构建一致的字段顺序
const fieldOrder = ref<string[]>([]);
const displayFields = computed<string[]>(() => {
  // 收集所有潜在字段（来源于映射或当前记录）
  const allFields = new Set<string>();
  if (sourceFields.value.length) {
    sourceFields.value.forEach((f) => allFields.add(f));
  } else {
    records.value.forEach((r) =>
      Object.keys(r || {}).forEach((k) => allFields.add(k)),
    );
  }

  // 如果有全局排序，先按排序排列，再补充未参与排序的剩余字段
  if (fieldOrder.value.length) {
    const ordered = [...fieldOrder.value];
    const leftover = Array.from(allFields).filter(
      (f) => !fieldOrder.value.includes(f),
    );
    return ordered.concat(leftover);
  }
  // 否则直接使用全部字段集合
  return Array.from(allFields);
});

// 详情面板的“基本信息”字段集合：避免首次默认搜索展示所有字段
// 优先使用模板提供的 _source 字段；若无则基于常用字段与已选行数据挑选有限字段
const basicDisplayFields = computed<string[]>(() => {
  const row = selectedRow.value || {};
  const hasField = (f: string) => row && f in row;

  // 模板提供了 _source 时，直接按该集展示，限制最多 20 个并仅显示当前行存在的字段
  if (sourceFields.value.length) {
    return sourceFields.value.filter(hasField).slice(0, 20);
  }

  // 常见基础字段优先级列表（标题 + 关键字段 + 常用元信息）
  const preferred = Array.from(
    new Set<string>([
      // 标题候选
      ...TITLE_FIELDS,
      // 关键字段候选
      ...KEY_FIELDS,
      // 常用基础字段
      "publication_category",
      "data_type",
      "type",
      "publish_time",
      "published_at",
      "create_time",
      "authors",
      "keywords",
      "language",
      "publisher",
      "data_source",
      "source",
      "pdf_url",
      "abstract",
    ]),
  );

  const preferredPresent = preferred.filter(hasField);
  if (preferredPresent.length) {
    return preferredPresent.slice(0, 20);
  }

  // 兜底：按全局字段顺序选择有限数量，避免一次性展示全部字段
  const ordered = displayFields.value.filter(hasField);
  return ordered.slice(0, 12);
});

// 规范化聚合结果，便于左侧展示
const normalizedAggs = computed<Record<string, any>>(() => {
  const aggs = results.value?.aggregations;
  if (!aggs) return {};
  const tplQuery =
    templateDetail.value?.query || templateDetail.value?.query_content;

  // 收集条目，包含识别字段，后续按优先级排序
  const entries: Array<{
    name: string;
    info: any;
    isPreferred: boolean;
    orderHint: number;
  }> = [];
  const preferredFields = new Set([
    "publication_category",
    "data_type",
    "type",
  ]);

  Object.entries(aggs).forEach(([name, cfg]: [string, any]) => {
    if (cfg?.buckets && Array.isArray(cfg.buckets)) {
      const field = tplQuery?.aggs?.[name]?.terms?.field;
      const info = { type: "terms", buckets: cfg.buckets, field, raw: cfg };
      const nameLower = String(name).toLowerCase();
      const isPreferred =
        (field && preferredFields.has(String(field))) ||
        nameLower.includes("data_type") ||
        nameLower.includes("publication") ||
        nameLower.includes("type");
      // 使用 orderHint 便于扩展更多优先策略
      const orderHint = isPreferred ? 0 : 1;
      entries.push({ name, info, isPreferred, orderHint });
    } else if (cfg?.value !== undefined) {
      // sum/avg/max/min/value_count
      const type = cfg.meta?.type || "metric";
      const info = { type, value: cfg.value, raw: cfg };
      entries.push({ name, info, isPreferred: false, orderHint: 2 });
    } else {
      const info = { type: "unknown", raw: cfg };
      entries.push({ name, info, isPreferred: false, orderHint: 3 });
    }
  });

  // 排序：优先显示“数据类型/出版物类型”等首选聚合，其余保持原相对顺序
  const sorted = entries.sort((a, b) => a.orderHint - b.orderHint);
  const out: Record<string, any> = {};
  sorted.forEach((e) => {
    out[e.name] = e.info;
  });
  return out;
});

onMounted(async () => {
  await initFromTemplate();
  // 初始化加载字段中文映射，确保下拉框显示中文
  if (
    Object.keys(fieldMappings.value).length === 0 &&
    props.packageData?.datasource_id &&
    selectedIndices.value.length > 0
  ) {
    await loadInitialFieldMappings();
  }
  if (!defaultSearchField.value && availableFieldNames.value.length > 0) {
    // 默认选择"全部字段"（空值），而不是第一个字段
    defaultSearchField.value = "";
  }
  const aggKeys = Object.keys(normalizedAggs.value || {});
  if (aggKeys.length) {
    // 默认展开全部聚合项
    activeAggs.value = aggKeys;
  }
});

// 聚合变化时默认全部展开
watch(normalizedAggs, (val) => {
  const keys = Object.keys(val || {});
  activeAggs.value = keys;
});

async function initFromTemplate() {
  try {
    if (!props.packageData?.template_id) return;
    const resp: any = await templateApi.getByType(
      props.packageData.template_id,
      "es",
    );
    const detail = resp?.data || resp;
    templateDetail.value = detail;

    // 解析 indices
    const indices = detail?.indices || detail?.config?.indices || [];
    if (Array.isArray(indices)) selectedIndices.value = indices;

    // 如果模板未提供索引，尝试从资源回退
    await ensureIndicesFromResource();

    // 解析 query/_source
    const q = detail?.query || detail?.query_content || null;
    if (q && Array.isArray(q._source)) {
      sourceFields.value = q._source;
    }

    // 解析模板条件（锁定为限定条件）
    const conditionsCfg = detail?.config?.conditions || [];
    fixedConditions.value = conditionsCfg.filter(
      (c: any) => c.locked || c.lockType === "locked",
    );

    // 如未提供_source，尝试加载字段映射
    if (
      availableFieldNames.value.length === 0 &&
      props.packageData?.datasource_id &&
      selectedIndices.value.length
    ) {
      const fieldsResp = await getESFieldMapping(
        props.packageData.datasource_id,
        selectedIndices.value,
      );
      const fields = (fieldsResp?.data || []) as Array<{
        name: string;
        type?: string;
      }>;
      availableFields.value = fields;
    }
  } catch (e) {
    console.error("加载ES模板详情失败:", e);
  }
}

// 初始化场景：单独调用接口获取字段映射（含中文显示名）
async function loadInitialFieldMappings() {
  try {
    const req: any = {
      datasourceId: props.packageData!.datasource_id,
      index: selectedIndices.value,
      query: { match_all: {} },
      size: 0,
      from: 0,
      _source: [],
    };
    const resp = await executeESQuery(req);
    // 兼容不同返回结构：优先从 resp.data 读取
    const data: any = resp?.data || resp;
    const mappings = data?.fieldMappings || resp?.fieldMappings;
    if (mappings && typeof mappings === "object") {
      fieldMappings.value = mappings;
    }
  } catch (e) {
    console.warn("初始化加载字段映射失败:", e);
  }
}

/**
 * 从关联数据资源回退解析ES索引
 * 优先使用 packageData.resource_id，其次尝试 data_resource_id
 */
async function ensureIndicesFromResource() {
  try {
    if (selectedIndices.value.length) return;
    const resId =
      props.packageData?.resource_id || props.packageData?.data_resource_id;
    if (!resId) return;
    const resp = await dataResourceApi.getResourceDetail(Number(resId));
    const resource: any = resp?.data || resp;
    const idx = resource?.index_name || resource?.table_name;
    if (idx) {
      selectedIndices.value = [idx];
    }
  } catch (e) {
    console.warn("从数据资源解析索引失败:", e);
  }
}

// 索引就绪状态：有数据源ID且已解析到索引
const isIndicesReady = computed(() => {
  return (
    Boolean(props.packageData?.datasource_id) &&
    selectedIndices.value.length > 0
  );
});

function addCondition() {
  const field = availableFieldNames.value[0];
  if (!field) {
    ElMessage.warning("暂无可用字段");
    return;
  }
  conditions.push({ field, type: "match", value: "", logic: "must" });
}

function removeCondition(i: number) {
  conditions.splice(i, 1);
}

/**
 * 重置查询条件
 * 行为：清空查询与分页状态，同时隐藏导出进度与下载入口
 */
function resetConditions() {
  conditions.splice(0, conditions.length);
  defaultSearchField.value = "";
  defaultSearchValue.value = "";
  results.value = null;
  fieldOrder.value = [];
  // 重置分页与滑动游标
  currentPage.value = 1;
  lastPageLoaded.value = 1;
  lastSearchAfter.value = null;
  pagingMode.value = "offset";

  // 清空导出状态，确保重置后不显示进度或下载
  exportStatus.value = null;
  exportProgress.value = null;
  exportFileUrl.value = null;
  latestFileAvailable.value = false;
  latestDownloadUrl.value = null;
  if (exportPollingTimer.value) {
    clearInterval(exportPollingTimer.value);
    exportPollingTimer.value = null;
  }
}

function formatFixedCondition(cond: any): string {
  const name = cond?.name || cond?.field || "";
  const op = cond?.operator || cond?.type || "match";
  if (op === "range") {
    const gte = cond?.default_value?.min ?? cond?.min ?? cond?.gte;
    const lte = cond?.default_value?.max ?? cond?.max ?? cond?.lte;
    return `${name} ∈ [${gte ?? ""} - ${lte ?? ""}]`;
  }
  const val = cond?.default_value ?? cond?.value ?? "";
  return `${name} ${op} ${val}`;
}

function buildDSL(): any {
  const bool = {
    must: [] as any[],
    should: [] as any[],
    must_not: [] as any[],
  };

  // 固定条件
  fixedConditions.value.forEach((cond: any) => {
    const field = cond?.name || cond?.field;
    const op = cond?.operator || cond?.type || "match";
    const val = cond?.default_value ?? cond?.value;
    if (!field) return;
    switch (op) {
      case "term":
        bool.must.push({ term: { [field]: val } });
        break;
      case "match":
        bool.must.push({ match: { [field]: val } });
        break;
      case "prefix":
        bool.must.push({ prefix: { [field]: val } });
        break;
      case "wildcard":
        bool.must.push({ wildcard: { [field]: val } });
        break;
      case "exists":
        bool.must.push({ exists: { field } });
        break;
      case "range":
        const gte = cond?.default_value?.min ?? cond?.min ?? cond?.gte;
        const lte = cond?.default_value?.max ?? cond?.max ?? cond?.lte;
        const range: any = {};
        if (gte !== undefined) range.gte = gte;
        if (lte !== undefined) range.lte = lte;
        bool.must.push({ range: { [field]: range } });
        break;
      default:
        bool.must.push({ match: { [field]: val } });
        break;
    }
  });

  // 默认搜索条件（如果有输入值）
  if (defaultSearchValue.value && defaultSearchValue.value.trim()) {
    if (defaultSearchField.value) {
      const keyword = defaultSearchValue.value.trim();
      const fld = defaultSearchField.value;
      // 指定字段为 pages（嵌套）时，构造 nested + inner_hits 高亮
      if (fld === "pages" || fld.startsWith("pages")) {
        bool.must.push({
          nested: {
            path: "pages",
            query: {
              match: { "pages.content": keyword },
            },
            inner_hits: {
              name: "pages",
              highlight: {
                fields: {
                  "pages.content": {
                    fragment_size: 200,
                    number_of_fragments: 5,
                    pre_tags: ["<em>"],
                    post_tags: ["</em>"],
                  },
                },
              },
              size: 20,
            },
          },
        });
      } else {
        // 非嵌套字段，使用 match 查询
        bool.must.push({
          match: { [fld]: keyword },
        });
      }
    } else {
      // 未指定字段时，对所有可用字段进行multi_match查询
      if (availableFieldNames.value.length > 0) {
        const nonDateFields = availableFieldNames.value.filter((f) => {
          const t =
            fieldMappings.value[f]?.type ||
            availableFields.value.find((af) => af.name === f)?.type;
          return t !== "date" && t !== "date_nanos";
        });
        if (nonDateFields.length > 0) {
          bool.must.push({
            multi_match: {
              query: defaultSearchValue.value.trim(),
              fields: nonDateFields,
              type: "best_fields",
            },
          });
        }
      }
    }
  }

  // 动态条件
  conditions.forEach((c) => {
    if (!c.field) return;
    let clause: any = {};

    if (c.field === "_all_fields") {
      const nonDateFields = availableFieldNames.value.filter((f) => {
        const t =
          fieldMappings.value[f]?.type ||
          availableFields.value.find((af) => af.name === f)?.type;
        return t !== "date" && t !== "date_nanos" && t !== "nested";
      });

      if (nonDateFields.length > 0) {
        if (c.type === "match" || c.type === "term") {
          clause = {
            multi_match: {
              query: c.value,
              fields: nonDateFields,
              type: "best_fields",
              operator: "and",
            },
          };
        } else if (c.type === "wildcard" || c.type === "prefix") {
          const shouldClauses = nonDateFields.map((f) => {
            let fieldName = f;
            const t =
              fieldMappings.value[f]?.type ||
              availableFields.value.find((af) => af.name === f)?.type;

            // 如果是 text 类型，且未指定 .keyword 后缀，则自动追加 .keyword
            if (t === "text" && !fieldName.endsWith(".keyword")) {
              fieldName = `${fieldName}.keyword`;
            }

            if (c.type === "wildcard") {
              return {
                wildcard: {
                  [fieldName]: {
                    value: `*${c.value}*`,
                    case_insensitive: true,
                  },
                },
              };
            } else {
              // prefix
              return {
                prefix: {
                  [fieldName]: {
                    value: c.value,
                    case_insensitive: true,
                  },
                },
              };
            }
          });

          clause = {
            bool: {
              should: shouldClauses,
              minimum_should_match: 1,
            },
          };
        }
      }
    } else {
      // pages 字段为嵌套类型，改造为 nested 查询，并附带 inner_hits 高亮
      const isPagesField = c.field === "pages" || c.field.startsWith("pages");
      if (isPagesField) {
        const f = "pages.content";
        switch (c.type) {
          case "term":
            clause = {
              nested: {
                path: "pages",
                query: { term: { [f]: c.value } },
                inner_hits: {
                  name: "pages",
                  highlight: {
                    fields: {
                      "pages.content": {
                        fragment_size: 200,
                        number_of_fragments: 5,
                        pre_tags: ["<em>"],
                        post_tags: ["</em>"],
                      },
                    },
                  },
                  size: 20,
                },
              },
            };
            break;
          case "match":
            clause = {
              nested: {
                path: "pages",
                query: { match: { [f]: c.value } },
                inner_hits: {
                  name: "pages",
                  highlight: {
                    fields: {
                      "pages.content": {
                        fragment_size: 200,
                        number_of_fragments: 5,
                        pre_tags: ["<em>"],
                        post_tags: ["</em>"],
                      },
                    },
                  },
                  size: 20,
                },
              },
            };
            break;
          case "prefix":
            clause = {
              nested: {
                path: "pages",
                query: {
                  prefix: { [f]: { value: c.value, case_insensitive: true } },
                },
                inner_hits: { name: "pages" },
              },
            };
            break;
          case "wildcard":
            clause = {
              nested: {
                path: "pages",
                query: {
                  wildcard: {
                    [f]: { value: `*${c.value}*`, case_insensitive: true },
                  },
                },
                inner_hits: { name: "pages" },
              },
            };
            break;
          case "exists":
            clause = {
              nested: {
                path: "pages",
                query: { exists: { field: f } },
                inner_hits: { name: "pages" },
              },
            };
            break;
          case "range":
            const range: any = {};
            if (c.value?.gte !== undefined) range.gte = c.value.gte;
            if (c.value?.lte !== undefined) range.lte = c.value.lte;
            clause = {
              nested: {
                path: "pages",
                query: { range: { [f]: range } },
                inner_hits: { name: "pages" },
              },
            };
            break;
        }
      } else {
        switch (c.type) {
          case "term":
            {
              let termField = c.field;
              // 尝试获取字段类型
              const fType =
                fieldMappings.value[c.field]?.type ||
                availableFields.value.find((af) => af.name === c.field)?.type;

              // 如果是 text 类型，且未指定 .keyword 后缀，则自动追加 .keyword 以支持精确匹配
              if (fType === "text" && !termField.endsWith(".keyword")) {
                termField = `${termField}.keyword`;
              }
              clause = { term: { [termField]: c.value } };
            }
            break;
          case "match":
            clause = {
              match: { [c.field]: { query: c.value, operator: "and" } },
            };
            break;
          case "prefix":
            {
              let prefixField = c.field;
              const fType =
                fieldMappings.value[c.field]?.type ||
                availableFields.value.find((af) => af.name === c.field)?.type;

              if (fType === "text" && !prefixField.endsWith(".keyword")) {
                prefixField = `${prefixField}.keyword`;
              }
              clause = {
                prefix: {
                  [prefixField]: { value: c.value, case_insensitive: true },
                },
              };
            }
            break;
          case "wildcard":
            {
              let wcField = c.field;
              const fType =
                fieldMappings.value[c.field]?.type ||
                availableFields.value.find((af) => af.name === c.field)?.type;

              if (fType === "text" && !wcField.endsWith(".keyword")) {
                wcField = `${wcField}.keyword`;
              }
              clause = {
                wildcard: {
                  [wcField]: { value: `*${c.value}*`, case_insensitive: true },
                },
              };
            }
            break;
          case "exists":
            clause = { exists: { field: c.field } };
            break;
          case "range":
            const range: any = {};
            if (c.value?.gte !== undefined) range.gte = c.value.gte;
            if (c.value?.lte !== undefined) range.lte = c.value.lte;
            clause = { range: { [c.field]: range } };
            break;
        }
      }
    }
    if (Object.keys(clause).length) {
      bool[c.logic].push(clause);
    }
  });

  const query: any = { query: {} };
  if (bool.must.length || bool.should.length || bool.must_not.length) {
    query.query = { bool };
  } else {
    query.query = { match_all: {} };
  }
  if (availableFieldNames.value.length) {
    query._source = availableFieldNames.value;
  }
  // 分页基础：滑动查询不设置 from，仅设置 size
  query.size = pageSize.value;
  if (pagingMode.value === "offset") {
    query.from = (currentPage.value - 1) * pageSize.value;
  }
  // 排序：
  // - offset 模式：优先使用 update_time desc；无则不设置排序（使用默认）
  // - search_after 模式：使用 update_time desc 并追加 _shard_doc 作为稳定tie-breaker；无 update_time 时仅 _shard_doc
  if (pagingMode.value === "search_after") {
    if (availableFieldNames.value.includes("update_time")) {
      query.sort = [
        { update_time: { order: "desc" } },
        { _shard_doc: { order: "asc" } },
      ];
    } else {
      query.sort = [{ _shard_doc: { order: "asc" } }];
    }
  } else {
    if (availableFieldNames.value.includes("update_time")) {
      query.sort = [{ update_time: { order: "desc" } }];
    }
  }

  // 如果模板定义了聚合，沿用之（便于左侧展示）
  const tplQuery =
    templateDetail.value?.query || templateDetail.value?.query_content;
  if (tplQuery?.aggs) {
    query.aggs = tplQuery.aggs;
  }
  return query;
}

/**
 * 执行查询
 * 行为：在发起新的查询前清空导出相关状态并隐藏进度区
 */
async function executeQuery() {
  try {
    if (!props.packageData?.datasource_id) {
      ElMessage.error("缺少数据源ID");
      return;
    }
    if (!selectedIndices.value.length) {
      ElMessage.error("缺少索引信息，无法进行查询");
      return;
    }

    // 清空导出状态，避免在重新/重置查询后仍显示进度或下载
    exportStatus.value = null;
    exportProgress.value = null;
    exportFileUrl.value = null;
    latestFileAvailable.value = false;
    latestDownloadUrl.value = null;
    if (exportPollingTimer.value) {
      clearInterval(exportPollingTimer.value);
      exportPollingTimer.value = null;
    }

    loading.value = true;
    // 更新已执行查询的搜索词，用于高亮显示
    // 优先使用顶部搜索框
    if (defaultSearchValue.value && defaultSearchValue.value.trim()) {
      executedSearchValue.value = defaultSearchValue.value.trim();
    } else {
      // 否则从高级条件中提取
      const keywords: string[] = [];
      conditions.forEach((c) => {
        if (
          ["match", "term", "prefix", "wildcard"].includes(c.type) &&
          c.value
        ) {
          if (typeof c.value === "string") {
            keywords.push(c.value);
          }
        }
        // Multi-match or _all_fields
        if (c.field === "_all_fields" && typeof c.value === "string") {
          keywords.push(c.value);
        }
      });
      executedSearchValue.value = keywords;
    }
    const dsl = buildDSL();
    const req: any = {
      datasourceId: props.packageData.datasource_id,
      index: selectedIndices.value,
      query: dsl.query,
      size: dsl.size,
      from: dsl.from,
    };
    if (dsl.sort) req.sort = dsl.sort;
    if (dsl._source) req._source = dsl._source;
    if (dsl.aggs) req.aggs = dsl.aggs;

    // 添加模板中预设的查询条件（如果存在）
    const tplQuery =
      templateDetail.value?.query || templateDetail.value?.query_content;
    if (tplQuery && tplQuery.query) {
      // 修复查询结构，确保不会出现 {match_all: {}, bool: {...}} 这种非法结构
      if (tplQuery.query.bool) {
        // 如果模板中有bool查询条件，则与动态构建的查询合并
        if (req.query.bool) {
          // 合并must条件
          if (
            tplQuery.query.bool.must &&
            Array.isArray(tplQuery.query.bool.must)
          ) {
            req.query.bool.must = [
              ...req.query.bool.must,
              ...tplQuery.query.bool.must,
            ];
          }
          // 合并should条件
          if (
            tplQuery.query.bool.should &&
            Array.isArray(tplQuery.query.bool.should)
          ) {
            req.query.bool.should = [
              ...req.query.bool.should,
              ...tplQuery.query.bool.should,
            ];
          }
          // 合并must_not条件
          if (
            tplQuery.query.bool.must_not &&
            Array.isArray(tplQuery.query.bool.must_not)
          ) {
            req.query.bool.must_not = [
              ...req.query.bool.must_not,
              ...tplQuery.query.bool.must_not,
            ];
          }
        } else {
          // 如果动态查询没有bool条件，则直接使用模板的bool条件
          req.query.bool = tplQuery.query.bool;
        }
      } else if (tplQuery.query.match_all) {
        // 如果模板查询是match_all，则将其添加到bool查询的must条件中
        if (req.query.bool) {
          req.query.bool.must = req.query.bool.must || [];
          req.query.bool.must.push({ match_all: {} });
        } else {
          // 如果既没有动态bool查询也没有模板bool查询，则直接使用模板查询
          req.query = tplQuery.query;
        }
      } else if (Object.keys(tplQuery.query).length > 0) {
        // 如果模板查询有其他类型的查询条件，则将其添加到bool查询的must条件中
        if (req.query.bool) {
          req.query.bool.must = req.query.bool.must || [];
          req.query.bool.must.push(tplQuery.query);
        } else {
          // 创建新的bool查询并添加模板查询条件
          req.query = {
            bool: {
              must: [tplQuery.query],
              should: [],
              must_not: [],
            },
          };
        }
      }
    }

    // 确保查询结构正确，修复可能的非法结构
    if (req.query && req.query.match_all !== undefined && req.query.bool) {
      // 将match_all和bool合并为合法的bool查询
      const matchAllClause = { match_all: req.query.match_all || {} };
      req.query = {
        bool: {
          must: [matchAllClause, ...(req.query.bool.must || [])],
          should: req.query.bool.should || [],
          must_not: req.query.bool.must_not || [],
        },
      };
    }

    // 滑动查询：不传 from，传递 search_after
    if (pagingMode.value === "search_after") {
      delete req.from;
      if (lastSearchAfter.value && Array.isArray(lastSearchAfter.value)) {
        req.search_after = lastSearchAfter.value;
      }
    }
    const resp = await executeESQuery(req);

    // 处理响应数据
    if (resp?.data) {
      // 从 resp.data 中提取 fieldMappings 和 stats
      const {
        fieldMappings: respFieldMappings,
        stats,
        ...esData
      } = resp.data as any;

      // 更新 fieldMappings
      if (respFieldMappings) {
        fieldMappings.value = respFieldMappings;
        console.log("fieldMappings 已更新:", fieldMappings.value);
      } else {
        console.log("响应中未收到 fieldMappings");
      }

      // 设置 ES 查询结果
      results.value = esData;
      // 重置卡片增量渲染数量
      visibleCount.value = Math.min(CARD_INITIAL_BATCH, records.value.length);
      // 更新下一页的游标（search_after）
      try {
        const cursor = (esData as any)?.cursor || (resp as any)?.cursor;
        const nextSearchAfter = cursor?.nextSearchAfter;
        if (pagingMode.value === "search_after") {
          if (nextSearchAfter) {
            lastSearchAfter.value = nextSearchAfter;
          } else {
            const hits = esData?.hits?.hits || [];
            if (
              hits.length > 0 &&
              Array.isArray((hits[hits.length - 1] as any)?.sort)
            ) {
              lastSearchAfter.value = (hits[hits.length - 1] as any).sort;
            }
          }
        } else {
          const hits = esData?.hits?.hits || [];
          if (hits.length > 0 && Array.isArray(hits[hits.length - 1]?.sort)) {
            lastSearchAfter.value = hits[hits.length - 1].sort;
          } else {
            lastSearchAfter.value = null;
          }
        }
      } catch (e) {
        // 游标更新失败不影响显示
      }
    } else {
      results.value = resp;
    }

    // 计算全局字段顺序（基于值长度的升序）
    computeFieldOrder();
  } catch (e) {
    console.error("执行ES查询失败:", e);
    ElMessage.error("执行ES查询失败");
  } finally {
    loading.value = false;
  }
}

function computeFieldOrder() {
  // 仅基于当前页前10行，空值不参与平均值统计，但需要识别“全为空”的字段以置前
  const topN = records.value.slice(0, Math.min(10, records.value.length));
  const lenStats: Record<string, { total: number; count: number }> = {};
  const allFieldsSet = new Set<string>();

  // 收集所有出现过的字段（或映射提供的字段）
  if (sourceFields.value.length) {
    sourceFields.value.forEach((f) => allFieldsSet.add(f));
  }
  topN.forEach((row) => {
    Object.keys(row || {}).forEach((k) => allFieldsSet.add(k));
    Object.entries(row || {}).forEach(([k, v]) => {
      if (isEmptyValue(v)) return;
      const l = getValueLength(v);
      if (!lenStats[k]) lenStats[k] = { total: 0, count: 0 };
      lenStats[k].total += l;
      lenStats[k].count += 1;
    });
  });

  const allFields = Array.from(allFieldsSet);
  const nonEmptyFields = Object.keys(lenStats);
  const emptyFields = allFields.filter((f) => !nonEmptyFields.includes(f));

  const entries = Object.entries(lenStats).map(([k, s]) => ({
    field: k,
    avg: s.total / (s.count || 1),
  }));
  // 按平均长度升序：短字段优先（在“空字段”之后）
  entries.sort((a, b) => a.avg - b.avg);

  fieldOrder.value = emptyFields.concat(entries.map((e) => e.field));
}

function isEmptyValue(v: any): boolean {
  if (v === null || v === undefined) return true;
  if (typeof v === "string") return v.trim().length === 0;
  if (Array.isArray(v)) return v.length === 0;
  if (typeof v === "object") return Object.keys(v).length === 0;
  return false;
}

function getValueLength(v: any): number {
  if (v === null || v === undefined) return 0;
  if (typeof v === "string") return v.length;
  if (typeof v === "number") return String(v).length;
  if (Array.isArray(v)) return JSON.stringify(v).length;
  if (typeof v === "object") return JSON.stringify(v).length;
  return String(v).length;
}

function formatCell(v: any): string {
  if (v === null || v === undefined) return "-";
  if (typeof v === "string") return mapTypeLabel(v);
  try {
    return JSON.stringify(v);
  } catch {
    return String(v);
  }
}

function formatTime(t?: string): string {
  if (!t) return "";
  try {
    const d = new Date(t);
    if (isNaN(d.getTime())) return String(t);
    return d.toLocaleString();
  } catch {
    return String(t || "");
  }
}

// 英文数据类型到中文的映射
const typeLabelMap: Record<string, string> = {
  BOOK: "图书",
  JOURNAL_ARTICLE: "期刊文章",
  CONFERENCE_PAPER: "会议论文",
  REPORT: "报告",
  THESIS: "学位论文",
  STANDARD: "标准",
  PATENT: "专利",
  OTHER: "其他",
};

function mapTypeLabel(val: any): string {
  const key = String(val ?? "").toUpperCase();
  return typeLabelMap[key] || String(val ?? "");
}

function formatAggKey(val: any): string {
  const label = mapTypeLabel(val);
  return getValueLength(label) > 40
    ? formatText(String(label), 40)
    : String(label);
}

function formatText(text: string, max: number): string {
  if (!text) return "";
  return text.length > max ? text.slice(0, max - 1) + "…" : text;
}

// 是否需要 tooltip（依据内容长度与阈值）
function shouldTooltip(value: any, limit: number): boolean {
  return getValueLength(value) > limit;
}

// 高亮搜索关键词的函数
function highlightText(text: string, keyword: string | string[]): string {
  if (!text || !keyword) return text;
  if (Array.isArray(keyword) && keyword.length === 0) return text;

  let pattern = "";
  if (Array.isArray(keyword)) {
    // 过滤空字符串并转义
    const escaped = keyword
      .filter((k) => k && typeof k === "string" && k.trim())
      .map((k) => k.replace(/[.*+?^${}()|[\]\\]/g, "\\$&"));
    if (escaped.length === 0) return text;
    // 按长度降序排序，优先匹配长词
    escaped.sort((a, b) => b.length - a.length);
    pattern = `(${escaped.join("|")})`;
  } else {
    pattern = `(${keyword.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")})`;
  }

  const regex = new RegExp(pattern, "gi");
  return text.replace(regex, '<span class="highlight">$1</span>');
}

// 带高亮的格式化文本函数
function formatTextWithHighlight(
  text: string,
  max: number | null,
  keyword?: string | string[],
): string {
  if (!text) return "";

  // 先截断文本
  const truncatedText =
    max && text.length > max ? text.slice(0, max - 1) + "…" : text;

  // 如果有搜索关键词，则高亮显示
  if (keyword) {
    if (typeof keyword === "string" && !keyword.trim()) return truncatedText;
    if (Array.isArray(keyword) && keyword.length === 0) return truncatedText;

    return highlightText(truncatedText, keyword);
  }

  return truncatedText;
}

// 卡片视图：标题字段与关键字段选择
const TITLE_FIELDS = [
  "title",
  "name",
  "doc_title",
  "headline",
  "subject",
  "paper_title",
];
function getTitleField(row: Record<string, any>): string {
  const r = row || {};
  for (const f of TITLE_FIELDS) {
    if (f in r) return f;
  }
  const keys = Object.keys(r);
  return keys.length ? keys[0] : "";
}
const KEY_FIELDS = [
  "language",
  "publication_category",
  "data_source",
  "publisher",
  "pageNumber",
  "snippet",
  "abstract",
];
function getKeyFields(row: Record<string, any>): string[] {
  const r = row || {};
  const picked = KEY_FIELDS.filter((f) => f in r);
  if (picked.length) return picked.slice(0, 6);
  return displayFields.value.slice(0, 6).filter((f) => f in r);
}

function copyRow(row: Record<string, any>) {
  try {
    navigator.clipboard.writeText(JSON.stringify(row, null, 2));
    ElMessage.success("复制成功");
  } catch (e) {
    ElMessage.error("复制失败");
  }
}

// 获取字段显示名称（优先显示 display_name，其次注释comment，最后字段名）
function getFieldDisplayName(fieldName: string): string {
  // 特殊映射：pages 字段在下拉与展示层统一显示为“全文”
  if (fieldName === "pages" || fieldName === "pages.content") {
    return "全文";
  }
  // 特殊映射：命中文本信息
  if (fieldName === "pageNumber") {
    return "命中全文页码";
  }
  if (fieldName === "snippet") {
    return "节选";
  }
  const fieldMapping = fieldMappings.value[fieldName];
  if (fieldMapping?.display_name) {
    return fieldMapping.display_name;
  }
  if (fieldMapping?.comment) {
    return fieldMapping.comment;
  }
  return fieldName;
}

// 全屏切换函数
function toggleFullscreen() {
  isFullscreen.value = !isFullscreen.value;

  if (isFullscreen.value) {
    // 进入全屏模式
    document.body.style.overflow = "hidden";
  } else {
    // 退出全屏模式
    document.body.style.overflow = "";
  }
}

function onAggBucketClick(aggName: string, bucket: any) {
  const agg = normalizedAggs.value[aggName];
  const field = agg?.field;
  if (!field) {
    ElMessage.warning("无法添加筛选：未找到聚合字段");
    return;
  }
  conditions.push({ field, type: "term", value: bucket.key, logic: "must" });
  executeQuery();
}

// 长内容阈值（达到或超过则整行展示）
const LONG_THRESHOLD = 100;
// 文本截断阈值：普通行与宽行分别使用不同上限
const DEFAULT_MAX_CHARS = 300;
const WIDE_MAX_CHARS = 500;

// 构建卡片行分块：遵循全局顺序，长内容占满一行，其余三等分
function buildCardChunks(
  row: Record<string, any>,
): Array<{ fields: string[]; wide?: boolean }> {
  const orderedFields = displayFields.value.filter((f) => row && f in row);
  const chunks: Array<{ fields: string[]; wide?: boolean }> = [];
  let currentRow: string[] = [];

  orderedFields.forEach((f) => {
    const len = getValueLength(row[f]);
    const isLong = len >= LONG_THRESHOLD;

    if (isLong) {
      // 先推送当前累积行
      if (currentRow.length) {
        chunks.push({ fields: currentRow });
        currentRow = [];
      }
      // 长内容独占一行
      chunks.push({ fields: [f], wide: true });
    } else {
      currentRow.push(f);
      if (currentRow.length >= 3) {
        chunks.push({ fields: currentRow });
        currentRow = [];
      }
    }
  });

  if (currentRow.length) {
    chunks.push({ fields: currentRow });
  }
  return chunks;
}

function onPageSizeChange(size: number) {
  pageSize.value = size;
  currentPage.value = 1;
  // 重置滑动游标状态
  pagingMode.value = "offset";
  lastPageLoaded.value = 1;
  lastSearchAfter.value = null;
  executeQuery();
}

async function downloadResourcePackage() {
  try {
    if (!props.packageData?.id) {
      ElMessage.error("缺少资源包ID");
      return;
    }
    if (!selectedIndices.value.length) {
      ElMessage.error("缺少索引信息，无法下载");
      return;
    }

    downloadLoading.value = true;

    // 构建查询数据
    const dsl = buildDSL();
    const queryData = {
      index: selectedIndices.value,
      query: dsl.query,
      _source: dsl._source,
    };

    // 调用下载API
    const response = await fetch(
      `/api/v1/resource-packages/${props.packageData.id}/download`,
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${localStorage.getItem("token")}`,
        },
        body: JSON.stringify(queryData),
      },
    );

    const result = await response.json();

    if (!response.ok) {
      throw new Error(result.message || "下载失败");
    }

    if (result.success) {
      const hasNew = !!(result.data && result.data.has_new_data);
      if (hasNew) {
        // 有新数据，自动下载文件
        const downloadUrl = result.data.download_url;
        const filename = result.data.filename;

        if (downloadUrl) {
          // 优先使用 window.open 触发浏览器下载，避免跨域导致的 download 属性失效
          const newWin = window.open(downloadUrl, "_blank");
          // 若被拦截或失败则回退到创建链接点击
          if (!newWin) {
            try {
              const link = document.createElement("a");
              link.href = downloadUrl;
              link.download = filename || "";
              document.body.appendChild(link);
              link.click();
              document.body.removeChild(link);
            } catch (e) {
              console.warn("下载链接触发失败，已尝试回退方案:", e);
            }
          }

          ElMessage.success("Excel文件生成成功，正在下载...");
        } else {
          ElMessage.error("未返回下载链接");
        }
      } else {
        // 无新数据
        ElMessage.warning(result.message || "无最新数据，无需下载资源包");
      }
    } else {
      throw new Error(result.message || "下载失败");
    }
  } catch (error) {
    console.error("下载资源包失败:", error);
    ElMessage.error(error.message || "下载失败，请稍后重试");
  } finally {
    downloadLoading.value = false;
  }
}

// 打开下载弹窗
function openDownloadDialog() {
  dialogData.excel_time = props.packageData?.excel_time;
  dialogData.download_time = props.packageData?.download_time;
  dialogData.download_url = props.packageData?.download_url;
  downloadDialogVisible.value = true;
  fetchHistoryFiles();
}

async function fetchHistoryFiles() {
  try {
    if (!props.packageData?.id) return;
    historyLoading.value = true;
    const resp = await resourcePackageApi.listFiles(
      props.packageData.id,
      1,
      50,
    );
    if (resp.success) {
      historyFiles.value = resp.data?.items || [];
    } else {
      historyFiles.value = [];
    }
  } catch (e) {
    console.warn("加载历史文件失败:", e);
    historyFiles.value = [];
  } finally {
    historyLoading.value = false;
  }
}

function formatHistoryLabel(f: ResourcePackageFile): string {
  const t = f.generated_at ? new Date(f.generated_at).toLocaleString() : "";
  return `${f.filename} (${t})`;
}

async function handleDownloadHistory() {
  try {
    if (!props.packageData?.id || !selectedFileId.value) {
      ElMessage.error("请选择需要下载的历史文件");
      return;
    }
    historyDownloadLoading.value = true;
    const resp = await resourcePackageApi.downloadFile(
      props.packageData.id,
      selectedFileId.value,
    );
    if (!resp.success) {
      throw new Error(resp.message || "下载失败");
    }
    const url = resp.data?.download_url;
    const filename = resp.data?.filename || "";
    if (url) {
      const newWin = window.open(url, "_blank");
      if (!newWin) {
        try {
          const link = document.createElement("a");
          link.href = url;
          link.download = filename;
          document.body.appendChild(link);
          link.click();
          document.body.removeChild(link);
        } catch (e) {
          console.warn("下载链接触发失败，已尝试回退方案:", e);
        }
      }
      ElMessage.success("正在下载历史文件...");
    } else {
      ElMessage.error("未返回下载链接");
    }
  } catch (e: any) {
    console.error("下载历史文件失败:", e);
    ElMessage.error(e.message || "下载失败，请稍后重试");
  } finally {
    historyDownloadLoading.value = false;
  }
}

async function handleGenerateExcel() {
  try {
    if (!props.packageData?.id) {
      ElMessage.error("缺少资源包ID");
      return;
    }
    if (!selectedIndices.value) {
      ElMessage.error("缺少索引信息，无法生成Excel");
      return;
    }
    generateLoading.value = true;
    const dsl = buildDSL();
    const payload: any = {
      index: selectedIndices.value,
      query: dsl.query,
    };
    if (dsl._source) payload._source = dsl._source;

    const resp = await resourcePackageApi.generateExcel(
      props.packageData.id,
      payload,
    );
    if (resp?.success) {
      const hasNew = resp?.data?.has_new_data;
      if (hasNew === false) {
        ElMessage.warning(resp?.message || "无最新数据，无需生成");
        // 不更新 excel_time，保持原值
      } else {
        // 更新弹窗中的下载链接
        const data = resp.data || {};
        if (data.download_url) dialogData.download_url = data.download_url;
        // 仅在有新数据时刷新弹窗时间为本地当前时间
        dialogData.excel_time = new Date().toISOString();
        ElMessage.success("Excel文件生成成功");
      }
    } else {
      ElMessage.error(resp?.message || "生成Excel失败，请稍后重试");
    }
  } catch (e: any) {
    console.error("生成Excel失败:", e);
    ElMessage.error(e?.message || "生成Excel失败，请稍后重试");
  } finally {
    generateLoading.value = false;
  }
}

async function handleDownloadLatest() {
  try {
    if (!props.packageData?.id) {
      ElMessage.error("缺少资源包ID");
      return;
    }
    if (!dialogData.download_url) {
      ElMessage.error("暂无可下载的最新资源包，请先生成Excel");
      return;
    }
    latestDownloadLoading.value = true;
    const resp = await resourcePackageApi.downloadLatest(props.packageData.id);
    if (!resp.success) {
      throw new Error(resp.message || "下载失败");
    }
    const url = resp.data?.download_url || dialogData.download_url;
    const filename = resp.data?.filename || "";
    if (url) {
      const newWin = window.open(url, "_blank");
      if (!newWin) {
        try {
          const link = document.createElement("a");
          link.href = url;
          link.download = filename;
          document.body.appendChild(link);
          link.click();
          document.body.removeChild(link);
        } catch (e) {
          console.warn("下载链接触发失败，已尝试回退方案:", e);
        }
      }
      // 更新最新下载时间（若后端返回）
      if (resp.data?.download_time)
        dialogData.download_time = resp.data.download_time;
      // 使用本地当前时间作为显示值
      dialogData.download_time = new Date().toISOString();
      ElMessage.success("正在下载最新资源包...");
    } else {
      ElMessage.error("未返回下载链接");
    }
  } catch (e: any) {
    console.error("下载最新资源包失败:", e);
    ElMessage.error(e.message || "下载失败，请稍后重试");
  } finally {
    latestDownloadLoading.value = false;
  }
}

const exportAllLoading = ref(false);
const exportTaskId = ref(null);
const exportPollingTimer = ref(null);
const exportStatus = ref<
  "started" | "processing" | "completed" | "failed" | null
>(null);
const exportProgress = ref<{
  total?: number;
  processed: number;
  percentage?: number;
  pages_fetched: number;
  files_generated: number;
  current_file_rows: number;
} | null>(null);
const exportFileUrl = ref<string | null>(null);
const latestFileAvailable = ref<boolean>(false);
const latestDownloadUrl = ref<string | null>(null);
const latestFileCheckTimer = ref<any>(null);
const exportPercentage = computed<number | undefined>(() => {
  if (!exportProgress.value) return undefined;
  const p = exportProgress.value;
  if (typeof p.percentage === "number")
    return Math.max(0, Math.min(100, p.percentage));
  if (typeof p.total === "number" && p.total > 0) {
    const val = Math.round((p.processed * 10000) / p.total) / 100;
    return Math.max(0, Math.min(100, val));
  }
  return undefined;
});

// 可下载状态：导出已完成且进度100%
const canDownloadNow = computed<boolean>(() => {
  const statusOk = exportStatus.value === "completed";
  const percent = exportPercentage.value;
  const progressPercent = exportProgress.value?.percentage;
  const isFull =
    (typeof percent === "number" && Math.round(percent) >= 100) ||
    progressPercent === 100 ||
    progressPercent === 100.0;
  return Boolean(statusOk && isFull);
});

/**
 * 格式化数字为本地化字符串
 * @param num 数字或字符串
 */
function formatNumber(num: number | string | undefined): string {
  if (num === null || num === undefined || num === "") return "";
  const numValue = typeof num === "string" ? parseFloat(num) : num;
  if (isNaN(numValue as number)) return String(num);
  return (numValue as number).toLocaleString("zh-CN");
}

/**
 * 导出全部结果（异步导出）
 * 触发后端异步任务，返回 task_id，并开始轮询任务状态以展示进度。
 */
const exportAllResults = async (columns?: string[], skipConfirm = false) => {
  try {
    if (!skipConfirm) {
      await ElMessageBox.confirm(
        "确定要导出全部查询结果吗？这可能需要一些时间，导出完成后会提供下载链接。",
        "确认导出",
        {
          confirmButtonText: "确定",
          cancelButtonText: "取消",
          type: "info",
        },
      );
    }

    exportAllLoading.value = true;

    // 构建查询数据
    const dsl = buildDSL();
    const queryData = {
      index: selectedIndices.value,
      query: dsl.query,
      _source: columns && columns.length > 0 ? columns : dsl._source,
    };

    // 优先检查是否有与当前查询条件完全匹配的缓存文件（有效期1小时）
    const cacheResp = await resourcePackageApi.getLatestExportFileByQuery(
      props.packageData.id,
      queryData,
    );
    if (cacheResp.success) {
      const fileData = cacheResp.data;
      latestFileAvailable.value = true;
      latestDownloadUrl.value = fileData?.download_url || null;
      ElMessage.success("命中缓存，正在下载...");
      if (fileData?.download_url) {
        window.open(fileData.download_url, "_blank");
      }
      // 命中缓存则不再触发导出任务
      return;
    }

    // 调用后端异步导出API（统一请求封装）
    const resp = await resourcePackageApi.exportAllResults(
      props.packageData.id,
      queryData,
    );
    if (!resp.success) {
      throw new Error(resp.message || "导出请求失败");
    }
    ElMessage.success("已开始导出全部结果");
    exportTaskId.value = resp.data?.task_id;
    exportStatus.value = "started";
    exportProgress.value = null;
    startPollingExportStatus();
  } catch (error: any) {
    if (error !== "cancel") {
      console.error("导出全部结果失败:", error);
      ElMessage.error(error.message || "导出请求失败");
    }
  } finally {
    exportAllLoading.value = false;
  }
};

/**
 * 开始轮询导出状态
 * 定时请求后端任务状态，更新进度与状态，完成后自动触发下载。
 */
const startPollingExportStatus = () => {
  // 清除之前的轮询定时器
  if (exportPollingTimer.value) {
    clearInterval(exportPollingTimer.value);
  }

  // 每5秒轮询一次任务状态
  exportPollingTimer.value = setInterval(async () => {
    if (!exportTaskId.value) {
      clearInterval(exportPollingTimer.value);
      return;
    }

    try {
      const resp = await resourcePackageApi.getExportStatus(
        props.packageData.id,
        exportTaskId.value,
      );
      if (resp.success) {
        const status = resp.data;
        exportStatus.value = status?.status || null;
        exportProgress.value = status?.progress || null;
        exportFileUrl.value = status?.file_url || exportFileUrl.value;
        exportFileUrl.value = status?.file_url || exportFileUrl.value;

        if (status.status === "completed") {
          // 导出完成，提供下载链接
          clearInterval(exportPollingTimer.value);
          ElMessage.success("导出完成，准备下载文件");
          downloadExportFile();
          exportTaskId.value = null;
        } else if (status.status === "failed") {
          // 导出失败
          clearInterval(exportPollingTimer.value);
          ElMessage.error(status?.message || "导出失败");
          exportTaskId.value = null;
        }
        // 其他状态（started, processing）继续轮询
      } else {
        console.error("获取导出状态失败:", resp.message);
      }
    } catch (error) {
      console.error("轮询导出状态失败:", error);
    }
  }, 5000); // 每5秒轮询一次
};

/**
 * 检查最新的导出文件
 * 功能：
 * - 主动查询后端是否已有未过期的导出文件
 * - 若存在，则设置 latestFileAvailable 与 latestDownloadUrl 用于显示下载链接
 */
async function checkLatestExportFile() {
  try {
    if (!props.packageData?.id) return;
    // 构建与导出一致的查询指纹
    const dsl = buildDSL();
    const queryData = {
      index: selectedIndices.value,
      query: dsl.query,
      _source: dsl._source,
    };
    // 先按查询条件检查匹配的缓存文件
    const respByQuery = await resourcePackageApi.getLatestExportFileByQuery(
      props.packageData.id,
      queryData,
    );
    if (respByQuery.success) {
      latestFileAvailable.value = true;
      latestDownloadUrl.value = respByQuery.data?.download_url || null;
      return;
    }
    // 回退：获取包维度的最新文件（可能与当前查询不一致，不显示下载链接）
    latestFileAvailable.value = false;
    latestDownloadUrl.value = null;
  } catch (e) {
    latestFileAvailable.value = false;
    latestDownloadUrl.value = null;
  }
}

/**
 * 下载导出文件
 * 功能：
 * - 在导出完成后获取最新的预签名下载链接并发起下载
 * - 保留文件1小时（后端策略），不再进行前端的自动删除
 */
const downloadExportFile = async () => {
  try {
    // 首先检查是否有最新的导出文件
    const dsl = buildDSL();
    const queryData = {
      index: selectedIndices.value,
      query: dsl.query,
      _source: dsl._source,
    };
    const respByQuery = await resourcePackageApi.getLatestExportFileByQuery(
      props.packageData.id,
      queryData,
    );
    if (respByQuery.success) {
      const fileData = respByQuery.data;
      window.open(fileData.download_url, "_blank");
      latestFileAvailable.value = true;
      latestDownloadUrl.value = fileData.download_url;
      return;
    }
    // 回退：若轮询状态中有URL则使用
    if (exportFileUrl.value) {
      window.open(exportFileUrl.value, "_blank");
      return;
    }
    ElMessage.warning(
      respByQuery.message || "没有可用的导出文件或文件已过期，请重新导出",
    );
  } catch (error) {
    console.error("下载导出文件失败:", error);
    ElMessage.error("下载导出文件失败");
  }
};

// 组件卸载时清除定时器
onUnmounted(() => {
  if (exportPollingTimer.value) {
    clearInterval(exportPollingTimer.value);
  }
  if (latestFileCheckTimer.value) {
    clearInterval(latestFileCheckTimer.value);
  }
});

// 按需求：仅在用户点击“导出全部结果”后进行缓存检查，此处不在页面加载时自动检查

// 暴露查询方法，便于父组件在进入页面时触发默认查询
defineExpose({
  executeQuery,
  isIndicesReady,
});
</script>

<style scoped lang="scss">
.es-package-query-panel {
  display: flex;
  flex-direction: column;
  gap: 16px;
  // height: 100vh;
  // overflow: hidden;
  :deep(.el-card) {
    border: none;
  }
  :deep(.el-card__body) {
    padding: 2px;
  }
}

.header-card > :deep(.el-card__header) {
  padding: 5px 16px;
  border: none;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 16px;
}

.card-title {
  font-weight: 600;
  font-size: 20px;
  color: #303133;
  padding: 5px 0;
}

.header-search {
  display: flex;
  align-items: center;
  gap: 8px;
  justify-content: center;
}
.advanced-toggle-btn {
  margin-left: 8px;
}

.header-actions {
  display: flex;
  gap: 8px;
}

.section {
  // border: 1px solid #ebeef5;
  border-radius: 8px;
  background: #fff;
}
.section + .section {
  margin-top: 10px;
}
.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 5px 12px;
  border-bottom: 1px dashed #ebeef5;
}
.section-body {
  padding: 0px 8px 5px;

  :deep(.el-input-group__prepend) {
    background-color: white;
  }
}

.filters-section .section-body {
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.filters-detail-section {
  border-bottom: 1px solid #ebeef5;
}
.filters-detail-section .section-body {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.section-title {
  font-weight: 700;
  font-size: 15px;
  color: #606266;
}

/* 抽屉与折叠面板样式优化 */
.detail-drawer {
  :deep(.el-drawer__body) {
    padding: 0; /* 由自定义头和主体控制内边距 */
  }
}
.detail-header {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 16px;
  border-bottom: 1px solid #ebeef5;
}
.detail-title {
  font-size: 18px;
  font-weight: 700;
  color: #303133;
  flex: 1;
}
.detail-body {
  padding: 12px 0px;
}
.narrow-content {
  // max-width: 1100px;
  margin: 0 40px;
}
.detail-collapse {
  /* 让每个 item 内部内容更有内边距感 */
}
.collapse-title {
  display: flex;
  align-items: center;
  font-size: 16px;
  font-weight: 700;
  color: #303133;
}
.collapse-title .left-bar {
  width: 5px;
  height: 23px;
  background: #409eff;
  border-radius: 2px;
  margin-right: 8px;
}
.collapse-content {
  padding: 8px 20px;
}
.detail-form {
  :deep(.el-form-item) {
    margin-bottom: 12px;
  }
  :deep(.el-form-item__label) {
    padding-right: 8px;
  }
}

.locked-conditions {
  margin-bottom: 8px;
}
.condition-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 6px;
}
.condition-tag {
  margin: 0;
}

.default-search {
  margin-bottom: 8px;
}
.search-controls {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 6px;
}

.query-builder {
  margin-top: 8px;
}
.qb-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}
.conditions {
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.condition-item {
  display: flex;
  align-items: center;
  gap: 8px;
}
.dash {
  margin: 0 6px;
  color: #909399;
}

.results-section {
  box-shadow: none;
}
.results-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.view-switch {
  display: flex;
  align-items: center;
}
.display-toggles {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-left: 12px;
}

.results-card {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.results-card .section-body {
  flex: 1;
  overflow: hidden;
}

.results-grid {
  display: grid;
  grid-template-columns: 1fr 4fr; /* 20% / 80% */
  gap: 16px;
  height: calc(100vh - 230px);
}

.agg-pane {
  border-right: 1px solid #ebeef5;
  padding-right: 8px;
  overflow-y: auto;
  height: calc(100% - 50px);
}
.agg-header {
  font-weight: 600;
  color: #606266;
  margin-bottom: 8px;
}
.agg-empty {
  padding: 8px 0;
}
.aggregations {
  display: flex;
  flex-direction: column;
  gap: 10px;
  min-height: 300px;
  padding-right: 6px;
}
.agg-card {
  border-radius: 6px;
  padding: 5px 8px;
}
.agg-title {
  border-bottom: 1px solid #ebeef5;
  font-weight: 600;
  padding-bottom: 6px;
  color: #303133;
}
.agg-body {
  margin-top: 5px;
}
.agg-row {
  display: flex;
  justify-content: space-between;
  font-size: 12px;
  padding: 2px 0;
}
.agg-row.clickable {
  cursor: pointer;
  padding: 5px 0;
  border-radius: 4px;
}
.agg-row.clickable:hover {
  background: #f5f7fa;
}
.agg-key {
  color: #606266;
  max-width: 70%;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.agg-count {
  color: #303133;
}
.agg-json {
  font-size: 12px;
  background: #f9fafc;
  padding: 8px;
  border-radius: 4px;
  overflow: auto;
}

/* 表格容器样式 */
.table-container {
  width: 100%;
  min-height: 300px;
  overflow: auto;
  border: 1px solid #e4e7ed;
  border-radius: 4px;
}

.table-container .el-table {
  height: 100%;
}

/* 卡片容器样式 */
.cards-container {
  width: 100%;
  min-height: 300px;
  overflow-y: auto;
  // padding: 8px;
}

.result-summary {
  color: #606266;
  font-size: 13px;
  padding: 4px 5px 10px;
  text-align: right;
  border-bottom: 1px solid #e4e7ed;
}

.result-pane {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  height: 100%;
}
.cards {
  display: flex;
  flex-direction: column;
  // gap: 6px;
  :deep(.el-card) {
    border-top: 1px solid #e4e7ed;
  }
}
.result-card {
  width: 100%;
  position: relative;
  // height: 180px;
}
.card-content {
  display: flex;
  flex-direction: column;
  gap: 6px;
  padding-bottom: 5px;
}
.card-row {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 8px;
}
.card-row.wide {
  grid-template-columns: 1fr;
}
.kv {
  display: flex;
  // gap: 6px;
  font-size: 13px;
}
.k {
  color: #606266;
  min-width: 70px;
  /** background: #f5f7fa; **/
  padding: 0 6px;
  border-radius: 4px;
}
.v {
  color: #303133;
  word-break: break-word;
}
.v.wrap {
  white-space: pre-wrap;
}
.cell {
  display: inline-block;
  max-width: 100%;
}
.cell.wrap {
  white-space: pre-wrap;
}
.cell.ellipsis {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.cards.compact .kv {
  font-size: 12px;
}
.cards.compact .card-row {
  gap: 6px;
}

/* 卡片复制按钮固定在右下角 */
.card-copy-btn {
  position: absolute;
  right: 10px;
  bottom: 10px;
}

.no-data {
  padding: 20px;
  min-height: calc(100vh - 230px);
  display: flex;
  align-items: center;
  justify-content: center;
}
.pager {
  height: 50px;
  padding: 8px 0;
  display: flex;
  justify-content: flex-end;
  flex-shrink: 0;
  border-top: 1px solid #e4e7ed;
}

@media (max-width: 1024px) {
  .results-grid {
    grid-template-columns: 1fr 3fr;
  }
  .card-row {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 768px) {
  .results-grid {
    grid-template-columns: 1fr;
  }
  .agg-pane {
    border-right: none;
    padding-right: 0;
  }
  .card-row {
    grid-template-columns: 1fr;
  }
}
.download-info {
  margin: 8px 0 4px;
}
.info-row {
  display: flex;
  margin-bottom: 6px;
  align-items: center;
}
.info-row .label {
  color: #606266;
  width: 220px;
}
.info-row .value {
  color: #303133;
}

/* 搜索关键词高亮样式 */
:deep(.highlight) {
  background-color: #fff3cd !important;
  color: #856404 !important;
  padding: 1px 2px !important;
  border-radius: 2px !important;
  font-weight: 500 !important;
}

/* 全屏模式样式 */
.results-card.fullscreen-mode {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  width: 100vw !important;
  height: 100vh !important;
  z-index: 9999;
  margin: 0;
  border-radius: 0;
}

.results-card.fullscreen-mode :deep(.el-card__body) {
  overflow: auto;
}

.results-card.fullscreen-mode .results-grid {
  height: 93vh;
}
.results-card.fullscreen-mode .no-data {
  min-height: 93vh;
}
</style>
