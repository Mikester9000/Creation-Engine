/**
 * @file AIAssist.cpp
 * @brief Implementation of the offline, deterministic AI-assist module.
 *
 * =============================================================================
 * TEACHING NOTE — Rule-Based AI vs Neural AI
 * =============================================================================
 *
 * This file contains the ENTIRE "AI" logic — roughly 200 lines of lookup
 * tables and arithmetic. Compare this with a neural diffusion model that
 * would require gigabytes of weights. The trade-off:
 *
 *   Rule-Based         Neural Net
 *   ─────────────      ─────────────────────────────────────
 *   Fully inspectable  Opaque (weights can't be read)
 *   Deterministic      Stochastic (unless seeded carefully)
 *   Fast (<1ms)        Slow (seconds on GPU, minutes on CPU)
 *   Offline            Usually requires server / GPU
 *   Limited coverage   Handles novel prompts gracefully
 *   Easy to teach      Hard to teach (needs ML background)
 *
 * For a TEACHING game engine, rule-based is the right choice. Students can
 * edit the tables below and immediately see the effect on generated textures.
 *
 * @author  Creation Engine Project
 * @version 1.0
 */

#include "ai/AIAssist.hpp"

#include <algorithm>
#include <cctype>
#include <sstream>
#include <unordered_map>
#include <vector>
#include <string>

