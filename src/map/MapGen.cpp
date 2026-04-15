/**
 * @file MapGen.cpp
 * @brief Implementation of the procedural tilemap generator.
 *
 * =============================================================================
 * TEACHING NOTE — Map Generation Algorithms Used Here
 * =============================================================================
 *
 * OUTDOOR TERRAIN (heightmap-driven)
 * ────────────────────────────────────
 * 1. Generate a fractional Brownian motion (fBm) height field.
 * 2. Threshold the height field into biome bands.
 * 3. Optionally carve a river by hill-descent path.
 * 4. Optionally place a road by terrain-gradient path.
 * 5. Scatter props (trees, chests, save points) in valid tiles.
 *
 * DUNGEON (BSP room placement)
 * ─────────────────────────────
 * 1. Fill map with WALL.
 * 2. Randomly place rectangular rooms (no overlap).
 * 3. Connect each room to the previous with an L-shaped corridor.
 * 4. Place DOOR tiles at corridor–room junctions.
 * 5. Place STAIRS_UP in first room, STAIRS_DOWN in last room.
 *
 * @author  Creation Engine Project
 * @version 1.0
 */

#include "map/MapGen.hpp"

#include <cmath>
#include <algorithm>
#include <random>
#include <limits>
#include <functional>

#include "util/Noise.hpp"
#include "util/JsonWriter.hpp"

namespace ce {

// =============================================================================
// Internal helpers
// =============================================================================

namespace {

// ─────────────────────────────────────────────────────────────────────────────
// Seeded pseudo-random integer helper
// ─────────────────────────────────────────────────────────────────────────────

/**
 * @brief Simple deterministic LCG random generator for map placement.
 *
 * TEACHING NOTE — LCG (Linear Congruential Generator)
 * An LCG produces a sequence: X_{n+1} = (a*X_n + c) mod m.
 * Parameters below are from Knuth's MMIX (widely cited in literature).
 * Sufficient quality for game-level procedural placement; not suitable
 * for cryptography or Monte Carlo simulation.
 */
struct LCG {
    uint64_t state;
    explicit LCG(uint64_t seed) : state(seed ^ 0xDeadBeefCafeULL) {}

    /** @brief Return next value in [0, 1). */
    float nextFloat() {
        state = state * 6364136223846793005ULL + 1442695040888963407ULL;
        return static_cast<float>((state >> 33) & 0x7FFFFFFFu) /
               static_cast<float>(0x7FFFFFFFu);
    }

