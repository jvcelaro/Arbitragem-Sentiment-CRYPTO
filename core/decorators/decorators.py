import time
from functools import wraps
import logging
import asyncio
from typing import Any, Callable, Dict, Optional, Tuple, Union, Type

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

    with open(r"D:\Projetos\Arbitragem e Sentiment CRYPT\Project\storage\performance_.txt", "w", encoding="utf-8") as file:
        file.write(_performance_metrics)
        file.close()

def get_performance_stats(function_name: Optional[str] = None) -> Dict[str, Any]:
    if function_name:
        return _performance_metrics.get(function_name, [])
    return _performance_metrics.copy()


def retry_on_failure(max_attempts: int = 3, 
                    delay: float = 1.0,
                    backoff_factor: float = 2.0,
                    jitter: bool = True,
                    exceptions: Tuple[Type[Exception], ...] = (Exception,)):
    """
    Decorator que implementa retry automático com backoff exponencial.
    
    Args:
        max_attempts: Número máximo de tentativas (padrão: 3)
        delay: Delay inicial entre tentativas em segundos (padrão: 1.0)
        backoff_factor: Fator multiplicador do delay a cada tentativa (padrão: 2.0)
        jitter: Se True, adiciona variação aleatória ao delay (padrão: True)
        exceptions: Tupla de exceções que devem disparar retry (padrão: Exception)
    
    Features:
    - Backoff exponencial com jitter opcional
    - Configurável para exceções específicas
    - Logs detalhados de cada tentativa
    - Suporte para funções sync e async
    """
    
    def decorator(func: Callable) -> Callable:
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            current_delay = delay
            last_exception = None
            
            for attempt in range(1, max_attempts + 1):
                try:
                    if attempt == 1:
                        logger.debug(f"[RETRY] {func.__name__} - Primeira tentativa")
                    else:
                        logger.info(f"[RETRY] {func.__name__} - Tentativa {attempt}/{max_attempts}")
                    
                    result = func(*args, **kwargs)
                    
                    if attempt > 1:
                        logger.info(f"[RETRY SUCCESS] {func.__name__} sucedeu na tentativa {attempt}")
                    
                    return result
                    
                except exceptions as e:
                    last_exception = e
                    logger.warning(
                        f"[RETRY FAIL] {func.__name__} falhou na tentativa {attempt}/{max_attempts}: "
                        f"{type(e).__name__}: {str(e)[:100]}"
                    )
                    
                    # Se é a última tentativa, não faz delay
                    if attempt == max_attempts:
                        logger.error(f"[RETRY EXHAUSTED] {func.__name__} falhou após {max_attempts} tentativas")
                        break
                    
                    # Calcula delay com backoff e jitter
                    actual_delay = _calculate_delay(current_delay, jitter)
                    logger.debug(f"[RETRY DELAY] Aguardando {actual_delay:.2f}s antes da próxima tentativa")
                    
                    time.sleep(actual_delay)
                    current_delay *= backoff_factor
                
                except Exception as e:
                    # Exceção não está na lista - falha imediatamente
                    logger.error(
                        f"[RETRY ABORT] {func.__name__} falhou com exceção não-retryable: "
                        f"{type(e).__name__}: {str(e)}"
                    )
                    raise
            
            # Se chegou aqui, todas as tentativas falharam
            raise last_exception
        
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            current_delay = delay
            last_exception = None
            
            for attempt in range(1, max_attempts + 1):
                try:
                    if attempt == 1:
                        logger.debug(f"[RETRY] {func.__name__} (async) - Primeira tentativa")
                    else:
                        logger.info(f"[RETRY] {func.__name__} (async) - Tentativa {attempt}/{max_attempts}")
                    
                    result = await func(*args, **kwargs)
                    
                    if attempt > 1:
                        logger.info(f"[RETRY SUCCESS] {func.__name__} (async) sucedeu na tentativa {attempt}")
                    
                    return result
                    
                except exceptions as e:
                    last_exception = e
                    logger.warning(
                        f"[RETRY FAIL] {func.__name__} (async) falhou na tentativa {attempt}/{max_attempts}: "
                        f"{type(e).__name__}: {str(e)[:100]}"
                    )
                    
                    if attempt == max_attempts:
                        logger.error(f"[RETRY EXHAUSTED] {func.__name__} (async) falhou após {max_attempts} tentativas")
                        break
                    
                    actual_delay = _calculate_delay(current_delay, jitter)
                    logger.debug(f"[RETRY DELAY] Aguardando {actual_delay:.2f}s antes da próxima tentativa (async)")
                    
                    await asyncio.sleep(actual_delay)
                    current_delay *= backoff_factor
                
                except Exception as e:
                    logger.error(
                        f"[RETRY ABORT] {func.__name__} (async) falhou com exceção não-retryable: "
                        f"{type(e).__name__}: {str(e)}"
                    )
                    raise
            
            raise last_exception
        
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator

def _calculate_delay(base_delay: float, use_jitter: bool) -> float:
    """
    Calcula delay com jitter opcional para evitar thundering herd.
    """
    if not use_jitter:
        return base_delay
    
    # Adiciona variação aleatória de ±25%
    jitter_range = base_delay * 0.25
    jitter_offset = random.uniform(-jitter_range, jitter_range)
    
    return max(0.1, base_delay + jitter_offset)  # Mínimo 0.1s

# Decorators pré-configurados para casos específicos