namespace ce {

// =============================================================================
// Internal: keyword tokeniser
// =============================================================================

namespace {

/**
 * @brief Split a prompt string into lowercase tokens on whitespace/punctuation.
 *
 * TEACHING NOTE — Tokenisation
 * Tokenisation is the first step of any NLP (Natural Language Processing)
 * pipeline. Here we use a simple character-level approach:
 *   • Convert to lowercase.
 *   • Split on any non-alphanumeric character.
 *   • Skip empty tokens.
 *
 * A production system would also handle: stemming ("stones" → "stone"),
 * stop-word removal ("a", "the", "with"), and synonym expansion.
 *
 * @param text  Input prompt string.
 * @return      Vector of lowercase tokens.
 */
std::vector<std::string> tokenise(const std::string& text)
{
    std::vector<std::string> tokens;
    std::string current;
    for (char c : text) {
        if (std::isalnum(static_cast<unsigned char>(c))) {
            current += static_cast<char>(std::tolower(static_cast<unsigned char>(c)));
        } else {
            if (!current.empty()) {
                tokens.push_back(current);
                current.clear();
            }
        }
    }
    if (!current.empty()) tokens.push_back(current);
    return tokens;
}

/**
 * @brief Check whether any of the prompt tokens match a given keyword.
 * @param tokens  Tokenised prompt.
 * @param kw      Keyword to look for (lowercase, no spaces).
 * @return        true if found.
 */
bool hasKeyword(const std::vector<std::string>& tokens, const std::string& kw)
{
    return std::find(tokens.begin(), tokens.end(), kw) != tokens.end();
}

// =============================================================================
// Material preset table
// =============================================================================

/**
 * @struct MaterialPreset
 * @brief A named set of default PBR values for a recognisable surface type.
 *
 * TEACHING NOTE — PBR Presets
 * These values are derived from reference tables used by FFXV artists
 * (and documented in Epic's UE4 PBR guide and similar resources).
 * "Wet" is a modifier, not a base preset — see the modifier table below.
 */
struct MaterialPreset {
    std::string keyword;
    std::array<float,3> baseColor;
    float roughness;
    float metallic;
    std::array<float,3> emissive;
    float noiseScale;    ///< Suggested noise scale for this surface type.
    int   octaves;       ///< Suggested octave count.
    float normalStrength;///< Normal-map bump intensity.
};

// FFXV-calibrated material presets
static const std::vector<MaterialPreset> MATERIAL_PRESETS = {
    // keyword        baseColor                roughness  metallic  emissive           scale  oct  nStr
    {"stone",   {0.32f, 0.30f, 0.28f},   0.85f,  0.00f, {0,0,0},         8.0f, 4, 4.0f},
    {"rock",    {0.28f, 0.26f, 0.24f},   0.90f,  0.00f, {0,0,0},         8.0f, 5, 5.0f},
    {"cliff",   {0.25f, 0.23f, 0.20f},   0.92f,  0.00f, {0,0,0},        10.0f, 6, 6.0f},
    {"dirt",    {0.28f, 0.22f, 0.15f},   0.92f,  0.00f, {0,0,0},         6.0f, 3, 2.0f},
    {"mud",     {0.20f, 0.15f, 0.10f},   0.95f,  0.00f, {0,0,0},         5.0f, 4, 3.0f},
    {"sand",    {0.76f, 0.70f, 0.50f},   0.90f,  0.00f, {0,0,0},        12.0f, 3, 1.5f},
    {"grass",   {0.18f, 0.30f, 0.10f},   0.90f,  0.00f, {0,0,0},        10.0f, 4, 2.0f},
    {"soil",    {0.18f, 0.14f, 0.10f},   0.90f,  0.00f, {0,0,0},         7.0f, 4, 2.0f},
    {"water",   {0.03f, 0.09f, 0.15f},   0.05f,  0.00f, {0,0,0},        16.0f, 3, 8.0f},
    {"ice",     {0.72f, 0.80f, 0.90f},   0.04f,  0.00f, {0,0,0},        20.0f, 2, 3.0f},
    {"snow",    {0.90f, 0.92f, 0.95f},   0.85f,  0.00f, {0,0,0},        14.0f, 3, 1.5f},
    {"wood",    {0.42f, 0.28f, 0.16f},   0.85f,  0.00f, {0,0,0},         6.0f, 4, 3.0f},
    {"bark",    {0.30f, 0.20f, 0.12f},   0.90f,  0.00f, {0,0,0},         7.0f, 5, 4.0f},
    {"moss",    {0.12f, 0.22f, 0.08f},   0.92f,  0.00f, {0,0,0},         8.0f, 5, 3.0f},
    {"metal",   {0.56f, 0.57f, 0.58f},   0.30f,  1.00f, {0,0,0},        12.0f, 3, 2.0f},
    {"iron",    {0.52f, 0.50f, 0.48f},   0.35f,  1.00f, {0,0,0},        10.0f, 4, 3.0f},
    {"steel",   {0.60f, 0.60f, 0.62f},   0.20f,  1.00f, {0,0,0},        12.0f, 3, 2.0f},
    {"gold",    {1.00f, 0.77f, 0.34f},   0.20f,  1.00f, {0,0,0},        10.0f, 3, 1.5f},
    {"copper",  {0.95f, 0.64f, 0.54f},   0.25f,  1.00f, {0,0,0},        10.0f, 3, 2.0f},
    {"silver",  {0.97f, 0.96f, 0.91f},   0.15f,  1.00f, {0,0,0},        10.0f, 2, 1.5f},
    {"lava",    {0.60f, 0.20f, 0.05f},   0.80f,  0.00f, {1.0f,0.4f,0.05f}, 6.0f, 5, 5.0f},
    {"fire",    {0.80f, 0.30f, 0.02f},   0.70f,  0.00f, {1.0f,0.5f,0.1f},  5.0f, 4, 4.0f},
    {"marble",  {0.85f, 0.82f, 0.80f},   0.10f,  0.00f, {0,0,0},        16.0f, 6, 2.0f},
    {"concrete",{0.55f, 0.53f, 0.50f},   0.80f,  0.00f, {0,0,0},         8.0f, 3, 2.0f},
    {"brick",   {0.55f, 0.28f, 0.20f},   0.88f,  0.00f, {0,0,0},         6.0f, 4, 3.0f},
    {"tile",    {0.70f, 0.68f, 0.65f},   0.25f,  0.00f, {0,0,0},        12.0f, 3, 1.5f},
    {"floor",   {0.45f, 0.42f, 0.40f},   0.70f,  0.00f, {0,0,0},         8.0f, 3, 2.0f},
    {"wall",    {0.50f, 0.48f, 0.45f},   0.82f,  0.00f, {0,0,0},         8.0f, 4, 3.0f},
    {"road",    {0.30f, 0.28f, 0.24f},   0.88f,  0.00f, {0,0,0},        10.0f, 3, 2.0f},
};

/**
 * @brief Find the best-matching material preset for the given tokens.
 *
 * Returns the FIRST match in prompt order. If no keyword matches, returns
 * the "stone" default (a safe neutral material).
 */
const MaterialPreset& findPreset(const std::vector<std::string>& tokens)
{
    for (const std::string& tok : tokens) {
        for (const MaterialPreset& p : MATERIAL_PRESETS) {
            if (p.keyword == tok) return p;
        }
    }
    // Default: stone
    return MATERIAL_PRESETS[0];
}

// =============================================================================
// Material modifier table
// =============================================================================

/**
 * @struct MaterialModifier
 * @brief A keyword that adjusts existing PBR values rather than setting them.
 *
 * TEACHING NOTE — Compositional Prompts
 * "wet stone" should produce stone material with a wet-surface modification.
 * By separating presets (nouns) from modifiers (adjectives), we get a simple
 * compositional system:
 *
 *   prompt = [modifiers] + [base material noun]
 *
 * Each modifier multiplies or adds to the base values. This mirrors how
 * real-world material editors work: start from a base material, then apply
 * layers of adjustments.
 */
struct MaterialModifier {
    std::string       keyword;
    float             roughnessMul  = 1.0f;  ///< Multiply roughness by this.
    float             metallicAdd   = 0.0f;  ///< Add to metallic.
    float             colorDarken   = 1.0f;  ///< Multiply all colour channels.
    float             normalStrMul  = 1.0f;  ///< Multiply normal strength.
};

static const std::vector<MaterialModifier> MATERIAL_MODIFIERS = {
    // keyword      roughMul  metalAdd  darkMul  normMul
    {"wet",         0.45f,    0.00f,    0.80f,   0.8f},  // wet → smoother, darker
    {"dry",         1.10f,    0.00f,    1.10f,   1.2f},  // dry → rougher, lighter
    {"polished",    0.20f,    0.05f,    1.05f,   0.4f},  // polished → very smooth
    {"rough",       1.20f,    0.00f,    0.95f,   1.5f},  // rough → more bumpy
    {"cracked",     1.15f,    0.00f,    0.90f,   2.0f},  // cracked → extra detail
    {"aged",        1.10f,    0.00f,    0.88f,   1.3f},  // aged → rougher, darker
    {"burnt",       1.05f,    0.00f,    0.70f,   1.2f},  // burnt → darker
    {"mossy",       1.05f,    0.00f,    0.85f,   1.1f},  // mossy → slightly darker
    {"dusty",       1.08f,    0.00f,    1.05f,   0.9f},  // dusty → lighter, rougher
    {"shiny",       0.30f,    0.10f,    1.02f,   0.5f},  // shiny → smooth
    {"dark",        1.00f,    0.00f,    0.60f,   1.0f},  // dark → darker colour
    {"light",       1.00f,    0.00f,    1.40f,   1.0f},  // light → lighter colour
    {"red",         1.00f,    0.00f,    1.00f,   1.0f},  // handled as colour tint
    {"blue",        1.00f,    0.00f,    1.00f,   1.0f},
    {"green",       1.00f,    0.00f,    1.00f,   1.0f},
    {"rusty",       1.15f,    0.05f,    0.85f,   1.4f},  // rusty metal → rougher
    {"ancient",     1.10f,    0.00f,    0.80f,   1.3f},
    {"fresh",       0.90f,    0.00f,    1.05f,   0.9f},
    {"deep",        1.00f,    0.00f,    0.75f,   1.1f},
    {"shallow",     1.00f,    0.00f,    1.10f,   0.8f},
};

// Colour tints applied by certain adjective keywords
static const std::unordered_map<std::string, std::array<float,3>> COLOR_TINTS = {
    {"red",    {1.4f, 0.7f, 0.7f}},
    {"blue",   {0.7f, 0.8f, 1.4f}},
    {"green",  {0.7f, 1.4f, 0.7f}},
    {"orange", {1.4f, 0.9f, 0.5f}},
    {"yellow", {1.4f, 1.4f, 0.6f}},
    {"purple", {1.1f, 0.7f, 1.4f}},
    {"black",  {0.3f, 0.3f, 0.3f}},
    {"white",  {1.6f, 1.6f, 1.6f}},
    {"grey",   {1.0f, 1.0f, 1.0f}},
    {"gray",   {1.0f, 1.0f, 1.0f}},
};

/**
 * @brief Apply all matching modifiers from the token list to a Material.
 */
void applyModifiers(Material& mat, const std::vector<std::string>& tokens)
{
    for (const std::string& tok : tokens) {
        for (const MaterialModifier& m : MATERIAL_MODIFIERS) {
            if (m.keyword == tok) {
                mat.roughness  = std::max(0.0f, std::min(1.0f, mat.roughness * m.roughnessMul));
                mat.metallic   = std::max(0.0f, std::min(1.0f, mat.metallic  + m.metallicAdd));
                for (int c = 0; c < 3; ++c)
                    mat.baseColor[c] = std::max(0.0f, std::min(1.0f,
                                           mat.baseColor[c] * m.colorDarken));
            }
        }
        // Colour tints
        auto it = COLOR_TINTS.find(tok);
        if (it != COLOR_TINTS.end()) {
            for (int c = 0; c < 3; ++c)
                mat.baseColor[c] = std::max(0.0f, std::min(1.0f,
                                       mat.baseColor[c] * it->second[c]));
        }
    }
}

// =============================================================================
// Map prompt keyword table
// =============================================================================

/**
 * @brief Parse map-related keywords from the prompt tokens.
 *
 * TEACHING NOTE — Compositional Map Prompts
 * Map prompts work similarly to material prompts but control topology and
 * biome parameters rather than PBR values. Examples:
 *   "forest"     → mostly FOREST/GRASS tiles
 *   "river"      → carve a winding WATER path
 *   "road"       → add a ROAD crossing
 *   "dungeon"    → switch to room-corridor mode
 *   "mountain"   → raise height thresholds for more MOUNTAIN tiles
 *   "desert"     → high SAND coverage (lower noise scale)
 *   "beach"      → flat terrain with water edges
 */
void applyMapKeywords(MapGenOptions& opts, const std::vector<std::string>& tokens)
{
    if (hasKeyword(tokens, "river")   || hasKeyword(tokens, "stream") ||
        hasKeyword(tokens, "creek")   || hasKeyword(tokens, "lake"))
        opts.hasRiver = true;

    if (hasKeyword(tokens, "road")    || hasKeyword(tokens, "path") ||
        hasKeyword(tokens, "trail")   || hasKeyword(tokens, "highway"))
        opts.hasRoad = true;

    if (hasKeyword(tokens, "dungeon") || hasKeyword(tokens, "cave") ||
        hasKeyword(tokens, "cavern")  || hasKeyword(tokens, "underground") ||
        hasKeyword(tokens, "ruins"))
        opts.isDungeon = true;

    // Map size hints
    if (hasKeyword(tokens, "large") || hasKeyword(tokens, "huge") ||
        hasKeyword(tokens, "big"))   { opts.width = 96; opts.height = 96; }
    if (hasKeyword(tokens, "small") || hasKeyword(tokens, "tiny"))
                                     { opts.width = 32; opts.height = 32; }

    // Terrain frequency adjustments
    if (hasKeyword(tokens, "mountain") || hasKeyword(tokens, "highland"))
        opts.noiseScale = 12.0f;  // smaller scale → more dramatic peaks

    if (hasKeyword(tokens, "desert") || hasKeyword(tokens, "plains") ||
        hasKeyword(tokens, "flat"))
        opts.noiseScale = 24.0f;  // larger scale → flatter terrain

    if (hasKeyword(tokens, "island") || hasKeyword(tokens, "coastal"))
        opts.hasRiver = true;     // coastal maps always have water

    // More rooms for larger dungeons
    if (opts.isDungeon) {
        if (hasKeyword(tokens, "large") || hasKeyword(tokens, "huge"))
            opts.numRooms = 16;
        else if (hasKeyword(tokens, "small"))
            opts.numRooms = 5;
    }
}

} // anonymous namespace

// =============================================================================
// Public API
// =============================================================================

AITextureParams aiInferTexture(const std::string& prompt,
                               uint32_t           seed,
                               const std::string& name)
{
    AITextureParams result;

    // Tokenise the prompt
    auto tokens = tokenise(prompt);

    // Find the closest material preset
    const MaterialPreset& preset = findPreset(tokens);

    // Populate material from preset
    Material& mat    = result.material;
    mat.name         = name;
    mat.prompt       = prompt;
    mat.seed         = seed;
    mat.baseColor    = preset.baseColor;
    mat.roughness    = preset.roughness;
    mat.metallic     = preset.metallic;
    mat.emissive     = preset.emissive;
    mat.ao           = 1.0f;  // AO is always 1.0 (map handles the variation)

    // Apply adjective modifiers (wet, polished, dark, etc.)
    applyModifiers(mat, tokens);

    // Populate texture generator settings from preset
    result.genOpts.noiseScale     = preset.noiseScale;
    result.genOpts.octaves        = preset.octaves;
    result.genOpts.normalStrength = preset.normalStrength;
    // Resolution: default 64×64 (sufficient for PBR teaching demo)
    result.genOpts.width  = 64;
    result.genOpts.height = 64;

    return result;
}

AIMapParams aiInferMap(const std::string& prompt, uint32_t seed)
{
    (void)seed;  // Seed is stored in TileMap; reserved for future AI refinement.
    AIMapParams result;

    auto tokens = tokenise(prompt);

    // Set defaults
    result.genOpts.width      = 64;
    result.genOpts.height     = 64;
    result.genOpts.tileSize   = 64;
    result.genOpts.octaves    = 5;
    result.genOpts.noiseScale = 16.0f;
    result.genOpts.hasRiver   = false;
    result.genOpts.hasRoad    = false;
    result.genOpts.isDungeon  = false;
    result.genOpts.numRooms   = 8;

    // Apply map-specific keyword rules
    applyMapKeywords(result.genOpts, tokens);

    // Infer a suggested terrain material from the prompt
    const MaterialPreset& preset = findPreset(tokens);
    result.suggestedMaterial = preset.keyword;

    return result;
}

} // namespace ce