    /** @brief Return integer in [lo, hi] inclusive. */
    int nextInt(int lo, int hi) {
        return lo + static_cast<int>(nextFloat() * static_cast<float>(hi - lo + 1));
    }
};

// ─────────────────────────────────────────────────────────────────────────────
// Height field helpers
// ─────────────────────────────────────────────────────────────────────────────

/**
 * @brief Sample terrain height at tile (x, y) using fBm noise.
 *
 * The result is in [0, 1]. Higher values = higher elevation.
 */
float terrainHeight(int x, int y,
                    float noiseScale, int octaves, uint32_t seed)
{
    // Normalise coordinates so the noise frequency is independent of map size
    float fx = static_cast<float>(x) / noiseScale;
    float fy = static_cast<float>(y) / noiseScale;
    return fbm(fx, fy, seed, octaves);
}

// ─────────────────────────────────────────────────────────────────────────────
// Tile assignment from height
// ─────────────────────────────────────────────────────────────────────────────

/**
 * @brief Map a height value in [0,1] to a tile ID using FFXV-like thresholds.
 *
 * TEACHING NOTE — Biome Thresholds
 * These constants control the balance of terrain types. Adjust them to produce
 * different biome mixes:
 *   • Lower WATER_MAX → more water (e.g., archipelago map).
 *   • Raise MOUNTAIN_MIN → fewer mountains (e.g., plains map).
 *   • Narrow FOREST band → sparser trees.
 */
int heightToTile(float h)
{
    constexpr float WATER_MAX    = 0.25f;
    constexpr float SAND_MAX     = 0.38f;
    constexpr float GRASS_MAX    = 0.68f;
    constexpr float FOREST_MAX   = 0.82f;
    // Above FOREST_MAX → MOUNTAIN

    if (h < WATER_MAX)    return TILE_WATER;
    if (h < SAND_MAX)     return TILE_SAND;
    if (h < GRASS_MAX)    return TILE_GRASS;
    if (h < FOREST_MAX)   return TILE_FOREST;
    return TILE_MOUNTAIN;
}

// ─────────────────────────────────────────────────────────────────────────────
// River carving
// ─────────────────────────────────────────────────────────────────────────────

/**
 * @brief Carve a river by following the steepest descent from a high point.
 *
 * TEACHING NOTE — Hill-Descent River Generation
 * This is a simplified version of the "downhill" river algorithm used in
 * many terrain generators:
 *   1. Pick a starting tile with height > 0.6 (mountain/forest region).
 *   2. At each step, move to the neighbouring tile with the lowest height.
 *   3. Mark visited tiles as WATER (or BRIDGE if crossing a ROAD/WALL).
 *   4. Stop when reaching the map edge or a WATER tile.
 *
 * The result is a naturally winding river that respects the terrain.
 *
 * @param map    Tilemap to modify.
 * @param heights Flat height field (same indexing as tiles).
 * @param rng    LCG for random start-point selection.
 */
void carveRiver(TileMap&                  map,
                const std::vector<float>& heights,
                LCG&                      rng)
{
    const int W = map.width, H = map.height;

    // Find a good starting tile: tall terrain in the upper half of the map
    int startX = -1, startY = -1;
    float bestH = 0.0f;
    for (int attempt = 0; attempt < 200; ++attempt) {
        int cx = rng.nextInt(W / 4, 3 * W / 4);
        int cy = rng.nextInt(0,     H / 3);
        float h = heights[static_cast<size_t>(cy * W + cx)];
        if (h > bestH && map.at(cx, cy) != TILE_WATER) {
            bestH = h;
            startX = cx;
            startY = cy;
        }
    }
    if (startX < 0) { startX = W / 2; startY = 0; }

    // Walk downhill
    int cx = startX, cy = startY;
    constexpr int MAX_STEPS = 2000;
    const int dx4[] = {1, -1, 0, 0};
    const int dy4[] = {0,  0, 1,-1};

    for (int step = 0; step < MAX_STEPS; ++step) {
        int tile = map.at(cx, cy);
        if (tile == TILE_ROAD || tile == TILE_WALL) {
            map.at(cx, cy) = TILE_BRIDGE;
        } else {
            map.at(cx, cy) = TILE_WATER;
        }

        // Stop at map edge
        if (cx == 0 || cy == 0 || cx == W - 1 || cy == H - 1) break;

        // Find lowest neighbour
        int bestNX = cx, bestNY = cy;
        float bestNH = heights[static_cast<size_t>(cy * W + cx)];

        for (int d = 0; d < 4; ++d) {
            int nx = cx + dx4[d], ny = cy + dy4[d];
            if (!map.inBounds(nx, ny)) continue;
            float nh = heights[static_cast<size_t>(ny * W + nx)];
            if (nh < bestNH) {
                bestNH = nh;
                bestNX = nx;
                bestNY = ny;
            }
        }

        // If truly stuck (local minimum), add a tiny jitter to break out
        if (bestNX == cx && bestNY == cy) {
            int d = static_cast<int>(rng.nextFloat() * 4.0f) % 4;
            bestNX = cx + dx4[d];
            bestNY = cy + dy4[d];
            if (!map.inBounds(bestNX, bestNY)) break;
        }

        cx = bestNX;
        cy = bestNY;
    }
}

// ─────────────────────────────────────────────────────────────────────────────
// Road placement
// ─────────────────────────────────────────────────────────────────────────────

/**
 * @brief Place a road across the map following the gentlest gradient.
 *
 * TEACHING NOTE — Road Generation
 * Roads avoid water and steep slopes. This is a simplified A*-like traversal:
 *   • Start at a random point on the left edge.
 *   • Walk toward the right edge, preferring tiles with low height variation
 *     (flat terrain) over tiles with large height changes (steep hills).
 *   • Mark each tile as ROAD unless it is WATER (impassable).
 *
 * A full road generator would use A* with a proper cost heuristic. For now,
 * greedy horizontal walk + vertical steering is sufficient for teaching.
 *
 * @param map     Tilemap to modify.
 * @param heights Flat height field.
 * @param rng     LCG for random start-point selection.
 */
void placeRoad(TileMap&                  map,
               const std::vector<float>& heights,
               LCG&                      rng)
{
    const int W = map.width, H = map.height;

    int cy = rng.nextInt(H / 4, 3 * H / 4);  // random vertical starting position

    for (int x = 0; x < W; ++x) {
        // Steer vertically toward the flattest neighbour
        int bestY = cy;
        float bestGrad = std::numeric_limits<float>::max();

        for (int dy = -2; dy <= 2; ++dy) {
            int ny = cy + dy;
            if (ny < 0 || ny >= H) continue;
            // Gradient = |h(x,ny) - h(x-1,ny)| (prefer flat terrain)
            float h0 = heights[static_cast<size_t>(ny * W + x)];
            float h1 = (x > 0) ? heights[static_cast<size_t>(ny * W + (x - 1))] : h0;
            float grad = std::abs(h0 - h1) + std::abs(static_cast<float>(ny - cy)) * 0.05f;
            if (grad < bestGrad) {
                bestGrad = grad;
                bestY = ny;
            }
        }
        cy = bestY;

        int tile = map.at(x, cy);
        if (tile != TILE_WATER) {
            map.at(x, cy) = TILE_ROAD;
        } else {
            // Bridge over water
            map.at(x, cy) = TILE_BRIDGE;
        }
    }
}

// ─────────────────────────────────────────────────────────────────────────────
// Prop scattering
// ─────────────────────────────────────────────────────────────────────────────

/**
 * @brief Scatter decorative props on valid tiles.
 *
 * TEACHING NOTE — Prop Placement
 * Props are interactive objects (chests, save points, shops) placed at
 * specific tile positions. In a real game, props are loaded as entities
 * into the ECS alongside the tilemap. The JSON format stores them as a
 * separate array so the loader can spawn them independently.
 *
 * @param map          Tilemap to add props to.
 * @param rng          LCG for placement randomness.
 * @param numChests    Number of chests to place.
 * @param numSavePoints Number of save points to place.
 */
void scatterProps(TileMap& map, LCG& rng,
                  int numChests    = 3,
                  int numSavePoints = 1)
{
    auto tryPlace = [&](const std::string& type, int allowedTile, int count,
                        const std::string& label)
    {
        int W = map.width, H = map.height;
        for (int i = 0; i < count; ++i) {
            for (int attempt = 0; attempt < 200; ++attempt) {
                int x = rng.nextInt(1, W - 2);
                int y = rng.nextInt(1, H - 2);
                if (map.at(x, y) == allowedTile) {
                    map.props.push_back({type, x, y, label});
                    break;
                }
            }
        }
    };

    tryPlace("chest",      TILE_GRASS,  numChests,    "Treasure Chest");
    tryPlace("save_point", TILE_GRASS,  numSavePoints,"Save Crystal");
}

// ─────────────────────────────────────────────────────────────────────────────
// Dungeon generator
// ─────────────────────────────────────────────────────────────────────────────

/**
 * @brief Simple random-room dungeon generator.
 *
 * TEACHING NOTE — Room-and-Corridor Dungeons
 * This is one of the oldest procedural techniques in games (Rogue, 1980).
 * The algorithm:
 *   1. Fill with WALL.
 *   2. Place rooms at random positions (reject overlaps).
 *   3. Connect room centres with L-shaped FLOOR corridors.
 *   4. Add DOOR at each room entry, STAIRS at start/end.
 *
 * A "BSP dungeon" divides the map recursively and places one room per leaf
 * node — this avoids all overlap checking. For teaching purposes, the simpler
 * rejection-sampling approach here is easier to follow.
 */
void generateDungeon(TileMap& map, LCG& rng, int numRooms)
{
    const int W = map.width, H = map.height;

    // Fill with WALL
    std::fill(map.tiles.begin(), map.tiles.end(), TILE_WALL);

    struct Room { int x, y, w, h; };
    std::vector<Room> rooms;

    // Place rooms (reject overlapping)
    for (int attempt = 0; attempt < numRooms * 20 && static_cast<int>(rooms.size()) < numRooms; ++attempt) {
        int rw = rng.nextInt(4, std::min(12, W / 4));
        int rh = rng.nextInt(3, std::min( 8, H / 4));
        int rx = rng.nextInt(1, W - rw - 1);
        int ry = rng.nextInt(1, H - rh - 1);

        // Check no overlap with existing rooms (+1 padding for walls)
        bool overlap = false;
        for (const Room& r : rooms) {
            if (rx < r.x + r.w + 1 && rx + rw + 1 > r.x &&
                ry < r.y + r.h + 1 && ry + rh + 1 > r.y) {
                overlap = true;
                break;
            }
        }
        if (overlap) continue;

        // Carve room floor
        for (int dy = 0; dy < rh; ++dy)
            for (int dx = 0; dx < rw; ++dx)
                map.at(rx + dx, ry + dy) = TILE_FLOOR;

        rooms.push_back({rx, ry, rw, rh});
    }

    // Connect rooms with L-shaped corridors
    for (size_t i = 1; i < rooms.size(); ++i) {
        int ax = rooms[i-1].x + rooms[i-1].w / 2;
        int ay = rooms[i-1].y + rooms[i-1].h / 2;
        int bx = rooms[i].x   + rooms[i].w   / 2;
        int by = rooms[i].y   + rooms[i].h   / 2;

        // Horizontal segment then vertical (or vice versa)
        bool hFirst = rng.nextFloat() < 0.5f;
        if (hFirst) {
            for (int x = std::min(ax,bx); x <= std::max(ax,bx); ++x)
                if (map.inBounds(x, ay)) map.at(x, ay) = TILE_FLOOR;
            for (int y = std::min(ay,by); y <= std::max(ay,by); ++y)
                if (map.inBounds(bx, y)) map.at(bx, y) = TILE_FLOOR;
        } else {
            for (int y = std::min(ay,by); y <= std::max(ay,by); ++y)
                if (map.inBounds(ax, y)) map.at(ax, y) = TILE_FLOOR;
            for (int x = std::min(ax,bx); x <= std::max(ax,bx); ++x)
                if (map.inBounds(x, by)) map.at(x, by) = TILE_FLOOR;
        }
    }

    // Place stairs and props
    if (!rooms.empty()) {
        const Room& first = rooms.front();
        const Room& last  = rooms.back();
        int fcx = first.x + first.w / 2;
        int fcy = first.y + first.h / 2;
        int lcx = last.x  + last.w  / 2;
        int lcy = last.y  + last.h  / 2;
        map.at(fcx, fcy) = TILE_STAIRS_UP;
        map.at(lcx, lcy) = TILE_STAIRS_DN;
        map.props.push_back({"stairs_up",   fcx, fcy, "Entrance Stairs"});
        map.props.push_back({"stairs_down", lcx, lcy, "Exit Stairs"});

        // Scatter chests in other rooms
        for (size_t i = 1; i + 1 < rooms.size(); ++i) {
            if (rng.nextFloat() < 0.4f) {
                int cx = rooms[i].x + rng.nextInt(1, rooms[i].w - 2);
                int cy = rooms[i].y + rng.nextInt(1, rooms[i].h - 2);
                map.at(cx, cy) = TILE_CHEST;
                map.props.push_back({"chest", cx, cy, "Dungeon Chest"});
            }
        }
    }
}

// ─────────────────────────────────────────────────────────────────────────────
// Outdoor terrain generator
// ─────────────────────────────────────────────────────────────────────────────

/**
 * @brief Generate heightmap-driven outdoor terrain with optional river/road.
 */
void generateOutdoor(TileMap& map, LCG& rng, const MapGenOptions& opts, uint32_t seed)
{
    const int W = map.width, H = map.height;

    // Build height field
    std::vector<float> heights(static_cast<size_t>(W * H));
    for (int y = 0; y < H; ++y)
        for (int x = 0; x < W; ++x)
            heights[static_cast<size_t>(y * W + x)] =
                terrainHeight(x, y, opts.noiseScale, opts.octaves, seed);

    // Assign base tile from height
    for (int y = 0; y < H; ++y)
        for (int x = 0; x < W; ++x)
            map.at(x, y) = heightToTile(heights[static_cast<size_t>(y * W + x)]);

    // Optional river
    if (opts.hasRiver) carveRiver(map, heights, rng);

    // Optional road
    if (opts.hasRoad) placeRoad(map, heights, rng);

    // Scatter props on grass tiles
    scatterProps(map, rng, 3, 1);

    // Add a camp/shop in the middle of a grass region
    for (int attempt = 0; attempt < 300; ++attempt) {
        int x = rng.nextInt(W / 4, 3 * W / 4);
        int y = rng.nextInt(H / 4, 3 * H / 4);
        if (map.at(x, y) == TILE_GRASS) {
            map.props.push_back({"shop", x, y, "Outpost Shop"});
            break;
        }
    }
}

} // anonymous namespace

// =============================================================================
// Public API — generateMap
// =============================================================================

TileMap generateMap(const std::string&  name,
                    const std::string&  prompt,
                    uint32_t            seed,
                    const MapGenOptions& opts)
{
    TileMap map;
    map.name    = name;
    map.prompt  = prompt;
    map.seed    = seed;
    map.width   = opts.width;
    map.height  = opts.height;
    map.tileSize = opts.tileSize;
    map.tileset = name + "_tileset.json";
    map.tiles.assign(static_cast<size_t>(opts.width * opts.height), TILE_GRASS);

    LCG rng(static_cast<uint64_t>(seed));

    if (opts.isDungeon) {
        generateDungeon(map, rng, opts.numRooms);
    } else {
        generateOutdoor(map, rng, opts, seed);
    }

    return map;
}

// =============================================================================
// Public API — mapToJson
// =============================================================================

/**
 * @brief Serialise a TileMap to a pretty-printed JSON string.
 *
 * Schema:
 * @code
 * {
 *   "version": "1.0",
 *   "name": "forest_river",
 *   "prompt": "forest with river and road",
 *   "seed": 123,
 *   "width": 64,
 *   "height": 64,
 *   "tileSize": 64,
 *   "tileset": "forest_river_tileset.json",
 *   "tiles": [3, 3, 2, ...],
 *   "props": [
 *     {"type": "chest", "x": 10, "y": 5, "label": "Treasure Chest"},
 *     ...
 *   ]
 * }
 * @endcode
 */
std::string mapToJson(const TileMap& map)
{
    JsonWriter j;
    j.beginObject();

    j.keyString("version",  map.version);
    j.keyString("name",     map.name);
    j.keyString("prompt",   map.prompt);
    j.keyInt   ("seed",     static_cast<int64_t>(map.seed));
    j.keyInt   ("width",    map.width);
    j.keyInt   ("height",   map.height);
    j.keyInt   ("tileSize", map.tileSize);
    j.keyString("tileset",  map.tileset);

    // ── tiles array ──────────────────────────────────────────────────────────
    j.writeKey("tiles");
    j.beginArray();
    for (int id : map.tiles) j.writeInt(static_cast<int64_t>(id));
    j.endArray();

    // ── props array ──────────────────────────────────────────────────────────
    j.writeKey("props");
    j.beginArray();
    for (const Prop& p : map.props) {
        j.beginObject();
            j.keyString("type",  p.type);
            j.keyInt   ("x",     static_cast<int64_t>(p.x));
            j.keyInt   ("y",     static_cast<int64_t>(p.y));
            j.keyString("label", p.label);
        j.endObject();
    }
    j.endArray();

    j.endObject();
    return j.str();
}

} // namespace ce
