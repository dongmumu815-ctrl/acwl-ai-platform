-- ACWL-AI 测试数据插入脚本
-- 注意：运行此脚本前请确保数据库已创建并执行了schema.sql

USE `acwl-ai-data`;

-- 插入测试用户数据
INSERT INTO acwl_users (username, password_hash, email, role) VALUES
('admin', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj/RK.PmvlG.', 'admin@acwl.ai', 'admin'),
('developer', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj/RK.PmvlG.', 'dev@acwl.ai', 'user'),
('researcher', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj/RK.PmvlG.', 'research@acwl.ai', 'user'),
('tester', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj/RK.PmvlG.', 'test@acwl.ai', 'user');

-- 插入测试模型数据
INSERT INTO acwl_models (name, version, description, base_model, model_type, model_size, parameters, framework, quantization, source_url, local_path, is_active) VALUES
('ChatGLM3', '6B', 'ChatGLM3-6B 对话语言模型', 'ChatGLM3-6B', 'LLM', 12884901888, 6000000000, 'PyTorch', 'FP16', 'https://huggingface.co/THUDM/chatglm3-6b', '/models/chatglm3-6b', TRUE),
('Qwen', '7B-Chat', 'Qwen-7B-Chat 对话模型', 'Qwen-7B', 'LLM', 14316557312, 7000000000, 'PyTorch', 'FP16', 'https://huggingface.co/Qwen/Qwen-7B-Chat', '/models/qwen-7b-chat', TRUE),
('BGE-Large', 'zh-v1.5', 'BGE中文向量模型', 'BGE-Large-zh', 'EMBEDDING', 1073741824, 326000000, 'PyTorch', 'FP32', 'https://huggingface.co/BAAI/bge-large-zh-v1.5', '/models/bge-large-zh-v1.5', TRUE),
('Llama2', '7B-Chat', 'Llama2 7B 对话模型', 'Llama2-7B', 'LLM', 13476838400, 7000000000, 'PyTorch', 'INT8', 'https://huggingface.co/meta-llama/Llama-2-7b-chat-hf', '/models/llama2-7b-chat', FALSE),
('CLIP', 'ViT-B/32', 'CLIP 多模态模型', 'CLIP-ViT-B-32', 'MULTIMODAL', 605028352, 151000000, 'PyTorch', 'FP16', 'https://huggingface.co/openai/clip-vit-base-patch32', '/models/clip-vit-b-32', FALSE);

-- 插入测试服务器数据
INSERT INTO acwl_servers (name, ip_address, ssh_port, ssh_username, server_type, os_info, status, total_memory, total_storage, total_cpu_cores) VALUES
('GPU-Server-01', '10.20.1.201', 22, 'root', 'physical', 'Ubuntu 22.04 LTS', 'online', '128GB', '2TB', 32),
('GPU-Server-02', '10.20.1.202', 22, 'root', 'physical', 'Ubuntu 22.04 LTS', 'online', '256GB', '4TB', 64),
('Cloud-Server-01', '10.20.1.203', 22, 'ubuntu', 'cloud', 'Ubuntu 20.04 LTS', 'online', '64GB', '1TB', 16);

-- 插入测试GPU资源数据
INSERT INTO acwl_gpu_resources (server_id, gpu_name, gpu_type, memory_size, cuda_version, device_id, is_available) VALUES
(1, 'NVIDIA A100', 'A100', '80GB', '12.1', '0', TRUE),
(1, 'NVIDIA A100', 'A100', '80GB', '12.1', '1', TRUE),
(2, 'NVIDIA V100', 'V100', '32GB', '11.8', '0', TRUE),
(2, 'NVIDIA V100', 'V100', '32GB', '11.8', '1', TRUE),
(2, 'NVIDIA V100', 'V100', '32GB', '11.8', '2', TRUE),
(2, 'NVIDIA V100', 'V100', '32GB', '11.8', '3', TRUE),
(3, 'NVIDIA RTX 4090', 'RTX 4090', '24GB', '12.0', '0', TRUE);

-- 插入测试部署数据
INSERT INTO acwl_deployments (model_id, deployment_name, deployment_type, server_id, status, endpoint_url, deploy_path, config, gpu_config, runtime_env, max_concurrent_requests, created_by) VALUES
(1, 'ChatGLM3-6B-Production', 'vLLM', 1, 'running', 'http://10.20.1.201:8001/v1', '/deployments/chatglm3-6b-prod', 
 '{"max_model_len": 8192, "tensor_parallel_size": 1, "dtype": "half"}', 
 '{"gpu_ids": [0], "gpu_memory_utilization": 0.8}', 
 '{"cuda_version": "12.1", "python_version": "3.10", "torch_version": "2.0.1"}', 
 100, 1),
(2, 'Qwen-7B-Development', 'vLLM', 2, 'running', 'http://10.20.1.202:8002/v1', '/deployments/qwen-7b-dev', 
 '{"max_model_len": 4096, "tensor_parallel_size": 2, "dtype": "half"}', 
 '{"gpu_ids": [0, 1], "gpu_memory_utilization": 0.9}', 
 '{"cuda_version": "11.8", "python_version": "3.10", "torch_version": "2.0.1"}', 
 50, 2),
(3, 'BGE-Embedding-Service', 'HuggingFace', 3, 'running', 'http://10.20.1.203:8003/v1', '/deployments/bge-embedding', 
 '{"batch_size": 32, "max_length": 512}', 
 '{"gpu_ids": [0], "gpu_memory_utilization": 0.6}', 
 '{"cuda_version": "12.0", "python_version": "3.10", "transformers_version": "4.35.0"}', 
 200, 1);

-- 插入部署GPU关联数据
INSERT INTO acwl_deployment_gpus (deployment_id, gpu_id, memory_limit) VALUES
(1, 1, '60GB'),
(2, 3, '28GB'),
(2, 4, '28GB'),
(3, 7, '16GB');

-- 插入测试数据集数据
INSERT INTO acwl_datasets (name, description, dataset_type, format, size, record_count, storage_path, is_public, created_by) VALUES
('中文对话数据集', '用于训练中文对话模型的数据集', 'Text', 'JSONL', 1073741824, 100000, '/datasets/chinese_dialogue', TRUE, 1),
('英文问答数据集', '英文问答对数据集', 'Text', 'JSON', 536870912, 50000, '/datasets/english_qa', TRUE, 1),
('多模态图文数据集', '图像和文本配对数据集', 'Multimodal', 'JSON', 5368709120, 25000, '/datasets/multimodal_image_text', FALSE, 2),
('代码生成数据集', '用于代码生成任务的数据集', 'Text', 'JSONL', 2147483648, 75000, '/datasets/code_generation', TRUE, 2);

-- 插入测试微调任务数据
INSERT INTO acwl_fine_tuning_jobs (name, model_id, dataset_id, status, hyperparameters, output_model_name, metrics, log_path, created_by) VALUES
('ChatGLM3领域微调', 1, 1, 'completed', 
 '{"learning_rate": 2e-5, "batch_size": 4, "epochs": 3, "warmup_steps": 100}', 
 'ChatGLM3-6B-Domain-Tuned', 
 '{"train_loss": 0.85, "eval_loss": 0.92, "perplexity": 2.51}', 
 '/logs/finetune_chatglm3_domain.log', 1),
('Qwen代码微调', 2, 4, 'running', 
 '{"learning_rate": 1e-5, "batch_size": 8, "epochs": 5, "warmup_steps": 200}', 
 'Qwen-7B-Code-Tuned', 
 '{"train_loss": 1.12}', 
 '/logs/finetune_qwen_code.log', 2);

-- 插入测试提示词模板数据
INSERT INTO acwl_prompt_templates (name, description, content, variables, category, is_public, created_by) VALUES
('代码生成模板', '用于生成代码的提示词模板', 
 '请根据以下需求生成{language}代码：\n需求：{requirement}\n\n请提供完整的代码实现，包含必要的注释。', 
 '["language", "requirement"]', '代码生成', TRUE, 1),
('文档总结模板', '用于文档总结的提示词模板', 
 '请对以下文档进行总结：\n\n{document}\n\n请提供一个简洁的总结，突出关键信息。', 
 '["document"]', '文档处理', TRUE, 1),
('翻译模板', '多语言翻译提示词模板', 
 '请将以下{source_lang}文本翻译成{target_lang}：\n\n{text}\n\n请保持原文的语气和风格。', 
 '["source_lang", "target_lang", "text"]', '翻译', TRUE, 2),
('问答模板', '智能问答提示词模板', 
 '基于以下上下文回答问题：\n\n上下文：{context}\n\n问题：{question}\n\n请提供准确、详细的答案。', 
 '["context", "question"]', '问答', TRUE, 1);

-- 插入测试知识库数据
INSERT INTO acwl_knowledge_bases (name, description, embedding_model_id, storage_type, config, created_by) VALUES
('技术文档知识库', '存储技术文档和API文档的知识库', 3, 'Faiss', 
 '{"dimension": 1024, "index_type": "IVF", "nlist": 100}', 1),
('产品手册知识库', '产品使用手册和FAQ知识库', 3, 'Milvus', 
 '{"dimension": 1024, "metric_type": "IP", "index_type": "IVF_FLAT"}', 2);

-- 插入测试知识库文档数据
INSERT INTO acwl_knowledge_documents (knowledge_base_id, title, content, file_type, status, metadata, created_by) VALUES
(1, 'FastAPI开发指南', 'FastAPI是一个现代、快速的Web框架，用于构建API...', 'markdown', 'processed', 
 '{"author": "技术团队", "version": "1.0", "tags": ["FastAPI", "Python", "API"]}', 1),
(1, 'Docker部署手册', 'Docker是一个开源的容器化平台...', 'markdown', 'processed', 
 '{"author": "运维团队", "version": "2.1", "tags": ["Docker", "容器", "部署"]}', 1),
(2, '产品功能介绍', 'ACWL-AI平台提供了完整的大模型管理和部署解决方案...', 'text', 'processed', 
 '{"category": "产品介绍", "priority": "high"}', 2);

-- 插入测试API密钥数据
INSERT INTO acwl_api_keys (user_id, key_name, api_key, is_active, expires_at) VALUES
(1, '管理员主密钥', 'ak-admin-1234567890abcdef1234567890abcdef', TRUE, '2025-12-31 23:59:59'),
(2, '开发环境密钥', 'ak-dev-abcdef1234567890abcdef1234567890', TRUE, '2024-12-31 23:59:59'),
(3, '研究项目密钥', 'ak-research-1234abcd5678efgh9012ijkl3456mnop', TRUE, '2024-06-30 23:59:59');

-- 插入测试Agent数据
INSERT INTO acwl_agents (name, description, model_id, prompt_template_id, config, tools, is_active, created_by) VALUES
('代码助手', '专门用于代码生成和代码审查的AI助手', 1, 1, 
 '{"temperature": 0.2, "max_tokens": 2048, "top_p": 0.9}', 
 '["code_executor", "syntax_checker", "documentation_generator"]', TRUE, 1),
('文档助手', '用于文档处理和总结的AI助手', 2, 2, 
 '{"temperature": 0.3, "max_tokens": 1024, "top_p": 0.8}', 
 '["document_parser", "summarizer", "keyword_extractor"]', TRUE, 2),
('翻译助手', '多语言翻译AI助手', 1, 3, 
 '{"temperature": 0.1, "max_tokens": 1024, "top_p": 0.95}', 
 '["language_detector", "translator", "grammar_checker"]', TRUE, 1);

-- 插入测试脚本数据
INSERT INTO acwl_scripts (name, description, content, language, is_public, created_by) VALUES
('模型部署脚本', '自动化模型部署脚本', 
 '#!/bin/bash\n# 模型部署自动化脚本\necho "开始部署模型..."\n# 部署逻辑\necho "部署完成"', 
 'bash', TRUE, 1),
('数据预处理脚本', 'Python数据预处理脚本', 
 'import pandas as pd\nimport json\n\ndef preprocess_data(input_file, output_file):\n    """数据预处理函数"""\n    # 处理逻辑\n    pass', 
 'python', TRUE, 2);

-- 插入测试系统设置数据
INSERT INTO acwl_system_settings (setting_key, setting_value, description) VALUES
('max_concurrent_deployments', '10', '系统最大并发部署数量'),
('default_model_timeout', '300', '默认模型响应超时时间（秒）'),
('enable_gpu_monitoring', 'true', '是否启用GPU监控'),
('log_retention_days', '30', '日志保留天数'),
('api_rate_limit', '1000', 'API调用频率限制（每分钟）');

-- 插入测试使用日志数据
INSERT INTO acwl_usage_logs (user_id, model_id, deployment_id, api_key_id, request_type, tokens_input, tokens_output, duration_ms, status_code, request_ip, request_data, response_data) VALUES
(1, 1, 1, 1, 'chat', 50, 120, 1500, 200, '192.168.1.100', 
 '{"messages": [{"role": "user", "content": "Hello, please introduce FastAPI"}]}', 
 '{"choices": [{"message": {"role": "assistant", "content": "FastAPI is a modern, fast web framework for building APIs with Python..."}}]}'),
(2, 2, 2, 2, 'completion', 80, 200, 2300, 200, '192.168.1.101', 
 '{"prompt": "Please generate a Python function", "max_tokens": 200}', 
 '{"choices": [{"text": "def example_function():\\n    pass"}]}'),
(3, 3, 3, 3, 'embedding', 30, 0, 800, 200, '192.168.1.102', 
 '{"input": "This is a test text"}', 
 '{"data": [{"embedding": [0.1, 0.2, 0.3]}]}');

-- 插入测试部署模板数据
INSERT INTO acwl_deployment_templates (name, description, deployment_type, template_config, created_by) VALUES
('vLLM标准模板', 'vLLM部署的标准配置模板', 'vLLM', 
 '{"max_model_len": 4096, "tensor_parallel_size": 1, "dtype": "half", "gpu_memory_utilization": 0.8, "max_num_seqs": 256}', 1),
('Ollama轻量模板', 'Ollama部署的轻量级配置模板', 'Ollama', 
 '{"num_ctx": 2048, "num_gpu": 1, "num_thread": 8, "repeat_penalty": 1.1}', 1),
('HuggingFace推理模板', 'HuggingFace Transformers推理配置模板', 'HuggingFace', 
 '{"device_map": "auto", "torch_dtype": "float16", "trust_remote_code": true, "max_memory": {"0": "20GB"}}', 2);

-- 插入测试工作流数据
INSERT INTO acwl_workflows (name, description, workflow_definition, is_active, created_by) VALUES
('文档处理工作流', '自动化文档处理和总结工作流', 
 '{"steps": [{"name": "文档解析", "type": "document_parser", "config": {}}, {"name": "内容总结", "type": "summarizer", "config": {"max_length": 200}}, {"name": "关键词提取", "type": "keyword_extractor", "config": {"top_k": 10}}]}', 
 TRUE, 1),
('代码审查工作流', '自动化代码审查工作流', 
 '{"steps": [{"name": "语法检查", "type": "syntax_checker", "config": {}}, {"name": "代码分析", "type": "code_analyzer", "config": {}}, {"name": "建议生成", "type": "suggestion_generator", "config": {}}]}', 
 TRUE, 2);

COMMIT;

-- 显示插入结果统计
SELECT 
    'acwl_users' as table_name, COUNT(*) as record_count FROM acwl_users
UNION ALL
SELECT 'acwl_models', COUNT(*) FROM acwl_models
UNION ALL
SELECT 'acwl_servers', COUNT(*) FROM acwl_servers
UNION ALL
SELECT 'acwl_gpu_resources', COUNT(*) FROM acwl_gpu_resources
UNION ALL
SELECT 'acwl_deployments', COUNT(*) FROM acwl_deployments
UNION ALL
SELECT 'acwl_datasets', COUNT(*) FROM acwl_datasets
UNION ALL
SELECT 'acwl_fine_tuning_jobs', COUNT(*) FROM acwl_fine_tuning_jobs
UNION ALL
SELECT 'acwl_prompt_templates', COUNT(*) FROM acwl_prompt_templates
UNION ALL
SELECT 'acwl_knowledge_bases', COUNT(*) FROM acwl_knowledge_bases
UNION ALL
SELECT 'acwl_api_keys', COUNT(*) FROM acwl_api_keys
UNION ALL
SELECT 'acwl_agents', COUNT(*) FROM acwl_agents
UNION ALL
SELECT 'acwl_scripts', COUNT(*) FROM acwl_scripts
UNION ALL
SELECT 'acwl_system_settings', COUNT(*) FROM acwl_system_settings
UNION ALL
SELECT 'acwl_usage_logs', COUNT(*) FROM acwl_usage_logs
UNION ALL
SELECT 'acwl_deployment_templates', COUNT(*) FROM acwl_deployment_templates
UNION ALL
SELECT 'acwl_workflows', COUNT(*) FROM acwl_workflows;

-- 插入测试项目数据
INSERT INTO acwl_projects (name, description, status, project_type, start_date, end_date, members_count, priority, tags, project_metadata, created_by) VALUES
('AI模型训练项目', '用于训练和优化各种AI模型的项目', 'active', 'model_training', '2024-01-01', '2024-12-31', 5, 'high', '["AI", "机器学习", "深度学习"]', '{"budget": 100000, "department": "AI研发部"}', 1),
('数据分析平台', '企业数据分析和商业智能平台开发', 'active', 'data_analysis', '2024-02-01', '2024-11-30', 8, 'medium', '["数据分析", "BI", "可视化"]', '{"budget": 80000, "department": "数据部"}', 1),
('ETL数据管道', '构建企业级ETL数据处理管道', 'active', 'etl_pipeline', '2024-01-15', '2024-10-15', 3, 'high', '["ETL", "数据处理", "自动化"]', '{"budget": 60000, "department": "数据工程部"}', 2),
('通用开发项目', '通用软件开发和测试项目', 'active', 'general', '2024-03-01', '2024-09-30', 6, 'medium', '["开发", "测试", "通用"]', '{"budget": 50000, "department": "研发部"}', 2),
('历史数据迁移', '已完成的数据迁移项目', 'archived', 'etl_pipeline', '2023-06-01', '2023-12-31', 4, 'low', '["数据迁移", "历史项目"]', '{"budget": 30000, "department": "运维部"}', 1);

-- 插入项目成员数据
INSERT INTO acwl_project_members (project_id, user_id, role, permissions, invited_by, is_active, notes) VALUES
(1, 1, 'admin', '{"permissions": ["all"]}', NULL, TRUE, '项目创建者'),
(1, 2, 'developer', '{"permissions": ["read", "write", "execute"]}', 1, TRUE, 'AI算法工程师'),
(1, 3, 'developer', '{"permissions": ["read", "write"]}', 1, TRUE, '数据科学家'),
(2, 1, 'admin', '{"permissions": ["all"]}', NULL, TRUE, '项目负责人'),
(2, 2, 'viewer', '{"permissions": ["read"]}', 1, TRUE, '技术顾问'),
(2, 4, 'developer', '{"permissions": ["read", "write"]}', 1, TRUE, '前端开发工程师'),
(3, 2, 'admin', '{"permissions": ["all"]}', NULL, TRUE, '项目负责人'),
(3, 3, 'developer', '{"permissions": ["read", "write", "execute"]}', 2, TRUE, '数据工程师'),
(4, 2, 'admin', '{"permissions": ["all"]}', NULL, TRUE, '项目负责人'),
(4, 4, 'developer', '{"permissions": ["read", "write"]}', 2, TRUE, '全栈开发工程师'),
(5, 1, 'admin', '{"permissions": ["all"]}', NULL, TRUE, '项目负责人');

SELECT 'acwl_projects', COUNT(*) FROM acwl_projects
UNION ALL
SELECT 'acwl_project_members', COUNT(*) FROM acwl_project_members;

SELECT '测试数据插入完成！' as status;