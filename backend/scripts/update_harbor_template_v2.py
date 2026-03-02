import asyncio
import sys
import os

# 将 backend 目录添加到路径以便导入 app 模块
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import AsyncSessionLocal
from app.models.application import AppTemplate, AppType, AppInstance
from sqlalchemy import select

# Harbor Docker Compose 模板
# 基于用户提供的配置，适配 acwl-ai-data 的部署环境
# 移除了 cap_drop/cap_add 等可能导致权限问题的配置，简化为标准配置
# 使用 Jinja2 变量替换配置项
# [2026-02-27] 重大更新：
# 1. 移除 cap_drop/cap_add，避免权限问题
# 2. 将所有 Volume 映射到 {{ data_volume }} 下，不再映射 /var/log 或其他系统目录
# 3. 简化日志配置，直接输出到 data_volume/log
HARBOR_TEMPLATE = """
services:
  log:
    image: goharbor/harbor-log:v2.12.1
    container_name: harbor-log
    restart: always
    volumes:
      - {{ data_volume }}/log/:/var/log/docker/:z
      - {{ data_volume }}/common/config/log/logrotate.conf:/etc/logrotate.d/logrotate.conf
      - {{ data_volume }}/common/config/log/rsyslog_docker.conf:/etc/rsyslog.d/rsyslog_docker.conf
    ports:
      - 127.0.0.1:1514:10514
    networks:
      - harbor
  registry:
    image: goharbor/registry-photon:v2.12.1
    container_name: registry
    restart: always
    volumes:
      - {{ data_volume }}/registry:/storage:z
      - {{ data_volume }}/common/config/registry/:/etc/registry/:z
      - {{ data_volume }}/common/config/registry/root.crt:/etc/registry/root.crt
      - {{ data_volume }}/common/config/shared/trust-certificates:/harbor_cust_cert
    networks:
      - harbor
    depends_on:
      - log
    logging:
      driver: "syslog"
      options:
        syslog-address: "tcp://localhost:1514"
        tag: "registry"
  registryctl:
    image: goharbor/harbor-registryctl:v2.12.1
    container_name: registryctl
    env_file:
      - {{ data_volume }}/common/config/registryctl/env
    restart: always
    volumes:
      - {{ data_volume }}/registry:/storage:z
      - {{ data_volume }}/common/config/registry/:/etc/registry/:z
      - {{ data_volume }}/common/config/registry/root.crt:/etc/registry/root.crt
      - {{ data_volume }}/common/config/registryctl/config.yml:/etc/registryctl/config.yml
      - {{ data_volume }}/common/config/shared/trust-certificates:/harbor_cust_cert
    networks:
      - harbor
    depends_on:
      - log
    logging:
      driver: "syslog"
      options:
        syslog-address: "tcp://localhost:1514"
        tag: "registryctl"
  postgresql:
    image: goharbor/harbor-db:v2.12.1
    container_name: harbor-db
    restart: always
    volumes:
      - {{ data_volume }}/database:/var/lib/postgresql/data:z
    networks:
      harbor:
    env_file:
      - {{ data_volume }}/common/config/db/env
    depends_on:
      - log
    logging:
      driver: "syslog"
      options:
        syslog-address: "tcp://localhost:1514"
        tag: "postgresql"
    shm_size: '1gb'
  core:
    image: goharbor/harbor-core:v2.12.1
    container_name: harbor-core
    env_file:
      - {{ data_volume }}/common/config/core/env
    restart: always
    volumes:
      - {{ data_volume }}/ca_download/:/etc/core/ca/:z
      - {{ data_volume }}/data/:/data/:z
      - {{ data_volume }}/common/config/core/certificates/:/etc/core/certificates/:z
      - {{ data_volume }}/common/config/core/app.conf:/etc/core/app.conf
      - {{ data_volume }}/common/config/core/private_key.pem:/etc/core/private_key.pem
      - {{ data_volume }}/common/config/core/certificates/secretkey:/etc/core/key
      - {{ data_volume }}/common/config/shared/trust-certificates:/harbor_cust_cert
    networks:
      - harbor
    depends_on:
      - log
      - registry
      - redis
      - postgresql
    logging:
      driver: "syslog"
      options:
        syslog-address: "tcp://localhost:1514"
        tag: "core"
  portal:
    image: goharbor/harbor-portal:v2.12.1
    container_name: harbor-portal
    restart: always
    volumes:
      - {{ data_volume }}/common/config/portal/nginx.conf:/etc/nginx/nginx.conf
    networks:
      - harbor
    depends_on:
      - log
    logging:
      driver: "syslog"
      options:
        syslog-address: "tcp://localhost:1514"
        tag: "portal"

  jobservice:
    image: goharbor/harbor-jobservice:v2.12.1
    container_name: harbor-jobservice
    env_file:
      - {{ data_volume }}/common/config/jobservice/env
    restart: always
    volumes:
      - {{ data_volume }}/job_logs:/var/log/jobs:z
      - {{ data_volume }}/common/config/jobservice/config.yml:/etc/jobservice/config.yml
      - {{ data_volume }}/common/config/shared/trust-certificates:/harbor_cust_cert
    networks:
      - harbor
    depends_on:
      - core
    logging:
      driver: "syslog"
      options:
        syslog-address: "tcp://localhost:1514"
        tag: "jobservice"
  redis:
    image: goharbor/redis-photon:v2.12.1
    container_name: redis
    restart: always
    volumes:
      - {{ data_volume }}/redis:/var/lib/redis
    networks:
      harbor:
    depends_on:
      - log
    logging:
      driver: "syslog"
      options:
        syslog-address: "tcp://localhost:1514"
        tag: "redis"
  proxy:
    image: goharbor/nginx-photon:v2.12.1
    container_name: nginx
    restart: always
    volumes:
      - {{ data_volume }}/common/config/nginx:/etc/nginx:z
      - {{ data_volume }}/common/config/shared/trust-certificates:/harbor_cust_cert
    networks:
      - harbor
    ports:
      - {{ http_port }}:8080
      - {{ https_port }}:8443
    depends_on:
      - registry
      - core
      - portal
      - log
    logging:
      driver: "syslog"
      options:
        syslog-address: "tcp://localhost:1514"
        tag: "proxy"
networks:
  harbor:
    external: false
"""

