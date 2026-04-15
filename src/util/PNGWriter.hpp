/**
 * @file PNGWriter.hpp
 * @brief Zero-dependency PNG encoder for writing PBR texture maps to disk.
 *
 * =============================================================================
 * TEACHING NOTE — PNG File Format
 * =============================================================================
 *
 * PNG (Portable Network Graphics) stores images losslessly using:
 *   1. A file signature (8 bytes) to identify the format.
 *   2. A series of "chunks", each with: [length][type][data][CRC32].
 *   3. Required chunks: IHDR (header), IDAT (pixel data), IEND (end marker).
 *
 * CHUNK STRUCTURE
 * ───────────────
 *   ┌──────────┬──────────┬──────────────┬──────────┐
 *   │ 4 bytes  │ 4 bytes  │  N bytes     │ 4 bytes  │
 *   │ Length   │ Type     │  Data        │ CRC32    │
 *   └──────────┴──────────┴──────────────┴──────────┘
 *
 * IDAT DATA FORMAT
 * ─────────────────
 * The pixel data in IDAT is zlib-compressed. Each scanline (row) is prefixed
 * with a 1-byte filter type before compression. We use filter type 0 (None).
 *
 * This implementation uses DEFLATE "stored" mode (BTYPE=00) — no compression.
 * The output PNG is valid but slightly larger than compressed PNGs.
 * For teaching, this makes the encoder self-contained with no zlib dependency.
 *
 * CHECKSUMS
 * ──────────
 * • CRC32  : Detects corrupt chunks. Polynomial 0xEDB88320 (IEEE 802.3).
 * • Adler32: Zlib wrapper integrity check. Used inside IDAT.
 *
 * LESSON EXERCISES
 * ─────────────────
 * 1. Open a generated PNG in a hex editor — find the "IHDR", "IDAT" bytes.
 * 2. The first 8 bytes are always {0x89,P,N,G,\r,\n,0x1A,\n} — why?
 *    (The 0x89 catches 7-bit ASCII truncation; \r\n catches CR/LF translation.)
 * 3. Add support for filter type 1 (Sub filter) and compare file sizes.
 *
 * @author  Creation Engine Project
 * @version 1.0
 */

#pragma once

#include <cstdint>
#include <cstring>
#include <fstream>
#include <string>
#include <vector>
#include <algorithm>

