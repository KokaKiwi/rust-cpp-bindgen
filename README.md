rust-cpp-bindgen
================

An attempt to bind some C++ code to Rust.

The binding is done by proxyfying C++ functions and methods to C-like functions, and binding them in Rust.

Example
=======

You can check an usage example at: [https://github.com/KokaKiwi/rust-llvm](https://github.com/KokaKiwi/rust-llvm)

WARNING
=======

This project is not aimed yet to be used in a safe manner, it's actually just a lot of Python code which generate some Rust code from C++ API representation in Python.

You should not use it yet for your projects.