CONFIG_SCHEMA = {
  "type": "object",
  "properties": {
    "http_port": {
      "type": "integer",
      "title": "HTTP Port",
      "default": 80,
      "description": "Harbor HTTP 访问端口"
    },
    "https_port": {
      "type": "integer",
      "title": "HTTPS Port",
      "default": 443,
      "description": "Harbor HTTPS 访问端口"
    },
    "harbor_admin_password": {
      "type": "string",
      "title": "Admin Password",
      "default": "Harbor12345",
      "description": "管理员初始密码"
    },
    "data_volume": {
      "type": "string",
      "title": "Data Path",
      "default": "/data/harbor",
      "description": "宿主机数据存储路径 (包含配置和数据)"
    },
    "external_url": {
      "type": "string",
      "title": "External URL",
      "description": "外部访问地址 (http://ip:port 或 https://domain)"
    }
  },
  "required": ["http_port", "https_port", "harbor_admin_password", "data_volume"]
}

# Harbor Installer Script 模板
# 用于在目标服务器上生成配置文件
# 作为 pre_deploy_script 嵌入到主模板中
INSTALLER_SCRIPT = """#!/bin/bash
# Harbor 初始化安装脚本 (Simplified Config Mode)
# 用途：在部署前检查并生成最小化配置，无需依赖 goharbor/prepare 容器
# 直接生成配置文件，避免 python/docker 依赖问题

set -e

INSTALL_PATH="{{ data_volume }}"
HOSTNAME="{{ hostname }}"
HTTP_PORT="{{ http_port }}"
HTTPS_PORT="{{ https_port }}"

# 默认端口处理
if [ -z "$HTTP_PORT" ]; then HTTP_PORT=5000; fi
if [ -z "$HTTPS_PORT" ]; then HTTPS_PORT=443; fi

# 如果 hostname 未定义，尝试从 external_url 提取，或使用默认值
if [ -z "$HOSTNAME" ] || [ "$HOSTNAME" = "{{ hostname }}" ]; then
    if [ -n "{{ external_url }}" ]; then
        # 尝试提取域名 (简单提取)
        # 支持 http://10.20.1.204:5000 这种格式
        HOSTNAME=$(echo "{{ external_url }}" | sed -E 's/https?:\/\///' | cut -d: -f1 | cut -d/ -f1)
    else
        HOSTNAME="reg.mydomain.com"
    fi
fi

echo "Checking Harbor config at $INSTALL_PATH..."

# 检查核心配置文件是否存在
# [UPDATE] 移除“存在即跳过”逻辑，强制更新配置文件以确保 Nginx PID 和 Core Cache 等配置生效
# if [ -f "$INSTALL_PATH/common/config/core/env" ] && [ -f "$INSTALL_PATH/common/config/db/env" ]; then
#     echo "Configuration exists. Skipping generation."
#     exit 0
# fi

echo "Generating default configurations..."

mkdir -p $INSTALL_PATH/common/config
mkdir -p $INSTALL_PATH/common/config/core
mkdir -p $INSTALL_PATH/common/config/db
mkdir -p $INSTALL_PATH/common/config/jobservice
mkdir -p $INSTALL_PATH/common/config/log
mkdir -p $INSTALL_PATH/common/config/nginx
mkdir -p $INSTALL_PATH/common/config/portal
mkdir -p $INSTALL_PATH/common/config/registry
mkdir -p $INSTALL_PATH/common/config/registryctl
mkdir -p $INSTALL_PATH/common/config/shared/trust-certificates

# --- Generate Core Config ---
# Prepare variables for Core env
EXT_URL="{{ external_url }}"
if [ -z "$EXT_URL" ]; then
    if [ "$HTTP_PORT" != "5000" ] && [ "$HTTP_PORT" != "{{ http_port }}" ]; then
        EXT_URL="http://$HOSTNAME:$HTTP_PORT"
    elif [ "$HTTPS_PORT" != "443" ] && [ "$HTTPS_PORT" != "{{ https_port }}" ]; then
        EXT_URL="https://$HOSTNAME:$HTTPS_PORT"
    else
        EXT_URL="http://$HOSTNAME:5000"
    fi
fi

ADM_PWD="{{ harbor_admin_password }}"
if [ -z "$ADM_PWD" ]; then
    ADM_PWD="Harbor12345"
fi

# Generate or load JobService Secret
mkdir -p $INSTALL_PATH/common/config/secret
if [ ! -f "$INSTALL_PATH/common/config/secret/jobservice_secret" ]; then
    if command -v python3 &> /dev/null; then
        python3 -c "import secrets; print(secrets.token_urlsafe(16), end='')" > $INSTALL_PATH/common/config/secret/jobservice_secret
    else
        openssl rand -base64 16 | tr -d '\n' > $INSTALL_PATH/common/config/secret/jobservice_secret
    fi
fi
JOBSERVICE_SECRET=$(cat $INSTALL_PATH/common/config/secret/jobservice_secret)

cat > $INSTALL_PATH/common/config/core/env <<EOF
LOG_LEVEL=info
CONFIG_PATH=/etc/core/app.conf
SYNC_REGISTRY=false
CHART_CACHE_DRIVER=redis
MAX_JOB_WORKERS=10
TOKEN_SERVICE_URL=http://core:8080/service/token
TOKEN_KEY_PATH=/etc/core/key
ADMIN_PASSWORD=$ADM_PWD
DATABASE_TYPE=postgresql
POSTGRESQL_HOST=postgresql
POSTGRESQL_PORT=5432
POSTGRESQL_USERNAME=postgres
POSTGRESQL_PASSWORD=root123
POSTGRESQL_DATABASE=registry
REDIS_URL=redis://redis:6379/0
EXT_ENDPOINT=$EXT_URL
CORE_URL=http://core:8080
JOBSERVICE_URL=http://jobservice:8080
JOBSERVICE_SECRET=$JOBSERVICE_SECRET
REGISTRY_URL=http://registry:5000
REGISTRY_CONTROLLER_URL=http://registryctl:8080
PORTAL_URL=http://portal:80
# Cache Configuration
_REDIS_URL_CORE=redis://redis:6379/0
_REDIS_URL_REG=redis://redis:6379/1
_REDIS_URL_JOB=redis://redis:6379/2
EOF

cat > $INSTALL_PATH/common/config/core/app.conf <<EOF
appname = Harbor
runmode = prod
enablegzip = true
jobservice_secret = $JOBSERVICE_SECRET

[dev]
httpport = 8080
[prod]
httpport = 8080
EOF

# --- Generate DB Config ---
cat > $INSTALL_PATH/common/config/db/env <<EOF
POSTGRES_PASSWORD=root123
EOF

# --- Generate JobService Config ---
cat > $INSTALL_PATH/common/config/jobservice/env <<EOF
CORE_URL=http://core:8080
JOBSERVICE_SECRET=$JOBSERVICE_SECRET
EOF

cat > $INSTALL_PATH/common/config/jobservice/config.yml <<EOF
protocol: "http"
port: 8080
worker_pool:
  workers: 10
  backend: "redis"
  redis_pool:
    redis_url: "redis://redis:6379/2"
    namespace: "harbor_job_service_namespace"
job_loggers:
  - name: "STD_OUTPUT"
    level: "INFO"
loggers:
  - name: "STD_OUTPUT"
    level: "INFO"
EOF

# --- Generate Registry Config ---
cat > $INSTALL_PATH/common/config/registry/config.yml <<EOF
version: 0.1
log:
  level: info
  fields:
    service: registry
storage:
  cache:
    layerinfo: redis
  filesystem:
    rootdirectory: /storage
  maintenance:
    uploadpurging:
      enabled: false
  delete:
    enabled: true
http:
  addr: :5000
  secret: Harbor12345
  debug:
    addr: localhost:5001
auth:
  token:
    realm: $EXT_URL/service/token
    service: harbor-registry
    issuer: harbor-token-issuer
    rootcertbundle: /etc/registry/root.crt
redis:
  addr: redis:6379
  db: 1
  dial_timeout: 10ms
  read_timeout: 10ms
  write_timeout: 10ms
  pool:
    maxidle: 16
    maxactive: 64
    idletimeout: 300s
EOF

# --- Generate RegistryCtl Config ---
cat > $INSTALL_PATH/common/config/registryctl/env <<EOF
CORE_URL=http://core:8080
CONFIG=/etc/registryctl/config.yml
EOF

# RegistryCtl 需要读取 Registry 的配置
# 但它期望的配置路径是 /etc/registry/config.yml (容器内路径)
# 我们已经在 docker-compose 中挂载了
cat > $INSTALL_PATH/common/config/registryctl/config.yml <<EOF
registry_config: "/etc/registry/config.yml"
registry:
  config: "/etc/registry/config.yml"
log_level: info
EOF

# --- Generate Nginx Config ---
cat > $INSTALL_PATH/common/config/nginx/nginx.conf <<EOF
worker_processes auto;
pid /tmp/nginx.pid;
events {
    worker_connections 1024;
    use epoll;
    multi_accept on;
}
http {
    tcp_nodelay on;
    # Fix permission denied on temp paths by pointing them to /tmp
    client_body_temp_path /tmp/client_body_temp;
    proxy_temp_path       /tmp/proxy_temp;
    fastcgi_temp_path     /tmp/fastcgi_temp;
    uwsgi_temp_path       /tmp/uwsgi_temp;
    scgi_temp_path        /tmp/scgi_temp;
    
    # Increase body size for docker push
    client_max_body_size 0;

    # include /etc/nginx/mime.types;
    # default_type application/octet-stream;
    
    # 简化的 mime types，避免依赖外部文件
    types {
        text/html                             html htm shtml;
        text/css                              css;
        text/xml                              xml;
        image/gif                             gif;
        image/jpeg                            jpeg jpg;
        application/javascript                js;
        application/atom+xml                  atom;
        application/rss+xml                   rss;
        text/mathml                           mml;
        text/plain                            txt;
        text/vnd.sun.j2me.app-descriptor      jad;
        text/vnd.wap.wml                      wml;
        text/x-component                      htc;
        image/png                             png;
        image/tiff                            tif tiff;
        image/vnd.wap.wbmp                    wbmp;
        image/x-icon                          ico;
        image/x-jng                           jng;
        image/x-ms-bmp                        bmp;
        image/svg+xml                         svg svgz;
        image/webp                            webp;
        application/font-woff                 woff;
        application/java-archive              jar war ear;
        application/json                      json;
        application/mac-binhex40              hqx;
        application/msword                    doc;
        application/pdf                       pdf;
        application/postscript                ps eps ai;
        application/rtf                       rtf;
        application/vnd.apple.mpegurl         m3u8;
        application/vnd.ms-excel              xls;
        application/vnd.ms-powerpoint         ppt;
        application/vnd.wap.wmlc              wmlc;
        application/vnd.google-earth.kml+xml  kml;
        application/vnd.google-earth.kmz      kmz;
        application/x-7z-compressed           7z;
        application/x-cocoa                   cco;
        application/x-java-archive-diff       jardiff;
        application/x-java-jnlp-file          jnlp;
        application/x-makeself                run;
        application/x-perl                    pl pm;
        application/x-pilot                   prc pdb;
        application/x-rar-compressed          rar;
        application/x-redhat-package-manager  rpm;
        application/x-sea                     sea;
        application/x-shockwave-flash         swf;
        application/x-stuffit                 sit;
        application/x-tcl                     tcl tk;
        application/x-x509-ca-cert            der pem crt;
        application/x-xpinstall               xpi;
        application/xhtml+xml                 xhtml;
        application/xspf                      xspf;
        application/zip                       zip;
        application/octet-stream              bin exe dll;
        application/octet-stream              deb;
        application/octet-stream              dmg;
        application/octet-stream              iso img;
        application/octet-stream              msi msp msm;
        application/vnd.openxmlformats-officedocument.wordprocessingml.document    docx;
        application/vnd.openxmlformats-officedocument.spreadsheetml.sheet          xlsx;
        application/vnd.openxmlformats-officedocument.presentationml.presentation  pptx;
        audio/midi                            mid midi kar;
        audio/mpeg                            mp3;
        audio/ogg                             ogg;
        audio/x-m4a                           m4a;
        audio/x-realaudio                     ra;
        video/3gpp                            3gpp 3gp;
        video/mp2t                            ts;
        video/mp4                             mp4;
        video/mpeg                            mpeg mpg;
        video/quicktime                       mov;
        video/webm                            webm;
        video/x-flv                           flv;
        video/x-m4v                           m4v;
        video/x-mng                           mng;
        video/x-ms-asf                        asx asf;
        video/x-ms-wmv                        wmv;
        video/x-msvideo                       avi;
    }
    default_type application/octet-stream;
    
    server {
        listen 8080;
        server_tokens off;
        
        location / {
            proxy_pass http://portal:80/;
            proxy_set_header Host \$host;
            proxy_set_header X-Real-IP \$remote_addr;
            proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        }
        
        location /api/ {
            proxy_pass http://core:8080/api/;
            proxy_set_header Host \$host;
            proxy_set_header X-Real-IP \$remote_addr;
            proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        }
        
        location /service/ {
            proxy_pass http://core:8080/service/;
            proxy_set_header Host \$host;
            proxy_set_header X-Real-IP \$remote_addr;
            proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        }
        
        location /v2/ {
            proxy_pass http://core:8080/v2/;
            proxy_set_header Host \$host;
            proxy_set_header X-Real-IP \$remote_addr;
            proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        }
    }
}
EOF

# --- Generate Portal Config ---
cat > $INSTALL_PATH/common/config/portal/nginx.conf <<EOF
worker_processes auto;
pid /tmp/nginx.pid;
events {
    worker_connections 1024;
    use epoll;
    multi_accept on;
}
http {
    tcp_nodelay on;
    # Fix permission denied on temp paths by pointing them to /tmp
    client_body_temp_path /tmp/client_body_temp;
    proxy_temp_path       /tmp/proxy_temp;
    fastcgi_temp_path     /tmp/fastcgi_temp;
    uwsgi_temp_path       /tmp/uwsgi_temp;
    scgi_temp_path        /tmp/scgi_temp;
    
    # Increase body size for portal
    client_max_body_size 0;

    # include /etc/nginx/mime.types;
    types {
        text/html                             html htm shtml;
        text/css                              css;
        text/xml                              xml;
        image/gif                             gif;
        image/jpeg                            jpeg jpg;
        application/javascript                js;
        application/json                      json;
        application/font-woff                 woff;
        image/png                             png;
        image/svg+xml                         svg svgz;
    }
    default_type application/octet-stream;
    server {
        listen 80;
        server_tokens off;
        root /usr/share/nginx/html;
        index index.html index.htm;
        location / {
            try_files \$uri \$uri/ /index.html;
        }
    }
}
EOF

# --- Generate Log Config ---
cat > $INSTALL_PATH/common/config/log/logrotate.conf <<EOF
/var/log/docker/*.log {
    rotate 50
    size 200M
    missingok
    nocreate
    sharedscripts
    postrotate
        /usr/bin/killall -HUP rsyslogd
    endscript
}
EOF

cat > $INSTALL_PATH/common/config/log/rsyslog_docker.conf <<EOF
\$FileCreateMode 0644
template(name="DockerLogFileName" type="list") {
    constant(value="/var/log/docker/")
    property(name="syslogtag" securepath="replace" \
             regex.expression="docker/\\(.*\\)\\[" regex.submatch="1")
    constant(value="/current")
}
if \$programname =~ 'docker' then {
    action(type="omfile" dynaFile="DockerLogFileName")
    stop
}
EOF

# --- Generate Certificates (Self-Signed) ---
echo "Generating self-signed certificates..."
# 仅当私钥不存在时才生成，避免覆盖现有证书
# [UPDATE] 为了修复 Token 签名问题，我们需要确保证书和私钥是匹配的
# 如果是全新的安装 (INSTALL_PATH 被清理了)，这里会重新生成
# 如果是修复模式，我们可以选择强制覆盖 (如果之前的有问题)
# 但目前我们先保持“不存在则生成”的逻辑，用户可以通过清理目录来强制重新生成
if [ -f "$INSTALL_PATH/common/config/core/private_key.pem" ]; then
    echo "Certificates already exist. Checking validity..."
    # 简单的有效性检查，这里可以加
    # 目前跳过
else
    if ! command -v openssl &> /dev/null; then
        echo "Warning: openssl not found. Skipping certificate generation. Harbor might fail to start if keys are missing."
    else
        mkdir -p $INSTALL_PATH/common/config/core/certificates
        
        # Core Private Key (PKCS#1 for compatibility)
        # Note: OpenSSL 3.0+ generates PKCS#8 by default, which Harbor Core might not like.
        # Force convert to PKCS#1 (Traditional)
        openssl genrsa -out $INSTALL_PATH/common/config/core/private_key.pem 4096
        mv $INSTALL_PATH/common/config/core/private_key.pem $INSTALL_PATH/common/config/core/private_key.pem.raw
        openssl rsa -in $INSTALL_PATH/common/config/core/private_key.pem.raw -out $INSTALL_PATH/common/config/core/private_key.pem -traditional
        rm $INSTALL_PATH/common/config/core/private_key.pem.raw
        
        openssl rsa -in $INSTALL_PATH/common/config/core/private_key.pem -pubout -out $INSTALL_PATH/common/config/core/public_key.pem
        
        # Registry Root Cert (Signed by Core Private Key)
        # Use existing private key to generate CSR
        # IMPORTANT: Subject must include CN=harbor-registry (or whatever audience is expected?)
        # Actually audience is checked against the token claim, not the cert subject.
        # The cert subject matters for TLS, but here we are using it for Token Signing verification?
        # No, for Token Signing: Core uses Private Key to sign. Registry uses Public Key (Root Cert) to verify.
        # The Root Cert in registry/root.crt should contain the Public Key corresponding to Core's Private Key.
        
        openssl req -new -key $INSTALL_PATH/common/config/core/private_key.pem -out $INSTALL_PATH/common/config/registry/root.csr -subj "/C=CN/ST=BJ/L=BJ/O=Harbor/CN=harbor-registry"
        
        # Sign CSR with the SAME key (Self-signed)
        openssl x509 -req -days 3650 -in $INSTALL_PATH/common/config/registry/root.csr -signkey $INSTALL_PATH/common/config/core/private_key.pem -out $INSTALL_PATH/common/config/registry/root.crt
        
        # Secret Key
        if command -v python3 &> /dev/null; then
            python3 -c "import secrets; print(secrets.token_urlsafe(16), end='')" > $INSTALL_PATH/common/config/core/certificates/secretkey
        else
            # Fallback
            openssl rand -base64 16 | tr -d '\n' > $INSTALL_PATH/common/config/core/certificates/secretkey
        fi
    fi
fi

# --- Fix Permissions ---
echo "Fixing permissions..."
# Harbor DB (PostgreSQL) requires 999:999
# Harbor Redis requires 999:999
# Harbor Registry requires 10000:10000
# Harbor Core/JobService requires 10000:10000

# Create data directories if not exist
mkdir -p $INSTALL_PATH/database
mkdir -p $INSTALL_PATH/redis
mkdir -p $INSTALL_PATH/registry
mkdir -p $INSTALL_PATH/job_logs

# Force remove old data if it exists and looks corrupted (optional, be careful)
# But for permission denied errors on initdb, it's often better to start fresh if the dir is empty-ish
# or just force chown recursively

# Apply permissions
# We use numeric IDs to avoid dependency on host user existence
# IMPORTANT: Recursive chown to ensure all subdirectories (like pg15) are owned by the correct user
echo "Applying chown 999:999 to database..."
chown -R 999:999 $INSTALL_PATH/database
echo "Applying chown 999:999 to redis..."
chown -R 999:999 $INSTALL_PATH/redis
echo "Applying chown 10000:10000 to registry..."
chown -R 10000:10000 $INSTALL_PATH/registry
echo "Applying chown 10000:10000 to job_logs..."
chown -R 10000:10000 $INSTALL_PATH/job_logs

# Fix Nginx permissions
# Nginx needs to write to /etc/nginx/client_body_temp etc. if it's not configured to use /tmp
# Or we can just ensure the mapped config dir is writable
echo "Applying chown 10000:10000 to common/config/nginx..."
chown -R 10000:10000 $INSTALL_PATH/common/config/nginx
echo "Applying chown 10000:10000 to common/config/portal..."
chown -R 10000:10000 $INSTALL_PATH/common/config/portal

# Ensure config is readable
chmod -R 755 $INSTALL_PATH/common/config

echo "Harbor configuration generated successfully."
"""

