from bindgen.ast.objects import *
from bindgen.ast.utils import submodpath
from .ns import llvm
from .LLVMContext import LLVMContext
from .ADT.StringRef import StringRef
from .ADT.ArrayRef import ArrayRef

Type = llvm.Class('Type')
Type.modpath = submodpath(['ty'])

CompositeType = llvm.Class('CompositeType', Type)
FunctionType = llvm.Class('FunctionType', Type)
IntegerType = llvm.Class('IntegerType', Type)

SequentialType = llvm.Class('SequentialType', CompositeType)
SequentialType.modpath = submodpath(['seq'])
StructType = llvm.Class('StructType', CompositeType)

ArrayType = llvm.Class('ArrayType', SequentialType)
PointerType = llvm.Class('PointerType', SequentialType)
VectorType = llvm.Class('VectorType', SequentialType)

@Type.body
class Type:
    _includes_ = ['llvm/IR/Type.h']

    TypeID = Enum(values=[
        ('VoidTyID', 0), 'HalfTyID', 'FloatTyID', 'DoubleTyID',
        'X86_FP80TyID', 'FP128TyID', 'PPC_FP128TyID', 'LabelTyID',
        'MetadataTyID', 'X86_MMXTyID', 'IntegerTyID', 'FunctionTyID',
        'StructTyID', 'ArrayTyID', 'PointerTyID', 'VectorTyID',
    ])

    getContext = Method(ref(LLVMContext), const=True)
    dump = Method(const=True)

    getTypeID = Method(TypeID, const=True)

    def type_checker():
        return Method(Bool, const=True)

    isVoidTy = type_checker()
    isHalfTy = type_checker()
    isFloatTy = type_checker()
    isDoubleTy = type_checker()
    isX86_FP80Ty = type_checker()
    isFP128Ty = type_checker()
    isPPC_FP128Ty = type_checker()
    isFloatingPointTy = type_checker()
    isX86_MMXTy = type_checker()
    isFPOrFPVectorTy = type_checker()
    isLabelTy = type_checker()
    isMetadataTy = type_checker()
    isIntOrIntVectorTy = type_checker()
    isFunctionTy = type_checker()
    isStructTy = type_checker()
    isArrayTy = type_checker()
    isPointerTy = type_checker()
    isPtrOrPtrVectorTy = type_checker()
    isVectorTy = type_checker()
    isEmptyTy = type_checker()
    isFirstClassType = type_checker()
    isSingleValueType = type_checker()
    isAggregateType = type_checker()
    isSized = type_checker()
    isIntegerTy = type_checker()

    isFunctionVarArg = Method(Bool, const=True)

    getStructName = Method(StringRef, const=True)
    getStructNumElements = Method(UnsignedInt, const=True)
    getStructElementType = Method(ptr(Type), (UnsignedInt, 'idx'), const=True)
    getSequentialElementType = Method(ptr(Type), const=True)

    def type_factory():
        return StaticMethod(ptr(Type), (ref(LLVMContext), 'ctx'))

    getVoidTy = type_factory()
    getLabelTy = type_factory()
    getHalfTy = type_factory()
    getFloatTy = type_factory()
    getDoubleTy = type_factory()
    getMetadataTy = type_factory()
    getX86_FP80Ty = type_factory()
    getFP128Ty = type_factory()
    getPPC_FP128Ty = type_factory()
    getX86_MMXTy = type_factory()

    def integer_factory():
        return StaticMethod(ptr(IntegerType), (ref(LLVMContext), 'ctx'))

    getIntNTy = StaticMethod(ptr(IntegerType), (ref(LLVMContext), 'ctx'), (UnsignedInt, 'size'))
    getInt1Ty = integer_factory()
    getInt8Ty = integer_factory()
    getInt16Ty = integer_factory()
    getInt32Ty = integer_factory()
    getInt64Ty = integer_factory()

    def pointer_factory():
        return StaticMethod(ptr(PointerType), (ref(LLVMContext), 'ctx'))

    getIntNPtrTy = StaticMethod(ptr(PointerType), (ref(LLVMContext), 'ctx'), (UnsignedInt, 'size'))
    getHalfPtrTy = pointer_factory()
    getFloatPtrTy = pointer_factory()
    getDoublePtrTy = pointer_factory()
    getX86_FP80PtrTy = pointer_factory()
    getFP128PtrTy = pointer_factory()
    getPPC_FP128PtrTy = pointer_factory()
    getX86_MMXPtrTy = pointer_factory()
    getInt1PtrTy = pointer_factory()
    getInt8PtrTy = pointer_factory()
    getInt16PtrTy = pointer_factory()
    getInt32PtrTy = pointer_factory()
    getInt64PtrTy = pointer_factory()

    getContainedType = Method(ptr(Type), (UnsignedInt, 'idx'), const=True)
    getNumContainedTypes = Method(UnsignedInt, const=True)

    getFunctionParamType = Method(ptr(Type), (UnsignedInt, 'idx'), const=True)
    getFunctionNumParams = Method(UnsignedInt, const=True)

    getPointerElementType = Method(ptr(Type), const=True)
    getPointerAddressSpace = Method(UnsignedInt, const=True)
    getPointerTo = Method(ptr(PointerType), (UnsignedInt, 'idx'))

