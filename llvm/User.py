from bindgen.ast.objects import *
from bindgen.ast.utils import submodpath
from .ns import llvm
from .Value import Value

User = llvm.Class('User', Value)
User.modpath = submodpath(['user'])

Operator = llvm.Class('Operator', User)
