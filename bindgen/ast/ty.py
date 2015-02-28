import enum


class Type(object):

    @property
    def tyname(self):
        return self.__class__.__name__

    def __eq__(self, other):
        return hash(self) == hash(other)

    def __hash__(self):
        return self._hash()

    def _hash(self):
        return hash(self.__class__.__name__)

    def __repr__(self):
        return 'Type `%s`' % (self.tyname)

# Basic types


class BuiltinType(Type):
    Type = enum.Enum('Type', '''
        void

        char int
        uchar uint
        size

        int8 int16 int32 int64
        uint8 uint16 uint32 uint64

        double float

        bool
    ''', module=__name__)

    def __init__(self, ty):
        if isinstance(ty, str):
            ty = BuiltinType.Type[ty]

        self.ty = ty

    @property
    def tyname(self):
        return self.ty.name

    def _hash(self):
        return hash(self.__class__) + hash(self.ty)

Void = BuiltinType('void')

Char = BuiltinType('char')
Int = BuiltinType('int')

UnsignedChar = BuiltinType('uchar')
UnsignedInt = BuiltinType('uint')

SizeTy = BuiltinType('size')

Int8 = BuiltinType('int8')
Int16 = BuiltinType('int16')
Int32 = BuiltinType('int32')
Int64 = BuiltinType('int64')

UnsignedInt8 = BuiltinType('uint8')
UnsignedInt16 = BuiltinType('uint16')
UnsignedInt32 = BuiltinType('uint32')
UnsignedInt64 = BuiltinType('uint64')

Double = BuiltinType('double')
Float = BuiltinType('float')

Bool = BuiltinType('bool')

# Special types


class Optionnable(Type):

    def __init__(self, subtype, default):
        self.subtype = subtype
        self.default = default

    @property
    def tyname(self):
        return 'option_%s' % (self.subtype.tyname)

    def _hash(self):
        return hash(self.__class__) + hash(self.subtype) + hash(self.default)

# Complex types


class String(Type):

    def __init__(self, const=False):
        self.const = const

    @property
    def name(self):
        const = '_const' if self.const else ''
        return 'string%s' % (const)

    @property
    def tyname(self):
        const = ' const' if self.const else ''
        return 'string%s' % (const)

    def _hash(self):
        return hash(self.__class__) + hash(self.const)


class OptionnableString(Optionnable):

    def __init__(self, default='""', **kwargs):
        super().__init__(String(**kwargs), default)

OptionString = OptionnableString

# Make some aliases for optionnable types
Option = Optionnable


class Ref(Type):

    def __init__(self, subtype, const=False):
        self.subtype = subtype
        self.const = const

    @property
    def tyname(self):
        const = '_const' if self.const else ''
        return 'ref_%s%s' % (self.subtype.tyname, const)

    def _hash(self):
        return hash(self.__class__) + hash(self.subtype) + hash(self.const)

ref = Ref


class Pointer(Type):

    def __init__(self, subtype, const=False, owned=False, nullable=True):
        self.subtype = subtype
        self.const = const
        self.owned = owned
        self.nullable = nullable

    @property
    def tyname(self):
        const = '_const' if self.const else ''
        return 'ptr_%s%s' % (self.subtype.tyname, const)

    def _hash(self):
        return hash(self.__class__) + hash(self.subtype) + hash(self.const) + hash(self.owned) + hash(self.nullable)

ptr = Pointer


class OptionnablePointer(Optionnable):

    def __init__(self, *args, **kwargs):
        super().__init__(Pointer(*args, **kwargs), 'NULL')

OptionPointer = OptionnablePointer

# Describe a pointer which can't be null
# /!\ USE IT WISELY /!\


def sptr(*args, **kwargs):
    return ptr(*args, nullable=False, **kwargs)
