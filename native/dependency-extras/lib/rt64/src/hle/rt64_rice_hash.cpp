//
// RT64
//
// SPDX-License-Identifier: GPL-2.0-or-later
//
// Rice texture hashes, worked out live from RDRAM. This file is under the GNU General Public License,
// version 2 or later, unlike the rest of RT64 (MIT). Its hashing is RT64's texture_hasher tool's
// (src/tools/texture_hasher/texture_hasher.cpp), which "has been referenced from GlideN64 and RiceVideo
// to imitate their hashing algorithms" and is under the GPL to comply with their licenses:
// - the Rice CRC (RiceCRC32, the palette CRC over cimax + 1 entries) is GlideHQ's, in GLideN64's
//   src/GLideNHQ/TxUtil.cpp, copyright (C) 2007 Hiroshi Morii, GPL version 2 or later;
// - the sizes hashed (ReverseDXT, CalculateMaxCI, the tile and block dimensions) are Rice Video's
//   (Rice1964; mupen64plus-video-rice, GPL version 2 or later), as GLideN64 also uses them. GLideN64
//   (Sergey Lipskiy and contributors) is under the GPL version 2: src/tools/texture_hasher/GLIDEN64-LICENSE.
// Which RDRAM a load read follows TextureManager::dumpTexture (rt64_rdp_tmem.cpp), whose dumps
// texture_hasher reads.
//
// This program is free software; you can redistribute it and/or modify it under the terms of the GNU
// General Public License as published by the Free Software Foundation; either version 2 of the License,
// or (at your option) any later version. This program is distributed in the hope that it will be
// useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
// FOR A PARTICULAR PURPOSE. See the GNU General Public License (https://www.gnu.org/licenses/) for
// more details.
//

#include "rt64_rice_hash.h"

#include <algorithm>
#include <cstdio>
#include <cstring>

#include "shared/rt64_f3d_defines.h"

#include "rt64_state.h"

namespace RT64 {
    namespace {
        // RDRAM as RT64 sees it (State::RDRAMSize is its last byte).
        constexpr uint32_t RiceRDRAMBytes = 0x800000;

        uint32_t CalculateDXT(uint32_t txl2words) {
            if (txl2words == 0) {
                return 1U;
            }
            else {
                return (2048 + txl2words - 1) / txl2words;
            }
        }

        uint32_t Txl2Words(uint32_t width, uint32_t size) {
            static const uint32_t sizeBytes[4] = { 0, 1, 2, 4 };
            if (size == 0) {
                return std::max(1U, width / 16);
            }
            else {
                return std::max(1U, width * sizeBytes[size] / 8);
            }
        }

        int ReverseDXT(uint32_t val, uint32_t width, uint32_t size) {
            if (val == 0x800) {
                return 1;
            }

            int low = 2047 / val;
            if (CalculateDXT(low) > val) {
                low++;
            }

            int high = 2047 / (val - 1);
            if (low == high) {
                return low;
            }

            for (int i = low; i <= high; i++) {
                if (Txl2Words(width, size) == (uint32_t)i) {
                    return i;
                }
            }

            return (low + high) / 2;
        }

        uint8_t CalculateMaxCI8b(const uint8_t *src, uint32_t width, uint32_t height, uint32_t rowStride) {
            uint8_t val = 0;
            for (uint32_t y = 0; y < height; ++y) {
                const uint8_t *buf = src + rowStride * y;
                for (uint32_t x = 0; x < width; ++x) {
                    if (buf[x] > val) {
                        val = buf[x];
                    }

                    if (val == 0xFF) {
                        return uint8_t(0xFF);
                    }
                }
            }

            return val;
        }

        uint8_t CalculateMaxCI4b(const uint8_t *src, uint32_t width, uint32_t height, uint32_t rowStride) {
            uint8_t val = 0;
            width >>= 1;
            for (uint32_t y = 0; y < height; ++y) {
                const uint8_t *buf = src + rowStride * y;
                for (uint32_t x = 0; x < width; ++x) {
                    const uint8_t val1 = buf[x] >> 4;
                    const uint8_t val2 = buf[x] & 0xF;
                    val = std::max(val, std::max(val1, val2));
                    if (val == 0xF) {
                        return uint8_t(0xF);
                    }
                }
            }

            return val;
        }

