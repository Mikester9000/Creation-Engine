/**
 * AssetIO.cpp - Implementation of asset I/O for the Creation Engine.
 *
 * The STB single-header implementations must be defined exactly once per
 * translation unit. We place them here so they are compiled only once.
 */

// STB implementations - must come before any other includes
#define STB_IMAGE_IMPLEMENTATION
#include "../vendor/stb_image.h"

#define STB_IMAGE_WRITE_IMPLEMENTATION
#include "../vendor/stb_image_write.h"

#include "AssetIO.h"
#include <fstream>
#include <sstream>
#include <iostream>
#include <sys/stat.h>
#include <sys/types.h>
#include <cstring>

// ============================================================
//  PNG I/O
// ============================================================

bool AssetIO::savePNG(const std::string& path, const Texture& tex) {
    if (tex.pixels.empty()) {
        std::cerr << "AssetIO::savePNG: empty texture.\n";
        return false;
    }
    // Color struct is 4 consecutive RGBA bytes - same layout stb expects.
    const unsigned char* data =
        reinterpret_cast<const unsigned char*>(tex.pixels.data());
    int stride = tex.width * 4;  // bytes per row
    int ok = stbi_write_png(path.c_str(), tex.width, tex.height, 4, data, stride);
    if (!ok) {
        std::cerr << "AssetIO::savePNG: stbi_write_png failed: " << path << "\n";
        return false;
    }
    return true;
}

bool AssetIO::loadPNG(const std::string& path, Texture& tex) {
    int w = 0, h = 0, channels = 0;
    // Request 4 channels (RGBA) regardless of source format.
    unsigned char* data = stbi_load(path.c_str(), &w, &h, &channels, 4);
    if (!data) {
        std::cerr << "AssetIO::loadPNG: failed to load '" << path << "': "
                  << stbi_failure_reason() << "\n";
        return false;
    }
    tex.resize(w, h);
    std::memcpy(tex.pixels.data(), data, static_cast<size_t>(w * h * 4));
    stbi_image_free(data);
    return true;
}

// ============================================================
//  JSON helpers (file-local, anonymous namespace)
// ============================================================

namespace {

// Escape a string for safe embedding in JSON.
std::string jsonEscape(const std::string& s) {
    std::string out;
    out.reserve(s.size());
    for (unsigned char c : s) {
        if      (c == '"')  out += "\\\"";
        else if (c == '\\') out += "\\\\";
        else if (c == '\n') out += "\\n";
        else if (c == '\r') out += "\\r";
        else if (c == '\t') out += "\\t";
        else                out += static_cast<char>(c);
    }
    return out;
}

// Emit:  "key": "value"
std::string jkv(const std::string& indent, const std::string& key, const std::string& val) {
    return indent + "\"" + key + "\": \"" + jsonEscape(val) + "\"";
}

// Emit:  "key": integer
std::string jkn(const std::string& indent, const std::string& key, long long val) {
    return indent + "\"" + key + "\": " + std::to_string(val);
}

// Emit:  "key": float
std::string jkf(const std::string& indent, const std::string& key, float val) {
    std::ostringstream oss;
    oss << indent << "\"" << key << "\": " << val;
    return oss.str();
}

// Emit:  "key": true|false
std::string jkb(const std::string& indent, const std::string& key, bool val) {
    return indent + "\"" + key + "\": " + (val ? "true" : "false");
}

// Extract the string value for "key": "VALUE" from a JSON snippet.
std::string extractString(const std::string& json, const std::string& key) {
    std::string search = "\"" + key + "\"";
    size_t pos = json.find(search);
    if (pos == std::string::npos) return "";
    pos = json.find(':', pos);
    if (pos == std::string::npos) return "";
    pos = json.find('"', pos);
    if (pos == std::string::npos) return "";
    ++pos;  // skip opening quote
    std::string result;
    while (pos < json.size() && json[pos] != '"') {
        if (json[pos] == '\\' && pos + 1 < json.size()) {
            ++pos;
            if      (json[pos] == '"')  result += '"';
            else if (json[pos] == '\\') result += '\\';
            else if (json[pos] == 'n')  result += '\n';
            else if (json[pos] == 'r')  result += '\r';
            else if (json[pos] == 't')  result += '\t';
            else                        result += json[pos];
        } else {
            result += json[pos];
        }
        ++pos;
    }
    return result;
}

// Extract the integer value for "key": NUMBER from a JSON snippet.
int extractInt(const std::string& json, const std::string& key) {
    std::string search = "\"" + key + "\"";
    size_t pos = json.find(search);
    if (pos == std::string::npos) return 0;
    pos = json.find(':', pos);
    if (pos == std::string::npos) return 0;
    ++pos;
    while (pos < json.size() &&
           (json[pos] == ' ' || json[pos] == '\n' ||
            json[pos] == '\r' || json[pos] == '\t')) ++pos;
    size_t start = pos;
    if (pos < json.size() && json[pos] == '-') ++pos;
    while (pos < json.size() && std::isdigit(static_cast<unsigned char>(json[pos]))) ++pos;
    if (pos == start) return 0;
    try { return std::stoi(json.substr(start, pos - start)); }
    catch (...) { return 0; }
}

// Extract the bool value for "key": true|false from a JSON snippet.
bool extractBool(const std::string& json, const std::string& key) {
    std::string search = "\"" + key + "\"";
    size_t pos = json.find(search);
    if (pos == std::string::npos) return false;
    pos = json.find(':', pos);
    if (pos == std::string::npos) return false;
    pos = json.find_first_not_of(" \t\n\r", pos + 1);
    if (pos == std::string::npos) return false;
    return json.compare(pos, 4, "true") == 0;
}

// Read an entire file into a string.
std::string readFile(const std::string& path) {
    std::ifstream f(path);
    if (!f.is_open()) return "";
    return std::string(std::istreambuf_iterator<char>(f),
                       std::istreambuf_iterator<char>());
}

} // anonymous namespace

