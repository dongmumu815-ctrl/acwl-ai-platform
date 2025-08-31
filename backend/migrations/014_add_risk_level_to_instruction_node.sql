-- 添加 risk_level 字段到 acwl_instruction_nodes 表
-- 迁移文件: 014_add_risk_level_to_instruction_node.sql
-- 创建时间: 2024-12-19
-- 描述: 为指令节点表添加风险等级字段

-- 1. 添加 risk_level 字段
ALTER TABLE instruction_nodes 
ADD COLUMN risk_level ENUM('safe', 'low', 'medium', 'high', 'critical') 
NOT NULL DEFAULT 'medium' 
COMMENT '风险等级' 
AFTER condition_text;

-- 2. 添加索引以提高查询性能
CREATE INDEX idx_instruction_nodes_risk_level ON instruction_nodes(risk_level);

-- 3. 更新现有数据的风险等级（可选，根据业务需求调整）
-- 示例：将包含特定关键词的节点设置为高风险
-- UPDATE instruction_nodes 
-- SET risk_level = 'high' 
-- WHERE keywords LIKE '%删除%' OR keywords LIKE '%清空%' OR title LIKE '%删除%';

-- 4. 将包含安全操作的节点设置为安全等级
-- UPDATE instruction_nodes 
-- SET risk_level = 'safe' 
-- WHERE keywords LIKE '%查询%' OR keywords LIKE '%查看%' OR title LIKE '%查询%';

COMMIT;