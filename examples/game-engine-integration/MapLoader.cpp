/**
 * MapLoader.cpp - Implementation of the example map loader.
 */

#include "MapLoader.h"
#include "../../src/AssetIO.h"
#include <iostream>

bool MapLoader::load(const std::string& path, GameMap& out) {
    if (!AssetIO::loadMap(path, out)) {
        std::cerr << "MapLoader: failed to load '" << path << "'\n";
        return false;
    }
    std::cout << "MapLoader: loaded '" << path << "'\n";
    printInfo(out);
    return true;
}

void MapLoader::printInfo(const GameMap& map) {
    std::cout << "  Map: " << map.name
              << "  " << map.mapWidth << "x" << map.mapHeight << " tiles"
              << "  (tile " << map.tileWidth << "x" << map.tileHeight << " px)\n";
    std::cout << "  Tile layers    : " << map.tileLayers.size()   << "\n";
    std::cout << "  Object layers  : " << map.objectLayers.size() << "\n";
    std::cout << "  Entities       : " << map.entities.size()     << "\n";
    std::cout << "  Spawn points   : " << map.spawnPoints.size()  << "\n";
    std::cout << "  Triggers       : " << map.triggers.size()     << "\n";
}
