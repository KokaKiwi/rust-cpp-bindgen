from bindgen.ast.objects import *
from .ns import llvm
from .User import User

@llvm.body
class llvm_body:
    _includes_ = ['llvm/IR/Instruction.h']

Instruction = llvm.Class('Instruction', User)

AtomicCmpXchgInst = llvm.Class('AtomicCmpXchgInst', Instruction)
AtomicRMWInst = llvm.Class('AtomicRMWInst', Instruction)
BinaryOperator = llvm.Class('BinaryOperator', Instruction)
CallInst = llvm.Class('CallInst', Instruction)
CmpInst = llvm.Class('CmpInst', Instruction)
ExtractElementInst = llvm.Class('ExtractElementInst', Instruction)
FenceInst = llvm.Class('FenceInst', Instruction)
GetElementPtrInst = llvm.Class('GetElementPtrInst', Instruction)
InsertElementInst = llvm.Class('InsertElementInst', Instruction)
InsertValueInst = llvm.Class('InsertValueInst', Instruction)
LandingPadInst = llvm.Class('LandingPadInst', Instruction)
PHINode = llvm.Class('PHINode', Instruction)
SelectInst = llvm.Class('SelectInst', Instruction)
ShuffleVectorInst = llvm.Class('ShuffleVectorInst', Instruction)
StoreInst = llvm.Class('StoreInst', Instruction)
TerminatorInst = llvm.Class('TerminatorInst', Instruction)
UnaryInstruction = llvm.Class('UnaryInstruction', Instruction)

BranchInst = llvm.Class('BranchInst', TerminatorInst)
IndirectBrInst = llvm.Class('IndirectBrInst', TerminatorInst)
InvokeInst = llvm.Class('InvokeInst', TerminatorInst)
ResumeInst = llvm.Class('ResumeInst', TerminatorInst)
ReturnInst = llvm.Class('ReturnInst', TerminatorInst)
SwitchInst = llvm.Class('SwitchInst', TerminatorInst)
UnreachableInst = llvm.Class('UnreachableInst', TerminatorInst)

AllocaInst = llvm.Class('AllocaInst', UnaryInstruction)
CastInst = llvm.Class('CastInst', UnaryInstruction)
ExtractValueInst = llvm.Class('ExtractValueInst', UnaryInstruction)
LoadInst = llvm.Class('LoadInst', UnaryInstruction)
VAArgInst = llvm.Class('VAArgInst', UnaryInstruction)

AddrSpaceCastInst = llvm.Class('AddrSpaceCastInst', CastInst)
BitCastInst = llvm.Class('BitCastInst', CastInst)
FPExtInst = llvm.Class('FPExtInst', CastInst)
FPToSIInst = llvm.Class('FPToSIInst', CastInst)
