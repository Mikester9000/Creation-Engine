/**
 * AIAssist.cpp - Implementation of keyword-based AI assistance.
 *
 * The interpretTexture and interpretMap functions scan the user's prompt for
 * known keywords and select appropriate generation settings. Adding new themes
 * is as simple as adding another if/else branch.
 */

#include "AIAssist.h"
#include <algorithm>
#include <cctype>

// ============================================================
//  Private helpers
// ============================================================

std::string AIAssist::toLower(const std::string& s) {
    std::string out = s;
    std::transform(out.begin(), out.end(), out.begin(),
                   [](unsigned char c) { return static_cast<char>(std::tolower(c)); });
    return out;
}

bool AIAssist::contains(const std::string& haystack, const std::string& needle) {
    return toLower(haystack).find(toLower(needle)) != std::string::npos;
}

// ============================================================
//  interpretTexture
// ============================================================

TextureRequest AIAssist::interpretTexture(const std::string& prompt, uint32_t seed,
                                           int width, int height) {
    TextureRequest req;
    req.seed   = seed;
    req.width  = width;
    req.height = height;

    // Default: grey Perlin noise (generic stone/surface)
    req.type    = "noise";
    req.color1  = {200, 200, 200, 255};
    req.color2  = {50,  50,  50,  255};
    req.scale   = 32.0f;
    req.octaves = 4;

    if (contains(prompt, "lava") || contains(prompt, "fire") || contains(prompt, "magma")) {
        req.type   = "cellular";
        req.color1 = {255,  60,   0, 255};   // bright orange
        req.color2 = {100,   0,   0, 255};   // deep red
        req.scale  = 20.0f;

    } else if (contains(prompt, "ocean") || contains(prompt, "water") || contains(prompt, "sea")) {
        req.type    = "noise";
        req.color1  = {0,   80, 200, 255};   // deep blue
        req.color2  = {0,  200, 255, 255};   // light cyan
        req.scale   = 40.0f;
        req.octaves = 5;

    } else if (contains(prompt, "grass") || contains(prompt, "meadow")) {
        req.type   = "noise";
        req.color1 = {0, 180,  0, 255};
        req.color2 = {0, 100,  0, 255};
        req.scale  = 25.0f;

    } else if (contains(prompt, "stone") || contains(prompt, "rock") || contains(prompt, "mossy")) {
        req.type   = "cellular";
        req.color1 = {120, 120, 120, 255};
        req.color2 = contains(prompt, "mossy") ?
                     Color{40, 100, 40, 255} : Color{60, 60, 60, 255};
        req.scale  = 15.0f;

    } else if (contains(prompt, "sand") || contains(prompt, "desert")) {
        req.type    = "noise";
        req.color1  = {240, 210, 130, 255};
        req.color2  = {180, 150,  80, 255};
        req.scale   = 50.0f;
        req.octaves = 3;

    } else if (contains(prompt, "space") || contains(prompt, "nebula") || contains(prompt, "star")) {
        req.type    = "noise";
        req.color1  = {150,   0, 255, 255};  // purple
        req.color2  = {  0,   0,  20, 255};  // near-black
        req.scale   = 60.0f;
        req.octaves = 6;

    } else if (contains(prompt, "checker") || contains(prompt, "checkerboard") ||
               contains(prompt, "tile")) {
        req.type   = "checker";
        req.color1 = {255, 255, 255, 255};
        req.color2 = {  0,   0,   0, 255};

    } else if (contains(prompt, "gradient") || contains(prompt, "sky")) {
        req.type   = "gradient";
        req.color1 = {100, 180, 255, 255};   // sky blue
        req.color2 = {255, 200,  80, 255};   // warm horizon

    } else if (contains(prompt, "wood") || contains(prompt, "bark")) {
        req.type    = "noise";
        req.color1  = {120,  80, 40, 255};
        req.color2  = { 60,  30, 10, 255};
        req.scale   = 10.0f;
        req.octaves = 6;

    } else if (contains(prompt, "snow") || contains(prompt, "ice") || contains(prompt, "frost")) {
        req.type    = "noise";
        req.color1  = {240, 248, 255, 255};
        req.color2  = {180, 210, 255, 255};
        req.scale   = 30.0f;
        req.octaves = 3;

    } else if (contains(prompt, "mud") || contains(prompt, "dirt")) {
        req.type   = "noise";
        req.color1 = {100,  70, 30, 255};
        req.color2 = { 60,  40, 10, 255};
        req.scale  = 20.0f;

    } else if (contains(prompt, "cloud")) {
        req.type    = "noise";
        req.color1  = {255, 255, 255, 255};
        req.color2  = {180, 200, 230, 255};
        req.scale   = 50.0f;
        req.octaves = 5;
    }

    return req;
}

