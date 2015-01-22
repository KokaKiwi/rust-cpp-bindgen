from .ns import *
from .cls import *
from .enum import *
from .func import *
from .ty import *

def is_class_type(ty):
    return isinstance(ty, Class) or is_class_container(ty)

def is_class_container(ty):
    return isinstance(ty, (Pointer, Ref, Option)) and is_class_type(ty.subtype)

def get_class_type(ty):
    if isinstance(ty, (Pointer, Ref, Option)):
        return get_class_type(ty.subtype)
    if isinstance(ty, Class):
        return ty
    return None

def get_class_ptr(ty):
    if isinstance(ty, (Option)):
        return get_class_ptr(ty.subtype)
    if isinstance(ty, (Pointer)) and is_class_type(ty.subtype):
        return ty
    return None

def get_class_ref(ty):
    if isinstance(ty, (Option)):
        return get_class_ptr(ty.subtype)
    if isinstance(ty, (Ref)) and is_class_type(ty.subtype):
        return ty
    return None
