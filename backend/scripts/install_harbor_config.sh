#!/bin/bash
# Harbor 初始化安装脚本
# 用途：生成 Harbor 所需的配置文件 (common/config)
# 使用方法：sudo ./install_harbor_config.sh <install_path> <hostname>

INSTALL_PATH=${1:-/data/harbor}
HOSTNAME=${2:-reg.mydomain.com}

echo "Installing Harbor config to $INSTALL_PATH with hostname $HOSTNAME..."

# 检查 docker compose
if ! command -v docker &> /dev/null; then
    echo "Error: docker is not installed."
    exit 1
fi

# 下载 Harbor 安装包 (离线包或在线安装包) 以提取配置文件
# 为了简化，这里我们直接下载 harbor-offline-installer
# 注意：这里假设网络可以访问 github
HARBOR_VERSION="v2.12.1"
TEMP_DIR="/tmp/harbor_install"
mkdir -p $TEMP_DIR

if [ ! -f "$TEMP_DIR/harbor.tgz" ]; then
    echo "Downloading Harbor installer..."
    # 使用加速地址或官方地址
    curl -L "https://github.com/goharbor/harbor/releases/download/${HARBOR_VERSION}/harbor-offline-installer-${HARBOR_VERSION}.tgz" -o "$TEMP_DIR/harbor.tgz"
fi

echo "Extracting installer..."
tar xzf "$TEMP_DIR/harbor.tgz" -C $TEMP_DIR

# 准备目录
mkdir -p $INSTALL_PATH

# 复制 harbor.yml.tmpl 并配置
cp $TEMP_DIR/harbor/harbor.yml.tmpl $TEMP_DIR/harbor/harbor.yml
sed -i "s/hostname: reg.mydomain.com/hostname: $HOSTNAME/g" $TEMP_DIR/harbor/harbor.yml
# 禁用 https (如果需要，后续可手动开启)
# sed -i 's/https:/# https:/g' $TEMP_DIR/harbor/harbor.yml
# sed -i 's/port: 443/# port: 443/g' $TEMP_DIR/harbor/harbor.yml
# sed -i 's/certificate:/# certificate:/g' $TEMP_DIR/harbor/harbor.yml
# sed -i 's/private_key:/# private_key:/g' $TEMP_DIR/harbor/harbor.yml

# 运行 prepare 脚本生成 common/config
echo "Generating configuration..."
cd $TEMP_DIR/harbor
# 需要 sudo 权限运行 prepare
./prepare

# 将生成的 common 目录复制到安装路径
echo "Copying config to $INSTALL_PATH..."
cp -r common $INSTALL_PATH/

# 清理
rm -rf $TEMP_DIR

echo "Harbor configuration installed successfully at $INSTALL_PATH/common"
echo "You can now deploy Harbor using the Application Market."
