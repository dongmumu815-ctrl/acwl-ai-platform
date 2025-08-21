-- 用户表
CREATE TABLE acwl_users (
    id INT PRIMARY KEY AUTO_INCREMENT COMMENT '用户ID，自增主键',
    username VARCHAR(50) NOT NULL UNIQUE COMMENT '用户名，唯一',
    password_hash VARCHAR(255) NOT NULL COMMENT '密码哈希值',
    email VARCHAR(100) NOT NULL UNIQUE COMMENT '电子邮箱，唯一',
    role VARCHAR(20) NOT NULL DEFAULT 'user' COMMENT '用户角色，如admin、user等',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间'
) COMMENT '系统用户信息表，存储用户账号和权限信息';

-- 模型表
CREATE TABLE acwl_models (
    id INT PRIMARY KEY AUTO_INCREMENT COMMENT '模型ID，自增主键',
    name VARCHAR(100) NOT NULL COMMENT '模型名称',
    version VARCHAR(50) NOT NULL COMMENT '模型版本',
    description TEXT COMMENT '模型描述',
    base_model VARCHAR(100) COMMENT '基础模型名称',
    model_type ENUM('LLM', 'EMBEDDING', 'MULTIMODAL', 'OTHER') NOT NULL COMMENT '模型类型：LLM、Embedding、多模态或其他',
    model_size BIGINT COMMENT '模型大小(字节)',
    parameters BIGINT COMMENT '参数量',
    framework VARCHAR(50) COMMENT '框架，如PyTorch、TensorFlow等',
    quantization VARCHAR(20) COMMENT '量化类型，如FP16、INT8等',
    source_url TEXT COMMENT '模型下载地址',
    local_path TEXT COMMENT '本地存储路径',
    is_active BOOLEAN DEFAULT FALSE COMMENT '是否激活',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    UNIQUE KEY (name, version) COMMENT '模型名称和版本的唯一组合'
) COMMENT '大模型信息表，存储系统中所有模型的基本信息和元数据';

-- 部署实例表
CREATE TABLE acwl_deployments (
    id INT PRIMARY KEY AUTO_INCREMENT COMMENT '部署ID，自增主键',
    model_id INT NOT NULL COMMENT '关联的模型ID',
    deployment_name VARCHAR(100) NOT NULL COMMENT '部署名称',
    deployment_type ENUM('vLLM', 'Ollama', 'HuggingFace', 'Other') NOT NULL COMMENT '部署类型：vLLM、Ollama、HuggingFace或其他',
    server_id INT COMMENT '部署服务器ID',
    status ENUM('pending', 'running', 'stopped', 'failed') NOT NULL COMMENT '部署状态：待处理、运行中、已停止、失败',
    endpoint_url VARCHAR(255) COMMENT '端点URL',
    deploy_path TEXT COMMENT '部署路径',
    config JSON COMMENT '部署配置，如资源分配等',
    gpu_config JSON COMMENT 'GPU配置，如设备ID列表、显存限制等',
    runtime_env JSON COMMENT '运行环境配置，如CUDA版本、Python环境等',
    restart_policy VARCHAR(50) DEFAULT 'no' COMMENT '重启策略：no, always, on-failure等',
    max_concurrent_requests INT COMMENT '最大并发请求数',
    deployment_logs TEXT COMMENT '部署日志路径',
    created_by INT COMMENT '创建者ID',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间'
) COMMENT '模型部署实例表，记录模型的部署信息和运行状态';

-- 资源表
CREATE TABLE acwl_resources (
    id INT PRIMARY KEY AUTO_INCREMENT COMMENT '资源ID，自增主键',
    name VARCHAR(100) NOT NULL COMMENT '资源名称',
    resource_type ENUM('GPU', 'CPU', 'Memory', 'Storage') NOT NULL COMMENT '资源类型：GPU、CPU、内存、存储',
    capacity VARCHAR(50) NOT NULL COMMENT '容量，如"16GB"、"8 cores"等',
    is_available BOOLEAN DEFAULT TRUE COMMENT '是否可用',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间'
) COMMENT '计算资源表，管理系统可用的计算资源如GPU、CPU等';

