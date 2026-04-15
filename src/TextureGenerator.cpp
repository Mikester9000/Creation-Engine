/**
 * TextureGenerator.cpp - Implementation of procedural texture generation.
 *
 * Each method is documented with step-by-step comments so you can follow
 * the algorithm without needing external references.
 */

#include "TextureGenerator.h"
#include <cmath>
#include <algorithm>

// ============================================================
//  Private helpers
// ============================================================

uint8_t TextureGenerator::lerpChannel(float t, uint8_t a, uint8_t b) {
    // Interpolate a single byte channel; clamp to avoid overflow.
    float result = static_cast<float>(a) + t * (static_cast<float>(b) - static_cast<float>(a));
    if (result < 0.0f)   result = 0.0f;
    if (result > 255.0f) result = 255.0f;
    return static_cast<uint8_t>(result);
}

Color TextureGenerator::lerpColor(float t, Color c1, Color c2) {
    // Interpolate all four channels independently.
    return {
        lerpChannel(t, c1.r, c2.r),
        lerpChannel(t, c1.g, c2.g),
        lerpChannel(t, c1.b, c2.b),
        lerpChannel(t, c1.a, c2.a)
    };
}

// ============================================================
//  solidColor
// ============================================================

Texture TextureGenerator::solidColor(int w, int h, Color c) {
    Texture tex;
    tex.resize(w, h);
    // Fill every pixel with the same colour.
    for (auto& px : tex.pixels) px = c;
    return tex;
}

// ============================================================
//  checkerboard
// ============================================================

Texture TextureGenerator::checkerboard(int w, int h, Color c1, Color c2, int cellSize) {
    Texture tex;
    tex.resize(w, h);
    for (int y = 0; y < h; ++y) {
        for (int x = 0; x < w; ++x) {
            // Determine which cell (cx, cy) this pixel falls in.
            // Sum of cell indices: even = c1, odd = c2.
            int cx = x / cellSize;
            int cy = y / cellSize;
            bool even = (cx + cy) % 2 == 0;
            tex.at(x, y) = even ? c1 : c2;
        }
    }
    return tex;
}

// ============================================================
//  stripes
// ============================================================

Texture TextureGenerator::stripes(int w, int h, Color c1, Color c2,
                                   int stripeWidth, bool horizontal) {
    Texture tex;
    tex.resize(w, h);
    for (int y = 0; y < h; ++y) {
        for (int x = 0; x < w; ++x) {
            // Use either the x or y coordinate to determine the band index.
            int idx  = horizontal ? y : x;
            bool even = (idx / stripeWidth) % 2 == 0;
            tex.at(x, y) = even ? c1 : c2;
        }
    }
    return tex;
}

// ============================================================
//  perlinNoise
// ============================================================

Texture TextureGenerator::perlinNoise(int w, int h, uint32_t seed,
                                       int octaves, float scale, Color tint) {
    Texture tex;
    tex.resize(w, h);
    PerlinNoise noise(seed);

    for (int y = 0; y < h; ++y) {
        for (int x = 0; x < w; ++x) {
            // Divide pixel position by scale so larger scale = bigger features.
            float nx = static_cast<float>(x) / scale;
            float ny = static_cast<float>(y) / scale;

            // Get fBm noise value in [-1, 1].
            float v = noise.octaveNoise2D(nx, ny, octaves, 0.5f);

            // Remap to [0, 1] then clamp for safety.
            float t = (v + 1.0f) * 0.5f;
            t = std::max(0.0f, std::min(1.0f, t));

            // Multiply tint colour by the brightness t.
            tex.at(x, y) = {
                static_cast<uint8_t>(tint.r * t),
                static_cast<uint8_t>(tint.g * t),
                static_cast<uint8_t>(tint.b * t),
                255
            };
        }
    }
    return tex;
}

// ============================================================
//  cellular
// ============================================================

Texture TextureGenerator::cellular(int w, int h, uint32_t seed,
                                    float scale, Color c1, Color c2) {
    Texture tex;
    tex.resize(w, h);
    PerlinNoise noise(seed);

    for (int y = 0; y < h; ++y) {
        for (int x = 0; x < w; ++x) {
            float nx = static_cast<float>(x) / scale;
            float ny = static_cast<float>(y) / scale;

            // Cellular noise returns distance [0,1] to nearest feature point.
            float d = noise.cellular2D(nx, ny);
            d = std::max(0.0f, std::min(1.0f, d));

            // Map distance to a colour blend: c1 near feature, c2 far away.
            tex.at(x, y) = lerpColor(d, c1, c2);
        }
    }
    return tex;
}

// ============================================================
//  gradient
// ============================================================

