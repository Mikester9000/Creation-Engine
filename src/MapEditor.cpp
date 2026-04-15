/**
 * MapEditor.cpp - Implementation of tile-based map editing.
 *
 * This file shows how procedural generation techniques (Perlin noise, random walks)
 * are applied to create game-ready tile maps in a data-driven architecture.
 */

#include "MapEditor.h"
#include "Noise.h"
#include <cmath>
#include <random>
#include <algorithm>

// ============================================================
//  createEmpty
// ============================================================

GameMap MapEditor::createEmpty(int widthTiles, int heightTiles,
                                int tileW, int tileH,
                                const std::string& tilesetPath) {
    GameMap map;
    map.name        = "untitled";
    map.mapWidth    = widthTiles;
    map.mapHeight   = heightTiles;
    map.tileWidth   = tileW;
    map.tileHeight  = tileH;
    map.tilesetPath = tilesetPath;

    // Create a single ground layer filled with tile ID 1 (ground).
    TileLayer ground;
    ground.name = "ground";
    ground.resize(widthTiles, heightTiles);
    for (auto& t : ground.tiles) t = 1;
    map.tileLayers.push_back(ground);

    return map;
}

// ============================================================
//  generateTerrain
// ============================================================

void MapEditor::generateTerrain(GameMap& map, uint32_t seed,
                                  float scale, float threshold) {
    PerlinNoise noise(seed);

    // If no layers exist yet, add one.
    if (map.tileLayers.empty()) {
        TileLayer ground;
        ground.name = "ground";
        ground.resize(map.mapWidth, map.mapHeight);
        map.tileLayers.push_back(ground);
    }

    TileLayer& ground = map.tileLayers[0];

    for (int y = 0; y < map.mapHeight; ++y) {
        for (int x = 0; x < map.mapWidth; ++x) {
            // Scale pixel coordinates into noise space.
            // Dividing by scale means a larger scale value gives smoother terrain.
            float nx = static_cast<float>(x) / scale;
            float ny = static_cast<float>(y) / scale;

            // 4-octave fBm gives natural-looking terrain with detail at multiple scales.
            float v = noise.octaveNoise2D(nx, ny, 4, 0.5f);

            // Remap from [-1,1] to [0,1] for thresholding.
            float t = (v + 1.0f) * 0.5f;

            // Above threshold = wall, below = walkable ground.
            ground.at(x, y) = (t > threshold) ? 2 : 1;
        }
    }

    // Force the map border to be solid walls.
    // This prevents the player from walking off the edge.
    for (int x = 0; x < map.mapWidth; ++x) {
        ground.at(x, 0)               = 2;
        ground.at(x, map.mapHeight-1) = 2;
    }
    for (int y = 0; y < map.mapHeight; ++y) {
        ground.at(0,               y) = 2;
        ground.at(map.mapWidth-1,  y) = 2;
    }
}

// ============================================================
//  generateRiver
// ============================================================

void MapEditor::generateRiver(GameMap& map, uint32_t seed) {
    // Create a new layer specifically for the river so it composites
    // independently from the ground/collision layer.
    TileLayer river;
    river.name = "river";
    river.resize(map.mapWidth, map.mapHeight);

    std::mt19937 rng(seed);
    // Small random drift each row simulates the natural meandering of a river.
    std::uniform_real_distribution<float> drift(-0.5f, 0.5f);

    // Start near the horizontal centre of the map.
    float rx = static_cast<float>(map.mapWidth) * 0.5f;

    for (int y = 0; y < map.mapHeight; ++y) {
        // Drift the river x position slightly.
        rx += drift(rng);

        // Round to integer tile coordinate and clamp away from the border.
        int ix = static_cast<int>(std::round(rx));
        ix = std::max(1, std::min(map.mapWidth - 3, ix));

        // Make the river 2 tiles wide.
        river.at(ix,     y) = 3;
        if (ix + 1 < map.mapWidth - 1) river.at(ix + 1, y) = 3;

        // Override the ground layer under the river to clear any walls,
        // so the river is passable terrain.
        if (!map.tileLayers.empty()) {
            map.tileLayers[0].at(ix, y) = 1;
            if (ix + 1 < map.mapWidth - 1)
                map.tileLayers[0].at(ix + 1, y) = 1;
        }

        // Slowly pull the river back toward the centre to avoid clipping the border.
        rx = rx * 0.9f + static_cast<float>(map.mapWidth) * 0.5f * 0.1f;
    }

    map.tileLayers.push_back(river);
}