-- 部署资源关联表
CREATE TABLE acwl_deployment_resources (
    deployment_id INT NOT NULL COMMENT '部署ID',
    resource_id INT NOT NULL COMMENT '资源ID',
    allocation_amount VARCHAR(50) NOT NULL COMMENT '分配量，如"8GB"、"4 cores"等',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    PRIMARY KEY (deployment_id, resource_id) COMMENT '复合主键'
) COMMENT '部署资源关联表，记录每个部署实例使用的计算资源情况';

-- 数据集表
CREATE TABLE acwl_datasets (
    id INT PRIMARY KEY AUTO_INCREMENT COMMENT '数据集ID，自增主键',
    name VARCHAR(100) NOT NULL COMMENT '数据集名称',
    description TEXT COMMENT '数据集描述',
    dataset_type ENUM('Text', 'Image', 'Audio', 'Video', 'Multimodal') NOT NULL COMMENT '数据集类型：文本、图像、音频、视频、多模态',
    format VARCHAR(50) COMMENT '格式，如JSON、CSV、JSONL等',
    size BIGINT COMMENT '数据集大小(字节)',
    record_count INT COMMENT '记录数量',
    storage_path TEXT COMMENT '存储路径',
    is_public BOOLEAN DEFAULT FALSE COMMENT '是否公开',
    created_by INT COMMENT '创建者ID',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间'
) COMMENT '数据集表，存储用于训练、微调和评估模型的数据集信息';

-- 微调任务表
CREATE TABLE acwl_fine_tuning_jobs (
    id INT PRIMARY KEY AUTO_INCREMENT COMMENT '微调任务ID，自增主键',
    name VARCHAR(100) NOT NULL COMMENT '任务名称',
    model_id INT NOT NULL COMMENT '基础模型ID',
    dataset_id INT NOT NULL COMMENT '训练数据集ID',
    status ENUM('pending', 'running', 'completed', 'failed') NOT NULL COMMENT '任务状态：待处理、运行中、已完成、失败',
    hyperparameters JSON COMMENT '超参数配置',
    output_model_name VARCHAR(100) COMMENT '输出模型名称',
    output_model_id INT COMMENT '输出模型ID，完成后填充',
    metrics JSON COMMENT '训练指标',
    log_path TEXT COMMENT '日志路径',
    created_by INT COMMENT '创建者ID',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间'
) COMMENT '微调任务表，记录模型微调过程的配置、状态和结果';

-- 提示词模板表
CREATE TABLE acwl_prompt_templates (
    id INT PRIMARY KEY AUTO_INCREMENT COMMENT '提示词模板ID，自增主键',
    name VARCHAR(100) NOT NULL COMMENT '模板名称',
    description TEXT COMMENT '模板描述',
    content TEXT NOT NULL COMMENT '模板内容',
    variables JSON COMMENT '变量列表',
    category VARCHAR(50) COMMENT '分类',
    is_public BOOLEAN DEFAULT FALSE COMMENT '是否公开',
    created_by INT COMMENT '创建者ID',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间'
) COMMENT '提示词模板表，存储预定义的提示词模板，用于指导模型生成特定类型的内容';

-- 脚本表
CREATE TABLE acwl_scripts (
    id INT PRIMARY KEY AUTO_INCREMENT COMMENT '脚本ID，自增主键',
    name VARCHAR(100) NOT NULL COMMENT '脚本名称',
    description TEXT COMMENT '脚本描述',
    content TEXT NOT NULL COMMENT '脚本内容',
    language VARCHAR(50) NOT NULL COMMENT '脚本语言，如Python、JavaScript等',
    is_public BOOLEAN DEFAULT FALSE COMMENT '是否公开',
    created_by INT COMMENT '创建者ID',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间'
) COMMENT '脚本表，存储用于自动化任务和处理的脚本代码';

-- Agent表
CREATE TABLE acwl_agents (
    id INT PRIMARY KEY AUTO_INCREMENT COMMENT 'Agent ID，自增主键',
    name VARCHAR(100) NOT NULL COMMENT 'Agent名称',
    description TEXT COMMENT 'Agent描述',
    model_id INT NOT NULL COMMENT '使用的模型ID',
    prompt_template_id INT COMMENT '使用的提示词模板ID',
    config JSON COMMENT 'Agent配置',
    tools JSON COMMENT '可用工具列表',
    is_active BOOLEAN DEFAULT FALSE COMMENT '是否激活',
    created_by INT COMMENT '创建者ID',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间'
) COMMENT 'Agent表，定义基于大模型的智能代理及其行为配置';