Texture TextureGenerator::gradient(int w, int h, Color c1, Color c2, float angleDegrees) {
    Texture tex;
    tex.resize(w, h);

    // Convert angle to a direction vector.
    float rad = angleDegrees * 3.14159265f / 180.0f;
    float dx  = std::cos(rad);
    float dy  = std::sin(rad);

    // Centre of image used as the origin for projection.
    float cx = w * 0.5f;
    float cy = h * 0.5f;

    // Maximum projection distance along the chosen direction (half the projected span).
    float maxProj = std::abs(dx) * w * 0.5f + std::abs(dy) * h * 0.5f;
    if (maxProj < 1e-6f) maxProj = 1.0f; // guard divide-by-zero

    for (int y = 0; y < h; ++y) {
        for (int x = 0; x < w; ++x) {
            // Project (x,y) offset from centre onto the gradient direction.
            float proj = (x - cx) * dx + (y - cy) * dy;
            // Map from [-maxProj, maxProj] to [0, 1].
            float t = (proj / maxProj) * 0.5f + 0.5f;
            t = std::max(0.0f, std::min(1.0f, t));
            tex.at(x, y) = lerpColor(t, c1, c2);
        }
    }
    return tex;
}

// ============================================================
//  radialGradient
// ============================================================

Texture TextureGenerator::radialGradient(int w, int h, Color innerColor, Color outerColor) {
    Texture tex;
    tex.resize(w, h);

    float cx   = w * 0.5f;
    float cy   = h * 0.5f;
    // Normalise by the half-diagonal so corners reach t=1.
    float maxR = std::sqrt(cx * cx + cy * cy);
    if (maxR < 1e-6f) maxR = 1.0f;

    for (int y = 0; y < h; ++y) {
        for (int x = 0; x < w; ++x) {
            float ddx = x - cx;
            float ddy = y - cy;
            float r   = std::sqrt(ddx * ddx + ddy * ddy) / maxR;
            r = std::max(0.0f, std::min(1.0f, r));
            // t=0 at centre -> innerColor; t=1 at corner -> outerColor.
            tex.at(x, y) = lerpColor(r, innerColor, outerColor);
        }
    }
    return tex;
}

// ============================================================
//  normalMapFromHeight
// ============================================================

Texture TextureGenerator::normalMapFromHeight(const Texture& hm, float strength) {
    Texture tex;
    tex.resize(hm.width, hm.height);
    int w = hm.width;
    int h = hm.height;

    // Helper lambda: sample greyscale height at (x,y), clamped to image bounds.
    auto getH = [&](int x, int y) -> float {
        x = std::max(0, std::min(w - 1, x));
        y = std::max(0, std::min(h - 1, y));
        const Color& c = hm.at(x, y);
        // Average the RGB channels for a greyscale luminance value in [0,1].
        return (static_cast<float>(c.r) + c.g + c.b) / (3.0f * 255.0f);
    };

    for (int y = 0; y < h; ++y) {
        for (int x = 0; x < w; ++x) {
            // 3x3 Sobel filter to estimate the height gradient.
            // Sobel X kernel: [-1 0 +1 / -2 0 +2 / -1 0 +1]
            float dX = (getH(x+1,y-1) + 2.0f*getH(x+1,y) + getH(x+1,y+1))
                     - (getH(x-1,y-1) + 2.0f*getH(x-1,y) + getH(x-1,y+1));
            // Sobel Y kernel: [-1 -2 -1 / 0 0 0 / +1 +2 +1]
            float dY = (getH(x-1,y+1) + 2.0f*getH(x,y+1) + getH(x+1,y+1))
                     - (getH(x-1,y-1) + 2.0f*getH(x,y-1) + getH(x+1,y-1));

            // Build the surface normal: the height gradient forms the XY components;
            // the Z component points upward (away from the surface).
            float nx = -dX * strength;
            float ny = -dY * strength;
            float nz = 1.0f;

            // Normalise to unit length.
            float len = std::sqrt(nx*nx + ny*ny + nz*nz);
            if (len < 1e-6f) len = 1.0f;
            nx /= len; ny /= len; nz /= len;

            // Encode in RGB: map [-1,1] -> [0,255]. Z stays in [0,1] -> [0,255].
            tex.at(x, y) = {
                static_cast<uint8_t>((nx * 0.5f + 0.5f) * 255.0f),
                static_cast<uint8_t>((ny * 0.5f + 0.5f) * 255.0f),
                static_cast<uint8_t>((nz * 0.5f + 0.5f) * 255.0f),
                255
            };
        }
    }
    return tex;
}

// ============================================================
//  spriteSheet
// ============================================================

Texture TextureGenerator::spriteSheet(int w, int h, const Texture& tile,
                                       int tileW, int tileH) {
    Texture tex;
    tex.resize(w, h);

    for (int y = 0; y < h; ++y) {
        for (int x = 0; x < w; ++x) {
            // Determine position within the repeating tile region (modulo wrap).
            // Then scale to the tile texture's actual pixel dimensions.
            int tx = (x % tileW) * tile.width  / tileW;
            int ty = (y % tileH) * tile.height / tileH;

            // Clamp to valid tile pixel range to avoid out-of-bounds access.
            tx = std::max(0, std::min(tile.width  - 1, tx));
            ty = std::max(0, std::min(tile.height - 1, ty));

            tex.at(x, y) = tile.at(tx, ty);
        }
    }
    return tex;
}
