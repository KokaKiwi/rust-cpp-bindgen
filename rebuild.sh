#!/bin/bash
set -e
ROOT_DIR=$(realpath $(dirname $0))

CXX="clang++"
CXXFLAGS="`llvm-config --cppflags` -fPIC -std=c++11"
RUSTC="rustc"
RUSTDOC="rustdoc"

run() {
    echo "+ $*"
    $*
}

_cmd="$1"
stopif() {
    if test "${_cmd}" = "$1"; then
        exit 0
    fi
}

cd ${ROOT_DIR}

rm -rf out
run python main.py llvm out

stopif "gen"

pushd out &>/dev/null

# Compile FFI lib
run ${CXX} ${CXXFLAGS} -c -o ffi.o ffi.cpp
run ar rc libffi_native.a ffi.o
run ranlib libffi_native.a

# Compile Rust lib
if test "${_cmd}" = "expand"; then
    run ${RUSTC} --crate-name llvm -L /usr/lib --crate-type lib --pretty expanded -o expand.rs lib.rs
    exit 0
fi

run ${RUSTC} --crate-name llvm -L /usr/lib --crate-type lib lib.rs

stopif "build"

run ${RUSTDOC} --crate-name llvm -L /usr/lib -o doc lib.rs

stopif "doc"

popd &>/dev/null

run ${RUSTC} -L out -l ffi_native -o out/llvm_simple example/simple.rs

case "${_cmd}" in
    "run")
        run out/llvm_simple
        ;;

    "valgrind")
        run valgrind out/llvm_simple
        ;;
esac
