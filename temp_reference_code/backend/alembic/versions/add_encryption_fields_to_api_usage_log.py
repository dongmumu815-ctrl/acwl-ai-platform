"""Add encryption fields to api_usage_log

Revision ID: add_encryption_fields
Revises: 
Create Date: 2024-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = 'add_encryption_fields'
down_revision = None  # 请根据实际情况修改为上一个版本的revision ID
branch_labels = None
depends_on = None


def upgrade():
    """Add encryption related fields to api_usage_logs table"""
    # 添加加密相关字段
    op.add_column('api_usage_logs', sa.Column('is_encrypted', sa.Boolean(), nullable=False, default=False, comment='是否为加密请求'))
    op.add_column('api_usage_logs', sa.Column('timestamp', sa.String(50), nullable=True, comment='请求时间戳（加密请求）'))
    op.add_column('api_usage_logs', sa.Column('nonce', sa.String(100), nullable=True, comment='随机数（加密请求）'))
    op.add_column('api_usage_logs', sa.Column('encrypted_data', sa.Text(), nullable=True, comment='加密数据（加密请求）'))
    op.add_column('api_usage_logs', sa.Column('iv', sa.String(100), nullable=True, comment='初始化向量（加密请求）'))
    op.add_column('api_usage_logs', sa.Column('signature', sa.String(200), nullable=True, comment='数据签名（加密请求）'))
    op.add_column('api_usage_logs', sa.Column('needread', sa.Boolean(), nullable=True, comment='是否需要读取（加密请求）'))
    
    # 添加索引
    op.create_index('idx_api_usage_logs_is_encrypted', 'api_usage_logs', ['is_encrypted'])
    op.create_index('idx_api_usage_logs_timestamp', 'api_usage_logs', ['timestamp'])
    op.create_index('idx_api_usage_logs_nonce', 'api_usage_logs', ['nonce'])


def downgrade():
    """Remove encryption related fields from api_usage_logs table"""
    # 删除索引
    op.drop_index('idx_api_usage_logs_nonce', 'api_usage_logs')
    op.drop_index('idx_api_usage_logs_timestamp', 'api_usage_logs')
    op.drop_index('idx_api_usage_logs_is_encrypted', 'api_usage_logs')
    
    # 删除字段
    op.drop_column('api_usage_logs', 'needread')
    op.drop_column('api_usage_logs', 'signature')
    op.drop_column('api_usage_logs', 'iv')
    op.drop_column('api_usage_logs', 'encrypted_data')
    op.drop_column('api_usage_logs', 'nonce')
    op.drop_column('api_usage_logs', 'timestamp')
    op.drop_column('api_usage_logs', 'is_encrypted')