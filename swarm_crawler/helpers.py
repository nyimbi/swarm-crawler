from copy import copy
import sys
from contextlib import contextmanager

@contextmanager
def included_local_path():
    orig_path = copy(sys.path)
    sys.path.insert(0, '')
    try:
        yield
    finally:
        sys.path = orig_path

