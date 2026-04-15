/**
 * main.cpp - Creation Engine CLI entry point.
 *
 * Supported commands:
 *
 *   creation-engine create-texture
 *       --type    TYPE        noise|cellular|checker|stripes|gradient|radial|solid
 *       --seed    N           integer seed (default 0)
 *       --size    WxH         e.g. 64x64 (default 64x64)
 *       --color   RRGGBB      primary colour hex (default ffffff)
 *       --color2  RRGGBB      secondary colour hex (default 000000)
 *       --scale   F           noise scale (default 32)
 *       --octaves N           fBm octaves (default 4)
 *       --out     PATH        output PNG file (required)
 *
 *   creation-engine create-tileset
 *       --from    TEXTURE     path to sprite sheet PNG
 *       --tile    WxH         tile size in pixels (default 16x16)
 *       --out     PATH.json   output JSON file (required)
 *
 *   creation-engine create-map
 *       --width   N           map width  in tiles (default 20)
 *       --height  N           map height in tiles (default 15)
 *       --tileSize N          tile pixel size (default 16)
 *       --tileset PATH.json   tileset definition (auto-created if absent)
 *       --seed    N           generation seed (default 0)
 *       --out     PATH.json   output JSON file (required)
 *
 *   creation-engine ai texture
 *       --prompt  "TEXT"      natural-language description (required)
 *       --seed    N           seed (default 0)
 *       --size    WxH         output size (default 64x64)
 *       --out     PATH        output PNG file (required)
 *
 *   creation-engine ai map
 *       --prompt  "TEXT"      natural-language description (required)
 *       --width   N           map width  in tiles (default 20)
 *       --height  N           map height in tiles (default 15)
 *       --tileSize N          tile pixel size (default 16)
 *       --tileset PATH.json   tileset definition (auto-created if absent)
 *       --seed    N           seed (default 0)
 *       --out     PATH.json   output JSON file (required)
 */

#include <iostream>
#include <string>
#include <vector>
#include <fstream>
#include <cstdlib>

#include "TextureGenerator.h"
#include "MapEditor.h"
#include "AssetIO.h"
#include "AIAssist.h"

// ============================================================
//  Argument parsing helpers
// ============================================================

/** Return the argument following flag, or "" if not found. */
static std::string getArg(int argc, char* argv[], const std::string& flag) {
    for (int i = 1; i < argc - 1; ++i) {
        if (std::string(argv[i]) == flag) return argv[i + 1];
    }
    return "";
}

/** Parse "RRGGBB" hex string into a Color. Returns grey on error. */
static Color parseHex(const std::string& hex) {
    if (hex.size() < 6) return {128, 128, 128, 255};
    try {
        unsigned r = std::stoul(hex.substr(0, 2), nullptr, 16);
        unsigned g = std::stoul(hex.substr(2, 2), nullptr, 16);
        unsigned b = std::stoul(hex.substr(4, 2), nullptr, 16);
        return {static_cast<uint8_t>(r), static_cast<uint8_t>(g),
                static_cast<uint8_t>(b), 255};
    } catch (...) {
        return {128, 128, 128, 255};
    }
}

/** Parse "WxH" string into w and h. Defaults to 64x64 on error. */
static void parseSize(const std::string& s, int& w, int& h) {
    auto pos = s.find('x');
    if (pos == std::string::npos) { w = 64; h = 64; return; }
    try {
        w = std::stoi(s.substr(0, pos));
        h = std::stoi(s.substr(pos + 1));
    } catch (...) { w = 64; h = 64; }
    if (w <= 0) w = 64;
    if (h <= 0) h = 64;
}

/**
 * Collect all --color / --color2 values from argv in order.
 * The first value is used as color1, the second as color2.
 */
static std::vector<std::string> getColorArgs(int argc, char* argv[]) {
    std::vector<std::string> out;
    for (int i = 1; i < argc - 1; ++i) {
        std::string s(argv[i]);
        if (s == "--color" || s == "--color2") out.push_back(argv[i + 1]);
    }
    return out;
}

