/**
 * @file JsonWriter.hpp
 * @brief Minimal, zero-dependency JSON builder for exporting materials and maps.
 *
 * =============================================================================
 * TEACHING NOTE — JSON as a Game Asset Format
 * =============================================================================
 *
 * JSON (JavaScript Object Notation, RFC 8259) has become the standard human-
 * readable format for game asset manifests, level files, and material
 * descriptors.  Why JSON over binary formats?
 *
 *   ADVANTAGES
 *   • Human-readable: inspect/edit assets without a special tool.
 *   • Self-describing: field names are embedded in the file.
 *   • Wide ecosystem: parseable from any language without custom code.
 *   • Version-friendly: adding new fields doesn't break old parsers.
 *
 *   TRADE-OFFS
 *   • Larger files than binary formats.
 *   • Slower to parse (text → numbers involves conversion).
 *   For teaching and prototyping these trade-offs are acceptable.
 *
 * DESIGN OF THIS WRITER
 * ─────────────────────
 * The writer uses a "comma-before-element" approach:
 *   • The first element in a container writes no comma.
 *   • Every subsequent element writes "," before itself.
 *   • Newlines and indentation are written before every key or array element.
 * This avoids look-ahead (trailing comma problems) and backtracking.
 *
 * LESSON EXERCISES
 * ─────────────────
 * 1. Add a writeComment() helper that prefixes keys with "// comment" — is
 *    this valid JSON? (No. JSON has no comment syntax. JSONC does.)
 * 2. Add a writeBinary() helper that base64-encodes raw bytes inline — useful
 *    for embedding small textures directly in a material file.
 *
 * @author  Creation Engine Project
 * @version 1.0
 */

#pragma once

#include <cstdio>
#include <cmath>
#include <string>
#include <vector>

namespace ce {

/**
 * @class JsonWriter
 * @brief Streaming JSON builder with automatic indentation.
 *
 * Usage:
 * @code
 *   JsonWriter j;
 *   j.beginObject();
 *     j.keyString("name", "wet_stone");
 *     j.keyFloat("roughness", 0.85f);
 *     j.writeKey("layers");
 *     j.beginArray();
 *       j.writeInt(0);
 *       j.writeInt(1);
 *     j.endArray();
 *   j.endObject();
 *   std::string json = j.str();
 * @endcode
 */
class JsonWriter {
public:

    explicit JsonWriter(int indentSpaces = 2)
        : m_spaces(indentSpaces) {}

    // -------------------------------------------------------------------------
    // Object / Array brackets
    // -------------------------------------------------------------------------

    void beginObject() { openBracket('{'); }
    void endObject()   { closeBracket('}'); }
    void beginArray()  { openBracket('['); }
    void endArray()    { closeBracket(']'); }

    // -------------------------------------------------------------------------
    // Key (object context only)
    // -------------------------------------------------------------------------

    /**
     * @brief Write an object key ("key": ).
     * Must be followed immediately by a value write.
     */
    void writeKey(const std::string& key)
    {
        // In object context, each key is an "element" that gets comma + newline.
        insertCommaAndIndent();
        m_buf += '"';
        m_buf += escapeString(key);
        m_buf += "\": ";
        m_afterKey = true;
    }

    // -------------------------------------------------------------------------
    // Value writers
    // -------------------------------------------------------------------------

    void writeString(const std::string& v)
    {
        preValue();
        m_buf += '"';
        m_buf += escapeString(v);
        m_buf += '"';
    }

    void writeInt(int64_t v)
    {
        preValue();
        m_buf += std::to_string(v);
    }

    void writeBool(bool v)
    {
        preValue();
        m_buf += v ? "true" : "false";
    }

    void writeNull()
    {
        preValue();
        m_buf += "null";
    }

    /**
     * @brief Write a floating-point number with up to 6 significant figures.
     *
     * TEACHING NOTE — Float precision in JSON
     * PBR parameters (roughness, metallic) only need ~3 decimal places.
     * Using %g avoids trailing zeros (0.500000 → 0.5).
     */
    void writeFloat(float v)
    {
        preValue();
        if (std::isnan(v) || std::isinf(v)) {
            m_buf += "null";   // JSON does not support NaN / Infinity
        } else {
            char buf[32];
            std::snprintf(buf, sizeof(buf), "%.6g", static_cast<double>(v));
            m_buf += buf;
        }
    }

