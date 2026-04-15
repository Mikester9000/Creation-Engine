/**
 * AssetIO.h - Asset input/output for the Creation Engine.
 *
 * This module handles:
 *  - Saving and loading PNG images via stb_image / stb_image_write
 *  - Writing JSON metadata files for textures, tilesets, and maps
 *  - Reading JSON metadata files back into C++ structs
 *
 * Educational note: Rather than pulling in a full JSON library, this module
 * serialises to JSON with simple string concatenation and parses with basic
 * string searching. This is practical for a fixed-schema file format and
 * teaches how structured text formats work at a low level.
 */

#pragma once
#include <string>
#include <vector>
#include "TextureGenerator.h"
#include "MapEditor.h"

// ============================================================
//  TilesetDef
// ============================================================

/**
 * TileInfo describes one tile in a tileset.
 * id     - zero-based index matching the tile ID used in TileLayer grids
 * name   - human-readable label ("ground", "wall", etc.)
 * solid  - true if the tile blocks movement (used by collision detection)
 */
struct TileInfo {
    int         id    = 0;
    std::string name;
    bool        solid = false;
};

/**
 * TilesetDef describes a sprite-sheet tileset:
 *  texturePath - path to the PNG sprite sheet
 *  tileWidth / tileHeight - pixel dimensions of one tile
 *  tiles - metadata for each tile frame
 */
struct TilesetDef {
    std::string          texturePath;
    int                  tileWidth  = 16;
    int                  tileHeight = 16;
    std::vector<TileInfo> tiles;
};

// ============================================================
//  AssetIO
// ============================================================

/**
 * AssetIO - Static utility class for reading and writing assets.
 */
class AssetIO {
public:
    // ---- PNG image I/O ----

    /**
     * savePNG - Write a Texture to a PNG file.
     * @param path  Destination file path.
     * @param tex   Texture to save (RGBA, 4 bytes per pixel).
     * @return true on success.
     */
    static bool savePNG(const std::string& path, const Texture& tex);

    /**
     * loadPNG - Load an image file (PNG/JPEG/BMP) into a Texture.
     * The image is always converted to 4-channel RGBA.
     * @param path  Source file path.
     * @param tex   Output Texture.
     * @return true on success.
     */
    static bool loadPNG(const std::string& path, Texture& tex);

    // ---- JSON metadata ----

    /**
     * saveTextureMetadata - Write a simple JSON sidecar file for a texture.
     * Fields: name, width, height, type, seed.
     */
    static bool saveTextureMetadata(const std::string& path,
                                     const std::string& name,
                                     int w, int h,
                                     const std::string& type,
                                     uint32_t seed);

    /**
     * saveTileset - Serialise a TilesetDef to a JSON file.
     */
    static bool saveTileset(const std::string& path, const TilesetDef& ts);

    /**
     * loadTileset - Deserialise a TilesetDef from a JSON file.
     */
    static bool loadTileset(const std::string& path, TilesetDef& ts);

    /**
     * saveMap - Serialise a GameMap to a JSON file.
     * Includes all tile layers, object layers, entities, spawn points, triggers.
     */
    static bool saveMap(const std::string& path, const GameMap& map);

    /**
     * loadMap - Deserialise a GameMap from a JSON file.
     */
    static bool loadMap(const std::string& path, GameMap& map);

    // ---- Utility ----

    /**
     * ensureDirectory - Create a directory (and all parents) if it does not exist.
     * @return true if the directory exists (or was successfully created).
     */
    static bool ensureDirectory(const std::string& path);
};