namespace ce {

// =============================================================================
// Section 1 — CRC32 (PNG chunk integrity)
// =============================================================================

/**
 * @brief Compute the CRC32 checksum used by PNG chunks.
 *
 * TEACHING NOTE — CRC32
 * CRC (Cyclic Redundancy Check) detects accidental data corruption.
 * The polynomial 0xEDB88320 is the bit-reversed form of 0x04C11DB7 (IEEE 802.3).
 * CRC is computed incrementally: feed bytes one by one, XOR with polynomial.
 *
 * @param data  Pointer to the data bytes.
 * @param len   Number of bytes.
 * @return      32-bit CRC checksum.
 */
inline uint32_t crc32(const uint8_t* data, size_t len)
{
    static const uint32_t POLY = 0xEDB88320u;
    uint32_t crc = 0xFFFFFFFFu;
    for (size_t i = 0; i < len; ++i) {
        crc ^= static_cast<uint32_t>(data[i]);
        for (int k = 0; k < 8; ++k) {
            // Branchless: if LSB set, XOR with polynomial; else just shift.
            crc = (crc >> 1) ^ (POLY & static_cast<uint32_t>(-(crc & 1u)));
        }
    }
    return crc ^ 0xFFFFFFFFu;
}

// =============================================================================
// Section 2 — Adler32 (zlib wrapper integrity)
// =============================================================================

/**
 * @brief Compute Adler32 checksum (RFC 1950, used inside zlib IDAT data).
 *
 * TEACHING NOTE — Adler32
 * Adler32 uses two running sums s1 and s2, both modulo 65521 (largest prime
 * below 65536). Simpler and faster than CRC32, but slightly weaker.
 *
 * @param data  Data bytes.
 * @param len   Number of bytes.
 * @return      32-bit Adler32 checksum (s2 in high 16 bits, s1 in low 16).
 */
inline uint32_t adler32(const uint8_t* data, size_t len)
{
    constexpr uint32_t MOD = 65521u;
    uint32_t s1 = 1u, s2 = 0u;
    for (size_t i = 0; i < len; ++i) {
        s1 = (s1 + data[i]) % MOD;
        s2 = (s2 + s1)      % MOD;
    }
    return (s2 << 16) | s1;
}

// =============================================================================
// Section 3 — Helper: big-endian write
// =============================================================================

/** @brief Write a 32-bit value in big-endian byte order into buf[0..3]. */
inline void writeBE32(uint8_t* buf, uint32_t v)
{
    buf[0] = (v >> 24) & 0xFFu;
    buf[1] = (v >> 16) & 0xFFu;
    buf[2] = (v >>  8) & 0xFFu;
    buf[3] =  v        & 0xFFu;
}

// =============================================================================
// Section 4 — PNG Chunk writer
// =============================================================================

/**
 * @brief Write one PNG chunk to an output stream.
 *
 * @param out   Binary output stream.
 * @param type  4-character chunk type string (e.g., "IHDR").
 * @param data  Pointer to chunk data bytes (may be nullptr if len == 0).
 * @param len   Number of data bytes.
 */
inline void writeChunk(std::ofstream& out,
                       const char*    type,
                       const uint8_t* data,
                       size_t         len)
{
    // Length field (big-endian)
    uint8_t lenBuf[4];
    writeBE32(lenBuf, static_cast<uint32_t>(len));
    out.write(reinterpret_cast<const char*>(lenBuf), 4);

    // Type bytes
    out.write(type, 4);

    // Data bytes
    if (data && len > 0)
        out.write(reinterpret_cast<const char*>(data), static_cast<std::streamsize>(len));

    // CRC32 over type + data — compute incrementally to avoid a large allocation
    // and the associated -Wstringop-overflow false-positive when len is unknown.
    uint32_t crc = 0xFFFFFFFFu;
    auto crcStep = [&](const uint8_t* buf, size_t n) {
        static const uint32_t POLY = 0xEDB88320u;
        for (size_t i = 0; i < n; ++i) {
            crc ^= static_cast<uint32_t>(buf[i]);
            for (int k = 0; k < 8; ++k)
                crc = (crc >> 1) ^ (POLY & static_cast<uint32_t>(-(crc & 1u)));
        }
    };
    crcStep(reinterpret_cast<const uint8_t*>(type), 4);
    if (data && len > 0) crcStep(data, len);
    crc ^= 0xFFFFFFFFu;

    uint8_t crcOut[4];
    writeBE32(crcOut, crc);
    out.write(reinterpret_cast<const char*>(crcOut), 4);
}

// =============================================================================
// Section 5 — PNG Writer (main entry point)
// =============================================================================

/**
 * @brief Write pixel data to a PNG file.
 *
 * Supports:
 *   - RGB  (channels == 3, PNG color type 2)
 *   - RGBA (channels == 4, PNG color type 6)
 *   - Grayscale (channels == 1, PNG color type 0)
 *
 * Uses uncompressed DEFLATE (stored blocks) — valid PNG, no compression.
 * For the purpose of teaching asset pipelines, uncompressed PNGs are fine;
 * a real-world pipeline would pass these through optipng or pngcrush.
 *
 * DEFLATE Stored-Block Format (RFC 1951 §3.2.4)
 * ───────────────────────────────────────────────
 *   Byte 0: BFINAL(1 bit) | BTYPE=00(2 bits) | padding(5 bits)
 *   Bytes 1-2: LEN  (little-endian 16-bit)
 *   Bytes 3-4: NLEN (one's-complement of LEN, little-endian)
 *   Bytes 5..LEN+4: raw data
 *
 * @param filename  Output file path.
 * @param width     Image width in pixels.
 * @param height    Image height in pixels.
 * @param channels  1 (gray), 3 (RGB), or 4 (RGBA).
 * @param data      Row-major pixel data (top to bottom, left to right).
 *                  Expected size: width * height * channels bytes.
 * @return          true on success, false if the file could not be opened.
 */
inline bool writePNG(const std::string& filename,
                     int                width,
                     int                height,
                     int                channels,
                     const uint8_t*     data)
{
    std::ofstream out(filename, std::ios::binary);
    if (!out.is_open()) return false;

    // ---------------------------------------------------------
    // Step 1: Build raw scanlines with filter byte 0 (None)
    // ---------------------------------------------------------
    // TEACHING NOTE — Filter Types
    // Before compression, each row can optionally be "filtered" to improve
    // compression ratio. Filter 0 (None) stores the raw pixel values.
    // The filter byte is part of the compressed data, not a metadata header.

    const int rowStride   = width * channels;
    const int filtRowSize = 1 + rowStride;     // filter byte + pixels

    std::vector<uint8_t> scanlines;
    scanlines.reserve(static_cast<size_t>(height) * static_cast<size_t>(filtRowSize));

    for (int y = 0; y < height; ++y) {
        scanlines.push_back(0x00u);  // filter type 0 = None
        const uint8_t* row = data + static_cast<size_t>(y) * static_cast<size_t>(rowStride);
        scanlines.insert(scanlines.end(), row, row + rowStride);
    }

    // ---------------------------------------------------------
    // Step 2: Compute Adler32 over the raw scanlines
    //         (goes at the end of the zlib stream)
    // ---------------------------------------------------------
    uint32_t a32 = adler32(scanlines.data(), scanlines.size());

    // ---------------------------------------------------------
    // Step 3: Build IDAT payload (zlib header + deflate blocks + adler32)
    // ---------------------------------------------------------

    std::vector<uint8_t> idat;
    idat.reserve(scanlines.size() + 128);

    // Zlib header (RFC 1950 §2.2)
    // CMF = 0x78: deflate (CM=8), window size 32 KB (CINFO=7)
    // FLG must satisfy (CMF*256 + FLG) % 31 == 0.
    //   0x78 * 256 = 30720; 30720 % 31 = 30; FLG = 1 makes sum = 30721 % 31 = 0.
    idat.push_back(0x78u);  // CMF
    idat.push_back(0x01u);  // FLG

    // Deflate stored blocks (max 65535 bytes each)
    constexpr size_t MAX_BLOCK = 65535u;
    size_t offset = 0;
    const size_t total = scanlines.size();

    while (offset < total) {
        const size_t blockLen  = std::min(MAX_BLOCK, total - offset);
        const bool   isFinal   = (offset + blockLen >= total);
        const uint16_t len16   = static_cast<uint16_t>(blockLen);
        const uint16_t nlen16  = static_cast<uint16_t>(~len16);

        // Block header
        idat.push_back(isFinal ? 0x01u : 0x00u);      // BFINAL | BTYPE=00
        idat.push_back( len16        & 0xFFu);         // LEN low
        idat.push_back((len16 >> 8)  & 0xFFu);         // LEN high
        idat.push_back( nlen16       & 0xFFu);         // NLEN low
        idat.push_back((nlen16 >> 8) & 0xFFu);         // NLEN high

        // Block data
        idat.insert(idat.end(),
                    scanlines.begin() + static_cast<ptrdiff_t>(offset),
                    scanlines.begin() + static_cast<ptrdiff_t>(offset + blockLen));
        offset += blockLen;
    }

    // Adler32 trailer (big-endian, RFC 1950)
    idat.push_back((a32 >> 24) & 0xFFu);
    idat.push_back((a32 >> 16) & 0xFFu);
    idat.push_back((a32 >>  8) & 0xFFu);
    idat.push_back( a32        & 0xFFu);

    // ---------------------------------------------------------
    // Step 4: Determine PNG color type from channel count
    // ---------------------------------------------------------
    uint8_t colorType = 0;
    switch (channels) {
        case 1: colorType = 0; break;  // Grayscale
        case 3: colorType = 2; break;  // RGB
        case 4: colorType = 6; break;  // RGBA
        default: return false;         // Unsupported
    }

    // ---------------------------------------------------------
    // Step 5: Assemble and write the PNG file
    // ---------------------------------------------------------

    // PNG file signature (always the same 8 bytes)
    const uint8_t sig[] = {0x89, 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x1A, 0x0A};
    out.write(reinterpret_cast<const char*>(sig), 8);

    // IHDR chunk (13 bytes of image header)
    uint8_t ihdr[13];
    writeBE32(ihdr + 0, static_cast<uint32_t>(width));
    writeBE32(ihdr + 4, static_cast<uint32_t>(height));
    ihdr[8]  = 8;          // Bit depth: 8 bits per channel
    ihdr[9]  = colorType;  // Color type
    ihdr[10] = 0;          // Compression method (always 0 in PNG)
    ihdr[11] = 0;          // Filter method (always 0)
    ihdr[12] = 0;          // Interlace method (0 = no interlace)
    writeChunk(out, "IHDR", ihdr, 13);

    // IDAT chunk (compressed pixel data)
    writeChunk(out, "IDAT", idat.data(), idat.size());

    // IEND chunk (end marker, no data)
    writeChunk(out, "IEND", nullptr, 0);

    return true;
}

} // namespace ce
