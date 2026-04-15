/**
 * @file MapGen.hpp
 * @brief Procedural tilemap generator — produces JSON tilemaps compatible
 *        with the Game-Engine-for-Teaching- TileType enum.
 *
 * =============================================================================
 * TEACHING NOTE — Procedural Map Generation
 * =============================================================================
 *
 * A tilemap represents the game world as a 2D grid of integer tile IDs.
 * This module generates tilemaps using two techniques:
 *
 * 1. HEIGHTMAP-BASED TERRAIN (outdoor maps)
 *    ─────────────────────────────────────────
 *    Generate a noise-based height field h(x,y) ∈ [0,1], then assign tiles
 *    by thresholding:
 *
 *      h < 0.25               → WATER  (2)  — low valleys
 *      0.25 ≤ h < 0.40        → SAND   (4)  — beaches / riverbanks
 *      0.40 ≤ h < 0.72        → GRASS  (3)  — flatlands
 *      0.72 ≤ h < 0.82        → FOREST (5)  — wooded hills
 *      h ≥ 0.82               → MOUNTAIN (6)— high peaks
 *
 *    This produces natural-looking biome transitions without hard edges.
 *
 * 2. ROOM-AND-CORRIDOR DUNGEON (indoor maps)
 *    ─────────────────────────────────────────
 *    The classic BSP (Binary Space Partitioning) or random-placement algorithm:
 *    a. Fill map with WALL.
 *    b. Place N random rectangular rooms.
 *    c. Connect rooms with L-shaped corridors of FLOOR.
 *    d. Add DOOR at room entrances, STAIRS in first/last room.
 *
 * 3. RIVER CARVING (heightmap post-process)
 *    ─────────────────────────────────────────
 *    A river flows from a high point to the map edge by following the steepest
 *    descent of the height field. Tiles along the path become WATER or BRIDGE.
 *
 * 4. ROAD PLACEMENT
 *    ─────────────────────────────────────────
 *    Roads follow the gentlest gradient between two random points on opposite
 *    map edges. Tiles along the path become ROAD.
 *
 * JSON FORMAT (see MapGen.cpp for the full output schema)
 * ─────────────────────────────────────────────────────────
 * The output JSON is designed to be loaded directly by the Game Engine's
 * TileMap class with minimal modification.
 *
 * TILE ID TABLE (matches Game-Engine-for-Teaching- TileType enum)
 * ────────────────────────────────────────────────────────────────
 *   ID   TileType      Char   Description
 *    0   FLOOR          .     Walkable floor (indoor)
 *    1   WALL           #     Solid wall
 *    2   WATER          ~     Liquid, impassable
 *    3   GRASS          ,     Outdoor grass
 *    4   SAND           :     Sand / beach
 *    5   FOREST         T     Dense trees
 *    6   MOUNTAIN       ^     Rocky high ground
 *    7   ROAD           =     Paved road
 *    8   DOOR           +     Doorway
 *    9   STAIRS_UP      <     Staircase up
 *   10   STAIRS_DOWN    >     Staircase down
 *   11   CHEST          C     Treasure chest
 *   12   SAVE_POINT     S     Save point
 *   13   SHOP_TILE      $     Shop
 *   14   INN_TILE       I     Inn
 *   15   BRIDGE         =     Bridge over water
 *
 * @author  Creation Engine Project
 * @version 1.0
 */

#pragma once

#include <string>
#include <vector>
#include <cstdint>

