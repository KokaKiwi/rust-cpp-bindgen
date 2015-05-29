extern crate bindgen_example;

use bindgen_example::ffi;

fn main() {
    let sample = ffi::Sample::new("a rustacean");
    ffi::Sample::sayHi(sample);
    ffi::Sample::delete(sample);
}
