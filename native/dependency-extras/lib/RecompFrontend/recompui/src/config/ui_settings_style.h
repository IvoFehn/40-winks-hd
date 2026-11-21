#pragma once

#include "elements/ui_types.h"

namespace recompui::settings_style {
    inline constexpr float width = 1248.0f;
    inline constexpr float height = 800.0f;
    inline constexpr float radius = 20.0f;

    inline constexpr Color scrim{7, 9, 18, 112};
    inline constexpr Color panel{21, 24, 40, 252};
    inline constexpr Color inset{16, 19, 32};
    inline constexpr Color control{31, 36, 55};
    inline constexpr Color hovered{45, 51, 75};
    inline constexpr Color border{58, 64, 87};
    inline constexpr Color divider{42, 47, 68};
    inline constexpr Color text{244, 244, 251};
    inline constexpr Color muted{173, 182, 207};
    inline constexpr Color subdued{130, 141, 171};
    inline constexpr Color accent{250, 210, 139};
    inline constexpr Color accent_hover{255, 227, 176};
    inline constexpr Color accent_background{62, 49, 39};
    inline constexpr Color accent_border{139, 106, 63};
    inline constexpr Color accent_ink{39, 29, 24};
}
