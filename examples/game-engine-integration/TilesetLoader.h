/**
 * TilesetLoader.h - Example: loading Creation Engine tileset JSON files.
 *
 * A tileset describes how a sprite sheet is divided into individual tiles.
 * This loader reads the JSON format produced by:
 *   creation-engine create-tileset --out tileset.json
 */

#pragma once
#include <string>
#include <vector>

/** Runtime representation of a single tile from the tileset. */
struct TileDesc {
    int         id    = 0;
    std::string name;
    bool        solid = false;   // Does this tile block movement?
};

/** Runtime representation of a complete tileset. */
struct Tileset {
    std::string            texturePath; // Path to the sprite sheet PNG
    int                    tileWidth  = 16;
    int                    tileHeight = 16;
    std::vector<TileDesc>  tiles;

    /** Look up tile metadata by ID. Returns nullptr if not found. */
    const TileDesc* getById(int id) const {
        for (const auto& t : tiles)
            if (t.id == id) return &t;
        return nullptr;
    }
};

/**
 * TilesetLoader - Reads a tileset JSON file into a Tileset struct.
 */
class TilesetLoader {
public:
    /**
     * load - Parse a tileset JSON file into a Tileset.
     * @param path  Path to the .tileset.json file.
     * @param out   Output Tileset.
     * @return true on success.
     */
    static bool load(const std::string& path, Tileset& out);
};