/** Ensure output directory exists; silently succeeds if path has no directory part. */
static void ensureOutputDir(const std::string& outPath) {
    auto sep = outPath.find_last_of("/\\");
    if (sep != std::string::npos) {
        std::string dir = outPath.substr(0, sep);
        if (!dir.empty()) AssetIO::ensureDirectory(dir);
    }
}

// ============================================================
//  Default tileset definition
// ============================================================

static TilesetDef defaultTileset() {
    TilesetDef ts;
    ts.texturePath = "assets/textures/default_tileset.png";
    ts.tileWidth   = 16;
    ts.tileHeight  = 16;
    ts.tiles = {
        {0, "empty",  false},
        {1, "ground", false},
        {2, "wall",   true },
        {3, "water",  false},
        {4, "bwall",  true },
        {5, "bfloor", false}
    };
    return ts;
}

/** Return tilesetPath, creating a default JSON file if the path does not exist. */
static std::string ensureTileset(const std::string& tilesetPath) {
    if (tilesetPath.empty()) {
        std::string def = "assets/maps/default.tileset.json";
        std::ifstream test(def);
        if (!test.is_open()) {
            AssetIO::ensureDirectory("assets/maps");
            AssetIO::saveTileset(def, defaultTileset());
        }
        return def;
    }
    std::ifstream test(tilesetPath);
    if (!test.is_open()) {
        ensureOutputDir(tilesetPath);
        AssetIO::saveTileset(tilesetPath, defaultTileset());
    }
    return tilesetPath;
}

// ============================================================
//  Command handlers
// ============================================================

static int cmdCreateTexture(int argc, char* argv[]) {
    std::string type     = getArg(argc, argv, "--type");
    std::string seedStr  = getArg(argc, argv, "--seed");
    std::string sizeStr  = getArg(argc, argv, "--size");
    std::string outPath  = getArg(argc, argv, "--out");
    std::string scaleStr = getArg(argc, argv, "--scale");
    std::string octStr   = getArg(argc, argv, "--octaves");

    if (type.empty())    type    = "noise";
    if (outPath.empty()) { std::cerr << "Error: --out is required\n"; return 1; }

    uint32_t seed    = seedStr.empty()  ? 0u    : static_cast<uint32_t>(std::stoul(seedStr));
    float    scale   = scaleStr.empty() ? 32.0f : std::stof(scaleStr);
    int      octaves = octStr.empty()   ? 4     : std::stoi(octStr);

    int w = 64, h = 64;
    if (!sizeStr.empty()) parseSize(sizeStr, w, h);

    auto colors = getColorArgs(argc, argv);
    Color c1 = colors.size() > 0 ? parseHex(colors[0]) : Color{255, 255, 255, 255};
    Color c2 = colors.size() > 1 ? parseHex(colors[1]) : Color{  0,   0,   0, 255};

    Texture tex;
    if      (type == "noise"    ) tex = TextureGenerator::perlinNoise(w, h, seed, octaves, scale, c1);
    else if (type == "cellular" ) tex = TextureGenerator::cellular(w, h, seed, scale, c1, c2);
    else if (type == "checker"  ) tex = TextureGenerator::checkerboard(w, h, c1, c2, 8);
    else if (type == "stripes"  ) tex = TextureGenerator::stripes(w, h, c1, c2, 8, false);
    else if (type == "gradient" ) tex = TextureGenerator::gradient(w, h, c1, c2, 90.0f);
    else if (type == "radial"   ) tex = TextureGenerator::radialGradient(w, h, c1, c2);
    else if (type == "solid"    ) tex = TextureGenerator::solidColor(w, h, c1);
    else {
        std::cerr << "Unknown texture type: " << type
                  << "\n  Valid types: noise cellular checker stripes gradient radial solid\n";
        return 1;
    }

    ensureOutputDir(outPath);
    if (!AssetIO::savePNG(outPath, tex)) return 1;

    // Write a JSON sidecar next to the PNG.
    AssetIO::saveTextureMetadata(outPath + ".meta.json", outPath, w, h, type, seed);

    std::cout << "Texture saved: " << outPath << "  (" << w << "x" << h << ")\n";
    return 0;
}

