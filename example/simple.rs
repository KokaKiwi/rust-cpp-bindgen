#![allow(unstable)]

extern crate llvm;
extern crate libc;

use llvm::llvm::ty::{Type, StructType, TypeExt};
use llvm::llvm::ty::seq::{PointerType};

fn main() {
    let ctx = llvm::llvm::get_global_context();

    let ty = StructType::create(ctx, &[
        &Type::get_int8_ty(ctx),
        &PointerType::get(Type::get_int8_ty(ctx), 0),
    ], "dummy");
    ty.dump();
}
