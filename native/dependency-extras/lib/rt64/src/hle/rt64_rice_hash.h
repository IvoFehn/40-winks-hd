//
// RT64
//
// SPDX-License-Identifier: GPL-2.0-or-later
//
// Rice texture hashes, worked out live from RDRAM so texture packs named for GLideN64 and Rice Video
// (<name>#<crc>#<format>#<size>[#<palette crc>]_all.png) replace textures without a dumped database.
// The hashing imitates GLideN64's and Rice Video's, as RT64's texture_hasher tool does, and is under
// the GPL, version 2 or later, like its sources (see rt64_rice_hash.cpp for them).
//

#pragma once

#include <string>
#include <vector>

#include "common/rt64_load_types.h"

namespace RT64 {
    struct State;

    // The Rice names a pack could give the texture loadTile samples (as width x height, with this TLUT):
    // "crc#format#size" and, with a palette, "crc#format#size#palette crc" (GLideN64 only names the
    // palette of CI textures, so for others the name without it comes first). Empty if the load isn't
    // one Rice hashes.
    std::vector<std::string> riceTextureKeys(const State *state, const LoadTile &loadTile, uint16_t width, uint16_t height, uint32_t tlut);
};
