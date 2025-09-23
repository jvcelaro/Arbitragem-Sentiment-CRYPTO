import time
from functools import wraps
import logging
import asyncio
from typing import Any, Callable, Dict, Optional

logger = logging.getLogger(__name__)

def performance_monitor(func: Callable) -> Callable:
    
    @wraps(func)
    def sync_wrapper(*args, **kwargs):
        start_time = time.time()
        function_name = func.__name__
        
        logger.debug(f"[PERFORMANCE] Iniciando execução: {function_name}")
        
        try:
            result = func(*args, **kwargs)
            duration = time.time() - start_time
            
            logger.info(f"[PERFORMANCE] {function_name} executada em {duration:.4f}s")
            
            _save_performance_metric(function_name, duration, success=True)
            
            return result
            
        except Exception as e:
            duration = time.time() - start_time
            logger.error(f"[PERFORMANCE] {function_name} falhou após {duration:.4f}s: {e}")
            
            _save_performance_metric(function_name, duration, success=False, error=str(e))
            raise
    
    @wraps(func)
    async def async_wrapper(*args, **kwargs):
        start_time = time.time()
        function_name = func.__name__
        
        logger.debug(f"[PERFORMANCE] Iniciando execução async: {function_name}")
        
        try:
            result = await func(*args, **kwargs)
            duration = time.time() - start_time
            
            logger.info(f"[PERFORMANCE] {function_name} (async) executada em {duration:.4f}s")
            
            _save_performance_metric(function_name, duration, success=True, is_async=True)
            
            return result
            
        except Exception as e:
            duration = time.time() - start_time
            logger.error(f"[PERFORMANCE] {function_name} (async) falhou após {duration:.4f}s: {e}")
            
            _save_performance_metric(function_name, duration, success=False, error=str(e), is_async=True)
            raise
    
    if asyncio.iscoroutinefunction(func):
        return async_wrapper
    else:
        return sync_wrapper

_performance_metrics: Dict[str, list] = {}

def _save_performance_metric(function_name: str, duration: float, success: bool, 
                           error: Optional[str] = None, is_async: bool = False):
    if function_name not in _performance_metrics:
        _performance_metrics[function_name] = []
    
    metric = {
        'timestamp': time.time(),
        'duration': duration,
        'success': success,
        'is_async': is_async,
        'error': error
    }
    
    _performance_metrics[function_name].append(metric)
    
    if len(_performance_metrics[function_name]) > 100:
        _performance_metrics[function_name] = _performance_metrics[function_name][-100:]

def get_performance_stats(function_name: Optional[str] = None) -> Dict[str, Any]:
    if function_name:
        return _performance_metrics.get(function_name, [])
    return _performance_metrics.copy()