cmake_minimum_required(VERSION 3.12)
project(icn-traceroute)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

# Include subdirectories
add_subdirectory(client)
add_subdirectory(producer)
