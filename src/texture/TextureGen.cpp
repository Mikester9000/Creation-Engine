/**
 * @file TextureGen.cpp
 * @brief Implementation of the PBR-lite texture generator.
 *
 * =============================================================================
 * TEACHING NOTE — Generating Each PBR Channel
 * =============================================================================
 *
 * All six channels (albedo, normal, roughness, metallic, AO, emissive) derive
 * from the same underlying noise height field h(x,y). Using the same seed
 * with per-channel offsets ensures all maps "agree" about the surface:
 * a bump in the albedo map corresponds to a bump in the normal map, a rougher
 * region in the roughness map, etc.
 *
 * SEED OFFSETS (defined as constants below)
 * ──────────────────────────────────────────
 * Each channel uses a different seed offset to prevent two maps from being
 * correlated (i.e., identical). If they shared the exact same noise call
 * sequence they would produce redundant data.
 *
 * @author  Creation Engine Project
 * @version 1.0
 */

#include "texture/TextureGen.hpp"

#include <cmath>
#include <algorithm>

#include "util/Noise.hpp"
#include "util/PNGWriter.hpp"

namespace ce {

// =============================================================================
// Seed offsets per PBR channel
// =============================================================================
// Must be multiples of OCTAVE_SEED_STRIDE (1000) to avoid intra-octave
// collisions between channels.

constexpr uint32_t CHANNEL_SEED_ALBEDO    = 0u;
constexpr uint32_t CHANNEL_SEED_NORMAL    = 1000u;
constexpr uint32_t CHANNEL_SEED_ROUGHNESS = 2000u;
constexpr uint32_t CHANNEL_SEED_METALLIC  = 3000u;
constexpr uint32_t CHANNEL_SEED_AO        = 4000u;
constexpr uint32_t CHANNEL_SEED_EMISSIVE  = 5000u;

// =============================================================================
// Internal helpers
// =============================================================================

namespace {

/** @brief Clamp a float to [0, 1]. */
inline float clamp01(float v) { return std::max(0.0f, std::min(1.0f, v)); }

/** @brief Convert a [0,1] float to a uint8 [0,255]. */
inline uint8_t toU8(float v) { return static_cast<uint8_t>(clamp01(v) * 255.0f + 0.5f); }

/**
 * @brief Sample fBm noise at pixel (px, py) using the given scale and seed.
 *
 * This helper centralises the pixel-to-world-space conversion that all
 * channel generators share:
 *   worldX = pixelX / scale
 *   worldY = pixelY / scale
 *
 * @param px     Pixel X coordinate.
 * @param py     Pixel Y coordinate.
 * @param scale  Spatial scale (higher = lower frequency detail).
 * @param oct    Number of fBm octaves.
 * @param seed   Combined seed (base seed + channel offset).
 * @return       Noise value in [0, 1].
 */
inline float sampleNoise(int px, int py, float scale, int oct, uint32_t seed)
{
    return fbm(static_cast<float>(px) / scale,
               static_cast<float>(py) / scale,
               seed, oct);
}

// ─────────────────────────────────────────────────────────────────────────────
// Albedo generator
// ─────────────────────────────────────────────────────────────────────────────

/**
 * @brief Generate the albedo (base colour) PNG map.
 *
 * TEACHING NOTE — Albedo
 * The albedo is the raw surface colour under perfectly white, diffuse light.
 * We start from mat.baseColor and add noise-driven variation so identical
 * tiles don't look like cloned stamps. The tint range ±15% (0.85…1.15) is
 * small enough to preserve colour identity but large enough to prevent
 * repetition — similar to how FFXV stone tiles have subtle hue variation.
 */
std::vector<uint8_t> genAlbedo(const Material& mat,
                                int w, int h, float scale, int oct, uint32_t seed)
{
    // Tint variation: 0.85 at noise=0, 1.15 at noise=1 (±15% range).
    constexpr float TINT_MIN     = 0.85f;
    constexpr float TINT_RANGE   = 0.30f;

    std::vector<uint8_t> buf(static_cast<size_t>(w * h * 3));

    for (int y = 0; y < h; ++y) {
        for (int x = 0; x < w; ++x) {
            const float tint = TINT_MIN + TINT_RANGE * sampleNoise(x, y, scale, oct, seed);
            const size_t idx = static_cast<size_t>((y * w + x) * 3);
            buf[idx + 0] = toU8(mat.baseColor[0] * tint);
            buf[idx + 1] = toU8(mat.baseColor[1] * tint);
            buf[idx + 2] = toU8(mat.baseColor[2] * tint);
        }
    }
    return buf;
}

// ─────────────────────────────────────────────────────────────────────────────
// Normal map generator
// ─────────────────────────────────────────────────────────────────────────────

/**
 * @brief Generate a tangent-space normal map from a noise height field.
 *
 * TEACHING NOTE — Normal Maps
 * A normal map stores a per-pixel surface normal vector in tangent space
 * (Z = up from the surface, X/Y lie along the surface).
 *
 * We derive normals from a height field h(x,y) using central differences:
 *
 *   dh/dx ≈ (h(x+1, y) - h(x-1, y)) / 2
 *   dh/dy ≈ (h(x, y+1) - h(x, y-1)) / 2
 *
 * Cross-product of tangent vectors → normal (-dh/dx, -dh/dy, 1), normalised.
 * Encoding: map [-1,1] to [0,255] per channel.
 * A flat surface encodes as (128, 128, 255) — pointing straight up.
 *
 * @param strength  How pronounced the height variation is in the normal map.
 *                  Higher = more dramatic bumps.
 */
std::vector<uint8_t> genNormal(int w, int h, float scale, int oct, uint32_t seed,
                                float strength)
{
    std::vector<uint8_t> buf(static_cast<size_t>(w * h * 3));

    for (int y = 0; y < h; ++y) {
        for (int x = 0; x < w; ++x) {
            // Central differences using wrap-around for seamless tiling.
            const float dX = sampleNoise((x + 1) % w, y, scale, oct, seed)
                           - sampleNoise((x - 1 + w) % w, y, scale, oct, seed);
            const float dY = sampleNoise(x, (y + 1) % h, scale, oct, seed)
                           - sampleNoise(x, (y - 1 + h) % h, scale, oct, seed);

            float nx = -dX * strength;
            float ny = -dY * strength;
            float nz = 1.0f;
            const float len = std::sqrt(nx * nx + ny * ny + nz * nz);
            nx /= len;  ny /= len;  nz /= len;

            const size_t idx = static_cast<size_t>((y * w + x) * 3);
            buf[idx + 0] = toU8((nx + 1.0f) * 0.5f);
            buf[idx + 1] = toU8((ny + 1.0f) * 0.5f);
            buf[idx + 2] = toU8((nz + 1.0f) * 0.5f);
        }
    }
    return buf;
}

// ─────────────────────────────────────────────────────────────────────────────
// Grayscale channel (roughness, metallic) generator
// ─────────────────────────────────────────────────────────────────────────────

/**
 * @brief Generate a greyscale PBR channel map (roughness or metallic).
 *
 * The base scalar PBR value is shifted by noise-driven variation in
 * [base - variation, base + variation].
 *
 * @param base       Scalar PBR value from the material definition [0,1].
 * @param variation  Max noise-driven deviation from base (e.g., 0.12).
 */
std::vector<uint8_t> genGrayscale(float base, float variation,
                                   int w, int h, float scale, int oct, uint32_t seed)
{
    std::vector<uint8_t> buf(static_cast<size_t>(w * h));

    for (int y = 0; y < h; ++y) {
        for (int x = 0; x < w; ++x) {
            const float n = sampleNoise(x, y, scale, oct, seed);
            // Map noise [0,1] to variation range [-variation, +variation]
            const float v = base + variation * (n - 0.5f) * 2.0f;
            buf[static_cast<size_t>(y * w + x)] = toU8(v);
        }
    }
    return buf;
}

// ─────────────────────────────────────────────────────────────────────────────
// AO generator
// ─────────────────────────────────────────────────────────────────────────────

/**
 * @brief Generate an ambient occlusion map.
 *
 * TEACHING NOTE — Ambient Occlusion
 * AO simulates the tendency of concave areas to receive less ambient light.
 * We approximate this by inverting the noise: areas where noise is high
 * (raised bumps) receive full AO (bright=1.0), while recessed areas
 * (low noise) are darkened:
 *
 *   ao(x,y) = 1.0 - aoStrength * (1.0 - fbm(x,y))
 *
 * @param aoStrength  Darkness of the deepest crevice (e.g., 0.35 = 35% dark).
 */
std::vector<uint8_t> genAO(float aoStrength,
                            int w, int h, float scale, int oct, uint32_t seed)
{
    std::vector<uint8_t> buf(static_cast<size_t>(w * h));

    for (int y = 0; y < h; ++y) {
        for (int x = 0; x < w; ++x) {
            const float n  = sampleNoise(x, y, scale, oct, seed);
            const float ao = 1.0f - aoStrength * (1.0f - n);
            buf[static_cast<size_t>(y * w + x)] = toU8(ao);
        }
    }
    return buf;
}

// ─────────────────────────────────────────────────────────────────────────────
// Emissive generator
// ─────────────────────────────────────────────────────────────────────────────

/**
 * @brief Generate an emissive map (black for non-glowing materials).
 *
 * For emissive materials (lava, neon, fire) ridged noise concentrates the
 * glow into thin vein-like cracks that exceed an emission threshold.
 * The threshold (0.6) means only the brightest 40% of ridges emit light.
 */
std::vector<uint8_t> genEmissive(const Material& mat,
                                  int w, int h, float scale, int oct, uint32_t seed)
{
    constexpr float EMIT_THRESHOLD = 0.6f;
    constexpr float EMIT_RANGE     = 1.0f - EMIT_THRESHOLD;

    const bool hasEmission = (mat.emissive[0] + mat.emissive[1] + mat.emissive[2]) > 0.001f;

    std::vector<uint8_t> buf(static_cast<size_t>(w * h * 3), 0);
    if (!hasEmission) return buf;   // Early-out for non-emissive materials.

    for (int y = 0; y < h; ++y) {
        for (int x = 0; x < w; ++x) {
            const float n = ridgedFbm(static_cast<float>(x) / scale,
                                      static_cast<float>(y) / scale,
                                      seed, oct);
            // Only ridges above the threshold emit; normalise to [0, 1].
            const float emitFactor = std::max(0.0f, (n - EMIT_THRESHOLD) / EMIT_RANGE);

            const size_t idx = static_cast<size_t>((y * w + x) * 3);
            buf[idx + 0] = toU8(mat.emissive[0] * emitFactor);
            buf[idx + 1] = toU8(mat.emissive[1] * emitFactor);
            buf[idx + 2] = toU8(mat.emissive[2] * emitFactor);
        }
    }
    return buf;
}

// ─────────────────────────────────────────────────────────────────────────────
// Texture filename builder
// ─────────────────────────────────────────────────────────────────────────────

/** @brief Build: "<outputDir>/<materialName>_<channel>.png". */
std::string texturePath(const std::string& outputDir,
                        const std::string& materialName,
                        const std::string& channel)
{
    return outputDir + "/" + materialName + "_" + channel + ".png";
}

} // anonymous namespace

// =============================================================================
// Public API
// =============================================================================

bool generateTextures(Material&            mat,
                      const std::string&   outputDir,
                      const TexGenOptions& opts)
{
    const int   W     = opts.width;
    const int   H     = opts.height;
    const float SCALE = opts.noiseScale;
    const int   OCT   = opts.octaves;
    const float STR   = opts.normalStrength;

    // Convenience: build full seed for each channel.
    const uint32_t seedAlbedo    = mat.seed + CHANNEL_SEED_ALBEDO;
    const uint32_t seedNormal    = mat.seed + CHANNEL_SEED_NORMAL;
    const uint32_t seedRoughness = mat.seed + CHANNEL_SEED_ROUGHNESS;
    const uint32_t seedMetallic  = mat.seed + CHANNEL_SEED_METALLIC;
    const uint32_t seedAO        = mat.seed + CHANNEL_SEED_AO;
    const uint32_t seedEmissive  = mat.seed + CHANNEL_SEED_EMISSIVE;

    bool ok = true;

    // ── Albedo ────────────────────────────────────────────────────────────────
    {
        const auto pixels = genAlbedo(mat, W, H, SCALE, OCT, seedAlbedo);
        const std::string path = texturePath(outputDir, mat.name, "albedo");
        ok &= writePNG(path, W, H, 3, pixels.data());
        mat.texAlbedo = mat.name + "_albedo.png";
    }

    // ── Normal ────────────────────────────────────────────────────────────────
    {
        const auto pixels = genNormal(W, H, SCALE, OCT, seedNormal, STR);
        const std::string path = texturePath(outputDir, mat.name, "normal");
        ok &= writePNG(path, W, H, 3, pixels.data());
        mat.texNormal = mat.name + "_normal.png";
    }

    // ── Roughness ─────────────────────────────────────────────────────────────
    {
        constexpr float ROUGHNESS_VARIATION = 0.12f;  // ±12% around base value.
        const auto pixels = genGrayscale(mat.roughness, ROUGHNESS_VARIATION,
                                          W, H, SCALE, OCT, seedRoughness);
        const std::string path = texturePath(outputDir, mat.name, "roughness");
        ok &= writePNG(path, W, H, 1, pixels.data());
        mat.texRoughness = mat.name + "_roughness.png";
    }

    // ── Metallic ──────────────────────────────────────────────────────────────
    {
        // Metallic surfaces have more variation than dielectrics, but still small
        // — real metals are highly uniform; only oxidation/patina adds variation.
        const float metallicVariation = (mat.metallic > 0.5f) ? 0.05f : 0.02f;
        const auto pixels = genGrayscale(mat.metallic, metallicVariation,
                                          W, H, SCALE, OCT, seedMetallic);
        const std::string path = texturePath(outputDir, mat.name, "metallic");
        ok &= writePNG(path, W, H, 1, pixels.data());
        mat.texMetallic = mat.name + "_metallic.png";
    }

    // ── AO ───────────────────────────────────────────────────────────────────
    {
        // Rougher/porous materials (stone, soil) have stronger ambient occlusion
        // because their micro-crevices are deeper relative to smooth materials.
        const float aoStrength = 0.15f + 0.25f * mat.roughness;
        const auto pixels = genAO(aoStrength, W, H, SCALE, OCT, seedAO);
        const std::string path = texturePath(outputDir, mat.name, "ao");
        ok &= writePNG(path, W, H, 1, pixels.data());
        mat.texAO = mat.name + "_ao.png";
    }

    // ── Emissive ──────────────────────────────────────────────────────────────
    {
        const auto pixels = genEmissive(mat, W, H, SCALE, OCT, seedEmissive);
        const std::string path = texturePath(outputDir, mat.name, "emissive");
        ok &= writePNG(path, W, H, 3, pixels.data());
        // Record texture path only for genuinely emissive materials.
        const bool hasEmission = (mat.emissive[0] + mat.emissive[1] + mat.emissive[2]) > 0.001f;
        mat.texEmissive = hasEmission ? (mat.name + "_emissive.png") : "";
    }

    return ok;
}

} // namespace ce
