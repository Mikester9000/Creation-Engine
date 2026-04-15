/**
 * TextureLoader.cpp - Implementation of the example texture loader.
 *
 * In a real project, define STB_IMAGE_IMPLEMENTATION in exactly one .cpp file.
 * Here we show the pattern; the actual definition lives in AssetIO.cpp when
 * you link against the Creation Engine library.
 */

#include "TextureLoader.h"
#include <iostream>
#include <cstring>

// If building standalone (not linked against Creation Engine), uncomment:
// #define STB_IMAGE_IMPLEMENTATION
// #include "../../vendor/stb_image.h"

// When linked against the Creation Engine the stb_image symbols are already
// available from AssetIO.o, so we just forward-declare what we need.
extern "C" {
    unsigned char* stbi_load(const char* filename, int* x, int* y,
                              int* channels_in_file, int desired_channels);
    void stbi_image_free(void* retval_from_stbi_load);
    const char* stbi_failure_reason(void);
}

bool TextureLoader::loadCPU(const std::string& path, CPUImage& out) {
    int w = 0, h = 0, ch = 0;
    // Force RGBA (4 channels) so the pixel layout is always consistent.
    unsigned char* data = stbi_load(path.c_str(), &w, &h, &ch, 4);
    if (!data) {
        std::cerr << "TextureLoader: failed to load '" << path << "': "
                  << stbi_failure_reason() << "\n";
        return false;
    }

    out.width    = w;
    out.height   = h;
    out.channels = 4;
    out.pixels.resize(static_cast<size_t>(w * h * 4));
    std::memcpy(out.pixels.data(), data, out.pixels.size());
    stbi_image_free(data);

    std::cout << "TextureLoader: loaded '" << path << "' (" << w << "x" << h << ")\n";
    return true;
}

GPUTextureHandle TextureLoader::uploadToGPU(const CPUImage& img) {
    if (img.pixels.empty()) {
        std::cerr << "TextureLoader::uploadToGPU: empty image\n";
        return 0;
    }

    // === STUB ===
    // Replace this block with real GPU upload code, e.g.:
    //   GLuint texID;
    //   glGenTextures(1, &texID);
    //   glBindTexture(GL_TEXTURE_2D, texID);
    //   glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA8, img.width, img.height,
    //                0, GL_RGBA, GL_UNSIGNED_BYTE, img.pixels.data());
    //   glGenerateMipmap(GL_TEXTURE_2D);
    //   return texID;
    // ============

    // Return a fake non-zero handle so callers can detect success.
    static GPUTextureHandle nextHandle = 1;
    GPUTextureHandle h = nextHandle++;
    std::cout << "TextureLoader: (stub) uploaded " << img.width << "x" << img.height
              << " texture as GPU handle " << h << "\n";
    return h;
}

void TextureLoader::freeGPU(GPUTextureHandle handle) {
    // In a real engine: glDeleteTextures(1, &handle);
    std::cout << "TextureLoader: (stub) freed GPU handle " << handle << "\n";
}
