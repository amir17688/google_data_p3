""" repr_to_str_decorator gets around IPython wanting to take the
# __repr__ of string output instead of __str__. """

import functools

def r_to_s(func):
    """Decorator method for Workbench methods returning a str"""

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        """Decorator method for Workbench methods returning a str"""

        class ReprToStr(str):
            """Replaces a class __repr__ with it's string representation"""
            def __repr__(self):
                return str(self)
        return ReprToStr(func(*args, **kwargs))
    return wrapper
