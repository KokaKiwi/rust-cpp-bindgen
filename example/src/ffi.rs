#![allow(dead_code)]
#![allow(non_camel_case_types)]
#![allow(non_snake_case)]
extern crate libc;

#[repr(C)]
pub struct Sample;

#[repr(C)]
pub struct std_string_const {
    pub data: *const libc::c_char,
    pub length: libc::size_t,
}

pub mod raw {
    extern "C" {
        pub fn Sample_delete(inst: *mut super::Sample);
        pub fn Sample_new(name: super::std_string_const) -> *mut super::Sample;
        pub fn Sample_sayHi(inst: *const super::Sample);
    }
}

pub mod Sample {
    #[inline(always)]
    pub fn delete(inst: *mut super::Sample) {
        unsafe {
            super::raw::Sample_delete(inst)
        }
    }

    #[inline(always)]
    pub fn new(name: &str) -> *mut super::Sample {
        let name = super::std_string_const {
            data: unsafe { ::std::mem::transmute(name.as_ptr()) },
            length: name.len() as super::libc::size_t,
        };
        unsafe {
            super::raw::Sample_new(name)
        }
    }

    #[inline(always)]
    pub fn sayHi(inst: *const super::Sample) {
        unsafe {
            super::raw::Sample_sayHi(inst)
        }
    }
}
