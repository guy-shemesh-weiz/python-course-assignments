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
        description="Biology Unit Converter CLI (ASCII-only units). "
        "Use subcommands for volume, mass, conc, and cross-family conversions.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    sub = p.add_subparsers(dest="cmd", required=True, metavar="COMMAND")

    # volume
    pv = sub.add_parser(
        "volume",
        help="Convert volume units",
        description=(
            f"Convert volume between units.\nSupported units: {', '.join(conv.ASCII_VOLUME)}"
        ),
    )
    pv.add_argument("value", type=float, help="Numeric value to convert (e.g., 2.5)")
    pv.add_argument(
    "from_unit", type=str, help=f"Source unit ({', '.join(conv.ASCII_VOLUME)})"
    )
    pv.add_argument(
    "to_unit", type=str, help=f"Target unit ({', '.join(conv.ASCII_VOLUME)})"
    )

    # mass
    pm = sub.add_parser(
        "mass",
        help="Convert mass units",
        description=(
            f"Convert mass between units.\nSupported units: {', '.join(conv.ASCII_MASS)}"
        ),
    )
    pm.add_argument("value", type=float, help="Numeric value to convert")
    pm.add_argument(
    "from_unit", type=str, help=f"Source unit ({', '.join(conv.ASCII_MASS)})"
    )
    pm.add_argument("to_unit", type=str, help=f"Target unit ({', '.join(conv.ASCII_MASS)})")

    # conc within-family
    pc = sub.add_parser(
        "conc",
        help="Convert concentration within SAME family",
        description=(
            "Convert concentration within the same family ONLY.\n"
            f"Molarity units: {', '.join(conv.ASCII_MOLAR)}\n"
            f"Mass concentration units: {', '.join(conv.ASCII_MASSCONC).replace('%', '%%')}\n"
            "NOTE: For cross-family conversions (molarity <-> mass concentration), "
            "use the dedicated commands that require --mw."
        ),
    )
    pc.add_argument("value", type=float, help="Numeric value to convert")
    pc.add_argument("from_unit", type=str, help=f"Source unit (molarity or mass-conc)")
    pc.add_argument("to_unit", type=str, help=f"Target unit (same family as source)")

    # molarity to mass concentration
    pmtmc = sub.add_parser(
        "molarity-to-massconc",
        help="Molarity -> Mass concentration (requires --mw)",
        description=(
            "Convert molarity to mass concentration.\n"
            f"Molarity units: {', '.join(conv.ASCII_MOLAR)}\n"
            f"Mass concentration units: {', '.join(conv.ASCII_MASSCONC).replace('%', '%%')}\n"
            "Requires molar mass (g/mol) via --mw."
        ),
    )
    pmtmc.add_argument("value", type=float, help="Numeric value to convert")
    pmtmc.add_argument(
    "from_unit", type=str, help=f"Source molarity unit ({', '.join(conv.ASCII_MOLAR)})"
    )
    pmtmc.add_argument(
    "to_unit", type=str, help=f"Target mass-conc unit ({', '.join(conv.ASCII_MASSCONC).replace('%', '%%')})"
    )
    pmtmc.add_argument(
        "--mw",
        type=float,
        required=True,
        help="Molar mass in g/mol (e.g., 58.44 for NaCl)",
    )

    # mass concentration to molarity
    pmctm = sub.add_parser(
        "massconc-to-molarity",
        help="Mass concentration -> Molarity (requires --mw)",
        description=(
            "Convert mass concentration to molarity.\n"
            f"Mass concentration units: {', '.join(conv.ASCII_MASSCONC).replace('%', '%%')}\n"
            f"Molarity units: {', '.join(conv.ASCII_MOLAR)}\n"
            "Requires molar mass (g/mol) via --mw."
        ),
    )
    pmctm.add_argument("value", type=float, help="Numeric value to convert")
    pmctm.add_argument(
    "from_unit", type=str, help=f"Source mass-conc unit ({', '.join(conv.ASCII_MASSCONC).replace('%', '%%')})"
    )
    pmctm.add_argument(
    "to_unit", type=str, help=f"Target molarity unit ({', '.join(conv.ASCII_MOLAR)})"
    )
    pmctm.add_argument("--mw", type=float, required=True, help="Molar mass in g/mol")

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
