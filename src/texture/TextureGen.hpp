/**
 * @file TextureGen.hpp
 * @brief PBR-lite texture generator — produces albedo, normal, roughness,
 *        metallic, AO, and emissive PNG maps from a Material definition.
 *
 * =============================================================================
 * TEACHING NOTE — PBR Texture Maps
 * =============================================================================
 *
 * Each PBR channel is stored as a separate greyscale or RGB PNG:
 *
 *   Albedo    (RGB)  — The "colour" of the surface. Generated using the
 *                      material's baseColor tinted by low-frequency noise.
 *
 *   Normal    (RGB)  — Encodes the surface micro-normal as (R=X, G=Y, B=Z),
 *                      remapped from [-1,1] to [0,255]. Derived from a height
 *                      field using finite differences (central differences):
 *                        dx = h(x+1, y) - h(x-1, y)
 *                        dy = h(x, y+1) - h(x, y-1)
 *                        N  = normalize(-dx * strength, -dy * strength, 1.0)
 *
 *   Roughness (Gray) — Greyscale map: bright = rough, dark = smooth.
 *
 *   Metallic  (Gray) — Greyscale map: white = metal, black = dielectric.
 *
 *   AO        (Gray) — Ambient Occlusion: bright = fully lit, dark = occluded.
 *                      Crevices in the noise heightfield appear darker.
 *
 *   Emissive  (RGB)  — Non-zero only for glowing surfaces (lava, embers, neon).
 *
 * Each map uses the same noise seed + a channel-specific offset so all maps
 * share the same surface detail but vary independently.
 *
 * @author  Creation Engine Project
 * @version 1.0
 */

#pragma once

#include <string>
#include <vector>
#include <cstdint>
#include "material/Material.hpp"

namespace ce {

// =============================================================================
// TextureGen Options
// =============================================================================

/**
 * @struct TexGenOptions
 * @brief Configuration for the texture generator.
 */
struct TexGenOptions {
    int      width          = 64;    ///< Texture width  in pixels.
    int      height         = 64;    ///< Texture height in pixels.
    int      octaves        = 4;     ///< fBm octave count (detail level).
    float    noiseScale     = 8.0f;  ///< World-space frequency of noise.
    float    normalStrength = 4.0f;  ///< How pronounced the normal map bumps are.
};

// =============================================================================
// Interface
// =============================================================================

/**
 * @brief Generate all PBR texture maps for a material and write them to disk.
 *
 * For each channel (albedo, normal, roughness, metallic, AO, emissive) this
 * function:
 *   1. Evaluates the procedural noise field at every pixel.
 *   2. Maps the noise value to an 8-bit channel value using the material's
 *      scalar PBR parameters.
 *   3. Writes a PNG file to `outputDir`.
 *
 * The `mat` object's texture filename fields are populated with the generated
 * paths (relative to `outputDir`) so the caller can immediately serialise the
 * material JSON.
 *
 * @param mat        Material definition (modified in-place with texture paths).
 * @param outputDir  Directory where PNG files are written (must exist).
 * @param opts       Generator settings (resolution, noise parameters).
 * @return           true if all files were written successfully.
 */
bool generateTextures(Material&          mat,
                      const std::string& outputDir,
                      const TexGenOptions& opts = TexGenOptions{});

} // namespace ce
