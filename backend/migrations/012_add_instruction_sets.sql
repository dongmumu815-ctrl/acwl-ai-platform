-- 创建指令集表
CREATE TABLE instruction_sets (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL COMMENT '指令集名称',
    description TEXT COMMENT '指令集描述',
    version VARCHAR(50) DEFAULT '1.0.0' COMMENT '版本号',
    status ENUM('ACTIVE', 'INACTIVE', 'DRAFT') DEFAULT 'DRAFT' COMMENT '状态',
    created_by INT COMMENT '创建者ID',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    INDEX idx_name (name),
    INDEX idx_status (status),
    INDEX idx_created_by (created_by)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='指令集表';

-- 创建指令节点表
CREATE TABLE instruction_nodes (
    id INT AUTO_INCREMENT PRIMARY KEY,
    instruction_set_id INT NOT NULL COMMENT '所属指令集ID',
    parent_id INT NULL COMMENT '父节点ID，NULL表示根节点',
    node_type ENUM('CONDITION', 'ACTION', 'RESULT') NOT NULL COMMENT '节点类型：条件/动作/结果',
    title VARCHAR(255) NOT NULL COMMENT '节点标题',
    description TEXT COMMENT '节点描述',
    condition_text TEXT COMMENT '条件文本（用于AI判断）',
    condition_type ENUM('TEXT_ANALYSIS', 'KEYWORD_MATCH', 'REGEX_MATCH', 'AI_CLASSIFICATION') DEFAULT 'AI_CLASSIFICATION' COMMENT '条件类型',
    action_type ENUM('CONTINUE', 'STOP', 'BRANCH', 'CLASSIFY') DEFAULT 'CONTINUE' COMMENT '动作类型',
    result_value VARCHAR(500) COMMENT '结果值',
    result_confidence DECIMAL(3,2) DEFAULT 0.00 COMMENT '结果置信度',
    sort_order INT DEFAULT 0 COMMENT '排序顺序',
    is_active BOOLEAN DEFAULT TRUE COMMENT '是否激活',
    metadata JSON COMMENT '扩展元数据',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    FOREIGN KEY (instruction_set_id) REFERENCES instruction_sets(id) ON DELETE CASCADE,
    FOREIGN KEY (parent_id) REFERENCES instruction_nodes(id) ON DELETE CASCADE,
    INDEX idx_instruction_set (instruction_set_id),
    INDEX idx_parent (parent_id),
    INDEX idx_node_type (node_type),
    INDEX idx_sort_order (sort_order),
    INDEX idx_active (is_active)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='指令节点表';

-- 创建指令执行历史表
CREATE TABLE instruction_executions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    instruction_set_id INT NOT NULL COMMENT '指令集ID',
    input_text TEXT NOT NULL COMMENT '输入文本',
    execution_path JSON COMMENT '执行路径（节点ID数组）',
    final_result VARCHAR(500) COMMENT '最终结果',
    confidence_score DECIMAL(3,2) COMMENT '置信度分数',
    execution_time_ms INT COMMENT '执行时间（毫秒）',
    status ENUM('SUCCESS', 'FAILED', 'TIMEOUT') DEFAULT 'SUCCESS' COMMENT '执行状态',
    error_message TEXT COMMENT '错误信息',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    FOREIGN KEY (instruction_set_id) REFERENCES instruction_sets(id) ON DELETE CASCADE,
    INDEX idx_instruction_set (instruction_set_id),
    INDEX idx_status (status),
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='指令执行历史表';

-- 插入示例数据
INSERT INTO instruction_sets (name, description, version, status) VALUES 
('内容审核指令集', '用于检测文本内容是否包含敏感信息的决策树指令集', '1.0.0', 'ACTIVE');

SET @instruction_set_id = LAST_INSERT_ID();

-- 插入示例节点
INSERT INTO instruction_nodes (instruction_set_id, parent_id, node_type, title, description, condition_text, sort_order) VALUES 
(@instruction_set_id, NULL, 'CONDITION', '根节点：内容分类', '开始内容审核流程', '请分析以下文本内容', 0),
(@instruction_set_id, 1, 'CONDITION', '宗教内容检测', '检测是否包含宗教相关内容', '这段文本是否涉及宗教内容？', 1),
(@instruction_set_id, 2, 'CONDITION', '佛教内容检测', '进一步检测是否为佛教相关', '这段文本是否特指佛教相关内容？', 1),
(@instruction_set_id, 2, 'CONDITION', '其他宗教检测', '检测其他宗教内容', '这段文本涉及哪种宗教？', 2),
(@instruction_set_id, 1, 'CONDITION', '色情内容检测', '检测是否包含色情相关内容', '这段文本是否涉及色情内容？', 2),
(@instruction_set_id, 5, 'CONDITION', '色情程度分析', '分析色情内容的严重程度', '这段色情内容的严重程度如何？', 1),
(@instruction_set_id, 1, 'CONDITION', '暴力内容检测', '检测是否包含暴力相关内容', '这段文本是否涉及暴力内容？', 3);