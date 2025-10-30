-- 迁移：创建资源包Excel文件历史表
-- 目的：记录每次生成的Excel文件，支持历史下载

CREATE TABLE IF NOT EXISTS resource_package_files (
  id INT AUTO_INCREMENT PRIMARY KEY,
  package_id INT NOT NULL COMMENT '资源包ID',
  filename VARCHAR(255) NOT NULL COMMENT '文件名',
  object_path VARCHAR(500) NOT NULL COMMENT 'MinIO对象路径',
  generated_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '生成时间',
  CONSTRAINT fk_rpf_package
    FOREIGN KEY (package_id)
    REFERENCES resource_packages(id)
    ON DELETE CASCADE
) COMMENT='资源包Excel文件历史';

-- 索引优化
CREATE INDEX idx_rpf_package ON resource_package_files(package_id);
CREATE INDEX idx_rpf_generated_at ON resource_package_files(generated_at);