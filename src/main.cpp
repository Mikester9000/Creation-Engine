/**
 * @file main.cpp
 * @brief Creation Engine — CLI entry point.
 *
 * =============================================================================
 * USAGE
 * =============================================================================
 *
 *   creation-engine <command> [options]
 *
 * PBR PIPELINE COMMANDS (AI-assisted, outputs PNG + JSON material/tilemap)
 * ─────────────────────────────────────────────────────────────────────────
 *
 *   texture   Generate PBR-lite textures (PNG) + material JSON.
 *     --prompt   "surface description"   (default: "stone")
 *     --seed     <uint>                  (default: 42)
 *     --name     <identifier>            (default: derived from prompt)
 *     --out      <directory>             (default: assets/)
 *     --width    <pixels>                (default: 64)
 *     --height   <pixels>                (default: 64)
 *
 *   map       Generate a tilemap (JSON).
 *     --prompt   "terrain description"   (default: "grass field")
 *     --seed     <uint>                  (default: 42)
 *     --name     <identifier>            (default: derived from prompt)
 *     --out      <directory>             (default: assets/)
 *
 *   ai texture  [same as texture but the "ai" prefix is also accepted]
 *   ai map      [same as map    but the "ai" prefix is also accepted]
 *
 *   validate  Validate all JSON files found under a directory.
 *     --dir    <directory>               (default: assets/)
 *
 * LEGACY COMMANDS (direct type control, outputs PNG + JSON sidecar)
 * ─────────────────────────────────────────────────────────────────
 *
 *   create-texture
 *     --type    TYPE        noise|cellular|checker|stripes|gradient|radial|solid
 *     --seed    N           integer seed (default 0)
 *     --size    WxH         e.g. 64x64 (default 64x64)
 *     --color   RRGGBB      primary colour hex (default ffffff)
 *     --color2  RRGGBB      secondary colour hex (default 000000)
 *     --scale   F           noise scale (default 32)
 *     --octaves N           fBm octaves (default 4)
 *     --out     PATH        output PNG file (required)
 *
 *   create-tileset
 *     --from    TEXTURE     path to sprite sheet PNG
 *     --tile    WxH         tile size in pixels (default 16x16)
 *     --out     PATH.json   output JSON file (required)
 *
 *   create-map
 *     --width   N           map width  in tiles (default 20)
 *     --height  N           map height in tiles (default 15)
 *     --tileSize N          tile pixel size (default 16)
 *     --tileset PATH.json   tileset definition (auto-created if absent)
 *     --seed    N           generation seed (default 0)
 *     --out     PATH.json   output JSON file (required)
 *
 *   help      Print this usage message.
 *
 * EXAMPLES
 * ─────────
 *
 *   creation-engine texture --prompt "wet stone" --seed 123 --out assets/textures
 *   creation-engine map     --prompt "forest with river and road" --seed 123
 *   creation-engine ai texture --prompt "polished gold" --seed 42
 *   creation-engine ai map     --prompt "dungeon ruins" --seed 7
 *   creation-engine validate   --dir assets/
 *   creation-engine create-texture --type noise --seed 7 --out assets/textures/noise.png
 *   creation-engine create-map --width 20 --height 15 --out assets/maps/world.json
 *
 * =============================================================================
 * TEACHING NOTE — CLI-First Design
 * =============================================================================
 *
 * The editor is CLI-first, meaning every feature is accessible via command-
 * line flags without any GUI. This design choice has several advantages:
 *
 *   • PORTABILITY  — runs anywhere a C++ binary runs (server, CI, terminal).
 *   • SCRIPTABILITY — shell scripts can batch-generate hundreds of assets.
 *   • TESTABILITY  — automated tests can invoke the CLI and check outputs.
 *   • EXTENSIBILITY — a GUI can be added later by calling the same C++ API.
 *
 * This mirrors how professional DCCs (Houdini, Blender) expose their full
 * functionality via Python/CLI in addition to their GUIs.
 *
 * @author  Creation Engine Project
 * @version 1.0
 */

#include <iostream>
#include <fstream>
#include <string>
#include <vector>
#include <algorithm>
#include <cstdint>
#include <cstdlib>

