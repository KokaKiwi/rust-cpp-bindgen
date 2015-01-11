from bindgen.ast.objects import *
from .ns import llvm

LLVMContext = llvm.Class('LLVMContext')

@llvm.body
class llvm_body:
    _includes_ = ['llvm/IR/LLVMContext.h']

    getGlobalContext = Function(ref(LLVMContext))
