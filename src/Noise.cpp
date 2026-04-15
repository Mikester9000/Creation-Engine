/**
 * Noise.cpp - Implementation of procedural noise algorithms.
 *
 * This file implements the PerlinNoise class declared in Noise.h.
 * Reading through this file will show you exactly how each algorithm works
 * step by step, with comments explaining the math at each stage.
 */

#include "Noise.h"
#include <cmath>
#include <numeric>
#include <algorithm>
#include <random>

// ============================================================
//  Constructor
// ============================================================

PerlinNoise::PerlinNoise(uint32_t seed) {
    // Step 1: Create a base permutation array containing 0..255
    std::array<int, 256> base;
    std::iota(base.begin(), base.end(), 0);   // fill with 0,1,2,...,255

    // Step 2: Shuffle it using the seed for deterministic randomness.
    //         std::mt19937 is the Mersenne Twister PRNG - a high-quality
    //         generator well-suited for games and simulations.
    std::mt19937 rng(seed);
    std::shuffle(base.begin(), base.end(), rng);

    // Step 3: Double the table to avoid modulo operations during lookup.
    //         p_[i] and p_[i+256] hold the same value, allowing us to
    //         index p_[X+1] without wrapping manually.
    for (int i = 0; i < 256; ++i) {
        p_[i]       = base[i];
        p_[i + 256] = base[i];
    }
}

// ============================================================
//  Private helpers
// ============================================================

float PerlinNoise::fade(float t) {
    // Ken Perlin's improved fade function: 6t^5 - 15t^4 + 10t^3
    // This provides C2 continuity at grid boundaries, eliminating
    // the visual "blocky" artefacts of linear interpolation.
    // The derivative at t=0 and t=1 is zero, so transitions are smooth.
    return t * t * t * (t * (t * 6.0f - 15.0f) + 10.0f);
}

float PerlinNoise::lerp(float t, float a, float b) {
    // Standard linear interpolation: move t fraction of the way from a to b.
    return a + t * (b - a);
}

float PerlinNoise::grad2D(int hash, float x, float y) {
    // Use the lowest 3 bits of hash to select one of 8 gradient directions.
    // These are the 8 possible (+-1, +-1) diagonal and axis-aligned unit vectors in 2D.
    // Taking the dot product with (x,y) gives a smooth contribution from each grid corner.
    switch (hash & 7) {
        case 0: return  x + y;    //  (1, 1)
        case 1: return -x + y;    // (-1, 1)
        case 2: return  x - y;    //  (1,-1)
        case 3: return -x - y;    // (-1,-1)
        case 4: return  x;        //  (1, 0)
        case 5: return -x;        // (-1, 0)
        case 6: return  y;        //  (0, 1)
        case 7: return -y;        //  (0,-1)
        default: return 0.0f;     // unreachable
    }
}

float PerlinNoise::hash2D(int ix, int iy) const {
    // Produce a pseudo-random float in [0,1) from an integer grid cell (ix,iy).
    // We chain through the permutation table twice to mix x and y coordinates.
    // The & 255 ensures we stay within the table bounds.
    int h = p_[(p_[ix & 255] + iy) & 255];
    return static_cast<float>(h) / 255.0f;
}

// ============================================================
//  noise2D
// ============================================================

