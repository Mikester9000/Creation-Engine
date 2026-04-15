cmake_minimum_required(VERSION 3.14)
project(CreationEngine VERSION 1.0 LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Include paths: src/ for our headers, vendor/ for stb
include_directories(src vendor)

# All source files
file(GLOB SOURCES "src/*.cpp")

add_executable(creation-engine ${SOURCES})

target_compile_options(creation-engine PRIVATE -Wall -Wextra)

# Link math library (required on some Linux distros for std::sqrt etc.)
target_link_libraries(creation-engine m)

install(TARGETS creation-engine DESTINATION bin)
