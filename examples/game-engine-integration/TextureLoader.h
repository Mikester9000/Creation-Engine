/**
 * TextureLoader.h - Example: loading Creation Engine textures into a game engine.
 *
 * This example shows how a real-time game engine might load the PNG files
 * produced by the Creation Engine CLI. In a real project you would replace
 * the stub "upload to GPU" comment with actual OpenGL/Vulkan/DirectX calls.
 */

#pragma once
#include <string>
#include <cstdint>
#include <vector>

/** GPU handle for a 2-D texture (opaque integer in real engines). */
using GPUTextureHandle = uint32_t;

/** Raw CPU-side image data ready for upload. */
struct CPUImage {
    int width    = 0;
    int height   = 0;
    int channels = 4;              // always RGBA in this loader
    std::vector<uint8_t> pixels;   // row-major RGBA bytes
};

/**
 * TextureLoader - Loads PNG images into CPU memory and (optionally) GPU textures.
 *
 * Usage:
 *   CPUImage img;
 *   if (TextureLoader::loadCPU("assets/textures/noise.png", img)) {
 *       GPUTextureHandle handle = TextureLoader::uploadToGPU(img);
 *       // Use handle in draw calls.
 *   }
 */
class TextureLoader {
public:
    /**
     * loadCPU - Decode a PNG/JPEG/BMP image from disk into a CPUImage.
     * Uses stb_image under the hood (already compiled into the Creation Engine).
     * @return true on success.
     */
    static bool loadCPU(const std::string& path, CPUImage& out);

    /**
     * uploadToGPU - Upload a CPUImage to the GPU and return a handle.
     * In this stub the function just prints what it would do.
     * Replace with real glTexImage2D / vkCreateImage calls.
     * @return A non-zero GPU handle on success, 0 on failure.
     */
    static GPUTextureHandle uploadToGPU(const CPUImage& img);

    /**
     * freeGPU - Release a GPU texture handle when it is no longer needed.
     */
    static void freeGPU(GPUTextureHandle handle);
};
