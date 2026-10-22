# Keeping Cereysus in sync with Odysseus

## Branches and remotes

| Name | What it is |
|---|---|
| `origin` | the fork, https://github.com/JakeReiniel/cereysus |
| `upstream` | https://github.com/odysseus-dev/odysseus.git (default branch `dev`) |
| `odysseus` | pristine mirror of `upstream/dev`; no Cereysus work lands here |
| `cereysus` | the product branch (the fork's default branch) |
| `batch/<id>-<slug>` | one branch per piece of work, merged into `cereysus`; each finished chat is tagged `cereysus-bN` |

## Sync steps

```powershell
git remote add upstream https://github.com/odysseus-dev/odysseus.git   # once
git fetch upstream
git switch odysseus
git merge --ff-only upstream/dev
git push origin odysseus
git switch cereysus
git merge odysseus
```

If the merge reports conflicts:

1. Take upstream's side of each conflict (while on `cereysus`, that is `git checkout --theirs <file>`), then `git add <file>`.
2. Look for leftovers before committing. A hand-edited conflict can leave marker text or a stray branch-name line behind:
   `git grep -n -E '^(<<<<<<<|>>>>>>>)( |$)'` and `git grep -n -E '^(HEAD|batch/.*)$'`. Both must print nothing
   (a line of `=======` also shows up in some license text files; that is fine).
3. Re-apply the rebrand (next section), run the tests, then commit.

## The rebrand tool

`tools/rebrand/` renames the product in user-visible text and keeps identifiers, URLs, headers and licenses as they are.
It needs Python 3.11 or newer and PyYAML.

```powershell
python tools/rebrand/rebrand.py                 # dry run: unified diff and a residual-hit report
python tools/rebrand/rebrand.py --apply         # write the changes (idempotent; keeps CRLF and LF byte for byte)
python tools/rebrand/rebrand.py --check         # exit 1 if changes are pending or a rule drifted
python tools/rebrand/rebrand.py --inventory docs/cereysus/REBRAND_INVENTORY.md
python -m pytest tools/rebrand/test_rebrand.py
```

Everything is driven by `tools/rebrand/rebrand-map.yml`: path policies (first match wins), protected patterns, explicit
rules and file renames. After a merge, run `--apply`, then `--check`, and read the report:

- A `RULE DRIFT` line means upstream changed text that a rule targets. Fix the rule in the map.
- Hits in a file with no policy land in the report as held; give the file a policy if it should be renamed.
- Tier 0 files (`LICENSE`, `ACKNOWLEDGMENTS.md`, `THIRD_PARTY_PROVENANCE.json`, `licenses/`) are never edited by the tool.
  `ACKNOWLEDGMENTS.md` may only be appended to by hand.
- `website/` is left as upstream has it (owner decision).

## Checks after every merge

1. `python tools/rebrand/rebrand.py --check` exits 0.
2. Run the exclusion scan you keep outside the repository. It prints `path:line` for each hit and must report 0.
3. Run the targeted tests:
   `python -m pytest tools/rebrand/test_rebrand.py tests/test_cereysus_themes_static.py tests/test_cereysus_brand_assets_static.py tests/test_cereysus_notices_static.py`
   The full suite takes about 30 minutes; run it in chunks. `docs/cereysus/BASELINE.md` lists the failures that come from
   the environment (no browser, no `tmux`) and not from the code.
4. When a theme or a CSS token changed, re-record the computed-style baseline on a machine with Node and Playwright:
   `python scripts/css_snapshot.py --write-baseline`.
5. When static assets changed, raise the `-cy` suffix in the `sw-cache-name` rule of the map, so installed apps refetch them.
6. When the PWA icons change, also update the three `RESTORE-012` to `RESTORE-014` hashes in `PUBLICATION_ASSET_DECISIONS.md`;
   `tests/test_publication_plan_b.py` checks them and the manifest icon purposes.
