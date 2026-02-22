FROM docker.m.daocloud.io/library/python:3.12-slim

# 设置工作目录
WORKDIR /app

# 设置环境变量
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    TZ=Asia/Shanghai

# 安装系统依赖和基本的 Shell 工具
# 包含: curl, wget, git, iputils-ping (ping), net-tools (ifconfig), procps (ps), vim
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    wget \
    git \
    iputils-ping \
    net-tools \
    procps \
    vim \
    default-mysql-client \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY requirements-docker.txt requirements.txt

# 安装 Python 依赖
# 使用阿里云源加速，并增加超时时间
RUN pip install --no-cache-dir --default-timeout=1000 -r requirements.txt -i http://mirrors.aliyun.com/pypi/simple/ --trusted-host mirrors.aliyun.com

# 复制项目代码
COPY . .

# 赋予脚本执行权限
RUN chmod +x entrypoint.sh executor_service.py scheduler_service.py

# 暴露端口 (仅作为文档，实际由 docker run -p 控制)
EXPOSE 8000

# 设置入口点
ENTRYPOINT ["./entrypoint.sh"]