INSTALLER_SCHEMA = {
  "type": "object",
  "properties": {
    "data_volume": {
      "type": "string",
      "title": "Install Path",
      "default": "/data/harbor",
      "description": "Harbor 配置安装路径"
    },
    "hostname": {
      "type": "string",
      "title": "Hostname",
      "default": "reg.mydomain.com",
      "description": "Harbor 主机名"
    }
  },
  "required": ["data_volume", "hostname"]
}

async def update_harbor_template():
    async with AsyncSessionLocal() as session:
        # 1. Update Template
        print("Found 1 existing Harbor templates. Updating...")
        stmt = select(AppTemplate).where(AppTemplate.name.ilike("%Harbor%"))
        result = await session.execute(stmt)
        templates = result.scalars().all()
        
        harbor_tpl_ids = []
        
        for tpl in templates:
            # Skip installer templates in this loop
            if "installer" in tpl.name.lower():
                continue
                
            if "harbor" in tpl.name.lower():
                tpl.deploy_template = HARBOR_TEMPLATE
                tpl.version = "v2.12.1"
                tpl.description = "Harbor v2.12.1 (Official Images). 支持自动安装配置 (Auto-Install)。"
                tpl.config_schema = CONFIG_SCHEMA
                tpl.default_config = {
                    "http_port": 5000,
                    "https_port": 443,
                    "harbor_admin_password": "Harbor12345",
                    "data_volume": "/data/harbor",
                    "external_url": "http://10.20.1.204:5000",
                    "pre_deploy_script": INSTALLER_SCRIPT
                }
                tpl.app_type = AppType.docker_compose
                harbor_tpl_ids.append(tpl.id)
        
        await session.commit()
        print(f"Harbor templates updated. IDs: {harbor_tpl_ids}")

        # 2. Update/Create Installer Template (Optional, keep for compatibility)
        print("Updating Harbor Installer template...")
        stmt = select(AppTemplate).where(AppTemplate.name == "Harbor Installer (Config Gen)")
        result = await session.execute(stmt)
        installer_tpl = result.scalar_one_or_none()
        
        if installer_tpl:
            installer_tpl.deploy_template = INSTALLER_SCRIPT
            installer_tpl.config_schema = INSTALLER_SCHEMA
            # Ensure it's shell_script
            installer_tpl.app_type = AppType.shell_script
        else:
            new_tpl = AppTemplate(
                name="Harbor Installer (Config Gen)",
                version="v2.12.1",
                description="Harbor 配置文件生成工具 (已集成到主应用，不再推荐单独使用)",
                app_type=AppType.shell_script,
                config_schema=INSTALLER_SCHEMA,
                default_config={
                    "data_volume": "/data/harbor",
                    "hostname": "reg.mydomain.com"
                },
                deploy_template=INSTALLER_SCRIPT,
                is_system=True
            )
            session.add(new_tpl)
        
        await session.commit()
        print("Harbor Installer template updated/created.")
        
        # 3. CRITICAL: Force Update Existing Instances
        # 用户可能已经创建了实例，实例中保存了旧的配置副本 (deploy_template, pre_deploy_script)
        # 我们必须刷新这些实例的配置，否则部署时仍会使用旧脚本。
        if harbor_tpl_ids:
            print(f"Checking existing instances for templates {harbor_tpl_ids}...")
            stmt_inst = select(AppInstance).where(AppInstance.template_id.in_(harbor_tpl_ids))
            res_inst = await session.execute(stmt_inst)
            instances = res_inst.scalars().all()
            
            for inst in instances:
                print(f"Updating instance {inst.id} ({inst.name})...")
                # 重新加载 config
                current_config = inst.config or {}
                
                # 强制更新 deploy_template
                # 注意：如果用户自定义了模板，这里会覆盖。但在修复 Bug 阶段，必须覆盖。
                current_config['deploy_template'] = HARBOR_TEMPLATE
                
                # 强制更新 pre_deploy_script
                current_config['pre_deploy_script'] = INSTALLER_SCRIPT
                
                # 确保默认配置项存在 (如果缺失)
                defaults = {
                    "http_port": 80,
                    "https_port": 443,
                    "harbor_admin_password": "Harbor12345",
                    "data_volume": "/data/harbor",
                    "external_url": "http://reg.mydomain.com"
                }
                for k, v in defaults.items():
                    if k not in current_config:
                        current_config[k] = v
                
                # 触发 SQLAlchemy 更新 (JSON 字段有时需要显式赋值)
                inst.config = dict(current_config)
                session.add(inst)
            
            await session.commit()
            print(f"Updated {len(instances)} existing instances.")

if __name__ == "__main__":
    import sys
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(update_harbor_template())
