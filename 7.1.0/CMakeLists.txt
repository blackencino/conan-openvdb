cmake_minimum_required(VERSION 3.10.0)
project(cmake_wrapper)

set(CONAN_BASIC_SETUP_ARGS)
if(APPLE)
    # When building shared libraries
    # the binaries in the build tree need RPATHS
    list(APPEND CONAN_BASIC_SETUP_ARGS KEEP_RPATHS)
    set(CMAKE_SKIP_INSTALL_RPATH 1)
endif()

include(conanbuildinfo.cmake)
conan_basic_setup(${CONAN_BASIC_SETUP_ARGS})

if(WIN32)
add_compile_options("/D NOMINMAX")
endif()

add_subdirectory(source_subfolder)
