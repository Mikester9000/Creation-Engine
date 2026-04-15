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
// Constants
// =============================================================================

/// Per-octave seed stride — each noise octave uses a different seed to
/// prevent correlation between frequency layers.
constexpr uint32_t OCTAVE_SEED_STRIDE = 1000u;

// Default fBm parameters, exposed as constants for easy lesson-plan tuning.
constexpr int   FBM_DEFAULT_OCTAVES     = 4;
constexpr float FBM_DEFAULT_LACUNARITY  = 2.0f;   ///< Frequency multiplier per octave.
constexpr float FBM_DEFAULT_PERSISTENCE = 0.5f;   ///< Amplitude multiplier per octave.

// =============================================================================
// Section 1 — Hash Function
// =============================================================================

/**
 * @brief Mix two integers and a seed into a single pseudo-random 32-bit value.
 *
 * TEACHING NOTE — Integer Hash
 * Uses a sequence of XOR-shifts and multiplications to scatter bits
 * across the full 32-bit range. The multipliers (1619, 31337, 6791) are
 * large primes chosen to maximise bit avalanche (changing one input bit
 * changes roughly half the output bits). NOT cryptographically secure, but
 * fast and adequate for visual procedural generation.
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
    // XOR-shift finalisation — distributes any remaining bias.
    h ^= (h >> 16);
    h *= 0x45d9f3bu;
    h ^= (h >> 16);
    return h;
}

/**
 * @brief Convert a hash to a float in [0, 1].
 *
 * Divide by the maximum uint32 value so the full integer range maps to
 * the full floating-point unit interval.
 *
 * @param h  Raw hash value.
 * @return   Float in the range [0.0, 1.0].
 */
inline float hashToFloat(uint32_t h)
{
    return static_cast<float>(h) / static_cast<float>(0xFFFFFFFFu);
}

// =============================================================================
// Section 2 — Interpolation
// =============================================================================

/**
 * @brief Smoothstep (cubic Hermite) interpolation: smoother than linear.
 *
 * TEACHING NOTE — Smoothstep vs Linear
 * Linear interpolation (lerp) produces a grid-like blocky pattern because
 * the derivative is discontinuous at cell boundaries. Smoothstep (3t² - 2t³)
 * makes the first derivative zero at t=0 and t=1, so adjacent cells blend
 * seamlessly into each other. This eliminates the "blocky" look.
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
 *   1. Decompose (fx, fy) into integer cell (cellX, cellY) and fractional
 *      (fracX, fracY).
 *   2. Hash all four corners of the cell to [0,1] values.
 *   3. Bilinearly interpolate using smoothstep-remapped fractions.
 *
 * @param fx    Continuous X coordinate.
 * @param fy    Continuous Y coordinate.
 * @param seed  Seed for this noise layer.
 * @return      Noise value in [0, 1].
 */
inline float valueNoise(float fx, float fy, uint32_t seed)
{
    const int32_t cellX = static_cast<int32_t>(std::floor(fx));
    const int32_t cellY = static_cast<int32_t>(std::floor(fy));

    // Fractional position within the cell, smoothed for seamless blending.
    const float fracX = smoothstep(fx - static_cast<float>(cellX));
    const float fracY = smoothstep(fy - static_cast<float>(cellY));

    // Sample the four grid corners.
    const float v00 = hashToFloat(hash2(cellX,     cellY,     seed));
    const float v10 = hashToFloat(hash2(cellX + 1, cellY,     seed));
    const float v01 = hashToFloat(hash2(cellX,     cellY + 1, seed));
    const float v11 = hashToFloat(hash2(cellX + 1, cellY + 1, seed));

    // Bilinear interpolation: X first, then Y.
    return lerp(lerp(v00, v10, fracX),
                lerp(v01, v11, fracX),
                fracY);
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
 *   result = Σᵢ (persistenceⁱ × valueNoise(lacunarityⁱ × x, y, seed + i))
 *
 * The output is normalised to approximately [0, 1] by dividing by the
 * sum of amplitudes (the geometric series sum).
 *
 * @param fx          X coordinate (normalised world-space units).
 * @param fy          Y coordinate.
 * @param seed        Differentiates independent noise fields.
 * @param octaves     Number of frequency layers (2–8 is typical).
 * @param lacunarity  Frequency multiplier per octave (default 2.0).
 * @param persistence Amplitude multiplier per octave (default 0.5).
 * @return            Noise value approximately in [0, 1].
 */
inline float fbm(float    fx,
                 float    fy,
                 uint32_t seed,
                 int      octaves     = FBM_DEFAULT_OCTAVES,
                 float    lacunarity  = FBM_DEFAULT_LACUNARITY,
                 float    persistence = FBM_DEFAULT_PERSISTENCE)
{
    float value    = 0.0f;
    float amplitude = 1.0f;
    float frequency = 1.0f;
    float maxValue  = 0.0f;   // Sum of amplitudes; used to normalise output.

    for (int i = 0; i < octaves; ++i) {
        value    += amplitude * valueNoise(fx * frequency, fy * frequency,
                                           seed + static_cast<uint32_t>(i) * OCTAVE_SEED_STRIDE);
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
 * By computing (1 - |2n - 1|) instead of n, smooth dome peaks become sharp
 * ridges. Used for mountain ranges and rocky surfaces in FFXV-style landscapes.
 *
 * @param fx      X coordinate.
 * @param fy      Y coordinate.
 * @param seed    Seed.
 * @param octaves Number of octaves.
 * @return        Ridged noise value in [0, 1].
 */
inline float ridgedFbm(float fx, float fy, uint32_t seed,
                       int octaves = FBM_DEFAULT_OCTAVES)
{
    float value    = 0.0f;
    float amplitude = 1.0f;
    float frequency = 1.0f;
    float maxValue  = 0.0f;

    for (int i = 0; i < octaves; ++i) {
        float n = valueNoise(fx * frequency, fy * frequency,
                             seed + static_cast<uint32_t>(i) * OCTAVE_SEED_STRIDE);
        // Invert absolute deviation from 0.5 to create ridges at peaks.
        n = 1.0f - std::abs(2.0f * n - 1.0f);
        value    += amplitude * n;
        maxValue += amplitude;
        amplitude *= FBM_DEFAULT_PERSISTENCE;
        frequency *= FBM_DEFAULT_LACUNARITY;
    }

    return value / maxValue;
}

} // namespace ce
