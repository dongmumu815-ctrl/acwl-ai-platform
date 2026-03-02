
import paramiko

HOST = "10.20.1.204"
USER = "ubuntu"
PASS = "cepiec1qaz@WSXaczt8912059Nxtektppyoud"

# Template from update_harbor_template_v2.py
# Replaced {{ data_volume }} with /data/harbor
# Replaced {{ http_port }} with 80
# Replaced {{ https_port }} with 443
DOCKER_COMPOSE_CONTENT = """version: '2.3'
services:
  log:
    image: goharbor/harbor-log:v2.12.1
    container_name: harbor-log
    restart: always
    volumes:
      - /data/harbor/log/:/var/log/docker/:z
      - /data/harbor/common/config/log/logrotate.conf:/etc/logrotate.d/logrotate.conf
      - /data/harbor/common/config/log/rsyslog_docker.conf:/etc/rsyslog.d/rsyslog_docker.conf
    ports:
      - 127.0.0.1:1514:10514
    networks:
      - harbor
  registry:
    image: goharbor/registry-photon:v2.12.1
    container_name: registry
    restart: always
    volumes:
      - /data/harbor/registry:/storage:z
      - /data/harbor/common/config/registry/:/etc/registry/:z
      - /data/harbor/common/config/registry/root.crt:/etc/registry/root.crt
      - /data/harbor/common/config/shared/trust-certificates:/harbor_cust_cert
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
      - /data/harbor/common/config/registryctl/env
    restart: always
    volumes:
      - /data/harbor/registry:/storage:z
      - /data/harbor/common/config/registry/:/etc/registry/:z
      - /data/harbor/common/config/registry/root.crt:/etc/registry/root.crt
      - /data/harbor/common/config/registryctl/config.yml:/etc/registryctl/config.yml
      - /data/harbor/common/config/shared/trust-certificates:/harbor_cust_cert
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
      - /data/harbor/database:/var/lib/postgresql/data:z
    networks:
      harbor:
    env_file:
      - /data/harbor/common/config/db/env
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
      - /data/harbor/common/config/core/env
    restart: always
    volumes:
      - /data/harbor/ca_download/:/etc/core/ca/:z
      - /data/harbor/data/:/data/:z
      - /data/harbor/common/config/core/certificates/:/etc/core/certificates/:z
      - /data/harbor/common/config/core/app.conf:/etc/core/app.conf
      - /data/harbor/common/config/core/private_key.pem:/etc/core/private_key.pem
      - /data/harbor/common/config/core/certificates/secretkey:/etc/core/key
      - /data/harbor/common/config/shared/trust-certificates:/harbor_cust_cert
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
      - /data/harbor/common/config/portal/nginx.conf:/etc/nginx/nginx.conf
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
      - /data/harbor/common/config/jobservice/env
    restart: always
    volumes:
      - /data/harbor/job_logs:/var/log/jobs:z
      - /data/harbor/common/config/jobservice/config.yml:/etc/jobservice/config.yml
      - /data/harbor/common/config/shared/trust-certificates:/harbor_cust_cert
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
      - /data/harbor/redis:/var/lib/redis
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
      - /data/harbor/common/config/nginx:/etc/nginx:z
      - /data/harbor/common/config/shared/trust-certificates:/harbor_cust_cert
    networks:
      - harbor
    ports:
      - 80:8080
      - 443:8443
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

def main():
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(HOST, username=USER, password=PASS)
        
        print("Restoring docker-compose.yml...")
        
        # Write to temporary file then move with sudo
        sftp = ssh.open_sftp()
        with sftp.file("/tmp/docker-compose.yml", "w") as f:
            f.write(DOCKER_COMPOSE_CONTENT)
        sftp.close()
        
        # Move it to /data/harbor
        cmd = f"echo '{PASS}' | sudo -S mv /tmp/docker-compose.yml /data/harbor/docker-compose.yml"
        stdin, stdout, stderr = ssh.exec_command(cmd)
        print(stdout.read().decode())
        print(stderr.read().decode())
        
        print("docker-compose.yml restored.")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        ssh.close()

if __name__ == "__main__":
    main()
