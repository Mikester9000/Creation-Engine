/**
 * validate_assets.cpp - Basic asset validation tests for the Creation Engine.
 * Compile and run via: bash tests/run_tests.sh
 */
#include <iostream>
#include <fstream>
#include <string>
#include <cstdlib>

static bool fileExists(const std::string& path) {
    std::ifstream f(path);
    return f.is_open();
}

static bool fileNonEmpty(const std::string& path) {
    std::ifstream f(path, std::ios::binary | std::ios::ate);
    return f.is_open() && f.tellg() > 0;
}

static int pass = 0, fail = 0;

static void check(const std::string& name, bool ok) {
    if (ok) { std::cout << "  [PASS] " << name << "\n"; ++pass; }
    else     { std::cerr << "  [FAIL] " << name << "\n"; ++fail; }
}

int main() {
    std::cout << "=== Asset Validation Tests ===\n";
    check("test_noise.png exists",    fileNonEmpty("assets/textures/test_noise.png"));
    check("test_checker.png exists",  fileNonEmpty("assets/textures/test_checker.png"));
    check("test_lava.png exists",     fileNonEmpty("assets/textures/test_lava.png"));
    check("test_map.json exists",     fileNonEmpty("assets/maps/test_map.json"));
    check("test_forest.json exists",  fileNonEmpty("assets/maps/test_forest.json"));
    check("default tileset exists",   fileNonEmpty("assets/maps/default.tileset.json"));
    std::cout << "\nResults: " << pass << " passed, " << fail << " failed\n";
    return fail > 0 ? 1 : 0;
}
