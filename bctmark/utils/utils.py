import time


def print_ex_time(func):
    def wrapper(*args, **kwargs):
        start_time = time.time()
        response = func(*args, **kwargs)
        print("Function %s executed in %s seconds" % (func.__name__, time.time() - start_time))
        return response
    return wrapper
