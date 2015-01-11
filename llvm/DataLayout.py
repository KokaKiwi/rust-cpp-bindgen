from bindgen.ast.objects import *
from .ns import llvm

DataLayout = llvm.Class('DataLayout')

@DataLayout.body
class DataLayout:
    _includes_ = ['llvm/IR/DataLayout.h']
