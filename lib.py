from functional import seq
from functools import wraps
import sys
import time


class logtime:
    @classmethod
    def _log_msg(cls, f, elapsed_time, *args, **kwargs):
        arg_string = (seq(args).map(repr) +
                      seq(kwargs.items()).map(
                          lambda kv: '{!r}={!r}'.format(kv[0], kv[1]))
                      ).make_string(', ')

        log_msg = "{}({}) - execution time: {:.2f} ".format(f.__name__, arg_string, elapsed_time)
        return log_msg

    def __init__(self, logger=None, handler=None):
        if logger:
            self.handler = lambda f, elapsed_time, *args, **kwargs: \
                logger.info(logtime._log_msg(f, elapsed_time, *args, **kwargs))
        elif handler:
            self.handler = lambda  f, elapsed_time, *args, **kwargs: handler(f, elapsed_time, *args, **kwargs)
            
        else:
            self.handler = lambda f, elapsed_time, *args, **kwargs: \
                print(logtime._log_msg(f, elapsed_time, *args, **kwargs), file=sys.stderr)
            
        
    def __call__(self, f):
        def wrapped(*args, **kwargs):
            start = time.time()
            out = f(*args, **kwargs)
            end = time.time()

            self.handler(f, end-start, *args, **kwargs)
            return out
        return wrapped