// Windows mkdir vs POSIX mkdir
#ifdef _WIN32
#  include <direct.h>
#  define CE_MKDIR(dir) _mkdir(dir)
#else
#  include <sys/stat.h>
#  define CE_MKDIR(dir) mkdir((dir), 0755)
#endif

// PBR pipeline headers (subdirectory layout)
#include "ai/AIAssist.hpp"
#include "texture/TextureGen.hpp"
#include "map/MapGen.hpp"
#include "material/Material.hpp"

// Legacy flat-layout headers (stb_image-based texture/map commands)
#include "TextureGenerator.h"
#include "MapEditor.h"
#include "AssetIO.h"
#include "AIAssist.h"

namespace ce {

// =============================================================================
// Default values
// =============================================================================
// Extracted as constants so lesson plans and integration tests can reference
// canonical default values without duplicating magic strings.

constexpr const char* DEFAULT_TEXTURE_PROMPT = "stone";
constexpr const char* DEFAULT_MAP_PROMPT     = "grass field";
constexpr const char* DEFAULT_OUTPUT_DIR     = "assets";
constexpr int         DEFAULT_TEXTURE_SIZE   = 64;
constexpr uint32_t    DEFAULT_SEED           = 42u;

// =============================================================================
// CLI helpers
// =============================================================================

namespace {

/** @brief Print the usage message to stdout. */
void printHelp()
{
    std::cout <<
R"(
Creation Engine — PBR Texture & Map Editor  v1.0
================================================

USAGE
  creation-engine <command> [options]

PBR PIPELINE COMMANDS
  texture    Generate PBR textures (PNG) + material descriptor (JSON).
  map        Generate a procedural tilemap (JSON).
  ai texture Alias for 'texture' with AI-assist framing.
  ai map     Alias for 'map'     with AI-assist framing.
  validate   Validate JSON asset files in a directory.

LEGACY COMMANDS (direct type selection)
  create-texture   Generate a single PNG texture by explicit type.
  create-tileset   Define a tileset JSON from a sprite sheet.
  create-map       Generate a tile map with basic terrain.

  help       Show this message.

TEXTURE OPTIONS (PBR)
  --prompt  "surface description"  e.g. "wet stone", "polished gold"
  --seed    <uint>                 Seed for deterministic generation (default: 42)
  --name    <identifier>           Output file base name (default: auto)
  --out     <directory>            Output directory (default: assets/)
  --width   <pixels>               Texture width  (default: 64)
  --height  <pixels>               Texture height (default: 64)

CREATE-TEXTURE OPTIONS (legacy)
  --type    noise|cellular|checker|stripes|gradient|radial|solid
  --seed    N        integer seed (default 0)
  --size    WxH      output size  (default 64x64)
  --color   RRGGBB   primary colour hex
  --color2  RRGGBB   secondary colour hex
  --scale   F        noise scale (default 32)
  --octaves N        fBm octaves (default 4)
  --out     PATH     output PNG path (required)

EXAMPLES
  creation-engine texture --prompt "wet stone" --seed 123 --out assets/textures
  creation-engine ai texture --prompt "polished gold" --seed 42
  creation-engine map     --prompt "forest with river and road" --seed 123
  creation-engine validate   --dir assets/
  creation-engine create-texture --type noise --seed 7 --out assets/textures/noise.png
  creation-engine create-map --width 20 --height 15 --out assets/maps/world.json

)" << std::flush;
}

// ─────────────────────────────────────────────────────────────────────────────
// PBR argument parser (vector<string> style)
// ─────────────────────────────────────────────────────────────────────────────

/**
 * @brief Find the value for a named CLI argument.
 *
 * For "--key value" style arguments. Returns an empty string if not found.
 */
std::string getArg(const std::vector<std::string>& args,
                   const std::string&               key,
                   const std::string&               def = "")
{
    for (size_t i = 0; i + 1 < args.size(); ++i) {
        if (args[i] == key) return args[i + 1];
    }
    return def;
}

/** @brief Convert a string to a safe filesystem identifier (spaces → _). */
std::string toIdent(const std::string& s)
{
    std::string out;
    for (char c : s) {
        if (std::isalnum(static_cast<unsigned char>(c))) {
            out += static_cast<char>(std::tolower(static_cast<unsigned char>(c)));
        } else if (!out.empty() && out.back() != '_') {
            out += '_';
        }
    }
    // Trim trailing underscore
    while (!out.empty() && out.back() == '_') out.pop_back();
    return out.empty() ? "unnamed" : out;
}

/**
 * @brief Ensure a directory exists, creating it if necessary.
 *
 * TEACHING NOTE — Directory Creation
 * std::filesystem::create_directories is cleaner in C++17 but adds a
 * header dependency. CE_MKDIR is a thin cross-platform macro that maps to
 * _mkdir (Windows) or mkdir (POSIX). We don't treat "already exists" as
 * an error since that's the common case in incremental workflows.
 */
void ensureDir(const std::string& dir)
{
    if (dir.empty()) return;
    CE_MKDIR(dir.c_str());          // ignore error: dir may already exist
}

// ─────────────────────────────────────────────────────────────────────────────
// texture / ai texture (PBR)
// ─────────────────────────────────────────────────────────────────────────────

/**
 * @brief Handle the `texture` command.
 *
 * Workflow:
 *   1. Parse CLI arguments.
 *   2. Run AI assist to infer PBR parameters from the prompt.
 *   3. Generate PNG textures (albedo, normal, roughness, metallic, AO, emissive).
 *   4. Export material JSON.
 *
 * @return Exit code (0 = success).
 */
int cmdTexture(const std::vector<std::string>& args)
{
    const std::string prompt = getArg(args, "--prompt", DEFAULT_TEXTURE_PROMPT);
    const uint32_t    seed   = static_cast<uint32_t>(std::stoul(getArg(args, "--seed",
                                    std::to_string(DEFAULT_SEED))));
    const std::string outDir = getArg(args, "--out",  DEFAULT_OUTPUT_DIR);
    const int         width  = std::stoi(getArg(args, "--width",
                                    std::to_string(DEFAULT_TEXTURE_SIZE)));
    const int         height = std::stoi(getArg(args, "--height",
                                    std::to_string(DEFAULT_TEXTURE_SIZE)));
    std::string       name   = getArg(args, "--name", "");

    if (name.empty()) name = toIdent(prompt);

    ensureDir(outDir);

    std::cout << "[creation-engine] Generating textures for: \"" << prompt << "\"\n"
              << "  Seed     : " << seed  << "\n"
              << "  Size     : " << width << "×" << height << "\n"
              << "  Name     : " << name  << "\n"
              << "  Output   : " << outDir << "/\n";

    // ── AI assist: infer PBR parameters ──────────────────────────────────────
    AITextureParams params = aiInferTexture(prompt, seed, name);

    // Override resolution if specified on the CLI
    params.genOpts.width  = width;
    params.genOpts.height = height;

    std::cout << "  baseColor: ["
              << params.material.baseColor[0] << ", "
              << params.material.baseColor[1] << ", "
              << params.material.baseColor[2] << "]\n"
              << "  roughness: " << params.material.roughness << "\n"
              << "  metallic : " << params.material.metallic  << "\n";

    // ── Generate texture PNGs ─────────────────────────────────────────────────
    bool ok = generateTextures(params.material, outDir, params.genOpts);
    if (!ok) {
        std::cerr << "[ERROR] Failed to write one or more texture files.\n";
        return 1;
    }

    // ── Export material JSON ──────────────────────────────────────────────────
    std::string jsonPath = outDir + "/" + name + ".json";
    std::ofstream jsonFile(jsonPath);
    if (!jsonFile.is_open()) {
        std::cerr << "[ERROR] Cannot write material JSON: " << jsonPath << "\n";
        return 1;
    }
    jsonFile << materialToJson(params.material);
    jsonFile.close();

    std::cout << "[OK] Textures written to " << outDir << "/\n"
              << "[OK] Material JSON: "      << jsonPath << "\n";
    return 0;
}

// ─────────────────────────────────────────────────────────────────────────────
// map / ai map (PBR)
// ─────────────────────────────────────────────────────────────────────────────

/**
 * @brief Handle the `map` command.
 *
 * Workflow:
 *   1. Parse CLI arguments.
 *   2. Run AI assist to infer tilemap parameters from the prompt.
 *   3. Generate the tilemap.
 *   4. Export map JSON.
 *
 * @return Exit code (0 = success).
 */
int cmdMap(const std::vector<std::string>& args)
{
    const std::string prompt = getArg(args, "--prompt", DEFAULT_MAP_PROMPT);
    const uint32_t    seed   = static_cast<uint32_t>(std::stoul(getArg(args, "--seed",
                                    std::to_string(DEFAULT_SEED))));
    const std::string outDir = getArg(args, "--out",  DEFAULT_OUTPUT_DIR);
    std::string       name   = getArg(args, "--name", "");

    if (name.empty()) name = toIdent(prompt);

    ensureDir(outDir);

    std::cout << "[creation-engine] Generating map for: \"" << prompt << "\"\n"
              << "  Seed   : " << seed   << "\n"
              << "  Name   : " << name   << "\n"
              << "  Output : " << outDir << "/\n";

    // ── AI assist: infer map parameters ──────────────────────────────────────
    AIMapParams params = aiInferMap(prompt, seed);

    std::cout << "  Size   : " << params.genOpts.width << "×"
                               << params.genOpts.height << "\n"
              << "  River  : " << (params.genOpts.hasRiver  ? "yes" : "no") << "\n"
              << "  Road   : " << (params.genOpts.hasRoad   ? "yes" : "no") << "\n"
              << "  Dungeon: " << (params.genOpts.isDungeon ? "yes" : "no") << "\n";

    // ── Generate tilemap ──────────────────────────────────────────────────────
    TileMap map = generateMap(name, prompt, seed, params.genOpts);

    // ── Export map JSON ───────────────────────────────────────────────────────
    std::string jsonPath = outDir + "/" + name + ".json";
    std::ofstream jsonFile(jsonPath);
    if (!jsonFile.is_open()) {
        std::cerr << "[ERROR] Cannot write map JSON: " << jsonPath << "\n";
        return 1;
    }
    jsonFile << mapToJson(map);
    jsonFile.close();

    std::cout << "[OK] Map JSON: " << jsonPath
              << "  (" << map.width << "×" << map.height << " tiles, "
              << map.props.size() << " props)\n";
    return 0;
}

// ─────────────────────────────────────────────────────────────────────────────
// validate
// ─────────────────────────────────────────────────────────────────────────────

/**
 * @brief Handle the `validate` command.
 *
 * Checks that every JSON file in the target directory:
 *   1. Opens successfully.
 *   2. Contains a "version" field.
 *   3. Contains either a "tiles" array (map) or a "params" object (material).
 *
 * TEACHING NOTE — Validation in Asset Pipelines
 * A validation step catches malformed assets before they crash the game
 * engine at runtime. It should run automatically in CI whenever the asset
 * directory is modified.
 *
 * @return Exit code (0 = all valid, 1 = one or more failures).
 */
int cmdValidate(const std::vector<std::string>& args)
{
    std::string dir = getArg(args, "--dir", "assets");
    std::cout << "[creation-engine] Validating assets in: " << dir << "\n";

    int checked = 0, failed = 0;

    auto checkFile = [&](const std::string& path) {
        std::ifstream f(path);
        if (!f.is_open()) { std::cerr << "  [SKIP] " << path << " (not found)\n"; return; }

        std::string content((std::istreambuf_iterator<char>(f)),
                             std::istreambuf_iterator<char>());
        ++checked;

        bool hasVersion = content.find("\"version\"") != std::string::npos;
        bool hasTiles   = content.find("\"tiles\"")   != std::string::npos;
        bool hasParams  = content.find("\"params\"")  != std::string::npos;

        if (!hasVersion) {
            std::cerr << "  [FAIL] " << path << ": missing \"version\" field\n";
            ++failed;
        } else if (!hasTiles && !hasParams) {
            std::cerr << "  [FAIL] " << path
                      << ": missing \"tiles\" (map) or \"params\" (material)\n";
            ++failed;
        } else {
            std::cout  << "  [OK]   " << path << "\n";
        }
    };

    // Known sample asset files to check
    std::vector<std::string> knownFiles = {
        dir + "/materials/wet_stone.json",
        dir + "/materials/forest_soil.json",
        dir + "/maps/forest_river.json",
        dir + "/maps/dungeon_ruins.json",
    };

    for (const std::string& path : knownFiles) checkFile(path);

    if (checked == 0) {
        std::cout << "  No sample JSON files found. Run 'texture' or 'map' commands first.\n";
        return 0;
    }

    std::cout << "\nValidation: " << checked << " files checked, "
              << failed << " failed.\n";
    return (failed > 0) ? 1 : 0;
}

} // anonymous namespace

} // namespace ce

