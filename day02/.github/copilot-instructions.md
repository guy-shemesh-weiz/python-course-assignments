## Quick context

This repository is a small Python project (single-package style) providing a biology unit conversion library and three frontends: a CLI, a Tkinter GUI, and an interactive terminal prompt. Key files:

- `bio_unit_converters.py` — the pure library, public API functions: `convert_volume`, `convert_mass`, `convert_concentration`, `molarity_to_mass_conc`, `mass_conc_to_molarity` (see `__all__`).
- `bio_unit_converter_cli.py` — CLI frontend (argparse) with subcommands: `volume`, `mass`, `conc`, `molarity-to-massconc`, `massconc-to-molarity`.
- `bio_unit_converter_gui.py` — Tkinter GUI that calls the same library.
- `bio_unit_converter_interactive.py` — prompt-based interactive frontend.

## Big-picture architecture

- Single source-of-truth library: `bio_unit_converters.py`. All user-facing frontends import and rely on its conversion functions.
- Frontends are thin wrappers that mostly validate or parse input and pass normalized units to the library.
- Cross-family conversions (molarity <-> mass concentration) require an explicit molar mass (g/mol) parameter.

## Project-specific conventions (do not change without reason)

- Unit normalization: the library normalizes micro symbols. Either `u` (ASCII) or `µ`/`μ` are supported — frontends normalize inputs before calling the library. Follow `_normalize_unit` / `normalize_unit` behavior.
- ASCII-only CLI: the CLI documents and expects typeable ASCII units (e.g. `uL`, `ug`) but maps them to the library's formats; preserve `ASCII_VOLUME`, `ASCII_MASS`, etc., when editing the CLI.
- Numeric formatting: conversion outputs are printed with `f"{out:.10g}"` (10 significant digits). Keep consistent formatting in new frontends/tools.
- Percent w/v handling: `%w/v` is implemented as `10 g/L` (g per 100 mL => 10 g/L). If you add units, ensure conversion tables mirror the dictionary keys in the library.

## Files and patterns to reference when coding

- Look at the unit mapping dicts in `bio_unit_converters.py`: `_VOLUME_TO_L`, `_MASS_TO_G`, `_MOLARITY_TO_M`, `_MASSCONC_TO_G_PER_L`. Add units by updating these maps and corresponding frontend unit lists.
- Public API is small and type-annotated. Prefer calling the library functions rather than reimplementing conversion logic in frontends.
- Error strategy: the library raises `ValueError` for unsupported conversions; the CLI converts exceptions to stderr and returns exit code `1`. Tests or new CLIs should mirror this behavior.

## Common developer workflows (explicit commands)

- Run CLI examples (from repo folder):
  - `python3 bio_unit_converter_cli.py volume 2 mL uL`
  - `python3 bio_unit_converter_cli.py molarity-to-massconc 50 uM mg/L --mw 180.156`
- Run GUI: `python3 bio_unit_converter_gui.py` (uses Tkinter)
- Run interactive prompt: `python3 bio_unit_converter_interactive.py`

There is no build/packaging or automated test harness in the repo — running the scripts with `python3` is the canonical way to smoke-test changes.

## Integration points & responsibilities

- Any new UI or integration should import `bio_unit_converters` and call the public functions. Do not duplicate unit tables; reuse or import them where possible.
- Cross-family conversions must accept and validate a molar mass (`mw` / `--mw`) and pass it to the relevant library function.

## Helpful examples to copy / follow

- CLI subcommand wiring (use `build_parser()` from `bio_unit_converter_cli.py` as a reference) — create subparsers and mirror the existing argument names.
- Unit normalization helper: `_normalize_unit` in the library and `normalize_unit` in the GUI show how to normalize `μ/µ` to a canonical form — reuse this when parsing inputs.

## What not to change lightly

- Changing unit mapping constants or normalization rules without updating all frontends will break the CLI/GUI/interactive parity.
- Changing output formatting or CLI exit codes — keep `stderr` on errors and non-zero exit code for programmatic clients.

## If you need to add tests

- Add small unit tests that import `bio_unit_converters` and verify:
  - round-trip conversions within a family (e.g., mL -> L -> mL)
  - cross-family conversions with a known molar mass
  - normalization of `u` vs `µ`

---

If anything in this file is unclear or you want additional examples (small unit tests, sample inputs/outputs, or CI rules), tell me which section to expand and I will update it.
