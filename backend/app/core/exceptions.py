from fastapi import HTTPException


class AppException(HTTPException):
    def __init__(self, status_code: int = 500, detail: str = "服务器内部错误"):
        super().__init__(status_code=status_code, detail=detail)


class NotFoundException(AppException):
    def __init__(self, detail: str = "资源未找到"):
        super().__init__(status_code=404, detail=detail)


class ValidationException(AppException):
    def __init__(self, detail: str = "参数验证失败"):
        super().__init__(status_code=400, detail=detail)


class ScanException(AppException):
    def __init__(self, detail: str = "扫描错误"):
        super().__init__(status_code=500, detail=detail)


class MetadataException(AppException):
    def __init__(self, detail: str = "元数据处理错误"):
        super().__init__(status_code=500, detail=detail)


class RenameException(AppException):
    def __init__(self, detail: str = "重命名操作错误"):
        super().__init__(status_code=400, detail=detail)


class AIException(AppException):
    def __init__(self, detail: str = "AI 服务不可用"):
        super().__init__(status_code=503, detail=detail)