-- 知识库表
CREATE TABLE acwl_knowledge_bases (
    id INT PRIMARY KEY AUTO_INCREMENT COMMENT '知识库ID，自增主键',
    name VARCHAR(100) NOT NULL COMMENT '知识库名称',
    description TEXT COMMENT '知识库描述',
    embedding_model_id INT COMMENT '用于向量化的模型ID',
    storage_type VARCHAR(50) COMMENT '存储类型，如Faiss、Milvus、Pinecone等',
    config JSON COMMENT '配置信息',
    created_by INT COMMENT '创建者ID',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间'
) COMMENT '知识库表，管理用于增强模型回答的外部知识库';

-- 知识库文档表
CREATE TABLE acwl_knowledge_documents (
    id INT PRIMARY KEY AUTO_INCREMENT COMMENT '文档ID，自增主键',
    knowledge_base_id INT NOT NULL COMMENT '所属知识库ID',
    title VARCHAR(255) NOT NULL COMMENT '文档标题',
    content TEXT COMMENT '文档内容',
    file_path TEXT COMMENT '文件路径',
    file_type VARCHAR(50) COMMENT '文件类型',
    status ENUM('pending', 'processed', 'failed') NOT NULL DEFAULT 'pending' COMMENT '处理状态：待处理、已处理、失败',
    metadata JSON COMMENT '元数据',
    created_by INT COMMENT '创建者ID',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间'
) COMMENT '知识库文档表，存储知识库中的文档内容和处理状态';

-- 模型评估表
CREATE TABLE acwl_model_evaluations (
    id INT PRIMARY KEY AUTO_INCREMENT COMMENT '评估ID，自增主键',
    model_id INT NOT NULL COMMENT '被评估的模型ID',
    dataset_id INT NOT NULL COMMENT '评估数据集ID',
    metrics JSON COMMENT '评估指标',
    evaluation_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '评估日期',
    created_by INT COMMENT '创建者ID'
) COMMENT '模型评估表，记录模型性能评估的结果和指标';

-- API密钥表
CREATE TABLE acwl_api_keys (
    id INT PRIMARY KEY AUTO_INCREMENT COMMENT 'API密钥ID，自增主键',
    user_id INT NOT NULL COMMENT '所属用户ID',
    key_name VARCHAR(100) NOT NULL COMMENT '密钥名称',
    api_key VARCHAR(255) NOT NULL COMMENT 'API密钥值',
    is_active BOOLEAN DEFAULT TRUE COMMENT '是否激活',
    last_used_at TIMESTAMP NULL COMMENT '最后使用时间',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    expires_at TIMESTAMP NULL COMMENT '过期时间'
) COMMENT 'API密钥表，管理用户访问系统API的认证密钥';

-- 使用日志表
CREATE TABLE acwl_usage_logs (
    id INT PRIMARY KEY AUTO_INCREMENT COMMENT '日志ID，自增主键',
    user_id INT COMMENT '用户ID',
    model_id INT COMMENT '模型ID',
    deployment_id INT COMMENT '部署ID',
    api_key_id INT COMMENT 'API密钥ID',
    request_type VARCHAR(50) COMMENT '请求类型，如completion、chat、embedding等',
    tokens_input INT COMMENT '输入token数',
    tokens_output INT COMMENT '输出token数',
    duration_ms INT COMMENT '请求持续时间(毫秒)',
    status_code INT COMMENT '状态码',
    request_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '请求时间',
    request_ip VARCHAR(45) COMMENT '请求IP地址',
    request_data JSON COMMENT '请求数据',
    response_data JSON COMMENT '响应数据'
) COMMENT '使用日志表，记录系统API调用和模型使用的详细日志';

-- 工作流表
CREATE TABLE acwl_workflows (
    id INT PRIMARY KEY AUTO_INCREMENT COMMENT '工作流ID，自增主键',
    name VARCHAR(100) NOT NULL COMMENT '工作流名称',
    description TEXT COMMENT '工作流描述',
    workflow_definition JSON COMMENT '工作流定义',
    is_active BOOLEAN DEFAULT FALSE COMMENT '是否激活',
    created_by INT COMMENT '创建者ID',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间'
) COMMENT '工作流表，定义和管理复杂的模型调用流程和任务编排';

