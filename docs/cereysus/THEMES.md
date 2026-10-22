# Cereysus themes

Two built-in presets, `cereysus-dark` (default) and `cereysus-light`, defined in `static/js/theme.js`
(`THEMES`) and listed first in `src/theme_palette.py` (`THEME_PRESETS`). Every upstream preset is kept.
The values are the owner's palette, mapped onto the engine's five core colors plus `advanced` overrides.

## Mapping (owner token to engine key)

| Owner token | Engine key | Dark | Light |
|---|---|---|---|
| `--bg` | `bg` | `#1B1B3A` | `#F3F3F3` |
| `--text` | `fg` | `#E6E9F2` | `#1A2B44` |
| `--card` | `panel`, `advanced.aiBubbleBg` | `#252441` | `#FFFFFF` |
| `--border` | `border` | `#2E2D55` | `#E5D1B8` |
| `--primary` | `red` (engine accent: links, focus, scrollbar) | `#2EC4CF` | `#3D5A80` |
| `--primary-bg` | `advanced.sendBtnBg`, `advanced.toggleActive` | `#0F7A85` | `#3D5A80` |
| `--accent` | `advanced.brandColor` | `#C9A87C` | `#C6A680` |
| `--accent2` | `advanced.brandMixTo` (dark also `sendBtnHover`) | `#367BB9` | `#DDBB99` |
| `--bg2` | `advanced.sidebarBg`, `advanced.userBubbleBg` | `#141428` | `#EAEAEA` |
| `--border2` | `advanced.bubbleBorder` | `#3A3968` | `#D4C4A8` |
| `--text2` | `text2`, published as `--cereysus-text2` and mapped to `--color-muted` | `#B8BFCF` | `#2C2C2C` |

Syntax colors, semantic colors and the focus ring stay engine-derived (DEC-5).

## Deviations from the proposed mapping

| Item | Value | Why |
|---|---|---|
| `advanced.inputBorder`, light | `#8F8B83` | DEC-4: 3.06:1 on `--bg`, 3.39:1 on `--card` (owner's `--border2` is 1.7:1) |
| `advanced.inputBorder`, dark | `#717092` | Same rule for dark: 3.51:1 on `--bg`, 3.15:1 on `--card` (owner's `--border2` is 1.4:1) |
| `advanced.sendBtnHover`, light | `#314866` | The send button label is white; white on `--accent2` `#DDBB99` is 1.8:1, on `#314866` 9.3:1 |

## Contrast (WCAG 2.x, computed)

| Pair | Dark | Light |
|---|---:|---:|
| text on `--bg` / `--card` | 13.68 / 12.29 | 12.85 / 14.26 |
| `--text2` on `--bg` / `--card` | 9.01 / 8.09 | 12.59 / 13.97 |
| `--primary` on `--bg` / `--card` | 7.84 / 7.04 | 6.37 / 7.06 |
| white on send button | 5.07 | 7.06 |
| white on send button hover | 4.48 | 9.34 |
| login button label (white on 66 % / 78 % mix of `--primary` with black) | 4.61 | 9.61 |

`tests/test_cereysus_themes_static.py` enforces these rules from the source files.

## Where the default theme is duplicated

Keep these in step with `DEFAULT_THEME`: the `:root` block of `static/css/00-tokens.css`, the `:root` block and
saved-theme script of `static/login.html`, the `theme-color` meta and the app-loader fallbacks in `static/index.html`,
`theme_color` and `background_color` in `static/manifest.json`, and `svgThemeCss()` in `static/js/markdown.js`.
The Notes pastel fallbacks are left alone on purpose.

## Known limits (not verifiable without a browser)

- A browser that already saved a theme keeps it. Pick **Cereysus Dark** in Theme, or clear the `odysseus-theme` key.
- Controls that paint white text directly on the accent (`--red`) read at about 2.1:1 on Cereysus Dark. The send
  button and the login button are handled; any other one found in the visual check is a separate fix.
- The brand wordmark in `--accent` on the light sidebar is 1.9:1 (logotype, so WCAG exempts it); `--text` is used for
  all other text on accent fills.
- The toggle knob (`--panel`) against the dark track (`--primary-bg`) is 2.94:1, just under 3:1.
- `--text2` replaces the muted-text token (27 uses in 7 stylesheets, plus the SVG sandbox). In the light theme it is
  `#2C2C2C`, so secondary text is nearly as dark as body text. That is the owner's palette.
- `tests/css_snapshot/baseline.json` was recorded with the upstream defaults. Re-record it on a machine with Node and
  Playwright: `python scripts/css_snapshot.py --write-baseline`.
