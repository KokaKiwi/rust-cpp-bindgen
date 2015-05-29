#include <iostream>
#include "extern_lib.hpp"

Sample::Sample(const std::string &name)
    : name(name)
{}

void Sample::sayHi() const
{
    std::cout << "Hi, I'm " << this->name << "!" << std::endl;
}