// ============================================================
//  generateVillage
// ============================================================

void MapEditor::generateVillage(GameMap& map, uint32_t seed, int buildingCount) {
    // A dedicated layer keeps building tiles separate from terrain.
    TileLayer village;
    village.name = "village";
    village.resize(map.mapWidth, map.mapHeight);

    // Use a different seed offset so village layout is independent of terrain.
    std::mt19937 rng(seed + 1000);
    std::uniform_int_distribution<int> rx(2, std::max(2, map.mapWidth  - 8));
    std::uniform_int_distribution<int> ry(2, std::max(2, map.mapHeight - 8));
    std::uniform_int_distribution<int> rw(3, 6);
    std::uniform_int_distribution<int> rh(3, 5);

    // Ensure the object layer exists before adding buildings.
    if (map.objectLayers.empty()) {
        ObjectLayer ol;
        ol.name = "buildings";
        map.objectLayers.push_back(ol);
    }

    for (int b = 0; b < buildingCount; ++b) {
        int bx = rx(rng);
        int by = ry(rng);
        int bw = rw(rng);
        int bh = rh(rng);

        // Clamp so buildings don't spill past the border.
        if (bx + bw >= map.mapWidth  - 1) bw = map.mapWidth  - 2 - bx;
        if (by + bh >= map.mapHeight - 1) bh = map.mapHeight - 2 - by;
        if (bw < 2 || bh < 2) continue;

        // Draw the building: perimeter = wall tiles, interior = floor tiles.
        for (int y = by; y < by + bh; ++y) {
            for (int x = bx; x < bx + bw; ++x) {
                bool isWall = (x == bx || x == bx+bw-1 || y == by || y == by+bh-1);
                village.at(x, y) = isWall ? 4 : 5;

                // Also clear any terrain walls so buildings sit on open ground.
                if (!map.tileLayers.empty() && !isWall) {
                    map.tileLayers[0].at(x, y) = 1;
                }
            }
        }

        // Register the building footprint as a MapObject for game-logic use.
        MapObject obj;
        obj.name = "building_" + std::to_string(b);
        obj.type = "building";
        obj.x = static_cast<float>(bx * map.tileWidth);
        obj.y = static_cast<float>(by * map.tileHeight);
        obj.w = static_cast<float>(bw * map.tileWidth);
        obj.h = static_cast<float>(bh * map.tileHeight);
        map.objectLayers[0].objects.push_back(obj);
    }

    map.tileLayers.push_back(village);
}

// ============================================================
//  addSpawnPoint / addTrigger / addEntity
// ============================================================

void MapEditor::addSpawnPoint(GameMap& map, const std::string& name, float x, float y) {
    SpawnPoint sp;
    sp.name = name;
    sp.x    = x;
    sp.y    = y;
    map.spawnPoints.push_back(sp);
}

void MapEditor::addTrigger(GameMap& map, const std::string& name,
                            const std::string& action,
                            float x, float y, float w, float h) {
    Trigger trig;
    trig.name   = name;
    trig.action = action;
    trig.x = x; trig.y = y;
    trig.w = w; trig.h = h;
    map.triggers.push_back(trig);
}

void MapEditor::addEntity(GameMap& map, const std::string& id,
                           const std::string& type, float x, float y) {
    MapEntity ent;
    ent.id   = id;
    ent.type = type;
    ent.x    = x;
    ent.y    = y;
    map.entities.push_back(ent);
}
