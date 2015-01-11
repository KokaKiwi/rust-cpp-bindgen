from bindgen.ast.objects import *
from bindgen.ast.utils import submodpath
from .ns import llvm
from .User import User

@llvm.body
class llvm_body:
    _includes_ = ['llvm/IR/Constants.h']

Constant = llvm.Class('Constant', User)
Constant.modpath = submodpath(['constant'])

BlockAddress = llvm.Class('BlockAddress', Constant)
ConstantAggregateZero = llvm.Class('ConstantAggregateZero', Constant)
ConstantArray = llvm.Class('ConstantArray', Constant)
ConstantDataSequential = llvm.Class('ConstantDataSequential', Constant)
ConstantExpr = llvm.Class('ConstantExpr', Constant)
ConstantFP = llvm.Class('ConstantFP', Constant)
ConstantInt = llvm.Class('ConstantInt', Constant)
ConstantPointerNull = llvm.Class('ConstantPointerNull', Constant)
ConstantStruct = llvm.Class('ConstantStruct', Constant)
ConstantVector = llvm.Class('ConstantVector', Constant)
GlobalValue = llvm.Class('GlobalValue', Constant)
UndefValue = llvm.Class('UndefValue', Constant)

ConstantDataArray = llvm.Class('ConstantDataArray', ConstantDataSequential)
ConstantDataVector = llvm.Class('ConstantDataVector', ConstantDataSequential)

BinaryConstantExpr = llvm.Class('BinaryConstantExpr', ConstantExpr)
CompareConstantExpr = llvm.Class('CompareConstantExpr', ConstantExpr)
ExtractElementConstantExpr = llvm.Class('ExtractElementConstantExpr', ConstantExpr)
ExtractValueConstantExpr = llvm.Class('ExtractValueConstantExpr', ConstantExpr)
GetElementPtrConstantExpr = llvm.Class('GetElementPtrConstantExpr', ConstantExpr)
InsertElementConstantExpr = llvm.Class('InsertElementConstantExpr', ConstantExpr)
InsertValueConstantExpr = llvm.Class('InsertValueConstantExpr', ConstantExpr)