namespace ce {

// =============================================================================
// Tile ID constants — mirrors Game-Engine-for-Teaching- TileType enum
// =============================================================================

/// @defgroup TileIDs Tile identifier constants (match TileType enum in engine)
/// @{
constexpr int TILE_FLOOR      = 0;
constexpr int TILE_WALL       = 1;
constexpr int TILE_WATER      = 2;
constexpr int TILE_GRASS      = 3;
constexpr int TILE_SAND       = 4;
constexpr int TILE_FOREST     = 5;
constexpr int TILE_MOUNTAIN   = 6;
constexpr int TILE_ROAD       = 7;
constexpr int TILE_DOOR       = 8;
constexpr int TILE_STAIRS_UP  = 9;
constexpr int TILE_STAIRS_DN  = 10;
constexpr int TILE_CHEST      = 11;
constexpr int TILE_SAVE_POINT = 12;
constexpr int TILE_SHOP       = 13;
constexpr int TILE_INN        = 14;
constexpr int TILE_BRIDGE     = 15;
/// @}

// =============================================================================
// TileMap data structure
// =============================================================================

/**
 * @struct Prop
 * @brief A named object placed on the map at a specific tile coordinate.
 *
 * Examples: a chest at (5,3), a save crystal at (12, 20).
 */
struct Prop {
    std::string type;  ///< Prop type name (e.g., "chest", "save_point").
    int         x;     ///< Tile column.
    int         y;     ///< Tile row.
    std::string label; ///< Optional human-readable label.
};

/**
 * @struct TileMap
 * @brief A 2D tilemap with optional prop list and generation metadata.
 */
struct TileMap {
    std::string        name;               ///< Map name (e.g., "forest_river").
    std::string        version  = "1.0";   ///< Format version.
    std::string        prompt;             ///< Generation prompt.
    uint32_t           seed     = 0;       ///< Seed used for generation.
    int                width    = 32;      ///< Width  in tiles.
    int                height   = 32;      ///< Height in tiles.
    int                tileSize = 64;      ///< Pixels per tile (for reference).
    std::string        tileset;            ///< Path to material/tileset JSON.
    std::vector<int>   tiles;              ///< Flat tile ID array [row-major].
    std::vector<Prop>  props;              ///< Decorations and interactive objects.

    /** @brief Access tile at (col, row). */
    int& at(int x, int y) { return tiles[static_cast<size_t>(y * width + x)]; }
    int  at(int x, int y) const { return tiles[static_cast<size_t>(y * width + x)]; }

    /** @brief True if coordinate is inside the map. */
    bool inBounds(int x, int y) const { return x >= 0 && y >= 0 && x < width && y < height; }
};

// =============================================================================
// MapGen options
// =============================================================================

/**
 * @struct MapGenOptions
 * @brief Control knobs for the map generator.
 */
struct MapGenOptions {
    int   width      = 64;    ///< Map width in tiles.
    int   height     = 64;    ///< Map height in tiles.
    int   tileSize   = 64;    ///< Tile size in pixels (metadata only).
    bool  hasRiver   = false; ///< Carve a winding river through the map.
    bool  hasRoad    = false; ///< Add a road across the map.
    bool  isDungeon  = false; ///< Generate a room-corridor dungeon instead of outdoor terrain.
    int   numRooms   = 8;     ///< (Dungeon only) number of rooms to place.
    float noiseScale = 16.0f; ///< Spatial frequency of the terrain noise.
    int   octaves    = 5;     ///< Number of fBm octaves for terrain.
};

// =============================================================================
// Interface
// =============================================================================

/**
 * @brief Generate a tilemap using procedural rules.
 *
 * @param name    Map name (used in the JSON "name" field).
 * @param prompt  Original prompt string (stored for traceability).
 * @param seed    RNG seed for deterministic generation.
 * @param opts    Generator configuration.
 * @return        Populated TileMap ready for JSON export or game loading.
 */
TileMap generateMap(const std::string&  name,
                    const std::string&  prompt,
                    uint32_t            seed,
                    const MapGenOptions& opts = MapGenOptions{});

/**
 * @brief Serialise a TileMap to a JSON string.
 *
 * @param map  The tilemap to serialise.
 * @return     Pretty-printed JSON string (see format spec in MapGen.hpp header).
 */
std::string mapToJson(const TileMap& map);

} // namespace ce
