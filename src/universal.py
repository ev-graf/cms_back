import functools
import time

from requests import exceptions


def retry_request(max_retries=3, delay=2, backoff=2):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            retries = 0
            current_delay = delay

            while retries <= max_retries:
                try:
                    return func(*args, **kwargs)
                except (exceptions.ConnectionError, exceptions.Timeout, exceptions.HTTPError) as e:
                    # print(f"Ошибка: {e}, пробую снова через {current_delay} сек.")
                    retries += 1
                    if retries > max_retries:
                        raise
                    time.sleep(current_delay)
                    current_delay *= backoff
            return None
        return wrapper
    return decorator
