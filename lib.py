from functional import seq
from functools import wraps
import sys
import time


def logtime(logger=None, handler=None):
    def wrapped_f(f):
        def wrapped(*args, **kwargs):
            start = time.time()
            out = f(*args, **kwargs)
            end = time.time()

            arg_string = (seq(args).map(repr) +
                          seq(kwargs.items()).map(
                              lambda kv: '{!r}={!r}'.format(kv[0], kv[1]))
                          ).make_string(', ')

            log_msg = "{}({}) execution time: {:.2f} ".format(f.__name__, arg_string, end-start)

            if logger:
                logger.debug(log_msg)
            elif handler:
                handler(end-start, f.__name__, *args, **kwargs, )
            else:
                print(log_msg, file=sys.stderr)

            return out
        return wrapped
    return wrapped_f
