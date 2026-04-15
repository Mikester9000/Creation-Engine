/**
 * TilesetLoader.cpp - Implementation of the example tileset loader.
 *
 * Delegates to AssetIO::loadTileset() which parses the JSON format.
 * In a standalone project (not linked against Creation Engine) you would
 * replicate the extractString/extractInt/extractBool helpers here.
 */

#include "TilesetLoader.h"
#include "../../src/AssetIO.h"
#include <iostream>

bool TilesetLoader::load(const std::string& path, Tileset& out) {
    TilesetDef def;
    if (!AssetIO::loadTileset(path, def)) {
        std::cerr << "TilesetLoader: failed to load '" << path << "'\n";
        return false;
    }

    out.texturePath = def.texturePath;
    out.tileWidth   = def.tileWidth;
    out.tileHeight  = def.tileHeight;
    out.tiles.clear();
    out.tiles.reserve(def.tiles.size());

    for (const auto& ti : def.tiles) {
        TileDesc td;
        td.id    = ti.id;
        td.name  = ti.name;
        td.solid = ti.solid;
        out.tiles.push_back(td);
    }

    std::cout << "TilesetLoader: loaded '" << path << "' ("
              << out.tiles.size() << " tiles, "
              << out.tileWidth << "x" << out.tileHeight << " px each)\n";
    return true;
}