    // -------------------------------------------------------------------------
    // Convenience: key + value in one call
    // -------------------------------------------------------------------------

    void keyString(const std::string& k, const std::string& v)
    { writeKey(k); writeString(v); }

    void keyInt  (const std::string& k, int64_t v) { writeKey(k); writeInt(v);   }
    void keyFloat(const std::string& k, float   v) { writeKey(k); writeFloat(v); }
    void keyBool (const std::string& k, bool    v) { writeKey(k); writeBool(v);  }
    void keyNull (const std::string& k)            { writeKey(k); writeNull();   }

    // -------------------------------------------------------------------------
    // Output
    // -------------------------------------------------------------------------

    /** @brief Return the complete JSON string. */
    const std::string& str() const { return m_buf; }

private:

    // -------------------------------------------------------------------------
    // Container open / close
    // -------------------------------------------------------------------------

    /**
     * @brief Open a container bracket ({ or [).
     *
     * If called after a key (object value context), write inline.
     * If called as an array element or top-level, prepend comma + newline.
     */
    void openBracket(char br)
    {
        if (!m_afterKey && !m_levels.empty()) {
            // We're an array element — handle comma and newline.
            insertCommaAndIndent();
        }
        // If m_afterKey, the key line already set up indent; just write inline.
        m_afterKey = false;

        m_buf += br;
        m_buf += '\n';
        ++m_indent;
        m_levels.push_back({false});
    }

    /**
     * @brief Close a container bracket (} or ]).
     * Writes a newline + indent before the bracket only if elements were written.
     */
    void closeBracket(char br)
    {
        const bool hadElements = !m_levels.empty() && m_levels.back().hasElements;
        --m_indent;
        m_levels.pop_back();
        if (hadElements) {
            m_buf += '\n';
            m_buf += indentStr();
        }
        m_buf += br;
    }

    // -------------------------------------------------------------------------
    // Primitive value preamble
    // -------------------------------------------------------------------------

    /**
     * @brief Called before writing any primitive value.
     * Handles comma + newline + indent for array elements; nothing for key values.
     */
    void preValue()
    {
        if (m_afterKey) {
            // Writing the value for an object key: already indented by writeKey.
            m_afterKey = false;
        } else {
            // Array element: comma + newline + indent.
            insertCommaAndIndent();
        }
    }

    // -------------------------------------------------------------------------
    // Comma + indent insertion
    // -------------------------------------------------------------------------

    /**
     * @brief Insert comma separator and newline + indent before an element or key.
     *
     * TEACHING NOTE — Comma-Before Design
     * Tracking whether to emit a comma BEFORE each element is simpler than
     * tracking trailing commas (which would require look-ahead or backtracking).
     * The rule: the first element in a container gets no comma;
     * every subsequent element gets "," prepended.
     */
    void insertCommaAndIndent()
    {
        if (!m_levels.empty() && m_levels.back().hasElements) {
            m_buf += ',';
        }
        if (!m_levels.empty()) {
            m_levels.back().hasElements = true;
        }
        m_buf += '\n';
        m_buf += indentStr();
    }

    // -------------------------------------------------------------------------
    // Helpers
    // -------------------------------------------------------------------------

    std::string indentStr() const
    {
        return std::string(static_cast<size_t>(m_indent * m_spaces), ' ');
    }

    /**
     * @brief Escape special characters per JSON spec (RFC 8259 §7).
     */
    static std::string escapeString(const std::string& s)
    {
        std::string out;
        out.reserve(s.size() + 4);
        for (char c : s) {
            switch (c) {
                case '"':  out += "\\\""; break;
                case '\\': out += "\\\\"; break;
                case '\n': out += "\\n";  break;
                case '\r': out += "\\r";  break;
                case '\t': out += "\\t";  break;
                default:
                    if (static_cast<unsigned char>(c) < 0x20) {
                        char esc[8];
                        std::snprintf(esc, sizeof(esc), "\\u%04x",
                                      static_cast<unsigned char>(c));
                        out += esc;
                    } else {
                        out += c;
                    }
                    break;
            }
        }
        return out;
    }

    // -------------------------------------------------------------------------
    // State
    // -------------------------------------------------------------------------

    std::string m_buf;
    int         m_indent   = 0;
    int         m_spaces   = 2;
    bool        m_afterKey = false;

    struct Level { bool hasElements = false; };
    std::vector<Level> m_levels;  ///< Stack of open containers.
};

} // namespace ce

