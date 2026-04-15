/**
 * AIAssist.h - Keyword-based AI assistance for the Creation Engine.
 *
 * This is NOT a machine-learning system. Instead it uses a lookup table of
 * keywords found in the user's prompt to map them to generation parameters.
 *
 * Educational note: This technique - called "keyword/intent matching" - is a
 * simple form of natural-language understanding used in early chatbots and is
 * still practical for constrained domains such as game-content generation.
 */

#pragma once
#include <string>
#include "TextureGenerator.h"
#include "MapEditor.h"

// ============================================================
//  TextureRequest
// ============================================================

/**
 * TextureRequest holds all parameters needed to generate a texture.
 * It is produced by AIAssist::interpretTexture() from a text prompt.
 */
struct TextureRequest {
    std::string type;      // "noise", "cellular", "checker", "gradient", "radial", "solid"
    Color       color1;    // Primary colour
    Color       color2;    // Secondary colour
    float       scale   = 32.0f;
    int         octaves = 4;
    uint32_t    seed    = 0;
    int         width   = 64;
    int         height  = 64;
};

// ============================================================
//  MapRequest
// ============================================================

/**
 * MapRequest holds parameters for procedural map generation.
 * It is produced by AIAssist::interpretMap() from a text prompt.
 */
struct MapRequest {
    bool  generateTerrain = true;
    bool  generateRiver   = false;
    bool  generateVillage = false;
    float threshold       = 0.55f;  // Noise threshold for wall/ground split
    float scale           = 5.0f;   // Noise scale for terrain features
    int   buildingCount   = 5;
    uint32_t seed         = 0;
};

// ============================================================
//  AIAssist
// ============================================================

/**
 * AIAssist - Keyword-based prompt interpreter.
 *
 * All methods are static. Usage:
 *   TextureRequest req = AIAssist::interpretTexture("lava rock", seed, 64, 64);
 *   Texture tex = AIAssist::generateTextureFromRequest(req);
 */
class AIAssist {
public:
    /**
     * interpretTexture - Parse a natural-language prompt and produce a TextureRequest.
     *
     * Recognised themes include: lava/fire, ocean/water, grass, stone/rock/mossy,
     * sand/desert, space/nebula, checker, gradient/sky, wood/bark, snow/ice.
     */
    static TextureRequest interpretTexture(const std::string& prompt, uint32_t seed,
                                            int width, int height);

    /**
     * interpretMap - Parse a natural-language prompt and produce a MapRequest.
     *
     * Recognised biomes include: dungeon/cave, forest, village/town, plain/field,
     * island/coast. River/stream keywords independently enable river generation.
     */
    static MapRequest interpretMap(const std::string& prompt, uint32_t seed);

    /**
     * generateTextureFromRequest - Execute a TextureRequest and return the Texture.
     */
    static Texture generateTextureFromRequest(const TextureRequest& req);

    /**
     * generateMapFromRequest - Execute a MapRequest and return a populated GameMap.
     */
    static GameMap generateMapFromRequest(const MapRequest& req,
                                           int widthTiles, int heightTiles,
                                           int tileW, int tileH,
                                           const std::string& tilesetPath);

private:
    /** Convert a string to lowercase for case-insensitive matching. */
    static std::string toLower(const std::string& s);

    /** Return true if haystack contains needle (case-insensitive). */
    static bool contains(const std::string& haystack, const std::string& needle);
};
