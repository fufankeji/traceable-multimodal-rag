"""
简单的文件日志记录器
"""
import sys
from datetime import datetime
from pathlib import Path

class SimpleLogger:
    def __init__(self, log_file="logs/api_requests.log"):
        self.log_dir = Path("logs")
        self.log_dir.mkdir(exist_ok=True)
        self.log_file = self.log_dir / f"api_{datetime.now().strftime('%Y%m%d')}.log"
        
    def log(self, message):
        """同时输出到控制台和文件"""
        timestamp = datetime.now().strftime('%H:%M:%S')
        log_msg = f"[{timestamp}] {message}"
        
        # 输出到控制台
        print(log_msg)
        sys.stdout.flush()
        
        # 写入文件
        try:
            with open(self.log_file, 'a', encoding='utf-8') as f:
                f.write(log_msg + '\n')
        except:
            pass

# 全局logger实例
api_logger = SimpleLogger()

def log_request(message):
    """记录API请求"""
    api_logger.log(message)
