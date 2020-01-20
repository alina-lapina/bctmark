import time
from datetime import datetime


def print_ex_time(func):
    def wrapper(*args, **kwargs):
        start_time = time.time()
        response = func(*args, **kwargs)
        endtime = datetime.today().strftime('%Y-%m-%d-%H:%M:%S')
        print("Function %s executed in %s seconds (at %s)" % (func.__name__, time.time() - start_time, endtime))
        return response
    return wrapper
