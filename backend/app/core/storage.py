"""对象存储客户端——骨架模式下为零依赖 mock。

真实实现使用 boto3 连接 MinIO/S3。骨架阶段不连接任何对象存储：``MockStorage``
在每次"保存/取回"时记录它实际读到的 S3 凭据，证明凭据确实被消费，但不发起网络请求。

接回真实存储时，恢复 boto3 客户端装配即可，``StorageClient`` 的方法签名保持不变。
"""

from __future__ import annotations

import hashlib

from app.core.config import settings
from app.core.credentials import log_credential_use
from app.core.logging import get_logger

logger = get_logger("storage")


class StorageClient:
    """对象存储的薄封装——骨架模式只记录日志，不落对象存储。"""

    def __init__(self, bucket: str | None = None) -> None:
        self.bucket = bucket or settings.s3_bucket
        log_credential_use(
            "s3_endpoint_url",
            "s3_access_key",
            "s3_secret_key",
            "s3_bucket",
            "s3_region",
            purpose="init object storage client (mock)",
        )

    def put_object(self, key: str, data: bytes, content_type: str) -> str:
        log_credential_use("s3_access_key", "s3_secret_key", purpose=f"put_object {key} (mock)")
        logger.info("storage.put_object", bucket=self.bucket, key=key, bytes=len(data))
        return key

    def presigned_url(self, key: str, expires: int = 3600) -> str:
        log_credential_use("s3_access_key", "s3_secret_key", purpose=f"presign {key} (mock)")
        return f"mock://{self.bucket}/{key}?expires={expires}"

    @staticmethod
    def content_hash(data: bytes) -> str:
        return hashlib.sha256(data).hexdigest()


def get_storage() -> StorageClient:
    return StorageClient()