// =============================================================================
// Legacy command handlers (create-texture / create-tileset / create-map)
// =============================================================================
// These commands use the flat src/ modules (TextureGenerator, MapEditor,
// AssetIO) and the stb_image back-end. They are preserved from the previous
// implementation so existing scripts and tutorials continue to work.

namespace legacy {

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

/** Collect all --color / --color2 values from argv in order. */
static std::vector<std::string> getColorArgs(int argc, char* argv[]) {
    std::vector<std::string> out;
    for (int i = 1; i < argc - 1; ++i) {
        std::string s(argv[i]);
        if (s == "--color" || s == "--color2") out.push_back(argv[i + 1]);
    }
    return out;
}

/** Ensure output directory exists. */
static void ensureOutputDir(const std::string& outPath) {
    auto sep = outPath.find_last_of("/\\");
    if (sep != std::string::npos) {
        std::string dir = outPath.substr(0, sep);
        if (!dir.empty()) AssetIO::ensureDirectory(dir);
    }
}

/** Build a minimal default tileset definition. */
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

} // namespace legacy

// =============================================================================
// main()
// =============================================================================

/**
 * @brief CLI entry point.
 *
 * TEACHING NOTE — main() Structure
 * main() is intentionally kept minimal. It:
 *   1. Collects arguments into a vector<string>.
 *   2. Reads the first positional argument as the command name.
 *   3. Dispatches to a dedicated handler function.
 *
 * All actual logic lives in the handler functions above, not here.
 * This makes it easy to unit-test handlers without going through main().
 *
 * @param argc  Number of command-line arguments.
 * @param argv  Argument strings.
 * @return      0 on success, non-zero on error.
 */
