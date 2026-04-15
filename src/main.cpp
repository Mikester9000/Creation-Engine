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
 * COMMANDS
 * ─────────
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

// Windows mkdir vs POSIX mkdir
#ifdef _WIN32
#  include <direct.h>
#  define CE_MKDIR(dir) _mkdir(dir)
#else
#  include <sys/stat.h>
#  define CE_MKDIR(dir) mkdir((dir), 0755)
#endif

#include "ai/AIAssist.hpp"
#include "texture/TextureGen.hpp"
#include "map/MapGen.hpp"
#include "material/Material.hpp"

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

COMMANDS
  texture    Generate PBR textures (PNG) + material descriptor (JSON).
  map        Generate a procedural tilemap (JSON).
  ai texture Alias for 'texture' with AI-assist framing.
  ai map     Alias for 'map'     with AI-assist framing.
  validate   Validate JSON asset files in a directory.
  help       Show this message.

TEXTURE OPTIONS
  --prompt  "surface description"  e.g. "wet stone", "polished gold"
  --seed    <uint>                 Seed for deterministic generation (default: 42)
  --name    <identifier>           Output file base name (default: auto)
  --out     <directory>            Output directory (default: assets/)
  --width   <pixels>               Texture width  (default: 64)
  --height  <pixels>               Texture height (default: 64)

MAP OPTIONS
  --prompt  "terrain description"  e.g. "forest with river and road"
  --seed    <uint>                 Seed for deterministic generation (default: 42)
  --name    <identifier>           Output file base name (default: auto)
  --out     <directory>            Output directory (default: assets/)

VALIDATE OPTIONS
  --dir     <directory>            Directory to scan for JSON files (default: assets/)

EXAMPLES
  creation-engine texture --prompt "wet stone" --seed 123 --out assets/textures
  creation-engine map     --prompt "forest with river and road" --seed 123
  creation-engine ai texture --prompt "polished gold" --seed 42
  creation-engine ai map     --prompt "dungeon ruins" --seed 7
  creation-engine validate   --dir assets/

GENERATED FILES (texture command)
  <out>/<name>_albedo.png
  <out>/<name>_normal.png
  <out>/<name>_roughness.png
  <out>/<name>_metallic.png
  <out>/<name>_ao.png
  <out>/<name>_emissive.png    (only if emissive material)
  <out>/<name>.json            (PBR material descriptor)

GENERATED FILES (map command)
  <out>/<name>.json            (tilemap data)

)" << std::flush;
}

// ─────────────────────────────────────────────────────────────────────────────
// Argument parser
// ─────────────────────────────────────────────────────────────────────────────

/**
 * @brief Find the value for a named CLI argument.
 *
 * For "--key value" style arguments. Returns an empty string if not found.
 *
 * TEACHING NOTE — Argument Parsing
 * This manual scan is easy to understand but O(n) per lookup. Production
 * parsers (getopt, CLI11, argparse) use hashed structures for O(1) lookup
 * and also handle short flags, required args, and type validation.
 *
 * @param args  Full argv vector (excluding argv[0]).
 * @param key   Flag name including "--" prefix.
 * @param def   Default value if key is absent.
 * @return      Value string following the key, or `def`.
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
    // Remove trailing underscore
    while (!out.empty() && out.back() == '_') out.pop_back();
    return out.empty() ? "material" : out;
}

/** @brief Ensure a directory exists (creates it if necessary). */
void ensureDir(const std::string& dir)
{
    CE_MKDIR(dir.c_str());
}

} // anonymous namespace

// =============================================================================
// Command handlers
// =============================================================================

// ─────────────────────────────────────────────────────────────────────────────
// texture / ai texture
// ─────────────────────────────────────────────────────────────────────────────

/**
 * @brief Handle the `texture` command.
 *
 * Workflow:
 *   1. Parse CLI arguments.
 *   2. Run AI assist to infer PBR parameters from the prompt.
 *   3. Generate texture PNG files.
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
    std::string       name   = getArg(args, "--name", "");
    const int         width  = std::stoi(getArg(args, "--width",
                                    std::to_string(DEFAULT_TEXTURE_SIZE)));
    const int         height = std::stoi(getArg(args, "--height",
                                    std::to_string(DEFAULT_TEXTURE_SIZE)));

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
// map / ai map
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
 * engine at runtime. It should run automatically in CI (Continuous
 * Integration) whenever the asset directory is modified. Think of it as
 * a "type checker" for your data files.
 *
 * @return Exit code (0 = all valid, 1 = one or more failures).
 */
int cmdValidate(const std::vector<std::string>& args)
{
    std::string dir = getArg(args, "--dir", "assets");
    std::cout << "[creation-engine] Validating assets in: " << dir << "\n";

    // Collect all .json files by scanning common subdirectories
    std::vector<std::string> subdirs = {
        dir,
        dir + "/textures",
        dir + "/materials",
        dir + "/maps",
    };

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

} // namespace ce

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
    // Collect all arguments (excluding argv[0] = program name)
    std::vector<std::string> args;
    for (int i = 1; i < argc; ++i) args.emplace_back(argv[i]);

    if (args.empty()) {
        ce::printHelp();
        return 0;
    }

    // Dispatch on first argument (command name)
    std::string cmd = args[0];

    // Support "ai texture" and "ai map" as two-word commands
    if (cmd == "ai" && args.size() >= 2) {
        cmd = "ai_" + args[1];
        args.erase(args.begin(), args.begin() + 2);  // remove "ai" + subcommand
    } else {
        args.erase(args.begin());  // remove command word
    }

    if (cmd == "texture" || cmd == "ai_texture")
        return ce::cmdTexture(args);

    if (cmd == "map"     || cmd == "ai_map")
        return ce::cmdMap(args);

    if (cmd == "validate")
        return ce::cmdValidate(args);

    if (cmd == "help" || cmd == "--help" || cmd == "-h") {
        ce::printHelp();
        return 0;
    }

    std::cerr << "[ERROR] Unknown command: '" << cmd << "'\n"
              << "Run 'creation-engine help' for usage.\n";
    return 1;
}
