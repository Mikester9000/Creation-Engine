/**
 * @file TextureGen.cpp
 * @brief Implementation of the PBR-lite texture generator.
 *
 * =============================================================================
 * TEACHING NOTE — Generating Each PBR Channel
 * =============================================================================
 *
 * All channels derive from the same underlying noise height field h(x,y).
 * Using the same seed (plus a channel offset) ensures all maps "agree" about
 * the surface topology: a bump in the albedo map corresponds to a bump in the
 * normal map, a rougher region in the roughness map, etc.
 *
 *   SEED OFFSETS (avoid correlated maps)
 *   ────────────────────────────────────
 *   Albedo    seed + 0
 *   Normal    seed + 1000  (height field derived from this)
 *   Roughness seed + 2000
 *   Metallic  seed + 3000
 *   AO        seed + 4000
 *   Emissive  seed + 5000
 *
 * Using different seed offsets prevents two maps from being identical
 * (which would happen if they shared the exact same noise call sequence).
 *
 * @author  Creation Engine Project
 * @version 1.0
 */

#include "texture/TextureGen.hpp"

#include <cmath>
#include <algorithm>
#include <sstream>

#include "util/Noise.hpp"
#include "util/PNGWriter.hpp"

namespace ce {

// =============================================================================
// Internal helpers
// =============================================================================

namespace {

/** @brief Clamp a float to [0, 1]. */
inline float clamp01(float v) { return std::max(0.0f, std::min(1.0f, v)); }

/** @brief Convert a [0,1] float to a uint8 [0,255]. */
inline uint8_t toU8(float v) { return static_cast<uint8_t>(clamp01(v) * 255.0f + 0.5f); }

// ─────────────────────────────────────────────────────────────────────────────
// Albedo generator
// ─────────────────────────────────────────────────────────────────────────────

/**
 * @brief Generate the albedo (base colour) PNG map.
 *
 * TEACHING NOTE — Albedo
 * The albedo is the raw surface colour under perfectly white, diffuse light.
 * We start from mat.baseColor and add noise-driven variation so identical tiles
 * don't look like cloned stamps.
 *
 * Variation amount: ±15% (controlled by the 0.15 factor).
 * This is similar to how FFXV stone tiles have subtle colour variation across
 * their surfaces to avoid repetition.
 *
 * @param mat   Material (provides baseColor).
 * @param w, h  Texture dimensions.
 * @param scale Noise spatial frequency.
 * @param oct   Number of fBm octaves.
 * @param seed  Noise seed.
 * @return      RGB pixel buffer (w * h * 3 bytes).
 */
std::vector<uint8_t> genAlbedo(const Material& mat,
                                int w, int h,
                                float scale, int oct, uint32_t seed)
{
    std::vector<uint8_t> buf(static_cast<size_t>(w * h * 3));

    for (int y = 0; y < h; ++y) {
        for (int x = 0; x < w; ++x) {
            // Sample fBm noise in [0,1]
            float n = fbm(static_cast<float>(x) / scale,
                          static_cast<float>(y) / scale,
                          seed, oct);

            // Apply noise as a multiplicative tint: ×(0.85 … 1.15)
            float tint = 0.85f + 0.30f * n;

            size_t idx = static_cast<size_t>((y * w + x) * 3);
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
 * A normal map stores a surface normal vector per pixel in tangent space.
 * Tangent space means the Z axis points "up" out of the surface; X and Y lie
 * along the surface.
 *
 * We derive normals from a procedural height field h(x,y) using central
 * finite differences:
 *
 *   dh/dx ≈ (h(x+1,y) - h(x-1,y)) / 2
 *   dh/dy ≈ (h(x,y+1) - h(x,y-1)) / 2
 *
 * The surface tangent in X is (1, 0, dh/dx) and in Y is (0, 1, dh/dy).
 * Their cross product gives the normal: (-dh/dx, -dh/dy, 1), normalised.
 *
 * Encoding: (N + 1) / 2 → [0,255] per channel.
 * A flat surface would be (128, 128, 255) — pointing straight up.
 *
 * @param strength  How much height variation affects the normals. Higher
 *                  = more dramatic bumps.
 */
std::vector<uint8_t> genNormal(int w, int h,
                                float scale, int oct, uint32_t seed,
                                float strength)
{
    std::vector<uint8_t> buf(static_cast<size_t>(w * h * 3));

    // Lambda to sample height at any (integer) pixel coordinate.
    auto height = [&](int px, int py) -> float {
        return fbm(static_cast<float>(px) / scale,
                   static_cast<float>(py) / scale,
                   seed, oct);
    };

    for (int y = 0; y < h; ++y) {
        for (int x = 0; x < w; ++x) {
            // Central differences (wrap at texture edges for seamless tiling)
            float dX = height((x + 1) % w, y) - height((x - 1 + w) % w, y);
            float dY = height(x, (y + 1) % h) - height(x, (y - 1 + h) % h);

            // Normal: (-dX*strength, -dY*strength, 1), then normalised
            float nx = -dX * strength;
            float ny = -dY * strength;
            float nz = 1.0f;
            float len = std::sqrt(nx * nx + ny * ny + nz * nz);
            nx /= len;
            ny /= len;
            nz /= len;

            // Encode to [0, 255]: (v + 1) / 2 * 255
            size_t idx = static_cast<size_t>((y * w + x) * 3);
            buf[idx + 0] = toU8((nx + 1.0f) * 0.5f);
            buf[idx + 1] = toU8((ny + 1.0f) * 0.5f);
            buf[idx + 2] = toU8((nz + 1.0f) * 0.5f);
        }
    }
    return buf;
}

// ─────────────────────────────────────────────────────────────────────────────
// Grayscale channel (roughness, metallic, AO) generator
// ─────────────────────────────────────────────────────────────────────────────

/**
 * @brief Generate a greyscale PBR channel map.
 *
 * The base value is shifted by noise-driven variation.
 *
 * @param base       Scalar PBR value from the material [0,1].
 * @param variation  Max noise-driven deviation from base (e.g., 0.15).
 */
std::vector<uint8_t> genGrayscale(float base, float variation,
                                   int w, int h,
                                   float scale, int oct, uint32_t seed)
{
    std::vector<uint8_t> buf(static_cast<size_t>(w * h));

    for (int y = 0; y < h; ++y) {
        for (int x = 0; x < w; ++x) {
            float n = fbm(static_cast<float>(x) / scale,
                          static_cast<float>(y) / scale,
                          seed, oct);
            float v = base + variation * (n - 0.5f) * 2.0f;
            buf[static_cast<size_t>(y * w + x)] = toU8(v);
        }
    }
    return buf;
}

// ─────────────────────────────────────────────────────────────────────────────
// AO generator — darker in "crevices" (high-frequency noise peaks)
// ─────────────────────────────────────────────────────────────────────────────

/**
 * @brief Generate an ambient occlusion map.
 *
 * TEACHING NOTE — Ambient Occlusion
 * AO simulates the tendency of concave areas to receive less ambient light.
 * We approximate this by inverting the high-frequency noise: areas where the
 * noise is high (raised bumps) receive full AO (bright), while areas where
 * noise is low (recesses) are slightly darkened.
 *
 *   ao(x,y) = 1.0 - occlusionStrength * (1.0 - fbm(x,y))
 *
 * @param aoStrength  How dark the darkest crevice gets (e.g., 0.35 = 35% dark).
 */
std::vector<uint8_t> genAO(float aoStrength,
                             int w, int h,
                             float scale, int oct, uint32_t seed)
{
    std::vector<uint8_t> buf(static_cast<size_t>(w * h));

    for (int y = 0; y < h; ++y) {
        for (int x = 0; x < w; ++x) {
            float n = fbm(static_cast<float>(x) / scale,
                          static_cast<float>(y) / scale,
                          seed, oct);
            // Recessed areas (n close to 0) get darkened
            float ao = 1.0f - aoStrength * (1.0f - n);
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
 * For emissive materials (lava, neon, fire) this adds a noise-modulated
 * glow. The emissive colour comes from mat.emissive.
 */
std::vector<uint8_t> genEmissive(const Material& mat,
                                  int w, int h,
                                  float scale, int oct, uint32_t seed)
{
    std::vector<uint8_t> buf(static_cast<size_t>(w * h * 3), 0);

    bool hasEmission = (mat.emissive[0] + mat.emissive[1] + mat.emissive[2]) > 0.001f;
    if (!hasEmission) return buf;

    for (int y = 0; y < h; ++y) {
        for (int x = 0; x < w; ++x) {
            // Use ridged noise so emission concentrates in thin veins (lava cracks)
            float n = ridgedFbm(static_cast<float>(x) / scale,
                                static_cast<float>(y) / scale,
                                seed, oct);
            // Only the brightest noise peaks emit (threshold = 0.6)
            float e = std::max(0.0f, (n - 0.6f) / 0.4f);

            size_t idx = static_cast<size_t>((y * w + x) * 3);
            buf[idx + 0] = toU8(mat.emissive[0] * e);
            buf[idx + 1] = toU8(mat.emissive[1] * e);
            buf[idx + 2] = toU8(mat.emissive[2] * e);
        }
    }
    return buf;
}

// ─────────────────────────────────────────────────────────────────────────────
// Filename builder
// ─────────────────────────────────────────────────────────────────────────────

/** @brief Build a texture file path: "<dir>/<matName>_<channel>.png". */
std::string texPath(const std::string& dir,
                    const std::string& matName,
                    const std::string& channel)
{
    return dir + "/" + matName + "_" + channel + ".png";
}

} // anonymous namespace

// =============================================================================
// Public API
// =============================================================================

bool generateTextures(Material&           mat,
                      const std::string&  outputDir,
                      const TexGenOptions& opts)
{
    const int   W     = opts.width;
    const int   H     = opts.height;
    const float SCALE = opts.noiseScale;
    const int   OCT   = opts.octaves;
    const float STR   = opts.normalStrength;

    bool ok = true;

    // ── Albedo ───────────────────────────────────────────────────────────────
    {
        auto buf  = genAlbedo(mat, W, H, SCALE, OCT, mat.seed);
        std::string path = texPath(outputDir, mat.name, "albedo");
        ok &= writePNG(path, W, H, 3, buf.data());
        mat.texAlbedo = mat.name + "_albedo.png";
    }

    // ── Normal ───────────────────────────────────────────────────────────────
    {
        auto buf  = genNormal(W, H, SCALE, OCT, mat.seed + 1000u, STR);
        std::string path = texPath(outputDir, mat.name, "normal");
        ok &= writePNG(path, W, H, 3, buf.data());
        mat.texNormal = mat.name + "_normal.png";
    }

    // ── Roughness ─────────────────────────────────────────────────────────────
    {
        // variation of ±0.12 around the base roughness
        auto buf  = genGrayscale(mat.roughness, 0.12f, W, H, SCALE, OCT,
                                  mat.seed + 2000u);
        std::string path = texPath(outputDir, mat.name, "roughness");
        ok &= writePNG(path, W, H, 1, buf.data());
        mat.texRoughness = mat.name + "_roughness.png";
    }

    // ── Metallic ──────────────────────────────────────────────────────────────
    {
        // Metals have very small variation; dielectrics stay near 0.
        float var = (mat.metallic > 0.5f) ? 0.05f : 0.02f;
        auto buf  = genGrayscale(mat.metallic, var, W, H, SCALE, OCT,
                                  mat.seed + 3000u);
        std::string path = texPath(outputDir, mat.name, "metallic");
        ok &= writePNG(path, W, H, 1, buf.data());
        mat.texMetallic = mat.name + "_metallic.png";
    }

    // ── AO ───────────────────────────────────────────────────────────────────
    {
        // aoStrength: how dark the darkest crevices get.
        // Rough/porous materials (stone, soil) have stronger AO.
        float aoStr = 0.15f + 0.25f * mat.roughness;
        auto buf    = genAO(aoStr, W, H, SCALE, OCT, mat.seed + 4000u);
        std::string path = texPath(outputDir, mat.name, "ao");
        ok &= writePNG(path, W, H, 1, buf.data());
        mat.texAO = mat.name + "_ao.png";
    }

    // ── Emissive ──────────────────────────────────────────────────────────────
    {
        auto buf  = genEmissive(mat, W, H, SCALE, OCT, mat.seed + 5000u);
        std::string path = texPath(outputDir, mat.name, "emissive");
        ok &= writePNG(path, W, H, 3, buf.data());
        // Only record the texture path if we actually have emission
        bool hasEmission = (mat.emissive[0] + mat.emissive[1] + mat.emissive[2]) > 0.001f;
        mat.texEmissive = hasEmission ? (mat.name + "_emissive.png") : "";
    }

    return ok;
}

} // namespace ce
