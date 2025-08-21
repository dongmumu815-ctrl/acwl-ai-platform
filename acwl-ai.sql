/*
 Navicat Premium Dump SQL

 Source Server         : 10.20.1.200-mysql
 Source Server Type    : MySQL
 Source Server Version : 80033 (8.0.33)
 Source Host           : 10.20.1.200:3306
 Source Schema         : acwl-ai

 Target Server Type    : MySQL
 Target Server Version : 80033 (8.0.33)
 File Encoding         : 65001

 Date: 21/07/2025 17:13:47
*/

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- ----------------------------
-- Table structure for acwl_agents
-- ----------------------------
DROP TABLE IF EXISTS `acwl_agents`;
CREATE TABLE `acwl_agents`  (
  `id` int NOT NULL AUTO_INCREMENT COMMENT 'Agent ID，自增主键',
  `name` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT 'Agent名称',
  `description` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL COMMENT 'Agent描述',
  `model_id` int NOT NULL COMMENT '使用的模型ID',
  `prompt_template_id` int NULL DEFAULT NULL COMMENT '使用的提示词模板ID',
  `config` json NULL COMMENT 'Agent配置',
  `tools` json NULL COMMENT '可用工具列表',
  `is_active` tinyint(1) NULL DEFAULT 0 COMMENT '是否激活',
  `created_by` int NULL DEFAULT NULL COMMENT '创建者ID',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 7 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_general_ci COMMENT = 'Agent表，定义基于大模型的智能代理及其行为配置' ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of acwl_agents
-- ----------------------------
INSERT INTO `acwl_agents` VALUES (4, '代码助手', '专门用于代码生成和代码审查的AI助手', 1, 1, '{\"top_p\": 0.9, \"max_tokens\": 2048, \"temperature\": 0.2}', '[\"code_executor\", \"syntax_checker\", \"documentation_generator\"]', 1, 1, '2025-07-09 14:41:40', '2025-07-09 14:41:40');
INSERT INTO `acwl_agents` VALUES (5, '文档助手', '用于文档处理和总结的AI助手', 2, 2, '{\"top_p\": 0.8, \"max_tokens\": 1024, \"temperature\": 0.3}', '[\"document_parser\", \"summarizer\", \"keyword_extractor\"]', 1, 2, '2025-07-09 14:41:40', '2025-07-09 14:41:40');
INSERT INTO `acwl_agents` VALUES (6, '翻译助手', '多语言翻译AI助手', 1, 3, '{\"top_p\": 0.95, \"max_tokens\": 1024, \"temperature\": 0.1}', '[\"language_detector\", \"translator\", \"grammar_checker\"]', 1, 1, '2025-07-09 14:41:40', '2025-07-09 14:41:40');

-- ----------------------------
-- Table structure for acwl_api_keys
-- ----------------------------
DROP TABLE IF EXISTS `acwl_api_keys`;
CREATE TABLE `acwl_api_keys`  (
  `id` int NOT NULL AUTO_INCREMENT COMMENT 'API密钥ID，自增主键',
  `user_id` int NOT NULL COMMENT '所属用户ID',
  `key_name` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '密钥名称',
  `api_key` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT 'API密钥值',
  `is_active` tinyint(1) NULL DEFAULT 1 COMMENT '是否激活',
  `last_used_at` timestamp NULL DEFAULT NULL COMMENT '最后使用时间',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `expires_at` timestamp NULL DEFAULT NULL COMMENT '过期时间',
  PRIMARY KEY (`id`) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 7 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_general_ci COMMENT = 'API密钥表，管理用户访问系统API的认证密钥' ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of acwl_api_keys
-- ----------------------------
INSERT INTO `acwl_api_keys` VALUES (4, 1, '管理员主密钥', 'ak-admin-1234567890abcdef1234567890abcdef', 1, NULL, '2025-07-09 14:41:40', '2025-12-31 23:59:59');
INSERT INTO `acwl_api_keys` VALUES (5, 2, '开发环境密钥', 'ak-dev-abcdef1234567890abcdef1234567890', 1, NULL, '2025-07-09 14:41:40', '2024-12-31 23:59:59');
INSERT INTO `acwl_api_keys` VALUES (6, 3, '研究项目密钥', 'ak-research-1234abcd5678efgh9012ijkl3456mnop', 1, NULL, '2025-07-09 14:41:40', '2024-06-30 23:59:59');

-- ----------------------------
-- Table structure for acwl_datasets
-- ----------------------------
DROP TABLE IF EXISTS `acwl_datasets`;
CREATE TABLE `acwl_datasets`  (
  `id` int NOT NULL AUTO_INCREMENT COMMENT '数据集ID，自增主键',
  `name` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '数据集名称',
  `description` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL COMMENT '数据集描述',
  `dataset_type` enum('Text','Image','Audio','Video','Multimodal') CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '数据集类型：文本、图像、音频、视频、多模态',
  `format` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT '格式，如JSON、CSV、JSONL等',
  `size` bigint NULL DEFAULT NULL COMMENT '数据集大小(字节)',
  `record_count` int NULL DEFAULT NULL COMMENT '记录数量',
  `storage_path` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL COMMENT '存储路径',
  `is_public` tinyint(1) NULL DEFAULT 0 COMMENT '是否公开',
  `status` enum('pending','processing','ready','error') CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL DEFAULT 'pending' COMMENT '数据集状态',
  `tags` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL COMMENT '标签，JSON格式存储',
  `preview_data` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL COMMENT '预览数据，JSON格式存储',
  `created_by` int NULL DEFAULT NULL COMMENT '创建者ID',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`) USING BTREE,
  INDEX `idx_datasets_status`(`status` ASC) USING BTREE,
  INDEX `idx_datasets_type`(`dataset_type` ASC) USING BTREE,
  INDEX `idx_datasets_created_by`(`created_by` ASC) USING BTREE,
  INDEX `idx_datasets_created_at`(`created_at` ASC) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 9 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_general_ci COMMENT = '数据集表，存储用于训练、微调和评估模型的数据集信息' ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of acwl_datasets
-- ----------------------------
INSERT INTO `acwl_datasets` VALUES (5, '中文对话数据集', '用于训练中文对话模型的数据集', 'Text', 'JSONL', 1073741824, 100000, '/datasets/chinese_dialogue', 1, 'ready', NULL, NULL, 1, '2025-07-09 14:41:40', '2025-07-11 16:48:33');
INSERT INTO `acwl_datasets` VALUES (6, '英文问答数据集', '英文问答对数据集', 'Text', 'JSON', 536870912, 50000, '/datasets/english_qa', 1, 'ready', NULL, NULL, 1, '2025-07-09 14:41:40', '2025-07-11 16:48:33');
INSERT INTO `acwl_datasets` VALUES (7, '多模态图文数据集', '图像和文本配对数据集', 'Multimodal', 'JSON', 5368709120, 25000, '/datasets/multimodal_image_text', 0, 'ready', NULL, NULL, 2, '2025-07-09 14:41:40', '2025-07-11 16:48:33');
INSERT INTO `acwl_datasets` VALUES (8, '代码生成数据集', '用于代码生成任务的数据集', 'Text', 'JSONL', 2147483648, 75000, '/datasets/code_generation', 1, 'ready', NULL, NULL, 2, '2025-07-09 14:41:40', '2025-07-11 16:48:33');

-- ----------------------------
-- Table structure for acwl_deployment_gpus
-- ----------------------------
DROP TABLE IF EXISTS `acwl_deployment_gpus`;
CREATE TABLE `acwl_deployment_gpus`  (
  `deployment_id` int NOT NULL COMMENT '部署ID',
  `gpu_id` int NOT NULL COMMENT 'GPU ID',
  `memory_limit` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT '显存限制',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  PRIMARY KEY (`deployment_id`, `gpu_id`) USING BTREE COMMENT '复合主键'
) ENGINE = InnoDB CHARACTER SET = utf8mb4 COLLATE = utf8mb4_general_ci COMMENT = '部署GPU关联表，记录部署使用的GPU资源' ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of acwl_deployment_gpus
-- ----------------------------
INSERT INTO `acwl_deployment_gpus` VALUES (1, 1, '60GB', '2025-07-09 14:41:40');
INSERT INTO `acwl_deployment_gpus` VALUES (2, 3, '28GB', '2025-07-09 14:41:40');
INSERT INTO `acwl_deployment_gpus` VALUES (2, 4, '28GB', '2025-07-09 14:41:40');
INSERT INTO `acwl_deployment_gpus` VALUES (3, 7, '16GB', '2025-07-09 14:41:40');

-- ----------------------------
-- Table structure for acwl_deployment_metrics
-- ----------------------------
DROP TABLE IF EXISTS `acwl_deployment_metrics`;
CREATE TABLE `acwl_deployment_metrics`  (
  `id` int NOT NULL AUTO_INCREMENT COMMENT '指标ID，自增主键',
  `deployment_id` int NOT NULL COMMENT '部署ID',
  `timestamp` timestamp NULL DEFAULT CURRENT_TIMESTAMP COMMENT '记录时间',
  `gpu_utilization` json NULL COMMENT 'GPU利用率',
  `gpu_memory_used` json NULL COMMENT 'GPU内存使用',
  `cpu_utilization` float NULL DEFAULT NULL COMMENT 'CPU利用率',
  `memory_used` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT '内存使用',
  `request_count` int NULL DEFAULT NULL COMMENT '请求数',
  `average_latency` int NULL DEFAULT NULL COMMENT '平均延迟(毫秒)',
  `p95_latency` int NULL DEFAULT NULL COMMENT '95%延迟(毫秒)',
  `p99_latency` int NULL DEFAULT NULL COMMENT '99%延迟(毫秒)',
  `error_count` int NULL DEFAULT NULL COMMENT '错误数',
  PRIMARY KEY (`id`) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 1 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_general_ci COMMENT = '部署监控表，记录部署实例的性能指标' ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of acwl_deployment_metrics
-- ----------------------------

-- ----------------------------
-- Table structure for acwl_deployment_resources
-- ----------------------------
DROP TABLE IF EXISTS `acwl_deployment_resources`;
CREATE TABLE `acwl_deployment_resources`  (
  `deployment_id` int NOT NULL COMMENT '部署ID',
  `resource_id` int NOT NULL COMMENT '资源ID',
  `allocation_amount` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '分配量，如\"8GB\"、\"4 cores\"等',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  PRIMARY KEY (`deployment_id`, `resource_id`) USING BTREE COMMENT '复合主键'
) ENGINE = InnoDB CHARACTER SET = utf8mb4 COLLATE = utf8mb4_general_ci COMMENT = '部署资源关联表，记录每个部署实例使用的计算资源情况' ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of acwl_deployment_resources
-- ----------------------------

-- ----------------------------
-- Table structure for acwl_deployment_templates
-- ----------------------------
DROP TABLE IF EXISTS `acwl_deployment_templates`;
CREATE TABLE `acwl_deployment_templates`  (
  `id` int NOT NULL AUTO_INCREMENT COMMENT '模板ID，自增主键',
  `name` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '模板名称',
  `description` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL COMMENT '模板描述',
  `deployment_type` enum('vLLM','Ollama','HuggingFace','Other') CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '部署类型',
  `template_config` json NOT NULL COMMENT '模板配置',
  `created_by` int NULL DEFAULT NULL COMMENT '创建者ID',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 4 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_general_ci COMMENT = '部署模板表，存储预定义的部署配置模板' ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of acwl_deployment_templates
-- ----------------------------
INSERT INTO `acwl_deployment_templates` VALUES (1, 'vLLM标准模板', 'vLLM部署的标准配置模板', 'vLLM', '{\"dtype\": \"half\", \"max_num_seqs\": 256, \"max_model_len\": 4096, \"tensor_parallel_size\": 1, \"gpu_memory_utilization\": 0.8}', 1, '2025-07-09 14:41:40', '2025-07-09 14:41:40');
INSERT INTO `acwl_deployment_templates` VALUES (2, 'Ollama轻量模板', 'Ollama部署的轻量级配置模板', 'Ollama', '{\"num_ctx\": 2048, \"num_gpu\": 1, \"num_thread\": 8, \"repeat_penalty\": 1.1}', 1, '2025-07-09 14:41:40', '2025-07-09 14:41:40');
INSERT INTO `acwl_deployment_templates` VALUES (3, 'HuggingFace推理模板', 'HuggingFace Transformers推理配置模板', 'HuggingFace', '{\"device_map\": \"auto\", \"max_memory\": {\"0\": \"20GB\"}, \"torch_dtype\": \"float16\", \"trust_remote_code\": true}', 2, '2025-07-09 14:41:40', '2025-07-09 14:41:40');

-- ----------------------------
-- Table structure for acwl_deployments
-- ----------------------------
DROP TABLE IF EXISTS `acwl_deployments`;
CREATE TABLE `acwl_deployments`  (
  `id` int NOT NULL AUTO_INCREMENT COMMENT '部署ID，自增主键',
  `model_id` int NOT NULL COMMENT '关联的模型ID',
  `deployment_name` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '部署名称',
  `deployment_type` enum('vLLM','Ollama','HuggingFace','Other') CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '部署类型：vLLM、Ollama、HuggingFace或其他',
  `server_id` int NULL DEFAULT NULL COMMENT '部署服务器ID',
  `status` enum('pending','running','stopped','failed') CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '部署状态：待处理、运行中、已停止、失败',
  `endpoint_url` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT '端点URL',
  `deploy_path` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL COMMENT '部署路径',
  `config` json NULL COMMENT '部署配置，如资源分配等',
  `gpu_config` json NULL COMMENT 'GPU配置，如设备ID列表、显存限制等',
  `runtime_env` json NULL COMMENT '运行环境配置，如CUDA版本、Python环境等',
  `restart_policy` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT 'no' COMMENT '重启策略：no, always, on-failure等',
  `max_concurrent_requests` int NULL DEFAULT NULL COMMENT '最大并发请求数',
  `deployment_logs` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL COMMENT '部署日志路径',
  `created_by` int NULL DEFAULT NULL COMMENT '创建者ID',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 7 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_general_ci COMMENT = '模型部署实例表，记录模型的部署信息和运行状态' ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of acwl_deployments
-- ----------------------------
INSERT INTO `acwl_deployments` VALUES (4, 1, 'ChatGLM3-6B-Production', 'vLLM', 1, 'running', 'http://10.20.1.201:8001/v1', '/deployments/chatglm3-6b-prod', '{\"dtype\": \"half\", \"max_model_len\": 8192, \"tensor_parallel_size\": 1}', '{\"gpu_ids\": [0], \"gpu_memory_utilization\": 0.8}', '{\"cuda_version\": \"12.1\", \"torch_version\": \"2.0.1\", \"python_version\": \"3.10\"}', 'no', 100, NULL, 1, '2025-07-09 14:41:40', '2025-07-09 14:41:40');
INSERT INTO `acwl_deployments` VALUES (5, 2, 'Qwen-7B-Development', 'vLLM', 2, 'running', 'http://10.20.1.202:8002/v1', '/deployments/qwen-7b-dev', '{\"dtype\": \"half\", \"max_model_len\": 4096, \"tensor_parallel_size\": 2}', '{\"gpu_ids\": [0, 1], \"gpu_memory_utilization\": 0.9}', '{\"cuda_version\": \"11.8\", \"torch_version\": \"2.0.1\", \"python_version\": \"3.10\"}', 'no', 50, NULL, 2, '2025-07-09 14:41:40', '2025-07-09 14:41:40');
INSERT INTO `acwl_deployments` VALUES (6, 3, 'BGE-Embedding-Service', 'HuggingFace', 3, 'running', 'http://10.20.1.203:8003/v1', '/deployments/bge-embedding', '{\"batch_size\": 32, \"max_length\": 512}', '{\"gpu_ids\": [0], \"gpu_memory_utilization\": 0.6}', '{\"cuda_version\": \"12.0\", \"python_version\": \"3.10\", \"transformers_version\": \"4.35.0\"}', 'no', 200, NULL, 1, '2025-07-09 14:41:40', '2025-07-09 14:41:40');

-- ----------------------------
-- Table structure for acwl_fine_tuning_jobs
-- ----------------------------
DROP TABLE IF EXISTS `acwl_fine_tuning_jobs`;
CREATE TABLE `acwl_fine_tuning_jobs`  (
  `id` int NOT NULL AUTO_INCREMENT COMMENT '微调任务ID，自增主键',
  `name` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '任务名称',
  `model_id` int NOT NULL COMMENT '基础模型ID',
  `dataset_id` int NOT NULL COMMENT '训练数据集ID',
  `status` enum('pending','running','completed','failed') CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '任务状态：待处理、运行中、已完成、失败',
  `hyperparameters` json NULL COMMENT '超参数配置',
  `output_model_name` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT '输出模型名称',
  `output_model_id` int NULL DEFAULT NULL COMMENT '输出模型ID，完成后填充',
  `metrics` json NULL COMMENT '训练指标',
  `log_path` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL COMMENT '日志路径',
  `created_by` int NULL DEFAULT NULL COMMENT '创建者ID',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 5 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_general_ci COMMENT = '微调任务表，记录模型微调过程的配置、状态和结果' ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of acwl_fine_tuning_jobs
-- ----------------------------
INSERT INTO `acwl_fine_tuning_jobs` VALUES (3, 'ChatGLM3领域微调', 1, 1, 'completed', '{\"epochs\": 3, \"batch_size\": 4, \"warmup_steps\": 100, \"learning_rate\": 0.00002}', 'ChatGLM3-6B-Domain-Tuned', NULL, '{\"eval_loss\": 0.92, \"perplexity\": 2.51, \"train_loss\": 0.85}', '/logs/finetune_chatglm3_domain.log', 1, '2025-07-09 14:41:40', '2025-07-09 14:41:40');
INSERT INTO `acwl_fine_tuning_jobs` VALUES (4, 'Qwen代码微调', 2, 4, 'running', '{\"epochs\": 5, \"batch_size\": 8, \"warmup_steps\": 200, \"learning_rate\": 0.00001}', 'Qwen-7B-Code-Tuned', NULL, '{\"train_loss\": 1.12}', '/logs/finetune_qwen_code.log', 2, '2025-07-09 14:41:40', '2025-07-09 14:41:40');

-- ----------------------------
-- Table structure for acwl_gpu_resources
-- ----------------------------
DROP TABLE IF EXISTS `acwl_gpu_resources`;
CREATE TABLE `acwl_gpu_resources`  (
  `id` int NOT NULL AUTO_INCREMENT COMMENT 'GPU资源ID，自增主键',
  `server_id` int NOT NULL COMMENT '所属服务器ID',
  `gpu_name` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT 'GPU名称',
  `gpu_type` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT 'GPU类型，如NVIDIA A100, V100等',
  `memory_size` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT 'GPU内存大小',
  `cuda_version` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT 'CUDA版本',
  `device_id` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT '设备ID',
  `is_available` tinyint(1) NULL DEFAULT 1 COMMENT '是否可用',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 15 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_general_ci COMMENT = 'GPU资源表，记录服务器上的GPU资源信息' ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of acwl_gpu_resources
-- ----------------------------
INSERT INTO `acwl_gpu_resources` VALUES (8, 1, 'NVIDIA A100', 'A100', '80GB', '12.1', '0', 1, '2025-07-09 14:41:40', '2025-07-09 14:41:40');
INSERT INTO `acwl_gpu_resources` VALUES (9, 1, 'NVIDIA A100', 'A100', '80GB', '12.1', '1', 1, '2025-07-09 14:41:40', '2025-07-09 14:41:40');
INSERT INTO `acwl_gpu_resources` VALUES (10, 2, 'NVIDIA V100', 'V100', '32GB', '11.8', '0', 1, '2025-07-09 14:41:40', '2025-07-09 14:41:40');
INSERT INTO `acwl_gpu_resources` VALUES (11, 2, 'NVIDIA V100', 'V100', '32GB', '11.8', '1', 1, '2025-07-09 14:41:40', '2025-07-09 14:41:40');
INSERT INTO `acwl_gpu_resources` VALUES (12, 2, 'NVIDIA V100', 'V100', '32GB', '11.8', '2', 1, '2025-07-09 14:41:40', '2025-07-09 14:41:40');
INSERT INTO `acwl_gpu_resources` VALUES (13, 2, 'NVIDIA V100', 'V100', '32GB', '11.8', '3', 1, '2025-07-09 14:41:40', '2025-07-09 14:41:40');
INSERT INTO `acwl_gpu_resources` VALUES (14, 3, 'NVIDIA RTX 4090', 'RTX 4090', '24GB', '12.0', '0', 1, '2025-07-09 14:41:40', '2025-07-09 14:41:40');

-- ----------------------------
-- Table structure for acwl_knowledge_bases
-- ----------------------------
DROP TABLE IF EXISTS `acwl_knowledge_bases`;
CREATE TABLE `acwl_knowledge_bases`  (
  `id` int NOT NULL AUTO_INCREMENT COMMENT '知识库ID，自增主键',
  `name` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '知识库名称',
  `description` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL COMMENT '知识库描述',
  `embedding_model_id` int NULL DEFAULT NULL COMMENT '用于向量化的模型ID',
  `storage_type` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT '存储类型，如Faiss、Milvus、Pinecone等',
  `config` json NULL COMMENT '配置信息',
  `created_by` int NULL DEFAULT NULL COMMENT '创建者ID',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 5 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_general_ci COMMENT = '知识库表，管理用于增强模型回答的外部知识库' ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of acwl_knowledge_bases
-- ----------------------------
INSERT INTO `acwl_knowledge_bases` VALUES (3, '技术文档知识库', '存储技术文档和API文档的知识库', 3, 'Faiss', '{\"nlist\": 100, \"dimension\": 1024, \"index_type\": \"IVF\"}', 1, '2025-07-09 14:41:40', '2025-07-09 14:41:40');
INSERT INTO `acwl_knowledge_bases` VALUES (4, '产品手册知识库', '产品使用手册和FAQ知识库', 3, 'Milvus', '{\"dimension\": 1024, \"index_type\": \"IVF_FLAT\", \"metric_type\": \"IP\"}', 2, '2025-07-09 14:41:40', '2025-07-09 14:41:40');

-- ----------------------------
-- Table structure for acwl_knowledge_documents
-- ----------------------------
DROP TABLE IF EXISTS `acwl_knowledge_documents`;
CREATE TABLE `acwl_knowledge_documents`  (
  `id` int NOT NULL AUTO_INCREMENT COMMENT '文档ID，自增主键',
  `knowledge_base_id` int NOT NULL COMMENT '所属知识库ID',
  `title` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '文档标题',
  `content` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL COMMENT '文档内容',
  `file_path` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL COMMENT '文件路径',
  `file_type` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT '文件类型',
  `status` enum('pending','processed','failed') CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL DEFAULT 'pending' COMMENT '处理状态：待处理、已处理、失败',
  `metadata` json NULL COMMENT '元数据',
  `created_by` int NULL DEFAULT NULL COMMENT '创建者ID',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 7 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_general_ci COMMENT = '知识库文档表，存储知识库中的文档内容和处理状态' ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of acwl_knowledge_documents
-- ----------------------------
INSERT INTO `acwl_knowledge_documents` VALUES (4, 1, 'FastAPI开发指南', 'FastAPI是一个现代、快速的Web框架，用于构建API...', NULL, 'markdown', 'processed', '{\"tags\": [\"FastAPI\", \"Python\", \"API\"], \"author\": \"技术团队\", \"version\": \"1.0\"}', 1, '2025-07-09 14:41:40', '2025-07-09 14:41:40');
INSERT INTO `acwl_knowledge_documents` VALUES (5, 1, 'Docker部署手册', 'Docker是一个开源的容器化平台...', NULL, 'markdown', 'processed', '{\"tags\": [\"Docker\", \"容器\", \"部署\"], \"author\": \"运维团队\", \"version\": \"2.1\"}', 1, '2025-07-09 14:41:40', '2025-07-09 14:41:40');
INSERT INTO `acwl_knowledge_documents` VALUES (6, 2, '产品功能介绍', 'ACWL-AI平台提供了完整的大模型管理和部署解决方案...', NULL, 'text', 'processed', '{\"category\": \"产品介绍\", \"priority\": \"high\"}', 2, '2025-07-09 14:41:40', '2025-07-09 14:41:40');

-- ----------------------------
-- Table structure for acwl_model_evaluations
-- ----------------------------
DROP TABLE IF EXISTS `acwl_model_evaluations`;
CREATE TABLE `acwl_model_evaluations`  (
  `id` int NOT NULL AUTO_INCREMENT COMMENT '评估ID，自增主键',
  `model_id` int NOT NULL COMMENT '被评估的模型ID',
  `dataset_id` int NOT NULL COMMENT '评估数据集ID',
  `metrics` json NULL COMMENT '评估指标',
  `evaluation_date` timestamp NULL DEFAULT CURRENT_TIMESTAMP COMMENT '评估日期',
  `created_by` int NULL DEFAULT NULL COMMENT '创建者ID',
  PRIMARY KEY (`id`) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 1 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_general_ci COMMENT = '模型评估表，记录模型性能评估的结果和指标' ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of acwl_model_evaluations
-- ----------------------------

-- ----------------------------
-- Table structure for acwl_models
-- ----------------------------
DROP TABLE IF EXISTS `acwl_models`;
CREATE TABLE `acwl_models`  (
  `id` int NOT NULL AUTO_INCREMENT COMMENT '模型ID，自增主键',
  `name` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '模型名称',
  `version` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '模型版本',
  `description` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL COMMENT '模型描述',
  `base_model` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT '基础模型名称',
  `model_type` enum('LLM','EMBEDDING','MULTIMODAL','OTHER') CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL,
  `model_size` bigint NULL DEFAULT NULL COMMENT '模型大小(字节)',
  `parameters` bigint NULL DEFAULT NULL COMMENT '参数量',
  `framework` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT '框架，如PyTorch、TensorFlow等',
  `quantization` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT '量化类型，如FP16、INT8等',
  `source_url` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL COMMENT '模型下载地址',
  `local_path` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL COMMENT '本地存储路径',
  `is_active` tinyint(1) NULL DEFAULT 0 COMMENT '是否激活',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `name`(`name` ASC, `version` ASC) USING BTREE COMMENT '模型名称和版本的唯一组合'
) ENGINE = InnoDB AUTO_INCREMENT = 12 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_general_ci COMMENT = '大模型信息表，存储系统中所有模型的基本信息和元数据' ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of acwl_models
-- ----------------------------
INSERT INTO `acwl_models` VALUES (6, 'cepiec-translate', '6B', '翻译模型0.8', 'ChatGLM3-6B', 'LLM', 12884901888, 6000000000, 'PyTorch', 'FP16', 'https://huggingface.co/THUDM/chatglm3-6b', '/models/chatglm3-6b', 1, '2025-07-09 14:41:40', '2025-07-11 14:28:56');
INSERT INTO `acwl_models` VALUES (7, 'Qwen-vl-2.5', '7B-Chat', 'Qwen-7B-Chat 对话模型', 'Qwen-7B', 'LLM', 14316557312, 7000000000, 'PyTorch', 'FP16', 'https://huggingface.co/Qwen/Qwen-7B-Chat', '/models/qwen-7b-chat', 1, '2025-07-09 14:41:40', '2025-07-11 14:26:30');
INSERT INTO `acwl_models` VALUES (8, 'Qwen3', 'zh-v1.5', 'BGE中文向量模型', 'BGE-Large-zh', 'EMBEDDING', 1073741824, 326000000, 'PyTorch', 'FP32', 'https://huggingface.co/BAAI/bge-large-zh-v1.5', '/models/bge-large-zh-v1.5', 1, '2025-07-09 14:41:40', '2025-07-11 14:26:26');
INSERT INTO `acwl_models` VALUES (9, 'Deepseek', '7B-Chat', 'Llama2 7B 对话模型', 'Llama2-7B', 'LLM', 13476838400, 7000000000, 'PyTorch', 'INT8', 'https://huggingface.co/meta-llama/Llama-2-7b-chat-hf', '/models/llama2-7b-chat', 0, '2025-07-09 14:41:40', '2025-07-11 14:26:58');
INSERT INTO `acwl_models` VALUES (10, 'qwen2.5', 'ViT-B/32', 'CLIP 多模态模型', 'CLIP-ViT-B-32', 'MULTIMODAL', 605028352, 151000000, 'PyTorch', 'FP16', 'https://huggingface.co/openai/clip-vit-base-patch32', '/models/clip-vit-b-32', 0, '2025-07-09 14:41:40', '2025-07-11 14:27:49');
INSERT INTO `acwl_models` VALUES (11, 'cepiec-read', '1.0', '审读模型0.8', NULL, 'LLM', 242461, NULL, 'PyTorch', NULL, NULL, '/models/adsfasdf-1.0\\cvs2db.sql', 1, '2025-07-10 22:53:19', '2025-07-11 14:29:21');

-- ----------------------------
-- Table structure for acwl_prompt_templates
-- ----------------------------
DROP TABLE IF EXISTS `acwl_prompt_templates`;
CREATE TABLE `acwl_prompt_templates`  (
  `id` int NOT NULL AUTO_INCREMENT COMMENT '提示词模板ID，自增主键',
  `name` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '模板名称',
  `description` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL COMMENT '模板描述',
  `content` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '模板内容',
  `variables` json NULL COMMENT '变量列表',
  `category` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT '分类',
  `is_public` tinyint(1) NULL DEFAULT 0 COMMENT '是否公开',
  `created_by` int NULL DEFAULT NULL COMMENT '创建者ID',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 9 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_general_ci COMMENT = '提示词模板表，存储预定义的提示词模板，用于指导模型生成特定类型的内容' ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of acwl_prompt_templates
-- ----------------------------
INSERT INTO `acwl_prompt_templates` VALUES (5, '代码生成模板', '用于生成代码的提示词模板', '请根据以下需求生成{language}代码：\n需求：{requirement}\n\n请提供完整的代码实现，包含必要的注释。', '[\"language\", \"requirement\"]', '代码生成', 1, 1, '2025-07-09 14:41:40', '2025-07-09 14:41:40');
INSERT INTO `acwl_prompt_templates` VALUES (6, '文档总结模板', '用于文档总结的提示词模板', '请对以下文档进行总结：\n\n{document}\n\n请提供一个简洁的总结，突出关键信息。', '[\"document\"]', '文档处理', 1, 1, '2025-07-09 14:41:40', '2025-07-09 14:41:40');
INSERT INTO `acwl_prompt_templates` VALUES (7, '翻译模板', '多语言翻译提示词模板', '请将以下{source_lang}文本翻译成{target_lang}：\n\n{text}\n\n请保持原文的语气和风格。', '[\"source_lang\", \"target_lang\", \"text\"]', '翻译', 1, 2, '2025-07-09 14:41:40', '2025-07-09 14:41:40');
INSERT INTO `acwl_prompt_templates` VALUES (8, '问答模板', '智能问答提示词模板', '基于以下上下文回答问题：\n\n上下文：{context}\n\n问题：{question}\n\n请提供准确、详细的答案。', '[\"context\", \"question\"]', '问答', 1, 1, '2025-07-09 14:41:40', '2025-07-09 14:41:40');

-- ----------------------------
-- Table structure for acwl_resources
-- ----------------------------
DROP TABLE IF EXISTS `acwl_resources`;
CREATE TABLE `acwl_resources`  (
  `id` int NOT NULL AUTO_INCREMENT COMMENT '资源ID，自增主键',
  `name` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '资源名称',
  `resource_type` enum('GPU','CPU','Memory','Storage') CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '资源类型：GPU、CPU、内存、存储',
  `capacity` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '容量，如\"16GB\"、\"8 cores\"等',
  `is_available` tinyint(1) NULL DEFAULT 1 COMMENT '是否可用',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 1 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_general_ci COMMENT = '计算资源表，管理系统可用的计算资源如GPU、CPU等' ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of acwl_resources
-- ----------------------------

-- ----------------------------
-- Table structure for acwl_scripts
-- ----------------------------
DROP TABLE IF EXISTS `acwl_scripts`;
CREATE TABLE `acwl_scripts`  (
  `id` int NOT NULL AUTO_INCREMENT COMMENT '脚本ID，自增主键',
  `name` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '脚本名称',
  `description` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL COMMENT '脚本描述',
  `content` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '脚本内容',
  `language` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '脚本语言，如Python、JavaScript等',
  `is_public` tinyint(1) NULL DEFAULT 0 COMMENT '是否公开',
  `created_by` int NULL DEFAULT NULL COMMENT '创建者ID',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 5 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_general_ci COMMENT = '脚本表，存储用于自动化任务和处理的脚本代码' ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of acwl_scripts
-- ----------------------------
INSERT INTO `acwl_scripts` VALUES (3, '模型部署脚本', '自动化模型部署脚本', '#!/bin/bash\n# 模型部署自动化脚本\necho \"开始部署模型...\"\n# 部署逻辑\necho \"部署完成\"', 'bash', 1, 1, '2025-07-09 14:41:40', '2025-07-09 14:41:40');
INSERT INTO `acwl_scripts` VALUES (4, '数据预处理脚本', 'Python数据预处理脚本', 'import pandas as pd\nimport json\n\ndef preprocess_data(input_file, output_file):\n    \"\"\"数据预处理函数\"\"\"\n    # 处理逻辑\n    pass', 'python', 1, 2, '2025-07-09 14:41:40', '2025-07-09 14:41:40');

-- ----------------------------
-- Table structure for acwl_server_metrics
-- ----------------------------
DROP TABLE IF EXISTS `acwl_server_metrics`;
CREATE TABLE `acwl_server_metrics`  (
  `id` int NOT NULL AUTO_INCREMENT COMMENT '指标ID，自增主键',
  `server_id` int NOT NULL COMMENT '服务器ID',
  `cpu_usage` float NULL DEFAULT NULL COMMENT 'CPU使用率（百分比）',
  `memory_usage` float NULL DEFAULT NULL COMMENT '内存使用率（百分比）',
  `disk_usage` float NULL DEFAULT NULL COMMENT '磁盘使用率（百分比）',
  `network_in` float NULL DEFAULT NULL COMMENT '网络入流量（MB/s）',
  `network_out` float NULL DEFAULT NULL COMMENT '网络出流量（MB/s）',
  `gpu_metrics` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL COMMENT 'GPU监控数据（JSON格式）',
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`) USING BTREE,
  INDEX `server_id`(`server_id` ASC) USING BTREE,
  CONSTRAINT `acwl_server_metrics_ibfk_1` FOREIGN KEY (`server_id`) REFERENCES `acwl_servers` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT
) ENGINE = InnoDB AUTO_INCREMENT = 1 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_general_ci COMMENT = '服务器监控指标表，记录服务器的实时监控数据' ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of acwl_server_metrics
-- ----------------------------

-- ----------------------------
-- Table structure for acwl_servers
-- ----------------------------
DROP TABLE IF EXISTS `acwl_servers`;
CREATE TABLE `acwl_servers`  (
  `id` int NOT NULL AUTO_INCREMENT COMMENT '服务器ID，自增主键',
  `name` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '服务器名称',
  `ip_address` varchar(45) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '服务器IP地址',
  `ssh_port` int NULL DEFAULT 22 COMMENT 'SSH端口',
  `ssh_username` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT 'SSH用户名',
  `ssh_key_path` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL COMMENT 'SSH密钥路径',
  `ssh_password` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT 'SSH密码（加密存储）',
  `server_type` enum('physical','virtual','cloud') CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '服务器类型：物理机、虚拟机、云服务器',
  `os_info` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT '操作系统信息',
  `status` enum('online','offline','maintenance') CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL DEFAULT 'offline' COMMENT '服务器状态',
  `total_memory` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT '总内存',
  `total_storage` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT '总存储空间',
  `total_cpu_cores` int NULL DEFAULT NULL COMMENT '总CPU核心数',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 7 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_general_ci COMMENT = '服务器表，存储部署大模型服务的物理或虚拟服务器信息' ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of acwl_servers
-- ----------------------------
INSERT INTO `acwl_servers` VALUES (4, 'GPU-Server-01', '10.20.1.201', 22, 'root', NULL, NULL, 'physical', 'Ubuntu 22.04 LTS', 'online', '128GB', '2TB', 32, '2025-07-09 14:41:40', '2025-07-09 14:41:40');
INSERT INTO `acwl_servers` VALUES (5, 'GPU-Server-02', '10.20.1.202', 22, 'root', NULL, NULL, 'physical', 'Ubuntu 22.04 LTS', 'online', '256GB', '4TB', 64, '2025-07-09 14:41:40', '2025-07-09 14:41:40');
INSERT INTO `acwl_servers` VALUES (6, 'Cloud-Server-01', '10.20.1.203', 22, 'ubuntu', NULL, NULL, 'cloud', 'Ubuntu 20.06 LTS', 'online', '64GB', '1TB', 16, '2025-07-09 14:41:40', '2025-07-09 22:43:57');

-- ----------------------------
-- Table structure for acwl_system_settings
-- ----------------------------
DROP TABLE IF EXISTS `acwl_system_settings`;
CREATE TABLE `acwl_system_settings`  (
  `id` int NOT NULL AUTO_INCREMENT COMMENT '设置ID，自增主键',
  `setting_key` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '设置键，唯一',
  `setting_value` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL COMMENT '设置值',
  `description` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL COMMENT '设置描述',
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `setting_key`(`setting_key` ASC) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 11 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_general_ci COMMENT = '系统设置表，存储全局配置参数和系统级设置' ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of acwl_system_settings
-- ----------------------------
INSERT INTO `acwl_system_settings` VALUES (6, 'max_concurrent_deployments', '10', '系统最大并发部署数量', '2025-07-09 14:41:40');
INSERT INTO `acwl_system_settings` VALUES (7, 'default_model_timeout', '300', '默认模型响应超时时间（秒）', '2025-07-09 14:41:40');
INSERT INTO `acwl_system_settings` VALUES (8, 'enable_gpu_monitoring', 'true', '是否启用GPU监控', '2025-07-09 14:41:40');
INSERT INTO `acwl_system_settings` VALUES (9, 'log_retention_days', '30', '日志保留天数', '2025-07-09 14:41:40');
INSERT INTO `acwl_system_settings` VALUES (10, 'api_rate_limit', '1000', 'API调用频率限制（每分钟）', '2025-07-09 14:41:40');

-- ----------------------------
-- Table structure for acwl_usage_logs
-- ----------------------------
DROP TABLE IF EXISTS `acwl_usage_logs`;
CREATE TABLE `acwl_usage_logs`  (
  `id` int NOT NULL AUTO_INCREMENT COMMENT '日志ID，自增主键',
  `user_id` int NULL DEFAULT NULL COMMENT '用户ID',
  `model_id` int NULL DEFAULT NULL COMMENT '模型ID',
  `deployment_id` int NULL DEFAULT NULL COMMENT '部署ID',
  `api_key_id` int NULL DEFAULT NULL COMMENT 'API密钥ID',
  `request_type` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT '请求类型，如completion、chat、embedding等',
  `tokens_input` int NULL DEFAULT NULL COMMENT '输入token数',
  `tokens_output` int NULL DEFAULT NULL COMMENT '输出token数',
  `duration_ms` int NULL DEFAULT NULL COMMENT '请求持续时间(毫秒)',
  `status_code` int NULL DEFAULT NULL COMMENT '状态码',
  `request_time` timestamp NULL DEFAULT CURRENT_TIMESTAMP COMMENT '请求时间',
  `request_ip` varchar(45) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT '请求IP地址',
  `request_data` json NULL COMMENT '请求数据',
  `response_data` json NULL COMMENT '响应数据',
  PRIMARY KEY (`id`) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 7 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_general_ci COMMENT = '使用日志表，记录系统API调用和模型使用的详细日志' ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of acwl_usage_logs
-- ----------------------------
INSERT INTO `acwl_usage_logs` VALUES (4, 1, 1, 1, 1, 'chat', 50, 120, 1500, 200, '2025-07-09 14:41:40', '192.168.1.100', '{\"messages\": [{\"role\": \"user\", \"content\": \"Hello, please introduce FastAPI\"}]}', '{\"choices\": [{\"message\": {\"role\": \"assistant\", \"content\": \"FastAPI is a modern, fast web framework for building APIs with Python...\"}}]}');
INSERT INTO `acwl_usage_logs` VALUES (5, 2, 2, 2, 2, 'completion', 80, 200, 2300, 200, '2025-07-09 14:41:40', '192.168.1.101', '{\"prompt\": \"Please generate a Python function\", \"max_tokens\": 200}', '{\"choices\": [{\"text\": \"def example_function():\\n    pass\"}]}');
INSERT INTO `acwl_usage_logs` VALUES (6, 3, 3, 3, 3, 'embedding', 30, 0, 800, 200, '2025-07-09 14:41:40', '192.168.1.102', '{\"input\": \"This is a test text\"}', '{\"data\": [{\"embedding\": [0.1, 0.2, 0.3]}]}');

-- ----------------------------
-- Table structure for acwl_users
-- ----------------------------
DROP TABLE IF EXISTS `acwl_users`;
CREATE TABLE `acwl_users`  (
  `id` int NOT NULL AUTO_INCREMENT COMMENT '用户ID，自增主键',
  `username` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '用户名，唯一',
  `password_hash` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '密码哈希值',
  `email` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '电子邮箱，唯一',
  `role` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL DEFAULT 'user' COMMENT '用户角色，如admin、user等',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `username`(`username` ASC) USING BTREE,
  UNIQUE INDEX `email`(`email` ASC) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 10 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_general_ci COMMENT = '系统用户信息表，存储用户账号和权限信息' ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of acwl_users
-- ----------------------------
INSERT INTO `acwl_users` VALUES (5, 'admin', '$2b$12$LyZhiCZnwN4w7Eg/6AVfpOdi9JTmxVx951lw/sNkgBd6Biqj2KT2m', 'admin@acwl.ai', 'admin', '2025-07-09 14:41:40', '2025-07-10 19:27:37');
INSERT INTO `acwl_users` VALUES (6, 'developer', '$2b$12$JOEa6c1c5L3vg62VLrhTs.Xvoic3yj.h51hhUN3cmmzoqYX6juHKu', 'dev@acwl.ai', 'user', '2025-07-09 14:41:40', '2025-07-10 19:26:47');
INSERT INTO `acwl_users` VALUES (7, 'researcher', '$2b$12$JOEa6c1c5L3vg62VLrhTs.Xvoic3yj.h51hhUN3cmmzoqYX6juHKu', 'research@acwl.ai', 'user', '2025-07-09 14:41:40', '2025-07-10 19:26:47');
INSERT INTO `acwl_users` VALUES (8, 'tester', '$2b$12$JOEa6c1c5L3vg62VLrhTs.Xvoic3yj.h51hhUN3cmmzoqYX6juHKu', 'test@acwl.ai', 'user', '2025-07-09 14:41:40', '2025-07-10 19:26:47');
INSERT INTO `acwl_users` VALUES (9, 'newuser', '$2b$12$3OcBiZWX.iTXQlGFTR2JSe6PPs/0WhBGrgEM3ceZK8Z7vsHWzxy5m', 'newuser@example.com', 'user', '2025-07-10 22:59:38', '2025-07-10 22:59:38');

-- ----------------------------
-- Table structure for acwl_workflows
-- ----------------------------
DROP TABLE IF EXISTS `acwl_workflows`;
CREATE TABLE `acwl_workflows`  (
  `id` int NOT NULL AUTO_INCREMENT COMMENT '工作流ID，自增主键',
  `name` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '工作流名称',
  `description` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL COMMENT '工作流描述',
  `workflow_definition` json NULL COMMENT '工作流定义',
  `is_active` tinyint(1) NULL DEFAULT 0 COMMENT '是否激活',
  `created_by` int NULL DEFAULT NULL COMMENT '创建者ID',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 3 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_general_ci COMMENT = '工作流表，定义和管理复杂的模型调用流程和任务编排' ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of acwl_workflows
-- ----------------------------
INSERT INTO `acwl_workflows` VALUES (1, '文档处理工作流', '自动化文档处理和总结工作流', '{\"steps\": [{\"name\": \"文档解析\", \"type\": \"document_parser\", \"config\": {}}, {\"name\": \"内容总结\", \"type\": \"summarizer\", \"config\": {\"max_length\": 200}}, {\"name\": \"关键词提取\", \"type\": \"keyword_extractor\", \"config\": {\"top_k\": 10}}]}', 1, 1, '2025-07-09 14:41:40', '2025-07-09 14:41:40');
INSERT INTO `acwl_workflows` VALUES (2, '代码审查工作流', '自动化代码审查工作流', '{\"steps\": [{\"name\": \"语法检查\", \"type\": \"syntax_checker\", \"config\": {}}, {\"name\": \"代码分析\", \"type\": \"code_analyzer\", \"config\": {}}, {\"name\": \"建议生成\", \"type\": \"suggestion_generator\", \"config\": {}}]}', 1, 2, '2025-07-09 14:41:40', '2025-07-09 14:41:40');

-- ----------------------------
-- Table structure for cpc_agents
-- ----------------------------
DROP TABLE IF EXISTS `cpc_agents`;
CREATE TABLE `cpc_agents`  (
  `id` bigint NOT NULL,
  `name` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL,
  `description` text CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL,
  `node_type` enum('router','agent') CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL,
  `parent_id` bigint NULL DEFAULT NULL,
  `system_message` text CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL,
  `llm_config` json NULL,
  `tools` json NULL,
  `tool_configs` json NULL,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `name`(`name` ASC) USING BTREE
) ENGINE = InnoDB CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of cpc_agents
-- ----------------------------

SET FOREIGN_KEY_CHECKS = 1;
