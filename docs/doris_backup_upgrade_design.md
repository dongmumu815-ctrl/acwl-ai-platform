# Doris 集群备份与升级方案设计

## 1. 备份方案 (Backup Strategy)

### 1.1 背景
Doris 支持两种主要的备份方式：
1.  **物理备份 (Snapshot Backup)**: 使用 `BACKUP` 命令将数据快照上传到远端仓库 (S3/HDFS)。这是官方推荐的全量/增量备份方式。
2.  **逻辑备份 (Logical Backup)**: 使用 `mysqldump` 导出表结构 (Schema) 或 `EXPORT` 导出数据 (CSV/Parquet)。

### 1.2 现状与限制
当前部署架构为多节点 Docker 容器部署 (3 FE + 5 BE)。
*   **本地备份限制**: Doris 的 `LOCAL` 仓库类型仅适用于单机测试。在集群模式下，快照数据分散在各个 BE 节点的本地磁盘上，无法直接聚合成一个可恢复的备份包，除非所有节点挂载了同一个共享存储 (NFS/Ceph)。
*   **推荐方案**: 使用 S3 兼容的对象存储 (如 MinIO, AWS S3, Aliyun OSS) 作为备份仓库。

### 1.3 实施计划

#### 第一阶段：基础设施准备 (已完成)
*   **Volume 挂载**: 已更新 Doris 部署模板，为所有 FE/BE 容器添加了 `/backup` 卷映射：
    *   宿主机路径: `{{ data_root_path }}/backup` (默认 `/data/doris/backup`)
    *   容器内路径: `/opt/apache-doris/backup`
    *   *作用*: 允许用户挂载 NFS 到宿主机的 `/data/doris/backup` 实现共享存储备份，或用于导出 Schema 文件。

#### 第二阶段：功能实现
1.  **Schema 备份 (轻量级)**
    *   **功能**: 导出所有数据库和表的建表语句。
    *   **实现**: 后端调用 `mysqldump --no-data`。
    *   **存储**: 保存到 `/data/doris/backup/schema_{date}.sql`。

2.  **快照备份 (完整数据)**
    *   **前置条件**: 用户需配置 S3/MinIO 信息。
    *   **API**:
        *   `POST /api/doris/repository`: 创建/更新仓库配置 (`CREATE REPOSITORY ... ON LOCATION ...`).
        *   `POST /api/doris/backup`: 触发备份 (`BACKUP SNAPSHOT ...`).
        *   `GET /api/doris/backup`: 查询备份状态 (`SHOW BACKUP`).

## 2. 升级方案 (Rolling Upgrade Strategy)

### 2.1 核心原则
Doris 支持滚动升级 (Rolling Upgrade)，允许在不中断服务的情况下逐个升级节点。
*   **顺序**: BE -> FE (Follower/Observer) -> FE (Master)。
*   **版本跨度**: 建议小版本平滑升级 (如 4.0.3 -> 4.0.4)。大版本升级需参考官方 Release Notes。

### 2.2 自动化升级流程设计

后端将实现 `upgrade_doris_cluster(instance_id, target_version)` 方法，执行以下步骤：

1.  **健康检查 (Pre-check)**
    *   检查所有节点状态必须为 `Alive`。
    *   检查是否有正在进行的 Schema Change 或 Rebalance 任务。

2.  **BE 节点升级 (逐个执行)**
    *   对于每个 BE 节点：
        1.  **Stop**: `docker stop <be_container>`
        2.  **Update Config**: 更新 `docker-compose.yml` 中的镜像版本。
        3.  **Start**: `docker up -d <be_service>`
        4.  **Verify**: 轮询 `SHOW BACKENDS` 直到该节点状态变为 `Alive` 且 `Version` 匹配目标版本。
        5.  **Next**: 继续下一个 BE。

3.  **FE 节点升级**
    *   **识别角色**: 通过 `SHOW FRONTENDS` 区分 Master 和 Follower/Observer。
    *   **升级 Followers/Observers**: 逐个重启并验证。
    *   **升级 Master**:
        *   最后重启 Master。
        *   重启期间会有短暂的元数据不可用 (选举过程)。
        *   验证新 Master 选举成功且服务恢复。

### 2.3 回滚策略
*   如果升级过程中某个节点启动失败，自动化流程暂停。
*   允许用户选择“回滚”，即使用旧版本镜像重新启动该节点。

## 3. 下一步建议
1.  **配置 S3/MinIO**: 建议在环境中部署 MinIO 或配置云存储，以便实现真正的生产级数据备份。
2.  **测试升级**: 在测试环境验证 4.0.3 -> 4.0.x 的滚动升级流程。
