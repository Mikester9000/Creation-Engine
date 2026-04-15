/**
 * MapLoader.h - Example: loading Creation Engine map JSON files.
 *
 * Loads the JSON format produced by:
 *   creation-engine create-map  --out level.json
 *   creation-engine ai map      --out level.json
 */

#pragma once
#include <string>
#include "../../src/MapEditor.h"

/**
 * MapLoader - Reads a map JSON file into a GameMap struct.
 */
class MapLoader {
public:
    /**
     * load - Parse a map JSON file into a GameMap.
     * @param path  Path to the .json map file.
     * @param out   Output GameMap.
     * @return true on success.
     */
    static bool load(const std::string& path, GameMap& out);

    /**
     * printInfo - Print a summary of a loaded map to stdout.
     */
    static void printInfo(const GameMap& map);
};
