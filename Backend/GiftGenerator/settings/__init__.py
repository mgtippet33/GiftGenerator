from .base import *

try:
    from .local import *
except ImportError:
    print("You need the [SECRET_KEY]")
