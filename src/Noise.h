/**
 * Noise.h - Procedural noise generators for the Creation Engine
 *
 * This module provides several types of procedural noise:
 *  - Perlin noise (classic gradient noise by Ken Perlin, improved 2002)
 *  - Fractal Brownian Motion (fBm) via octave stacking
 *  - Worley / Cellular noise (distance to nearest feature point)
 *
 * These noise functions are the core building blocks for procedural
 * texture generation, terrain heightmaps, and map feature placement.
 *
 * Educational note: Noise functions are deterministic (same seed = same output)
 * but produce results that look organic and random. This is critical for
 * reproducible procedural content in games.
 */

#pragma once
#include <cstdint>
#include <array>

/**
 * PerlinNoise - Ken Perlin's classic gradient noise algorithm (1985, improved 2002).
 *
 * Algorithm summary:
 *  1. A permutation table maps each integer grid coordinate to a pseudo-random
 *     gradient direction.
 *  2. The input point is located in a unit grid cell; dot products are computed
 *     between the cell-corner gradients and the vectors from those corners to the
 *     point.
 *  3. The four dot products are smoothly interpolated using a fade curve
 *     (6t^5 - 15t^4 + 10t^3) which gives C2 continuity (no visible seams).
 */
class PerlinNoise {
public:
    /**
     * Constructor: seeds the permutation table.
     * @param seed  32-bit seed value; different seeds produce entirely different noise fields.
     */
    explicit PerlinNoise(uint32_t seed = 0);

    /**
     * noise2D - Sample Perlin noise at a 2D coordinate.
     * @param x  Horizontal coordinate (float, any range)
     * @param y  Vertical coordinate   (float, any range)
     * @return   Value in the approximate range [-1, 1]
     *
     * Note: at integer coordinates the noise is always 0 (gradient dot product = 0).
     * Scale the inputs (e.g. x/64.0f) to control the feature size.
     */
    float noise2D(float x, float y) const;

    /**
     * octaveNoise2D - Fractal Brownian Motion: sum multiple octaves of noise.
     *
     * Each successive octave doubles the frequency and halves the amplitude
     * (multiplied by persistence). This stacking creates detail at multiple
     * scales, mimicking natural phenomena like terrain and clouds.
     *
     * @param x            Horizontal coordinate
     * @param y            Vertical coordinate
     * @param octaves      Number of noise layers to combine (typically 4-8)
     * @param persistence  How quickly amplitude decreases (0-1; 0.5 is typical)
     * @return             Normalised value in approximately [-1, 1]
     */
    float octaveNoise2D(float x, float y, int octaves, float persistence) const;

    /**
     * cellular2D - Worley (cellular) noise: returns distance to the nearest
     * random feature point in a tiled grid.
     *
     * The result looks like a Voronoi diagram - useful for rocky, bubbly, or
     * biological textures.
     *
     * @param x   Horizontal coordinate
     * @param y   Vertical coordinate
     * @return    Distance to nearest feature point, roughly in [0, 1]
     */
    float cellular2D(float x, float y) const;

private:
    /**
     * p_ is the doubled permutation table (512 entries) containing integers
     * 0-255 in a seeded random order. Doubling avoids out-of-bounds access when
     * adding the second coordinate index.
     */
    std::array<int, 512> p_;

    // ---------- helper functions ----------

    /** Smooth fade curve: 6t^5 - 15t^4 + 10t^3 (Perlin's improved formula) */
    static float fade(float t);

    /** Linear interpolation between a and b by t in [0,1] */
    static float lerp(float t, float a, float b);

    /**
     * grad2D - Compute the dot product of a pseudo-random gradient vector
     * (chosen by hash) with the vector (x, y).
     * The 8 possible gradients are the 8 diagonal/axis-aligned unit vectors.
     */
    static float grad2D(int hash, float x, float y);

    /**
     * hash2D - Return a pseudo-random float in [0,1) for an integer grid cell.
     * Used by cellular2D to place a random feature point inside each cell.
     */
    float hash2D(int ix, int iy) const;
};
