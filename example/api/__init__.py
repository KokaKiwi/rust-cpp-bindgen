from bindgen.ast import *

root = Namespace()
@root.body
class root:
    _includes_ = {
        'extern_lib.hpp',
    }

@root.Class('Sample')
class Sample:
    new = Constructor((String(const=True), 'name'))
    delete = Destructor()

    sayHi = Method(const=True)
