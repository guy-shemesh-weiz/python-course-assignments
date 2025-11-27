# Copilot instructions for this repository

Purpose: give AI coding agents the minimal, concrete knowledge needed to be productive in this repo.

Overview
- This workspace contains small, self-contained daily Python exercises (folders `day01/` .. `day05/`).
- Each day is effectively its own mini-project: source, frontends, and tests live inside the day directory.

Big picture & architecture (what to know immediately)
- The canonical biology unit-conversion library is `bio_unit_converters.py` (found in `day02/` and an updated, Pint-based version in `day03/`).
  - Public API functions to call: `convert_volume`, `convert_mass`, `convert_concentration`, `molarity_to_mass_conc`, `mass_conc_to_molarity`.
  - `day02/` uses hand-rolled dictionaries. `day03/` uses `pint` for conversions; both preserve the same public API and unit lists.
- Thin frontends reuse that library: `bio_unit_converter_cli.py` (CLI), `bio_unit_converter_gui.py` (Tkinter), and `bio_unit_converter_interactive.py` (prompt).
- Separately, `day04/` is a different utility (gene CLI): `cli.py` (UI) calls `business.py` (network + cache). Treat day folders as independent modules unless you intentionally coordinate changes across days.

Project-specific conventions (do not change without cross-check)
- Unit normalization: code normalizes micro-symbols — both ASCII `u` and unicode `µ`/`μ` are accepted. Use `_normalize_unit` / `normalize_unit` helpers rather than ad-hoc string handling.
- ASCII-friendly CLI: frontends expose ASCII-friendly unit names (e.g., `uL`, `ug`) while mapping to canonical forms in the library. Keep `ASCII_*` lists aligned with `VOLUME_UNITS`, `MASS_UNITS`, etc.
- Percent w/v: `%w/v` is treated as 10 g/L (g per 100 mL => 10 g/L). This special-case mapping appears in the conversion helpers — preserve it when adding units.
- Output formatting: conversion outputs in existing frontends use 10 significant digits style (e.g., `f"{out:.10g}"`) — keep consistent when adding printing/CLI behavior.

Key files to inspect / copy patterns from
- `day02/bio_unit_converters.py` — simple dict-based implementation and unit maps.
- `day03/bio_unit_converters.py` — Pint-backed implementation; includes `_unit_to_pint_string` and `_pint_convert` helpers. Prefer this for any new conversion work.
- `day02/bio_unit_converter_cli.py` / `day03/bio_unit_converter_cli.py` — example subparser wiring and error handling (print to stderr and return non-zero on failure).
- `day04/cli.py` and `day04/business.py` — pattern for separating UI (CLI) and business/network logic, with a simple JSON cache (`cache.json`) and robust fallback strategies.
- Tests: `day02/tests/` and `day03/tests/` show the test style and how tests import local modules (they insert the repo parent into `sys.path`).

Developer workflows & commands
- Run a frontend from its day folder, e.g.:
  - `python3 bio_unit_converter_cli.py volume 2 mL uL`
  - `python3 bio_unit_converter_gui.py` (starts Tkinter UI)
  - `python3 bio_unit_converter_interactive.py` (prompt)
- Run tests from the project root or day folder. Example (day03 uses Pint):
  - `cd day03 && python3 -m pytest -q`
- Dependencies live in per-day `requirements.txt` (e.g., `day03/requirements.txt` includes `pint>=0.23`, `pytest>=7.0`). Install in a venv per-day when needed.

Patterns, error handling & integration points
- Reuse the library: new UIs or features should import the public functions from `bio_unit_converters.py` instead of reimplementing conversion logic.
- Error model: the library raises `ValueError` for unsupported or incompatible conversions. Frontends translate these to user-facing messages and non-zero exit codes.
- Cache & network: `day04/business.py` shows a best-effort cache model that tolerates save failures and normalizes legacy cache formats. When adding network calls, follow the same defensiveness.

Tests & examples to mirror
- Unit tests include:
  - round-trip conversion tests (volume round-trip)
  - cross-family conversion with known molar mass (molarity <-> mass concentration)
  - normalization of `u` vs `µ`
- When adding tests: place them under the same `dayNN/tests/` folder and follow existing import pattern (tests insert the parent dir onto `sys.path`).

Small actionable rules for an AI coding agent
1. Always prefer calling `bio_unit_converters` public API. If you must edit unit mappings, update both canonical lists (`VOLUME_UNITS`, etc.) and ASCII lists (`ASCII_*`).
2. Preserve micro-symbol normalization and `%w/v` semantics.
3. Keep CLI text and exit-code behavior consistent with existing CLIs: human-friendly errors on stderr, exit code `1` for failures.
4. If you add a dependency (like `pint`), update the appropriate `dayNN/requirements.txt` and only change the day where the new dependency is required.
5. Run the local tests in that day directory before submitting changes.

Notes / where to look for more examples
- See `day03/.github/copilot-instructions.md` for the per-day AI note history and prompts used during development. Use it only as background — the repo-level file above is the source of truth for behavior.

If any of these items are unclear or you want more examples (small unit tests, sample CLI inputs/outputs, or CI rules), tell me which section to expand and I will update this file.