// ============================================================
//  saveTextureMetadata
// ============================================================

bool AssetIO::saveTextureMetadata(const std::string& path,
                                   const std::string& name,
                                   int w, int h,
                                   const std::string& type,
                                   uint32_t seed) {
    std::ofstream f(path);
    if (!f.is_open()) {
        std::cerr << "AssetIO::saveTextureMetadata: cannot open '" << path << "'\n";
        return false;
    }
    f << "{\n";
    f << jkv("  ", "name",   name)                          << ",\n";
    f << jkn("  ", "width",  static_cast<long long>(w))     << ",\n";
    f << jkn("  ", "height", static_cast<long long>(h))     << ",\n";
    f << jkv("  ", "type",   type)                          << ",\n";
    f << jkn("  ", "seed",   static_cast<long long>(seed))  << "\n";
    f << "}\n";
    return true;
}

// ============================================================
//  saveTileset / loadTileset
// ============================================================

bool AssetIO::saveTileset(const std::string& path, const TilesetDef& ts) {
    std::ofstream f(path);
    if (!f.is_open()) {
        std::cerr << "AssetIO::saveTileset: cannot open '" << path << "'\n";
        return false;
    }
    f << "{\n";
    f << jkv("  ", "texturePath", ts.texturePath)              << ",\n";
    f << jkn("  ", "tileWidth",   ts.tileWidth)                << ",\n";
    f << jkn("  ", "tileHeight",  ts.tileHeight)               << ",\n";
    f << "  \"tiles\": [\n";
    for (size_t i = 0; i < ts.tiles.size(); ++i) {
        const auto& t = ts.tiles[i];
        f << "    {\n";
        f << jkn("      ", "id",    t.id)    << ",\n";
        f << jkv("      ", "name",  t.name)  << ",\n";
        f << jkb("      ", "solid", t.solid) << "\n";
        f << "    }";
        if (i + 1 < ts.tiles.size()) f << ",";
        f << "\n";
    }
    f << "  ]\n}\n";
    return true;
}

bool AssetIO::loadTileset(const std::string& path, TilesetDef& ts) {
    std::string json = readFile(path);
    if (json.empty()) {
        std::cerr << "AssetIO::loadTileset: cannot read '" << path << "'\n";
        return false;
    }
    ts.texturePath = extractString(json, "texturePath");
    ts.tileWidth   = extractInt(json, "tileWidth");
    ts.tileHeight  = extractInt(json, "tileHeight");
    if (ts.tileWidth  == 0) ts.tileWidth  = 16;
    if (ts.tileHeight == 0) ts.tileHeight = 16;

    // Locate and parse the "tiles" array.
    size_t arrStart = json.find("\"tiles\"");
    if (arrStart != std::string::npos) {
        arrStart = json.find('[', arrStart);
        if (arrStart != std::string::npos) {
            size_t arrEnd = json.find(']', arrStart);
            if (arrEnd != std::string::npos) {
                std::string arr = json.substr(arrStart, arrEnd - arrStart + 1);
                size_t p = 0;
                while ((p = arr.find('{', p)) != std::string::npos) {
                    size_t e = arr.find('}', p);
                    if (e == std::string::npos) break;
                    std::string obj = arr.substr(p, e - p + 1);
                    TileInfo ti;
                    ti.id    = extractInt(obj,    "id");
                    ti.name  = extractString(obj, "name");
                    ti.solid = extractBool(obj,   "solid");
                    ts.tiles.push_back(ti);
                    p = e + 1;
                }
            }
        }
    }
    return true;
}

