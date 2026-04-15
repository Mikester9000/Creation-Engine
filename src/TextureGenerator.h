/**
 * TextureGenerator.h - Procedural texture generation for the Creation Engine.
 *
 * This module provides a collection of static factory methods for generating
 * common procedural textures. Each method returns a Texture object (a flat
 * RGBA pixel array) that can be saved to disk via AssetIO::savePNG().
 *
 * Educational note: All textures are generated purely in software (CPU-side).
 * In a real engine you would upload these to the GPU as OpenGL/Vulkan textures.
 * Understanding CPU-side generation first makes GPU approaches easier to learn.
 */

#pragma once
#include <vector>
#include <cstdint>
#include "Noise.h"

// ============================================================
//  Color - 32-bit RGBA colour
// ============================================================

/**
 * Color holds a single pixel's red, green, blue, and alpha (opacity) channels.
 * Each channel is an unsigned 8-bit integer in the range [0, 255].
 *
 * Examples:
 *   Color{255,   0,   0, 255}  -> opaque red
 *   Color{  0, 128,   0, 128}  -> semi-transparent green
 *   Color{255, 255, 255,   0}  -> fully transparent white
 */
struct Color {
    uint8_t r = 0;   // Red   channel (0-255)
    uint8_t g = 0;   // Green channel (0-255)
    uint8_t b = 0;   // Blue  channel (0-255)
    uint8_t a = 255; // Alpha channel (0 = transparent, 255 = opaque)
};

// ============================================================
//  Texture - 2D RGBA pixel grid
// ============================================================

/**
 * Texture stores a rectangular grid of Color pixels in row-major order.
 *
 * Pixel layout: pixels[y * width + x] gives the color at column x, row y.
 *
 * (0,0) is the top-left corner; x increases rightward; y increases downward.
 * This matches the convention used by stb_image / most image formats.
 */
struct Texture {
    int width  = 0;            // Width  in pixels
    int height = 0;            // Height in pixels
    std::vector<Color> pixels; // Flat pixel array, row-major

    /** Helper: return pixel reference at (x, y). No bounds checking. */
    Color&       at(int x, int y)       { return pixels[y * width + x]; }
    const Color& at(int x, int y) const { return pixels[y * width + x]; }

    /** Allocate a blank (all-zero alpha=255) pixel array for given dimensions. */
    void resize(int w, int h) {
        width = w; height = h;
        pixels.assign(w * h, Color{0, 0, 0, 255});
    }
};

// ============================================================
//  TextureGenerator
// ============================================================

/**
 * TextureGenerator - Static factory for common procedural textures.
 *
 * All methods are static - there is no state. Call them like:
 *   Texture t = TextureGenerator::checkerboard(64, 64, white, black, 8);
 */
class TextureGenerator {
public:
    // -----------------------------------------------------------
    // Solid colour fill
    // -----------------------------------------------------------
    /**
     * solidColor - Create a single-colour texture.
     * Every pixel is set to the given colour. Useful as a base layer or
     * for testing the asset pipeline.
     */
    static Texture solidColor(int w, int h, Color c);

    // -----------------------------------------------------------
    // Checkerboard pattern
    // -----------------------------------------------------------
    /**
     * checkerboard - Generate an alternating two-colour grid.
     * @param cellSize  Side length of each square tile in pixels.
     *
     * The pattern is computed by checking whether (x/cellSize + y/cellSize)
     * is even or odd, then selecting colour c1 or c2 accordingly.
     */
    static Texture checkerboard(int w, int h, Color c1, Color c2, int cellSize);

    // -----------------------------------------------------------
    // Stripe pattern
    // -----------------------------------------------------------
    /**
     * stripes - Alternating coloured bands.
     * @param stripeWidth  Width (or height) of each band in pixels.
     * @param horizontal   If true, bands run horizontally; otherwise vertically.
     */
    static Texture stripes(int w, int h, Color c1, Color c2, int stripeWidth, bool horizontal);

    // -----------------------------------------------------------
    // Perlin noise texture
    // -----------------------------------------------------------
    /**
     * perlinNoise - Generate a texture from fractal Brownian motion noise.
     *
     * The raw noise value in [-1,1] is mapped to [0,1] and then used to
     * tint a colour. Setting tint to white gives a greyscale heightmap.
     *
     * @param scale    Divides pixel coordinates; larger = bigger features.
     * @param tint     Colour multiplied by the noise brightness.
     */
    static Texture perlinNoise(int w, int h, uint32_t seed, int octaves, float scale, Color tint);

    // -----------------------------------------------------------
    // Cellular / Worley noise texture
    // -----------------------------------------------------------
    /**
     * cellular - Generate a Voronoi/cellular noise texture.
     * Near a feature point the pixel is c1; at maximum distance it is c2.
     *
     * @param scale  Controls the density of feature points (larger = fewer cells).
     */
    static Texture cellular(int w, int h, uint32_t seed, float scale, Color c1, Color c2);

    // -----------------------------------------------------------
    // Linear gradient
    // -----------------------------------------------------------
    /**
     * gradient - Smooth colour gradient along a given direction.
     * @param angleDegrees  0 = left->right, 90 = top->bottom.
     *
     * For each pixel, the normalised projection of (x,y) onto the gradient
     * axis is used to interpolate between c1 and c2.
     */
    static Texture gradient(int w, int h, Color c1, Color c2, float angleDegrees);

    // -----------------------------------------------------------
    // Radial gradient
    // -----------------------------------------------------------
    /**
     * radialGradient - Circular gradient emanating from the centre.
     * innerColor appears at the centre; outerColor at the corners.
     */
    static Texture radialGradient(int w, int h, Color innerColor, Color outerColor);

    // -----------------------------------------------------------
    // Normal map from height map
    // -----------------------------------------------------------
    /**
     * normalMapFromHeight - Derive a tangent-space normal map from a greyscale
     * height map texture using a Sobel filter.
     *
     * Convention (same as most game engines):
     *   R = normal.x mapped from [-1,1] to [0,255]
     *   G = normal.y mapped from [-1,1] to [0,255]
     *   B = normal.z mapped from [ 0,1] to [0,255]  (always positive/upward)
     *
     * @param strength  Exaggerates the surface bumps; typical range 1-10.
     */
    static Texture normalMapFromHeight(const Texture& heightMap, float strength);

    // -----------------------------------------------------------
    // Sprite sheet / tile-fill
    // -----------------------------------------------------------
    /**
     * spriteSheet - Tile a smaller sub-texture across a larger canvas.
     * @param tile   The tile texture to repeat.
     * @param tileW  Width  of each tile region in the output.
     * @param tileH  Height of each tile region in the output.
     */
    static Texture spriteSheet(int w, int h, const Texture& tile, int tileW, int tileH);

private:
    /** Lerp a single colour channel between a and b by t in [0,1] */
    static uint8_t lerpChannel(float t, uint8_t a, uint8_t b);

    /** Linearly interpolate between two Colors */
    static Color lerpColor(float t, Color c1, Color c2);
};
