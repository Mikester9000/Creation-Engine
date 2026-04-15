/**
 * MapEditor.h - Tile-based map editing for the Creation Engine.
 *
 * This module defines a layered tile map structure and provides factory
 * methods for creating and procedurally populating maps.
 *
 * Key structures:
 *  - TileLayer   : 2D grid of tile IDs referencing a tileset
 *  - ObjectLayer : Named objects with positions, sizes, and properties
 *  - MapEntity   : Entities (players, enemies, items) placed on the map
 *  - SpawnPoint  : Named spawn locations
 *  - Trigger     : Rectangular trigger zones with action strings
 *  - GameMap     : Container holding all layers plus metadata
 *  - MapEditor   : Static methods to create and procedurally populate maps
 *
 * Educational note: Layered tile maps (popularised by the Tiled editor format)
 * separate concerns: ground tiles, collision, decoration, and objects live on
 * different layers, making it easy to update one without affecting others.
 */

#pragma once
#include <string>
#include <vector>
#include <map>
#include <cstdint>

// ============================================================
//  TileLayer
// ============================================================

/**
 * TileLayer stores a 2D grid of integer tile IDs.
 *
 * Tile ID conventions used in this engine:
 *   0 = empty / no tile
 *   1 = ground / floor
 *   2 = wall / impassable
 *   3 = water / river
 *   4 = building wall
 *   5 = building floor
 */
struct TileLayer {
    std::string name;       // Human-readable layer name, e.g. "ground", "collision"
    int width  = 0;         // Columns in the grid
    int height = 0;         // Rows in the grid
    std::vector<int> tiles; // Row-major flat array; tiles[y*width+x] = tileID

    /** Resize and zero-fill the tile grid. */
    void resize(int w, int h) {
        width = w; height = h;
        tiles.assign(w * h, 0);
    }

    int&       at(int x, int y)       { return tiles[y * width + x]; }
    const int& at(int x, int y) const { return tiles[y * width + x]; }
};

// ============================================================
//  MapObject
// ============================================================

/**
 * MapObject is a named rectangle placed in world-pixel space.
 * Objects are used for trigger zones, doors, chest positions, etc.
 * Properties carry arbitrary key-value metadata.
 */
struct MapObject {
    std::string name;
    std::string type;  // e.g. "trigger", "spawn", "chest", "door"
    float x = 0, y = 0;  // Top-left position in pixels
    float w = 0, h = 0;  // Width / height in pixels
    std::map<std::string, std::string> properties;
};

/**
 * ObjectLayer groups a set of MapObjects under a common name.
 * One map can have multiple object layers, e.g. "triggers", "npcs".
 */
struct ObjectLayer {
    std::string name;
    std::vector<MapObject> objects;
};

// ============================================================
//  MapEntity
// ============================================================

/**
 * MapEntity represents a game object (player, enemy, NPC, item)
 * placed at a specific pixel position in the map.
 */
struct MapEntity {
    std::string id;     // Unique string identifier, e.g. "enemy_01"
    std::string type;   // "player", "enemy", "npc", "item"
    float x = 0, y = 0;
    std::map<std::string, std::string> properties;
};

// ============================================================
//  SpawnPoint
// ============================================================

/** A named location where a player or entity can be spawned. */
struct SpawnPoint {
    std::string name;
    float x = 0, y = 0;
};

// ============================================================
//  Trigger
// ============================================================

/**
 * Trigger is a rectangular zone that fires an action when entered.
 * The action string is parsed by the game engine at runtime,
 * e.g. "load_level:level2" or "play_cutscene:intro".
 */
struct Trigger {
    std::string name;
    std::string action;
    float x = 0, y = 0;
    float w = 0, h = 0;
};

// ============================================================
//  GameMap
// ============================================================

/**
 * GameMap is the top-level container for a complete tile map.
 * It holds multiple tile layers, object layers, entities, spawn points,
 * and triggers - everything needed to describe a game level.
 */
struct GameMap {
    std::string name;
    int mapWidth   = 0;   // Width  in tiles
    int mapHeight  = 0;   // Height in tiles
    int tileWidth  = 16;  // Width  of each tile in pixels
    int tileHeight = 16;  // Height of each tile in pixels
    std::string tilesetPath;

    std::vector<TileLayer>   tileLayers;
    std::vector<ObjectLayer> objectLayers;
    std::vector<MapEntity>   entities;
    std::vector<SpawnPoint>  spawnPoints;
    std::vector<Trigger>     triggers;
};

// ============================================================
//  MapEditor
// ============================================================

/**
 * MapEditor provides static factory methods to create and populate GameMaps.
 * All methods operate on a GameMap passed by reference, so you can chain
 * multiple generation steps on the same map.
 */
class MapEditor {
public:
    /**
     * createEmpty - Create a blank map with one ground layer filled with ID 1.
     */
    static GameMap createEmpty(int widthTiles, int heightTiles,
                                int tileW, int tileH,
                                const std::string& tilesetPath);

    /**
     * generateTerrain - Use Perlin noise to place walls and ground tiles.
     *
     * Noise values above threshold become walls (ID 2); below become ground (ID 1).
     * The map border is always forced to walls.
     *
     * @param scale      Noise scale (larger = smoother, bigger terrain features)
     * @param threshold  Noise threshold in [0,1]; higher = fewer walls
     */
    static void generateTerrain(GameMap& map, uint32_t seed,
                                  float scale, float threshold);

    /**
     * generateRiver - Add a river layer that winds from the top to the bottom.
     * River tiles use ID 3.  The underlying ground tiles are cleared to ID 1.
     */
    static void generateRiver(GameMap& map, uint32_t seed);

    /**
     * generateVillage - Place rectangular building footprints on a new layer.
     * Building walls = ID 4, building floors = ID 5.
     * Each building is also registered as a MapObject in the first object layer.
     *
     * @param buildingCount  How many building footprints to attempt to place.
     */
    static void generateVillage(GameMap& map, uint32_t seed, int buildingCount);

    /** addSpawnPoint - Add a named spawn location to the map. */
    static void addSpawnPoint(GameMap& map, const std::string& name, float x, float y);

    /** addTrigger - Add a rectangular trigger zone with an action string. */
    static void addTrigger(GameMap& map, const std::string& name,
                            const std::string& action,
                            float x, float y, float w, float h);

    /** addEntity - Place an entity (enemy, item, NPC) at a pixel position. */
    static void addEntity(GameMap& map, const std::string& id,
                           const std::string& type, float x, float y);
};