// ============================================================
//  saveMap / loadMap
// ============================================================

bool AssetIO::saveMap(const std::string& path, const GameMap& map) {
    std::ofstream f(path);
    if (!f.is_open()) {
        std::cerr << "AssetIO::saveMap: cannot open '" << path << "'\n";
        return false;
    }

    f << "{\n";
    f << jkv("  ", "name",        map.name)                               << ",\n";
    f << jkn("  ", "width",       static_cast<long long>(map.mapWidth))   << ",\n";
    f << jkn("  ", "height",      static_cast<long long>(map.mapHeight))  << ",\n";
    f << jkn("  ", "tileWidth",   static_cast<long long>(map.tileWidth))  << ",\n";
    f << jkn("  ", "tileHeight",  static_cast<long long>(map.tileHeight)) << ",\n";
    f << jkv("  ", "tilesetPath", map.tilesetPath)                        << ",\n";

    // ---- tileLayers ----
    f << "  \"tileLayers\": [\n";
    for (size_t li = 0; li < map.tileLayers.size(); ++li) {
        const auto& layer = map.tileLayers[li];
        f << "    {\n";
        f << jkv("      ", "name",   layer.name)                             << ",\n";
        f << jkn("      ", "width",  static_cast<long long>(layer.width))    << ",\n";
        f << jkn("      ", "height", static_cast<long long>(layer.height))   << ",\n";
        f << "      \"tiles\": [";
        for (size_t ti = 0; ti < layer.tiles.size(); ++ti) {
            f << layer.tiles[ti];
            if (ti + 1 < layer.tiles.size()) f << ",";
        }
        f << "]\n    }";
        if (li + 1 < map.tileLayers.size()) f << ",";
        f << "\n";
    }
    f << "  ],\n";

    // ---- objectLayers ----
    f << "  \"objectLayers\": [\n";
    for (size_t oli = 0; oli < map.objectLayers.size(); ++oli) {
        const auto& ol = map.objectLayers[oli];
        f << "    {\n";
        f << jkv("      ", "name", ol.name) << ",\n";
        f << "      \"objects\": [\n";
        for (size_t oi = 0; oi < ol.objects.size(); ++oi) {
            const auto& obj = ol.objects[oi];
            f << "        {\n";
            f << jkv("          ", "name", obj.name) << ",\n";
            f << jkv("          ", "type", obj.type) << ",\n";
            f << jkf("          ", "x",    obj.x)    << ",\n";
            f << jkf("          ", "y",    obj.y)    << ",\n";
            f << jkf("          ", "w",    obj.w)    << ",\n";
            f << jkf("          ", "h",    obj.h)    << "\n";
            f << "        }";
            if (oi + 1 < ol.objects.size()) f << ",";
            f << "\n";
        }
        f << "      ]\n    }";
        if (oli + 1 < map.objectLayers.size()) f << ",";
        f << "\n";
    }
    f << "  ],\n";

    // ---- entities ----
    f << "  \"entities\": [\n";
    for (size_t ei = 0; ei < map.entities.size(); ++ei) {
        const auto& ent = map.entities[ei];
        f << "    {\n";
        f << jkv("      ", "id",   ent.id)   << ",\n";
        f << jkv("      ", "type", ent.type) << ",\n";
        f << jkf("      ", "x",    ent.x)    << ",\n";
        f << jkf("      ", "y",    ent.y)    << "\n";
        f << "    }";
        if (ei + 1 < map.entities.size()) f << ",";
        f << "\n";
    }
    f << "  ],\n";

    // ---- spawnPoints ----
    f << "  \"spawnPoints\": [\n";
    for (size_t si = 0; si < map.spawnPoints.size(); ++si) {
        const auto& sp = map.spawnPoints[si];
        f << "    {\n";
        f << jkv("      ", "name", sp.name) << ",\n";
        f << jkf("      ", "x",   sp.x)    << ",\n";
        f << jkf("      ", "y",   sp.y)    << "\n";
        f << "    }";
        if (si + 1 < map.spawnPoints.size()) f << ",";
        f << "\n";
    }
    f << "  ],\n";

    // ---- triggers ----
    f << "  \"triggers\": [\n";
    for (size_t ti = 0; ti < map.triggers.size(); ++ti) {
        const auto& trig = map.triggers[ti];
        f << "    {\n";
        f << jkv("      ", "name",   trig.name)   << ",\n";
        f << jkv("      ", "action", trig.action) << ",\n";
        f << jkf("      ", "x",      trig.x)      << ",\n";
        f << jkf("      ", "y",      trig.y)      << ",\n";
        f << jkf("      ", "w",      trig.w)      << ",\n";
        f << jkf("      ", "h",      trig.h)      << "\n";
        f << "    }";
        if (ti + 1 < map.triggers.size()) f << ",";
        f << "\n";
    }
    f << "  ]\n}\n";

    return true;
}

