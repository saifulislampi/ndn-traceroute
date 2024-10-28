cmake_minimum_required(VERSION 3.12)
project(traceroute-client)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

find_package(PkgConfig REQUIRED)
pkg_check_modules(NDN_CXX REQUIRED libndn-cxx)

include_directories(${NDN_CXX_INCLUDE_DIRS})
link_directories(${NDN_CXX_LIBRARY_DIRS})
add_definitions(${NDN_CXX_CFLAGS_OTHER})

add_executable(traceroute-client src/traceroute-client.cpp)
target_link_libraries(traceroute-client ${NDN_CXX_LIBRARIES})
