import asyncio
import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.core.database import AsyncSessionLocal
from app.models.application import AppTemplate, AppType
from sqlalchemy import select

# vLLM Docker Compose 模板
# 更新说明：
# 1. 增加 ModelScope 支持 (VLLM_USE_MODELSCOPE)
# 2. 增加 ModelScope 缓存挂载
# 3. 增加高级配置项 (tensor_parallel_size, gpu_memory_utilization, served_model_name)
# 4. 支持本地模型挂载和远程模型下载两种模式
VLLM_TEMPLATE = """version: '3.8'

services:
  vllm:
    image: vllm/vllm-openai:latest
    runtime: nvidia
    restart: always
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: {{ gpu_count | default(1) }}
              capabilities: [gpu]
    volumes:
      # 挂载 HuggingFace 和 ModelScope 缓存
      - {{ data_path | default('/data/vllm-cache') }}/huggingface:/root/.cache/huggingface
      - {{ data_path | default('/data/vllm-cache') }}/modelscope:/root/.cache/modelscope
      # 仅当使用本地模型时才挂载模型路径
      {% if use_local_model %}
      - {{ model_path }}:/model
      {% endif %}
    ports:
      - "{{ host_port | default(8000) }}:8000"
    environment:
      - HUGGING_FACE_HUB_TOKEN={{ hf_token }}
      - VLLM_USE_MODELSCOPE={{ use_modelscope | default('true') }}
      # 如果未指定 tensor_parallel_size，默认使用 gpu_count
      - VLLM_TENSOR_PARALLEL_SIZE={{ tensor_parallel_size | default(gpu_count) | default(1) }}
      # 其他环境变量
      - VLLM_GPU_MEMORY_UTILIZATION={{ gpu_memory_utilization | default(0.9) }}
    ipc: host
    # 构建命令
    # 如果是本地模型，使用 /model；如果是远程模型，直接使用 model_path (即 ID)
    command: >
      --model {% if use_local_model %}/model{% else %}{{ model_path }}{% endif %}
      --host 0.0.0.0 
      --port 8000 
      --tensor-parallel-size {{ tensor_parallel_size | default(gpu_count) | default(1) }}
      --gpu-memory-utilization {{ gpu_memory_utilization | default(0.9) }}
      {% if served_model_name %}--served-model-name {{ served_model_name }}{% endif %}
      {{ extra_args }}
"""

# 配置 Schema
CONFIG_SCHEMA = {
    "type": "object",
    "properties": {
        "model_path": {
            "type": "string",
            "title": "模型路径或ID",
            "description": "【核心配置】如果是本地模型，请填写宿主机上模型文件夹的绝对路径（例如 /data/models/chatglm3）；如果是远程模型，请填写模型 ID（例如 zai-org/GLM-5-FP8）",
            "default": "zai-org/GLM-5-FP8"
        },
        "use_local_model": {
            "type": "boolean",
            "title": "使用本地模型",
            "description": "勾选后，系统会将上方填写的【模型路径】直接挂载到容器内使用。请确保路径存在且有读取权限。",
            "default": False
        },
        "use_modelscope": {
            "type": "boolean",
            "title": "使用 ModelScope",
            "description": "启用 VLLM_USE_MODELSCOPE 环境变量，从 ModelScope 下载模型（不勾选则默认从 HuggingFace 下载）",
            "default": True
        },
        "host_port": {
            "type": "integer",
            "title": "服务端口",
            "description": "宿主机暴露的端口",
            "default": 8000,
            "minimum": 1024,
            "maximum": 65535
        },
        "gpu_count": {
            "type": "integer",
            "title": "GPU数量",
            "description": "分配给该实例的GPU数量",
            "default": 1,
            "minimum": 1
        },
        "tensor_parallel_size": {
            "type": "integer",
            "title": "张量并行度 (TP)",
            "description": "通常等于 GPU 数量",
            "default": 1,
            "minimum": 1
        },
        "gpu_memory_utilization": {
            "type": "number",
            "title": "GPU显存利用率",
            "description": "vLLM 占用的显存比例 (0.0 - 1.0)",
            "default": 0.85,
            "minimum": 0.1,
            "maximum": 1.0
        },
        "served_model_name": {
            "type": "string",
            "title": "服务模型名称",
            "description": "API 返回的模型名称，留空则使用模型路径",
            "default": "glm-5-fp8"
        },
        "data_path": {
            "type": "string",
            "title": "缓存存储路径",
            "description": "【辅助配置】用于存储 HuggingFace/ModelScope 下载的缓存文件。建议使用统一的共享目录（如 /data/vllm-cache）。",
            "default": "/data/vllm-cache"
        },
        "hf_token": {
            "type": "string",
            "title": "Hugging Face Token",
            "description": "如有需要，请提供 HF Token",
            "default": ""
        },
        "extra_args": {
            "type": "string",
            "title": "额外启动参数",
            "description": "传递给 vLLM 的额外参数，例如 --speculative-config.method mtp --speculative-config.num_speculative_tokens 1",
            "default": "--speculative-config.method mtp --speculative-config.num_speculative_tokens 1 --tool-call-parser glm47 --reasoning-parser glm45 --enable-auto-tool-choice"
        }
    },
    "required": ["model_path", "host_port"]
}

DEFAULT_CONFIG = {
    "model_path": "zai-org/GLM-5-FP8",
    "use_local_model": False,
    "use_modelscope": True,
    "host_port": 8000,
    "gpu_count": 1,
    "tensor_parallel_size": 1,
    "gpu_memory_utilization": 0.85,
    "served_model_name": "glm-5-fp8",
    "data_path": "/data/vllm-cache",
    "extra_args": "--speculative-config.method mtp --speculative-config.num_speculative_tokens 1 --tool-call-parser glm47 --reasoning-parser glm45 --enable-auto-tool-choice"
}

async def main():
    print("🚀 开始更新 vLLM 应用模板...")
    
    async with AsyncSessionLocal() as db:
        # 检查是否已存在
        stmt = select(AppTemplate).where(AppTemplate.name == "vllm")
        result = await db.execute(stmt)
        existing_template = result.scalar_one_or_none()
        
        if existing_template:
            print("⚠️  模板 'vllm' 已存在，正在更新...")
            existing_template.display_name = "vLLM Inference Server (Advanced)"
            existing_template.version = "latest"
            existing_template.app_type = AppType.docker_compose
            existing_template.config_schema = CONFIG_SCHEMA
            existing_template.default_config = DEFAULT_CONFIG
            existing_template.deploy_template = VLLM_TEMPLATE
            existing_template.is_system = True
            existing_template.description = "vLLM 高性能推理服务，支持 ModelScope 模型下载与高级参数配置。"
            existing_template.icon = "https://raw.githubusercontent.com/vllm-project/vllm/main/docs/source/assets/logos/vllm-logo-text-light.png"
        else:
            print("✨ 创建新模板 'vllm'...")
            new_template = AppTemplate(
                name="vllm",
                display_name="vLLM Inference Server (Advanced)",
                version="latest",
                description="vLLM 高性能推理服务，支持 ModelScope 模型下载与高级参数配置。",
                icon="https://raw.githubusercontent.com/vllm-project/vllm/main/docs/source/assets/logos/vllm-logo-text-light.png",
                app_type=AppType.docker_compose,
                config_schema=CONFIG_SCHEMA,
                default_config=DEFAULT_CONFIG,
                deploy_template=VLLM_TEMPLATE,
                is_system=True
            )
            db.add(new_template)
        
        await db.commit()
        print("✅ vLLM 模板更新完成！")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        print(f"❌ 发生错误: {e}")
        sys.exit(1)
