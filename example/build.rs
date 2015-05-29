extern crate gcc;

fn main() {
    gcc::Config::new()
        .cpp(true)
        .file("src/ffi.cpp")
        .include(".")
        .compile("libbindgen_example_ffi.a");

    gcc::Config::new()
        .cpp(true)
        .file("extern_lib.cpp")
        .compile("libextern_lib.a");
}
