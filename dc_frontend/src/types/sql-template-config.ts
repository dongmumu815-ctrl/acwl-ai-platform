/**
 * SQL模板配置类型定义
 */

export interface SQLTemplateCondition {
  /** 字段名 */
  field: string;
  /** 字段显示名称 */
  label: string;
  /** 字段类型 */
  type: "string" | "number" | "date" | "datetime" | "boolean" | "select";
  /** 是否必填 */
  required: boolean;
  /** 默认值 */
  defaultValue?: any;
  /** 占位符文本 */
  placeholder?: string;
  /** 选项列表（当type为select时） */
  options?: Array<{ label: string; value: any }>;
  /** 验证规则 */
  validation?: {
    min?: number;
    max?: number;
    pattern?: string;
    message?: string;
  };
}

export interface SQLTemplateLockedCondition {
  /** 字段名 */
  field: string;
  /** 字段显示名称 */
  label: string;
  /** 字段类型 */
  type: "string" | "number" | "date" | "datetime" | "boolean" | "select";
  /** 锁定的值 */
  lockedValue: any;
  /** 锁定原因说明 */
  reason?: string;
  /** 选项列表（当type为select时，用于显示锁定值的标签） */
  options?: Array<{ label: string; value: any }>;
}

export interface SQLTemplateConfig {
  /** 必填条件列表 */
  requiredConditions: SQLTemplateCondition[];
  /** 可选条件列表 */
  optionalConditions: SQLTemplateCondition[];
  /** 锁定条件列表（显示但不可修改） */
  lockedConditions?: SQLTemplateLockedCondition[];
  /** 预设条件（固定值，不显示在UI中） */
  presetConditions?: Record<string, any>;
  /** 模板描述 */
  description?: string;
}

/**
 * 配置示例：
 * {
 *   "requiredConditions": [
 *     {
 *       "field": "parent_id",
 *       "label": "父级ID",
 *       "type": "number",
 *       "required": true,
 *       "defaultValue": 1,
 *       "placeholder": "请输入父级ID"
 *     }
 *   ],
 *   "optionalConditions": [
 *     {
 *       "field": "name",
 *       "label": "名称",
 *       "type": "string",
 *       "required": false,
 *       "placeholder": "请输入名称进行筛选"
 *     },
 *     {
 *       "field": "status",
 *       "label": "状态",
 *       "type": "select",
 *       "required": false,
 *       "options": [
 *         { "label": "启用", "value": 1 },
 *         { "label": "禁用", "value": 0 }
 *       ]
 *     }
 *   ],
 *   "presetConditions": {
 *     "deleted": 0
 *   },
 *   "description": "查询指定父级下的代理信息"
 * }
 */
