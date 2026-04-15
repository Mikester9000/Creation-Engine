# ===========================================================================
# CMakeLists.txt — Creation Engine (Texture + Map Editor)
# ===========================================================================
#
# TEACHING NOTE — CMake Basics
# ─────────────────────────────
# CMake generates platform-specific build files (Makefile on Linux, .sln on
# Windows) from this platform-neutral description. Typical workflow:
#
#   mkdir build && cd build
#   cmake ..          <- generates Makefile
#   make -j4          <- compiles
#   ./creation-engine texture --prompt "wet stone" --seed 42
#
# Out-of-source builds keep generated files out of the source tree.

cmake_minimum_required(VERSION 3.14)
project(CreationEngine VERSION 1.0 LANGUAGES CXX)

# ---------------------------------------------------------------------------
# C++ Standard
# ---------------------------------------------------------------------------
# C++17 is required for:
#   • std::filesystem (optional, not used here)
#   • if constexpr
#   • structured bindings
#   • std::string_view
set(CMAKE_CXX_STANDARD          17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS        OFF)

# ---------------------------------------------------------------------------
# Compiler warnings
# ---------------------------------------------------------------------------
if(MSVC)
    add_compile_options(/W4)
else()
    add_compile_options(-Wall -Wextra -Wpedantic)
endif()

# ---------------------------------------------------------------------------
# Build type defaults
# ---------------------------------------------------------------------------
if(NOT CMAKE_BUILD_TYPE)
    set(CMAKE_BUILD_TYPE Release CACHE STRING "" FORCE)
endif()
message(STATUS "Build type: ${CMAKE_BUILD_TYPE}")

# ---------------------------------------------------------------------------
# Sources
# ---------------------------------------------------------------------------
# PBR pipeline modules (subdirectory layout)
set(SOURCES
    src/main.cpp
    src/texture/TextureGen.cpp
    src/map/MapGen.cpp
    src/ai/AIAssist.cpp
    # Legacy flat-layout modules (stb_image-based create-texture/map commands)
    src/TextureGenerator.cpp
    src/MapEditor.cpp
    src/AssetIO.cpp
    src/Noise.cpp
)

add_executable(creation-engine ${SOURCES})

# Include paths:
#   src/        — our own headers (both flat and subdirectory)
#   vendor/     — stb_image / stb_image_write (header-only, used by AssetIO)
target_include_directories(creation-engine PRIVATE src/ vendor/)

# Link math library (required on some Linux distros for std::sqrt etc.)
target_link_libraries(creation-engine m)

install(TARGETS creation-engine DESTINATION bin)

# ---------------------------------------------------------------------------
# Print configuration summary
# ---------------------------------------------------------------------------
message(STATUS "=== Creation Engine Build ===")
message(STATUS "  C++ Standard : ${CMAKE_CXX_STANDARD}")
message(STATUS "  Build type   : ${CMAKE_BUILD_TYPE}")
message(STATUS "=============================")
