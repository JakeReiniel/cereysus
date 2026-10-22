# Cereysus brand assets

The source of truth is `assets/branding/cereysus/`. The app serves the copies listed below.
`tests/test_cereysus_brand_assets_static.py` checks that the copies are byte-identical to the sources.

| Source file | Shipped copy | Used for |
|---|---|---|
| `cereysus-hardhat.svg` | `static/branding/cereysus-hardhat.svg` | Welcome screen and login page (`<img>`), precached by the service worker |
| `cereysus-hardhat.png` (1254 x 1254) | not shipped | Documents and README |
| `cereysus-wordmark.png` (780 x 210, navy badge) | not shipped | README header |
| `cereysus-wordmark.svg` (168 x 40, outlined text) | not shipped | Vector wordmark for documents and print |
| `icon.ico` (9 sizes, 16 to 256 px) | `static/icon.ico` | Windows executable icon (`Cereysus.spec`) |
| `icon-192.png`, `icon-512.png` | `static/icons/` | Favicon and manifest icons, purpose `any` |
| `icon-maskable-512.png` | `static/icons/` | Manifest icon, purpose `maskable` only |
| `apple-touch-icon-180.png` | `static/icons/` | `apple-touch-icon` link in `index.html` and `login.html` |

## Notes

- **Maskable and Apple icons.** Both use an opaque `#1B1B3A` background. The maskable artwork stays inside the 80 %
  safe circle (farthest artwork pixel 158 px from the center, limit 205 px), so Android can crop it safely. The
  manifest marks the 192 and 512 px icons `any` and only the dedicated file `maskable`.
- **Wordmark lettering (DEC-10).** The `<text>` element was converted to outlines with a static fill `#C9A87C`,
  because CSS variables and web fonts do not apply inside an `<img>`. The owner's wordmark PNG is set in DejaVu Sans
  Bold (the SVG's own font stack names Poppins, which would be narrower), so the outlines come from DejaVu Sans Bold
  at the SVG's 25 unit size. They match the PNG lettering (overlap 0.93 against the PNG text). Poppins outlines are
  possible if you prefer them.
- **Favicon.** The hat is multi-tone and cannot be tinted, so the root route uses the static `icon-192.png`. The
  per-route line icons (calendar, notes, and so on) still follow the theme accent.
- **Tray and splash.** `launcher.py` loads `static/icons/icon-192.png` for the tray icon (64 px) and the splash
  screen (64 px), and draws a simple tan hard hat if the file cannot be read.
- **Updating an asset.** Replace the file in `assets/branding/cereysus/`, copy it to its shipped location, and raise
  the `-cy` suffix in the `sw-cache-name` rule of `tools/rebrand/rebrand-map.yml` so installed apps refetch it.
  If it is one of the three PWA icons, also update its `RESTORE-012` to `RESTORE-014` hash in `PUBLICATION_ASSET_DECISIONS.md`.
