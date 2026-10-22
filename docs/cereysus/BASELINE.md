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

### Result (owner, 2026-10-17, after Batch 0B)

- The script found **Python 3.14.8**, outside the 3.11 to 3.12 range this project documents. Everything installed and
  the server started on `http://127.0.0.1:7000` with auth enabled, the built-in MCP servers connected and the task
  scheduler running. Treat 3.14 as working for now; the sandbox checks use Python 3.12.
- The browser tab title is "Cereysus Chat" and the new tagline shows on the welcome screen.
- `/demo` ended without its closing line. Cause: the last tour step's button reads "finish tour", but upstream wires it to
  the same cancel path as "skip tour", and that path returns before the closing line. Fixed in Batch 0 chat 2 (rule
  `tour-finish-closing`); "skip tour" stays silent, as upstream.
- The log reports **ChromaDB not reachable at localhost:8100**. The document vector store, the memory vector store and the
  tool index start in degraded mode. `requirements.txt` ships only `chromadb-client`; upstream's Docker compose supplies
  the server and this PC has no Docker. This affects approved items A12 (Batch 1), A6 (Batch 3), E3 (Batch 15) and E7 to E9
  (Batch 17). Decide the Docker-free path at the start of Batch 1: a local ChromaDB server started by the launcher, or an
  in-process client.

## 7. Full run in Batch 0 chat 2 (2026-10-20)

The whole suite ran on the chat 2 tree in chunks (14,299 tests collected, plus the four new test files). Result: 13,764 passed,
76 failed, 22 errors. Every failure and error was then run again on the unmodified tree (the owner's `cereysus` tip `5ffa963`):

- **74 failures and 20 teardown errors** reproduce on the unmodified tree. They need a browser, `tmux`, process containment or an
  IPv6 loopback, so they are environment failures (75 and 20 at `c74f475`). The failures by file are in the first table below.
- **2 failures were mine and are fixed:** `tests/test_publication_plan_b.py` pins the SHA-256 of the three restored PWA icons in
  `PUBLICATION_ASSET_DECISIONS.md` and the old manifest icon purposes. The ledger now records the Cereysus icons (a note says so)
  and the test expects purpose `any` for the 192 and 512 px icons.
- **2 collection errors** (`tests/test_manage_mcp_command_allowlist.py`, `tests/test_manage_settings_token_budget.py`) appear only
  when they are collected after a test that replaces `src.agent_tools` in `sys.modules`; they occur on the unmodified tree with the
  same file order and pass on their own (46 tests).

| Failing test file | Failures |
|---|---:|
| `tests/test_codeql_python_residual_closure.py` | 4 |
| `tests/test_containment_process_tree.py` | 1 |
| `tests/test_css_computed_style_snapshot.py` | 4 |
| `tests/test_doc_library_open_orphaned.py` | 1 |
| `tests/test_document_history_controls.py` | 1 |
| `tests/test_document_library_mobile_footer.py` | 1 |
| `tests/test_document_module_api.py` | 3 |
| `tests/test_document_outline.py` | 1 |
| `tests/test_document_rich_checklist_enter.py` | 1 |
| `tests/test_document_rich_color_reset_and_contrast.py` | 1 |
| `tests/test_document_rich_docx_export.py` | 2 |
| `tests/test_document_rich_find_boundaries.py` | 1 |
| `tests/test_document_rich_font_color_controls.py` | 1 |
| `tests/test_document_rich_heading_enter.py` | 2 |
| `tests/test_document_rich_image_caption.py` | 1 |
| `tests/test_document_rich_input_rules.py` | 1 |
| `tests/test_document_rich_keyboard_shortcuts.py` | 1 |
| `tests/test_document_rich_selection_toolbar.py` | 1 |
| `tests/test_document_rich_slash_menu.py` | 1 |
| `tests/test_document_rich_smart_link_paste.py` | 1 |
| `tests/test_document_rich_structure_tools.py` | 1 |
| `tests/test_document_rich_table_cell_alignment.py` | 1 |
| `tests/test_document_rich_table_header_preservation.py` | 1 |
| `tests/test_document_rich_table_headers.py` | 1 |
| `tests/test_document_rich_table_merge_split.py` | 1 |
| `tests/test_document_rich_table_tab_history.py` | 1 |
| `tests/test_document_rich_toolbar_menus.py` | 3 |
| `tests/test_document_save_shortcut.py` | 1 |
| `tests/test_document_save_status.py` | 1 |
| `tests/test_document_toolbar_order.py` | 1 |
| `tests/test_email_library_module_graph_js.py` | 2 |
| `tests/test_escape_inner_layers.py` | 2 |
| `tests/test_exact_approval_ungranted_process.py` | 1 |
| `tests/test_execution_filesystem_boundary.py` | 1 |
| `tests/test_frontend_foundation_offline_js.py` | 1 |
| `tests/test_history_resume_rendering_js.py` | 1 |
| `tests/test_live_fallback_round_attribution.py` | 3 |
| `tests/test_notes_reference_browser.py` | 2 |
| `tests/test_notes_reference_contracts_js.py` | 1 |
| `tests/test_orphan_reaping.py` | 1 |
| `tests/test_preview_execution_evidence.py` | 1 |
| `tests/test_production_external_bridge.py` | 1 |
| `tests/test_runtime_evidence_contract.py` | 2 |
| `tests/test_shell_routes.py` | 1 |
| `tests/test_turn_rendering_js.py` | 1 |
| `tests/test_wave3_local_control.py` | 6 |
| `tests/test_workspace_artifact_tool_floor.py` | 3 |
| `tests/test_workspace_confine.py` | 2 |

| Teardown errors | Errors |
|---|---:|
| `tests/test_null_owner_gates.py` | 20 |