def retry_network_errors(max_attempts: int = 3, delay: float = 2.0):
    """
    Decorator especializado para erros de rede/conectividade.
    Retry apenas em exceções relacionadas à conectividade.
    """
    import aiohttp
    
    network_exceptions = (
        ConnectionError,
        TimeoutError,
        OSError,  # Network unreachable, etc.
        aiohttp.ClientError,
        aiohttp.ServerTimeoutError,
        aiohttp.ClientConnectionError,
        aiohttp.ClientConnectorError
    )
    
    return retry_on_failure(
        max_attempts=max_attempts,
        delay=delay,
        backoff_factor=1.5,  # Backoff mais suave para rede
        jitter=True,
        exceptions=network_exceptions
    )

def retry_api_errors(max_attempts: int = 2, delay: float = 1.0):
    """
    Decorator especializado para erros de API.
    Retry em erros temporários (5xx), mas não em erros de cliente (4xx).
    """
    import aiohttp
    
    # Exceções que indicam erro temporário do servidor
    api_exceptions = (
        aiohttp.ServerTimeoutError,
        aiohttp.ServerConnectionError,
        aiohttp.ServerDisconnectedError
    )
    
    return retry_on_failure(
        max_attempts=max_attempts,
        delay=delay,
        backoff_factor=2.0,
        jitter=True,
        exceptions=api_exceptions
    )

def retry_database_errors(max_attempts: int = 3, delay: float = 0.5):
    """
    Decorator para erros de banco de dados.
    Retry em deadlocks, timeouts, mas não em constraint violations.
    """
    # Exceções comuns de DB que podem ser retryables
    database_exceptions = (
        ConnectionError,
        TimeoutError,
        # Adicione exceções específicas do seu DB aqui
        # psycopg2.OperationalError,
        # sqlite3.OperationalError,
    )
    
    return retry_on_failure(
        max_attempts=max_attempts,
        delay=delay,
        backoff_factor=1.8,
        jitter=True,
        exceptions=database_exceptions
    )

# Classe para rastrear estatísticas de retry
class RetryStats:
    """Classe para coletar estatísticas de retry (opcional)"""
    
    def __init__(self):
        self.stats = {}
    
    def record_attempt(self, func_name: str, attempt: int, success: bool, exception: str = None):
        """Registra uma tentativa de retry"""
        if func_name not in self.stats:
            self.stats[func_name] = {
                'total_calls': 0,
                'successful_calls': 0,
                'failed_calls': 0,
                'total_attempts': 0,
                'retry_success_rate': 0.0
            }
        
        self.stats[func_name]['total_attempts'] += 1
        
        if attempt == 1:
            self.stats[func_name]['total_calls'] += 1
        
        if success:
            self.stats[func_name]['successful_calls'] += 1
        elif attempt >= 3:  # Falhou após múltiplas tentativas
            self.stats[func_name]['failed_calls'] += 1
        
        # Recalcula success rate
        total = self.stats[func_name]['total_calls']
        successful = self.stats[func_name]['successful_calls']
        self.stats[func_name]['retry_success_rate'] = (successful / total * 100) if total > 0 else 0.0
    
    def get_stats(self, func_name: str = None) -> dict:
        """Retorna estatísticas de retry"""
        if func_name:
            return self.stats.get(func_name, {})
        return self.stats.copy()
    
    def reset_stats(self):
        """Reseta todas as estatísticas"""
        self.stats.clear()

# Instância global de estatísticas (opcional)
retry_stats = RetryStats()

# Exemplo de uso e testes
if __name__ == "__main__":
    import random
    
    # Configura logging
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    @retry_on_failure(max_attempts=4, delay=0.5, backoff_factor=1.5)
    def unreliable_function(success_rate: float = 0.3):
        """Função que falha probabilisticamente para teste"""
        if random.random() < success_rate:
            return "Sucesso!"
        else:
            raise ConnectionError("Falha simulada de rede")
    
    @retry_network_errors(max_attempts=3, delay=0.2)
    async def unreliable_async_function(success_rate: float = 0.4):
        """Função async que falha probabilisticamente"""
        await asyncio.sleep(0.1)  # Simula operação
        if random.random() < success_rate:
            return "Sucesso async!"
        else:
            raise ConnectionError("Falha simulada async")
    
    @retry_on_failure(max_attempts=2, delay=0.1, exceptions=(ValueError,))
    def function_with_specific_exception():
        """Testa retry apenas para exceções específicas"""
        if random.random() < 0.5:
            raise ValueError("Erro que pode ser retryado")
        else:
            raise TypeError("Erro que NÃO pode ser retryado")
    
    async def test_retry_functionality():
        print("=== TESTE DO RETRY ===")
        
        # Teste 1: Função que eventualmente sucede
        print("\n1. Testando função com retry eventual:")
        try:
            result = unreliable_function(success_rate=0.4)
            print(f"Resultado: {result}")
        except Exception as e:
            print(f"Falhou completamente: {e}")
        
        # Teste 2: Função async
        print("\n2. Testando função async com retry:")
        try:
            result = await unreliable_async_function(success_rate=0.6)
            print(f"Resultado async: {result}")
        except Exception as e:
            print(f"Falhou completamente (async): {e}")
        
        # Teste 3: Exceção específica
        print("\n3. Testando retry com exceção específica:")
        try:
            function_with_specific_exception()
        except ValueError as e:
            print(f"ValueError (retryable): {e}")
        except TypeError as e:
            print(f"TypeError (não-retryable): {e}")
        
        # Teste 4: Múltiplas chamadas para ver padrões
        print("\n4. Testando múltiplas chamadas:")
        successes = 0
        failures = 0
        
        for i in range(10):
            try:
                unreliable_function(success_rate=0.7)
                successes += 1
            except:
                failures += 1
        
        print(f"De 10 tentativas: {successes} sucessos, {failures} falhas")
        
        print("\n=== FIM DOS TESTES ===")
    
    # Executa testes
    asyncio.run(test_retry_functionality())