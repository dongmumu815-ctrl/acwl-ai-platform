#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Snowflake ID 生成器

- 默认使用 2020-01-01 00:00:00 的自定义 epoch
- datacenter_id 和 worker_id 可通过环境变量配置：
  ACWL_DATACENTER_ID、ACWL_WORKER_ID

提供：
- generate_snowflake_int() -> int
- generate_snowflake_id() -> str（字符串形式，便于在 varchar 字段存储）
"""
from __future__ import annotations

import os
import time
import threading
from typing import Optional


class SnowflakeGenerator:
    """简化版雪花算法生成器，线程安全"""

    def __init__(
        self,
        datacenter_id: int = 1,
        worker_id: int = 1,
        epoch_ms: int = 1577836800000,  # 2020-01-01 00:00:00 UTC
    ) -> None:
        # 位数分配
        self.worker_id_bits = 5
        self.datacenter_id_bits = 5
        self.sequence_bits = 12

        # 最大值
        self.max_worker_id = (1 << self.worker_id_bits) - 1
        self.max_datacenter_id = (1 << self.datacenter_id_bits) - 1

        # 位移
        self.worker_id_shift = self.sequence_bits
        self.datacenter_id_shift = self.sequence_bits + self.worker_id_bits
        self.timestamp_left_shift = (
            self.sequence_bits + self.worker_id_bits + self.datacenter_id_bits
        )
        self.sequence_mask = (1 << self.sequence_bits) - 1

        # 参数
        if not (0 <= worker_id <= self.max_worker_id):
            raise ValueError(f"worker_id 超出范围 [0, {self.max_worker_id}]，当前: {worker_id}")
        if not (0 <= datacenter_id <= self.max_datacenter_id):
            raise ValueError(
                f"datacenter_id 超出范围 [0, {self.max_datacenter_id}]，当前: {datacenter_id}"
            )

        self.datacenter_id = datacenter_id
        self.worker_id = worker_id
        self.epoch_ms = epoch_ms

        # 状态
        self.sequence = 0
        self.last_timestamp = -1
        self._lock = threading.Lock()

    def _timestamp(self) -> int:
        return int(time.time() * 1000)

    def _wait_next_millis(self, last_ts: int) -> int:
        ts = self._timestamp()
        while ts <= last_ts:
            time.sleep(0.0001)  # 100 微秒
            ts = self._timestamp()
        return ts

    def get_id(self) -> int:
        """生成一个新的雪花 ID（整数）。"""
        with self._lock:
            ts = self._timestamp()

            # 时钟回拨保护
            if ts < self.last_timestamp:
                # 等待到 last_timestamp 之后
                ts = self._wait_next_millis(self.last_timestamp)

            if ts == self.last_timestamp:
                # 同毫秒内自增序列
                self.sequence = (self.sequence + 1) & self.sequence_mask
                if self.sequence == 0:
                    # 序列溢出，等待下一毫秒
                    ts = self._wait_next_millis(self.last_timestamp)
            else:
                # 新毫秒重置序列
                self.sequence = 0

            self.last_timestamp = ts

            # 组合各部分成为 64 位 ID
            diff = ts - self.epoch_ms
            snowflake_id = (
                (diff << self.timestamp_left_shift)
                | (self.datacenter_id << self.datacenter_id_shift)
                | (self.worker_id << self.worker_id_shift)
                | self.sequence
            )
            return snowflake_id


# 初始化默认生成器（支持环境变量覆盖）
_default_datacenter_id = int(os.getenv("ACWL_DATACENTER_ID", "1"))
_default_worker_id = int(os.getenv("ACWL_WORKER_ID", "1"))
_default_epoch_ms = int(os.getenv("ACWL_EPOCH_MS", "1577836800000"))
_generator = SnowflakeGenerator(
    datacenter_id=_default_datacenter_id,
    worker_id=_default_worker_id,
    epoch_ms=_default_epoch_ms,
)


def generate_snowflake_int() -> int:
    """返回整数形式雪花 ID。"""
    return _generator.get_id()


def generate_snowflake_id() -> str:
    """返回字符串形式雪花 ID（便于 varchar 存储）。"""
    return str(generate_snowflake_int())