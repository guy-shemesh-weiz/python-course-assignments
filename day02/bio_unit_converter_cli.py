#!/usr/bin/env python3
"""
bio_unit_converter_cli.py
-------------------------
Command-line interface that uses bio_unit_converters.py library.

ASCII-only units supported (typeable on a standard keyboard):
  Volume: L, mL, uL, nL
  Mass: kg, g, mg, ug, ng
  Molarity: M, mM, uM, nM
  Mass concentration: g/L, mg/mL, ug/mL, ng/uL, mg/L, ug/L, ng/L, %w/v

Examples:
  python bio_unit_converter_cli.py volume 2 mL uL
  python bio_unit_converter_cli.py mass 5 mg ug
  python bio_unit_converter_cli.py conc 3 mM uM
  python bio_unit_converter_cli.py conc 1 mg/mL g/L
  python bio_unit_converter_cli.py molarity-to-massconc 50 uM mg/L --mw 180.156
  python bio_unit_converter_cli.py massconc-to-molarity 0.9 %w/v mM --mw 58.44
"""

import argparse
import sys

import bio_unit_converters as conv


def _ascii_to_lib(u: str) -> str:
    """Map ASCII-only user inputs to library-accepted forms (normalizing micro to 'u' which library handles)."""
    return u  # library already supports both 'u' and 'µ' forms


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="bio_unit_converter_cli.py",
        description=(
            "Biology Unit Converter CLI - Convert between common biological units\n\n"
            "This tool supports conversions within three main families:\n"
            "  • Volume (L, mL, uL, nL)\n"
            "  • Mass (kg, g, mg, ug, ng)\n"
            "  • Concentration (molarity and mass concentration)\n\n"
            "For conversions between molarity and mass concentration, "
            "you must provide the molar mass (--mw) of the substance."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "EXAMPLES:\n"
            "  # Convert volumes\n"
            "  python bio_unit_converter_cli.py volume 2 mL uL\n"
            "  python bio_unit_converter_cli.py volume 1.5 L mL\n\n"
            "  # Convert masses\n"
            "  python bio_unit_converter_cli.py mass 5 mg ug\n"
            "  python bio_unit_converter_cli.py mass 0.5 kg g\n\n"
            "  # Convert concentrations (within family)\n"
            "  python bio_unit_converter_cli.py conc 3 mM uM\n"
            "  python bio_unit_converter_cli.py conc 1 mg/mL g/L\n\n"
            "  # Cross-family conversions (requires molar mass)\n"
            "  python bio_unit_converter_cli.py molarity-to-massconc 50 uM mg/L --mw 180.156\n"
            "  python bio_unit_converter_cli.py massconc-to-molarity 0.9 %%w/v mM --mw 58.44\n\n"
            "For help on a specific command: python bio_unit_converter_cli.py COMMAND -h"
        ),
    )
    sub = p.add_subparsers(dest="cmd", required=True, metavar="COMMAND")

    # volume
    pv = sub.add_parser(
        "volume",
        help="Convert volume units (L, mL, uL, nL)",
        description=(
            "Convert volume between units.\n\n"
            f"Supported units: {', '.join(conv.ASCII_VOLUME)}\n\n"
            "Examples:\n"
            "  python bio_unit_converter_cli.py volume 2 mL uL\n"
            "  python bio_unit_converter_cli.py volume 0.5 L mL"
        ),
    )
    pv.add_argument("value", type=float, help="Numeric value to convert (e.g., 2.5)")
    pv.add_argument(
    "from_unit", type=str, help=f"Source unit (e.g., mL, uL, L, nL)"
    )
    pv.add_argument(
    "to_unit", type=str, help=f"Target unit (e.g., mL, uL, L, nL)"
    )

    # mass
    pm = sub.add_parser(
        "mass",
        help="Convert mass units (kg, g, mg, ug, ng)",
        description=(
            "Convert mass between units.\n\n"
            f"Supported units: {', '.join(conv.ASCII_MASS)}\n\n"
            "Examples:\n"
            "  python bio_unit_converter_cli.py mass 5 mg ug\n"
            "  python bio_unit_converter_cli.py mass 0.1 g mg"
        ),
    )
    pm.add_argument("value", type=float, help="Numeric value to convert")
    pm.add_argument(
    "from_unit", type=str, help=f"Source unit (e.g., mg, ug, g, ng, kg)"
    )
    pm.add_argument("to_unit", type=str, help=f"Target unit (e.g., mg, ug, g, ng, kg)")

    # conc within-family
    pc = sub.add_parser(
        "conc",
        help="Convert concentrations within the SAME family",
        description=(
            "Convert concentration within the same family ONLY.\n\n"
            f"Molarity units: {', '.join(conv.ASCII_MOLAR)}\n"
            f"Mass concentration units: {', '.join(conv.ASCII_MASSCONC).replace('%', '%%')}\n\n"
            "NOTE: For cross-family conversions (molarity <-> mass concentration), "
            "use the dedicated 'molarity-to-massconc' or 'massconc-to-molarity' commands "
            "which require --mw (molar mass).\n\n"
            "Examples:\n"
            "  python bio_unit_converter_cli.py conc 3 mM uM\n"
            "  python bio_unit_converter_cli.py conc 1 mg/mL g/L"
        ),
    )
    pc.add_argument("value", type=float, help="Numeric value to convert")
    pc.add_argument("from_unit", type=str, help=f"Source unit (molarity: M, mM, uM, nM OR mass-conc: g/L, mg/mL, ug/mL, ng/uL, mg/L, ug/L, ng/L, %%w/v)")
    pc.add_argument("to_unit", type=str, help=f"Target unit (must be same family as source)")

    # molarity to mass concentration
    pmtmc = sub.add_parser(
        "molarity-to-massconc",
        help="Convert molarity to mass concentration (requires molar mass)",
        description=(
            "Convert molarity to mass concentration.\n\n"
            f"Molarity units: {', '.join(conv.ASCII_MOLAR)}\n"
            f"Mass concentration units: {', '.join(conv.ASCII_MASSCONC).replace('%', '%%')}\n\n"
            "REQUIRED: Molar mass (--mw) in g/mol\n\n"
            "Examples:\n"
            "  python bio_unit_converter_cli.py molarity-to-massconc 50 uM mg/L --mw 180.156\n"
            "  python bio_unit_converter_cli.py molarity-to-massconc 1 M g/L --mw 58.44"
        ),
    )
    pmtmc.add_argument("value", type=float, help="Numeric value to convert")
    pmtmc.add_argument(
    "from_unit", type=str, help=f"Source molarity unit (M, mM, uM, nM)"
    )
    pmtmc.add_argument(
    "to_unit", type=str, help=f"Target mass-conc unit (g/L, mg/mL, ug/mL, ng/uL, mg/L, ug/L, ng/L, %%w/v)"
    )
    pmtmc.add_argument(
        "--mw",
        type=float,
        required=True,
        help="Molar mass in g/mol (e.g., 180.156 for glucose, 58.44 for NaCl)",
    )

    # mass concentration to molarity
    pmctm = sub.add_parser(
        "massconc-to-molarity",
        help="Convert mass concentration to molarity (requires molar mass)",
        description=(
            "Convert mass concentration to molarity.\n\n"
            f"Mass concentration units: {', '.join(conv.ASCII_MASSCONC).replace('%', '%%')}\n"
            f"Molarity units: {', '.join(conv.ASCII_MOLAR)}\n\n"
            "REQUIRED: Molar mass (--mw) in g/mol\n\n"
            "Examples:\n"
            "  python bio_unit_converter_cli.py massconc-to-molarity 0.9 %%w/v mM --mw 58.44\n"
            "  python bio_unit_converter_cli.py massconc-to-molarity 10 g/L uM --mw 180.156"
        ),
    )
    pmctm.add_argument("value", type=float, help="Numeric value to convert")
    pmctm.add_argument(
    "from_unit", type=str, help=f"Source mass-conc unit (g/L, mg/mL, ug/mL, ng/uL, mg/L, ug/L, ng/L, %%w/v)"
    )
    pmctm.add_argument(
    "to_unit", type=str, help=f"Target molarity unit (M, mM, uM, nM)"
    )
    pmctm.add_argument("--mw", type=float, required=True, help="Molar mass in g/mol (e.g., 58.44 for NaCl, 180.156 for glucose)")

    return p


def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        if args.cmd == "volume":
            out = conv.convert_volume(
                args.value, _ascii_to_lib(args.from_unit), _ascii_to_lib(args.to_unit)
            )
        elif args.cmd == "mass":
            out = conv.convert_mass(
                args.value, _ascii_to_lib(args.from_unit), _ascii_to_lib(args.to_unit)
            )
        elif args.cmd == "conc":
            out = conv.convert_concentration(
                args.value, _ascii_to_lib(args.from_unit), _ascii_to_lib(args.to_unit)
            )
        elif args.cmd == "molarity-to-massconc":
            out = conv.molarity_to_mass_conc(
                args.value,
                _ascii_to_lib(args.from_unit),
                _ascii_to_lib(args.to_unit),
                args.mw,
            )
        elif args.cmd == "massconc-to-molarity":
            out = conv.mass_conc_to_molarity(
                args.value,
                _ascii_to_lib(args.from_unit),
                _ascii_to_lib(args.to_unit),
                args.mw,
            )
        else:
            parser.error("Unknown command")
            return 2
        print(f"{out:.10g}")
        return 0
    except Exception as e:
        sys.stderr.write(str(e) + "\n")
        return 1


if __name__ == "__main__":
    main()
