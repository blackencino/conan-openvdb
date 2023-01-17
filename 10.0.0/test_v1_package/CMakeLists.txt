cmake_minimum_required(VERSION 3.10.0)
project(test_package CXX)

find_package(OpenVDB REQUIRED)

add_executable(example ../test_package/example.cpp)
target_link_libraries(example PUBLIC OpenVDB::OpenVDB)
target_compile_features(example PUBLIC cxx_std_14)
