import functools
from functools import wraps


def log_decorator(logger, level=10):
    def real_decorator(function):
        @wraps(function)
        def wrapper(*args, **kwargs):
            name = function.__name__
            logger.log(level=level, msg=f"Start {name}")
            out = function(*args, **kwargs)
            logger.log(level=level, msg=f"End {name}")
            return out

        return wrapper

    return real_decorator
