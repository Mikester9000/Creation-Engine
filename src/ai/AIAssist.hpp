/**
 * @file AIAssist.hpp
 * @brief Offline, deterministic "AI assist" module.
 *
 * =============================================================================
 * TEACHING NOTE — What Does "AI Assist" Mean Here?
 * =============================================================================
 *
 * In a real-world production pipeline (Unreal Engine 5, Adobe Firefly, etc.)
 * "AI texture generation" calls an external neural network (diffusion model).
 * That requires:
 *   • A multi-GB model checkpoint
 *   • GPU memory and compute
 *   • Internet / license for hosted APIs
 *
 * For TEACHING purposes, we implement AI assist as a RULE-BASED SYSTEM:
 *
 *   prompt (string)  →  parse keywords  →  PBR parameters  →  generator
 *
 * This is deterministic, runs offline, requires no network, and is 100%
 * transparent — students can READ and MODIFY the rules. Real AI systems are
 * black boxes; rule-based systems are white boxes.
 *
 * KEYWORD EXTRACTION
 * ───────────────────
 * The module tokenises the prompt on whitespace/punctuation and matches
 * each token against a lookup table of known material/terrain descriptors.
 * Multiple matching keywords are combined (e.g., "wet" + "stone" →
 * stone material with reduced roughness).
 *
 * PRACTICAL PBR APPROXIMATION
 * ─────────────────────────────
 * The keyword-to-parameter mapping is calibrated against the FFXV reference
 * values from Material.hpp. Each keyword can:
 *   • Set a base material preset (stone, metal, grass, water, …)
 *   • Modify individual PBR channels (wet → roughness *= 0.5, …)
 *   • Set emissive colour (lava → emissive = orange, …)
 *   • Enable map features (river, road, dungeon, …)
 *
 * LESSON EXERCISES
 * ─────────────────
 * 1. Add a new keyword "rusty" that adds slight orange tint to metallic mats.
 * 2. Add a "snow" keyword: white baseColor, roughness 0.9, metallic 0.
 * 3. Implement a simple "confidence score" that returns the top 3 matched
 *    presets and lets the user choose interactively.
 *
 * @author  Creation Engine Project
 * @version 1.0
 */

#pragma once

#include <string>
#include "material/Material.hpp"
#include "texture/TextureGen.hpp"
#include "map/MapGen.hpp"

namespace ce {

// =============================================================================
// AI Assist results
// =============================================================================

/**
 * @struct AITextureParams
 * @brief The PBR + generator parameters inferred from a prompt.
 *
 * Passed directly to TextureGen::generateTextures() after the AI step.
 */
struct AITextureParams {
    Material     material;      ///< Inferred PBR material definition.
    TexGenOptions genOpts;      ///< Inferred texture generator settings.
};

/**
 * @struct AIMapParams
 * @brief The tilemap generator parameters inferred from a map prompt.
 */
struct AIMapParams {
    MapGenOptions genOpts;     ///< Inferred map generator settings.
    std::string   suggestedMaterial; ///< Terrain material name for this map.
};

// =============================================================================
// AI Assist interface
// =============================================================================

/**
 * @brief Infer PBR material + texture-generator parameters from a text prompt.
 *
 * @param prompt  Free-text description (e.g., "wet stone", "polished gold").
 * @param seed    Seed to embed in the material (ensures reproducibility).
 * @param name    Material identifier used in file names.
 * @return        AITextureParams with fully-populated material and gen options.
 */
AITextureParams aiInferTexture(const std::string& prompt,
                               uint32_t           seed,
                               const std::string& name);

/**
 * @brief Infer tilemap generator options from a map description prompt.
 *
 * @param prompt  Free-text description (e.g., "forest with river and road").
 * @param seed    Seed for the generator.
 * @return        AIMapParams with populated MapGenOptions.
 */
AIMapParams aiInferMap(const std::string& prompt, uint32_t seed);

} // namespace ce
