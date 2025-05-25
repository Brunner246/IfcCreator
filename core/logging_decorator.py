import functools
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)


def logger(func, level=logging.INFO):
    # https://docs.python.org/3.12/library/functools.html#functools.wraps
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        args_repr = [repr(a) for a in args]
        kwargs_repr = [f"{k}={v!r}" for k, v in kwargs.items()]
        signature = ", ".join(args_repr + kwargs_repr)
        logging.log(level, f"Calling {func.__name__}({signature})")
        result = func(*args, **kwargs)
        logging.log(level, f"{func.__name__!r} returned {result!r}")
        return result

    return wrapper