        uint32_t RiceCRC32(const uint8_t *src, int width, int height, int size, int rowStride) {
            uint32_t crc32Ret = 0;
            const uint32_t bytesPerLine = width << size >> 1;
            int y = height - 1;
            while (y >= 0) {
                uint32_t esi = 0;
                int x = bytesPerLine - 4;
                while (x >= 0) {
                    std::memcpy(&esi, src + x, sizeof(esi));
                    esi ^= x;

                    crc32Ret = (crc32Ret << 4) + ((crc32Ret >> 28) & 15);
                    crc32Ret += esi;
                    x -= 4;
                }

                esi ^= y;
                crc32Ret += esi;
                src += rowStride;
                --y;
            }

            return crc32Ret;
        }

        std::string hashString(uint32_t hash) {
            char hexStr[16];
            snprintf(hexStr, sizeof(hexStr), "%08x", hash);
            return std::string(hexStr);
        }
    }

    std::vector<std::string> riceTextureKeys(const State *state, const LoadTile &loadTile, uint16_t width, uint16_t height, uint32_t tlut) {
        const LoadTile &drawTile = loadTile;
        const LoadOperation &loadOp = state->rdp->rice.lastLoadOpByTMEM[loadTile.tmem];

        // The RDRAM the load read (TextureManager::dumpTexture).
        uint32_t rdramStart = loadOp.texture.address;
        uint32_t rdramCount = 0;
        const uint32_t commonBytesOffset = (loadOp.tile.uls >> 2) << loadOp.texture.siz >> 1;
        uint32_t commonBytesPerRow = loadOp.texture.width << loadOp.texture.siz >> 1;
        if (loadOp.type == LoadOperation::Type::Block) {
            const uint32_t wordCount = ((loadOp.tile.lrs - loadOp.tile.uls) >> (4 - loadOp.tile.siz)) + 1;
            rdramStart = loadOp.texture.address + commonBytesOffset + commonBytesPerRow * loadOp.tile.ult;
            rdramCount = (wordCount << 3);
            commonBytesPerRow = std::max(commonBytesPerRow, uint32_t(loadTile.line) << 3U);
        }
        else if (loadOp.type == LoadOperation::Type::Tile) {
            const uint32_t rowCount = 1 + ((loadOp.tile.lrt >> 2) - (loadOp.tile.ult >> 2));
            rdramStart = loadOp.texture.address + commonBytesOffset + commonBytesPerRow * (loadOp.tile.ult >> 2);
            rdramCount = rowCount * commonBytesPerRow;
        }
        else {
            return {};
        }

        const uint32_t loadTileBpr = width << loadTile.siz >> 1;
        rdramCount = std::max(rdramCount, std::max(loadTileBpr, commonBytesPerRow) * height);
        if ((rdramCount == 0) || (rdramStart >= RiceRDRAMBytes) || (rdramCount > (RiceRDRAMBytes - rdramStart))) {
            return {};
        }

        const uint8_t *rdramBytes = state->RDRAM + rdramStart;

        // The size Rice hashes (texture_hasher's addRiceHash).
        int bpl;
        int hashWidth, hashHeight;
        if (loadOp.type == LoadOperation::Type::Tile) {
            uint16_t tileWidth = (std::max((loadOp.tile.lrs >> 2) - (loadOp.tile.uls >> 2), 0) + 1) & 0x03FF;
            uint16_t tileHeight = (std::max((loadOp.tile.lrt >> 2) - (loadOp.tile.ult >> 2), 0) + 1) & 0x03FF;
            tileWidth = (loadOp.tile.masks != 0) ? std::min(tileWidth, uint16_t(1U << loadOp.tile.masks)) : tileWidth;
            bpl = loadOp.texture.width << loadOp.texture.siz >> 1;
            hashWidth = std::min(tileWidth, loadOp.texture.width);
            if (loadOp.tile.siz > drawTile.siz) {
                hashWidth <<= loadOp.tile.siz - drawTile.siz;
            }

            hashHeight = (loadOp.tile.maskt != 0) ? std::min(tileHeight, uint16_t(1U << loadOp.tile.maskt)) : tileHeight;
        }
        else {
            const int tileWidth = std::max((drawTile.lrs >> 2) - (drawTile.uls >> 2), 0) + 1;
            const int tileHeight = std::max((drawTile.lrt >> 2) - (drawTile.ult >> 2), 0) + 1;
            const int maskWidth = (drawTile.masks == 0) ? tileWidth : (1 << drawTile.masks);
            const int maskHeight = (drawTile.maskt == 0) ? tileHeight : (1 << drawTile.maskt);
            const bool clamps = (drawTile.masks == 0) || (drawTile.cms & G_TX_CLAMP);
            const bool clampt = (drawTile.maskt == 0) || (drawTile.cmt & G_TX_CLAMP);
            hashWidth = (clamps && (tileWidth <= 256)) ? std::min(maskWidth, tileWidth) : maskWidth;
            hashHeight = ((clampt && (tileHeight <= 256)) || (maskHeight > 256)) ? std::min(maskHeight, tileHeight) : maskHeight;
            if (drawTile.siz == G_IM_SIZ_32b) {
                bpl = drawTile.line << 4;
            }
            else if (loadOp.tile.lrt == 0) {
                bpl = drawTile.line << 3;
            }
            else {
                uint32_t dxt = loadOp.tile.lrt;
                if (dxt > 1) {
                    dxt = ReverseDXT(dxt, loadOp.texture.width, loadOp.texture.siz);
                }

                bpl = dxt << 3;
            }
        }

        // Rice hashes at least this many bytes; texture_hasher skips a texture whose dump is shorter.
        if ((hashWidth <= 0) || (hashHeight <= 0) || (bpl <= 0)) {
            return {};
        }

        const uint32_t expectedSize = (hashHeight - 1) * bpl + (hashWidth << drawTile.siz >> 1);
        if (expectedSize > rdramCount) {
            return {};
        }

        const uint32_t riceCrc = RiceCRC32(rdramBytes, hashWidth, hashHeight, drawTile.siz, bpl);
        const std::string key = hashString(riceCrc) + "#" + std::to_string(drawTile.fmt) + "#" + std::to_string(drawTile.siz);
        if (tlut == 0) {
            return { key };
        }

        // The palette, as loaded last into the TLUT half of TMEM (TextureManager::dumpTexture).
        const bool CI4 = (drawTile.siz == G_IM_SIZ_4b);
        const int32_t paletteTMEM = (RDP_TMEM_WORDS >> 1) + (CI4 ? (drawTile.palette << 4) : 0);
        const LoadOperation &paletteLoadOp = state->rdp->rice.lastLoadOpByTMEM[paletteTMEM];
        const uint32_t paletteBytesOffset = (paletteLoadOp.tile.uls >> 2) << paletteLoadOp.texture.siz >> 1;
        const uint32_t paletteBytesPerRow = paletteLoadOp.texture.width << paletteLoadOp.texture.siz >> 1;
        const uint32_t paletteRowCount = 1 + ((paletteLoadOp.tile.lrt >> 2) - (paletteLoadOp.tile.ult >> 2));
        const uint32_t paletteWordsPerRow = ((paletteLoadOp.tile.lrs >> 2) - (paletteLoadOp.tile.uls >> 2)) + 1;
        const uint32_t paletteRdramStart = paletteLoadOp.texture.address + paletteBytesOffset + paletteBytesPerRow * (paletteLoadOp.tile.ult >> 2);
        const uint32_t paletteRdramCount = (paletteRowCount - 1) * paletteBytesPerRow + (paletteWordsPerRow << 3);
        if ((paletteRdramCount == 0) || (paletteRdramStart >= RiceRDRAMBytes) || (paletteRdramCount > (RiceRDRAMBytes - paletteRdramStart))) {
            return { key };
        }

        const uint8_t *paletteBytes = state->RDRAM + paletteRdramStart;
        const uint8_t cimax = CI4 ? CalculateMaxCI4b(rdramBytes, hashWidth, hashHeight, bpl) : CalculateMaxCI8b(rdramBytes, hashWidth, hashHeight, bpl);

        // The palette CRC hashes cimax + 1 entries of two bytes: make sure they're in RDRAM.
        if ((uint32_t(cimax) + 1) * 2 > (RiceRDRAMBytes - paletteRdramStart)) {
            return { key };
        }

        const uint32_t ricePaletteCrc = RiceCRC32(paletteBytes, cimax + 1, 1, 2, CI4 ? 32 : 512);

        const std::string paletteKey = key + "#" + hashString(ricePaletteCrc);
        if (drawTile.fmt == G_IM_FMT_CI) {
            return { paletteKey, key };
        }
        else {
            return { key, paletteKey };
        }
    }
};
