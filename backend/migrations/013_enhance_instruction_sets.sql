-- 增强指令集功能的数据库迁移
-- 添加新的节点类型、配置字段和评分机制

-- 1. 更新节点类型枚举
ALTER TABLE instruction_nodes 
MODIFY COLUMN node_type ENUM(
    'EXECUTOR',      -- 执行器节点（根节点）
    'CONDITION',     -- 条件判断节点
    'ACTION',        -- 动作执行节点
    'BRANCH',        -- 分支节点
    'AGGREGATOR',    -- 聚合器节点
    'CLASSIFIER',    -- 分类器节点
    'RESULT'         -- 结果节点
) NOT NULL COMMENT '节点类型';

-- 2. 更新条件类型枚举
ALTER TABLE instruction_nodes 
MODIFY COLUMN condition_type ENUM(
    'TEXT_ANALYSIS',
    'KEYWORD_MATCH', 
    'REGEX_MATCH',
    'AI_CLASSIFICATION',
    'SENTIMENT_ANALYSIS',  -- 情感分析
    'CONTENT_SAFETY',      -- 内容安全检测
    'CUSTOM_FUNCTION'      -- 自定义函数
) DEFAULT 'AI_CLASSIFICATION' COMMENT '条件类型';

-- 3. 更新动作类型枚举
ALTER TABLE instruction_nodes 
MODIFY COLUMN action_type ENUM(
    'CONTINUE',
    'STOP', 
    'BRANCH',
    'CLASSIFY',
    'APPROVE',           -- 通过审核
    'REJECT',            -- 拒绝审核
    'FLAG_CONTENT',      -- 标记内容
    'SEND_NOTIFICATION', -- 发送通知
    'LOG_EVENT',         -- 记录事件
    'CUSTOM_ACTION'      -- 自定义动作
) DEFAULT 'CONTINUE' COMMENT '动作类型';

-- 4. 添加新的配置字段
ALTER TABLE instruction_nodes 
ADD COLUMN executor_config JSON COMMENT '执行器配置（JSON格式）',
ADD COLUMN score_config JSON COMMENT '评分配置（JSON格式）',
ADD COLUMN condition_config JSON COMMENT '条件配置（JSON格式，替代原有字段）',
ADD COLUMN action_config JSON COMMENT '动作配置（JSON格式）';

-- 5. 更新执行状态枚举
ALTER TABLE instruction_executions 
MODIFY COLUMN status ENUM(
    'SUCCESS',
    'FAILED', 
    'TIMEOUT',
    'PENDING',     -- 待处理
    'CANCELLED'    -- 已取消
) DEFAULT 'PENDING' COMMENT '执行状态';

-- 6. 创建节点评分表
CREATE TABLE instruction_node_scores (
    id INT AUTO_INCREMENT PRIMARY KEY,
    node_id INT NOT NULL COMMENT '节点ID',
    execution_id INT NOT NULL COMMENT '执行记录ID',
    score_type ENUM(
        'ACCURACY',     -- 准确性
        'CONFIDENCE',   -- 置信度
        'PERFORMANCE',  -- 性能
        'RELEVANCE',    -- 相关性
        'SAFETY'        -- 安全性
    ) NOT NULL COMMENT '评分类型',
    score_value DECIMAL(5,4) NOT NULL COMMENT '评分值（0-1）',
    weight DECIMAL(3,2) DEFAULT 1.00 COMMENT '权重',
    metadata JSON COMMENT '评分元数据',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    FOREIGN KEY (node_id) REFERENCES instruction_nodes(id) ON DELETE CASCADE,
    FOREIGN KEY (execution_id) REFERENCES instruction_executions(id) ON DELETE CASCADE,
    INDEX idx_node_execution (node_id, execution_id),
    INDEX idx_score_type (score_type),
    INDEX idx_score_value (score_value)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='节点评分表';

-- 7. 创建执行上下文表
CREATE TABLE instruction_execution_contexts (
    id INT AUTO_INCREMENT PRIMARY KEY,
    execution_id INT NOT NULL COMMENT '执行记录ID',
    context_data JSON NOT NULL COMMENT '执行上下文数据',
    variables JSON COMMENT '执行变量',
    session_id VARCHAR(255) COMMENT '会话ID',
    user_id INT COMMENT '用户ID',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    FOREIGN KEY (execution_id) REFERENCES instruction_executions(id) ON DELETE CASCADE,
    INDEX idx_execution (execution_id),
    INDEX idx_session (session_id),
    INDEX idx_user (user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='指令执行上下文表';

-- 8. 创建节点关系表（用于复杂的节点依赖关系）
CREATE TABLE instruction_node_relations (
    id INT AUTO_INCREMENT PRIMARY KEY,
    source_node_id INT NOT NULL COMMENT '源节点ID',
    target_node_id INT NOT NULL COMMENT '目标节点ID',
    relation_type ENUM(
        'PARENT_CHILD',   -- 父子关系
        'DEPENDENCY',     -- 依赖关系
        'AGGREGATION',    -- 聚合关系
        'CLASSIFICATION'  -- 分类关系
    ) NOT NULL COMMENT '关系类型',
    condition_expression TEXT COMMENT '条件表达式',
    weight DECIMAL(3,2) DEFAULT 1.00 COMMENT '关系权重',
    metadata JSON COMMENT '关系元数据',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    FOREIGN KEY (source_node_id) REFERENCES instruction_nodes(id) ON DELETE CASCADE,
    FOREIGN KEY (target_node_id) REFERENCES instruction_nodes(id) ON DELETE CASCADE,
    INDEX idx_source_target (source_node_id, target_node_id),
    INDEX idx_relation_type (relation_type),
    UNIQUE KEY uk_source_target_type (source_node_id, target_node_id, relation_type)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='节点关系表';

-- 9. 更新示例数据，添加执行器根节点
UPDATE instruction_nodes 
SET node_type = 'EXECUTOR',
    title = '内容审核执行器',
    description = '内容审核流程的执行器节点，负责协调整个审核流程',
    executor_config = JSON_OBJECT(
        'strategy', 'SEQUENTIAL',
        'timeout_ms', 30000,
        'retry_count', 2,
        'early_stop_conditions', JSON_ARRAY(
            JSON_OBJECT(
                'condition_type', 'confidence_threshold',
                'threshold_value', 0.95,
                'operator', 'gte'
            )
        )
    ),
    score_config = JSON_OBJECT(
        'enabled', true,
        'score_types', JSON_ARRAY('ACCURACY', 'CONFIDENCE', 'SAFETY'),
        'weights', JSON_OBJECT(
            'ACCURACY', 0.4,
            'CONFIDENCE', 0.3,
            'SAFETY', 0.3
        ),
        'aggregation_method', 'WEIGHTED_AVERAGE',
        'min_threshold', 0.6
    )
WHERE parent_id IS NULL;

-- 10. 迁移完成

COMMIT;