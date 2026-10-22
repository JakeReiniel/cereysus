# Notice

Cereysus is a modified version of Odysseus (https://github.com/odysseus-dev/odysseus), licensed under the GNU AGPL-3.0-or-later. Modifications (c) 2026 Cereysus.

## What this means

- Cereysus is distributed under the same license as Odysseus. The full text is in [LICENSE](LICENSE). Third-party
  licenses and acknowledgments are in [ACKNOWLEDGMENTS.md](ACKNOWLEDGMENTS.md) and `licenses/`. None of them was changed.
- The upstream copyright and license notices stay in every file that carries them.
- Cereysus was modified in 2026. The git history of this repository records every change, file by file.
- Source code: https://github.com/JakeReiniel/cereysus. Anyone who uses a running copy of Cereysus over a network can get
  its corresponding source there (AGPL-3.0, section 13).

## Modifications

- The product name, logos, icons and the Cereysus light and dark themes.
- A rebrand tool (`tools/rebrand/`) that applies the name change as an idempotent script, so upstream merges stay cheap.
- Technical notes in `docs/cereysus/`.

Files carrying the upstream name in identifiers, environment variables, storage keys and links were left as they are on
purpose; `docs/cereysus/REBRAND_INVENTORY.md` lists every occurrence and how it was handled.