-- 系统设置表
CREATE TABLE acwl_system_settings (
    id INT PRIMARY KEY AUTO_INCREMENT COMMENT '设置ID，自增主键',
    setting_key VARCHAR(100) NOT NULL UNIQUE COMMENT '设置键，唯一',
    setting_value TEXT COMMENT '设置值',
    description TEXT COMMENT '设置描述',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间'
) COMMENT '系统设置表，存储全局配置参数和系统级设置';

-- 服务器表
CREATE TABLE acwl_servers (
    id INT PRIMARY KEY AUTO_INCREMENT COMMENT '服务器ID，自增主键',
    name VARCHAR(100) NOT NULL COMMENT '服务器名称',
    ip_address VARCHAR(45) NOT NULL COMMENT '服务器IP地址',
    ssh_port INT DEFAULT 22 COMMENT 'SSH端口',
    ssh_username VARCHAR(50) COMMENT 'SSH用户名',
    ssh_key_path TEXT COMMENT 'SSH密钥路径',
    ssh_password VARCHAR(255) COMMENT 'SSH密码（加密存储）',
    server_type ENUM('physical', 'virtual', 'cloud') NOT NULL COMMENT '服务器类型：物理机、虚拟机、云服务器',
    os_info VARCHAR(100) COMMENT '操作系统信息',
    status ENUM('online', 'offline', 'maintenance') NOT NULL DEFAULT 'offline' COMMENT '服务器状态',
    total_memory VARCHAR(50) COMMENT '总内存',
    total_storage VARCHAR(50) COMMENT '总存储空间',
    total_cpu_cores INT COMMENT '总CPU核心数',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间'
) COMMENT '服务器表，存储部署大模型服务的物理或虚拟服务器信息';

-- GPU资源表
CREATE TABLE acwl_gpu_resources (
    id INT PRIMARY KEY AUTO_INCREMENT COMMENT 'GPU资源ID，自增主键',
    server_id INT NOT NULL COMMENT '所属服务器ID',
    gpu_name VARCHAR(100) NOT NULL COMMENT 'GPU名称',
    gpu_type VARCHAR(50) COMMENT 'GPU类型，如NVIDIA A100, V100等',
    memory_size VARCHAR(50) COMMENT 'GPU内存大小',
    cuda_version VARCHAR(20) COMMENT 'CUDA版本',
    device_id VARCHAR(20) COMMENT '设备ID',
    is_available BOOLEAN DEFAULT TRUE COMMENT '是否可用',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间'
) COMMENT 'GPU资源表，记录服务器上的GPU资源信息';

-- 部署GPU关联表
CREATE TABLE acwl_deployment_gpus (
    deployment_id INT NOT NULL COMMENT '部署ID',
    gpu_id INT NOT NULL COMMENT 'GPU ID',
    memory_limit VARCHAR(50) COMMENT '显存限制',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    PRIMARY KEY (deployment_id, gpu_id) COMMENT '复合主键'
) COMMENT '部署GPU关联表，记录部署使用的GPU资源';

-- 部署模板表
CREATE TABLE acwl_deployment_templates (
    id INT PRIMARY KEY AUTO_INCREMENT COMMENT '模板ID，自增主键',
    name VARCHAR(100) NOT NULL COMMENT '模板名称',
    description TEXT COMMENT '模板描述',
    deployment_type ENUM('vLLM', 'Ollama', 'HuggingFace', 'Other') NOT NULL COMMENT '部署类型',
    template_config JSON NOT NULL COMMENT '模板配置',
    created_by INT COMMENT '创建者ID',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间'
) COMMENT '部署模板表，存储预定义的部署配置模板';

-- 部署监控表
CREATE TABLE acwl_deployment_metrics (
    id INT PRIMARY KEY AUTO_INCREMENT COMMENT '指标ID，自增主键',
    deployment_id INT NOT NULL COMMENT '部署ID',
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '记录时间',
    gpu_utilization JSON COMMENT 'GPU利用率',
    gpu_memory_used JSON COMMENT 'GPU内存使用',
    cpu_utilization FLOAT COMMENT 'CPU利用率',
    memory_used VARCHAR(50) COMMENT '内存使用',
    request_count INT COMMENT '请求数',
    average_latency INT COMMENT '平均延迟(毫秒)',
    p95_latency INT COMMENT '95%延迟(毫秒)',
    p99_latency INT COMMENT '99%延迟(毫秒)',
    error_count INT COMMENT '错误数'
) COMMENT '部署监控表，记录部署实例的性能指标';