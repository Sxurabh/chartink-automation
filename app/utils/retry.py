import time
import functools

def retry(max_attempts=3, delay=2, backoff=2, exceptions=(Exception,), logger=None):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt < max_attempts:
                        wait = delay * (backoff ** (attempt - 1))
                        if logger:
                            logger.warning(f"Retry {attempt}/{max_attempts} for {func.__name__}: {e}. Waiting {wait}s...")
                        time.sleep(wait)
                    else:
                        if logger:
                            logger.error(f"All {max_attempts} attempts failed for {func.__name__}: {e}")
                        raise
            raise last_exception
        return wrapper
    return decorator
