from bindgen.ast import *

root = Namespace()
@root.body
class root:
    _includes_ = {
        'extern_lib.hpp',
    }

Sample = root.Class('Sample')
@Sample.body
class Sample:
    new = Constructor((String(const=True), 'name'))
    delete = Destructor()

    sayHi = Method(const=True)
