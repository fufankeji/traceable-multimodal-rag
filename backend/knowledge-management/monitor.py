"""
性能监控和统计工具
"""
from typing import Dict, List
from datetime import datetime, timedelta
from collections import defaultdict
import time
from functools import wraps

class PerformanceMonitor:
    """性能监控器"""
    
    def __init__(self):
        self.stats = defaultdict(list)
        self.error_count = defaultdict(int)
        self.start_time = datetime.now()
    
    def record_request(self, endpoint: str, duration: float, success: bool):
        """记录请求"""
        self.stats[endpoint].append({
            "duration": duration,
            "success": success,
            "timestamp": datetime.now()
        })
        
        if not success:
            self.error_count[endpoint] += 1
    
    def get_stats(self, endpoint: str = None) -> Dict:
        """获取统计信息"""
        if endpoint:
            return self._calculate_endpoint_stats(endpoint)
        
        # 返回所有端点的统计
        return {
            ep: self._calculate_endpoint_stats(ep)
            for ep in self.stats.keys()
        }
    
    def _calculate_endpoint_stats(self, endpoint: str) -> Dict:
        """计算单个端点的统计信息"""
        records = self.stats[endpoint]
        
        if not records:
            return {
                "total_requests": 0,
                "success_rate": 0,
                "avg_duration": 0,
                "min_duration": 0,
                "max_duration": 0
            }
        
        durations = [r["duration"] for r in records]
        successes = sum(1 for r in records if r["success"])
        
        return {
            "total_requests": len(records),
            "success_rate": successes / len(records) if records else 0,
            "avg_duration": sum(durations) / len(durations),
            "min_duration": min(durations),
            "max_duration": max(durations),
            "error_count": self.error_count[endpoint]
        }
    
    def get_recent_errors(self, minutes: int = 60) -> List[Dict]:
        """获取最近的错误"""
        cutoff_time = datetime.now() - timedelta(minutes=minutes)
        errors = []
        
        for endpoint, records in self.stats.items():
            for record in records:
                if not record["success"] and record["timestamp"] > cutoff_time:
                    errors.append({
                        "endpoint": endpoint,
                        "timestamp": record["timestamp"],
                        "duration": record["duration"]
                    })
        
        return sorted(errors, key=lambda x: x["timestamp"], reverse=True)
    
    def get_system_info(self) -> Dict:
        """获取系统信息"""
        total_requests = sum(len(records) for records in self.stats.values())
        total_errors = sum(self.error_count.values())
        uptime = datetime.now() - self.start_time
        
        return {
            "uptime_seconds": uptime.total_seconds(),
            "total_requests": total_requests,
            "total_errors": total_errors,
            "error_rate": total_errors / total_requests if total_requests > 0 else 0,
            "endpoints": list(self.stats.keys())
        }

# 全局监控器实例
monitor = PerformanceMonitor()

def monitor_performance(endpoint_name: str = None):
    """性能监控装饰器"""
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            name = endpoint_name or func.__name__
            start_time = time.time()
            success = True
            
            try:
                result = await func(*args, **kwargs)
                return result
            except Exception as e:
                success = False
                raise
            finally:
                duration = time.time() - start_time
                monitor.record_request(name, duration, success)
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            name = endpoint_name or func.__name__
            start_time = time.time()
            success = True
            
            try:
                result = func(*args, **kwargs)
                return result
            except Exception as e:
                success = False
                raise
            finally:
                duration = time.time() - start_time
                monitor.record_request(name, duration, success)
        
        # 根据函数类型返回对应的包装器
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator

def get_monitor_report() -> Dict:
    """生成监控报告"""
    stats = monitor.get_stats()
    system_info = monitor.get_system_info()
    recent_errors = monitor.get_recent_errors(60)
    
    # 计算最慢的端点
    slowest_endpoints = sorted(
        [
            {"endpoint": ep, "avg_duration": stat["avg_duration"]}
            for ep, stat in stats.items()
        ],
        key=lambda x: x["avg_duration"],
        reverse=True
    )[:5]
    
    # 计算错误最多的端点
    most_errors = sorted(
        [
            {"endpoint": ep, "error_count": stat["error_count"]}
            for ep, stat in stats.items()
        ],
        key=lambda x: x["error_count"],
        reverse=True
    )[:5]
    
    return {
        "system_info": system_info,
        "endpoint_stats": stats,
        "slowest_endpoints": slowest_endpoints,
        "most_errors": most_errors,
        "recent_errors": recent_errors[:10]
    }