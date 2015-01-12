from .ns import *
from .cls import *
from .enum import *
from .func import *
from .ty import *

def is_class_type(ty):
    return isinstance(ty, (Pointer, Ref)) and isinstance(ty.subtype, Class)