float PerlinNoise::noise2D(float x, float y) const {
    // --- Step 1: Find the integer cell that contains (x,y) ---
    // We floor the coordinates to find the lower-left corner of the grid cell.
    // The & 255 wraps coordinates into [0,255] so the permutation table repeats.
    int X = static_cast<int>(std::floor(x)) & 255;
    int Y = static_cast<int>(std::floor(y)) & 255;

    // --- Step 2: Compute the fractional position inside the cell ---
    float xf = x - std::floor(x);   // 0.0 <= xf < 1.0
    float yf = y - std::floor(y);   // 0.0 <= yf < 1.0

    // --- Step 3: Apply the fade curve to the fractional parts ---
    // This smooths the interpolation weights, producing the characteristic
    // "cloud-like" appearance of Perlin noise instead of a blocky look.
    float u = fade(xf);
    float v = fade(yf);

    // --- Step 4: Compute hashes for the 4 corners of the cell ---
    //   A references corner (X,   Y  )  bottom-left
    //   B references corner (X+1, Y  )  bottom-right
    //   A+1 references      (X,   Y+1)  top-left
    //   B+1 references      (X+1, Y+1)  top-right
    int A = p_[X]     + Y;
    int B = p_[X + 1] + Y;

    // --- Step 5: Compute gradient contributions from each corner ---
    // Each corner contributes based on its gradient direction and the vector
    // pointing from that corner toward the sample point (xf, yf).
    float g00 = grad2D(p_[A],     xf,        yf       );  // bottom-left
    float g10 = grad2D(p_[B],     xf - 1.0f, yf       );  // bottom-right
    float g01 = grad2D(p_[A + 1], xf,        yf - 1.0f);  // top-left
    float g11 = grad2D(p_[B + 1], xf - 1.0f, yf - 1.0f);  // top-right

    // --- Step 6: Bilinear interpolation using faded weights ---
    // First interpolate along x at the bottom edge and the top edge,
    // then interpolate vertically between those two results.
    float x1 = lerp(u, g00, g10);  // bottom edge blend
    float x2 = lerp(u, g01, g11);  // top edge blend
    return lerp(v, x1, x2);        // final vertical blend
}

// ============================================================
//  octaveNoise2D (Fractal Brownian Motion)
// ============================================================

float PerlinNoise::octaveNoise2D(float x, float y, int octaves, float persistence) const {
    float total     = 0.0f;
    float frequency = 1.0f;   // doubles each octave to add higher-frequency detail
    float amplitude = 1.0f;   // controlled by persistence - decreases each octave
    float maxValue  = 0.0f;   // sum of all amplitudes, used to normalise the result

    for (int i = 0; i < octaves; ++i) {
        // Sample noise at the current frequency and weight by current amplitude
        total += noise2D(x * frequency, y * frequency) * amplitude;

        // Track the maximum possible output for normalisation
        maxValue += amplitude;

        // Each octave: half the amplitude (persistence=0.5 is typical)
        amplitude *= persistence;

        // Each octave: double the frequency (add finer detail)
        frequency *= 2.0f;
    }

    // Normalise to approximately [-1, 1]
    return total / maxValue;
}

// ============================================================
//  cellular2D (Worley noise)
// ============================================================

float PerlinNoise::cellular2D(float x, float y) const {
    // --- Step 1: Find the integer cell containing (x,y) ---
    int ix = static_cast<int>(std::floor(x));
    int iy = static_cast<int>(std::floor(y));

    float minDist = 1e10f;  // start with a large sentinel value

    // --- Step 2: Search the 3x3 neighbourhood of cells ---
    // The nearest feature point must lie in the current cell or one of its
    // 8 neighbours (because each point is randomly placed within its own cell,
    // so points in adjacent cells can be closer than 1 unit away).
    for (int dy = -1; dy <= 1; ++dy) {
        for (int dx = -1; dx <= 1; ++dx) {
            int cx = ix + dx;
            int cy = iy + dy;

            // --- Step 3: Place a random feature point inside this cell ---
            // hash2D gives a consistent pseudo-random offset in [0,1) for each cell.
            // We need two independent values for x and y, so we use different
            // input permutations (offset by 17 and 31 to break correlations).
            float fx = static_cast<float>(cx) + hash2D(cx,      cy     );
            float fy = static_cast<float>(cy) + hash2D(cy + 17, cx + 31);

            // --- Step 4: Euclidean distance to this feature point ---
            float ddx  = x - fx;
            float ddy  = y - fy;
            float dist = std::sqrt(ddx * ddx + ddy * ddy);

            if (dist < minDist) minDist = dist;
        }
    }

    // Clamp result to [0, 1]; maximum possible distance in this 3x3 search is ~sqrt(2)
    return std::min(minDist, 1.0f);
}