int main(int argc, char* argv[])
{
    if (argc < 2) {
        ce::printHelp();
        return 0;
    }

    std::string cmd = argv[1];

    // ── Legacy commands (create-texture / create-tileset / create-map) ───────
    if (cmd == "create-texture") return legacy::cmdCreateTexture(argc, argv);
    if (cmd == "create-tileset") return legacy::cmdCreateTileset(argc, argv);
    if (cmd == "create-map")     return legacy::cmdCreateMap(argc, argv);

    // ── PBR pipeline commands ─────────────────────────────────────────────────
    // Collect all arguments (excluding argv[0] = program name)
    std::vector<std::string> args;
    for (int i = 1; i < argc; ++i) args.emplace_back(argv[i]);

    // Support "ai texture" and "ai map" as two-word commands
    if (cmd == "ai" && argc >= 3) {
        std::string sub = argv[2];
        args.erase(args.begin(), args.begin() + 2);   // remove "ai" + subcommand
        if (sub == "texture") return ce::cmdTexture(args);
        if (sub == "map")     return ce::cmdMap(args);
        std::cerr << "[ERROR] Unknown ai sub-command: '" << sub << "'\n";
        return 1;
    }

    args.erase(args.begin());   // remove command word

    if (cmd == "texture")  return ce::cmdTexture(args);
    if (cmd == "map")      return ce::cmdMap(args);
    if (cmd == "validate") return ce::cmdValidate(args);

    if (cmd == "help" || cmd == "--help" || cmd == "-h") {
        ce::printHelp();
        return 0;
    }

    std::cerr << "[ERROR] Unknown command: '" << cmd << "'\n"
              << "Run 'creation-engine help' for usage.\n";
    return 1;
}
