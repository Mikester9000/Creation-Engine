/**
 * @file Material.hpp
 * @brief PBR-lite material definition and JSON export.
 *
 * =============================================================================
 * TEACHING NOTE — PBR (Physically Based Rendering) Materials
 * =============================================================================
 *
 * PBR is the standard shading model used in modern AAA games (FFXV, Cyberpunk,
 * Horizon Zero Dawn). It models how light interacts with surfaces using a
 * small set of physically-motivated parameters:
 *
 *   baseColor   — The intrinsic colour of the surface under white diffuse light.
 *                 Also called "albedo". For metals this tints specular reflections.
 *
 *   roughness   — 0.0 = mirror-smooth (polished metal, ice, water);
 *                 1.0 = completely diffuse (chalk, unfinished plaster).
 *                 Controls the spread of specular highlights (GGX micro-facet).
 *
 *   metallic    — 0.0 = dielectric (stone, wood, skin, plastic);
 *                 1.0 = metal (iron, gold, copper).
 *                 Metals have no diffuse lobe; reflectance comes from baseColor.
 *
 *   ao          — Ambient Occlusion [0,1]. Darkens micro-crevices and contact
 *                 shadows that are missed by real-time lighting.
 *
 *   emissive    — RGB radiance for self-illuminating surfaces (lava, neon, fire).
 *                 Black = no emission.
 *
 * PRACTICAL FFXV APPROXIMATION
 * ─────────────────────────────
 * FFXV uses the standard UE4-derived PBR model. Typical material values:
 *
 *   Material     baseColor          roughness  metallic
 *   ─────────────────────────────────────────────────────
 *   Wet stone    (0.22, 0.22, 0.22)   0.45      0.00
 *   Dry stone    (0.32, 0.30, 0.28)   0.85      0.00
 *   Forest soil  (0.18, 0.14, 0.10)   0.90      0.00
 *   River water  (0.03, 0.09, 0.15)   0.05      0.00
 *   Dirt road    (0.28, 0.22, 0.15)   0.92      0.00
 *   Iron metal   (0.56, 0.57, 0.58)   0.30      1.00
 *   Gold         (1.00, 0.77, 0.34)   0.20      1.00
 *   Sand         (0.76, 0.70, 0.50)   0.90      0.00
 *
 * LESSON EXERCISES
 * ─────────────────
 * 1. Set metallic=1.0 on a stone material — does it look right? (No — metals
 *    must also have a dark/coloured baseColor, not grey.)
 * 2. Set roughness=0.0 on grass — the engine renders it as a mirror. Why?
 *    (roughness=0 → infinitely narrow specular lobe → mirror reflection.)
 *
 * @author  Creation Engine Project
 * @version 1.0
 */

#pragma once

#include <cstdint>
#include <string>
#include <array>
#include "util/JsonWriter.hpp"

namespace ce {

// =============================================================================
// PBR-lite Material Struct
// =============================================================================

/// JSON format version — increment when the schema changes.
constexpr const char* MATERIAL_FORMAT_VERSION = "1.0";

/**
 * @struct Material
 * @brief All parameters for a single PBR-lite material surface.
 *
 * Texture filenames are relative paths from the material JSON file.
 * Empty string means "no texture; use the scalar parameter value directly".
 */
struct Material {

    // ── Identity ──────────────────────────────────────────────────────────────
    std::string name;               ///< Identifier (e.g., "wet_stone").
    std::string version = MATERIAL_FORMAT_VERSION;  ///< JSON format version.

    // ── Scalar PBR parameters ─────────────────────────────────────────────────
    // These values are used when the corresponding texture is absent, and also
    // act as the "base multiplier" when a texture is present.

    std::array<float,3> baseColor = {0.5f, 0.5f, 0.5f};  ///< Linear RGB [0,1].
    float roughness  = 0.8f;   ///< Micro-surface roughness [0,1].
    float metallic   = 0.0f;   ///< Metallic factor [0,1].
    float ao         = 1.0f;   ///< Global AO multiplier [0,1].
    std::array<float,3> emissive = {0.0f, 0.0f, 0.0f};   ///< Emission RGB.

    // ── Texture maps (relative file paths) ───────────────────────────────────
    // Naming convention: <materialName>_<channel>.png
    std::string texAlbedo;      ///< Albedo / base-colour map.
    std::string texNormal;      ///< Tangent-space normal map.
    std::string texRoughness;   ///< Roughness (R channel of combined ORM map).
    std::string texMetallic;    ///< Metallic  (B channel of combined ORM map).
    std::string texAO;          ///< Ambient occlusion (G channel of ORM map).
    std::string texEmissive;    ///< Emissive colour map (blank = no emission).

    // ── Noise/generation metadata ─────────────────────────────────────────────
    uint32_t    seed        = 0;    ///< Seed used to generate this material.
    std::string prompt;             ///< Original prompt string (for traceability).
};

// =============================================================================
// JSON Serialisation
// =============================================================================

/**
 * @brief Serialise a Material to a JSON string.
 *
 * Output format (asset spec):
 * @code
 * {
 *   "version": "1.0",
 *   "name": "wet_stone",
 *   "prompt": "wet stone",
 *   "seed": 123,
 *   "params": {
 *     "baseColor": [0.22, 0.22, 0.22],
 *     "roughness": 0.45,
 *     "metallic": 0.0,
 *     "ao": 1.0,
 *     "emissive": [0.0, 0.0, 0.0]
 *   },
 *   "textures": {
 *     "albedo":    "wet_stone_albedo.png",
 *     "normal":    "wet_stone_normal.png",
 *     "roughness": "wet_stone_roughness.png",
 *     "metallic":  "wet_stone_metallic.png",
 *     "ao":        "wet_stone_ao.png",
 *     "emissive":  ""
 *   }
 * }
 * @endcode
 *
 * @param mat  Material to serialise.
 * @return     Pretty-printed JSON string.
 */
inline std::string materialToJson(const Material& mat)
{
    JsonWriter j;
    j.beginObject();

    j.keyString("version", mat.version);
    j.keyString("name",    mat.name);
    j.keyString("prompt",  mat.prompt);
    j.keyInt   ("seed",    static_cast<int64_t>(mat.seed));

    // ── params ──
    j.writeKey("params");
    j.beginObject();

        j.writeKey("baseColor");
        j.beginArray();
            j.writeFloat(mat.baseColor[0]);
            j.writeFloat(mat.baseColor[1]);
            j.writeFloat(mat.baseColor[2]);
        j.endArray();

        j.keyFloat("roughness", mat.roughness);
        j.keyFloat("metallic",  mat.metallic);
        j.keyFloat("ao",        mat.ao);

        j.writeKey("emissive");
        j.beginArray();
            j.writeFloat(mat.emissive[0]);
            j.writeFloat(mat.emissive[1]);
            j.writeFloat(mat.emissive[2]);
        j.endArray();

    j.endObject();

    // ── textures ──
    j.writeKey("textures");
    j.beginObject();
        j.keyString("albedo",    mat.texAlbedo);
        j.keyString("normal",    mat.texNormal);
        j.keyString("roughness", mat.texRoughness);
        j.keyString("metallic",  mat.texMetallic);
        j.keyString("ao",        mat.texAO);
        j.keyString("emissive",  mat.texEmissive);
    j.endObject();

    j.endObject();
    return j.str();
}

} // namespace ce
