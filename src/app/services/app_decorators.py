import asyncio
import sys
import time
import traceback
from functools import wraps

from app.services.logger import SWCoreLogger

LOGGER = SWCoreLogger().get_logger()


# Декоратор для ожидания выполнения функции по настройкам
def settings_sleep(seconds_for_sleep):
    def wrapper(func):
        @wraps(func)
        async def sync_inner(*args, **kwargs):
            # Спим сколько указано
            await asyncio.sleep(seconds_for_sleep)
            result = await func(*args, **kwargs)
            return result

        @wraps(func)
        async def async_inner(*args, **kwargs):
            # Спим сколько указано
            await asyncio.sleep(seconds_for_sleep)
            result = await func(*args, **kwargs)
            return result

        if asyncio.iscoroutinefunction(func):
            return async_inner
        return sync_inner

    return wrapper


# Декоратор для логирования ошибок
def error_logger(func):
    @wraps(func)
    def sync_inner(*args, **kwargs):
        try:
            func_result = func(*args, **kwargs)
            return func_result
        except Exception as error:
            error_type, error_value, error_trace = sys.exc_info()
            traceback.print_exception(error_type, error_value, error_trace, limit=5, file=sys.stdout)
            LOGGER.error(f"{error} {error_type} {error_value} {traceback.extract_tb(error_trace)}")

    @wraps(func)
    async def async_inner(*args, **kwargs):
        try:
            func_result = await func(*args, **kwargs)
            return func_result
        except Exception as error:
            error_type, error_value, error_trace = sys.exc_info()
            traceback.print_exception(error_type, error_value, error_trace, limit=5, file=sys.stdout)
            LOGGER.error(f"{error} {error_type} {error_value} {traceback.extract_tb(error_trace)}")

    if asyncio.iscoroutinefunction(func):
        return async_inner
    return sync_inner


# Декоратор для логирования времени выполнения функции
def log_execution_time(func):
    @wraps(func)
    def sync_inner(*args, **kwargs):
        start = time.perf_counter()
        func_result = func(*args, **kwargs)
        executing_time = time.perf_counter() - start
        LOGGER.debug(f"Выполнение {func.__name__} за {executing_time:0.2f} секунд. Данные {args=} {kwargs=}")
        return func_result

    @wraps(func)
    async def async_inner(*args, **kwargs):
        start = time.perf_counter()
        func_result = await func(*args, **kwargs)
        executing_time = time.perf_counter() - start
        LOGGER.debug(f"Выполнение {func.__name__} за {executing_time:0.2f} секунд. Данные {args=} {kwargs=}")
        return func_result

    if asyncio.iscoroutinefunction(func):
        return async_inner
    return sync_inner
