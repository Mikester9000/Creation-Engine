/**
 * @file Noise.hpp
 * @brief Seeded deterministic value noise for procedural texture/map generation.
 *
 * =============================================================================
 * TEACHING NOTE — Procedural Noise
 * =============================================================================
 *
 * Procedural noise is a mathematical function that maps coordinates to smooth,
 * pseudo-random values. It is the foundation of procedural content generation
 * in games (terrain, textures, cave systems, weather, etc.).
 *
 * TYPES OF NOISE USED HERE
 * ─────────────────────────
 * 1. Value Noise
 *    - Hash each integer grid point to a pseudo-random value in [0, 1].
 *    - Bilinear interpolation between adjacent grid values for smoothness.
 *    - Result: organic-looking patterns with no visible grid seams.
 *
 * 2. Fractional Brownian Motion (fBm)
 *    - Layer multiple octaves of value noise at increasing frequencies
 *      and decreasing amplitudes (lacunarity ×2, persistence ×0.5).
 *    - Produces natural "rough" surfaces (mountain ridges, stone surfaces).
 *    - The number of octaves controls detail level (more = finer detail).
 *
 * DETERMINISM
 * ────────────
 * The seed parameter ensures that identical inputs always produce identical
 * outputs. This is critical for a save/reload pipeline: generating a texture
 * with seed 42 tomorrow gives the same pixels as today.
 *
 * LESSON EXERCISES
 * ─────────────────
 * 1. Change the octave count from 4 to 1 — observe the texture becomes
 *    blobby and low-frequency.
 * 2. Change persistence from 0.5 to 0.8 — higher-frequency octaves get
 *    more weight, producing rougher, noisier surfaces.
 * 3. Change lacunarity from 2.0 to 3.0 — octave frequency jumps faster,
 *    creating finer detail at smaller scales.
 *
 * @author  Creation Engine Project
 * @version 1.0
 */

#pragma once

#include <cstdint>
#include <cmath>