static int cmdCreateTileset(int argc, char* argv[]) {
    std::string fromPath = getArg(argc, argv, "--from");
    std::string tileStr  = getArg(argc, argv, "--tile");
    std::string outPath  = getArg(argc, argv, "--out");

    if (outPath.empty()) { std::cerr << "Error: --out is required\n"; return 1; }

    int tileW = 16, tileH = 16;
    if (!tileStr.empty()) parseSize(tileStr, tileW, tileH);

    TilesetDef ts = defaultTileset();
    if (!fromPath.empty()) ts.texturePath = fromPath;
    ts.tileWidth  = tileW;
    ts.tileHeight = tileH;

    ensureOutputDir(outPath);
    if (!AssetIO::saveTileset(outPath, ts)) return 1;
    std::cout << "Tileset saved: " << outPath << "\n";
    return 0;
}

static int cmdCreateMap(int argc, char* argv[]) {
    std::string widthStr    = getArg(argc, argv, "--width");
    std::string heightStr   = getArg(argc, argv, "--height");
    std::string tileSzStr   = getArg(argc, argv, "--tileSize");
    std::string tilesetPath = getArg(argc, argv, "--tileset");
    std::string outPath     = getArg(argc, argv, "--out");
    std::string seedStr     = getArg(argc, argv, "--seed");

    if (outPath.empty()) { std::cerr << "Error: --out is required\n"; return 1; }

    int mapW   = widthStr.empty()  ? 20 : std::stoi(widthStr);
    int mapH   = heightStr.empty() ? 15 : std::stoi(heightStr);
    int tileSz = tileSzStr.empty() ? 16 : std::stoi(tileSzStr);
    uint32_t seed = seedStr.empty() ? 0u : static_cast<uint32_t>(std::stoul(seedStr));

    tilesetPath = ensureTileset(tilesetPath);
    ensureOutputDir(outPath);

    GameMap map = MapEditor::createEmpty(mapW, mapH, tileSz, tileSz, tilesetPath);
    MapEditor::generateTerrain(map, seed, 5.0f, 0.55f);
    MapEditor::addSpawnPoint(map, "player_start",
                              static_cast<float>(mapW / 2 * tileSz),
                              static_cast<float>(mapH / 2 * tileSz));

    if (!AssetIO::saveMap(outPath, map)) return 1;
    std::cout << "Map saved: " << outPath
              << "  (" << mapW << "x" << mapH << " tiles)\n";
    return 0;
}

static int cmdAITexture(int argc, char* argv[]) {
    std::string prompt  = getArg(argc, argv, "--prompt");
    std::string seedStr = getArg(argc, argv, "--seed");
    std::string sizeStr = getArg(argc, argv, "--size");
    std::string outPath = getArg(argc, argv, "--out");

    if (outPath.empty())  { std::cerr << "Error: --out is required\n";    return 1; }
    if (prompt.empty())   { std::cerr << "Error: --prompt is required\n"; return 1; }

    uint32_t seed = seedStr.empty() ? 0u : static_cast<uint32_t>(std::stoul(seedStr));
    int w = 64, h = 64;
    if (!sizeStr.empty()) parseSize(sizeStr, w, h);

    std::cout << "Interpreting prompt: \"" << prompt << "\"\n";
    TextureRequest req = AIAssist::interpretTexture(prompt, seed, w, h);
    std::cout << "  -> type=" << req.type << "  scale=" << req.scale
              << "  octaves=" << req.octaves << "\n";

    Texture tex = AIAssist::generateTextureFromRequest(req);

    ensureOutputDir(outPath);
    if (!AssetIO::savePNG(outPath, tex)) return 1;
    AssetIO::saveTextureMetadata(outPath + ".meta.json", outPath, w, h, req.type, seed);

    std::cout << "AI texture saved: " << outPath << "  (" << w << "x" << h << ")\n";
    return 0;
}

