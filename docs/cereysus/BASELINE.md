# Cereysus baseline (Batch 0A)

Recorded 2026-10-16, before any Batch 0B change. This is the reference point for everything that follows.

## 1. Code base

| Item | Value |
|---|---|
| Upstream `dev` | `c74f475` (2026-10-15), five commits after `c3819e3` (README community section, Notes decomposition, skills refactor, upload no-login fix) |
| Fork `odysseus` | pristine mirror, `c3819e3` on GitHub; the sync fast-forwards it to `c74f475` |
| Fork `cereysus` | `953553c` (owner's brand-asset commit on `c3819e3`), then `odysseus` merged in: merge commit `3d50e7f`, no conflicts |
| Tracked files | 2,637 (1,812 `.py`, 362 `.js`, 95 `.mjs`); `src/agent_loop.py` 38,039 lines; 21 CSS files with 1,930 `!important` |
| Name census | 774 text files, 4,759 lines, 5,335 occurrences (`Odysseus` 1,015, `odysseus` 2,916, `ODYSSEUS` 1,404; `odysseus-dev` 106 of the lower-case ones) |
| Owner exclusion scan | 60 inherited hits in the same 6 files as at `c3819e3`; removed by Batch 0F |

The classified census is in `REBRAND_INVENTORY.md`.

## 2. Sandbox used for checks

Ubuntu 24 (Linux), 1 CPU, 4 GB RAM, Python 3.12.3, Node 22.22.2, git 2.43.0, pytest 9.1.1, dependencies from `requirements.txt` and `requirements-dev.txt`.
No browser, no Playwright, no `tmux`, no process containment, no IPv6 loopback, no Windows. Anything that needs those is marked "not verified" in `CHANGES.md` and must be checked on the owner's PC.

## 3. Test baseline

The suite collects 14,275 tests in 1,319 files. It was run in 10 chunks of about 1,500 tests on the 0B tree. Result: **14,119 passed, 81 skipped, 75 failed**, plus 20 teardown errors that come from one upstream test file.

All 75 failures and all 20 errors were then re-run on the unmodified tree (`3d50e7f`) and fail there in exactly the same way, so none of them comes from the rebrand. A full run of the unmodified tree was not completed in the sandbox; the claim is therefore "no new failures", not "everything else passes on the unmodified tree".

| Count | Cause | Files |
|---:|---|---|
| 50 | Needs a real browser (Node/Playwright suites) | `test_document_*` (32), `test_css_computed_style_snapshot` (4), `test_live_fallback_round_attribution` (3), `test_email_library_module_graph_js` (2), `test_escape_inner_layers` (2), `test_notes_reference_browser` (2), `test_doc_library_open_orphaned`, `test_frontend_foundation_offline_js`, `test_history_resume_rendering_js`, `test_notes_reference_contracts_js`, `test_turn_rendering_js` (1 each) |
| 14 | No process containment in the sandbox ("containment unavailable") or PTY and process-tree limits | `test_workspace_artifact_tool_floor` (3), `test_workspace_confine` (2), `test_runtime_evidence_contract` (2), `test_containment_process_tree`, `test_exact_approval_ungranted_process`, `test_execution_filesystem_boundary`, `test_orphan_reaping`, `test_preview_execution_evidence`, `test_production_external_bridge`, `test_shell_routes` (1 each) |
| 6 | `tmux` missing | `test_wave3_local_control` |
| 4 | No IPv6 loopback | `test_codeql_python_residual_closure` (dual-stack localhost) |
| 1 | **Repository state, not the sandbox** | `test_docs_no_orphan_images`: the three images the owner committed under `assets/branding/cereysus/` (`apple-touch-icon-180.png`, `cereysus-hardhat.png`, `cereysus-wordmark.png`) are not referenced by any tracked text. Batch 0D references them (README, `index.html`), which turns this test green. |
| 20 errors | Upstream test hygiene guard ("test left bare module stub(s) in sys.modules: src.webhook_manager") at teardown | `test_null_owner_gates` (the tests themselves pass) |

Tests that need a browser cannot be run by Claude. For Batches 0C and 0D the owner's visual check replaces them (see the owner checks in the Development Prompt).

## 4. Brand assets (owner commit `953553c`)

All nine files are present in `assets/branding/cereysus/` and match the audit in the Development Prompt (6.6):

| File | Check |
|---|---|
| `icon-maskable-512.png` | 512x512, opaque `#1B1B3A`, differs from `icon-512.png`; no artwork outside the 80 % safe circle (0 of 10,507 samples) |
| `apple-touch-icon-180.png` | 180x180, opaque `#1B1B3A` |
| `icon.ico` | 9 sizes: 16, 24, 32, 48, 64, 72, 96, 128, 256 |
| `cereysus-hardhat.svg` | viewBox 1095, 4 paths, no `<text>` |
| `cereysus-wordmark.svg` | viewBox 168x40, still has one `<text>` element (Poppins): the text is outlined in 0D (DEC-10) |
| `cereysus-hardhat.png`, `cereysus-wordmark.png`, `icon-192.png`, `icon-512.png` | present, sizes as listed in 6.5 |

## 5. Upstream facts re-verified for Batches 0C-0F

- Every path and line number in Development Prompt sections 5 and 6.3 still holds at `c74f475`.
- The built-in "Odysseus" character exists in three places: `static/js/presets.js` (id `odysseus`, name and prompt), `static/js/tasks.js` (label in the task character list) and `src/reminder_personas.py`. 0B rewrites the prompt and renames the label; the id stays (it is stored in settings and tasks).
- `static/js/slashCommands.js` has an `/odyssey` easter egg that prints Homer quotations. The quotation naming the hero is not the product name and is left alone.
- Two persisted texts double as lookup keys and are not renamed (proposal P-1): the reminder e-mail subject marker and the e-mail auto-reply task description.
- Notes were decomposed upstream: `static/js/notes.js` is now a five-line shim. The notes colour fallbacks live in `frontend/src/features/notes/ui/colors.js` and are deployed byte-for-byte to `static/js/features/notes/ui/colors.js` (`frontend/modules.json`; a test enforces the identity). Batch 0C must edit both copies together or leave those pastel note colours alone.
- `.gitattributes` forces CRLF in the working tree for `*.ps1` and `*.bat` and LF for `*.sh` and `frontend/src/**`; the index holds LF. The rebrand tool preserves line endings byte for byte.

## 6. Owner's boot check of `launch-windows.ps1` (to be run on the PC)

Run it once on the branch as you have it (before applying 0B if you can; 5 minutes) and once after 0B:

```powershell
cd C:\path\to\cereysus
powershell -ExecutionPolicy Bypass -File .\launch-windows.ps1 -Port 7000 -BindHost 127.0.0.1
```

Expected: the script finds Python 3.11 or 3.12 and Git's bash, creates the virtual environment, installs the requirements (several minutes on the first run), starts the server and prints `http://127.0.0.1:7000`. Open that address, create the admin account and confirm the chat page loads. Send back: the Python and Git versions the script reports, how long the first start took, and any error text.