// ============================================================
//  interpretMap
// ============================================================

MapRequest AIAssist::interpretMap(const std::string& prompt, uint32_t seed) {
    MapRequest req;
    req.seed = seed;

    if (contains(prompt, "dungeon") || contains(prompt, "cave")) {
        // Dense walls, no natural features
        req.generateTerrain = true;
        req.threshold       = 0.45f;
        req.scale           = 4.0f;
        req.generateRiver   = false;
        req.generateVillage = false;

    } else if (contains(prompt, "forest")) {
        req.generateTerrain = true;
        req.threshold       = 0.60f;
        req.scale           = 6.0f;
        req.generateRiver   = contains(prompt, "river") || contains(prompt, "stream");
        req.generateVillage = false;

    } else if (contains(prompt, "village") || contains(prompt, "town")) {
        req.generateTerrain = true;
        req.threshold       = 0.70f;  // mostly open for buildings
        req.scale           = 8.0f;
        req.generateVillage = true;
        req.buildingCount   = contains(prompt, "town") ? 10 : 5;
        req.generateRiver   = contains(prompt, "river");

    } else if (contains(prompt, "plain") || contains(prompt, "field") ||
               contains(prompt, "open")) {
        req.generateTerrain = true;
        req.threshold       = 0.80f;  // very few walls
        req.scale           = 10.0f;
        req.generateRiver   = false;
        req.generateVillage = false;

    } else if (contains(prompt, "island") || contains(prompt, "coast")) {
        req.generateTerrain = true;
        req.threshold       = 0.50f;
        req.scale           = 5.0f;
        req.generateRiver   = contains(prompt, "river");
        req.generateVillage = false;

    } else {
        // Default: medium density terrain
        req.generateTerrain = true;
        req.threshold       = 0.55f;
        req.scale           = 5.0f;
    }

    // River can be requested independently of the biome keyword.
    if (contains(prompt, "river") || contains(prompt, "stream") || contains(prompt, "water")) {
        req.generateRiver = true;
    }

    return req;
}

// ============================================================
//  generateTextureFromRequest
// ============================================================

Texture AIAssist::generateTextureFromRequest(const TextureRequest& req) {
    if (req.type == "cellular") {
        return TextureGenerator::cellular(req.width, req.height, req.seed,
                                           req.scale, req.color1, req.color2);
    } else if (req.type == "checker") {
        return TextureGenerator::checkerboard(req.width, req.height,
                                               req.color1, req.color2, 8);
    } else if (req.type == "gradient") {
        return TextureGenerator::gradient(req.width, req.height,
                                           req.color1, req.color2, 90.0f);
    } else if (req.type == "radial") {
        return TextureGenerator::radialGradient(req.width, req.height,
                                                 req.color1, req.color2);
    } else if (req.type == "solid") {
        return TextureGenerator::solidColor(req.width, req.height, req.color1);
    } else {
        // Default: Perlin/fBm noise
        return TextureGenerator::perlinNoise(req.width, req.height, req.seed,
                                              req.octaves, req.scale, req.color1);
    }
}

// ============================================================
//  generateMapFromRequest
// ============================================================

GameMap AIAssist::generateMapFromRequest(const MapRequest& req,
                                          int widthTiles, int heightTiles,
                                          int tileW, int tileH,
                                          const std::string& tilesetPath) {
    // Start with a blank map.
    GameMap map = MapEditor::createEmpty(widthTiles, heightTiles, tileW, tileH, tilesetPath);

    // Apply each enabled generation step in order.
    if (req.generateTerrain) {
        MapEditor::generateTerrain(map, req.seed, req.scale, req.threshold);
    }
    if (req.generateRiver) {
        // Use a different seed offset so the river position is independent of terrain.
        MapEditor::generateRiver(map, req.seed + 1);
    }
    if (req.generateVillage) {
        MapEditor::generateVillage(map, req.seed + 2, req.buildingCount);
    }

    // Always add a default player spawn point in the centre of the map.
    MapEditor::addSpawnPoint(map, "player_start",
                              static_cast<float>(widthTiles  / 2 * tileW),
                              static_cast<float>(heightTiles / 2 * tileH));

    return map;
}