@llvm.body
class llvm_body:
    _includes_ = ['llvm/IR/DerivedTypes.h']

def classof_method():
    return StaticMethod(Bool, (ptr(Type, const=True), 'ty'))

@IntegerType.body
class IntegerType:
    getBitWidth = Method(UnsignedInt, const=True)

    getBitMask = Method(UnsignedInt64, const=True)
    getSignBit = Method(UnsignedInt64, const=True)

    isPowerOf2ByteWidth = Method(Bool, const=True)

    get = StaticMethod(ptr(IntegerType), (ref(LLVMContext), 'ctx'), (UnsignedInt, 'NumBits'))
    classof = classof_method()

@FunctionType.body
class FunctionType:
    isVarArg = Method(Bool, const=True)

    getReturnType = Method(ptr(Type), const=True)
    getParamType = Method(ptr(Type), (UnsignedInt, 'idx'), const=True)
    getNumParams = Method(UnsignedInt, const=True)

    get = StaticMethod(ptr(FunctionType), (ptr(Type), 'Result'), (ArrayRef(ptr(Type)), 'Params'), (Bool, 'isVarArg'))

    isValidReturnType = StaticMethod(Bool, (ptr(Type), 'ty'))
    isValidArgumentType = StaticMethod(Bool, (ptr(Type), 'ty'))

    classof = classof_method()

@CompositeType.body
class CompositeType:
    getTypeAtIndex = Method(ptr(Type), (UnsignedInt, 'idx'))
    indexValid = Method(Bool, (UnsignedInt, 'idx'), const=True)

    classof = classof_method()

@StructType.body
class StructType:
    isPacked = Method(Bool, const=True)
    isLiteral = Method(Bool, const=True)
    isOpaque = Method(Bool, const=True)
    isSized = Method(Bool, const=True)

    hasName = Method(Bool, const=True)
    getName = Method(StringRef, const=True)
    setName = Method(Void, (StringRef, 'Name'))

    setBody = Method(Void, (ArrayRef(ptr(Type)), 'Elements'))
    setBodyPacked = Method(Void, (ArrayRef(ptr(Type)), 'Elements'), (Bool, 'isPacked')).with_call_name('setBody')

    isLayoutIdentical = Method(Bool, (ptr(StructType), 'Other'), const=True)

    getNumElements = Method(UnsignedInt, const=True)
    getElementType = Method(ptr(Type), (UnsignedInt, 'idx'), const=True)

    create = StaticMethod(ptr(StructType), (ref(LLVMContext), 'ctx'), (ArrayRef(ptr(Type)), 'Elements'), (StringRef, 'Name'))
    createPacked = StaticMethod(ptr(StructType), (ref(LLVMContext), 'ctx'), (ArrayRef(ptr(Type)), 'Elements'), (StringRef, 'Name'), (Bool, 'isPacked')).with_call_name('create')

    isValidElementType = StaticMethod(Bool, (ptr(Type), 'ty'))

    classof = classof_method()

@SequentialType.body
class SequentialType:
    getElementType = Method(ptr(Type), const=True)

    classof = classof_method()

@VectorType.body
class VectorType:
    getNumElements = Method(UnsignedInt, const=True)
    getBitWidth = Method(UnsignedInt, const=True)

    get = StaticMethod(ptr(VectorType), (ptr(Type), 'ty'), (UnsignedInt, 'NumElements'))
    getInteger = StaticMethod(ptr(VectorType), (ptr(VectorType), 'ty'))
    getExtendedElementVectorType = StaticMethod(ptr(VectorType), (ptr(VectorType), 'ty'))
    getTruncatedElementVectorType = StaticMethod(ptr(VectorType), (ptr(VectorType), 'ty'))
    getHalfElementsVectorType = StaticMethod(ptr(VectorType), (ptr(VectorType), 'ty'))
    getDoubleElementsVectorType = StaticMethod(ptr(VectorType), (ptr(VectorType), 'ty'))

    isValidElementType = StaticMethod(Bool, (ptr(Type), 'ty'))

    classof = classof_method()

@PointerType.body
class PointerType:
    getAddressSpace = Method(UnsignedInt, const=True)

    get = StaticMethod(ptr(PointerType), (ptr(Type), 'ElementType'), (UnsignedInt, 'AddressSpace'))
    getUnqual = StaticMethod(ptr(PointerType), (ptr(Type), 'ElementType'))

    isValidElementType = StaticMethod(Bool, (ptr(Type), 'ty'))

    classof = classof_method()

@ArrayType.body
class ArrayType:
    getNumElements = Method(UnsignedInt64, const=True)

    get = StaticMethod(ptr(ArrayType), (ptr(Type), 'ElementType'), (UnsignedInt64, 'NumElements'))

    isValidElementType = StaticMethod(Bool, (ptr(Type), 'ty'))

    classof = classof_method()