bool AssetIO::loadMap(const std::string& path, GameMap& map) {
    std::string json = readFile(path);
    if (json.empty()) {
        std::cerr << "AssetIO::loadMap: cannot read '" << path << "'\n";
        return false;
    }

    map.name        = extractString(json, "name");
    map.mapWidth    = extractInt(json,    "width");
    map.mapHeight   = extractInt(json,    "height");
    map.tileWidth   = extractInt(json,    "tileWidth");
    map.tileHeight  = extractInt(json,    "tileHeight");
    map.tilesetPath = extractString(json, "tilesetPath");

    if (map.tileWidth  == 0) map.tileWidth  = 16;
    if (map.tileHeight == 0) map.tileHeight = 16;

    // Parse tileLayers array using bracket-depth walk.
    size_t layersStart = json.find("\"tileLayers\"");
    if (layersStart != std::string::npos) {
        layersStart = json.find('[', layersStart);
        if (layersStart != std::string::npos) {
            // Walk to find the matching ']' at depth 0.
            int depth = 0;
            size_t layersEnd = layersStart;
            for (size_t i = layersStart; i < json.size(); ++i) {
                if      (json[i] == '[') ++depth;
                else if (json[i] == ']') { --depth; if (depth == 0) { layersEnd = i; break; } }
            }
            std::string layersArr = json.substr(layersStart, layersEnd - layersStart + 1);

            // Each layer is a '{' ... '}' block.
            size_t p = 1;
            while ((p = layersArr.find('{', p)) != std::string::npos) {
                int d = 0;
                size_t start = p;
                for (size_t i = start; i < layersArr.size(); ++i) {
                    if      (layersArr[i] == '{') ++d;
                    else if (layersArr[i] == '}') { --d; if (d == 0) { p = i; break; } }
                }
                std::string obj = layersArr.substr(start, p - start + 1);

                TileLayer layer;
                layer.name   = extractString(obj, "name");
                layer.width  = extractInt(obj,    "width");
                layer.height = extractInt(obj,    "height");

                if (layer.width > 0 && layer.height > 0) {
                    layer.tiles.reserve(
                        static_cast<size_t>(layer.width) * static_cast<size_t>(layer.height));
                    size_t ta = obj.find("\"tiles\"");
                    if (ta != std::string::npos) {
                        ta = obj.find('[', ta);
                        size_t te = obj.find(']', ta);
                        if (ta != std::string::npos && te != std::string::npos) {
                            std::string tArr = obj.substr(ta + 1, te - ta - 1);
                            std::istringstream ss(tArr);
                            std::string tok;
                            while (std::getline(ss, tok, ',')) {
                                try { layer.tiles.push_back(std::stoi(tok)); }
                                catch (...) {}
                            }
                        }
                    }
                }
                map.tileLayers.push_back(layer);
                ++p;
            }
        }
    }
    return true;
}

// ============================================================
//  ensureDirectory
// ============================================================

bool AssetIO::ensureDirectory(const std::string& path) {
    // Walk the path component by component, creating each directory that
    // does not yet exist. mkdir() returns 0 on success, -1 on error;
    // EEXIST is not an error - the directory already exists.
    std::string current;
    for (size_t i = 0; i <= path.size(); ++i) {
        char c = (i < path.size()) ? path[i] : '\0';
        if (c == '/' || c == '\\' || c == '\0') {
            if (!current.empty()) {
                mkdir(current.c_str(), 0755);  // ignore errors (may already exist)
            }
            if (c != '\0') current += c;
        } else {
            current += c;
        }
    }
    struct stat st{};
    return stat(path.c_str(), &st) == 0 && S_ISDIR(st.st_mode);
}
