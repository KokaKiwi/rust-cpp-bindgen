#ifndef FFI_H_
#define FFI_H_

#ifdef __cplusplus
#include "extern_lib.hpp"
#endif /* __cplusplus */

#ifdef __cplusplus
typedef ::Sample Sample;
#else
typedef struct {} Sample;
#endif /* __cplusplus */

typedef struct {
    char const* data;
    size_t length;
} std_string_const;

extern "C"
void Sample_delete(Sample* self);

extern "C"
Sample* Sample_new(std_string_const name);

extern "C"
void Sample_sayHi(Sample const* self);

#endif /* FFI_H_ */