static int cmdAIMap(int argc, char* argv[]) {
    std::string prompt      = getArg(argc, argv, "--prompt");
    std::string widthStr    = getArg(argc, argv, "--width");
    std::string heightStr   = getArg(argc, argv, "--height");
    std::string tileSzStr   = getArg(argc, argv, "--tileSize");
    std::string tilesetPath = getArg(argc, argv, "--tileset");
    std::string outPath     = getArg(argc, argv, "--out");
    std::string seedStr     = getArg(argc, argv, "--seed");

    if (outPath.empty())  { std::cerr << "Error: --out is required\n";    return 1; }
    if (prompt.empty())   { std::cerr << "Error: --prompt is required\n"; return 1; }

    int mapW   = widthStr.empty()  ? 20 : std::stoi(widthStr);
    int mapH   = heightStr.empty() ? 15 : std::stoi(heightStr);
    int tileSz = tileSzStr.empty() ? 16 : std::stoi(tileSzStr);
    uint32_t seed = seedStr.empty() ? 0u : static_cast<uint32_t>(std::stoul(seedStr));

    tilesetPath = ensureTileset(tilesetPath);
    ensureOutputDir(outPath);

    std::cout << "Interpreting map prompt: \"" << prompt << "\"\n";
    MapRequest req = AIAssist::interpretMap(prompt, seed);
    std::cout << "  -> terrain=" << req.generateTerrain
              << "  river=" << req.generateRiver
              << "  village=" << req.generateVillage
              << "  threshold=" << req.threshold << "\n";

    GameMap map = AIAssist::generateMapFromRequest(req, mapW, mapH, tileSz, tileSz, tilesetPath);

    if (!AssetIO::saveMap(outPath, map)) return 1;
    std::cout << "AI map saved: " << outPath
              << "  (" << mapW << "x" << mapH << " tiles)\n";
    return 0;
}

// ============================================================
//  print_usage
// ============================================================

static void printUsage(const char* prog) {
    std::cout <<
        "Usage:\n"
        "  " << prog << " create-texture --type TYPE --seed N --size WxH --out PATH\n"
        "  " << prog << " create-tileset --from TEXTURE --tile WxH --out PATH.json\n"
        "  " << prog << " create-map --width N --height N --tileSize N [--tileset PATH] --out PATH.json\n"
        "  " << prog << " ai texture --prompt \"TEXT\" [--seed N] [--size WxH] --out PATH\n"
        "  " << prog << " ai map --prompt \"TEXT\" [--width N] [--height N] [--seed N] --out PATH.json\n"
        "\n"
        "Texture types: noise cellular checker stripes gradient radial solid\n"
        "AI texture prompts: lava, ocean, grass, stone, sand, space, checker, sky, wood, snow...\n"
        "AI map prompts: dungeon, forest, forest with river, village, town, plains, island...\n";
}

// ============================================================
//  main
// ============================================================

int main(int argc, char* argv[]) {
    if (argc < 2) {
        printUsage(argv[0]);
        return 0;
    }

    std::string cmd = argv[1];

    if (cmd == "create-texture") return cmdCreateTexture(argc, argv);
    if (cmd == "create-tileset") return cmdCreateTileset(argc, argv);
    if (cmd == "create-map")     return cmdCreateMap(argc, argv);

    if (cmd == "ai" && argc >= 3) {
        std::string sub = argv[2];
        if (sub == "texture") return cmdAITexture(argc, argv);
        if (sub == "map")     return cmdAIMap(argc, argv);
        std::cerr << "Unknown ai sub-command: " << sub << "\n";
        return 1;
    }

    if (cmd == "--help" || cmd == "-h") {
        printUsage(argv[0]);
        return 0;
    }

    std::cerr << "Unknown command: " << cmd << "\n";
    printUsage(argv[0]);
    return 1;
}
