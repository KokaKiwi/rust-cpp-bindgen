from bindgen.ast.objects import *
from bindgen.ast.utils import submodpath
from .ns import llvm
from .ADT.StringRef import StringRef
from .LLVMContext import LLVMContext
from .Type import Type

Value = llvm.Class('Value')
Value.modpath = submodpath(['value'])

Argument = llvm.Class('Argument', Value)
BasicBlock = llvm.Class('BasicBlock', Value)
InlineAsm = llvm.Class('InlineAsm', Value)
MetadataAsValue = llvm.Class('MetadataAsValue', Value)

@Value.body
class Value:
    _includes_ = ['llvm/IR/Value.h']

    ValueTy = Enum(values=[
        'ArgumentVal', 'BasicBlockVal', 'FunctionVal', 'GlobalAliasVal',
        'GlobalVariableVal', 'UndefValueVal', 'BlockAddressVal', 'ConstantExprVal',
        'ConstantAggregateZeroVal', 'ConstantDataArrayVal', 'ConstantDataVectorVal', 'ConstantIntVal',
        'ConstantFPVal', 'ConstantArrayVal', 'ConstantStructVal', 'ConstantVectorVal',
        'ConstantPointerNullVal', 'MetadataAsValueVal', 'InlineAsmVal', 'InstructionVal',
        ('ConstantFirstVal', 'FunctionVal'), ('ConstantLastVal', 'ConstantPointerNullVal'),
    ])

    delete = Destructor()

    dump = Method(const=True)

    getType = Method(ptr(Type), const=True)
    getContext = Method(ref(LLVMContext), const=True)

    hasName = Method(Bool, const=True)
    getName = Method(StringRef, const=True)
    setName = Method(Void, (StringRef, 'Name'))
    takeName = Method(Void, (ptr(Value), 'Value'))

    replaceAllUsesWith = Method(Void, (ptr(Value), 'Value'))

    hasOneUse = Method(Bool, const=True)
    hasNUses = Method(Bool, (UnsignedInt, 'N'), const=True)
    hasNUsesOrMore = Method(Bool, (UnsignedInt, 'N'), const=True)
    isUsedInBasicBlock = Method(Bool, (ptr(BasicBlock, const=True), 'BB'), const=True)
    getNumUses = Method(UnsignedInt, const=True)

    getValueID = Method(UnsignedInt, const=True)
