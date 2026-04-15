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
// Constants
// =============================================================================

// CRC32 (IEEE 802.3) polynomial, bit-reversed form of 0x04C11DB7.
constexpr uint32_t CRC32_POLYNOMIAL        = 0xEDB88320u;
// Adler32 modulus (largest prime below 2^16 = 65536).
constexpr uint32_t ADLER32_MOD             = 65521u;
// Maximum bytes per DEFLATE stored block (RFC 1951 §3.2.4).
constexpr size_t   DEFLATE_MAX_BLOCK_BYTES = 65535u;

// PNG file signature — same 8 bytes in every valid PNG file.
// 0x89 catches 7-bit ASCII truncation; \r\n catches CR/LF translation.
static const uint8_t PNG_SIGNATURE[8] = {0x89, 0x50, 0x4E, 0x47,
                                          0x0D, 0x0A, 0x1A, 0x0A};
// Zlib header bytes for "deflate, 32 KB window, no dictionary".
// (CMF=0x78, FLG=0x01 such that (CMF*256+FLG) % 31 == 0)
constexpr uint8_t ZLIB_CMF = 0x78u;
constexpr uint8_t ZLIB_FLG = 0x01u;

// =============================================================================
// Section 1 — CRC32 (PNG chunk integrity)
// =============================================================================

/**
 * @brief Compute the CRC32 checksum used by PNG chunks.
 *
 * TEACHING NOTE — CRC32
 * CRC (Cyclic Redundancy Check) detects accidental data corruption.
 * The polynomial is the bit-reversed form of 0x04C11DB7 (IEEE 802.3).
 * Each byte is XOR-ed into the running CRC and then reduced through 8
 * single-bit polynomial divisions. The branchless form `(crc >> 1) ^ (P & -(crc & 1))`
 * is equivalent to "if LSB=1 then XOR with P, else just shift" but avoids
 * a branch prediction miss on every bit.
 *
 * @param data  Pointer to the data bytes.
 * @param len   Number of bytes.
 * @return      32-bit CRC checksum.
 */
