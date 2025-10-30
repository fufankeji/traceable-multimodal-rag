import logging
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler
from datetime import datetime

# 创建logs目录
LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)

# 日志格式
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

def setup_logger(name: str, level: int = logging.INFO) -> logging.Logger:
    """
    配置日志记录器
    
    Args:
        name: 日志记录器名称
        level: 日志级别
    
    Returns:
        配置好的日志记录器
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # 避免重复添加handler
    if logger.handlers:
        return logger
    
    # 控制台输出
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_formatter = logging.Formatter(LOG_FORMAT, DATE_FORMAT)
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)
    
    # 文件输出 - 所有日志
    file_handler = RotatingFileHandler(
        LOG_DIR / f"{name}.log",
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5,
        encoding='utf-8'
    )
    file_handler.setLevel(level)
    file_formatter = logging.Formatter(LOG_FORMAT, DATE_FORMAT)
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)
    
    # 错误日志单独记录
    error_handler = RotatingFileHandler(
        LOG_DIR / f"{name}_error.log",
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5,
        encoding='utf-8'
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(file_formatter)
    logger.addHandler(error_handler)
    
    return logger

# 创建默认日志记录器
app_logger = setup_logger("rag_app")
sql_logger = setup_logger("rag_sql")
milvus_logger = setup_logger("rag_milvus")
api_logger = setup_logger("rag_api")

def log_request(endpoint: str, method: str, status_code: int, duration: float):
    """记录API请求日志"""
    api_logger.info(
        f"API请求 - {method} {endpoint} - 状态码: {status_code} - 耗时: {duration:.3f}s"
    )

def log_error(error: Exception, context: str = ""):
    """记录错误日志"""
    if context:
        app_logger.error(f"{context} - {type(error).__name__}: {str(error)}", exc_info=True)
    else:
        app_logger.error(f"{type(error).__name__}: {str(error)}", exc_info=True)

def log_upload(filename: str, chunk_count: int, success: bool, duration: float):
    """记录文件上传日志"""
    if success:
        app_logger.info(
            f"文件上传成功 - 文件: {filename}, Chunks: {chunk_count}, 耗时: {duration:.3f}s"
        )
    else:
        app_logger.error(f"文件上传失败 - 文件: {filename}")

def log_search(query: str, kb_name: str, result_count: int, duration: float):
    """记录检索日志"""
    app_logger.info(
        f"检索 - 知识库: {kb_name}, 查询: {query[:50]}..., "
        f"结果数: {result_count}, 耗时: {duration:.3f}s"
    )