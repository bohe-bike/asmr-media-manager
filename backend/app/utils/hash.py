import hashlib


def compute_file_hash(file_path: str, chunk_size: int = 65536) -> str:
    """计算文件 SHA256 哈希值，使用分块读取支持大文件"""
    sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        while True:
            data = f.read(chunk_size)
            if not data:
                break
            sha256.update(data)
    return sha256.hexdigest()