inline uint32_t crc32(const uint8_t* data, size_t len)
{
    uint32_t crc = 0xFFFFFFFFu;
    for (size_t i = 0; i < len; ++i) {
        crc ^= static_cast<uint32_t>(data[i]);
        for (int bit = 0; bit < 8; ++bit) {
            crc = (crc >> 1) ^ (CRC32_POLYNOMIAL & static_cast<uint32_t>(-(crc & 1u)));
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
 * Adler32 uses two running sums s1 and s2, both modulo ADLER32_MOD (65521).
 * s1 accumulates byte values; s2 accumulates running values of s1.
 * Simpler and faster than CRC32, but slightly weaker against burst errors.
 *
 * @param data  Data bytes.
 * @param len   Number of bytes.
 * @return      32-bit Adler32 (s2 in high 16 bits, s1 in low 16).
 */
inline uint32_t adler32(const uint8_t* data, size_t len)
{
    uint32_t s1 = 1u, s2 = 0u;
    for (size_t i = 0; i < len; ++i) {
        s1 = (s1 + data[i]) % ADLER32_MOD;
        s2 = (s2 + s1)      % ADLER32_MOD;
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
 * Incremental CRC is computed directly over the type + data bytes to avoid
 * allocating a combined buffer (which would trigger a compiler warning for
 * very large chunks).
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
    // 1. Length field (big-endian)
    uint8_t lenBuf[4];
    writeBE32(lenBuf, static_cast<uint32_t>(len));
    out.write(reinterpret_cast<const char*>(lenBuf), 4);

    // 2. Type bytes
    out.write(type, 4);

    // 3. Data bytes
    if (data && len > 0)
        out.write(reinterpret_cast<const char*>(data), static_cast<std::streamsize>(len));

    // 4. CRC32 computed incrementally over type + data to avoid a large allocation.
    uint32_t crc = 0xFFFFFFFFu;
    auto updateCRC = [&](const uint8_t* buf, size_t n) {
        for (size_t i = 0; i < n; ++i) {
            crc ^= static_cast<uint32_t>(buf[i]);
            for (int bit = 0; bit < 8; ++bit)
                crc = (crc >> 1) ^ (CRC32_POLYNOMIAL & static_cast<uint32_t>(-(crc & 1u)));
        }
    };
    updateCRC(reinterpret_cast<const uint8_t*>(type), 4);
    if (data && len > 0) updateCRC(data, len);
    crc ^= 0xFFFFFFFFu;

    uint8_t crcBuf[4];
    writeBE32(crcBuf, crc);
    out.write(reinterpret_cast<const char*>(crcBuf), 4);
}

// =============================================================================
// Section 5 — PNG Writer (main entry point)
// =============================================================================

/**
 * @brief Write pixel data to a PNG file.
 *
 * Supports:
 *   - Grayscale (channels == 1, PNG color type 0)
 *   - RGB       (channels == 3, PNG color type 2)
 *   - RGBA      (channels == 4, PNG color type 6)
 *
 * Uses uncompressed DEFLATE (stored blocks) — valid PNG, no compression.
 * A production pipeline would compress with zlib or optipng, but the
 * uncompressed form is self-contained and easy to teach.
 *
 * DEFLATE Stored-Block Format (RFC 1951 §3.2.4)
 * ───────────────────────────────────────────────
 *   Byte 0   : BFINAL(1b) | BTYPE=00(2b) | padding(5b)
 *   Bytes 1-2: LEN  (little-endian 16-bit block length)
 *   Bytes 3-4: NLEN (one's-complement of LEN, little-endian)
 *   Bytes 5.. : raw data (up to DEFLATE_MAX_BLOCK_BYTES bytes)
 *
 * @param filename  Output file path.
 * @param width     Image width in pixels.
 * @param height    Image height in pixels.
 * @param channels  1 (gray), 3 (RGB), or 4 (RGBA).
 * @param data      Row-major pixel data (top-to-bottom, left-to-right).
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
    // Before compression, each row is optionally "filtered" to improve
    // compression. Filter 0 (None) stores raw pixel bytes — the simplest
    // choice, optimal for our uncompressed output.

    const int rowBytes       = width * channels;
    const int filteredRowLen = 1 + rowBytes;  // filter byte + pixel bytes

    std::vector<uint8_t> scanlines;
    scanlines.reserve(static_cast<size_t>(height) * static_cast<size_t>(filteredRowLen));

    for (int row = 0; row < height; ++row) {
        scanlines.push_back(0x00u);  // Filter type 0 = None
        const uint8_t* rowPtr = data + static_cast<size_t>(row) * static_cast<size_t>(rowBytes);
        scanlines.insert(scanlines.end(), rowPtr, rowPtr + rowBytes);
    }

    // ---------------------------------------------------------
    // Step 2: Adler32 checksum of raw scanlines (zlib trailer)
    // ---------------------------------------------------------
    const uint32_t adler = adler32(scanlines.data(), scanlines.size());

    // ---------------------------------------------------------
    // Step 3: Build IDAT payload  = zlib header
    //                             + DEFLATE stored blocks
    //                             + Adler32 trailer
    // ---------------------------------------------------------
    std::vector<uint8_t> idat;
    idat.reserve(scanlines.size() + 128);

    // Zlib stream header (RFC 1950 §2.2)
    idat.push_back(ZLIB_CMF);
    idat.push_back(ZLIB_FLG);

    // DEFLATE stored blocks (each up to DEFLATE_MAX_BLOCK_BYTES bytes)
    size_t       offset = 0;
    const size_t total  = scanlines.size();

    while (offset < total) {
        const size_t   blockLen = std::min(DEFLATE_MAX_BLOCK_BYTES, total - offset);
        const bool     isFinal  = (offset + blockLen >= total);
        const uint16_t len16    = static_cast<uint16_t>(blockLen);
        const uint16_t nlen16   = static_cast<uint16_t>(~len16);

        // Block header: BFINAL | BTYPE=00 | LEN | ~LEN
        idat.push_back(isFinal ? 0x01u : 0x00u);  // BFINAL=1 for last block
        idat.push_back( len16        & 0xFFu);     // LEN  low byte
        idat.push_back((len16 >> 8)  & 0xFFu);     // LEN  high byte
        idat.push_back( nlen16       & 0xFFu);     // NLEN low byte
        idat.push_back((nlen16 >> 8) & 0xFFu);     // NLEN high byte

        idat.insert(idat.end(),
                    scanlines.begin() + static_cast<ptrdiff_t>(offset),
                    scanlines.begin() + static_cast<ptrdiff_t>(offset + blockLen));
        offset += blockLen;
    }

    // Adler32 trailer (big-endian, RFC 1950 §2.2)
    idat.push_back((adler >> 24) & 0xFFu);
    idat.push_back((adler >> 16) & 0xFFu);
    idat.push_back((adler >>  8) & 0xFFu);
    idat.push_back( adler        & 0xFFu);

    // ---------------------------------------------------------
    // Step 4: Determine PNG color type from channel count
    // ---------------------------------------------------------
    uint8_t colorType = 0;
    switch (channels) {
        case 1: colorType = 0; break;  // Grayscale
        case 3: colorType = 2; break;  // RGB truecolor
        case 4: colorType = 6; break;  // RGBA
        default: return false;         // Unsupported channel count
    }

    // ---------------------------------------------------------
    // Step 5: Write PNG file — signature, IHDR, IDAT, IEND
    // ---------------------------------------------------------

    out.write(reinterpret_cast<const char*>(PNG_SIGNATURE), 8);

    // IHDR: 13 bytes of image metadata
    uint8_t ihdr[13];
    writeBE32(ihdr + 0, static_cast<uint32_t>(width));
    writeBE32(ihdr + 4, static_cast<uint32_t>(height));
    ihdr[8]  = 8;          // Bit depth: 8 bits per channel
    ihdr[9]  = colorType;  // Color type (see above)
    ihdr[10] = 0;          // Compression method (always 0 in PNG spec)
    ihdr[11] = 0;          // Filter method (always 0)
    ihdr[12] = 0;          // Interlace method (0 = no interlace)
    writeChunk(out, "IHDR", ihdr, 13);

    writeChunk(out, "IDAT", idat.data(), idat.size());
    writeChunk(out, "IEND", nullptr, 0);

    return true;
}

} // namespace ce
