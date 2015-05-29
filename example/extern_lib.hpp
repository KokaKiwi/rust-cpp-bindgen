#pragma once

#include <string>

class Sample
{
public:
    Sample(const std::string &name);

public:
    void sayHi() const;

private:
    std::string name;
};