namespace ce {

// =============================================================================
// Section 1 — Hash Function
// =============================================================================

/**
 * @brief Mix two integers and a seed into a single pseudo-random 32-bit value.
 *
 * TEACHING NOTE — Integer Hash
 * Uses a sequence of XOR-shifts and multiplications to scatter bits
 * across the full 32-bit range. This is NOT cryptographically secure,
 * but it is fast and produces good visual randomness for procedural generation.
 *
 * @param x     Integer X coordinate.
 * @param y     Integer Y coordinate.
 * @param seed  Seed to differentiate noise instances.
 * @return      A pseudo-random 32-bit integer.
 */
inline uint32_t hash2(int32_t x, int32_t y, uint32_t seed)
{
    uint32_t h = static_cast<uint32_t>(x) * 1619u
               ^ static_cast<uint32_t>(y) * 31337u
               ^ seed * 6791u;
    h ^= (h >> 16);
    h *= 0x45d9f3b;
    h ^= (h >> 16);
    return h;
}

/**
 * @brief Convert a hash to a float in [0, 1].
 *
 * @param h  Raw hash value.
 * @return   Float in the range [0.0, 1.0].
 */
inline float hashToFloat(uint32_t h)
{
    // Take the upper 23 bits (mantissa of float), form a number in [1,2),
    // then subtract 1 to get [0, 1).
    // A simpler approach: divide by max uint32 value.
    return static_cast<float>(h) / static_cast<float>(0xFFFFFFFFu);
}

// =============================================================================
// Section 2 — Interpolation
// =============================================================================

/**
 * @brief Smoothstep (cubic Hermite) interpolation: smoother than linear.
 *
 * TEACHING NOTE — Smoothstep vs Linear
 * Linear interpolation produces a grid-like blocky pattern because the
 * derivative is discontinuous at cell boundaries. Smoothstep (3t² - 2t³)
 * ensures the first derivative is zero at t=0 and t=1, removing the
 * "blocky" look.
 *
 * @param t  Parameter in [0, 1].
 * @return   Smoothly remapped parameter.
 */
inline float smoothstep(float t)
{
    return t * t * (3.0f - 2.0f * t);
}

/**
 * @brief Linear interpolation between a and b by t.
 *
 * @param a  Start value.
 * @param b  End value.
 * @param t  Interpolation factor in [0, 1].
 * @return   a + t*(b - a)
 */
inline float lerp(float a, float b, float t)
{
    return a + t * (b - a);
}

// =============================================================================
// Section 3 — Value Noise
// =============================================================================

/**
 * @brief Sample 2D value noise at a continuous coordinate.
 *
 * Algorithm:
 *   1. Decompose (fx, fy) into integer cell (ix, iy) and fractional (tx, ty).
 *   2. Hash all four corners of the cell to [0,1] values.
 *   3. Bilinearly interpolate using smoothstep-remapped tx, ty.
 *
 * @param fx    Continuous X coordinate.
 * @param fy    Continuous Y coordinate.
 * @param seed  Seed for this noise layer.
 * @return      Noise value in [0, 1].
 */
inline float valueNoise(float fx, float fy, uint32_t seed)
{
    // Integer cell coordinates
    int32_t ix = static_cast<int32_t>(std::floor(fx));
    int32_t iy = static_cast<int32_t>(std::floor(fy));

    // Fractional position within cell
    float tx = fx - static_cast<float>(ix);
    float ty = fy - static_cast<float>(iy);

    // Smooth the fractional part
    float ux = smoothstep(tx);
    float uy = smoothstep(ty);

    // Sample the four corners of the cell
    float v00 = hashToFloat(hash2(ix,     iy,     seed));
    float v10 = hashToFloat(hash2(ix + 1, iy,     seed));
    float v01 = hashToFloat(hash2(ix,     iy + 1, seed));
    float v11 = hashToFloat(hash2(ix + 1, iy + 1, seed));

    // Bilinear interpolation
    float top    = lerp(v00, v10, ux);
    float bottom = lerp(v01, v11, ux);
    return lerp(top, bottom, uy);
}

// =============================================================================
// Section 4 — Fractional Brownian Motion (fBm)
// =============================================================================

/**
 * @brief Multi-octave fractional Brownian motion noise.
 *
 * TEACHING NOTE — Octaves in Noise
 * Each octave doubles the frequency (lacunarity = 2.0) and halves the
 * amplitude (persistence = 0.5). The result is a sum of noise at different
 * scales, mimicking natural fractal patterns (mountains, clouds, stone).
 *
 *   result = Σ (amplitude^i * noise(frequency^i * x, frequency^i * y))
 *
 * The output is normalised to approximately [0, 1] by dividing by the
 * sum of amplitudes.
 *
 * @param fx         X coordinate (in world-space units, not pixel-space).
 * @param fy         Y coordinate.
 * @param seed       Seed differentiates independent noise fields.
 * @param octaves    Number of frequency layers (2–8 is typical).
 * @param lacunarity Frequency multiplier per octave (default 2.0).
 * @param persistence Amplitude multiplier per octave (default 0.5).
 * @return           Noise value approximately in [0, 1].
 */
inline float fbm(float fx, float fy, uint32_t seed,
                 int   octaves     = 4,
                 float lacunarity  = 2.0f,
                 float persistence = 0.5f)
{
    float value     = 0.0f;
    float amplitude = 1.0f;
    float frequency = 1.0f;
    float maxValue  = 0.0f;  // Used for normalisation.

    for (int i = 0; i < octaves; ++i) {
        // Each octave uses a different seed offset to avoid correlation.
        value    += amplitude * valueNoise(fx * frequency,
                                           fy * frequency,
                                           seed + static_cast<uint32_t>(i * 1000));
        maxValue += amplitude;
        amplitude *= persistence;
        frequency *= lacunarity;
    }

    return value / maxValue;
}

/**
 * @brief Ridged multi-fractal noise — produces sharp mountain ridges.
 *
 * TEACHING NOTE — Ridged Noise
 * By inverting the absolute value of noise (1 - |2n - 1|), peaks
 * become sharp ridges instead of smooth domes. Used for mountain ranges
 * and rocky surfaces in FFXV-style landscapes.
 *
 * @param fx      X coordinate.
 * @param fy      Y coordinate.
 * @param seed    Seed.
 * @param octaves Number of octaves.
 * @return        Ridged noise value in [0, 1].
 */
inline float ridgedFbm(float fx, float fy, uint32_t seed, int octaves = 4)
{
    float value     = 0.0f;
    float amplitude = 1.0f;
    float frequency = 1.0f;
    float maxValue  = 0.0f;

    for (int i = 0; i < octaves; ++i) {
        float n = valueNoise(fx * frequency, fy * frequency,
                             seed + static_cast<uint32_t>(i * 1000));
        // Invert to create ridges
        n = 1.0f - std::abs(2.0f * n - 1.0f);
        value    += amplitude * n;
        maxValue += amplitude;
        amplitude *= 0.5f;
        frequency *= 2.0f;
    }

    return value / maxValue;
}

} // namespace ce
