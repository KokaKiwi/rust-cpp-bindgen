#include "extern_lib.hpp"
#include "ffi.h"

extern "C"
void Sample_delete(Sample* self)
{
    delete self;
}

extern "C"
Sample* Sample_new(std_string_const _name)
{
    std::string name(_name.data, _name.length);
    return new(std::nothrow) ::Sample(name);
}

extern "C"
void Sample_sayHi(Sample const* self)
{
    self->sayHi();
}
